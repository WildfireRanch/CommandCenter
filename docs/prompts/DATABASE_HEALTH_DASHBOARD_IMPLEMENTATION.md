# Database Health Dashboard - Implementation Prompt

**Date Created:** 2025-10-15
**Version:** 1.0
**Purpose:** Implement a comprehensive database health monitoring dashboard as a new tab in the PowerPlant Energy Dashboard

---

## 📋 Context Documents to Read First

**CRITICAL: Read these documents BEFORE starting implementation:**

1. **System Architecture & State:**
   - `docs/V1.5_MASTER_REFERENCE.md` - Current system architecture, API endpoints, database schema
   - `docs/CLAUDE_NAVIGATION_GUIDE.md` - Navigation and documentation structure
   - `docs/INDEX.md` - Complete documentation index

2. **Database & Polling Context:**
   - `docs/prompts/MASTER_DB_QUALITY_AND_POLLING_VALIDATION.md` - Health check commands and expected values
   - `docs/AGENT_DATABASE_FIX_SUMMARY.md` - Recent fixes and polling architecture
   - `railway/src/services/solark_poller.py` - SolArk poller implementation
   - `railway/src/services/victron_poller.py` - Victron poller implementation

3. **Frontend Architecture:**
   - `vercel/src/app/energy/page.tsx` - Energy dashboard structure
   - `vercel/src/app/energy/components/` - Existing dashboard components
   - `docs/reference/CommandCenter Code Style Guide.md` - Code standards

4. **API Reference:**
   - `railway/src/api/main.py` - All API endpoints (look for `/health`, `/solark/health`, `/victron/health`)
   - `railway/src/api/endpoints/` - Endpoint implementations

---

## 🎯 Project Goal

Create a **Database Health Dashboard** as a new tab in the existing PowerPlant Energy Dashboard that:

1. **Displays real-time health metrics** for database and pollers
2. **Runs automated health checks** every 5 minutes
3. **Stores historical health data** for 2-week trend analysis
4. **Provides visual indicators** (green/yellow/red) for quick status assessment
5. **Shows actionable alerts** when issues are detected

---

## 🔧 Implementation Requirements

### **Backend Requirements**

#### 1. Create New Health Monitoring Endpoint
**File:** `railway/src/api/endpoints/health_monitoring.py` (create new file)

**Endpoint:** `GET /health/monitoring/status`

**Purpose:** Aggregate all health metrics into a single comprehensive response

**Response Schema:**
```typescript
{
  timestamp: string;           // ISO 8601 timestamp
  overall_status: "healthy" | "degraded" | "critical";

  // Database Connection
  database: {
    connected: boolean;
    connection_pool: {
      active_connections: number;
      idle_connections: number;
      max_connections: number;
    };
    response_time_ms: number;
  };

  // SolArk Poller Health
  solark_poller: {
    is_running: boolean;
    is_healthy: boolean;
    last_poll_attempt: string;  // ISO 8601
    last_successful_poll: string;
    consecutive_failures: number;
    poll_interval_seconds: number;
    total_polls_24h: number;
    total_records_saved_24h: number;
  };

  // Victron Poller Health
  victron_poller: {
    is_running: boolean;
    is_healthy: boolean;
    last_poll_attempt: string;
    last_successful_poll: string;
    consecutive_failures: number;
    poll_interval_seconds: number;
    total_polls_24h: number;
    total_records_saved_24h: number;
    api_requests_this_hour: number;
    rate_limit_max: number;
  };

  // Data Quality Metrics
  data_quality: {
    solark: {
      total_records: number;
      oldest_record: string;
      newest_record: string;
      records_last_hour: number;
      records_last_24h: number;
      records_last_7d: number;
      null_percentage: number;
      expected_records_24h: number;
      collection_health_pct: number;  // actual/expected * 100
    };
    victron: {
      total_records: number;
      oldest_record: string;
      newest_record: string;
      records_last_hour: number;
      records_last_24h: number;
      records_last_72h: number;  // Victron retention limit
      null_percentage: number;
      expected_records_24h: number;
      collection_health_pct: number;
    };
  };

  // Database Size & Performance
  database_metrics: {
    solark_table: {
      total_size_mb: number;
      total_rows: number;
      index_size_mb: number;
      avg_row_size_bytes: number;
    };
    victron_table: {
      total_size_mb: number;
      total_rows: number;
      index_size_mb: number;
      avg_row_size_bytes: number;
    };
  };

  // Alerts & Warnings
  alerts: Array<{
    severity: "critical" | "warning" | "info";
    component: "database" | "solark_poller" | "victron_poller" | "data_quality";
    message: string;
    timestamp: string;
  }>;
}
```

