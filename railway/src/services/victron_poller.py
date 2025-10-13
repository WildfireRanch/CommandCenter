# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/services/victron_poller.py
# PURPOSE: Background polling service for Victron VRM API
#
# WHAT IT DOES:
#   - Polls Victron VRM API every 3 minutes for battery data
#   - Stores readings in victron.battery_readings table
#   - Tracks polling health and API rate limits
#   - Handles errors gracefully without crashing
#
# DEPENDENCIES:
#   - asyncio (background task scheduling)
#   - psycopg2 (database connection)
#   - victron integration (VRM API client)
#
# ENVIRONMENT VARIABLES:
#   - VICTRON_POLL_INTERVAL: Polling interval in seconds (default: 180)
#   - DATABASE_URL: PostgreSQL connection string
#
# USAGE:
#   # In FastAPI app startup:
#   from services.victron_poller import VictronPoller
#
#   poller = VictronPoller()
#   asyncio.create_task(poller.start())
# ═══════════════════════════════════════════════════════════════════════════

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from ..integrations.victron import VictronVRMClient, RateLimitError
from ..utils.db import get_connection, execute

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_POLL_INTERVAL = 180  # 3 minutes (20 requests/hour)
POLL_INTERVAL = int(os.getenv("VICTRON_POLL_INTERVAL", DEFAULT_POLL_INTERVAL))
MAX_CONSECUTIVE_FAILURES = 10  # Alert threshold


# ─────────────────────────────────────────────────────────────────────────────
# VictronPoller Class
# ─────────────────────────────────────────────────────────────────────────────

