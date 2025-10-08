# CommandCenter

AI-powered energy management system with CrewAI agents, MCP integration, and production-ready multi-platform deployment.

## 🎯 Project Status

**Current Phase:** Production Deployment Complete! 🚀
**Progress:** 99% complete
**Last Updated:** 2025-10-08 (Session 018D - KB Dashboard Operational!)

### Quick Stats
- ✅ **Production Services:** 2 deployed (API, Frontend)
- ✅ **Agents:** 1 operational (Solar Controller with memory)
- ✅ **API Endpoints:** 18+ operational endpoints
- ✅ **Frontend Pages:** 7 complete pages with live data
- ✅ **Knowledge Base:** ⚡ **OPERATIONAL!** 15 docs synced, deletion handling, collapsible UI
- ✅ **MCP Server:** Ready for Claude Desktop
- ✅ **Streamlit Ops Dashboard:** 4 pages running locally
- ✅ **Database:** PostgreSQL + TimescaleDB + pgvector on Railway
- 🎉 **Status:** Production-ready and battle-tested!

---

## 🏗️ Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   PRODUCTION STACK                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Vercel (Next.js Frontend)                                  │
│  ├─ / (Home - Live energy dashboard)                        │
│  ├─ /dashboard (Historical charts)                          │
│  ├─ /chat (Agent interaction)                               │
│  ├─ /kb (Knowledge Base Dashboard) ✨ OPERATIONAL!          │
│  ├─ /energy (Power flow details)                            │
│  ├─ /logs (Activity history)                                │
│  └─ /status (System health)                                 │
│         │                                                    │
│         └──────────→ Railway (FastAPI API)                  │
│                      └─ api.wildfireranch.us                │
│                                                              │
│  Railway PostgreSQL (TimescaleDB)                           │
│  └─ Used by API                                             │
│                                                              │
│  Local Development Services:                                │
│  ├─ Streamlit Ops Dashboard (Port 8502)                     │
│  └─ MCP Server (Port 8080)                                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Production URLs
- **Frontend:** Your Vercel domain
- **API:** https://api.wildfireranch.us
- **KB Dashboard:** https://mcp.wildfireranch.us/kb ⚡ **NEW!**
- **API Docs:** https://api.wildfireranch.us/docs
- **Database:** PostgreSQL on Railway (internal)

---

## ✨ Features

### Completed ✅

#### Frontend (Next.js + TypeScript)
- **7 Complete Pages:**
  - Home dashboard with real-time energy data
  - Energy analytics with Recharts visualizations
  - Agent chat interface
  - Knowledge Base dashboard (Google Drive sync)
  - Detailed energy metrics and power flow
  - Activity logs (conversations & energy data)
  - System health monitoring
- **Real-time Updates:** Auto-refresh every 10-30 seconds
- **Responsive Design:** Mobile-first with Tailwind CSS
- **Bitcoin Punk Icons:** Character-based navigation
- **OAuth Authentication:** Google sign-in with auto-redirect protection

#### Backend (FastAPI + Python)
- **Energy Management:**
  - SolArk data collection and persistence
  - TimescaleDB time-series storage
  - Historical data queries and statistics
- **AI Agent System:**
  - Multi-turn conversations with context
  - CrewAI-powered solar controller agent
  - Conversation history and retrieval
- **Knowledge Base System:** ⚡ **OPERATIONAL!**
  - Google Drive integration (service account + OAuth)
  - Multi-format support (Google Docs, PDFs, Spreadsheets)
  - Full & Smart sync with real-time progress tracking
  - Automatic deletion detection and cleanup
  - Vector embeddings with pgvector (OpenAI)
  - Semantic search capabilities
  - Context file management (CONTEXT folder)
  - Collapsible folder tree UI
  - 15 documents synced, 141k tokens indexed
- **API Endpoints:**
  - `/health` - System health checks
  - `/energy/*` - Energy data and statistics
  - `/agent/*` - AI agent interaction
  - `/conversations/*` - Chat history
  - `/system/*` - System statistics
  - `/kb/*` - Knowledge base sync and search

#### CrewAI Studio (Streamlit)
- **No-Code Agent Builder:**
  - Visual agent creation
  - Crew configuration and management
  - Task workflow setup
  - Knowledge source integration
  - Custom tool support
