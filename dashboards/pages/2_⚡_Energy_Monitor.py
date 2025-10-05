"""
Energy Monitor Dashboard
Real-time solar production, battery status, and historical trends
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from components.api_client import api
from components.db_client import db

st.set_page_config(
    page_title="Energy Monitor | CommandCenter",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ Energy Monitoring Dashboard")
st.caption("Solar production, battery status, and power flow")

# Auto-refresh
col1, col2 = st.columns([3, 1])
with col2:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

st.markdown("---")

# Latest Energy Data
st.markdown("### 📊 Current Status")

with st.spinner("Fetching latest energy data..."):
    latest = api.get_latest_energy()

if latest and "error" not in latest:
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        soc = latest.get("battery_soc", 0)
        st.metric(
            "🔋 Battery SOC",
            f"{soc:.1f}%",
            delta=f"{soc - 50:.1f}%" if soc else None,
            delta_color="normal" if soc > 50 else "inverse"
        )

    with col2:
        solar = latest.get("solar_power", 0)
        st.metric(
            "☀️ Solar Power",
            f"{solar:.0f} W",
            delta="Producing" if solar > 0 else "Idle"
        )

    with col3:
        load = latest.get("load_power", 0)
        st.metric(
            "🏠 Load Power",
            f"{load:.0f} W",
            delta="Active"
        )

    with col4:
        battery_pwr = latest.get("battery_power", 0)
        direction = "⬇️ Charging" if battery_pwr > 0 else "⬆️ Discharging" if battery_pwr < 0 else "⏸️ Idle"
        st.metric(
            "🔌 Battery Power",
            f"{abs(battery_pwr):.0f} W",
            delta=direction
        )

    # Detailed info
    with st.expander("📋 Detailed Information"):
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Battery Details**")
            st.text(f"Voltage: {latest.get('battery_voltage', 0):.1f} V")
            st.text(f"Current: {latest.get('battery_current', 0):.1f} A")
            st.text(f"Temperature: {latest.get('battery_temp', 0):.1f} °C")

        with col2:
            st.markdown("**Grid & System**")
            st.text(f"Grid Power: {latest.get('grid_power', 0):.0f} W")
            st.text(f"Timestamp: {latest.get('timestamp', 'N/A')}")

else:
    st.error("❌ Could not fetch energy data")
    st.json(latest)

st.markdown("---")

# Historical Charts
st.markdown("### 📈 Historical Trends")

# Time range selector
col1, col2 = st.columns([2, 1])
with col1:
    time_range = st.selectbox(
        "Time Range",
        options=[1, 6, 12, 24, 48, 72],
        index=3,  # Default to 24 hours
        format_func=lambda x: f"Last {x} hours"
    )

with st.spinner(f"Loading {time_range} hours of data..."):
    df = db.get_recent_energy_data(hours=time_range)

if not df.empty:
    # Battery SOC Chart
    st.markdown("#### 🔋 Battery State of Charge")
    fig_soc = go.Figure()
    fig_soc.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['battery_soc'],
        mode='lines',
        name='Battery SOC',
        line=dict(color='#10b981', width=2),
        fill='tozeroy',
        fillcolor='rgba(16, 185, 129, 0.1)'
    ))
    fig_soc.update_layout(
        xaxis_title="Time",
        yaxis_title="State of Charge (%)",
        hovermode='x unified',
        height=300,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_soc, use_container_width=True)

    # Power Flow Chart
    st.markdown("#### ⚡ Power Flow")
    fig_power = go.Figure()

    fig_power.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['solar_power'],
        mode='lines',
        name='Solar Production',
        line=dict(color='#f59e0b', width=2)
    ))

    fig_power.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['load_power'],
        mode='lines',
        name='Load Consumption',
        line=dict(color='#3b82f6', width=2)
    ))

    fig_power.add_trace(go.Scatter(
        x=df['timestamp'],
        y=df['battery_power'],
        mode='lines',
        name='Battery Power',
        line=dict(color='#10b981', width=2)
    ))

    fig_power.update_layout(
        xaxis_title="Time",
        yaxis_title="Power (W)",
        hovermode='x unified',
        height=400,
        margin=dict(l=0, r=0, t=30, b=0)
    )
    st.plotly_chart(fig_power, use_container_width=True)

    # Energy Statistics
    st.markdown("#### 📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        avg_soc = df['battery_soc'].mean()
        st.metric("Avg Battery SOC", f"{avg_soc:.1f}%")

    with col2:
        max_solar = df['solar_power'].max()
        st.metric("Peak Solar", f"{max_solar:.0f} W")

    with col3:
        avg_load = df['load_power'].mean()
        st.metric("Avg Load", f"{avg_load:.0f} W")

    with col4:
        total_solar = df['solar_power'].sum() / 1000  # Convert to kWh (rough estimate)
        st.metric("Est. Solar Energy", f"{total_solar:.1f} kWh")

    # Data Table
    with st.expander("📋 Raw Data"):
        st.dataframe(
            df.sort_values('timestamp', ascending=False),
            use_container_width=True,
            hide_index=True
        )
        st.caption(f"Showing {len(df)} records from last {time_range} hours")

else:
    st.warning("No energy data available for the selected time range")

st.markdown("---")

# System Insights
st.markdown("### 💡 Insights")

if not df.empty and latest:
    # Calculate insights
    current_soc = latest.get("battery_soc", 0)
    current_solar = latest.get("solar_power", 0)
    current_load = latest.get("load_power", 0)

    insights = []

    # SOC insights
    if current_soc > 80:
        insights.append("✅ Battery is well charged")
    elif current_soc > 50:
        insights.append("🟡 Battery is at moderate level")
    else:
        insights.append("⚠️ Battery is low - consider charging")

    # Solar insights
    if current_solar > current_load:
        surplus = current_solar - current_load
        insights.append(f"☀️ Solar surplus: {surplus:.0f}W available for battery charging or export")
    elif current_solar > 0:
        insights.append(f"⚡ Solar is active but not covering full load")
    else:
        insights.append("🌙 No solar production (nighttime or cloudy)")

    # Display insights
    for insight in insights:
        st.info(insight)

# Footer
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
