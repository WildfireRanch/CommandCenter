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

# Custom CSS to match Next.js design with compressed vertical spacing
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

    /* Compress vertical spacing - reduce padding throughout */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 1rem !important;
    }

    /* Reduce space between elements */
    .element-container {
        margin-bottom: 0.5rem !important;
    }

    /* Compress metric cards */
    [data-testid="stMetric"] {
        background-color: white;
        padding: 0.75rem !important;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }

    /* Metric labels - reduce spacing */
    [data-testid="stMetricLabel"] {
        padding-bottom: 0.25rem !important;
    }

    /* Metric values - keep font size, reduce padding */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 600;
        padding-top: 0 !important;
        padding-bottom: 0.25rem !important;
    }

    /* Metric delta - compress */
    [data-testid="stMetricDelta"] {
        padding-top: 0 !important;
    }

    /* Headers - reduce margin */
    h1 {
        color: #111827;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        padding-top: 0 !important;
    }

    h2, h3 {
        color: #111827;
        margin-top: 0.75rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Info boxes - compress */
    .stAlert {
        padding: 0.75rem !important;
        margin-bottom: 0.75rem !important;
    }

    /* Buttons - keep size, reduce margin */
    .stButton>button {
        border-radius: 6px;
        font-weight: 500;
        padding: 0.5rem 1rem !important;
    }

    .stButton {
        margin-top: 0.5rem !important;
    }

    /* Horizontal rules - reduce margin */
    hr {
        margin-top: 1rem !important;
        margin-bottom: 1rem !important;
    }

    /* Column gaps - reduce */
    [data-testid="column"] {
        padding: 0.25rem !important;
    }

    /* Markdown blocks - reduce spacing */
    .stMarkdown {
        margin-bottom: 0.5rem !important;
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
