# V1.9 Critical Fixes + Agent Integration Prompt

**Date:** 2025-10-17
**Phase:** Week 1, Day 5 + Critical Security Fixes
**Prerequisites:** V1.9 API endpoints deployed and working
**Reference:** V1.9_CODE_AUDIT_REPORT.md, SESSION_037_COMPLETION_REPORT.md

---

## 🎯 Mission

Implement critical security fixes and agent integration layer for V1.9 User Preferences System.

**What you're building:**
1. Security hardening (authentication, SQL injection fixes)
2. Performance optimizations (query efficiency)
3. Agent integration (voltage-SOC converter, orchestrator updates)
4. Test coverage (basic test suite)

**Why this matters:**
- Current V1.9 API is functionally complete but has security vulnerabilities
- Agents don't use user preferences yet (still hardcoded thresholds)
- System needs to be production-ready for deployment

---

## 📋 Task Breakdown

### Part 1: Critical Security Fixes (Priority 1) ⚠️

#### Task 1.1: Add API Key Authentication

**Problem:** All API endpoints are completely public.

**Solution:** Implement simple API key authentication middleware.

**Implementation:**
```python
# railway/src/api/middleware/auth.py
from fastapi import Header, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
import os

API_KEY = os.getenv("API_KEY", "")  # Set in Railway environment

class APIKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip auth for health check and docs
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Require X-API-Key header for all other endpoints
        api_key = request.headers.get("X-API-Key")

        if not api_key or api_key != API_KEY:
            raise HTTPException(
                status_code=401,
                detail="Invalid or missing API key"
            )

        return await call_next(request)

# In railway/src/api/main.py
from .middleware.auth import APIKeyMiddleware

app.add_middleware(APIKeyMiddleware)
```

**Environment Setup:**
```bash
# In Railway dashboard, set:
API_KEY=generate-a-long-random-string-here

# For local testing:
echo "API_KEY=dev-key-12345" >> .env
```

**Testing:**
```bash
# Without key (should fail)
curl https://api.wildfireranch.us/api/preferences
# Response: 401 Unauthorized

# With key (should work)
curl -H "X-API-Key: your-key-here" https://api.wildfireranch.us/api/preferences
# Response: 200 OK with preferences
```

**Files to Create:**
- `railway/src/api/middleware/__init__.py`
- `railway/src/api/middleware/auth.py`

**Files to Modify:**
- `railway/src/api/main.py` (add middleware)

---

#### Task 1.2: Fix SQL Injection Vulnerability

**Problem:** UPDATE endpoints build dynamic SQL without field whitelisting.

**Vulnerable Code (preferences.py:222-226):**
```python
for field, value in update_data.items():
    set_clauses.append(f"{field} = %s")  # Field name not validated!
```

**Solution:** Whitelist allowed fields explicitly.

**Implementation:**
```python
# railway/src/api/routes/preferences.py

# Add at top of file
ALLOWED_UPDATE_FIELDS = {
    'voltage_at_0_percent', 'voltage_at_100_percent', 'voltage_curve',
    'battery_chemistry', 'battery_nominal_voltage',
    'battery_absolute_min', 'battery_absolute_max',
    'voltage_shutdown', 'voltage_critical_low', 'voltage_low',
    'voltage_restart', 'voltage_optimal_min', 'voltage_optimal_max',
    'voltage_float', 'voltage_absorption', 'voltage_full',
    'user_prefers_soc_display', 'use_custom_soc_mapping', 'display_units',
    'timezone', 'location_lat', 'location_lon',
    'operating_mode', 'grid_import_allowed'
}

@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(updates: UserPreferencesUpdate):
    try:
        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(400, detail="No fields to update")

        # WHITELIST VALIDATION (NEW)
        for field in update_data.keys():
            if field not in ALLOWED_UPDATE_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' is not allowed for updates"
                )

        # Now safe to build query
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        # ... rest of update logic
```

**Apply to all three files:**
- `railway/src/api/routes/preferences.py` (ALLOWED_UPDATE_FIELDS)
- `railway/src/api/routes/miners.py` (ALLOWED_MINER_FIELDS)
- `railway/src/api/routes/hvac.py` (ALLOWED_HVAC_FIELDS)

