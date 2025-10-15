# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/endpoints/health_monitoring.py
# PURPOSE: Comprehensive database and poller health monitoring endpoint
#
# WHAT IT DOES:
#   - Aggregates health metrics from all system components
#   - Provides single endpoint for frontend health dashboard
#   - Generates alerts based on health status
#   - Caches responses for 30 seconds to reduce load
#
# DEPENDENCIES:
#   - services/solark_poller.py (poller health)
#   - services/victron_poller.py (poller health)
#   - utils/db.py (database queries)
#
# ENDPOINTS:
#   - GET /health/monitoring/status - Current health snapshot
#   - GET /health/monitoring/history - Historical health data
# ═══════════════════════════════════════════════════════════════════════════

import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from functools import lru_cache

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from ...utils.db import get_connection, query_one, query_all
from ...services.solark_poller import get_poller as get_solark_poller
from ...services.victron_poller import get_poller as get_victron_poller

logger = logging.getLogger(__name__)

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
# Response Models
# ─────────────────────────────────────────────────────────────────────────────

class ConnectionPoolInfo(BaseModel):
    active_connections: int
    idle_connections: int
    max_connections: int


class DatabaseHealth(BaseModel):
    connected: bool
    connection_pool: ConnectionPoolInfo
    response_time_ms: float


class PollerHealth(BaseModel):
    is_running: bool
    is_healthy: bool
    last_poll_attempt: Optional[str]
    last_successful_poll: Optional[str]
    consecutive_failures: int
    poll_interval_seconds: int
    total_polls_24h: int
    total_records_saved_24h: int


class VictronPollerHealth(PollerHealth):
    api_requests_this_hour: int
    rate_limit_max: int


class DataQualityMetrics(BaseModel):
    total_records: int
    oldest_record: Optional[str]
    newest_record: Optional[str]
    records_last_hour: int
    records_last_24h: int
    records_last_7d: int
    null_percentage: float
    expected_records_24h: int
    collection_health_pct: float


class VictronDataQuality(BaseModel):
    total_records: int
    oldest_record: Optional[str]
    newest_record: Optional[str]
    records_last_hour: int
    records_last_24h: int
    records_last_72h: int
    null_percentage: float
    expected_records_24h: int
    collection_health_pct: float


class TableMetrics(BaseModel):
    total_size_mb: float
    total_rows: int
    index_size_mb: float
    avg_row_size_bytes: float


class DatabaseMetrics(BaseModel):
    solark_table: TableMetrics
    victron_table: TableMetrics


class Alert(BaseModel):
    severity: str  # "critical" | "warning" | "info"
    component: str  # "database" | "solark_poller" | "victron_poller" | "data_quality"
    message: str
    timestamp: str


class HealthMonitoringResponse(BaseModel):
    timestamp: str
    overall_status: str  # "healthy" | "degraded" | "critical"
    database: DatabaseHealth
    solark_poller: PollerHealth
    victron_poller: VictronPollerHealth
    data_quality: Dict[str, Any]
    database_metrics: DatabaseMetrics
    alerts: List[Alert]


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_database_health() -> Dict[str, Any]:
    """
    Get database connection health and pool statistics.

    Returns:
        Dict with database health metrics
    """
    start_time = time.time()

    try:
        with get_connection() as conn:
            # Test query to measure response time
            query_one(conn, "SELECT 1")

            # Get connection pool stats
            pool_stats = query_one(
                conn,
                """
                SELECT
                    (SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database() AND state = 'active') as active,
                    (SELECT COUNT(*) FROM pg_stat_activity WHERE datname = current_database() AND state = 'idle') as idle,
                    (SELECT setting::int FROM pg_settings WHERE name = 'max_connections') as max_conn
                """
            )

            response_time = (time.time() - start_time) * 1000  # Convert to ms

            return {
                'connected': True,
                'connection_pool': {
                    'active_connections': pool_stats['active'],
                    'idle_connections': pool_stats['idle'],
                    'max_connections': pool_stats['max_conn']
                },
                'response_time_ms': round(response_time, 2)
            }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            'connected': False,
            'connection_pool': {
                'active_connections': 0,
                'idle_connections': 0,
                'max_connections': 0
            },
            'response_time_ms': 0.0
        }


