# ARCHIVED - Not Used in CommandCenter V1
# CrewAI Studio - Quick Start Tutorial

**Goal:** Create your first agent and crew in 10 minutes
**Level:** Beginner
**Date:** October 6, 2025

---

## Prerequisites

- ✅ CrewAI Studio accessible at https://studio.wildfireranch.us
- ✅ OpenAI API key configured in Railway
- ✅ Database connected (PostgreSQL)

---

## Tutorial: Build a Solar Data Analyst Crew

We'll create a simple 2-agent crew that:
1. **Agent 1:** Analyzes solar production data
2. **Agent 2:** Provides optimization recommendations

---

## Part 1: Enable Tools (2 minutes)

### Step 1: Navigate to Tools Page

1. Open https://studio.wildfireranch.us
2. Click **"Tools"** in left sidebar

### Step 2: Enable Essential Tools

Check these boxes:
- ✅ **DuckDuckGoSearchTool** (for web research)
- ✅ **CustomFileWriteTool** (to save reports)
- ✅ **CustomCodeInterpreterTool** (for data analysis)

The page auto-saves when you check boxes.

**Result:** You should see checkmarks next to enabled tools.

---

## Part 2: Create First Agent (5 minutes)

### Step 1: Navigate to Agents Page

Click **"Agents"** in left sidebar

### Step 2: Click "Create agent"

You'll see a form with multiple fields.

### Step 3: Fill in Agent Details

**Agent Name/Role:**
```
Solar Data Analyst
```

**Goal:**
```
Analyze solar production data and identify patterns, anomalies, and performance issues
```

**Backstory:**
```
You are an experienced renewable energy analyst with 10+ years of expertise in solar panel performance optimization. You excel at identifying patterns in time-series energy data and providing data-driven insights. Your analyses are thorough yet concise, always focusing on actionable findings.
```

### Step 4: Configure Agent Settings

**LLM (Model):**
- Select: **GPT-3.5-turbo** (cost-effective for testing)

**Tools:**
- Check: ✅ **DuckDuckGoSearchTool**
- Check: ✅ **CustomCodeInterpreterTool**

**Advanced Options:**
- **Verbose:** ✅ True (enables detailed logging)
- **Allow Delegation:** ❌ False (agent works independently)
- **Max Iterations:** 15 (default)

### Step 5: Save Agent

Click **"Save"** button at bottom

**Result:** Agent appears in the agents list. You should see:
```
✅ Solar Data Analyst
   Goal: Analyze solar production data...
   Tools: DuckDuckGoSearchTool, CustomCodeInterpreterTool
```

### Verification Test

**Refresh the page** (Ctrl+R or Cmd+R)

- Agent should still be there ✅ (proves database persistence)

---

## Part 3: Create a Task (3 minutes)

### Step 1: Navigate to Tasks Page

Click **"Tasks"** in left sidebar

### Step 2: Click "Create task"

### Step 3: Fill in Task Details

**Description:**
```
Analyze solar production data from a typical solar installation. Research current solar panel efficiency standards and best practices. Identify 3-5 key metrics that indicate optimal performance. Explain what patterns would indicate potential issues.
```

**Expected Output:**
```
A structured report in markdown format with:
1. Summary: Brief overview of solar performance analysis
2. Key Metrics: List of 3-5 important performance indicators
3. Optimal Patterns: What good performance looks like
4. Warning Signs: Patterns that indicate issues
5. Recommendations: General best practices for monitoring

Format as markdown with clear headers and bullet points.
```

**Agent:**
- Select: **Solar Data Analyst** (from dropdown)

**Context:**
- Leave empty (this is our first task, no dependencies)

### Step 4: Save Task

Click **"Save"** button

**Result:** Task appears in tasks list

---

## Part 4: Create a Crew (2 minutes)

### Step 1: Navigate to Crews Page

Click **"Crews"** in left sidebar

### Step 2: Click "Create crew"

### Step 3: Configure Crew

**Name:**
```
Solar Analysis Crew
```

**Description:**
```
Analyzes solar system performance and provides optimization insights
```

**Process:**
- Select: **Sequential** (tasks run in order)

**Agents:**
- Click "Add Agent" button
- Select: ✅ **Solar Data Analyst**

**Tasks:**
- Click "Add Task" button
- Select: ✅ **Analyze solar production data...** (the task we created)

### Step 4: Save Crew

Click **"Save"** button

**Result:** Crew appears in crews list with:
- Name: Solar Analysis Crew
- Agents: 1 (Solar Data Analyst)
- Tasks: 1
- Process: Sequential

---

## Part 5: Run Your Crew! (3 minutes)

### Step 1: Navigate to Kickoff! Page

Click **"Kickoff!"** in left sidebar

### Step 2: Select Your Crew

From dropdown:
- Select: **Solar Analysis Crew**

You'll see:
- Crew details
- Agents assigned
- Tasks to execute

### Step 3: Kickoff!

Click the big **"Kickoff Crew"** button

### Step 4: Monitor Execution

You'll see:
- **Status updates** in real-time
- **Agent thoughts** (because we enabled verbose mode)
- **Tool usage** (if agent searches web or runs code)
- **Progress through tasks**

**Expected timeline:**
- Task 1: 1-2 minutes (research and analysis)
- Total: 2-3 minutes

### Step 5: Review Results

When execution completes:
- **Status:** ✅ Success
- **Output:** Markdown report with solar analysis findings

