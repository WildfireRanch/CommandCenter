# Session 020: Energy Orchestrator Agent + Router Integration

**Copy this entire prompt to start your next session with Claude Code**

---

## 🎯 Session Goal

Build the **Energy Orchestrator Agent** with intelligent routing - a complete planning and optimization system that makes decisions about battery usage, miner operations, and energy allocation.

**What We're Building Today:**
1. **Energy Orchestrator Agent** - Planning & optimization specialist (6 hours)
2. **Update Manager Agent** - Enhanced routing logic (2 hours)

**Total Time:** 6-8 hours
**Current Progress:** V1.5 at 80% complete
**After This:** Session 3 (Polish & Ship) then V1.5 is DONE! 🚀

---

## 📋 Context: Where We Are

### ✅ What's Already Working
- **Backend API:** 18+ endpoints operational
- **Solar Controller Agent:** Monitors real-time status (battery, solar, load, grid)
- **Manager Agent:** Routes queries to Solar Controller OR KB search
- **Knowledge Base:** Full sync, search, deletion working
- **Database:** PostgreSQL + TimescaleDB + pgvector
- **Frontend:** 7 pages, all functional
- **Chat:** Working (bug fixed in Session 019)

### 🔨 What We're Building Today

**Energy Orchestrator Agent** with 3 tools:
1. **Battery Optimizer** - Recommends charge/discharge actions based on SOC and time
2. **Miner Coordinator** - Controls miner on/off based on power availability
3. **Energy Planner** - Creates 24-hour action plans

**Manager Agent Update:**
- Add Energy Orchestrator routing
- Enhanced keyword detection for planning queries
- Can coordinate both Solar Controller (status) and Energy Orchestrator (planning)

### 📚 Key Documents to Read First
1. **[docs/CODEBASE_AUDIT_OCT2025.md](../CODEBASE_AUDIT_OCT2025.md)** - Complete system inventory
2. **[docs/ORCHESTRATION_LAYER_DESIGN.md](../ORCHESTRATION_LAYER_DESIGN.md)** - Manager agent architecture
3. **[railway/src/agents/solar_controller.py](../../railway/src/agents/solar_controller.py)** - Agent pattern to follow
4. **[railway/src/agents/manager.py](../../railway/src/agents/manager.py)** - Current routing logic

---

## 🚀 Part 1: Build Energy Orchestrator Tools (4 hours)

### Tool 1: Battery Optimizer (1.5 hours)

**Create file:** `railway/src/tools/battery_optimizer.py`

**Purpose:** Recommend battery charge/discharge actions based on current state

