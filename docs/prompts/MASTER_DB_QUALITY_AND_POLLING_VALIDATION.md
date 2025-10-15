# Master Database Quality & Polling Validation

**Purpose:** Quick-check protocol for database health, polling status, and agent data access

**Target:** Backend database, pollers, API endpoints, and agent tool functionality

**Priority:** Critical - Ensures agents have access to time-series data for analytics

**Last Updated:** 2025-10-15

---

## 🔥 CRITICAL LEARNINGS (2025-10-15)

### Common Root Causes When Agents Can't See Data

#### ❌ **Issue #1: Missing Continuous Pollers**
**Symptom:** Agent says "no data available" for historical queries

**Root Cause:** No background service continuously collecting data
- Data only saved when agent queries (reactive, not proactive)
- Results in 1-10 records/day instead of 480+

**Solution:** Create continuous poller services
```python
# Example: railway/src/services/solark_poller.py
- Polls API every 180 seconds (3 minutes)
- Stores data automatically in database
- Runs as background task in FastAPI startup
```

**How to Check:**
```bash
curl https://api.wildfireranch.us/solark/health | jq '.data.is_running'
# Should return: true
```

**Files to Check:**
- `railway/src/services/solark_poller.py`
- `railway/src/services/victron_poller.py`
- `railway/src/api/main.py` (lifespan startup section)

---

#### ❌ **Issue #2: Missing Database Schema**
**Symptom:** Agent tools fail with PostgreSQL errors

**Root Cause:** Tables don't exist even though migration files do
- Schema initialization not run
- Agent queries `victron.battery_readings` → table doesn't exist → error

**Solution:** Initialize schema via API
```bash
curl -X POST https://api.wildfireranch.us/db/init-schema
```

**How to Verify:**
```bash
curl https://api.wildfireranch.us/victron/health
# Should NOT return "table does not exist" error
```

---

#### ❌ **Issue #3: Sparse Data Collection**
**Symptom:** Queries return 1-10 records when expecting hundreds

**Root Cause:** Polling interval too long or poller not running
- Need 480 records/day (20 per hour) for good analytics
- < 100 records/day = insufficient granularity

**Solution:** Set polling interval to 180 seconds (3 minutes)
```python
# In poller service
DEFAULT_POLL_INTERVAL = 180  # 3 minutes
```

**How to Check:**
```bash
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq '.stats.total_records'
# Should return: ~480 after 24 hours
```

---

### 🚀 Quick Health Check (30 seconds)

Run these commands to verify system health:

```bash
# 1. Check API health
curl https://api.wildfireranch.us/health | jq '.checks'

# 2. Check SolArk poller
curl https://api.wildfireranch.us/solark/health | jq '{running: .data.is_running, healthy: .data.is_healthy, interval: .data.poll_interval_seconds, records_24h: .data.readings_count_24h}'

# 3. Check Victron poller
curl https://api.wildfireranch.us/victron/health | jq '{running: .data.poller_running, healthy: .data.is_healthy, records_24h: .data.readings_count_24h}'

# 4. Check data availability
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq '{total_records: .stats.total_records, avg_soc: .stats.avg_soc}'
```

**Expected Results:**
- API health: `database_connected: true`
- SolArk poller: `is_running: true`, `poll_interval_seconds: 180`, `records_24h: ~480`
- Victron poller: `poller_running: true`, `records_24h: ~480`
- Data stats: `total_records: 400-500` (after 24 hours of collection)

---

### 🔧 Quick Fixes

#### Fix #1: Schema Not Initialized
```bash
curl -X POST https://api.wildfireranch.us/db/init-schema
```

#### Fix #2: Poller Not Running
Check Railway logs for errors:
```bash
railway logs
# Look for: "☀️ SolArk poller: ✅" or "🔋 Victron poller: ✅"
```

#### Fix #3: Manual Poll Test
```bash
# Trigger immediate poll
curl -X POST https://api.wildfireranch.us/solark/poll-now
curl -X POST https://api.wildfireranch.us/victron/poll-now
```

---

### 📊 Expected Polling Configuration

**Both pollers should run at 180-second intervals:**

| Poller | Interval | Records/Hour | Records/Day | Purpose |
|--------|----------|--------------|-------------|---------|
| SolArk | 180s (3min) | 20 | 480 | Energy metrics |
| Victron | 180s (3min) | 20 | 480 | Battery metrics |

