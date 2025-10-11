"""
Agent Telemetry System

PURPOSE: Track agent health, performance, and activity
WHAT: Decorators and utilities for agent monitoring
WHY: Provides observability into agent behavior and performance
"""

import logging
import time
from functools import wraps
from typing import Optional, Dict, Any

from .db import get_connection, execute

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Event Logging
# ─────────────────────────────────────────────────────────────────────────────

def log_agent_event(
    agent_name: str,
    event_type: str,
    event_status: str = "success",
    query: Optional[str] = None,
    tool_name: Optional[str] = None,
    duration_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    conversation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log an agent event to the database.

    Args:
        agent_name: Name of the agent (e.g., 'Manager', 'Solar Controller')
        event_type: Type of event ('start', 'stop', 'tool_call', 'error', 'query')
        event_status: Status ('success', 'failure', 'in_progress')
        query: User query if applicable
        tool_name: Tool name if this is a tool call
        duration_ms: Execution duration in milliseconds
        error_message: Error details if failed
        conversation_id: Associated conversation UUID
        metadata: Additional event data as dict
    """
    try:
        import json

        with get_connection() as conn:
            execute(
                conn,
                """
                INSERT INTO agent_metrics.agent_events
                (agent_name, event_type, event_status, query, tool_name, duration_ms,
                 error_message, conversation_id, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    agent_name,
                    event_type,
                    event_status,
                    query,
                    tool_name,
                    duration_ms,
                    error_message,
                    conversation_id,
                    json.dumps(metadata) if metadata else None
                ),
                commit=True
            )
    except Exception as e:
        logger.warning(f"Failed to log agent event: {e}")


