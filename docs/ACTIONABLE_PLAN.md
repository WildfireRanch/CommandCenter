# V1.6 Context Fixes - Actionable Deployment Plan

**Status:** 🟡 Code Ready - Production Testing Required
**Risk Level:** LOW
**Estimated Time to Production:** 90 minutes

---

## Test Results Summary

### What We Validated ✅

| Test | Result | Confidence |
|------|--------|------------|
| Code Structure | ✅ PASS | 100% |
| Routing Logic | ✅ PASS | 100% |
| Context Loading (Mock) | ✅ PASS | 95% |
| Crew Context Passing | ✅ PASS | 100% |

### What We Couldn't Test ⏸️

| Test | Blocker | Risk |
|------|---------|------|
| Real Context from DB | No database access | MEDIUM |
| Multi-turn Conversations | No session persistence | MEDIUM |
| Performance Metrics | No production data | LOW |
| End-to-End Flows | No API+DB integration | MEDIUM |

---

## Critical Gaps Identified

### 🔴 Gap 1: No Context Files in Production Database
**Impact:** If KB has no context files, agents won't have system knowledge
**Fix Time:** 10 minutes
**See:** Action 1.1 below

### 🔴 Gap 2: No End-to-End Validation
**Impact:** Unknown if full flow works with real data
**Fix Time:** 10 minutes testing
**See:** Phase 2 below

### 🟡 Gap 3: No Performance Baseline
**Impact:** Can't detect performance regressions
**Fix Time:** 15 minutes
**See:** Action 3.1 below

---

## Actionable Plan - Three Phases

### 📋 Phase 1: Pre-Production (20 minutes) - REQUIRED

#### ☐ Action 1.1: Check Context Files Exist (10 min)

```bash
# Connect to production database
psql $DATABASE_URL

# Check for context files
SELECT id, title, is_context_file, LENGTH(full_content) as size
FROM kb_documents
WHERE is_context_file = TRUE;
```

**If No Results Found:**
```bash
# Re-sync from Google Drive
cd railway
python -m src.kb.sync

# OR manually mark docs
UPDATE kb_documents
SET is_context_file = TRUE
WHERE title IN (
  'System Hardware Specifications',
  'Energy Management Policies',
  'Operating Procedures'
);
```

**Success:** At least 1 doc with `is_context_file=TRUE`, total size 1,500-5,000 chars

---

#### ☐ Action 1.2: Deploy to Production (5 min)

```bash
git push origin main
# Railway auto-deploys

# Monitor deployment
railway status
railway logs
```

**Success:** API starts without errors, health check returns 200

---

#### ☐ Action 1.3: Run Verification Script (5 min)

```bash
railway run bash
cd railway
python scripts/verify_context_setup.py
```

**Expected Output:**
```
✅ Database Connection
✅ Context Files Exist
✅ get_context_files() Returns Data
✅ Agent Loads Context
✅ Routing Returns Decisions
✅ Crew Functions Accept Context
```

**If ANY check fails:** STOP - Fix before proceeding

---

### 🧪 Phase 2: Production Validation (10 minutes) - CRITICAL

#### ☐ Test 2.1: System Knowledge (2 min)

```bash
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What inverter model are you managing?"}'
```

**✅ Pass:** Mentions specific hardware (e.g., "SolArk 15K"), <5s response
**❌ Fail:** Generic answer or "let me search..."

---

#### ☐ Test 2.2: Policy Knowledge (2 min)

```bash
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold?"}'
```

**✅ Pass:** Immediate answer (e.g., "30%"), no KB search
**❌ Fail:** Searches KB or gives generic answer

---

#### ☐ Test 2.3: Multi-Turn Context (3 min)

```bash
# Turn 1
SESSION=$(curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}' | jq -r '.session_id')

# Turn 2
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Is that good?\", \"session_id\": \"$SESSION\"}"
```

**✅ Pass:** Turn 2 references specific battery level from Turn 1
**❌ Fail:** "What are you referring to?"

---

#### ☐ Test 2.4: Cross-Agent Context (3 min)

```bash
# Turn 1 - Solar Controller
SESSION=$(curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "How much solar am I generating?"}' | jq -r '.session_id')

# Turn 2 - Energy Orchestrator
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Should I charge the battery?\", \"session_id\": \"$SESSION\"}"
```

**✅ Pass:** Turn 2 uses solar data from Turn 1
**❌ Fail:** Context lost between agents - CRITICAL ISSUE

---

### 📊 Phase 3: Monitoring Setup (55 minutes) - DO SAME DAY

#### ☐ Action 3.1: Performance Baseline (15 min)

```sql
-- Token usage
SELECT
  agent_name,
  AVG(token_count) as avg_tokens,
  MAX(token_count) as max_tokens
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;

-- Latency
SELECT
  agent_name,
  AVG(duration_seconds) as avg_seconds,
  percentile_cont(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;
```

**Target Metrics:**
- Token usage: 5,000-8,000/query
- P95 latency: <5 seconds
- Error rate: <5%

