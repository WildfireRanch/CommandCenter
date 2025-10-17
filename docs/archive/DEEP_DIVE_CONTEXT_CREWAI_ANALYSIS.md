# Deep Dive: Context Management & CrewAI Architecture Analysis
**Date:** 2025-10-11
**System:** CommandCenter V1.5 - Multi-agent energy management system
**Investigation:** Why context isn't working and how CrewAI is actually being used

---

## Executive Summary

### Critical Findings

**GOOD NEWS:** The system architecture is fundamentally sound and follows modern best practices.

**BAD NEWS:** The **"CONTEXT folder" system you think exists DOES NOT ACTUALLY EXIST**. There is NO code that loads context_ prefixed files into agent system prompts.

### What We Found

1. **Context Architecture:** There IS a proper KB system with `is_context_file` flagging, but agents aren't loading it
2. **CrewAI Usage:** The framework is being used correctly with proper task/agent/crew patterns
3. **The Real Problem:** Context lives in the Knowledge Base but requires **explicit search tool calls** - it's NOT automatically available to agents

---

## Part 1: Context Architecture - Current State

### 1.1 How Context ACTUALLY Works (With Evidence)

#### The Knowledge Base System (What EXISTS)

**File:** `railway/src/kb/sync.py` (lines 107-439)

```python
# ACTUAL CONTEXT DETECTION CODE (line 258-262)
is_context = (
    '/CONTEXT/' in folder_path.upper() or
    folder_name.upper() == 'CONTEXT' or
    'context' in file_name.lower()
)
```

**What this does:**
- Syncs Google Drive folders recursively
- Detects files with "context" in path/filename
- Sets `is_context_file=TRUE` flag in database
- Stores full content in `kb_documents.full_content`
- Chunks content and generates embeddings in `kb_chunks`

**Evidence this is working:** `railway/src/tools/kb_search.py` lines 111-164 shows a `get_context_files()` function that CAN retrieve these files.

#### The Critical Gap (What DOESN'T EXIST)

**SEARCHED FOR:**
```bash
grep -r "get_context_files" railway/src/agents/
# RESULT: No matches found
```

**CONCLUSION:** The `get_context_files()` function exists but is **NEVER CALLED** by any agent.

### 1.2 Context Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     GOOGLE DRIVE FOLDER                          │
│  └── CONTEXT/                                                    │
│      ├── solar-shack-context.docx    ← marked is_context=TRUE   │
│      ├── system-capabilities.docx    ← marked is_context=TRUE   │
│      └── operational-policies.docx   ← marked is_context=TRUE   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      [KB Sync Service]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DATABASE                         │
│                                                                   │
│  kb_documents table:                                             │
│    ├── full_content (complete text)                             │
│    └── is_context_file=TRUE  ← FLAG IS SET!                     │
│                                                                   │
│  kb_chunks table:                                                │
│    ├── chunk_text (512 token chunks)                            │
│    └── embedding (vector for similarity search)                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              ┌───────────────┴───────────────┐
              ↓                               ↓
    [Tool: search_knowledge_base]    [Tool: get_context_files]
              ↓                               ↓
         ✅ CALLED                      ❌ NEVER CALLED
         by agents                      by anyone
         when needed
              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       AGENTS (CrewAI)                            │
│                                                                   │
│  ❌ System Prompt: NO context loaded here                       │
│  ❌ Backstory: NO context loaded here                           │
│  ❌ Task Description: NO context loaded here                    │
│                                                                   │
│  ✅ Tools: search_knowledge_base available                      │
│     └── Agent MUST explicitly call tool to get context          │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 The Two-Tier System (What You THOUGHT You Had)

**Your Assumption:**
- **Tier 1 (CONTEXT):** Files with `context_` prefix always loaded into agent system prompts
- **Tier 2 (KB):** Everything else searchable via semantic search

**Reality:**
- **Tier 1 (CONTEXT):** Files flagged `is_context_file=TRUE` stored in database, retrievable via `get_context_files()`, **BUT NEVER ACTUALLY RETRIEVED**
- **Tier 2 (KB):** Everything (including context files) searchable via `search_knowledge_base` tool

**Why This Matters:**
Your agents have to **actively search** for system capabilities, operational procedures, and specifications. They don't "just know" this information.

### 1.4 Context Loading - WHERE and WHEN

#### WHERE Context SHOULD Be Loaded

**Option A: Agent Backstory** (Current approach - PARTIAL)

File: `railway/src/agents/solar_controller.py` (lines 217-246)

```python
def create_energy_monitor_agent() -> Agent:
    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems...",
        backstory="""You are an expert energy systems analyst...

        You have access to a knowledge base with detailed system
        documentation, operating procedures, and specifications.
        When you need information about thresholds, limits, or
        procedures, use the Search Knowledge Base tool.
        ❌ NO ACTUAL CONTEXT LOADED HERE
        """,
        tools=[...],
        verbose=True,
    )
```

**Problem:** The backstory TELLS the agent about the knowledge base but doesn't GIVE it the context.

**Option B: Task Description** (Current approach - PARTIAL)

File: `railway/src/agents/manager.py` (lines 269-316)

```python
def create_routing_task(query: str, context: str = "", agent: Agent = None) -> Task:
    context_section = ""
    if context:
        context_section = f"""
Previous conversation context:
{context}

You can use this context to better understand the user's current question.
"""
    # ✅ Conversation history IS loaded
    # ❌ System context/capabilities NOT loaded
```

