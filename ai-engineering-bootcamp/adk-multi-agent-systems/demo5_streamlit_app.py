"""Demo 5 Streamlit UI -- Cross-Session Memory for the Capstone FAQ Agent

Proves durable, cross-session recall visually: ask something that states a
preference (Session A), then ask an unrelated question that depends on that
preference (Session B). Each "Ask" click builds a brand-new
InMemorySessionService -- so nothing carries over in the agent's own chat
history between the two turns. If Session B still knows the answer, it can
only be because it read it back from the durable /memory store on the
deployed capstone API, not because it remembers the conversation.

No API keys are hardcoded -- GOOGLE_API_KEY, CAPSTONE_API_BASE_URL, etc. are
all read from the environment via python-dotenv, same as every other file
in this folder.

Run:
    streamlit run demo5_streamlit_app.py
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

from demo4_faq_capstone import CAPSTONE_API_BASE_URL, MAX_LLM_CALLS
from demo5_agentic_memory import memory_agent, recall_facts

# --- Page setup ---

st.set_page_config(page_title="Capstone Memory Demo", layout="centered")
st.title("Capstone FAQ Agent -- Cross-Session Memory")
st.caption(
    "Each 'Ask' click starts a brand-new agent session (fresh InMemorySessionService). "
    "Any recall you see did NOT come from chat history -- it came from the durable "
    "/memory store on the deployed capstone API."
)

api_key = os.getenv("GOOGLE_API_KEY")

with st.sidebar:
    st.markdown("### Status")
    if api_key:
        st.success("Google API Key")
    else:
        st.error("Google API Key -- not set in .env")
    st.caption(f"Capstone API: {CAPSTONE_API_BASE_URL}")
    st.caption(f"Step limit: max_llm_calls={MAX_LLM_CALLS}")

    st.markdown("### Durable memory store (live)")
    st.caption("Read directly from GET /memory -- not through the agent.")
    if st.button("Refresh"):
        st.rerun()
    try:
        facts = recall_facts()
        if facts.get("error"):
            st.error(facts["error"])
        elif facts:
            for key, value in facts.items():
                st.write(f"**{key}**: {value}")
        else:
            st.info("Nothing stored yet.")
    except Exception as exc:
        st.error(f"Could not read memory: {exc}")

if not api_key:
    st.error("Set GOOGLE_API_KEY in .env before running.")
    st.stop()

# --- Agent runner ---

def run_agent_sync(message: str, timeout: int = 120):
    """Run the memory-enabled agent in a brand-new session, synchronously."""

    async def _run():
        service = InMemorySessionService()
        runner = Runner(agent=memory_agent, app_name="capstone_memory_ui", session_service=service)
        session = await service.create_session(app_name="capstone_memory_ui", user_id="user1")
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


def render_turn(label: str, final_answer: str, trace: list):
    st.markdown(f"**{label}**")
    st.markdown(final_answer)
    with st.expander("Think -> Act -> Observe trace"):
        for i, step in enumerate(trace, start=1):
            render = STEP_RENDER.get(step["step"], st.write)
            render(f"**{i}. {step['step']}** -- {step['detail'][:600]}")


# --- Session A ---

st.markdown("---")
st.subheader("Session A -- state a preference")
q1 = st.text_input(
    "Ask something that also states a stable fact about you:",
    value="Please call me Greg from now on, and answer in English. "
    "What does the culture memo say about the Dream Team?",
    key="q1",
)
if st.button("Ask (Session A)", type="primary"):
    with st.spinner("Running agent (new session)..."):
        try:
            final, trace = run_agent_sync(q1.strip())
            st.session_state["a_final"], st.session_state["a_trace"] = final, trace
        except Exception as exc:
            st.error(f"Agent run failed: {exc}")

if st.session_state.get("a_final"):
    render_turn("Question:  " + st.session_state.get("q1", ""), st.session_state["a_final"], st.session_state["a_trace"])

# --- Session B ---

st.markdown("---")
st.subheader("Session B -- fresh session, nothing re-stated")
q2 = st.text_input(
    "Ask a follow-up that depends on the fact above, with no chat history to lean on:",
    value="What's my name, and what language should you answer in?",
    key="q2",
)
if st.button("Ask (Session B)", type="primary"):
    with st.spinner("Running agent (new session)..."):
        try:
            final, trace = run_agent_sync(q2.strip())
            st.session_state["b_final"], st.session_state["b_trace"] = final, trace
        except Exception as exc:
            st.error(f"Agent run failed: {exc}")

if st.session_state.get("b_final"):
    render_turn("Question:  " + st.session_state.get("q2", ""), st.session_state["b_final"], st.session_state["b_trace"])
