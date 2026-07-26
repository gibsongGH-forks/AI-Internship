"""Week 1 live demo — five stages in one file, built up live in class."""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

import vector_store

# Load .env from this folder so the key is found regardless of shell working directory.
_ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(_ENV_PATH)

# Reuse one client so TLS handshakes are not repeated on every request.
app = FastAPI()
client = OpenAI()  # Reads OPENAI_API_KEY from the environment; never hardcode keys.

# Stage 4 default — strong general model; swap at request time for the live demo.
DEFAULT_MODEL = "gpt-4o"

# Stage 5 — per-1K-token input/output USD (derived from OpenAI list prices).
MODEL_PRICES_PER_1K: dict[str, tuple[float, float]] = {
    "gpt-4o": (0.0025, 0.01),
    "gpt-4o-mini": (0.00015, 0.0006),
    "o3-mini": (0.0011, 0.0044),
}

# /ingest chunking — configurable via env vars so tuning doesn't require a code change.
INGEST_CHUNK_SIZE = int(os.getenv("INGEST_CHUNK_SIZE", "800"))
INGEST_CHUNK_OVERLAP = int(os.getenv("INGEST_CHUNK_OVERLAP", "100"))

# /ask retrieval — how many chunks to ground each answer in.
RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))

GROUNDING_PROMPT_TEMPLATE = """Answer the QUESTION using ONLY the CONTEXT below.

Rules:
- Do not use any knowledge outside the CONTEXT.
- Cite the document each fact comes from using [document_id] right after the claim.
- If the CONTEXT does not contain enough information to answer, say so plainly \
instead of guessing.

CONTEXT:
{context}

QUESTION:
{question}"""


def build_grounding_prompt(question: str, chunks: list[dict]) -> str:
    """Turn retrieved chunks into a prompt the model must answer strictly from."""

    if chunks:
        context = "\n\n".join(f"[{chunk['document_id']}] {chunk['text']}" for chunk in chunks)
    else:
        context = "(no relevant context found)"
    return GROUNDING_PROMPT_TEMPLATE.format(context=context, question=question)


class Answer(BaseModel):
    """Structured model output — this is what turns a chatbot into a component."""

    answer: str
    confidence: float = Field(ge=0.0, le=1.0)
    sources_needed: bool


class AskRequest(BaseModel):
    """Typed request body so bad input is rejected before we spend tokens."""

    question: str
    force_bad: bool = False  # Stage 3 demo knob — first attempt breaks schema on purpose.
    model: str | None = None  # Stage 4 — optional override to swap models live.


class AskResponse(BaseModel):
    """Typed response so callers always get the same shape back."""

    answer: Answer
    tokens_used: int
    model: str
    latency_ms: int
    cost_usd: float
    retrieved_chunk_ids: list[str]


