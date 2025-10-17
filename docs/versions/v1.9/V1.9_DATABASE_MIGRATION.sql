-- CommandCenter V1.9 Database Migration
-- User Preferences & Voltage-Based Decision System
-- CRITICAL: Backup database before running!
-- Test on staging first!

BEGIN;

-- ============================================================================
-- MIGRATION VERSION TRACKING
-- ============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    applied_at TIMESTAMPTZ DEFAULT NOW(),
    description TEXT
);

INSERT INTO schema_migrations (version, description) 
VALUES ('v1.9.0', 'User preferences, miner profiles, HVAC zones');

-- ============================================================================
-- TABLE 1: USERS
-- ============================================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT DEFAULT 'admin' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login TIMESTAMPTZ,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

CREATE INDEX idx_users_email ON users(email);

-- ============================================================================
-- TABLE 2: USER_PREFERENCES (Voltage-based)
-- ============================================================================

CREATE TABLE user_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Battery Calibration (Voltage-SOC Mapping)
    voltage_at_0_percent DECIMAL(4,2) DEFAULT 45.0 NOT NULL,
    voltage_at_100_percent DECIMAL(4,2) DEFAULT 56.0 NOT NULL,
    voltage_curve JSONB DEFAULT NULL,
    
    -- Battery Specs
    battery_chemistry TEXT DEFAULT 'LiFePO4',
    battery_nominal_voltage DECIMAL(4,2) DEFAULT 51.2,
    battery_absolute_min DECIMAL(4,2) DEFAULT 43.0,
    battery_absolute_max DECIMAL(4,2) DEFAULT 58.8,
    
    -- Operating Thresholds (ALL IN VOLTAGE)
    voltage_shutdown DECIMAL(4,2) DEFAULT 44.0 NOT NULL,
    voltage_critical_low DECIMAL(4,2) DEFAULT 45.0 NOT NULL,
    voltage_low DECIMAL(4,2) DEFAULT 47.0 NOT NULL,
    voltage_restart DECIMAL(4,2) DEFAULT 50.0 NOT NULL,
    voltage_optimal_min DECIMAL(4,2) DEFAULT 50.0 NOT NULL,
    voltage_optimal_max DECIMAL(4,2) DEFAULT 54.5 NOT NULL,
    voltage_float DECIMAL(4,2) DEFAULT 54.0 NOT NULL,
    voltage_absorption DECIMAL(4,2) DEFAULT 57.6 NOT NULL,
    voltage_full DECIMAL(4,2) DEFAULT 56.0 NOT NULL,
    
    -- Display Preferences
    user_prefers_soc_display BOOLEAN DEFAULT true,
    use_custom_soc_mapping BOOLEAN DEFAULT true,
    display_units TEXT DEFAULT 'metric',
    
    -- System Settings
    timezone TEXT DEFAULT 'America/Los_Angeles',
    location_lat DECIMAL(10,7),
    location_lon DECIMAL(10,7),
    operating_mode TEXT DEFAULT 'balanced',
    grid_import_allowed BOOLEAN DEFAULT false,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_voltage_calibration CHECK (
        voltage_at_0_percent < voltage_at_100_percent
    ),
    CONSTRAINT valid_voltage_ranges CHECK (
        voltage_shutdown < voltage_critical_low AND
        voltage_critical_low <= voltage_low AND
        voltage_low < voltage_restart AND
        voltage_restart <= voltage_optimal_min AND
        voltage_optimal_min < voltage_optimal_max AND
        voltage_optimal_max <= voltage_float AND
        voltage_float < voltage_absorption AND
        voltage_absorption <= voltage_full AND
        voltage_full <= battery_absolute_max
    ),
    CONSTRAINT one_preference_per_user UNIQUE (user_id)
);

CREATE INDEX idx_user_preferences_user ON user_preferences(user_id);

-- ============================================================================
-- TABLE 3: MINER_PROFILES (Priority-based)
-- ============================================================================

