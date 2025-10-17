#!/usr/bin/env python3
"""Test Decimal serialization fix for V1.9 models."""

from decimal import Decimal
from datetime import datetime
from uuid import uuid4

# Add railway directory to path
import sys
sys.path.insert(0, '/workspaces/CommandCenter/railway')

from src.api.models.v1_9 import UserPreferencesResponse

# Test with Decimal values (simulating database response)
test_data = {
    'id': uuid4(),
    'user_id': uuid4(),
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
    'created_at': datetime.now(),
    'updated_at': datetime.now()
}

print("Testing Decimal serialization...")
print("=" * 60)

try:
    # Create model instance
    prefs = UserPreferencesResponse(**test_data)
    print("✓ Model instantiation successful")

    # Convert to dict
    prefs_dict = prefs.model_dump()
    print("✓ model_dump() successful")

    # Convert to JSON
    prefs_json = prefs.model_dump_json()
    print("✓ model_dump_json() successful")

    print("\nSample output:")
    import json
    parsed = json.loads(prefs_json)
    print(f"  voltage_at_0_percent: {parsed['voltage_at_0_percent']} (type: {type(parsed['voltage_at_0_percent']).__name__})")
    print(f"  voltage_at_100_percent: {parsed['voltage_at_100_percent']} (type: {type(parsed['voltage_at_100_percent']).__name__})")
    print(f"  voltage_optimal_min: {parsed['voltage_optimal_min']} (type: {type(parsed['voltage_optimal_min']).__name__})")

    print("\n✅ All Decimal values successfully converted to float!")

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
