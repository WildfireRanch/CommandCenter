# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/utils/solark_storage.py
# PURPOSE: Store SolArk energy data in TimescaleDB
#
# WHAT IT DOES:
#   - Saves real-time SolArk data to database
#   - Queries historical energy data
#   - Provides time-series analysis utilities
#
# DEPENDENCIES:
#   - psycopg2 (PostgreSQL adapter)
#   - utils.db (database utilities)
#
# USAGE:
#   from utils.solark_storage import save_plant_flow, get_recent_data
#
#   # Save current status
#   save_plant_flow(status_dict)
#
#   # Get last hour of data
#   data = get_recent_data(hours=1)
# ═══════════════════════════════════════════════════════════════════════════

import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from psycopg2.extras import Json
from .db import get_connection, query_one, query_all, execute


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_PLANT_ID = int(os.getenv("SOLARK_PLANT_ID", "146453"))


# ─────────────────────────────────────────────────────────────────────────────
# Data Storage
# ─────────────────────────────────────────────────────────────────────────────

def save_plant_flow(
    status: Dict[str, Any],
    plant_id: Optional[int] = None
) -> int:
    """
    Save SolArk plant flow data to database.

    Args:
        status: Status dict from get_solark_status() or fetch_plant_flow()
        plant_id: Plant ID (defaults to SOLARK_PLANT_ID env var)

    Returns:
        int: ID of the inserted record

    Example:
        >>> from tools.solark import get_solark_status
        >>> status = get_solark_status()
        >>> record_id = save_plant_flow(status)
        >>> print(f"Saved as record {record_id}")
    """
    if plant_id is None:
        plant_id = DEFAULT_PLANT_ID

    # Get raw data if available, otherwise use the status dict
    raw_data = status.get("raw", status)

    # Extract all fields from raw data
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO solark.plant_flow (
                plant_id,
                pv_power,
                batt_power,
                grid_power,
                load_power,
                gen_power,
                min_power,
                soc,
                pv_to_load,
                pv_to_grid,
                pv_to_bat,
                bat_to_load,
                grid_to_load,
                gen_to_load,
                exists_gen,
                exists_min,
                gen_on,
                micro_on,
                exists_meter,
                bms_comm_fault_flag,
                pv_details,
                exist_think_power,
                raw_json
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s
            ) RETURNING id
            """,
            (
                plant_id,
                raw_data.get("pvPower", 0),
                raw_data.get("battPower", 0),
                raw_data.get("gridOrMeterPower", 0),
                raw_data.get("loadOrEpsPower", 0),
                raw_data.get("genPower", 0),
                raw_data.get("minPower", 0),
                raw_data.get("soc", 0),
                raw_data.get("pvTo", False),
                raw_data.get("toGrid", False),
                raw_data.get("toBat", False),
                raw_data.get("batTo", False),
                raw_data.get("gridTo", False),
                raw_data.get("genTo", False),
                raw_data.get("existsGen", False),
                raw_data.get("existsMin", False),
                raw_data.get("genOn", False),
                raw_data.get("microOn", False),
                raw_data.get("existsMeter", False),
                raw_data.get("bmsCommFaultFlag", False),
                raw_data.get("pv"),
                raw_data.get("existThinkPower", False),
                Json(raw_data)
            )
        )

        record_id = cursor.fetchone()[0]
        conn.commit()

    return record_id


# ─────────────────────────────────────────────────────────────────────────────
# Data Retrieval
# ─────────────────────────────────────────────────────────────────────────────

def get_recent_data(
    hours: int = 1,
    plant_id: Optional[int] = None,
    limit: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Get recent plant flow data from database.

    Args:
        hours: Number of hours to look back (default: 1)
        plant_id: Plant ID to filter by (defaults to SOLARK_PLANT_ID)
        limit: Maximum number of records to return

    Returns:
        List of plant flow records, ordered by most recent first

    Example:
        >>> data = get_recent_data(hours=24)
        >>> print(f"Got {len(data)} records from last 24 hours")
    """
    if plant_id is None:
        plant_id = DEFAULT_PLANT_ID

    since = datetime.utcnow() - timedelta(hours=hours)

    with get_connection() as conn:
        query = """
            SELECT
                id,
                plant_id,
                created_at,
                pv_power,
                batt_power,
                grid_power,
                load_power,
                soc,
                pv_to_load,
                pv_to_grid,
                pv_to_bat,
                bat_to_load,
                grid_to_load
            FROM solark.plant_flow
            WHERE plant_id = %s AND created_at >= %s
            ORDER BY created_at DESC
        """

        params = [plant_id, since]

        if limit:
            query += " LIMIT %s"
            params.append(limit)

        return query_all(conn, query, tuple(params))


