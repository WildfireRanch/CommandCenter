# Quick Reference: Context Fixes Deployment

**Version:** 1.6-context-fixes
**Date:** 2025-10-11
**Status:** ✅ Code Complete - Ready for Deployment Testing

---

## Pre-Deployment Checklist

### 1. Environment Requirements

- [ ] PostgreSQL database accessible
- [ ] TimescaleDB extension enabled
- [ ] Environment variables configured:
  - `DATABASE_URL` or individual DB connection vars
  - `OPENAI_API_KEY` (for CrewAI)
  - `SOLARK_*` variables (for inverter access)

### 2. Database Verification

```bash
# Connect to production database
psql $DATABASE_URL

# Check for context files
SELECT id, title, is_context_file
FROM kb_documents
WHERE is_context_file = TRUE;

# Expected: At least 1-2 documents marked as context files
# If none found, need to sync from Google Drive CONTEXT folder
```

### 3. Context Files Setup

**If no context files exist in KB:**

```bash
# Option 1: Re-sync from Google Drive
cd railway
python -m src.kb.sync

# Option 2: Manually mark existing docs as context
psql $DATABASE_URL -c "
UPDATE kb_documents
SET is_context_file = TRUE
WHERE title IN (
  'System Hardware Specifications',
  'Energy Management Policies',
  'Operating Procedures'
);
"
```

### 4. Deploy Code

```bash
# Pull latest changes
git pull origin main

# Restart API service (Railway automatically restarts on git push)
# Or manually:
railway up
```

---

## Post-Deployment Testing

### Test 1: System Knowledge (2 min)

**Goal:** Verify agents have system context embedded

```bash
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What system are you managing?"}'
```

**Expected Response:**
- Mentions "SolArk 15K" inverter
- Mentions "48kWh battery bank"
- Mentions specific hardware details
- NO "let me search..." phrases

**If Failed:**
- Check `get_context_files()` returns data
- Check context files exist in KB
- Check agent backstory includes context section

---

### Test 2: Context Continuity (3 min)

**Goal:** Verify multi-turn conversations preserve context

```bash
# First question
SESSION=$(curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}' | jq -r '.session_id')

echo "Session ID: $SESSION"

# Second question referencing first
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Is that good?\", \"session_id\": \"$SESSION\"}"
```

**Expected Response (2nd question):**
- References specific battery level from first response
- Provides context-aware answer
- NO "What are you asking about?"

**If Failed:**
- Check API passes `context` to specialist crews
- Check routing preserves context
- Check session history loaded from DB

---

### Test 3: Policy Knowledge (2 min)

**Goal:** Verify agents answer policy questions without searching

```bash
curl -X POST https://your-api.railway.app/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold?"}'
```

**Expected Response:**
- Immediate answer: "30%" or "40%" (whatever your policy is)
- References policy from system context
- NO tool usage for `search_knowledge_base`

**If Failed:**
- Verify policy is in a document marked `is_context_file=TRUE`
- Check `get_context_files()` includes policy doc
- Check agent backstory formatting

---

## Performance Monitoring

### Key Metrics to Watch

```bash
# Token usage (from agent telemetry)
psql $DATABASE_URL -c "
SELECT
  agent_name,
  AVG(token_count) as avg_tokens,
  MAX(token_count) as max_tokens
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;
"

# Response latency
psql $DATABASE_URL -c "
SELECT
  agent_name,
  AVG(duration_seconds) as avg_seconds,
  MAX(duration_seconds) as max_seconds
FROM agent_executions
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY agent_name;
"
```

**Target Metrics:**
- Token usage: 5,000-8,000 per query
- Latency: <5 seconds p95
- Error rate: <5%

**Alarm Thresholds:**
- Token usage: >10,000 per query
- Latency: >8 seconds
- Error rate: >10%

---

## Common Issues & Fixes

### Issue 1: "No system context found"

**Symptom:** Agents don't mention specific hardware

**Fix:**
```bash
# Check context files exist
psql $DATABASE_URL -c "
SELECT id, title, is_context_file
FROM kb_documents
WHERE is_context_file = TRUE;
"

# If none, mark appropriate docs
psql $DATABASE_URL -c "
UPDATE kb_documents
SET is_context_file = TRUE
WHERE title ILIKE '%specification%'
   OR title ILIKE '%policy%'
   OR title ILIKE '%hardware%';
"
```

### Issue 2: Context lost in routing

**Symptom:** Multi-turn conversations don't reference previous responses

**Check:**
```python
# In railway/src/api/main.py, verify line ~920:
specialist_crew = create_energy_crew(
    query=request.message,
    conversation_context=context  # ← Must be present
)
```

### Issue 3: High token usage

**Symptom:** Token counts >10,000 per query

**Fix:**
```bash
# Check context file sizes
psql $DATABASE_URL -c "
SELECT
  title,
  LENGTH(full_content) as content_length
FROM kb_documents
WHERE is_context_file = TRUE
ORDER BY content_length DESC;
"

# If too large, split or reduce context files
# Target: Total context <8,000 tokens (~6,000 words)
```

### Issue 4: Agents still searching for policies

**Symptom:** `search_knowledge_base` tool called for policy questions

**Fix:**
- Ensure policy doc is marked `is_context_file=TRUE`
- Verify policy text is in `full_content` field
- Check agent backstory instructs to check context first

---

## Rollback Procedure

If issues occur in production:

### Quick Rollback (revert all changes)

```bash
git revert HEAD
git push origin main
# Railway auto-deploys
```

### Partial Rollback (revert only Fix #1)

```bash
git checkout HEAD~1 railway/src/agents/solar_controller.py
git checkout HEAD~1 railway/src/agents/energy_orchestrator.py
git commit -m "Rollback: Remove system context loading from agents"
git push origin main
```

### Partial Rollback (revert only Fix #2)

```bash
git checkout HEAD~1 railway/src/agents/manager.py
git checkout HEAD~1 railway/src/api/main.py
git commit -m "Rollback: Restore direct routing without context passing"
git push origin main
```

---

## Success Criteria

✅ **Deployment is successful if:**

1. **System Knowledge Test:** Agent mentions specific hardware without searching
2. **Context Continuity Test:** Multi-turn conversation references previous response
3. **Policy Knowledge Test:** Agent answers policy questions immediately
4. **Performance:**
   - Token usage: 5,000-8,000/query
   - Latency: <5 seconds p95
   - Error rate: <5%

---

## Files Changed in This Release

- `railway/src/agents/solar_controller.py` (Fix #1)
- `railway/src/agents/energy_orchestrator.py` (Fix #1)
- `railway/src/agents/manager.py` (Fix #2)
- `railway/src/api/main.py` (Fix #2)

---

## Related Documentation

- [Deep Dive Analysis](DEEP_DIVE_CONTEXT_CREWAI_ANALYSIS.md)
- [Implementation Summary](CONTEXT_FIXES_IMPLEMENTATION.md)
- [Test Results](CONTEXT_FIXES_TEST_RESULTS.md)
- [Quick Reference - System Overview](QUICK_REFERENCE_CommandCenter.md)

---

## Support

If issues persist after following this guide:

1. Check logs: `railway logs`
2. Review agent telemetry in database
3. Test individual components:
   - `get_context_files()` function
   - Manager routing decisions
   - Specialist crew creation with context

---

**END OF DEPLOYMENT REFERENCE**