- **Production Deployment:**
  - Railway deployment ready
  - PostgreSQL integration
  - Multi-LLM support (OpenAI, Anthropic, Ollama, Groq)

#### Infrastructure
- **Database:** PostgreSQL 16 + TimescaleDB + pgvector extensions
- **Deployment:** Railway (API, Studio, DB) + Vercel (Frontend)
- **Monitoring:** Health checks and integration tests
- **Documentation:** Comprehensive deployment guides
- **Authentication:** NextAuth.js with Google OAuth

### In Progress 🔄
- Production monitoring setup
- Additional hardware integrations (Shelly, Miners)

### Planned 📋 (See [KB_ROADMAP.md](KB_ROADMAP.md) for details)
- **Knowledge Base Enhancements:**
  - Settings implementation (auto-sync, configurable params)
  - Advanced search with filters
  - Additional file types (Word, PowerPoint, Markdown)
  - Bulk operations (multi-select, delete, re-sync)
  - Analytics dashboard
- **System Enhancements:**
  - Optimization automation
  - Scheduled crew execution
  - WebSocket real-time updates
  - Redis caching layer
  - Mobile app (React Native)

---

## 📚 Documentation

### Quick Start Guides
- **[QUICK_START.md](QUICK_START.md)** - 5-minute production deployment
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Complete step-by-step guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Full system architecture

### Service-Specific Guides
- **[CrewAI Studio Railway Setup](crewai-studio/RAILWAY_SETUP.md)** - Railway deployment
- **[MCP Server Setup](mcp-server/INSTALL.md)** - Claude Desktop integration
- **[Streamlit Ops Dashboard](dashboards/README.md)** - Admin dashboard guide
- **[Authentication Guide](docs/AUTHENTICATION_GUIDE.md)** - How to protect pages with OAuth

### Knowledge Base Documentation
- **[KB_ROADMAP.md](KB_ROADMAP.md)** - Complete feature roadmap and future plans
- **[Session 018D Summary](docs/SESSION_018D_FILES_TAB_COMPLETION.md)** - Latest: Files tab + deletion handling
- **[Session 018C Summary](docs/SESSION_018C_SYNC_IMPROVEMENTS.md)** - Sync improvements
- **[Session 018B Testing Guide](docs/SESSION_018B_TESTING_GUIDE.md)** - End-to-end testing
- **[Session 018 Summary](docs/SESSION_018_COMPLETION_SUMMARY.md)** - Initial KB implementation

### Other Session Notes
- **[Session 012 Summary](docs/sessions/SESSION_012_SUMMARY.md)** - Production deployment
- **[Session 011 Summary](SESSION_011_SUMMARY.md)** - Frontend integration
- **[All Session Notes](docs/sessions/)** - Complete development history