def get_solark_data_quality() -> Dict[str, Any]:
    """
    Get SolArk data quality metrics.

    Returns:
        Dict with data quality metrics
    """
    try:
        with get_connection() as conn:
            # Get record counts by time period
            stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total_records,
                    MIN(created_at) as oldest_record,
                    MAX(created_at) as newest_record,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as last_hour,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
                    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as last_7d
                FROM solark.plant_flow
                """
            )

            # Get NULL percentage (checking key fields)
            null_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE pv_power IS NULL OR batt_power IS NULL OR soc IS NULL) as nulls
                FROM solark.plant_flow
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                """
            )

            null_pct = 0.0
            if null_stats['total'] > 0:
                null_pct = round((null_stats['nulls'] / null_stats['total']) * 100, 2)

            # Expected records: 480 per day (3-minute intervals)
            expected_24h = 480
            collection_health = 0.0
            if stats['last_24h'] > 0:
                collection_health = round((stats['last_24h'] / expected_24h) * 100, 2)

            return {
                'total_records': stats['total_records'],
                'oldest_record': stats['oldest_record'].isoformat() if stats['oldest_record'] else None,
                'newest_record': stats['newest_record'].isoformat() if stats['newest_record'] else None,
                'records_last_hour': stats['last_hour'],
                'records_last_24h': stats['last_24h'],
                'records_last_7d': stats['last_7d'],
                'null_percentage': null_pct,
                'expected_records_24h': expected_24h,
                'collection_health_pct': collection_health
            }
    except Exception as e:
        logger.error(f"Failed to get SolArk data quality: {e}")
        return {
            'total_records': 0,
            'oldest_record': None,
            'newest_record': None,
            'records_last_hour': 0,
            'records_last_24h': 0,
            'records_last_7d': 0,
            'null_percentage': 0.0,
            'expected_records_24h': 480,
            'collection_health_pct': 0.0
        }


def get_victron_data_quality() -> Dict[str, Any]:
    """
    Get Victron data quality metrics.

    Returns:
        Dict with data quality metrics
    """
    try:
        with get_connection() as conn:
            # Get record counts by time period
            stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total_records,
                    MIN(timestamp) as oldest_record,
                    MAX(timestamp) as newest_record,
                    COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '1 hour') as last_hour,
                    COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '24 hours') as last_24h,
                    COUNT(*) FILTER (WHERE timestamp >= NOW() - INTERVAL '72 hours') as last_72h
                FROM victron.battery_readings
                """
            )

            # Get NULL percentage
            null_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE soc IS NULL OR voltage IS NULL OR current IS NULL) as nulls
                FROM victron.battery_readings
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
                """
            )

            null_pct = 0.0
            if null_stats['total'] > 0:
                null_pct = round((null_stats['nulls'] / null_stats['total']) * 100, 2)

            # Expected records: 480 per day (3-minute intervals)
            expected_24h = 480
            collection_health = 0.0
            if stats['last_24h'] > 0:
                collection_health = round((stats['last_24h'] / expected_24h) * 100, 2)

            return {
                'total_records': stats['total_records'],
                'oldest_record': stats['oldest_record'].isoformat() if stats['oldest_record'] else None,
                'newest_record': stats['newest_record'].isoformat() if stats['newest_record'] else None,
                'records_last_hour': stats['last_hour'],
                'records_last_24h': stats['last_24h'],
                'records_last_72h': stats['last_72h'],
                'null_percentage': null_pct,
                'expected_records_24h': expected_24h,
                'collection_health_pct': collection_health
            }
    except Exception as e:
        logger.error(f"Failed to get Victron data quality: {e}")
        return {
            'total_records': 0,
            'oldest_record': None,
            'newest_record': None,
            'records_last_hour': 0,
            'records_last_24h': 0,
            'records_last_72h': 0,
            'null_percentage': 0.0,
            'expected_records_24h': 480,
            'collection_health_pct': 0.0
        }


