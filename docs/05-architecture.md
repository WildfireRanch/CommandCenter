# Phase 1.4: CommandCenter Architecture Design

**Date:** October 3, 2025  
**Project:** CommandCenter V1  
**Phase:** Discovery - Architecture Design  
**Previous Phases:** Audit ✅ | Requirements ✅ | Port Plan ✅

---

## Executive Summary

CommandCenter V1 is a **CrewAI-based energy orchestration system** deployed across Vercel (frontend/MCP) and Railway (backend/agents). The architecture prioritizes:

1. **Reliability** - Replace fragile custom orchestration with proven CrewAI frameworkgit 
2. **Maintainability** - Clear separation of concerns, understandable by solo developer
3. **Extensibility** - Foundation supports V2 features without major refactor
4. **Safety** - Multiple layers of validation before hardware commands execute

**Core Innovation:** MCP server exposes CrewAI agents as tools to AI clients (Claude, Cursor, etc.) while maintaining full conversational context and safety guardrails.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   AI Clients                             │
│          (Claude, Cursor, Custom Apps)                   │
└────────────────────┬────────────────────────────────────┘
                     │ MCP Protocol (SSE/HTTP)
┌────────────────────▼────────────────────────────────────┐
│              Vercel (MCP Server)                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Next.js App Router (App Directory)              │   │
│  │  - /api/mcp/route.ts (MCP Handler)               │   │
│  │  - Streamable HTTP transport                     │   │
│  │  - Tool exposure to AI clients                   │   │
│  └──────────────────┬───────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │ HTTPS API Calls
┌─────────────────────▼───────────────────────────────────┐
│           Railway (CrewAI Backend)                       │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI Application                             │   │
│  │  - /api/crew/execute (Run crew with task)        │   │
│  │  - /api/tools/* (Individual tool endpoints)      │   │
│  │  - /api/status (System status)                   │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  CommandCenter Crew (Main)                       │   │
│  │  ┌────────────────────────────────────────────┐  │   │
│  │  │  1. Conversation Agent                     │  │   │
│  │  │     - Parse user intent                    │  │   │
│  │  │     - Ask clarifying questions             │  │   │
│  │  │     - Confirm destructive actions          │  │   │
│  │  └────────────────┬───────────────────────────┘  │   │
│  │                   │ delegates to                  │   │
│  │  ┌────────────────▼───────────────────────────┐  │   │
│  │  │  2. Energy Orchestrator Agent              │  │   │
│  │  │     - Analyze system state                 │  │   │
│  │  │     - Make optimization decisions          │  │   │
│  │  │     - Explain reasoning                    │  │   │
│  │  └────────────────┬───────────────────────────┘  │   │
│  │                   │ uses                          │   │
│  │  ┌────────────────▼───────────────────────────┐  │   │
│  │  │  3. Hardware Control Agent                 │  │   │
│  │  │     - Execute tool calls with validation   │  │   │
│  │  │     - Apply safety guardrails              │  │   │
│  │  │     - Log all actions                      │  │   │
│  │  └────────────────┬───────────────────────────┘  │   │
│  └───────────────────┼──────────────────────────────┘   │
│                      │ calls                            │
│  ┌───────────────────▼──────────────────────────────┐   │
│  │  CrewAI Tools Layer                              │   │
│  │  - solark_tool (SolArk inverter control)         │   │
│  │  - shelly_tool (Relay/switch control)            │   │
│  │  - miner_tool (Bitcoin miner management)         │   │
│  │  - victron_tool (Victron system queries)         │   │
│  │  - nodered_tool (Flow triggers)                  │   │
│  │  - database_tool (PostgreSQL queries)            │   │
│  └──────────────────┬───────────────────────────────┘   │
└─────────────────────┼───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
┌────────▼────────┐    ┌───────────▼──────────┐
│  PostgreSQL     │    │  Hardware/Services   │
│  - Telemetry    │    │  - SolArk inverter   │
│  - Action log   │    │  - Shelly devices    │
│  - KB index     │    │  - Bitcoin miners    │
│  - Preferences  │    │  - Victron Cerbo GX  │
└─────────────────┘    │  - Node-RED          │
                       └──────────────────────┘

┌────────────────────────────────────────────────┐
│  Supporting Services (Railway)                 │
│  - Knowledge Base (Google Docs sync)           │
│  - Memory System (Session + Action logging)    │
│  - Scheduler (Cron jobs)                       │
└────────────────────────────────────────────────┘
```

---

## Component Deep Dive

### 1. Vercel Layer (MCP Server)

**Purpose:** Expose CrewAI capabilities via MCP protocol to AI clients

**Technology Stack:**
- Next.js 14+ (App Router)
- Vercel MCP Handler (`@vercel/mcp-handler`)
- Vercel AI SDK
- Fluid Compute enabled

**File Structure:**
```
vercel/
├── app/
│   ├── api/
│   │   └── mcp/
│   │       └── route.ts          # MCP endpoint
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Landing page (optional)
├── lib/
│   ├── mcp/
│   │   ├── tools.ts              # Tool definitions for MCP
│   │   └── client.ts             # Railway API client
│   └── config.ts                 # Configuration
├── public/                       # Static assets
├── package.json
├── tsconfig.json
└── vercel.json                   # Deployment config
```

**MCP Tools Exposed:**
```typescript
// lib/mcp/tools.ts
export const mcpTools = [
  {
    name: "execute_energy_task",
    description: "Execute an energy management task using the CommandCenter crew",
    parameters: {
      task: "string - Natural language description of task",
      confirm_required: "boolean - Whether to require confirmation"
    }
  },
  {
    name: "query_system_status",
    description: "Get current status of energy systems",
    parameters: {}
  },
  {
    name: "review_action_history",
    description: "Review recent actions taken by the system",
    parameters: {
      hours: "number - How many hours of history to retrieve"
    }
  }
]
```

**Key Routes:**
- `GET /api/mcp` - MCP endpoint (SSE for streaming)
- `POST /api/mcp` - Execute MCP tool calls
- `GET /api/health` - Health check

**Environment Variables (Vercel):**
```env
RAILWAY_API_URL=https://commandcenter-production.up.railway.app
RAILWAY_API_KEY=<secret>
OPENAI_API_KEY=<secret>
```

**Deployment:**
```bash
# From commandcenter/vercel/
vercel deploy --prod
```

**Why Vercel for MCP:**
- ✅ Global edge network (low latency)
- ✅ Serverless functions (auto-scaling)
- ✅ Fluid Compute (90% cost savings)
- ✅ Built-in SSL/HTTPS
- ✅ Zero-config deployment

---

### 2. Railway Layer (CrewAI Backend)

**Purpose:** Run CrewAI agents, tools, and supporting services

**Technology Stack:**
- Python 3.10+
- CrewAI framework
- FastAPI (API server)
- PostgreSQL (data persistence)
- Uvicorn (ASGI server)

**File Structure:**
```
railway/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── conversation.py       # Conversation Agent
│   │   ├── orchestrator.py       # Energy Orchestrator
│   │   └── hardware.py           # Hardware Control Agent
│   ├── crews/
│   │   ├── __init__.py
│   │   └── main_crew.py          # CommandCenter main crew
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── solark.py             # SolArk tool
│   │   ├── shelly.py             # Shelly tool
│   │   ├── miners.py             # Miner tool
│   │   ├── victron.py            # Victron tool
│   │   ├── nodered.py            # Node-RED tool
│   │   └── database.py           # Database tool
│   ├── integrations/
│   │   ├── __init__.py
│   │   ├── google_docs.py        # Google Docs sync
│   │   └── google_auth.py        # OAuth
│   ├── kb/
│   │   ├── __init__.py
│   │   ├── indexer.py            # Document indexing
│   │   └── retriever.py          # Retrieval
│   ├── memory/
│   │   ├── __init__.py
│   │   └── session.py            # Session memory
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.sql            # Database schema
│   │   └── models.py             # SQLAlchemy models
│   ├── api/
│   │   ├── __init__.py
│   │   ├── main.py               # FastAPI app
│   │   └── routes/
│   │       ├── crew.py           # /api/crew/*
│   │       ├── tools.py          # /api/tools/*
│   │       └── status.py         # /api/status
│   └── config/
│       ├── __init__.py
│       └── settings.py           # Configuration
├── tests/                        # Test suite
├── alembic/                      # DB migrations
├── requirements.txt
├── Dockerfile
├── railway.json                  # Railway config
└── README.md
```

**API Endpoints:**
```python
# FastAPI routes
POST   /api/crew/execute          # Execute crew with task
GET    /api/crew/status/{task_id} # Get task status
POST   /api/tools/solark          # Direct tool call
POST   /api/tools/shelly          # Direct tool call
POST   /api/tools/miners          # Direct tool call
GET    /api/status                # System status
GET    /api/status/hardware       # Hardware status
GET    /api/history               # Action history
POST   /api/kb/sync               # Trigger KB sync
GET    /api/kb/search             # Search KB
```

**Environment Variables (Railway):**
```env
DATABASE_URL=postgresql://...
OPENAI_API_KEY=<secret>
GOOGLE_DOCS_CREDENTIALS=<json>
SOLARK_HOST=192.168.1.100
VICTRON_VRM_TOKEN=<secret>
REDIS_URL=redis://...
```

**Railway Services:**
```yaml
# railway.json
{
  "services": [
    {
      "name": "commandcenter-api",
      "source": {
        "repo": "wildfireranch/commandcenter",
        "directory": "railway"
      },
      "build": {
        "builder": "DOCKERFILE",
        "dockerfilePath": "Dockerfile"
      },
      "deploy": {
        "numReplicas": 1,
        "restartPolicyType": "ON_FAILURE"
      }
    },
    {
      "name": "postgresql",
      "source": {
        "image": "postgres:15"
      }
    },
    {
      "name": "redis",
      "source": {
        "image": "redis:7"
      }
    }
  ]
}
```

**Why Railway for Backend:**
- ✅ Pay-per-use (idle = cheap)
- ✅ Built-in PostgreSQL/Redis
- ✅ Vertical autoscaling
- ✅ Simple deployment
- ✅ Good for long-running processes

---

### 3. CrewAI Crew Structure

**Main Crew: `CommandCenterCrew`**

```python
# src/crews/main_crew.py
from crewai import Crew, Agent, Task
from src.agents.conversation import conversation_agent
from src.agents.orchestrator import energy_orchestrator
from src.agents.hardware import hardware_control_agent

class CommandCenterCrew:
    def __init__(self):
        self.crew = Crew(
            agents=[
                conversation_agent,
                energy_orchestrator,
                hardware_control_agent
            ],
            tasks=[],  # Tasks created dynamically
            process="sequential",  # Tasks run in order
            memory=True,  # Enable session memory
            verbose=True
        )
    
    def execute(self, user_task: str) -> dict:
        """Execute a user task through the crew"""
        
        # Create task for conversation agent
        main_task = Task(
            description=f"User request: {user_task}",
            agent=conversation_agent,
            expected_output="Completed action with confirmation"
        )
        
        # Execute crew
        result = self.crew.kickoff(tasks=[main_task])
        
        return {
            "success": True,
            "result": result,
            "actions_taken": self._extract_actions(result)
        }
```

**Agent Hierarchy:**

```
User Request
    ↓
Conversation Agent (Entry point)
    │
    ├─→ Clarify intent
    ├─→ Validate input
    └─→ Delegate to Orchestrator
            ↓
Energy Orchestrator (Decision maker)
    │
    ├─→ Query system state
    ├─→ Analyze conditions
    ├─→ Formulate plan
    ├─→ Explain reasoning
    └─→ Delegate to Hardware Control
            ↓
Hardware Control Agent (Executor)
    │
    ├─→ Validate action safety
    ├─→ Check prerequisites
    ├─→ Execute tool call
    ├─→ Verify result
    └─→ Log action
            ↓
        Result returned to user
```

---

### 4. Agent Definitions

#### Agent 1: Conversation Agent

```python
# src/agents/conversation.py
from crewai import Agent
from crewai_tools import tool

conversation_agent = Agent(
    role="User Interface Specialist",
    goal="Understand user intent and facilitate natural conversation",
    backstory="""You are a friendly and helpful interface between the user and 
    the CommandCenter energy system. You excel at understanding natural language 
    requests, asking clarifying questions when needed, and explaining complex 
    technical operations in simple terms. Safety is your priority - you always 
    confirm destructive actions before executing.""",
    
    verbose=True,
    allow_delegation=True,  # Can delegate to other agents
    
    tools=[],  # No direct tools, delegates to orchestrator
)
```

**Responsibilities:**
- Parse user natural language input
- Ask clarifying questions
- Confirm destructive actions
- Explain system responses in user-friendly language
- Handle conversation context
- Delegate to Energy Orchestrator

**Example Interactions:**
```
User: "Turn off the miners"
Conversation Agent: "I'll pause the Bitcoin miners. They're currently running. 
                     This will take about 30 seconds. Shall I proceed?"

User: "yes"
Conversation Agent: → delegates to Energy Orchestrator
```

---

#### Agent 2: Energy Orchestrator

```python
# src/agents/orchestrator.py
from crewai import Agent
from src.tools.database import query_system_status
from src.tools.victron import get_battery_soc

energy_orchestrator = Agent(
    role="Energy System Optimization Specialist",
    goal="Optimize off-grid energy usage to maximize battery health and minimize costs",
    backstory="""You are an expert in off-grid energy systems with deep knowledge 
    of battery management, solar production, and load balancing. You analyze system 
    state (SOC, weather, time, loads) and make intelligent decisions about when to 
    charge, discharge, run loads, and preserve battery capacity. You always explain 
    your reasoning and defer to user preferences.""",
    
    verbose=True,
    allow_delegation=True,  # Can delegate to Hardware Control
    
    tools=[
        query_system_status,  # Get current state
        get_battery_soc,      # Check battery level
    ],
)
```

**Responsibilities:**
- Analyze system state (SOC, grid, weather, time)
- Make optimization decisions
- Plan multi-step actions
- Explain reasoning to user
- Learn from user corrections
- Delegate execution to Hardware Control Agent

**Example Decision Flow:**
```python
# Orchestrator internal reasoning
1. Query current SOC → 45%
2. Check time → 6pm (peak rates)
3. Check miners → Running
4. Check weather forecast → Clear tomorrow (good solar)

Decision: Pause miners to preserve battery
Reasoning: "SOC is below 50% during peak hours, and tomorrow's 
            forecast shows good solar. Pausing miners now preserves 
            battery for evening loads and we can resume tomorrow 
            when solar production is strong."

→ Delegates to Hardware Control: "pause_miners"
```

---

#### Agent 3: Hardware Control Agent

```python
# src/agents/hardware.py
from crewai import Agent
from src.tools.solark import set_solark_mode
from src.tools.shelly import control_shelly
from src.tools.miners import control_miners
from src.tools.victron import query_victron
from src.tools.nodered import trigger_flow
from src.tools.database import log_action

hardware_control_agent = Agent(
    role="Hardware Control & Safety Specialist",
    goal="Execute hardware commands safely and reliably with comprehensive validation",
    backstory="""You are a meticulous hardware control specialist responsible for 
    the final execution of commands to physical systems. You validate every action 
    before execution, maintain detailed logs, and have multiple safety mechanisms 
    to prevent unintended consequences. You never skip validation steps.""",
    
    verbose=True,
    allow_delegation=False,  # Final executor, doesn't delegate
    
    tools=[
        set_solark_mode,
        control_shelly,
        control_miners,
        query_victron,
        trigger_flow,
        log_action,
    ],
)
```

**Responsibilities:**
- Execute tool calls to hardware
- Validate action safety before execution
- Apply safety guardrails (dry-run, confirmation)
- Verify action completed successfully
- Log all actions to database
- Handle errors gracefully
- Rollback failed actions when possible

**Safety Checklist (executed for every action):**
```python
1. Validate prerequisites
   - Is system in correct state?
   - Are required services reachable?
   
2. Check safety limits
   - Would this exceed safe SOC limits?
   - Is this action allowed in current mode?
   
3. Dry-run (if available)
   - Simulate action without executing
   
4. Execute action
   - Send command to hardware
   
5. Verify result
   - Check action completed as expected
   
6. Log action
   - Record timestamp, agent, action, result, user
   
7. Handle errors
   - Rollback if possible
   - Alert user if failed
```

---

### 5. Tool Layer Architecture

Each tool follows a standard pattern:

```python
# src/tools/template.py
from crewai_tools import tool
from typing import Literal
import logging

logger = logging.getLogger(__name__)

@tool("Tool name that describes what it does")
def tool_name(
    param1: str,
    param2: Literal["option1", "option2"] = "option1",
    dry_run: bool = False,
    confirm: bool = True
) -> dict:
    """
    Detailed description of what this tool does.
    
    Args:
        param1: Description of parameter
        param2: Description with allowed values
        dry_run: If True, simulate without executing
        confirm: If True, requires user confirmation
    
    Returns:
        dict: {
            success: bool,
            message: str,
            data: dict,  # Tool-specific data
            action_logged: bool
        }
    
    Raises:
        ValueError: If parameters invalid
        ConnectionError: If service unreachable
    """
    
    # 1. Validate inputs
    if not param1:
        raise ValueError("param1 is required")
    
    # 2. Dry-run mode
    if dry_run:
        logger.info(f"DRY RUN: Would execute {tool_name} with {param1}")
        return {
            "success": True,
            "message": f"DRY RUN: Would {action_description}",
            "data": {},
            "action_logged": False
        }
    
    # 3. Check prerequisites
    if not _check_service_health():
        raise ConnectionError("Service not reachable")
    
    # 4. Execute action
    try:
        result = _execute_actual_command(param1, param2)
    except Exception as e:
        logger.error(f"Failed to execute {tool_name}: {e}")
        return {
            "success": False,
            "message": f"Error: {str(e)}",
            "data": {},
            "action_logged": True  # Log failures too
        }
    
    # 5. Verify result
    verified = _verify_action_completed(result)
    
    # 6. Log action
    _log_to_database(
        tool=tool_name,
        params={"param1": param1, "param2": param2},
        result=result,
        success=verified
    )
    
    # 7. Return structured result
    return {
        "success": verified,
        "message": "Action completed successfully" if verified else "Action failed verification",
        "data": result,
        "action_logged": True
    }
```

**Tool Categories:**

1. **Hardware Control Tools**
   - `solark.py` - SolArk inverter
   - `shelly.py` - Relays/switches
   - `miners.py` - Bitcoin miners

2. **Data Query Tools**
   - `victron.py` - Victron system status
   - `database.py` - PostgreSQL queries

3. **Integration Tools**
   - `nodered.py` - Node-RED flows
   - `kb_search.py` - Knowledge base

---

### 6. Knowledge Base Architecture

**Components:**

```
Knowledge Base System
├── Google Docs Sync (Daily)
│   ├── OAuth authentication
│   ├── Folder traversal
│   └── Document download
├── Indexer
│   ├── Parse documents
│   ├── Chunk content (512 tokens)
│   └── Generate embeddings (OpenAI)
└── Retriever
    ├── Semantic search
    ├── Rank results
    └── Return top 3-5 chunks
```

**Database Schema:**

```sql
-- Knowledge base tables
CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE,
    title VARCHAR(500),
    content TEXT,
    category VARCHAR(100),  -- Hardware, Procedures, etc.
    last_synced TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id),
    chunk_text TEXT,
    chunk_index INTEGER,  -- Position in document
    embedding VECTOR(1536),  -- OpenAI embedding
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_kb_chunks_embedding ON kb_chunks 
USING ivfflat (embedding vector_cosine_ops);
```

**Sync Workflow:**

```python
# Daily at midnight (Railway cron job)
1. Authenticate with Google OAuth
2. List all docs in "CommandCenter KB" folder
3. For each doc:
   - Check if modified since last sync
   - If modified:
     a. Download content
     b. Parse and chunk (512 tokens)
     c. Generate embeddings
     d. Upsert to database
4. Delete removed docs from DB
5. Log sync results
```

**Retrieval Workflow:**

```python
# When agent needs context
1. Agent calls kb_search(query="SolArk grid charge procedure")
2. Generate query embedding
3. Cosine similarity search in kb_chunks
4. Return top 5 chunks with metadata:
   - chunk_text
   - document_title
   - similarity_score
5. Agent uses context to answer/act
```

---

### 7. Memory System Architecture

**Three-Tier Memory (CrewAI + Custom):**

```
┌─────────────────────────────────────┐
│   Session Memory (CrewAI)           │
│   - Current conversation only       │
│   - Cleared after task complete     │
│   - Used for: context, follow-ups   │
└─────────────────────────────────────┘
           ↓ persists to
┌─────────────────────────────────────┐
│   Action History (PostgreSQL)       │
│   - Permanent log of all actions    │
│   - Queryable: "last 10 actions"    │
│   - Used for: audit, debugging      │
└─────────────────────────────────────┘
           ↓ informs
┌─────────────────────────────────────┐
│   Preferences (Key-Value)           │
│   - User-corrected defaults         │
│   - Example: min_soc_threshold=30   │
│   - Used for: personalization       │
└─────────────────────────────────────┘
```

**Database Schema:**

```sql
-- Session memory (temporary)
CREATE TABLE agent_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE,
    conversation_history JSONB,
    context JSONB,
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP
);

-- Action history (permanent)
CREATE TABLE action_log (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    agent VARCHAR(100),  -- Which agent
    tool VARCHAR(100),   -- Which tool
    action VARCHAR(200), -- What action
    parameters JSONB,    -- Tool params
    result JSONB,        -- Tool result
    success BOOLEAN,
    user_confirmed BOOLEAN,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Preferences (simple key-value)
CREATE TABLE preferences (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB,
    description TEXT,
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**CrewAI Memory Configuration:**

```python
# In crew definition
crew = Crew(
    agents=[...],
    tasks=[...],
    memory=True,  # Enable CrewAI memory
    memory_config={
        "provider": "mem0",  # Or custom
        "config": {
            "collection_name": "commandcenter_sessions",
            "embedding_model": "text-embedding-3-small"
        }
    }
)
```

---

### 8. Data Flow Diagrams

#### Flow 1: User Command Execution

```
User: "Pause the miners"
    ↓
MCP Server (Vercel)
    ↓ HTTPS POST /api/crew/execute
Railway FastAPI
    ↓ Create Task
Conversation Agent
    ↓ Parse: "pause miners"
    ↓ Validate: action is clear
    ↓ Confirm: "Miners running, pause? (yes/no)"
User: "yes"
    ↓
Conversation Agent → Energy Orchestrator
    ↓ Check: SOC=45%, Time=6pm
    ↓ Decide: "Safe to pause"
    ↓ Explain: "Pausing to preserve battery"
Energy Orchestrator → Hardware Control Agent
    ↓ Validate: Prerequisites met
    ↓ Execute: control_miners(action="pause")
Hardware Control Agent → Miner Tool
    ↓ SSH connection
    ↓ Execute: systemctl stop miner
    ↓ Verify: Process stopped
    ↓ Log: Action to database
Miner Tool → Hardware Control Agent
    ↓ Result: {success: true}
Hardware Control Agent → Energy Orchestrator
    ↓ Result: "Miners paused successfully"
Energy Orchestrator → Conversation Agent
    ↓ Format: User-friendly message
Conversation Agent → Railway API
    ↓ Result: "Miners paused. SOC now at 45%."
Railway API → MCP Server
    ↓ Stream result
MCP Server → User
    ↓
User sees: "Miners paused successfully. Battery at 45%."
```

---

#### Flow 2: Autonomous Optimization

```
Railway Cron (every 15 minutes)
    ↓ Trigger
Energy Orchestrator
    ↓ Query system state
    ↓ SOC: 75%
    ↓ Time: 3pm
    ↓ Weather: Clear (good solar)
    ↓ Miners: Paused
    ↓
    ↓ Analyze: "Excess solar available"
    ↓ Decision: "Resume miners"
    ↓ Formulate recommendation
Energy Orchestrator → Conversation Agent
    ↓ Message: "Recommendation ready"
Conversation Agent → MCP Server (notification)
    ↓ Push notification to user
User (via Claude): "What's the recommendation?"
    ↓
MCP Server → Railway API → Conversation Agent
    ↓ Retrieve stored recommendation
Conversation Agent:
    "Resume miners? SOC at 75% with 2 hours of 
     good solar remaining. Excess capacity available."
User: "yes"
    ↓
[Same execution flow as Flow 1]
```

---

#### Flow 3: Knowledge Base Query

```
User: "How do I manually switch SolArk to battery mode?"
    ↓
Conversation Agent
    ↓ Recognize: Needs KB lookup
    ↓ Search KB: "SolArk battery mode procedure"
    ↓
KB Retriever
    ↓ Generate embedding
    ↓ Cosine similarity search
    ↓ Return top 3 chunks:
       1. "SolArk Manual - Battery Mode Setup"
       2. "Operating Modes Overview"
       3. "Troubleshooting Battery Mode"
    ↓
Conversation Agent
    ↓ Synthesize answer with citations
    ↓ Response: "To switch to battery mode:
       1. Press Settings button
       2. Navigate to Operating Mode
       3. Select 'Battery Priority'
       (Source: SolArk Manual)"
    ↓
User receives answer with citation
```

---

### 9. Deployment Architecture

**Production Environment:**

```
┌──────────────────────────────────────────────────┐
│  Vercel (Global Edge)                            │
│  - MCP Server: https://mcp.commandcenter.app     │
│  - Region: Auto (edge locations)                 │
│  - Scaling: Serverless (auto)                    │
└──────────────────┬───────────────────────────────┘
                   │ HTTPS
┌──────────────────▼───────────────────────────────┐
│  Railway (us-west1)                              │
│  ┌────────────────────────────────────────────┐  │
│  │  commandcenter-api                         │  │
│  │  - FastAPI app                             │  │
│  │  - CrewAI agents                           │  │
│  │  - Replicas: 1 (scale up if needed)       │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  postgresql                                │  │
│  │  - Version: 15                             │  │
│  │  - Storage: 10GB (expandable)              │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  redis                                     │  │
│  │  - Version: 7                              │  │
│  │  - Used for: Caching, rate limiting       │  │
│  └────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────┘
                   │ Local network / Internet
┌──────────────────▼───────────────────────────────┐
│  Hardware (Local Network)                        │
│  - SolArk: 192.168.1.100                         │
│  - Shelly devices: 192.168.1.50-60               │
│  - Miners: 192.168.1.70-72                       │
│  - Victron: cloud.victronenergy.com              │
└──────────────────────────────────────────────────┘
```

**Scaling Strategy:**

| Component | V1 (Solo) | V2 (Growth) | V3 (Scale) |
|-----------|-----------|-------------|------------|
| Vercel | Hobby ($0) | Pro ($20) | Enterprise |
| Railway API | 1 replica | 2-3 replicas | 5+ replicas |
| PostgreSQL | 10GB | 50GB | 200GB+ |
| Requests/day | 100-500 | 1,000-5,000 | 10,000+ |
| Cost/month | $15-30 | $50-100 | $200-500 |

---

### 10. Security Architecture

**Authentication Flow:**

```
User → Claude (with MCP)
    ↓ MCP Protocol (includes user context)
MCP Server (Vercel)
    ↓ Verify: Allowed origin
    ↓ Check: Rate limits
    ↓ Add: Request signature
Railway API
    ↓ Verify: Signature valid
    ↓ Check: User permissions (future)
    ↓ Execute: Crew task
```

**Secrets Management:**

```
Vercel Environment Variables:
- RAILWAY_API_KEY (Railway API authentication)
- OPENAI_API_KEY (For embeddings, if needed)

Railway Environment Variables:
- DATABASE_URL (Auto-provided by Railway)
- REDIS_URL (Auto-provided by Railway)
- OPENAI_API_KEY (For LLM calls)
- GOOGLE_DOCS_CREDENTIALS (OAuth JSON)
- SOLARK_USERNAME, SOLARK_PASSWORD
- VICTRON_VRM_TOKEN
- ALLOWED_IPS (Whitelist for hardware commands)
```

**Network Security:**

```
Vercel → Railway: HTTPS only, API key required
Railway → Database: Internal network (not exposed)
Railway → Hardware: Local network (VPN or wireguard)
Railway → External APIs: HTTPS, token-based auth
```

**Safety Mechanisms:**

1. **Input Validation**
   - All tool parameters validated
   - Type checking with Pydantic
   - Range/enum validation

2. **Rate Limiting**
   - Max 100 requests/hour per user (Redis)
   - Tool-specific limits (e.g., max 10 hardware commands/minute)

3. **Dry-Run Mode**
   - Every destructive action supports dry-run
   - User can test without executing

4. **Confirmation Required**
   - Destructive actions require explicit "yes"
   - Confirmations logged

5. **Action Logging**
   - Every command logged (who, what, when, result)
   - Audit trail for accountability

6. **Rollback Capability**
   - Some actions support rollback
   - System remembers previous state

---

### 11. Monitoring & Observability

**Logging Strategy:**

```python
# Application logs
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('commandcenter.log'),
        logging.StreamHandler()  # Also to console
    ]
)

# Log levels
- ERROR: Action failures, exceptions
- WARNING: Unusual states, degraded performance
- INFO: Action completions, state changes
- DEBUG: Detailed execution (dev only)
```

**Metrics to Track:**

```python
# System metrics
- API response time (p50, p95, p99)
- Crew execution time
- Tool success rate
- Database query time

# Business metrics
- Actions per day
- Most-used tools
- User confirmations (yes/no ratio)
- Autonomous vs manual actions

# Hardware metrics
- Average SOC
- Grid on/off time
- Miner uptime
- Command success rate
```

**Alerting:**

```
Critical Alerts (immediate):
- Hardware command failed 3x in a row
- Database unreachable
- SOC below 10% (emergency)

Warning Alerts (within 1 hour):
- API latency > 5 seconds
- Tool success rate < 90%
- KB sync failed

Info Alerts (daily summary):
- Action count
- Average SOC
- Cost summary
```

---

## Technology Decision Summary

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| Framework | CrewAI | MIT license, easy multi-agent, 100k+ community |
| MCP Server | Vercel + Next.js | Global edge, serverless, Fluid Compute |
| Backend | Railway | Pay-per-use, simple, fast cold starts |
| API Server | FastAPI | Fast, async, OpenAPI docs |
| Database | PostgreSQL | Proven, supports vectors (pgvector) |
| Cache | Redis | Fast, built into Railway |
| Embeddings | OpenAI | Best quality, reasonable cost |
| Deployment | Git push | Zero-config, automatic |

---

## Development Workflow

**Local Development:**

```bash
# Terminal 1: Railway backend
cd commandcenter/railway
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload

# Terminal 2: Vercel frontend
cd commandcenter/vercel
npm install
npm run dev

# Terminal 3: PostgreSQL (local)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=dev postgres:15
```

**Testing Workflow:**

```bash
# Unit tests (tools)
pytest tests/tools/

# Integration tests (crews)
pytest tests/integration/

# End-to-end tests (API)
pytest tests/e2e/
```

**Deployment Workflow:**

```bash
# Railway (backend)
git push origin main
# Auto-deploys to Railway

# Vercel (MCP server)
cd vercel/
vercel deploy --prod
```

---

## Migration from Relay

**Phase 1: Parallel Run (Week 1)**
- CommandCenter built alongside Relay
- No production traffic yet
- Test in isolation

**Phase 2: Shadow Mode (Week 2)**
- CommandCenter receives same inputs as Relay
- Compare outputs
- No actions executed yet (dry-run only)

**Phase 3: Soft Launch (Week 3)**
- CommandCenter handles read-only queries
- Relay still handles hardware commands
- Validate accuracy

**Phase 4: Full Cutover (Week 4)**
- CommandCenter handles all traffic
- Relay kept as backup (paused)
- Monitor for 1 week

**Phase 5: Decommission Relay (Week 5+)**
- Archive Relay codebase
- Preserve data
- Full CommandCenter ownership

---

## Success Metrics

**Technical Metrics:**
- [ ] API response time < 2 seconds (p95)
- [ ] Tool success rate > 99%
- [ ] Crew execution time < 30 seconds
- [ ] Zero critical bugs after 2 weeks
- [ ] 99%+ uptime

**User Experience Metrics:**
- [ ] User rarely needs to rephrase
- [ ] Recommendations accepted > 80% of time
- [ ] Zero unexpected hardware state changes
- [ ] User can explain how system works
- [ ] User confident to add new features

**Business Metrics:**
- [ ] Monthly cost < $100
- [ ] Energy savings measurable
- [ ] Battery health improved
- [ ] System pays for itself

---

## Risk Mitigation

**Risk:** Hardware commands fail  
**Mitigation:** Dry-run mode, retry logic, rollback capability

**Risk:** Database corruption  
**Mitigation:** Daily backups, Railway snapshots, schema migrations

**Risk:** API latency too high  
**Mitigation:** Caching (Redis), async processing, Fluid Compute

**Risk:** Cost overruns  
**Mitigation:** Budget alerts, usage monitoring, Railway pay-per-use

**Risk:** Security breach  
**Mitigation:** API keys, rate limiting, input validation, audit logs

---

## Next Steps

**Phase 2: Planning (2-3 days)**
1. Create detailed implementation checklist
2. Set up Railway project
3. Set up Vercel project
4. Initialize GitHub repo structure
5. Configure CI/CD

**Phase 3: Build (2-3 weeks)**
1. **Week 1:** Port tools, set up database
2. **Week 2:** Build agents and crews
3. **Week 3:** Integrate MCP, test end-to-end

**Phase 4: Deploy (3-5 days)**
1. Deploy to Railway staging
2. Deploy to Vercel staging
3. Test in staging
4. Deploy to production
5. Monitor

**Phase 5: Optimize (Ongoing)**
1. Performance tuning
2. Cost optimization
3. Feature additions from V2 backlog

---

## Appendix: Configuration Files

### `railway.json`
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "Dockerfile"
  },
  "deploy": {
    "numReplicas": 1,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### `vercel.json`
```json
{
  "buildCommand": "npm run build",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "regions": ["iad1"]
}
```

### `Dockerfile` (Railway)
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run FastAPI with uvicorn
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

**Architecture Design Complete. Ready for Phase 2: Planning & Implementation.**