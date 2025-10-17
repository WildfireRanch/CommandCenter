"""
API Route Constants

WHAT: Field whitelists for UPDATE operations
WHY: Prevent SQL injection via dynamic field names
HOW: Only allow specific, validated fields in UPDATE queries
"""

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
