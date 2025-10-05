# CommandCenter

AI-powered energy management system with CrewAI agents, MCP integration, and multi-platform access.

## 🎯 Project Status

**Current Phase:** MCP Integration Complete 🎉
**Progress:** 75% complete
**Last Updated:** 2025-10-05

### Quick Stats
- ✅ Agents Deployed: 1/5 (Solar Controller with memory)
- ✅ API Endpoints: 9 operational
- ✅ MCP Server: Ready for Claude Desktop
- 🔄 Current Sprint: CrewAI Studio Integration
- 📅 Next: GUI Management Interface

## 🏗️ Architecture

```
Claude Desktop → MCP Server → Railway API → PostgreSQL + TimescaleDB
                  (stdio)       (FastAPI)     (Conversations + Energy Data)
```

**Production URLs:**
- Railway API: https://api.wildfireranch.us
- Database: PostgreSQL on Railway (TimescaleDB enabled)

## ✨ Features

### Completed ✅
- **Agent Memory**: Multi-turn conversations with context
- **Energy Tracking**: SolArk data persistence to TimescaleDB
- **MCP Server**: Claude Desktop integration via Model Context Protocol
- **Conversation History**: Full conversation storage and retrieval
- **Real-time Monitoring**: Latest energy snapshots and statistics

### In Progress 🔄
- **CrewAI Studio**: GUI for agent management (Next session)

### Planned 📋
- Custom frontend dashboard
- Additional hardware integrations (Shelly, Miners)
- Optimization automation

## 📚 Documentation

- [Session Notes](docs/sessions/) - Detailed progress logs
- [MCP Server Setup](mcp-server/INSTALL.md) - Claude Desktop integration
- [API Documentation](https://api.wildfireranch.us/docs) - Interactive API docs

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