def get_latest_snapshot(plant_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """
    Get the most recent plant flow snapshot.

    Args:
        plant_id: Plant ID (defaults to SOLARK_PLANT_ID)

    Returns:
        Dict with latest data, or None if no data exists

    Example:
        >>> latest = get_latest_snapshot()
        >>> if latest:
        ...     print(f"Latest SOC: {latest['soc']}%")
    """
    if plant_id is None:
        plant_id = DEFAULT_PLANT_ID

    with get_connection() as conn:
        return query_one(
            conn,
            """
            SELECT
                id,
                plant_id,
                created_at,
                pv_power,
                batt_power,
                grid_power,
                load_power,
                soc,
                pv_to_load,
                pv_to_grid,
                pv_to_bat,
                bat_to_load,
                grid_to_load
            FROM solark.plant_flow
            WHERE plant_id = %s
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (plant_id,)
        )


def get_energy_stats(
    hours: int = 24,
    plant_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Get aggregated energy statistics for a time period.

    Args:
        hours: Number of hours to analyze (default: 24)
        plant_id: Plant ID (defaults to SOLARK_PLANT_ID)

    Returns:
        Dict with statistics:
            - avg_soc: Average battery state of charge
            - max_pv_power: Peak solar production
            - avg_load_power: Average load consumption
            - total_records: Number of data points

    Example:
        >>> stats = get_energy_stats(hours=24)
        >>> print(f"24h avg SOC: {stats['avg_soc']:.1f}%")
        >>> print(f"Peak solar: {stats['max_pv_power']}W")
    """
    if plant_id is None:
        plant_id = DEFAULT_PLANT_ID

    since = datetime.utcnow() - timedelta(hours=hours)

    with get_connection() as conn:
        result = query_one(
            conn,
            """
            SELECT
                AVG(soc) as avg_soc,
                MIN(soc) as min_soc,
                MAX(soc) as max_soc,
                MAX(pv_power) as max_pv_power,
                AVG(pv_power) as avg_pv_power,
                AVG(load_power) as avg_load_power,
                MAX(load_power) as max_load_power,
                COUNT(*) as total_records
            FROM solark.plant_flow
            WHERE plant_id = %s AND created_at >= %s
            """,
            (plant_id, since)
        )

    return result or {}


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test SolArk data storage."""
    print("🔍 Testing SolArk data storage...\n")

    # Test 1: Save current data
    print("📊 Fetching and saving current SolArk data...")
    try:
        from ..tools.solark import get_solark_status

        status = get_solark_status()
        record_id = save_plant_flow(status)
        print(f"✅ Saved record {record_id}")
        print(f"   SOC: {status['soc']}%")
        print(f"   PV: {status['pv_power']}W")
    except Exception as e:
        print(f"⚠️  Could not save data: {e}")

    # Test 2: Retrieve recent data
    print("\n📖 Retrieving last hour of data...")
    data = get_recent_data(hours=1, limit=5)
    print(f"✅ Found {len(data)} records")
    for record in data[:3]:
        print(f"   {record['created_at']}: SOC={record['soc']}% PV={record['pv_power']}W")

    # Test 3: Get latest snapshot
    print("\n📸 Latest snapshot:")
    latest = get_latest_snapshot()
    if latest:
        print(f"✅ {latest['created_at']}")
        print(f"   SOC: {latest['soc']}%")
        print(f"   PV: {latest['pv_power']}W")

    # Test 4: Get stats
    print("\n📈 24-hour statistics:")
    stats = get_energy_stats(hours=24)
    if stats.get('total_records', 0) > 0:
        print(f"✅ Based on {stats['total_records']} records")
        print(f"   Avg SOC: {stats['avg_soc']:.1f}%")
        print(f"   Peak Solar: {stats['max_pv_power']}W")
        print(f"   Avg Load: {stats['avg_load_power']:.0f}W")
    else:
        print("⚠️  No data available yet")

    print("\n✅ All tests passed!")