**Implementation Notes:**
- Aggregate data from existing endpoints: `/health`, `/solark/health`, `/victron/health`
- Query database directly for table size metrics using `pg_total_relation_size()`
- Calculate data quality metrics using SQL queries
- Apply business logic to determine overall_status and alerts
- Cache response for 30 seconds to reduce database load

**SQL Queries Needed:**
```sql
-- Database connection pool stats
SELECT * FROM pg_stat_activity WHERE datname = current_database();

-- Table size metrics
SELECT
  pg_size_pretty(pg_total_relation_size('solark.plant_flow')) as total_size,
  pg_size_pretty(pg_relation_size('solark.plant_flow')) as table_size,
  pg_size_pretty(pg_indexes_size('solark.plant_flow')) as indexes_size,
  (SELECT COUNT(*) FROM solark.plant_flow) as total_rows;

-- Data quality: NULL percentage
SELECT
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE pv_power IS NULL OR batt_power IS NULL OR soc IS NULL) as nulls,
  ROUND((COUNT(*) FILTER (WHERE pv_power IS NULL OR batt_power IS NULL OR soc IS NULL)::numeric / COUNT(*) * 100), 2) as null_pct
FROM solark.plant_flow
WHERE created_at >= NOW() - INTERVAL '24 hours';

-- Data collection health
SELECT
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '1 hour') as last_hour,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '24 hours') as last_24h,
  COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '7 days') as last_7d
FROM solark.plant_flow;
```

---

#### 2. Create Health History Storage
**File:** `railway/src/database/migrations/004_health_monitoring.sql` (create new file)

**Purpose:** Store historical health metrics for trend analysis

**Schema:**
```sql
CREATE SCHEMA IF NOT EXISTS monitoring;

CREATE TABLE monitoring.health_snapshots (
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
SELECT create_hypertable('monitoring.health_snapshots', 'timestamp');

-- Retention policy: keep 14 days
SELECT add_retention_policy('monitoring.health_snapshots', INTERVAL '14 days');

-- Index for fast queries
CREATE INDEX idx_health_snapshots_timestamp ON monitoring.health_snapshots(timestamp DESC);
CREATE INDEX idx_health_snapshots_status ON monitoring.health_snapshots(overall_status, timestamp DESC);
```

---

#### 3. Create Background Health Monitoring Service
**File:** `railway/src/services/health_monitor.py` (create new file)

**Purpose:** Automatically collect and store health metrics every 5 minutes

**Implementation:**
```python
class HealthMonitor:
    """
    Background service that monitors database and poller health.
    Runs every 5 minutes and stores snapshots for historical analysis.
    """

    def __init__(self):
        self.interval = 300  # 5 minutes
        self.is_running = False

    async def start(self):
        """Start continuous health monitoring loop"""
        # Poll health endpoint
        # Store snapshot in monitoring.health_snapshots
        # Run every 5 minutes
        pass

    async def collect_health_snapshot(self):
        """Collect current health metrics and store in database"""
        pass

    async def check_alerts(self):
        """Analyze current state and generate alerts"""
        pass
```

**Integrate into FastAPI startup:**
- Add to `railway/src/api/main.py` lifespan function
- Start alongside SolArk and Victron pollers

---

#### 4. Create Health History Query Endpoint
**Endpoint:** `GET /health/monitoring/history`

**Query Parameters:**
- `hours` (optional, default: 24, max: 336 for 14 days)
- `metric` (optional: "overall" | "solark" | "victron" | "database")

**Purpose:** Return historical health data for trend charts

**Response:**
```typescript
{
  status: "success";
  hours: number;
  data: Array<{
    timestamp: string;
    overall_status: string;
    solark_collection_health_pct: number;
    victron_collection_health_pct: number;
    db_response_time_ms: number;
    solark_records_24h: number;
    victron_records_24h: number;
    critical_alerts: number;
    warning_alerts: number;
  }>;
}
```

---

### **Frontend Requirements**

#### 1. Create New Dashboard Tab
**File:** `vercel/src/app/energy/page.tsx` (modify existing)

**Changes:**
- Add new tab: "Database Health" (icon: activity monitor or heartbeat)
- Position after existing tabs (Real-time, Historical, Analytics, etc.)
- Tab should be accessible but not prominently featured (utility tab)