class VictronPoller:
    """
    Background service for polling Victron VRM API.

    Responsibilities:
    - Poll VRM API every POLL_INTERVAL seconds
    - Store battery data in database
    - Track polling health and failures
    - Respect API rate limits
    - Recover from transient errors
    """

    def __init__(self):
        """Initialize the poller with VRM client and state tracking."""
        self.client: Optional[VictronVRMClient] = None
        self.installation_id = os.getenv("VICTRON_INSTALLATION_ID")
        self.poll_interval = POLL_INTERVAL

        # State tracking
        self.is_running = False
        self.last_poll_attempt: Optional[datetime] = None
        self.last_successful_poll: Optional[datetime] = None
        self.consecutive_failures = 0

        logger.info(f"VictronPoller initialized (interval: {self.poll_interval}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # Main Polling Loop
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self):
        """
        Start the continuous polling loop.

        This runs indefinitely in the background, polling the VRM API
        every POLL_INTERVAL seconds and storing the results.
        """
        logger.info("Starting Victron VRM poller...")
        self.is_running = True

        # Initialize VRM client with API token
        try:
            # Use pre-generated VRM_API_TOKEN instead of username/password
            # The token-based auth works while username/password gets 401 errors
            api_token = os.getenv("VRM_API_TOKEN")
            if not api_token:
                logger.warning("VRM_API_TOKEN not set, falling back to username/password auth")
                self.client = VictronVRMClient()
                await self.client.authenticate()
            else:
                # Use token directly - no need to call authenticate()
                self.client = VictronVRMClient(api_token=api_token)
                logger.info("VRM client initialized with API token")

            logger.info("VRM client authenticated successfully")
        except Exception as e:
            logger.error(f"Failed to initialize VRM client: {e}")
            self.is_running = False
            return

        # Main polling loop
        while self.is_running:
            try:
                await self.poll_and_store()

                # Reset failure counter on success
                if self.consecutive_failures > 0:
                    logger.info("Polling recovered after failures")
                    self.consecutive_failures = 0

            except Exception as e:
                self.consecutive_failures += 1
                logger.error(
                    f"Polling error (failure {self.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}"
                )

                # Alert if too many failures
                if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.critical(
                        f"Victron poller unhealthy: {self.consecutive_failures} consecutive failures"
                    )

                # Update polling status with error
                await self._update_polling_status(error=str(e))

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

        logger.info("Victron poller stopped")

    async def stop(self):
        """Stop the polling loop gracefully."""
        logger.info("Stopping Victron poller...")
        self.is_running = False

        if self.client:
            self.client.close()

    # ─────────────────────────────────────────────────────────────────────────
    # Poll and Store
    # ─────────────────────────────────────────────────────────────────────────

    async def poll_and_store(self) -> Dict[str, Any]:
        """
        Poll VRM API and store battery data in database.

        Returns:
            Dict containing the battery data that was stored

        Raises:
            Exception: If polling or storage fails
        """
        self.last_poll_attempt = datetime.now()

        logger.debug("Polling Victron VRM API...")

        # Ensure we're authenticated
        await self.client.ensure_authenticated()

        # Fetch battery data from VRM API
        try:
            battery_data = await self.client.get_battery_data(
                installation_id=self.installation_id
            )
        except RateLimitError as e:
            logger.error(f"Rate limit exceeded: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch battery data: {e}")
            raise

        # Store in database
        try:
            await self._store_battery_reading(battery_data)
        except Exception as e:
            logger.error(f"Failed to store battery data: {e}")
            raise

        # Update polling status (success)
        self.last_successful_poll = datetime.now()
        await self._update_polling_status()

        logger.info(
            f"Battery data stored: SOC={battery_data.get('soc')}%, "
            f"V={battery_data.get('voltage')}V, "
            f"I={battery_data.get('current')}A"
        )

        return battery_data

    # ─────────────────────────────────────────────────────────────────────────
    # Database Operations
    # ─────────────────────────────────────────────────────────────────────────

    async def _store_battery_reading(self, data: Dict[str, Any]):
        """
        Store battery reading in victron.battery_readings table.

        Args:
            data: Battery data dict from VRM API
        """
        query = """
            INSERT INTO victron.battery_readings (
                timestamp,
                installation_id,
                soc,
                voltage,
                current,
                power,
                state,
                temperature
            ) VALUES (
                NOW(),
                %s, %s, %s, %s, %s, %s, %s
            )
        """

        params = (
            data.get('installation_id'),
            data.get('soc'),
            data.get('voltage'),
            data.get('current'),
            data.get('power'),
            data.get('state'),
            data.get('temperature')
        )

        # Execute in async-safe way
        loop = asyncio.get_event_loop()

        def _execute():
            with get_connection() as conn:
                return execute(conn, query, params, commit=True)

        await loop.run_in_executor(None, _execute)

    async def _update_polling_status(self, error: Optional[str] = None):
        """
        Update victron.polling_status table with latest poll status.

        Args:
            error: Error message if poll failed, None if successful
        """
        # Get rate limit status from client
        rate_limit = self.client.get_rate_limit_status()

        query = """
            UPDATE victron.polling_status
            SET
                last_poll_attempt = %s,
                last_successful_poll = %s,
                last_error = %s,
                requests_this_hour = %s,
                hour_window_start = %s,
                consecutive_failures = %s,
                is_healthy = %s,
                updated_at = NOW()
            WHERE id = 1
        """

        params = (
            self.last_poll_attempt,
            self.last_successful_poll,
            error,
            rate_limit['requests_used'],
            rate_limit['window_start'],
            self.consecutive_failures,
            self.consecutive_failures < MAX_CONSECUTIVE_FAILURES
        )

        # Execute in async-safe way
        loop = asyncio.get_event_loop()

        def _execute():
            with get_connection() as conn:
                return execute(conn, query, params, commit=True)

        await loop.run_in_executor(None, _execute)

    # ─────────────────────────────────────────────────────────────────────────
    # Health Status
    # ─────────────────────────────────────────────────────────────────────────

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get current poller health status.

        Returns:
            Dict with poller status information
        """
        return {
            'is_running': self.is_running,
            'last_poll_attempt': self.last_poll_attempt.isoformat() if self.last_poll_attempt else None,
            'last_successful_poll': self.last_successful_poll.isoformat() if self.last_successful_poll else None,
            'consecutive_failures': self.consecutive_failures,
            'is_healthy': self.consecutive_failures < MAX_CONSECUTIVE_FAILURES,
            'poll_interval_seconds': self.poll_interval,
            'rate_limit': self.client.get_rate_limit_status() if self.client else None
        }


# ─────────────────────────────────────────────────────────────────────────────
# Global Poller Instance
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance for the application
_poller_instance: Optional[VictronPoller] = None


def get_poller() -> VictronPoller:
    """
    Get the global VictronPoller instance.

    Returns:
        VictronPoller instance
    """
    global _poller_instance

    if _poller_instance is None:
        _poller_instance = VictronPoller()

    return _poller_instance


async def start_poller():
    """Start the global poller instance."""
    poller = get_poller()
    await poller.start()


async def stop_poller():
    """Stop the global poller instance."""
    global _poller_instance

    if _poller_instance:
        await _poller_instance.stop()
        _poller_instance = None


# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test the poller
    import asyncio

    async def test():
        """Test the poller for one iteration."""
        poller = VictronPoller()

        # Do one poll
        data = await poller.poll_and_store()
        print(f"Battery data: {data}")

        # Check health
        health = poller.get_health_status()
        print(f"Health: {health}")

        # Cleanup
        await poller.stop()

    asyncio.run(test())
