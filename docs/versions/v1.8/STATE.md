# CommandCenter V1.8 System State

**Version:** 1.8.0
**Status:** Production
**Last Updated:** 2025-10-16
**Purpose:** Complete V1.8 system reference (replaces V1.5_MASTER_REFERENCE.md)

---

## ⭐ Quick Facts

### Production URLs
- **Frontend:** https://your-vercel-domain.vercel.app
- **API:** https://api.wildfireranch.us
- **API Docs:** https://api.wildfireranch.us/docs
- **KB Dashboard:** https://mcp.wildfireranch.us/kb
- **SolArk:** http://192.168.1.23 (local network)

### Technology Stack
- **Framework:** CrewAI (multi-agent)
- **Backend:** FastAPI (Railway)
- **Frontend:** Next.js 14 (Vercel)
- **Database:** PostgreSQL 16 + TimescaleDB + pgvector
- **Cache:** Redis (Railway) - NEW in V1.8
- **AI:** OpenAI GPT-4 + text-embedding-3-small
- **Web Search:** Tavily API

---

## 🎉 What's New in V1.8

### Smart Context Loading
- **Query Classification:** Automatic routing (SYSTEM/RESEARCH/PLANNING/GENERAL)
- **Token Budget:** Enforced per query type (1k-4k tokens)
- **Redis Caching:** 5-minute TTL with 60%+ hit rate
- **Performance:** 40-60% token reduction
- **Cost Savings:** $180-$300/year

### Agent Visualization Dashboard
- **Real-time Insights:** 4-tab interface at `/chat`
- **Token Tracking:** Per-query and session totals
- **Cache Metrics:** Hit rate, savings, performance
- **Agent Breakdown:** Contribution analysis
- **Accessibility:** WCAG 2.1 AA compliant

### Testing Infrastructure
- **Interactive Dashboard:** `/testing` route
- **Memory Monitor:** Real-time leak detection
- **Performance Bench:** Stress testing tools
- **Edge Cases:** 10 comprehensive tests (all passing)

### Research Agent (V1.7)
- **Web Search:** Tavily integration for current info
- **Smart Routing:** Research queries → Research Agent
- **Tools:** `tavily_search`, `tavily_extract`

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   PRODUCTION STACK                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Vercel (Next.js Frontend)                                  │
│  ├─ / (Home - Live energy dashboard)                        │
│  ├─ /dashboard (Historical charts)                          │
│  ├─ /chat (Agent interaction + Viz Panel) ✨ V1.8!          │
│  ├─ /kb (Knowledge Base Dashboard)                          │
│  ├─ /agents (Agent Monitor)                                 │
│  ├─ /testing (Developer Testing Dashboard) ✨ V1.8!         │
│  ├─ /energy (Power flow details)                            │
│  ├─ /logs (Activity history)                                │
│  └─ /status (System health)                                 │
│         │                                                    │
│         └──────────→ Railway (FastAPI API)                  │
│                      └─ api.wildfireranch.us                │
│                                                              │
│  Railway PostgreSQL (TimescaleDB + pgvector)                │
│  └─ Used by API                                             │
│                                                              │
│  Railway Redis ✨ NEW!                                       │
│  └─ Smart Context Caching (V1.8)                            │
│                                                              │
│  Local Development Services:                                │
│  ├─ Streamlit Ops Dashboard (Port 8502)                     │
│  └─ MCP Server (Port 8080)                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 Active Agents (4 Total)

### 1. Manager Agent (Query Router)
**File:** `railway/src/agents/manager.py`
**Role:** Query Router and Coordinator
**Max Iterations:** 3 (optimized)

**Tools:**
- `route_to_solar_controller(query)` - Real-time status
- `route_to_energy_orchestrator(query)` - Planning/optimization
- `route_to_research_agent(query)` - Web search queries
- `search_kb_directly(query)` - Documentation

**Routing Logic:**
- Real-time questions (battery, solar, current) → Solar Controller
- Planning questions (should we, optimize) → Energy Orchestrator
- Research questions (industry info, current trends) → Research Agent
- Documentation questions (specs, threshold, how-to) → KB Search

### 2. Solar Controller Agent
**File:** `railway/src/agents/solar_controller.py`
**Role:** Energy Systems Monitor and Status Reporter
**Response Time:** ~5-6 seconds (real-time), ~3-5s (historical)

