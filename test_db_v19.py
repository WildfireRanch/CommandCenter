#!/usr/bin/env python3
"""Test V1.9 database and API routes."""

import sys
sys.path.insert(0, '/workspaces/CommandCenter/railway')

from src.utils.db import get_connection, query_one

DEFAULT_USER_ID = "a0000000-0000-0000-0000-000000000001"

print("Testing V1.9 database...")
print("=" * 60)

try:
    with get_connection() as conn:
        # Check if user_preferences table exists
        table_check = query_one(
            conn,
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_name = 'user_preferences'
            ) as exists
            """,
            as_dict=True
        )

        print(f"✓ user_preferences table exists: {table_check['exists']}")

        if not table_check['exists']:
            print("\n❌ Table not found! Run migration first:")
            print("   curl -X POST https://api.wildfireranch.us/db/run-v19-migration")
            sys.exit(1)

        # Try to query preferences
        prefs = query_one(
            conn,
            """
            SELECT
                id, user_id,
                voltage_at_0_percent, voltage_at_100_percent, voltage_curve,
                battery_chemistry, battery_nominal_voltage,
                battery_absolute_min, battery_absolute_max,
                voltage_shutdown, voltage_critical_low, voltage_low,
                voltage_restart, voltage_optimal_min, voltage_optimal_max,
                voltage_float, voltage_absorption, voltage_full,
                user_prefers_soc_display, use_custom_soc_mapping, display_units,
                timezone, location_lat, location_lon,
                operating_mode, grid_import_allowed,
                created_at, updated_at
            FROM user_preferences
            WHERE user_id = %s::uuid
            LIMIT 1
            """,
            (DEFAULT_USER_ID,),
            as_dict=True
        )

        if not prefs:
            print("\n❌ No preferences found for default user!")
            print(f"   User ID: {DEFAULT_USER_ID}")
            print("   Run migration to create default data.")
            sys.exit(1)

        print(f"✓ Found preferences for user: {prefs['user_id']}")
        print(f"\nPreferences data:")
        print(f"  voltage_at_0_percent: {prefs['voltage_at_0_percent']} (type: {type(prefs['voltage_at_0_percent']).__name__})")
        print(f"  voltage_at_100_percent: {prefs['voltage_at_100_percent']} (type: {type(prefs['voltage_at_100_percent']).__name__})")
        print(f"  voltage_optimal_min: {prefs['voltage_optimal_min']} (type: {type(prefs['voltage_optimal_min']).__name__})")
        print(f"  voltage_optimal_max: {prefs['voltage_optimal_max']} (type: {type(prefs['voltage_optimal_max']).__name__})")
        print(f"  timezone: {prefs['timezone']}")
        print(f"  operating_mode: {prefs['operating_mode']}")

        # Now try to create Pydantic model
        print("\nTesting Pydantic model serialization...")
        from src.api.models.v1_9 import UserPreferencesResponse

        model = UserPreferencesResponse(**prefs)
        print("✓ Pydantic model instantiation successful")

        json_str = model.model_dump_json()
        print("✓ JSON serialization successful")

        import json
        parsed = json.loads(json_str)
        print(f"\nJSON output sample:")
        print(f"  voltage_at_0_percent: {parsed['voltage_at_0_percent']} (type: {type(parsed['voltage_at_0_percent']).__name__})")

        print("\n✅ All tests passed! Database and models working correctly.")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
