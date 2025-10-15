#!/usr/bin/env python3
"""
Create Victron tables via a temporary API endpoint.
This runs in the Railway environment where DATABASE_URL works.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.db import get_connection

def create_victron_tables():
    """Create victron schema and tables."""

    print("Creating Victron database tables...")

    with get_connection() as conn:
        conn.autocommit = True
        cursor = conn.cursor()

        # Create schema
        print("1. Creating victron schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS victron;")

        # Create battery_readings table
        print("2. Creating battery_readings table...")
        cursor.execute("""
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
        """)

        # Create polling_status table
        print("3. Creating polling_status table...")
        cursor.execute("""
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
        """)

        # Insert default polling status
        print("4. Inserting default polling status...")
        cursor.execute("""
        INSERT INTO victron.polling_status (id, updated_at)
        VALUES (1, NOW())
        ON CONFLICT (id) DO NOTHING;
        """)

        # Create indexes
        print("5. Creating indexes...")
        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_battery_readings_timestamp
            ON victron.battery_readings(timestamp DESC);
        """)

        cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_battery_readings_installation
            ON victron.battery_readings(installation_id, timestamp DESC);
        """)

        # Verify
        print("6. Verifying tables...")
        cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'victron'
        ORDER BY table_name;
        """)
        tables = cursor.fetchall()

        cursor.close()

    print(f"\n✅ SUCCESS! Tables created: {[t[0] for t in tables]}")
    return tables

if __name__ == "__main__":
    create_victron_tables()