**Implementation:**
```python
from crewai.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool("Battery Optimizer")
def optimize_battery(soc: float, time_of_day: int, weather_forecast: str = "unknown") -> str:
    """
    Recommend battery charge/discharge actions based on current state.

    Use this tool to get intelligent battery management recommendations that
    optimize for longevity, cost, and reliability.

    Args:
        soc: Current battery state of charge (0-100)
        time_of_day: Hour in 24-hour format (0-23)
        weather_forecast: "sunny", "cloudy", "clear", or "unknown"

    Returns:
        str: Recommendation with reasoning

    Decision Logic:
    - If SOC < 20%: CRITICAL - charge immediately from any source
    - If SOC < 40% and time_of_day > 16: Charge tonight (preserve battery for morning)
    - If SOC > 80% and time_of_day < 16 and sunny: Allow discharge (excess solar available)
    - If SOC 40-80%: Maintain (normal operation range)
    - Always include target SOC and reasoning

    Examples:
        >>> optimize_battery(45, 18, "clear")
        "CHARGE recommended. SOC is 45% and solar production will stop soon.
        Target 60%+ for morning operations. Grid charging acceptable tonight."

        >>> optimize_battery(85, 12, "sunny")
        "DISCHARGE OK. SOC is 85%, solar production strong (midday, sunny).
        Can discharge to 60% supporting miners and load. Battery longevity: optimal range is 40-80%."

        >>> optimize_battery(18, 14, "cloudy")
        "CRITICAL CHARGE. SOC is 18% - below minimum safe threshold (20%).
        Charge immediately from any available source. Risk of system shutdown."
    """
    try:
        logger.info(f"Battery optimization requested: SOC={soc}%, hour={time_of_day}, weather={weather_forecast}")

        # Critical low battery
        if soc < 20:
            return (
                f"⚠️ CRITICAL CHARGE IMMEDIATELY\\n"
                f"SOC: {soc}% (below minimum 20% threshold)\\n"
                f"Action: Charge from any available source NOW\\n"
                f"Risk: System shutdown imminent\\n"
                f"Target: Bring to 40%+ ASAP"
            )

        # Low battery, approaching evening
        if soc < 40 and time_of_day >= 16:
            return (
                f"🔋 CHARGE recommended\\n"
                f"SOC: {soc}% (below optimal 40-80% range)\\n"
                f"Time: {time_of_day}:00 (solar production ending soon)\\n"
                f"Action: Begin charging tonight\\n"
                f"Target: 60%+ for reliable morning operations\\n"
                f"Source: Grid charging acceptable during off-peak hours"
            )

        # High battery, strong solar
        if soc > 80 and time_of_day >= 8 and time_of_day <= 16:
            if weather_forecast == "sunny":
                return (
                    f"✅ DISCHARGE OK\\n"
                    f"SOC: {soc}% (above optimal range)\\n"
                    f"Time: {time_of_day}:00 (peak solar hours)\\n"
                    f"Weather: {weather_forecast} (strong production expected)\\n"
                    f"Action: Allow discharge to 60% supporting load and miners\\n"
                    f"Note: Staying in 40-80% range extends battery life"
                )
            else:
                return (
                    f"⚡ MAINTAIN recommended\\n"
                    f"SOC: {soc}% (high but weather uncertain)\\n"
                    f"Time: {time_of_day}:00\\n"
                    f"Weather: {weather_forecast}\\n"
                    f"Action: Hold current level, monitor production\\n"
                    f"Reason: Cloudy conditions may reduce solar charging ability"
                )

        # Normal operating range
        if 40 <= soc <= 80:
            return (
                f"✅ MAINTAIN optimal range\\n"
                f"SOC: {soc}% (optimal 40-80% for battery longevity)\\n"
                f"Time: {time_of_day}:00\\n"
                f"Action: No action needed, continue normal operations\\n"
                f"Status: Battery health optimal in this range"
            )

        # Edge cases
        return (
            f"📊 MODERATE action suggested\\n"
            f"SOC: {soc}%\\n"
            f"Time: {time_of_day}:00\\n"
            f"Action: Move toward optimal 40-80% range\\n"
            f"Target: {'Charge to 60%' if soc < 40 else 'Discharge to 60%'}"
        )

    except Exception as e:
        logger.error(f"Battery optimizer error: {e}")
        return f"Error in battery optimization: {str(e)}"
```

**Test it:**
```bash
cd railway
python -c "from src.tools.battery_optimizer import optimize_battery; print(optimize_battery(45, 18, 'clear'))"
python -c "from src.tools.battery_optimizer import optimize_battery; print(optimize_battery(85, 12, 'sunny'))"
python -c "from src.tools.battery_optimizer import optimize_battery; print(optimize_battery(18, 14, 'cloudy'))"
```

---

### Tool 2: Miner Coordinator (1.5 hours)

**Create file:** `railway/src/tools/miner_coordinator.py`

**Purpose:** Decide whether to run bitcoin miners based on power availability