**Tools:**
- `get_energy_status()` - Current snapshot from SolArk
- `get_detailed_status()` - Detailed current data
- `get_historical_stats(hours)` - Time-series statistics
- `get_time_series_data(hours, limit)` - Raw timestamped records
- `search_knowledge_base()` - Context for explanations

**Example Queries:**
- "What's my battery level?"
- "How much solar am I producing?"
- "What was my average solar production yesterday?"

### 3. Energy Orchestrator Agent
**File:** `railway/src/agents/energy_orchestrator.py`
**Role:** Energy Operations Manager and Optimization Specialist
**Response Time:** ~13-15 seconds

**Tools:**
- `get_current_status()` - Current energy state
- `get_historical_stats(hours)` - Time-series for planning
- `optimize_battery()` - Battery recommendations
- `coordinate_miners()` - Miner scheduling
- `create_energy_plan()` - 24-hour planning
- `search_knowledge_base()` - Operating procedures

**Example Queries:**
- "Should we run the miners tonight?"
- "Create an energy plan for today"
- "When's the best time to charge the battery?"

### 4. Research Agent (V1.7)
**File:** `railway/src/agents/research_agent.py`
**Role:** Industry Research and Current Information Specialist
**Response Time:** ~27 seconds

**Tools:**
- `tavily_search(query)` - Web search for current info
- `tavily_extract(urls)` - Extract content from URLs
- `search_knowledge_base()` - Internal documentation

**Example Queries:**
- "What are the latest solar inverter trends?"
- "Current Bitcoin mining profitability"
- "Best practices for LiFePO4 battery maintenance"

---

## ⚡ Smart Context Loading (V1.8)

### Query Classification System
Automatically categorizes queries and applies appropriate token budgets:

| Type | Budget | Use Case | Example |
|------|--------|----------|---------|
| SYSTEM | 2k tokens | Hardware-specific queries | "What's my battery level?" |
| RESEARCH | 4k tokens | Industry research | "Latest solar tech?" |
| PLANNING | 3.5k tokens | Optimization decisions | "Should we mine?" |
| GENERAL | 1k tokens | Casual conversation | "Good morning" |

### Redis Caching
- **Cache Key:** Query hash + classification
- **TTL:** 5 minutes
- **Hit Rate:** 60%+ in production
- **Graceful Degradation:** Falls back to full context if Redis unavailable

### Performance Metrics
- **Token Reduction:** 40-60% (5k-8k → 2k-4k)
- **Cost Savings:** $180-$300/year
- **Response Time:** No degradation (caching actually improves)
- **Cache Hit Latency:** < 10ms

---

## 📊 API Endpoints (18+)

### Core
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | API version info |
| `/health` | GET | System health check |
| `/system/stats` | GET | System statistics (DB record counts) |

### Database Management
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/db/init-schema` | POST | Initialize database schema |
| `/db/schema-status` | GET | Check database schema status |
| `/db/run-health-migration` | POST | Run health monitoring migration (004) |
| `/db/run-solark-migration` | POST | Run SolArk schema migration (005) |

### Energy Data
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/energy/latest` | GET | Latest energy snapshot |
| `/energy/stats?hours=24` | GET | Energy statistics (avg, min, max) |

