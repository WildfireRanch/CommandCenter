# CommandCenter V2 Roadmap

**Version:** V1.6 → V2.0 Modular Plan  
**Created:** October 10, 2025  
**Foundation:** V1.5.0 (Production Ready)  
**Timeline:** 19 weeks (~4.5 months)

---

## 🎯 Executive Summary

CommandCenter V2 transforms the current intelligent monitoring system into a full autonomous energy management platform. Built on the solid V1.5 foundation, V2 adds:

- **Data Foundation** (V1.6): Accurate time-series from all sources
- **Hardware Control** (V1.7): Safe manual device control
- **Safety & Rules** (V1.8): User preferences and guardrails
- **Full Observability** (V1.9): Real-time monitoring dashboards
- **Automation** (V2.0): Intelligent autonomous operation

**Approach:** 5 incremental versions, each independently valuable, fully tested, production-deployed.

---

## 📋 V1.5 Foundation (Current State)

### What We Have
**Reference:** `docs/V1.5_MASTER_REFERENCE.md`

**Agents (3):**
- Manager (query routing)
- Solar Controller (real-time status)
- Energy Orchestrator (planning & recommendations)

**Tools (6):**
- KB search (semantic)
- SolArk status
- Battery optimizer
- Miner coordinator
- Energy planner

**Data Sources (Current):**
- ✅ SolArk screen scrape (solar/load/grid)
- ✅ Knowledge Base (15 docs, 141,889 tokens)
- ✅ Agent conversations
- ❌ NO Victron Cerbo data
- ❌ NO Shelly power monitoring

**Database (8 tables):**
- `agent.*` - Conversations, messages
- `solark.*` - Energy data
- `public.*` - KB documents, chunks, sync log

**APIs (18+ endpoints):**
- Agent chat, conversations
- Energy data, stats
- KB sync, search
- Health monitoring

**Deployment:**
- Railway: Backend API + Dashboard
- Vercel: Frontend (planned)
- PostgreSQL + TimescaleDB + pgvector

---

## 🏗️ Architectural Principles

### Cloud-First Strategy ✅
**Decision:** Use cloud APIs exclusively
- Victron VRM API (not local)
- Shelly Cloud API (not local)
- No Node-RED, no local MQTT
- **Reason:** Remote operation 5/7 days, better reliability, faster development

### Desktop-First Development ✅
**Decision:** Build full web dashboard before mobile
- Complete feature set at wildfireranch.us
- Mobile PWA in V2+ (informed by desktop learnings)

### Hardware Reality ✅
**Critical Understanding:**

**Victron Cerbo GX:**
- Battery monitor ONLY (read-only)
- Shunt + temp sensor
- NO control capability
- Excellent VRM Cloud API
- **Use for:** Primary battery data source

**SolArk:**
- Charge controller (actual control)
- Screen scrape works (no Modbus access yet)
- **Use for:** Solar/load/grid data

**Shelly:**
- Load control (on/off switches)
- Power monitoring per device
- **Use for:** Device control + consumption tracking

### Data Lifecycle Policy ✅
**Polling Frequencies:**
- Victron Cerbo: Every 3 minutes (battery)
- SolArk: Every 2 minutes (solar/load/grid)  
- Shelly: Every 2 minutes (power per device)

**Retention:**
- Raw data: 72 hours
- Hourly aggregates: 30 days
- Daily aggregates: 2 years

**Storage Impact:** ~2.5 MB total (negligible)

---

## 🗺️ Version Progression

```
V1.5 ✅ (COMPLETE)
  ↓
V1.6 (2 weeks) → Data Foundation
  ↓
V1.7 (2-3 weeks) → Control Foundation
  ↓
V1.8 (2-3 weeks) → Safety & Preferences
  ↓
V1.9 (2-3 weeks) → Full Observability
  ↓
V2.0 (2-3 weeks) → Automation Engine
```

---

# V1.6: Data Foundation (2 weeks)

## Goal
Collect accurate time-series data from all sources with retention policy.

## Deliverables

### Week 1: Multi-Source Data Collection

**Victron Cerbo Integration:**
- [ ] VRM API client (`railway/src/integrations/victron.py`)
- [ ] Battery readings table (`victron.battery_readings`)
- [ ] Polling service (3-minute intervals)
- [ ] API endpoint: `GET /victron/battery/current`
- [ ] API endpoint: `GET /victron/battery/history`

