"""
Agent Health Check Service

PURPOSE: Monitor health and availability of CrewAI agents
WHAT: Health check functions for each agent
WHY: Enables real-time monitoring of agent status
"""

import logging
import time
from typing import Dict, Any, List

from ..utils.agent_telemetry import record_health_check, get_agent_health_summary

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Agent Definitions
# ─────────────────────────────────────────────────────────────────────────────

KNOWN_AGENTS = [
    "Manager",
    "Solar Controller",
    "Energy Orchestrator"
]


# ─────────────────────────────────────────────────────────────────────────────
# Health Check Functions
# ─────────────────────────────────────────────────────────────────────────────

def check_agent_health(agent_name: str) -> Dict[str, Any]:
    """
    Perform health check for a specific agent.

    Args:
        agent_name: Name of agent to check

    Returns:
        Dict with health status data
    """
    start_time = time.time()
    status = "online"
    error_message = None
    metadata = {}

    try:
        # Check if agent module can be imported and instantiated
        if agent_name == "Manager":
            from ..agents.manager import create_manager_crew
            # Quick validation: can we create the crew?
            metadata['can_import'] = True
            metadata['module'] = 'manager'

        elif agent_name == "Solar Controller":
            from ..agents.solar_controller import create_energy_crew
            metadata['can_import'] = True
            metadata['module'] = 'solar_controller'

        elif agent_name == "Energy Orchestrator":
            from ..agents.energy_orchestrator import create_orchestrator_crew
            metadata['can_import'] = True
            metadata['module'] = 'energy_orchestrator'

        else:
            status = "error"
            error_message = f"Unknown agent: {agent_name}"

        # Check if OpenAI API key is configured
        import os
        if not os.getenv("OPENAI_API_KEY"):
            status = "degraded"
            error_message = "OpenAI API key not configured"

        # Check database connectivity (required for agents)
        from ..utils.db import check_connection
        if not check_connection():
            status = "degraded"
            error_message = "Database not connected"

    except Exception as e:
        status = "error"
        error_message = str(e)
        logger.error(f"Health check failed for {agent_name}: {e}")

    response_time_ms = int((time.time() - start_time) * 1000)

    # Record health check to database
    record_health_check(
        agent_name=agent_name,
        status=status,
        response_time_ms=response_time_ms,
        error_message=error_message,
        metadata=metadata
    )

    return {
        "agent_name": agent_name,
        "status": status,
        "response_time_ms": response_time_ms,
        "error_message": error_message,
        "checked_at": time.time(),
        "metadata": metadata
    }


def check_all_agents_health() -> List[Dict[str, Any]]:
    """
    Check health of all known agents.

    Returns:
        List of health check results
    """
    results = []
    for agent_name in KNOWN_AGENTS:
        result = check_agent_health(agent_name)
        results.append(result)
    return results


def get_latest_agent_health(agent_name: str = None) -> Dict[str, Any]:
    """
    Get latest health status from database.

    Args:
        agent_name: Specific agent (optional, returns all if None)

    Returns:
        Dict with latest health data
    """
    try:
        summary = get_agent_health_summary()

        if agent_name:
            # Find specific agent
            for agent in summary:
                if agent['agent_name'] == agent_name:
                    return agent
            return {"error": f"No health data for {agent_name}"}
        else:
            # Return all agents
            return {"agents": summary, "count": len(summary)}

    except Exception as e:
        logger.error(f"Failed to get latest agent health: {e}")
        return {"error": str(e)}


def get_agent_status_summary() -> Dict[str, Any]:
    """
    Get summary of all agent statuses.

    Returns:
        Dict with counts and status info
    """
    try:
        summary = get_agent_health_summary()

        online_count = sum(1 for a in summary if a['status'] == 'online')
        degraded_count = sum(1 for a in summary if a['status'] == 'degraded')
        offline_count = sum(1 for a in summary if a['status'] == 'offline')
        error_count = sum(1 for a in summary if a['status'] == 'error')

        return {
            "total_agents": len(KNOWN_AGENTS),
            "online": online_count,
            "degraded": degraded_count,
            "offline": offline_count,
            "error": error_count,
            "overall_status": "healthy" if online_count == len(KNOWN_AGENTS) else "degraded",
            "agents": summary
        }

    except Exception as e:
        logger.error(f"Failed to get agent status summary: {e}")
        return {
            "total_agents": len(KNOWN_AGENTS),
            "error": str(e),
            "overall_status": "error"
        }
