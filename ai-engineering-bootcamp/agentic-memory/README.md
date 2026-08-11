# Week 5: Anatomy of Agentic Memory

Hands-on demos for **AI Engineering Bootcamp** Session 5.

## Interactive lab (start here)

```bash
cd ai-engineering-bootcamp/agentic-memory/demo-ui
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). No API key needed.

| # | What you practice |
|---|-------------------|
| 1 | Context budget |
| 2 | Vector search vs graph lookup |
| 3 | Rules after chat compaction |
| 4 | Search vs synthesis |
| 5 | Self-editing memory |
| 6 | Crash mid-run and resume |
| 7 | Memory poisoning |

## Notebook (optional code path)

```bash
cd ai-engineering-bootcamp/agentic-memory
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # optional OPENAI_API_KEY for one LLM cell
jupyter notebook week5_agentic_memory_notebook.ipynb
```

## Slides

Session deck on the TAI platform: `/courses/ai-engineering-bootcamp/week-5-agentic-memory`

## Related reading

- [Open Knowledge Format (OKF) spec](https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md) - portable markdown + YAML knowledge wikis for agents. This lab's `sample_notes/` are a simplified cousin of that pattern, not an OKF bundle.
- [Introducing OKF (Google Cloud Blog)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)

## Repo layout

```
agentic-memory/
  demo-ui/                         # Next.js lab
  week5_agentic_memory_notebook.ipynb
  memory_helpers.py
  sample_notes/
  requirements.txt
  .env.example
```
