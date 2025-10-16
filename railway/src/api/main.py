# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/main.py
# PURPOSE: FastAPI application entrypoint for CommandCenter backend
#
# WHAT IT DOES:
#   - Starts the API server
#   - Configures CORS for Vercel MCP integration
#   - Sets up health endpoints with database checks
#   - Loads CrewAI agent routes
#   - Provides request tracking and logging
#
# DEPENDENCIES:
#   - FastAPI (web framework)
#   - uvicorn (ASGI server)
#   - CrewAI (agent framework)
#   - psycopg2 (database adapter)
#
# ENVIRONMENT VARIABLES:
#   - ALLOWED_ORIGINS: Comma-separated list of allowed CORS origins
#   - OPENAI_API_KEY: OpenAI API key for CrewAI
#   - DATABASE_URL: PostgreSQL connection string (from Railway)
#   - SOLARK_EMAIL: SolArk Cloud login
#   - SOLARK_PASSWORD: SolArk Cloud password
#   - SOLARK_PLANT_ID: SolArk plant ID (optional, defaults to 146453)
#   - ENV: Environment name (development/production)
#
# RUNS ON:
#   - Railway (production): Auto-deployed from GitHub
#   - Local: uvicorn src.api.main:app --reload
# ═══════════════════════════════════════════════════════════════════════════

import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

# Load environment variables from repo root
root_dir = Path(__file__).parent.parent.parent
env_file = root_dir / ".env"
load_dotenv(dotenv_path=env_file)

# Import agents and utilities
from ..agents.manager import create_manager_crew
from ..utils.db import check_connection as check_db_connection

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("commandcenter.api")


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    message: str
    session_id: Optional[str] = None  # For multi-turn conversations
    user_id: Optional[str] = None  # For context personalization (V1.8+)

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's my battery level?",
                "session_id": "optional-conversation-uuid",
                "user_id": "optional-user-id"
            }
        }


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    response: str
    query: str
    agent_role: str
    duration_ms: int
    session_id: str  # Conversation ID for continuing the conversation
    # V1.8: Smart Context metadata
    context_tokens: Optional[int] = None  # Tokens used for context
    cache_hit: Optional[bool] = None  # Was context loaded from cache?
    query_type: Optional[str] = None  # Classified query type (system/research/planning/general)

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your battery is at 52% and currently discharging at 3160W.",
                "query": "What's my battery level?",
                "agent_role": "Energy Systems Monitor",
                "duration_ms": 1250,
                "session_id": "abc123-uuid",
                "context_tokens": 2400,
                "cache_hit": False,
                "query_type": "system"
            }
        }


# ─────────────────────────────────────────────────────────────────────────────
# Configuration Helpers
# ─────────────────────────────────────────────────────────────────────────────

def parse_cors_origins(value: str | None) -> list[str]:
    """
    Parse CORS origins from environment variable.
    
    WHAT: Converts comma/space-separated string into list of origins
    WHY: CORS middleware needs a list, but env vars are strings
    HOW: Split by comma and spaces, strip whitespace, deduplicate
    
    Args:
        value: String like "https://app.com,https://api.com" or None
        
    Returns:
        List of unique origin URLs, empty list if value is None
    """
    if not value:
        return []
    
    # Split by comma first, then by spaces
    parts = [
        p.strip()
        for chunk in value.split(",")
        for p in chunk.split()
        if p.strip()
    ]
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(parts))


# ─────────────────────────────────────────────────────────────────────────────
# Middleware Classes
# ─────────────────────────────────────────────────────────────────────────────

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attach unique correlation ID to each request.
    
    WHAT: Adds a unique ID to every request/response
    WHY: Makes debugging easier - trace a single request through logs
    HOW: Checks for x-corr-id header, generates UUID if missing
    """
    
    async def dispatch(self, request: Request, call_next):
        # Get correlation ID from header or generate new one
        cid = request.headers.get("x-corr-id") or f"{uuid.uuid4().hex[:8]}"
        request.state.corr_id = cid
        
        # Process request
        response = await call_next(request)
        
        # Add correlation ID to response
        response.headers["x-corr-id"] = cid
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request with timing information.
    
    LOG FORMAT: request method=GET path=/health cid=abc123 status=200 dur_ms=45
    """
    
    async def dispatch(self, request: Request, call_next):
        t0 = time.perf_counter()
        method = request.method
        path = request.url.path
        status = None
        
        try:
            response = await call_next(request)
            status = response.status_code
            return response
        finally:
            dur_ms = int((time.perf_counter() - t0) * 1000)
            cid = getattr(request.state, "corr_id", "-")
            
            logger.info(
                "request method=%s path=%s cid=%s status=%s dur_ms=%s",
                method,
                path,
                cid,
                status if status is not None else "ERR",
                dur_ms
            )