**Shelly Power Monitoring:**
- [ ] Shelly Cloud API client (`railway/src/integrations/shelly.py`)
- [ ] Device registry (`shelly.devices` table)
- [ ] Power readings table (`shelly.power_readings`)
- [ ] Polling service (2-minute intervals)
- [ ] API endpoint: `GET /shelly/power/current`
- [ ] API endpoint: `GET /shelly/device/{name}/history`

**SolArk Standardization:**
- [ ] Verify 2-minute polling
- [ ] Ensure consistent data storage
- [ ] Error handling improvements

### Week 2: Data Management

**Database:**
- [ ] TimescaleDB schemas (battery, power, system)
- [ ] Aggregation queries (hourly, daily)
- [ ] Retention cleanup scripts (manual)
- [ ] Migration: `migrations/003_victron_schema.sql`
- [ ] Migration: `migrations/004_shelly_schema.sql`

**Agent Tools:**
- [ ] `get_cerbo_battery_status()` - current accurate battery
- [ ] `get_device_power_usage()` - Shelly power consumption
- [ ] `analyze_power_trend()` - device usage analysis

**Simple Dashboard:**
- [ ] Power monitor page (`/power`)
- [ ] Device status cards
- [ ] 24-hour usage chart

**Monitoring:**
- [ ] Polling health check
- [ ] Data gap detection
- [ ] Alert if polling fails >10 min

## Success Criteria
- ✅ Cerbo, SolArk, Shelly all flowing
- ✅ Database under 10 MB
- ✅ No polling failures >5%
- ✅ Agents use Cerbo for battery decisions
- ✅ Can see per-device power consumption

## NOT in V1.6
- ❌ Hardware control
- ❌ Real-time updates
- ❌ Automation
- ❌ Advanced UI polish

---

# V1.7: Control Foundation (2-3 weeks)

## Goal
Manually control hardware safely (no automation yet).

## Deliverables

### Week 1: Control API

**Shelly Control:**
- [ ] Control client (`railway/src/services/hardware_control.py`)
- [ ] Turn on/off commands
- [ ] Action logging (`shelly.actions` table)
- [ ] Command verification (poll after execution)
- [ ] Rollback mechanism (store previous state)

**API Endpoints:**
- [ ] `POST /shelly/device/{name}/on`
- [ ] `POST /shelly/device/{name}/off`
- [ ] `GET /shelly/actions/history`

**Agent Tools:**
- [ ] `control_shelly_plug()` - recommendation only
- [ ] Agents suggest, don't execute

### Week 2: Control UI

**Hardware Control Page (`/hardware`):**
- [ ] Device cards with toggles
- [ ] Confirmation modal ("Turn off Miner 1?")
- [ ] Success/failure notifications
- [ ] Action history timeline
- [ ] Loading states

**Error Handling:**
- [ ] Timeout handling (retry 3x)
- [ ] Offline device detection
- [ ] Clear error messages
- [ ] Retry button

### Week 3: Integration & Testing

**Testing:**
- [ ] Test on/off commands (use test device)
- [ ] Verify action logging
- [ ] Test rollback on failure
- [ ] Test offline device handling

**Documentation:**
- [ ] Control API guide
- [ ] User manual for hardware page
- [ ] Safety checklist

## Success Criteria
- ✅ Can control any Shelly device from dashboard
- ✅ All actions logged (who/when/result)
- ✅ Success rate >98%
- ✅ Failed commands rollback automatically
- ✅ Clear UI feedback

## NOT in V1.7
- ❌ Agent auto-execution
- ❌ Automation rules
- ❌ Email/SMS approvals
- ❌ Safety boundaries

---

# V1.8: Safety & Preferences (2-3 weeks)

## Goal
User-defined rules and safety guardrails.

## Deliverables

### Week 1: Preferences System

**Database Schema:**
- [ ] `user_preferences` table
- [ ] `automation_rules` table (structure only)

**Preference Categories:**

**Energy Rules:**
- Min SOC threshold (30%)
- Target SOC (80%)
- Pause miners below (50%)
- Resume miners above (80%)
- Max grid draw watts
- Solar priority hours

**Automation Settings:**
- Auto-pause miners (yes/no)
- Require confirmation (always/sometimes/never)

**Notification Settings:**
- Email address
- Critical alerts only vs all
- Quiet hours

**Settings Page (`/settings`):**
- [ ] Form-based preference editor
- [ ] Save/load preferences
- [ ] Validation
- [ ] Reset to defaults

### Week 2: Safety System

**Safety Validator:**
- [ ] SOC not below critical (20%)
- [ ] Grid within limits
- [ ] No conflicting actions
- [ ] Device state checks
- [ ] Time window validation

