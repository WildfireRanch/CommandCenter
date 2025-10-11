# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/solar_controller.py
# PURPOSE: CrewAI agent for monitoring and managing energy systems
#
# WHAT IT DOES:
#   - Monitors SolArk inverter status (battery, solar, load, grid)
#   - Answers questions about current energy state
#   - Provides energy insights and recommendations
#
# DEPENDENCIES:
#   - crewai (agent framework)
#   - tools.solark (SolArk API integration)
#
# USAGE:
#   from agents.solar_controller import create_energy_crew
#
#   crew = create_energy_crew()
#   result = crew.kickoff(inputs={"query": "What's my battery level?"})
#   print(result)
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task
from crewai.tools import tool

from ..tools.solark import get_solark_status, format_status_summary
from ..tools.kb_search import search_knowledge_base, get_context_files
from ..utils.solark_storage import get_energy_stats, get_recent_data
from ..utils.agent_telemetry import track_agent_execution


# ─────────────────────────────────────────────────────────────────────────────
# Tool Definitions (CrewAI-compatible wrappers)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Get SolArk Status")
def get_energy_status() -> str:
    """
    Get current energy system status from SolArk inverter.
    
    Returns real-time data including:
    - Battery state of charge (%)
    - Solar production (W)
    - Battery charge/discharge rate (W)
    - House load consumption (W)
    - Grid import/export (W)
    
    Use this tool whenever the user asks about:
    - Battery level or charge state
    - Solar production
    - Power consumption
    - Grid usage
    - System status
    
    Returns:
        str: Formatted summary of current energy status
        
    Example output:
        "🔋 Battery: 52% (discharging at 3160W)
         ☀️ Solar: 1347W | ⚡ Load: 4250W | 🔌 Grid: 0W"
    """
    try:
        status = get_solark_status()
        return format_status_summary(status)
    except Exception as e:
        return f"❌ Error fetching SolArk status: {str(e)}"


@tool("Get Detailed Energy Data")
def get_detailed_status() -> dict:
    """
    Get detailed energy system data (raw numbers).

    Returns complete data structure with all metrics.
    Use this when you need specific numeric values for calculations
    or detailed analysis.

    Returns:
        dict: Detailed energy data with keys:
            - soc: Battery % (0-100)
            - pv_power: Solar production in watts
            - battery_power: Battery charge/discharge in watts
            - load_power: House load in watts
            - grid_power: Grid import/export in watts
            - charging: Boolean - is battery charging?
            - discharging: Boolean - is battery discharging?
            - exporting: Boolean - exporting to grid?
            - importing: Boolean - importing from grid?
    """
    try:
        status = get_solark_status()
        # Return dict without the 'raw' key (too verbose)
        return {k: v for k, v in status.items() if k != 'raw'}
    except Exception as e:
        return {"error": str(e)}