**Testing:**
```bash
# Try to inject invalid field
curl -X PUT https://api.wildfireranch.us/api/preferences \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"invalid_field": "value"}'
# Expected: 400 Bad Request - field not allowed
```

---

#### Task 1.3: Remove Debug Endpoints

**Problem:** Debug endpoints expose internal system state.

**Solution:** Remove or move to protected internal router.

**Implementation:**
```python
# Option A: Remove completely
# Delete these endpoints from preferences.py:
# - /debug-version (lines 34-45)
# - /debug-pydantic (lines 48-93)
# - /debug-raw (lines 96-118)

# Option B: Move to internal router (better for troubleshooting)
# railway/src/api/routes/internal.py
from fastapi import APIRouter, Depends
from ...middleware.auth import verify_internal_access

router = APIRouter(prefix="/internal", tags=["internal"])

@router.get("/debug/preferences-version", dependencies=[Depends(verify_internal_access)])
async def debug_model_version():
    # Move debug endpoint here
    pass
```

**Choose Option A** for simplicity. Remove the debug endpoints entirely.

---

#### Task 1.4: Secure Default User ID

**Problem:** Hardcoded UUID is well-known.

**Solution:** Move to environment variable.

**Implementation:**
```python
# railway/src/api/routes/preferences.py
import os

# OLD:
# DEFAULT_USER_ID = "a0000000-0000-0000-0000-000000000001"

# NEW:
DEFAULT_USER_ID = os.getenv(
    "DEFAULT_USER_ID",
    "a0000000-0000-0000-0000-000000000001"  # Fallback for local dev
)

# Apply to all three route files
```

**Environment Setup:**
```bash
# In Railway dashboard, set a new random UUID:
DEFAULT_USER_ID=8f7e6d5c-4b3a-2190-8765-fedcba098765
```

**Migration Update:**
```sql
-- Update migration to use env var or generate random UUID
INSERT INTO users (id, email, password_hash, role)
VALUES (
    gen_random_uuid(),  -- Generate instead of hardcode
    'admin@wildfireranch.us',
    crypt('CHANGE_ME_IN_PRODUCTION', gen_salt('bf')),
    'admin'
)
ON CONFLICT (id) DO NOTHING;
```

---

### Part 2: Performance Optimizations (Priority 2) ⚡

#### Task 2.1: Fix N+1 Query Problem in UPDATE Endpoints

**Problem:** UPDATE operations use 2 database queries (UPDATE + SELECT).

**Current Code (preferences.py:234-268):**
```python
# Step 1: UPDATE
execute(conn, "UPDATE user_preferences SET ...")

# Step 2: SELECT (separate query!)
updated_prefs = query_one(conn, "SELECT * FROM user_preferences WHERE ...")
```

**Optimized Solution:** Use PostgreSQL RETURNING clause.

**Implementation:**
```python
@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(updates: UserPreferencesUpdate):
    try:
        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(400, detail="No fields to update")

        # Validate fields
        for field in update_data.keys():
            if field not in ALLOWED_UPDATE_FIELDS:
                raise HTTPException(400, f"Field '{field}' not allowed")

        # Build SET clause
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        set_clauses.append("updated_at = NOW()")
        values.append(DEFAULT_USER_ID)

        with get_connection() as conn:
            # Single query with RETURNING (NEW!)
            updated_prefs = query_one(
                conn,
                f"""
                UPDATE user_preferences
                SET {', '.join(set_clauses)}
                WHERE user_id = %s::uuid
                RETURNING
                    id, user_id,
                    voltage_at_0_percent, voltage_at_100_percent, voltage_curve,
                    battery_chemistry, battery_nominal_voltage,
                    battery_absolute_min, battery_absolute_max,
                    voltage_shutdown, voltage_critical_low, voltage_low,
                    voltage_restart, voltage_optimal_min, voltage_optimal_max,
                    voltage_float, voltage_absorption, voltage_full,
                    user_prefers_soc_display, use_custom_soc_mapping, display_units,
                    timezone, location_lat, location_lon,
                    operating_mode, grid_import_allowed,
                    created_at, updated_at
                """,
                tuple(values),
                as_dict=True
            )

            if not updated_prefs:
                raise HTTPException(404, detail="Preferences not found")

            logger.info(f"Updated preferences: {list(update_data.keys())}")
            return updated_prefs
```

