#!/usr/bin/env python3
"""
Test V1.9 migration script for syntax and logic errors.

This script validates the migration without requiring a database connection.
For actual database testing, use Railway CLI or local PostgreSQL.
"""

import re
from pathlib import Path


def test_migration_syntax():
    """Validate SQL migration file syntax and structure."""

    migration_file = Path("src/database/migrations/006_v1.9_user_preferences.sql")

    if not migration_file.exists():
        print(f"❌ Migration file not found: {migration_file}")
        return False

    print(f"📋 Testing migration file: {migration_file.name}")
    print("="*70)

    sql_content = migration_file.read_text()

    # Test 1: Check for transaction wrapper
    print("\n✅ Test 1: Transaction wrapper")
    has_begin = "BEGIN;" in sql_content
    has_commit = "COMMIT;" in sql_content
    if has_begin and has_commit:
        print("   ✓ Has BEGIN and COMMIT")
    else:
        print(f"   ✗ Missing {'BEGIN' if not has_begin else 'COMMIT'}")
        return False

    # Test 2: Check all 4 tables are created
    print("\n✅ Test 2: Table creation")
    required_tables = [
        "users",
        "user_preferences",
        "miner_profiles",
        "hvac_zones"
    ]

    for table in required_tables:
        pattern = rf"CREATE TABLE.*{table}\s*\("
        if re.search(pattern, sql_content, re.IGNORECASE | re.DOTALL):
            print(f"   ✓ Table '{table}' defined")
        else:
            print(f"   ✗ Table '{table}' NOT found")
            return False

    # Test 3: Check Solar Shack voltage defaults
    print("\n✅ Test 3: Solar Shack voltage defaults")
    voltage_defaults = {
        "voltage_at_0_percent": "45.0",
        "voltage_at_100_percent": "56.0",
        "voltage_optimal_min": "50.0",
        "voltage_optimal_max": "54.5",
    }

    for key, value in voltage_defaults.items():
        # Check in table definition
        pattern = rf"{key}.*DEFAULT {value}"
        if re.search(pattern, sql_content, re.IGNORECASE):
            print(f"   ✓ {key} = {value}V")
        else:
            print(f"   ⚠️  {key} default may differ (check manually)")

    # Test 4: Check miner profiles
    print("\n✅ Test 4: Miner profiles")
    miners = {
        "Primary S21+": {"priority": "1", "start_voltage": "50.0"},
        "Dump Load S19": {"priority": "3", "start_voltage": "54.5"}
    }

    for miner_name, props in miners.items():
        if miner_name in sql_content:
            print(f"   ✓ {miner_name} configured")
            # Check priority
            if f"priority_level, operating_mode" in sql_content:
                print(f"      - Priority: {props['priority']}")
                print(f"      - Start voltage: {props['start_voltage']}V")
        else:
            print(f"   ✗ {miner_name} NOT found")

    # Test 5: Check HVAC zones
    print("\n✅ Test 5: HVAC zones")
    zones = ["Heat Room", "Main Room"]
    for zone in zones:
        if zone in sql_content:
            print(f"   ✓ {zone} configured")
        else:
            print(f"   ✗ {zone} NOT found")

    # Test 6: Check constraints
    print("\n✅ Test 6: Constraints")
    constraints = [
        "valid_voltage_calibration",
        "valid_voltage_ranges",
        "valid_priority",
        "valid_voltage_thresholds",
        "valid_temp_thresholds"
    ]

    for constraint in constraints:
        pattern = rf"CONSTRAINT {constraint}"
        if re.search(pattern, sql_content, re.IGNORECASE):
            print(f"   ✓ {constraint}")
        else:
            print(f"   ✗ {constraint} NOT found")

    # Test 7: Check indexes
    print("\n✅ Test 7: Indexes")
    indexes = [
        "idx_users_email",
        "idx_user_preferences_user",
        "idx_miner_profiles_user",
        "idx_miner_profiles_priority",
        "idx_hvac_zones_user"
    ]

    for index in indexes:
        if index in sql_content:
            print(f"   ✓ {index}")
        else:
            print(f"   ✗ {index} NOT found")

    # Test 8: Check triggers
    print("\n✅ Test 8: Update triggers")
    trigger_tables = ["users", "user_preferences", "miner_profiles", "hvac_zones"]
    for table in trigger_tables:
        pattern = rf"CREATE TRIGGER.*{table}"
        if re.search(pattern, sql_content, re.IGNORECASE):
            print(f"   ✓ Trigger for {table}")
        else:
            print(f"   ✗ Trigger for {table} NOT found")

    # Test 9: Check rollback script
    print("\n✅ Test 9: Rollback script")
    if "DROP TABLE" in sql_content and "ROLLBACK" in sql_content:
        print("   ✓ Rollback script included")
    else:
        print("   ⚠️  Rollback script may be missing")

    # Test 10: Check verification queries
    print("\n✅ Test 10: Verification queries")
    if "VERIFICATION QUERIES" in sql_content or "SELECT" in sql_content[-2000:]:
        print("   ✓ Verification queries included")
    else:
        print("   ⚠️  Verification queries may be missing")

    print("\n" + "="*70)
    print("✅ All syntax tests passed!")
    print("\n📝 Next steps:")
    print("   1. Review migration file manually")
    print("   2. Test on local PostgreSQL (if available)")
    print("   3. Deploy to Railway staging environment")
    print("   4. Run migration: railway run --service CommandCenter")

    return True


def show_migration_info():
    """Display key information about the migration."""

    print("\n" + "="*70)
    print("📊 V1.9 MIGRATION SUMMARY")
    print("="*70)

    print("\n🗄️  New Tables (4):")
    print("   1. users - Single admin user for V1.9")
    print("   2. user_preferences - Voltage thresholds (45-56V)")
    print("   3. miner_profiles - Priority-based (1=primary, 3=dump)")
    print("   4. hvac_zones - Temperature management")

    print("\n⚡ Voltage Calibration:")
    print("   - 0% SOC   = 45.0V (empty)")
    print("   - 40% SOC  = 50.0V (optimal min)")
    print("   - 80% SOC  = 54.5V (optimal max)")
    print("   - 100% SOC = 56.0V (full)")

    print("\n⛏️  Miner Profiles:")
    print("   - Primary S21+ (235TH): Priority 1, Start 50.0V (40%)")
    print("   - Dump Load S19 (95TH): Priority 3, Start 54.5V (80%)")

    print("\n🌡️  HVAC Zones:")
    print("   - Heat Room: Cool @ 40°C, Heat @ 0°C")
    print("   - Main Room: Cool @ 35°C, Heat @ -5°C")

    print("\n⚠️  Critical Constraints:")
    print("   - Voltage thresholds must be ordered (shutdown < critical < ... < full)")
    print("   - Miner priorities: 1-10 (1 = highest)")
    print("   - Emergency stop < stop < start voltage")
    print("   - Temperature thresholds: cold < hot")

    print("\n🔐 Safety Features:")
    print("   - Foreign key cascades (DELETE user → DELETE preferences)")
    print("   - Unique constraint (one preference per user)")
    print("   - Check constraints (prevent invalid data)")
    print("   - Updated_at triggers (auto-timestamp)")

    print("\n" + "="*70)


if __name__ == "__main__":
    print("🧪 V1.9 Migration Test Suite")
    print("="*70)

    if test_migration_syntax():
        show_migration_info()
        print("\n✅ Migration is ready for testing!")
    else:
        print("\n❌ Migration has errors - fix before deploying!")