**Pending Actions System:**
- [ ] `pending_actions` table
- [ ] Create pending action
- [ ] Email approval flow
- [ ] SMS approval flow (Twilio webhook)
- [ ] Expiration logic (5-minute timeout)

**Notification Templates:**
- [ ] Email: approval request
- [ ] SMS: "Reply YES to approve"
- [ ] Email: action result

### Week 3: Integration

**Control Flow Updates:**
- [ ] Wire safety checks to all control endpoints
- [ ] Agent tools check preferences
- [ ] UI shows pending approvals
- [ ] Re-validation before execution

**Testing:**
- [ ] Test all safety checks
- [ ] Test email approval end-to-end
- [ ] Test SMS approval parsing
- [ ] Test expiration handling

## Success Criteria
- ✅ Unsafe actions blocked
- ✅ Email approval works
- ✅ SMS approval works
- ✅ Preferences enforced
- ✅ No dangerous actions possible

## NOT in V1.8
- ❌ Automation rules (V2.0)
- ❌ Learning mode
- ❌ Advanced UI
- ❌ Real-time updates

---

# V1.9: Full Observability (2-3 weeks)

## Goal
See what's happening in real-time.

## Deliverables

### Week 1: Enhanced Chat

**Chat Interface (`/chat`):**
- [ ] Agent selector dropdown
- [ ] Live progress ("Calling Shelly API...")
- [ ] Response metadata (agent, duration, tools)
- [ ] Source citations (KB docs linked)
- [ ] Pending action display
- [ ] Error handling with suggestions
- [ ] Conversation history sidebar
- [ ] Export conversation

### Week 2: Agent Activity Monitor

**Activity Monitor Page (`/agents`):**
- [ ] Live status grid (all agents/services)
- [ ] Activity feed (last 100 actions, real-time)
- [ ] Tool usage stats (bar charts)
- [ ] Performance metrics (response times)
- [ ] Filters (by agent, date, status, tool)

**Monitoring API:**
- [ ] `GET /agents/activity` - recent events
- [ ] `GET /agents/stats` - aggregated metrics

### Week 3: System Health Dashboard

**Health Dashboard (`/health`):**
- [ ] Component status (API, DB, agents, APIs)
- [ ] Recent errors log (24h)
- [ ] Performance charts (response times, query volume)
- [ ] Resource usage (DB size, connections)
- [ ] Alert configuration UI

**Real-Time Updates:**
- [ ] Fast polling (5 seconds) OR WebSocket
- [ ] Start with polling, upgrade to WS if needed

## Success Criteria
- ✅ Can see what agents doing live
- ✅ System health visible at a glance
- ✅ Error alerts work
- ✅ Performance metrics accurate
- ✅ Professional, polished UI

## NOT in V1.9
- ❌ Automation
- ❌ Advanced analytics
- ❌ Mobile app

---

# V2.0: Automation Engine (2-3 weeks)

## Goal
Intelligent, autonomous operation.

## Deliverables

### Week 1: Rules Engine

**Rules System:**
- [ ] Rules database schema
- [ ] Rule builder UI (if/then logic)
- [ ] Trigger types (SOC, time, power, weather)
- [ ] Action types (pause/resume, set mode, notify)
- [ ] Rule validation (prevent conflicts)
- [ ] Rule management (enable/disable/edit)

**Background Engine:**
- [ ] Evaluate rules every 5 minutes
- [ ] Execute matching rules
- [ ] Respect cooldowns
- [ ] Safety checks before execution
- [ ] Log all decisions

**Automation Page (`/automation`):**
- [ ] Active rules list
- [ ] Recent automation activity
- [ ] Add/edit rule UI
- [ ] Rule triggers this week

### Week 2: Smart Automation

**Learning Mode:**
- [ ] Watch user approvals
- [ ] Detect patterns
- [ ] Suggest new rules
- [ ] Confidence scoring
- [ ] "You always approve this - automate?"

**Test Mode:**
- [ ] Simulate rules without executing
- [ ] Show what would happen
- [ ] Safe testing before enabling

**Rule Priority:**
- [ ] Manual > automation > agent
- [ ] Conflict resolution
- [ ] Lock mechanism (serialize actions)

### Week 3: Emergency & Polish

**Emergency Controls:**
- [ ] Big red STOP button (top nav)
- [ ] Disables all automation
- [ ] Requires manual re-enable
- [ ] Logs who stopped and why

**Advanced Features:**
- [ ] One-time scheduled actions
- [ ] Recurring schedules
- [ ] Multi-step workflows
- [ ] Conditional next steps

**Final Testing:**
- [ ] Run 1 week in test mode
- [ ] Validate rule execution
- [ ] Test emergency stop
- [ ] Performance testing