**What IS Working:** Conversation history from previous turns (lines 848-854 in `api/main.py`)

**What ISN'T Working:** System capabilities, specifications, operational procedures

#### WHEN Context Is Loaded

**Current Flow:**

1. **API Request** (`/ask` endpoint) - `railway/src/api/main.py:776`
2. **Get conversation context** - Lines 848-854
   ```python
   context = get_conversation_context(
       agent_role=agent_role,
       current_conversation_id=conversation_id,
       max_conversations=3,
       max_messages_per_conversation=6
   )
   ```
3. **Create crew with context** - Line 890
   ```python
   crew = create_manager_crew(request.message, context)
   ```
4. **Manager receives context** - `manager.py:241-263`
5. **Manager routes to specialist** - Lines 64-78 (Solar) or 115-129 (Orchestrator)
6. **Specialist receives query** - Lines 309-336 in `solar_controller.py`

**What's Loaded at Each Step:**
- ✅ User's current query
- ✅ Previous conversation messages (last 3 conversations, 6 messages each)
- ❌ System capabilities/specifications
- ❌ Operational procedures
- ❌ Hardware details
- ❌ Policy thresholds

### 1.5 Context Types Analysis

**What agents need to know:**

| Context Type | Where It Lives | How Agents Access It | Status |
|-------------|----------------|---------------------|--------|
| **System Architecture** | KB (is_context=TRUE) | ❌ Should be in system prompt | MISSING |
| **Hardware Specs** | KB (is_context=TRUE) | ❌ Should be in system prompt | MISSING |
| **Operational Procedures** | KB | ✅ search_knowledge_base tool | WORKS |
| **Business Rules** | KB | ✅ search_knowledge_base tool | WORKS |
| **User Preferences** | Not implemented | N/A | MISSING |
| **Historical Patterns** | Database (solark.telemetry) | ✅ Tools (get_historical_stats, get_time_series_data) | WORKS |
| **Conversation History** | Database (agent.conversations) | ✅ Loaded automatically | WORKS |
| **Current System State** | SolArk API + DB | ✅ Tools (get_solark_status) | WORKS |

**Analysis:**
- **Data Access:** Excellent - agents have good tools
- **Core Knowledge:** Missing - agents don't know what system they're running
- **Historical Context:** Excellent - full time-series data access
- **Conversation Memory:** Working - recent chats are provided

---

## Part 2: CrewAI Architecture - Implementation Analysis

### 2.1 CrewAI Framework Fundamentals (How YOU'RE Using It)

#### Hierarchy: Crew → Agents → Tasks

**Evidence from codebase:**

**Manager Crew** (`railway/src/agents/manager.py:323-352`)
```python
@track_agent_execution("Manager")
def create_manager_crew(query: str, context: str = "") -> Crew:
    agent = create_manager_agent()  # 1 Agent
    task = create_routing_task(query, context, agent=agent)  # 1 Task

    return Crew(
        agents=[agent],  # ✅ List of agents
        tasks=[task],    # ✅ List of tasks
        process=Process.sequential,  # ✅ Execution strategy
        verbose=True,
    )
```

**Solar Controller Crew** (`railway/src/agents/solar_controller.py:308-336`)
```python
@track_agent_execution("Solar Controller")
def create_energy_crew(query: str, conversation_context: str = "") -> Crew:
    agent = create_energy_monitor_agent()  # 1 Agent
    task = create_status_task(query, conversation_context, agent=agent)  # 1 Task

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,  # No process specified - defaults to sequential
    )
```

**Energy Orchestrator Crew** (`railway/src/agents/energy_orchestrator.py:208-218`)
```python
@track_agent_execution("Energy Orchestrator")
def create_orchestrator_crew(query: str, context: str = "") -> Crew:
    agent = create_energy_orchestrator()
    task = create_orchestrator_task(query, context, agent=agent)

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )
```

**Assessment:** ✅ **CORRECT USAGE**
- Each crew has 1 agent and 1 task (simple, clean)
- Process.sequential used appropriately
- Task bound to agent correctly

### 2.2 Agent Communication Pattern

**Your Current Architecture:**

```
User Query
    ↓
┌─────────────────────────────────────┐
│   Manager Agent (Orchestrator)      │
│   Role: "Query Router"              │
│   Tools:                             │
│     - route_to_solar_controller ────┼─→ Creates NEW Crew
│     - route_to_energy_orchestrator ─┼─→ Creates NEW Crew
│     - search_kb_directly ───────────┼─→ Direct search
└─────────────────────────────────────┘
                ↓
                ↓ Tool calls create_energy_crew()
                ↓
┌─────────────────────────────────────┐
│   Solar Controller Agent            │
│   Role: "Energy Systems Monitor"    │
│   Tools:                             │
│     - get_energy_status             │
│     - get_detailed_status           │
│     - get_historical_stats          │
│     - get_time_series_data          │
│     - search_knowledge_base         │
└─────────────────────────────────────┘
```

**Key Code Evidence:**

**Manager's Routing Tool** (`manager.py:32-78`)
```python
@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    # Ensure query is a string
    if isinstance(query, dict):
        query = query.get('query') or str(query)
    query = str(query)

    crew = create_energy_crew(query)  # ← Creates NEW CREW
    result = crew.kickoff()           # ← Runs it

    return json.dumps({
        "response": str(result),
        "agent_used": "Solar Controller",
        "agent_role": "Energy Systems Monitor"
    })
```