def get_table_metrics() -> Dict[str, Any]:
    """
    Get database table size and row count metrics.

    Returns:
        Dict with table metrics
    """
    try:
        with get_connection() as conn:
            # SolArk table metrics
            solark_stats = query_one(
                conn,
                """
                SELECT
                    pg_total_relation_size('solark.plant_flow') / (1024.0 * 1024.0) as total_size_mb,
                    pg_relation_size('solark.plant_flow') / (1024.0 * 1024.0) as table_size_mb,
                    pg_indexes_size('solark.plant_flow') / (1024.0 * 1024.0) as index_size_mb,
                    (SELECT COUNT(*) FROM solark.plant_flow) as total_rows
                """
            )

            # Victron table metrics
            victron_stats = query_one(
                conn,
                """
                SELECT
                    pg_total_relation_size('victron.battery_readings') / (1024.0 * 1024.0) as total_size_mb,
                    pg_relation_size('victron.battery_readings') / (1024.0 * 1024.0) as table_size_mb,
                    pg_indexes_size('victron.battery_readings') / (1024.0 * 1024.0) as index_size_mb,
                    (SELECT COUNT(*) FROM victron.battery_readings) as total_rows
                """
            )

            # Calculate average row size
            solark_avg_row = 0.0
            if solark_stats['total_rows'] > 0:
                solark_avg_row = (solark_stats['table_size_mb'] * 1024 * 1024) / solark_stats['total_rows']

            victron_avg_row = 0.0
            if victron_stats['total_rows'] > 0:
                victron_avg_row = (victron_stats['table_size_mb'] * 1024 * 1024) / victron_stats['total_rows']

            return {
                'solark_table': {
                    'total_size_mb': round(solark_stats['total_size_mb'], 2),
                    'total_rows': solark_stats['total_rows'],
                    'index_size_mb': round(solark_stats['index_size_mb'], 2),
                    'avg_row_size_bytes': round(solark_avg_row, 2)
                },
                'victron_table': {
                    'total_size_mb': round(victron_stats['total_size_mb'], 2),
                    'total_rows': victron_stats['total_rows'],
                    'index_size_mb': round(victron_stats['index_size_mb'], 2),
                    'avg_row_size_bytes': round(victron_avg_row, 2)
                }
            }
    except Exception as e:
        logger.error(f"Failed to get table metrics: {e}")
        return {
            'solark_table': {
                'total_size_mb': 0.0,
                'total_rows': 0,
                'index_size_mb': 0.0,
                'avg_row_size_bytes': 0.0
            },
            'victron_table': {
                'total_size_mb': 0.0,
                'total_rows': 0,
                'index_size_mb': 0.0,
                'avg_row_size_bytes': 0.0
            }
        }


def calculate_overall_status(metrics: Dict[str, Any]) -> str:
    """
    Calculate overall system health status.

    Business Logic:
    - CRITICAL if: database disconnected OR any poller has >5 consecutive failures
    - DEGRADED if: collection_health < 90% OR response_time > 1000ms
    - HEALTHY if: all checks pass

    Args:
        metrics: All health metrics

    Returns:
        "healthy" | "degraded" | "critical"
    """
    # Critical conditions
    if not metrics['database']['connected']:
        return 'critical'

    if (metrics['solark_poller']['consecutive_failures'] > 5 or
        metrics['victron_poller']['consecutive_failures'] > 5):
        return 'critical'

    # Degraded conditions
    if (metrics['data_quality']['solark']['collection_health_pct'] < 90 or
        metrics['data_quality']['victron']['collection_health_pct'] < 90):
        return 'degraded'

    if metrics['database']['response_time_ms'] > 1000:
        return 'degraded'

    return 'healthy'