### API Documentation
- **[Interactive API Docs](https://api.wildfireranch.us/docs)** - Swagger UI
- **[ReDoc](https://api.wildfireranch.us/redoc)** - Alternative API docs

---

## 🚀 Quick Start

### 1. Deploy to Production (5 Minutes)

```bash
# Already done if you followed Session 012!
# If not, see QUICK_START.md for complete guide

# 1. CrewAI Studio is on Railway ✅
# 2. API is on Railway ✅
# 3. Frontend is on Vercel ✅
# 4. Just add NEXT_PUBLIC_STUDIO_URL to Vercel
```

### 2. Use with Claude Desktop (MCP)

```bash
# Install MCP Server
cd mcp-server
npm install
npm run build

# Configure Claude Desktop
# Follow: mcp-server/INSTALL.md

# Use the tools:
# - ask_agent - Chat with solar controller
# - get_energy_data - Get current energy stats
# - get_solar_stats - Get solar production data
```

### 3. Local Development

```bash
# Start all services locally

# Terminal 1: Next.js Frontend
cd vercel
npm run dev
# → http://localhost:3001

# Terminal 2: CrewAI Studio
cd crewai-studio
streamlit run app/app.py --server.port 8501
# → http://localhost:8501

# Terminal 3: Streamlit Ops Dashboard
cd dashboards
streamlit run Home.py --server.port 8502
# → http://localhost:8502

# Terminal 4: MCP Server (optional)
cd mcp-server
npm run dev
# → localhost:8080
```

### 4. Run Tests

```bash
# Health check all services
./scripts/health-check.sh

# Integration tests
./scripts/test-integration.sh

# Deployment status
./scripts/check-deployment.sh
```

---

## 🛠️ Tech Stack

### Frontend
- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **Charts:** Recharts
- **Icons:** Lucide React
- **Deployment:** Vercel

### Backend
- **API:** FastAPI (Python 3.12)
- **Database:** PostgreSQL 16 + TimescaleDB
- **ORM:** SQLAlchemy
- **AI:** CrewAI + LangChain
- **LLM:** OpenAI GPT-4
- **Deployment:** Railway

### Agent Studio
- **Framework:** Streamlit
- **Database:** PostgreSQL (shared)
- **Features:** No-code agent builder
- **LLM Support:** OpenAI, Anthropic, Ollama, Groq
- **Deployment:** Railway

### Infrastructure
- **Hosting:** Railway (backend) + Vercel (frontend)
- **Database:** Railway PostgreSQL
- **CI/CD:** GitHub + Auto-deploy
- **Monitoring:** Built-in health checks

---

## 📋 Environment Variables

### Vercel (Next.js)
```env
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us
```

### Railway API (FastAPI)
```env
DATABASE_URL=<auto-configured>
SOLARK_API_KEY=<your-solark-key>
OPENAI_API_KEY=<your-openai-key>
```

### Railway Studio (CrewAI)
```env
OPENAI_API_KEY=<your-openai-key>
DB_URL=${{Postgres.DATABASE_URL}}
PORT=${{PORT}}
```

---

## 🧪 Testing

### Automated Tests
```bash
# Health check (all services)
./scripts/health-check.sh

# Integration tests (API)
./scripts/test-integration.sh
```

### Manual Testing
- [ ] Frontend loads with live energy data
- [ ] Dashboard shows charts
- [ ] Chat sends/receives agent messages
- [ ] Studio loads in iframe
- [ ] Energy page shows power flow
- [ ] Logs display conversations
- [ ] Status page reports health

---

## 🎯 Project Highlights

### Production-Grade Features
✅ **Robust Error Handling** - Graceful degradation and fallbacks
✅ **Comprehensive Testing** - Automated health checks
✅ **Complete Documentation** - Deployment and architecture guides
✅ **Monitoring** - Health endpoints and system stats
✅ **Security** - Environment variables, HTTPS everywhere
✅ **Scalability** - Railway auto-scaling, Vercel CDN

### Innovation
- Multi-agent AI system with CrewAI
- Real-time energy monitoring with TimescaleDB
- No-code agent builder (CrewAI Studio)
- Claude Desktop integration via MCP
- Bitcoin punk character navigation

---

## 🤝 Contributing

This is a private project, but we follow best practices:
- Comprehensive commit messages
- Session-based development tracking
- Complete documentation
- Test coverage for critical paths

---

## 📝 License

Private Project - WildfireRanch © 2025

---

## 🆘 Support & Resources

### Documentation
- [Quick Start](QUICK_START.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Architecture](ARCHITECTURE.md)

### Dashboards
- [Railway](https://railway.app/dashboard)
- [Vercel](https://vercel.com/dashboard)
- [API Docs](https://api.wildfireranch.us/docs)

### Issues
- [GitHub Issues](https://github.com/WildfireRanch/CommandCenter/issues)
- Session notes in `/docs/sessions/`

---

## 🎉 Recent Updates

**Session 018C (2025-10-08):**
- ✅ Implemented Google OAuth auto-redirect authentication
- ✅ Added PDF document support to Knowledge Base
- ✅ Added Google Sheets support to Knowledge Base
- ✅ Fixed smart sync change detection
- ✅ Enhanced sync logging and debugging
- ✅ All 15 files syncing successfully (7 Docs, 7 PDFs, 1 Sheet)

**Session 012 (2025-10-05):**
- ✅ Deployed CrewAI Studio to Railway
- ✅ Fixed git submodule blocking commits
- ✅ Resolved Railway PORT variable issue
- ✅ Created comprehensive deployment docs
- ✅ Production-ready deployment complete!

**Session 011 (2025-10-05):**
- ✅ Built all 7 Next.js frontend pages
- ✅ Integrated CrewAI Studio as "Operator"
- ✅ Added smart fallback UI
- ✅ Created testing infrastructure

See [Session Notes](docs/sessions/) for complete history.

---

**Status: Production Deployment Complete! 🚀**

*Built with ❤️ using Claude Code*
