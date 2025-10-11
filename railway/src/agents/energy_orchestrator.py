# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/energy_orchestrator.py
# PURPOSE: Energy planning and optimization agent
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task
from crewai.tools import tool

from ..tools.battery_optimizer import optimize_battery
from ..tools.miner_coordinator import coordinate_miners
from ..tools.energy_planner import create_energy_plan
from ..tools.kb_search import search_knowledge_base
from ..tools.solark import get_solark_status, format_status_summary
from ..utils.solark_storage import get_energy_stats, get_recent_data
from ..utils.agent_telemetry import track_agent_execution


# Wrapper tool to get current status for planning
@tool("Get Current Energy Status")
def get_current_status() -> str:
    """
    Get current energy system status for planning decisions.

    Returns current battery SOC, solar production, load, and grid usage.
    Use this before making planning recommendations.
    """
    try:
        status = get_solark_status()
        return format_status_summary(status)
    except Exception as e:
        return f"Error getting status: {str(e)}"


@tool("Get Historical Energy Statistics")
def get_historical_stats(hours: int = 24) -> str:
    """
    Get aggregated energy statistics over a time period.

    Returns statistical summary of energy data from the database including:
    - Average, minimum, and maximum battery SOC (%)
    - Average and peak solar production (W)
    - Average and peak load consumption (W)
    - Total number of data points analyzed

    Use this tool when planning decisions require historical context:
    - Understanding typical load patterns
    - Analyzing battery discharge rates
    - Planning based on solar production trends

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        str: Formatted statistics summary
    """
    try:
        stats = get_energy_stats(hours=hours)

        if not stats or stats.get('total_records', 0) == 0:
            return f"No energy data available for the last {hours} hours."

        # Format the statistics
        result = f"📊 Last {hours} hours (based on {stats['total_records']:,} data points):\n"
        result += f"🔋 Battery SOC: avg {stats['avg_soc']:.1f}%, min {stats['min_soc']:.1f}%, max {stats['max_soc']:.1f}%\n"
        result += f"☀️ Solar: avg {stats['avg_pv_power']:.0f}W, peak {stats['max_pv_power']:.0f}W\n"
        result += f"⚡ Load: avg {stats['avg_load_power']:.0f}W, peak {stats['max_load_power']:.0f}W"

        return result
    except Exception as e:
        return f"❌ Error fetching historical statistics: {str(e)}"


@tool("Get Time Series Energy Data")
def get_time_series_data(hours: int = 24, limit: int = 100) -> str:
    """
    Get raw time-series energy data points from the database.

    Returns list of timestamped energy records showing exact values at specific times.
    Useful for analyzing patterns and trends for planning decisions.

    Use this tool when planning requires understanding:
    - Energy usage patterns over time
    - When peak loads typically occur
    - Solar production curves throughout the day

    Args:
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        str: Formatted list of timestamped data points
    """
    try:
        # Limit to reasonable max
        limit = min(limit, 1000)

        records = get_recent_data(hours=hours, limit=limit)

        if not records:
            return f"No energy data available for the last {hours} hours."

        # Format the records
        result = f"📈 Last {hours} hours of data ({len(records)} records, most recent first):\n\n"

        for record in records:
            timestamp = record['created_at']
            soc = record['soc']
            pv = record['pv_power']
            load = record['load_power']
            batt = record['batt_power']

            # Determine battery state
            if batt > 0:
                batt_state = "charging"
            elif batt < 0:
                batt_state = "discharging"
            else:
                batt_state = "idle"

            result += f"{timestamp} | SOC: {soc:.0f}% | Solar: {pv:,}W | Load: {load:,}W | Battery: {batt:+,}W ({batt_state})\n"

        return result
    except Exception as e:
        return f"❌ Error fetching time-series data: {str(e)}"


def create_energy_orchestrator() -> Agent:
    """Create the Energy Orchestrator agent."""
    # Load system context from knowledge base
    from ..tools.kb_search import get_context_files
    system_context = get_context_files()

    # Build backstory with system context
    backstory = """You are the energy operations manager for a solar-powered
    off-grid ranch with battery storage and bitcoin mining operations.

    """

    # Add system context if available
    if system_context:
        backstory += f"""
═══════════════════════════════════════════
SYSTEM CONTEXT (Always Available)
═══════════════════════════════════════════

{system_context}

═══════════════════════════════════════════

"""

    backstory += """
    Your responsibilities:
    - Optimize battery charge/discharge cycles for longevity
    - Coordinate bitcoin miner operations based on available power
    - Create 24-hour energy plans considering forecasts and priorities
    - Balance profitability (mining) with reliability (always-on power)
    - Ensure battery is never damaged by over-discharge

    You have access to:
    - Real-time system status (battery, solar, load, grid)
    - Knowledge base with operational policies and thresholds
    - Planning tools for battery, miners, and scheduling

    Your priorities (in order):
    1. System reliability (never let battery go critical)
    2. Battery health (operate in 40-80% range when possible)
    3. Cost optimization (minimize grid usage)
    4. Mining profitability (when conditions allow)

    You make data-driven decisions, cite policies from your system context and
    the knowledge base, and provide clear reasoning for all recommendations.

    IMPORTANT: Use historical data tools to inform your planning decisions.
    Never guess about past energy patterns - query the database."""

    return Agent(
        role="Energy Operations Manager",
        goal="Plan and optimize daily energy usage to maximize reliability and minimize costs",
        backstory=backstory,
        tools=[
            get_current_status,
            get_historical_stats,
            get_time_series_data,
            optimize_battery,
            coordinate_miners,
            create_energy_plan,
            search_knowledge_base
        ],
        verbose=True,
        allow_delegation=False,
    )


def create_orchestrator_task(query: str, context: str = "", agent: Agent = None) -> Task:
    """Create planning/optimization task."""
    context_section = ""
    if context:
        context_section = f"\n\nPrevious conversation context:\n{context}\n"

    # Create agent if not provided
    if agent is None:
        agent = create_energy_orchestrator()

    return Task(
        description=f"""Handle this energy planning or optimization query: {query}
        {context_section}
        Instructions:
        1. For current status: use Get Current Energy Status tool
        2. For historical context: use Get Historical Energy Statistics or Get Time Series Energy Data
        3. For battery optimization: use Battery Optimizer tool
        4. For miner coordination: use Miner Coordinator tool
        5. For planning/scheduling: use Energy Planner tool
        6. For policies/thresholds: search Knowledge Base
        7. Base ALL planning decisions on REAL DATA from tools
        8. Provide clear recommendations with reasoning
        9. Cite sources when referencing policies

        The user's question: {query}
        """,
        expected_output="""A clear, actionable response with:
        - Specific recommendations or plans
        - Reasoning based on ACTUAL DATA (current + historical)
        - Any relevant warnings or considerations
        - Citations to knowledge base when applicable
        - No speculation or guessing""",
        agent=agent,
    )


@track_agent_execution("Energy Orchestrator")
def create_orchestrator_crew(query: str, context: str = "") -> Crew:
    """Create crew for energy planning queries."""
    agent = create_energy_orchestrator()
    task = create_orchestrator_task(query, context, agent=agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the orchestrator from command line."""
    import sys

    test_query = "Should we run the miners right now?"

    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])

    print(f"🤖 Testing Energy Orchestrator")
    print(f"📝 Query: {test_query}\n")

    try:
        crew = create_orchestrator_crew(test_query)
        result = crew.kickoff()

        print("\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(result)
        print("="*70)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
