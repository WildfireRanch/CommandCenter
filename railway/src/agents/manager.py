# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/manager.py
# PURPOSE: Manager agent for routing queries to specialized agents
#
# WHAT IT DOES:
#   - Analyzes user query intent
#   - Routes to appropriate specialist agent
#   - Coordinates multi-agent queries
#   - Handles clarification requests
#
# ROUTING LOGIC:
#   - Status queries → Solar Controller agent
#   - Documentation → Direct KB search
#   - Planning → Energy Orchestrator (future)
#   - Complex → Multi-agent coordination
#   - Unclear → Ask for clarification
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task, Process
from crewai.tools import tool

from .solar_controller import create_energy_crew
from .energy_orchestrator import create_orchestrator_crew
from .research_agent import create_research_crew
from ..tools.kb_search import search_knowledge_base
from ..utils.agent_telemetry import track_agent_execution


# ─────────────────────────────────────────────────────────────────────────────
# Routing Tools - Return routing decisions (not full execution)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    """
    Indicate that this query should be routed to the Solar Controller agent.

    Use this tool when the user asks about:
    - Current battery level, SOC, or charge status
    - Current solar production (how much solar power right now)
    - Current power consumption or house load
    - Grid usage (importing/exporting right now)
    - Real-time system status
    - "What is happening now" type questions
    - Historical energy data or trends
    - System configuration questions (inverter model, battery specs, hardware details)
    - Questions about THIS SPECIFIC SYSTEM's characteristics

    The Solar Controller has embedded knowledge about the system configuration
    and can answer questions like "what inverter do you have" without searching.

    Examples:
    - "What's my battery level?"
    - "How much solar am I producing?"
    - "What's my current power usage?"
    - "Am I using grid power right now?"
    - "Show me yesterday's solar production"
    - "What inverter model do you have?"
    - "What are your battery specs?"
    - "Tell me about your hardware"

    Args:
        query (str): The user's question about current/real-time status or system config.

    Returns:
        str: Routing decision in JSON format
    """
    import json
    return json.dumps({
        "action": "route",
        "agent": "Solar Controller",
        "agent_role": "Energy Systems Monitor",
        "query": str(query)
    })


@tool("Route to Energy Orchestrator")
def route_to_energy_orchestrator(query: str) -> str:
    """
    Indicate that this query should be routed to the Energy Orchestrator agent.

    Use when query is about:
    - "Should we" questions (run miners, charge battery, etc.)
    - Planning or scheduling
    - Optimization recommendations
    - Energy forecasts or predictions
    - Miner control decisions
    - Battery management strategies
    - Creating energy plans

    Examples:
    - "Should we run the miners tonight?"
    - "Create an energy plan for today"
    - "What's the best time to charge the battery?"
    - "When should we stop the miners?"
    - "What's the battery optimization recommendation?"

    Args:
        query (str): Planning/optimization question.

    Returns:
        str: Routing decision in JSON format
    """
    import json
    return json.dumps({
        "action": "route",
        "agent": "Energy Orchestrator",
        "agent_role": "Energy Operations Manager",
        "query": str(query)
    })


@tool("Route to Research Agent")
def route_to_research_agent(query: str) -> str:
    """
    Route to Research Agent for abstract, research, or comparative queries.

    Use when query involves:
    - Industry best practices or trends ("What are best practices for...")
    - Technology comparisons ("X vs Y", "Should I upgrade to...")
    - System comparisons ("How does my system compare to...")
    - Strategic planning ("What should I consider for...", "Is it worth...")
    - Expert opinions ("What do experts say about...", "What's the latest on...")
    - Future technology or market trends
    - Abstract or conceptual questions
    - Questions requiring current web information
    - Research-backed recommendations

    Examples:
    - "What are the latest trends in solar storage?"
    - "Should I upgrade to bifacial solar panels?"
    - "How does my energy cost compare to grid-tied systems?"
    - "What do experts say about LiFePO4 battery longevity?"
    - "Compare SolArk vs Victron inverters"
    - "What are best practices for off-grid battery sizing?"
    - "Is it worth adding more solar panels given current technology?"
    - "What's the latest research on solid-state batteries?"

    Args:
        query (str): Research, comparison, or strategic question.

    Returns:
        str: Routing decision in JSON format
    """
    import json
    return json.dumps({
        "action": "route",
        "agent": "Research Agent",
        "agent_role": "Energy Systems Research Consultant",
        "query": str(query)
    })


@tool("Search Knowledge Base")
def search_kb_directly(query: str) -> str:
    """
    Search the knowledge base for GENERAL documentation and procedures.

    IMPORTANT: Use this ONLY for general/reference documentation questions.
    For questions about THIS SPECIFIC SYSTEM's configuration, route to Solar Controller instead.

    Use this tool when the user asks:
    - General "how to" procedures (not specific to this system)
    - Technical documentation or reference material
    - Product manuals or guides
    - WHEN Solar Controller says "I need to check the documentation"

    DO NOT use this for:
    - Questions about this system's hardware (inverter model, battery specs)
    - Questions about current status (battery level, solar production)
    - Questions about system-specific thresholds or policies

    Examples of CORRECT usage:
    - "How do LiFePO4 batteries work in general?"
    - "What are best practices for solar panel maintenance?"
    - "Show me the full Victron manual"

    Examples of INCORRECT usage (route to Solar Controller instead):
    - "What inverter do you have?" → Solar Controller knows this
    - "What's your minimum SOC threshold?" → Solar Controller knows this
    - "What are your battery specs?" → Solar Controller knows this

    Args:
        query (str): The documentation or information question. Must be a simple string.

    Returns:
        str: Relevant documentation with source citations
    """
    import json
    try:
        # Ensure query is a string (handle cases where LLM passes dict)
        if isinstance(query, dict):
            query = query.get('query') or query.get('description') or str(query)
        query = str(query)

        kb_result = search_knowledge_base.func(query, limit=5)

        # For KB search, return simple format that won't confuse the Manager agent
        # The formatted text from KB search is ready to use as-is
        return f"{kb_result}\n\n[Source: Knowledge Base Search]"
    except Exception as e:
        return json.dumps({
            "response": f"Error searching knowledge base: {str(e)}",
            "agent_used": "Knowledge Base",
            "error": True
        })


# ─────────────────────────────────────────────────────────────────────────────
# Manager Agent Definition
# ─────────────────────────────────────────────────────────────────────────────

def create_manager_agent() -> Agent:
    """
    Create the Manager/Router agent.

    WHAT: Intelligent query router that analyzes intent
    WHY: Different types of questions need different specialists
    HOW: Analyzes query, routes to appropriate tool/agent

    Returns:
        Agent: Configured manager agent with routing tools
    """
    return Agent(
        role="Query Router and Coordinator",
        goal="Analyze user queries and route them to the most appropriate specialist or information source",
        backstory="""You are a ROUTING-ONLY agent. Your ONLY job is to call the right
        tool and return its output EXACTLY as received - DO NOT reformat, summarize,
        or add commentary.

        CRITICAL: You must return tool output VERBATIM. Do not interpret, reformat,
        or explain the tool's response. Just return it exactly as the tool gives it.

        Your tools:
        1. route_to_solar_controller - For status queries AND system configuration questions
        2. route_to_energy_orchestrator - For planning/optimization queries
        3. route_to_research_agent - For research, comparisons, and strategic questions
        4. search_kb_directly - For GENERAL documentation (NOT system-specific questions)

        ROUTING RULES (call tool immediately):

        System questions → route_to_solar_controller(query)
        Examples: battery level, solar production, inverter model, battery specs,
                  system configuration, "what do you have", "tell me about your system"

        Planning questions → route_to_energy_orchestrator(query)
        Examples: should we run miners, create plan, optimization, decisions

        Research/comparison questions → route_to_research_agent(query)
        Examples: "what are best practices", "should I upgrade", "how does X compare to Y",
                  "what's the latest on", "what do experts say", industry trends

        General documentation → search_kb_directly(query)
        Examples: "how do LiFePO4 batteries work", "show me the Victron manual"
        NOTE: System-specific questions go to Solar Controller, not KB search!

        Off-topic/greetings → Respond briefly (only case where you don't use a tool)
        Examples: hello, who am I, unrelated topics

        CRITICAL OUTPUT RULE:
        When you call a tool, return EXACTLY what the tool returns. Do not:
        - Reformat the response
        - Add your own commentary
        - Summarize or interpret
        - Change any formatting

        If the tool returns JSON, return that JSON. If it returns text, return that text.
        Your output = Tool output (no changes).""",
        tools=[
            route_to_solar_controller,
            route_to_energy_orchestrator,
            route_to_research_agent,
            search_kb_directly
        ],
        verbose=True,
        allow_delegation=False,  # Don't delegate - just route and return
        max_iter=3,  # Reduced: Call tool once, return result (was 10)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task Definition
# ─────────────────────────────────────────────────────────────────────────────

def create_routing_task(query: str, context: str = "", agent: Agent = None) -> Task:
    """
    Create task for manager to analyze and route the query.

    Args:
        query: User's question
        context: Previous conversation history (optional)
        agent: Pre-created agent instance (optional, will create if not provided)

    Returns:
        Task: Configured routing task
    """
    # Add context if available
    context_section = ""
    if context:
        context_section = f"""
Previous conversation context:
{context}

You can use this context to better understand the user's current question.
If they say "is that good?" or "what about now?" - they're likely referring
to something from the previous conversation.
"""

    # Create agent if not provided
    if agent is None:
        agent = create_manager_agent()

    return Task(
        description=f"""YOU MUST USE A TOOL FOR THIS QUERY. Do not respond without calling a tool first.

User query: "{query}"
{context_section}

MANDATORY TOOL USAGE - You MUST call a tool immediately:

1. REAL-TIME queries (battery, solar, power, status, current, now):
   → IMMEDIATELY call: route_to_solar_controller("{query}")

2. PLANNING queries (should we, create plan, optimize, decide, when):
   → IMMEDIATELY call: route_to_energy_orchestrator("{query}")

3. DOCUMENTATION queries (what is, how to, specifications, specs, threshold, policy):
   → IMMEDIATELY call: search_kb_directly("{query}")

4. OFF-TOPIC only (hello, who am I, unrelated):
   → Brief response

CRITICAL: For queries #1-3, your FIRST action must be calling the tool.
Do not think, analyze, or explain - JUST CALL THE TOOL IMMEDIATELY.

CRITICAL RULES:
- You MUST call a tool for energy/solar queries - do not explain routing, DO THE ROUTING
- Pass the query as a simple string parameter
- Return ONLY the tool's output - no additional commentary
- Do NOT tell users which agent to use - USE THE TOOL YOURSELF
- Do NOT explain what the tools do - JUST USE THEM

Final answer format: Return EXACTLY what the tool returns - no modifications.""",
        expected_output="""Return the tool's output verbatim.

For Solar Controller and Energy Orchestrator:
- These return JSON strings - return the complete JSON exactly

For Knowledge Base:
- Returns formatted text with sources - return that text exactly

DO NOT:
- Reformat, parse, or extract parts of the response
- Add your own commentary or explanations
- Change formatting or structure
- Iterate multiple times trying to improve the response

Call the tool once, get the result, return it immediately as your final answer.""",
        agent=agent,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Crew Assembly
# ─────────────────────────────────────────────────────────────────────────────

@track_agent_execution("Manager")
def create_manager_crew(query: str, context: str = "") -> Crew:
    """
    Create manager crew for intelligent query routing.

    WHAT: Crew that routes queries to appropriate specialists
    WHY: Different questions need different sources of information
    HOW: Manager agent analyzes intent and delegates to tools

    Args:
        query: User's question
        context: Previous conversation history (optional)

    Returns:
        Crew: Ready-to-execute crew with manager agent

    Example:
        >>> crew = create_manager_crew("What's my battery level?")
        >>> result = crew.kickoff()
        >>> print(result)  # Returns Solar Controller response
    """
    agent = create_manager_agent()
    task = create_routing_task(query, context, agent=agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the manager agent from command line."""
    import sys

    # Default test queries
    test_queries = [
        "What's my battery level?",  # Should route to Solar Controller
        "What is the minimum SOC threshold?",  # Should search KB
        "Help me",  # Should ask for clarification
    ]

    # Allow custom query from command line
    if len(sys.argv) > 1:
        test_queries = [" ".join(sys.argv[1:])]

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"🤖 Testing Manager Agent")
        print(f"📝 Query: {query}")
        print(f"{'='*70}\n")

        try:
            crew = create_manager_crew(query)
            result = crew.kickoff()

            print(f"\n{'='*70}")
            print("RESULT:")
            print(f"{'='*70}")
            print(result)
            print(f"{'='*70}\n")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