**Assessment:**
- ✅ **Pattern:** Tool-based routing (not delegation)
- ✅ **Execution:** Each specialist gets its own crew instance
- ❌ **Context Loss:** When new crew is created, specialist doesn't get Manager's context
- ⚠️ **Unusual but valid:** Most CrewAI examples use hierarchical process with delegation, but tool-based routing works

### 2.3 Context Passing in CrewAI

**What SHOULD Happen (Your Intent):**

Manager routes to Solar Controller → Solar Controller sees:
1. User's original query
2. Conversation history
3. Manager's analysis
4. Previous interactions

**What ACTUALLY Happens:**

**Manager Crew Execution** (`api/main.py:889-893`)
```python
# Create manager crew to route query intelligently
crew = create_manager_crew(request.message, context)  # ← Context passed
result = crew.kickoff()
```

**Manager Passes Query to Tool** (`manager.py:64`)
```python
crew = create_energy_crew(query)  # ← Query passed, but NOT context!
result = crew.kickoff()
```

**Solar Controller Receives** (`solar_controller.py:309`)
```python
def create_energy_crew(query: str, conversation_context: str = "") -> Crew:
    # conversation_context parameter EXISTS
    # BUT is never populated when called from manager tool!
```

**THE BUG:** Manager's routing tools don't pass `context` parameter to specialist crews.

**Evidence:**
```python
# manager.py line 64 - CURRENT (WRONG)
crew = create_energy_crew(query)

# Should be - FIXED
crew = create_energy_crew(query, conversation_context=context)
```

But wait - the Manager tool doesn't even HAVE access to context! It's not passed as a parameter.

**Root Cause:** Manager's routing tools are defined at module level (line 32) and don't have access to the context that's passed to create_routing_task() on line 241.

### 2.4 Memory & State Management

**What CrewAI Provides:**
- Short-term memory (task outputs within a crew)
- Long-term memory (RAG-based, optional)
- Shared memory (between agents in same crew)

**What YOU'RE Using:**
- ❌ Not using CrewAI's memory system
- ✅ Custom conversation storage in PostgreSQL (`agent.conversations`, `agent.messages`)
- ✅ Context retrieval from database (`get_conversation_context`)

**Assessment:** ✅ **VALID APPROACH**
- You're building stateless agents with external memory
- Each crew execution is independent
- Context explicitly loaded from DB before crew creation
- This is MORE robust than CrewAI's built-in memory for production systems

**File Evidence:** `railway/src/utils/conversation.py:262-360`
```python
def get_conversation_context(...) -> str:
    """
    Get formatted conversation context for agent prompts.

    Retrieves recent conversations and formats them as context
    that can be included in agent prompts to provide memory.
    """
    # Queries database for recent conversations
    # Formats as readable context string
    # Returns to be included in task description
```

### 2.5 Tool Design Assessment

**Your Tools:**

| Tool | Type | Design Quality | Notes |
|------|------|----------------|-------|
| `route_to_solar_controller` | Routing | ⚠️ Problematic | Creates new crew, loses context |
| `route_to_energy_orchestrator` | Routing | ⚠️ Problematic | Creates new crew, loses context |
| `search_kb_directly` | Data Access | ✅ Good | Direct function call, simple |
| `get_energy_status` | Data Access | ✅ Excellent | Well-documented, error handling |
| `get_detailed_status` | Data Access | ✅ Excellent | Returns structured data |
| `get_historical_stats` | Data Access | ✅ Excellent | Aggregations from DB |
| `get_time_series_data` | Data Access | ✅ Excellent | Raw data points |
| `search_knowledge_base` | Data Access | ✅ Excellent | Semantic search with citations |

**Pattern Analysis:**

**Data Access Tools (GOOD):**
```python
@tool("Get SolArk Status")
def get_energy_status() -> str:
    """Get current energy system status..."""
    try:
        status = get_solark_status()
        return format_status_summary(status)
    except Exception as e:
        return f"❌ Error: {str(e)}"
```
✅ Simple, focused, single responsibility
✅ Good error handling
✅ Clear documentation

**Routing Tools (PROBLEMATIC):**
```python
@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    """Route to Solar Controller agent..."""
    crew = create_energy_crew(query)  # ← Creates separate execution context
    result = crew.kickoff()
    return json.dumps({"response": str(result), ...})
```
⚠️ Too much responsibility (routing + execution)
⚠️ Context loss
⚠️ No access to parent crew's state

---

## Part 3: Root Cause Analysis

### 3.1 Why Agents Don't Use Context Properly

**Problem 1: System Capabilities Not Loaded**

**Root Cause:** The `get_context_files()` function exists but is never called.

**Impact:** Agents don't know:
- What system they're managing
- What hardware is available
- What capabilities they have

**Example Failure:**
```
User: "What system are you running on?"
Agent: "I'm managing a solar-powered off-grid system..." ← Generic, not specific
```

**Should be:**
```
Agent: "I'm managing CommandCenter V1.5 at Wildfire Ranch.
We have a SolArk 15K inverter, 48kWh LiFePO4 battery bank,
14.6kW solar array, and 5 Antminer S19 miners."
```

**Problem 2: Context Lost Between Manager and Specialists**

**Root Cause:** Manager's routing tools don't have access to conversation context.

**Code Path:**
1. API receives request with `context` → ✅ Loaded from DB
2. Manager crew created with `context` → ✅ Passed to task
3. Manager calls `route_to_solar_controller(query)` → ❌ Context not available
4. New crew created without context → ❌ Context lost