@tool("Get Historical Energy Statistics")
def get_historical_stats(hours: int = 24) -> str:
    """
    Get aggregated energy statistics over a time period.

    Returns statistical summary of energy data from the database including:
    - Average, minimum, and maximum battery SOC (%)
    - Average and peak solar production (W)
    - Average and peak load consumption (W)
    - Total number of data points analyzed

    Use this tool when the user asks about:
    - Historical averages (e.g., "What was my average solar production yesterday?")
    - Peak values (e.g., "What was my max solar output today?")
    - Battery trends (e.g., "How low did my battery go last night?")

    Args:
        hours: Number of hours to look back (default: 24)

    Returns:
        str: Formatted statistics summary

    Example output:
        "📊 Last 24 hours (based on 1,440 data points):
         🔋 Battery SOC: avg 67.2%, min 42.0%, max 98.5%
         ☀️ Solar: avg 2,341W, peak 5,847W
         ⚡ Load: avg 1,823W, peak 4,250W"
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
    This is essential for answering time-specific questions.

    Use this tool when the user asks about:
    - Specific times (e.g., "What time did I hit 2500W yesterday?")
    - Exact values at a point in time (e.g., "What was my SOC at 3pm?")
    - Trends over time (e.g., "Show me solar production this morning")
    - Finding when thresholds were crossed

    Args:
        hours: Number of hours to look back (default: 24)
        limit: Maximum number of records to return (default: 100, max: 1000)

    Returns:
        str: Formatted list of timestamped data points

    Example output:
        "📈 Last 24 hours of data (100 most recent points):
         2025-10-10 14:35:22 | SOC: 67% | Solar: 3,240W | Load: 1,850W | Battery: +1,390W (charging)
         2025-10-10 14:30:18 | SOC: 66% | Solar: 3,180W | Load: 1,920W | Battery: +1,260W (charging)
         ..."
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


# ─────────────────────────────────────────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────────────────────────────────────────

def create_energy_monitor_agent() -> Agent:
    """
    Create the Energy Monitor agent.

    WHAT: Agent that monitors and reports on energy systems
    WHY: Users need to check battery, solar, and power status
    HOW: Uses SolArk tools to fetch and interpret real-time data

    Returns:
        Agent: Configured CrewAI agent for energy monitoring
    """
    # Load system context from knowledge base
    system_context = get_context_files()

    # Build backstory with system context
    backstory = """You are an expert energy systems analyst specializing in
    solar + battery installations. You monitor a SolArk inverter system and
    help the homeowner understand their energy production, consumption, and
    battery status. You communicate clearly with accurate numbers and helpful
    context. When asked about status, you always use the real-time tools to
    get current data - never guess or use old information.

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
    CRITICAL INSTRUCTION: Your SYSTEM CONTEXT above contains all the key facts about
    this specific system (hardware specs, policies, thresholds). For questions about
    "your system", "this system", system configuration, or specifications - answer
    DIRECTLY from your System Context above. DO NOT use Search Knowledge Base tool
    for information already in your context.

    ONLY use Search Knowledge Base tool when:
    - You need detailed procedures or manuals not in your context
    - User explicitly asks for documentation ("show me the manual")
    - Information is genuinely missing from your System Context

    When you DO use KB search, always cite sources.

    IMPORTANT: When users ask about historical data, time-based questions, or
    specific times/dates, you MUST use the Get Time Series Energy Data tool
    to query the database. NEVER guess or make up times - always check the
    actual data."""

    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems and provide clear, accurate status reports",
        backstory=backstory,
        tools=[
            get_energy_status,
            get_detailed_status,
            get_historical_stats,
            get_time_series_data,
            search_knowledge_base
        ],
        verbose=True,
        allow_delegation=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task Templates
# ─────────────────────────────────────────────────────────────────────────────

def create_status_task(query: str, conversation_context: str = "", agent: Agent = None) -> Task:
    """
    Create a task to answer energy status questions.

    Args:
        query: User's question (e.g., "What's my battery level?")
        conversation_context: Previous conversation history (optional)
        agent: Pre-created agent instance (optional, will create if not provided)

    Returns:
        Task: Configured task for the energy monitor agent
    """
    # Build task description with context if available
    context_section = ""
    if conversation_context:
        context_section = f"\n\n{conversation_context}\n\n"

    # Create agent if not provided
    if agent is None:
        agent = create_energy_monitor_agent()

    return Task(
        description=f"""Answer this question about the energy system: {query}
        {context_section}
        Instructions:
        1. For CURRENT status questions: Use 'Get SolArk Status' tool
        2. For HISTORICAL questions (yesterday, last hour, average, peak, "hour-by-hour", trends, etc.):
           - Use 'Get Historical Energy Statistics' for averages/peaks/summary stats
           - Use 'Get Time Series Energy Data' for detailed breakdowns, specific times, or hourly data
        3. For questions asking for "breakdowns", "hourly data", "over time", or "what time did X happen?":
           YOU MUST use 'Get Time Series Energy Data' tool - this data EXISTS in the database
        4. Answer the specific question asked with REAL DATA from tools
        5. Provide helpful context if relevant
        6. Use clear language and accurate numbers
        7. NEVER say "data is not available" without trying the historical tools first
        8. NEVER guess times, dates, or values - always query the database
        9. If the data shows something noteworthy (like low battery), mention it

        The user's question: {query}
        """,
        expected_output="""A clear, accurate answer to the user's question with:
        - Direct answer to what was asked
        - Specific numbers from ACTUAL DATA (not guesses)
        - Timestamps when answering time-based questions
        - Brief context if helpful
        - References to previous conversations if relevant
        - No speculation or guessing""",
        agent=agent,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Crew Assembly
# ─────────────────────────────────────────────────────────────────────────────

@track_agent_execution("Solar Controller")
def create_energy_crew(query: str, conversation_context: str = "") -> Crew:
    """
    Create a crew to handle energy monitoring queries.

    WHAT: Assembles agent + task into executable crew
    WHY: CrewAI needs a crew to run tasks
    HOW: Combines energy monitor agent with status task, includes conversation history

    Args:
        query: User's question about energy system
        conversation_context: Previous conversation history (optional)

    Returns:
        Crew: Ready-to-execute crew

    Example:
        >>> crew = create_energy_crew("What's my battery level?")
        >>> result = crew.kickoff()
        >>> print(result)
    """
    agent = create_energy_monitor_agent()
    task = create_status_task(query, conversation_context, agent=agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the energy controller agent from command line."""
    import sys
    
    # Default test query
    test_query = "What's my current battery level?"
    
    # Allow custom query from command line
    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])
    
    print(f"🤖 Testing Energy Controller Agent")
    print(f"📝 Query: {test_query}\n")
    
    try:
        crew = create_energy_crew(test_query)
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
        sys.exit(1)