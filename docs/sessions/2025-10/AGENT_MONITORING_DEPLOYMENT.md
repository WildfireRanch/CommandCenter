# Agent Monitoring System - Deployment Guide

**Created:** October 11, 2025
**Version:** V1.5.1 → V1.6.0
**Status:** Ready for Deployment

---

## 🎯 What Was Built

Comprehensive agent health monitoring, performance tracking, and real-time activity dashboards.

### Backend Components (Railway)
1. **Database Schema** - 4 tables for agent metrics tracking
2. **Telemetry System** - Automatic event logging for all agent activities
3. **Health Check Service** - Real-time agent status monitoring
4. **7 New API Endpoints** - Complete monitoring API

### Frontend Components (Vercel)
1. **Agent Monitor Page** (`/agents`) - Full dashboard with charts and activity feed
2. **Enhanced Status Page** - Added agent health section
3. **2 Reusable Components** - AgentHealthCard + AgentActivityFeed
4. **Updated Navigation** - Added Agent Monitor to sidebar

---

## 📋 Pre-Deployment Checklist

### ✅ Files Created/Modified

**Backend (Railway):**
- ✅ [railway/src/database/migrations/002_agent_metrics.sql](../railway/src/database/migrations/002_agent_metrics.sql) - NEW
- ✅ [railway/src/utils/agent_telemetry.py](../railway/src/utils/agent_telemetry.py) - NEW
- ✅ [railway/src/services/agent_health.py](../railway/src/services/agent_health.py) - NEW
- ✅ [railway/src/api/main.py](../railway/src/api/main.py) - MODIFIED (added 7 endpoints)
- ✅ [railway/src/agents/solar_controller.py](../railway/src/agents/solar_controller.py) - MODIFIED (added telemetry)
- ✅ [railway/src/agents/energy_orchestrator.py](../railway/src/agents/energy_orchestrator.py) - MODIFIED (added telemetry)
- ✅ [railway/src/agents/manager.py](../railway/src/agents/manager.py) - MODIFIED (added telemetry)

**Frontend (Vercel):**
- ✅ [vercel/src/components/AgentHealthCard.tsx](../vercel/src/components/AgentHealthCard.tsx) - NEW
- ✅ [vercel/src/components/AgentActivityFeed.tsx](../vercel/src/components/AgentActivityFeed.tsx) - NEW
- ✅ [vercel/src/app/agents/page.tsx](../vercel/src/app/agents/page.tsx) - NEW
- ✅ [vercel/src/app/status/page.tsx](../vercel/src/app/status/page.tsx) - MODIFIED (added agent health)
- ✅ [vercel/src/components/Sidebar.tsx](../vercel/src/components/Sidebar.tsx) - MODIFIED (added link)

---

## 🚀 Deployment Steps

### Step 1: Run Database Migration

**Option A: Via API (Recommended)**
```bash
curl -X POST https://api.wildfireranch.us/db/init-schema \
  -H "Content-Type: application/json"
```

**Option B: Direct SQL in Railway Console**
1. Go to Railway Dashboard → PostgreSQL
2. Click "Query" tab
3. Paste contents of `railway/src/database/migrations/002_agent_metrics.sql`
4. Execute

**Verify Migration Success:**
```bash
curl https://api.wildfireranch.us/db/schema-status | jq
```

Look for `agent_metrics` schema in the response.

---

### Step 2: Deploy Backend to Railway

```bash
cd /workspaces/CommandCenter

# Stage all changes
git add railway/

# Commit
git commit -m "Add agent health monitoring and telemetry system

- Add database schema for agent metrics tracking
- Implement telemetry middleware with decorators
- Create health check service for all agents
- Add 7 new API endpoints for agent monitoring
- Instrument all 3 agents with telemetry tracking
- Implements V1.6.0 agent observability features"

# Push to Railway (auto-deploys)
git push origin main
```

**Verify Deployment:**
```bash
# Check API health
curl https://api.wildfireranch.us/health | jq

# Test new endpoints
curl https://api.wildfireranch.us/agents/health | jq
curl https://api.wildfireranch.us/agents/activity?limit=10 | jq
curl https://api.wildfireranch.us/system/stats | jq
```

---

### Step 3: Deploy Frontend to Vercel

```bash
# Stage frontend changes
git add vercel/

# Commit
git commit -m "Add comprehensive agent monitoring dashboard

- Create Agent Monitor page with health cards and charts
- Add AgentHealthCard and AgentActivityFeed components
- Enhance Status page with agent health section
- Add Agent Monitor link to navigation sidebar
- Real-time activity feed with auto-refresh
- Performance analytics and tool usage charts"

# Push (Vercel auto-deploys)
git push origin main
```

**Verify Deployment:**
Visit: https://dashboard.wildfireranch.us/agents

---

### Step 4: Smoke Test

**Test Agent Monitoring:**
1. Visit `/agents` page
2. Should see 3 agent health cards (Manager, Solar Controller, Energy Orchestrator)
3. Initially may show "degraded" status (normal until agents run)