**Why 3 minutes?**
- Adequate resolution for energy analytics
- Respects API rate limits (Victron: 50/hour max)
- Balances data granularity with API efficiency
- Provides 480 daily data points for rich time-series analysis

---

### 🎯 Agent Tool Dependencies

**Agent tools that require continuous data:**

1. **`get_historical_stats(hours=24)`**
   - Requires: 480 records/day from `solark.plant_flow`
   - Breaks if: < 100 records/day (insufficient data)

2. **`get_time_series_data(hours=24, limit=100)`**
   - Requires: Continuous records from `solark.plant_flow`
   - Breaks if: Large gaps (> 10 min between records)

3. **`get_victron_battery_status()`**
   - Requires: `victron.battery_readings` table exists
   - Breaks if: Table missing or no recent data (> 10 min old)

4. **`get_victron_battery_history(hours=24)`**
   - Requires: 480 records/day from `victron.battery_readings`
   - Breaks if: < 100 records/day

**How agents use this data:**
- Historical comparisons: "What was my solar production yesterday?"
- Trend analysis: "Show me battery level over the last 6 hours"
- Time-based queries: "What time did I hit 2500W?"
- Analytics: Daily averages, peaks, patterns

---

## 📋 Full Validation Checklist

### PHASE 1: Database Schema Validation (15-20 min)

#### Step 1.1: Verify SolArk Schema
**What to check:**
- `solark.plant_flow` table exists and has data
- Check table structure and indexes
- Verify data retention period
- Check for missing or NULL values

**Commands:**
```bash
# Via API (quick check)
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq

# Via Database (detailed)
railway run psql -c "
SELECT
    COUNT(*) as total_records,
    MIN(created_at) as oldest_record,
    MAX(created_at) as newest_record,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as records_last_24h,
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as records_last_7d
FROM solark.plant_flow;
"
```

**Expected Results:**
- Table exists in `solark` schema ✅
- Records from last 24 hours: ~480 (20 per hour)
- Records from last 7 days: ~3,360
- No excessive NULL values in critical columns (< 5%)

**Questions to Answer:**
- [ ] How many records exist in total?
- [ ] What's the oldest record date?
- [ ] How frequently is data being collected? (should be 20 records/hour)
- [ ] Are there any significant gaps in data collection? (> 10 min)
- [ ] What percentage of records have NULL values?

---

#### Step 1.2: Verify Victron Schema
**What to check:**
- `victron` schema exists
- `victron.battery_readings` table exists
- `victron.polling_status` table exists
- Check if Victron poller is running

**Commands:**
```bash
# Via API (quick check)
curl https://api.wildfireranch.us/victron/health | jq

# Check recent readings
curl https://api.wildfireranch.us/victron/battery/current | jq
```

**Expected Results:**
- Schema exists ✅
- Tables exist: `battery_readings`, `polling_status` ✅
- Recent data (< 3 minutes old) ✅
- `polling_status` shows `is_healthy = true` ✅
- Records from last 24h: ~480

**Questions to Answer:**
- [ ] Does the Victron schema exist?
- [ ] If yes, how many battery readings exist?
- [ ] Is the Victron poller healthy and running?
- [ ] How frequently is Victron data collected? (should be every 3 min)
- [ ] Are there discrepancies between Victron SOC and SolArk SOC? (< 5% diff is normal)

**Action Items if Victron Missing:**
- [ ] Initialize Victron schema: `curl -X POST https://api.wildfireranch.us/db/init-schema`
- [ ] Check if Victron poller service is running (Railway logs)
- [ ] Verify Victron API credentials are set (`VICTRON_VRM_USERNAME`, `VRM_API_TOKEN`)
- [ ] Wait 5-10 minutes and re-check health

---

#### Step 1.3: Check TimescaleDB Configuration
**What to check:**
- TimescaleDB extension is enabled
- Hypertables are configured
- Retention policies are active

**Commands:**
```bash
railway run psql -c "SELECT * FROM pg_extension WHERE extname = 'timescaledb';"

railway run psql -c "
SELECT
    hypertable_schema,
    hypertable_name,
    num_chunks,
    compression_enabled
FROM timescaledb_information.hypertables;
"
```

**Expected Results:**
- TimescaleDB extension installed ✅
- `solark.plant_flow` is a hypertable ✅
- `victron.battery_readings` is a hypertable ✅
- Retention policy for Victron: 72 hours

