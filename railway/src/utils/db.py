# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/utils/db.py
# PURPOSE: Database connection and query utilities
#
# WHAT IT DOES:
#   - Manages PostgreSQL connection pool
#   - Provides helper functions for common queries
#   - Handles connection errors gracefully
#
# DEPENDENCIES:
#   - psycopg2-binary (PostgreSQL adapter)
#   - python-dotenv (environment variables)
#
# ENVIRONMENT VARIABLES:
#   - DATABASE_URL: PostgreSQL connection string (from Railway)
#
# USAGE:
#   from utils.db import get_connection, query_one, query_all
#   
#   with get_connection() as conn:
#       result = query_one(conn, "SELECT * FROM table WHERE id = %s", (1,))
# ═══════════════════════════════════════════════════════════════════════════

import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple

import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError(
        "DATABASE_URL not set. Configure it in Railway or your .env file."
    )

# Connection pool (reuse connections for performance)
# Start with 2 connections, max 10
_connection_pool: Optional[SimpleConnectionPool] = None


# ─────────────────────────────────────────────────────────────────────────────
# Connection Pool Management
# ─────────────────────────────────────────────────────────────────────────────

def get_pool() -> SimpleConnectionPool:
    """
    Get or create the connection pool.
    
    WHAT: Lazy-loads connection pool on first use
    WHY: Reusing connections is much faster than creating new ones
    HOW: Creates pool once, returns same instance on subsequent calls
    
    Returns:
        SimpleConnectionPool: Shared connection pool
    """
    global _connection_pool
    
    if _connection_pool is None:
        _connection_pool = SimpleConnectionPool(
            minconn=2,      # Minimum connections to keep open
            maxconn=10,     # Maximum connections allowed
            dsn=DATABASE_URL,
        )
    
    return _connection_pool


@contextmanager
def get_connection():
    """
    Get a database connection from the pool.
    
    WHAT: Context manager that provides a connection and returns it to pool
    WHY: Ensures connections are always returned, even on errors
    HOW: Gets from pool, yields to caller, returns on exit
    
    Yields:
        psycopg2.connection: Database connection
        
    Example:
        >>> with get_connection() as conn:
        ...     cursor = conn.cursor()
        ...     cursor.execute("SELECT 1")
    """
    pool = get_pool()
    conn = pool.getconn()
    
    try:
        yield conn
    finally:
        # Always return connection to pool, even on error
        pool.putconn(conn)


def close_pool():
    """
    Close all connections in the pool.
    
    WHAT: Shuts down the connection pool
    WHY: Clean shutdown when application stops
    HOW: Closes all connections and resets pool
    
    Use this on application shutdown (not needed in Railway - it handles it)
    """
    global _connection_pool
    
    if _connection_pool is not None:
        _connection_pool.closeall()
        _connection_pool = None


# ─────────────────────────────────────────────────────────────────────────────
# Query Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def query_one(
    conn,
    query: str,
    params: Optional[Tuple] = None,
    as_dict: bool = True,
) -> Optional[Dict[str, Any]]:
    """
    Execute query and return single row.
    
    WHAT: Runs SELECT query, returns first row or None
    WHY: Common pattern - get one record by ID, latest record, etc.
    HOW: Execute query, fetch one, return as dict or tuple
    
    Args:
        conn: Database connection from get_connection()
        query: SQL query with %s placeholders
        params: Tuple of parameters to substitute
        as_dict: Return as dict (True) or tuple (False)
        
    Returns:
        Dict or tuple for the row, or None if no results
        
    Example:
        >>> with get_connection() as conn:
        ...     row = query_one(
        ...         conn,
        ...         "SELECT * FROM users WHERE id = %s",
        ...         (123,)
        ...     )
        ...     print(row["name"])
    """
    cursor_factory = RealDictCursor if as_dict else None
    
    with conn.cursor(cursor_factory=cursor_factory) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchone()


def query_all(
    conn,
    query: str,
    params: Optional[Tuple] = None,
    as_dict: bool = True,
) -> List[Dict[str, Any]]:
    """
    Execute query and return all rows.
    
    WHAT: Runs SELECT query, returns list of all rows
    WHY: Common pattern - get multiple records
    HOW: Execute query, fetch all, return as list of dicts or tuples
    
    Args:
        conn: Database connection from get_connection()
        query: SQL query with %s placeholders
        params: Tuple of parameters to substitute
        as_dict: Return as dicts (True) or tuples (False)
        
    Returns:
        List of dicts or tuples, empty list if no results
        
    Example:
        >>> with get_connection() as conn:
        ...     rows = query_all(
        ...         conn,
        ...         "SELECT * FROM users WHERE active = %s",
        ...         (True,)
        ...     )
        ...     for row in rows:
        ...         print(row["name"])
    """
    cursor_factory = RealDictCursor if as_dict else None
    
    with conn.cursor(cursor_factory=cursor_factory) as cursor:
        cursor.execute(query, params or ())
        return cursor.fetchall()


def execute(
    conn,
    query: str,
    params: Optional[Tuple] = None,
    commit: bool = True,
) -> int:
    """
    Execute INSERT/UPDATE/DELETE query.
    
    WHAT: Runs a query that modifies data
    WHY: Common pattern - insert, update, or delete records
    HOW: Execute query, optionally commit, return affected row count
    
    Args:
        conn: Database connection from get_connection()
        query: SQL query with %s placeholders
        params: Tuple of parameters to substitute
        commit: Automatically commit transaction (default: True)
        
    Returns:
        int: Number of rows affected
        
    Example:
        >>> with get_connection() as conn:
        ...     rows_affected = execute(
        ...         conn,
        ...         "UPDATE users SET active = %s WHERE id = %s",
        ...         (False, 123)
        ...     )
        ...     print(f"Updated {rows_affected} rows")
    """
    with conn.cursor() as cursor:
        cursor.execute(query, params or ())
        
        if commit:
            conn.commit()
        
        return cursor.rowcount