## Success Criteria
- ✅ Rules execute automatically
- ✅ No unsafe actions possible
- ✅ Learning mode suggests useful rules
- ✅ Emergency stop works instantly
- ✅ System operates autonomously
- ✅ 1 week stable operation

---

## 🚨 Critical Gaps & Mitigation

### V1.6 Gaps

**Gap: API Rate Limits**
- **Risk:** Victron VRM 50/hour, we need 20/hour (safe)
- **Mitigation:** Cache aggressively, 3-min polling adequate

**Gap: Initial Device Setup**
- **Risk:** How to onboard new Shelly devices
- **Solution:** Setup wizard in V1.6 Week 2
- **Features:** Discover devices, bulk import, device naming

**Gap: Polling Health Monitoring**
- **Risk:** Polling fails silently
- **Solution:** Health check endpoint, alert if >10 min down
- **Metrics:** Poll success rate, last successful poll time

### V1.7 Gaps

**Gap: Command Reliability**
- **Risk:** Command sent but timeout, did it work?
- **Solution:** Verification step (poll state after command)
- **Features:** Max 3 retries, rollback if verification fails

**Gap: Offline Device Handling**
- **Risk:** Device offline when trying to control
- **Solution:** Pre-check device online, clear error message
- **Features:** Retry queue, manual retry button

### V1.8 Gaps

**Gap: Action Conflict Resolution**
- **Risk:** Multiple actions on same device
- **Solution:** Lock mechanism, serialize actions
- **Features:** Priority system, conflict detection

**Gap: Approval Flow Edge Cases**
- **Risk:** Link clicked twice, expired action
- **Solution:** Idempotent approval, clear expiration handling
- **Features:** Duplicate click prevention, timeout warnings

### V1.9 Gaps

**Gap: Frontend State Management**
- **Risk:** Multiple tabs out of sync
- **Solution:** Polling every 5s, cache invalidation
- **Consider:** WebSocket if polling too slow

**Gap: Performance Under Load**
- **Risk:** Dashboard slow with many charts
- **Solution:** Query optimization, lazy loading
- **Features:** Caching, connection pooling

### V2.0 Gaps

**Gap: Rule Validation**
- **Risk:** User creates dangerous/conflicting rules
- **Solution:** Validate before saving, simulate first
- **Features:** Conflict detection, safety bounds

