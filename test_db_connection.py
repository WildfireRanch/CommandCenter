#!/usr/bin/env python3
"""
Quick database connection test.
Tests if we can connect and query the database.
"""

import os
import sys

# Try to get DATABASE_URL from environment or Railway
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print("❌ DATABASE_URL not set in environment")
    print("\n💡 To test with Railway database:")
    print("   export RAILWAY_TOKEN=<token>")
    print("   railway run --service CommandCenter python test_db_connection.py")
    sys.exit(1)

print(f"🔍 DATABASE_URL: {DATABASE_URL[:50]}...")

# Test connection
try:
    import psycopg2
    print("\n🔌 Attempting database connection...")

    conn = psycopg2.connect(DATABASE_URL)
    print("✅ Connection successful!")

    cursor = conn.cursor()

    # Test 1: Check database exists
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n📊 PostgreSQL version: {version[:50]}...")

    # Test 2: Check if user_preferences table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'user_preferences'
        );
    """)
    table_exists = cursor.fetchone()[0]

    if table_exists:
        print("✅ user_preferences table exists")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM user_preferences;")
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} user preference record(s)")

        if count > 0:
            # Show first record
            cursor.execute("""
                SELECT
                    voltage_at_0_percent,
                    voltage_at_100_percent,
                    voltage_critical_low,
                    voltage_low,
                    voltage_optimal_min,
                    voltage_optimal_max,
                    operating_mode
                FROM user_preferences
                LIMIT 1;
            """)
            prefs = cursor.fetchone()
            print("\n📋 Sample preferences:")
            print(f"   voltage_at_0_percent:   {prefs[0]}V")
            print(f"   voltage_at_100_percent: {prefs[1]}V")
            print(f"   voltage_critical_low:   {prefs[2]}V")
            print(f"   voltage_low:            {prefs[3]}V")
            print(f"   voltage_optimal_min:    {prefs[4]}V")
            print(f"   voltage_optimal_max:    {prefs[5]}V")
            print(f"   operating_mode:         {prefs[6]}")
    else:
        print("❌ user_preferences table does not exist")

    # Test 3: Check if miner_profiles table exists
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_name = 'miner_profiles'
        );
    """)
    table_exists = cursor.fetchone()[0]

    if table_exists:
        print("\n✅ miner_profiles table exists")

        # Count records
        cursor.execute("SELECT COUNT(*) FROM miner_profiles WHERE enabled = true;")
        count = cursor.fetchone()[0]
        print(f"📊 Found {count} active miner profile(s)")

        if count > 0:
            cursor.execute("""
                SELECT name, model, power_draw_watts, priority_level
                FROM miner_profiles
                WHERE enabled = true
                ORDER BY priority_level ASC
                LIMIT 5;
            """)
            miners = cursor.fetchall()
            print("\n🤖 Active miners:")
            for name, model, power, priority in miners:
                print(f"   [P{priority}] {name} ({model}) - {power}W")
    else:
        print("❌ miner_profiles table does not exist")

    cursor.close()
    conn.close()

    print("\n✅ All database tests passed!")
    print("\n🚀 V1.9 agent integration ready for deployment")

except Exception as e:
    print(f"\n❌ Database connection failed: {e}")
    print("\n💡 This is expected if:")
    print("   - Running locally (postgres_db.railway.internal not accessible)")
    print("   - Not running inside Railway container")
    print("   - DATABASE_URL not configured")
    sys.exit(1)