---

#### ☐ Action 3.2: Error Rate Monitoring (10 min)

```sql
SELECT
  agent_name,
  COUNT(*) as total,
  COUNT(*) FILTER (WHERE error IS NOT NULL) as errors,
  ROUND(100.0 * COUNT(*) FILTER (WHERE error IS NOT NULL) / COUNT(*), 2) as error_pct
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;
```

**Alert if:** Error rate >5%

---

#### ☐ Action 3.3: Setup Alerts (30 min)

| Metric | Warning | Critical |
|--------|---------|----------|
| Tokens | >9k | >10k |
| Latency | >6s | >8s |
| Errors | >5% | >10% |

Configure via Railway dashboard or PostgreSQL monitoring

---

## Quick Reference - What Changed

### Files Modified
- [railway/src/agents/solar_controller.py](railway/src/agents/solar_controller.py:219) - Loads context
- [railway/src/agents/energy_orchestrator.py](railway/src/agents/energy_orchestrator.py:130) - Loads context
- [railway/src/agents/manager.py](railway/src/agents/manager.py:60) - Returns decisions
- [railway/src/api/main.py](railway/src/api/main.py:888) - Two-step routing

### What to Check if Issues Occur

**Problem:** Agent doesn't know system details
- Check: Context files exist (`SELECT * FROM kb_documents WHERE is_context_file=TRUE`)
- Check: `get_context_files()` returns data (logs)
- Check: Agent backstory includes "SYSTEM CONTEXT"

**Problem:** Context lost in multi-turn
- Check: API passes `conversation_context` to crews (logs line ~920)
- Check: Routing returns JSON decision (logs line ~900)
- Check: Session history loads from DB

**Problem:** High token usage (>10k)
- Check: Context file sizes in DB
- Consider: Reduce context or split into smaller files
- Target: Total context <6,000 tokens

---

## Rollback Procedure

### If Critical Issues in Production

```bash
# Quick rollback - revert all changes
git revert HEAD
git push origin main

# Railway auto-deploys (2-3 min)
```

### Partial Rollback Options

```bash
# Revert only Fix #1 (context loading)
git checkout HEAD~1 railway/src/agents/solar_controller.py
git checkout HEAD~1 railway/src/agents/energy_orchestrator.py
git commit -m "Rollback: Remove context loading"
git push origin main

# Revert only Fix #2 (routing)
git checkout HEAD~1 railway/src/agents/manager.py
git checkout HEAD~1 railway/src/api/main.py
git commit -m "Rollback: Restore direct routing"
git push origin main
```

**Rollback Time:** <5 minutes

---

## Success Criteria

### Deployment is successful if:

✅ All 4 Phase 2 tests pass
✅ Token usage: 5,000-8,000/query
✅ Latency: <5 seconds
✅ Error rate: <5%

### Proceed to full production if:

✅ Phase 1 complete (verification script passes)
✅ Phase 2 complete (all 4 tests pass)
✅ Phase 3 started (monitoring in place)

---

## Timeline

| Phase | Duration | When |
|-------|----------|------|
| Phase 1 - Pre-Production | 20 min | Before deploy |
| Phase 2 - Validation | 10 min | Immediately after deploy |
| Phase 3 - Monitoring | 55 min | Same day |
| **Total** | **85 min** | **Day 1** |

---

## Resources

- **Full Gap Analysis:** [docs/TEST_RESULTS_AND_GAPS.md](TEST_RESULTS_AND_GAPS.md)
- **Deployment Guide:** [docs/QUICK_REFERENCE_DEPLOYMENT.md](QUICK_REFERENCE_DEPLOYMENT.md)
- **Implementation Details:** [docs/CONTEXT_FIXES_IMPLEMENTATION.md](CONTEXT_FIXES_IMPLEMENTATION.md)
- **Deep Dive Analysis:** [docs/DEEP_DIVE_CONTEXT_CREWAI_ANALYSIS.md](DEEP_DIVE_CONTEXT_CREWAI_ANALYSIS.md)

---

## Checklist - Print and Execute

```
PRE-PRODUCTION (20 min)
□ 1.1 Verify context files exist in DB
□ 1.2 Deploy code to production
□ 1.3 Run verification script (all checks pass)

PRODUCTION VALIDATION (10 min)
□ 2.1 Test: System knowledge
□ 2.2 Test: Policy knowledge
□ 2.3 Test: Multi-turn context (same agent)
□ 2.4 Test: Multi-turn context (cross-agent)

MONITORING (55 min)
□ 3.1 Establish performance baseline
□ 3.2 Check error rates
□ 3.3 Setup performance alerts

POST-DEPLOYMENT
□ Document actual metrics vs. targets
□ Create incident response plan
□ Schedule 7-day review
```

---

**READY TO DEPLOY** 🚀

Next Step: Execute Phase 1, Action 1.1 (Verify context files)

---

**END OF ACTIONABLE PLAN**
