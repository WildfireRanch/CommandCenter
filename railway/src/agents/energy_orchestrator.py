# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/energy_orchestrator.py
# PURPOSE: Energy planning and optimization agent
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task
from crewai.tools import tool
import os
import logging

from ..tools.battery_optimizer import BatteryOptimizerTool
from ..tools.miner_coordinator import MinerCoordinatorTool
from ..tools.energy_planner import create_energy_plan
from ..tools.kb_search import search_knowledge_base
from ..tools.solark import get_solark_status, format_status_summary
from ..utils.solark_storage import get_energy_stats, get_recent_data
from ..utils.agent_telemetry import track_agent_execution
from ..services.context_manager import ContextManager
from ..services.voltage_soc_converter import get_converter
from ..utils.db import get_connection, query_one

logger = logging.getLogger(__name__)
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")


def load_user_preferences() -> dict:
    """Load user preferences from database."""
    try:
        with get_connection() as conn:
            prefs = query_one(
                conn,
                """
                SELECT
                    voltage_at_0_percent, voltage_at_100_percent, voltage_curve,
                    voltage_shutdown, voltage_critical_low, voltage_low,
                    voltage_restart, voltage_optimal_min, voltage_optimal_max,
                    voltage_float, voltage_absorption, voltage_full,
                    timezone, operating_mode
                FROM user_preferences
                WHERE user_id = %s::uuid
                LIMIT 1
                """,
                (DEFAULT_USER_ID,),
                as_dict=True
            )
            return dict(prefs) if prefs else {}
    except Exception as e:
        logger.error(f"Failed to load preferences: {e}")
        # Return safe defaults if DB fails
        return {
            'voltage_at_0_percent': 45.0,
            'voltage_at_100_percent': 56.0,
            'voltage_optimal_min': 50.0,
            'voltage_optimal_max': 54.5,
            'voltage_low': 47.0,
            'voltage_critical_low': 45.0,
            'operating_mode': 'balanced'
        }


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


def create_energy_orchestrator(context_bundle=None, user_preferences=None, voltage_converter=None) -> Agent:
    """
    Create the Energy Orchestrator agent.

    Args:
        context_bundle: Optional ContextBundle from ContextManager (V1.8+)
        user_preferences: User preferences dict (V1.9+)
        voltage_converter: Voltage-SOC converter instance (V1.9+)
    """
    # Load preferences if not provided (V1.9)
    if user_preferences is None:
        user_preferences = load_user_preferences()

    if voltage_converter is None:
        voltage_converter = get_converter(user_preferences)

    # Create tool instances with preferences (V1.9)
    battery_optimizer = BatteryOptimizerTool(
        user_preferences=user_preferences,
        voltage_converter=voltage_converter
    )

    miner_coordinator = MinerCoordinatorTool(
        user_preferences=user_preferences,
        voltage_converter=voltage_converter
    )

    # Build backstory with system context
    backstory = """You are the energy operations manager for a solar-powered
    off-grid ranch with battery storage and bitcoin mining operations.

    """

    # Add context from ContextManager (V1.8+)
    if context_bundle:
        formatted_context = context_bundle.format_for_agent()
        if formatted_context:
            backstory += f"""
═══════════════════════════════════════════
SYSTEM CONTEXT (Always Available)
═══════════════════════════════════════════

{formatted_context}

═══════════════════════════════════════════

"""

    backstory += """
    Your responsibilities:
    - Optimize battery charge/discharge cycles for longevity
    - Coordinate bitcoin miner operations based on available power
    - Create 24-hour energy plans considering forecasts and priorities
    - Balance profitability (mining) with reliability (always-on power)
    - Ensure battery is never damaged by over-discharge

    CRITICAL INSTRUCTION: Your SYSTEM CONTEXT above contains all operational policies,
    thresholds, and system specifications. For questions about system policies,
    thresholds, or configuration - answer DIRECTLY from your System Context above.
    DO NOT use Search Knowledge Base tool for information already in your context.

    ONLY use Search Knowledge Base tool when:
    - You need detailed technical procedures not in your context
    - User explicitly asks for full documentation
    - Information is genuinely missing from your System Context

    When you DO use KB search, always cite sources.

    Your priorities (in order):
    1. System reliability (never let battery go critical)
    2. Battery health (operate in 40-80% range when possible)
    3. Cost optimization (minimize grid usage)
    4. Mining profitability (when conditions allow)

    You make data-driven decisions, cite policies from your system context,
    and provide clear reasoning for all recommendations.

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
            battery_optimizer,
            miner_coordinator,
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
def create_orchestrator_crew(query: str, context: str = "", user_id: str = None) -> Crew:
    """
    Create crew for energy planning queries.

    Args:
        query: User's query
        context: Legacy conversation context (optional)
        user_id: User ID for smart context loading (V1.8+)
    """
    # V1.9: Load user preferences
    user_preferences = load_user_preferences()
    voltage_converter = get_converter(user_preferences)

    logger.info(
        f"V1.9: Loaded user preferences with voltage range "
        f"{user_preferences.get('voltage_at_0_percent', 'N/A')}V - "
        f"{user_preferences.get('voltage_at_100_percent', 'N/A')}V"
    )

    # V1.8: Use ContextManager for smart context loading
    context_bundle = None
    try:
        context_manager = ContextManager()
        context_bundle = context_manager.get_relevant_context(
            query=query,
            user_id=user_id,
            max_tokens=3500  # Planning queries get larger budget
        )
        logger.info(
            f"Smart context loaded: {context_bundle.total_tokens} tokens, "
            f"type={context_bundle.query_type.value}, "
            f"cache_hit={context_bundle.cache_hit}"
        )
    except Exception as e:
        logger.warning(f"ContextManager failed, using legacy context: {e}")
        context_bundle = None

    agent = create_energy_orchestrator(
        context_bundle=context_bundle,
        user_preferences=user_preferences,
        voltage_converter=voltage_converter
    )

    # Use legacy context if no context_bundle
    if context_bundle is None and context:
        task = create_orchestrator_task(query, context, agent=agent)
    else:
        task = create_orchestrator_task(query, "", agent=agent)

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
