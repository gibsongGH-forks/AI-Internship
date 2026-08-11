# ADK Multi-Agent Systems

Progressive demos showing multi-agent system design using [Google's Agent Development Kit (ADK)](https://google.github.io/adk-docs/).

| Demo | What it shows | Protocol |
|------|--------------|----------|
| **Demo 1** — Routing | Router agent delegates to billing, technical, and escalation specialists | Local tools |
| **Demo 2** — MCP | Agent queries a live Supabase database; tools are auto-discovered at runtime | MCP |
| **Demo 3** — Full System | Combines routing + MCP + A2A with a remote shipping agent | MCP + A2A |
| **Demo 4** — Capstone FAQ | Single agent, one real tool (`search_docs` against the deployed RAG API), bounded step limit, prompt-injection defense | Local tool over HTTP |
| **Demo 5** — Agentic Memory | Extends Demo 4 with a durable, gated, cross-session memory store | Local tool over HTTP |
| **Streamlit Apps** | `streamlit_app.py` covers Demos 1-3; `demo4_streamlit_app.py` and `demo5_streamlit_app.py` are dedicated UIs for their demos | All |

## Prerequisites

- **Python 3.12+** (required — earlier versions have asyncio incompatibilities with MCP)
- **Node.js / npm** (needed by the Supabase MCP server, launched via `npx`)
- A **Google API key** for Gemini models → [Get one here](https://aistudio.google.com/apikey)
- A **Supabase project** with a Personal Access Token → [Generate here](https://supabase.com/dashboard/account/tokens) *(Demos 2 & 3 only)*

## Setup

### 1. Create and activate a virtual environment

**With [uv](https://docs.astral.sh/uv/) (recommended):**

```bash
uv venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
uv pip install -e .
```

**With plain pip:**

```bash
python3 -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
pip install -e .
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```
GOOGLE_API_KEY=your_google_api_key_here
SUPABASE_ACCESS_TOKEN=your_personal_access_token_here
SUPABASE_PROJECT_REF=your_project_ref_here
```

## Running the demos

### Demo 1 — Multi-Agent Routing (local tools only)

```bash
python demo1_routing.py
```

### Demo 2 — MCP + Supabase

Requires `SUPABASE_ACCESS_TOKEN` and `SUPABASE_PROJECT_REF` in `.env`.

```bash
python demo2_mcp.py
```

### Demo 3 — Full System (Routing + MCP + A2A)

Start the shipping agent in one terminal, then run the demo in another:

```bash
# Terminal 1 — start the A2A shipping agent
uvicorn shipping_agent:app --port 8001

# Terminal 2 — run the demo
python demo3_full_system.py
```

### Streamlit App (interactive UI for Demos 1-3)

```bash
# Terminal 1 — start the A2A shipping agent (needed for Demo 3)
uvicorn shipping_agent:app --port 8001

# Terminal 2 — launch the Streamlit app
streamlit run streamlit_app.py
```

### Demo 4 — Capstone FAQ Agent (single agent, real tool)

Calls the deployed capstone RAG API (`ai-engineering-bootcamp-v2/week-1/`) over HTTP — no local setup needed beyond `GOOGLE_API_KEY`.

```bash
python demo4_faq_capstone.py
# or the UI:
streamlit run demo4_streamlit_app.py
```

### Demo 5 — Agentic Memory (durable, cross-session recall)

Extends Demo 4 with `remember_fact` / `recall_facts` tools backed by the durable memory store added to the same capstone API (`/memory` endpoints). See [Memory (Session 5)](#memory-session-5) below for what's stored and why.

```bash
python demo5_agentic_memory.py
# or the UI (two sections: state a preference, then a fresh session that recalls it):
streamlit run demo5_streamlit_app.py
```

To test against a local API instead of the deployed one, set
`CAPSTONE_API_BASE_URL=http://127.0.0.1:8000` before running either command.

## Architecture

```
User Query
    │
    ▼
┌───────────────────────┐
│     Router Agent       │
├───────┬───────┬───────┤
│       │       │       │
▼       ▼       ▼       │
Billing  Tech  Shipping │
│       │       │       │
▼       ▼       ▼       │
MCP    Local    A2A     │
Server  Tools  Protocol │
│               │       │
▼               ▼       │
Supabase     Remote     │
  DB         Agent      │
└───────────────────────┘
```

## Memory (Session 5)

**What do I keep?** Three facts, and only these: `preferred_name`, `preferred_language`, and `last_topic` — a small, high-signal set analogous to a support bot remembering a user's language and open ticket ID, not an attempt to remember everything. Retrieved document chunks, tool dumps, and one-off task details are never written to durable memory; they stay in the ADK session's ephemeral event history and are gone once that session ends. **When do I write it?** Only when the model decides the user has stated one of those three facts as a stable preference (e.g. "call me Alex", "answer in Spanish"), via the gated `remember_fact` tool — never automatically, never for arbitrary keys. **Where does it live?** A single JSON file (`memory_store.py` / `memory_store.json`) on the same deployed capstone API process as the RAG endpoints (`ai-engineering-bootcamp-v2/week-1/`, on Render), exposed over `POST/GET /memory`. It's on local disk, not a hosted database — the simplest option that satisfies "survive a process restart," which is genuinely true (verified by killing the API process and reading the fact back from a freshly started one) but not true across a full container rebuild if the host's disk isn't persistent; that's a known, accepted limitation for a bootcamp capstone rather than production infra. **How do I get it back?** `recall_facts()` calls `GET /memory` at the start of a session and folds the result into that turn's context — this is what proves *cross-session* recall rather than just long chat history, since each demo session/process starts with zero prior conversation. **When do I forget?** Never automatically today — there's no TTL or explicit forget tool yet; a value only changes by being explicitly replaced (`remember_fact` again with the same key). The write gate (fixed allow-list of 3 keys) is what keeps this from growing unbounded, not expiry.

