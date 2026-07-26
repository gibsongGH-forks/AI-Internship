# Week 1 — `/ask` Demo (5 stages)

Build a typed LLM endpoint step by step. Each stage is a standalone FastAPI app you can run and compare.

## Live deployment

- **API:** https://ai-internship-jx6n.onrender.com (FastAPI, deployed on Render free tier — first request after idle time can take 10+ seconds to cold-start)
- **Streamlit UI:** https://ai-internship-s7lvc6untbnbke3f8ughtk.streamlit.app/ (deployed on Streamlit Community Cloud, points at the Render API by default)

## Model choice & cost

`main.py` defaults to `gpt-4o` for answer quality on grounded RAG questions, with `gpt-4o-mini` and `o3-mini` available as per-request overrides (`model` field) when lower cost matters more than quality. Cost is computed per call from the real `prompt_tokens`/`completion_tokens` in the OpenAI response against list price per model (`MODEL_PRICES_PER_1K` in `main.py`), so `cost_usd` in every `/ask` response reflects the actual model used, not an estimate.

## Setup

```bash
cp .env.example .env          # OPENAI_API_KEY=sk-...
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Demo stages

| Stage | File | What you learn |
|-------|------|----------------|
| 1 | `serve_stage1.py` | Bare `/ask` — string answer + `tokens_used` |
| 2 | `serve_stage2.py` | Structured output via Pydantic + `completions.parse` |
| 3 | `serve_stage3.py` | Validation guardrail + retry (`force_bad` demo knob) |
| 4 | `serve_stage4.py` | Per-request `model` override + `latency_ms` |
| 5 | `serve_stage5.py` / `main.py` | Full system + `cost_usd` readout |

Run one stage at a time (only one server on port 8000):

```bash
uvicorn serve_stage1:app --host 127.0.0.1 --port 8000 --reload
# or the full system:
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

## Streamlit demo runner

Interactive UI for all five stages:

```bash
streamlit run demo_page.py
```

Open http://localhost:8501. Set **API base URL** to `http://127.0.0.1:8000` and start the matching stage server in another terminal — or just use the [live public UI](https://ai-internship-s7lvc6untbnbke3f8ughtk.streamlit.app/), which defaults to the deployed Render API and needs no local setup.

## Guardrail proof (Stage 3)

Demo 3 in the Streamlit UI has a `force_bad` checkbox. When checked, `/ask` deliberately asks the model for a malformed `Answer` (a string instead of a float for `confidence`) on the first attempt. `call_model_unsafe` validates that raw response with `Answer.model_validate_json(...)`; the resulting `pydantic.ValidationError` is caught in `ask()`'s retry loop, which falls back to the schema-enforced `call_model_structured` path (OpenAI structured outputs) and returns a clean, valid response — the malformed first attempt never reaches the client. Without this guardrail, the invalid response (a `confidence` field that fails the `Answer` schema) would either be returned to callers as-is or crash the endpoint with an unhandled exception.

## Test with curl

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is RAG in one sentence?"}'
```

Stage 5 example (model + cost):

```bash
curl -s -X POST http://127.0.0.1:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is chunking?", "model": "gpt-4o-mini"}'
```

## Smoke-test all stages

Requires `.venv` and a valid `OPENAI_API_KEY`:

```bash
python test_all_stages.py
```

## Project layout

```
week-1/
├── main.py              # Full system (stages 1–5 combined)
├── serve_stage1.py … serve_stage5.py
├── demo_page.py         # Streamlit test UI
├── test_all_stages.py   # Automated stage smoke tests
├── requirements.txt
├── .env.example
└── .gitignore
```
