# 🎨 CrewAI Studio Setup Guide

## Overview

CrewAI Studio is a Streamlit-based GUI for managing and running CrewAI agents and tasks. It provides a no-code interface for creating, configuring, and monitoring AI agent crews.

## Architecture

```
Claude Desktop → MCP Server → Railway API → PostgreSQL
Web Browser → CrewAI Studio → Railway API → PostgreSQL
```

Both the MCP Server and CrewAI Studio connect to the same Railway PostgreSQL database, allowing unified agent management.

## Installation

### Local Development

1. **Clone and Install**
   ```bash
   cd /workspaces/CommandCenter/crewai-studio
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   - Copy `.env_example` to `.env`
   - Set `OPENAI_API_KEY`
   - For local dev: Use SQLite (default)
   - For Railway: Use PostgreSQL connection string

3. **Run Locally**
   ```bash
   source venv/bin/activate
   streamlit run app/app.py
   ```

   Access at: `http://localhost:8501`

### Railway Deployment

#### Option 1: Docker on Railway

1. **Update .env for Railway**
   ```env
   DB_URL=postgresql://postgres:PASSWORD@postgres.railway.internal:5432/commandcenter
   OPENAI_API_KEY=your-key-here
   ```

2. **Deploy using docker-compose-railway.yaml**
   ```bash
   docker-compose -f docker-compose-railway.yaml up --build
   ```

#### Option 2: Railway Service (Recommended)

1. **Create new Railway service**
   - In Railway dashboard, create new service
   - Connect to GitHub repository
   - Set root directory to `/crewai-studio`

2. **Set Environment Variables in Railway**
   ```
   DB_URL=${{Postgres.DATABASE_URL}}  # References existing PostgreSQL
   OPENAI_API_KEY=sk-proj-...
   AGENTOPS_ENABLED=False
   ```

3. **Configure Build**
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run app/app.py --server.headless true --server.port $PORT`
   - Expose Port: 8501

4. **Deploy**
   - Railway will auto-deploy on push
   - Access via Railway-provided URL

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Yes | - |
| `DB_URL` | PostgreSQL connection string | No | `sqlite:///crewai.db` |
| `AGENTOPS_ENABLED` | Enable AgentOps telemetry | No | `False` |
| `GROQ_API_KEY` | Groq API key | No | - |
| `ANTHROPIC_API_KEY` | Anthropic API key | No | - |
| `SERPER_API_KEY` | Serper search API key | No | - |

### Database Setup

CrewAI Studio supports both SQLite and PostgreSQL:

- **SQLite** (Local Dev): Automatically created as `crewai.db`
- **PostgreSQL** (Production): Set `DB_URL` to Railway connection string

The app creates these tables automatically:
- `entities` - Stores agents, tasks, crews, and tools

## Features

### Agent Management
- Create and configure AI agents
- Set roles, goals, and backstories
- Assign tools to agents
- Configure LLM settings per agent

### Task Configuration
- Define tasks with descriptions
- Set expected outputs
- Assign tasks to agents
- Configure task dependencies

### Crew Orchestration
- Create crews from agents and tasks
- Choose process type (sequential/hierarchical)
- Run crews and monitor progress
- View execution results

### Tool Integration
- Built-in tools library
- Custom tool creation
- Tool assignment to agents
- Web search, file operations, and more

### Knowledge Sources
- Integrate document knowledge bases
- Support for PDF, DOCX, TXT
- Vector embeddings for RAG
- Knowledge source assignment to agents

## Integration with CommandCenter

### Shared Database
Both MCP Server and CrewAI Studio use the same PostgreSQL database:

```
Railway PostgreSQL
├── MCP Server (Read/Write)
│   └── Agent conversations
│   └── Energy data
│   └── System health
└── CrewAI Studio (Read/Write)
    └── Agent definitions
    └── Task configurations
    └── Crew orchestration
```

### Accessing Existing Agents

To use your Solar Controller agent in CrewAI Studio:

1. **Export Agent from MCP**
   - Document agent configuration
   - Note tools and capabilities

2. **Recreate in CrewAI Studio**
   - Navigate to "My Agents"
   - Click "Create New Agent"
   - Set role: "Solar Controller"
   - Configure tools and LLM settings

3. **Build Crews**
   - Create tasks for agent
   - Combine with other agents
   - Run orchestrated workflows

## Usage Examples

### Example 1: Solar Monitoring Crew

**Agents:**
- Solar Controller (energy monitoring)
- Data Analyst (pattern analysis)
- Alert Manager (notifications)

**Tasks:**
1. Fetch solar data
2. Analyze patterns
3. Generate alerts

**Process:** Sequential

### Example 2: Autonomous Energy Optimization

**Agents:**
- Solar Controller
- Weather Forecaster
- Load Optimizer

**Tasks:**
1. Get current energy state
2. Fetch weather forecast
3. Optimize load distribution
4. Execute changes

**Process:** Hierarchical (Solar Controller as manager)

## API Integration

### Connecting to Railway API

CrewAI Studio can integrate with your Railway API:

1. **Create API Tool**
   ```python
   # In CrewAI Studio > Tools > Custom Tool
   import requests

   def get_energy_data():
       response = requests.get(
           "https://api.wildfireranch.us/energy/latest",
           headers={"X-API-Key": "your-api-key"}
       )
       return response.json()
   ```

2. **Assign to Agent**
   - Navigate to agent configuration
   - Add custom tool
   - Enable tool in agent settings

## Deployment Options Summary

| Method | Database | Best For | Setup Complexity |
|--------|----------|----------|------------------|
| Local Dev | SQLite | Testing, Development | Low |
| Docker Local | PostgreSQL | Local production-like | Medium |
| Railway Service | Railway PostgreSQL | Production | Low |
| Docker on Railway | Railway PostgreSQL | Custom deployments | Medium |

## Troubleshooting

### Database Connection Issues
- **Local dev**: Remove `DB_URL` from `.env` to use SQLite
- **Railway internal**: Use `postgres.railway.internal` hostname
- **Railway external**: Use public connection string from Railway dashboard

### Streamlit Errors
- Clear cache: `streamlit cache clear`
- Restart server
- Check Python version (requires 3.12+)

### Missing Dependencies
```bash
pip install --upgrade -r requirements.txt
```

## Next Steps

1. **Create First Agent**
   - Navigate to "My Agents"
   - Click "Create New Agent"
   - Configure and save

2. **Define Tasks**
   - Go to "My Tasks"
   - Create task for agent
   - Set expected output

3. **Build Crew**
   - Visit "My Crews"
   - Create new crew
   - Add agents and tasks
   - Run crew!

4. **Monitor Results**
   - Check "Results" page
   - View execution logs
   - Analyze output

## Resources

- [CrewAI Documentation](https://docs.crewai.com)
- [Streamlit Docs](https://docs.streamlit.io)
- [Railway Guides](https://docs.railway.app)
- [CrewAI Studio GitHub](https://github.com/strnad/CrewAI-Studio)

## Support

For issues specific to:
- **CrewAI Studio**: [GitHub Issues](https://github.com/strnad/CrewAI-Studio/issues)
- **CommandCenter**: See project documentation
- **Railway**: Railway community forum
