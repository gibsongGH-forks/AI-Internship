"""
Demo 4 Streamlit UI -- Capstone FAQ Agent

A minimal UI around demo4_faq_capstone.py's root_agent: enter a question,
run the agent, and see the raw Think / Act / Observe / Respond event trace
plus the final answer. No API keys are hardcoded -- GOOGLE_API_KEY (and the
optional CAPSTONE_API_BASE_URL / CAPSTONE_API_TIMEOUT overrides) are read
from the environment via python-dotenv, same as demo4_faq_capstone.py.

Run:
    streamlit run demo4_streamlit_app.py
"""

import asyncio
import concurrent.futures
import os
import sys

import streamlit as st
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv()

from google.adk.agents import RunConfig
from google.adk.agents.invocation_context import LlmCallsLimitExceededError
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from demo4_faq_capstone import root_agent, MAX_LLM_CALLS, CAPSTONE_API_BASE_URL

# --- Page setup ---

st.set_page_config(page_title="Capstone FAQ Agent", layout="centered")
st.title("Capstone FAQ Agent")
st.caption("Google ADK single agent + one real tool: search_docs -> live RAG API")

# GOOGLE_API_KEY is read from the environment (.env locally, host secrets in
# deployment) -- never hardcoded here or anywhere in this file.
api_key = os.getenv("GOOGLE_API_KEY")

with st.sidebar:
    st.markdown("### Status")
    if api_key:
        st.success("Google API Key")
    else:
        st.error("Google API Key -- not set in .env")
    st.caption(f"RAG API: {CAPSTONE_API_BASE_URL}")
    st.caption(f"Step limit: max_llm_calls={MAX_LLM_CALLS}")

if not api_key:
    st.error("Set GOOGLE_API_KEY in .env before running.")
    st.stop()

# --- Agent runner ---

def run_agent_sync(message: str, timeout: int = 120):
    """Run the ADK agent synchronously, collecting a Think/Act/Observe trace."""

    async def _run():
        service = InMemorySessionService()
        runner = Runner(agent=root_agent, app_name="capstone_faq_ui", session_service=service)
        session = await service.create_session(app_name="capstone_faq_ui", user_id="user1")
        content = types.Content(role="user", parts=[types.Part(text=message)])
        run_config = RunConfig(max_llm_calls=MAX_LLM_CALLS)

        trace, final = [], "(no response)"
        try:
            async for event in runner.run_async(
                user_id="user1", session_id=session.id, new_message=content, run_config=run_config
            ):
                for call in event.get_function_calls():
                    trace.append({"step": "ACT", "detail": f"call {call.name}({dict(call.args or {})})"})
                for resp in event.get_function_responses():
                    trace.append({"step": "OBSERVE", "detail": f"{resp.name} -> {resp.response}"})
                if event.content and event.content.parts:
                    text = "".join(p.text for p in event.content.parts if p.text)
                    if text:
                        if event.is_final_response():
                            trace.append({"step": "RESPOND", "detail": text})
                            final = text
                        else:
                            trace.append({"step": "THINK", "detail": text})
        except LlmCallsLimitExceededError:
            final = f"(stopped: hit the max_llm_calls={MAX_LLM_CALLS} step limit)"
            trace.append({"step": "STOP", "detail": final})
        return final, trace

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(asyncio.run, _run()).result(timeout=timeout)


STEP_RENDER = {
    "ACT": st.warning,
    "OBSERVE": st.success,
    "THINK": st.info,
    "RESPOND": st.info,
    "STOP": st.error,
}

# --- Input ---

question = st.text_input(
    "Ask a question about the indexed docs:",
    placeholder="e.g. What does the culture memo say about the Dream Team?",
)
run_clicked = st.button("Ask", type="primary")

if run_clicked and question.strip():
    with st.spinner("Running agent (may take 10-60s on a cold API start)..."):
        try:
            final_answer, trace = run_agent_sync(question.strip())
            st.session_state["trace"] = trace
            st.session_state["final"] = final_answer
            st.session_state["question"] = question.strip()
        except Exception as exc:
            st.error(f"Agent run failed: {exc}")

# --- Output ---

if st.session_state.get("final"):
    st.markdown("---")
    st.markdown(f"**Question:** {st.session_state['question']}")
    st.subheader("Final Answer")
    st.markdown(st.session_state["final"])

    with st.expander("Think -> Act -> Observe trace", expanded=True):
        for i, step in enumerate(st.session_state.get("trace", []), start=1):
            render = STEP_RENDER.get(step["step"], st.write)
            render(f"**{i}. {step['step']}** -- {step['detail'][:600]}")