**Impact:** Specialists can't reference previous conversations.

**Example Failure:**
```
Turn 1:
User: "What's my battery level?"
Solar Controller: "Your battery is at 52%"

Turn 2 (same session):
User: "Is that good?"
Solar Controller: "What are you asking about?" ← Lost context
```

**Problem 3: Agents Must Search for Procedures**

**Root Cause:** Operational procedures stored in KB but not preloaded.

**Impact:** Agent has to make extra tool calls to find basic information.

**Example:**
```
User: "What's the minimum battery SOC?"
Agent: [calls search_knowledge_base("minimum battery SOC")]
Agent: "The minimum SOC is 30%"
```

**Should be:**
```
Agent: "The minimum SOC is 30% (system policy)"
```

### 3.2 What's Working Well

**✅ Data Access:**
- Excellent tool design
- Comprehensive data coverage
- Good error handling
- Historical data access is outstanding

**✅ Conversation Persistence:**
- All conversations stored
- Messages tracked with metadata
- Event logging comprehensive

**✅ CrewAI Usage:**
- Correct hierarchical structure
- Proper task/agent binding
- Sequential process appropriate

**✅ Agent Definitions:**
- Clear roles and goals
- Detailed backstories
- Verbose mode enabled for debugging

**✅ API Design:**
- Clean request/response models
- Good error handling
- Health checks comprehensive

---

## Part 4: Recommendations & Solutions

### 4.1 Quick Wins (Can Implement Immediately)

#### Fix #1: Load System Context into Agent Backstories

**File:** `railway/src/agents/solar_controller.py`

**Current (lines 217-246):**
```python
def create_energy_monitor_agent() -> Agent:
    return Agent(
        role="Energy Systems Monitor",
        backstory="""You are an expert energy systems analyst...
        You have access to a knowledge base...""",
        tools=[...],
    )
```

**Fixed:**
```python
def create_energy_monitor_agent() -> Agent:
    from ..tools.kb_search import get_context_files

    # Load system context ONCE when agent is created
    system_context = get_context_files()

    backstory = """You are an expert energy systems analyst specializing in
    solar + battery installations. You monitor a SolArk inverter system at
    Wildfire Ranch and help the homeowner understand their energy production,
    consumption, and battery status.

    SYSTEM CONTEXT (Always available):
    """

    if system_context:
        backstory += f"\n{system_context}\n"
    else:
        backstory += "\n[System context not available - use Search Knowledge Base tool for specifications]\n"

    backstory += """
    You have access to real-time monitoring tools and historical data.
    When asked about current status, use the real-time tools.
    When asked about thresholds or procedures, check your system context above first.
    """

    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems and provide clear, accurate status reports",
        backstory=backstory,
        tools=[...],
    )
```

**Benefits:**
- ✅ Agent knows system capabilities immediately
- ✅ No extra tool calls needed for basic info
- ✅ Consistent system knowledge across all interactions
- ⚠️ Watch for token limits (context loaded into every task)

**Token Budget Consideration:**
- System context: ~2,000-5,000 tokens (estimate)
- Agent backstory: ~500 tokens
- Task description: ~500 tokens
- Total overhead: ~3,000-6,000 tokens per request
- Claude 3.5 Sonnet context window: 200,000 tokens
- **Verdict:** Plenty of room

#### Fix #2: Pass Context Through Routing Tools

**Problem:** Manager's routing tools can't access conversation context.

**Solution Options:**

**Option A: Make routing tools context-aware (Complex)**

**Option B: Redesign routing to use direct function calls (Simpler)**

Current flow:
```
Manager (Crew 1) → Tool → Creates Crew 2 (no context)
```

Better flow:
```
Manager (Crew 1) → Returns routing decision → API creates Crew 2 with context
```

**File:** `railway/src/api/main.py` (lines 889-895)

**Current:**
```python
# Create manager crew to route query intelligently
crew = create_manager_crew(request.message, context)
result = crew.kickoff()
result_str = str(result)
```

**Fixed (Pseudo-code):**
```python
# Get routing decision from manager
manager_crew = create_manager_crew(request.message, context)
routing_decision = manager_crew.kickoff()

# Parse routing decision
decision = parse_routing_decision(routing_decision)

# Route to appropriate agent WITH context
if decision.agent == "Solar Controller":
    specialist_crew = create_energy_crew(request.message, context)
elif decision.agent == "Energy Orchestrator":
    specialist_crew = create_orchestrator_crew(request.message, context)
else:
    # Direct response from manager (greetings, etc.)
    return routing_decision

result = specialist_crew.kickoff()
```

**Benefits:**
- ✅ Context flows to specialists
- ✅ Cleaner separation of concerns
- ✅ Manager becomes pure router (no execution)

**Trade-offs:**
- ⚠️ Two crew executions per request (Manager + Specialist)
- ⚠️ More latency
- ⚠️ Need robust routing decision parser

#### Fix #3: Enhanced Agent System Prompts

**Add a dedicated "System Context" section to each agent's backstory:**

