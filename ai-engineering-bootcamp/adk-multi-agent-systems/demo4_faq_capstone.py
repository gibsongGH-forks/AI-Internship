"""
Demo 4: Capstone FAQ Agent (single agent, one real tool)

Patterns copied from:
  - demo1_routing.py  -> tool function shape, Agent(...) fields, ask()/main() runner harness
  - demo2_mcp.py      -> single-agent-no-router shape (one Agent, no sub_agents/root router)
New in this file (not in demo1/2/3):
  - RunConfig(max_llm_calls=...) as a hard step-limit so the agent can't loop forever
  - Per-event Think / Act / Observe logging over the raw ADK event stream
  - search_docs is a real tool: it calls GET /debug/retrieve on the live Session 1/2
    capstone RAG API (FastAPI + Pinecone) over HTTP and returns real chunks

Run: python demo4_faq_capstone.py
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
import httpx
from google.adk.agents import Agent, RunConfig
from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

MODEL = "gemini-flash-lite-latest"

# Hard cap on LLM calls for one invocation. A single tool-call round trip is
# normally ~2 calls (decide to call the tool, then synthesize the answer);
# this leaves headroom without allowing an unbounded loop.
MAX_LLM_CALLS = 4

# The capstone RAG API's GET /debug/retrieve endpoint (see week-1/main.py).
# Render free tier cold-starts, so the timeout is generous on purpose.
CAPSTONE_API_BASE_URL = os.getenv("CAPSTONE_API_BASE_URL", "https://ai-internship-jx6n.onrender.com")
CAPSTONE_API_TIMEOUT = float(os.getenv("CAPSTONE_API_TIMEOUT", "60"))

# --- Tools ---

def search_docs(query: str) -> dict:
    """Search the capstone knowledge base for text relevant to the query.

    Calls GET /debug/retrieve on the live capstone RAG API (FastAPI + Pinecone,
    embedding model text-embedding-3-small) and returns the top matching chunks,
    each with a document_id, similarity score, and the chunk text. No LLM call
    happens inside the tool -- retrieval only. Call this before answering any
    factual question; if it returns no results, or an error, say so plainly
    instead of guessing.
    """
    try:
        response = httpx.get(
            f"{CAPSTONE_API_BASE_URL}/debug/retrieve",
            params={"q": query},
            timeout=CAPSTONE_API_TIMEOUT,
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        return {
            "error": f"capstone API returned HTTP {exc.response.status_code}",
            "detail": exc.response.text[:500],
            "query": query,
        }
    except httpx.HTTPError as exc:
        return {"error": f"could not reach capstone API: {exc}", "query": query}

    data = response.json()
    results = data.get("results", [])
    return {
        "query": query,
        "result_count": len(results),
        "results": [
            {
                "document_id": r.get("document_id"),
                "score": r.get("score"),
                "text": r.get("text"),
            }
            for r in results
        ],
    }

# --- Agent ---

root_agent = Agent(
    name="capstone_faq_agent",
    model=MODEL,
    instruction=(
        "You are the FAQ agent for a personal capstone project about a small set of "
        "reference documents.\n"
        "\n"
        "Goal: answer the user's question using ONLY facts returned by the search_docs tool.\n"
        "\n"
        "Constraints:\n"
        "- Always call search_docs at least once before answering a factual question.\n"
        "- Never answer from your own general knowledge -- only from what search_docs returns.\n"
        "- If search_docs has no relevant result, say plainly that the documents don't cover "
        "it instead of guessing.\n"
        "- Cite the source document for every claim, if the tool result provides one.\n"
        "\n"
        "Done: you have called search_docs at least once, and you return exactly one final "
        "answer that either cites its source or clearly states the answer isn't in the "
        "available documents."
    ),
    tools=[search_docs],
)

# --- Runner (with step-limit + Think/Act/Observe logging) ---

async def ask(agent, message, max_llm_calls: int = MAX_LLM_CALLS) -> str:
    service = InMemorySessionService()
    runner = Runner(agent=agent, app_name="capstone_faq", session_service=service)
    session = await service.create_session(app_name="capstone_faq", user_id="user1")
    content = types.Content(role="user", parts=[types.Part(text=message)])
    run_config = RunConfig(max_llm_calls=max_llm_calls)

    final_text = "(no response)"
    try:
        async for event in runner.run_async(
            user_id="user1",
            session_id=session.id,
            new_message=content,
            run_config=run_config,
        ):
            for call in event.get_function_calls():
                print(f"  ACT     [{event.author}] call {call.name}({dict(call.args or {})})")

            for resp in event.get_function_responses():
                print(f"  OBSERVE [{event.author}] {resp.name} -> {resp.response}")

            if event.content and event.content.parts:
                text = "".join(p.text for p in event.content.parts if p.text)
                if text:
                    label = "RESPOND" if event.is_final_response() else "THINK  "
                    print(f"  {label} [{event.author}] {text}")

            if event.is_final_response() and event.content and event.content.parts:
                final_text = event.content.parts[0].text
    except LlmCallsLimitExceededError:
        final_text = f"(stopped: hit the max_llm_calls={max_llm_calls} step limit)"

    return final_text

async def main():
    tests = [
        ("FAQ", "What does the culture memo say about the Dream Team?"),
    ]
    for label, query in tests:
        print(f"\n--- {label} ---")
        print(f"User: {query}\n")
        answer = await ask(root_agent, query)
        print(f"\nFinal answer: {answer}\n")

if __name__ == "__main__":
    asyncio.run(main())