### Agent Chat
| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/ask` | POST | Send message to agents (with smart context) |
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
| `/kb/context-test` | GET | Diagnostic endpoint (V1.8) |

---

## 🗄️ Database Schema

### Agent Schema (agent.*)

```sql
-- Conversations
CREATE TABLE agent.conversations (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages
CREATE TABLE agent.messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER REFERENCES agent.conversations(id),
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    agent_used VARCHAR(100),
    agent_role VARCHAR(200),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_conversations_session_id ON agent.conversations(session_id);
CREATE INDEX idx_messages_conversation_id ON agent.messages(conversation_id);
CREATE INDEX idx_messages_created_at ON agent.messages(created_at DESC);
```

### SolArk Schema (solark.*)

```sql
-- Telemetry (TimescaleDB hypertable support)
-- Migration: 005_solark_schema.sql (Session 034)
CREATE TABLE solark.telemetry (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Battery metrics
    soc FLOAT,                    -- State of Charge (%)
    batt_power FLOAT,             -- Battery power (W, + = charging, - = discharging)
    batt_voltage FLOAT,           -- Battery voltage (V)
    batt_current FLOAT,           -- Battery current (A)

    -- Solar metrics
    pv_power FLOAT,               -- Total PV production (W)
    pv_voltage FLOAT,             -- PV voltage (V)
    pv_current FLOAT,             -- PV current (A)

    -- Load metrics
    load_power FLOAT,             -- Total load consumption (W)

    -- Grid metrics
    grid_power FLOAT,             -- Grid power (W, + = export, - = import)
    pv_to_grid FLOAT,             -- PV to grid export (W)
    grid_to_load FLOAT,           -- Grid to load import (W)

    -- Power flow indicators
    pv_to_load BOOLEAN DEFAULT FALSE,
    pv_to_bat BOOLEAN DEFAULT FALSE,
    bat_to_load BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX idx_solark_telemetry_timestamp ON solark.telemetry(timestamp DESC);
CREATE INDEX idx_solark_telemetry_plant_id ON solark.telemetry(plant_id);
CREATE INDEX idx_solark_telemetry_created_at ON solark.telemetry(created_at DESC);
```

### Knowledge Base Schema (public)

```sql
-- Documents
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
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Chunks with embeddings
CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id),
    chunk_text TEXT,
    chunk_index INTEGER,
    token_count INTEGER,
    embedding VECTOR(1536),  -- OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sync log
CREATE TABLE kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(50),
    documents_processed INTEGER,
    documents_updated INTEGER,
    documents_failed INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(100)
);

-- Vector index
CREATE INDEX kb_chunks_embedding_idx ON kb_chunks
USING ivfflat (embedding vector_cosine_ops);
```

---

## 🔧 Environment Variables

### Backend (Railway)
```bash
# Required
DATABASE_URL=postgresql://...              # Auto-provided by Railway
REDIS_URL=redis://...                      # Auto-provided by Railway (V1.8)
OPENAI_API_KEY=<secret>                    # For embeddings + LLM
TAVILY_API_KEY=<secret>                    # For web search (V1.7)
SOLARK_API_URL=http://192.168.1.23        # Local network
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>       # Google Drive service account
KB_FOLDER_ID=<google-drive-folder-id>     # Target folder for KB sync