**Implementation:**
```python
from crewai.tools import tool
import logging

logger = logging.getLogger(__name__)

@tool("Miner Coordinator")
def coordinate_miners(available_power: float, current_load: float, soc: float) -> str:
    """
    Decide whether to run bitcoin miners based on power availability and battery state.

    Use this tool to make intelligent miner control decisions that balance
    profitability with system reliability and battery health.

    Args:
        available_power: Watts available from solar + battery (after current load)
        current_load: Current house load in watts
        soc: Battery state of charge (0-100)

    Returns:
        str: Decision (START/STOP/MAINTAIN) with reasoning

    Policy (configurable via KB):
    - Miners draw ~2000W
    - Only START if SOC >= 60% (reserve margin)
    - STOP if SOC drops below 40% (protect battery)
    - Need 2500W+ available (miner load + safety buffer)
    - Never start miners if battery critical (<20%)

    Examples:
        >>> coordinate_miners(3500, 1200, 65)
        "START miners. SOC is 65% (above 60% threshold), available power 3500W
        exceeds requirement of 2500W. Profitable to mine with current conditions."

        >>> coordinate_miners(1800, 1200, 55)
        "STOP miners. Available power (1800W) insufficient for safe miner operation
        (need 2500W minimum). SOC is 55% but power constraint takes priority."

        >>> coordinate_miners(3000, 1000, 35)
        "STOP miners. SOC is 35% (below 40% threshold). Battery protection
        takes priority over mining profitability. Will resume when SOC >= 60%."
    """
    try:
        logger.info(f"Miner coordination requested: available={available_power}W, load={current_load}W, SOC={soc}%")

        # Constants (these can be moved to KB later)
        MINER_POWER_DRAW = 2000  # Watts per miner
        MIN_AVAILABLE_POWER = 2500  # Minimum watts needed (miner + buffer)
        MIN_SOC_TO_START = 60  # Don't start unless battery healthy
        MIN_SOC_TO_RUN = 40  # Stop if battery gets low
        CRITICAL_SOC = 20  # Never run if this low

        # Critical battery state - always stop
        if soc < CRITICAL_SOC:
            return (
                f"⛔ STOP miners IMMEDIATELY\\n"
                f"SOC: {soc}% (CRITICAL - below {CRITICAL_SOC}%)\\n"
                f"Reason: Battery protection is priority #1\\n"
                f"Action: Stop all miners immediately\\n"
                f"Resume when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Low battery - stop even if power available
        if soc < MIN_SOC_TO_RUN:
            return (
                f"🛑 STOP miners\\n"
                f"SOC: {soc}% (below {MIN_SOC_TO_RUN}% threshold)\\n"
                f"Available Power: {available_power}W (sufficient but SOC too low)\\n"
                f"Reason: Battery protection takes priority over mining\\n"
                f"Action: Stop miners, allow battery to charge\\n"
                f"Resume when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Insufficient power - stop regardless of SOC
        if available_power < MIN_AVAILABLE_POWER:
            return (
                f"🛑 STOP miners\\n"
                f"Available Power: {available_power}W (need {MIN_AVAILABLE_POWER}W minimum)\\n"
                f"SOC: {soc}% (adequate but power insufficient)\\n"
                f"Reason: Insufficient power for safe miner operation\\n"
                f"Miner Draw: ~{MINER_POWER_DRAW}W + {MIN_AVAILABLE_POWER - MINER_POWER_DRAW}W buffer\\n"
                f"Action: Stop miners until solar production increases or load decreases"
            )

        # Good conditions but SOC not quite ready to start
        if soc >= MIN_SOC_TO_RUN and soc < MIN_SOC_TO_START and available_power >= MIN_AVAILABLE_POWER:
            return (
                f"⏸️ MAINTAIN (don't start new miners)\\n"
                f"SOC: {soc}% (safe to run but below {MIN_SOC_TO_START}% start threshold)\\n"
                f"Available Power: {available_power}W (sufficient)\\n"
                f"Action: If miners already running, continue. Don't start new ones.\\n"
                f"Reason: Build battery reserve before adding more load\\n"
                f"Start miners when: SOC >= {MIN_SOC_TO_START}%"
            )

        # Excellent conditions - start or continue miners
        if soc >= MIN_SOC_TO_START and available_power >= MIN_AVAILABLE_POWER:
            return (
                f"✅ START/CONTINUE miners\\n"
                f"SOC: {soc}% (above {MIN_SOC_TO_START}% threshold) ✓\\n"
                f"Available Power: {available_power}W (exceeds {MIN_AVAILABLE_POWER}W requirement) ✓\\n"
                f"Current Load: {current_load}W\\n"
                f"Miner Power: ~{MINER_POWER_DRAW}W\\n"
                f"Action: Safe to run miners, conditions optimal\\n"
                f"Monitor: Stop if SOC drops below {MIN_SOC_TO_RUN}% or available power < {MIN_AVAILABLE_POWER}W"
            )

        # Fallback
        return (
            f"⏸️ MAINTAIN current state\\n"
            f"SOC: {soc}%\\n"
            f"Available Power: {available_power}W\\n"
            f"Action: Continue current operations, monitor conditions"
        )

    except Exception as e:
        logger.error(f"Miner coordinator error: {e}")
        return f"Error in miner coordination: {str(e)}"
```

