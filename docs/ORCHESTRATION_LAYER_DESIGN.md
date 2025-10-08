# Orchestration Layer Design
**Date:** October 8, 2025
**Purpose:** Route user queries to the appropriate specialized agent(s)
**Approach:** Manager Agent pattern using CrewAI hierarchical crews

---

## Problem Statement

Currently, the `/ask` endpoint only routes to the Solar Controller agent. We need:
1. Multiple specialized agents (Solar Controller, Energy Orchestrator, KB Search)
2. Intelligent routing based on query intent
3. Ability to coordinate multiple agents for complex queries
4. Clean API that frontend can call

---

## Solution: Manager Agent Pattern

### Architecture

```
User Query
    ↓
/ask endpoint
    ↓
Manager Agent (Orchestrator)
    ↓
Analyzes intent → Routes to:
    ├─ Solar Controller Agent (status, monitoring)
    ├─ Energy Orchestrator Agent (planning, optimization)
    └─ Direct KB Search (documentation lookup)
```

### How It Works

**Manager Agent:**
- Analyzes user query to determine intent
- Decides which agent(s) to engage
- Can delegate to one or multiple agents
- Synthesizes responses if multiple agents used
- Has access to routing tool

**Specialized Agents:**
- Solar Controller: Real-time status, monitoring
- Energy Orchestrator: Planning, optimization, miner control
- KB Search: Can be used by any agent OR directly for pure doc queries

---

## Implementation Plan

### Phase 1: Create Manager Agent (30 min)

**File:** `railway/src/agents/manager.py`

**Manager Agent:**
- **Role:** "Query Router and Coordinator"
- **Goal:** "Analyze user queries and route to appropriate specialized agents"
- **Tools:**
  - `route_to_solar_controller()` - Delegate status queries
  - `route_to_energy_orchestrator()` - Delegate planning queries
  - `search_knowledge_base()` - Direct KB search

**Routing Logic:**
```python
Keywords/Intent → Agent
─────────────────────────
"battery", "SOC", "status", "current" → Solar Controller
"plan", "optimize", "should we", "miner" → Energy Orchestrator
"how to", "what is", "documentation" → Direct KB Search
Complex multi-part queries → Multiple agents (sequential)
```

### Phase 2: Update /ask Endpoint (15 min)

**File:** `railway/src/api/main.py`

**Change:**
```python
# OLD: Direct to Solar Controller
crew = create_energy_crew(request.message, context)

# NEW: Route through Manager
crew = create_manager_crew(request.message, context)
```

**Manager crew:**
- Creates manager agent
- Creates task for query analysis + routing
- Uses hierarchical process (manager delegates to workers)

### Phase 3: Agent Integration (15 min)

**Update agent files:**
- `solar_controller.py` - Keep as-is (already a tool-using agent)
- `energy_orchestrator.py` - Create in Session 2 (not yet built)
- `manager.py` - New file

**Manager can call:**
```python
@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    """Route status/monitoring queries to Solar Controller agent."""
    crew = create_energy_crew(query)
    return crew.kickoff()

@tool("Route to Energy Orchestrator")
def route_to_energy_orchestrator(query: str) -> str:
    """Route planning/optimization queries to Energy Orchestrator."""
    crew = create_orchestrator_crew(query)
    return crew.kickoff()
```

---

## Routing Decision Tree

```
Query Analysis:
├─ Contains status keywords (battery, solar, current, now)
│  └─ → Solar Controller Agent
│
├─ Contains planning keywords (plan, optimize, should, recommend)
│  └─ → Energy Orchestrator Agent
│
├─ Contains documentation keywords (how, what is, procedure, manual)
│  └─ → Direct KB Search Tool
│
├─ Complex query (multiple intents)
│  └─ → Manager delegates to multiple agents sequentially
│
└─ Ambiguous
   └─ → Manager asks clarifying question
```

---

## Example Routing Scenarios

### Scenario 1: Simple Status Query
**User:** "What's my battery level?"
**Intent:** Status check
**Route:** Solar Controller Agent
**Tools Used:** get_energy_status()
**Response:** "Your battery is at 52% and currently discharging at 3160W."

### Scenario 2: Planning Query
**User:** "Should we run the miners tonight?"
**Intent:** Planning/optimization
**Route:** Energy Orchestrator Agent
**Tools Used:** battery_optimizer, energy_planner, search_kb_tool (for policies)
**Response:** "Based on current SOC (52%) and tonight's forecast, I recommend delaying miner start until 2am when battery is >70%. Current policy requires >60% SOC to run miners."

### Scenario 3: Documentation Query
**User:** "What's the minimum SOC threshold for the battery?"
**Intent:** Documentation lookup
**Route:** Direct KB Search
**Tools Used:** search_knowledge_base()
**Response:** "According to the Solar System Manual, the minimum battery SOC threshold is 20%. Operating below this can damage the battery. The recommended target SOC is 40-80% for daily operation."

### Scenario 4: Complex Multi-Agent Query
**User:** "Check the current solar status and create an energy plan for today"
**Intent:** Status + Planning (multi-agent)
**Route:** Manager → Solar Controller (first) → Energy Orchestrator (second)
**Process:**
1. Manager analyzes: needs both status AND planning
2. Delegates to Solar Controller for current status
3. Passes status to Energy Orchestrator for planning
4. Synthesizes both responses
**Response:** "Current Status: Battery at 52%, solar producing 1347W, load at 4250W. Based on this, here's today's plan: [orchestrator output]..."