# ─────────────────────────────────────────────────────────────────────────────
# Application Factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    WHAT: Builds the complete API server with all configuration
    WHY: Centralizes setup, makes testing easier
    HOW: Creates FastAPI instance, adds middleware, mounts routes
    """
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Application lifecycle management (startup/shutdown)."""
        # ─────────────────────────────────────────────────────────────────
        # STARTUP
        # ─────────────────────────────────────────────────────────────────
        print("🚀 CommandCenter API starting...")

        # Create required directories
        data_dir = Path(os.getenv("INDEX_ROOT", "./data/index"))
        data_dir.mkdir(parents=True, exist_ok=True)

        # Log configuration
        print(f"📋 Environment: {os.getenv('ENV', 'development')}")
        print(f"🔑 OpenAI API key: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
        print(f"☀️ SolArk credentials: {'✅' if os.getenv('SOLARK_EMAIL') else '❌'}")
        print(f"🗄️ Database configured: {'✅' if os.getenv('DATABASE_URL') else '❌'}")
        print(f"🔋 Victron credentials: {'✅' if os.getenv('VICTRON_VRM_USERNAME') else '❌'}")

        # Test database connection
        if os.getenv("DATABASE_URL"):
            if check_db_connection():
                print("🗄️ Database connected: ✅")
            else:
                print("🗄️ Database connected: ❌ (WARNING: Database unreachable)")

        # Start SolArk poller (V1.7) if credentials configured
        solark_task = None
        if os.getenv("SOLARK_EMAIL") and os.getenv("SOLARK_PASSWORD"):
            try:
                import asyncio
                from ..services.solark_poller import start_poller as start_solark_poller

                print("☀️ Starting SolArk poller...")
                solark_task = asyncio.create_task(start_solark_poller())
                print("☀️ SolArk poller: ✅")
            except Exception as e:
                print(f"☀️ SolArk poller: ❌ (WARNING: {e})")
        else:
            print("☀️ SolArk poller: ⏭️  (skipped - credentials not configured)")

        # Start Victron poller (V1.6) if credentials configured
        victron_task = None
        if os.getenv("VICTRON_VRM_USERNAME") and os.getenv("VICTRON_VRM_PASSWORD"):
            try:
                import asyncio
                from ..services.victron_poller import start_poller as start_victron_poller

                print("🔋 Starting Victron VRM poller...")
                victron_task = asyncio.create_task(start_victron_poller())
                print("🔋 Victron VRM poller: ✅")
            except Exception as e:
                print(f"🔋 Victron VRM poller: ❌ (WARNING: {e})")
        else:
            print("🔋 Victron VRM poller: ⏭️  (skipped - credentials not configured)")

        # Start Health Monitor (V1.8)
        health_monitor_task = None
        try:
            import asyncio
            from ..services.health_monitor import start_monitor

            print("🏥 Starting Health Monitor...")
            health_monitor_task = asyncio.create_task(start_monitor())
            print("🏥 Health Monitor: ✅")
        except Exception as e:
            print(f"🏥 Health Monitor: ❌ (WARNING: {e})")

        yield

        # ─────────────────────────────────────────────────────────────────
        # SHUTDOWN
        # ─────────────────────────────────────────────────────────────────
        print("👋 CommandCenter API shutting down...")

        # Stop SolArk poller
        if solark_task:
            try:
                from ..services.solark_poller import stop_poller as stop_solark_poller
                print("☀️ Stopping SolArk poller...")
                await stop_solark_poller()
                solark_task.cancel()
                try:
                    await solark_task
                except asyncio.CancelledError:
                    pass
                print("☀️ SolArk poller stopped: ✅")
            except Exception as e:
                print(f"☀️ SolArk poller stop error: {e}")

        # Stop Victron poller
        if victron_task:
            try:
                from ..services.victron_poller import stop_poller as stop_victron_poller
                print("🔋 Stopping Victron poller...")
                await stop_victron_poller()
                victron_task.cancel()
                try:
                    await victron_task
                except asyncio.CancelledError:
                    pass
                print("🔋 Victron poller stopped: ✅")
            except Exception as e:
                print(f"🔋 Victron poller stop error: {e}")

        # Stop Health Monitor
        if health_monitor_task:
            try:
                from ..services.health_monitor import stop_monitor
                print("🏥 Stopping Health Monitor...")
                await stop_monitor()
                health_monitor_task.cancel()
                try:
                    await health_monitor_task
                except asyncio.CancelledError:
                    pass
                print("🏥 Health Monitor stopped: ✅")
            except Exception as e:
                print(f"🏥 Health Monitor stop error: {e}")
    
    # Create FastAPI app
    app = FastAPI(
        title="CommandCenter API",
        description="CrewAI-powered energy management and automation backend",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # CORS Configuration
    # ─────────────────────────────────────────────────────────────────────────
    
    allowed_origins = parse_cors_origins(os.getenv("ALLOWED_ORIGINS"))
    app_env = os.getenv("ENV", "development").lower()
    
    # Development fallback: allow localhost
    if not allowed_origins and app_env in {"dev", "development"}:
        allowed_origins = [
            "http://localhost:3000",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
        ]
    
    if allowed_origins:
        logger.info("cors_config origins=%s", allowed_origins)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["x-corr-id"],
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Add Middlewares
    # ─────────────────────────────────────────────────────────────────────────
    
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(AccessLogMiddleware)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Health Endpoints
    # ─────────────────────────────────────────────────────────────────────────
    
    @app.get("/")
    async def root():
        """
        API root endpoint.
        
        Returns basic API info and links to documentation.
        """
        return {
            "name": "CommandCenter API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs",
            "health": "/health",
        }
    
    @app.get("/health")
    async def health_check():
        """
        Comprehensive health check endpoint.
        
        WHAT: Returns detailed status of all system components
        WHY: Used by Railway, monitoring, and debugging
        HOW: Checks API, database, and service configurations
        
        Returns:
            dict: Health status with component checks
            
        Example response:
            {
                "status": "healthy",
                "checks": {
                    "api": "ok",
                    "openai_configured": true,
                    "solark_configured": true,
                    "database_configured": true,
                    "database_connected": true
                },
                "timestamp": 1234567890.123
            }
        """
        checks = {
            "api": "ok",
            "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
            "solark_configured": bool(os.getenv("SOLARK_EMAIL") and os.getenv("SOLARK_PASSWORD")),
            "database_configured": bool(os.getenv("DATABASE_URL")),
            "database_connected": check_db_connection() if os.getenv("DATABASE_URL") else False,
        }
        
        # System is healthy if core dependencies are working
        # SolArk is optional (not all queries need it)
        healthy = (
            checks["api"] == "ok" and
            checks["openai_configured"] and
            checks["database_connected"]
        )
        
        return {
            "status": "healthy" if healthy else "degraded",
            "checks": checks,
            "timestamp": time.time(),
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Database Management Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    @app.post("/db/init-schema")
    async def initialize_schema():
        """
        Initialize database schema (run migrations).

        WHAT: Creates all tables, extensions, and indexes
        WHY: First-time setup or schema updates
        HOW: Runs migration SQL file via db.init_schema()

        Returns:
            dict: Success status and message

        Raises:
            HTTPException: If schema initialization fails
        """
        try:
            from ..utils.db import init_schema

            logger.info("schema_init_requested")
            init_schema()
            logger.info("schema_init_completed")

            return {
                "status": "success",
                "message": "Database schema initialized successfully",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("schema_init_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Schema initialization failed: {str(e)}"
            )

    @app.post("/db/run-health-migration")
    async def run_health_monitoring_migration():
        """
        Run health monitoring migration specifically.

        WHAT: Creates monitoring schema and health_snapshots table
        WHY: Dedicated endpoint for troubleshooting migration issues
        HOW: Runs 004_health_monitoring.sql with detailed logging

        Returns:
            dict: Migration status with detailed output
        """
        try:
            import subprocess
            import tempfile
            from pathlib import Path
            import os

            logger.info("health_migration_requested")

            # Find migration file
            migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
            migration_file = migrations_dir / "004_health_monitoring.sql"

            if not migration_file.exists():
                return {
                    "status": "error",
                    "message": f"Migration file not found: {migration_file}",
                    "file_path": str(migration_file),
                    "migrations_dir_exists": migrations_dir.exists(),
                }

            # Read SQL
            schema_sql = migration_file.read_text()

            # Get DATABASE_URL
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return {
                    "status": "error",
                    "message": "DATABASE_URL not set"
                }

            # Try using psql first
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                    f.write(schema_sql)
                    temp_file = f.name

                result = subprocess.run(
                    ['psql', db_url, '-f', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                os.unlink(temp_file)

                if result.returncode == 0:
                    logger.info("health_migration_completed_via_psql")
                    return {
                        "status": "success",
                        "message": "Migration completed via psql",
                        "method": "psql",
                        "stdout": result.stdout,
                        "timestamp": time.time(),
                    }
                else:
                    return {
                        "status": "error",
                        "message": "psql execution failed",
                        "method": "psql",
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }

            except FileNotFoundError:
                # psql not available, use psycopg2
                logger.info("psql_not_found_using_psycopg2")
                from ..utils.db import get_connection

                with get_connection() as conn:
                    conn.autocommit = True
                    cursor = conn.cursor()

                    # Execute each statement separately
                    statements = [s.strip() for s in schema_sql.split(';') if s.strip() and not s.strip().startswith('--')]

                    executed = []
                    errors = []

                    for i, stmt in enumerate(statements):
                        try:
                            if stmt:
                                cursor.execute(stmt + ';')
                                executed.append(f"Statement {i+1}: OK")
                        except Exception as e:
                            errors.append(f"Statement {i+1}: {str(e)[:100]}")

                    cursor.close()

                    if errors:
                        return {
                            "status": "partial",
                            "message": f"Executed {len(executed)}/{len(statements)} statements",
                            "method": "psycopg2",
                            "executed": executed,
                            "errors": errors,
                        }
                    else:
                        logger.info("health_migration_completed_via_psycopg2")
                        return {
                            "status": "success",
                            "message": "Migration completed via psycopg2",
                            "method": "psycopg2",
                            "executed": executed,
                            "timestamp": time.time(),
                        }

        except Exception as e:
            logger.exception("health_migration_failed error=%s", e)
            return {
                "status": "error",
                "message": str(e),
                "type": type(e).__name__,
            }

    @app.post("/db/run-solark-migration")
    async def run_solark_migration():
        """
        Run SolArk schema migration specifically.

        WHAT: Creates solark schema and solark.telemetry hypertable
        WHY: Fix /system/stats endpoint error - table missing
        HOW: Runs 005_solark_schema.sql with detailed logging

        Returns:
            dict: Migration status with detailed output
        """
        try:
            import subprocess
            import tempfile
            from pathlib import Path
            import os

            logger.info("solark_migration_requested")

            # Find migration file
            migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
            migration_file = migrations_dir / "005_solark_schema.sql"

            if not migration_file.exists():
                return {
                    "status": "error",
                    "message": f"Migration file not found: {migration_file}",
                    "file_path": str(migration_file),
                    "migrations_dir_exists": migrations_dir.exists(),
                }

            # Read SQL
            schema_sql = migration_file.read_text()

            # Get DATABASE_URL
            db_url = os.getenv('DATABASE_URL')
            if not db_url:
                return {
                    "status": "error",
                    "message": "DATABASE_URL not set"
                }

            # Try using psql first (required for DO blocks)
            try:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
                    f.write(schema_sql)
                    temp_file = f.name

                result = subprocess.run(
                    ['psql', db_url, '-f', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=30
                )

                os.unlink(temp_file)

                if result.returncode == 0:
                    logger.info("solark_migration_completed_via_psql")
                    return {
                        "status": "success",
                        "message": "SolArk migration completed via psql",
                        "method": "psql",
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "timestamp": time.time(),
                    }
                else:
                    return {
                        "status": "error",
                        "message": "psql execution failed",
                        "method": "psql",
                        "returncode": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                    }

            except FileNotFoundError:
                return {
                    "status": "error",
                    "message": "psql not found - required for multi-statement SQL with DO blocks",
                    "help": "Install postgresql-client in Docker container"
                }

        except Exception as e:
            logger.exception("solark_migration_failed error=%s", e)
            return {
                "status": "error",
                "message": str(e),
                "type": type(e).__name__,
            }

    @app.post("/db/create-victron-tables")
    async def create_victron_tables():
        """
        Create Victron database tables (temporary emergency fix).

        WHAT: Creates victron schema and required tables
        WHY: Migration failing due to TimescaleDB dependency
        HOW: Direct SQL execution

        Returns:
            dict: Success status and table names created
        """
        try:
            from ..utils.db import get_connection

            logger.info("victron_tables_creation_requested")

            with get_connection() as conn:
                conn.autocommit = True
                cursor = conn.cursor()

                # Create schema
                cursor.execute("CREATE SCHEMA IF NOT EXISTS victron;")

                # Create battery_readings table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS victron.battery_readings (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    installation_id VARCHAR(100),
                    soc FLOAT NOT NULL,
                    voltage FLOAT,
                    current FLOAT,
                    power FLOAT,
                    state VARCHAR(20),
                    temperature FLOAT,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """)

                # Create polling_status table
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS victron.polling_status (
                    id SERIAL PRIMARY KEY,
                    last_poll_attempt TIMESTAMPTZ,
                    last_successful_poll TIMESTAMPTZ,
                    last_error TEXT,
                    requests_this_hour INTEGER DEFAULT 0,
                    hour_window_start TIMESTAMPTZ DEFAULT NOW(),
                    consecutive_failures INTEGER DEFAULT 0,
                    is_healthy BOOLEAN DEFAULT TRUE,
                    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );
                """)

                # Insert default polling status
                cursor.execute("""
                INSERT INTO victron.polling_status (id, updated_at)
                VALUES (1, NOW())
                ON CONFLICT (id) DO NOTHING;
                """)

                # Create indexes
                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_battery_readings_timestamp
                    ON victron.battery_readings(timestamp DESC);
                """)

                cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_battery_readings_installation
                    ON victron.battery_readings(installation_id, timestamp DESC);
                """)

                # Verify
                cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'victron'
                ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                table_names = [t[0] for t in tables]

                cursor.close()

            logger.info(f"victron_tables_created tables={table_names}")

            return {
                "status": "success",
                "message": "Victron tables created successfully",
                "tables": table_names,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.exception("victron_tables_creation_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create Victron tables: {str(e)}"
            )

    @app.post("/db/migrate-kb-schema")
    async def migrate_kb_schema():
        """
        Migrate KB schema (add folder_path and mime_type columns).

        WHAT: Adds folder_path and mime_type columns and index to kb_documents table
        WHY: Support for recursive folder scanning and file type tracking (Session 018C)
        HOW: Checks if columns exist, adds if missing, creates index

        Returns:
            dict: Success status and message

        Raises:
            HTTPException: If migration fails
        """
        try:
            from ..utils.db import get_connection, execute, query_one

            logger.info("kb_schema_migration_requested")
            messages = []

            with get_connection() as conn:
                # Check if folder_path column exists
                result = query_one(
                    conn,
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'kb_documents'
                    AND column_name = 'folder_path'
                    """
                )

                if result:
                    msg = "folder_path column already exists"
                    logger.info(msg)
                    messages.append(msg)
                else:
                    logger.info("Adding folder_path column...")
                    execute(
                        conn,
                        "ALTER TABLE kb_documents ADD COLUMN folder_path VARCHAR(1000)",
                        commit=True
                    )
                    msg = "folder_path column added successfully"
                    logger.info(msg)
                    messages.append(msg)

                # Check if mime_type column exists
                result = query_one(
                    conn,
                    """
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'kb_documents'
                    AND column_name = 'mime_type'
                    """
                )

                if result:
                    msg = "mime_type column already exists"
                    logger.info(msg)
                    messages.append(msg)
                else:
                    logger.info("Adding mime_type column...")
                    execute(
                        conn,
                        "ALTER TABLE kb_documents ADD COLUMN mime_type VARCHAR(200)",
                        commit=True
                    )
                    msg = "mime_type column added successfully"
                    logger.info(msg)
                    messages.append(msg)

                # Create index on folder_path for faster queries
                logger.info("Creating index on folder_path...")
                try:
                    execute(
                        conn,
                        """
                        CREATE INDEX IF NOT EXISTS idx_kb_documents_folder_path
                        ON kb_documents(folder_path)
                        """,
                        commit=True
                    )
                    logger.info("Index created successfully")
                except Exception as e:
                    logger.warning(f"Index may already exist: {e}")

            logger.info("kb_schema_migration_completed")

            return {
                "status": "success",
                "message": f"KB schema migration completed: {', '.join(messages)}",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("kb_schema_migration_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"KB schema migration failed: {str(e)}"
            )

    @app.post("/db/init-kb-schema")
    async def initialize_kb_schema():
        """
        Initialize Knowledge Base schema only.

        WHAT: Creates KB tables (kb_documents, kb_chunks, kb_sync_log)
        WHY: Add KB functionality to existing database
        HOW: Runs 001_knowledge_base.sql migration

        Returns:
            dict: Success status and message
        """
        try:
            from pathlib import Path
            from ..utils.db import get_connection

            migrations_dir = Path(__file__).parent.parent / "database" / "migrations"
            kb_migration = migrations_dir / "001_knowledge_base.sql"

            if not kb_migration.exists():
                raise HTTPException(
                    status_code=500,
                    detail=f"KB migration file not found: {kb_migration}"
                )

            logger.info("kb_schema_init_requested")
            sql = kb_migration.read_text()

            with get_connection() as conn:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(sql)

            logger.info("kb_schema_init_completed")

            return {
                "status": "success",
                "message": "Knowledge Base schema initialized successfully",
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("kb_schema_init_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"KB schema initialization failed: {str(e)}"
            )

    @app.get("/db/schema-status")
    async def schema_status():
        """
        Check database schema status.

        Returns information about tables, extensions, and hypertables.
        """
        try:
            from ..utils.db import get_connection, query_all

            with get_connection() as conn:
                # Get all tables
                tables = query_all(
                    conn,
                    """
                    SELECT table_schema, table_name
                    FROM information_schema.tables
                    WHERE table_schema IN ('agent', 'solark')
                    ORDER BY table_schema, table_name
                    """,
                    as_dict=True
                )

                # Get extensions
                extensions = query_all(
                    conn,
                    "SELECT extname, extversion FROM pg_extension WHERE extname IN ('timescaledb', 'vector', 'uuid-ossp')",
                    as_dict=True
                )

                # Try to get hypertables (may fail if timescaledb not loaded)
                try:
                    hypertables = query_all(
                        conn,
                        """
                        SELECT hypertable_schema, hypertable_name
                        FROM _timescaledb_catalog.hypertable
                        """,
                        as_dict=True
                    )
                except:
                    hypertables = []

                return {
                    "status": "success",
                    "tables": tables,
                    "extensions": extensions,
                    "hypertables": hypertables,
                    "timestamp": time.time(),
                }

        except Exception as e:
            logger.exception("schema_status_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Schema status check failed: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Energy Data Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/energy/latest")
    async def get_latest_energy():
        """
        Get the most recent energy system snapshot from database.

        Returns:
            dict: Latest energy data with timestamp
        """
        try:
            from ..utils.solark_storage import get_latest_snapshot

            snapshot = get_latest_snapshot()

            if not snapshot:
                return {
                    "status": "no_data",
                    "message": "No energy data available yet",
                    "timestamp": time.time(),
                }

            return {
                "status": "success",
                "data": snapshot,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_latest_energy_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get latest energy data: {str(e)}"
            )

    @app.get("/energy/recent")
    async def get_recent_energy(hours: int = 1, limit: int = 100):
        """
        Get recent energy data points.

        Args:
            hours: Number of hours to look back (default: 1)
            limit: Maximum number of records (default: 100, max: 1000)

        Returns:
            dict: List of energy data points
        """
        try:
            from ..utils.solark_storage import get_recent_data

            # Limit the maximum
            limit = min(limit, 1000)

            data = get_recent_data(hours=hours, limit=limit)

            return {
                "status": "success",
                "count": len(data),
                "hours": hours,
                "data": data,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_recent_energy_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get recent energy data: {str(e)}"
            )

    @app.get("/energy/stats")
    async def get_energy_statistics(hours: int = 24):
        """
        Get aggregated energy statistics.

        Args:
            hours: Number of hours to analyze (default: 24)

        Returns:
            dict: Statistical summary of energy data
        """
        try:
            from ..utils.solark_storage import get_energy_stats

            stats = get_energy_stats(hours=hours)

            if not stats or stats.get('total_records', 0) == 0:
                return {
                    "status": "no_data",
                    "message": f"No energy data available for the last {hours} hours",
                    "timestamp": time.time(),
                }

            return {
                "status": "success",
                "hours": hours,
                "stats": stats,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_energy_stats_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get energy statistics: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Victron Endpoints (V1.6)
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/victron/battery/current")
    async def get_victron_battery_current():
        """
        Get latest Victron battery reading.

        Returns the most recent battery data from Victron Cerbo GX including
        state of charge, voltage, current, power, temperature, and state.

        Returns:
            dict: Latest battery reading with all metrics
        """
        try:
            from ..utils.db import get_connection, query_one

            with get_connection() as conn:
                reading = query_one(
                    conn,
                    """
                    SELECT
                        timestamp,
                        installation_id,
                        soc,
                        voltage,
                        current,
                        power,
                        state,
                        temperature,
                        created_at
                    FROM victron.battery_readings
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """,
                    as_dict=True
                )

            if not reading:
                return {
                    "status": "no_data",
                    "message": "No Victron battery data available yet",
                    "timestamp": time.time(),
                }

            return {
                "status": "success",
                "data": {
                    "timestamp": reading["timestamp"].isoformat() if reading.get("timestamp") else None,
                    "installation_id": reading.get("installation_id"),
                    "soc": reading.get("soc"),
                    "voltage": reading.get("voltage"),
                    "current": reading.get("current"),
                    "power": reading.get("power"),
                    "state": reading.get("state"),
                    "temperature": reading.get("temperature"),
                },
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_victron_battery_current_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get Victron battery data: {str(e)}"
            )

    @app.get("/victron/battery/history")
    async def get_victron_battery_history(hours: int = 24, limit: int = 100):
        """
        Get historical Victron battery readings.

        Args:
            hours: Number of hours to look back (default: 24, max: 72)
            limit: Maximum number of records (default: 100, max: 1000)

        Returns:
            dict: List of battery readings over time
        """
        try:
            from ..utils.db import get_connection, query_all

            # Enforce limits (72 hours max due to retention policy)
            hours = min(hours, 72)
            limit = min(limit, 1000)

            with get_connection() as conn:
                readings = query_all(
                    conn,
                    """
                    SELECT
                        timestamp,
                        installation_id,
                        soc,
                        voltage,
                        current,
                        power,
                        state,
                        temperature
                    FROM victron.battery_readings
                    WHERE timestamp >= NOW() - INTERVAL '%s hours'
                    ORDER BY timestamp DESC
                    LIMIT %s
                    """,
                    (hours, limit),
                    as_dict=True
                )

            # Format timestamps
            formatted_readings = []
            for r in readings:
                formatted_readings.append({
                    "timestamp": r["timestamp"].isoformat() if r.get("timestamp") else None,
                    "installation_id": r.get("installation_id"),
                    "soc": r.get("soc"),
                    "voltage": r.get("voltage"),
                    "current": r.get("current"),
                    "power": r.get("power"),
                    "state": r.get("state"),
                    "temperature": r.get("temperature"),
                })

            return {
                "status": "success",
                "count": len(formatted_readings),
                "hours": hours,
                "data": formatted_readings,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_victron_battery_history_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get Victron battery history: {str(e)}"
            )

    @app.get("/victron/health")
    async def get_victron_health():
        """
        Check Victron integration health status.

        Returns poller status, API rate limits, and recent polling statistics.

        Returns:
            dict: Comprehensive health status
        """
        try:
            from ..utils.db import get_connection, query_one, query_all

            with get_connection() as conn:
                # Get polling status
                status = query_one(
                    conn,
                    "SELECT * FROM victron.polling_status WHERE id = 1",
                    as_dict=True
                )

                # Get count of readings in last 24 hours
                readings_count = query_one(
                    conn,
                    """
                    SELECT COUNT(*) as count
                    FROM victron.battery_readings
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    """,
                    as_dict=True
                )

            if not status:
                return {
                    "status": "not_initialized",
                    "message": "Victron poller not yet initialized",
                    "timestamp": time.time(),
                }

            return {
                "status": "success",
                "data": {
                    "poller_running": status.get("is_healthy", False),
                    "last_poll_attempt": status["last_poll_attempt"].isoformat() if status.get("last_poll_attempt") else None,
                    "last_successful_poll": status["last_successful_poll"].isoformat() if status.get("last_successful_poll") else None,
                    "last_error": status.get("last_error"),
                    "consecutive_failures": status.get("consecutive_failures", 0),
                    "is_healthy": status.get("is_healthy", False),
                    "readings_count_24h": readings_count.get("count", 0) if readings_count else 0,
                    "api_requests_this_hour": status.get("requests_this_hour", 0),
                    "rate_limit_max": 50,
                },
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_victron_health_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get Victron health status: {str(e)}"
            )

    @app.post("/victron/poll-now")
    async def trigger_victron_poll():
        """
        Manually trigger a Victron VRM API poll (for testing).

        This bypasses the normal 3-minute polling interval and fetches
        battery data immediately.

        Returns:
            dict: Battery data that was fetched
        """
        try:
            from ..services.victron_poller import get_poller

            poller = get_poller()
            data = await poller.poll_and_store()

            return {
                "status": "success",
                "message": "Poll completed successfully",
                "data": data,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("trigger_victron_poll_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger Victron poll: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # SolArk Poller Endpoints (V1.7)
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/solark/health")
    async def get_solark_health():
        """
        Check SolArk poller health status.

        Returns poller status and recent polling statistics.

        Returns:
            dict: Comprehensive health status
        """
        try:
            from ..services.solark_poller import get_poller
            from ..utils.db import get_connection, query_one

            # Get in-memory poller status
            poller = get_poller()
            health = poller.get_health_status()

            # Get count of readings in last 24 hours from database
            with get_connection() as conn:
                readings_count = query_one(
                    conn,
                    """
                    SELECT COUNT(*) as count
                    FROM solark.plant_flow
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                    """,
                    as_dict=True
                )

            return {
                "status": "success",
                "data": {
                    **health,
                    "readings_count_24h": readings_count.get("count", 0) if readings_count else 0,
                },
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_solark_health_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get SolArk health status: {str(e)}"
            )

    @app.post("/solark/poll-now")
    async def trigger_solark_poll():
        """
        Manually trigger a SolArk API poll (for testing).

        This bypasses the normal polling interval and fetches
        energy data immediately.

        Returns:
            dict: Energy data that was fetched
        """
        try:
            from ..services.solark_poller import get_poller

            poller = get_poller()
            data = await poller.poll_and_store()

            return {
                "status": "success",
                "message": "Poll completed successfully",
                "data": data,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("trigger_solark_poll_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to trigger SolArk poll: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Energy Analytics Endpoints (V1.7)
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/energy/history")
    async def get_energy_history(
        hours: int = Query(default=24, ge=1, le=720),
        limit: int = Query(default=1000, ge=1, le=5000)
    ):
        """
        Get historical energy data combining SolArk and Victron sources.

        Returns time-series data with:
        - Solar production (SolArk)
        - Battery SOC (Victron + SolArk)
        - Load consumption (SolArk)
        - Grid import/export (SolArk)
        - Battery voltage, current, temperature (Victron)

        Args:
            hours: Number of hours to look back (default: 24, max: 720/30 days)
            limit: Maximum number of records (default: 1000, max: 5000)

        Returns:
            dict: Time-series energy data with merged SolArk + Victron readings
        """
        try:
            from datetime import datetime, timedelta
            from ..utils.db import get_connection, query_all

            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            with get_connection() as conn:
                # Query SolArk data
                solark_data = query_all(
                    conn,
                    """
                    SELECT
                        created_at as timestamp,
                        pv_power,
                        batt_power as battery_power,
                        soc,
                        load_power,
                        grid_power
                    FROM solark.plant_flow
                    WHERE created_at >= %s AND created_at <= %s
                    ORDER BY created_at ASC
                    LIMIT %s
                    """,
                    (start_time, end_time, limit)
                )

                # Query Victron data (if schema exists)
                victron_data = []
                try:
                    victron_data = query_all(
                        conn,
                        """
                        SELECT
                            timestamp,
                            soc as victron_soc,
                            voltage,
                            current,
                            power as battery_power_victron,
                            temperature,
                            state
                        FROM victron.battery_readings
                        WHERE timestamp >= %s AND timestamp <= %s
                        ORDER BY timestamp ASC
                        LIMIT %s
                        """,
                        (start_time, end_time, limit)
                    )
                except Exception as victron_error:
                    # Victron schema doesn't exist yet, skip it
                    logger.warning(f"Victron data not available: {victron_error}")
                    victron_data = []

            # Merge datasets by timestamp (simple approach: create lookup dict)
            victron_by_time = {}
            for v in victron_data:
                # Round to nearest minute for matching
                time_key = v['timestamp'].replace(second=0, microsecond=0)
                victron_by_time[time_key] = v

            # Merge SolArk data with Victron data
            merged_data = []
            for s in solark_data:
                time_key = s['timestamp'].replace(second=0, microsecond=0)
                victron = victron_by_time.get(time_key, {})

                merged_data.append({
                    'timestamp': s['timestamp'].isoformat(),
                    'pv_power': s.get('pv_power', 0),
                    'battery_power': s.get('battery_power', 0),
                    'soc': s.get('soc', 0),
                    'load_power': s.get('load_power', 0),
                    'grid_power': s.get('grid_power', 0),
                    'victron_soc': victron.get('victron_soc'),
                    'voltage': victron.get('voltage'),
                    'current': victron.get('current'),
                    'temperature': victron.get('temperature'),
                    'battery_state': victron.get('state'),
                })

            return {
                "status": "success",
                "hours": hours,
                "count": len(merged_data),
                "data": merged_data,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.exception("get_energy_history_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch energy history: {str(e)}"
            )

    @app.get("/energy/analytics/daily")
    async def get_daily_analytics(
        days: int = Query(default=30, ge=1, le=365)
    ):
        """
        Get daily aggregated energy statistics.

        Returns:
        - Total solar production per day
        - Average battery SOC per day
        - Total load consumption per day
        - Grid import/export totals
        - Efficiency metrics
        - EXCESS ENERGY (wasted solar power)

        Args:
            days: Number of days to analyze (default: 30, max: 365)

        Returns:
            dict: Daily aggregated statistics with excess energy calculations
        """
        try:
            from datetime import datetime, timedelta
            from ..utils.db import get_connection, query_all

            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=days)

            with get_connection() as conn:
                # Query daily aggregates with excess energy calculation
                daily_stats = query_all(
                    conn,
                    """
                    SELECT
                        DATE(created_at) as date,
                        AVG(pv_power) as avg_solar,
                        MAX(pv_power) as peak_solar,
                        SUM(pv_power) / 60000.0 as total_solar_kwh,
                        AVG(soc) as avg_soc,
                        MIN(soc) as min_soc,
                        MAX(soc) as max_soc,
                        AVG(load_power) as avg_load,
                        SUM(load_power) / 60000.0 as total_load_kwh,
                        AVG(batt_power) as avg_battery_power,
                        SUM(CASE WHEN batt_power > 0 THEN batt_power ELSE 0 END) / 60000.0 as battery_charging_kwh,
                        SUM(CASE WHEN grid_power > 0 THEN grid_power ELSE 0 END) / 60000.0 as grid_import_kwh,
                        SUM(CASE WHEN grid_power < 0 THEN ABS(grid_power) ELSE 0 END) / 60000.0 as grid_export_kwh,
                        COUNT(*) as data_points
                    FROM solark.plant_flow
                    WHERE DATE(created_at) >= %s AND DATE(created_at) <= %s
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                    """,
                    (start_date, end_date)
                )

            # Calculate additional metrics including EXCESS ENERGY
            for day in daily_stats:
                day['date'] = day['date'].isoformat()

                # Convert Decimal to float for calculations
                total_solar = float(day['total_solar_kwh'] or 0)
                total_load = float(day['total_load_kwh'] or 0)
                grid_import = float(day['grid_import_kwh'] or 0)
                grid_export = float(day['grid_export_kwh'] or 0)
                battery_charging = float(day['battery_charging_kwh'] or 0)

                # Solar self-consumption percentage
                day['solar_self_consumption_pct'] = round(
                    (total_solar - grid_export) / total_solar * 100, 1
                ) if total_solar > 0 else 0

                # Grid independence percentage
                day['grid_independence_pct'] = round(
                    (total_load - grid_import) / total_load * 100, 1
                ) if total_load > 0 else 0

                # ⚡ CRITICAL: Calculate EXCESS (WASTED) ENERGY
                # Excess = Solar Production - (Load + Battery Charging)
                solar_used = total_load + battery_charging
                day['excess_energy_kwh'] = round(max(0, total_solar - solar_used), 2)

                # Excess as percentage of total solar
                day['excess_energy_pct'] = round(
                    day['excess_energy_kwh'] / total_solar * 100, 1
                ) if total_solar > 0 else 0

                # Potential value if excess was used (assuming $0.05/kWh value)
                day['excess_value_usd'] = round(day['excess_energy_kwh'] * 0.05, 2)

                # Round other values
                day['total_solar_kwh'] = round(total_solar, 2)
                day['total_load_kwh'] = round(total_load, 2)
                day['battery_charging_kwh'] = round(battery_charging, 2)
                day['grid_import_kwh'] = round(grid_import, 2)
                day['grid_export_kwh'] = round(grid_export, 2)
                day['avg_solar'] = round(float(day['avg_solar'] or 0), 0)
                day['peak_solar'] = round(float(day['peak_solar'] or 0), 0)
                day['avg_soc'] = round(float(day['avg_soc'] or 0), 1)
                day['min_soc'] = round(float(day['min_soc'] or 0), 1)
                day['max_soc'] = round(float(day['max_soc'] or 0), 1)
                day['avg_load'] = round(float(day['avg_load'] or 0), 0)

            return {
                "status": "success",
                "days": days,
                "count": len(daily_stats),
                "data": daily_stats,
                "timestamp": time.time()
            }

        except Exception as e:
            logger.exception("get_daily_analytics_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to fetch daily analytics: {str(e)}"
            )

    @app.get("/energy/analytics/cost")
    async def get_cost_analytics(
        start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
        end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
        import_rate: float = Query(default=0.12, description="Grid import rate ($/kWh)"),
        export_rate: float = Query(default=0.08, description="Grid export rate ($/kWh)")
    ):
        """
        Calculate energy costs and savings.

        Returns:
        - Grid import costs
        - Grid export revenue
        - Solar savings (avoided grid purchases)
        - Net savings
        - ROI metrics

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            import_rate: Grid import rate in $/kWh (default: 0.12)
            export_rate: Grid export rate in $/kWh (default: 0.08)

        Returns:
            dict: Cost analysis and savings calculations
        """
        try:
            from datetime import datetime
            from ..utils.db import get_connection, query_one

            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            with get_connection() as conn:
                # Query energy totals
                totals = query_one(
                    conn,
                    """
                    SELECT
                        SUM(CASE WHEN grid_power > 0 THEN grid_power ELSE 0 END) / 60000.0 as grid_import_kwh,
                        SUM(CASE WHEN grid_power < 0 THEN ABS(grid_power) ELSE 0 END) / 60000.0 as grid_export_kwh,
                        SUM(pv_power) / 60000.0 as total_solar_kwh,
                        SUM(load_power) / 60000.0 as total_load_kwh
                    FROM solark.plant_flow
                    WHERE created_at >= %s AND created_at <= %s
                    """,
                    (start, end),
                    as_dict=True
                )

            if not totals:
                raise HTTPException(status_code=404, detail="No data available for the specified period")

            # Calculate costs (convert Decimal to float for calculations)
            grid_import_kwh = float(totals['grid_import_kwh'] or 0)
            grid_export_kwh = float(totals['grid_export_kwh'] or 0)
            total_solar_kwh = float(totals['total_solar_kwh'] or 0)
            total_load_kwh = float(totals['total_load_kwh'] or 0)

            grid_import_cost = grid_import_kwh * import_rate
            grid_export_revenue = grid_export_kwh * export_rate

            # Solar savings = solar used directly (not exported) * import rate
            solar_self_consumed = total_solar_kwh - grid_export_kwh
            solar_savings = solar_self_consumed * import_rate

            net_savings = solar_savings + grid_export_revenue - grid_import_cost

            return {
                "status": "success",
                "period": {
                    "start": start_date,
                    "end": end_date,
                    "days": (end - start).days + 1
                },
                "energy": {
                    "solar_produced_kwh": round(total_solar_kwh, 2),
                    "load_consumed_kwh": round(total_load_kwh, 2),
                    "grid_import_kwh": round(grid_import_kwh, 2),
                    "grid_export_kwh": round(grid_export_kwh, 2),
                    "solar_self_consumed_kwh": round(solar_self_consumed, 2)
                },
                "costs": {
                    "grid_import_cost": round(grid_import_cost, 2),
                    "grid_export_revenue": round(grid_export_revenue, 2),
                    "solar_savings": round(solar_savings, 2),
                    "net_savings": round(net_savings, 2)
                },
                "rates": {
                    "import_rate_per_kwh": import_rate,
                    "export_rate_per_kwh": export_rate
                },
                "metrics": {
                    "solar_self_consumption_pct": round(
                        solar_self_consumed / total_solar_kwh * 100, 1
                    ) if total_solar_kwh > 0 else 0,
                    "grid_independence_pct": round(
                        (total_load_kwh - grid_import_kwh) / total_load_kwh * 100, 1
                    ) if total_load_kwh > 0 else 0
                },
                "timestamp": time.time()
            }

        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
        except Exception as e:
            logger.exception("get_cost_analytics_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to calculate costs: {str(e)}"
            )

    @app.get("/energy/predictions/soc")
    async def predict_battery_soc(
        hours: int = Query(default=24, ge=1, le=72, description="Hours to predict")
    ):
        """
        Predict future battery SOC based on historical patterns.

        Uses 7-day historical averages by hour-of-day and day-of-week
        to forecast battery state of charge.

        Args:
            hours: Number of hours to predict (default: 24, max: 72)

        Returns:
            dict: Predicted SOC values with confidence levels
        """
        try:
            from datetime import datetime, timedelta
            from ..utils.db import get_connection, query_all, query_one

            current_time = datetime.utcnow()

            # Get current SOC (try Victron first, fall back to SolArk)
            with get_connection() as conn:
                current_reading = None

                # Try Victron first (most accurate)
                try:
                    current_reading = query_one(
                        conn,
                        """
                        SELECT soc, voltage, current, power
                        FROM victron.battery_readings
                        ORDER BY timestamp DESC
                        LIMIT 1
                        """,
                        as_dict=True
                    )
                except Exception:
                    # Victron schema might not exist yet
                    pass

                if not current_reading:
                    # Fall back to SolArk
                    current_reading = query_one(
                        conn,
                        """
                        SELECT soc, batt_power as power
                        FROM solark.plant_flow
                        ORDER BY created_at DESC
                        LIMIT 1
                        """,
                        as_dict=True
                    )

                if not current_reading:
                    raise HTTPException(status_code=404, detail="No current battery data available")

                # Get historical patterns for each hour/day combination
                historical_patterns = query_all(
                    conn,
                    """
                    SELECT
                        EXTRACT(HOUR FROM created_at) as hour,
                        EXTRACT(DOW FROM created_at) as day_of_week,
                        AVG(batt_power) as avg_battery_power,
                        AVG(pv_power) as avg_solar_power
                    FROM solark.plant_flow
                    WHERE created_at >= NOW() - INTERVAL '7 days'
                    GROUP BY EXTRACT(HOUR FROM created_at), EXTRACT(DOW FROM created_at)
                    """,
                    ()
                )

            # Simple prediction: current SOC + estimated charge/discharge
            predictions = []
            predicted_soc = current_reading['soc']

            # Battery capacity assumption (adjust based on your system)
            battery_capacity_wh = 10000  # 10kWh

            for h in range(hours):
                future_time = current_time + timedelta(hours=h)
                hour = future_time.hour
                dow = future_time.weekday()

                # Find historical average for this hour/day
                pattern = next(
                    (p for p in historical_patterns if p['hour'] == hour and p['day_of_week'] == dow),
                    None
                )

                if pattern and pattern['avg_battery_power']:
                    # Estimate SOC change based on historical battery power
                    avg_power = pattern['avg_battery_power']
                    soc_change = (avg_power / battery_capacity_wh) * 100  # % change per hour
                    predicted_soc = max(0, min(100, predicted_soc + soc_change))
                    confidence = "medium"
                else:
                    # No historical data, assume no change
                    confidence = "low"

                predictions.append({
                    "timestamp": future_time.isoformat(),
                    "hour": hour,
                    "predicted_soc": round(predicted_soc, 1),
                    "confidence": confidence
                })

            return {
                "status": "success",
                "current_soc": round(current_reading['soc'], 1),
                "prediction_hours": hours,
                "predictions": predictions,
                "model": "historical_average_7d",
                "note": "Predictions based on 7-day historical patterns. Actual results may vary with weather and usage.",
                "timestamp": time.time()
            }

        except Exception as e:
            logger.exception("predict_battery_soc_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to predict SOC: {str(e)}"
            )

    @app.get("/energy/analytics/excess")
    async def get_excess_energy_analytics(
        hours: int = Query(default=24, ge=1, le=168, description="Hours to analyze")
    ):
        """
        ⚡ CRITICAL ENDPOINT: Track excess (wasted) solar energy.

        Excess Energy = Solar Production - (Load Consumption + Battery Charging)

        This represents lost opportunity to run additional loads like:
        - Bitcoin miners during peak solar
        - Irrigation pumps
        - Water heaters or HVAC
        - Other deferrable loads

        Args:
            hours: Number of hours to analyze (default: 24, max: 168/7 days)

        Returns:
            dict: Excess energy analysis with time-series data and recommendations
        """
        try:
            from datetime import datetime, timedelta
            from ..utils.db import get_connection, query_all

            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)

            with get_connection() as conn:
                # Query energy data with excess calculation
                excess_data = query_all(
                    conn,
                    """
                    SELECT
                        created_at as timestamp,
                        pv_power,
                        load_power,
                        batt_power as battery_power,
                        soc,
                        -- Calculate excess power in real-time
                        CASE
                            WHEN pv_power > (load_power + CASE WHEN batt_power > 0 THEN batt_power ELSE 0 END)
                            THEN pv_power - (load_power + CASE WHEN batt_power > 0 THEN batt_power ELSE 0 END)
                            ELSE 0
                        END as excess_power
                    FROM solark.plant_flow
                    WHERE created_at >= %s AND created_at <= %s
                    ORDER BY created_at ASC
                    """,
                    (start_time, end_time)
                )

            if not excess_data:
                return {
                    "status": "no_data",
                    "message": f"No energy data available for the last {hours} hours",
                    "timestamp": time.time()
                }

            # Calculate summary metrics
            total_excess_kwh = sum(row['excess_power'] for row in excess_data) / 60000.0
            avg_excess_power = sum(row['excess_power'] for row in excess_data) / len(excess_data)
            peak_excess_power = max(row['excess_power'] for row in excess_data)

            # Find peak excess times
            peak_excess_times = sorted(excess_data, key=lambda x: x['excess_power'], reverse=True)[:10]

            # Calculate hourly patterns
            hourly_excess = {}
            for row in excess_data:
                hour = row['timestamp'].hour
                if hour not in hourly_excess:
                    hourly_excess[hour] = []
                hourly_excess[hour].append(row['excess_power'])

            hourly_avg = {
                hour: sum(powers) / len(powers)
                for hour, powers in hourly_excess.items()
            }

            # Find best hours to run heavy loads
            best_load_hours = sorted(hourly_avg.items(), key=lambda x: x[1], reverse=True)[:5]

            # Generate recommendations
            potential_value = total_excess_kwh * 0.05  # $0.05/kWh value
            recommendations = []

            if total_excess_kwh > 5:
                recommendations.append({
                    "priority": "high",
                    "action": "Deploy Bitcoin Miners",
                    "details": f"You have {total_excess_kwh:.1f} kWh/day of excess energy. This could power ~{int(total_excess_kwh * 20)} TH/s of mining hashrate.",
                    "potential_revenue": f"${potential_value:.2f}/day"
                })

            if peak_excess_power > 2000:
                best_hours_str = ', '.join(f"{h:02d}:00" for h, _ in best_load_hours[:3])
                recommendations.append({
                    "priority": "medium",
                    "action": "Schedule Irrigation",
                    "details": f"Peak excess power is {peak_excess_power:.0f}W. Run irrigation pumps during hours: {best_hours_str}",
                    "potential_savings": "Avoid grid import costs"
                })

            if total_excess_kwh > 10:
                best_hours_str = ', '.join(f"{h:02d}:00" for h, _ in best_load_hours[:2])
                recommendations.append({
                    "priority": "medium",
                    "action": "Pre-heat Water",
                    "details": f"Excess energy could heat water during {best_hours_str}, reducing evening grid usage",
                    "potential_savings": "~$30/month on water heating"
                })

            if best_load_hours and best_load_hours[0][1] > 1000:
                recommendations.append({
                    "priority": "low",
                    "action": "EV Charging Optimization",
                    "details": f"Best charging window: {best_load_hours[0][0]:02d}:00-{(best_load_hours[0][0]+2)%24:02d}:00 when excess averages {best_load_hours[0][1]:.0f}W",
                    "potential_savings": "100% solar charging"
                })

            # Downsample time-series data for performance (every 5th point)
            time_series = [
                {
                    "timestamp": row['timestamp'].isoformat(),
                    "excess_power": round(row['excess_power'], 0),
                    "soc": round(row['soc'], 1)
                }
                for i, row in enumerate(excess_data) if i % 5 == 0
            ]

            return {
                "status": "success",
                "period": {
                    "hours": hours,
                    "start": start_time.isoformat(),
                    "end": end_time.isoformat()
                },
                "summary": {
                    "total_excess_kwh": round(total_excess_kwh, 2),
                    "avg_excess_power_w": round(avg_excess_power, 0),
                    "peak_excess_power_w": round(peak_excess_power, 0),
                    "potential_value_usd": round(potential_value, 2),
                    "data_points": len(excess_data)
                },
                "time_series": time_series,
                "peak_excess_times": [
                    {
                        "timestamp": row['timestamp'].isoformat(),
                        "excess_power": round(row['excess_power'], 0),
                        "soc": round(row['soc'], 1)
                    }
                    for row in peak_excess_times
                ],
                "hourly_patterns": {
                    f"{hour:02d}:00": round(avg, 0)
                    for hour, avg in sorted(hourly_avg.items())
                },
                "recommendations": {
                    "best_load_hours": [
                        {
                            "hour": f"{hour:02d}:00",
                            "avg_excess_w": round(avg, 0),
                            "potential_kwh_daily": round(avg / 1000, 2)
                        }
                        for hour, avg in best_load_hours
                    ],
                    "suggested_actions": recommendations
                },
                "timestamp": time.time()
            }

        except Exception as e:
            logger.exception("get_excess_energy_analytics_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze excess energy: {str(e)}"
            )

    @app.get("/energy/analytics/load-opportunities")
    async def get_load_opportunities():
        """
        ⚡ CRITICAL: Identify optimal times to run discretionary loads.

        Analyzes:
        - Battery SOC levels
        - Solar production forecasts (based on historical patterns)
        - Current excess energy
        - Grid import/export status

        Returns real-time recommendations for:
        - Bitcoin miner operations
        - Irrigation pump scheduling
        - Water heater activation
        - HVAC preconditioning
        - Other deferrable loads

        Note: This provides recommendations only. A future agent will
        poll this endpoint to automate load control.

        Returns:
            dict: Real-time load scheduling opportunities
        """
        try:
            from datetime import datetime, timedelta
            from ..utils.db import get_connection, query_one, query_all

            current_time = datetime.utcnow()

            with get_connection() as conn:
                # Get current system status
                current_data = query_one(
                    conn,
                    """
                    SELECT
                        pv_power,
                        load_power,
                        batt_power as battery_power,
                        soc,
                        grid_power,
                        created_at
                    FROM solark.plant_flow
                    ORDER BY created_at DESC
                    LIMIT 1
                    """,
                    as_dict=True
                )

                if not current_data:
                    raise HTTPException(status_code=404, detail="No current energy data available")

                # Calculate current excess
                battery_charging = max(0, current_data['battery_power'])
                current_excess = max(0, current_data['pv_power'] - (current_data['load_power'] + battery_charging))

                # Get historical solar production for next few hours (7-day avg)
                hour_now = current_time.hour
                forecast = []

                for h in range(6):  # Next 6 hours
                    future_hour = (hour_now + h) % 24
                    avg_solar = query_one(
                        conn,
                        """
                        SELECT AVG(pv_power) as avg_power
                        FROM solark.plant_flow
                        WHERE EXTRACT(HOUR FROM created_at) = %s
                          AND created_at >= NOW() - INTERVAL '7 days'
                        """,
                        (future_hour,),
                        as_dict=True
                    )

                    forecast.append({
                        "hour": future_hour,
                        "predicted_solar_w": round(avg_solar['avg_power'] if avg_solar and avg_solar['avg_power'] else 0, 0)
                    })

            # Determine load opportunities
            opportunities = []

            # Opportunity 1: Run miners NOW if excess > 1000W
            if current_excess > 1000:
                opportunities.append({
                    "type": "immediate",
                    "load": "Bitcoin Miners",
                    "action": "START",
                    "power_available": round(current_excess, 0),
                    "reason": f"Current excess: {current_excess:.0f}W available for immediate use",
                    "priority": "high",
                    "duration_estimate": "Until solar production drops or battery needs charging"
                })

            # Opportunity 2: Run irrigation if SOC > 80% and solar > 3kW
            if current_data['soc'] > 80 and current_data['pv_power'] > 3000:
                opportunities.append({
                    "type": "immediate",
                    "load": "Irrigation Pumps",
                    "action": "START",
                    "power_available": round(current_data['pv_power'] - current_data['load_power'], 0),
                    "reason": f"Battery well charged ({current_data['soc']:.1f}%), high solar production",
                    "priority": "medium",
                    "duration_estimate": "2-3 hours while sun is high"
                })

            # Opportunity 3: Pre-heat water if excess and SOC > 70%
            if current_excess > 500 and current_data['soc'] > 70:
                opportunities.append({
                    "type": "immediate",
                    "load": "Water Heater",
                    "action": "START",
                    "power_available": round(min(current_excess, 1500), 0),
                    "reason": "Excess solar available, store energy as hot water",
                    "priority": "low",
                    "duration_estimate": "30-60 minutes"
                })

            # Opportunity 4: Schedule loads for upcoming peak hours
            peak_solar_hour = max(forecast, key=lambda x: x['predicted_solar_w'])
            if peak_solar_hour['predicted_solar_w'] > 4000:
                opportunities.append({
                    "type": "scheduled",
                    "load": "Heavy Loads (Miners, Pumps, etc.)",
                    "action": "SCHEDULE",
                    "scheduled_time": f"{peak_solar_hour['hour']:02d}:00",
                    "power_available": round(peak_solar_hour['predicted_solar_w'] * 0.7, 0),
                    "reason": f"Peak solar production expected at {peak_solar_hour['hour']:02d}:00",
                    "priority": "medium",
                    "duration_estimate": "1-2 hours during peak production"
                })

            # Opportunity 5: Avoid loads if battery low and no solar
            if current_data['soc'] < 30 and current_data['pv_power'] < 500:
                opportunities.append({
                    "type": "warning",
                    "load": "All Discretionary Loads",
                    "action": "STOP",
                    "power_available": 0,
                    "reason": f"Low battery ({current_data['soc']:.1f}%), minimal solar production",
                    "priority": "high",
                    "duration_estimate": "Until battery recharged or solar production increases"
                })

            return {
                "status": "success",
                "timestamp": current_time.isoformat(),
                "current_status": {
                    "solar_power_w": round(current_data['pv_power'], 0),
                    "load_power_w": round(current_data['load_power'], 0),
                    "battery_soc_pct": round(current_data['soc'], 1),
                    "excess_power_w": round(current_excess, 0),
                    "grid_power_w": round(current_data['grid_power'], 0)
                },
                "solar_forecast_6h": forecast,
                "opportunities": opportunities,
                "summary": {
                    "total_opportunities": len(opportunities),
                    "immediate_actions": len([o for o in opportunities if o['type'] == 'immediate']),
                    "scheduled_actions": len([o for o in opportunities if o['type'] == 'scheduled']),
                    "warnings": len([o for o in opportunities if o['type'] == 'warning'])
                }
            }

        except Exception as e:
            logger.exception("get_load_opportunities_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to detect load opportunities: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/conversations")
    async def list_conversations(limit: int = 10):
        """
        List recent conversations.

        Args:
            limit: Maximum number of conversations to return (default: 10)

        Returns:
            dict: List of conversations with metadata
        """
        try:
            from ..utils.conversation import get_recent_conversations

            conversations = get_recent_conversations(limit=limit)

            return {
                "status": "success",
                "count": len(conversations),
                "conversations": conversations,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("list_conversations_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list conversations: {str(e)}"
            )

    @app.get("/conversations/{conversation_id}")
    async def get_conversation_detail(conversation_id: str):
        """
        Get conversation details with all messages.

        Args:
            conversation_id: UUID of the conversation

        Returns:
            dict: Conversation metadata and all messages
        """
        try:
            from ..utils.conversation import get_conversation, get_conversation_messages

            conversation = get_conversation(conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")

            messages = get_conversation_messages(conversation_id)

            return {
                "status": "success",
                "conversation": conversation,
                "messages": messages,
                "timestamp": time.time(),
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.exception("get_conversation_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get conversation: {str(e)}"
            )

    
    @app.post("/ask", response_model=AskResponse)
    async def ask_agent(request: AskRequest):
        """
        Ask the Solar Controller agent a question.

        WHAT: Processes user questions through CrewAI agent
        WHY: Main interface for interacting with the agent system
        HOW: Creates crew, runs task, returns result, stores in database

        Args:
            request: AskRequest with user's message

        Returns:
            AskResponse with agent's answer and metadata

        Raises:
            HTTPException: If agent execution fails

        Example:
            POST /ask
            {"message": "What's my battery level?"}

            Response:
            {
                "response": "Your battery is at 52%...",
                "query": "What's my battery level?",
                "agent_role": "Energy Systems Monitor",
                "duration_ms": 1250
            }
        """
        start_time = time.time()
        conversation_id = None

        try:
            from ..utils.conversation import (
                create_conversation,
                add_message,
                log_event,
                get_conversation_context,
                get_conversation
            )

            agent_role = "Energy Systems Monitor"

            # Handle session continuity
            if request.session_id:
                # Validate UUID format
                try:
                    from uuid import UUID
                    UUID(request.session_id)  # Validates format
                    # Continue existing conversation
                    conversation_id = request.session_id
                    existing_conv = get_conversation(conversation_id)
                    if not existing_conv:
                        # Session ID doesn't exist in DB, create new conversation
                        conversation_id = create_conversation(
                            agent_role=agent_role,
                            title=request.message[:100] if len(request.message) <= 100 else request.message[:97] + "..."
                        )
                except (ValueError, AttributeError):
                    # Invalid UUID format, create new conversation
                    conversation_id = create_conversation(
                        agent_role=agent_role,
                        title=request.message[:100] if len(request.message) <= 100 else request.message[:97] + "..."
                    )
            else:
                # Create new conversation
                conversation_id = create_conversation(
                    agent_role=agent_role,
                    title=request.message[:100] if len(request.message) <= 100 else request.message[:97] + "..."
                )

            # Get conversation context (previous conversations, excluding current)
            context = get_conversation_context(
                agent_role=agent_role,
                current_conversation_id=conversation_id,
                max_conversations=3,
                max_messages_per_conversation=6
            )

            # Log task start
            log_event(
                level="info",
                event_type="task_start",
                message=f"Processing query: {request.message}",
                agent_role=agent_role,
                conversation_id=conversation_id
            )

            # Store user message
            add_message(
                conversation_id=conversation_id,
                role="user",
                content=request.message
            )

            # FAST PATH: Direct KB search for GENERAL documentation queries only
            # System-specific questions should route through Manager to Solar Controller
            query_lower = request.message.lower()

            # Keywords for GENERAL documentation (not system-specific)
            general_doc_keywords = ['manual', 'documentation', 'guide', 'instructions',
                                   'how do i', 'how to', 'show me the']

            # Exclude system-specific question patterns
            system_specific_patterns = ['your', 'my', 'our', 'this system', 'you have',
                                        'what is the', 'what are the']

            is_general_doc = any(keyword in query_lower for keyword in general_doc_keywords)
            is_system_specific = any(pattern in query_lower for pattern in system_specific_patterns)

            # Only use Fast-Path for general documentation, NOT system-specific questions
            if is_general_doc and not is_system_specific and len(request.message) > 10:
                # Direct KB search - bypass Manager agent to prevent timeout
                from ..tools.kb_search import search_knowledge_base
                logger.info(f"Fast-path KB search for general documentation: {request.message}")
                result_str = search_knowledge_base.func(request.message, limit=5)
                agent_used = "Knowledge Base"
                agent_role = "Documentation Search"
            else:
                # Create manager crew to get routing decision
                manager_crew = create_manager_crew(request.message, context)

                # Run manager to get routing decision
                manager_result = manager_crew.kickoff()
                manager_result_str = str(manager_result)

                # Try to parse routing decision
                import json
                import re

                routing_decision = None
                try:
                    # Try direct JSON parse first
                    try:
                        routing_decision = json.loads(manager_result_str)
                    except json.JSONDecodeError:
                        # Try to extract JSON from markdown code blocks or text
                        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', manager_result_str, re.DOTALL)
                        if json_match:
                            routing_decision = json.loads(json_match.group(1))
                        else:
                            # Try to find any JSON object in the string
                            json_match = re.search(r'(\{.*?"action".*?\})', manager_result_str, re.DOTALL)
                            if json_match:
                                routing_decision = json.loads(json_match.group(1))
                except Exception as e:
                    logger.warning(f"Could not parse routing decision: {e}")

                # Check if this is a routing decision
                if routing_decision and routing_decision.get("action") == "route":
                    target_agent = routing_decision.get("agent")
                    logger.info(f"Manager routing to: {target_agent}")

                    # Route to appropriate specialist WITH context (V1.8: pass user_id)
                    if target_agent == "Solar Controller":
                        from ..agents.solar_controller import create_energy_crew
                        specialist_crew = create_energy_crew(
                            query=request.message,
                            conversation_context=context,
                            user_id=request.user_id  # V1.8: Smart context
                        )
                        result = specialist_crew.kickoff()
                        result_str = str(result)
                        agent_used = "Solar Controller"
                        agent_role = "Energy Systems Monitor"

                    elif target_agent == "Energy Orchestrator":
                        from ..agents.energy_orchestrator import create_orchestrator_crew
                        specialist_crew = create_orchestrator_crew(
                            query=request.message,
                            context=context,
                            user_id=request.user_id  # V1.8: Smart context
                        )
                        result = specialist_crew.kickoff()
                        result_str = str(result)
                        agent_used = "Energy Orchestrator"
                        agent_role = "Energy Operations Manager"

                    elif target_agent == "Research Agent":
                        from ..agents.research_agent import create_research_crew
                        specialist_crew = create_research_crew(
                            query=request.message,
                            user_id=request.user_id  # V1.8: Smart context
                        )
                        result = specialist_crew.kickoff()
                        result_str = str(result)
                        agent_used = "Research Agent"
                        agent_role = "Energy Systems Research Consultant"

                    else:
                        # Unknown agent, return manager's response
                        result_str = manager_result_str
                        agent_used = "Manager"
                else:
                    # Manager handled directly (greetings, etc.)
                    result_str = manager_result_str
                    agent_used = "Manager"

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # V1.8: Get context metadata (if ContextManager was used)
            context_tokens = None
            cache_hit = None
            query_type = None
            try:
                from ..services.context_manager import ContextManager
                from ..services.context_classifier import classify_query

                # Classify query to get type
                classified_type, confidence = classify_query(request.message)
                query_type = classified_type.value

                # Try to get context stats from ContextManager
                # Note: This is a simplified approach - in production, agents should return this metadata
                context_manager = ContextManager()
                test_bundle = context_manager.get_relevant_context(
                    query=request.message,
                    user_id=request.user_id,
                    max_tokens=3000
                )
                context_tokens = test_bundle.total_tokens
                cache_hit = test_bundle.cache_hit

                logger.info(
                    f"Context metadata: tokens={context_tokens}, "
                    f"cache_hit={cache_hit}, type={query_type}"
                )
            except Exception as e:
                logger.warning(f"Failed to get context metadata: {e}")

            # Store assistant response
            add_message(
                conversation_id=conversation_id,
                role="assistant",
                content=result_str,
                agent_role=agent_used,
                duration_ms=duration_ms
            )

            # Log task completion
            log_event(
                level="info",
                event_type="task_complete",
                message=f"Query completed in {duration_ms}ms by {agent_used}",
                agent_role=agent_used,
                conversation_id=conversation_id,
                data={
                    "duration_ms": duration_ms,
                    "agent_used": agent_used,
                    "context_tokens": context_tokens,  # V1.8
                    "cache_hit": cache_hit,  # V1.8
                    "query_type": query_type  # V1.8
                }
            )

            # Return response with session_id for multi-turn conversations
            return AskResponse(
                response=result_str,
                query=request.message,
                agent_role=agent_used,
                duration_ms=duration_ms,
                session_id=conversation_id,
                # V1.8: Context metadata
                context_tokens=context_tokens,
                cache_hit=cache_hit,
                query_type=query_type,
            )

        except Exception as e:
            # Log error with details
            logger.exception("agent_execution_failed error=%s", e)

            # Log error to database if we have a conversation
            if conversation_id:
                try:
                    from ..utils.conversation import log_event
                    log_event(
                        level="error",
                        event_type="error",
                        message=f"Agent execution failed: {str(e)}",
                        agent_role="Energy Systems Monitor",
                        conversation_id=conversation_id,
                        data={"error": str(e)}
                    )
                except:
                    pass  # Don't fail if logging fails

            # Return HTTP 500 with error details
            raise HTTPException(
                status_code=500,
                detail=f"Agent execution failed: {str(e)}"
            )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Agent Monitoring Endpoints
    # ─────────────────────────────────────────────────────────────────────────

    @app.get("/agents/health")
    async def get_agents_health():
        """
        Get health status of all agents.

        Returns latest health check data for each agent.
        """
        try:
            from ..services.agent_health import get_agent_status_summary

            summary = get_agent_status_summary()

            return {
                "status": "success",
                "data": summary,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agents_health_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent health: {str(e)}"
            )

    @app.get("/agents/{agent_name}/health")
    async def get_agent_health(agent_name: str):
        """
        Get health status of a specific agent.

        Args:
            agent_name: Name of the agent (Manager, Solar Controller, Energy Orchestrator)
        """
        try:
            from ..services.agent_health import check_agent_health

            health = check_agent_health(agent_name)

            return {
                "status": "success",
                "data": health,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agent_health_failed agent=%s error=%s", agent_name, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent health: {str(e)}"
            )

    @app.get("/agents/activity")
    async def get_agents_activity(limit: int = 100):
        """
        Get recent agent activity events.

        Args:
            limit: Maximum number of events to return (default: 100, max: 1000)
        """
        try:
            from ..utils.agent_telemetry import get_recent_agent_activity

            limit = min(limit, 1000)  # Cap at 1000
            activity = get_recent_agent_activity(limit=limit)

            return {
                "status": "success",
                "count": len(activity),
                "data": activity,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agents_activity_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent activity: {str(e)}"
            )

    @app.get("/agents/{agent_name}/activity")
    async def get_agent_activity(agent_name: str, limit: int = 100):
        """
        Get activity for a specific agent.

        Args:
            agent_name: Agent name to filter by
            limit: Maximum number of events (default: 100, max: 1000)
        """
        try:
            from ..utils.agent_telemetry import get_recent_agent_activity

            limit = min(limit, 1000)
            activity = get_recent_agent_activity(limit=limit, agent_name=agent_name)

            return {
                "status": "success",
                "agent_name": agent_name,
                "count": len(activity),
                "data": activity,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agent_activity_failed agent=%s error=%s", agent_name, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent activity: {str(e)}"
            )

    @app.get("/agents/metrics")
    async def get_agents_metrics(hours: int = 24):
        """
        Get aggregated performance metrics for all agents.

        Args:
            hours: Hours to look back (default: 24)
        """
        try:
            from ..utils.agent_telemetry import get_agent_metrics

            metrics = get_agent_metrics(hours=hours)

            return {
                "status": "success",
                "hours": hours,
                "data": metrics,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agents_metrics_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent metrics: {str(e)}"
            )

    @app.get("/agents/{agent_name}/metrics")
    async def get_agent_metrics_detail(agent_name: str, hours: int = 24):
        """
        Get metrics for a specific agent.

        Args:
            agent_name: Agent name to filter by
            hours: Hours to look back (default: 24)
        """
        try:
            from ..utils.agent_telemetry import get_agent_metrics

            metrics = get_agent_metrics(agent_name=agent_name, hours=hours)

            return {
                "status": "success",
                "agent_name": agent_name,
                "hours": hours,
                "data": metrics,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_agent_metrics_failed agent=%s error=%s", agent_name, e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get agent metrics: {str(e)}"
            )

    @app.get("/system/stats")
    async def get_system_stats():
        """
        Get comprehensive system statistics.

        Returns counts and metrics across all system components.
        """
        try:
            from ..utils.db import get_connection, query_one

            stats = {}

            with get_connection() as conn:
                # Energy snapshots count
                result = query_one(
                    conn,
                    "SELECT COUNT(*) as count FROM solark.telemetry"
                )
                stats['total_energy_snapshots'] = result['count'] if result else 0

                # Conversations count
                result = query_one(
                    conn,
                    "SELECT COUNT(*) as count FROM agent.conversations"
                )
                stats['total_conversations'] = result['count'] if result else 0

                # Conversations today
                result = query_one(
                    conn,
                    """
                    SELECT COUNT(*) as count FROM agent.conversations
                    WHERE created_at > CURRENT_DATE
                    """
                )
                stats['conversations_today'] = result['count'] if result else 0

                # Latest energy data
                result = query_one(
                    conn,
                    """
                    SELECT timestamp, soc as battery_soc, pv_power as solar_power
                    FROM solark.telemetry
                    ORDER BY timestamp DESC
                    LIMIT 1
                    """
                )
                if result:
                    stats['latest_energy'] = dict(result)
                else:
                    stats['latest_energy'] = None

                # Agent activity count (last 24h)
                try:
                    result = query_one(
                        conn,
                        """
                        SELECT COUNT(*) as count FROM agent_metrics.agent_events
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                        """
                    )
                    stats['agent_events_24h'] = result['count'] if result else 0
                except:
                    stats['agent_events_24h'] = 0  # Table may not exist yet

            return {
                "status": "success",
                "data": stats,
                "timestamp": time.time(),
            }

        except Exception as e:
            logger.exception("get_system_stats_failed error=%s", e)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get system stats: {str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Include API Routes
    # ─────────────────────────────────────────────────────────────────────────

    from .routes import kb
    app.include_router(kb.router)

    # Health monitoring endpoints (V1.8)
    from .endpoints import health_monitoring
    app.include_router(health_monitoring.router)

    logger.info("✅ CommandCenter API initialized")
    return app


# ─────────────────────────────────────────────────────────────────────────────
# Create Application Instance
# ─────────────────────────────────────────────────────────────────────────────

# This is what Railway/uvicorn runs
app = create_app()


# ─────────────────────────────────────────────────────────────────────────────
# Development Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Run API locally for development.
    
    Usage:
        python -m src.api.main
        
    Or (recommended):
        uvicorn src.api.main:app --reload
    """
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )