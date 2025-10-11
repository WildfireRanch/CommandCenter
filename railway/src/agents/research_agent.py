# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/research_agent.py
# PURPOSE: CrewAI Research Agent for abstract queries and web research
#
# WHAT IT DOES:
#   - Handles abstract, conceptual, and research-oriented questions
#   - Performs web searches for current industry information
#   - Compares system against industry standards and best practices
#   - Provides research-backed recommendations and strategic insights
#
# DEPENDENCIES:
#   - crewai (agent framework)
#   - tools.kb_search (local knowledge base access)
#   - tools.mcp_client (Tavily web search via MCP)
#
# USAGE:
#   from agents.research_agent import create_research_crew
#
#   crew = create_research_crew()
#   result = crew.kickoff(inputs={"query": "What are best practices for off-grid solar?"})
#   print(result)
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task

from ..tools.kb_search import search_knowledge_base, get_context_files
from ..tools.mcp_client import tavily_search, tavily_extract
from ..utils.agent_telemetry import track_agent_execution


# ─────────────────────────────────────────────────────────────────────────────
# Agent Definition
# ─────────────────────────────────────────────────────────────────────────────

def create_research_agent() -> Agent:
    """
    Create the Research Agent with full context + web search.

    WHAT: Generalist agent for abstract questions, industry research, comparisons
    WHY: Users need research-backed insights for planning and decision-making
    HOW: Combines full system context + KB search + web search (Tavily MCP)

    Returns:
        Agent: Configured CrewAI agent for research and strategic analysis
    """
    # Load ALL context (24KB) - Research Agent needs comprehensive understanding
    full_context = get_context_files()

    backstory = f"""You are a senior energy systems consultant with deep expertise
    in off-grid solar installations, battery storage, and sustainable energy systems.

    You specialize in research, strategic planning, and technology analysis. Your
    role is to provide research-backed recommendations, industry comparisons, and
    long-term strategic insights.

    ═══════════════════════════════════════════════════════════════════
    COMPLETE SYSTEM CONTEXT
    ═══════════════════════════════════════════════════════════════════

    {full_context}

    ═══════════════════════════════════════════════════════════════════

    YOUR CAPABILITIES:

    1. SYSTEM KNOWLEDGE (from context above)
       - Complete hardware specifications for user's system
       - All operational policies, thresholds, and priorities
       - User preferences and system history
       - Current system performance and capabilities

    2. KNOWLEDGE BASE ACCESS (search_knowledge_base tool)
       - Detailed technical documentation
       - Operating procedures and manuals
       - Historical learnings and best practices
       - Specific how-to guides and troubleshooting

    3. WEB SEARCH (tavily_search tool via Tavily MCP)
       - Current industry trends and news
       - Recent technology developments and innovations
       - Expert opinions and case studies
       - Vendor comparisons and product reviews
       - Latest research papers and articles

    4. WEB CONTENT EXTRACTION (tavily_extract tool)
       - Deep-dive into specific articles and documentation
       - Extract detailed information from URLs
       - Analyze technical specifications and reviews

    ═══════════════════════════════════════════════════════════════════
    TOOL USAGE GUIDELINES
    ═══════════════════════════════════════════════════════════════════

    Use SYSTEM CONTEXT (embedded above) when:
    - User asks about THEIR specific system specifications
    - User asks about THEIR system's performance or status
    - Comparing THEIR system to industry standards
    - Making recommendations specific to THEIR setup

    Use KNOWLEDGE BASE (search_knowledge_base) when:
    - Need detailed procedures or how-to guides
    - Looking for internal documentation or manuals
    - Seeking historical learnings specific to this system
    - Finding troubleshooting information

    Use WEB SEARCH (tavily_search) when:
    - User asks "What are best practices for..."
    - User asks "What's the latest on [technology]..."
    - User asks "How does X compare to Y..."
    - User asks "Should I upgrade to..."
    - User asks "What do experts say about..."
    - Need current industry trends or recent news
    - Comparing technologies, vendors, or products
    - Finding expert opinions or case studies
    - Information not in system context or KB

    Use WEB EXTRACT (tavily_extract) when:
    - Found a relevant article in web search results
    - User provides a specific URL to analyze
    - Need full content from a particular source

    ═══════════════════════════════════════════════════════════════════
    RESPONSE GUIDELINES
    ═══════════════════════════════════════════════════════════════════

    1. ALWAYS cite your sources:
       - System Context: "According to your system specifications..."
       - Knowledge Base: "From the system documentation..."
       - Web Search: "According to [Source Name] ([URL])..."

    2. COMBINE multiple information sources:
       - Start with user's system context
       - Add relevant KB information if available
       - Supplement with current web research
       - Compare and synthesize all sources

    3. PROVIDE actionable recommendations:
       - Be specific and practical
       - Consider user's current system and constraints
       - Include pros/cons and trade-offs
       - Suggest next steps or considerations

    4. FOCUS on research quality:
       - Prioritize recent, authoritative sources
       - Cross-reference information when possible
       - Acknowledge uncertainty or conflicting information
       - Distinguish facts from opinions

    5. STRUCTURE your response:
       - Start with direct answer to the question
       - Provide supporting evidence and citations
       - Include relevant context from user's system
       - End with recommendations or next steps

    ═══════════════════════════════════════════════════════════════════

    Your goal is to provide thoughtful, well-researched answers that help the
    user make informed decisions about their energy system and future planning.
    """

    return Agent(
        role="Energy Systems Research Consultant",
        goal="Provide research-backed insights, industry comparisons, and strategic recommendations",
        backstory=backstory,
        tools=[
            search_knowledge_base,      # Local KB for detailed procedures
            tavily_search,              # Web search via Tavily MCP
            tavily_extract,             # Deep article extraction via MCP
        ],
        verbose=True,
        allow_delegation=False,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Task Templates
# ─────────────────────────────────────────────────────────────────────────────

def create_research_task(query: str, agent: Agent = None) -> Task:
    """
    Create a task for research queries.

    Args:
        query: User's research question
        agent: Pre-created agent instance (optional, will create if not provided)

    Returns:
        Task: Configured task for the research agent
    """
    # Create agent if not provided
    if agent is None:
        agent = create_research_agent()

    return Task(
        description=f"""Answer this research question: {query}

        Instructions:
        1. Start with your SYSTEM CONTEXT (embedded above) for user-specific facts
        2. Use KNOWLEDGE BASE (search_knowledge_base) for detailed procedures/manuals
        3. Use WEB SEARCH (tavily_search) for:
           - Current industry trends and news
           - Technology comparisons and reviews
           - Expert opinions and case studies
           - Information not in system context or KB
        4. ALWAYS cite your sources:
           - System Context: "According to your system specifications..."
           - Knowledge Base: "From the system documentation..."
           - Web Search: "According to [Source Name] ([URL])..."
        5. Combine multiple sources for comprehensive answers
        6. Provide actionable recommendations specific to the user's system
        7. Structure response: Direct answer → Evidence → Context → Recommendations

        The user's question: {query}
        """,
        expected_output="""A comprehensive, well-researched answer with:
        - Direct answer to the question
        - Citations from multiple sources (system context, KB, and/or web search)
        - Supporting evidence and context
        - Specific recommendations or next steps
        - All facts properly sourced (no hallucinations)""",
        agent=agent,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Crew Factory
# ─────────────────────────────────────────────────────────────────────────────

def create_research_crew(query: str) -> Crew:
    """
    Create a crew with the Research Agent.

    WHAT: Single-agent crew for research and strategic analysis
    WHY: Standardized interface for executing research queries
    HOW: Creates agent + task + crew for query processing

    Args:
        query: User's research question

    Returns:
        Crew: Configured crew ready to process research queries
    """
    # Create the agent
    agent = create_research_agent()

    # Create the task with query
    task = create_research_task(query, agent=agent)

    # Create and return the crew
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )

    return crew


# ─────────────────────────────────────────────────────────────────────────────
# Main Execution Wrapper
# ─────────────────────────────────────────────────────────────────────────────

@track_agent_execution
def execute_research_query(query: str) -> dict:
    """
    Execute a research query using the Research Agent.

    WHAT: High-level wrapper for research query execution
    WHY: Provides clean API for calling from routing layer
    HOW: Creates crew, executes query, handles errors

    Args:
        query: User's research question

    Returns:
        dict: {
            "success": bool,
            "response": str (agent's answer),
            "error": str (if failed),
            "agent": "Research Agent"
        }
    """
    try:
        crew = create_research_crew(query)
        result = crew.kickoff()

        return {
            "success": True,
            "response": str(result),
            "agent": "Research Agent"
        }

    except Exception as e:
        return {
            "success": False,
            "response": None,
            "error": str(e),
            "agent": "Research Agent"
        }


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the Research Agent from command line.

    Usage:
        python -m src.agents.research_agent

    Requires:
        - Database connection for context and KB
        - TAVILY_API_KEY for web search
    """
    print("🔬 Testing Research Agent...\n")

    # Test query
    test_query = "What are current best practices for sizing off-grid solar battery systems?"

    print(f"Query: {test_query}")
    print("-" * 80)

    result = execute_research_query(test_query)

    if result["success"]:
        print(f"\n✅ Agent: {result['agent']}")
        print(f"\nResponse:\n{result['response']}")
    else:
        print(f"\n❌ Error: {result['error']}")

    print("-" * 80)
    print("\n✅ Test complete!")