```python
SYSTEM_CONTEXT_TEMPLATE = """
═══════════════════════════════════════════
SYSTEM CONTEXT (CommandCenter V1.5)
═══════════════════════════════════════════

HARDWARE:
- SolArk 15K Inverter (15kW continuous, 20kW surge)
- 48kWh LiFePO4 Battery Bank (51.2V nominal)
- 14.6kW Solar Array (36x 405W panels)
- 5x Antminer S19 Miners (3,250W each, 16.25kW total)
- Multiple Shelly Plug S smart outlets

CAPABILITIES:
- Real-time monitoring via SolArk Cloud API
- Historical data analysis (PostgreSQL + TimescaleDB)
- Miner control via Shelly smart plugs
- Battery optimization algorithms
- Energy planning and forecasting

OPERATING POLICIES:
- Minimum Battery SOC: 30% (never go below)
- Safe Operating Range: 40-80%
- Grid Import: Avoid except emergencies
- Miner Priority: Run only with excess solar
- Battery Protection: Top priority

LIMITATIONS:
- Cannot control SolArk settings directly
- Cannot modify system configuration
- Miner control via Shelly plugs only
- No real-time weather data integration (yet)

═══════════════════════════════════════════
"""
```

**Benefits:**
- ✅ Agents know their exact capabilities
- ✅ Clear operating boundaries
- ✅ Consistent system knowledge
- ✅ Reduces hallucinations

### 4.2 Medium-Term Improvements

#### Improvement #1: Implement CrewAI Hierarchical Process

**Current:** Each agent in its own crew (isolated)

**Better:** Single crew with hierarchical delegation

**File:** Create new `railway/src/agents/unified_crew.py`

```python
from crewai import Agent, Crew, Task, Process

def create_unified_crew(query: str, context: str = "") -> Crew:
    """
    Create a unified crew with manager and specialists.

    Uses CrewAI's hierarchical process for proper delegation
    """

    # Create all agents
    manager = create_manager_agent()
    solar_controller = create_energy_monitor_agent()
    orchestrator = create_energy_orchestrator()

    # Create task for manager
    task = Task(
        description=f"""Analyze this query and delegate to the appropriate specialist:

        Query: {query}

        {context}

        Available specialists:
        - Solar Controller: Real-time status queries
        - Energy Orchestrator: Planning and optimization

        Delegate to the specialist or answer directly if appropriate.
        """,
        expected_output="Answer to the user's question",
        agent=manager,
    )

    return Crew(
        agents=[manager, solar_controller, orchestrator],
        tasks=[task],
        process=Process.hierarchical,  # ← Key change
        manager_llm="gpt-4",  # Manager uses GPT-4 for routing
        verbose=True,
    )
```

**Benefits:**
- ✅ All agents share context automatically
- ✅ Native CrewAI delegation (more efficient)
- ✅ Manager can coordinate multi-agent responses
- ⚠️ Requires testing (different execution model)

#### Improvement #2: Smart Context Loading

**Instead of loading ALL context files, load selectively based on query:**

```python
def get_relevant_context(query: str, max_tokens: int = 2000) -> str:
    """
    Load only relevant context based on query.

    Uses semantic similarity to find most relevant context files.
    """
    from ..kb.sync import generate_embeddings
    from ..utils.db import get_connection, query_all

    # Generate query embedding
    query_embedding = generate_embeddings([query])[0]

    with get_connection() as conn:
        # Find most similar context files
        context_docs = query_all(
            conn,
            """
            SELECT title, full_content,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM kb_documents
            WHERE is_context_file = TRUE
            ORDER BY similarity DESC
            LIMIT 3
            """,
            (query_embedding,),
            as_dict=True
        )

    # Build context string (truncate if needed)
    context = "RELEVANT SYSTEM CONTEXT:\n\n"
    tokens_used = 0

    for doc in context_docs:
        doc_tokens = len(doc['full_content']) // 4
        if tokens_used + doc_tokens > max_tokens:
            break

        context += f"## {doc['title']}\n{doc['full_content']}\n\n"
        tokens_used += doc_tokens

    return context
```

**Benefits:**
- ✅ Only loads relevant context
- ✅ Token-efficient
- ✅ Scales better with more docs

#### Improvement #3: Context Caching

**Anthropic's Context Caching (Available in API):**

```python
# Use Claude's prompt caching for system context
# System context is cached and reused across requests

import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    system=[
        {
            "type": "text",
            "text": SYSTEM_CONTEXT,  # Loaded once
            "cache_control": {"type": "ephemeral"}  # ← Cached for 5 min
        },
        {
            "type": "text",
            "text": f"Current conversation context:\n{context}"
        }
    ],
    messages=[{"role": "user", "content": query}]
)
```

**Benefits:**
- ✅ 90% cost reduction for cached tokens
- ✅ Faster response times
- ✅ Can include more context without cost penalty

**Note:** CrewAI supports Claude models, but need to verify caching support.

### 4.3 Long-Term Architecture Changes

#### Change #1: Separate Configuration from Code

**Create:** `railway/src/config/system_context.py`