### Scenario 5: Ambiguous Query
**User:** "What should I do?"
**Intent:** Unclear
**Route:** Manager handles directly
**Response:** "I can help with several things: check your solar system status, create an energy plan, or look up documentation. What would you like to know about?"

---

## Implementation Code Structure

### File: `railway/src/agents/manager.py`

```python
from crewai import Agent, Crew, Task, Process
from crewai.tools import tool

from .solar_controller import create_energy_crew
# from .energy_orchestrator import create_orchestrator_crew  # Session 2
from ..tools.kb_search import search_knowledge_base


@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    """
    Route to Solar Controller for real-time status queries.

    Use when query is about:
    - Current battery level/SOC
    - Current solar production
    - Current power consumption
    - System status right now
    - Grid usage

    Args:
        query: The user's question about current status

    Returns:
        Response from Solar Controller agent
    """
    crew = create_energy_crew(query)
    result = crew.kickoff()
    return str(result)


@tool("Search Documentation")
def search_documentation(query: str) -> str:
    """
    Search knowledge base for documentation and procedures.

    Use when query is about:
    - "How to" questions
    - "What is" questions
    - Operating procedures
    - System specifications
    - Maintenance guidelines
    - Policies and thresholds

    Args:
        query: The documentation question

    Returns:
        Relevant documentation with citations
    """
    return search_knowledge_base(query, limit=5)


def create_manager_agent() -> Agent:
    """Create the Manager/Router agent."""
    return Agent(
        role="Query Router and Coordinator",
        goal="Analyze user queries and route them to the most appropriate agent or tool",
        backstory="""You are an intelligent query router for a solar energy
        management system. You analyze what the user is asking for and route
        their query to the right specialist:

        - Solar Controller: For real-time status and monitoring
        - Energy Orchestrator: For planning and optimization (future)
        - Knowledge Base: For documentation and procedures

        If a query is complex and needs multiple specialists, you coordinate
        between them. If a query is unclear, you ask for clarification.

        You are concise and efficient - you route queries, you don't answer
        them yourself unless they're about what you can do.""",
        tools=[route_to_solar_controller, search_documentation],
        verbose=True,
        allow_delegation=True,
    )


def create_routing_task(query: str, context: str = "") -> Task:
    """Create task for manager to route the query."""
    context_section = f"\n\nPrevious conversation context:\n{context}\n" if context else ""

    return Task(
        description=f"""Analyze this user query and route it appropriately:

        User query: {query}
        {context_section}

        Instructions:
        1. Determine the intent of the query
        2. If it's about current status/monitoring → use Solar Controller
        3. If it's about documentation/procedures → search Knowledge Base
        4. If it's unclear → ask the user for clarification
        5. Provide the response from the appropriate source

        Do not answer the query yourself - route it to the right tool.""",
        expected_output="""Either:
        - Response from Solar Controller agent
        - Response from Knowledge Base search
        - A clarifying question if intent is unclear""",
        agent=create_manager_agent(),
    )


def create_manager_crew(query: str, context: str = "") -> Crew:
    """
    Create manager crew for routing queries.

    Args:
        query: User's question
        context: Previous conversation history

    Returns:
        Crew with manager agent
    """
    agent = create_manager_agent()
    task = create_routing_task(query, context)

    return Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
        verbose=True,
    )
```

### File: `railway/src/api/main.py` (update)

```python
# OLD (line ~863):
from ..agents.solar_controller import create_energy_crew
crew = create_energy_crew(request.message, context)

# NEW:
from ..agents.manager import create_manager_crew
crew = create_manager_crew(request.message, context)
```

---

## Benefits

✅ **Scalable:** Easy to add new agents (just add new routing tool)
✅ **Intelligent:** Manager can analyze intent and route appropriately
✅ **Flexible:** Can coordinate multiple agents for complex queries
✅ **Clean API:** Frontend still calls `/ask`, routing is transparent
✅ **Maintainable:** Each agent stays focused on its specialty

---

## Testing Plan

### Test 1: Simple Status Query
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}'
```
**Expected:** Manager routes to Solar Controller, returns current SOC

### Test 2: Documentation Query
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold?"}'
```
**Expected:** Manager searches KB directly, returns policy with citation

### Test 3: Ambiguous Query
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me"}'
```
**Expected:** Manager asks clarifying question

### Test 4: Multi-turn Conversation
```bash
# First query
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}'

# Follow-up (using session_id from response)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Is that good?", "session_id": "abc-123-xyz"}'
```
**Expected:** Manager understands context, routes appropriately

---

## Future Enhancements (V2)

- **Add Energy Orchestrator routing** (Session 2)
- **Multi-agent coordination** for complex queries
- **Query classification ML model** instead of keyword matching
- **Streaming responses** for long-running queries
- **Agent performance metrics** (which agent is faster/better)
- **Fallback routing** if preferred agent fails

---

## Next Steps

1. ✅ Design complete (this document)
2. Implement `manager.py`
3. Update `/ask` endpoint to use manager
4. Test routing with various query types
5. Deploy to Railway
6. Update frontend if needed (no changes required)

---

**Ready to implement!** Estimated time: 1 hour
