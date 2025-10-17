# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/routes/hvac.py
# PURPOSE: HVAC zones API routes (V1.9)
#
# WHAT IT DOES:
#   - Manages HVAC zones for temperature-based climate control
#   - Provides full CRUD operations (Create, Read, Update, Delete)
#   - Validates temperature thresholds
#
# ENDPOINTS:
#   GET    /api/hvac/zones           - List all HVAC zones
#   POST   /api/hvac/zones           - Create new HVAC zone
#   GET    /api/hvac/zones/{id}      - Get single HVAC zone
#   PUT    /api/hvac/zones/{id}      - Update HVAC zone
#   DELETE /api/hvac/zones/{id}      - Delete HVAC zone
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Path
from typing import List
from uuid import UUID
import logging

from ...utils.db import get_connection, query_all, query_one, execute
from ..models.v1_9 import (
    HVACZoneResponse,
    HVACZoneBase,
    HVACZoneUpdate
)

router = APIRouter(prefix="/hvac/zones", tags=["hvac"])
logger = logging.getLogger(__name__)

# Default user ID for V1.9 (single-user system)
DEFAULT_USER_ID = "a0000000-0000-0000-0000-000000000001"


@router.get("", response_model=List[HVACZoneResponse])
async def list_zones():
    """
    List all HVAC zones.

    Returns array of zone configurations with temperature thresholds
    and device settings.

    Example response:
    ```json
    [
        {
            "id": "uuid",
            "zone_name": "Heat Room",
            "zone_type": "equipment",
            "temp_too_hot": 40.0,
            "temp_hot_ok": 35.0,
            "temp_too_cold": 0.0,
            "temp_cold_ok": 5.0,
            "exhaust_fan_enabled": true,
            "exhaust_fan_device_id": "ac_infinity_1",
            "heating_enabled": true,
            "heating_priority_1": "miner",
            "heating_priority_2": "heater",
            "enabled": true
        }
    ]
    ```
    """
    try:
        with get_connection() as conn:
            zones = query_all(
                conn,
                """
                SELECT
                    id, user_id, zone_name, zone_type,
                    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
                    exhaust_fan_enabled, exhaust_fan_device_id,
                    exhaust_fan_speed_auto, exhaust_fan_max_speed,
                    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
                    only_heat_when_solar, minimum_solar_for_heating_watts,
                    block_charging_below_temp,
                    enabled, temperature_sensor_id,
                    created_at, updated_at
                FROM hvac_zones
                WHERE user_id = %s::uuid
                ORDER BY zone_name ASC
                """,
                (DEFAULT_USER_ID,),
                as_dict=True
            )

            return zones

    except Exception as e:
        logger.exception(f"Failed to list HVAC zones: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list HVAC zones: {str(e)}"
        )


@router.post("", response_model=HVACZoneResponse, status_code=201)
async def create_zone(zone: HVACZoneBase):
    """
    Create a new HVAC zone.

    Validates temperature thresholds:
    - temp_too_cold < temp_cold_ok
    - temp_hot_ok < temp_too_hot

    Example request:
    ```json
    {
        "zone_name": "Server Room",
        "zone_type": "equipment",
        "temp_too_hot": 30.0,
        "temp_hot_ok": 25.0,
        "temp_too_cold": 10.0,
        "temp_cold_ok": 15.0,
        "exhaust_fan_enabled": true,
        "exhaust_fan_device_id": "ac_infinity_3",
        "exhaust_fan_speed_auto": true,
        "exhaust_fan_max_speed": 10,
        "heating_enabled": false,
        "enabled": true
    }
    ```

    Returns the created zone with ID and timestamps.
    """
    try:
        with get_connection() as conn:
            # Insert new zone
            new_zone = query_one(
                conn,
                """
                INSERT INTO hvac_zones (
                    user_id, zone_name, zone_type,
                    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
                    exhaust_fan_enabled, exhaust_fan_device_id,
                    exhaust_fan_speed_auto, exhaust_fan_max_speed,
                    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
                    only_heat_when_solar, minimum_solar_for_heating_watts,
                    block_charging_below_temp,
                    enabled, temperature_sensor_id
                ) VALUES (
                    %s::uuid, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s, %s, %s,
                    %s, %s,
                    %s,
                    %s, %s
                )
                RETURNING
                    id, user_id, zone_name, zone_type,
                    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
                    exhaust_fan_enabled, exhaust_fan_device_id,
                    exhaust_fan_speed_auto, exhaust_fan_max_speed,
                    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
                    only_heat_when_solar, minimum_solar_for_heating_watts,
                    block_charging_below_temp,
                    enabled, temperature_sensor_id,
                    created_at, updated_at
                """,
                (
                    DEFAULT_USER_ID, zone.zone_name, zone.zone_type,
                    zone.temp_too_hot, zone.temp_hot_ok, zone.temp_too_cold, zone.temp_cold_ok,
                    zone.exhaust_fan_enabled, zone.exhaust_fan_device_id,
                    zone.exhaust_fan_speed_auto, zone.exhaust_fan_max_speed,
                    zone.heating_enabled, zone.heating_priority_1, zone.heating_priority_2, zone.heater_device_id,
                    zone.only_heat_when_solar, zone.minimum_solar_for_heating_watts,
                    zone.block_charging_below_temp,
                    zone.enabled, zone.temperature_sensor_id
                ),
                as_dict=True
            )

            logger.info(f"Created HVAC zone: {zone.zone_name}")
            return new_zone

    except Exception as e:
        logger.exception(f"Failed to create HVAC zone: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create HVAC zone: {str(e)}"
        )


