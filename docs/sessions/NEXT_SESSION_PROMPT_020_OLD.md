# Session 020 Start Prompt: Build Energy Orchestrator Agent

**Copy this entire prompt to start your next session with Claude Code**

---

## 🎯 Session Goal

Build the **Energy Orchestrator Agent** - a planning and optimization agent that makes intelligent decisions about battery usage, miner operations, and energy allocation based on current state, forecasts, and policies.

**Estimated Time:** 6-8 hours
**Current Progress:** V1.5 at 80% complete
**After This:** Session 3 (Polish & Ship) then V1.5 is DONE! 🚀

---

## 📋 Context: Where We Are

### ✅ What's Already Working
- **Backend API:** 18+ endpoints operational
- **Solar Controller Agent:** Monitors real-time status (battery, solar, load, grid)
- **Manager Agent:** Routes queries intelligently to specialists
- **Knowledge Base:** Full sync, search, deletion working
- **Database:** PostgreSQL + TimescaleDB + pgvector
- **Frontend:** 7 pages, all functional
- **Chat:** Working (bug fixed in Session 019)

### 🔨 What We're Building Today
**Energy Orchestrator Agent** with 3 tools:
1. **Battery Optimizer** - Recommends charge/discharge actions
2. **Miner Coordinator** - Controls miner on/off based on power availability
3. **Energy Planner** - Creates 24-hour action plans

### 📚 Key Documents to Read First
1. **[docs/CODEBASE_AUDIT_OCT2025.md](CODEBASE_AUDIT_OCT2025.md)** - Complete system inventory
2. **[docs/ORCHESTRATION_LAYER_DESIGN.md](ORCHESTRATION_LAYER_DESIGN.md)** - Manager agent architecture
3. **[docs/08-Remaining_v1-5.md](08-Remaining_%20v1-5.md)** - V1.5 execution plan
4. **[docs/sessions/SESSION_019_ORCHESTRATION_SUMMARY.md](sessions/SESSION_019_ORCHESTRATION_SUMMARY.md)** - Last session summary

---

## 🚀 Step-by-Step Instructions

### Phase 1: Design the Agent (1 hour)

**Task:** Create the Energy Orchestrator design document

**Create file:** `docs/ENERGY_ORCHESTRATOR_DESIGN.md`

**What to include:**
1. **Agent Role & Backstory**
   - Role: "Energy System Planner and Coordinator"
   - Goal: Optimize energy usage while ensuring reliable power
   - Backstory: Solar-powered off-grid ranch coordinator

2. **Decision-Making Logic**
   - Battery optimization (charge during off-peak, discharge during peak)
   - Miner control (pause when SOC < 40%, resume when SOC > 60%)
   - Energy planning (24-hour forecast-based scheduling)

3. **Tools Required**
   - `battery_optimizer(soc, time_of_day, weather)` → recommendation
   - `miner_coordinator(available_power, current_load)` → on/off decision
   - `energy_planner(forecast, current_state)` → 24h plan

4. **Safety Guardrails**
   - Never discharge battery below 20%
   - Always confirm before major changes
   - Dry-run mode by default

5. **Integration Points**
   - Works with Solar Controller (gets current status)
   - Uses KB search (for policies and thresholds)
   - Logs decisions to database

**Reference Documents:**
- Look at `railway/src/agents/solar_controller.py` for agent pattern
- Check `docs/02-old-stack-audit.md` for old Relay concepts to adapt

**Deliverable:** Design doc for review before building

---

### Phase 2: Build the Tools (3-4 hours)

**Task:** Create 3 tools for energy management

#### Tool 1: Battery Optimizer

**Create file:** `railway/src/tools/battery_optimizer.py`

```python
from crewai.tools import tool
from typing import Dict, Any

@tool("Battery Optimizer")
def optimize_battery(soc: float, time_of_day: int, weather_forecast: str = "unknown") -> str:
    """
    Recommend battery charge/discharge actions based on current state.

    Args:
        soc: Current battery state of charge (0-100)
        time_of_day: Hour (0-23)
        weather_forecast: "sunny", "cloudy", "clear", or "unknown"

    Returns:
        Recommendation with reasoning

    Logic:
    - If SOC < 20%: CRITICAL - charge immediately
    - If SOC < 40% and time_of_day > 16: Charge tonight (preserve battery)
    - If SOC > 80% and time_of_day < 16 and sunny: Allow discharge (use solar)
    - If SOC 40-80%: Maintain (normal operation)

    Example:
        optimize_battery(45, 18, "clear") → "Charge battery tonight. SOC is 45%
        and solar production will stop soon. Target 60%+ for morning operations."
    """
    # Implementation here
    pass
```

**What to implement:**
- Decision tree based on SOC, time, weather
- Return structured recommendation with reasoning
- Include target SOC ranges
- Log decision to database (optional)

#### Tool 2: Miner Coordinator

**Create file:** `railway/src/tools/miner_coordinator.py`