**Apply to:**
- `preferences.py` (update_preferences endpoint)
- `miners.py` (update_miner endpoint)
- `hvac.py` (update_zone endpoint)

**Performance Gain:** ~50% faster UPDATE operations

---

#### Task 2.2: Add Field Whitelists as Constants

**Create shared constants file:**
```python
# railway/src/api/routes/constants.py

# User Preferences allowed fields
ALLOWED_PREFERENCE_FIELDS = {
    'voltage_at_0_percent', 'voltage_at_100_percent', 'voltage_curve',
    'battery_chemistry', 'battery_nominal_voltage',
    'battery_absolute_min', 'battery_absolute_max',
    'voltage_shutdown', 'voltage_critical_low', 'voltage_low',
    'voltage_restart', 'voltage_optimal_min', 'voltage_optimal_max',
    'voltage_float', 'voltage_absorption', 'voltage_full',
    'user_prefers_soc_display', 'use_custom_soc_mapping', 'display_units',
    'timezone', 'location_lat', 'location_lon',
    'operating_mode', 'grid_import_allowed'
}

# Miner Profile allowed fields
ALLOWED_MINER_FIELDS = {
    'name', 'model', 'hashrate_ths', 'power_draw_watts',
    'priority_level', 'operating_mode',
    'start_voltage', 'stop_voltage', 'emergency_stop_voltage',
    'start_hysteresis_minutes', 'stop_hysteresis_minutes',
    'require_excess_solar', 'minimum_excess_watts', 'maximum_runtime_hours',
    'prefer_time_start', 'prefer_time_end', 'allow_outside_schedule',
    'require_sunny_weather', 'minimum_solar_production_watts',
    'enabled', 'control_method', 'device_identifier'
}

# HVAC Zone allowed fields
ALLOWED_HVAC_FIELDS = {
    'zone_name', 'zone_type',
    'temp_too_hot', 'temp_hot_ok', 'temp_too_cold', 'temp_cold_ok',
    'exhaust_fan_enabled', 'exhaust_fan_device_id',
    'exhaust_fan_speed_auto', 'exhaust_fan_max_speed',
    'heating_enabled', 'heating_priority_1', 'heating_priority_2', 'heater_device_id',
    'only_heat_when_solar', 'minimum_solar_for_heating_watts',
    'block_charging_below_temp',
    'enabled', 'temperature_sensor_id'
}
```

---

### Part 3: Agent Integration (Priority 3) 🤖

#### Task 3.1: Create Voltage-SOC Converter Service

**Purpose:** Convert between battery voltage and SOC% using user preferences.

