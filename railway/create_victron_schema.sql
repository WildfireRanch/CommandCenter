-- Create victron schema WITHOUT TimescaleDB dependency
CREATE SCHEMA IF NOT EXISTS victron;

-- Create battery_readings table
CREATE TABLE IF NOT EXISTS victron.battery_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    installation_id VARCHAR(100),
    soc FLOAT NOT NULL,
    voltage FLOAT,
    current FLOAT,
    power FLOAT,
    state VARCHAR(20),
    temperature FLOAT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create polling_status table
CREATE TABLE IF NOT EXISTS victron.polling_status (
    id SERIAL PRIMARY KEY,
    last_poll_attempt TIMESTAMPTZ,
    last_successful_poll TIMESTAMPTZ,
    last_error TEXT,
    requests_this_hour INTEGER DEFAULT 0,
    hour_window_start TIMESTAMPTZ DEFAULT NOW(),
    consecutive_failures INTEGER DEFAULT 0,
    is_healthy BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default polling status
INSERT INTO victron.polling_status (id, updated_at)
VALUES (1, NOW())
ON CONFLICT (id) DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_battery_readings_timestamp
    ON victron.battery_readings(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_battery_readings_installation
    ON victron.battery_readings(installation_id, timestamp DESC);

-- Show tables
\dt victron.*

SELECT 'Victron schema created successfully!' as result;
