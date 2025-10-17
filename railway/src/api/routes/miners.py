# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/routes/miners.py
# PURPOSE: Miner profiles API routes (V1.9)
#
# WHAT IT DOES:
#   - Manages miner profiles for priority-based power allocation
#   - Provides full CRUD operations (Create, Read, Update, Delete)
#   - Validates voltage thresholds and priority levels
#
# ENDPOINTS:
#   GET    /api/miners           - List all miner profiles
#   POST   /api/miners           - Create new miner profile
#   GET    /api/miners/{id}      - Get single miner profile
#   PUT    /api/miners/{id}      - Update miner profile
#   DELETE /api/miners/{id}      - Delete miner profile
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Path
from typing import List
from uuid import UUID
import logging
import os

from ...utils.db import get_connection, query_all, query_one, execute
from ..models.v1_9 import (
    MinerProfileResponse,
    MinerProfileBase,
    MinerProfileUpdate
)
from .constants import ALLOWED_MINER_FIELDS

router = APIRouter(prefix="/miners", tags=["miners"])
logger = logging.getLogger(__name__)

# Default user ID for V1.9 (single-user system)
# SECURITY: Load from environment variable (set in Railway)
DEFAULT_USER_ID = os.getenv(
    "DEFAULT_USER_ID",
    "a0000000-0000-0000-0000-000000000001"  # Fallback for local dev
)


@router.get("", response_model=List[MinerProfileResponse])
async def list_miners():
    """
    List all miner profiles ordered by priority (1=highest).

    Returns array of miner profiles with complete configuration.

    Example response:
    ```json
    [
        {
            "id": "uuid",
            "name": "Primary S21+ (Revenue)",
            "model": "Antminer S21+ 235TH",
            "priority_level": 1,
            "start_voltage": 50.0,
            "stop_voltage": 47.0,
            "require_excess_solar": false,
            "enabled": true
        },
        {
            "id": "uuid",
            "name": "Dump Load S19 #1",
            "model": "Antminer S19 95TH",
            "priority_level": 3,
            "start_voltage": 54.5,
            "require_excess_solar": true,
            "enabled": true
        }
    ]
    ```
    """
    try:
        with get_connection() as conn:
            miners = query_all(
                conn,
                """
                SELECT
                    id, user_id, name, model, hashrate_ths, power_draw_watts,
                    priority_level, operating_mode,
                    start_voltage, stop_voltage, emergency_stop_voltage,
                    start_hysteresis_minutes, stop_hysteresis_minutes,
                    require_excess_solar, minimum_excess_watts, maximum_runtime_hours,
                    prefer_time_start, prefer_time_end, allow_outside_schedule,
                    require_sunny_weather, minimum_solar_production_watts,
                    enabled, control_method, device_identifier,
                    created_at, updated_at
                FROM miner_profiles
                WHERE user_id = %s::uuid
                ORDER BY priority_level ASC, name ASC
                """,
                (DEFAULT_USER_ID,),
                as_dict=True
            )

            return miners

    except Exception as e:
        logger.exception(f"Failed to list miners: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list miners: {str(e)}"
        )


@router.post("", response_model=MinerProfileResponse, status_code=201)
async def create_miner(miner: MinerProfileBase):
    """
    Create a new miner profile.

    Validates voltage thresholds (emergency_stop < stop < start)
    and priority level (1-10).

    Example request:
    ```json
    {
        "name": "Secondary S19 Pro",
        "model": "Antminer S19 Pro 110TH",
        "hashrate_ths": 110.0,
        "power_draw_watts": 3250,
        "priority_level": 2,
        "operating_mode": "balanced",
        "start_voltage": 52.0,
        "stop_voltage": 49.0,
        "emergency_stop_voltage": 47.0,
        "require_excess_solar": false,
        "enabled": true,
        "control_method": "shelly",
        "device_identifier": "192.168.1.100"
    }
    ```

    Returns the created miner profile with ID and timestamps.
    """
    try:
        with get_connection() as conn:
            # Insert new miner
            new_miner = query_one(
                conn,
                """
                INSERT INTO miner_profiles (
                    user_id, name, model, hashrate_ths, power_draw_watts,
                    priority_level, operating_mode,
                    start_voltage, stop_voltage, emergency_stop_voltage,
                    start_hysteresis_minutes, stop_hysteresis_minutes,
                    require_excess_solar, minimum_excess_watts, maximum_runtime_hours,
                    prefer_time_start, prefer_time_end, allow_outside_schedule,
                    require_sunny_weather, minimum_solar_production_watts,
                    enabled, control_method, device_identifier
                ) VALUES (
                    %s::uuid, %s, %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s,
                    %s, %s, %s,
                    %s, %s,
                    %s, %s, %s
                )
                RETURNING
                    id, user_id, name, model, hashrate_ths, power_draw_watts,
                    priority_level, operating_mode,
                    start_voltage, stop_voltage, emergency_stop_voltage,
                    start_hysteresis_minutes, stop_hysteresis_minutes,
                    require_excess_solar, minimum_excess_watts, maximum_runtime_hours,
                    prefer_time_start, prefer_time_end, allow_outside_schedule,
                    require_sunny_weather, minimum_solar_production_watts,
                    enabled, control_method, device_identifier,
                    created_at, updated_at
                """,
                (
                    DEFAULT_USER_ID, miner.name, miner.model, miner.hashrate_ths, miner.power_draw_watts,
                    miner.priority_level, miner.operating_mode,
                    miner.start_voltage, miner.stop_voltage, miner.emergency_stop_voltage,
                    miner.start_hysteresis_minutes, miner.stop_hysteresis_minutes,
                    miner.require_excess_solar, miner.minimum_excess_watts, miner.maximum_runtime_hours,
                    miner.prefer_time_start, miner.prefer_time_end, miner.allow_outside_schedule,
                    miner.require_sunny_weather, miner.minimum_solar_production_watts,
                    miner.enabled, miner.control_method, miner.device_identifier
                ),
                as_dict=True
            )

            logger.info(f"Created miner profile: {miner.name} (priority {miner.priority_level})")
            return new_miner

    except Exception as e:
        logger.exception(f"Failed to create miner: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create miner: {str(e)}"
        )


