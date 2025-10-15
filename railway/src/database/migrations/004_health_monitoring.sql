-- ═══════════════════════════════════════════════════════════════════════════
-- FILE: railway/src/database/migrations/004_health_monitoring.sql
-- PURPOSE: Create health monitoring schema and tables
--
-- WHAT IT DOES:
--   - Creates monitoring schema for health tracking
--   - Creates health_snapshots table for historical health data
--   - Sets up TimescaleDB hypertable for efficient time-series queries
--   - Configures 14-day retention policy
--   - Creates indexes for fast queries
--
-- DEPENDENCIES:
--   - TimescaleDB extension (already installed)
--   - PostgreSQL 15+
--
-- USAGE:
--   psql $DATABASE_URL -f 004_health_monitoring.sql
-- ═══════════════════════════════════════════════════════════════════════════

-- Create monitoring schema
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create health_snapshots table
CREATE TABLE IF NOT EXISTS monitoring.health_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Overall status
    overall_status VARCHAR(20) NOT NULL,

    -- Database metrics
    db_connected BOOLEAN NOT NULL,
    db_active_connections INTEGER,
    db_response_time_ms NUMERIC(10,2),

    -- SolArk poller
    solark_running BOOLEAN,
    solark_healthy BOOLEAN,
    solark_consecutive_failures INTEGER,
    solark_records_24h INTEGER,
    solark_collection_health_pct NUMERIC(5,2),

    -- Victron poller
    victron_running BOOLEAN,
    victron_healthy BOOLEAN,
    victron_consecutive_failures INTEGER,
    victron_records_24h INTEGER,
    victron_collection_health_pct NUMERIC(5,2),
    victron_api_requests_hour INTEGER,

    -- Data quality
    solark_null_pct NUMERIC(5,2),
    victron_null_pct NUMERIC(5,2),

    -- Database size
    solark_table_size_mb NUMERIC(10,2),
    victron_table_size_mb NUMERIC(10,2),

    -- Alert count
    critical_alerts INTEGER DEFAULT 0,
    warning_alerts INTEGER DEFAULT 0
);

-- Create hypertable for time-series optimization (only if not already created)
-- This will fail gracefully if the table is already a hypertable
DO $$
BEGIN
    PERFORM create_hypertable('monitoring.health_snapshots', 'timestamp', if_not_exists => TRUE);
EXCEPTION
    WHEN OTHERS THEN
        RAISE NOTICE 'Hypertable already exists or could not be created: %', SQLERRM;
END
$$;

-- Add retention policy: keep 14 days
-- Remove existing policy first if it exists
SELECT remove_retention_policy('monitoring.health_snapshots', if_exists => true);
SELECT add_retention_policy('monitoring.health_snapshots', INTERVAL '14 days');

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_health_snapshots_timestamp
    ON monitoring.health_snapshots(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_health_snapshots_status
    ON monitoring.health_snapshots(overall_status, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_health_snapshots_collection_health
    ON monitoring.health_snapshots(solark_collection_health_pct, victron_collection_health_pct);

-- Grant permissions (if using restricted users)
GRANT USAGE ON SCHEMA monitoring TO PUBLIC;
GRANT SELECT, INSERT ON monitoring.health_snapshots TO PUBLIC;
GRANT USAGE, SELECT ON SEQUENCE monitoring.health_snapshots_id_seq TO PUBLIC;

-- Verify table was created
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'monitoring'
        AND table_name = 'health_snapshots'
    ) THEN
        RAISE NOTICE 'SUCCESS: monitoring.health_snapshots table created';
    ELSE
        RAISE EXCEPTION 'FAILED: monitoring.health_snapshots table not found';
    END IF;
END
$$;

-- Display table info
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname = 'monitoring'
AND tablename = 'health_snapshots';

RAISE NOTICE 'Migration 004_health_monitoring.sql completed successfully';
