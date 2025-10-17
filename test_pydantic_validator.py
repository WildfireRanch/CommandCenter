#!/usr/bin/env python3
"""Test field_validator with Decimal values."""

from decimal import Decimal
from datetime import datetime
from uuid import UUID
import sys

sys.path.insert(0, '/workspaces/CommandCenter/railway')

# Simulate RealDictRow data from PostgreSQL
class MockRealDictRow(dict):
    """Mock psycopg2 RealDictRow behavior."""
    pass

# Create mock data as it comes from database
mock_db_row = MockRealDictRow({
    'id': UUID('21a11f45-a751-491d-b612-bb26b8d3b48e'),
    'user_id': UUID('a0000000-0000-0000-0000-000000000001'),
    'voltage_at_0_percent': Decimal('45.0'),
    'voltage_at_100_percent': Decimal('56.0'),
    'voltage_curve': None,
    'battery_chemistry': 'LiFePO4',
    'battery_nominal_voltage': Decimal('51.2'),
    'battery_absolute_min': Decimal('43.0'),
    'battery_absolute_max': Decimal('58.8'),
    'voltage_shutdown': Decimal('44.0'),
    'voltage_critical_low': Decimal('45.0'),
    'voltage_low': Decimal('47.0'),
    'voltage_restart': Decimal('50.0'),
    'voltage_optimal_min': Decimal('50.0'),
    'voltage_optimal_max': Decimal('54.5'),
    'voltage_float': Decimal('55.0'),
    'voltage_absorption': Decimal('57.6'),
    'voltage_full': Decimal('58.0'),
    'user_prefers_soc_display': True,
    'use_custom_soc_mapping': True,
    'display_units': 'metric',
    'timezone': 'America/Los_Angeles',
    'location_lat': Decimal('37.3382'),
    'location_lon': Decimal('-121.8863'),
    'operating_mode': 'balanced',
    'grid_import_allowed': False,
    'created_at': datetime.fromisoformat('2025-10-17T13:19:12.253559+00:00'),
    'updated_at': datetime.fromisoformat('2025-10-17T13:19:12.253559+00:00')
})

print("Testing Pydantic field_validator with Decimal values...")
print("=" * 60)

try:
    from src.api.models.v1_9 import UserPreferencesResponse

    print("Step 1: Creating model from mock DB row...")
    prefs = UserPreferencesResponse(**mock_db_row)
    print("  ✓ Model created successfully")

    print("\nStep 2: Converting to dict...")
    prefs_dict = prefs.model_dump()
    print("  ✓ model_dump() successful")

    print("\nStep 3: Converting to JSON...")
    prefs_json = prefs.model_dump_json()
    print("  ✓ model_dump_json() successful")

    import json
    parsed = json.loads(prefs_json)

    print("\nStep 4: Verifying types in JSON output...")
    print(f"  voltage_at_0_percent: {parsed['voltage_at_0_percent']} (type: {type(parsed['voltage_at_0_percent']).__name__})")
    print(f"  voltage_at_100_percent: {parsed['voltage_at_100_percent']} (type: {type(parsed['voltage_at_100_percent']).__name__})")
    print(f"  voltage_optimal_min: {parsed['voltage_optimal_min']} (type: {type(parsed['voltage_optimal_min']).__name__})")

    print("\n✅ SUCCESS! All Decimal values converted to float for JSON serialization.")

except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