**Test it:**
```bash
cd railway
python -c "from src.tools.miner_coordinator import coordinate_miners; print(coordinate_miners(3500, 1200, 65))"
python -c "from src.tools.miner_coordinator import coordinate_miners; print(coordinate_miners(1800, 1200, 55))"
python -c "from src.tools.miner_coordinator import coordinate_miners; print(coordinate_miners(3000, 1000, 35))"
```

---

### Tool 3: Energy Planner (1 hour)

**Create file:** `railway/src/tools/energy_planner.py`

**Purpose:** Create 24-hour energy action plan

**Implementation:**
```python
from crewai.tools import tool
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

@tool("Energy Planner")
def create_energy_plan(current_soc: float, time_now: int, forecast: str = "typical") -> str:
    """
    Create 24-hour energy action plan based on current state and forecast.

    Use this tool to generate hour-by-hour recommendations for the next 24 hours,
    optimizing battery usage, miner operations, and grid interaction.

    Args:
        current_soc: Current battery state of charge (0-100)
        time_now: Current hour in 24-hour format (0-23)
        forecast: "sunny", "cloudy", "typical", or "rainy"

    Returns:
        str: Formatted 24-hour plan with hourly recommendations

    Planning Logic:
    - Solar production curve: 0W before 6am, peak 10am-2pm, 0W after 6pm
    - Forecast adjusts peak production (sunny=100%, typical=75%, cloudy=50%, rainy=25%)
    - Battery: charge to 60%+ before peak solar, discharge to 40% overnight OK
    - Miners: run during peak solar (10am-4pm) if conditions allow
    - Grid: use for charging only if SOC critical or off-peak hours

    Example output:
        "📅 24-Hour Energy Plan (Starting 18:00)

        Current Status: SOC 52%, Forecast: typical

        NOW (18:00-22:00) - Evening Charge Window
        ├─ Solar: 0W (sunset complete)
        ├─ Battery: Charge from grid if < 40% (currently 52% - OK)
        ├─ Miners: OFF (conserve battery for overnight)
        └─ Action: Minimal discharge, house load only

        22:00-06:00 - Overnight Conservation
        ├─ Solar: 0W
        ├─ Battery: Slow discharge (house load ~1200W)
        ├─ Miners: OFF
        └─ Target SOC at 6am: 45%+ (currently 52%, should end ~48%)

        06:00-10:00 - Morning Solar Ramp
        ├─ Solar: 0W → 4000W (gradual increase)
        ├─ Battery: Begin charging as production exceeds load
        ├─ Miners: OFF (let battery charge first)
        └─ Target: Reach 60%+ by 10am

        10:00-16:00 - Peak Production Window ☀️
        ├─ Solar: 5000-6000W (forecast: typical = 75% of max)
        ├─ Battery: Maintain 60-80% (optimal range)
        ├─ Miners: START if SOC >= 60% and available power > 2500W
        ├─ Load: House (~1200W) + Miners (~2000W) = 3200W
        └─ Action: Profitable mining with excess solar

        16:00-18:00 - Evening Wind-Down
        ├─ Solar: 4000W → 0W (rapid decline)
        ├─ Battery: Stop charging, prepare for evening
        ├─ Miners: STOP by 17:00 latest
        └─ Target: Enter evening at 55%+ SOC"
    """
    try:
        logger.info(f"Energy plan requested: SOC={current_soc}%, hour={time_now}, forecast={forecast}")

        # Solar production multipliers based on forecast
        forecast_multipliers = {
            "sunny": 1.0,
            "typical": 0.75,
            "cloudy": 0.50,
            "rainy": 0.25
        }
        multiplier = forecast_multipliers.get(forecast.lower(), 0.75)

        # Build the plan
        plan = f"📅 24-Hour Energy Plan (Starting {time_now:02d}:00)\\n\\n"
        plan += f"Current Status: SOC {current_soc}%, Forecast: {forecast}\\n"
        plan += f"Solar Production: {int(multiplier * 100)}% of typical\\n\\n"

        # Current evening (18:00-22:00)
        if 18 <= time_now or time_now < 6:
            plan += "🌙 NOW → Evening/Night Period (18:00-06:00)\\n"
            plan += "├─ Solar: 0W (no production overnight)\\n"
            if current_soc < 40:
                plan += f"├─ Battery: CHARGE from grid (currently {current_soc}% - below 40%)\\n"
                plan += "├─ Miners: OFF (allow battery to charge)\\n"
                plan += f"└─ ⚠️ PRIORITY: Bring SOC to 60%+ before morning\\n\\n"
            else:
                plan += f"├─ Battery: Slow discharge OK (currently {current_soc}% - safe)\\n"
                plan += "├─ Miners: OFF (conserve for overnight)\\n"
                plan += f"└─ Expected SOC at 6am: ~{max(40, current_soc - 8)}% (normal overnight draw)\\n\\n"

        # Morning (6:00-10:00)
        plan += "🌅 Morning Solar Ramp (06:00-10:00)\\n"
        plan += f"├─ Solar: 0W → {int(4000 * multiplier)}W (gradual increase)\\n"
        plan += "├─ Battery: Begin charging as production > load\\n"
        plan += "├─ Miners: OFF (let battery charge first)\\n"
        plan += "└─ Target: Reach 60%+ SOC by 10am for miner operations\\n\\n"

        # Peak production (10:00-16:00)
        plan += f"☀️ Peak Production Window (10:00-16:00)\\n"
        plan += f"├─ Solar: {int(5000 * multiplier)}-{int(6000 * multiplier)}W (peak hours)\\n"

        if multiplier >= 0.6:  # Good solar conditions
            plan += "├─ Battery: Maintain 60-80% (optimal range)\\n"
            plan += "├─ Miners: START if SOC >= 60% and power available\\n"
            plan += f"├─ Estimated available: {int(5000 * multiplier)} - 1200 (load) = {int(5000 * multiplier - 1200)}W\\n"
            plan += "└─ ✅ PROFITABLE mining window - excess solar available\\n\\n"
        else:  # Poor solar conditions
            plan += "├─ Battery: Charge what you can (limited production)\\n"
            plan += "├─ Miners: Likely OFF (insufficient solar)\\n"
            plan += f"├─ Estimated available: {int(5000 * multiplier)} - 1200 (load) = {int(5000 * multiplier - 1200)}W\\n"
            plan += f"└─ ⚠️ LOW PRODUCTION ({forecast}) - conserve battery\\n\\n"

        # Evening wind-down (16:00-18:00)
        plan += "🌇 Evening Wind-Down (16:00-18:00)\\n"
        plan += f"├─ Solar: {int(4000 * multiplier)}W → 0W (rapid decline)\\n"
        plan += "├─ Battery: Stop charging, prepare for night\\n"
        plan += "├─ Miners: STOP by 17:00 latest\\n"
        plan += "└─ Target: Enter evening at 55%+ SOC\\n\\n"

        # Summary
        plan += "📊 24-Hour Summary\\n"
        plan += f"├─ Expected Solar: {int(20 * multiplier)}kWh (forecast-adjusted)\\n"
        plan += f"├─ Miner Potential: {'6 hours' if multiplier >= 0.6 else '0-2 hours'} (10am-4pm window)\\n"
        plan += f"├─ Grid Usage: {'Minimal' if current_soc >= 40 else 'Charge tonight required'}\\n"
        plan += "└─ Battery Cycles: ~0.3 (healthy, extends battery life)\\n"

        return plan

    except Exception as e:
        logger.error(f"Energy planner error: {e}")
        return f"Error creating energy plan: {str(e)}"
```

