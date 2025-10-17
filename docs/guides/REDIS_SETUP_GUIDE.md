# Redis Setup Guide for Railway
**Date:** 2025-10-12
**Purpose:** Quick reference for adding Redis to CommandCenter deployment
**Time Required:** 5 minutes

---

## 🎯 What Redis Does in CommandCenter

Redis powers V1.8 Smart Context Loading by caching context bundles:

- **Without Redis:** System works, but loads context fresh every time (slower, more tokens)
- **With Redis:** Context cached for 5 minutes (faster, 40-60% token savings)

**Bottom Line:** Redis is optional but highly recommended for cost savings.

---

## 🚀 Quick Setup (Railway Dashboard)

### Step 1: Add Redis Service (2 minutes)

1. Go to **Railway Dashboard**: https://railway.app/dashboard
2. Select your **CommandCenter** project
3. Click **"+ New"** button
4. Select **"Database"**
5. Choose **"Add Redis"**
6. Railway automatically provisions Redis (takes ~2 min)

**That's it!** Railway automatically:
- Creates Redis instance
- Sets `REDIS_URL` environment variable
- Links Redis to your backend service
- Restarts backend with Redis connected

### Step 2: Verify Connection (1 minute)

1. In Railway dashboard, go to **Backend Service → View Logs**
2. Look for:
   ```
   ✅ Redis connected: redis://default:xxxxx@...
   ```
3. If you see this, Redis is working! ✅

### Step 3: Test Cache (2 minutes)

Send the same query twice to test caching:

```bash
# First request (cache miss)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?", "user_id": "test123"}'

# Wait 2 seconds, then repeat (cache hit)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?", "user_id": "test123"}'
```

**Expected:**
- 1st request: `"cache_hit": false`, `"context_tokens": ~2400`
- 2nd request: `"cache_hit": true`, `"context_tokens": ~2400` (same tokens, but faster!)

---

## 🔧 Environment Variables

Railway automatically sets `REDIS_URL`. Optional overrides:

### Default Values (Already in Code)

```bash
REDIS_MAX_RETRIES=3          # Retry failed connections
REDIS_TIMEOUT=5              # Connection timeout (seconds)
REDIS_SSL=false              # Use SSL (auto-detected from URL)
```

### Cache Configuration (Optional)

```bash
CONTEXT_CACHE_ENABLED=true   # Enable/disable caching
CONTEXT_CACHE_TTL=300        # Cache lifetime (5 minutes)
```

**Note:** You don't need to set these unless you want different values. Defaults are optimized.

---

## 📊 What to Monitor

### In Railway Logs (Backend Service)

**Good Signs:**
```
✅ Redis connected: redis://...
✅ Smart context loaded: 2400 tokens, type=system, cache_hit=False
✅ Cache hit for query type system
```

**Warning Signs:**
```
⚠️ Redis connection failed: ... Caching disabled.
```
**Action:** Check Redis service status, verify it's linked to backend

### In API Responses

Every response includes metadata:
```json
{
  "response": "Your battery is at 67%...",
  "context_tokens": 2400,        // Should be 2k-4k (down from 5k-8k)
  "cache_hit": true,             // True after first query
  "query_type": "system"         // Classification working
}
```

---

## 🐛 Troubleshooting

### Problem: "Redis connection failed"

**Check:**
1. Redis service is running in Railway dashboard
2. `REDIS_URL` environment variable is set
3. Redis and backend are in same project

**Fix:**
- Restart Redis service
- Restart backend service
- Verify services are linked

### Problem: "cache_hit" always false

**Check:**
1. Using same `user_id` for repeat queries
2. Queries are within 5-minute TTL window
3. `CONTEXT_CACHE_ENABLED=true` (default)

**Fix:**
- Use consistent `user_id` in requests
- Queries must be similar (classification-based caching)

### Problem: Token usage not reduced

**Check:**
1. Query classification working (check logs)
2. Token budgets configured correctly
3. KB search filtering properly

**Fix:**
- Review V1.8_IMPLEMENTATION_COMPLETE.md troubleshooting
- Check context_config.py values
- Verify query_type in responses

---

## 📈 Expected Results

### Immediate (After Adding Redis)

- ✅ Backend logs show "Redis connected"
- ✅ No errors in Railway logs
- ✅ API responses include cache metadata

### Within 1 Hour

- ✅ Cache hit rate starts increasing
- ✅ Token usage drops to 2k-4k range
- ✅ Response times improve for cached queries

### Within 1 Week

| Metric | Target | Where to Check |
|--------|--------|----------------|
| Cache hit rate | >60% | Railway logs: count "cache_hit=true" |
| Avg tokens/query | 2.6k-4k | API responses: "context_tokens" |
| Token reduction | 40-60% | Compare to old logs (~6k tokens) |
| Cost savings | 40-60% | OpenAI API dashboard |

---

## 💡 Pro Tips

1. **Monitor Early:** Watch Railway logs for first 24 hours after adding Redis
2. **Test Different Query Types:** Try system, research, planning, and general queries
3. **Use Consistent user_id:** Better cache hit rates with same user
4. **Cache Warming:** First queries are always cache misses (expected)
5. **TTL Sweet Spot:** 5 minutes balances freshness vs hit rate

---

## 🎯 Success Criteria

**Redis is working correctly if:**
- ✅ Backend logs show "Redis connected"
- ✅ Second identical query has `cache_hit: true`
- ✅ Token usage is 40-60% lower than before
- ✅ No "Redis connection failed" warnings

**System is healthy without Redis if:**
- ✅ Queries work normally
- ✅ Logs show "Caching disabled" (expected)
- ✅ Token usage still 40-60% lower (V1.8 smart loading)
- ✅ Just no cache speed boost

---

## 📞 Reference Links

**Railway Resources:**
- Dashboard: https://railway.app/dashboard
- Redis Docs: https://docs.railway.app/databases/redis
- Environment Variables: Project → Service → Variables

**CommandCenter Docs:**
- Full Guide: [V1.8_IMPLEMENTATION_COMPLETE.md](V1.8_IMPLEMENTATION_COMPLETE.md)
- Deployment: [V1.8_DEPLOYMENT_READY.md](V1.8_DEPLOYMENT_READY.md)
- Validation: [DEPLOYMENT_VALIDATION_REPORT.md](DEPLOYMENT_VALIDATION_REPORT.md)

**Code Files:**
- Redis Client: `railway/src/services/redis_client.py`
- Context Manager: `railway/src/services/context_manager.py`
- Config: `railway/src/config/context_config.py`

---

## ⏱️ Time Estimate

| Task | Time |
|------|------|
| Add Redis in Railway | 2 min |
| Wait for provisioning | 2 min |
| Verify connection | 1 min |
| Test caching | 2 min |
| **Total** | **7 min** |

---

## ✅ Checklist

- [ ] Open Railway dashboard
- [ ] Select CommandCenter project
- [ ] Click "+ New" → "Database" → "Add Redis"
- [ ] Wait for provisioning (~2 min)
- [ ] Check backend logs for "Redis connected"
- [ ] Test API with duplicate query
- [ ] Verify `cache_hit: true` on second request
- [ ] Monitor token usage (should be 2k-4k)
- [ ] Check cache hit rate after 1 hour (>50%)

---

**🚀 That's it! Add Redis and enjoy 40-60% cost savings! 🚀**
