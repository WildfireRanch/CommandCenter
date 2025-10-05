-- ═══════════════════════════════════════════════════════════════════════════
-- FILE: railway/migrations/001_agent_memory_schema.sql
-- PURPOSE: Initialize database schema for agent conversations and memory
--
-- WHAT IT DOES:
--   - Enables required extensions (TimescaleDB, pgvector)
--   - Creates tables for conversations, messages, and agent memory
--   - Sets up indexes for fast queries
--   - Configures TimescaleDB hypertables for time-series data
--
-- DEPENDENCIES:
--   - PostgreSQL 16+
--   - timescaledb extension
--   - pgvector extension
--
-- USAGE:
--   psql $DATABASE_URL < migrations/001_agent_memory_schema.sql
--
--   Or from Python:
--   python -m src.utils.db
-- ═══════════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. Enable Extensions
-- ─────────────────────────────────────────────────────────────────────────────

-- NOTE: Railway's TimescaleDB image pre-loads timescaledb extension
-- We only need to check/enable vector and uuid extensions

-- pgvector: Vector similarity search for embeddings
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector') THEN
        CREATE EXTENSION vector;
    END IF;
END $$;

-- uuid-ossp: UUID generation
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'uuid-ossp') THEN
        CREATE EXTENSION "uuid-ossp";
    END IF;
END $$;


-- ─────────────────────────────────────────────────────────────────────────────
-- 2. Create Schemas
-- ─────────────────────────────────────────────────────────────────────────────

-- Agent data schema
CREATE SCHEMA IF NOT EXISTS agent;

-- SolArk hardware data schema
CREATE SCHEMA IF NOT EXISTS solark;