def compute_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Turn real usage into dollars — same prompt, different model, different cost."""

    prices = MODEL_PRICES_PER_1K.get(model, MODEL_PRICES_PER_1K[DEFAULT_MODEL])
    input_per_1k, output_per_1k = prices
    return (prompt_tokens / 1000 * input_per_1k) + (completion_tokens / 1000 * output_per_1k)


def call_model_structured(question: str, model: str) -> tuple[Answer, int, int, int]:
    """
    Stage 2 center: OpenAI structured output forces exactly the Answer schema.
    Returns parsed answer plus token counts from billing metadata.
    """

    completion = client.chat.completions.parse(
        model=model,
        messages=[{"role": "user", "content": question}],
        response_format=Answer,
    )

    parsed = completion.choices[0].message.parsed
    if parsed is None:
        raise ValueError("Model returned no parseable structured output")

    usage = completion.usage
    total = usage.total_tokens if usage else 0
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return parsed, total, prompt_tokens, completion_tokens


def call_model_unsafe(question: str, model: str) -> tuple[Answer, int, int, int]:
    """
    Stage 3 demo path: free-form JSON call, then validate locally.
    The bad instruction makes confidence a string so Pydantic rejects it reliably.
    """

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": (
                    f"{question}\n\n"
                    "Reply with ONLY a JSON object using keys answer, confidence, sources_needed. "
                    "Set confidence to the string 'very high' (not a number)."
                ),
            }
        ],
    )

    raw = completion.choices[0].message.content or ""
    # Guardrail: refuse malformed output instead of passing it through to clients.
    answer = Answer.model_validate_json(raw)

    usage = completion.usage
    total = usage.total_tokens if usage else 0
    prompt_tokens = usage.prompt_tokens if usage else 0
    completion_tokens = usage.completion_tokens if usage else 0
    return answer, total, prompt_tokens, completion_tokens


@app.post("/ask")
def ask(body: AskRequest) -> AskResponse:
    """Answer one question, grounded in retrieved chunks, with cost visibility."""

    model = body.model or DEFAULT_MODEL
    last_error: str | None = None

    retrieved = vector_store.query_similar(body.question, top_k=RAG_TOP_K)
    retrieved_chunk_ids = [chunk["id"] for chunk in retrieved]
    prompt = build_grounding_prompt(body.question, retrieved)

    # Stage 3: one retry keeps the logic legible while still protecting callers.
    for attempt in range(2):
        try:
            start = time.perf_counter()

            # First attempt with force_bad uses the unsafe path; retry uses structured output.
            use_bad_path = body.force_bad and attempt == 0
            if use_bad_path:
                answer, tokens_used, prompt_tokens, completion_tokens = call_model_unsafe(
                    prompt, model
                )
            else:
                answer, tokens_used, prompt_tokens, completion_tokens = call_model_structured(
                    prompt, model
                )

            latency_ms = int((time.perf_counter() - start) * 1000)
            cost_usd = compute_cost_usd(model, prompt_tokens, completion_tokens)

            return AskResponse(
                answer=answer,
                tokens_used=tokens_used,
                model=model,
                latency_ms=latency_ms,
                cost_usd=round(cost_usd, 6),
                retrieved_chunk_ids=retrieved_chunk_ids,
            )
        except (ValidationError, ValueError) as exc:
            last_error = str(exc)
            continue

    # Clean failure — never leak a half-parsed response to the client.
    raise HTTPException(
        status_code=502,
        detail=f"Model response failed schema validation after retry: {last_error}",
    )


class IngestRequest(BaseModel):
    """Typed request body for indexing a document into the vector store."""

    document_id: str
    text: str
    metadata: dict | None = None  # e.g. {"source": "notes.pdf"}


class IngestResponse(BaseModel):
    """Typed response so callers always get the same shape back."""

    document_id: str
    chunks_indexed: int
    status: str


@app.post("/ingest")
def ingest(body: IngestRequest) -> IngestResponse:
    """
    Chunk, embed, and upsert one document into the vector store.

    curl -s -X POST http://127.0.0.1:8000/ingest \
      -H "Content-Type: application/json" \
      -d '{
            "document_id": "doc-1",
            "text": "Some long document text to index...",
            "metadata": {"source": "notes.pdf"}
          }'
    """

    if not body.text or not body.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=INGEST_CHUNK_SIZE, chunk_overlap=INGEST_CHUNK_OVERLAP
    )
    pieces = splitter.split_text(body.text)
    if not pieces:
        raise HTTPException(status_code=400, detail="text produced no chunks")

    source = (body.metadata or {}).get("source")
    chunks = [
        {
            "id": f"{body.document_id}-{i}",
            "text": piece,
            "metadata": {
                "document_id": body.document_id,
                "chunk_index": i,
                # Pinecone rejects null metadata values, so omit source when absent.
                **({"source": source} if source is not None else {}),
            },
        }
        for i, piece in enumerate(pieces)
    ]

    chunks_indexed = vector_store.upsert_chunks(chunks)

    return IngestResponse(document_id=body.document_id, chunks_indexed=chunks_indexed, status="ok")


class RetrieveResult(BaseModel):
    """One retrieved chunk with its similarity score and source metadata."""

    id: str
    score: float
    document_id: str | None = None
    chunk_index: int | None = None
    source: str | None = None
    text: str


class RetrieveResponse(BaseModel):
    """Typed response so callers always get the same shape back."""

    query: str
    results: list[RetrieveResult]


@app.get("/debug/retrieve")
def debug_retrieve(q: str) -> RetrieveResponse:
    """
    Embed a question and return the top-5 most similar chunks. No LLM call —
    for verifying retrieval quality before wiring it into /ask.

    curl -s "http://127.0.0.1:8000/debug/retrieve?q=How%20many%20remote%20days%20are%20allowed%3F"
    """

    if not q or not q.strip():
        raise HTTPException(status_code=400, detail="q must not be empty")

    matches = vector_store.query_similar(q, top_k=5)
    return RetrieveResponse(query=q, results=[RetrieveResult(**match) for match in matches])


@app.get("/debug/pinecone")
def debug_pinecone() -> dict:
    """Confirm Pinecone is configured and reachable, for local and Render checks alike."""

    try:
        return vector_store.pinecone_health()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Pinecone unreachable: {exc}")
