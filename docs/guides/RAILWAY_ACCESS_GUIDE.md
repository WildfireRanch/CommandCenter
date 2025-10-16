# Railway Project Context for Claude Code

## Overview
I'm working with a Railway project. Railway is a deployment platform for applications, databases, and services. Please help me navigate and work with my Railway infrastructure using the Railway CLI and best practices.

**Current Project**: CommandCenterProject
**Environment**: production
**Services**: CommandCenter (FastAPI backend), POSTGRES_DB (PostgreSQL with TimescaleDB)

## Railway CLI Basics

### Essential Commands You Should Know
```bash
# Login and setup
railway login                    # Authenticate with Railway
railway link                     # Link to existing project
railway status                   # Show current project/environment

# Project exploration
railway list                     # List all my projects
railway environment              # List environments in current project
railway service                  # List services in current project

# Variables and config
railway variables               # Show all environment variables
railway variables --service <name>  # Variables for specific service
railway run <command>           # Run command with Railway env vars loaded

# Logs and monitoring
railway logs                    # Stream logs from current service
railway logs --service <name>   # Logs from specific service

# Database access
railway connect <service>       # Connect to database (PostgreSQL, MySQL, etc.)
railway run psql               # Connect to PostgreSQL with credentials loaded

# Deployment
railway up                      # Deploy current directory
railway redeploy --service <name> -y  # Redeploy service (use -y to skip confirmation for non-TTY)
```

### Important: Non-Interactive Environments

When running from GitHub Codespaces or CI/CD (non-TTY environments):
- **Always use `-y` flag** for commands that prompt for confirmation:
  ```bash
  railway redeploy --service CommandCenter -y
  ```
- Some commands won't work without TTY: `railway service`, `railway connect`
- Use `railway variables` to inspect environment without interaction
- Use `railway run <command>` to execute commands with Railway env vars loaded

## Project Structure

### When I ask you to explore my Railway project, please:
1. First run `railway status` to understand current context
2. Use `railway service` to list all services
3. Check `railway variables` to understand available environment variables
4. Review logs with `railway logs` when debugging