@router.get("/{miner_id}", response_model=MinerProfileResponse)
async def get_miner(
    miner_id: UUID = Path(..., description="Miner profile ID")
):
    """
    Get a single miner profile by ID.

    Returns complete miner configuration.

    Raises:
    - 404: Miner not found
    """
    try:
        with get_connection() as conn:
            miner = query_one(
                conn,
                """
                SELECT
                    id, user_id, name, model, hashrate_ths, power_draw_watts,
                    priority_level, operating_mode,
                    start_voltage, stop_voltage, emergency_stop_voltage,
                    start_hysteresis_minutes, stop_hysteresis_minutes,
                    require_excess_solar, minimum_excess_watts, maximum_runtime_hours,
                    prefer_time_start, prefer_time_end, allow_outside_schedule,
                    require_sunny_weather, minimum_solar_production_watts,
                    enabled, control_method, device_identifier,
                    created_at, updated_at
                FROM miner_profiles
                WHERE id = %s::uuid AND user_id = %s::uuid
                """,
                (str(miner_id), DEFAULT_USER_ID),
                as_dict=True
            )

            if not miner:
                raise HTTPException(
                    status_code=404,
                    detail=f"Miner profile {miner_id} not found"
                )

            return miner

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get miner: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get miner: {str(e)}"
        )


@router.put("/{miner_id}", response_model=MinerProfileResponse)
async def update_miner(
    updates: MinerProfileUpdate,
    miner_id: UUID = Path(..., description="Miner profile ID")
):
    """
    Update a miner profile.

    Only updates fields that are provided in the request body.
    All fields are optional.

    Example request:
    ```json
    {
        "start_voltage": 51.0,
        "stop_voltage": 48.0,
        "enabled": false
    }
    ```

    Returns the updated miner profile.

    Raises:
    - 404: Miner not found
    - 400: Invalid voltage ranges or priority
    """
    try:
        # Build dynamic UPDATE query from provided fields
        update_data = updates.model_dump(exclude_unset=True)
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields to update"
            )

        # SECURITY: Validate fields against whitelist (prevent SQL injection)
        for field in update_data.keys():
            if field not in ALLOWED_MINER_FIELDS:
                raise HTTPException(
                    status_code=400,
                    detail=f"Field '{field}' is not allowed for updates"
                )

        # Build SET clause
        set_clauses = []
        values = []
        for field, value in update_data.items():
            set_clauses.append(f"{field} = %s")
            values.append(value)

        # Add updated_at timestamp
        set_clauses.append("updated_at = NOW()")

        # Add miner_id and user_id for WHERE clause
        values.extend([str(miner_id), DEFAULT_USER_ID])

        with get_connection() as conn:
            # PERFORMANCE: Single query with RETURNING (instead of UPDATE + SELECT)
            updated_miner = query_one(
                conn,
                f"""
                UPDATE miner_profiles
                SET {', '.join(set_clauses)}
                WHERE id = %s::uuid AND user_id = %s::uuid
                RETURNING
                    id, user_id, name, model, hashrate_ths, power_draw_watts,
                    priority_level, operating_mode,
                    start_voltage, stop_voltage, emergency_stop_voltage,
                    start_hysteresis_minutes, stop_hysteresis_minutes,
                    require_excess_solar, minimum_excess_watts, maximum_runtime_hours,
                    prefer_time_start, prefer_time_end, allow_outside_schedule,
                    require_sunny_weather, minimum_solar_production_watts,
                    enabled, control_method, device_identifier,
                    created_at, updated_at
                """,
                tuple(values),
                as_dict=True
            )

            if not updated_miner:
                raise HTTPException(
                    status_code=404,
                    detail=f"Miner profile {miner_id} not found"
                )

            logger.info(f"Updated miner {miner_id}: {list(update_data.keys())}")
            return updated_miner

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update miner: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update miner: {str(e)}"
        )


@router.delete("/{miner_id}", status_code=204)
async def delete_miner(
    miner_id: UUID = Path(..., description="Miner profile ID")
):
    """
    Delete a miner profile.

    Permanently removes the miner profile from the database.
    This action cannot be undone.

    Returns 204 No Content on success.

    Raises:
    - 404: Miner not found
    """
    try:
        with get_connection() as conn:
            # Check if miner exists
            miner = query_one(
                conn,
                "SELECT id FROM miner_profiles WHERE id = %s::uuid AND user_id = %s::uuid",
                (str(miner_id), DEFAULT_USER_ID),
                as_dict=True
            )

            if not miner:
                raise HTTPException(
                    status_code=404,
                    detail=f"Miner profile {miner_id} not found"
                )

            # Delete miner
            execute(
                conn,
                "DELETE FROM miner_profiles WHERE id = %s::uuid AND user_id = %s::uuid",
                (str(miner_id), DEFAULT_USER_ID)
            )

            logger.info(f"Deleted miner profile {miner_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete miner: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete miner: {str(e)}"
        )