@router.get("/{zone_id}", response_model=HVACZoneResponse)
async def get_zone(
    zone_id: UUID = Path(..., description="HVAC zone ID")
):
    """
    Get a single HVAC zone by ID.

    Returns complete zone configuration.

    Raises:
    - 404: Zone not found
    """
    try:
        with get_connection() as conn:
            zone = query_one(
                conn,
                """
                SELECT
                    id, user_id, zone_name, zone_type,
                    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
                    exhaust_fan_enabled, exhaust_fan_device_id,
                    exhaust_fan_speed_auto, exhaust_fan_max_speed,
                    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
                    only_heat_when_solar, minimum_solar_for_heating_watts,
                    block_charging_below_temp,
                    enabled, temperature_sensor_id,
                    created_at, updated_at
                FROM hvac_zones
                WHERE id = %s::uuid AND user_id = %s::uuid
                """,
                (str(zone_id), DEFAULT_USER_ID),
                as_dict=True
            )

            if not zone:
                raise HTTPException(
                    status_code=404,
                    detail=f"HVAC zone {zone_id} not found"
                )

            return zone

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get HVAC zone: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get HVAC zone: {str(e)}"
        )


@router.put("/{zone_id}", response_model=HVACZoneResponse)
async def update_zone(
    updates: HVACZoneUpdate,
    zone_id: UUID = Path(..., description="HVAC zone ID")
):
    """
    Update an HVAC zone.

    Only updates fields that are provided in the request body.
    All fields are optional.

    Example request:
    ```json
    {
        "temp_too_hot": 35.0,
        "temp_hot_ok": 30.0,
        "exhaust_fan_max_speed": 8
    }
    ```

    Returns the updated zone.

    Raises:
    - 404: Zone not found
    - 400: Invalid temperature ranges
    """
    try:
        # Build dynamic UPDATE query from provided fields
        update_data = updates.dict(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )

        # Build SET clause
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        # Add updated_at timestamp
        set_clauses.append("updated_at = NOW()")

        # Add zone_id and user_id for WHERE clause
        values.extend([str(zone_id), DEFAULT_USER_ID])

        with get_connection() as conn:
            # Execute update
            execute(
                conn,
                f"""
                UPDATE hvac_zones
                SET {', '.join(set_clauses)}
                WHERE id = %s::uuid AND user_id = %s::uuid
                """,
                tuple(values)
            )

            # Fetch and return updated zone
            updated_zone = query_one(
                conn,
                """
                SELECT
                    id, user_id, zone_name, zone_type,
                    temp_too_hot, temp_hot_ok, temp_too_cold, temp_cold_ok,
                    exhaust_fan_enabled, exhaust_fan_device_id,
                    exhaust_fan_speed_auto, exhaust_fan_max_speed,
                    heating_enabled, heating_priority_1, heating_priority_2, heater_device_id,
                    only_heat_when_solar, minimum_solar_for_heating_watts,
                    block_charging_below_temp,
                    enabled, temperature_sensor_id,
                    created_at, updated_at
                FROM hvac_zones
                WHERE id = %s::uuid AND user_id = %s::uuid
                """,
                (str(zone_id), DEFAULT_USER_ID),
                as_dict=True
            )

            if not updated_zone:
                raise HTTPException(
                    status_code=404,
                    detail=f"HVAC zone {zone_id} not found"
                )

            logger.info(f"Updated HVAC zone {zone_id}: {list(update_data.keys())}")
            return updated_zone

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update HVAC zone: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update HVAC zone: {str(e)}"
        )


@router.delete("/{zone_id}", status_code=204)
async def delete_zone(
    zone_id: UUID = Path(..., description="HVAC zone ID")
):
    """
    Delete an HVAC zone.

    Permanently removes the zone from the database.
    This action cannot be undone.

    Returns 204 No Content on success.

    Raises:
    - 404: Zone not found
    """
    try:
        with get_connection() as conn:
            # Check if zone exists
            zone = query_one(
                conn,
                "SELECT id FROM hvac_zones WHERE id = %s::uuid AND user_id = %s::uuid",
                (str(zone_id), DEFAULT_USER_ID),
                as_dict=True
            )

            if not zone:
                raise HTTPException(
                    status_code=404,
                    detail=f"HVAC zone {zone_id} not found"
                )

            # Delete zone
            execute(
                conn,
                "DELETE FROM hvac_zones WHERE id = %s::uuid AND user_id = %s::uuid",
                (str(zone_id), DEFAULT_USER_ID)
            )

            logger.info(f"Deleted HVAC zone {zone_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete HVAC zone: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete HVAC zone: {str(e)}"
        )