CREATE TABLE miner_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Identity
    name TEXT NOT NULL,
    model TEXT,
    hashrate_ths DECIMAL(6,2),
    power_draw_watts INT NOT NULL,
    
    -- Priority & Strategy
    priority_level INT NOT NULL DEFAULT 5,
    operating_mode TEXT NOT NULL DEFAULT 'balanced',
    
    -- Voltage Thresholds
    start_voltage DECIMAL(4,2) NOT NULL,
    stop_voltage DECIMAL(4,2) NOT NULL,
    emergency_stop_voltage DECIMAL(4,2) NOT NULL,
    start_hysteresis_minutes INT DEFAULT 5,
    stop_hysteresis_minutes INT DEFAULT 2,
    
    -- Operating Constraints
    require_excess_solar BOOLEAN DEFAULT false,
    minimum_excess_watts INT,
    maximum_runtime_hours INT,
    
    -- Scheduling
    prefer_time_start INT CHECK (prefer_time_start BETWEEN 0 AND 23),
    prefer_time_end INT CHECK (prefer_time_end BETWEEN 0 AND 23),
    allow_outside_schedule BOOLEAN DEFAULT true,
    
    -- Weather Requirements (V2)
    require_sunny_weather BOOLEAN DEFAULT false,
    minimum_solar_production_watts INT,
    
    -- Status & Control
    enabled BOOLEAN DEFAULT true,
    control_method TEXT,
    device_identifier TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_started_at TIMESTAMPTZ,
    last_stopped_at TIMESTAMPTZ,
    total_runtime_hours DECIMAL(10,2) DEFAULT 0,
    
    CONSTRAINT valid_priority CHECK (priority_level BETWEEN 1 AND 10),
    CONSTRAINT valid_voltage_thresholds CHECK (
        emergency_stop_voltage < stop_voltage AND
        stop_voltage < start_voltage
    )
);

CREATE INDEX idx_miner_profiles_user ON miner_profiles(user_id);
CREATE INDEX idx_miner_profiles_priority ON miner_profiles(user_id, priority_level, enabled);

-- ============================================================================
-- TABLE 4: HVAC_ZONES (Temperature-based)
-- ============================================================================

CREATE TABLE hvac_zones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Identity
    zone_name TEXT NOT NULL,
    zone_type TEXT NOT NULL,
    
    -- Temperature Thresholds (Celsius)
    temp_too_hot DECIMAL(4,1),
    temp_hot_ok DECIMAL(4,1),
    temp_too_cold DECIMAL(4,1),
    temp_cold_ok DECIMAL(4,1),
    
    -- Cooling Devices
    exhaust_fan_enabled BOOLEAN DEFAULT false,
    exhaust_fan_device_id TEXT,
    exhaust_fan_speed_auto BOOLEAN DEFAULT true,
    exhaust_fan_max_speed INT DEFAULT 10,
    
    -- Heating Devices
    heating_enabled BOOLEAN DEFAULT false,
    heating_priority_1 TEXT,
    heating_priority_2 TEXT,
    heater_device_id TEXT,
    
    -- Operating Constraints
    only_heat_when_solar BOOLEAN DEFAULT true,
    minimum_solar_for_heating_watts INT,
    
    -- Battery Protection (CRITICAL for LiFePO4)
    block_charging_below_temp DECIMAL(4,1),
    
    -- Status
    enabled BOOLEAN DEFAULT true,
    temperature_sensor_id TEXT,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    CONSTRAINT valid_temp_thresholds CHECK (
        (temp_too_cold IS NULL OR temp_cold_ok IS NULL OR temp_too_cold < temp_cold_ok) AND
        (temp_hot_ok IS NULL OR temp_too_hot IS NULL OR temp_cold_ok < temp_hot_ok) AND
        (temp_hot_ok IS NULL OR temp_too_hot IS NULL OR temp_hot_ok < temp_too_hot)
    )
);

CREATE INDEX idx_hvac_zones_user ON hvac_zones(user_id);

-- ============================================================================
-- POPULATE DEFAULT DATA (Solar Shack Configuration)
-- ============================================================================

-- Create default user
INSERT INTO users (id, email, password_hash, role)
VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'admin@wildfireranch.us',
    '$2b$12$placeholder_hash_replace_in_production',
    'admin'
);

