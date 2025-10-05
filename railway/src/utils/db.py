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
    HOW: Enables extensions, then creates tables with optimizations
    
    Call this once when deploying to new database.
    """
    schema_sql = """
    -- Enable PostgreSQL extensions
    CREATE EXTENSION IF NOT EXISTS timescaledb;
    CREATE EXTENSION IF NOT EXISTS vector;
    
    -- Create schema for SolArk data
    CREATE SCHEMA IF NOT EXISTS solark;
    
    -- SolArk plant flow data (real-time snapshots)
    CREATE TABLE IF NOT EXISTS solark.plant_flow (
        id SERIAL PRIMARY KEY,
        plant_id INTEGER NOT NULL,
        ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        
        -- Power metrics (watts)
        pv_power INTEGER,
        batt_power INTEGER,
        grid_power INTEGER,
        load_power INTEGER,
        gen_power INTEGER,
        min_power INTEGER,
        
        -- Battery state
        soc REAL,  -- State of charge (%)
        
        -- Flow indicators (booleans)
        pv_to BOOLEAN,
        to_load BOOLEAN,
        to_grid BOOLEAN,
        to_bat BOOLEAN,
        bat_to BOOLEAN,
        grid_to BOOLEAN,
        gen_to BOOLEAN,
        min_to BOOLEAN,
        
        -- System flags
        exists_gen BOOLEAN,
        exists_min BOOLEAN,
        gen_on BOOLEAN,
        micro_on BOOLEAN,
        exists_meter BOOLEAN,
        bms_comm_fault_flag BOOLEAN,
        
        -- Additional data
        pv TEXT,
        exist_think_power BOOLEAN,
        
        -- Raw JSON for debugging
        raw_json JSONB
    );
    
    -- Index for fast time-range queries
    CREATE INDEX IF NOT EXISTS idx_plant_flow_ts 
        ON solark.plant_flow(ts DESC);
    
    -- Index for fast plant_id queries
    CREATE INDEX IF NOT EXISTS idx_plant_flow_plant_id 
        ON solark.plant_flow(plant_id, ts DESC);
    """
    
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
            conn.commit()
    
    print("✅ Database schema initialized")


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