**Implementation:**
```python
# railway/src/services/voltage_soc_converter.py

from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class VoltageSocConverter:
    """
    Bidirectional voltage <-> SOC% conversion using user calibration.

    WHAT: Converts battery voltage to SOC% and vice versa
    WHY: Agents make decisions on voltage, but users want to see SOC%
    HOW: Linear interpolation or custom curve-based interpolation

    Usage:
        converter = VoltageSocConverter(user_preferences)
        soc = converter.voltage_to_soc(52.3)  # Returns: 65.5
        voltage = converter.soc_to_voltage(50.0)  # Returns: 50.5
    """

    def __init__(self, preferences: Dict[str, Any]):
        """
        Initialize converter with user preferences.

        Args:
            preferences: User preferences dict from database
                - voltage_at_0_percent: Minimum voltage (e.g., 45.0V)
                - voltage_at_100_percent: Maximum voltage (e.g., 56.0V)
                - voltage_curve: Optional list of calibration points
        """
        self.v_min = float(preferences['voltage_at_0_percent'])
        self.v_max = float(preferences['voltage_at_100_percent'])
        self.curve = preferences.get('voltage_curve')

        logger.debug(f"Initialized converter: {self.v_min}V-{self.v_max}V")

    def voltage_to_soc(self, voltage: float) -> float:
        """
        Convert voltage to SOC percentage.

        Args:
            voltage: Battery voltage in volts

        Returns:
            SOC percentage (0-100)

        Example:
            >>> converter.voltage_to_soc(52.3)
            65.5
        """
        # Clamp to valid range
        if voltage <= self.v_min:
            return 0.0
        if voltage >= self.v_max:
            return 100.0

        # Use custom curve if available
        if self.curve and isinstance(self.curve, list) and len(self.curve) > 0:
            return self._interpolate_from_curve(voltage, self.curve)

        # Linear interpolation (fallback)
        return 100.0 * (voltage - self.v_min) / (self.v_max - self.v_min)

    def soc_to_voltage(self, soc: float) -> float:
        """
        Convert SOC percentage to voltage.

        Args:
            soc: State of charge percentage (0-100)

        Returns:
            Battery voltage in volts

        Example:
            >>> converter.soc_to_voltage(50.0)
            50.5
        """
        # Clamp to valid range
        if soc <= 0:
            return self.v_min
        if soc >= 100:
            return self.v_max

        # Use custom curve if available
        if self.curve and isinstance(self.curve, list) and len(self.curve) > 0:
            return self._reverse_interpolate_from_curve(soc, self.curve)

        # Linear interpolation (fallback)
        return self.v_min + (soc / 100.0) * (self.v_max - self.v_min)

    def _interpolate_from_curve(self, voltage: float, curve: List[Dict]) -> float:
        """
        Interpolate SOC from voltage using calibration curve.

        Curve format: [{"soc": 0, "voltage": 45.0}, {"soc": 15, "voltage": 47.0}, ...]
        """
        # Sort curve by voltage
        sorted_curve = sorted(curve, key=lambda x: x['voltage'])

        # Find bracketing points
        for i in range(len(sorted_curve) - 1):
            v1, soc1 = sorted_curve[i]['voltage'], sorted_curve[i]['soc']
            v2, soc2 = sorted_curve[i + 1]['voltage'], sorted_curve[i + 1]['soc']

            if v1 <= voltage <= v2:
                # Linear interpolation between points
                ratio = (voltage - v1) / (v2 - v1)
                return soc1 + ratio * (soc2 - soc1)

        # Shouldn't reach here due to clamping, but fallback to linear
        return self.voltage_to_soc(voltage)

    def _reverse_interpolate_from_curve(self, soc: float, curve: List[Dict]) -> float:
        """
        Interpolate voltage from SOC using calibration curve.
        """
        # Sort curve by SOC
        sorted_curve = sorted(curve, key=lambda x: x['soc'])

        # Find bracketing points
        for i in range(len(sorted_curve) - 1):
            soc1, v1 = sorted_curve[i]['soc'], sorted_curve[i]['voltage']
            soc2, v2 = sorted_curve[i + 1]['soc'], sorted_curve[i + 1]['voltage']

            if soc1 <= soc <= soc2:
                # Linear interpolation between points
                ratio = (soc - soc1) / (soc2 - soc1)
                return v1 + ratio * (v2 - v1)

        # Fallback to linear
        return self.soc_to_voltage(soc)


def get_converter(preferences: Dict[str, Any]) -> VoltageSocConverter:
    """
    Factory function to create converter from preferences.

    Usage:
        prefs = get_user_preferences()
        converter = get_converter(prefs)
        soc = converter.voltage_to_soc(52.3)
    """
    return VoltageSocConverter(preferences)
```