# Optional
API_KEY=<secret>                           # Dashboard auth
ALLOWED_ORIGINS=https://dashboard...       # CORS origins
```

### Frontend (Vercel)
```bash
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us  # If using CrewAI Studio
```

---

## 📈 Performance Metrics

| Component | V1.7 | V1.8 | Improvement |
|-----------|------|------|-------------|
| Avg Token Usage | 5k-8k | 2k-4k | 40-60% ↓ |
| Solar Controller | 5-6s | 5-6s | Stable |
| Energy Orchestrator | 13-15s | 13-15s | Stable |
| Research Agent | 27s | 27s | Stable |
| Cache Hit Rate | N/A | 60%+ | New |
| API Response (/latest) | 50-100ms | 50-100ms | Stable |

---

## 🚨 Quick Troubleshooting

### KB Search Returns Empty
1. Check `kb_sync_log` for recent successful sync
2. Verify embeddings were generated (`kb_chunks.embedding NOT NULL`)
3. Test query embedding generation (OpenAI API key valid?)
4. Check vector index exists: `\d kb_chunks` in psql

### Agent Timeout
1. Check `OPENAI_API_KEY` is set
2. Verify OpenAI API is reachable
3. Check Manager agent `max_iter` (should be 3)
4. Review agent backstory for iteration-causing patterns

### Redis Connection Issues
1. Verify `REDIS_URL` environment variable
2. Check Railway Redis service status
3. System gracefully degrades if Redis unavailable
4. Check logs for connection errors

### Smart Context Not Working
1. Test `/kb/context-test` endpoint
2. Verify Redis is running
3. Check query classification logic
4. Review context loading in agent backstories

---

## 🛠️ File Locations

### Backend Core
- **API:** `railway/src/api/main.py` (includes smart context loading)
- **Agents:** `railway/src/agents/`
- **Tools:** `railway/src/tools/`
- **KB:** `railway/src/kb/`
- **Database:** `railway/src/utils/db.py`
- **Context Loading:** `railway/src/utils/context_loader.py` (V1.8)

### Frontend (Next.js)
- **Pages:** `vercel/app/` (App Router)
- **Components:** `vercel/components/`
- **Agent Viz:** `vercel/components/AgentVisualization.tsx` (V1.8)
- **Testing:** `vercel/app/testing/` (V1.8)

### Documentation
- **Current State:** `docs/versions/v1.8/STATE.md` (this file)
- **API Reference:** `docs/versions/v1.8/API_REFERENCE.md`
- **Deployment:** `docs/versions/v1.8/DEPLOYMENT.md`
- **Release Notes:** `docs/versions/v1.8/RELEASE_NOTES.md`

---

## 🎯 Production Statistics (V1.8)

- **Documents Synced:** 15
- **Total Tokens:** 147K
- **Folders:** 4 (CONTEXT + 3)
- **Database Tables:** 8
- **API Endpoints:** 18+
- **Frontend Pages:** 9
- **Active Agents:** 4
- **Cache Hit Rate:** 60%+
- **Token Reduction:** 40-60%
- **Annual Cost Savings:** $180-$300

---

## 📊 V1.8 Validation (2025-10-16)

**Comprehensive V1-V2 Validation Audit completed. See [Session 033](docs/sessions/2025-10/session-033-v1-v2-validation-audit.md) for full details.**

### Performance Claims Validated
- ✅ **Token Reduction:** 79-87% (exceeds claimed 40-60%)
- ✅ **Cache Hit Rate:** Confirmed working (Redis operational)
- ✅ **Cost Savings:** $474/year (exceeds claimed $180-$300)
- ⚠️ **Response Time:** 10s avg (acceptable, includes LLM latency)

### System Health: 🟢 EXCELLENT (85% tested)
- **Total Features:** 89 inventoried
- **Production-Ready:** 85%
- **Critical Issues:** 0 (solark.telemetry fixed in Session 034 ✅)
- **Overall Readiness Score:** 8.7/10 ⭐⭐⭐⭐

### V2.0 Readiness: 🟢 GO (10-week MVP achievable)
- **Early Wins:** 2 of 8 V2.0 features already complete (25% head start)
- **Timeline Savings:** 4-6 weeks (from 16 weeks to 10-12 weeks)
- **Critical Blocker:** User preferences system (2 weeks to implement)

**Full Audit Reports:**
- [Feature Inventory](docs/sessions/2025-10/validation-audit-feature-inventory.md) - 89 features catalogued
- [V2.0 Comparison](docs/sessions/2025-10/validation-audit-v2-comparison.md) - Gap analysis & timeline
- [Test Results](docs/sessions/2025-10/validation-audit-test-results.md) - Performance validation
- [V2.0 Readiness](docs/sessions/2025-10/validation-audit-v2-readiness.md) - 10-dimensional scoring

---

## 🔮 Roadmap

### V1.9 (Deferred)
- Enhanced monitoring and observability
- Additional hardware integrations (Victron completion, Shelly)
- Advanced analytics dashboard

### V2.0 MVP (10 weeks - Recommended)
**Must-Have:**
- ✅ Unified Architecture (DONE in V1.8)
- ✅ Smart Context Loading (DONE in V1.8)
- 🔴 User Preferences (2 weeks)
- 🔴 Proactive Alerts (2 weeks)
- 🔴 Weather Integration (2 weeks)
- ✅ Victron Integration (1 week to complete)

**Defer to V2.1:**
- ML Optimization (3 weeks)
- Mobile Native App (4 weeks - use responsive web/PWA for V2.0)

### V2.0 Vision (Original)
- Full automation engine
- Mobile app (React Native or PWA)
- WebSocket real-time updates
- Multi-tenant support

---

## 📞 Support & Resources

### Dashboards
- **Railway:** app.railway.app (backend/dashboard/DB)
- **Vercel:** vercel.com/dashboard
- **API Docs:** https://api.wildfireranch.us/docs

### Related Documentation
- **Architecture:** `/docs/reference/architecture-decisions.md`
- **Code Style:** `/docs/reference/code-style.md`
- **Deployment:** `/docs/versions/v1.8/DEPLOYMENT.md`
- **Migration from V1.7:** `/docs/versions/v1.8/MIGRATION.md`

---

**V1.8 System State Reference**
**Last Updated:** 2025-10-16
**Status:** Production Ready ✅
