#!/usr/bin/env python3
"""
Run database migrations for CommandCenter.

Usage:
    python run_migration.py migrations/001_agent_memory_schema.sql
"""

import os
import sys
from pathlib import Path

import psycopg2
from dotenv import load_dotenv

# Load environment variables
root_dir = Path(__file__).parent.parent  # Go up to CommandCenter root
env_file = root_dir / ".env"
load_dotenv(dotenv_path=env_file)

def run_migration(sql_file: Path):
    """Run a SQL migration file."""
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("❌ DATABASE_URL not set")
        print("   Make sure your .env file is configured")
        return False

    if not sql_file.exists():
        print(f"❌ Migration file not found: {sql_file}")
        return False

    print(f"📋 Running migration: {sql_file.name}")
    print(f"🗄️  Database: {database_url.split('@')[1] if '@' in database_url else 'configured'}")

    try:
        # Read SQL file
        sql = sql_file.read_text()

        # Connect to database
        print("🔌 Connecting to database...")
        conn = psycopg2.connect(database_url)
        conn.autocommit = True  # Auto-commit for DDL statements

        # Execute migration
        print("⚙️  Executing migration...")
        with conn.cursor() as cursor:
            cursor.execute(sql)

        print("✅ Migration completed successfully!")

        # Close connection
        conn.close()
        return True

    except psycopg2.Error as e:
        print(f"❌ Migration failed: {e}")
        print(f"\n📄 Error details:")
        print(f"   SQLSTATE: {e.pgcode}")
        print(f"   Message: {e.pgerror}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


if __name__ == "__main__":
    # Default migration file
    migration_file = Path("migrations/001_agent_memory_schema.sql")

    # Allow custom file from command line
    if len(sys.argv) > 1:
        migration_file = Path(sys.argv[1])

    # Ensure we're in the railway directory
    os.chdir(Path(__file__).parent)

    # Run migration
    success = run_migration(migration_file)

    # Exit with appropriate code
    sys.exit(0 if success else 1)
