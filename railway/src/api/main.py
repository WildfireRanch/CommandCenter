# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/main.py
# PURPOSE: FastAPI application entrypoint for CommandCenter backend API
#
# WHAT IT DOES:
#   - Creates and configures the FastAPI web server
#   - Sets up CORS so Vercel MCP server can call this API
#   - Adds middleware for logging and request tracking
#   - Provides health check endpoints
#   - Will load CrewAI agent routes (when we build them)
#
# DEPENDENCIES:
#   - fastapi: Web framework
#   - uvicorn: ASGI server (runs the app)
#   - pydantic: Data validation
#
# ENVIRONMENT VARIABLES REQUIRED:
#   - ALLOWED_ORIGINS: Comma-separated URLs allowed to call this API
#                     Example: "https://mcp.wildfireranch.us,http://localhost:3000"
#   - OPENAI_API_KEY: Your OpenAI API key (for CrewAI agents)
#   - DATABASE_URL: PostgreSQL connection string
#   - ENV: Environment name (development/staging/production)
#
# ENVIRONMENT VARIABLES OPTIONAL:
#   - INDEX_ROOT: Where to store data files (default: ./data/index)
#   - SOLARK_EMAIL: SolArk Cloud login
#   - SOLARK_PASSWORD: SolArk Cloud password
#   - SOLARK_PLANT_ID: SolArk plant ID (optional, defaults to 146453)
#
# HOW TO RUN:
#   Local:      uvicorn src.api.main:app --reload --port 8000
#   Railway:    Automatically runs via Dockerfile
#   Test:       curl http://localhost:8000/health
#
# TROUBLESHOOTING:
#   - "CORS error": Check ALLOWED_ORIGINS includes your frontend URL
#   - "Port in use": Change port with --port 8001
#   - "Import errors": Activate venv and run: pip install -r requirements.txt
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# QUICK NAVIGATION:
#   Line 70:  Imports
#   Line 90:  Configuration & Environment Setup
#   Line 150: Middleware Classes (RequestID, AccessLog)
#   Line 250: Application Factory (create_app function)
#   Line 400: Health Endpoints
#   Line 450: Router Mounting (where we'll add CrewAI routes)
# ═══════════════════════════════════════════════════════════════════════════

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Imports: Standard Library
# ─────────────────────────────────────────────────────────────────────────────
import logging
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# Imports: Third-Party Packages
# ─────────────────────────────────────────────────────────────────────────────
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.gzip import GZipMiddleware

# ─────────────────────────────────────────────────────────────────────────────
# Imports: Local Modules
# ─────────────────────────────────────────────────────────────────────────────
from src.agents.solar_controller import create_energy_crew

# Import database utilities
from src.utils.db import check_connection as check_db_connection

# ─────────────────────────────────────────────────────────────────────────────
# Load Environment Variables
# ─────────────────────────────────────────────────────────────────────────────
from dotenv import load_dotenv
from pathlib import Path

# Load .env from repository root (not railway subdirectory)
root_dir = Path(__file__).parent.parent.parent  # Go up to repo root
env_file = root_dir / ".env"
load_dotenv(dotenv_path=env_file)

# ─────────────────────────────────────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────────────────────────────────────
logger = logging.getLogger("commandcenter.api")


# ─────────────────────────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    """Request model for /ask endpoint."""
    message: str

class AskResponse(BaseModel):
    """Response model for /ask endpoint."""
    response: str
    agent_role: str


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: Configuration & Environment Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _env(name: str, fallback: str = "") -> str:
    """
    Read environment variable with fallback value.
    
    WHAT: Gets value from environment variables
    WHY: Centralizes env var access with safe defaults
    HOW: Uses os.getenv with fallback if not set
    
    Args:
        name: Environment variable name (e.g., "API_KEY")
        fallback: Default value if variable not set (default: empty string)
        
    Returns:
        String value from environment or fallback
        
    Example:
        >>> _env("API_KEY", "dev-key")  # Returns actual API_KEY or "dev-key"
    """
    return os.getenv(name, fallback)