def log_tool_execution(
    agent_name: str,
    tool_name: str,
    input_params: Optional[Dict[str, Any]],
    output_data: Optional[str],
    success: bool,
    duration_ms: int,
    error_message: Optional[str] = None,
    conversation_id: Optional[str] = None
) -> None:
    """
    Log a tool execution to the database.

    Args:
        agent_name: Agent calling the tool
        tool_name: Name of the tool
        input_params: Tool input parameters as dict
        output_data: Tool output (truncated to 5000 chars)
        success: Whether execution succeeded
        duration_ms: Execution time
        error_message: Error details if failed
        conversation_id: Associated conversation UUID
    """
    try:
        import json

        # Truncate output if too large
        if output_data and len(output_data) > 5000:
            output_data = output_data[:5000] + "... [truncated]"

        with get_connection() as conn:
            execute(
                conn,
                """
                INSERT INTO agent_metrics.tool_execution_log
                (agent_name, tool_name, input_params, output_data, success,
                 duration_ms, error_message, conversation_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    agent_name,
                    tool_name,
                    json.dumps(input_params) if input_params else None,
                    output_data,
                    success,
                    duration_ms,
                    error_message,
                    conversation_id
                ),
                commit=True
            )
    except Exception as e:
        logger.warning(f"Failed to log tool execution: {e}")


def record_health_check(
    agent_name: str,
    status: str,
    response_time_ms: Optional[int] = None,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Record an agent health check.

    Args:
        agent_name: Agent being checked
        status: Health status ('online', 'offline', 'error', 'degraded')
        response_time_ms: Health check response time
        error_message: Error details if unhealthy
        metadata: Additional health data
    """
    try:
        import json

        with get_connection() as conn:
            execute(
                conn,
                """
                INSERT INTO agent_metrics.agent_health_checks
                (agent_name, status, response_time_ms, error_message, metadata)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    agent_name,
                    status,
                    response_time_ms,
                    error_message,
                    json.dumps(metadata) if metadata else None
                ),
                commit=True
            )
    except Exception as e:
        logger.warning(f"Failed to record health check: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# Decorators
# ─────────────────────────────────────────────────────────────────────────────

def track_agent_execution(agent_name: str):
    """
    Decorator to track agent crew execution.

    Logs start, stop, duration, and errors for agent crews.

    Usage:
        @track_agent_execution("Solar Controller")
        def create_energy_crew(query: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract query if available
            query = args[0] if args else kwargs.get('query', 'N/A')

            # Log start
            log_agent_event(
                agent_name=agent_name,
                event_type="start",
                event_status="in_progress",
                query=str(query)
            )

            start_time = time.time()
            error_occurred = False
            error_msg = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error_occurred = True
                error_msg = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)

                # Log stop
                log_agent_event(
                    agent_name=agent_name,
                    event_type="stop",
                    event_status="failure" if error_occurred else "success",
                    query=str(query),
                    duration_ms=duration_ms,
                    error_message=error_msg
                )

        return wrapper
    return decorator


def track_tool_call(agent_name: str, tool_name: str):
    """
    Decorator to track tool execution.

    Logs tool calls, inputs, outputs, duration, and errors.

    Usage:
        @track_tool_call("Solar Controller", "get_energy_status")
        def get_energy_status():
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            error_msg = None
            output = None

            # Capture input params
            input_params = {}
            if args:
                input_params['args'] = [str(arg)[:200] for arg in args]  # Truncate
            if kwargs:
                input_params['kwargs'] = {k: str(v)[:200] for k, v in kwargs.items()}

            try:
                result = func(*args, **kwargs)
                output = str(result)
                success = True
                return result
            except Exception as e:
                success = False
                error_msg = str(e)
                raise
            finally:
                duration_ms = int((time.time() - start_time) * 1000)

                # Log tool execution
                log_tool_execution(
                    agent_name=agent_name,
                    tool_name=tool_name,
                    input_params=input_params,
                    output_data=output,
                    success=success,
                    duration_ms=duration_ms,
                    error_message=error_msg
                )

                # Also log as agent event
                log_agent_event(
                    agent_name=agent_name,
                    event_type="tool_call",
                    event_status="success" if success else "failure",
                    tool_name=tool_name,
                    duration_ms=duration_ms,
                    error_message=error_msg
                )

        return wrapper
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# Query Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_agent_health_summary():
    """
    Get latest health status for all agents.

    Returns:
        List of dicts with agent health data
    """
    try:
        from .db import query_all

        with get_connection() as conn:
            return query_all(
                conn,
                "SELECT * FROM agent_metrics.agent_health_summary",
                as_dict=True
            )
    except Exception as e:
        logger.error(f"Failed to get agent health summary: {e}")
        return []


def get_recent_agent_activity(limit: int = 100, agent_name: Optional[str] = None):
    """
    Get recent agent activity events.

    Args:
        limit: Maximum number of events
        agent_name: Filter by specific agent (optional)

    Returns:
        List of dicts with event data
    """
    try:
        from .db import query_all

        with get_connection() as conn:
            if agent_name:
                return query_all(
                    conn,
                    """
                    SELECT * FROM agent_metrics.agent_events
                    WHERE agent_name = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (agent_name, limit),
                    as_dict=True
                )
            else:
                return query_all(
                    conn,
                    """
                    SELECT * FROM agent_metrics.agent_events
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                    as_dict=True
                )
    except Exception as e:
        logger.error(f"Failed to get recent agent activity: {e}")
        return []


def get_agent_metrics(agent_name: Optional[str] = None, hours: int = 24):
    """
    Get aggregated agent metrics.

    Args:
        agent_name: Filter by specific agent (optional)
        hours: Hours to look back

    Returns:
        Dict with aggregated metrics
    """
    try:
        from .db import query_one

        with get_connection() as conn:
            if agent_name:
                query = """
                SELECT
                    agent_name,
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE event_status = 'success') as successful_events,
                    COUNT(*) FILTER (WHERE event_status = 'failure') as failed_events,
                    AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as avg_duration_ms,
                    COUNT(*) FILTER (WHERE event_type = 'tool_call') as total_tool_calls
                FROM agent_metrics.agent_events
                WHERE agent_name = %s
                  AND created_at > NOW() - INTERVAL '%s hours'
                GROUP BY agent_name
                """
                params = (agent_name, hours)
            else:
                query = """
                SELECT
                    COUNT(*) as total_events,
                    COUNT(*) FILTER (WHERE event_status = 'success') as successful_events,
                    COUNT(*) FILTER (WHERE event_status = 'failure') as failed_events,
                    AVG(duration_ms) FILTER (WHERE duration_ms IS NOT NULL) as avg_duration_ms,
                    COUNT(*) FILTER (WHERE event_type = 'tool_call') as total_tool_calls
                FROM agent_metrics.agent_events
                WHERE created_at > NOW() - INTERVAL '%s hours'
                """
                params = (hours,)

            result = query_one(conn, query, params)
            return dict(result) if result else {}
    except Exception as e:
        logger.error(f"Failed to get agent metrics: {e}")
        return {}
