-- =====================================================
-- V1.9 Migration Validation Script
-- Purpose: Verify migration was successful
-- Run after: 006_v1.9_user_preferences.sql
-- =====================================================

\echo '=========================================='
\echo 'V1.9 Migration Validation'
\echo '=========================================='

-- Check 1: Verify migration tracking
\echo ''
\echo '1. Migration Tracking:'
SELECT version, description, applied_at
FROM schema_migrations
WHERE version = 'v1.9.0';

-- Check 2: Verify all tables exist
\echo ''
\echo '2. Table Existence:'
SELECT
    CASE
        WHEN COUNT(*) = 4 THEN '✓ All 4 tables exist'
        ELSE '✗ Missing tables: ' || (4 - COUNT(*))::text
    END AS status
FROM information_schema.tables
WHERE table_name IN ('users', 'user_preferences', 'miner_profiles', 'hvac_zones')
  AND table_schema = 'public';

-- List tables
SELECT table_name, table_type
FROM information_schema.tables
WHERE table_name IN ('users', 'user_preferences', 'miner_profiles', 'hvac_zones')
ORDER BY table_name;

-- Check 3: Verify user created
\echo ''
\echo '3. Default User:'
SELECT
    id,
    email,
    role,
    created_at
FROM users;

-- Check 4: Verify user preferences
\echo ''
\echo '4. User Preferences (Voltage Thresholds):'
SELECT
    voltage_at_0_percent || 'V = 0%' AS calibration_min,
    voltage_at_100_percent || 'V = 100%' AS calibration_max,
    voltage_optimal_min || 'V (optimal min)' AS optimal_min,
    voltage_optimal_max || 'V (optimal max)' AS optimal_max,
    battery_chemistry,
    operating_mode
FROM user_preferences;

-- Check 5: Verify voltage curve
\echo ''
\echo '5. Voltage Calibration Curve:'
SELECT
    jsonb_pretty(voltage_curve) AS voltage_soc_mapping
FROM user_preferences;

-- Check 6: Verify miner profiles
\echo ''
\echo '6. Miner Profiles:'
SELECT
    name,
    priority_level,
    power_draw_watts || 'W' AS power,
    start_voltage || 'V' AS start_v,
    stop_voltage || 'V' AS stop_v,
    require_excess_solar,
    enabled
FROM miner_profiles
ORDER BY priority_level;

-- Check 7: Verify HVAC zones
\echo ''
\echo '7. HVAC Zones:'
SELECT
    zone_name,
    zone_type,
    temp_too_hot || '°C (hot)' AS cooling_trigger,
    temp_too_cold || '°C (cold)' AS heating_trigger,
    exhaust_fan_enabled,
    heating_enabled
FROM hvac_zones
ORDER BY zone_name;

-- Check 8: Verify constraints
\echo ''
\echo '8. Constraints:'
SELECT
    conname AS constraint_name,
    contype AS type,
    CASE contype
        WHEN 'c' THEN 'CHECK'
        WHEN 'f' THEN 'FOREIGN KEY'
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'u' THEN 'UNIQUE'
        ELSE contype::text
    END AS constraint_type
FROM pg_constraint
WHERE conrelid IN (
    SELECT oid FROM pg_class
    WHERE relname IN ('users', 'user_preferences', 'miner_profiles', 'hvac_zones')
)
ORDER BY conrelid::regclass::text, conname;

-- Check 9: Verify indexes
\echo ''
\echo '9. Indexes:'
SELECT
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename IN ('users', 'user_preferences', 'miner_profiles', 'hvac_zones')
ORDER BY tablename, indexname;

-- Check 10: Verify triggers
\echo ''
\echo '10. Triggers:'
SELECT
    trigger_name,
    event_object_table AS table_name,
    action_timing,
    event_manipulation
FROM information_schema.triggers
WHERE event_object_table IN ('users', 'user_preferences', 'miner_profiles', 'hvac_zones')
ORDER BY event_object_table, trigger_name;

-- Check 11: Count records
\echo ''
\echo '11. Record Counts:'
SELECT
    'users' AS table_name,
    COUNT(*) AS record_count,
    CASE WHEN COUNT(*) = 1 THEN '✓' ELSE '✗' END AS expected
FROM users
UNION ALL
SELECT
    'user_preferences',
    COUNT(*),
    CASE WHEN COUNT(*) = 1 THEN '✓' ELSE '✗' END
FROM user_preferences
UNION ALL
SELECT
    'miner_profiles',
    COUNT(*),
    CASE WHEN COUNT(*) = 2 THEN '✓' ELSE '✗' END
FROM miner_profiles
UNION ALL
SELECT
    'hvac_zones',
    COUNT(*),
    CASE WHEN COUNT(*) = 2 THEN '✓' ELSE '✗' END
FROM hvac_zones;

-- Check 12: Test voltage threshold ordering
\echo ''
\echo '12. Voltage Threshold Ordering Test:'
SELECT
    CASE
        WHEN voltage_shutdown < voltage_critical_low
         AND voltage_critical_low <= voltage_low
         AND voltage_low < voltage_restart
         AND voltage_restart <= voltage_optimal_min
         AND voltage_optimal_min < voltage_optimal_max
         AND voltage_optimal_max <= voltage_float
         AND voltage_float < voltage_absorption
         THEN '✓ All voltage thresholds properly ordered'
        ELSE '✗ Voltage threshold ordering invalid'
    END AS validation_result,
    voltage_shutdown || 'V → ' ||
    voltage_critical_low || 'V → ' ||
    voltage_low || 'V → ' ||
    voltage_restart || 'V → ' ||
    voltage_optimal_min || 'V → ' ||
    voltage_optimal_max || 'V → ' ||
    voltage_float || 'V → ' ||
    voltage_absorption || 'V' AS voltage_sequence
FROM user_preferences;

-- Check 13: Test miner voltage thresholds
\echo ''
\echo '13. Miner Voltage Threshold Test:'
SELECT
    name,
    CASE
        WHEN emergency_stop_voltage < stop_voltage
         AND stop_voltage < start_voltage
         THEN '✓ Valid'
        ELSE '✗ Invalid'
    END AS validation,
    emergency_stop_voltage || 'V (emergency) < ' ||
    stop_voltage || 'V (stop) < ' ||
    start_voltage || 'V (start)' AS threshold_sequence
FROM miner_profiles
ORDER BY priority_level;

\echo ''
\echo '=========================================='
\echo 'Validation Complete!'
\echo '=========================================='
