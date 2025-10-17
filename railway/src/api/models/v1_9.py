# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/models/v1_9.py
# PURPOSE: Pydantic models for V1.9 User Preferences System
#
# WHAT IT DOES:
#   - Defines request/response models for preferences, miners, and HVAC zones
#   - Provides validation for voltage thresholds, priorities, temperatures
#   - Supports both create and update operations
#
# USED BY:
#   - railway/src/api/routes/preferences.py
#   - railway/src/api/routes/miners.py
#   - railway/src/api/routes/hvac.py
# ═══════════════════════════════════════════════════════════════════════════

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from pydantic import BaseModel, Field, validator, ConfigDict


# ─────────────────────────────────────────────────────────────────────────────
# User Preferences Models
# ─────────────────────────────────────────────────────────────────────────────

class UserPreferencesBase(BaseModel):
    """Base model for user preferences (voltage-based battery management)."""

    # Battery Calibration
    voltage_at_0_percent: float = Field(
        default=45.0,
        ge=40.0,
        le=50.0,
        description="Battery voltage at 0% SOC (e.g., 45.0V for Solar Shack)"
    )
    voltage_at_100_percent: float = Field(
        default=56.0,
        ge=50.0,
        le=60.0,
        description="Battery voltage at 100% SOC (e.g., 56.0V for Solar Shack)"
    )
    voltage_curve: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional non-linear voltage-SOC calibration curve (6-point)"
    )

    # Battery Specs
    battery_chemistry: str = Field(
        default="LiFePO4",
        description="Battery chemistry (LiFePO4, Li-ion, Lead-acid, etc.)"
    )
    battery_nominal_voltage: float = Field(
        default=51.2,
        description="Nominal battery voltage (e.g., 51.2V for 16S LiFePO4)"
    )
    battery_absolute_min: float = Field(
        default=43.0,
        description="Absolute minimum voltage (damage threshold)"
    )
    battery_absolute_max: float = Field(
        default=58.8,
        description="Absolute maximum voltage (damage threshold)"
    )

    # Operating Thresholds (VOLTAGE)
    voltage_shutdown: float = Field(
        default=44.0,
        description="Emergency shutdown voltage (stop all loads)"
    )
    voltage_critical_low: float = Field(
        default=45.0,
        description="Critical low voltage (0% SOC)"
    )
    voltage_low: float = Field(
        default=47.0,
        description="Low voltage warning (15% SOC)"
    )
    voltage_restart: float = Field(
        default=50.0,
        description="Restart voltage after low battery (40% SOC)"
    )
    voltage_optimal_min: float = Field(
        default=50.0,
        description="Optimal range minimum (40% SOC)"
    )
    voltage_optimal_max: float = Field(
        default=54.5,
        description="Optimal range maximum (80% SOC)"
    )
    voltage_float: float = Field(
        default=54.0,
        description="Float charging voltage"
    )
    voltage_absorption: float = Field(
        default=57.6,
        description="Absorption charging voltage"
    )
    voltage_full: float = Field(
        default=56.0,
        description="Battery full voltage (100% SOC)"
    )

    # Display Preferences
    user_prefers_soc_display: bool = Field(
        default=True,
        description="Show SOC% instead of voltage in UI"
    )
    use_custom_soc_mapping: bool = Field(
        default=True,
        description="Use custom voltage curve for SOC calculation"
    )
    display_units: str = Field(
        default="metric",
        description="Display units (metric or imperial)"
    )

    # System Settings
    timezone: str = Field(
        default="America/Los_Angeles",
        description="User timezone (e.g., America/Los_Angeles)"
    )
    location_lat: Optional[float] = Field(
        default=None,
        description="Latitude for solar calculations"
    )
    location_lon: Optional[float] = Field(
        default=None,
        description="Longitude for solar calculations"
    )
    operating_mode: str = Field(
        default="balanced",
        description="Operating mode (aggressive, balanced, conservative)"
    )
    grid_import_allowed: bool = Field(
        default=False,
        description="Allow grid import when needed"
    )

    @validator('voltage_at_100_percent')
    def validate_voltage_range(cls, v, values):
        """Ensure voltage_at_100_percent > voltage_at_0_percent."""
        if 'voltage_at_0_percent' in values:
            if v <= values['voltage_at_0_percent']:
                raise ValueError('voltage_at_100_percent must be > voltage_at_0_percent')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "voltage_at_0_percent": 45.0,
                "voltage_at_100_percent": 56.0,
                "voltage_optimal_min": 50.0,
                "voltage_optimal_max": 54.5,
                "timezone": "America/Los_Angeles",
                "operating_mode": "balanced"
            }
        }
    )