### My Project Components
(I'll tell you about my specific services, but typically includes):
- **Services**: Application containers (Node.js, Python, Go, etc.)
- **Databases**: PostgreSQL, MySQL, Redis, MongoDB
- **Environment**: Production, Staging, Development

## Service Communication

### Internal Networking
- Services can communicate using private networking
- Each service gets a private URL: `servicename.railway.internal`
- Use environment variables for service discovery
- Railway automatically injects `DATABASE_URL`, `REDIS_URL`, etc.

**IMPORTANT**: Internal Railway hostnames (`.railway.internal`) are **NOT accessible** from:
- GitHub Codespaces
- Local development machines
- CI/CD runners

They only work **inside the Railway network** between Railway services.

## Database Access Patterns

### PostgreSQL
```bash
# Connect directly
railway connect postgres

# Run migrations
railway run npm run migrate

# Dump database
railway run pg_dump > backup.sql
```

### MySQL
```bash
railway connect mysql
railway run npx prisma migrate deploy
```

### Redis
```bash
railway connect redis
railway run redis-cli
```

## Common Workflows

### 1. Debugging Connection Issues
```bash
# Check if service is running
railway status

# View recent logs
railway logs --tail 100

# Check environment variables
railway variables
```

### 2. Running Database Migrations

**Two Approaches:**

#### A) Use API Endpoints (Recommended for Remote Execution)
If your backend has migration endpoints:
```bash
# Run all migrations via init-schema endpoint
curl -X POST https://api.wildfireranch.us/db/init-schema

# Run specific migration with diagnostics
curl -X POST https://api.wildfireranch.us/db/run-health-migration
```

#### B) Use Railway CLI (For Local Scripts)
```bash
# Load Railway env vars and run migration script
railway run python3 railway/run_migration.py
railway run npm run migrate
railway run python manage.py migrate
```

**IMPORTANT**: Direct database connections from Codespaces/local won't work because:
- Railway `DATABASE_URL` uses internal hostname (`postgres_db.railway.internal`)
- This hostname is not resolvable outside Railway network
- Solution: Use API endpoints or ensure psql/migration tools are installed in Railway Docker container

### 3. Testing Locally with Railway Environment
```bash
# Run local dev with Railway variables
railway run npm run dev
railway run python app.py
```

### 4. Checking Service Health
```bash
# View logs in real-time
railway logs --service api

# Check deployment status
railway status
```

## Important Notes for Claude Code

1. **Environment Variables**: Always use `railway run` to execute commands that need access to Railway's environment variables (database URLs, API keys, etc.)

2. **Service References**: When services need to communicate:
   - Use `servicename.railway.internal` for internal networking
   - Reference via environment variables when possible
   - Check `railway variables` to see what's available

3. **Database URLs**: Railway auto-generates connection strings:
   - `DATABASE_URL` for PostgreSQL
   - `MYSQL_URL` for MySQL  
   - `REDIS_URL` for Redis
   - Check exact variable names with `railway variables`

4. **Logs are Key**: When something breaks, immediately check:
   ```bash
   railway logs --tail 200
   ```

5. **Multiple Services**: If I have multiple services, specify with `--service`:
   ```bash
   railway logs --service api
   railway variables --service worker
   ```

6. **Railway Logs Timeout**: `railway logs` command can timeout in Codespaces:
   - Limit output: `railway logs --tail 100`
   - Use `grep` to filter: `railway logs | grep -i error`
   - If it times out, check web dashboard or use API health endpoints

---

## Lessons Learned: Database Migrations on Railway

### Problem: Multi-Statement SQL Files Failing

**Symptom**: Migration endpoint returns success, but tables aren't created.

**Root Cause**:
- Python's `psycopg2.cursor.execute()` can only execute ONE statement at a time
- Splitting SQL on semicolons breaks PL/pgSQL blocks (DO $$...$$)
- Migration files with `DO` blocks need proper parsing

**Solution**:
1. **Install psql in Docker container**:
   ```dockerfile
   # In railway/Dockerfile
   RUN apt-get update && \
       apt-get install -y --no-install-recommends postgresql-client && \
       rm -rf /var/lib/apt/lists/*
   ```

2. **Use subprocess to call psql**:
   ```python
   import subprocess
   import tempfile

   with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False) as f:
       f.write(schema_sql)
       temp_file = f.name

   result = subprocess.run(
       ['psql', db_url, '-f', temp_file],
       capture_output=True,
       text=True,
       timeout=30
   )
   ```

3. **Fallback to psycopg2 if psql not available** (for local dev)

### Problem: Service Not Picking Up New Tables

**Symptom**: Table created successfully, but service still says "schema not found"

**Root Cause**:
- Services check schema at startup
- If check fails, service sets `is_running = False` and stops
- Creating table after startup doesn't trigger service to restart

**Solution**: Redeploy the service after creating tables:
```bash
railway redeploy --service CommandCenter -y
```

### Creating Diagnostic Endpoints

When migrations fail silently, create diagnostic endpoints:
```python
@app.post("/db/run-health-migration")
async def run_health_monitoring_migration():
    # Try psql first
    try:
        result = subprocess.run(['psql', db_url, '-f', temp_file], ...)
        return {
            "status": "success" if result.returncode == 0 else "error",
            "method": "psql",
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except FileNotFoundError:
        # Fall back to psycopg2 with detailed error tracking
        return {"status": "partial", "errors": [...]}
```

This helps identify:
- Whether psql is available
- Which SQL statements are failing
- Exact error messages for debugging

### Session 034: SolArk Telemetry Migration Success ✅

**Problem**: `/system/stats` endpoint failing with "relation 'solark.telemetry' does not exist"

**Discovery**:
- API code referenced `solark.telemetry` table that was never created
- No migration file existed (migrations 001-004 existed, but 005 was missing)
- Table structure needed to support comprehensive energy metrics

**Solution Applied**:
1. **Created migration 005_solark_schema.sql** with:
   - Comprehensive table structure (battery, solar, load, grid metrics)
   - TimescaleDB hypertable support with graceful fallback
   - Performance indexes
   - Built-in verification checks

2. **Added API migration endpoint** (`/db/run-solark-migration`):
   - Uses `psql` subprocess for complex SQL execution
   - Detailed logging and error reporting
   - Idempotent (safe to run multiple times)

3. **Deployment process**:
   ```bash
   # Committed migration files
   git push

   # Deployed new code with migration endpoint
   railway up --service CommandCenter --detach

   # Executed migration via API
   curl -X POST https://api.wildfireranch.us/db/run-solark-migration

   # Verified success
   curl https://api.wildfireranch.us/system/stats
   ```

**Key Takeaways**:
- ✅ API endpoints for migrations work perfectly from Codespaces
- ✅ `psql` in Docker container is essential for complex migrations
- ✅ Idempotent migrations (IF NOT EXISTS) allow safe re-runs
- ✅ Built-in verification checks catch migration failures immediately
- ✅ No service restart needed - new tables accessible immediately
- ✅ Migration completed in under 2 minutes total

**Files Modified**:
- `railway/src/database/migrations/005_solark_schema.sql` (new)
- `railway/src/api/main.py` (added migration endpoint)
- `railway/run_migration.py` (updated for migration 005)

**Result**: Production error resolved, `solark.telemetry` table operational with 0 records (ready for data collection)

**Reference**: [Session 034 Documentation](../../sessions/2025-10/session-034-solark-telemetry-migration.md)

---

## What I Need Help With

When working together, please:
- ✅ Suggest Railway CLI commands when needed
- ✅ Help me understand service relationships
- ✅ Debug using logs and environment variables
- ✅ Write code that works with Railway's environment
- ✅ Explain what each Railway command does before running it
- ✅ Check current Railway status before making changes

## My Current Project

**Project Name**: CommandCenterProject

**Services**:
- CommandCenter (FastAPI backend - Python 3.11)
- POSTGRES_DB (PostgreSQL 16 with TimescaleDB extension)

**Environment**: production

**Public Endpoints**:
- API: https://api.wildfireranch.us
- Dashboard: https://dashboard.wildfireranch.us

**Key Features**:
- SolArk solar inverter data collection
- Victron VRM battery monitoring
- Database health monitoring with historical snapshots
- Knowledge base integration

---

## Quick Reference Cheatsheet

**When in doubt**:
1. `railway status` - See where we are
2. `railway variables` - Check environment configuration
3. `curl https://api.wildfireranch.us/health` - Test if API is responding

**Common Tasks**:
```bash
# Deploy changes
git push origin main
railway redeploy --service CommandCenter -y

# Run migrations
curl -X POST https://api.wildfireranch.us/db/init-schema

# Check service health
curl https://api.wildfireranch.us/health/monitoring/status

# View recent logs (if not timing out)
railway logs --tail 50
```

**Troubleshooting**:
- Migration fails → Check if psql installed in Dockerfile
- Service not picking up changes → Redeploy with `railway redeploy`
- Can't connect to database → You're outside Railway network, use API endpoints
- Logs timing out → Use smaller tail limit or check via API health endpoints