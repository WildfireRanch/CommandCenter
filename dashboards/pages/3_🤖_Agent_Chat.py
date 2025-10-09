"""
Agent Chat Interface
Talk to your Solar Controller agent
Based on Next.js AskAgent component
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.api_client import api

st.set_page_config(
    page_title="Agent Chat | CommandCenter",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []
if "agent_name" not in st.session_state:
    st.session_state.agent_name = "Solar Controller"

st.title("🤖 Solar Controller Agent")
st.caption(f"Session ID: `{st.session_state.session_id}`")

# Sidebar - Agent info
with st.sidebar:
    st.markdown("### 🤖 Agent Information")

    if Path("assets/Echo.png").exists():
        st.image("assets/Echo.png", width=100)

    st.markdown(f"**Name:** {st.session_state.agent_name}")
    st.markdown("**Role:** Solar Energy Management")
    st.markdown("**Status:** 🟢 Online")

    st.markdown("---")

    st.markdown("### 💬 Conversation")
    st.metric("Messages", len(st.session_state.messages))

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = str(uuid.uuid4())
        st.rerun()

    st.markdown("---")

    st.markdown("### 💡 Example Questions")

    st.markdown("**☀️ Status Queries** (Solar Controller)")
    st.markdown("""
    - What's my current battery level?
    - How much solar are we generating?
    - What's the power usage right now?
    """)

    st.markdown("**⚡ Planning Queries** (Energy Orchestrator)")
    st.markdown("""
    - Should we run the miners?
    - When's the best time to charge?
    - Create an energy plan for today
    """)

    st.markdown("**📚 Knowledge Base**")
    st.markdown("""
    - What is the minimum SOC threshold?
    - What are the solar specifications?
    """)

st.markdown("---")

# Chat display area
chat_container = st.container()

with chat_container:
    if not st.session_state.messages:
        st.info("""
        👋 **Welcome!** I'm your Solar Controller agent.

        I can help you with:
        - 🔋 Battery status and state of charge
        - ☀️ Solar production monitoring
        - ⚡ Power consumption analysis
        - 💡 Energy optimization recommendations

        Ask me anything about your solar energy system!
        """)
    else:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]

            if role == "user":
                with st.chat_message("user", avatar="🧑"):
                    st.markdown(content)
            else:
                with st.chat_message("assistant", avatar="🤖"):
                    st.markdown(content)

# Chat input
user_input = st.chat_input("Ask about your solar system...")

if user_input:
    # Add user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now().isoformat()
    })

    # Display user message
    with chat_container:
        with st.chat_message("user", avatar="🧑"):
            st.markdown(user_input)

    # Get agent response
    with chat_container:
        with st.chat_message("assistant", avatar="🤖"):
            # Enhanced loading state
            loading_messages = [
                "Analyzing your query...",
                "Routing to specialist agent...",
                "Processing request..."
            ]
            import random
            with st.spinner(random.choice(loading_messages)):
                response = api.ask_agent(
                    message=user_input,
                    session_id=st.session_state.session_id
                )

            if response and "response" in response:
                agent_reply = response["response"]
                st.markdown(agent_reply)

                # Enhanced agent metadata display with icons
                if "agent_role" in response:
                    agent_icons = {
                        "Solar Controller": "☀️",
                        "Energy Systems Monitor": "☀️",
                        "Energy Orchestrator": "⚡",
                        "Energy Operations Manager": "⚡",
                        "Manager": "🎯",
                        "Query Router and Coordinator": "🎯"
                    }
                    agent_role = response["agent_role"]
                    icon = agent_icons.get(agent_role, "🤖")
                    st.caption(f"{icon} **Answered by:** {agent_role}")

                # Show duration if available
                if "duration_ms" in response:
                    duration_s = response["duration_ms"] / 1000
                    st.caption(f"⏱️ Response time: {duration_s:.2f}s")

                # Show source citations if KB was used
                if any(keyword in agent_reply.lower() for keyword in ["source:", "sources consulted:", "citation"]):
                    with st.expander("📚 Knowledge Base Sources", expanded=False):
                        st.info("This response includes information from the knowledge base.")

                # Add to message history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": agent_reply,
                    "timestamp": datetime.now().isoformat()
                })

            elif "error" in response:
                error_msg = response.get("error", "Unknown error")
                detail = response.get("detail", "")

                st.error(f"❌ Error: {error_msg}")

                if detail:
                    with st.expander("Error Details"):
                        st.code(detail)

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": f"❌ Error: {error_msg}",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                st.error("Unexpected response format")
                st.json(response)

    st.rerun()

st.markdown("---")

# Conversation tools
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("📥 Load Conversation", use_container_width=True):
        with st.spinner("Loading conversation history..."):
            conv = api.get_conversation(st.session_state.session_id)
            if conv and "messages" in conv:
                st.session_state.messages = conv["messages"]
                st.success(f"Loaded {len(conv['messages'])} messages")
                st.rerun()
            else:
                st.warning("No conversation history found")

with col2:
    if st.button("📋 Export Chat", use_container_width=True):
        if st.session_state.messages:
            # Create markdown export
            export_text = f"# Solar Controller Conversation\n\n"
            export_text += f"**Session ID:** {st.session_state.session_id}\n\n"
            export_text += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            export_text += "---\n\n"

            for msg in st.session_state.messages:
                role_emoji = "🧑" if msg["role"] == "user" else "🤖"
                export_text += f"### {role_emoji} {msg['role'].title()}\n\n"
                export_text += f"{msg['content']}\n\n"
                export_text += "---\n\n"

            st.download_button(
                label="💾 Download Markdown",
                data=export_text,
                file_name=f"conversation_{st.session_state.session_id[:8]}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("No messages to export")

with col3:
    if st.button("🔄 New Session", use_container_width=True):
        old_session = st.session_state.session_id
        st.session_state.session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.success(f"Started new session")
        st.rerun()

# Footer
st.caption(f"Connected to: {api.base_url}")
