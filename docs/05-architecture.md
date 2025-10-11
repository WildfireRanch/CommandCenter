# CommandCenter V1.5 Architecture

**Date:** December 10, 2025 (Updated from October 3, 2025)
**Project:** CommandCenter V1.5
**Status:** Production
**Previous Phases:** Audit ✅ | Requirements ✅ | Port Plan ✅ | V1.0 ✅ | V1.5 ✅

---

## Executive Summary

CommandCenter V1.5 is a **CrewAI-based energy orchestration system** deployed on Railway (backend/agents/dashboards) with intelligent multi-agent routing. The architecture prioritizes:

1. **Reliability** - Replace fragile custom orchestration with proven CrewAI framework
2. **Performance** - KB fast-path for sub-second documentation queries
3. **Maintainability** - Clear separation of concerns, understandable by solo developer
4. **Extensibility** - Foundation supports V2 features without major refactor
5. **Safety** - Multiple layers of validation before hardware commands execute

**Core Innovation:** Manager agent routes queries to specialized agents (Solar Controller, Energy Orchestrator) with KB fast-path bypass for documentation queries, achieving 50x performance improvement over nested agent calls.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   User Interface                         │
│          Streamlit Dashboards (5 pages)                  │
│  - Home (Quick Overview)                                 │
│  - System Health (API/DB status)                         │
│  - Energy Monitor (Real-time metrics)                    │
│  - Agent Chat (Conversational interface)                 │
│  - Logs Viewer (Conversation history)                    │
└────────────────────┬────────────────────────────────────┘
                     │ HTTPS API Calls
┌────────────────────▼────────────────────────────────────┐
│           Railway (FastAPI + CrewAI Backend)             │
│  ┌──────────────────────────────────────────────────┐   │
│  │  FastAPI Application (src/api/main.py)           │   │
│  │  - POST /ask (Agent chat endpoint)               │   │
│  │  - GET /conversations (History)                  │   │
│  │  - GET /energy/latest (Real-time data)           │   │
│  │  - GET /energy/stats (24h statistics)            │   │
│  │  - GET /health (System status)                   │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│  ┌──────────────────▼───────────────────────────────┐   │
│  │  KB FAST-PATH (Keyword Detection)                │   │
│  │  - Bypasses Manager agent for docs queries       │   │
│  │  - 50x faster (400ms vs 20s+)                    │   │
│  │  - Keywords: specs, threshold, policy, how-to    │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│                     ├───→ Direct KB Search (if keyword match)
│                     │                                    │
│                     └───→ Manager Crew (all other queries)
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  Manager Agent (Query Router)                    │   │
│  │  - Analyzes query intent                         │   │
│  │  - Routes to appropriate specialist              │   │
│  │  - Returns tool output verbatim                  │   │
│  │  Tools:                                          │   │
│  │    • route_to_solar_controller()                 │   │
│  │    • route_to_energy_orchestrator()              │   │
│  │    • search_kb_directly()                        │   │
│  └──────────────────┬───────────────────────────────┘   │
│                     │                                    │
│         ┌───────────┼───────────┐                        │
│         │           │           │                        │
│  ┌──────▼─────┐ ┌──▼──────┐ ┌──▼─────────────────┐      │
│  │  Solar     │ │ Energy  │ │  Knowledge Base    │      │
│  │  Controller│ │ Orch.   │ │  Search            │      │
│  │  Agent     │ │ Agent   │ │  (Direct/Routed)   │      │
│  │            │ │         │ │                    │      │
│  │ Real-time  │ │Planning │ │ Semantic search    │      │
│  │ monitoring │ │& optim. │ │ pgvector + OpenAI  │      │
│  └────────────┘ └─────────┘ └────────────────────┘      │
│         │           │                  │                 │
│  ┌──────▼───────────▼──────────────────▼──────────────┐  │
│  │  CrewAI Tools Layer                               │  │
│  │  - get_latest_energy (SolArk API)                 │  │
│  │  - get_energy_stats (Database queries)            │  │
│  │  - search_knowledge_base (KB retrieval)           │  │
│  └──────────────────┬────────────────────────────────┘  │
└─────────────────────┼───────────────────────────────────┘
                      │
         ┌────────────┴────────────┐
         │                         │
