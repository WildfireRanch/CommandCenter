-- ═══════════════════════════════════════════════════════════════════════════
-- FILE: railway/src/database/migrations/003_victron_schema_fixed.sql
-- PURPOSE: Initialize database schema for Victron Cerbo battery monitoring
--          (Fixed version that works without TimescaleDB)
--
-- WHAT IT DOES:
--   - Creates victron schema for battery data
--   - Creates battery_readings table
--   - Creates polling_status table
--   - Optionally converts to TimescaleDB hypertable if extension exists
--   - Sets up indexes for fast time-series queries
--
-- CHANGES FROM ORIGINAL:
--   - Gracefully handles missing TimescaleDB extension
--   - Creates tables even if TimescaleDB is not available
--   - Skips hypertable conversion and retention policies if TimescaleDB missing
--
-- USAGE:
--   railway run psql < railway/src/database/migrations/003_victron_schema_fixed.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Create Victron Schema
-- ─────────────────────────────────────────────────────────────────────────────

CREATE SCHEMA IF NOT EXISTS victron;

COMMENT ON SCHEMA victron IS 'Victron Cerbo GX battery monitoring data';


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Battery Readings Table
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS victron.battery_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Installation identifier
    installation_id VARCHAR(100),

    -- Core battery metrics
    soc FLOAT NOT NULL,                -- State of charge (%)
    voltage FLOAT,                     -- Battery voltage (V)
    current FLOAT,                     -- Battery current (A, +charging/-discharging)
    power FLOAT,                       -- Battery power (W)

    -- Battery state
    state VARCHAR(20),                 -- 'charging', 'discharging', 'idle'

    -- Temperature monitoring
    temperature FLOAT,                 -- Battery temperature (°C)

    -- Metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE victron.battery_readings IS 'Time-series battery data from Victron Cerbo GX';
COMMENT ON COLUMN victron.battery_readings.soc IS 'State of charge as percentage (0-100)';
COMMENT ON COLUMN victron.battery_readings.voltage IS 'Battery voltage in volts';
COMMENT ON COLUMN victron.battery_readings.current IS 'Battery current in amps (positive=charging, negative=discharging)';
COMMENT ON COLUMN victron.battery_readings.power IS 'Battery power in watts';
COMMENT ON COLUMN victron.battery_readings.state IS 'Battery state: charging, discharging, or idle';
COMMENT ON COLUMN victron.battery_readings.temperature IS 'Battery temperature in celsius';


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Convert to TimescaleDB Hypertable (if TimescaleDB is available)
-- ─────────────────────────────────────────────────────────────────────────────

-- Check if TimescaleDB extension exists before trying to use it
DO $$
DECLARE
    timescale_available BOOLEAN;
BEGIN
    -- Check if TimescaleDB extension is installed
    SELECT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) INTO timescale_available;

    IF timescale_available THEN
        -- TimescaleDB is available, check if already a hypertable
        IF NOT EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables
            WHERE hypertable_schema = 'victron'
            AND hypertable_name = 'battery_readings'
        ) THEN
            -- Convert to hypertable for efficient time-series queries
            PERFORM create_hypertable(
                'victron.battery_readings',
                'timestamp',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            );
            RAISE NOTICE '✓ Converted victron.battery_readings to TimescaleDB hypertable';
        ELSE
            RAISE NOTICE '✓ victron.battery_readings is already a hypertable';
        END IF;
    ELSE
        RAISE NOTICE '⚠ TimescaleDB not available - using standard PostgreSQL table';
        RAISE NOTICE '  Install TimescaleDB for better performance: CREATE EXTENSION timescaledb;';
    END IF;
END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Create Indexes
-- ─────────────────────────────────────────────────────────────────────────────

-- Index on timestamp (most common query pattern)
CREATE INDEX IF NOT EXISTS idx_battery_readings_timestamp
    ON victron.battery_readings(timestamp DESC);

-- Index on installation_id and timestamp (for multi-installation setups)
CREATE INDEX IF NOT EXISTS idx_battery_readings_installation
    ON victron.battery_readings(installation_id, timestamp DESC);