# ─────────────────────────────────────────────────────────────────────────────
# Schema Management
# ─────────────────────────────────────────────────────────────────────────────

def init_schema():
    """
    Initialize database schema (create tables if they don't exist).

    WHAT: Creates all required tables and extensions for CommandCenter
    WHY: First-time setup or schema updates
    HOW: Runs the main migration file

    Call this once when deploying to new database.
    """
    from pathlib import Path

    # Load migration SQL from file
    migration_file = Path(__file__).parent.parent.parent / "migrations" / "001_agent_memory_schema.sql"

    if not migration_file.exists():
        print(f"⚠️  Migration file not found: {migration_file}")
        print("   Using fallback schema creation...")
        _create_fallback_schema()
        return

    print(f"📋 Running migration: {migration_file.name}")
    schema_sql = migration_file.read_text()

    with get_connection() as conn:
        conn.autocommit = True  # Required for CREATE EXTENSION and hypertables
        with conn.cursor() as cursor:
            try:
                cursor.execute(schema_sql)
                print("✅ Database schema initialized from migration file")
            except Exception as e:
                print(f"❌ Migration failed: {e}")
                raise


def _create_fallback_schema():
    """Fallback schema creation if migration file not found."""
    schema_sql = """
    -- Enable PostgreSQL extensions
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS vector;
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

    -- Create schemas
    CREATE SCHEMA IF NOT EXISTS agent;
    CREATE SCHEMA IF NOT EXISTS solark;

    -- Basic agent.conversations table
    CREATE TABLE IF NOT EXISTS agent.conversations (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        user_id TEXT,
        agent_role TEXT NOT NULL,
        status TEXT DEFAULT 'active',
        title TEXT,
        summary TEXT,
        message_count INTEGER DEFAULT 0,
        total_tokens INTEGER DEFAULT 0,
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- Basic agent.messages table
    CREATE TABLE IF NOT EXISTS agent.messages (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        conversation_id UUID NOT NULL REFERENCES agent.conversations(id) ON DELETE CASCADE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        agent_role TEXT,
        tool_calls JSONB,
        tool_results JSONB,
        tokens_used INTEGER,
        duration_ms INTEGER,
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- Basic agent.memory table
    CREATE TABLE IF NOT EXISTS agent.memory (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        agent_role TEXT NOT NULL,
        memory_type TEXT NOT NULL,
        content TEXT NOT NULL,
        embedding vector(1536),
        importance REAL DEFAULT 0.5,
        access_count INTEGER DEFAULT 0,
        last_accessed_at TIMESTAMPTZ,
        conversation_id UUID REFERENCES agent.conversations(id) ON DELETE SET NULL,
        metadata JSONB DEFAULT '{}'::jsonb
    );

    -- SolArk plant flow data (real-time snapshots)
    CREATE TABLE IF NOT EXISTS solark.plant_flow (
        id BIGSERIAL PRIMARY KEY,
        plant_id INTEGER NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        -- Power metrics (watts)
        pv_power INTEGER,
        batt_power INTEGER,
        grid_power INTEGER,
        load_power INTEGER,
        gen_power INTEGER,
        min_power INTEGER,

        -- Battery state
        soc REAL,

        -- Flow indicators
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
        raw_json JSONB
    );

    -- Create basic indexes
    CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON agent.conversations(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON agent.messages(conversation_id, created_at ASC);
    CREATE INDEX IF NOT EXISTS idx_memory_agent_role ON agent.memory(agent_role, created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_plant_flow_created_at ON solark.plant_flow(created_at DESC);
    CREATE INDEX IF NOT EXISTS idx_plant_flow_plant_id ON solark.plant_flow(plant_id, created_at DESC);
    """

    with get_connection() as conn:
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)

    print("✅ Database schema initialized (fallback)")


# ─────────────────────────────────────────────────────────────────────────────
# Health Check
# ─────────────────────────────────────────────────────────────────────────────

def check_connection() -> bool:
    """
    Check if database connection is working.
    
    WHAT: Tests database connectivity
    WHY: Health checks, startup validation
    HOW: Runs simple SELECT 1 query
    
    Returns:
        bool: True if connection works, False otherwise
    """
    try:
        with get_connection() as conn:
            result = query_one(conn, "SELECT 1 AS test", as_dict=True)
            return result is not None and result.get("test") == 1
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test database connection and setup."""
    print("🔍 Testing database connection...")
    
    if check_connection():
        print("✅ Database connection successful!")
        
        # Initialize schema
        print("\n📋 Initializing schema...")
        init_schema()
        
        # Test query
        print("\n🔍 Testing query...")
        with get_connection() as conn:
            result = query_one(
                conn,
                "SELECT current_database() as db, version() as version",
                as_dict=True,
            )
            print(f"📊 Connected to: {result['db']}")
            print(f"🐘 PostgreSQL: {result['version'][:50]}...")
        
    else:
        print("❌ Database connection failed!")
        print("   Check DATABASE_URL environment variable")
        import sys
        sys.exit(1)