class UserPreferencesResponse(UserPreferencesBase):
    """Response model with additional fields."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPreferencesUpdate(BaseModel):
    """Update model (all fields optional)."""
    voltage_at_0_percent: Optional[float] = None
    voltage_at_100_percent: Optional[float] = None
    voltage_curve: Optional[Dict[str, Any]] = None
    battery_chemistry: Optional[str] = None
    battery_nominal_voltage: Optional[float] = None
    battery_absolute_min: Optional[float] = None
    battery_absolute_max: Optional[float] = None
    voltage_shutdown: Optional[float] = None
    voltage_critical_low: Optional[float] = None
    voltage_low: Optional[float] = None
    voltage_restart: Optional[float] = None
    voltage_optimal_min: Optional[float] = None
    voltage_optimal_max: Optional[float] = None
    voltage_float: Optional[float] = None
    voltage_absorption: Optional[float] = None
    voltage_full: Optional[float] = None
    user_prefers_soc_display: Optional[bool] = None
    use_custom_soc_mapping: Optional[bool] = None
    display_units: Optional[str] = None
    timezone: Optional[str] = None
    location_lat: Optional[float] = None
    location_lon: Optional[float] = None
    operating_mode: Optional[str] = None
    grid_import_allowed: Optional[bool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Miner Profile Models
# ─────────────────────────────────────────────────────────────────────────────

class MinerProfileBase(BaseModel):
    """Base model for miner profiles (priority-based power allocation)."""

    # Identity
    name: str = Field(description="Miner name (e.g., 'Primary S21+ (Revenue)')")
    model: Optional[str] = Field(default=None, description="Miner model (e.g., 'Antminer S21+ 235TH')")
    hashrate_ths: Optional[float] = Field(default=None, description="Hashrate in TH/s")
    power_draw_watts: int = Field(description="Power consumption in watts")

    # Priority & Strategy
    priority_level: int = Field(
        ge=1,
        le=10,
        description="Priority level (1=highest, 10=lowest)"
    )
    operating_mode: str = Field(
        default="balanced",
        description="Operating mode (aggressive, balanced, opportunistic)"
    )

    # Voltage Thresholds
    start_voltage: float = Field(description="Voltage to start miner (e.g., 50.0V = 40% SOC)")
    stop_voltage: float = Field(description="Voltage to stop miner (e.g., 47.0V = 15% SOC)")
    emergency_stop_voltage: float = Field(description="Emergency stop voltage (e.g., 45.0V = 0% SOC)")
    start_hysteresis_minutes: int = Field(default=5, description="Wait time before starting (minutes)")
    stop_hysteresis_minutes: int = Field(default=2, description="Wait time before stopping (minutes)")

    # Constraints
    require_excess_solar: bool = Field(
        default=False,
        description="Require excess solar production (dump load mode)"
    )
    minimum_excess_watts: Optional[int] = Field(
        default=None,
        description="Minimum excess watts required (for dump loads)"
    )
    maximum_runtime_hours: Optional[int] = Field(
        default=None,
        description="Maximum continuous runtime (hours)"
    )

    # Scheduling
    prefer_time_start: Optional[int] = Field(
        default=None,
        ge=0,
        le=23,
        description="Preferred start hour (0-23, e.g., 18 for 6pm)"
    )
    prefer_time_end: Optional[int] = Field(
        default=None,
        ge=0,
        le=23,
        description="Preferred end hour (0-23, e.g., 10 for 10am)"
    )
    allow_outside_schedule: bool = Field(
        default=True,
        description="Allow operation outside preferred schedule"
    )

    # Weather (V2)
    require_sunny_weather: bool = Field(default=False, description="Require sunny weather")
    minimum_solar_production_watts: Optional[int] = Field(
        default=None,
        description="Minimum solar production required (watts)"
    )

    # Status
    enabled: bool = Field(default=True, description="Miner enabled/disabled")
    control_method: Optional[str] = Field(
        default=None,
        description="Control method (smartload, shelly, manual, etc.)"
    )
    device_identifier: Optional[str] = Field(
        default=None,
        description="Device ID for control (e.g., Shelly IP address)"
    )

    @validator('stop_voltage')
    def validate_stop_voltage(cls, v, values):
        """Ensure stop_voltage < start_voltage."""
        if 'start_voltage' in values:
            if v >= values['start_voltage']:
                raise ValueError('stop_voltage must be < start_voltage')
        return v

    @validator('emergency_stop_voltage')
    def validate_emergency_stop_voltage(cls, v, values):
        """Ensure emergency_stop_voltage < stop_voltage."""
        if 'stop_voltage' in values:
            if v >= values['stop_voltage']:
                raise ValueError('emergency_stop_voltage must be < stop_voltage')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "Primary S21+ (Revenue)",
                "model": "Antminer S21+ 235TH",
                "hashrate_ths": 235.0,
                "power_draw_watts": 3878,
                "priority_level": 1,
                "operating_mode": "aggressive",
                "start_voltage": 50.0,
                "stop_voltage": 47.0,
                "emergency_stop_voltage": 45.0,
                "require_excess_solar": False,
                "enabled": True
            }
        }
    )


class MinerProfileResponse(MinerProfileBase):
    """Response model with additional fields."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MinerProfileUpdate(BaseModel):
    """Update model (all fields optional)."""
    name: Optional[str] = None
    model: Optional[str] = None
    hashrate_ths: Optional[float] = None
    power_draw_watts: Optional[int] = None
    priority_level: Optional[int] = Field(default=None, ge=1, le=10)
    operating_mode: Optional[str] = None
    start_voltage: Optional[float] = None
    stop_voltage: Optional[float] = None
    emergency_stop_voltage: Optional[float] = None
    start_hysteresis_minutes: Optional[int] = None
    stop_hysteresis_minutes: Optional[int] = None
    require_excess_solar: Optional[bool] = None
    minimum_excess_watts: Optional[int] = None
    maximum_runtime_hours: Optional[int] = None
    prefer_time_start: Optional[int] = Field(default=None, ge=0, le=23)
    prefer_time_end: Optional[int] = Field(default=None, ge=0, le=23)
    allow_outside_schedule: Optional[bool] = None
    require_sunny_weather: Optional[bool] = None
    minimum_solar_production_watts: Optional[int] = None
    enabled: Optional[bool] = None
    control_method: Optional[str] = None
    device_identifier: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# HVAC Zone Models
