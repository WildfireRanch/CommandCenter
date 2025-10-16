-- =====================================================
-- Migration: 005_solark_schema.sql
-- Purpose: Create solark schema and telemetry table
-- Date: 2025-10-16
-- =====================================================

-- Create solark schema
CREATE SCHEMA IF NOT EXISTS solark;

-- Create telemetry table
CREATE TABLE IF NOT EXISTS solark.telemetry (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Battery metrics
    soc FLOAT,                    -- State of Charge (%)
    batt_power FLOAT,             -- Battery power (W, + = charging, - = discharging)
    batt_voltage FLOAT,           -- Battery voltage (V)
    batt_current FLOAT,           -- Battery current (A)

    -- Solar metrics
    pv_power FLOAT,               -- Total PV production (W)
    pv_voltage FLOAT,             -- PV voltage (V)
    pv_current FLOAT,             -- PV current (A)

    -- Load metrics
    load_power FLOAT,             -- Total load consumption (W)

    -- Grid metrics
    grid_power FLOAT,             -- Grid power (W, + = export, - = import)
    pv_to_grid FLOAT,             -- PV to grid export (W)
    grid_to_load FLOAT,           -- Grid to load import (W)

    -- Power flow indicators (boolean flags)
    pv_to_load BOOLEAN DEFAULT FALSE,
    pv_to_bat BOOLEAN DEFAULT FALSE,
    bat_to_load BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);

-- Convert to TimescaleDB hypertable
-- Only run if TimescaleDB extension is available
DO $$
BEGIN
    -- Check if TimescaleDB is installed
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) THEN
        -- Check if table is not already a hypertable
        IF NOT EXISTS (
            SELECT 1 FROM timescaledb_information.hypertables
            WHERE hypertable_schema = 'solark'
            AND hypertable_name = 'telemetry'
        ) THEN
            -- Convert to hypertable
            PERFORM create_hypertable(
                'solark.telemetry',
                'timestamp',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            );

            RAISE NOTICE 'Created hypertable: solark.telemetry';
        ELSE
            RAISE NOTICE 'Hypertable already exists: solark.telemetry';
        END IF;
    ELSE
        RAISE NOTICE 'TimescaleDB not installed - table created as regular table';
    END IF;
END $$;

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_solark_telemetry_timestamp
    ON solark.telemetry (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_solark_telemetry_plant_id
    ON solark.telemetry (plant_id);

CREATE INDEX IF NOT EXISTS idx_solark_telemetry_created_at
    ON solark.telemetry (created_at DESC);

-- Optional: Add retention policy (90 days)
-- Uncomment if you want automatic data cleanup
/*
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM pg_extension WHERE extname = 'timescaledb'
    ) THEN
        PERFORM add_retention_policy(
            'solark.telemetry',
            INTERVAL '90 days',
            if_not_exists => TRUE
        );
        RAISE NOTICE 'Added retention policy: 90 days';
    END IF;
END $$;
*/

-- Verify table was created
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'solark'
        AND table_name = 'telemetry'
    ) THEN
        RAISE NOTICE 'SUCCESS: solark.telemetry table created';
    ELSE
        RAISE EXCEPTION 'FAILED: solark.telemetry table not created';
    END IF;
END $$;