**Test the converter:**
```python
# railway/tests/test_voltage_soc_converter.py
import pytest
from src.services.voltage_soc_converter import VoltageSocConverter

def test_linear_conversion():
    prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
        'voltage_curve': None
    }
    converter = VoltageSocConverter(prefs)

    # Test endpoints
    assert converter.voltage_to_soc(45.0) == 0.0
    assert converter.voltage_to_soc(56.0) == 100.0

    # Test midpoint (50.5V should be ~50%)
    soc = converter.voltage_to_soc(50.5)
    assert 49.0 <= soc <= 51.0  # Within 1% tolerance

    # Test reverse conversion
    voltage = converter.soc_to_voltage(50.0)
    assert 50.0 <= voltage <= 51.0

def test_curve_conversion():
    prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
        'voltage_curve': [
            {'soc': 0, 'voltage': 45.0},
            {'soc': 15, 'voltage': 47.0},
            {'soc': 40, 'voltage': 50.0},
            {'soc': 60, 'voltage': 52.0},
            {'soc': 80, 'voltage': 54.5},
            {'soc': 100, 'voltage': 56.0}
        ]
    }
    converter = VoltageSocConverter(prefs)

    # Test exact curve points
    assert converter.voltage_to_soc(47.0) == 15.0
    assert converter.voltage_to_soc(50.0) == 40.0

    # Test interpolation between points
    soc = converter.voltage_to_soc(51.0)  # Between 50.0V (40%) and 52.0V (60%)
    assert 48.0 <= soc <= 52.0
```

---

#### Task 3.2: Update Energy Orchestrator to Load Preferences

**File:** `railway/src/agents/energy_orchestrator.py`

**Add preferences loading:**
```python
# At top of file
from ..services.voltage_soc_converter import get_converter
from ..utils.db import get_connection, query_one

# Default user ID
DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")

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
        # Return safe defaults if DB fails
        return {
            'voltage_at_0_percent': 45.0,
            'voltage_at_100_percent': 56.0,
            'voltage_optimal_min': 50.0,
            'voltage_optimal_max': 54.5,
            'voltage_low': 47.0,
            'voltage_critical_low': 45.0,
            'operating_mode': 'balanced'
        }

# In create_energy_orchestrator_crew():
def create_energy_orchestrator_crew():
    """Create Energy Orchestrator crew with user preferences."""

    # Load preferences at crew creation
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

---

#### Task 3.3: Update Battery Optimizer Tool

**File:** `railway/src/tools/battery_optimizer.py`

**Add preferences support:**
```python
class BatteryOptimizerTool(BaseTool):
    name = "Battery Optimizer"
    description = "Analyzes battery state and recommends actions"

    def __init__(self, user_preferences: dict = None, voltage_converter=None):
        super().__init__()
        self.user_prefs = user_preferences or self._get_default_prefs()
        self.converter = voltage_converter

    def _run(self, telemetry: dict) -> str:
        """
        Analyze battery state using user-configured voltage thresholds.

        Args:
            telemetry: {
                'battery_voltage': 52.3,
                'battery_soc': 65.5,  # For display only
                'solar_power': 8450,
                'load_power': 1850
            }
        """
        voltage = telemetry['battery_voltage']

        # Use user-configured thresholds (NOT hardcoded!)
        v_critical = self.user_prefs['voltage_critical_low']
        v_low = self.user_prefs['voltage_low']
        v_optimal_min = self.user_prefs['voltage_optimal_min']
        v_optimal_max = self.user_prefs['voltage_optimal_max']

        # Calculate SOC for display
        if self.converter:
            soc = self.converter.voltage_to_soc(voltage)
            soc_display = f" ({soc:.1f}% SOC)"
        else:
            soc_display = ""

        # Decision logic using voltage thresholds
        if voltage <= v_critical:
            return f"🔴 CRITICAL: Battery at {voltage}V{soc_display} - Stop all loads immediately!"

        elif voltage <= v_low:
            return f"⚠️ LOW: Battery at {voltage}V{soc_display} - Reduce loads, prioritize charging"

        elif v_optimal_min <= voltage <= v_optimal_max:
            return f"✅ OPTIMAL: Battery at {voltage}V{soc_display} - Normal operation"

        elif voltage > v_optimal_max:
            return f"⚡ HIGH: Battery at {voltage}V{soc_display} - Can run high loads"

        else:
            return f"⏳ RECOVERING: Battery at {voltage}V{soc_display} - Wait for {self.user_prefs['voltage_restart']}V to restart"

    def _get_default_prefs(self):
        """Fallback defaults if preferences not loaded."""
        return {
            'voltage_critical_low': 45.0,
            'voltage_low': 47.0,
            'voltage_optimal_min': 50.0,
            'voltage_optimal_max': 54.5,
            'voltage_restart': 50.0
        }
