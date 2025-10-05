# CrewAI Studio - Quick Start

## 🚀 Start Local Development

```bash
cd /workspaces/CommandCenter/crewai-studio
source venv/bin/activate
streamlit run app/app.py
```

**Access**: http://localhost:8501

## 🎨 First Time Setup

### 1. Create Your First Agent

1. Navigate to **"My Agents"** in sidebar
2. Click **"Create New Agent"**
3. Fill in details:
   - **Role**: e.g., "Solar Energy Monitor"
   - **Goal**: e.g., "Monitor and analyze solar energy production"
   - **Backstory**: Give context and personality
4. **Select LLM**: Choose model (GPT-4, GPT-3.5, etc.)
5. **Add Tools**: Select from available tools
6. **Save Agent**

### 2. Define a Task

1. Go to **"My Tasks"**
2. Click **"Create New Task"**
3. Configure:
   - **Description**: What the task should do
   - **Expected Output**: What result you want
   - **Agent**: Assign to your agent
4. **Save Task**

### 3. Build a Crew

1. Visit **"My Crews"**
2. Click **"Create New Crew"**
3. Setup:
   - **Name**: Give your crew a name
   - **Process**: Sequential or Hierarchical
   - **Add Agents**: Select agents to include
   - **Add Tasks**: Select tasks to execute
4. **Save Crew**

### 4. Run Your Crew

1. Select crew from **"My Crews"**
2. Click **"Run Crew"**
3. Provide any required inputs
4. **Execute** and monitor progress
5. View results in **"Results"** page

## 🛠️ Available Tools

### Built-in Tools
- **Web Search**: DuckDuckGo, Serper
- **File Operations**: Read, Write, Directory
- **Code Tools**: Python REPL, Shell
- **Scraping**: Web scraping, API calls
- **Knowledge**: RAG, embeddings

### Custom Tools

Create custom tools to integrate with your infrastructure:

```python
# Example: Railway API Integration
import requests

def get_solar_data():
    """Fetch latest solar energy data from Railway API"""
    response = requests.get(
        "https://api.wildfireranch.us/energy/latest",
        headers={"X-API-Key": "your-api-key"}
    )
    return response.json()
```

Add in **Tools → Custom Tools**

## 📊 Example Crew: Solar Monitor

### Agents

**1. Solar Data Collector**
- Role: Data Collection Specialist
- Goal: Gather current solar energy metrics
- Tools: Custom API tool

**2. Pattern Analyzer**
- Role: Data Analyst
- Goal: Identify trends and anomalies
- Tools: Python REPL, Web Search

**3. Report Generator**
- Role: Technical Writer
- Goal: Create human-readable reports
- Tools: File operations

### Tasks

**Task 1: Fetch Data**
- Description: "Get latest solar energy data from the monitoring system"
- Agent: Solar Data Collector
- Output: JSON with current metrics

**Task 2: Analyze**
- Description: "Analyze the data for unusual patterns or optimization opportunities"
- Agent: Pattern Analyzer
- Output: Analysis summary with recommendations

**Task 3: Report**
- Description: "Generate a comprehensive report on solar system status"
- Agent: Report Generator
- Output: Markdown report file

### Crew Configuration
- Name: "Solar Monitoring Crew"
- Process: Sequential
- Agents: All three agents
- Tasks: All three tasks in order

## 🔧 Configuration

### Environment Variables

Located in `.env`:

```env
OPENAI_API_KEY=your-key-here    # Required
DB_URL=sqlite:///crewai.db      # Default (local)
AGENTOPS_ENABLED=False          # Optional monitoring
```

### Database

- **Local**: SQLite (`crewai.db`)
- **Production**: PostgreSQL (Railway)

Switch by changing `DB_URL` in `.env`

## 📁 Project Structure

```
crewai-studio/
├── app/
│   ├── app.py              # Main Streamlit app
│   ├── db_utils.py         # Database operations
│   ├── my_agent.py         # Agent management
│   ├── my_crew.py          # Crew orchestration
│   ├── my_task.py          # Task configuration
│   ├── my_tools.py         # Tool definitions
│   └── ...
├── .env                    # Environment config
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container config
└── docker-compose-railway.yaml  # Railway deployment
```

## 🐛 Troubleshooting

### App Won't Start
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Clear Streamlit cache
streamlit cache clear

# Check Python version (needs 3.12+)
python --version
```

### Database Issues
```bash
# Reset local database
rm crewai.db

# Restart app (it will recreate tables)
streamlit run app/app.py
```

### Import Errors
```bash
# Verify all packages installed
pip list | grep -E "(crewai|streamlit|langchain)"

# Reinstall specific package
pip install --upgrade crewai crewai-tools
```

## 📚 Learn More

### Crew Processes

**Sequential**: Tasks run one after another
- Task 1 → Task 2 → Task 3
- Output of one feeds into next
- Deterministic order

**Hierarchical**: Manager agent coordinates
- Manager delegates tasks
- Parallel execution possible
- More complex coordination

### Agent Roles

Best practices for role design:
- Be specific (not "helper" but "Solar Energy Analyst")
- Give clear goals (what success looks like)
- Provide context (backstory matters!)
- Assign relevant tools (don't overload)

### Task Design

Effective tasks have:
- Clear description of what to do
- Specific expected output format
- Appropriate agent assignment
- Reasonable complexity (not too broad)

## 🎯 Common Use Cases

### 1. Data Pipeline
- Agent 1: Fetch data
- Agent 2: Transform data
- Agent 3: Store/report data

### 2. Research Workflow
- Agent 1: Web search for info
- Agent 2: Summarize findings
- Agent 3: Generate report

### 3. Automation
- Agent 1: Monitor system
- Agent 2: Analyze status
- Agent 3: Take action or alert

### 4. Multi-Source Analysis
- Agent 1: Gather source 1
- Agent 2: Gather source 2
- Agent 3: Synthesize insights

## 💡 Tips & Tricks

1. **Start Simple**: One agent, one task, test it
2. **Iterate**: Add complexity gradually
3. **Use Backstory**: Gives agents personality and context
4. **Test Tools**: Verify tools work before adding to agents
5. **Monitor Results**: Review execution logs to improve
6. **Reuse Agents**: Same agent can be in multiple crews
7. **Version Control**: Export crews for backup

## 🔗 Resources

- [Full Documentation](./CREWAI_STUDIO_SETUP.md)
- [Railway Deployment](./README.railway.md)
- [CrewAI Docs](https://docs.crewai.com)
- [Streamlit Docs](https://docs.streamlit.io)

## ⚡ Quick Commands

```bash
# Start local
streamlit run app/app.py

# Start on specific port
streamlit run app/app.py --server.port 8502

# Start headless (for deployment)
streamlit run app/app.py --server.headless true

# Clear cache and restart
streamlit cache clear && streamlit run app/app.py
```

## 🚀 Deploy to Railway

See [README.railway.md](./README.railway.md) for complete deployment guide.

**Quick version:**
1. Create Railway service
2. Set root directory: `/crewai-studio`
3. Add environment variables
4. Deploy!

---

**Need Help?**
- Check logs in app
- Review [troubleshooting guide](./CREWAI_STUDIO_SETUP.md#troubleshooting)
- Visit [GitHub issues](https://github.com/strnad/CrewAI-Studio/issues)

**Ready to build your first crew?** 🎉
