# CommandCenter

AI-powered energy management system with CrewAI agents, MCP integration, and multi-platform access.

## 🎯 Project Status

**Current Phase:** Frontend Complete - Session 010 Done! 🎉
**Progress:** 85% complete
**Last Updated:** 2025-10-05 (Session 010)

### Quick Stats
- ✅ Agents Deployed: 1/5 (Solar Controller with memory)
- ✅ API Endpoints: 9 operational
- ✅ MCP Server: Ready for Claude Desktop
- ✅ CrewAI Studio: Running locally (port 8501)
- ✅ Streamlit Ops Dashboard: 4 pages complete (port 8502)
- ✅ Next.js Frontend: Main page working with live data! (port 3000)
- 🔄 Current Sprint: Complete remaining frontend pages
- 📅 Next: Deploy all dashboards to production

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│ Claude Desktop  │────────▶│   MCP Server     │
└─────────────────┘ stdio   │   (port 8080)    │
                             └────────┬─────────┘
                                      │
                                      ▼
┌─────────────────┐         ┌─────────────────┐
│  Next.js        │────────▶│  Railway API    │
│  Frontend       │  HTTPS  │  (FastAPI)      │
│  (Vercel)       │         └────────┬─────────┘
└─────────────────┘                  │
                                     │
┌─────────────────┐                  │
│  Streamlit Ops  │──────────────────┤
│  Dashboard      │  HTTPS + Direct  │
│  (port 8502)    │  PostgreSQL      │
└─────────────────┘                  │
                                     │
┌─────────────────┐                  │
│  CrewAI Studio  │──────────────────┤
│  (port 8501)    │  PostgreSQL      │
└─────────────────┘                  │
                                     ▼
                            ┌─────────────────┐
                            │   PostgreSQL    │
                            │  + TimescaleDB  │
                            │   (Railway)     │
                            └─────────────────┘
```

**Production URLs:**
- Railway API: https://api.wildfireranch.us ✅
- Database: PostgreSQL on Railway (TimescaleDB enabled) ✅
- Next.js Frontend: Ready for Vercel deployment
- Streamlit Ops: Ready for Railway deployment
- CrewAI Studio: Ready for Railway deployment

## ✨ Features

### Completed ✅
- **Agent Memory**: Multi-turn conversations with context
- **Energy Tracking**: SolArk data persistence to TimescaleDB
- **MCP Server**: Claude Desktop integration via Model Context Protocol
- **Conversation History**: Full conversation storage and retrieval
- **Real-time Monitoring**: Latest energy snapshots and statistics
- **CrewAI Studio**: GUI for no-code agent management ✅
- **Streamlit Ops Dashboard**: 4-page admin dashboard (System Health, Energy Monitor, Agent Chat, Logs) ✅
- **Next.js Frontend**: Main page with live data, sidebar with Bitcoin punk icons ✅

### In Progress 🔄
- **Frontend Pages**: Complete /dashboard, /chat, /energy, /logs, /status pages
- **Deployment**: Deploy all dashboards to production

### Planned 📋
- Additional hardware integrations (Shelly, Miners)
- Optimization automation
- Scheduled crew execution
- User authentication
- Dark mode

## 📚 Documentation

### Core Documentation
- [Session Notes](docs/sessions/) - Detailed progress logs
- [MCP Server Setup](mcp-server/INSTALL.md) - Claude Desktop integration
- [API Documentation](https://api.wildfireranch.us/docs) - Interactive API docs

### CrewAI Studio
- [Setup Guide](docs/CREWAI_STUDIO_SETUP.md) - Complete installation and configuration
- [Quick Start](crewai-studio/QUICKSTART.md) - Get started in 5 minutes
- [Railway Deployment](crewai-studio/README.railway.md) - Production deployment guide

## 🚀 Quick Start

### Use with Claude Desktop (Recommended)

1. **Install MCP Server:**
   ```bash
   cd mcp-server
   npm install
   npm run build
   ```

2. **Configure Claude Desktop:**
   Follow instructions in [mcp-server/INSTALL.md](mcp-server/INSTALL.md)

3. **Start using:**
   Ask Claude: "Use ask_agent to check my battery level"

### Use CrewAI Studio (GUI)

1. **Start locally:**
   ```bash
   cd crewai-studio
   source venv/bin/activate
   streamlit run app/app.py
   ```

2. **Access**: http://localhost:8501

3. **Create your first agent:**
   Follow the [Quick Start Guide](crewai-studio/QUICKSTART.md)

### Run Railway API Locally

```bash
# Set up environment
cp .env.example .env
# Edit .env with your keys

# Install dependencies
cd railway
pip install -r requirements.txt

# Run API
uvicorn src.api.main:app --reload
