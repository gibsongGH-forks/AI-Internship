# CLAUDE.md

Critical, durable rules for working in this repo. This file exists so these
rules survive context compaction -- they apply regardless of what's in chat
history at the time.

## Git workflow (non-negotiable)

- Never run `git add -A` or `git add .`. Stage only the specific files
  relevant to the current request.
- Never touch the user's personal untracked files if you happen to see them
  in `git status` (e.g. resume/eval PDFs, `.docx` files, stray log files in
  `ai-engineering-bootcamp-v2/week-1/`). Leave them untracked, always.
- Never `git commit` or `git push` without the user explicitly asking for it
  in that turn. Confirming a plan is not the same as confirming a push.
- Verify `git status --porcelain` before and after staging to confirm only
  the intended files are included.
- Prefer a new commit over amending. Don't force-push.

## Secrets

- Never print, log, or paste an actual secret value from a `.env` file --
  when checking whether one is set, list variable *names* only
  (`grep -o '^[A-Z_]*=' .env`).
- Never hardcode an API key in source. All secrets are read via
  `os.getenv()` / `python-dotenv`, one `.env` per project folder, always
  gitignored.

## Capstone project map

This is one ongoing capstone spanning several folders, built up session by
session in an AI Engineering Bootcamp:

- **`ai-engineering-bootcamp-v2/week-1/`** -- FastAPI + Pinecone RAG API
  (Sessions 1-2). Deployed on Render at
  `https://ai-internship-jx6n.onrender.com`. Free tier cold-starts after
  ~15 min idle (first hit after idle: 10-60s+; then fast). Auto-deploys on
  push to `main`.
- **`ai-engineering-bootcamp/adk-multi-agent-systems/`** -- Google ADK
  agents (Sessions 3-5) that call the deployed API above as a real tool.
  `demo1`-`demo3` are routing/MCP/A2A exercises. `demo4_faq_capstone.py` is
  the single-agent FAQ capstone (`search_docs` tool + prompt-injection
  defense). `demo5_agentic_memory.py` extends it with durable cross-session
  memory (see below). Each `demoN_streamlit_app.py` is a minimal UI for
  that demo; run with `streamlit run demoN_streamlit_app.py`.
- **`ai-engineering-bootcamp/agentic-memory/`** -- course reference
  material for Session 5 (notebook, `memory_helpers.py`, a Next.js concept
  lab). Not part of the deployed capstone; the actual Session 5 submission
  lives in `adk-multi-agent-systems/demo5_agentic_memory.py` and
  `ai-engineering-bootcamp-v2/week-1/memory_store.py`, adapted from this
  reference.

## Durable memory system (Session 5)

- Store: `ai-engineering-bootcamp-v2/week-1/memory_store.py`, one JSON file
  (`memory_store.json`, gitignored -- runtime data, not source) on the
  deployed API process. Exposed via `POST/GET /memory` and
  `GET /memory/{key}` in `main.py`.
- Write gate: only `memory_store.ALLOWED_KEYS` (`preferred_name`,
  `preferred_language`, `last_topic`) can ever be persisted -- enforced
  server-side (400 on any other key) AND in the agent's instruction in
  `demo5_agentic_memory.py`. Keep both lists in sync if this ever changes.
- To test the memory API against localhost instead of the live Render URL,
  set `CAPSTONE_API_BASE_URL=http://127.0.0.1:<port>` before running an ADK
  demo or its Streamlit app.

## Process hygiene

- After backgrounding a local server (`uvicorn`, `streamlit run`) for a
  smoke test, kill it and delete any test artifacts (log files, test-only
  `memory_store.json` writes) before finishing -- don't leave orphaned
  processes or stray files behind.