-- ─────────────────────────────────────────────────────────────────────────────
-- 3. Agent Conversations Table
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent.conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Conversation metadata
    user_id TEXT,                    -- Optional user identifier
    agent_role TEXT NOT NULL,        -- e.g., "Energy Systems Monitor"
    status TEXT DEFAULT 'active',    -- active, archived, deleted

    -- Conversation summary (for quick reference)
    title TEXT,                      -- Auto-generated or user-provided
    summary TEXT,                    -- Brief summary of conversation

    -- Metrics
    message_count INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,

    -- Metadata (flexible JSON storage)
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for fast lookups
CREATE INDEX IF NOT EXISTS idx_conversations_created_at
    ON agent.conversations(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id
    ON agent.conversations(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_agent_role
    ON agent.conversations(agent_role, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_conversations_status
    ON agent.conversations(status, created_at DESC);

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION agent.update_conversations_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER conversations_update_timestamp
    BEFORE UPDATE ON agent.conversations
    FOR EACH ROW
    EXECUTE FUNCTION agent.update_conversations_timestamp();


-- ─────────────────────────────────────────────────────────────────────────────
-- 4. Messages Table
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent.messages (
    id UUID DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES agent.conversations(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Message content
    role TEXT NOT NULL,              -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,

    -- Agent execution details
    agent_role TEXT,                 -- Which agent generated this (if assistant)
    tool_calls JSONB,                -- Tools called during this message
    tool_results JSONB,              -- Results from tool calls

    -- Metrics
    tokens_used INTEGER,
    duration_ms INTEGER,             -- Time to generate (if assistant message)

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb,

    -- Composite primary key including the partitioning column for TimescaleDB
    PRIMARY KEY (id, created_at)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id
    ON agent.messages(conversation_id, created_at ASC);

CREATE INDEX IF NOT EXISTS idx_messages_created_at
    ON agent.messages(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_messages_role
    ON agent.messages(role);

-- Convert to TimescaleDB hypertable (time-series optimization)
SELECT create_hypertable(
    'agent.messages',
    'created_at',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);


-- ─────────────────────────────────────────────────────────────────────────────
-- 5. Agent Memory Table (Long-term Memory with Embeddings)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent.memory (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Memory content
    agent_role TEXT NOT NULL,        -- Which agent this memory belongs to
    memory_type TEXT NOT NULL,       -- 'fact', 'insight', 'preference', 'context'
    content TEXT NOT NULL,           -- The actual memory text

    -- Vector embedding for semantic search (1536 dimensions for OpenAI)
    embedding vector(1536),

    -- Importance and retention
    importance REAL DEFAULT 0.5,     -- 0.0 to 1.0, affects retention
    access_count INTEGER DEFAULT 0,  -- How many times accessed
    last_accessed_at TIMESTAMPTZ,

    -- Context (no FK to messages due to composite PK)
    conversation_id UUID REFERENCES agent.conversations(id) ON DELETE SET NULL,
    source_message_id UUID,          -- No FK - messages has composite PK

    -- Metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_memory_agent_role
    ON agent.memory(agent_role, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_memory_type
    ON agent.memory(memory_type);

CREATE INDEX IF NOT EXISTS idx_memory_conversation
    ON agent.memory(conversation_id);

-- Vector similarity index (HNSW - Hierarchical Navigable Small World)
CREATE INDEX IF NOT EXISTS idx_memory_embedding
    ON agent.memory
    USING hnsw (embedding vector_cosine_ops);

-- Auto-update updated_at timestamp
CREATE TRIGGER memory_update_timestamp
    BEFORE UPDATE ON agent.memory
    FOR EACH ROW
    EXECUTE FUNCTION agent.update_conversations_timestamp();


-- ─────────────────────────────────────────────────────────────────────────────
-- 6. Agent Logs Table (System Events and Debugging)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS agent.logs (
    id BIGSERIAL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Log details
    level TEXT NOT NULL,             -- 'debug', 'info', 'warning', 'error'
    agent_role TEXT,
    event_type TEXT NOT NULL,        -- 'task_start', 'task_complete', 'tool_call', 'error'
    message TEXT NOT NULL,

    -- Context (no foreign keys on hypertables - use application-level constraints)
    conversation_id UUID,
    message_id UUID,

    -- Additional data
    data JSONB DEFAULT '{}'::jsonb,

    -- Composite primary key including the partitioning column for TimescaleDB
    PRIMARY KEY (id, created_at)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_logs_created_at
    ON agent.logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_logs_level
    ON agent.logs(level, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_logs_event_type
    ON agent.logs(event_type, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_logs_conversation
    ON agent.logs(conversation_id, created_at DESC);

-- Note: Foreign keys on hypertables can cause issues with partitioning
-- We'll enforce referential integrity at the application level

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'agent.logs',
    'created_at',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '7 days'
);


-- ─────────────────────────────────────────────────────────────────────────────
-- 7. SolArk Plant Flow Table (Real-time Energy Data)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS solark.plant_flow (
    id BIGSERIAL,
    plant_id INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Power metrics (watts)
    pv_power INTEGER,                -- Solar production
    batt_power INTEGER,              -- Battery charge/discharge
    grid_power INTEGER,              -- Grid import/export
    load_power INTEGER,              -- House load
    gen_power INTEGER,               -- Generator (if exists)
    min_power INTEGER,               -- Minimum power

    -- Battery state
    soc REAL,                        -- State of charge (%)

    -- Flow indicators (boolean flags)
    pv_to_load BOOLEAN,
    pv_to_grid BOOLEAN,
    pv_to_bat BOOLEAN,
    bat_to_load BOOLEAN,
    grid_to_load BOOLEAN,
    gen_to_load BOOLEAN,

    -- System flags
    exists_gen BOOLEAN,
    exists_min BOOLEAN,
    gen_on BOOLEAN,
    micro_on BOOLEAN,
    exists_meter BOOLEAN,
    bms_comm_fault_flag BOOLEAN,

    -- Additional data
    pv_details TEXT,
    exist_think_power BOOLEAN,

    -- Raw JSON for debugging
    raw_json JSONB,

    -- Composite primary key including the partitioning column for TimescaleDB
    PRIMARY KEY (id, created_at)
);

-- Indexes for fast time-range queries
CREATE INDEX IF NOT EXISTS idx_plant_flow_created_at
    ON solark.plant_flow(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_plant_flow_plant_id
    ON solark.plant_flow(plant_id, created_at DESC);

-- Convert to TimescaleDB hypertable
SELECT create_hypertable(
    'solark.plant_flow',
    'created_at',
    if_not_exists => TRUE,
    chunk_time_interval => INTERVAL '1 day'
);


-- ─────────────────────────────────────────────────────────────────────────────
-- 8. Helper Functions
-- ─────────────────────────────────────────────────────────────────────────────

-- Function to increment message count when a message is added
CREATE OR REPLACE FUNCTION agent.increment_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE agent.conversations
    SET message_count = message_count + 1,
        updated_at = NOW()
    WHERE id = NEW.conversation_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER messages_increment_count
    AFTER INSERT ON agent.messages
    FOR EACH ROW
    EXECUTE FUNCTION agent.increment_message_count();


-- Function to update memory access tracking
CREATE OR REPLACE FUNCTION agent.track_memory_access()
RETURNS TRIGGER AS $$
BEGIN
    NEW.access_count = OLD.access_count + 1;
    NEW.last_accessed_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Note: This trigger would be activated by application code when memory is retrieved
-- Not automatically triggered by SELECT queries


-- ─────────────────────────────────────────────────────────────────────────────
-- 9. Grant Permissions (if needed for specific users)
-- ─────────────────────────────────────────────────────────────────────────────

-- Grant usage on schemas
GRANT USAGE ON SCHEMA agent TO PUBLIC;
GRANT USAGE ON SCHEMA solark TO PUBLIC;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA agent TO PUBLIC;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA solark TO PUBLIC;

-- Grant sequence usage
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA agent TO PUBLIC;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA solark TO PUBLIC;


-- ═══════════════════════════════════════════════════════════════════════════
-- MIGRATION COMPLETE
-- ═══════════════════════════════════════════════════════════════════════════

-- Verify extensions
DO $$
BEGIN
    RAISE NOTICE '✅ Migration complete!';
    RAISE NOTICE '📦 Extensions enabled: timescaledb, vector, uuid-ossp';
    RAISE NOTICE '📋 Schemas created: agent, solark';
    RAISE NOTICE '📊 Tables created:';
    RAISE NOTICE '   - agent.conversations';
    RAISE NOTICE '   - agent.messages (hypertable)';
    RAISE NOTICE '   - agent.memory (with vector embeddings)';
    RAISE NOTICE '   - agent.logs (hypertable)';
    RAISE NOTICE '   - solark.plant_flow (hypertable)';
END;
$$;