```python
"""
System context configuration.

This file defines the system capabilities, hardware specs,
and operating policies that agents need to know.

Updated: Match your actual hardware setup
"""

SYSTEM_HARDWARE = {
    "inverter": {
        "model": "SolArk 15K",
        "continuous_power": "15kW",
        "surge_power": "20kW",
        "type": "Hybrid inverter/charger"
    },
    "battery": {
        "capacity": "48kWh",
        "chemistry": "LiFePO4",
        "voltage": "51.2V nominal",
        "manufacturer": "Custom bank"
    },
    "solar": {
        "total_capacity": "14.6kW",
        "panel_count": 36,
        "panel_wattage": "405W each"
    },
    "miners": {
        "count": 5,
        "model": "Antminer S19",
        "power_each": "3.25kW",
        "total_power": "16.25kW"
    }
}

SYSTEM_CAPABILITIES = {
    "monitoring": [
        "Real-time battery SOC",
        "Real-time solar production",
        "Real-time load consumption",
        "Grid import/export status",
        "Historical data analysis"
    ],
    "control": [
        "Bitcoin miner on/off (via Shelly plugs)",
        "Query energy planning recommendations"
    ],
    "cannot_do": [
        "Cannot control SolArk inverter settings",
        "Cannot modify battery charge parameters",
        "Cannot control individual appliances (except miners)",
        "Cannot access real-time weather data"
    ]
}

OPERATING_POLICIES = {
    "battery_soc": {
        "critical_minimum": 30,
        "safe_minimum": 40,
        "safe_maximum": 80,
        "absolute_maximum": 100
    },
    "grid_usage": {
        "policy": "minimize",
        "emergency_only": True
    },
    "miner_operation": {
        "priority": "excess_solar_only",
        "minimum_battery_soc": 50
    }
}

def get_system_context_text() -> str:
    """Generate formatted system context for agent backstories."""
    # Format the above dicts into readable text
    pass
```

#### Change #2: Agent Factory Pattern

**Create:** `railway/src/agents/factory.py`

```python
"""
Agent factory for creating agents with consistent context loading.
"""

from typing import Optional
from crewai import Agent
from ..config.system_context import get_system_context_text
from ..tools.kb_search import get_context_files

def create_agent(
    role: str,
    goal: str,
    backstory_template: str,
    tools: list,
    load_system_context: bool = True,
    load_kb_context: bool = False
) -> Agent:
    """
    Create an agent with consistent context loading.

    Args:
        role: Agent role
        goal: Agent goal
        backstory_template: Template with {system_context} placeholder
        tools: List of tools
        load_system_context: Load SYSTEM_HARDWARE/POLICIES (default: True)
        load_kb_context: Load full KB context files (default: False)
    """

    context_parts = []

    if load_system_context:
        context_parts.append(get_system_context_text())

    if load_kb_context:
        kb_context = get_context_files()
        if kb_context:
            context_parts.append(kb_context)

    full_context = "\n\n".join(context_parts)
    backstory = backstory_template.format(system_context=full_context)

    return Agent(
        role=role,
        goal=goal,
        backstory=backstory,
        tools=tools,
        verbose=True,
        allow_delegation=False
    )
```

#### Change #3: Unified Context Management Service

**Create:** `railway/src/services/context_manager.py`

```python
"""
Centralized context management service.

Handles loading, caching, and formatting of all context types.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ContextBundle:
    """Bundle of context for an agent."""
    system_context: str  # Hardware, capabilities, policies
    conversation_context: str  # Recent chat history
    kb_context: Optional[str]  # Knowledge base docs (if needed)
    loaded_at: datetime

    @property
    def is_stale(self, ttl_minutes: int = 60) -> bool:
        """Check if context needs refreshing."""
        return datetime.now() - self.loaded_at > timedelta(minutes=ttl_minutes)

class ContextManager:
    """Manages agent context lifecycle."""

    def __init__(self):
        self._cache: Dict[str, ContextBundle] = {}

    def get_context_for_agent(
        self,
        agent_role: str,
        query: str,
        conversation_id: Optional[str] = None,
        include_kb: bool = False
    ) -> ContextBundle:
        """
        Get complete context bundle for an agent.

        Uses caching to avoid redundant loads.
        """
        cache_key = f"{agent_role}:{conversation_id}"

        # Check cache
        if cache_key in self._cache:
            bundle = self._cache[cache_key]
            if not bundle.is_stale:
                return bundle

        # Load fresh context
        from ..config.system_context import get_system_context_text
        from ..utils.conversation import get_conversation_context
        from ..tools.kb_search import get_relevant_context

        system = get_system_context_text()
        conversation = get_conversation_context(agent_role, conversation_id)
        kb = get_relevant_context(query) if include_kb else None

        bundle = ContextBundle(
            system_context=system,
            conversation_context=conversation,
            kb_context=kb,
            loaded_at=datetime.now()
        )

        self._cache[cache_key] = bundle
        return bundle

    def format_for_backstory(self, bundle: ContextBundle) -> str:
        """Format context bundle for agent backstory."""
        parts = [bundle.system_context]

        if bundle.conversation_context:
            parts.append(f"\nRECENT CONVERSATIONS:\n{bundle.conversation_context}")

        if bundle.kb_context:
            parts.append(f"\nRELEVANT DOCUMENTATION:\n{bundle.kb_context}")

        return "\n\n".join(parts)
```

---

## Part 5: Testing Plan

### 5.1 Diagnostic Tests

#### Test 1: System Knowledge
```python
# Test if agent knows what system it's running on
query = "What system are you managing? What hardware do you have?"
expected_keywords = ["SolArk", "48kWh", "14.6kW", "Antminer", "Wildfire Ranch"]

result = ask_agent(query)
for keyword in expected_keywords:
    assert keyword in result, f"Missing: {keyword}"
```

#### Test 2: Context Continuity
```python
# Test multi-turn conversation
session_id = create_session()

response1 = ask_agent("What's my battery level?", session_id)
assert "52%" in response1  # or whatever current level is

response2 = ask_agent("Is that good?", session_id)
assert "52" in response2 or "battery" in response2.lower()
# Should reference the 52% from previous turn
```

#### Test 3: Policy Knowledge
```python
# Test if agent knows policies without searching
query = "What's the minimum battery SOC I should maintain?"
result = ask_agent(query)

# Agent should answer directly (not "let me search...")
assert "30%" in result or "40%" in result
# Should NOT contain "searching knowledge base..."
assert "searching" not in result.lower()
```

