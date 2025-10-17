#!/usr/bin/env python3
"""
V1.9 Integration Test
Tests the complete agent integration with user preferences.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.battery_optimizer import BatteryOptimizerTool
from src.tools.miner_coordinator import MinerCoordinatorTool
from src.services.voltage_soc_converter import get_converter

def test_battery_optimizer():
    """Test Battery Optimizer with mock preferences."""
    print("=" * 70)
    print("TEST 1: Battery Optimizer Integration")
    print("=" * 70)

    # Mock user preferences
    prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
        'voltage_critical_low': 45.0,
        'voltage_low': 47.0,
        'voltage_optimal_min': 50.0,
        'voltage_optimal_max': 54.5,
        'voltage_restart': 50.0,
    }

    # Create converter
    converter = get_converter(prefs)

    # Create tool
    tool = BatteryOptimizerTool(user_preferences=prefs, voltage_converter=converter)

    # Test scenarios
    test_cases = [
        (52.3, 8450, 1850, "Optimal voltage"),
        (47.0, 5000, 2000, "Low voltage"),
        (45.0, 3000, 1500, "Critical voltage"),
        (55.0, 9000, 1000, "High voltage"),
    ]

    for voltage, solar, load, description in test_cases:
        print(f"\n📊 {description}: {voltage}V, Solar={solar}W, Load={load}W")
        print("-" * 70)
        result = tool._run(voltage, solar, load)
        print(result)

    print("\n✅ Battery Optimizer test complete\n")
    return True


def test_miner_coordinator():
    """Test Miner Coordinator with mock preferences."""
    print("=" * 70)
    print("TEST 2: Miner Coordinator Integration")
    print("=" * 70)

    # Mock user preferences
    prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
    }

    # Create converter
    converter = get_converter(prefs)

    # Create tool
    tool = MinerCoordinatorTool(user_preferences=prefs, voltage_converter=converter)

    # Test scenario (will show "no miners" since DB not available)
    print("\n📊 Test: Voltage=52.3V, Solar=8450W, Load=1850W")
    print("-" * 70)
    result = tool._run(52.3, 8450, 1850)
    print(result)

    print("\n✅ Miner Coordinator test complete")
    print("ℹ️  Note: Shows 'No miners configured' because DB not available locally")
    print("\n")
    return True


def test_voltage_converter():
    """Test voltage-SOC converter."""
    print("=" * 70)
    print("TEST 3: Voltage-SOC Converter")
    print("=" * 70)

    prefs = {
        'voltage_at_0_percent': 45.0,
        'voltage_at_100_percent': 56.0,
        'voltage_curve': None  # Linear
    }

    converter = get_converter(prefs)

    test_voltages = [45.0, 47.0, 50.0, 52.3, 54.5, 56.0]

    print("\n📊 Voltage to SOC conversions:")
    print("-" * 70)
    for voltage in test_voltages:
        soc = converter.voltage_to_soc(voltage)
        print(f"  {voltage:5.1f}V → {soc:5.1f}% SOC")

    print("\n✅ Voltage converter test complete\n")
    return True


def main():
    """Run all integration tests."""
    print("\n" + "=" * 70)
    print("🚀 V1.9 AGENT INTEGRATION TEST SUITE")
    print("=" * 70)
    print()

    results = []

    try:
        results.append(("Voltage Converter", test_voltage_converter()))
    except Exception as e:
        print(f"❌ Voltage Converter test failed: {e}")
        results.append(("Voltage Converter", False))

    try:
        results.append(("Battery Optimizer", test_battery_optimizer()))
    except Exception as e:
        print(f"❌ Battery Optimizer test failed: {e}")
        results.append(("Battery Optimizer", False))

    try:
        results.append(("Miner Coordinator", test_miner_coordinator()))
    except Exception as e:
        print(f"❌ Miner Coordinator test failed: {e}")
        results.append(("Miner Coordinator", False))

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
        print("🎉 ALL TESTS PASSED")
        return 0
    else:
        print("⚠️  SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
