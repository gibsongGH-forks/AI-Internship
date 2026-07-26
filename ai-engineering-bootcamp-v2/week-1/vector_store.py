"""Pinecone vector store: shared embedding model, upsert/query helpers, and a health check."""

import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from pinecone import Pinecone

# Load .env from this folder so the keys are found regardless of shell working directory.
load_dotenv(Path(__file__).resolve().parent / ".env")

# Same model at ingest and query time — mismatched models produce meaningless similarity scores.
EMBEDDING_MODEL = "text-embedding-3-small"


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


_client = OpenAI()  # Reads OPENAI_API_KEY from the environment.
_pc = Pinecone(api_key=_require_env("PINECONE_API_KEY"))
_index = _pc.Index(_require_env("PINECONE_INDEX_NAME"))


def embed_text(text: str) -> list[float]:
    """Embed one piece of text with the shared embedding model."""

    response = _client.embeddings.create(model=EMBEDDING_MODEL, input=text)
    return response.data[0].embedding


def upsert_chunks(chunks: list[dict]) -> int:
    """Embed and upsert chunks. Each chunk needs 'id', 'text', and optional 'metadata'."""

    vectors = [
        {
            "id": chunk["id"],
            "values": embed_text(chunk["text"]),
            "metadata": {**chunk.get("metadata", {}), "text": chunk["text"]},
        }
        for chunk in chunks
    ]
    _index.upsert(vectors=vectors)
    return len(vectors)


def query_similar(text: str, top_k: int = 5) -> list[dict]:
    """Embed a query and return the top_k most similar stored chunks."""

    query_vector = embed_text(text)
    result = _index.query(vector=query_vector, top_k=top_k, include_metadata=True)
    matches = []
    for match in result.matches:
        metadata = match.metadata or {}
        matches.append(
            {
                "id": match.id,
                "score": match.score,
                "document_id": metadata.get("document_id"),
                "chunk_index": metadata.get("chunk_index"),
                "source": metadata.get("source"),
                "text": metadata.get("text", ""),
            }
        )
    return matches


def pinecone_health() -> dict:
    """Confirm Pinecone is reachable and report basic index stats."""

    stats = _index.describe_index_stats()
    return {
        "status": "ok",
        "index": os.environ["PINECONE_INDEX_NAME"],
        "dimension": stats.dimension,
        "total_vector_count": stats.total_vector_count,
    }