# ─────────────────────────────────────────────────────────────────────────────

class HVACZoneBase(BaseModel):
    """Base model for HVAC zones (temperature-based climate control)."""

    # Identity
    zone_name: str = Field(description="Zone name (e.g., 'Heat Room', 'Main Room')")
    zone_type: str = Field(description="Zone type (equipment, living, storage, etc.)")

    # Temperature Thresholds
    temp_too_hot: Optional[float] = Field(
        default=None,
        description="Temperature to turn on cooling (°C)"
    )
    temp_hot_ok: Optional[float] = Field(
        default=None,
        description="Temperature to turn off cooling (°C)"
    )
    temp_too_cold: Optional[float] = Field(
        default=None,
        description="Temperature to turn on heating (°C)"
    )
    temp_cold_ok: Optional[float] = Field(
        default=None,
        description="Temperature to turn off heating (°C)"
    )

    # Cooling
    exhaust_fan_enabled: bool = Field(default=False, description="Enable exhaust fan")
    exhaust_fan_device_id: Optional[str] = Field(
        default=None,
        description="Exhaust fan device ID (e.g., 'ac_infinity_1')"
    )
    exhaust_fan_speed_auto: bool = Field(
        default=True,
        description="Auto-adjust fan speed based on temperature"
    )
    exhaust_fan_max_speed: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Maximum fan speed (1-10)"
    )

    # Heating
    heating_enabled: bool = Field(default=False, description="Enable heating")
    heating_priority_1: Optional[str] = Field(
        default=None,
        description="Primary heating source (miner, heater, etc.)"
    )
    heating_priority_2: Optional[str] = Field(
        default=None,
        description="Secondary heating source"
    )
    heater_device_id: Optional[str] = Field(
        default=None,
        description="Heater device ID (e.g., 'shelly_heater_1')"
    )

    # Constraints
    only_heat_when_solar: bool = Field(
        default=True,
        description="Only heat when solar production is available"
    )
    minimum_solar_for_heating_watts: Optional[int] = Field(
        default=None,
        description="Minimum solar production required for heating (watts)"
    )

    # Battery Protection
    block_charging_below_temp: Optional[float] = Field(
        default=None,
        description="Block battery charging below this temperature (°C, for LiFePO4 safety)"
    )

    # Status
    enabled: bool = Field(default=True, description="Zone enabled/disabled")
    temperature_sensor_id: Optional[str] = Field(
        default=None,
        description="Temperature sensor ID"
    )

    @validator('temp_hot_ok')
    def validate_hot_ok(cls, v, values):
        """Ensure temp_hot_ok < temp_too_hot."""
        if v is not None and 'temp_too_hot' in values and values['temp_too_hot'] is not None:
            if v >= values['temp_too_hot']:
                raise ValueError('temp_hot_ok must be < temp_too_hot')
        return v

    @validator('temp_cold_ok')
    def validate_cold_ok(cls, v, values):
        """Ensure temp_cold_ok > temp_too_cold."""
        if v is not None and 'temp_too_cold' in values and values['temp_too_cold'] is not None:
            if v <= values['temp_too_cold']:
                raise ValueError('temp_cold_ok must be > temp_too_cold')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "zone_name": "Heat Room",
                "zone_type": "equipment",
                "temp_too_hot": 40.0,
                "temp_hot_ok": 35.0,
                "temp_too_cold": 0.0,
                "temp_cold_ok": 5.0,
                "exhaust_fan_enabled": True,
                "exhaust_fan_device_id": "ac_infinity_1",
                "heating_enabled": True,
                "heating_priority_1": "miner",
                "heating_priority_2": "heater",
                "only_heat_when_solar": True,
                "minimum_solar_for_heating_watts": 4000,
                "enabled": True
            }
        }
    )


class HVACZoneResponse(HVACZoneBase):
    """Response model with additional fields."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HVACZoneUpdate(BaseModel):
    """Update model (all fields optional)."""
    zone_name: Optional[str] = None
    zone_type: Optional[str] = None
    temp_too_hot: Optional[float] = None
    temp_hot_ok: Optional[float] = None
    temp_too_cold: Optional[float] = None
    temp_cold_ok: Optional[float] = None
    exhaust_fan_enabled: Optional[bool] = None
    exhaust_fan_device_id: Optional[str] = None
    exhaust_fan_speed_auto: Optional[bool] = None
    exhaust_fan_max_speed: Optional[int] = Field(default=None, ge=1, le=10)
    heating_enabled: Optional[bool] = None
    heating_priority_1: Optional[str] = None
    heating_priority_2: Optional[str] = None
    heater_device_id: Optional[str] = None
    only_heat_when_solar: Optional[bool] = None
    minimum_solar_for_heating_watts: Optional[int] = None
    block_charging_below_temp: Optional[float] = None
    enabled: Optional[bool] = None
    temperature_sensor_id: Optional[str] = None
