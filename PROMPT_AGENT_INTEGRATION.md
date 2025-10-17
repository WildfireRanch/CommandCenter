# 🤖 V1.9 Agent Integration Prompt (Tasks 3.2-3.4)

**Copy and paste this entire prompt into your next Claude Code session:**

---

I'm continuing CommandCenter V1.9 implementation - Agent Integration with User Preferences.

## 📚 Context Files (Read First)

1. **[CONTINUE_V1.9.md](CONTINUE_V1.9.md)** - Your main task guide
2. **[V1.9_TEST_REPORT.md](V1.9_TEST_REPORT.md)** - What was completed in Session 038
3. **[PROMPT_V1.9_FIXES_AND_AGENT_INTEGRATION.md](PROMPT_V1.9_FIXES_AND_AGENT_INTEGRATION.md)** - Full implementation guide (lines 579-842)
4. **[docs/sessions/2025-10/session-038-v1.9-security-fixes.md](docs/sessions/2025-10/session-038-v1.9-security-fixes.md)** - Session 038 summary

## ✅ Already Complete (Don't Redo)

- ✅ API Key Authentication middleware
- ✅ SQL Injection vulnerability patched
- ✅ Debug endpoints removed
- ✅ N+1 queries fixed (50% faster)
- ✅ Voltage-SOC converter service created and tested

## 🎯 Your Tasks (In Order)

### Task 3.2: Update Energy Orchestrator

**File:** `railway/src/agents/energy_orchestrator.py`

**Steps:**
1. Add imports:
   ```python
   from ..services.voltage_soc_converter import get_converter
   from ..utils.db import get_connection, query_one
   import os
   ```

2. Add at module level:
   ```python
   DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")
   ```

3. Add function to load preferences:
   ```python
   def load_user_preferences() -> dict:
       """Load user preferences from database."""
       try:
           with get_connection() as conn:
               prefs = query_one(
                   conn,
                   """
                   SELECT
                       voltage_at_0_percent, voltage_at_100_percent, voltage_curve,
                       voltage_shutdown, voltage_critical_low, voltage_low,
                       voltage_restart, voltage_optimal_min, voltage_optimal_max,
                       voltage_float, voltage_absorption, voltage_full,
                       timezone, operating_mode
                   FROM user_preferences
                   WHERE user_id = %s::uuid
                   LIMIT 1
                   """,
                   (DEFAULT_USER_ID,),
                   as_dict=True
               )
               return dict(prefs) if prefs else {}
       except Exception as e:
           logger.error(f"Failed to load preferences: {e}")
           return {
               'voltage_at_0_percent': 45.0,
               'voltage_at_100_percent': 56.0,
               'voltage_optimal_min': 50.0,
               'voltage_optimal_max': 54.5,
               'voltage_low': 47.0,
               'voltage_critical_low': 45.0,
               'operating_mode': 'balanced'
           }
   ```

4. Update crew creation function to load preferences and pass to tools:
   ```python
   def create_energy_orchestrator_crew():
       # Load preferences
       user_prefs = load_user_preferences()
       converter = get_converter(user_prefs)

       # Pass to tools
       battery_tool = BatteryOptimizerTool(
           user_preferences=user_prefs,
           voltage_converter=converter
       )

       miner_tool = MinerCoordinatorTool(
           user_preferences=user_prefs,
           voltage_converter=converter
       )

       # ... rest of crew setup
   ```

**Test:**
```python
prefs = load_user_preferences()
print(f"✅ Loaded {len(prefs)} preference values")
```

---

### Task 3.3: Update Battery Optimizer Tool

**File:** `railway/src/tools/battery_optimizer.py`

**Steps:**
1. Add `__init__` method to class:
   ```python
   def __init__(self, user_preferences: dict = None, voltage_converter=None):
       super().__init__()
       self.user_prefs = user_preferences or self._get_default_prefs()
       self.converter = voltage_converter
   ```

2. Update `_run` method to use user preferences:
   ```python
   def _run(self, telemetry: dict) -> str:
       voltage = telemetry['battery_voltage']

       # Use user thresholds (NOT hardcoded!)
       v_critical = self.user_prefs['voltage_critical_low']
       v_low = self.user_prefs['voltage_low']
       v_optimal_min = self.user_prefs['voltage_optimal_min']
       v_optimal_max = self.user_prefs['voltage_optimal_max']

       # Calculate SOC for display only
       if self.converter:
           soc = self.converter.voltage_to_soc(voltage)
           soc_display = f" ({soc:.1f}% SOC)"
       else:
           soc_display = ""

       # Decision logic using voltage
       if voltage <= v_critical:
           return f"🔴 CRITICAL: Battery at {voltage}V{soc_display} - Stop all loads!"
       elif voltage <= v_low:
           return f"⚠️ LOW: Battery at {voltage}V{soc_display} - Reduce loads"
       elif v_optimal_min <= voltage <= v_optimal_max:
           return f"✅ OPTIMAL: Battery at {voltage}V{soc_display} - Normal operation"
       elif voltage > v_optimal_max:
           return f"⚡ HIGH: Battery at {voltage}V{soc_display} - Can run high loads"
       else:
           return f"⏳ RECOVERING: Battery at {voltage}V{soc_display}"
   ```

3. Add fallback defaults:
   ```python
   def _get_default_prefs(self):
       return {
           'voltage_critical_low': 45.0,
           'voltage_low': 47.0,
           'voltage_optimal_min': 50.0,
           'voltage_optimal_max': 54.5,
           'voltage_restart': 50.0
       }
   ```