**Test it:**
```bash
cd railway
python -c "from src.tools.energy_planner import create_energy_plan; print(create_energy_plan(52, 18, 'typical'))"
python -c "from src.tools.energy_planner import create_energy_plan; print(create_energy_plan(35, 8, 'sunny'))"
```

---

## 🤖 Part 2: Create Energy Orchestrator Agent (2 hours)

**Create file:** `railway/src/agents/energy_orchestrator.py`

**Pattern:** Follow `railway/src/agents/solar_controller.py`

```python
# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/agents/energy_orchestrator.py
# PURPOSE: Energy planning and optimization agent
# ═══════════════════════════════════════════════════════════════════════════

from crewai import Agent, Crew, Task
from crewai.tools import tool

from ..tools.battery_optimizer import optimize_battery
from ..tools.miner_coordinator import coordinate_miners
from ..tools.energy_planner import create_energy_plan
from ..tools.kb_search import search_knowledge_base
from ..tools.solark import get_solark_status, format_status_summary


# Wrapper tool to get current status for planning
@tool("Get Current Energy Status")
def get_current_status() -> str:
    """
    Get current energy system status for planning decisions.

    Returns current battery SOC, solar production, load, and grid usage.
    Use this before making planning recommendations.
    """
    try:
        status = get_solark_status()
        return format_status_summary(status)
    except Exception as e:
        return f"Error getting status: {str(e)}"


def create_energy_orchestrator() -> Agent:
    """Create the Energy Orchestrator agent."""
    return Agent(
        role="Energy Operations Manager",
        goal="Plan and optimize daily energy usage to maximize reliability and minimize costs",
        backstory="""You are the energy operations manager for a solar-powered
        off-grid ranch with battery storage and bitcoin mining operations.

        Your responsibilities:
        - Optimize battery charge/discharge cycles for longevity
        - Coordinate bitcoin miner operations based on available power
        - Create 24-hour energy plans considering forecasts and priorities
        - Balance profitability (mining) with reliability (always-on power)
        - Ensure battery is never damaged by over-discharge

        You have access to:
        - Real-time system status (battery, solar, load, grid)
        - Knowledge base with operational policies and thresholds
        - Planning tools for battery, miners, and scheduling

        Your priorities (in order):
        1. System reliability (never let battery go critical)
        2. Battery health (operate in 40-80% range when possible)
        3. Cost optimization (minimize grid usage)
        4. Mining profitability (when conditions allow)

        You make data-driven decisions, cite policies from the knowledge base,
        and provide clear reasoning for all recommendations.""",
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
    context_section = ""
    if context:
        context_section = f"\\n\\nPrevious conversation context:\\n{context}\\n"

    return Task(
        description=f"""Handle this energy planning or optimization query: {query}
        {context_section}
        Instructions:
        1. If asking about current status, use Get Current Energy Status tool
        2. For battery questions, use Battery Optimizer tool
        3. For miner questions, use Miner Coordinator tool
        4. For planning/scheduling, use Energy Planner tool
        5. For policies/thresholds, search Knowledge Base
        6. Provide clear recommendations with reasoning
        7. Cite sources when referencing policies

        The user's question: {query}
        """,
        expected_output="""A clear, actionable response with:
        - Specific recommendations or plans
        - Reasoning based on current state and policies
        - Any relevant warnings or considerations
        - Citations to knowledge base when applicable
        - No speculation - use tools to get real data""",
        agent=create_energy_orchestrator(),
    )


def create_orchestrator_crew(query: str, context: str = "") -> Crew:
    """Create crew for energy planning queries."""
    agent = create_energy_orchestrator()
    task = create_orchestrator_task(query, context)

    return Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the orchestrator from command line."""
    import sys

    test_query = "Should we run the miners right now?"

    if len(sys.argv) > 1:
        test_query = " ".join(sys.argv[1:])

    print(f"🤖 Testing Energy Orchestrator")
    print(f"📝 Query: {test_query}\\n")

    try:
        crew = create_orchestrator_crew(test_query)
        result = crew.kickoff()

        print("\\n" + "="*70)
        print("RESULT:")
        print("="*70)
        print(result)
        print("="*70)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
```