#### Test 4: Capability Boundaries
```python
# Test if agent knows what it CANNOT do
query = "Can you change my inverter settings?"
result = ask_agent(query)

assert "cannot" in result.lower() or "unable" in result.lower()
# Should explicitly state limitations
```

### 5.2 Performance Tests

```python
# Test token usage before/after context loading
import tiktoken

def count_tokens(text: str) -> int:
    enc = tiktoken.encoding_for_model("gpt-3.5-turbo")
    return len(enc.encode(text))

# Before optimization
agent_without_context = create_energy_monitor_agent_v1()
tokens_before = count_tokens(agent_without_context.backstory)

# After optimization
agent_with_context = create_energy_monitor_agent_v2()
tokens_after = count_tokens(agent_with_context.backstory)

print(f"Tokens before: {tokens_before}")
print(f"Tokens after: {tokens_after}")
print(f"Increase: {tokens_after - tokens_before} tokens")

# Acceptable if under 200k token limit
assert tokens_after < 200000, "Exceeds Claude context window"
```

### 5.3 Integration Tests

```python
# Test full flow: API → Manager → Specialist → Response

def test_full_routing_with_context():
    """Test that context flows through entire system."""

    # Setup
    conversation_id = create_conversation("Energy Systems Monitor")
    add_message(conversation_id, "user", "What's my battery level?")
    add_message(conversation_id, "assistant", "Your battery is at 52%")

    # Test
    response = post_to_api({
        "message": "Is that good for running miners?",
        "session_id": conversation_id
    })

    # Assertions
    assert "52" in response['response'] or "battery" in response['response'].lower()
    assert "miner" in response['response'].lower()
    # Should reference both battery level AND miners (context + current query)
```

---

## Part 6: Migration Path

### Phase 1: Foundation (Week 1)
**Goal:** Load system context without breaking anything

**Tasks:**
1. Create `railway/src/config/system_context.py` with hardware/policy definitions
2. Update `get_context_files()` to return formatted text
3. Modify agent creation functions to call `get_context_files()`
4. Test that agents receive context
5. Deploy to staging
6. Run diagnostic tests

**Risk:** Low - Additive changes only

### Phase 2: Context Flow (Week 2)
**Goal:** Fix context loss between Manager and Specialists

**Tasks:**
1. Refactor routing tools to NOT create new crews
2. Update API to handle routing decisions explicitly
3. Pass context to specialist crews
4. Test multi-turn conversations
5. Deploy to staging
6. Run integration tests

**Risk:** Medium - Changes execution flow

### Phase 3: Optimization (Week 3)
**Goal:** Improve performance and token usage

**Tasks:**
1. Implement smart context loading (query-relevant only)
2. Add context caching
3. Measure token usage improvements
4. A/B test with and without optimizations
5. Deploy to production
6. Monitor metrics

**Risk:** Low - Performance improvements

### Phase 4: Architecture Refinement (Week 4)
**Goal:** Clean up and establish patterns

**Tasks:**
1. Create `ContextManager` service
2. Implement agent factory pattern
3. Refactor all agents to use factory
4. Update documentation
5. Create developer guide for adding new agents

**Risk:** Low - Refactoring only

---

## Part 7: Success Metrics

### Before vs After

| Metric | Before | Target After | Measure |
|--------|--------|-------------|---------|
| Agent knows system | ❌ No | ✅ Yes | Test 1 pass rate |
| Context continuity | ❌ 0% | ✅ 95%+ | Test 2 pass rate |
| Policy knowledge | ⚠️ Requires search | ✅ Immediate | Tool calls per query |
| Response accuracy | ⚠️ 70%? | ✅ 90%+ | User satisfaction |
| Avg response time | ~2-3s | ~2-3s | Latency p95 |
| Token usage | ~3k/query | ~5k/query | Cost monitoring |

### Key Performance Indicators (KPIs)

1. **Context Accuracy:** % of responses that include relevant system info
2. **Context Continuity:** % of multi-turn conversations where context is maintained
3. **First-Response Accuracy:** % of queries answered correctly without additional searches
4. **User Satisfaction:** Qualitative feedback (does agent seem knowledgeable?)
5. **Cost Efficiency:** Average tokens per query (should increase but remain manageable)

---

## Conclusion

### What We Learned

1. **Context System:** Exists in database but isn't loaded into agents
2. **CrewAI Usage:** Mostly correct, but routing pattern loses context
3. **Root Cause:** Design gap, not implementation bug
4. **Fix Complexity:** Low to medium (mostly config and data flow changes)

### What's Working

- Data access tools: Excellent
- Conversation storage: Solid
- KB infrastructure: Ready to use
- Agent definitions: Well-structured
- API design: Clean and extensible

### What Needs Fixing

Priority order:
1. **P0:** Load system context into agent backstories (Quick win)
2. **P0:** Fix context loss in routing (Critical for UX)
3. **P1:** Optimize token usage with smart loading
4. **P2:** Refactor to unified crew architecture
5. **P3:** Implement caching and performance optimizations

### Next Steps

1. Review this document with the team
2. Validate assumptions with quick prototype
3. Choose implementation approach (Quick fixes vs. Refactor)
4. Create detailed implementation tickets
5. Set up staging environment for testing
6. Begin Phase 1 implementation

---

## Appendix A: Code Examples

### Example 1: Enhanced Agent Creation (Before/After)