**Questions to Answer:**
- [ ] Is TimescaleDB properly configured?
- [ ] Are tables set up as hypertables for performance?
- [ ] Is data being automatically deleted per retention policies?
- [ ] How many days of SolArk data are being retained?

---

### PHASE 2: Poller Health Validation (10-15 min)

#### Step 2.1: SolArk Poller Health
**What to check:**
- Poller is running
- Polling frequency is correct (180s)
- No consecutive failures
- Data is fresh (< 5 min old)

**Commands:**
```bash
# Check poller health
curl https://api.wildfireranch.us/solark/health | jq

# Expected output:
{
  "status": "success",
  "data": {
    "is_running": true,
    "last_poll_attempt": "2025-10-15T16:30:00",
    "last_successful_poll": "2025-10-15T16:30:00",
    "consecutive_failures": 0,
    "is_healthy": true,
    "poll_interval_seconds": 180,
    "total_polls": 480,
    "total_records_saved": 480,
    "readings_count_24h": 480
  }
}

# Manually trigger poll (for testing)
curl -X POST https://api.wildfireranch.us/solark/poll-now | jq
```

**Red Flags:**
- ❌ `is_running: false` - Poller not started
- ❌ `consecutive_failures > 5` - API errors or auth issues
- ❌ `poll_interval_seconds != 180` - Wrong configuration
- ❌ `readings_count_24h < 400` - Missing data (after 24h of running)

**Questions to Answer:**
- [ ] Is poller running?
- [ ] When was last successful poll? (should be < 5 min ago)
- [ ] Any consecutive failures? (should be 0)
- [ ] How many records in last 24h? (should be ~480)

---

#### Step 2.2: Victron Poller Health
**What to check:**
- Poller is running
- Polling frequency is correct (180s)
- Respecting rate limits (< 50 requests/hour)
- No consecutive failures

**Commands:**
```bash
# Check poller health
curl https://api.wildfireranch.us/victron/health | jq

# Expected output:
{
  "status": "success",
  "data": {
    "poller_running": true,
    "last_poll_attempt": "2025-10-15T16:30:00",
    "last_successful_poll": "2025-10-15T16:30:00",
    "consecutive_failures": 0,
    "is_healthy": true,
    "readings_count_24h": 480,
    "api_requests_this_hour": 15,  // Should be < 50
    "rate_limit_max": 50
  }
}

# Manually trigger poll (for testing)
curl -X POST https://api.wildfireranch.us/victron/poll-now | jq
```

**Red Flags:**
- ❌ `poller_running: false` - Poller not started
- ❌ `consecutive_failures > 5` - API errors or auth issues
- ❌ `api_requests_this_hour > 45` - Approaching rate limit
- ❌ `readings_count_24h < 400` - Missing data

**Questions to Answer:**
- [ ] Is poller running?
- [ ] When was last successful poll? (should be < 5 min ago)
- [ ] How many API requests this hour? (should be < 20)
- [ ] Any consecutive failures? (should be 0)

---

### PHASE 3: Data Quality Checks (15-20 min)

#### Step 3.1: Check Data Freshness
```bash
# Check latest SolArk data
curl "https://api.wildfireranch.us/energy/latest" | jq '.data.created_at'
# Should be < 5 minutes ago

# Check latest Victron data (if available)
curl "https://api.wildfireranch.us/victron/battery/current" | jq '.timestamp'
# Should be < 5 minutes ago
```

#### Step 3.2: Check Data Completeness
```bash
# Check records per hour (should be ~20)
curl "https://api.wildfireranch.us/energy/stats?hours=1" | jq '.stats.total_records'

# Check records per day (should be ~480)
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq '.stats.total_records'

# Check for gaps
curl "https://api.wildfireranch.us/energy/history?hours=1&limit=100" | jq '.count'
```

#### Step 3.3: Check Value Ranges
```bash
# Check for unrealistic values
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq '.stats | {
  min_soc,
  max_soc,
  max_pv_power,
  max_load_power
}'

# Expected ranges:
# - SOC: 0-100%
# - PV power: 0-15000W (depends on system size)
# - Load power: 0-10000W (typical residential)
```

