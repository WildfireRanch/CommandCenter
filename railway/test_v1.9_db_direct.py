#!/usr/bin/env python3
"""
V1.9 Direct Database Test
Tests preference and miner loading from production database.
Designed to run on Railway with access to postgres_db.railway.internal
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.agents.energy_orchestrator import load_user_preferences
from src.tools.battery_optimizer import BatteryOptimizerTool
from src.tools.miner_coordinator import MinerCoordinatorTool
from src.services.voltage_soc_converter import get_converter

def test_preference_loading():
    """Test loading preferences from production database."""
    print("=" * 70)
    print("TEST 1: Load User Preferences from Database")
    print("=" * 70)

    try:
        prefs = load_user_preferences()

        if not prefs:
            print("❌ FAIL: No preferences loaded")
            return False

        print(f"\n✅ SUCCESS: Loaded {len(prefs)} preference fields")
        print("\n📊 Preference Values:")
        print("-" * 70)

        # Display key voltage thresholds
        key_fields = [
            'voltage_at_0_percent',
            'voltage_at_100_percent',
            'voltage_critical_low',
            'voltage_low',
            'voltage_restart',
            'voltage_optimal_min',
            'voltage_optimal_max',
            'operating_mode',
            'timezone'
        ]

        for field in key_fields:
            value = prefs.get(field, 'N/A')
            print(f"  {field:30s} = {value}")

        print("\n✅ Preference loading test complete\n")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_battery_optimizer_with_db_prefs():
    """Test Battery Optimizer with database preferences."""
    print("=" * 70)
    print("TEST 2: Battery Optimizer with Database Preferences")
    print("=" * 70)

    try:
        # Load preferences from DB
        prefs = load_user_preferences()
        converter = get_converter(prefs)

        # Create tool
        tool = BatteryOptimizerTool(
            user_preferences=prefs,
            voltage_converter=converter
        )

        # Test with sample voltage
        test_voltage = 52.3
        print(f"\n📊 Test voltage: {test_voltage}V")
        print("-" * 70)

        result = tool._run(test_voltage, 8450, 1850)
        print(result)

        print("\n✅ Battery Optimizer test complete\n")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_miner_coordinator_with_db():
    """Test Miner Coordinator with database miner profiles."""
    print("=" * 70)
    print("TEST 3: Miner Coordinator with Database Profiles")
    print("=" * 70)

    try:
        # Load preferences from DB
        prefs = load_user_preferences()
        converter = get_converter(prefs)

        # Create tool
        tool = MinerCoordinatorTool(
            user_preferences=prefs,
            voltage_converter=converter
        )

        # Test with sample telemetry
        print("\n📊 Test telemetry: Voltage=52.3V, Solar=8450W, Load=1850W")
        print("-" * 70)

        result = tool._run(52.3, 8450, 1850)
        print(result)

        # Check if miners were loaded
        miners = tool._load_miners()
        print(f"\n📊 Found {len(miners)} active miner profiles in database")

        if miners:
            print("\n🤖 Miner Profiles:")
            print("-" * 70)
            for miner in miners:
                print(f"  [P{miner['priority_level']}] {miner['name']} ({miner['model']}) - {miner['power_draw_watts']}W")

        print("\n✅ Miner Coordinator test complete\n")
        return True

    except Exception as e:
        print(f"❌ FAIL: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all database integration tests."""
    print("\n" + "=" * 70)
    print("🚀 V1.9 DATABASE INTEGRATION TEST SUITE")
    print("=" * 70)
    print("ℹ️  This test requires access to postgres_db.railway.internal")
    print("=" * 70)
    print()

    results = []

    # Test 1: Preference Loading
    try:
        results.append(("Preference Loading", test_preference_loading()))
    except Exception as e:
        print(f"❌ Preference loading test crashed: {e}")
        results.append(("Preference Loading", False))

    # Test 2: Battery Optimizer with DB Prefs
    try:
        results.append(("Battery Optimizer + DB", test_battery_optimizer_with_db_prefs()))
    except Exception as e:
        print(f"❌ Battery Optimizer test crashed: {e}")
        results.append(("Battery Optimizer + DB", False))

    # Test 3: Miner Coordinator with DB
    try:
        results.append(("Miner Coordinator + DB", test_miner_coordinator_with_db()))
    except Exception as e:
        print(f"❌ Miner Coordinator test crashed: {e}")
        results.append(("Miner Coordinator + DB", False))

    # Summary
    print("=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")

    all_passed = all(result[1] for result in results)

    print("=" * 70)
    if all_passed:
        print("🎉 ALL DATABASE TESTS PASSED")
        print("\n✅ V1.9 agent integration verified with production database!")
        return 0
    else:
        print("⚠️  SOME DATABASE TESTS FAILED")
        print("\nℹ️  This may be expected if:")
        print("   - Running locally without Railway network access")
        print("   - Database credentials not configured")
        print("   - No miner profiles configured in database yet")
        return 1


if __name__ == "__main__":
    sys.exit(main())