┌────────▼────────┐    ┌───────────▼──────────┐
│  PostgreSQL     │    │  External Services   │
│  - Telemetry    │    │  - SolArk inverter   │
│  - Conversations│    │    (192.168.1.23)    │
│  - KB documents │    │  - OpenAI API        │
│  - KB chunks    │    │    (embeddings)      │
│  - Action log   │    │                      │
└─────────────────┘    └──────────────────────┘
```

---

## Component Deep Dive

### 1. Frontend Layer (Streamlit Dashboards)

**Purpose:** User interface for monitoring and agent interaction

**Technology Stack:**
- Streamlit (Python web framework)
- Railway deployment (same host as backend)
- Custom CSS for unified design

**File Structure:**
```
dashboards/
├── Home.py                          # Main landing page
├── pages/
│   ├── 1_🏥_System_Health.py        # API/DB monitoring
│   ├── 2_⚡_Energy_Monitor.py       # Real-time energy data
│   ├── 3_🤖_Agent_Chat.py           # Conversational interface
│   └── 4_📊_Logs_Viewer.py          # Conversation history
├── components/
│   └── api_client.py                # Railway API client
└── assets/
    └── WildfireMang.png             # Branding
```

**Key Features:**

1. **Home Page** ([Home.py](dashboards/Home.py))
   - Quick overview metrics (SOC, Solar, Load, Grid Export)
   - Navigation shortcuts
   - Real-time data from `/energy/latest` endpoint

2. **System Health** ([1_🏥_System_Health.py](dashboards/pages/1_🏥_System_Health.py))
   - API health check
   - Database connectivity
   - Service status

3. **Energy Monitor** ([2_⚡_Energy_Monitor.py](dashboards/pages/2_⚡_Energy_Monitor.py))
   - 5 real-time metrics: SOC, Solar, Load, Battery Power, Grid Export
   - 24-hour statistics
   - Auto-refresh capability

4. **Agent Chat** ([3_🤖_Agent_Chat.py](dashboards/pages/3_🤖_Agent_Chat.py))
   - Conversational interface to CrewAI agents
   - Session management
   - Displays agent_used and agent_role metadata

5. **Logs Viewer** ([4_📊_Logs_Viewer.py](dashboards/pages/4_📊_Logs_Viewer.py))
   - Recent conversation history
   - Individual conversation details
   - Message inspector

**API Client:**
```python
# components/api_client.py
class RailwayAPIClient:
    def __init__(self):
        self.base_url = os.getenv("RAILWAY_API_URL", "https://api.wildfireranch.us")
        self.api_key = os.getenv("API_KEY", "")

    def ask_agent(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Send message to agent"""

    def get_latest_energy(self) -> Dict[str, Any]:
        """Get latest energy snapshot"""

    def get_energy_stats(self, hours: int = 24) -> Dict[str, Any]:
        """Get energy statistics"""
```

**Deployment:**
```bash
# From dashboards/
streamlit run Home.py --server.port 8501
```

**Environment Variables:**
```env
RAILWAY_API_URL=https://api.wildfireranch.us
API_KEY=<secret>
```

---

### 2. Railway Layer (CrewAI Backend)

**Purpose:** Run CrewAI agents, tools, API server, and dashboards

**Technology Stack:**
- Python 3.10+
- CrewAI framework
- FastAPI (API server)
- PostgreSQL with pgvector (data + embeddings)
- Uvicorn (ASGI server)

**File Structure:**
```
railway/
├── src/
│   ├── agents/
│   │   ├── manager.py               # Manager/Router agent
│   │   ├── solar_controller.py      # Real-time monitoring agent
│   │   ├── energy_orchestrator.py   # Planning/optimization agent
│   │   └── __init__.py
│   ├── tools/
│   │   ├── kb_search.py             # Knowledge Base search tool
│   │   ├── energy_monitor.py        # Energy data queries
│   │   └── __init__.py
│   ├── kb/
│   │   ├── sync.py                  # Google Drive sync + search logic
│   │   ├── google_drive.py          # Google Drive API integration
│   │   └── __init__.py
│   ├── api/
│   │   ├── main.py                  # FastAPI app (includes KB fast-path)
│   │   └── __init__.py
│   ├── utils/
│   │   └── db.py                    # Database utilities
│   └── config/
│       └── settings.py              # Configuration
├── tests/                           # Test suite
├── requirements.txt
├── Dockerfile
└── README.md
```

**API Endpoints:**
```python
# Main endpoints (src/api/main.py)
GET    /health                       # System health check
POST   /ask                          # Agent chat (with KB fast-path)
GET    /conversations                # Recent conversation list
GET    /conversations/{session_id}   # Single conversation detail
GET    /energy/latest                # Latest energy snapshot
GET    /energy/stats?hours=24        # Energy statistics
POST   /db/init-schema               # Initialize database schema
```

**KB Fast-Path Implementation:**
```python
# src/api/main.py - /ask endpoint
@app.post("/ask")
async def ask_agent(request: AskRequest):
    # CRITICAL: KB Fast-Path to avoid Manager agent timeout
    query_lower = request.message.lower()
    kb_keywords = ['specification', 'specs', 'threshold', 'policy',
                   'procedure', 'maintain', 'documentation', 'guide',
                   'manual', 'instructions', 'how do i', 'how to']

    is_kb_query = any(keyword in query_lower for keyword in kb_keywords)

    if is_kb_query and len(request.message) > 10:
        # Direct KB search - bypass Manager agent (400ms vs 20s+)
        from ..tools.kb_search import search_knowledge_base
        result_str = search_knowledge_base.func(request.message, limit=5)
        agent_used = "Knowledge Base"
        agent_role = "Documentation Search"
    else:
        # Manager crew routes to Solar Controller or Energy Orchestrator
        crew = create_manager_crew(request.message, context)
        result = crew.kickoff()
        # Extract metadata from JSON response
        agent_used, agent_role = parse_agent_metadata(result)
```

**Environment Variables (Railway):**
```env
DATABASE_URL=postgresql://...
OPENAI_API_KEY=<secret>
SOLARK_API_URL=http://192.168.1.23
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>  # Service account credentials for Google Drive
KB_FOLDER_ID=<google-drive-folder-id>  # Target folder for KB sync
```

**Why Railway:**
- ✅ Single deployment for backend + dashboards
- ✅ Built-in PostgreSQL with pgvector support
- ✅ Pay-per-use pricing
- ✅ Simple deployment from GitHub
- ✅ Good for long-running processes

---

### 3. Multi-Agent System Architecture

**V1.5 Agent Structure:**

```
User Query → KB Fast-Path Check
                │
                ├─→ [Keyword Match] → Direct KB Search (400ms)
                │
                └─→ [No Match] → Manager Agent
                                    │
                                    ├─→ Real-time query → Solar Controller Agent (5-6s)
                                    │
                                    ├─→ Planning query → Energy Orchestrator Agent (13-15s)
                                    │
                                    └─→ Documentation → KB Search via routing tool (fallback)
```

**Routing Decision Matrix:**

| Query Type | Keywords | Route To | Response Time |
|-----------|----------|----------|---------------|
| Documentation | specs, threshold, policy, how-to | KB Fast-Path | 400ms |
| Real-time status | battery, solar, current, now | Solar Controller | 5-6s |
| Planning/optimization | should we, create plan, optimize | Energy Orchestrator | 13-15s |
| Off-topic | hello, who am I | Manager (direct) | 2s |

---

### 4. Agent Definitions

#### Agent 1: Manager Agent (Query Router)

**File:** [railway/src/agents/manager.py](railway/src/agents/manager.py)

**Role:** "Query Router and Coordinator"

**Purpose:** Analyze user query intent and route to appropriate specialist

**Key Characteristics:**
- **Delegation:** False (doesn't delegate, just routes)
- **Max Iterations:** 3 (reduced from 10 to prevent over-thinking)
- **Output:** Returns tool output VERBATIM (no reformatting)

**Tools:**
1. `route_to_solar_controller(query: str)` - For real-time status queries
2. `route_to_energy_orchestrator(query: str)` - For planning/optimization
3. `search_kb_directly(query: str)` - For documentation queries

**Routing Logic:**
```python
# manager.py - Routing rules
Real-time questions → route_to_solar_controller(query)
Examples: battery level, solar production, current power, status

Planning questions → route_to_energy_orchestrator(query)
Examples: should we run miners, create plan, optimization

Documentation questions → search_kb_directly(query)
Examples: thresholds, specifications, policies, how-to guides
```

**Critical Design Decision (Session 024):**
- Manager agent MUST return tool output verbatim
- No iteration loops on KB results (was causing 20s+ timeouts)
- KB search returns simple text format (not JSON) to prevent re-parsing attempts
- Reduced max_iter from 10 to 3 to force immediate tool usage

---

#### Agent 2: Solar Controller Agent (Real-Time Monitor)

**File:** [railway/src/agents/solar_controller.py](railway/src/agents/solar_controller.py)

**Role:** "Energy Systems Monitor and Status Reporter"

**Purpose:** Answer real-time queries about current energy system state

**Responsibilities:**
- Current battery SOC/charge status
- Solar production (right now)
- House load/power consumption
- Grid import/export status
- System health checks

**Tools:**
- `get_latest_energy()` - Fetch current snapshot from SolArk API
- `get_energy_stats(hours=24)` - Historical statistics from database
- `search_knowledge_base()` - Context for explanations

**Example Queries:**
- "What's my battery level?"
- "How much solar am I producing?"
- "Am I using grid power right now?"

**Response Time:** ~5-6 seconds

---

#### Agent 3: Energy Orchestrator Agent (Planning & Optimization)

**File:** [railway/src/agents/energy_orchestrator.py](railway/src/agents/energy_orchestrator.py)

**Role:** "Energy Operations Manager and Optimization Specialist"

**Purpose:** Make planning and optimization decisions

**Responsibilities:**
- "Should we" questions (run miners, charge battery, etc.)
- Creating energy plans
- Optimization recommendations
- Battery management strategies
- Forecasting and predictions

**Tools:**
- `get_latest_energy()` - Current state for decision-making
- `get_energy_stats(hours=24)` - Historical patterns
- `search_knowledge_base()` - Operating procedures and thresholds

**Example Queries:**
- "Should we run the miners tonight?"
- "Create an energy plan for today"
- "When's the best time to charge the battery?"

**Response Time:** ~13-15 seconds (includes analysis)

---

### 5. Knowledge Base Architecture

**Components:**

```
Knowledge Base System
├── Database Storage (PostgreSQL)
│   ├── kb_documents (full documents)
│   └── kb_chunks (512-token chunks with embeddings)
├── Google Drive Sync Service (kb/sync.py + kb/google_drive.py)
│   ├── Service account authentication
│   ├── Recursive folder scanning
│   ├── Document fetching (Google Docs, PDFs, Spreadsheets)
│   ├── Content chunking (512 tokens)
│   ├── Embedding generation (OpenAI text-embedding-3-small)
│   └── Incremental sync (only changed docs)
└── Search Service (tools/kb_search.py)
    ├── Query embedding generation
    ├── Cosine similarity search (pgvector)
    └── Result formatting with citations
```

**Database Schema:**

```sql
-- Full documents
CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE,  -- Google Drive file ID
    title VARCHAR(500),
    folder VARCHAR(500),                 -- Folder name
    folder_path TEXT,                    -- Full path (e.g., "Root/Technical/SolArk")
    mime_type VARCHAR(100),              -- application/vnd.google-apps.document, etc.
    full_content TEXT,
    token_count INTEGER,
    is_context_file BOOLEAN DEFAULT FALSE,  -- Files in /CONTEXT/ folder
    last_synced TIMESTAMP,               -- When last synced from Google Drive
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chunked content with embeddings
CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id),
    chunk_text TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sync tracking
CREATE TABLE kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),              -- "full" or "context-only"
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50),                 -- "running", "completed", "failed"
    documents_processed INTEGER,
    documents_updated INTEGER,
    documents_failed INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(100)           -- "manual", "scheduled", etc.
);

-- Vector similarity index
CREATE INDEX kb_chunks_embedding_idx ON kb_chunks
USING ivfflat (embedding vector_cosine_ops);
```

**Sync Workflow:**

```python
# Automated sync from Google Drive
1. Authenticate with service account
2. Recursively scan target folder (and subfolders)
3. Filter to supported file types:
   - Google Docs (application/vnd.google-apps.document)
   - PDFs (application/pdf)
   - Google Sheets (application/vnd.google-apps.spreadsheet)
4. For each document:
   a. Check if modified since last_synced (skip if unchanged)
   b. Fetch content (format-specific extraction)
   c. Chunk into 512-token segments
   d. Generate embeddings via OpenAI
   e. Upsert to kb_documents table
   f. Delete old chunks, insert new chunks
5. Cleanup: Remove documents deleted from Drive
6. Log sync results to kb_sync_log
```

**Search Workflow:**

```python
# When agent or fast-path needs KB context
1. User query: "What is the minimum battery SOC threshold?"
2. Generate query embedding via OpenAI
3. Cosine similarity search in kb_chunks (using pgvector <=> operator)
4. Return top 5 chunks with metadata:
   - chunk_text (full content)
   - source (document title)
   - folder (folder name)
   - similarity score (0.0-1.0)
5. Format with citations
```

**Fast-Path vs Routed Search:**

| Aspect | Fast-Path | Routed (via Manager) |
|--------|-----------|---------------------|
| Trigger | Keyword match at API level | Manager agent decision |
| Performance | 400ms | 5-6s (if used) |
| Use Case | Common documentation queries | Complex queries needing context |
| Implementation | Direct tool call | Manager → routing tool → KB search |

**Why Fast-Path Was Critical (Session 024):**
- CrewAI nesting overhead: Manager → routing tool → KB search tool → OpenAI
- Original implementation: 20+ second timeouts
- Fast-path solution: Keyword detection bypasses Manager entirely
- Result: 50x performance improvement (20s → 400ms)

---

### 6. Conversation & Memory System

**Three-Tier Memory:**

```
┌─────────────────────────────────────┐
│   Session Context (In-Memory)       │
│   - Current conversation messages   │
│   - Used for follow-up questions    │
│   - Passed to Manager agent         │
└─────────────────────────────────────┘
           ↓ persists to
┌─────────────────────────────────────┐
│   Conversations (PostgreSQL)        │
│   - Permanent conversation history  │
│   - Queryable via /conversations    │
│   - Displayed in Logs Viewer        │
└─────────────────────────────────────┘
           ↓ extracted for
┌─────────────────────────────────────┐
│   Agent Metadata (Parsed)           │
│   - agent_used (Solar/Orchestrator) │
│   - agent_role (descriptive name)   │
│   - Displayed in chat interface     │
└─────────────────────────────────────┘
```

**Database Schema:**

```sql
-- Conversation sessions
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Individual messages
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    agent_used VARCHAR(100),     -- Extracted from response
    agent_role VARCHAR(200),     -- Extracted from response
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes for fast retrieval
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
```

**Conversation Flow:**

```python
# User sends message via /ask endpoint
1. Check if session_id exists or create new conversation
2. Save user message to messages table
3. Retrieve last 5 messages for context
4. Pass context to Manager agent or KB fast-path
5. Get response with agent metadata
6. Parse JSON to extract agent_used and agent_role
7. Save assistant response to messages table
8. Return to user with metadata
```

**Metadata Extraction:**

```python
# Example agent response (Solar Controller/Energy Orchestrator)
{
  "response": "Your battery is at 67% SOC...",
  "agent_used": "Solar Controller",
  "agent_role": "Energy Systems Monitor"
}

# KB Fast-Path response (plain text)
"Here's what I found:\n\n1. Minimum SOC: 30%...\n\n[Source: Knowledge Base Search]"
```

---

### 7. Energy Data Flow

**Data Sources:**

```
SolArk Inverter (192.168.1.23)
    ↓ Polled every 30s
Railway Backend (telemetry collector)
    ↓ Inserts into PostgreSQL
Telemetry Table
    ↓ Queried by API
Dashboard + Agents
```

**Telemetry Schema:**

```sql
CREATE TABLE telemetry (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    soc FLOAT,              -- Battery state of charge (%)
    batt_power FLOAT,       -- Battery power (W, +charging/-discharging)
    pv_power FLOAT,         -- Solar production (W)
    load_power FLOAT,       -- House load (W)
    pv_to_grid FLOAT,       -- Grid export (W, V1.5 addition)
    grid_to_load FLOAT,     -- Grid import (W)
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_telemetry_timestamp ON telemetry(timestamp DESC);
```

**API Endpoints:**

```python
# Get latest snapshot (last 30s)
GET /energy/latest
Response: {
  "status": "success",
  "data": {
    "timestamp": "2025-12-10T10:30:00Z",
    "soc": 67.0,
    "batt_power": 1200.0,
    "pv_power": 3500.0,
    "load_power": 2300.0,
    "pv_to_grid": 450.0,    # V1.5 addition
    "grid_to_load": 0.0
  }
}

# Get statistics (avg, min, max over time period)
GET /energy/stats?hours=24
Response: {
  "status": "success",
  "data": {
    "avg_soc": 65.2,
    "min_soc": 42.0,
    "max_soc": 89.0,
    "total_pv_production": 45000.0,  # Wh
    "total_grid_export": 12000.0     # Wh (V1.5 addition)
  }
}
```

**V1.5 Grid Export Enhancement:**
- Added `pv_to_grid` field to telemetry schema
- Displayed on Home page (4th metric)
- Displayed on Energy Monitor (5th metric)
- Shows real-time solar export to grid

---

### 8. Deployment Architecture

**Production Environment:**

```
┌──────────────────────────────────────────────────┐
│  Railway (Single Service)                        │
│  ┌────────────────────────────────────────────┐  │
│  │  commandcenter-backend                     │  │
│  │  - FastAPI app (port 8000)                 │  │
│  │  - Streamlit dashboards (port 8501)        │  │
│  │  - CrewAI agents                           │  │
│  │  - Telemetry collector                     │  │
│  └────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────┐  │
│  │  postgresql                                │  │
│  │  - Version: 15 with pgvector + TimescaleDB│  │
│  │  - Tables: 8 total                         │  │
│  │    • agent.* (4): conversations, messages, │  │
│  │      memory, logs                          │  │
│  │    • solark.* (1): plant_flow              │  │
│  │    • kb_* (3): documents, chunks, sync_log │  │
│  └────────────────────────────────────────────┘  │
└──────────────────┬───────────────────────────────┘
                   │ Local network
┌──────────────────▼───────────────────────────────┐
│  Hardware (Local Network)                        │
│  - SolArk: 192.168.1.23                          │
└──────────────────────────────────────────────────┘
```

**Public URLs:**
- Backend API: `https://api.wildfireranch.us`
- Streamlit Dashboard: `https://dashboard.wildfireranch.us`

**Deployment Process:**
```bash
# From repository root
git push origin main
# Railway auto-deploys from main branch
# Runs Dockerfile from railway/ directory
```

**Environment Variables:**
```env
DATABASE_URL=postgresql://...                    # Auto-provided by Railway
OPENAI_API_KEY=<secret>                         # For embeddings
SOLARK_API_URL=http://192.168.1.23             # Local network
API_KEY=<secret>                                # Dashboard auth
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>            # Google Drive service account
KB_FOLDER_ID=<google-drive-folder-id>          # Target folder for KB sync
```

---

### 9. Performance Characteristics

**V1.5 Performance Metrics (Session 024 Testing):**

| Component | Response Time | Notes |
|-----------|--------------|-------|
| KB Fast-Path | 400ms | Direct search, bypasses Manager |
| KB Routed | 5-6s | Via Manager agent (fallback) |
| Solar Controller | 5-6s | Includes API call to SolArk |
| Energy Orchestrator | 13-15s | Analysis + reasoning |
| Energy API (/latest) | 50-100ms | Direct database query |
| Dashboard Page Load | 1-2s | Includes API calls |

**Optimization Decisions (Session 024):**

1. **KB Fast-Path Architecture**
   - Problem: KB queries via Manager timing out (20s+)
   - Root Cause: CrewAI nesting overhead
   - Solution: Keyword detection at API level
   - Result: 50x improvement (20s → 400ms)
   - Trade-off: Keyword matching less intelligent, but vastly faster

2. **Manager Agent Tuning**
   - Reduced max_iter from 10 to 3
   - Set allow_delegation=False
   - Required verbatim tool output (no reformatting)
   - Result: Faster routing, no iteration loops

3. **Frontend Compression**
   - Reduced vertical padding by ~50%
   - Maintained font sizes for readability
   - Applied uniformly across all 5 pages
   - Result: More content visible per screen

---

### 10. Security Architecture

**Authentication:**
- API key authentication for dashboard → backend
- No public endpoints (behind Railway private network)
- SolArk API on local network only

**Secrets Management:**
```env
# Railway environment variables
DATABASE_URL=<auto-provided>
OPENAI_API_KEY=<secret>
API_KEY=<secret>
SOLARK_API_URL=http://192.168.1.23
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>  # Google Drive API access
KB_FOLDER_ID=<folder-id>              # Not secret, but configuration
```

**Network Security:**
- Backend API: HTTPS only
- Database: Internal Railway network (not exposed)
- SolArk: Local network (192.168.1.x)
- OpenAI API: HTTPS, API key auth
- Google Drive API: HTTPS, service account OAuth 2.0

**Input Validation:**
- All API endpoints use Pydantic models
- Session IDs validated before database queries
- Error handling for malformed requests

---

### 11. Session 024 Architectural Decisions

**Decision 1: KB Fast-Path Implementation**

**Context:** KB queries timing out at 20+ seconds via Manager agent routing

**Options Considered:**
1. Fix Manager agent behavior (tune instructions)
2. Optimize KB search tool performance
3. Bypass Manager for documentation queries

**Decision:** Implement KB fast-path at API level

**Rationale:**
- CrewAI nesting overhead unavoidable (Manager → routing tool → KB search tool)
- Even perfect agent behavior still incurs 5-6s overhead
- Documentation queries are frequent and latency-sensitive
- Keyword matching accurate enough for common patterns

**Implementation:**
```python
# src/api/main.py
kb_keywords = ['specification', 'specs', 'threshold', 'policy',
               'procedure', 'maintain', 'documentation', 'guide',
               'manual', 'instructions', 'how do i', 'how to']

if any(keyword in query_lower for keyword in kb_keywords):
    # Bypass Manager, call KB search directly
    result = search_knowledge_base.func(query, limit=5)
```

**Results:**
- KB queries: 400ms (was 20s+)
- 50x performance improvement
- User requirement: "key function, cannot be degraded" ✅

---

**Decision 2: Manager Agent Output Format**

**Context:** Manager agent reformatting tool output, causing iteration loops

**Problem:** KB search returns formatted text, Manager tried to parse as JSON and iterate

**Solution:**
1. KB search returns simple text (not JSON) to prevent parsing attempts
2. Manager instructed to return tool output VERBATIM
3. Reduced max_iter to 3 to force immediate completion

**Implementation:**
```python
# tools/kb_search.py - Changed from JSON to text
return f"{kb_result}\n\n[Source: Knowledge Base Search]"

# agents/manager.py - Verbatim output instruction
"""CRITICAL: Return tool output VERBATIM. Do not reformat, summarize,
or add commentary. Your output = Tool output (no changes)."""
```

**Results:**
- Manager no longer iterates on results
- Clean agent metadata extraction
- Consistent response format

---

**Decision 3: Grid Export Display**

**Context:** User requested "watts export not showing"

**Implementation:**
1. Added `pv_to_grid` extraction from SolArk API
2. Created 4th metric on Home page
3. Created 5th metric on Energy Monitor page
4. Used same data extraction pattern as other metrics

**Results:**
- Grid export visible on Home and Energy Monitor
- Consistent metric display format
- Real-time updates

---

**Decision 4: Compressed Vertical Spacing**

**Context:** User requested "compress the size of the boxes and spacing...vertically"

**Requirements:**
- Keep font sizes (readability)
- Reduce vertical padding/margins
- Apply uniformly across all pages

**Implementation:**
```css
/* Applied to all 5 dashboard pages */
.block-container {
    padding-top: 2rem !important;      /* was 3rem */
    padding-bottom: 1rem !important;   /* was 2rem */
}

[data-testid="stMetric"] {
    padding: 0.75rem !important;       /* was 1.5rem */
}
```

**Results:**
- ~50% reduction in vertical spacing
- Font sizes unchanged
- Uniform appearance across dashboard

---

## V1.5 Changes Summary

**New Features:**
1. ✅ Grid export display on Home and Energy Monitor
2. ✅ KB fast-path for sub-second documentation queries
3. ✅ Compressed vertical spacing across all dashboard pages
4. ✅ Agent metadata extraction (agent_used, agent_role)
5. ✅ Improved conversation history display

**Performance Improvements:**
1. ✅ KB search: 20s → 400ms (50x faster)
2. ✅ Manager agent routing optimized (max_iter: 10 → 3)
3. ✅ Dashboard page load improved

**Architecture Changes:**
1. ✅ KB fast-path bypass at API level
2. ✅ Manager agent output format standardized
3. ✅ Telemetry schema extended (pv_to_grid field)
4. ✅ Unified CSS across all dashboard pages

**Bug Fixes:**
1. ✅ KB timeout issue resolved
2. ✅ Manager agent iteration loops fixed
3. ✅ Grid export data extraction corrected
4. ✅ Inconsistent vertical spacing resolved

---

## Technology Decision Summary

| Component | Technology | Why Chosen |
|-----------|-----------|------------|
| Framework | CrewAI | MIT license, easy multi-agent, active community |
| Frontend | Streamlit | Fast prototyping, Python-native, built-in components |
| Backend | FastAPI | Fast, async, automatic OpenAPI docs |
| Deployment | Railway | Single service for backend+dashboards, built-in PostgreSQL |
| Database | PostgreSQL 15 + pgvector | Proven, supports vector embeddings |
| Embeddings | OpenAI text-embedding-3-small | Best quality, reasonable cost |
| Agent Routing | Manager pattern | Clear separation, specialized agents |
| KB Performance | Fast-path bypass | Pragmatic solution for latency requirement |

---

## Success Metrics (V1.5)

**Technical Metrics:**
- ✅ KB response time < 500ms (achieved 400ms)
- ✅ Solar Controller response < 10s (achieved 5-6s)
- ✅ Energy Orchestrator response < 20s (achieved 13-15s)
- ✅ Dashboard page load < 3s (achieved 1-2s)
- ✅ Zero critical bugs after production deployment

**User Experience Metrics:**
- ✅ Grid export visible on dashboard
- ✅ Compressed layout shows more data per screen
- ✅ Agent metadata displayed in chat
- ✅ Conversation history accessible
- ✅ KB queries respond instantly

**Business Metrics:**
- ✅ Production ready (deployed v1.5.0)
- ✅ No performance degradation
- ✅ Documentation complete
- ✅ All blocking issues resolved

---

## Next Steps (V2.0 and Beyond)

**Potential Enhancements:**
1. Hardware control agents (miners, battery management)
2. Autonomous optimization scheduler
3. Weather forecast integration
4. Historical analytics dashboard
5. Mobile-responsive design
6. Multi-user authentication

**Architecture Considerations:**
- Manager agent pattern scales to additional specialists
- KB fast-path pattern can extend to other query types
- Database schema supports additional telemetry fields
- Streamlit dashboard can add pages without refactor

---

**Architecture Documentation Updated for V1.5.0 - December 10, 2025**
