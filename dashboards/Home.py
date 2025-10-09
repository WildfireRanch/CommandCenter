"""
CommandCenter Operations Dashboard
Main entry point with custom sidebar navigation
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from components.api_client import api

# Page config
st.set_page_config(
    page_title="CommandCenter | Wildfire Ranch",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to match Next.js design
st.markdown("""
<style>
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* Main content area */
    .main {
        background-color: #f9fafb;
    }

    /* Cards */
    .stCard {
        background-color: white;
        border-radius: 8px;
        padding: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Headers */
    h1, h2, h3 {
        color: #111827;
    }

    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
    }

    /* Buttons */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
    }

    /* Logo and branding */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        font-size: 1.125rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
        padding: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar branding
with st.sidebar:
    col1, col2 = st.columns([1, 4])
    with col1:
        if Path("assets/WildfireMang.png").exists():
            st.image("assets/WildfireMang.png", width=40)
    with col2:
        st.markdown("### Wildfire Ranch")

    st.markdown("---")
    st.markdown("**CommandCenter v1.0**")
    st.caption("Operations Dashboard")

# Main content
st.title("⚡ CommandCenter")
st.markdown("### Welcome to Wildfire Ranch Operations")

st.info("""
**🎯 Navigation**: Use the sidebar to access different tools:
- 🏥 **System Health** - API status, database, service uptime
- ⚡ **Energy Monitor** - Solar production, battery, live data
- 🤖 **Agent Chat** - Talk to your Solar Controller
- 📊 **Logs** - View conversations and system activity
""")

# Quick stats overview
st.markdown("---")
st.markdown("### 📊 Quick Overview")

# Fetch latest energy data
latest = api.get_latest_energy()
energy_data = latest.get("data", {}) if latest and latest.get("status") == "success" else {}

col1, col2, col3, col4 = st.columns(4)

with col1:
    soc = energy_data.get("soc", 0)
    st.metric(
        label="🔋 Battery SOC",
        value=f"{soc:.0f}%" if soc else "N/A",
        delta="Charging" if energy_data.get("batt_power", 0) > 0 else "Discharging" if energy_data.get("batt_power", 0) < 0 else "Idle"
    )

with col2:
    solar = energy_data.get("pv_power", 0)
    st.metric(
        label="☀️ Solar Power",
        value=f"{solar:,.0f}W" if solar else "0W",
        delta="Producing" if solar > 0 else "Idle"
    )

with col3:
    load = energy_data.get("load_power", 0)
    st.metric(
        label="🏠 House Load",
        value=f"{load:,.0f}W" if load else "0W",
        delta="Active"
    )

with col4:
    grid_export = energy_data.get("pv_to_grid", 0)
    st.metric(
        label="⚡ Grid Export",
        value=f"{grid_export:,.0f}W" if grid_export else "0W",
        delta="Exporting" if grid_export > 0 else "None"
    )

st.markdown("---")

# Getting started section
st.markdown("### 🚀 Getting Started")

col1, col2 = st.columns(2)

with col1:
    st.markdown("""
    **System Monitoring**
    - Check API health and database connections
    - View real-time energy production data
    - Monitor agent activity and performance
    """)
    if st.button("🏥 Go to System Health", use_container_width=True):
        st.switch_page("pages/1_🏥_System_Health.py")

with col2:
    st.markdown("""
    **Agent Interaction**
    - Chat with your Solar Controller agent
    - View conversation history
    - Ask about energy status and optimization
    """)
    if st.button("🤖 Chat with Agent", use_container_width=True):
        st.switch_page("pages/3_🤖_Agent_Chat.py")

# Footer
st.markdown("---")
st.caption("Built with ❤️ for Wildfire Ranch | CommandCenter Dashboard v1.0")