```

---

#### Task 3.4: Update Miner Coordinator Tool

**File:** `railway/src/tools/miner_coordinator.py`

**Add multi-miner priority support:**
```python
from ..utils.db import get_connection, query_all
import os

DEFAULT_USER_ID = os.getenv("DEFAULT_USER_ID", "a0000000-0000-0000-0000-000000000001")

class MinerCoordinatorTool(BaseTool):
    name = "Miner Coordinator"
    description = "Manages multiple miners with priority-based allocation"

    def __init__(self, user_preferences: dict = None, voltage_converter=None):
        super().__init__()
        self.user_prefs = user_preferences or {}
        self.converter = voltage_converter

    def _run(self, telemetry: dict) -> str:
        """
        Coordinate multiple miners based on priority and constraints.

        Args:
            telemetry: {
                'battery_voltage': 52.3,
                'solar_power': 8450,
                'load_power': 1850
            }
        """
        voltage = telemetry['battery_voltage']
        solar = telemetry['solar_power']
        load = telemetry['load_power']

        # Load all active miners from database
        miners = self._load_miners()

        if not miners:
            return "No miner profiles configured."

        # Calculate available power budget
        available_power = solar - load
        power_budget = available_power

        decisions = []
        soc_display = ""

        if self.converter:
            soc = self.converter.voltage_to_soc(voltage)
            soc_display = f" ({soc:.1f}% SOC)"

        decisions.append(f"Battery: {voltage}V{soc_display}, Solar: {solar}W, Load: {load}W")
        decisions.append(f"Available power budget: {available_power}W\n")

        # Sort miners by priority (1 = highest)
        sorted_miners = sorted(miners, key=lambda m: m['priority_level'])

        for miner in sorted_miners:
            decision = self._evaluate_miner(miner, voltage, solar, power_budget)
            decisions.append(decision)

            # If miner can start, deduct from budget
            if "START" in decision:
                power_budget -= miner['power_draw_watts']

        return "\n".join(decisions)

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

    def _evaluate_miner(self, miner: dict, voltage: float, solar: float, budget: float) -> str:
        """
        Evaluate if a miner should start based on all constraints.

        Returns decision string.
        """
        name = miner['name']
        priority = miner['priority_level']
        power = miner['power_draw_watts']

        # Check voltage threshold
        if voltage < miner['start_voltage']:
            return f"❌ [{priority}] {name}: STOP - voltage {voltage}V < {miner['start_voltage']}V (start threshold)"

        # Check power budget
        if budget < power:
            return f"⏸️  [{priority}] {name}: WAIT - insufficient power ({budget}W available, needs {power}W)"

        # Check solar requirement (for dump loads)
        if miner['require_excess_solar']:
            if solar < miner.get('minimum_solar_production_watts', 0):
                return f"☀️  [{priority}] {name}: WAIT - insufficient solar ({solar}W, needs {miner['minimum_solar_production_watts']}W)"

            excess = solar - power
            if excess < miner.get('minimum_excess_watts', 0):
                return f"⚡ [{priority}] {name}: WAIT - insufficient excess ({excess}W, needs {miner['minimum_excess_watts']}W)"

        # All checks passed!
        return f"✅ [{priority}] {name}: START - {power}W allocated (budget remaining: {budget - power}W)"
```

---

### Part 4: Testing (Priority 4) 🧪

#### Task 4.1: Create Basic Test Suite

**Create test structure:**
```bash
railway/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_voltage_soc_converter.py
│   ├── test_api_auth.py
│   ├── test_api_preferences.py
│   ├── test_api_miners.py
│   └── test_api_hvac.py
```

**Setup pytest:**
```python
# railway/tests/conftest.py
import pytest
from fastapi.testclient import TestClient
import os

