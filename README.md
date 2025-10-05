# CommandCenter

AI-powered energy management system with CrewAI agents, MCP integration, and multi-platform access.

## 🎯 Project Status

**Current Phase:** CrewAI Studio Integration Complete 🎉
**Progress:** 80% complete
**Last Updated:** 2025-10-05

### Quick Stats
- ✅ Agents Deployed: 1/5 (Solar Controller with memory)
- ✅ API Endpoints: 9 operational
- ✅ MCP Server: Ready for Claude Desktop
- ✅ CrewAI Studio: Installed and ready for Railway deployment
- 🔄 Current Sprint: Railway deployment and first crew
- 📅 Next: Multi-agent orchestration workflows

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐
│ Claude Desktop  │────────▶│   MCP Server     │
└─────────────────┘ stdio   └────────┬─────────┘
                                     │
                                     ▼
                            ┌─────────────────┐
┌─────────────────┐         │  Railway API    │
│  Web Browser    │────────▶│  (FastAPI)      │
│ (CrewAI Studio) │  HTTPS  └────────┬─────────┘
└─────────────────┘                  │
                                     ▼
                            ┌─────────────────┐
                            │   PostgreSQL    │
                            │  + TimescaleDB  │
                            │   (Railway)     │
                            └─────────────────┘
```

**Production URLs:**
- Railway API: https://api.wildfireranch.us
- Database: PostgreSQL on Railway (TimescaleDB enabled)
- CrewAI Studio: Ready for deployment

## ✨ Features

### Completed ✅
- **Agent Memory**: Multi-turn conversations with context
- **Energy Tracking**: SolArk data persistence to TimescaleDB
- **MCP Server**: Claude Desktop integration via Model Context Protocol
- **Conversation History**: Full conversation storage and retrieval
- **Real-time Monitoring**: Latest energy snapshots and statistics
- **CrewAI Studio**: GUI for no-code agent management (local deployment ready)

### In Progress 🔄
- **Railway Deployment**: Deploy CrewAI Studio to production
- **Multi-Agent Crews**: Build coordinated agent workflows

### Planned 📋
- Custom frontend dashboard
- Additional hardware integrations (Shelly, Miners)
- Optimization automation
- Scheduled crew execution

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