def _parse_origins(value: str | None) -> list[str]:
    """
    Parse CORS origins from comma/space-separated string.
    
    WHAT: Converts string like "url1,url2" into list ["url1", "url2"]
    WHY: CORS middleware needs a list, but env vars are strings
    HOW: Split by comma and spaces, strip whitespace, remove duplicates
    
    Args:
        value: String like "https://app.com, https://api.com" or None
        
    Returns:
        List of unique origin URLs
        Returns empty list if value is None or empty
        
    Example:
        >>> _parse_origins("https://a.com,https://b.com")
        ["https://a.com", "https://b.com"]
        
    TROUBLESHOOTING:
        - Empty list returned: Check ALLOWED_ORIGINS is set in environment
        - Duplicates in result: Not possible, we deduplicate
    """
    # Return empty list if no value provided
    if not value:
        return []
    
    # Split by comma first, then by spaces (handles "a.com, b.com" and "a.com b.com")
    parts = [
        p.strip()  # Remove leading/trailing whitespace
        for chunk in value.split(",")  # Split by comma
        for p in chunk.split()  # Then split by spaces
        if p.strip()  # Only keep non-empty strings
    ]
    
    # Remove duplicates while preserving order
    # dict.fromkeys() keeps first occurrence of each item
    return list(dict.fromkeys(parts))


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: Middleware Classes
# 
# Middlewares run on EVERY request and add functionality like:
# - Request tracking (correlation IDs)
# - Access logging (who called what, when)
# - Response compression (gzip)
# ═══════════════════════════════════════════════════════════════════════════

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Attach unique correlation ID to each request.
    
    WHAT: Adds a unique ID to every request/response
    WHY: Makes debugging easier - you can trace a single request through logs
    HOW: Checks for x-corr-id header, generates one if missing
    
    USAGE:
        Request comes in → Check for x-corr-id header
        If present → Use it
        If missing → Generate new UUID
        Add to request.state.corr_id
        Add to response headers
        
    LOGS:
        Every request log will include cid=abc123 for tracking
        
    TROUBLESHOOTING:
        - Missing in logs: Check middleware is added to app
        - Same ID for multiple requests: Client is sending x-corr-id header
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and add correlation ID.
        
        Args:
            request: Incoming HTTP request
            call_next: Function to call next middleware/route
            
        Returns:
            HTTP response with x-corr-id header added
        """
        # Try to get correlation ID from request header
        # If not present, generate a new one (8 char hex)
        cid = request.headers.get("x-corr-id") or f"{uuid.uuid4().hex[:8]}"
        
        # Store on request.state so other code can access it
        request.state.corr_id = cid
        
        # Continue processing request
        response = await call_next(request)
        
        # Add correlation ID to response headers
        # This lets the client track the request too
        response.headers["x-corr-id"] = cid
        
        return response


class AccessLogMiddleware(BaseHTTPMiddleware):
    """
    Log every HTTP request with timing information.
    
    WHAT: Records all API calls with method, path, status, duration
    WHY: Essential for debugging and monitoring API usage
    HOW: Starts timer, processes request, logs result
    
    LOG FORMAT:
        request method=GET path=/health cid=abc123 status=200 dur_ms=45
        
    FIELDS:
        - method: HTTP method (GET, POST, etc.)
        - path: URL path (/health, /api/crew/execute, etc.)
        - cid: Correlation ID for request tracking
        - status: HTTP status code (200, 404, 500, etc.)
        - dur_ms: Request duration in milliseconds
        
    TROUBLESHOOTING:
        - No logs appearing: Check logging is configured
        - Status shows "ERR": Request failed before returning response
        - Very slow requests: Check dur_ms to identify bottlenecks
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        Process request and log timing/status.
        
        Args:
            request: Incoming HTTP request
            call_next: Function to call next middleware/route
            
        Returns:
            HTTP response (unchanged)
        """
        # Start timer using high-precision counter
        t0 = time.perf_counter()
        
        # Extract request details for logging
        method = request.method  # GET, POST, etc.
        path = request.url.path  # /health, /api/crew/execute, etc.
        status = None  # Will be set after response
        
        try:
            # Process request through rest of middleware chain and route
            response = await call_next(request)
            
            # Get status code from response
            status = response.status_code
            
            return response
            
        finally:
            # This runs even if request fails (exception)
            # Calculate duration in milliseconds
            dur_ms = int((time.perf_counter() - t0) * 1000)
            
            # Get correlation ID from request.state (set by RequestIDMiddleware)
            cid = getattr(request.state, "corr_id", "-")
            
            # Log the request
            # If status is None, request failed - show as "ERR"
            logger.info(
                "request method=%s path=%s cid=%s status=%s dur_ms=%s",
                method,
                path,
                cid,
                status if status is not None else "ERR",
                dur_ms
            )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: Application Factory
#
# This is where we create and configure the FastAPI application.
# It's a function (not just "app = FastAPI()") so we can configure it properly.
# ═══════════════════════════════════════════════════════════════════════════

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    WHAT: Builds the complete API server with all configuration
    WHY: Centralizes all setup in one place, makes testing easier
    HOW: Creates FastAPI instance, adds middleware, mounts routes
    
    Returns:
        Configured FastAPI application ready to run
        
    CONFIGURATION ORDER (IMPORTANT):
        1. Create app with lifespan
        2. Add CORS middleware (MUST be before routes)
        3. Add other middlewares
        4. Mount health endpoints early
        5. Mount feature routes
        
    TROUBLESHOOTING:
        - CORS errors: Check ALLOWED_ORIGINS is set
        - Routes not found: Check include_router() calls
        - Startup fails: Check lifespan() function errors
    """
    
    # ─────────────────────────────────────────────────────────────────────────
    # Lifespan: Startup and Shutdown Logic
    # ─────────────────────────────────────────────────────────────────────────
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Manage application lifecycle (startup/shutdown).
        
        WHAT: Runs code when app starts and stops
        WHY: Setup resources at start, cleanup at stop
        HOW: Code before yield = startup, after yield = shutdown
        
        STARTUP TASKS:
            - Create necessary directories
            - Verify writability of data directories
            - Log configuration for debugging
            
        SHUTDOWN TASKS:
            - Currently none (will add database cleanup later)
        """
        # ─────────────────────────────────────────────────────────────────
        # STARTUP
        # ─────────────────────────────────────────────────────────────────
        logger.info("🚀 CommandCenter API starting...")
        
        # Create required directories
        # INDEX_ROOT: Where we store data files (KB index, etc.)
        data_dir = Path(_env("INDEX_ROOT", "./data/index"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # SECRETS: Where we store sensitive files (Google OAuth, etc.)
        secrets_dir = Path("./secrets")
        secrets_dir.mkdir(parents=True, exist_ok=True)
        
        # Log what we created
        logger.info(
            "paths_ready data_dir=%s env=%s",
            str(data_dir),
            _env("ENV", "development")
        )
        
        # Log configuration (for debugging deployment issues)
        # Don't log actual keys, just whether they're present
        logger.info(
            "config openai_key=%s railway_env=%s",
            "present" if _env("OPENAI_API_KEY") else "MISSING",
            _env("RAILWAY_ENVIRONMENT", "local")
        )
        print(f"☀️ SolArk credentials configured: {'✅' if os.getenv('SOLARK_EMAIL') else '❌'}")
        print(f"🗄️ Database configured: {'✅' if os.getenv('DATABASE_URL') else '❌'}")

        # Yield control back to FastAPI (app is now running)
        yield
        
        # ─────────────────────────────────────────────────────────────────
        # SHUTDOWN
        # ─────────────────────────────────────────────────────────────────
        logger.info("👋 CommandCenter API shutting down...")
        
        # TODO: Add cleanup here later:
        # - Close database connections
        # - Flush logs
        # - Cancel background tasks
    
    # ─────────────────────────────────────────────────────────────────────────
    # Create FastAPI Application
    # ─────────────────────────────────────────────────────────────────────────
    app = FastAPI(
        title="CommandCenter API",
        description="CrewAI-powered energy orchestration backend",
        version="1.0.0",
        lifespan=lifespan,  # Use lifespan manager we defined above
        docs_url="/docs",  # Swagger UI at /docs
        redoc_url="/redoc",  # ReDoc at /redoc
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # CORS Configuration (Cross-Origin Resource Sharing)
    # 
    # WHAT: Allows Vercel MCP server to call this API from different domain
    # WHY: Browser security blocks cross-domain calls by default
    # HOW: Tell browser "it's OK to accept requests from these origins"
    # ─────────────────────────────────────────────────────────────────────────
    
    # Get allowed origins from environment
    allowed_origins = _parse_origins(_env("ALLOWED_ORIGINS"))
    app_env = _env("ENV", "development").lower()
    
    # In production, ALLOWED_ORIGINS is required
    # In development, we allow localhost by default
    if not allowed_origins:
        if app_env in {"prod", "production"}:
            raise RuntimeError(
                "ALLOWED_ORIGINS required in production. "
                "Set to your Vercel MCP URL: https://mcp.wildfireranch.us"
            )
        # Development default: allow localhost
        allowed_origins = ["http://localhost:3000", "http://localhost:3001"]
    
    logger.info("cors_config origins=%s env=%s", allowed_origins, app_env)
    
    # Add CORS middleware
    # IMPORTANT: This MUST be added before routes are mounted!
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,  # Which domains can call us
        allow_credentials=True,  # Allow cookies/auth headers
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # HTTP methods
        allow_headers=[
            "content-type",  # Request body type
            "authorization",  # Auth tokens
            "x-api-key",  # Our API key header
            "x-corr-id",  # Correlation ID for tracking
        ],
        expose_headers=["x-corr-id"],  # Headers browser can read from response
        max_age=600,  # Cache preflight requests for 10 minutes
    )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Add Other Middlewares
    # Order matters: They run in reverse order of addition
    # ─────────────────────────────────────────────────────────────────────────
    
    # GZip: Compress responses (saves bandwidth)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    
    # Request ID: Track each request with unique ID
    app.add_middleware(RequestIDMiddleware)
    
    # Access Log: Log all requests with timing
    app.add_middleware(AccessLogMiddleware)
    
    # ─────────────────────────────────────────────────────────────────────────
    # Health Endpoints (Mount Early)
    # These should ALWAYS be available, even if other routes fail
    # ─────────────────────────────────────────────────────────────────────────
    
    @app.get("/health")
    async def health_check():
        """
        Basic health check endpoint.
        
        WHAT: Returns simple status to verify API is running
        WHY: Used by Railway/monitoring to check if service is alive
        HOW: Always returns 200 OK with simple JSON
        
        USAGE:
            curl http://localhost:8000/health
            
        RESPONSE:
            {"status": "healthy", "service": "commandcenter-api"}
            
        TROUBLESHOOTING:
            - Can't reach endpoint: Check API is running
            - Returns error: Check logs for startup failures
        """
        return {
            "status": "healthy",
            "service": "commandcenter-api"
        }
    
    @app.get("/ready")
    async def readiness_check():
        """
        Readiness probe with dependency checks.
        
        WHAT: Checks if API is ready to handle requests
        WHY: Unlike /health, this checks dependencies (database, etc.)
        HOW: Verifies each required service is accessible
        
        USAGE:
            curl http://localhost:8000/ready
            
        RESPONSE:
            {
                "ready": true,
                "checks": {
                    "api": "ok",
                    "openai_key": "present",
                    "database": "not_checked"
                },
                "env": "development"
            }
            
        CHECKS:
            - api: Always "ok" if endpoint responds
            - openai_key: "present" or "missing"
            - database: "ok", "error", or "not_checked"
            
        TROUBLESHOOTING:
            - ready=false: Check which checks failed
            - openai_key=missing: Set OPENAI_API_KEY environment variable
            - database=error: Check DATABASE_URL connection string
        """
        checks = {
            "api": "ok",
            "openai_key": "present" if _env("OPENAI_API_KEY") else "missing",
            "database_configured": bool(os.getenv("DATABASE_URL")),
            "database_connected": check_db_connection(),
            "solark_configured": bool(os.getenv("SOLARK_EMAIL") and os.getenv("SOLARK_PASSWORD")),
        }

        # Consider ready if API is running, OpenAI configured, and database connected
        # SolArk is optional for some queries
        all_ok = (checks["api"] == "ok" and
                  checks["openai_key"] == "present" and
                  checks["database_connected"])
        
        return {
            "ready": all_ok,
            "checks": checks,
            "env": _env("ENV", "development")
        }
    
    # ─────────────────────────────────────────────────────────────────────────
    # Root Endpoint
    # ─────────────────────────────────────────────────────────────────────────
    
    @app.get("/")
    async def root():
        """
        API root with basic info and links.

        WHAT: Landing page for the API
        WHY: Helps users discover available endpoints
        HOW: Returns JSON with service info and useful links

        USAGE:
            curl http://localhost:8000/

        RESPONSE:
            {
                "service": "CommandCenter API",
                "version": "1.0.0",
                "status": "operational",
                "docs": "/docs",
                "health": "/health"
            }
        """
        return {
            "service": "CommandCenter API",
            "version": "1.0.0",
            "status": "operational",
            "docs": "/docs",  # Interactive API docs
            "health": "/health"  # Health check
        }

    @app.post("/ask", response_model=AskResponse)
    async def ask(request: AskRequest):
        """
        Ask the agent a question.

        WHAT: Sends user message to CrewAI agent for response
        WHY: Test that CrewAI + OpenAI integration works end-to-end
        HOW: Creates greeter agent, wraps message in task, executes

        USAGE:
            curl -X POST http://localhost:8000/ask \
                 -H "Content-Type: application/json" \
                 -d '{"message": "Hello!"}'

        TROUBLESHOOTING:
            - "No module named crewai": Run pip install -r requirements.txt
            - "OpenAI API error": Check OPENAI_API_KEY is set
            - Agent takes long time: First run downloads model, caches after
        """
        # Create the energy crew
        crew = create_energy_crew(request.message)

        # Execute the crew and return result
        result = crew.kickoff()

        return AskResponse(
            response=str(result),
            agent_role="Energy Controller"
        )
    
    # ─────────────────────────────────────────────────────────────────────────
    # Mount Feature Routers
    # 
    # TODO: Add routers as we build features
    # This is where we'll add CrewAI agent routes, tool routes, etc.
    # ─────────────────────────────────────────────────────────────────────────
    
    # EXAMPLE (uncomment when we build these):
    #
    # from .routes.crew import router as crew_router
    # app.include_router(
    #     crew_router,
    #     prefix="/api/crew",
    #     tags=["crew"]
    # )
    #
    # from .routes.tools import router as tools_router
    # app.include_router(
    #     tools_router,
    #     prefix="/api/tools",
    #     tags=["tools"]
    # )
    #
    # from .routes.status import router as status_router
    # app.include_router(
    #     status_router,
    #     prefix="/api/status",
    #     tags=["status"]
    # )
    
    logger.info("✅ CommandCenter API initialized")
    
    return app


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: Create Application Instance
#
# This is what uvicorn/Railway actually runs
# ═══════════════════════════════════════════════════════════════════════════

# Create the app instance
# This is imported by: uvicorn src.api.main:app
app = create_app()


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: Local Development Entry Point
#
# Only runs when you execute: python main.py
# Not used in production (Railway uses uvicorn directly)
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """
    Run the API locally for development.
    
    USAGE:
        python src/api/main.py
        
    OR (recommended):
        uvicorn src.api.main:app --reload --port 8000
        
    The uvicorn command is better because --reload auto-restarts on code changes
    """
    import uvicorn
    
    uvicorn.run(
        "main:app",  # Import path to app
        host="0.0.0.0",  # Listen on all interfaces
        port=8000,  # Default port
        reload=True,  # Auto-reload on code changes
        log_level="info"  # Logging verbosity
    )


# ═══════════════════════════════════════════════════════════════════════════
# END OF FILE
# ═══════════════════════════════════════════════════════════════════════════