**Red Flags:**
- ❌ SOC > 100% or < 0%
- ❌ Solar power > 0 at night (10pm-6am)
- ❌ Load power = 0 for extended periods
- ❌ Flatlined values (same value 100+ times)

---

### PHASE 4: Agent Tool Testing (10-15 min)

#### Step 4.1: Test Historical Stats Tool
```bash
# Simulates: agent.get_historical_stats(hours=24)
curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq

# Expected: Full statistics with ~480 data points
```

**Success Criteria:**
- Returns statistics ✅
- `total_records` >= 400 ✅
- `avg_soc`, `avg_pv_power`, `avg_load_power` are reasonable ✅

#### Step 4.2: Test Time-Series Tool
```bash
# Simulates: agent.get_time_series_data(hours=6, limit=100)
curl "https://api.wildfireranch.us/energy/history?hours=6&limit=100" | jq '.count'

# Expected: Returns array of timestamped records
```

**Success Criteria:**
- Returns data array ✅
- `count` >= 100 (after 6 hours of collection) ✅
- Each record has timestamp and all power metrics ✅

#### Step 4.3: Test Victron Battery Tool
```bash
# Simulates: agent.get_victron_battery_status()
curl "https://api.wildfireranch.us/victron/battery/current" | jq

# Expected: Current battery metrics (SOC, voltage, current, temp)
```

**Success Criteria:**
- Returns battery data ✅
- Timestamp is recent (< 5 min) ✅
- Values are realistic ✅

---

### PHASE 5: Quick Troubleshooting

#### Issue: "No data available"
**Symptom:** Agent says "no data available for the last X hours"

**Check:**
1. Poller health: `curl https://api.wildfireranch.us/solark/health`
2. Data count: `curl "https://api.wildfireranch.us/energy/stats?hours=24" | jq '.stats.total_records'`
3. Railway logs for errors

**Common Causes:**
- Poller not running (`is_running: false`)
- Insufficient data collection time (wait 1 hour for 20 records)
- Database connection issues
- API authentication failures

#### Issue: "Table does not exist"
**Symptom:** PostgreSQL error in agent responses

**Fix:**
```bash
curl -X POST https://api.wildfireranch.us/db/init-schema
```

**Verify:**
```bash
curl https://api.wildfireranch.us/victron/health
# Should not return PostgreSQL errors
```

#### Issue: Low data count
**Symptom:** `total_records < 100` after 6+ hours

**Check:**
1. Polling interval: `curl https://api.wildfireranch.us/solark/health | jq '.data.poll_interval_seconds'`
   - Should be: 180
2. Consecutive failures: `curl https://api.wildfireranch.us/solark/health | jq '.data.consecutive_failures'`
   - Should be: 0
3. Railway logs for repeated errors

**Common Causes:**
- Polling interval too long (> 300s)
- API authentication expired
- SolArk inverter offline or unreachable
- Database write failures

---

## 🎯 Quick Reference

### Health Check URLs
```
API Health:     https://api.wildfireranch.us/health
SolArk Poller:  https://api.wildfireranch.us/solark/health
Victron Poller: https://api.wildfireranch.us/victron/health
Latest Data:    https://api.wildfireranch.us/energy/latest
Data Stats:     https://api.wildfireranch.us/energy/stats?hours=24
```

### Expected Values (After 24h)
```
SolArk records:   ~480 (20/hour)
Victron records:  ~480 (20/hour)
Poll interval:    180 seconds (both)
Consecutive fails: 0 (both)
NULL values:      < 5%
```

### Quick Fixes
```bash
# Initialize schema
curl -X POST https://api.wildfireranch.us/db/init-schema

# Manual poll
curl -X POST https://api.wildfireranch.us/solark/poll-now
curl -X POST https://api.wildfireranch.us/victron/poll-now

# Check Railway logs
railway logs | grep -E "poller|error"
```

---

## 📚 Related Documentation

- **Fix Summary:** `docs/AGENT_DATABASE_FIX_SUMMARY.md`
- **Validation Report Example:** `docs/V1.7_VALIDATION_REPORT.md`
- **Architecture:** `docs/V1.5_MASTER_REFERENCE.md`
- **Poller Implementation:**
  - `railway/src/services/solark_poller.py`
  - `railway/src/services/victron_poller.py`

---

**Quick validation complete! For comprehensive testing, continue with original V1.7 validation phases (Endpoints, Frontend, Performance, Edge Cases).**