-- Index on created_at for cleanup queries
CREATE INDEX IF NOT EXISTS idx_battery_readings_created_at
    ON victron.battery_readings(created_at DESC);


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. Data Retention Policy (if TimescaleDB is available)
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    timescale_available BOOLEAN;
BEGIN
    -- Check if TimescaleDB extension is installed
    SELECT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) INTO timescale_available;

    IF timescale_available THEN
        -- Remove existing retention policy if it exists
        IF EXISTS (
            SELECT 1 FROM timescaledb_information.jobs
            WHERE proc_name = 'policy_retention'
            AND hypertable_name = 'battery_readings'
        ) THEN
            PERFORM remove_retention_policy('victron.battery_readings', if_exists => true);
        END IF;

        -- Add 72-hour retention policy
        PERFORM add_retention_policy(
            'victron.battery_readings',
            INTERVAL '72 hours',
            if_not_exists => true
        );

        RAISE NOTICE '✓ Added 72-hour retention policy to victron.battery_readings';
    ELSE
        RAISE NOTICE '⚠ Skipping retention policy (requires TimescaleDB)';
        RAISE NOTICE '  Consider manually cleaning old data or enabling TimescaleDB';
    END IF;
END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. Polling Status Table (Track poller health)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS victron.polling_status (
    id SERIAL PRIMARY KEY,

    -- Status tracking
    last_poll_attempt TIMESTAMPTZ,
    last_successful_poll TIMESTAMPTZ,
    last_error TEXT,

    -- API metrics
    requests_this_hour INTEGER DEFAULT 0,
    hour_window_start TIMESTAMPTZ DEFAULT NOW(),

    -- Health
    consecutive_failures INTEGER DEFAULT 0,
    is_healthy BOOLEAN DEFAULT TRUE,

    -- Metadata
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE victron.polling_status IS 'Tracks Victron polling service health and API rate limits';

-- Initialize with single row (singleton pattern)
INSERT INTO victron.polling_status (id, updated_at)
VALUES (1, NOW())
ON CONFLICT (id) DO NOTHING;

-- Auto-update timestamp
CREATE OR REPLACE FUNCTION victron.update_polling_status_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_update_polling_status_timestamp ON victron.polling_status;

CREATE TRIGGER trg_update_polling_status_timestamp
    BEFORE UPDATE ON victron.polling_status
    FOR EACH ROW
    EXECUTE FUNCTION victron.update_polling_status_timestamp();


-- ─────────────────────────────────────────────────────────────────────────────
-- 7. Helper Views
-- ─────────────────────────────────────────────────────────────────────────────

-- Latest battery reading view
CREATE OR REPLACE VIEW victron.latest_battery_reading AS
SELECT *
FROM victron.battery_readings
ORDER BY timestamp DESC
LIMIT 1;

COMMENT ON VIEW victron.latest_battery_reading IS 'Most recent battery reading from Victron';

-- Battery statistics for last 24 hours
CREATE OR REPLACE VIEW victron.battery_stats_24h AS
SELECT
    COUNT(*) as reading_count,
    MIN(timestamp) as first_reading,
    MAX(timestamp) as last_reading,
    AVG(soc) as avg_soc,
    MIN(soc) as min_soc,
    MAX(soc) as max_soc,
    AVG(voltage) as avg_voltage,
    MIN(voltage) as min_voltage,
    MAX(voltage) as max_voltage,
    AVG(current) as avg_current,
    AVG(power) as avg_power,
    AVG(temperature) as avg_temperature,
    MIN(temperature) as min_temperature,
    MAX(temperature) as max_temperature
FROM victron.battery_readings
WHERE timestamp >= NOW() - INTERVAL '24 hours';

COMMENT ON VIEW victron.battery_stats_24h IS '24-hour battery statistics';


-- ─────────────────────────────────────────────────────────────────────────────
-- 8. Verification
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    timescale_available BOOLEAN;
BEGIN
    -- Check if TimescaleDB extension is installed
    SELECT EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) INTO timescale_available;

    RAISE NOTICE '════════════════════════════════════════════════════════';
    RAISE NOTICE '✓ Victron schema created successfully';
    RAISE NOTICE '✓ victron.battery_readings table created';
    RAISE NOTICE '✓ victron.polling_status table created';
    RAISE NOTICE '✓ Indexes created for optimal query performance';
    RAISE NOTICE '✓ Helper views created';

    IF timescale_available THEN
        RAISE NOTICE '✓ TimescaleDB hypertable configured';
        RAISE NOTICE '✓ 72-hour retention policy applied';
    ELSE
        RAISE NOTICE '⚠ Running without TimescaleDB (performance may be reduced)';
    END IF;

    RAISE NOTICE '';
    RAISE NOTICE 'Ready for Victron Cerbo integration!';
    RAISE NOTICE '════════════════════════════════════════════════════════';
END $$;


-- ═══════════════════════════════════════════════════════════════════════════
-- End of Migration
-- ═══════════════════════════════════════════════════════════════════════════
