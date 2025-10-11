# CommandCenter System Context
**Version:** 1.5.0 (Production)
**Last Updated:** December 10, 2025
**Purpose:** Complete system context for AI agents and developers
**Owner:** Technical ranch owner managing off-grid solar operations

---

## 🎯 System Overview

### What is CommandCenter?
CommandCenter is an AI-powered energy management system for off-grid ranch operations. It combines:
- **Real-time monitoring** of solar, battery, grid, and load systems
- **Multi-agent AI system** (CrewAI-based) for intelligent decision-making
- **Knowledge base** with semantic search for documentation and procedures
- **Conversation memory** for context-aware interactions
- **Planning & optimization** for energy usage and Bitcoin mining operations

### Core Philosophy
- **Cloud-first:** Remote operation 5/7 days, no local dependencies
- **Desktop-first:** Full web dashboard before mobile (PWA in V2+)
- **Safety-first:** Multiple validation layers before hardware control
- **Maintainable:** Clear architecture, solo developer friendly
- **Production-ready:** V1.5 deployed, operational, reliable

---

## 🏗️ Architecture At-A-Glance

### Three-Tier System

```
┌─────────────────────────────────────────────┐
│  User Interface (Streamlit Dashboard)      │
│  - Home, System Health, Energy Monitor      │
│  - Agent Chat, Logs Viewer                  │
│  Railway: dashboard.wildfireranch.us        │
└────────────────┬────────────────────────────┘
                 │ HTTPS API
┌────────────────▼────────────────────────────┐
│  Backend API + Agent System (Railway)       │
│  ┌──────────────────────────────────────┐   │
│  │ KB FAST-PATH (400ms doc queries)     │   │
│  └──────────────────────────────────────┘   │
│  ┌──────────────────────────────────────┐   │
│  │ Manager Agent (Query Router)         │   │
│  │  ├─→ Solar Controller (status)       │   │
│  │  ├─→ Energy Orchestrator (planning)  │   │
│  │  └─→ KB Search (documentation)       │   │
│  └──────────────────────────────────────┘   │
│  api.wildfireranch.us                       │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  Data Layer (Railway PostgreSQL)            │
│  - Telemetry (TimescaleDB)                  │
│  - Conversations & Messages                 │
│  - Knowledge Base (pgvector)                │
└─────────────────────────────────────────────┘
```

### Technology Stack
- **Framework:** CrewAI (MIT license, multi-agent orchestration)
- **Frontend:** Streamlit (Python web framework, rapid prototyping)
- **Backend:** FastAPI (async, automatic OpenAPI docs)
- **Database:** PostgreSQL 15 + pgvector + TimescaleDB
- **Deployment:** Railway (single service, backend + dashboards)
- **AI/ML:** OpenAI GPT-4 (agents) + text-embedding-3-small (embeddings)
- **Data Source:** SolArk 15K inverter (local network: 192.168.1.23)

---

## 🤖 Multi-Agent System

### Agent Architecture (V1.5)

**Flow:** User Query → KB Fast-Path Check → Manager Agent → Specialist Agent → Response

### 1. Manager Agent (Query Router)
**File:** `railway/src/agents/manager.py`
**Role:** "Query Router and Coordinator"

**Purpose:** Analyze query intent and route to appropriate specialist

**Tools:**
- `route_to_solar_controller(query)` - Real-time status queries
- `route_to_energy_orchestrator(query)` - Planning/optimization queries
- `search_kb_directly(query)` - Documentation queries

