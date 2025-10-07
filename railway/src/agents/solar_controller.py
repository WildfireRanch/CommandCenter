# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/energy_controller.py
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
#   from agents.energy_controller import create_energy_crew
#   
#   crew = create_energy_crew()
#   result = crew.kickoff(inputs={"query": "What's my battery level?"})
#   print(result)
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task
from crewai.tools import tool

from ..tools.solark import get_solark_status, format_status_summary
from ..tools.kb_search import search_knowledge_base


# ─────────────────────────────────────────────────────────────────────────────
# Tool Definitions (CrewAI-compatible wrappers)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Search Knowledge Base")
def search_kb_tool(query: str) -> str:
    """
    Search the knowledge base for system documentation and procedures.

    Use this tool when you need information about:
    - Solar system specifications and limits
    - Battery operating thresholds (min SOC, target SOC, etc.)
    - Standard operating procedures
    - System maintenance guidelines
    - Hardware specifications
    - Business or operational policies

    Args:
        query: Natural language search query

    Returns:
        str: Relevant information with source citations

    Example:
        "What is the minimum battery SOC threshold?"
        "How should I handle low battery situations?"
        "What are the solar panel specifications?"
    """
    return search_knowledge_base(query, limit=5)


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
    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems and provide clear, accurate status reports",
        backstory="""You are an expert energy systems analyst specializing in
        solar + battery installations. You monitor a SolArk inverter system and
        help the homeowner understand their energy production, consumption, and
        battery status. You communicate clearly with accurate numbers and helpful
        context. When asked about status, you always use the real-time tools to
        get current data - never guess or use old information.

        You have access to a knowledge base with detailed system documentation,
        operating procedures, and specifications. When you need information about
        thresholds, limits, or procedures, use the Search Knowledge Base tool.
        Always cite your sources when referencing information from the KB.""",
        tools=[get_energy_status, get_detailed_status, search_kb_tool],
        verbose=True,
        allow_delegation=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task Templates
# ─────────────────────────────────────────────────────────────────────────────

def create_status_task(query: str, conversation_context: str = "") -> Task:
    """
    Create a task to answer energy status questions.

    Args:
        query: User's question (e.g., "What's my battery level?")
        conversation_context: Previous conversation history (optional)

    Returns:
        Task: Configured task for the energy monitor agent
    """
    # Build task description with context if available
    context_section = ""
    if conversation_context:
        context_section = f"\n\n{conversation_context}\n\n"

    return Task(
        description=f"""Answer this question about the energy system: {query}
        {context_section}
        Instructions:
        1. Use the 'Get SolArk Status' tool to fetch current data
        2. Answer the specific question asked
        3. Provide helpful context if relevant
        4. Use clear language and accurate numbers
        5. If the data shows something noteworthy (like low battery), mention it
        6. If there are previous conversations, you can reference them for context

        The user's question: {query}
        """,
        expected_output="""A clear, accurate answer to the user's question with:
        - Direct answer to what was asked
        - Specific numbers from current data
        - Brief context if helpful
        - References to previous conversations if relevant
        - No speculation or guessing""",
        agent=create_energy_monitor_agent(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# Crew Assembly
# ─────────────────────────────────────────────────────────────────────────────

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
    task = create_status_task(query, conversation_context)

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