---

#### 2. Create Database Health Component
**File:** `vercel/src/app/energy/components/DatabaseHealthTab.tsx` (create new)

**Layout Structure:**
```
┌─────────────────────────────────────────────────────────┐
│ DATABASE HEALTH MONITORING                    [Refresh] │
│ Last updated: 2 minutes ago                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  OVERALL    │  │  SOLARK     │  │  VICTRON    │    │
│  │  ● Healthy  │  │  ● Healthy  │  │  ● Healthy  │    │
│  │  100% uptime│  │  480/480    │  │  480/480    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ ACTIVE ALERTS                            [0]    │   │
│  │                                                  │   │
│  │ ✅ All systems operational                      │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 24-HOUR COLLECTION HEALTH                       │   │
│  │                                                  │   │
│  │  [Chart: Line graph showing collection %]       │   │
│  │   - SolArk: 100%                                │   │
│  │   - Victron: 98%                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │ POLLER STATS │  │ DATABASE     │  │ DATA        │  │
│  │              │  │ METRICS      │  │ QUALITY     │  │
│  │ Last poll:   │  │              │  │             │  │
│  │   2 min ago  │  │ Size: 1.2GB  │  │ NULL: 0.1%  │  │
│  │ Interval:    │  │ Rows: 156K   │  │ Gaps: None  │  │
│  │   180s       │  │ Response:    │  │ Outliers: 0 │  │
│  │ Failures: 0  │  │   45ms       │  │             │  │
│  └──────────────┘  └──────────────┘  └─────────────┘  │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 7-DAY TRENDS                        [▼ 14 days] │   │
│  │                                                  │   │
│  │  [Chart: Multi-line showing health % over time] │   │
│  │   - Overall Health                              │   │
│  │   - SolArk Collection                           │   │
│  │   - Victron Collection                          │   │
│  └─────────────────────────────────────────────────┘   │
│                                                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │ DETAILED METRICS                     [▼ Expand] │   │
│  │                                                  │   │
│  │  📊 SolArk Table                                │   │
│  │     • Total Records: 156,234                    │   │
│  │     • Oldest Record: 45 days ago                │   │
│  │     • Table Size: 856 MB                        │   │
│  │     • Index Size: 124 MB                        │   │
│  │     • Avg Row Size: 5.8 KB                      │   │
│  │                                                  │   │
│  │  📊 Victron Table                               │   │
│  │     • Total Records: 3,456                      │   │
│  │     • Oldest Record: 72 hours ago               │   │
│  │     • Table Size: 42 MB                         │   │
│  │     • Index Size: 8 MB                          │   │
│  │     • Avg Row Size: 12.8 KB                     │   │
│  │                                                  │   │
│  │  🔌 Connection Pool                             │   │
│  │     • Active: 3 / 20                            │   │
│  │     • Idle: 5                                   │   │
│  │     • Waiting: 0                                │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

#### 3. Component Features

**Status Indicators:**
- Green dot (●) = Healthy
- Yellow dot (●) = Degraded
- Red dot (●) = Critical
- Use consistent color scheme: `green-500`, `yellow-500`, `red-500`

**Auto-Refresh:**
- Poll `/health/monitoring/status` every 60 seconds
- Show "Last updated: X minutes ago" timestamp
- Manual refresh button available

**Alerts Section:**
- Show critical alerts prominently (red banner)
- Show warnings in yellow box
- Group alerts by component
- Include timestamp and actionable message
- If no alerts: "✅ All systems operational"

**Charts:**
- Use Recharts library (already in project)
- Line chart for collection health over time
- Area chart for 7-day trends
- Bar chart for hourly record counts (optional)

**Expandable Details:**
- Detailed metrics collapsed by default
- Click to expand and see full database statistics
- Include table sizes, row counts, retention info

---

#### 4. API Integration Hook
**File:** `vercel/src/hooks/useHealthMonitoring.ts` (create new)

```typescript
export function useHealthMonitoring(refreshInterval = 60000) {
  const [healthData, setHealthData] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch current status
  // Fetch historical data
  // Auto-refresh every 60 seconds
  // Handle errors gracefully

  return { healthData, historyData, loading, error, refresh };
}
```

---

### **Testing Requirements**

#### 1. Backend Testing
**Create:** `railway/tests/test_health_monitoring.py`

**Test Cases:**
- Health monitoring endpoint returns complete schema
- Historical data is stored correctly
- Background monitor runs on schedule
- Alerts are generated for known failure states
- Response time is < 500ms
- Database queries are optimized (use EXPLAIN ANALYZE)

#### 2. Frontend Testing
- Tab renders without errors
- Status indicators display correct colors
- Charts render with real data
- Auto-refresh works
- Manual refresh updates data
- Loading states are shown
- Error states are handled gracefully

#### 3. Integration Testing
- End-to-end: Frontend → API → Database → Response
- Verify all metrics are accurate
- Test with missing Victron data (should degrade gracefully)
- Test with database connection failure
- Test with poller stopped

---

## 📊 Success Criteria

### **Functional Requirements:**
- [ ] Health monitoring endpoint returns all required metrics
- [ ] Background monitor stores snapshots every 5 minutes
- [ ] Historical data retention works (14 days)
- [ ] Frontend tab displays all health metrics
- [ ] Auto-refresh works (60-second interval)
- [ ] Status indicators show correct colors
- [ ] Charts render historical trends
- [ ] Alerts display when issues detected
- [ ] Mobile responsive design

### **Performance Requirements:**
- [ ] Health endpoint responds in < 500ms
- [ ] Frontend renders in < 2 seconds
- [ ] Background monitor uses < 5% CPU
- [ ] Database queries use indexes efficiently
- [ ] No memory leaks in auto-refresh

### **Quality Requirements:**
- [ ] Code follows project style guide
- [ ] All functions have docstrings
- [ ] TypeScript types are complete
- [ ] Error handling is comprehensive
- [ ] Tests achieve > 80% coverage

---

## 🚀 Implementation Steps

### **Phase 1: Backend Foundation (4-6 hours)**
1. Read all context documents (30 min)
2. Create health monitoring endpoint (2 hours)
3. Create database migration for health_snapshots table (30 min)
4. Test endpoint manually with curl (30 min)
5. Create health history endpoint (1 hour)

### **Phase 2: Background Monitoring (2-3 hours)**
1. Create HealthMonitor service class (1.5 hours)
2. Integrate into FastAPI startup (30 min)
3. Test background collection (30 min)
4. Verify data is stored in database (30 min)

### **Phase 3: Frontend Implementation (4-6 hours)**
1. Create DatabaseHealthTab component (2 hours)
2. Create useHealthMonitoring hook (1 hour)
3. Implement status indicators and alerts (1 hour)
4. Add charts for trends (1.5 hours)
5. Style and polish UI (30 min)

### **Phase 4: Integration & Testing (2-3 hours)**
1. End-to-end testing (1 hour)
2. Write backend tests (1 hour)
3. Fix bugs and edge cases (1 hour)

### **Phase 5: Deployment (1 hour)**
1. Run database migration on Railway
2. Deploy backend to Railway
3. Deploy frontend to Vercel
4. Verify in production
5. Monitor for first 24 hours

**Total Estimated Time: 13-19 hours**

---

## 🔍 Key Implementation Notes

### **Business Logic for Overall Status:**
```python
def calculate_overall_status(metrics):
    """
    overall_status logic:
    - CRITICAL if: database disconnected OR any poller has >5 consecutive failures
    - DEGRADED if: collection_health < 90% OR response_time > 1000ms
    - HEALTHY if: all checks pass
    """
    if not metrics['database']['connected']:
        return 'critical'

    if (metrics['solark_poller']['consecutive_failures'] > 5 or
        metrics['victron_poller']['consecutive_failures'] > 5):
        return 'critical'

    if (metrics['data_quality']['solark']['collection_health_pct'] < 90 or
        metrics['data_quality']['victron']['collection_health_pct'] < 90):
        return 'degraded'

    if metrics['database']['response_time_ms'] > 1000:
        return 'degraded'

    return 'healthy'