def generate_alerts(metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate alerts based on health metrics.

    Args:
        metrics: All health metrics

    Returns:
        List of alert dictionaries
    """
    alerts = []
    now = datetime.now().isoformat()

    # Critical alerts
    if not metrics['database']['connected']:
        alerts.append({
            'severity': 'critical',
            'component': 'database',
            'message': 'Database connection lost. Check Railway logs immediately.',
            'timestamp': now
        })

    if metrics['solark_poller']['consecutive_failures'] > 5:
        alerts.append({
            'severity': 'critical',
            'component': 'solark_poller',
            'message': f'SolArk poller has {metrics["solark_poller"]["consecutive_failures"]} consecutive failures. Check poller logs.',
            'timestamp': now
        })

    if metrics['victron_poller']['consecutive_failures'] > 5:
        alerts.append({
            'severity': 'critical',
            'component': 'victron_poller',
            'message': f'Victron poller has {metrics["victron_poller"]["consecutive_failures"]} consecutive failures. Check poller logs.',
            'timestamp': now
        })

    # Warning alerts
    solark_health = metrics['data_quality']['solark']['collection_health_pct']
    if solark_health < 95:
        expected = metrics['data_quality']['solark']['expected_records_24h']
        actual = metrics['data_quality']['solark']['records_last_24h']
        alerts.append({
            'severity': 'warning',
            'component': 'solark_poller',
            'message': f'SolArk collection at {solark_health}%. Expected {expected} records/day, got {actual}.',
            'timestamp': now
        })

    victron_health = metrics['data_quality']['victron']['collection_health_pct']
    if victron_health < 95:
        expected = metrics['data_quality']['victron']['expected_records_24h']
        actual = metrics['data_quality']['victron']['records_last_24h']
        alerts.append({
            'severity': 'warning',
            'component': 'victron_poller',
            'message': f'Victron collection at {victron_health}%. Expected {expected} records/day, got {actual}.',
            'timestamp': now
        })

    # Info alerts
    api_requests = metrics['victron_poller'].get('api_requests_this_hour', 0)
    if api_requests > 45:
        alerts.append({
            'severity': 'info',
            'component': 'victron_poller',
            'message': f'Victron API approaching rate limit: {api_requests}/50 requests this hour.',
            'timestamp': now
        })

    return alerts


@lru_cache(maxsize=1)
def get_health_status_cached(cache_key: int) -> Dict[str, Any]:
    """
    Get health status with caching.

    Cache key changes every 30 seconds, providing 30-second cache.

    Args:
        cache_key: Current 30-second window (int(time.time() / 30))

    Returns:
        Health status dictionary
    """
    return fetch_health_status()


def fetch_health_status() -> Dict[str, Any]:
    """
    Fetch current health status from all components.

    Returns:
        Complete health status dictionary
    """
    # Get database health
    db_health = get_database_health()

    # Get poller health
    solark_poller = get_solark_poller()
    victron_poller = get_victron_poller()

    solark_health = solark_poller.get_health_status()
    victron_health = victron_poller.get_health_status()

    # Get data quality metrics
    solark_quality = get_solark_data_quality()
    victron_quality = get_victron_data_quality()

    # Get table metrics
    table_metrics = get_table_metrics()

    # Compile all metrics
    metrics = {
        'timestamp': datetime.now().isoformat(),
        'database': db_health,
        'solark_poller': {
            'is_running': solark_health['is_running'],
            'is_healthy': solark_health['is_healthy'],
            'last_poll_attempt': solark_health['last_poll_attempt'],
            'last_successful_poll': solark_health['last_successful_poll'],
            'consecutive_failures': solark_health['consecutive_failures'],
            'poll_interval_seconds': solark_health['poll_interval_seconds'],
            'total_polls_24h': solark_health.get('total_polls', 0),
            'total_records_saved_24h': solark_health.get('total_records_saved', 0)
        },
        'victron_poller': {
            'is_running': victron_health['is_running'],
            'is_healthy': victron_health['is_healthy'],
            'last_poll_attempt': victron_health['last_poll_attempt'],
            'last_successful_poll': victron_health['last_successful_poll'],
            'consecutive_failures': victron_health['consecutive_failures'],
            'poll_interval_seconds': victron_health['poll_interval_seconds'],
            'total_polls_24h': 0,  # Will be calculated from database
            'total_records_saved_24h': victron_quality['records_last_24h'],
            'api_requests_this_hour': victron_health.get('rate_limit', {}).get('requests_used', 0) if victron_health.get('rate_limit') else 0,
            'rate_limit_max': victron_health.get('rate_limit', {}).get('limit', 50) if victron_health.get('rate_limit') else 50
        },
        'data_quality': {
            'solark': solark_quality,
            'victron': victron_quality
        },
        'database_metrics': table_metrics
    }

    # Calculate overall status
    metrics['overall_status'] = calculate_overall_status(metrics)

    # Generate alerts
    metrics['alerts'] = generate_alerts(metrics)

    return metrics


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/health/monitoring/status", response_model=HealthMonitoringResponse)
async def get_health_monitoring_status():
    """
    Get current system health status.

    Returns comprehensive health metrics for:
    - Database connection and performance
    - SolArk and Victron pollers
    - Data quality and collection health
    - Table sizes and metrics
    - Active alerts

    Cached for 30 seconds to reduce database load.
    """
    try:
        # Use cache key that changes every 30 seconds
        cache_key = int(time.time() / 30)
        status = get_health_status_cached(cache_key)

        return status
    except Exception as e:
        logger.error(f"Failed to get health monitoring status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health/monitoring/history")
async def get_health_monitoring_history(
    hours: int = Query(default=24, ge=1, le=336, description="Hours of history (max 336 for 14 days)"),
    metric: Optional[str] = Query(default=None, description="Filter by metric: overall|solark|victron|database")
):
    """
    Get historical health monitoring data.

    Args:
        hours: Number of hours of history to return (max 336 for 14 days)
        metric: Optional filter by metric type

    Returns:
        Historical health data for trend analysis
    """
    try:
        with get_connection() as conn:
            query = """
                SELECT
                    timestamp,
                    overall_status,
                    solark_collection_health_pct,
                    victron_collection_health_pct,
                    db_response_time_ms,
                    solark_records_24h,
                    victron_records_24h,
                    critical_alerts,
                    warning_alerts
                FROM monitoring.health_snapshots
                WHERE timestamp >= NOW() - INTERVAL '%s hours'
                ORDER BY timestamp DESC
            """

            rows = query_all(conn, query, (hours,))

            return {
                'status': 'success',
                'hours': hours,
                'data': rows
            }
    except Exception as e:
        logger.error(f"Failed to get health history: {e}")
        raise HTTPException(status_code=500, detail=str(e))