**Configuration:**
- Max iterations: 3 (reduced from 10 to prevent over-thinking)
- Delegation: False (routes, doesn't delegate)
- Output: Returns tool output VERBATIM (no reformatting)

**Routing Logic:**
```python
# Real-time questions → Solar Controller
"battery level", "solar production", "current status"

# Planning questions → Energy Orchestrator
"should we", "optimize", "create plan", "recommend"

# Documentation → KB Search (or fast-path)
"specs", "threshold", "policy", "how to", "manual"
```

### 2. Solar Controller Agent
**File:** `railway/src/agents/solar_controller.py`
**Role:** "Energy Systems Monitor and Status Reporter"

**Purpose:** Answer real-time queries about current energy state

**Tools:**
- `get_energy_status()` - Current snapshot from SolArk API (real-time)
- `get_detailed_status()` - Detailed current data with raw numbers
- `get_historical_stats(hours)` - Time-series statistics (avg, min, max)
- `get_time_series_data(hours, limit)` - Raw timestamped records
- `search_knowledge_base()` - Context for explanations

**Response Time:** ~5-6 seconds (includes API call)

**Example Queries:**
- "What's my battery level?" → Uses get_energy_status()
- "How much solar am I producing?" → Uses get_energy_status()
- "Average solar yesterday?" → Uses get_historical_stats(24)

### 3. Energy Orchestrator Agent
**File:** `railway/src/agents/energy_orchestrator.py`
**Role:** "Energy Operations Manager and Optimization Specialist"

**Purpose:** Make planning and optimization decisions

**Tools:**
- `get_current_status()` - Current energy state for decision context
- `get_historical_stats(hours)` - Historical patterns for planning
- `get_time_series_data(hours, limit)` - Raw data for pattern analysis
- `optimize_battery()` - Battery optimization recommendations
- `coordinate_miners()` - Miner scheduling decisions
- `create_energy_plan()` - 24-hour energy planning
- `search_knowledge_base()` - Operating procedures and policies

**Response Time:** ~13-15 seconds (includes analysis + reasoning)

**Example Queries:**
- "Should we run miners tonight?" → Uses current + historical data
- "Create energy plan for today" → Uses create_energy_plan + patterns
- "Best time to charge battery?" → Uses time-series analysis

### KB Fast-Path System (V1.5 Innovation)

**Problem:** KB queries via Manager timing out (20+ seconds)
**Solution:** Keyword detection at API level bypasses Manager entirely
**Performance:** 400ms vs 20s+ (50x improvement)

**Implementation:**
```python
# In /ask endpoint (src/api/main.py)
kb_keywords = ['specification', 'specs', 'threshold', 'policy',
               'procedure', 'maintain', 'documentation', 'guide',
               'manual', 'instructions', 'how do i', 'how to']

if any(keyword in query_lower for keyword in kb_keywords):
    # Direct KB search - bypass Manager
    result = search_knowledge_base.func(query, limit=5)
    agent_used = "Knowledge Base"
    agent_role = "Documentation Search"
else:
    # Manager crew routes to specialist
    crew = create_manager_crew(query, context)
```

**Trade-off:** Keyword matching less intelligent than Manager routing, but vastly faster for common documentation queries.

**Known Limitations (Session 027):**
- "what is" excluded to avoid false positives ("what is my battery level")
- Meta/system queries ("what is command center") miss fast-path
- Solution: Add specific patterns like "what is the command" to keywords

---

### Edge Case Handling (V1.5.1 Planned)

**Query Distribution Analysis (Session 027):**
- **80%** - Energy queries → Routed correctly ✅
- **15%** - Meta/system queries → Need better handling ⚠️
- **5%** - Off-topic queries → Need fallback ⚠️

**Improvement Areas:**
1. **Manager Fallback** - Respond directly to meta/off-topic queries instead of routing
2. **KB Keywords** - Add "what is the command", "system overview" patterns
3. **KB Quality** - Remove irrelevant docs (Cisco switches, generic manuals)
4. **Context Files** - Create concise CommandCenter overview for "what is" queries

**Design Principle:** Keep specialized architecture, improve edge case handling

---

## 📊 Knowledge Base System

### Two-Tier Architecture

**Tier 1: Context Files (CONTEXT Folder)**
- Always loaded baseline knowledge
- Files in `/CONTEXT/` folder in Google Drive
- Flag: `is_context_file = TRUE` in database
- High-priority context for all agents
- Use: Critical facts, thresholds, policies

**Tier 2: Full Knowledge Base (All Folders)**
- Semantic search on demand
- All folders synced from Google Drive
- Vector embeddings (OpenAI text-embedding-3-small, 1536 dim)
- Chunked into 512-token segments
- Use: Detailed procedures, manuals, historical data

### Current Stats (Production)
- **15 documents** synced
- **141,889 tokens** indexed
- **4 folders:** CONTEXT (Tier 1), Bret-ME, SolarShack, Wildfire.Green
- **Supported formats:** Google Docs, PDFs, Google Sheets

### Database Schema
```sql
-- Full documents
CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE,
    title VARCHAR(500),
    folder VARCHAR(500),
    folder_path TEXT,
    mime_type VARCHAR(100),
    full_content TEXT,
    token_count INTEGER,
    is_context_file BOOLEAN DEFAULT FALSE,
    last_synced TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- Chunked content with embeddings
CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id),
    chunk_text TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    created_at TIMESTAMP
);

-- Vector similarity index
CREATE INDEX kb_chunks_embedding_idx ON kb_chunks
USING ivfflat (embedding vector_cosine_ops);
```

### Sync Process
1. Authenticate with Google service account
2. Recursively scan target folder
3. Filter to supported file types
4. Check if modified since last_synced (skip unchanged)
5. Fetch content (format-specific extraction)
6. Chunk into 512-token segments
7. Generate embeddings via OpenAI
8. Upsert to kb_documents table
9. Delete old chunks, insert new chunks
10. Cleanup: Remove documents deleted from Drive
11. Log sync results to kb_sync_log

### Search Process
1. Generate query embedding via OpenAI
2. Cosine similarity search in kb_chunks (pgvector <=> operator)
3. Return top 5 chunks with metadata
4. Format with citations (document title, folder, similarity score)

---

## 💾 Data & Conversation System

### Energy Telemetry Schema
```sql
CREATE TABLE solark.telemetry (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT NOW(),
    soc FLOAT,              -- Battery SOC (%)
    batt_power FLOAT,       -- Battery power (W, +charge/-discharge)
    pv_power FLOAT,         -- Solar production (W)
    load_power FLOAT,       -- House load (W)
    pv_to_grid FLOAT,       -- Grid export (W) - V1.5 addition
    grid_to_load FLOAT,     -- Grid import (W)
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Polling:** Every 30 seconds from SolArk API (192.168.1.23)
**Storage:** TimescaleDB hypertable for efficient time-series queries

### Conversation & Memory System

**Three-Tier Memory:**

1. **Session Context (In-Memory)**
   - Current conversation messages
   - Used for follow-up questions
   - Passed to Manager agent

2. **Conversations (PostgreSQL)**
   - Permanent conversation history
   - Queryable via `/conversations` endpoint
   - Displayed in Logs Viewer

3. **Agent Metadata (Parsed)**
   - `agent_used` (Solar Controller/Energy Orchestrator/KB)
   - `agent_role` (descriptive name)
   - Displayed in chat interface

**Schema:**
```sql
CREATE TABLE agent.conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agent.messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES agent.conversations(id),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    agent_used VARCHAR(100),
    agent_role VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🔌 API Reference

### Core Endpoints
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API version info |
| `/health` | GET | System health check |
| `/db/init-schema` | POST | Initialize database schema |

### Energy Data
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/energy/latest` | GET | Latest energy snapshot |
| `/energy/stats?hours=24` | GET | Energy statistics (avg, min, max) |

### Agent Chat
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ask` | POST | Send message to agents (with KB fast-path) |
| `/conversations` | GET | List recent conversations |
| `/conversations/{session_id}` | GET | Get conversation details |

### Knowledge Base
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/kb/sync` | POST | Sync from Google Drive (streaming) |
| `/kb/preview` | POST | Preview sync (dry run) |
| `/kb/search` | POST | Search KB with embeddings |
| `/kb/stats` | GET | KB statistics |
| `/kb/documents` | GET | List all documents |
| `/kb/folders` | GET | Get folder structure |

**Base URL:** https://api.wildfireranch.us
**Interactive Docs:** https://api.wildfireranch.us/docs

---

## ⚙️ Environment Variables

### Railway Backend
```bash
# Required
DATABASE_URL=postgresql://...              # Auto-provided by Railway
OPENAI_API_KEY=<secret>                    # For embeddings + LLM
SOLARK_API_URL=http://192.168.1.23        # Local network
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>       # Google Drive service account
KB_FOLDER_ID=<google-drive-folder-id>     # Target folder for KB sync

# Optional
API_KEY=<secret>                           # Dashboard auth
ALLOWED_ORIGINS=https://dashboard...       # CORS origins
```

### Railway Dashboard
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
API_KEY=<secret>
```

---

## 🖥️ Dashboard Pages

### 1. Home (Home.py)
- Quick overview metrics (SOC, Solar, Load, Grid Export)
- Navigation shortcuts
- Real-time data from `/energy/latest`

### 2. System Health (1_🏥_System_Health.py)
- API health check
- Database connectivity
- Service status indicators

### 3. Energy Monitor (2_⚡_Energy_Monitor.py)
- 5 real-time metrics: SOC, Solar, Load, Battery Power, Grid Export
- 24-hour statistics
- Auto-refresh capability

### 4. Agent Chat (3_🤖_Agent_Chat.py)
- Conversational interface to CrewAI agents
- Session management
- Displays agent_used and agent_role metadata
- Multi-turn conversation support

### 5. Logs Viewer (4_📊_Logs_Viewer.py)
- Recent conversation history
- Individual conversation details
- Message inspector

**Access:** https://dashboard.wildfireranch.us

---

## 📈 Performance Metrics (V1.5)

| Component | Response Time | Notes |
|-----------|--------------|-------|
| KB Fast-Path | 400ms | Direct search, bypasses Manager |
| KB Routed | 5-6s | Via Manager agent (fallback) |
| Solar Controller | 5-6s | Includes API call to SolArk |
| Energy Orchestrator | 13-15s | Analysis + reasoning |
| Energy API (/latest) | 50-100ms | Direct database query |
| Dashboard Page Load | 1-2s | Includes API calls |

**Key Optimization (Session 024):**
- KB queries: 20s+ → 400ms (50x improvement)
- Method: Fast-path keyword detection at API level
- Trade-off: Speed over perfect intent detection

---

## 🏠 Hardware & Energy System

### Solar Array
- **Inverter:** SolArk 15K hybrid inverter
- **Location:** 192.168.1.23 (local network)
- **Monitoring:** Real-time power generation, daily/lifetime totals
- **Data Source:** SolArk API integration (polled every 30s)

### Battery Storage
- **Chemistry:** Lithium iron phosphate (LiFePO4)
- **Monitoring:** State of charge (SOC), charging/discharging rates, temperature
- **Data Source:** SolArk BMS integration

### Bitcoin Mining
- **Purpose:** Monetize excess solar energy
- **Control:** Currently manual (V2 will add automated pause/resume)
- **Strategy:** Mine when solar abundant, pause when batteries need charging

### Grid Connection
- **Type:** Grid-tied with backup capability
- **Usage:** Supplemental power during low solar periods
- **Monitoring:** Import/export tracking

### Critical Thresholds (From KB Context Files)
- **Minimum SOC:** 30% (never go below)
- **Target SOC:** 80% (optimal)
- **Miner Pause:** Below 50% SOC
- **Miner Resume:** Above 80% SOC

---

## 🔧 Development & Deployment

### File Structure
```
CommandCenter/
├── railway/                    # Backend + Agent System
│   ├── src/
│   │   ├── agents/            # Manager, Solar Controller, Energy Orchestrator
│   │   ├── tools/             # KB search, energy monitor, battery optimizer
│   │   ├── kb/                # Google Drive sync, search logic
│   │   ├── api/               # FastAPI app (main.py has KB fast-path)
│   │   └── utils/             # Database utilities
│   ├── Dockerfile
│   └── requirements.txt
├── dashboards/                 # Streamlit Dashboard
│   ├── Home.py
│   ├── pages/                 # 4 pages
│   ├── components/            # API client
│   └── assets/
├── docs/                      # Documentation
│   ├── V1.5_MASTER_REFERENCE.md  # Primary reference
│   ├── 05-architecture.md        # Detailed architecture
│   ├── ORCHESTRATION_LAYER_DESIGN.md
│   ├── 06-knowledge-base-design.md
│   └── sessions/              # Development history
└── README.md
```

### Deployment Process
```bash
# From repository root
git push origin main

# Railway auto-deploys from main branch
# Uses Dockerfile in railway/ directory
# Build: docker build -f railway/Dockerfile .
# Start: uvicorn src.api.main:app --host 0.0.0.0 --port 8000
```

### Database Migrations
Located in `railway/migrations/`:
- `001_initial_schema.sql` - Agent tables
- `002_knowledge_base.sql` - KB tables
- Track version in `schema_migrations` table
- Apply only new migrations (idempotent)

---

## 🚨 Common Issues & Solutions

### KB Search Returns Empty
1. Check `kb_sync_log` for recent successful sync
2. Verify embeddings generated (`kb_chunks.embedding NOT NULL`)
3. Test query embedding generation (OpenAI API key valid?)
4. Check vector index exists: `\d kb_chunks` in psql

### Agent Timeout
1. Check `OPENAI_API_KEY` is set
2. Verify OpenAI API is reachable
3. Check Manager agent `max_iter` (should be 3)
4. Review agent backstory for iteration-causing patterns

### Dashboard Shows No Data
1. Check `API_KEY` matches between dashboard and backend
2. Verify `RAILWAY_API_URL` is correct
3. Test `/health` endpoint directly
4. Check CORS settings (`ALLOWED_ORIGINS`)

### SolArk Data Missing
1. Verify `SOLARK_API_URL` is reachable from Railway
2. Check local network access (192.168.1.23)
3. Test `/energy/latest` endpoint
4. Check telemetry table has recent data

### Conversation Not Persisted
1. Check `agent.conversations` table exists
2. Verify `session_id` is being generated
3. Check `agent.messages` foreign key constraints
4. Review `/ask` endpoint logging

---

## 🔮 V2 Roadmap (Planned)

### V1.6: Data Foundation (2 weeks)
- Victron Cerbo integration (battery monitoring)
- Shelly power monitoring (per-device consumption)
- Multi-source data collection
- Retention policies (72h raw, 30d hourly, 2yr daily)

### V1.7: Control Foundation (2-3 weeks)
- Manual hardware control (Shelly switches)
- Action logging and verification
- Rollback mechanism
- Safety validation layer

### V1.8: Safety & Preferences (2-3 weeks)
- User-defined rules and thresholds
- Safety validator (SOC limits, grid constraints)
- Email/SMS approval flow
- Pending actions system

### V1.9: Full Observability (2-3 weeks)
- Enhanced chat interface with live progress
- Agent activity monitor
- System health dashboard
- Real-time updates (polling or WebSocket)

### V2.0: Automation Engine (2-3 weeks)
- Rules engine (if/then automation)
- Learning mode (pattern detection)
- Test mode (simulate before execute)
- Emergency controls (kill switch)

**Total Timeline:** 19 weeks (~4.5 months) to full autonomous operation

---

## 📚 Key Documentation

### Primary References
1. **[V1.5_MASTER_REFERENCE.md](docs/V1.5_MASTER_REFERENCE.md)** - Current system state (quick reference)
2. **[05-architecture.md](docs/05-architecture.md)** - Detailed architecture with history
3. **[ORCHESTRATION_LAYER_DESIGN.md](docs/ORCHESTRATION_LAYER_DESIGN.md)** - Manager agent design
4. **[06-knowledge-base-design.md](docs/06-knowledge-base-design.md)** - KB system design
5. **[V2_Roadmap.md](docs/V2_Roadmap.md)** - Future development plan

### Guides
- **[AUTHENTICATION_GUIDE.md](docs/guides/AUTHENTICATION_GUIDE.md)** - OAuth setup
- **[KB_USER_TESTING_GUIDE.md](docs/guides/KB_USER_TESTING_GUIDE.md)** - KB testing
- **[CommandCenter Code Style Guide.md](docs/reference/CommandCenter%20Code%20Style%20Guide.md)** - Coding standards

### Recent Sessions
- **[SESSION_024_SUMMARY.md](docs/sessions/SESSION_024_SUMMARY.md)** - V1.5 walkthrough
- **[SESSION_023_SUMMARY.md](docs/sessions/SESSION_023_SUMMARY.md)** - Bug fixes
- **[SESSION_022_SUMMARY.md](docs/sessions/SESSION_022_SUMMARY.md)** - Production testing

---

## 🎯 Key Design Decisions

### Why CrewAI?
- MIT license (production-friendly)
- Easy multi-agent orchestration
- Active community and updates
- Natural tool integration
- Supports delegation and hierarchical crews

### Why Railway?
- Single deployment for backend + dashboards
- Built-in PostgreSQL with pgvector support
- Pay-per-use pricing
- Simple deployment from GitHub
- Good for long-running processes

### Why KB Fast-Path?
- CrewAI nesting overhead unavoidable
- Documentation queries are frequent
- Latency-sensitive user requirement
- 50x performance improvement (20s → 400ms)
- Trade-off accepted: speed over perfect intent detection

### Why Streamlit Dashboard?
- Fast prototyping
- Python-native (team skillset)
- Built-in components
- Easy Railway deployment
- Desktop-first approach (mobile PWA in V2)

---

## 🔐 Security Notes

### Authentication
- API key authentication for dashboard → backend
- No public endpoints (behind Railway private network)
- SolArk API on local network only (192.168.1.x)

### Secrets Management
- All secrets in Railway environment variables
- Database: Internal Railway network (not exposed)
- Google Drive: Service account OAuth 2.0
- OpenAI API: HTTPS, API key auth

### Input Validation
- All API endpoints use Pydantic models
- Session IDs validated before database queries
- Error handling for malformed requests

---

## 💡 Using This System

### Typical Workflows

**Morning Status Check:**
```
User: "What's the system status?"
→ Manager → Solar Controller
→ Response: SOC, solar, load, grid data
```

**Mining Decision:**
```
User: "Should I run the miner?"
→ Manager → Energy Orchestrator
→ Analysis: Current SOC, forecast, policies
→ Response: Recommendation with reasoning
```

**Documentation Query:**
```
User: "What's the battery SOC threshold?"
→ KB Fast-Path (bypasses Manager)
→ Direct search in KB
→ Response: <500ms with citations
```

**Planning:**
```
User: "Create energy plan for today"
→ Manager → Energy Orchestrator
→ Uses: Current status + historical patterns + KB policies
→ Response: Hour-by-hour plan with recommendations
```

### Agent Response Format

**Solar Controller (JSON):**
```json
{
  "response": "Your battery is at 67% SOC...",
  "agent_used": "Solar Controller",
  "agent_role": "Energy Systems Monitor"
}
```

**KB Fast-Path (Text):**
```
Here's what I found:

1. Minimum SOC: 30%...

[Source: Knowledge Base Search]
```

---

## 📊 System Stats (Current Production)

### Database
- **Tables:** 8 total
  - `agent.*` (4): conversations, messages, memory, logs
  - `solark.*` (1): telemetry
  - `kb_*` (3): documents, chunks, sync_log
- **Extensions:** pgvector, TimescaleDB
- **Size:** ~10 MB (controlled)

### Knowledge Base
- **Documents:** 15 synced
- **Tokens:** 141,889 total
- **Chunks:** 512 tokens each
- **Embeddings:** 1536 dimensions (OpenAI)
- **Folders:** 4 (CONTEXT + 3 others)

### API Usage
- **Endpoints:** 18+ operational
- **SolArk Polling:** Every 30s (within rate limits)
- **OpenAI:** Text-embedding-3-small + GPT-4
- **Cost:** <$1/month for KB operations

---

## 🏆 V1.5 Achievements

### What Works
✅ Real-time energy monitoring (SolArk integration)
✅ Multi-agent routing (Manager → Specialists)
✅ Knowledge base with semantic search
✅ Conversation memory & context
✅ KB fast-path (400ms documentation queries)
✅ 5-page Streamlit dashboard
✅ 18+ API endpoints operational
✅ Production deployed on Railway
✅ Grid export tracking (V1.5 addition)
✅ Compressed UI (50% vertical space reduction)

### Known Limitations
❌ No hardware control yet (read-only, V2 feature)
❌ No real-time push notifications (polling only)
❌ Context only available to Manager agent (not specialists)
❌ Manual KB sync (no auto-sync yet)
❌ Single user only (multi-user in V2)

---

## 🤝 Best Practices

### For Agents
- **Always check KB context files first** (Tier 1 knowledge)
- **Use KB search for detailed procedures** (Tier 2 knowledge)
- **Include citations in responses** (source, folder, similarity)
- **Be honest about uncertainty** (low confidence = say so)
- **Check recent conversation context** (session memory)

### For Developers
- **Use .func() for direct tool calls** (CrewAI convention)
- **Never skip DB migrations** (use numbered SQL files)
- **Test with real APIs** (not just mocks)
- **Deploy on weekends** (on-site for fast recovery)
- **Feature flags for gradual rollout** (deploy disabled, enable later)

### For Users
- **Be specific about timing** ("right now" vs "this afternoon")
- **Ask follow-up questions** (agents maintain context)
- **Request explanations** ("Why do you recommend that?")
- **Combine related questions** ("Status and should I mine?")

---

## 📞 Quick Reference

### URLs
- **Backend API:** https://api.wildfireranch.us
- **Dashboard:** https://dashboard.wildfireranch.us
- **API Docs:** https://api.wildfireranch.us/docs
- **SolArk Inverter:** http://192.168.1.23 (local)

### Key Files
- **Main API:** `railway/src/api/main.py` (has KB fast-path)
- **Manager Agent:** `railway/src/agents/manager.py`
- **Solar Controller:** `railway/src/agents/solar_controller.py`
- **Energy Orchestrator:** `railway/src/agents/energy_orchestrator.py`
- **KB Search:** `railway/src/tools/kb_search.py`

### Version Info
- **Python:** 3.10+
- **CrewAI:** Latest
- **FastAPI:** Latest
- **Streamlit:** Latest
- **PostgreSQL:** 15
- **pgvector:** Latest
- **TimescaleDB:** Latest

---

## 🚀 Getting Started (For New Agents/Developers)

### Read These First
1. This document (CONTEXT_CommandCenter_System.md) - System overview
2. V1.5_MASTER_REFERENCE.md - Quick facts and current state
3. 05-architecture.md - Detailed architecture
4. ORCHESTRATION_LAYER_DESIGN.md - How agents work together

### Then Explore
- API endpoints: https://api.wildfireranch.us/docs
- Dashboard: https://dashboard.wildfireranch.us
- Session history: docs/sessions/ folder
- Code: railway/src/ directory

### Key Concepts
- **Two-tier KB:** Context files (always) + Full KB (on demand)
- **Three agents:** Manager (router) + Solar Controller (status) + Energy Orchestrator (planning)
- **KB fast-path:** Keyword bypass for 50x faster doc queries
- **Conversation memory:** Session context + DB persistence + metadata

---

**System Status:** ✅ Production (V1.5.0)
**Last Updated:** December 10, 2025
**Next Version:** V1.6 (Data Foundation) - 2 weeks

**This context file is designed to be synced to the CommandCenter Knowledge Base for AI agent access.**
