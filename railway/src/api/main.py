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
from fastapi import FastAPI, HTTPException, Request
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

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's my battery level?",
                "session_id": "optional-conversation-uuid"
            }
        }


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    response: str
    query: str
    agent_role: str
    duration_ms: int
    session_id: str  # Conversation ID for continuing the conversation

    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your battery is at 52% and currently discharging at 3160W.",
                "query": "What's my battery level?",
                "agent_role": "Energy Systems Monitor",
                "duration_ms": 1250,
                "session_id": "abc123-uuid"
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
        
        # Test database connection
        if os.getenv("DATABASE_URL"):
            if check_db_connection():
                print("🗄️ Database connected: ✅")
            else:
                print("🗄️ Database connected: ❌ (WARNING: Database unreachable)")
        
        yield
        
        # ─────────────────────────────────────────────────────────────────
        # SHUTDOWN
        # ─────────────────────────────────────────────────────────────────
        print("👋 CommandCenter API shutting down...")
    
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

            # FAST PATH: Direct KB search for documentation queries (bypass Manager agent timeout)
            # Detect KB queries with simple keyword matching (avoid false positives)
            query_lower = request.message.lower()
            kb_keywords = ['specification', 'specs', 'threshold', 'policy', 'policies',
                          'procedure', 'maintain', 'maintenance', 'documentation', 'guide',
                          'manual', 'instructions', 'how do i', 'how to']
            # Avoid: "what is" (too broad - catches "what is my battery level")
            is_kb_query = any(keyword in query_lower for keyword in kb_keywords)

            if is_kb_query and len(request.message) > 10:
                # Direct KB search - bypass Manager agent to prevent timeout
                from ..tools.kb_search import search_knowledge_base
                logger.info(f"Direct KB search for query: {request.message}")
                result_str = search_knowledge_base.func(request.message, limit=5)
                agent_used = "Knowledge Base"
                agent_role = "Documentation Search"
            else:
                # Create manager crew to route query intelligently
                crew = create_manager_crew(request.message, context)

                # Run the crew (executes agent and task)
                result = crew.kickoff()
                result_str = str(result)
                agent_used = "Manager"  # Will be updated by JSON parsing below

            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)

            # Try to parse result as JSON (from routing tools)
            # Skip if we already set agent_used via KB fast path
            if 'agent_used' not in locals():
                agent_used = "Manager"  # Default
            try:
                import json
                import re

                # Try direct JSON parse first
                try:
                    result_data = json.loads(result_str)
                except json.JSONDecodeError:
                    # Try to extract JSON from markdown code blocks or text
                    json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_str, re.DOTALL)
                    if json_match:
                        result_data = json.loads(json_match.group(1))
                    else:
                        # Try to find any JSON object in the string
                        json_match = re.search(r'(\{[^{}]*"agent_used"[^{}]*\})', result_str, re.DOTALL)
                        if json_match:
                            result_data = json.loads(json_match.group(1))
                        else:
                            result_data = None

                if result_data and "agent_used" in result_data:
                    agent_used = result_data["agent_used"]
                    agent_role = result_data.get("agent_role", agent_role)
                    result_str = result_data["response"]
            except Exception as e:
                logger.warning(f"Could not parse agent routing JSON: {e}")
                pass  # Not JSON, use result as-is

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
                data={"duration_ms": duration_ms, "agent_used": agent_used}
            )

            # Return response with session_id for multi-turn conversations
            return AskResponse(
                response=result_str,
                query=request.message,
                agent_role=agent_used,
                duration_ms=duration_ms,
                session_id=conversation_id,
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
    # Include API Routes
    # ─────────────────────────────────────────────────────────────────────────

    from .routes import kb
    app.include_router(kb.router)

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