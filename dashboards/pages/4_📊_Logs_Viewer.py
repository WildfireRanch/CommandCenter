"""
Logs and Activity Viewer
View recent conversations, agent activity, and system events
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.api_client import api
from components.db_client import db

st.set_page_config(
    page_title="Logs Viewer | CommandCenter",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Logs & Activity Viewer")
st.caption("Recent conversations, agent activity, and system events")

# Controls
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    view_mode = st.selectbox(
        "View Mode",
        options=["Conversations", "Energy Logs", "System Activity"],
        index=0
    )
with col2:
    limit = st.number_input("Records to show", min_value=5, max_value=100, value=20)
with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

if view_mode == "Conversations":
    st.markdown("### 💬 Recent Conversations")

    with st.spinner("Loading conversations..."):
        conversations_df = db.get_recent_conversations(limit=limit)

    if not conversations_df.empty:
        # Display conversations table
        st.dataframe(
            conversations_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "session_id": st.column_config.TextColumn("Session ID", width="medium"),
                "created_at": st.column_config.DatetimeColumn("Created", width="medium"),
                "updated_at": st.column_config.DatetimeColumn("Last Activity", width="medium"),
                "message_count": st.column_config.NumberColumn("Messages", width="small"),
                "last_message_at": st.column_config.DatetimeColumn("Last Message", width="medium")
            }
        )

        # Conversation viewer
        st.markdown("---")
        st.markdown("### 🔍 View Conversation Details")

        selected_session = st.selectbox(
            "Select a conversation",
            options=conversations_df['session_id'].tolist(),
            format_func=lambda x: f"{x[:8]}... ({conversations_df[conversations_df['session_id']==x]['message_count'].values[0]} messages)"
        )

        if selected_session:
            with st.spinner("Loading conversation messages..."):
                messages = db.get_conversation_messages(selected_session)

            if messages:
                st.markdown(f"#### Conversation: `{selected_session}`")

                for msg in messages:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    timestamp = msg.get("created_at", "")

                    if role == "user":
                        with st.chat_message("user", avatar="🧑"):
                            st.markdown(content)
                            st.caption(f"🕐 {timestamp}")
                    else:
                        with st.chat_message("assistant", avatar="🤖"):
                            st.markdown(content)
                            st.caption(f"🕐 {timestamp}")

                # Export button
                if st.button("📥 Export This Conversation"):
                    export_text = f"# Conversation Export\n\n"
                    export_text += f"**Session ID:** {selected_session}\n\n"
                    export_text += "---\n\n"

                    for msg in messages:
                        role_emoji = "🧑" if msg["role"] == "user" else "🤖"
                        export_text += f"### {role_emoji} {msg['role'].title()}\n"
                        export_text += f"*{msg['created_at']}*\n\n"
                        export_text += f"{msg['content']}\n\n"
                        export_text += "---\n\n"

                    st.download_button(
                        label="💾 Download Markdown",
                        data=export_text,
                        file_name=f"conversation_{selected_session[:8]}.md",
                        mime="text/markdown"
                    )
            else:
                st.info("No messages in this conversation")
    else:
        st.info("No conversations found")

elif view_mode == "Energy Logs":
    st.markdown("### ⚡ Energy Data Logs")

    with st.spinner("Loading energy logs..."):
        energy_df = db.get_recent_energy_data(hours=24)

    if not energy_df.empty:
        st.dataframe(
            energy_df.head(limit),
            use_container_width=True,
            hide_index=True,
            column_config={
                "timestamp": st.column_config.DatetimeColumn("Timestamp", width="medium"),
                "battery_soc": st.column_config.NumberColumn("Battery SOC (%)", format="%.1f"),
                "battery_voltage": st.column_config.NumberColumn("Voltage (V)", format="%.1f"),
                "battery_power": st.column_config.NumberColumn("Battery (W)", format="%.0f"),
                "solar_power": st.column_config.NumberColumn("Solar (W)", format="%.0f"),
                "load_power": st.column_config.NumberColumn("Load (W)", format="%.0f"),
                "grid_power": st.column_config.NumberColumn("Grid (W)", format="%.0f")
            }
        )

        st.caption(f"Showing {min(limit, len(energy_df))} of {len(energy_df)} records from last 24 hours")

        # Download raw data
        if st.button("📥 Download CSV"):
            csv = energy_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Full Dataset",
                data=csv,
                file_name=f"energy_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    else:
        st.info("No energy data available")

elif view_mode == "System Activity":
    st.markdown("### 🔧 System Activity")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📊 Database Statistics")
        stats = db.get_system_stats()

        if stats:
            st.metric("Total Energy Snapshots", stats.get("total_energy_snapshots", 0))
            st.metric("Total Conversations", stats.get("total_conversations", 0))
            st.metric("Conversations Today", stats.get("conversations_today", 0))

            if stats.get("latest_energy"):
                st.markdown("**Latest Energy Snapshot:**")
                latest = stats["latest_energy"]
                st.text(f"Time: {latest.get('timestamp', 'N/A')}")
                st.text(f"SOC: {latest.get('battery_soc', 0):.1f}%")
                st.text(f"Solar: {latest.get('solar_power', 0):.0f}W")
        else:
            st.info("No statistics available")

    with col2:
        st.markdown("#### 🚀 API Activity")

        # Test API health
        health = api.health_check()
        if health and "status" in health:
            st.success(f"✅ API Status: {health['status']}")

            # Try to get recent conversations from API
            recent = api.get_recent_conversations(limit=5)
            if recent and "conversations" in recent:
                st.metric("Recent API Calls", len(recent["conversations"]))
            else:
                st.info("No recent API activity")
        else:
            st.error("❌ API Offline")

# Activity Summary
st.markdown("---")
st.markdown("### 📈 Activity Summary")

col1, col2, col3, col4 = st.columns(4)

stats = db.get_system_stats()

with col1:
    total_conv = stats.get("total_conversations", 0) if stats else 0
    st.metric("Total Conversations", total_conv)

with col2:
    today_conv = stats.get("conversations_today", 0) if stats else 0
    st.metric("Today's Conversations", today_conv)

with col3:
    total_snapshots = stats.get("total_energy_snapshots", 0) if stats else 0
    st.metric("Energy Snapshots", f"{total_snapshots:,}")

with col4:
    if stats and stats.get("latest_energy"):
        latest_time = stats["latest_energy"].get("timestamp", "N/A")
        st.metric("Latest Data", "Just now" if latest_time != "N/A" else "N/A")
    else:
        st.metric("Latest Data", "N/A")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
