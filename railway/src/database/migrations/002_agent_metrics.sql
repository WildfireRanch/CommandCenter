-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRATION: 002_agent_metrics.sql
-- PURPOSE: Add agent health monitoring, telemetry, and activity tracking
-- CREATED: 2025-10-11
-- ═══════════════════════════════════════════════════════════════════════════

-- Create schema for agent metrics if it doesn't exist
CREATE SCHEMA IF NOT EXISTS agent_metrics;

-- ─────────────────────────────────────────────────────────────────────────────
-- Table: agent_health_checks
-- PURPOSE: Track periodic health status for each agent
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_metrics.agent_health_checks (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,           -- e.g., 'Manager', 'Solar Controller', 'Energy Orchestrator'
    status VARCHAR(50) NOT NULL,                -- 'online', 'offline', 'error', 'degraded'
    response_time_ms INTEGER,                   -- Health check response time
    error_message TEXT,                         -- Error details if status = 'error'
    checked_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB                              -- Additional health check data
);

CREATE INDEX idx_agent_health_agent_name ON agent_metrics.agent_health_checks(agent_name);
CREATE INDEX idx_agent_health_checked_at ON agent_metrics.agent_health_checks(checked_at DESC);
CREATE INDEX idx_agent_health_status ON agent_metrics.agent_health_checks(status);

-- ─────────────────────────────────────────────────────────────────────────────
-- Table: agent_events
-- PURPOSE: Log all agent activities (starts, stops, tool calls, errors)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_metrics.agent_events (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,           -- Which agent
    event_type VARCHAR(50) NOT NULL,            -- 'start', 'stop', 'tool_call', 'error', 'query'
    event_status VARCHAR(50),                   -- 'success', 'failure', 'in_progress'
    query TEXT,                                 -- User query (if applicable)
    tool_name VARCHAR(100),                     -- Tool being called (if tool_call)
    duration_ms INTEGER,                        -- Execution duration
    error_message TEXT,                         -- Error details
    conversation_id VARCHAR(100),               -- Link to conversation
    metadata JSONB,                             -- Additional event data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_events_agent_name ON agent_metrics.agent_events(agent_name);
CREATE INDEX idx_agent_events_event_type ON agent_metrics.agent_events(event_type);
CREATE INDEX idx_agent_events_created_at ON agent_metrics.agent_events(created_at DESC);
CREATE INDEX idx_agent_events_conversation_id ON agent_metrics.agent_events(conversation_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- Table: tool_execution_log
-- PURPOSE: Detailed tracking of all tool executions
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_metrics.tool_execution_log (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,           -- Agent calling the tool
    tool_name VARCHAR(100) NOT NULL,            -- Tool being executed
    input_params JSONB,                         -- Tool input parameters
    output_data TEXT,                           -- Tool output (truncated if large)
    success BOOLEAN NOT NULL,                   -- Execution success/failure
    duration_ms INTEGER,                        -- Execution time
    error_message TEXT,                         -- Error if failed
    conversation_id VARCHAR(100),               -- Associated conversation
    executed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_tool_exec_agent_name ON agent_metrics.tool_execution_log(agent_name);
CREATE INDEX idx_tool_exec_tool_name ON agent_metrics.tool_execution_log(tool_name);
CREATE INDEX idx_tool_exec_executed_at ON agent_metrics.tool_execution_log(executed_at DESC);
CREATE INDEX idx_tool_exec_success ON agent_metrics.tool_execution_log(success);

-- ─────────────────────────────────────────────────────────────────────────────
-- Table: agent_performance_metrics
-- PURPOSE: Aggregated performance metrics (hourly rollups)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent_metrics.agent_performance_metrics (
    id SERIAL PRIMARY KEY,
    agent_name VARCHAR(100) NOT NULL,
    metric_hour TIMESTAMPTZ NOT NULL,           -- Hourly bucket
    total_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    failed_queries INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    total_tool_calls INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(agent_name, metric_hour)             -- Prevent duplicates
);

CREATE INDEX idx_perf_metrics_agent_name ON agent_metrics.agent_performance_metrics(agent_name);
CREATE INDEX idx_perf_metrics_hour ON agent_metrics.agent_performance_metrics(metric_hour DESC);

-- ─────────────────────────────────────────────────────────────────────────────
-- View: agent_health_summary
-- PURPOSE: Latest health status for each agent
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW agent_metrics.agent_health_summary AS
SELECT DISTINCT ON (agent_name)
    agent_name,
    status,
    response_time_ms,
    error_message,
    checked_at,
    metadata
FROM agent_metrics.agent_health_checks
ORDER BY agent_name, checked_at DESC;

-- ─────────────────────────────────────────────────────────────────────────────
-- View: recent_agent_activity
-- PURPOSE: Recent agent events (last 100)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW agent_metrics.recent_agent_activity AS
SELECT
    id,
    agent_name,
    event_type,
    event_status,
    query,
    tool_name,
    duration_ms,
    error_message,
    conversation_id,
    created_at
FROM agent_metrics.agent_events
ORDER BY created_at DESC
LIMIT 100;

-- ─────────────────────────────────────────────────────────────────────────────
-- Comments
-- ─────────────────────────────────────────────────────────────────────────────

COMMENT ON SCHEMA agent_metrics IS 'Agent health monitoring and telemetry data';
COMMENT ON TABLE agent_metrics.agent_health_checks IS 'Periodic health checks for each agent';
COMMENT ON TABLE agent_metrics.agent_events IS 'Audit log of all agent activities';
COMMENT ON TABLE agent_metrics.tool_execution_log IS 'Detailed tool execution tracking';
COMMENT ON TABLE agent_metrics.agent_performance_metrics IS 'Hourly aggregated performance metrics';

-- ═══════════════════════════════════════════════════════════════════════════
-- END OF MIGRATION
-- ═══════════════════════════════════════════════════════════════════════════
