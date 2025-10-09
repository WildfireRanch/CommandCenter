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
from ..tools.kb_search import search_knowledge_base


# ─────────────────────────────────────────────────────────────────────────────
# Routing Tools
# ─────────────────────────────────────────────────────────────────────────────

@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    """
    Route to Solar Controller agent for real-time status and monitoring queries.

    Use this tool when the user asks about:
    - Current battery level, SOC, or charge status
    - Current solar production (how much solar power right now)
    - Current power consumption or house load
    - Grid usage (importing/exporting right now)
    - Real-time system status
    - "What is happening now" type questions

    Examples:
    - "What's my battery level?"
    - "How much solar am I producing?"
    - "What's my current power usage?"
    - "Am I using grid power right now?"

    Args:
        query (str): The user's question about current/real-time status. Must be a simple string.

    Returns:
        str: JSON response from Solar Controller agent with current data
    """
    import json
    try:
        # Ensure query is a string (handle cases where LLM passes dict)
        if isinstance(query, dict):
            query = query.get('query') or query.get('description') or str(query)
        query = str(query)

        crew = create_energy_crew(query)
        result = crew.kickoff()

        # Return structured response with metadata
        return json.dumps({
            "response": str(result),
            "agent_used": "Solar Controller",
            "agent_role": "Energy Systems Monitor"
        })
    except Exception as e:
        return json.dumps({
            "response": f"Error routing to Solar Controller: {str(e)}",
            "agent_used": "Solar Controller",
            "error": True
        })


@tool("Route to Energy Orchestrator")
def route_to_energy_orchestrator(query: str) -> str:
    """
    Route to Energy Orchestrator for planning and optimization queries.

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
        query (str): Planning/optimization question. Must be a simple string.

    Returns:
        str: JSON response from Energy Orchestrator agent
    """
    import json
    try:
        # Ensure query is a string (handle cases where LLM passes dict)
        if isinstance(query, dict):
            query = query.get('query') or query.get('description') or str(query)
        query = str(query)

        crew = create_orchestrator_crew(query)
        result = crew.kickoff()

        # Return structured response with metadata
        return json.dumps({
            "response": str(result),
            "agent_used": "Energy Orchestrator",
            "agent_role": "Energy Operations Manager"
        })
    except Exception as e:
        return json.dumps({
            "response": f"Error routing to Energy Orchestrator: {str(e)}",
            "agent_used": "Energy Orchestrator",
            "error": True
        })


@tool("Search Knowledge Base")
def search_kb_directly(query: str) -> str:
    """
    Search the knowledge base for documentation, procedures, and specifications.

    Use this tool when the user asks:
    - "How to" questions (procedures, instructions)
    - "What is" questions (definitions, specifications)
    - Questions about policies, thresholds, or limits
    - Questions about maintenance or troubleshooting
    - Questions about system specifications
    - Historical information or documentation

    Examples:
    - "What is the minimum battery SOC threshold?"
    - "How do I maintain the solar panels?"
    - "What are the battery specifications?"
    - "What's the policy for running miners?"

    Args:
        query (str): The documentation or information question. Must be a simple string.

    Returns:
        str: Relevant documentation with source citations
    """
    try:
        # Ensure query is a string (handle cases where LLM passes dict)
        if isinstance(query, dict):
            query = query.get('query') or query.get('description') or str(query)
        query = str(query)

        return search_knowledge_base.func(query, limit=5)
    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


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
        backstory="""You are an intelligent query router for the Wildfire Ranch
        solar energy management system. Your job is to understand what the user
        is asking for and get them the right answer from the right source.

        You have access to:
        1. Solar Controller Agent - Real-time monitoring specialist
           (current battery, solar production, power usage, status)

        2. Energy Orchestrator Agent - Planning and optimization specialist
           (should we run miners, create energy plan, battery optimization)

        3. Knowledge Base - Documentation and procedures
           (specifications, policies, how-to guides, thresholds)

        ROUTING GUIDELINES:

        For CURRENT/REAL-TIME questions → Use Solar Controller
        - "What's my battery level?"
        - "How much solar am I producing?"
        - "What's the current status?"

        For PLANNING/OPTIMIZATION questions → Use Energy Orchestrator
        - "Should we run the miners?"
        - "Create an energy plan"
        - "When should we charge the battery?"
        - "What's the best strategy for..."

        For DOCUMENTATION/POLICY questions → Search Knowledge Base
        - "What is the minimum SOC threshold?"
        - "How do I maintain the panels?"
        - "What are the specifications?"

        For UNCLEAR or OFF-TOPIC questions → Provide helpful response
        - If the question is not related to energy/solar systems, politely
          explain this is an energy management assistant
        - If unclear what they need, ask for clarification
        - Examples: "who am I", "hello", "help" → Be friendly but direct

        IMPORTANT: When using tools, ALWAYS pass the original user query as a
        simple string to the 'query' parameter. Do NOT create complex objects
        or use different field names.

        You are CONCISE and DIRECT. You route queries to specialists - you
        don't try to answer technical questions yourself. Let the specialists
        do what they do best.""",
        tools=[route_to_solar_controller, route_to_energy_orchestrator, search_kb_directly],
        verbose=True,
        allow_delegation=True,
        max_iter=10,  # Prevent infinite retry loops
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

MANDATORY TOOL USAGE - You must call ONE of these tools:

1. If query is about CURRENT/REAL-TIME data (battery level, solar production, power usage, status):
   → CALL TOOL: route_to_solar_controller with parameter query="{query}"

2. If query is about PLANNING/DECISIONS (should we run miners, create plan, optimization):
   → CALL TOOL: route_to_energy_orchestrator with parameter query="{query}"

3. If query is about DOCUMENTATION/SPECS (thresholds, policies, how-to, specifications):
   → CALL TOOL: search_kb_directly with parameter query="{query}"

4. ONLY if query is completely off-topic (greetings, unrelated questions):
   → You may respond directly with a brief helpful message

CRITICAL RULES:
- You MUST call a tool for energy/solar queries - do not explain routing, DO THE ROUTING
- Pass the query as a simple string parameter
- Return ONLY the tool's output - no additional commentary
- Do NOT tell users which agent to use - USE THE TOOL YOURSELF
- Do NOT explain what the tools do - JUST USE THEM

Final answer format: Return exactly what the tool returns, nothing more.""",
        expected_output="""The direct output from whichever tool you called.

VALID outputs:
- Solar data from route_to_solar_controller tool
- Planning recommendation from route_to_energy_orchestrator tool
- Documentation from search_kb_directly tool
- Brief helpful message (only for off-topic queries)

INVALID outputs (never do these):
- "I suggest using the Energy Orchestrator agent"
- "You should ask about..."
- Explanations of routing logic
- Descriptions of what tools are available

You must return the actual answer, not routing advice.""",
        agent=agent,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Crew Assembly
# ─────────────────────────────────────────────────────────────────────────────

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