```python
from crewai.tools import tool

@tool("Miner Coordinator")
def coordinate_miners(available_power: float, current_load: float, soc: float) -> str:
    """
    Decide whether to run bitcoin miners based on power availability.

    Args:
        available_power: Watts available (solar + battery - load)
        current_load: Current house load in watts
        soc: Battery state of charge (0-100)

    Returns:
        Decision with reasoning

    Policy (can be overridden by KB):
    - Miners draw ~2000W
    - Only run if SOC > 60%
    - Only run if available_power > 2500W (buffer)
    - Pause if SOC drops below 40%

    Example:
        coordinate_miners(3500, 1200, 65) → "START miners. SOC is 65%, available
        power 3500W exceeds requirement of 2500W."
    """
    # Implementation here
    pass
```

**What to implement:**
- Check SOC threshold (from KB or hardcoded default)
- Calculate if enough power available
- Return START/STOP/MAINTAIN decision
- Include reasoning

#### Tool 3: Energy Planner

**Create file:** `railway/src/tools/energy_planner.py`

```python
from crewai.tools import tool
from typing import Dict

@tool("Energy Planner")
def create_energy_plan(current_soc: float, time_now: int, forecast: str = "typical") -> str:
    """
    Create 24-hour energy action plan.

    Args:
        current_soc: Current battery state of charge (0-100)
        time_now: Current hour (0-23)
        forecast: "sunny", "cloudy", "typical"

    Returns:
        Hour-by-hour plan for next 24 hours

    Plan includes:
    - Expected solar production by hour
    - Battery charge/discharge plan
    - Miner run windows
    - Critical actions (if any)

    Example output:
        "24-Hour Energy Plan:
        Now (18:00): SOC 52%, solar ending soon
        18:00-22:00: Charge battery from grid (if needed), miners OFF
        22:00-06:00: Minimal discharge, house load only
        06:00-10:00: Solar ramp-up, charge to 80%
        10:00-16:00: Miners ON (excess solar), maintain 60%+
        16:00-18:00: Reduce load, prepare for evening"
    """
    # Implementation here
    pass
```

**What to implement:**
- Generate hour-by-hour recommendations
- Account for typical solar curve (0W at night, peak at noon)
- Include miner scheduling
- Format as clear, actionable plan

**Testing Each Tool:**
```bash
# Test battery optimizer
cd railway
python -c "from src.tools.battery_optimizer import optimize_battery; print(optimize_battery(45, 18, 'clear'))"

# Test miner coordinator
python -c "from src.tools.miner_coordinator import coordinate_miners; print(coordinate_miners(3500, 1200, 65))"

# Test energy planner
python -c "from src.tools.energy_planner import create_energy_plan; print(create_energy_plan(52, 18, 'typical'))"
```

---

### Phase 3: Create the Agent (1-2 hours)

**Task:** Build the Energy Orchestrator agent

**Create file:** `railway/src/agents/energy_orchestrator.py`

**Follow the pattern from:** `railway/src/agents/solar_controller.py`

**Agent Structure:**
```python
from crewai import Agent, Crew, Task

from ..tools.battery_optimizer import optimize_battery
from ..tools.miner_coordinator import coordinate_miners
from ..tools.energy_planner import create_energy_plan
from ..tools.kb_search import search_knowledge_base
from ..tools.solark import get_solark_status  # To get current data

@tool("Get Current Energy Status")
def get_current_status() -> dict:
    """Get current energy system status for planning."""
    # Wrapper around get_solark_status for orchestrator
    pass

def create_energy_orchestrator() -> Agent:
    return Agent(
        role="Energy System Planner and Coordinator",
        goal="Optimize energy usage while ensuring reliable power supply",
        backstory="""You are responsible for optimizing energy usage at a
        solar-powered off-grid ranch. You coordinate between the solar controller,
        battery system, and bitcoin miners to maximize efficiency while ensuring
        reliable power. You make decisions based on current SOC, time of day,
        weather forecasts, and operational priorities.

        You have access to the knowledge base with operational procedures and
        policies. Always cite your sources when referencing policies.""",
        tools=[
            get_current_status,
            optimize_battery,
            coordinate_miners,
            create_energy_plan,
            search_knowledge_base
        ],
        verbose=True,
        allow_delegation=False,
    )

def create_orchestrator_task(query: str, context: str = "") -> Task:
    """Create planning/optimization task."""
    # Similar to create_status_task in solar_controller.py
    pass

def create_orchestrator_crew(query: str, context: str = "") -> Crew:
    """Create crew for energy planning queries."""
    agent = create_energy_orchestrator()
    task = create_orchestrator_task(query, context)

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )
```

**Test the agent:**
```bash
cd railway
python -m src.agents.energy_orchestrator "Should we run the miners right now?"
```

---

### Phase 4: Add Routing to Manager (30 min)

**Task:** Update Manager agent to route planning queries to Orchestrator

**File to edit:** `railway/src/agents/manager.py`

