# Session 034: SolArk Telemetry Table Migration

**Date:** 2025-10-16
**Status:** ✅ Complete
**Priority:** HIGH (Critical bug fix)

---

## Executive Summary

Successfully resolved critical database error blocking `/system/stats` endpoint by creating and executing migration 005 for the `solark.telemetry` table. The table was referenced in the API code but never actually created in the database, causing a "relation does not exist" error.

### Key Achievement
- Fixed production error: `relation "solark.telemetry" does not exist`
- Created comprehensive migration with TimescaleDB hypertable support
- Deployed new API endpoint for migration execution
- Verified all functionality working in production

---

## Problem Statement

### Issue
The `/system/stats` endpoint was failing with:
```
"detail": "Failed to get system stats: relation \"solark.telemetry\" does not exist"
```

### Root Cause
- API code at [railway/src/api/main.py:2815](../../railway/src/api/main.py#L2815-L2850) queries `solark.telemetry`
- No migration file existed to create this table
- Previous sessions created `monitoring.health_snapshots` (004) and `victron` schema, but `solark.telemetry` was overlooked

---

## Solution Implemented

### 1. Created Migration File
**File:** [railway/src/database/migrations/005_solark_schema.sql](../../railway/src/database/migrations/005_solark_schema.sql)

**Features:**
- Creates `solark` schema
- Creates `solark.telemetry` table with comprehensive energy metrics
- TimescaleDB hypertable support (with graceful fallback)
- Performance indexes on timestamp, plant_id, and created_at
- Idempotent (safe to run multiple times)
- Verification checks built-in

**Table Structure:**
```sql
CREATE TABLE solark.telemetry (
    id SERIAL PRIMARY KEY,
    plant_id INTEGER,
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),

    -- Battery metrics
    soc FLOAT,                    -- State of Charge (%)
    batt_power FLOAT,             -- Battery power (W)
    batt_voltage FLOAT,           -- Battery voltage (V)
    batt_current FLOAT,           -- Battery current (A)

    -- Solar metrics
    pv_power FLOAT,               -- Total PV production (W)
    pv_voltage FLOAT,             -- PV voltage (V)
    pv_current FLOAT,             -- PV current (A)

    -- Load metrics
    load_power FLOAT,             -- Total load consumption (W)

    -- Grid metrics
    grid_power FLOAT,             -- Grid power (W)
    pv_to_grid FLOAT,             -- PV to grid export (W)
    grid_to_load FLOAT,           -- Grid to load import (W)

    -- Power flow indicators
    pv_to_load BOOLEAN DEFAULT FALSE,
    pv_to_bat BOOLEAN DEFAULT FALSE,
    bat_to_load BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 2. Added API Migration Endpoint
**File:** [railway/src/api/main.py:611-702](../../railway/src/api/main.py#L611-L702)

**Endpoint:** `POST /db/run-solark-migration`

**Why Needed:**
- Railway internal hostnames (`.railway.internal`) not accessible from Codespaces
- Alternative to `railway run python3` commands that fail due to network restrictions
- Follows pattern from Session 032's health monitoring migration

**Method:**
- Uses `psql` subprocess for multi-statement SQL execution
- Handles DO blocks and complex migrations
- Detailed logging and error reporting
- Returns migration status, stdout, and stderr

### 3. Updated Migration Runner
**File:** [railway/run_migration.py](../../railway/run_migration.py)

**Changes:**
- Modified to run migration 005 (was hardcoded for 004)
- Uses `psql` via subprocess for multi-statement SQL
- Includes verification checks for table and hypertable creation
- Better error handling and output formatting

---

## Execution Process

### Step 1: Development
```bash
# Created migration file
railway/src/database/migrations/005_solark_schema.sql

# Updated migration runner
railway/run_migration.py

# Added API endpoint
railway/src/api/main.py
```

### Step 2: Deployment
```bash
# Committed changes
git add railway/src/database/migrations/005_solark_schema.sql \
        railway/src/api/main.py \
        railway/run_migration.py

git commit -m "Add SolArk telemetry table migration (005)"
git push

# Deployed to Railway
railway up --service CommandCenter --detach
```

### Step 3: Migration Execution
```bash
# Executed migration via API endpoint
curl -X POST https://api.wildfireranch.us/db/run-solark-migration

# Response:
{
  "status": "success",
  "message": "SolArk migration completed via psql",
  "method": "psql",
  "stdout": "CREATE SCHEMA\nCREATE TABLE\nDO\nCREATE INDEX...",
  "stderr": "NOTICE: SUCCESS: solark.telemetry table created",
  "timestamp": 1760580700.0955336
}
```

### Step 4: Verification
```bash
# Test /system/stats endpoint
curl https://api.wildfireranch.us/system/stats

# Response:
{
  "status": "success",
  "data": {
    "total_energy_snapshots": 0,
    "total_conversations": 141,
    "conversations_today": 3,
    "latest_energy": null,
    "agent_events_24h": 10
  }
}
```

---

## Verification Results

### ✅ All Checks Passing

1. **Migration File:** `005_solark_schema.sql` created (3.5KB)
2. **Schema Created:** `solark` schema exists in database
3. **Table Created:** `solark.telemetry` table exists
4. **Columns:** All required columns present (timestamp, soc, pv_power, etc.)
5. **Indexes:** 3 performance indexes created
6. **API Endpoint:** `/system/stats` returns success (no errors)
7. **Migration Idempotency:** Safe to re-run multiple times
8. **Health Check:** All systems operational
9. **Database Connection:** Active and healthy
10. **Migration Endpoint:** `/db/run-solark-migration` available

### Database Schema Status
```bash
curl https://api.wildfireranch.us/db/schema-status

# Shows:
{
  "tables": [
    {"table_schema": "solark", "table_name": "plant_flow"},
    {"table_schema": "solark", "table_name": "telemetry"},
    ...
  ]
}
```

---

## Key Learnings

### Railway Database Access Pattern
Following lessons from [docs/guides/RAILWAY_ACCESS_GUIDE.md](../../guides/RAILWAY_ACCESS_GUIDE.md):

1. **Network Isolation:** Railway internal hostnames only work within Railway network
2. **Access Methods:** Use API endpoints or `railway run` for database operations
3. **Multi-Statement SQL:** `psql` required for DO blocks (psycopg2 is single-statement only)
4. **Migration Strategy:** Create dedicated API endpoints for complex migrations

### Best Practices Applied
1. **Idempotent Migrations:** Use `IF NOT EXISTS` clauses
2. **Verification Checks:** Built-in SQL verification at end of migration
3. **Graceful Degradation:** TimescaleDB hypertable with fallback to regular table
4. **Comprehensive Logging:** Detailed output for troubleshooting
5. **API-First Approach:** Migration endpoints for remote execution

---

## Files Modified/Created

### New Files
- `railway/src/database/migrations/005_solark_schema.sql` (3.5KB)

### Modified Files
- `railway/run_migration.py` (updated for migration 005)
- `railway/src/api/main.py` (added `/db/run-solark-migration` endpoint)

### Git Commit
```
commit a52bac18
Author: WildfireRanch <208496887+WildfireRanch@users.noreply.github.com>
Date:   Thu Oct 16 02:06:00 2025 +0000

    Add SolArk telemetry table migration (005)

    - Create migration 005_solark_schema.sql
    - Creates solark schema and solark.telemetry hypertable
    - Adds /db/run-solark-migration API endpoint
    - Update run_migration.py to use psql for DO blocks
    - Fixes /system/stats endpoint error

    Fixes: relation "solark.telemetry" does not exist
```

---

## Related Sessions

- **Session 032:** Database Health Monitoring Migration (reference pattern)
- **Session 030:** Victron schema creation (similar approach)
- **Session 033:** V1-V2 Validation Audit (context for system state)

---

## Next Steps

### Immediate
- ✅ Table created and ready for data
- ✅ API endpoint working correctly
- ✅ No production errors

### Future Enhancements
1. **Data Collection:** SolArk poller will start populating this table
2. **Retention Policy:** Consider enabling 90-day retention (commented in migration)
3. **TimescaleDB:** Install extension for better time-series performance
4. **Monitoring:** Add alerts for table growth and query performance

---

## API Endpoints Added

### `POST /db/run-solark-migration`
Executes the SolArk schema migration.

**Usage:**
```bash
curl -X POST https://api.wildfireranch.us/db/run-solark-migration
```

**Response:**
```json
{
  "status": "success",
  "message": "SolArk migration completed via psql",
  "method": "psql",
  "stdout": "...",
  "stderr": "...",
  "timestamp": 1760580700.0955336
}
```

---

## Database Schema

### Tables in `solark` Schema
1. `solark.plant_flow` (existing)
2. `solark.telemetry` (new - migration 005)

### Indexes Created
1. `idx_solark_telemetry_timestamp` - Performance for time-range queries
2. `idx_solark_telemetry_plant_id` - Multi-plant support
3. `idx_solark_telemetry_created_at` - Metadata queries

---

## Testing Performed

### 1. Migration Execution
- ✅ Migration runs successfully
- ✅ Tables created with correct structure
- ✅ Indexes created
- ✅ No SQL errors

### 2. API Endpoint Testing
- ✅ `/system/stats` returns success (was failing before)
- ✅ `/health` shows all checks passing
- ✅ `/db/schema-status` shows solark.telemetry
- ✅ `/db/run-solark-migration` executes correctly

### 3. Idempotency Testing
- ✅ Migration can be run multiple times
- ✅ No errors when tables already exist
- ✅ Graceful "already exists" notices

### 4. Database Verification
- ✅ Schema exists: `solark`
- ✅ Table exists: `solark.telemetry`
- ✅ Columns match API expectations
- ✅ Ready to accept data

---

## Success Criteria - All Met ✅

- [x] `/system/stats` endpoint returns success
- [x] `solark.telemetry` table exists in database
- [x] No errors in Railway deployment logs
- [x] Table structure matches API requirements
- [x] Migration is idempotent
- [x] API endpoint for migration available
- [x] Documentation updated
- [x] Code committed and pushed

---

## Status: COMPLETE ✅

The SolArk telemetry table migration has been successfully implemented, deployed, and verified. The production error has been resolved and the system is ready for energy data collection.

**Time Invested:** ~90 minutes
**Complexity:** Medium (standard migration with API endpoint)
**Impact:** HIGH (fixed critical production error)
