"""Streamlit chat UI for mcp-agent-router.

Run with:
    streamlit run app.py
"""

import streamlit as st
from dotenv import load_dotenv

from mcp_agent_router.agent import Agent
from mcp_agent_router.audit import recent_tool_calls

load_dotenv()

st.set_page_config(page_title="mcp-agent-router", page_icon="\U0001F916", layout="centered")

if "agent" not in st.session_state:
    st.session_state.agent = Agent()
if "history" not in st.session_state:
    st.session_state.history = []

agent = st.session_state.agent

st.title("\U0001F916 mcp-agent-router")
st.caption(
    "A support assistant for a mock insurance company. Each message is routed to one "
    "of 3 tools (policy lookup, scheduling, FAQ search) via Claude's tool calling - "
    "see README.md for the architecture."
)

with st.sidebar:
    st.subheader("Available tools")
    for tool in agent.registry.anthropic_tools():
        st.write(f"**{tool['name']}**")
        st.caption(tool["description"])

    st.divider()
    st.subheader("Recent tool calls")
    logs = recent_tool_calls(limit=5)
    if not logs:
        st.caption("None yet - ask something to see audit entries here.")
    for log in logs:
        status = "ok" if log["success"] else "error"
        st.caption(f"`{log['tool_name']}` - {status} - {log['latency_ms']:.0f} ms")

def routed_tools(agent: Agent, since_idx: int) -> list[str]:
    names = []
    for message in agent.messages[since_idx:]:
        if message["role"] != "assistant":
            continue
        for block in message["content"]:
            if getattr(block, "type", None) == "tool_use":
                names.append(block.name)
    return names


for role, text, tools in st.session_state.history:
    with st.chat_message(role):
        if tools:
            st.caption("\U0001F527 Routed to: " + ", ".join(f"`{t}`" for t in tools))
        st.markdown(text)

if prompt := st.chat_input("Ask about a policy, book a call, or ask a general question..."):
    st.session_state.history.append(("user", prompt, []))
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        start_idx = len(agent.messages)
        with st.spinner("Thinking..."):
            reply = agent.send(prompt)
        tools = routed_tools(agent, start_idx)
        if tools:
            st.caption("\U0001F527 Routed to: " + ", ".join(f"`{t}`" for t in tools))
        else:
            st.caption("\U0001F4AC Answered directly - no tool call")
        st.markdown(reply)
    st.session_state.history.append(("assistant", reply, tools))
