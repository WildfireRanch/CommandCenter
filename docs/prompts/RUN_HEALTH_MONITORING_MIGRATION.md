# Run Health Monitoring Database Migration

**Date Created:** 2025-10-15
**Version:** 1.0
**Purpose:** Execute the final database migration to create the monitoring schema and health_snapshots table

---

## 🎯 Context

The Database Health Dashboard has been fully implemented and deployed. All code is in production and working except for the historical data endpoint, which requires the `monitoring.health_snapshots` table to be created in the database.

**What's Working:**
- ✅ Health status endpoint: `https://api.wildfireranch.us/health/monitoring/status`
- ✅ Frontend Dashboard Health tab deployed
- ✅ Background Health Monitor service integrated
- ✅ All code committed and deployed

**What's Needed:**
- ⏳ Run database migration to create `monitoring.health_snapshots` table
- ⏳ Verify history endpoint works

---

## 📋 Task

You have access to Railway project "CommandCenterProject" (production environment).

**Please execute the following SQL in the Railway PostgreSQL database:**

### Option 1: Use Railway Database Console

1. Go to Railway dashboard
2. Open POSTGRES_DB service
3. Click "Data" or open a database console
4. Run this SQL:

```sql
-- Create monitoring schema
CREATE SCHEMA IF NOT EXISTS monitoring;

-- Create health_snapshots table
CREATE TABLE IF NOT EXISTS monitoring.health_snapshots (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Overall status
    overall_status VARCHAR(20) NOT NULL,

    -- Database metrics
    db_connected BOOLEAN NOT NULL,
    db_active_connections INTEGER,
    db_response_time_ms NUMERIC(10,2),

    -- SolArk poller
    solark_running BOOLEAN,
    solark_healthy BOOLEAN,
    solark_consecutive_failures INTEGER,
    solark_records_24h INTEGER,
    solark_collection_health_pct NUMERIC(5,2),

    -- Victron poller
    victron_running BOOLEAN,
    victron_healthy BOOLEAN,
    victron_consecutive_failures INTEGER,
    victron_records_24h INTEGER,
    victron_collection_health_pct NUMERIC(5,2),
    victron_api_requests_hour INTEGER,

    -- Data quality
    solark_null_pct NUMERIC(5,2),
    victron_null_pct NUMERIC(5,2),

    -- Database size
    solark_table_size_mb NUMERIC(10,2),
    victron_table_size_mb NUMERIC(10,2),

    -- Alert count
    critical_alerts INTEGER DEFAULT 0,
    warning_alerts INTEGER DEFAULT 0
);

-- Create hypertable for time-series optimization
SELECT create_hypertable('monitoring.health_snapshots', 'timestamp', if_not_exists => TRUE);

-- Add 14-day retention policy
SELECT add_retention_policy('monitoring.health_snapshots', INTERVAL '14 days');

-- Create indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_health_snapshots_timestamp
    ON monitoring.health_snapshots(timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_health_snapshots_status
    ON monitoring.health_snapshots(overall_status, timestamp DESC);

-- Grant permissions
GRANT USAGE ON SCHEMA monitoring TO PUBLIC;
GRANT SELECT, INSERT ON monitoring.health_snapshots TO PUBLIC;
GRANT USAGE, SELECT ON SEQUENCE monitoring.health_snapshots_id_seq TO PUBLIC;
```

### Option 2: Use init-schema Endpoint (After Latest Deployment)

If the latest deployment (commit `7791d40a`) has been deployed to Railway backend:

```bash
curl -X POST https://api.wildfireranch.us/db/init-schema
```

This will run all migrations including `004_health_monitoring.sql`.

---

## ✅ Verification Steps

After running the migration:

### 1. Test History Endpoint
```bash
curl https://api.wildfireranch.us/health/monitoring/history?hours=1
```

**Expected Response:**
```json
{
  "status": "success",
  "hours": 1,
  "data": []
}
```

(Empty data array is expected - snapshots haven't been collected yet)

### 2. Wait 5-10 Minutes

The Health Monitor service collects snapshots every 5 minutes. After waiting, check again:

```bash
curl https://api.wildfireranch.us/health/monitoring/history?hours=1
```

**Expected Response:**
```json
{
  "status": "success",
  "hours": 1,
  "data": [
    {
      "timestamp": "2025-10-15T20:15:00.000Z",
      "overall_status": "healthy",
      "solark_collection_health_pct": 98.5,
      "victron_collection_health_pct": 97.2,
      ...
    }
  ]
}
```

### 3. Test Dashboard

1. Visit: https://dashboard.wildfireranch.us
2. Navigate to: **Energy Dashboard → Database Health tab**
3. Verify:
   - Status cards show current health
   - Charts render (may be empty at first)
   - Auto-refresh works
   - After 5-10 minutes, historical data appears in charts

---

## 🔍 Troubleshooting

### If Migration Fails

**Check for existing table:**
```sql
SELECT EXISTS (
    SELECT 1 FROM information_schema.tables
    WHERE table_schema = 'monitoring'
    AND table_name = 'health_snapshots'
);
```

**If table exists but endpoint still fails:**
```sql
-- Verify table structure
\d monitoring.health_snapshots

-- Check if it's a hypertable
SELECT * FROM timescaledb_information.hypertables
WHERE hypertable_name = 'health_snapshots';
```

**If history endpoint returns error:**
Check backend logs in Railway:
```bash
railway logs | grep -i "health\|monitoring"
```

---

## 📊 What Happens After Migration

1. **Immediately:**
   - History endpoint returns empty data (no snapshots yet)
   - Dashboard loads but charts are empty

2. **After 5 minutes:**
   - Background Health Monitor collects first snapshot
   - History endpoint returns first data point
   - Dashboard charts start showing data

3. **After 1 hour:**
   - 12 snapshots collected (5-minute intervals)
   - Charts show meaningful trends
   - All dashboard features fully functional

4. **After 14 days:**
   - Automatic retention policy starts removing old snapshots
   - Rolling 14-day window maintained

---

## 📁 Related Files

- **Migration SQL:** `railway/src/database/migrations/004_health_monitoring.sql`
- **Session Summary:** `docs/sessions/SESSION_031_SUMMARY.md`
- **Implementation Prompt:** `docs/prompts/DATABASE_HEALTH_DASHBOARD_IMPLEMENTATION.md`

---

## ✅ Success Criteria

- [ ] SQL executes without errors
- [ ] History endpoint returns `{"status": "success", ...}` (not an error)
- [ ] After 5-10 minutes, history endpoint returns data with snapshots
- [ ] Dashboard loads without errors
- [ ] Charts render (empty at first, populated after snapshots collect)
- [ ] Backend logs show: "Health snapshot #1 stored"

---

**Once complete, the Database Health Dashboard will be 100% operational!** 🎉
