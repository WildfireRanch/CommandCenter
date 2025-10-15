# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/services/health_monitor.py
# PURPOSE: Background service that monitors database and poller health
#
# WHAT IT DOES:
#   - Monitors system health every 5 minutes
#   - Stores health snapshots in monitoring.health_snapshots table
#   - Tracks trends for 14-day retention
#   - Runs continuously in the background
#
# DEPENDENCIES:
#   - asyncio (background task scheduling)
#   - psycopg2 (database connection)
#   - api/endpoints/health_monitoring.py (health status fetcher)
#
# ENVIRONMENT VARIABLES:
#   - HEALTH_MONITOR_INTERVAL: Monitoring interval in seconds (default: 300 = 5 min)
#   - DATABASE_URL: PostgreSQL connection string
#
# USAGE:
#   # In FastAPI app startup:
#   from services.health_monitor import HealthMonitor
#
#   monitor = HealthMonitor()
#   asyncio.create_task(monitor.start())
# ═══════════════════════════════════════════════════════════════════════════

import os
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from ..utils.db import get_connection, execute

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MONITOR_INTERVAL = 300  # 5 minutes
MONITOR_INTERVAL = int(os.getenv("HEALTH_MONITOR_INTERVAL", DEFAULT_MONITOR_INTERVAL))


# ─────────────────────────────────────────────────────────────────────────────
# HealthMonitor Class
# ─────────────────────────────────────────────────────────────────────────────

