"""Minimal Streamlit UI for the live /ingest and /ask RAG API.

The API is the source of truth: this page only sends requests and renders
whatever comes back — no chunking, embedding, or retrieval logic lives here.

Run:
  streamlit run rag_ui.py
"""

import os

import httpx
import streamlit as st

DEFAULT_BASE_URL = os.getenv("API_BASE_URL", "https://ai-internship-jx6n.onrender.com")


def call_ingest(base_url: str, document_id: str, text: str, source: str) -> tuple[int, dict | str]:
    payload = {"document_id": document_id, "text": text}
    if source.strip():
        payload["metadata"] = {"source": source.strip()}
    return _post(base_url, "/ingest", payload)


def call_ask(base_url: str, question: str) -> tuple[int, dict | str]:
    return _post(base_url, "/ask", {"question": question})


def _post(base_url: str, path: str, payload: dict) -> tuple[int, dict | str]:
    try:
        response = httpx.post(f"{base_url.rstrip('/')}{path}", json=payload, timeout=60.0)
        try:
            return response.status_code, response.json()
        except ValueError:
            return response.status_code, response.text
    except httpx.HTTPError as exc:
        return 0, {"error": str(exc)}


def document_ids_from_chunk_ids(chunk_ids: list[str]) -> list[str]:
    """Chunk ids are '{document_id}-{index}' — strip the trailing index."""
    seen: list[str] = []
    for chunk_id in chunk_ids:
        doc_id = chunk_id.rsplit("-", 1)[0]
        if doc_id not in seen:
            seen.append(doc_id)
    return seen


st.set_page_config(page_title="RAG demo", layout="wide")
st.title("RAG demo — `/ingest` + `/ask`")
st.caption("Talks to the live FastAPI service. This page has no RAG logic of its own.")

base_url = st.sidebar.text_input("API base URL", DEFAULT_BASE_URL)

ingest_tab, ask_tab = st.tabs(["Ingest a document", "Ask a question"])

with ingest_tab:
    document_id = st.text_input("document_id", placeholder="e.g. doc2_handbook")
    source = st.text_input("source (optional)", placeholder="e.g. doc2_handbook.txt")
    text = st.text_area("Document text", height=200, placeholder="Paste the document text here…")

    if st.button("Ingest", type="primary"):
        if not document_id.strip() or not text.strip():
            st.warning("document_id and text are both required.")
        else:
            with st.spinner("Calling /ingest..."):
                status, data = call_ingest(base_url, document_id.strip(), text, source)
            if status == 200 and isinstance(data, dict):
                st.success(f"Indexed {data.get('chunks_indexed')} chunk(s) under document_id '{data.get('document_id')}'.")
            else:
                st.error(f"HTTP {status}")
            st.json(data)

with ask_tab:
    question = st.text_input("Question", placeholder="Ask something covered by an ingested document…")

    if st.button("Ask", type="primary"):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            with st.spinner("Calling /ask..."):
                status, data = call_ask(base_url, question)

            if status != 200 or not isinstance(data, dict):
                st.error(f"HTTP {status}")
                st.json(data)
            else:
                answer = data.get("answer", {})
                answer_text = answer.get("answer", "")
                chunk_ids = data.get("retrieved_chunk_ids", [])
                doc_ids = document_ids_from_chunk_ids(chunk_ids)
                cited = [d for d in doc_ids if f"[{d}]" in answer_text]

                st.subheader("Answer")
                st.write(answer_text)

                col1, col2, col3 = st.columns(3)
                col1.metric("Confidence", f"{answer.get('confidence', 0):.2f}")
                col2.metric("Tokens used", data.get("tokens_used"))
                col3.metric("Cost (USD)", f"${data.get('cost_usd', 0):.6f}")

                if cited:
                    st.success(f"Cited source(s): {', '.join(f'`{d}`' for d in cited)}")
                else:
                    st.warning(
                        "No `[document_id]` citation found in the answer — likely a refusal "
                        "or an ungrounded response. Check the retrieved chunks below."
                    )

                st.markdown("**Retrieved chunk IDs** (top-k passed to the model):")
                st.code("\n".join(chunk_ids) or "(none)")

                with st.expander("Full JSON response"):
                    st.json(data)