# Set test environment
os.environ['API_KEY'] = 'test-key-12345'
os.environ['DEFAULT_USER_ID'] = 'a0000000-0000-0000-0000-000000000001'

from src.api.main import app

@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Headers with API key."""
    return {'X-API-Key': 'test-key-12345'}
```

**Test API authentication:**
```python
# railway/tests/test_api_auth.py
def test_requires_api_key(client):
    """Test that endpoints require API key."""
    response = client.get("/api/preferences")
    assert response.status_code == 401
    assert "Invalid or missing API key" in response.json()['detail']

def test_accepts_valid_api_key(client, auth_headers):
    """Test that valid API key is accepted."""
    response = client.get("/api/preferences", headers=auth_headers)
    assert response.status_code != 401  # May be 200 or 404 depending on data

def test_health_check_no_auth(client):
    """Health check should not require auth."""
    response = client.get("/health")
    assert response.status_code == 200
```

**Test preferences API:**
```python
# railway/tests/test_api_preferences.py
def test_get_preferences(client, auth_headers):
    """Test GET /api/preferences."""
    response = client.get("/api/preferences", headers=auth_headers)
    assert response.status_code in [200, 404]

    if response.status_code == 200:
        data = response.json()
        assert 'voltage_at_0_percent' in data
        assert 'voltage_at_100_percent' in data

def test_update_preferences_rejects_invalid_field(client, auth_headers):
    """Test that invalid fields are rejected."""
    response = client.put(
        "/api/preferences",
        headers=auth_headers,
        json={"invalid_field": "value"}
    )
    assert response.status_code == 400
    assert "not allowed" in response.json()['detail'].lower()

def test_update_preferences_validates_voltage_ranges(client, auth_headers):
    """Test that database constraints are enforced."""
    response = client.put(
        "/api/preferences",
        headers=auth_headers,
        json={
            "voltage_optimal_min": 55.0,
            "voltage_optimal_max": 50.0  # Invalid: min > max
        }
    )
    # Should fail at database constraint
    assert response.status_code in [400, 500]
```

**Run tests:**
```bash
cd railway
pip install pytest pytest-asyncio
pytest tests/ -v
```

---

### Part 5: Documentation Updates (Priority 5) 📝

#### Task 5.1: Fix API Path Documentation

**Update these files:**

1. **V1.9_TECHNICAL_SPECIFICATION.md:**
```markdown
# OLD (Line 171):
GET    /api/users/preferences       Get user preferences

# NEW:
GET    /api/preferences       Get user preferences
PUT    /api/preferences       Update preferences
POST   /api/preferences/reset Reset to defaults
```

2. **V1.9_quick_reference.md:**
```markdown
# Add authentication section
## 🔐 Authentication

All API endpoints require authentication (except /health and /docs).

**Header:**
```
X-API-Key: your-api-key-here
```

**Example:**
```bash
curl -H "X-API-Key: your-key" https://api.wildfireranch.us/api/preferences
```

**Setup:**
Set API_KEY environment variable in Railway dashboard.
```

---

#### Task 5.2: Create Agent Integration Guide

**Create new file:**
```markdown
# docs/versions/v1.9/V1.9_AGENT_INTEGRATION.md

# V1.9 Agent Integration Guide

## Overview

This guide explains how agents load and use user preferences.

## Architecture

```
User Query
    ↓
Energy Orchestrator
    ├─ Load preferences (database)
    ├─ Create voltage converter
    └─ Pass to tools
        ├─ Battery Optimizer (uses voltage thresholds)
        ├─ Miner Coordinator (uses priorities)
        └─ HVAC Controller (uses temp thresholds)
```

## Usage Example

```python
# 1. Load preferences
prefs = load_user_preferences()

# 2. Create converter
from services.voltage_soc_converter import get_converter
converter = get_converter(prefs)

# 3. Convert voltage to SOC for display
soc = converter.voltage_to_soc(52.3)  # Returns: 65.5

# 4. Make decisions on voltage
if voltage >= prefs['voltage_optimal_min']:
    print("Battery OK to run loads")
```

## Testing

Run agent integration tests:
```bash
pytest tests/test_agents/ -v
```
```

---

## 📊 Implementation Checklist

### Critical Security (Do First)
- [ ] Task 1.1: Add API key authentication middleware
- [ ] Task 1.2: Add field whitelisting to UPDATE endpoints
- [ ] Task 1.3: Remove debug endpoints
- [ ] Task 1.4: Move DEFAULT_USER_ID to environment variable

### Performance Optimizations
- [ ] Task 2.1: Fix N+1 queries with RETURNING clause (preferences)
- [ ] Task 2.1: Fix N+1 queries with RETURNING clause (miners)
- [ ] Task 2.1: Fix N+1 queries with RETURNING clause (hvac)
- [ ] Task 2.2: Create constants.py with field whitelists

### Agent Integration
- [ ] Task 3.1: Create voltage_soc_converter.py service
- [ ] Task 3.2: Update energy_orchestrator.py to load preferences
- [ ] Task 3.3: Update battery_optimizer.py to use voltage thresholds
- [ ] Task 3.4: Update miner_coordinator.py with priority support

### Testing
- [ ] Task 4.1: Set up pytest structure
- [ ] Task 4.1: Write authentication tests
- [ ] Task 4.1: Write preferences API tests
- [ ] Task 4.1: Write voltage converter tests

### Documentation
- [ ] Task 5.1: Fix API path documentation
- [ ] Task 5.2: Create agent integration guide
- [ ] Update README with authentication setup

---

## 🚀 Deployment Steps

### 1. Local Testing
```bash
# Run all tests
pytest railway/tests/ -v

# Test manually
curl -H "X-API-Key: test-key-12345" http://localhost:8000/api/preferences
```

### 2. Railway Deployment
```bash
# Set environment variables in Railway dashboard:
# - API_KEY=<generate-random-string>
# - DEFAULT_USER_ID=<existing-uuid-from-database>

# Commit and push
git add .
git commit -m "Add V1.9 security fixes and agent integration"
git push origin main

# Wait for Railway auto-deploy (90 seconds)
```

### 3. Production Verification
```bash
# Test authentication
curl https://api.wildfireranch.us/api/preferences
# Expected: 401 Unauthorized

curl -H "X-API-Key: your-railway-key" https://api.wildfireranch.us/api/preferences
# Expected: 200 OK with preferences

# Test agent integration
# Query the agent: "Should I start mining?"
# Agent should respond with voltage-based decision using user preferences
```

---

## 🎯 Success Criteria

### Security Fixed ✅
- [ ] All endpoints require authentication
- [ ] SQL injection vulnerability patched
- [ ] Debug endpoints removed
- [ ] Environment variables used for secrets

### Performance Improved ⚡
- [ ] UPDATE operations use single query (RETURNING)
- [ ] Field whitelisting prevents invalid updates
- [ ] No performance regression in tests

### Agents Integrated 🤖
- [ ] Voltage-SOC converter working (±2% accuracy)
- [ ] Energy Orchestrator loads preferences
- [ ] Battery Optimizer uses user voltage thresholds
- [ ] Miner Coordinator respects priority levels
- [ ] Agent responses include SOC% display

### Tests Passing 🧪
- [ ] All pytest tests green
- [ ] Manual testing confirms functionality
- [ ] No regressions in existing features

### Documented 📝
- [ ] API docs updated with auth requirements
- [ ] Agent integration guide created
- [ ] README updated with setup instructions

---

## 📞 Quick Reference

**Audit Report:** V1.9_CODE_AUDIT_REPORT.md
**Session History:** SESSION_037_COMPLETION_REPORT.md
**Architecture:** V1.9_ARCHITECTURE_SUMMARY.md
**API Docs:** https://api.wildfireranch.us/docs

**Need Help?**
- Check audit report for detailed issue descriptions
- See code examples above for implementation patterns
- Run tests to validate changes: `pytest railway/tests/ -v`

---

**Estimated Time:** 4-6 hours
**Priority:** HIGH (Security issues must be fixed before production)
**Next Step After This:** Frontend UI (Week 2)

Good luck! 🚀
