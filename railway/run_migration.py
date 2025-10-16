#!/usr/bin/env python3
"""
Run database migration 005_solark_schema.sql on Railway database.
Uses psql for multi-statement SQL execution with DO blocks.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_migration():
    # Get database URL
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ ERROR: DATABASE_URL not set")
        return False

    # Migration file path
    migration_file = Path(__file__).parent / 'src' / 'database' / 'migrations' / '005_solark_schema.sql'
    print(f"📂 Migration: {migration_file}")

    if not migration_file.exists():
        print(f"❌ ERROR: Migration file not found")
        return False

    # Check if psql is available
    print("🔍 Checking for psql...")
    try:
        result = subprocess.run(['which', 'psql'], capture_output=True, text=True)
        psql_path = result.stdout.strip()
        if psql_path:
            print(f"✅ Found psql: {psql_path}")
        else:
            print("❌ ERROR: psql not found. Install with: apt-get install postgresql-client")
            return False
    except Exception as e:
        print(f"❌ ERROR checking for psql: {e}")
        return False

    # Execute migration using psql
    print("🚀 Executing migration with psql...")
    try:
        result = subprocess.run(
            ['psql', database_url, '-f', str(migration_file)],
            capture_output=True,
            text=True,
            timeout=60
        )

        # Print output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    if 'NOTICE:' in line:
                        print(f"  ℹ️  {line.split('NOTICE:')[1].strip()}")
                    elif 'ERROR' in line:
                        print(f"  ❌ {line}")
                    else:
                        print(f"  {line}")

        if result.stderr:
            for line in result.stderr.split('\n'):
                if line.strip() and 'NOTICE' not in line:
                    print(f"  ⚠️  {line}")

        if result.returncode != 0:
            print(f"❌ Migration failed with exit code {result.returncode}")
            return False

        print("✅ Migration executed successfully")

        # Verify the table exists
        print("🔍 Verifying solark.telemetry table...")
        verify_cmd = [
            'psql', database_url, '-t', '-c',
            "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema = 'solark' AND table_name = 'telemetry')"
        ]
        verify_result = subprocess.run(verify_cmd, capture_output=True, text=True, timeout=10)

        if 't' in verify_result.stdout or 'true' in verify_result.stdout.lower():
            print("✅ Verified: solark.telemetry exists")

            # Check if it's a hypertable
            hypertable_cmd = [
                'psql', database_url, '-t', '-c',
                "SELECT EXISTS (SELECT 1 FROM timescaledb_information.hypertables WHERE hypertable_schema = 'solark' AND hypertable_name = 'telemetry')"
            ]
            ht_result = subprocess.run(hypertable_cmd, capture_output=True, text=True, timeout=10)
            if 't' in ht_result.stdout or 'true' in ht_result.stdout.lower():
                print("✅ Configured as TimescaleDB hypertable")

            return True
        else:
            print("❌ Table verification failed")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Migration timed out")
        return False
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False

if __name__ == '__main__':
    print("⚡ SolArk Schema Migration (005)")
    success = run_migration()
    sys.exit(0 if success else 1)
