# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/routes/preferences.py
# PURPOSE: User preferences API routes (V1.9)
#
# WHAT IT DOES:
#   - Manages user preferences for voltage-based battery management
#   - Provides GET, PUT, and RESET endpoints
#   - Validates voltage thresholds and ranges
#
# ENDPOINTS:
#   GET  /api/preferences      - Get current user preferences
#   PUT  /api/preferences      - Update user preferences
#   POST /api/preferences/reset - Reset preferences to defaults
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from ...utils.db import get_connection, query_one, execute
from ..models.v1_9 import (
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserPreferencesBase
)

router = APIRouter(prefix="/preferences", tags=["preferences"])
logger = logging.getLogger(__name__)

# Default user ID for V1.9 (single-user system)
DEFAULT_USER_ID = "a0000000-0000-0000-0000-000000000001"


@router.get("", response_model=UserPreferencesResponse)
async def get_preferences():
    """
    Get current user preferences.

    Returns voltage calibration, operating thresholds, and system settings.
    For V1.9, this returns preferences for the default admin user.

    Example response:
    ```json
    {
        "id": "uuid",
        "user_id": "uuid",
        "voltage_at_0_percent": 45.0,
        "voltage_at_100_percent": 56.0,
        "voltage_optimal_min": 50.0,
        "voltage_optimal_max": 54.5,
        "timezone": "America/Los_Angeles",
        "operating_mode": "balanced",
        "created_at": "2025-10-17T00:00:00Z",
        "updated_at": "2025-10-17T00:00:00Z"
    }
    ```
    """
    try:
        with get_connection() as conn:
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
                raise HTTPException(
                    status_code=404,
                    detail="User preferences not found. Run /db/init-schema to create default preferences."
                )

            return prefs

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to get preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get preferences: {str(e)}"
        )


@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(updates: UserPreferencesUpdate):
    """
    Update user preferences.

    Only updates fields that are provided in the request body.
    All fields are optional.

    Example request:
    ```json
    {
        "voltage_optimal_min": 51.0,
        "voltage_optimal_max": 55.0,
        "operating_mode": "aggressive"
    }
    ```

    Returns updated preferences object.

    Raises:
    - 404: Preferences not found
    - 400: Invalid voltage ranges or thresholds
    - 500: Database error
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

        # Add user_id for WHERE clause
        values.append(DEFAULT_USER_ID)

        with get_connection() as conn:
            # Execute update
            execute(
                conn,
                f"""
                UPDATE user_preferences
                SET {', '.join(set_clauses)}
                WHERE user_id = %s::uuid
                """,
                tuple(values)
            )

            # Fetch and return updated preferences
            updated_prefs = query_one(
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

            if not updated_prefs:
                raise HTTPException(
                    status_code=404,
                    detail="Preferences not found after update"
                )

            logger.info(f"Updated preferences: {list(update_data.keys())}")
            return updated_prefs

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Failed to update preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.post("/reset", response_model=UserPreferencesResponse)
async def reset_preferences():
    """
    Reset user preferences to Solar Shack defaults.

    This will restore:
    - Voltage calibration: 45V = 0%, 56V = 100%
    - Optimal range: 50.0V (40%) to 54.5V (80%)
    - All voltage thresholds to factory defaults
    - Timezone: America/Los_Angeles
    - Operating mode: balanced

    Returns the reset preferences object.
    """
    try:
        with get_connection() as conn:
            # Reset to defaults (same as migration defaults)
            execute(
                conn,
                """
                UPDATE user_preferences
                SET
                    voltage_at_0_percent = 45.0,
                    voltage_at_100_percent = 56.0,
                    voltage_curve = '[
                        {"soc": 0,   "voltage": 45.0},
                        {"soc": 15,  "voltage": 47.0},
                        {"soc": 40,  "voltage": 50.0},
                        {"soc": 60,  "voltage": 52.0},
                        {"soc": 80,  "voltage": 54.5},
                        {"soc": 100, "voltage": 56.0}
                    ]'::jsonb,
                    battery_chemistry = 'LiFePO4',
                    battery_nominal_voltage = 51.2,
                    battery_absolute_min = 43.0,
                    battery_absolute_max = 58.8,
                    voltage_shutdown = 44.0,
                    voltage_critical_low = 45.0,
                    voltage_low = 47.0,
                    voltage_restart = 50.0,
                    voltage_optimal_min = 50.0,
                    voltage_optimal_max = 54.5,
                    voltage_float = 54.0,
                    voltage_absorption = 57.6,
                    voltage_full = 56.0,
                    user_prefers_soc_display = true,
                    use_custom_soc_mapping = true,
                    display_units = 'metric',
                    timezone = 'America/Los_Angeles',
                    location_lat = 37.3382,
                    location_lon = -121.8863,
                    operating_mode = 'balanced',
                    grid_import_allowed = false,
                    updated_at = NOW()
                WHERE user_id = %s::uuid
                """,
                (DEFAULT_USER_ID,)
            )

            # Fetch and return reset preferences
            reset_prefs = query_one(
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

            logger.info("Preferences reset to defaults")
            return reset_prefs

    except Exception as e:
        logger.exception(f"Failed to reset preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reset preferences: {str(e)}"
        )
