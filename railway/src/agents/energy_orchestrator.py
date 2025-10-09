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


def create_energy_orchestrator() -> Agent:
    """Create the Energy Orchestrator agent."""
    return Agent(
        role="Energy Operations Manager",
        goal="Plan and optimize daily energy usage to maximize reliability and minimize costs",
        backstory="""You are the energy operations manager for a solar-powered
        off-grid ranch with battery storage and bitcoin mining operations.

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

        You make data-driven decisions, cite policies from the knowledge base,
        and provide clear reasoning for all recommendations.""",
        tools=[
            get_current_status,
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
        1. If asking about current status, use Get Current Energy Status tool
        2. For battery questions, use Battery Optimizer tool
        3. For miner questions, use Miner Coordinator tool
        4. For planning/scheduling, use Energy Planner tool
        5. For policies/thresholds, search Knowledge Base
        6. Provide clear recommendations with reasoning
        7. Cite sources when referencing policies

        The user's question: {query}
        """,
        expected_output="""A clear, actionable response with:
        - Specific recommendations or plans
        - Reasoning based on current state and policies
        - Any relevant warnings or considerations
        - Citations to knowledge base when applicable
        - No speculation - use tools to get real data""",
        agent=agent,
    )


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