**Sample Output:**
```markdown
# Solar Performance Analysis Report

## 1. Summary
Solar panel performance is measured by efficiency...

## 2. Key Metrics
- **Capacity Factor:** Actual vs theoretical production
- **Performance Ratio (PR):** Overall system efficiency
- **Specific Yield:** kWh per kW installed
...
```

---

## Part 6: View Results (1 minute)

### Step 1: Navigate to Results Page

Click **"Results"** in left sidebar

### Step 2: Find Your Execution

You'll see a list of crew runs:
- Timestamp: (when you ran it)
- Crew: Solar Analysis Crew
- Status: Success ✅

### Step 3: Click to Expand

Click on your execution to see:
- **Full output** (the markdown report)
- **Agent logs** (step-by-step thoughts)
- **Tool usage** (web searches, code execution)
- **Execution time**

### Step 4: Copy Output

You can copy the markdown report and use it!

---

## Part 7: Extend Your Crew (Optional)

### Create a Second Agent

**Role:** Energy Optimization Specialist

**Goal:** Provide specific, actionable recommendations to improve solar system efficiency

**Backstory:** You translate data insights into practical recommendations for system operators. You have 15+ years of field experience and excel at prioritizing improvements by impact and cost.

### Create a Second Task

**Description:** Based on the analysis results, provide 3-5 specific recommendations to optimize solar production. Include estimated impact and implementation difficulty for each.

**Expected Output:** Numbered list of recommendations with impact (High/Medium/Low) and difficulty (Easy/Medium/Hard)

**Agent:** Energy Optimization Specialist

**Context:** (Select the first task - this task will receive its output)

### Update Your Crew

1. Edit "Solar Analysis Crew"
2. Add second agent
3. Add second task
4. Save

### Run Again

Now your crew has 2 tasks:
1. Analyze performance (Agent 1)
2. Provide recommendations based on analysis (Agent 2 uses Agent 1's output)

---

## Troubleshooting

### Issue: "Agent not found" or Empty Dropdown

**Solution:**
- Refresh the page
- Ensure agent was saved (check Agents page)
- Database connection working (check Railway logs)

### Issue: Crew Execution Fails

**Check:**
1. **OpenAI API Key** configured in Railway
2. **Task description** is clear and specific
3. **Expected output** is well-defined
4. **Agent has necessary tools** enabled

**Common fixes:**
- Simplify task description
- Make expected output more specific
- Enable verbose mode to see where it fails

### Issue: Execution Takes Too Long

**Causes:**
- Task too complex
- Agent in reasoning loop
- Max iterations too high

**Solutions:**
- Break into smaller tasks
- Add more specific guidance in description
- Reduce max iterations (5-10 for simple tasks)

### Issue: Output Quality Poor

**Improve:**
1. **Agent backstory:** Add more expertise/context
2. **Task description:** Be more specific about what you want
3. **Expected output:** Provide example format
4. **LLM choice:** Try GPT-4 for better reasoning

---

## Quick Reference

### Agent Creation Checklist
- [ ] Clear, specific role
- [ ] Actionable goal
- [ ] Detailed backstory (2-4 sentences)
- [ ] Appropriate tools selected
- [ ] LLM model chosen
- [ ] Verbose mode ON (for learning)

### Task Creation Checklist
- [ ] Specific description with clear objective
- [ ] Expected output format defined
- [ ] Correct agent assigned
- [ ] Context tasks added (if building on previous work)

### Crew Creation Checklist
- [ ] Descriptive name
- [ ] Process type selected (Sequential for beginners)
- [ ] Agents added
- [ ] Tasks added in logical order

---

## Next Steps

### Experiment with Different Scenarios

Try creating crews for:
- **Research & Report:** Agent researches topic, another writes report
- **Data Analysis:** Agent analyzes data, another visualizes
- **Code Review:** Agent reviews code, another suggests improvements

### Learn Advanced Features

1. **Hierarchical Process:** Manager delegates to multiple agents
2. **Knowledge Base:** Add documents for agents to reference
3. **Custom Tools:** Create your own tools in Python
4. **Import/Export:** Share crew configurations

### Production Use

Once comfortable:
1. Use GPT-4 for complex reasoning tasks
2. Add authentication to protect your crews
3. Integrate with CommandCenter API
4. Automate crew execution via API calls

---

## Success Metrics

After this tutorial, you should be able to:
- ✅ Enable tools in Studio
- ✅ Create agents with roles, goals, and backstories
- ✅ Design tasks with clear descriptions and expected outputs
- ✅ Build crews that coordinate multiple agents
- ✅ Run crews and interpret results
- ✅ Debug issues when executions fail
- ✅ Extend crews with additional agents/tasks

---

## Resources

- **Full User Guide:** [CREWAI_STUDIO_USER_GUIDE.md](CREWAI_STUDIO_USER_GUIDE.md)
- **Testing Checklist:** [SESSION_015_TESTING_CHECKLIST.md](SESSION_015_TESTING_CHECKLIST.md)
- **CrewAI Docs:** https://docs.crewai.com/
- **Studio URL:** https://studio.wildfireranch.us

---

**Tutorial Complete!** 🎉

You now know how to create agents, tasks, and crews in CrewAI Studio!

**Time to build:** 10-15 minutes
**Difficulty:** Beginner
**Next:** Explore advanced features and build more complex crews!