**Before (Current):**
```python
def create_energy_monitor_agent() -> Agent:
    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems",
        backstory="""You are an expert energy systems analyst.
        You have access to a knowledge base with detailed documentation.""",
        tools=[get_energy_status, search_knowledge_base],
        verbose=True,
    )
```

**After (Proposed):**
```python
def create_energy_monitor_agent() -> Agent:
    from ..tools.kb_search import get_context_files

    system_context = get_context_files()

    backstory = f"""You are an expert energy systems analyst specializing in
    solar + battery installations at Wildfire Ranch.

    {system_context}

    You have access to real-time monitoring tools and can answer questions
    about current status, historical trends, and system capabilities.
    When asked about thresholds or procedures, refer to your system context above.
    """

    return Agent(
        role="Energy Systems Monitor",
        goal="Monitor solar, battery, and energy systems and provide accurate status reports",
        backstory=backstory,
        tools=[get_energy_status, get_historical_stats, search_knowledge_base],
        verbose=True,
    )
```

### Example 2: Context-Aware Routing

**Before (Current):**
```python
@tool("Route to Solar Controller")
def route_to_solar_controller(query: str) -> str:
    crew = create_energy_crew(query)  # No context
    result = crew.kickoff()
    return json.dumps({"response": str(result), ...})
```

**After (Proposed - Option A):**
```python
# In manager.py
def create_routing_tools(conversation_context: str):
    """Create routing tools with access to conversation context."""

    @tool("Route to Solar Controller")
    def route_to_solar_controller(query: str) -> str:
        # Has access to conversation_context from closure
        crew = create_energy_crew(query, conversation_context)
        result = crew.kickoff()
        return json.dumps({"response": str(result), ...})

    return [route_to_solar_controller, ...]

# In create_manager_agent()
def create_manager_agent(context: str = "") -> Agent:
    tools = create_routing_tools(context)  # Create tools with context
    return Agent(..., tools=tools, ...)
```

**After (Proposed - Option B - Cleaner):**
```python
# Remove routing tools entirely
# Manager just returns routing decision

# In api/main.py
manager_crew = create_manager_crew(request.message, context)
routing_result = manager_crew.kickoff()

# Parse decision
routing_decision = parse_manager_response(routing_result)

if routing_decision.route_to == "Solar Controller":
    specialist_crew = create_energy_crew(
        query=request.message,
        conversation_context=context
    )
    result = specialist_crew.kickoff()
elif routing_decision.route_to == "Energy Orchestrator":
    specialist_crew = create_orchestrator_crew(
        query=request.message,
        context=context
    )
    result = specialist_crew.kickoff()
else:
    # Manager handled it directly
    result = routing_result

return result
```

---

## Appendix B: Architecture Diagrams

### Current Architecture (Simplified)

```
┌─────────────────────────────────────────────────────────────────┐
│                         API REQUEST                              │
│                    /ask {"message": "..."}                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                  [Load conversation context from DB]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MANAGER CREW (Crew #1)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Manager Agent                                            │  │
│  │  - Receives: query + conversation_context                │  │
│  │  - Calls tool: route_to_solar_controller(query)          │  │
│  │    └─> Tool creates NEW crew WITHOUT context ❌          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                      [Tool execution]
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 SOLAR CONTROLLER CREW (Crew #2)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Solar Controller Agent                                   │  │
│  │  - Receives: query only                                   │  │
│  │  - Missing: conversation_context ❌                       │  │
│  │  - Missing: system_context ❌                             │  │
│  │  - Calls tools: get_energy_status, search_kb             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Return response to Manager]
                              ↓
                    [Manager returns to API]
                              ↓
                         [API returns to user]
```

### Proposed Architecture (With Fixes)

```
┌─────────────────────────────────────────────────────────────────┐
│                         API REQUEST                              │
│                    /ask {"message": "..."}                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
              [Load conversation context from DB]
              [Load system context from KB]  ← NEW
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    MANAGER CREW (Crew #1)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Manager Agent                                            │  │
│  │  - Receives: query + conversation_context + system_context│  │
│  │  - Returns: Routing decision                             │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [API parses decision]  ← NEW
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                 SOLAR CONTROLLER CREW (Crew #2)                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Solar Controller Agent                                   │  │
│  │  - Receives: query + conversation_context + system_context│  │
│  │  - Has: Full context ✅                                   │  │
│  │  - Backstory includes: Hardware specs, policies ✅        │  │
│  │  - Calls tools: get_energy_status (already knows basics)  │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
                    [Return response to API]
                              ↓
                         [API returns to user]
```

---

## Appendix C: Glossary

**Context (General):** Information that helps the agent understand the current situation

**System Context:** Static information about hardware, capabilities, and policies

**Conversation Context:** Previous messages in the current and recent conversations

**KB Context:** Relevant documentation retrieved from knowledge base

**Backstory:** CrewAI's term for the agent's personality/knowledge section

**Task Description:** The specific instructions for what the agent should do

**Crew:** CrewAI's execution unit (agents + tasks + process)

**Process.sequential:** Tasks execute one after another

**Process.hierarchical:** Manager agent delegates to specialists

**Tool:** Function that an agent can call to access data or perform actions

**Delegation:** Manager agent passing work to a specialist agent

**Routing:** Manager agent deciding which specialist should handle a query

**is_context_file:** Database flag marking important documents to preload

**get_context_files():** Function to retrieve all context files from KB

---

**END OF DOCUMENT**
