# OpenAI Rate Limit Handling Guide

**Issue Observed:** October 9, 2025 - Production testing revealed rate limiting during rapid queries

---

## 🔍 Problem Summary

**Symptom:** Queries hang or take very long (60s+)
**Logs Show:** `HTTP/1.1 429 Too Many Requests`
**Root Cause:** OpenAI API rate limits exceeded

### Why It Happens

Each user query triggers **4-7 OpenAI API calls**:
1. Manager agent analyzes query → 1 call
2. Manager routes to specialist → 1 call
3. Specialist agent processes → 1-3 calls
4. Tool result processing → 1-2 calls

**During testing:** Rapid queries (5-10 in a row) → Rate limit hit

---

## ✅ Current Handling (Working)

System already handles rate limits correctly:
- ✅ OpenAI SDK auto-retries with exponential backoff
- ✅ Requests eventually succeed
- ✅ No crashes or data loss
- ✅ User sees slower response but gets answer

**Evidence from logs:**
```
429 Too Many Requests
Retrying request in 0.677 seconds
HTTP/1.1 200 OK  ← Success after retry
```

---

## 📊 OpenAI Rate Limits by Tier

### Free Tier
- **Requests:** 3 RPM (requests per minute)
- **Tokens:** 40,000 TPM (tokens per minute)
- **Impact:** Can handle ~0.5 user queries per minute

### Tier 1 ($5+ spent)
- **Requests:** 500 RPM
- **Tokens:** 200,000 TPM
- **Impact:** Can handle ~100 user queries per minute

### Tier 2 ($50+ spent)
- **Requests:** 5,000 RPM
- **Tokens:** 2,000,000 TPM
- **Impact:** Can handle ~1,000 user queries per minute

**Check your tier:** https://platform.openai.com/account/limits

---

## 🚀 Optimization Options

### Option 1: Upgrade OpenAI Tier (Recommended)
**Cost:** $5-50 initial spend to reach Tier 1-2
**Benefit:** 100-1000x more capacity
**Best for:** Production use with multiple users

### Option 2: Implement Request Queuing
**Cost:** Development time
**Benefit:** Prevents rate limit hits
**Implementation:**
```python
# In main.py
from asyncio import Semaphore

# Limit concurrent agent requests
agent_semaphore = Semaphore(3)  # Max 3 concurrent

@app.post("/ask")
async def ask_agent(request: AskRequest):
    async with agent_semaphore:
        # Existing code...
```

### Option 3: Add Response Caching
**Cost:** Development time + storage
**Benefit:** Identical queries use cached responses
**Implementation:**
```python
# Cache common queries for 5 minutes
from functools import lru_cache
import hashlib

def cache_key(query: str) -> str:
    return hashlib.md5(query.lower().strip().encode()).hexdigest()

# Add to Redis or memory cache
```

### Option 4: Use Cheaper Model for Routing
**Cost:** Code changes
**Benefit:** Manager uses gpt-3.5-turbo (10x cheaper)
**Implementation:**
```python
# In manager.py agent definition
agent = Agent(
    role="Query Router",
    llm="gpt-3.5-turbo",  # Cheaper for simple routing
    # ... rest of config
)
```

### Option 5: Batch Processing
**Cost:** UX trade-off
**Benefit:** Queue requests, process in batches
**Best for:** Non-interactive workloads

---

## 🎯 Recommended Approach

### For Production Use:

**Short Term (Today):**
1. ✅ Current retry mechanism works - no code changes needed
2. ⚠️ Warn users that rapid queries may be slow
3. 📊 Monitor rate limit hits in logs

**Medium Term (This Week):**
1. 💰 Upgrade to OpenAI Tier 1 ($5 spend)
   - Dramatically increases capacity
   - Supports multiple concurrent users
   - Cost: ~$0.01-0.05 per query

**Long Term (V2.0):**
1. 🔄 Implement caching for common queries
2. 🎛️ Add request queuing with user feedback
3. 📊 Add rate limit monitoring dashboard
4. 🔀 Use cheaper models for simple tasks

---

## 💡 User Communication

### What to Tell Users

**Good Response:**
> "The system may be slower during high-demand periods as it processes multiple AI model calls per query. Typical response time is 10-30 seconds, but may take up to 60 seconds when busy."

**Even Better:**
> "Each query is analyzed by multiple AI specialists to provide the best answer. This may take 10-30 seconds. If you experience delays, please wait - your request is being processed."

---

## 📈 Monitoring Rate Limits

### Check Your Usage
```bash
# Check OpenAI usage
curl https://api.openai.com/v1/usage \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Add Logging
```python
# In main.py, after agent execution
logger.info(
    "query_completed",
    extra={
        "duration_ms": duration_ms,
        "agent_used": agent_used,
        "rate_limited": "429" in logs  # Track if we hit limits
    }
)
```

### Railway Alerts
Set up alerts for:
- Response time > 45 seconds
- Error rate > 10%
- Log messages containing "429"

---

## 🐛 Troubleshooting

### Query Takes 60+ Seconds
**Cause:** Rate limit hit, multiple retries
**Solution:** Wait it out or upgrade tier

### Query Times Out
**Cause:** Too many retries exceeded timeout
**Solution:** Increase timeout in api_client.py

### All Queries Slow
**Cause:** Exceeded daily quota
**Solution:** Wait 24hrs or upgrade tier

### Intermittent Slowness
**Cause:** Hitting rate limit periodically
**Solution:** Add queuing or upgrade tier

---

## 📊 Cost Analysis

### Current Cost (Per Query)
- Manager routing: ~500 tokens = $0.0003
- Specialist response: ~1500 tokens = $0.0009
- **Total:** ~$0.0012 per query

### Monthly Estimates
| Users | Queries/Day | Cost/Month |
|-------|-------------|------------|
| 1 (you) | 20 | $0.72 |
| 5 | 100 | $3.60 |
| 10 | 200 | $7.20 |
| 50 | 1000 | $36.00 |

**Tier 1 ($5 unlock) supports up to ~4,000 queries/day**

---

## ✅ Action Items

**Immediate:**
- [x] Document issue (this file)
- [x] Confirm current retry mechanism works
- [ ] Check your OpenAI tier and limits

**This Week:**
- [ ] Consider upgrading to Tier 1 if daily use expected
- [ ] Add user messaging about expected response times
- [ ] Monitor logs for rate limit frequency

**Future (V2.0):**
- [ ] Implement response caching
- [ ] Add request queuing
- [ ] Use gpt-3.5-turbo for routing
- [ ] Add rate limit dashboard

---

## 🎉 Bottom Line

**Current Status:** ✅ System handles rate limits correctly

**User Impact:** Queries may take 30-60s instead of 10-20s when rate limited

**Fix Required:** ❌ No immediate fix needed - system works

**Optimization:** ✅ Upgrade OpenAI tier for better performance ($5-50)

**Priority:** 🟡 Medium - System functional, optimization improves UX

---

**The system is working as designed!** Rate limits are an expected part of using OpenAI's API, and your system handles them gracefully. For production use with regular traffic, upgrading your OpenAI tier is the best solution.