**Add this tool:**
```python
@tool("Route to Energy Orchestrator")
def route_to_energy_orchestrator(query: str) -> str:
    """
    Route to Energy Orchestrator for planning and optimization queries.

    Use when query is about:
    - "Should we" questions (run miners, charge battery, etc.)
    - Planning or scheduling
    - Optimization recommendations
    - Energy forecasts or predictions
    - Miner control decisions

    Examples:
    - "Should we run the miners tonight?"
    - "Create an energy plan for today"
    - "What's the best time to charge the battery?"

    Args:
        query: Planning/optimization question

    Returns:
        Response from Energy Orchestrator agent
    """
    from .energy_orchestrator import create_orchestrator_crew
    crew = create_orchestrator_crew(query)
    result = crew.kickoff()
    return str(result)
```

**Update manager agent:**
- Add `route_to_energy_orchestrator` to tools list
- Update backstory to mention Energy Orchestrator

**Test routing:**
```bash
cd railway
python -m src.agents.manager "Should we run the miners now?"
# Should route to Energy Orchestrator
```

---

### Phase 5: Test & Deploy (1 hour)

#### Unit Tests

**Test each component:**
1. Battery optimizer with various SOC levels
2. Miner coordinator with different power scenarios
3. Energy planner with different times/forecasts
4. Agent responses to planning queries

#### Integration Tests

**Test these scenarios:**

1. **Planning Query:**
   ```bash
   curl -X POST https://api.wildfireranch.us/ask \
     -H "Content-Type: application/json" \
     -d '{"message": "Should we run the miners tonight?"}'
   ```
   Expected: Manager → Energy Orchestrator → Uses tools → Returns plan

2. **Current Status + Planning:**
   ```bash
   curl -X POST https://api.wildfireranch.us/ask \
     -H "Content-Type: application/json" \
     -d '{"message": "Check current status and create an energy plan"}'
   ```
   Expected: Manager → Both agents → Coordinated response

3. **KB Policy Query:**
   ```bash
   curl -X POST https://api.wildfireranch.us/ask \
     -H "Content-Type: application/json" \
     -d '{"message": "What is the miner SOC threshold policy?"}'
   ```
   Expected: Manager → KB Search → Policy from docs

#### Deploy to Railway

```bash
git add .
git commit -m "Add Energy Orchestrator agent with planning tools

Features:
- Battery optimizer tool (charge/discharge recommendations)
- Miner coordinator tool (on/off decisions)
- Energy planner tool (24-hour scheduling)
- Energy Orchestrator agent (planning & optimization)
- Manager routing to Orchestrator

Tested: All tools working, routing functional

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

**Monitor deployment:**
- Check Railway logs for errors
- Test via API endpoint
- Verify database logging

---

## 📝 Documentation

**Create file:** `docs/ENERGY_ORCHESTRATOR_TESTING.md`

**Document:**
- What was tested
- Test results (pass/fail)
- Example queries and responses
- Known limitations
- Next steps

---

## ✅ Success Criteria

**You're done when:**

- [ ] Design document created and makes sense
- [ ] All 3 tools built and tested individually
- [ ] Energy Orchestrator agent created
- [ ] Manager routes planning queries to Orchestrator
- [ ] Agent uses tools correctly
- [ ] Agent searches KB for policies
- [ ] All integration tests passing
- [ ] Deployed to Railway successfully
- [ ] Testing doc created
- [ ] No critical errors in Railway logs

---

## 🆘 If You Get Stuck

### Issue: Tools not working
```
Claude, the [tool name] isn't working correctly.

Error: [paste error]

Test case: [what you tried]
Expected: [what should happen]
Actual: [what happened]

Please debug:
1. Check tool function signature
2. Verify @tool decorator
3. Test with simple inputs
4. Check error logs
```

### Issue: Agent not using tools
```
Claude, the Energy Orchestrator isn't using the tools.

Query: [paste query]
Response: [agent response]
Expected: Should use [tool name]

Please check:
1. Are tools in agent's tools list?
2. Is tool description clear?
3. Is agent instruction clear?
4. Test tool directly
```

### Issue: Manager not routing correctly
```
Claude, the Manager is routing to the wrong agent.

Query: [paste query]
Routed to: [wrong agent]
Should route to: [correct agent]

Please:
1. Check routing tool descriptions
2. Update manager backstory if needed
3. Test routing logic
```

---

## 📊 Expected Time Breakdown

- Phase 1 (Design): 1 hour
- Phase 2 (Tools): 3-4 hours
- Phase 3 (Agent): 1-2 hours
- Phase 4 (Routing): 30 min
- Phase 5 (Testing): 1 hour
- **Total: 6-8 hours**

---

## 🎉 What Happens After This Session

**You'll have:**
- ✅ Energy Orchestrator agent working
- ✅ 3 planning/optimization tools
- ✅ Manager routing to 3 specialists
- ✅ V1.5 at ~95% complete!

**Then Session 3:**
- Polish chat interface (2-3 hours)
- Show KB sources in responses
- Add agent status indicators
- End-to-end testing
- **Tag V1.5 release and SHIP! 🚀**

---

## 🚀 Ready to Start?

**Copy this prompt and start your session!**

Good luck! You're almost at V1.5 ship! 💪

---

**Last Updated:** October 8, 2025 - Session 019 Complete
**Next Session:** Session 020 - Energy Orchestrator
**Current V1.5 Progress:** 80% → Will be 95% after this session
