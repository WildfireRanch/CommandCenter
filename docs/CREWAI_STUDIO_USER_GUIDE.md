# CrewAI Studio - Complete User Guide

**Last Updated:** October 6, 2025
**Version:** CommandCenter Production v1.0
**Studio URL:** https://studio.wildfireranch.us

---

## Table of Contents

1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Interface Navigation](#interface-navigation)
4. [Creating Agents](#creating-agents)
5. [Designing Tasks](#designing-tasks)
6. [Building Crews](#building-crews)
7. [Tools & Integrations](#tools--integrations)
8. [Knowledge Base](#knowledge-base)
9. [Running Crews](#running-crews)
10. [Viewing Results](#viewing-results)
11. [Import/Export](#importexport)
12. [Best Practices](#best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Overview

### What is CrewAI Studio?

CrewAI Studio is a **no-code visual interface** for creating and managing AI agent crews. It provides a graphical way to:

- 🤖 Create AI agents with specific roles and capabilities
- 📋 Design tasks for agents to complete
- 👥 Build crews (teams of agents working together)
- 🛠️ Configure tools and integrations
- 📚 Add knowledge sources for agents
- 🚀 Run crews and view results

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│              CrewAI Studio (Streamlit)                   │
│  https://studio.wildfireranch.us                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Agents  │  │  Tasks   │  │  Crews   │             │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘             │
│       │             │              │                    │
│       └─────────────┴──────────────┘                   │
│                     │                                   │
│              ┌──────▼──────┐                            │
│              │  PostgreSQL  │                           │
│              │  (Railway)   │                           │
│              └─────────────┘                            │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Key Features

- **Persistent Storage:** All agents, crews, and tasks are saved to PostgreSQL
- **Multi-LLM Support:** OpenAI, Anthropic (Claude), Groq, Ollama, and more
- **Built-in Tools:** Web search, file operations, code execution, API calls
- **Knowledge Integration:** Add documents and data sources for RAG (Retrieval Augmented Generation)
- **Process Types:** Sequential (linear) and Hierarchical (manager-based) execution
- **Real-time Execution:** Run crews and see results immediately

---

## Getting Started

### Accessing the Studio

**Primary Access (Production):**
```
https://studio.wildfireranch.us
```

**Embedded in Frontend:**
```
https://your-frontend-url/studio
```

**Local Development:**
```bash
cd /workspaces/CommandCenter/crewai-studio
streamlit run app/app.py --server.port 8501
```

### First Time Setup

1. **Access Studio:** Navigate to https://studio.wildfireranch.us
2. **Check Database Connection:** The Studio automatically connects to the CommandCenter PostgreSQL database
3. **Verify LLM Configuration:** OpenAI is configured by default (check Railway environment variables)
4. **Explore Interface:** Use the left sidebar to navigate between pages

---

## Interface Navigation

### Main Pages

The Studio has **8 main pages** accessible via the left sidebar:

| Page | Purpose | Icon |
|------|---------|------|
| **Crews** | Create and manage crews (teams of agents) | 👥 |
| **Tools** | Enable/configure tools for agents | 🛠️ |
| **Agents** | Create and configure individual agents | 🤖 |
| **Tasks** | Design tasks for agents to execute | 📋 |
| **Knowledge** | Add knowledge sources for RAG | 📚 |
| **Kickoff!** | Run crews with input parameters | 🚀 |
| **Results** | View execution logs and outputs | 📊 |
| **Import/export** | Backup/restore configurations | 💾 |

### Navigation Flow

**Recommended workflow:**
1. Start with **Tools** (enable needed tools)
2. Create **Agents** (define roles and capabilities)
3. Design **Tasks** (what agents should do)
4. Build **Crews** (assign agents to tasks)
5. Optional: Add **Knowledge** sources
6. **Kickoff!** (run your crew)
7. View **Results**

---

## Creating Agents

### What is an Agent?

An **agent** is an AI entity with:
- A specific **role** (e.g., "Research Analyst", "Content Writer")
- A defined **goal** (what it's trying to achieve)
- A **backstory** (context and personality)
- Optional **tools** (capabilities it can use)
- An **LLM** (the AI model powering it)

### Agent Configuration Fields

#### 1. Role (Required)
**Purpose:** Defines the agent's primary function

**Best Practices:**
- Be specific: ❌ "Helper" → ✅ "Solar Energy Data Analyst"
- Use professional titles: "Senior Python Developer", "Marketing Strategist"
- Avoid generic names: "Agent1", "Assistant"

**Examples:**
```
✅ "Senior Software Engineer specializing in Python and FastAPI"
✅ "Market Research Analyst with expertise in renewable energy"
✅ "Technical Writer focused on API documentation"
```

#### 2. Goal (Required)
**Purpose:** What the agent aims to accomplish

**Best Practices:**
- Start with an action verb: "Analyze", "Create", "Research", "Optimize"
- Be specific about outcomes
- Include success criteria when possible

**Examples:**
```
✅ "Analyze solar production data and identify optimization opportunities"
✅ "Create comprehensive API documentation that developers can easily follow"
✅ "Research market trends and provide actionable investment recommendations"
```

#### 3. Backstory (Required)
**Purpose:** Provides context, personality, and expertise

**Best Practices:**
- 2-4 sentences is ideal
- Include relevant experience/expertise
- Set expectations for behavior
- Add personality touches

**Examples:**
```
✅ "You are a veteran data analyst with 10+ years of experience in renewable
   energy systems. You have a keen eye for patterns and anomalies in time-series
   data. Your analyses are known for being thorough yet concise, always focusing
   on actionable insights. You communicate findings clearly to both technical
   and non-technical stakeholders."
```

#### 4. Tools (Optional)
**Purpose:** Capabilities the agent can use during execution

**Available Tools:**
- Web search (DuckDuckGo, Serper)
- File operations (read, write, search CSV)
- Code execution
- API calls
- Web scraping

**How to Assign:**
1. Enable tools in the **Tools** page first
2. In agent configuration, check the boxes for desired tools
3. Agent will have access to those tools during execution

**Best Practices:**
- Only assign tools the agent needs
- Web search tools for research agents
- File tools for data analysis agents
- Code interpreter for developers

#### 5. LLM Selection
**Purpose:** Choose which AI model powers the agent

**Available Models:**
- **GPT-4** (OpenAI): Best for complex reasoning, most expensive
- **GPT-3.5-turbo**: Fast and cost-effective for simple tasks
- **Claude** (Anthropic): Excellent for analysis and writing
- **Groq**: Fast inference, good for real-time applications
- **Ollama**: Local models, free but requires local setup

**Selection Guide:**
- **Complex tasks:** GPT-4, Claude Opus
- **Fast execution:** GPT-3.5-turbo, Groq
- **Cost-sensitive:** GPT-3.5-turbo, Ollama
- **Privacy-critical:** Ollama (local)

#### 6. Advanced Options

**Allow Delegation:**
- `True`: Agent can ask other agents for help
- `False`: Agent works independently
- **Use when:** Building hierarchical teams

**Verbose Mode:**
- `True`: Detailed logging of agent thoughts
- `False`: Minimal output
- **Use when:** Debugging or learning

**Max Iterations:**
- Controls how many steps agent can take
- Default: 15
- Increase for complex tasks, decrease for simple ones

---

## Designing Tasks

### What is a Task?

A **task** is a specific job for an agent to complete. Tasks are the building blocks of crew workflows.

### Task Configuration Fields

#### 1. Description (Required)
**Purpose:** Clearly explain what needs to be done

**Best Practices:**
- Start with action verb: "Analyze", "Write", "Research"
- Be specific about inputs and outputs
- Include constraints or requirements
- Reference data sources if applicable

**Examples:**
```
✅ "Analyze the solar production data from the past 30 days and identify any
   unusual patterns, anomalies, or performance issues. Consider factors like
   weather, time of day, and seasonal variations. Provide specific
   recommendations for optimization."

✅ "Research the latest developments in battery storage technology, focusing on
   lithium-ion alternatives. Compile findings into a structured report with
   sections for: technology overview, cost comparison, and implementation
   timeline."
```

#### 2. Expected Output (Required)
**Purpose:** Define what a successful completion looks like

**Best Practices:**
- Specify format: "JSON report", "Markdown document", "Python dict"
- List required sections/fields
- Provide examples when helpful

**Examples:**
```
✅ "A JSON report with the following structure:
   {
     'summary': 'Brief overview of findings',
     'anomalies': [{'date': '...', 'description': '...', 'severity': '...'}],
     'recommendations': ['...'],
     'confidence_score': 0-100
   }"

✅ "A markdown document with sections: Executive Summary, Methodology, Findings,
   Recommendations, and Next Steps. Include data visualizations as ASCII tables."
```

#### 3. Agent Assignment
**Purpose:** Which agent should execute this task

**Best Practices:**
- Match task to agent's role and expertise
- Consider tool requirements
- Think about task dependencies

#### 4. Context (Optional)
**Purpose:** Previous tasks that inform this one

**How it works:**
- Task can access outputs from context tasks
- Enables chaining and information flow
- Creates task dependencies

**Example Flow:**
```
Task 1: "Research solar panel manufacturers" (no context)
  ↓
Task 2: "Compare pricing from researched manufacturers" (context: Task 1)
  ↓
Task 3: "Create purchase recommendation" (context: Task 1, Task 2)
```

---

## Building Crews

### What is a Crew?

A **crew** is a team of agents working together to accomplish a goal. Crews coordinate multiple agents and tasks.

### Crew Configuration

#### 1. Name & Description
- **Name:** Short identifier (e.g., "Solar Analysis Crew")
- **Description:** Purpose and capabilities (optional but helpful)

#### 2. Process Type

**Sequential Process:**
```
Task 1 → Task 2 → Task 3 → Done
```
- Tasks execute in order
- Each task completes before next starts
- Simple, predictable, easy to debug

**Use when:**
- Clear linear workflow
- Tasks build on each other
- Single agent can handle all tasks
- Debugging is important

**Hierarchical Process:**
```
        Manager Agent
       /      |      \
   Agent 1  Agent 2  Agent 3
```
- Manager agent delegates tasks
- Agents work in parallel when possible
- Manager synthesizes results

**Use when:**
- Complex multi-step workflows
- Tasks can be parallelized
- Need dynamic task assignment
- Have diverse specialist agents

#### 3. Agent Assignment
- Add agents who will work in this crew
- For sequential: typically 1-3 agents
- For hierarchical: 3+ agents (one will be manager)

#### 4. Task Assignment
- Add tasks for the crew to execute
- Tasks will use their assigned agents
- Order matters in sequential process

---

## Tools & Integrations

### Built-in Tools

#### Web Search Tools

**DuckDuckGoSearchTool:**
- Free web search
- No API key required
- Good for general research
- Enable in Tools page → Check the box

**SerperDevTool:**
- Google search results
- Requires API key (set SERPER_API_KEY)
- More accurate than DuckDuckGo
- Better for specific queries

#### File Operation Tools

**CustomFileWriteTool:**
- Write content to files
- Useful for saving reports, data
- No configuration needed

**CSVSearchToolEnhanced:**
- Search and query CSV files
- Great for data analysis agents
- Can filter, aggregate, summarize

#### Development Tools

**CustomCodeInterpreterTool:**
- Execute Python code
- Useful for calculations, data processing
- Sandboxed environment
- Returns execution results

#### API Tools

**CustomApiTool:**
- Make HTTP requests to APIs
- GET, POST, PUT, DELETE support
- Useful for integrations
- Configure endpoint URLs

#### Web Scraping Tools

**ScrapeWebsiteToolEnhanced:**
- Extract content from websites
- HTML parsing
- Good for data collection

**ScrapflyScrapeWebsiteTool:**
- Advanced web scraping
- Handles JavaScript-heavy sites
- Requires SCRAPFLY_API_KEY

### Enabling Tools

1. Go to **Tools** page
2. Check boxes for tools you want to enable
3. Tools are now available for agent assignment

### Adding Custom Tools

Custom tools can be added in [crewai-studio/app/tools/](crewai-studio/app/tools/) directory. Each tool is a Python file that inherits from CrewAI's BaseTool.

---

## Knowledge Base

### What is Knowledge Base?

The Knowledge Base feature allows you to add **documents and data sources** that agents can reference during execution. This implements **RAG (Retrieval Augmented Generation)**.

### How It Works

1. **Add Knowledge:** Upload documents, add text, or connect data sources
2. **Embedding:** Content is vectorized and stored
3. **Retrieval:** When agent runs, relevant knowledge is retrieved based on task context
4. **Augmentation:** Retrieved knowledge is added to agent's context
5. **Generation:** Agent uses knowledge to inform its responses

### Adding Knowledge Sources

1. Go to **Knowledge** page
2. Click "Add Knowledge Source"
3. Choose type:
   - **Text:** Direct text input
   - **File:** Upload document (PDF, TXT, MD)
   - **URL:** Web page content
   - **API:** Dynamic data source

4. Add description (helps with retrieval)
5. Save

### Best Practices

- **Be specific:** Add knowledge relevant to your crew's tasks
- **Structure matters:** Well-organized documents retrieve better
- **Update regularly:** Keep knowledge current
- **Test retrieval:** Run crews and verify knowledge is being used

---

## Running Crews

### The Kickoff! Page

This is where you **execute your crews**.

### Running a Crew

1. **Go to Kickoff! page**
2. **Select a crew** from dropdown
3. **Review configuration:**
   - Agents assigned
   - Tasks defined
   - Process type
4. **Provide inputs** (if crew requires them)
5. **Click "Kickoff Crew"**

### Execution Process

**Sequential Crews:**
```
[Agent 1: Task 1] → [Agent 1: Task 2] → [Agent 2: Task 3] → Done
```
- Watch progress in real-time
- Each task shows status
- Can see agent thoughts (if verbose mode enabled)

**Hierarchical Crews:**
```
[Manager: Planning] → [Parallel Execution] → [Manager: Synthesis] → Done
```
- Manager decides task order
- Multiple agents may work simultaneously
- Manager compiles final result

### Monitoring Execution

- **Status indicator:** Shows current task
- **Agent output:** Real-time thoughts and actions (if verbose)
- **Tool usage:** See which tools agents are using
- **Completion:** Final result displayed

### Inputs & Parameters

Some crews may require inputs:
- Text fields for specific data
- Configuration options
- File uploads

Provide these before clicking "Kickoff".

---

## Viewing Results

### The Results Page

View **execution history** and **outputs** from crew runs.

### What You'll See

1. **Execution List:**
   - Timestamp
   - Crew name
   - Status (Success/Failed)
   - Duration

2. **Execution Details:**
   - Full output
   - Agent logs
   - Tool usage
   - Errors (if any)

3. **Output Data:**
   - Final result from crew
   - Format depends on tasks
   - Can be JSON, text, structured data

### Analyzing Results

**Success Indicators:**
- Status = "Success"
- All tasks completed
- Output matches expected format
- No error messages

**Debugging Failures:**
- Check error messages
- Review agent logs
- Verify tool access
- Check API key configuration
- Ensure task descriptions are clear

---

## Import/Export

### Backing Up Your Work

The **Import/export** page lets you save and restore configurations.

### Exporting

1. Go to Import/export page
2. Click "Export Crew Configuration"
3. Select what to include:
   - Agents
   - Tasks
   - Crews
   - Tools configuration
   - Knowledge sources
4. Download JSON file

### Importing

1. Go to Import/export page
2. Click "Import Configuration"
3. Upload JSON file
4. Review imported items
5. Confirm import

### Use Cases

- **Backup:** Save configurations before major changes
- **Migration:** Move crews between environments
- **Sharing:** Share crew templates with team
- **Version control:** Keep snapshots of working configurations

---

## Best Practices

### Agent Design

✅ **Do:**
- Give agents specific, professional roles
- Write detailed backstories (2-4 sentences)
- Include relevant expertise in backstory
- Use clear, actionable goals
- Assign only needed tools
- Test with verbose mode first

❌ **Don't:**
- Use generic roles like "Agent1", "Helper"
- Skip the backstory (it matters!)
- Give agents too many tools
- Make goals vague or open-ended

### Task Design

✅ **Do:**
- Start with action verbs
- Specify expected output format
- Include success criteria
- Reference data sources
- Use context to chain tasks
- Provide examples in description

❌ **Don't:**
- Be vague: "Do research"
- Skip expected output definition
- Create circular dependencies
- Make tasks too broad

### Crew Design

✅ **Do:**
- Start with sequential process (simpler)
- Use 2-4 agents for most crews
- Test each agent individually first
- Keep task count manageable (3-7 tasks)
- Use descriptive crew names
- Document crew purpose

❌ **Don't:**
- Jump to hierarchical without testing sequential
- Create crews with 10+ agents
- Skip individual agent testing
- Make overly complex workflows initially

### LLM Selection

✅ **Do:**
- Use GPT-4 for complex reasoning
- Use GPT-3.5 for simple, fast tasks
- Consider cost vs. quality tradeoffs
- Test different models for your use case
- Use Ollama for privacy-sensitive tasks

❌ **Don't:**
- Use GPT-4 for everything (expensive!)
- Skip cost analysis
- Ignore local model options
- Use same model for all agents

---

## Troubleshooting

### Common Issues

#### Issue: "Agent not responding" or "Timeout"
**Causes:**
- Task too complex
- Max iterations too low
- LLM rate limiting

**Solutions:**
- Increase max iterations
- Break task into smaller subtasks
- Check API key and rate limits
- Simplify task description

#### Issue: "Tool not found" or "Tool error"
**Causes:**
- Tool not enabled
- Missing API key
- Tool configuration error

**Solutions:**
- Enable tool in Tools page
- Set required API keys in Railway
- Check tool-specific configuration

#### Issue: "No output" or "Empty result"
**Causes:**
- Task description unclear
- Expected output not specified
- Agent lacks necessary tools

**Solutions:**
- Rewrite task with clearer instructions
- Specify exact output format
- Assign appropriate tools to agent

#### Issue: "Database connection error"
**Causes:**
- Database URL incorrect
- Network connectivity issue
- Database service down

**Solutions:**
- Verify DATABASE_URL in Railway
- Check Railway database service status
- Test connection with psql

#### Issue: "Crew stuck on one task"
**Causes:**
- Task too complex
- Agent reasoning loop
- Missing required information

**Solutions:**
- Add max iterations constraint
- Provide more context in task
- Enable verbose mode to see agent thoughts
- Simplify task requirements

---

## Additional Resources

### Documentation

- **CrewAI Official Docs:** https://docs.crewai.com/
- **CommandCenter Docs:** [/docs](/docs)
- **API Documentation:** https://api.wildfireranch.us/docs

### Example Crews

See [/docs/examples/](/docs/examples/) for:
- Solar Data Analysis Crew
- Research & Report Crew
- Code Review Crew
- Content Creation Crew

### Support

- **GitHub Issues:** https://github.com/WildfireRanch/CommandCenter/issues
- **Session Logs:** [/docs/sessions/](/docs/sessions/)

---

## Quick Reference Card

### Agent Creation Checklist
- [ ] Specific, professional role
- [ ] Clear, actionable goal
- [ ] Detailed backstory (2-4 sentences)
- [ ] Only needed tools assigned
- [ ] Appropriate LLM selected
- [ ] Verbose mode enabled (for testing)

### Task Creation Checklist
- [ ] Action verb in description
- [ ] Specific inputs/outputs defined
- [ ] Expected output format specified
- [ ] Correct agent assigned
- [ ] Context tasks added (if needed)
- [ ] Success criteria clear

### Crew Creation Checklist
- [ ] Descriptive name
- [ ] Purpose documented
- [ ] Process type selected (start with sequential)
- [ ] 2-4 agents assigned
- [ ] 3-7 tasks defined
- [ ] Task order logical
- [ ] Tested individually before deployment

---

**Last Updated:** October 6, 2025
**Version:** 1.0
**Maintained by:** CommandCenter Project
**Studio URL:** https://studio.wildfireranch.us
