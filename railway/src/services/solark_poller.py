# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/services/solark_poller.py
# PURPOSE: Background polling service for SolArk inverter data
#
# WHAT IT DOES:
#   - Polls SolArk API every 3 minutes for real-time energy data
#   - Stores readings in solark.plant_flow table
#   - Provides continuous time-series data for analytics
#   - Handles errors gracefully without crashing
#
# DEPENDENCIES:
#   - asyncio (background task scheduling)
#   - psycopg2 (database connection)
#   - tools.solark (SolArk API client)
#
# ENVIRONMENT VARIABLES:
#   - SOLARK_POLL_INTERVAL: Polling interval in seconds (default: 60)
#   - DATABASE_URL: PostgreSQL connection string
#
# USAGE:
#   # In FastAPI app startup:
#   from services.solark_poller import SolArkPoller
#
#   poller = SolArkPoller()
#   asyncio.create_task(poller.start())
# ═══════════════════════════════════════════════════════════════════════════

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_POLL_INTERVAL = 180  # 3 minutes (480 records/day)
POLL_INTERVAL = int(os.getenv("SOLARK_POLL_INTERVAL", DEFAULT_POLL_INTERVAL))
MAX_CONSECUTIVE_FAILURES = 10  # Alert threshold


# ─────────────────────────────────────────────────────────────────────────────
# SolArkPoller Class
# ─────────────────────────────────────────────────────────────────────────────

class SolArkPoller:
    """
    Background service for polling SolArk inverter API.

    Responsibilities:
    - Poll SolArk API every POLL_INTERVAL seconds
    - Store energy data in database (via get_solark_status)
    - Track polling health and failures
    - Recover from transient errors
    """

    def __init__(self):
        """Initialize the poller with state tracking."""
        self.poll_interval = POLL_INTERVAL

        # State tracking
        self.is_running = False
        self.last_poll_attempt: Optional[datetime] = None
        self.last_successful_poll: Optional[datetime] = None
        self.consecutive_failures = 0
        self.total_polls = 0
        self.total_records_saved = 0

        logger.info(f"SolArkPoller initialized (interval: {self.poll_interval}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # Main Polling Loop
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self):
        """
        Start the continuous polling loop.

        This runs indefinitely in the background, polling the SolArk API
        every POLL_INTERVAL seconds and storing the results.
        """
        logger.info("Starting SolArk poller...")
        self.is_running = True

        # Verify credentials are configured
        if not os.getenv("SOLARK_EMAIL") or not os.getenv("SOLARK_PASSWORD"):
            logger.error("SolArk credentials not configured (SOLARK_EMAIL, SOLARK_PASSWORD)")
            self.is_running = False
            return

        logger.info("SolArk credentials verified")

        # Main polling loop
        while self.is_running:
            try:
                await self.poll_and_store()

                # Reset failure counter on success
                if self.consecutive_failures > 0:
                    logger.info(f"SolArk polling recovered after {self.consecutive_failures} failures")
                    self.consecutive_failures = 0

            except Exception as e:
                self.consecutive_failures += 1
                logger.error(
                    f"SolArk polling error (failure {self.consecutive_failures}/{MAX_CONSECUTIVE_FAILURES}): {e}"
                )

                # Alert if too many failures
                if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    logger.critical(
                        f"SolArk poller unhealthy: {self.consecutive_failures} consecutive failures"
                    )

            # Wait before next poll
            await asyncio.sleep(self.poll_interval)

        logger.info("SolArk poller stopped")

    async def stop(self):
        """Stop the polling loop gracefully."""
        logger.info("Stopping SolArk poller...")
        self.is_running = False

    # ─────────────────────────────────────────────────────────────────────────
    # Poll and Store
    # ─────────────────────────────────────────────────────────────────────────

    async def poll_and_store(self) -> Dict[str, Any]:
        """
        Poll SolArk API and store energy data in database.

        Returns:
            Dict containing the energy data that was stored

        Raises:
            Exception: If polling or storage fails
        """
        self.last_poll_attempt = datetime.now()
        self.total_polls += 1

        logger.debug(f"Polling SolArk API (poll #{self.total_polls})...")

        # Run the synchronous get_solark_status in executor to avoid blocking
        loop = asyncio.get_event_loop()

        def _fetch_and_store():
            """Synchronous function to fetch and store data."""
            from ..tools.solark import get_solark_status

            # get_solark_status automatically saves to DB when save_to_db=True (default)
            status = get_solark_status(save_to_db=True)
            return status

        try:
            # Execute in thread pool to avoid blocking asyncio loop
            status = await loop.run_in_executor(None, _fetch_and_store)

            # Update success tracking
            self.last_successful_poll = datetime.now()

            if status.get("db_id"):
                self.total_records_saved += 1

            logger.info(
                f"SolArk data stored (record #{self.total_records_saved}): "
                f"SOC={status.get('soc')}%, "
                f"PV={status.get('pv_power')}W, "
                f"Load={status.get('load_power')}W, "
                f"db_id={status.get('db_id')}"
            )

            return status

        except Exception as e:
            logger.error(f"Failed to poll SolArk: {e}")
            raise

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
            'total_polls': self.total_polls,
            'total_records_saved': self.total_records_saved
        }


# ─────────────────────────────────────────────────────────────────────────────
# Global Poller Instance
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance for the application
_poller_instance: Optional[SolArkPoller] = None


def get_poller() -> SolArkPoller:
    """
    Get the global SolArkPoller instance.

    Returns:
        SolArkPoller instance
    """
    global _poller_instance

    if _poller_instance is None:
        _poller_instance = SolArkPoller()

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
        poller = SolArkPoller()

        # Do one poll
        data = await poller.poll_and_store()
        print(f"Energy data: {data}")

        # Check health
        health = poller.get_health_status()
        print(f"Health: {health}")

        # Cleanup
        await poller.stop()

    asyncio.run(test())