**Gap: Automation Testing**
- **Risk:** Can't test on production hardware
- **Solution:** Test mode (simulate don't execute)
- **Features:** Mock devices, dry-run mode

---

## 🔄 Cross-Version Concerns

### Database Migrations
**Strategy:** Incremental migrations, never breaking

```
migrations/
├── 001_initial_schema.sql (V1.5 ✅)
├── 002_knowledge_base.sql (V1.5 ✅)
├── 003_victron_schema.sql (V1.6)
├── 004_shelly_schema.sql (V1.6)
├── 005_control_actions.sql (V1.7)
├── 006_preferences.sql (V1.8)
├── 007_pending_actions.sql (V1.8)
├── 008_monitoring.sql (V1.9)
├── 009_automation_rules.sql (V2.0)
└── 010_learning_mode.sql (V2.0)
```

**Migration Runner:**
- Track version in `schema_migrations` table
- Apply only new migrations
- Idempotent (safe to re-run)

### API Versioning
**Strategy:** Backwards compatible

- V1 endpoints never break
- V2 endpoints can evolve
- Deprecate, don't delete
- 6-month deprecation notice

### Feature Flags
**Strategy:** Deploy code, enable gradually

```python
FEATURES = {
    'VICTRON_POLLING': os.getenv('FEATURE_VICTRON', 'true'),
    'HARDWARE_CONTROL': os.getenv('FEATURE_CONTROL', 'false'),
    'AUTOMATION': os.getenv('FEATURE_AUTOMATION', 'false')
}
```

**Benefits:**
- Deploy without enabling
- Test in production safely
- Rollback = flip flag
- Gradual rollout

### Caching Strategy

**V1.6:** In-memory cache (simple dict)
**V1.9:** Redis if performance issues
**V2.0:** Redis required (automation queries frequently)

**Cache TTLs:**
- Latest readings: 3 minutes
- Hourly aggregates: 1 hour
- Device list: 5 minutes

### Monitoring Progression

**Each version adds metrics:**

- V1.6: Poll success rate, data gaps
- V1.7: Control success rate, command latency
- V1.8: Safety blocks, approval response time
- V1.9: Agent response time, error rate
- V2.0: Rule execution rate, automation uptime

**Metrics Table:**
```sql
CREATE TABLE system_metrics (
    timestamp TIMESTAMPTZ,
    metric_name TEXT,
    metric_value REAL,
    metadata JSONB
);
```

---

## 📅 Deployment Strategy

### Each Version Follows This Pattern:

**1. Develop (1 week)**
- Build features locally
- Unit tests
- Integration tests with mocks

**2. Stage (2-3 days)**
- Deploy to staging
- Test with real APIs
- Manual testing checklist
- Performance check

**3. Deploy (Weekend)**
- Deploy Friday evening or Saturday
- You're on-site
- Can fix issues immediately
- Monitor for 24 hours

**4. Validate (1 week)**
- Monitor metrics
- Fix bugs discovered
- User feedback
- Stabilize before next version

**5. Document**
- Update V1.5_MASTER_REFERENCE.md
- User guides
- API documentation
- Known issues

### Rollback Plan

**If deployment breaks:**
1. Feature flag OFF (instant)
2. Git revert + redeploy (5 min)
3. Database rollback if needed (rare)

**Always deploy weekends when on-site for fast recovery.**

---

## 📊 Timeline Summary

| Version | Duration | Deliverable |
|---------|----------|-------------|
| V1.6 Data Foundation | 2 weeks | Time-series from all sources |
| V1.7 Control Foundation | 2-3 weeks | Manual hardware control |
| V1.8 Safety & Preferences | 2-3 weeks | Guardrails + user rules |
| V1.9 Full Observability | 2-3 weeks | Real-time monitoring |
| V2.0 Automation Engine | 2-3 weeks | Autonomous operation |
| **Total** | **11-15 weeks** | **Complete V2** |

**Part-time (15 hrs/week):** 5-7 months  
**Full-time (40 hrs/week):** 3-4 months

---

## ✅ Decision Framework

### For Each Feature, Ask:

1. **Does this depend on previous version?** (can't skip)
2. **Does this block next version?** (must complete)
3. **Can this be deferred?** (nice-to-have)
4. **Does this scale?** (won't break at 10x)
5. **Is this testable?** (can verify works)

**If No to any:** Redesign or defer

---

## 🎯 Success Criteria

### V1.6 Complete When:
- Cerbo, SolArk, Shelly all flowing
- 72-hour retention enforced
- Agents analyze power usage
- Database size stable

### V1.7 Complete When:
- Control all Shelly devices via dashboard
- Actions logged with audit trail
- >98% command success rate
- Rollback works on failure

### V1.8 Complete When:
- User preferences stored and enforced
- Safety validator blocks unsafe actions
- Email/SMS approval working
- No dangerous actions possible

### V1.9 Complete When:
- Real-time visibility into all operations
- Performance metrics accurate
- Error tracking functional
- Professional UI polish

### V2.0 Complete When:
- Rules execute autonomously
- Learning mode suggests improvements
- Emergency stop tested
- 1 week stable autonomous operation

---

## 🚀 V2+ Deferred Features

**Not in V2, consider for V3:**

- Mobile PWA (progressive web app)
- Advanced ML forecasting
- Multi-site support
- Extended integrations (weather, cameras)
- Local MQTT fallback
- Advanced analytics dashboards
- Cost optimization algorithms
- Battery health prediction

---

## 📚 Reference Documents

**Current State:**
- `docs/V1.5_MASTER_REFERENCE.md` - Current system
- `docs/05-architecture.md` - Detailed architecture
- `docs/ORCHESTRATION_LAYER_DESIGN.md` - Agent design

**Planning:**
- This document (`docs/V2_ROADMAP.md`)

**Code:**
- `railway/src/` - Backend code
- `vercel/src/` - Frontend code

**Sessions:**
- `docs/sessions/` - Development history

---

## 💡 Core Principles

### DO:
✅ Build incrementally (each version ships)
✅ Test thoroughly (every version validated)
✅ Deploy weekends (on-site for issues)
✅ Document decisions (future self will thank you)
✅ Follow data lifecycle (prevent bloat)
✅ Prioritize safety (never risk hardware)

### DON'T:
❌ Skip versions (dependencies matter)
❌ Deploy untested (integration tests required)
❌ Break V1.5 (backwards compatible)
❌ Over-engineer (MVP per version)
❌ Ignore gaps (address in planning)
❌ Rush automation (safety first)

---

**End of V2 Roadmap**

**Next Step:** Begin V1.6 Development

**Status:** Ready to Build

**Timeline:** 19 weeks to full autonomous operation

---

*Built on V1.5 foundation. Each version independently valuable. Modular, testable, production-ready.*