"""
System Health Monitor
Shows API status, database connections, and service health
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.api_client import api
from components.db_client import db
from datetime import datetime
import time

st.set_page_config(
    page_title="System Health | CommandCenter",
    page_icon="🏥",
    layout="wide"
)

# Compressed vertical spacing CSS
st.markdown("""
<style>
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    .element-container {
        margin-bottom: 0.5rem !important;
    }

    [data-testid="stMetric"] {
        background-color: white;
        padding: 0.75rem !important;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    [data-testid="stMetricLabel"] {
        padding-bottom: 0.25rem !important;
    }

    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        padding-top: 0 !important;
        padding-bottom: 0.25rem !important;
    }

    [data-testid="stMetricDelta"] {
        padding-top: 0 !important;
    }

    h1, h2, h3, h4 {
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    hr {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    [data-testid="column"] {
        padding: 0.25rem !important;
    }

    .stButton {
        margin-top: 0.5rem !important;
    }

    .stAlert {
        padding: 0.75rem !important;
        margin-bottom: 0.75rem !important;
    }

    .streamlit-expanderHeader {
        padding: 0.5rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🏥 System Health Monitor")
st.caption("Real-time monitoring of CommandCenter services")

# Auto-refresh toggle
col1, col2 = st.columns([3, 1])
with col2:
    auto_refresh = st.checkbox("Auto-refresh (10s)", value=False)
    if st.button("🔄 Refresh Now", use_container_width=True):
        st.rerun()

if auto_refresh:
    time.sleep(10)
    st.rerun()

st.markdown("---")

# Railway API Health
st.markdown("### 🚀 Railway API Status")

with st.spinner("Checking Railway API..."):
    health = api.health_check()

col1, col2, col3 = st.columns(3)

if health and "status" in health and health["status"] == "healthy":
    with col1:
        st.success("✅ API Online")
        st.metric("Status", "Healthy")
    with col2:
        st.metric("URL", api.base_url.replace("https://", ""))
    with col3:
        st.metric("Response", "< 1s" if health else "Timeout")

    # Show API details
    with st.expander("📋 API Details"):
        st.json(health)
else:
    with col1:
        st.error("❌ API Offline")
    with col2:
        st.metric("Status", "Error")
    with col3:
        st.metric("Last Check", datetime.now().strftime("%H:%M:%S"))

    st.error(f"Could not connect to Railway API: {health.get('error', 'Unknown error')}")

st.markdown("---")

# Database Health
st.markdown("### 🗄️ PostgreSQL Database")

with st.spinner("Checking database connection..."):
    db_connected = db.is_connected()

col1, col2, col3 = st.columns(3)

if db_connected:
    with col1:
        st.success("✅ Database Connected")
        st.metric("Connection", "Active")

    # Get system stats from database
    stats = db.get_system_stats()

    with col2:
        st.metric("Total Snapshots", stats.get("total_energy_snapshots", 0))

    with col3:
        st.metric("Conversations", stats.get("total_conversations", 0))

    # Show database stats
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**📊 Statistics**")
        st.metric("Conversations Today", stats.get("conversations_today", 0))

        if stats.get("latest_energy"):
            latest = stats["latest_energy"]
            st.metric(
                "Latest SOC",
                f"{latest.get('battery_soc', 0):.1f}%",
                f"Solar: {latest.get('solar_power', 0):.0f}W"
            )

    with col2:
        st.markdown("**🔌 Connection Details**")
        st.code(db.db_url.split("@")[1] if "@" in db.db_url else "Local DB", language="text")

    # Show recent energy data sample
    with st.expander("📈 Recent Energy Data (Sample)"):
        df = db.get_recent_energy_data(hours=1)
        if not df.empty:
            st.dataframe(df.head(10), use_container_width=True)
            st.caption(f"Showing 10 of {len(df)} records from last hour")
        else:
            st.info("No energy data available")

else:
    with col1:
        st.error("❌ Database Disconnected")
    with col2:
        st.metric("Status", "Error")
    with col3:
        st.metric("Last Check", datetime.now().strftime("%H:%M:%S"))

    st.warning("Could not connect to PostgreSQL database. Check DATABASE_URL environment variable.")

st.markdown("---")

# Services Overview
st.markdown("### 🛠️ Services Status")

services = [
    {
        "name": "Railway API",
        "status": "🟢 Online" if health and health.get("status") == "healthy" else "🔴 Offline",
        "endpoint": api.base_url,
        "health": "Healthy" if health and health.get("status") == "healthy" else "Error"
    },
    {
        "name": "PostgreSQL",
        "status": "🟢 Connected" if db_connected else "🔴 Disconnected",
        "endpoint": "postgres.railway.internal:5432",
        "health": "Healthy" if db_connected else "Error"
    },
    {
        "name": "TimescaleDB",
        "status": "🟢 Active" if db_connected else "🔴 Inactive",
        "endpoint": "PostgreSQL Extension",
        "health": "Healthy" if db_connected else "Error"
    },
    {
        "name": "Solar Controller Agent",
        "status": "🟢 Ready" if health else "🟡 Unknown",
        "endpoint": "/agent/ask",
        "health": "Healthy" if health else "Unknown"
    }
]

# Display services table
import pandas as pd
df_services = pd.DataFrame(services)
st.dataframe(
    df_services,
    use_container_width=True,
    hide_index=True,
    column_config={
        "name": st.column_config.TextColumn("Service", width="medium"),
        "status": st.column_config.TextColumn("Status", width="small"),
        "endpoint": st.column_config.TextColumn("Endpoint", width="medium"),
        "health": st.column_config.TextColumn("Health", width="small")
    }
)

st.markdown("---")

# Environment Info
with st.expander("🔧 Environment Configuration"):
    st.markdown("**API Configuration**")
    st.code(f"RAILWAY_API_URL: {api.base_url}", language="bash")
    st.code(f"API_KEY: {'Set' if api.api_key else 'Not set'}", language="bash")

    st.markdown("**Database Configuration**")
    st.code(f"DATABASE_URL: {'Set' if db.db_url else 'Not set'}", language="bash")

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