```

### **Alert Generation Logic:**
```python
alerts = []

# Critical alerts
if not db_connected:
    alerts.append({
        'severity': 'critical',
        'component': 'database',
        'message': 'Database connection lost. Check Railway logs immediately.',
        'timestamp': now()
    })

# Warning alerts
if solark_collection_health < 95:
    alerts.append({
        'severity': 'warning',
        'component': 'solark_poller',
        'message': f'SolArk collection at {solark_collection_health}%. Expected 480 records/day, got {actual_records}.',
        'timestamp': now()
    })

# Info alerts
if victron_api_requests > 45:
    alerts.append({
        'severity': 'info',
        'component': 'victron_poller',
        'message': f'Victron API approaching rate limit: {victron_api_requests}/50 requests this hour.',
        'timestamp': now()
    })
```

### **Caching Strategy:**
```python
# Cache health status for 30 seconds to reduce load
from functools import lru_cache
import time

@lru_cache(maxsize=1)
def get_health_status_cached(cache_key):
    return fetch_health_status()

# In endpoint:
cache_key = int(time.time() / 30)  # Changes every 30 seconds
return get_health_status_cached(cache_key)
```

---

## 📝 Code Style Requirements

**Follow project conventions:**
- Python: PEP 8, use type hints, docstrings for all functions
- TypeScript: Strict mode, explicit types, JSDoc comments
- React: Functional components with hooks
- File headers: Include purpose, what/why/how comments
- Error handling: Try/catch blocks with meaningful messages
- Logging: Use structured logging with appropriate levels

**Example File Header:**
```python
# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/endpoints/health_monitoring.py
# PURPOSE: Comprehensive database and poller health monitoring endpoint
#
# WHAT IT DOES:
#   - Aggregates health metrics from all system components
#   - Provides single endpoint for frontend health dashboard
#   - Generates alerts based on health status
#   - Caches responses for 30 seconds to reduce load
#
# DEPENDENCIES:
#   - services/solark_poller.py (poller health)
#   - services/victron_poller.py (poller health)
#   - utils/db.py (database queries)
#
# ENDPOINTS:
#   - GET /health/monitoring/status - Current health snapshot
#   - GET /health/monitoring/history - Historical health data
# ═══════════════════════════════════════════════════════════════════════════
```

---

## 🎯 Definition of Done

### **Backend Complete When:**
- [ ] `/health/monitoring/status` endpoint works and returns all metrics
- [ ] `/health/monitoring/history` endpoint returns 14 days of data
- [ ] Database migration creates `monitoring.health_snapshots` table
- [ ] Background HealthMonitor service runs and collects data every 5 minutes
- [ ] Health snapshots are visible in database: `SELECT * FROM monitoring.health_snapshots LIMIT 10;`
- [ ] Alerts are generated correctly for failure scenarios
- [ ] All backend tests pass
- [ ] Railway deployment successful

### **Frontend Complete When:**
- [ ] "Database Health" tab appears in energy dashboard
- [ ] All status indicators show correct colors
- [ ] Active alerts section displays (or "All systems operational")
- [ ] 24-hour collection health chart renders with real data
- [ ] 7-day trends chart renders with historical data
- [ ] Detailed metrics section expands/collapses
- [ ] Auto-refresh works (updates every 60 seconds)
- [ ] Manual refresh button works
- [ ] "Last updated" timestamp is accurate
- [ ] Mobile responsive
- [ ] No console errors
- [ ] Vercel deployment successful

### **System Complete When:**
- [ ] Health data visible in production dashboard
- [ ] Background monitoring confirmed running (check after 30 minutes)
- [ ] Historical data accumulating (check database has multiple snapshots)
- [ ] All 10 key health tests from MASTER_DB_QUALITY prompt are represented
- [ ] Documentation updated in V1.5_MASTER_REFERENCE.md
- [ ] README updated with new endpoint information

---

## 📚 Additional Resources

**Reference These Files During Implementation:**
- `vercel/src/app/energy/components/RealTimeTab.tsx` - Example tab component structure
- `vercel/src/hooks/useEnergyData.ts` - Example data fetching hook
- `railway/src/api/endpoints/energy_analytics.py` - Example analytics endpoints
- `railway/src/services/solark_poller.py` - Example background service
- `railway/src/database/migrations/001_initial_schema.sql` - Example migration

**Styling References:**
- Use Tailwind CSS classes consistent with existing dashboard
- Card component: `bg-white dark:bg-gray-800 rounded-lg shadow p-6`
- Status colors: `text-green-600`, `text-yellow-600`, `text-red-600`
- Charts: Match color scheme from existing analytics charts

---

## ✅ Final Checklist Before Marking Complete

- [ ] Read all context documents before starting
- [ ] Backend endpoints tested with curl
- [ ] Database migration ran successfully
- [ ] Background monitor verified running
- [ ] Frontend displays real data
- [ ] All charts render correctly
- [ ] Mobile responsive verified
- [ ] Error states tested
- [ ] Production deployment successful
- [ ] Monitored for 24 hours after deployment
- [ ] Documentation updated
- [ ] Code reviewed and approved
- [ ] Tests passing in CI/CD

---

**This prompt is comprehensive and ready to implement. Good luck! 🚀**
