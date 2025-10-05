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
from ..agents.solar_controller import create_energy_crew
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
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What's my battery level?"
            }
        }


class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    response: str
    query: str
    agent_role: str
    duration_ms: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Your battery is at 52% and currently discharging at 3160W.",
                "query": "What's my battery level?",
                "agent_role": "Energy Systems Monitor",
                "duration_ms": 1250
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

    # ─────────────────────────────────────────────────────────────────────────
    # Agent Endpoints
    # ─────────────────────────────────────────────────────────────────────────
    
    @app.post("/ask", response_model=AskResponse)
    async def ask_agent(request: AskRequest):
        """
        Ask the Solar Controller agent a question.
        
        WHAT: Processes user questions through CrewAI agent
        WHY: Main interface for interacting with the agent system
        HOW: Creates crew, runs task, returns result
        
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
        
        try:
            # Create crew with user's query
            crew = create_energy_crew(request.message)
            
            # Run the crew (executes agent and task)
            result = crew.kickoff()
            
            # Calculate duration
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Return response
            return AskResponse(
                response=str(result),
                query=request.message,
                agent_role="Energy Systems Monitor",
                duration_ms=duration_ms,
            )
            
        except Exception as e:
            # Log error with details
            logger.exception("agent_execution_failed error=%s", e)
            
            # Return HTTP 500 with error details
            raise HTTPException(
                status_code=500,
                detail=f"Agent execution failed: {str(e)}"
            )
    
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