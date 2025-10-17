# CommandCenter Quick Reference

**Version:** 1.5.0 | **Last Updated:** Dec 10, 2025 | **Status:** Production

---

## 🚀 Essential Facts

### URLs
- **Backend API:** https://api.wildfireranch.us
- **Dashboard:** https://dashboard.wildfireranch.us
- **API Docs:** https://api.wildfireranch.us/docs
- **SolArk:** http://192.168.1.23 (local)

### Tech Stack
- **Framework:** CrewAI (multi-agent)
- **Backend:** FastAPI (Railway)
- **Frontend:** Streamlit (Railway)
- **Database:** PostgreSQL 15 + pgvector + TimescaleDB
- **AI:** OpenAI GPT-4 + text-embedding-3-small

---

## 🤖 The Three Agents

### 1. Manager Agent (Router)
**Role:** Routes queries to the right specialist
**Tools:** route_to_solar_controller, route_to_energy_orchestrator, search_kb_directly
**When Used:** Every query (unless KB fast-path)

### 2. Solar Controller (Status)
**Role:** Real-time energy monitoring
**Tools:** get_energy_status, get_historical_stats, search_knowledge_base
**Response Time:** ~5-6 seconds
**Use For:** "What's my battery level?", "How much solar?", "Current status?"

### 3. Energy Orchestrator (Planning)
**Role:** Planning and optimization
**Tools:** optimize_battery, coordinate_miners, create_energy_plan, search_knowledge_base
**Response Time:** ~13-15 seconds
**Use For:** "Should we mine?", "Create plan", "Best time to charge?"

---

## ⚡ KB Fast-Path (The Secret Sauce)

**What:** Bypasses Manager for doc queries
**Performance:** 400ms vs 20s+ (50x faster)
**Triggers:** specs, threshold, policy, how to, manual, guide, instructions
**Example:** "What's the battery SOC threshold?" → Direct KB search

---

## 📊 Key Endpoints

### Energy
- `GET /energy/latest` - Current snapshot
- `GET /energy/stats?hours=24` - Statistics

### Agents
- `POST /ask` - Send query to agents
- `GET /conversations` - Chat history
- `GET /conversations/{id}` - Details

### Knowledge Base
- `POST /kb/sync` - Manual sync (streaming)
- `POST /kb/search` - Search KB
- `GET /kb/stats` - KB statistics

---

## 🗄️ Database Schemas

### Agent Tables (agent.*)
- **conversations** - Session tracking
- **messages** - User/assistant messages (with agent_used, agent_role)

### Energy Tables (solark.*)
- **telemetry** - Time-series data (TimescaleDB)
  - soc, batt_power, pv_power, load_power, pv_to_grid, grid_to_load

### Knowledge Base (public)
- **kb_documents** - Full docs (is_context_file flag)
- **kb_chunks** - 512-token chunks with embeddings (VECTOR(1536))
- **kb_sync_log** - Sync history

---

## 🔧 Environment Variables

### Backend (Railway)
```bash
DATABASE_URL=<auto>           # Railway provides
OPENAI_API_KEY=<secret>       # For AI + embeddings
SOLARK_API_URL=http://192.168.1.23
GOOGLE_SERVICE_ACCOUNT_JSON=<secret>
KB_FOLDER_ID=<folder-id>
API_KEY=<secret>              # Optional auth
```

### Dashboard (Railway)
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
API_KEY=<secret>
```

---

## 📈 Performance Targets

| Component | Target | Actual |
|-----------|--------|--------|
| KB Fast-Path | <1s | 400ms ✅ |
| Solar Controller | <10s | 5-6s ✅ |
| Energy Orchestrator | <20s | 13-15s ✅ |
| Energy API | <200ms | 50-100ms ✅ |

---

## 🏠 Hardware Thresholds

### Battery (From Context Files)
- **Minimum SOC:** 30% (never below)
- **Target SOC:** 80% (optimal)
- **Miner Pause:** <50% SOC
- **Miner Resume:** >80% SOC

### System
- **Solar Array:** 15kW capacity
- **Battery:** 40kWh LiFePO4
- **Inverter:** SolArk 15K
- **Polling:** Every 30 seconds

---

## 🚨 Quick Troubleshooting

### KB Search Empty?
1. Check `kb_sync_log` for recent sync
2. Verify embeddings exist (`kb_chunks.embedding NOT NULL`)
3. Test OpenAI API key

### Agent Timeout?
1. Check `OPENAI_API_KEY` set
2. Verify Manager `max_iter = 3`
3. Check agent backstory (no iteration loops)

### Dashboard No Data?
1. Verify `API_KEY` matches
2. Check `RAILWAY_API_URL` correct
3. Test `/health` endpoint

### SolArk Missing?
1. Verify `SOLARK_API_URL` reachable
2. Check local network (192.168.1.23)
3. Test `/energy/latest`

---

## 💡 Agent Query Examples

### Real-Time Status
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}'
```
→ Solar Controller (~5s)