**Test the agent:**
```bash
cd railway
python -m src.agents.energy_orchestrator "Should we run the miners tonight?"
python -m src.agents.energy_orchestrator "Create an energy plan for today"
python -m src.agents.energy_orchestrator "What's the battery optimization recommendation?"
```

---

## 🔀 Part 3: Update Manager Agent Routing (1 hour)

**Edit file:** `railway/src/agents/manager.py`

**Add this new routing tool:**

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
    - Battery management strategies

    Examples:
    - "Should we run the miners tonight?"
    - "Create an energy plan for today"
    - "What's the best time to charge the battery?"
    - "When should we stop the miners?"

    Args:
        query: Planning/optimization question

    Returns:
        Response from Energy Orchestrator agent
    """
    try:
        from .energy_orchestrator import create_orchestrator_crew
        crew = create_orchestrator_crew(query)
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error routing to Energy Orchestrator: {str(e)}"
```

**Update manager agent backstory** to mention Energy Orchestrator:

Find this section in `create_manager_agent()`:
```python
You have access to:
1. Solar Controller Agent - Real-time monitoring specialist
   (current battery, solar production, power usage, status)

2. Knowledge Base - Documentation and procedures
   (specifications, policies, how-to guides, thresholds)
```

**Change it to:**
```python
You have access to:
1. Solar Controller Agent - Real-time monitoring specialist
   (current battery, solar production, power usage, status)

2. Energy Orchestrator Agent - Planning and optimization specialist
   (should we run miners, create energy plan, battery optimization)

3. Knowledge Base - Documentation and procedures
   (specifications, policies, how-to guides, thresholds)
```

**Add routing guidelines:**
```python
ROUTING GUIDELINES:

For CURRENT/REAL-TIME questions → Use Solar Controller
- "What's my battery level?"
- "How much solar am I producing?"
- "What's the current status?"

For PLANNING/OPTIMIZATION questions → Use Energy Orchestrator
- "Should we run the miners?"
- "Create an energy plan"
- "When should we charge the battery?"
- "What's the best strategy for..."

For DOCUMENTATION/POLICY questions → Search Knowledge Base
- "What is the minimum SOC threshold?"
- "How do I maintain the panels?"
- "What are the specifications?"

For UNCLEAR questions → Ask for clarification
- "Help me" → Ask what they need help with
- "What should I do?" → Ask what they're trying to achieve
```

**Update the tools list:**
```python
tools=[route_to_solar_controller, route_to_energy_orchestrator, search_kb_directly],
```

---

## 🧪 Part 4: Testing (1 hour)

### Unit Tests

Test each component individually:

```bash
# Test tools
cd railway
python -c "from src.tools.battery_optimizer import optimize_battery; print(optimize_battery(45, 18, 'clear'))"
python -c "from src.tools.miner_coordinator import coordinate_miners; print(coordinate_miners(3500, 1200, 65))"
python -c "from src.tools.energy_planner import create_energy_plan; print(create_energy_plan(52, 18, 'typical'))"

# Test agent
python -m src.agents.energy_orchestrator "Should we run the miners now?"

# Test manager routing
python -m src.agents.manager "Should we run the miners now?"
# Should route to Energy Orchestrator

python -m src.agents.manager "What's my battery level?"
# Should route to Solar Controller
```

### Integration Tests

**Test 1: Planning Query**
```bash
curl -X POST https://api.wildfireranch.us/ask \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Should we run the miners tonight?"}'
```
**Expected:** Manager → Energy Orchestrator → Uses tools → Returns recommendation

**Test 2: Status Query**
```bash
curl -X POST https://api.wildfireranch.us/ask \\
  -H "Content-Type: application/json" \\
  -d '{"message": "What is my current battery level?"}'
```
**Expected:** Manager → Solar Controller → Returns current SOC

**Test 3: Multi-part Query**
```bash
curl -X POST https://api.wildfireranch.us/ask \\
  -H "Content-Type: application/json" \\
  -d '{"message": "Check current status and create an energy plan for today"}'
```
**Expected:** Manager delegates to both agents or handles sequentially

---

## 🚀 Part 5: Deploy (15 min)

```bash
git add .
git commit -m "Add Energy Orchestrator agent with planning tools

Features:
- Battery optimizer tool (charge/discharge recommendations)
- Miner coordinator tool (on/off decisions based on power/SOC)
- Energy planner tool (24-hour scheduling)
- Energy Orchestrator agent (planning & optimization specialist)
- Manager routing updated (routes to Orchestrator for planning queries)

All tools tested individually and integrated
Manager successfully routes planning vs status queries
V1.5 now at 95% complete!

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"

git push
```

**Monitor Railway deployment:**
- Check logs for errors
- Test via API endpoints
- Verify both agents working

---

## ✅ Success Criteria

**You're done when:**

- [ ] Battery optimizer tool works (tested with 3+ scenarios)
- [ ] Miner coordinator tool works (tested with 3+ scenarios)
- [ ] Energy planner tool works (tested with 2+ scenarios)
- [ ] Energy Orchestrator agent created and uses tools
- [ ] Manager routes planning queries to Orchestrator
- [ ] Manager routes status queries to Solar Controller
- [ ] All integration tests pass
- [ ] Deployed to Railway successfully
- [ ] No critical errors in logs

---

## 🆘 Troubleshooting

### Tools not working?
```
Claude, the [tool name] isn't working.
Error: [paste error]
Test case: [what you tried]

Please debug the tool function.
```

### Agent not using tools?
```
Claude, the Energy Orchestrator isn't using tools.
Query: [paste query]
Response: [what happened]

Please check:
1. Are tools in agent's tools list?
2. Tool descriptions clear?
3. Agent backstory mentions tools?
```

### Manager routing wrong?
```
Claude, Manager routing to wrong agent.
Query: [paste]
Routed to: [wrong agent]
Should be: [correct agent]

Please update routing logic.
```

---

## 🎉 After This Session

**You'll have:**
- ✅ Energy Orchestrator working with 3 tools
- ✅ Manager routing to 3 specialists
- ✅ Complete planning and monitoring system
- ✅ **V1.5 at 95% complete!**

**Then Session 021: Polish & Ship** (2-3 hours)
- Polish chat interface
- Show KB sources
- Agent status indicators
- End-to-end testing
- **Ship V1.5! 🚀**

---

## 📊 Time Breakdown

- Part 1 (Tools): 4 hours
  - Battery Optimizer: 1.5 hours
  - Miner Coordinator: 1.5 hours
  - Energy Planner: 1 hour
- Part 2 (Agent): 2 hours
- Part 3 (Routing): 1 hour
- Part 4 (Testing): 1 hour
- Part 5 (Deploy): 15 min
- **Total: 8 hours**

---

**Ready to build! Let's ship Energy Orchestrator!** 🚀

**Status:** All documentation organized, system at 80%, ready to code
**Next:** Build tools → Agent → Routing → Test → Deploy
**Then:** One more session and V1.5 ships! 💪