-- Create default preferences (from Solar Shack specs)
INSERT INTO user_preferences (
    user_id,
    voltage_at_0_percent,
    voltage_at_100_percent,
    voltage_curve,
    battery_chemistry,
    battery_nominal_voltage,
    battery_absolute_min,
    battery_absolute_max,
    voltage_shutdown,
    voltage_critical_low,
    voltage_low,
    voltage_restart,
    voltage_optimal_min,
    voltage_optimal_max,
    voltage_float,
    voltage_absorption,
    voltage_full,
    timezone,
    location_lat,
    location_lon,
    operating_mode,
    grid_import_allowed
) VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    45.0, 56.0,
    '[{"soc":0,"voltage":45.0},{"soc":15,"voltage":47.0},{"soc":40,"voltage":50.0},{"soc":60,"voltage":52.0},{"soc":80,"voltage":54.5},{"soc":100,"voltage":56.0}]'::jsonb,
    'LiFePO4', 51.2, 43.0, 58.8,
    44.0, 45.0, 47.0, 50.0, 50.0, 54.5, 54.0, 57.6, 56.0,
    'America/Los_Angeles', 37.3382, -121.8863, 'balanced', false
);

-- Create primary miner
INSERT INTO miner_profiles (
    user_id, name, model, hashrate_ths, power_draw_watts,
    priority_level, operating_mode,
    start_voltage, stop_voltage, emergency_stop_voltage,
    require_excess_solar, prefer_time_start, prefer_time_end,
    allow_outside_schedule, require_sunny_weather,
    enabled, control_method
) VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'Primary S21+ (Revenue)', 'Antminer S21+ 235TH', 235.0, 3878,
    1, 'aggressive',
    50.0, 47.0, 45.0,
    false, 18, 10,
    true, false,
    true, 'smartload'
);

-- Create dump load miner
INSERT INTO miner_profiles (
    user_id, name, model, hashrate_ths, power_draw_watts,
    priority_level, operating_mode,
    start_voltage, stop_voltage, emergency_stop_voltage,
    require_excess_solar, minimum_excess_watts, minimum_solar_production_watts,
    prefer_time_start, prefer_time_end, allow_outside_schedule,
    require_sunny_weather, enabled, control_method
) VALUES (
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'Dump Load S19 #1', 'Antminer S19 95TH', 95.0, 3250,
    3, 'opportunistic',
    54.5, 53.0, 50.0,
    true, 3500, 8000,
    10, 16, false,
    true, true, 'shelly'
);

-- Create HVAC zones
INSERT INTO hvac_zones (
    user_id, zone_name, zone_type,
    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
    exhaust_fan_enabled, exhaust_fan_device_id, exhaust_fan_speed_auto, exhaust_fan_max_speed,
    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
    only_heat_when_solar, minimum_solar_for_heating_watts,
    block_charging_below_temp, enabled
) VALUES 
(
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'Heat Room', 'equipment',
    40.0, 35.0, 0.0, 5.0,
    true, 'ac_infinity_1', true, 10,
    true, 'miner', 'heater', 'shelly_heater_1',
    true, 4000,
    0.0, true
),
(
    'a0000000-0000-0000-0000-000000000001'::uuid,
    'Main Room', 'equipment',
    35.0, 30.0, -5.0, 0.0,
    true, 'ac_infinity_2', true, 8,
    true, 'heater', 'none', 'shelly_heater_2',
    true, 2000,
    NULL, true
);

-- ============================================================================
-- UPDATE TRIGGERS
-- ============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_miner_profiles_updated_at BEFORE UPDATE ON miner_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_hvac_zones_updated_at BEFORE UPDATE ON hvac_zones
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

COMMIT;

-- ============================================================================
-- ROLLBACK SCRIPT (Run to undo migration)
-- ============================================================================

/*
BEGIN;
DROP TABLE IF EXISTS hvac_zones CASCADE;
DROP TABLE IF EXISTS miner_profiles CASCADE;
DROP TABLE IF EXISTS user_preferences CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
DELETE FROM schema_migrations WHERE version = 'v1.9.0';
COMMIT;
*/

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

SELECT 'Migration completed successfully!' AS status;

SELECT * FROM users;
SELECT * FROM user_preferences;
SELECT name, priority_level, start_voltage, stop_voltage FROM miner_profiles;
SELECT zone_name, temp_too_hot, temp_too_cold FROM hvac_zones;