### Planning
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Should we run miners now?"}'
```
→ Energy Orchestrator (~15s)

### Documentation
```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum SOC threshold?"}'
```
→ KB Fast-Path (~400ms)

---

## 📚 Two-Tier Knowledge Base

### Tier 1: Context Files (CONTEXT Folder)
- **Always loaded** in agent prompts
- **No search needed** (instant access)
- **Use for:** Critical facts, thresholds, policies
- **Flag:** `is_context_file = TRUE`

### Tier 2: Full KB (All Folders)
- **Searched on demand** (semantic search)
- **512-token chunks** with embeddings
- **Use for:** Detailed procedures, manuals
- **Search:** pgvector cosine similarity

---

## 🔐 Security Notes

- API key auth (dashboard → backend)
- Railway private network (no public DB)
- SolArk on local network only
- All secrets in env vars (not code)
- Pydantic validation on all endpoints

---

## 🎯 File Locations

### Backend Core
- API: `railway/src/api/main.py` (has KB fast-path)
- Agents: `railway/src/agents/`
- Tools: `railway/src/tools/`
- KB: `railway/src/kb/`

### Dashboard
- Pages: `dashboards/Home.py`, `dashboards/pages/`
- API Client: `dashboards/components/api_client.py`

### Docs
- Primary: `docs/V1.5_MASTER_REFERENCE.md`
- Architecture: `docs/05-architecture.md`
- Context: `docs/CONTEXT_CommandCenter_System.md`

---

## 🚀 Deployment

### From GitHub
```bash
git push origin main
# Railway auto-deploys
```

### Database Migration
```bash
curl -X POST https://api.wildfireranch.us/db/init-schema \
  -H "Content-Type: application/json"
```

### Check Health
```bash
curl https://api.wildfireranch.us/health | jq
```

---

## 📊 Current Production Stats

- **Documents:** 15 synced
- **Tokens:** 141,889 total
- **Folders:** 4 (CONTEXT + 3)
- **Tables:** 8 total
- **API Endpoints:** 18+
- **Dashboard Pages:** 5
- **Agents:** 3 active

---

## 🔮 V2 Roadmap (Upcoming)

- **V1.6 (2 weeks):** Victron Cerbo + Shelly integration
- **V1.7 (2-3 weeks):** Hardware control (manual)
- **V1.8 (2-3 weeks):** Safety rules + preferences
- **V1.9 (2-3 weeks):** Full observability
- **V2.0 (2-3 weeks):** Automation engine

**Total:** ~4.5 months to full autonomy

---

## 🛠️ Critical Design Decisions

### Why CrewAI?
MIT license, multi-agent, active community, easy tool integration

### Why Railway?
Single service (backend + dashboards), PostgreSQL included, GitHub auto-deploy

### Why KB Fast-Path?
CrewAI nesting overhead unavoidable, 50x improvement for doc queries

### Why Streamlit?
Fast prototyping, Python-native, desktop-first approach

---

## ✅ Best Practices

### For Agents
- Check context files first (Tier 1)
- Use KB search for details (Tier 2)
- Include citations in responses
- Be honest about uncertainty

### For Developers
- Use `.func()` for direct tool calls (CrewAI)
- Never skip DB migrations
- Test with real APIs (not mocks)
- Deploy on weekends (on-site)

### For Users
- Be specific about timing ("now" vs "later")
- Ask follow-ups (context maintained)
- Request explanations ("Why?")
- Combine related questions

---

## 📞 Emergency Contacts

### Services
- **Railway:** app.railway.app (backend/dashboard/DB)
- **Google Drive:** KB sync source
- **OpenAI:** API for agents + embeddings

### Rollback
```bash
# Revert deployment in Railway dashboard
# Or drop new schema:
DROP SCHEMA IF EXISTS new_schema CASCADE;
```

---

**Quick Reference | V1.5.0 | Production Ready**

For detailed info, see: [CONTEXT_CommandCenter_System.md](CONTEXT_CommandCenter_System.md)