class HealthMonitor:
    """
    Background service that monitors database and poller health.

    Responsibilities:
    - Collect health snapshots every MONITOR_INTERVAL seconds
    - Store snapshots in monitoring.health_snapshots table
    - Track system health trends
    - Log critical health events
    """

    def __init__(self):
        """Initialize the health monitor with state tracking."""
        self.interval = MONITOR_INTERVAL
        self.is_running = False
        self.last_snapshot: Optional[datetime] = None
        self.snapshot_count = 0

        logger.info(f"HealthMonitor initialized (interval: {self.interval}s)")

    # ─────────────────────────────────────────────────────────────────────────
    # Main Monitoring Loop
    # ─────────────────────────────────────────────────────────────────────────

    async def start(self):
        """
        Start the continuous health monitoring loop.

        This runs indefinitely in the background, collecting health snapshots
        every MONITOR_INTERVAL seconds and storing them in the database.
        """
        logger.info("Starting health monitor...")
        self.is_running = True

        # Verify database schema exists
        if not await self._verify_schema():
            logger.error("Health monitoring schema not found. Run migration 004_health_monitoring.sql first.")
            self.is_running = False
            return

        logger.info("Health monitoring schema verified")

        # Main monitoring loop
        while self.is_running:
            try:
                await self.collect_and_store_snapshot()

            except Exception as e:
                logger.error(f"Health monitoring error: {e}")

            # Wait before next snapshot
            await asyncio.sleep(self.interval)

        logger.info("Health monitor stopped")

    async def stop(self):
        """Stop the monitoring loop gracefully."""
        logger.info("Stopping health monitor...")
        self.is_running = False

    # ─────────────────────────────────────────────────────────────────────────
    # Snapshot Collection
    # ─────────────────────────────────────────────────────────────────────────

    async def collect_and_store_snapshot(self):
        """
        Collect current health metrics and store in database.

        This imports and calls the fetch_health_status function from the
        health_monitoring endpoint module to get current health data,
        then stores it in the monitoring.health_snapshots table.
        """
        self.snapshot_count += 1
        logger.debug(f"Collecting health snapshot #{self.snapshot_count}...")

        # Import here to avoid circular dependency
        from ..api.endpoints.health_monitoring import fetch_health_status

        try:
            # Fetch current health status
            loop = asyncio.get_event_loop()
            health_data = await loop.run_in_executor(None, fetch_health_status)

            # Store snapshot in database
            await self._store_snapshot(health_data)

            self.last_snapshot = datetime.now()

            # Log summary
            overall = health_data['overall_status']
            alert_count = len(health_data['alerts'])
            critical_count = sum(1 for a in health_data['alerts'] if a['severity'] == 'critical')

            logger.info(
                f"Health snapshot #{self.snapshot_count} stored: "
                f"status={overall}, alerts={alert_count} (critical={critical_count})"
            )

            # Log critical alerts
            if critical_count > 0:
                for alert in health_data['alerts']:
                    if alert['severity'] == 'critical':
                        logger.critical(f"HEALTH ALERT: {alert['message']}")

        except Exception as e:
            logger.error(f"Failed to collect health snapshot: {e}")
            raise

    async def _store_snapshot(self, health_data: Dict[str, Any]):
        """
        Store health snapshot in monitoring.health_snapshots table.

        Args:
            health_data: Health data dictionary from fetch_health_status()
        """
        query = """
            INSERT INTO monitoring.health_snapshots (
                timestamp,
                overall_status,
                db_connected,
                db_active_connections,
                db_response_time_ms,
                solark_running,
                solark_healthy,
                solark_consecutive_failures,
                solark_records_24h,
                solark_collection_health_pct,
                victron_running,
                victron_healthy,
                victron_consecutive_failures,
                victron_records_24h,
                victron_collection_health_pct,
                victron_api_requests_hour,
                solark_null_pct,
                victron_null_pct,
                solark_table_size_mb,
                victron_table_size_mb,
                critical_alerts,
                warning_alerts
            ) VALUES (
                NOW(),
                %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s,
                %s, %s
            )
        """

        # Count alerts by severity
        critical_alerts = sum(1 for a in health_data['alerts'] if a['severity'] == 'critical')
        warning_alerts = sum(1 for a in health_data['alerts'] if a['severity'] == 'warning')

        params = (
            health_data['overall_status'],
            health_data['database']['connected'],
            health_data['database']['connection_pool']['active_connections'],
            health_data['database']['response_time_ms'],
            health_data['solark_poller']['is_running'],
            health_data['solark_poller']['is_healthy'],
            health_data['solark_poller']['consecutive_failures'],
            health_data['data_quality']['solark']['records_last_24h'],
            health_data['data_quality']['solark']['collection_health_pct'],
            health_data['victron_poller']['is_running'],
            health_data['victron_poller']['is_healthy'],
            health_data['victron_poller']['consecutive_failures'],
            health_data['data_quality']['victron']['records_last_24h'],
            health_data['data_quality']['victron']['collection_health_pct'],
            health_data['victron_poller']['api_requests_this_hour'],
            health_data['data_quality']['solark']['null_percentage'],
            health_data['data_quality']['victron']['null_percentage'],
            health_data['database_metrics']['solark_table']['total_size_mb'],
            health_data['database_metrics']['victron_table']['total_size_mb'],
            critical_alerts,
            warning_alerts
        )

        # Execute in async-safe way
        loop = asyncio.get_event_loop()

        def _execute():
            with get_connection() as conn:
                return execute(conn, query, params, commit=True)

        await loop.run_in_executor(None, _execute)

    # ─────────────────────────────────────────────────────────────────────────
    # Schema Verification
    # ─────────────────────────────────────────────────────────────────────────

    async def _verify_schema(self) -> bool:
        """
        Verify that the monitoring schema and tables exist.

        Returns:
            True if schema exists, False otherwise
        """
        loop = asyncio.get_event_loop()

        def _check():
            try:
                with get_connection() as conn:
                    from ..utils.db import query_one
                    result = query_one(
                        conn,
                        """
                        SELECT EXISTS (
                            SELECT 1 FROM information_schema.tables
                            WHERE table_schema = 'monitoring'
                            AND table_name = 'health_snapshots'
                        ) as exists
                        """
                    )
                    return result['exists']
            except Exception as e:
                logger.error(f"Schema verification failed: {e}")
                return False

        return await loop.run_in_executor(None, _check)

    # ─────────────────────────────────────────────────────────────────────────
    # Health Status
    # ─────────────────────────────────────────────────────────────────────────

    def get_monitor_status(self) -> Dict[str, Any]:
        """
        Get current monitor status.

        Returns:
            Dict with monitor status information
        """
        return {
            'is_running': self.is_running,
            'interval_seconds': self.interval,
            'last_snapshot': self.last_snapshot.isoformat() if self.last_snapshot else None,
            'snapshot_count': self.snapshot_count
        }


# ─────────────────────────────────────────────────────────────────────────────
# Global Monitor Instance
# ─────────────────────────────────────────────────────────────────────────────

# Singleton instance for the application
_monitor_instance: Optional[HealthMonitor] = None


def get_monitor() -> HealthMonitor:
    """
    Get the global HealthMonitor instance.

    Returns:
        HealthMonitor instance
    """
    global _monitor_instance

    if _monitor_instance is None:
        _monitor_instance = HealthMonitor()

    return _monitor_instance


async def start_monitor():
    """Start the global health monitor instance."""
    monitor = get_monitor()
    await monitor.start()


async def stop_monitor():
    """Stop the global health monitor instance."""
    global _monitor_instance

    if _monitor_instance:
        await _monitor_instance.stop()
        _monitor_instance = None


# ─────────────────────────────────────────────────────────────────────────────
# Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Test the health monitor
    import asyncio

    async def test():
        """Test the health monitor for one iteration."""
        monitor = HealthMonitor()

        # Verify schema
        schema_exists = await monitor._verify_schema()
        print(f"Schema exists: {schema_exists}")

        if schema_exists:
            # Collect one snapshot
            await monitor.collect_and_store_snapshot()
            print("Snapshot collected successfully")

            # Check status
            status = monitor.get_monitor_status()
            print(f"Monitor status: {status}")

        # Cleanup
        await monitor.stop()

    asyncio.run(test())