**Trigger Agent Activity:**
1. Go to `/chat` page
2. Ask: "What's my battery level?"
3. Wait for response
4. Return to `/agents` page
5. Should see activity in the feed!

**Check Status Page:**
1. Visit `/status` page
2. Scroll to "Agent Services" section
3. Should show all 3 agents with health status

---

## 📊 New API Endpoints

All endpoints return JSON with `{ status, data, timestamp }` format.

### Agent Health
```bash
# Get all agents health
GET /agents/health

# Get specific agent health
GET /agents/Manager/health
GET /agents/Solar%20Controller/health
GET /agents/Energy%20Orchestrator/health
```

### Agent Activity
```bash
# Get recent activity (all agents)
GET /agents/activity?limit=100

# Get activity for specific agent
GET /agents/Manager/activity?limit=50
```

### Agent Metrics
```bash
# Get metrics for all agents (24h)
GET /agents/metrics?hours=24

# Get metrics for specific agent
GET /agents/Solar%20Controller/metrics?hours=24
```

### System Stats
```bash
# Get comprehensive system statistics
GET /system/stats
```

---

## 🔍 Testing Checklist

### Backend Tests
- [ ] Database migration ran successfully
- [ ] `/health` endpoint still works
- [ ] `/agents/health` returns agent status
- [ ] `/agents/activity` returns empty array (initially)
- [ ] `/system/stats` returns counts
- [ ] Agent chat triggers telemetry events

### Frontend Tests
- [ ] `/agents` page loads without errors
- [ ] Agent health cards display
- [ ] Charts render (may be empty initially)
- [ ] Activity feed shows "No recent activity" (initially)
- [ ] `/status` page shows agent services section
- [ ] Sidebar shows "Agent Monitor" link
- [ ] Navigation to `/agents` works

### End-to-End Tests
- [ ] Ask agent a question via `/chat`
- [ ] Check `/agents/activity` API - should have events
- [ ] Refresh `/agents` page - should show activity
- [ ] Health cards should show "online" status
- [ ] Activity feed should show the query event

---

## 🐛 Troubleshooting

### "No agent health data available"
**Cause:** Database migration not run or tables don't exist
**Fix:** Run migration (Step 1 above)

### "Agent status: degraded"
**Cause:** OpenAI API key not configured or database not connected
**Fix:** Check Railway environment variables

### "Activity feed empty"
**Cause:** No agents have run yet
**Fix:** Normal! Use the chat to trigger an agent, then check feed

### "Charts showing no data"
**Cause:** No metrics collected yet (need 24h of activity)
**Fix:** Normal for new deployment. Will populate as agents are used.

### Migration fails with "schema already exists"
**Cause:** Tables already exist from previous run
**Fix:** Safe to ignore if tables exist. Verify with `/db/schema-status`

---

## 📈 What to Expect After Deployment

### Immediately After Deployment
- ✅ All 3 agents show health status (likely "degraded" initially)
- ✅ Activity feed is empty
- ✅ Charts show "No data available"
- ✅ System stats show counts (conversations, energy snapshots)

### After First Agent Query
- ✅ Agent status changes to "online"
- ✅ Activity feed shows event
- ✅ Metrics start accumulating

### After 24 Hours of Use
- ✅ Charts populate with real data
- ✅ Success rate calculations meaningful
- ✅ Tool usage patterns visible
- ✅ Performance trends emerge

---

## 🎨 Features Overview

### Agent Monitor Page (`/agents`)
- **Summary Stats:** Online count, total events, avg success rate
- **Health Cards:** Status, last seen, response time, success rate per agent
- **Tool Usage Chart:** Bar chart comparing tool calls across agents
- **Performance Chart:** Line chart showing response times and success rates
- **Activity Feed:** Real-time scrolling list of agent events (auto-refreshes every 10s)

### Enhanced Status Page (`/status`)
- **Agent Services Section:** Grid of 3 agent cards with status indicators
- **Integrated Health Checks:** Shows agent response times
- **System-wide Statistics:** Updated with agent event counts

### Reusable Components
- **AgentHealthCard:** Displays single agent status with pulse animation
- **AgentActivityFeed:** Configurable activity list with auto-refresh

---

## 🔐 Security Notes

- All endpoints are public (no auth required currently)
- Telemetry data includes query text (may contain sensitive info)
- Consider adding auth if exposing publicly

---

## 📝 Next Steps

1. **Monitor for 24-48 hours** - Let metrics accumulate
2. **Review activity patterns** - See which agents are called most
3. **Check for errors** - Watch for failed events in activity feed
4. **Optimize based on data** - Use metrics to improve agent performance

---

## 🆘 Support

**Documentation:**
- This file: `/docs/AGENT_MONITORING_DEPLOYMENT.md`
- Master reference: `/docs/V1.5_MASTER_REFERENCE.md`
- V2 Roadmap: `/docs/V2_Roadmap.md`

**Check Logs:**
- Railway: Click service → "Logs" tab
- Vercel: Project dashboard → "Deployments" → Click deployment → "Function Logs"

---

**Deployed:** Awaiting deployment
**Version:** V1.6.0
**Ready:** YES ✅