**Test:**
```python
tool = BatteryOptimizerTool(prefs, converter)
result = tool._run({'battery_voltage': 52.3, 'solar_power': 8450, 'load_power': 1850})
print(result)
# Expected: "✅ OPTIMAL: Battery at 52.3V (65.5% SOC) - Normal operation"
```

---

### Task 3.4: Update Miner Coordinator Tool

**File:** `railway/src/tools/miner_coordinator.py`

**Steps:**
1. Add imports:
   ```python
   from ..utils.db import get_connection, query_all
   import os

   DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")
   ```

2. Add `__init__` method:
   ```python
   def __init__(self, user_preferences: dict = None, voltage_converter=None):
       super().__init__()
       self.user_prefs = user_preferences or {}
       self.converter = voltage_converter
   ```

3. Add method to load miners from database:
   ```python
   def _load_miners(self) -> list:
       """Load active miners from database."""
       try:
           with get_connection() as conn:
               miners = query_all(
                   conn,
                   """
                   SELECT
                       id, name, model, power_draw_watts, priority_level,
                       start_voltage, stop_voltage, emergency_stop_voltage,
                       require_excess_solar, minimum_excess_watts,
                       minimum_solar_production_watts, enabled
                   FROM miner_profiles
                   WHERE user_id = %s::uuid AND enabled = true
                   ORDER BY priority_level ASC
                   """,
                   (DEFAULT_USER_ID,),
                   as_dict=True
               )
               return list(miners)
       except Exception as e:
           logger.error(f"Failed to load miners: {e}")
           return []
   ```

4. Update `_run` method to use database miners:
   ```python
   def _run(self, telemetry: dict) -> str:
       voltage = telemetry['battery_voltage']
       solar = telemetry['solar_power']
       load = telemetry['load_power']

       miners = self._load_miners()
       if not miners:
           return "No miner profiles configured."

       available_power = solar - load
       power_budget = available_power
       decisions = []

       if self.converter:
           soc = self.converter.voltage_to_soc(voltage)
           soc_display = f" ({soc:.1f}% SOC)"
       else:
           soc_display = ""

       decisions.append(f"Battery: {voltage}V{soc_display}, Solar: {solar}W, Load: {load}W")
       decisions.append(f"Available power budget: {available_power}W\n")

       # Sort by priority (1 = highest)
       sorted_miners = sorted(miners, key=lambda m: m['priority_level'])

       for miner in sorted_miners:
           decision = self._evaluate_miner(miner, voltage, solar, power_budget)
           decisions.append(decision)

           if "START" in decision:
               power_budget -= miner['power_draw_watts']

       return "\n".join(decisions)
   ```

5. Add evaluation method:
   ```python
   def _evaluate_miner(self, miner: dict, voltage: float, solar: float, budget: float) -> str:
       name = miner['name']
       priority = miner['priority_level']
       power = miner['power_draw_watts']

       # Check voltage
       if voltage < miner['start_voltage']:
           return f"❌ [{priority}] {name}: STOP - voltage {voltage}V < {miner['start_voltage']}V"

       # Check power budget
       if budget < power:
           return f"⏸️  [{priority}] {name}: WAIT - insufficient power ({budget}W available, needs {power}W)"

       # Check solar (for dump loads)
       if miner['require_excess_solar']:
           if solar < miner.get('minimum_solar_production_watts', 0):
               return f"☀️  [{priority}] {name}: WAIT - insufficient solar"

           excess = solar - power
           if excess < miner.get('minimum_excess_watts', 0):
               return f"⚡ [{priority}] {name}: WAIT - insufficient excess"

       return f"✅ [{priority}] {name}: START - {power}W allocated (remaining: {budget - power}W)"
   ```

**Test:**
```python
tool = MinerCoordinatorTool(prefs, converter)
result = tool._run({'battery_voltage': 52.3, 'solar_power': 8450, 'load_power': 1850})
print(result)
# Expected: Priority-based allocation with voltage checks
```

---

## ⚠️ Critical Reminders

**DO:**
- ✅ Use voltage for ALL decisions (not SOC%)
- ✅ Load preferences from database
- ✅ Add SOC% for display only
- ✅ Handle database errors gracefully (use defaults)
- ✅ Test each component after implementing

**DON'T:**
- ❌ Make decisions based on SOC%
- ❌ Hardcode voltage thresholds
- ❌ Break if database unavailable
- ❌ Skip error handling

---

## ✅ Success Criteria

After completing all tasks:
- [ ] Energy orchestrator loads preferences from database
- [ ] Battery optimizer uses user voltage thresholds
- [ ] Miner coordinator loads profiles from database
- [ ] Priority-based allocation working (1 = highest)
- [ ] SOC% displayed for user feedback
- [ ] Decisions based on voltage (not SOC%)
- [ ] Graceful fallback if database unavailable
- [ ] All tools tested with sample data

---

## 📝 Session Output

When complete, create:
1. Session log: `docs/sessions/2025-10/session-039-v1.9-agent-integration.md`
2. Update `docs/INDEX.md` with session 039
3. Test report documenting all agent tests
4. Commit message following project style

---

## 🔗 Reference

**Full implementation guide:** PROMPT_V1.9_FIXES_AND_AGENT_INTEGRATION.md (lines 579-842)
**Continuation prompt:** CONTINUE_V1.9.md
**Test report:** V1.9_TEST_REPORT.md

---

**Start with Task 3.2 and work through in order. Test each component before moving to the next!** 🚀
