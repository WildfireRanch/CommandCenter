# Redis Setup via Railway CLI
**Date:** 2025-10-12
**Current Status:** ❌ Redis not found in project
**Solution:** Add Redis via CLI or Dashboard

---

## 📊 Current Project Status

```bash
Project: CommandCenterProject
Environment: production
Service: CommandCenter
Redis: ❌ NOT FOUND
```

**Confirmed via CLI:**
```bash
railway status
railway variables | grep -i redis
# Result: No Redis variables found
```

---

## 🚀 Option 1: Add Redis via CLI (Fastest)

### Single Command:
```bash
railway add --database redis
```

**What happens:**
1. Railway provisions a Redis instance (~2 minutes)
2. Automatically sets `REDIS_URL` environment variable
3. Links Redis to your current service
4. Triggers backend redeploy with Redis connected

### Verify Installation:
```bash
# Check Redis was added
railway variables | grep -i redis

# Expected output:
# REDIS_URL | redis://default:password@redis.railway.internal:6379
```

---

## 🖱️ Option 2: Add Redis via Dashboard (Visual)

If you prefer the GUI:

1. Go to https://railway.app/dashboard
2. Select "CommandCenterProject"
3. Click **"+ New"**
4. Select **"Database"**
5. Choose **"Add Redis"**
6. Done! (~2 minutes to provision)

---

## ✅ Verification Steps

### Step 1: Check Environment Variables
```bash
railway variables | grep -i redis
```

**Expected output:**
```
REDIS_URL | redis://default:{password}@redis.railway.internal:6379
```

### Step 2: Check Backend Logs
```bash
railway logs
```

**Look for:**
```
✅ Redis connected: redis://...
✅ Smart context loaded: X tokens, type=system, cache_hit=False
```

### Step 3: Test API
```bash
# First request (cache miss)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my battery level?",
    "user_id": "test_user"
  }'

# Response should include:
# "context_tokens": 2000-2500
# "cache_hit": false
# "query_type": "system"

# Wait 2 seconds, then repeat (cache hit)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is my battery level?",
    "user_id": "test_user"
  }'

# Response should now show:
# "cache_hit": true  ← Cache is working!
```

---

## 🔧 Useful Railway CLI Commands

### View Project Info
```bash
# Current project status
railway status

# All environment variables
railway variables

# View logs (live)
railway logs

# Open project dashboard
railway open
```

### Service Management
```bash
# List all projects
railway list

# Switch project
railway link

# Add a database
railway add --database redis
railway add --database postgres
railway add --database mysql
railway add --database mongo
```

### Connect to Redis (After Installation)
```bash
# Open Redis CLI
railway connect redis

# Or get shell access to service
railway shell
```

---

## 📊 What You'll See After Adding Redis

### In `railway variables`
```
╔═══════════════ Variables for CommandCenter ════════════════╗
║ DATABASE_URL      │ postgresql://...                       ║
║ REDIS_URL         │ redis://default:...@redis.railway...  ║  ← NEW!
║ OPENAI_API_KEY    │ sk-...                                ║
║ ...               │ ...                                    ║
╚════════════════════════════════════════════════════════════╝
```

### In Backend Logs (`railway logs`)
```
[INFO] Starting backend service...
[INFO] Connecting to PostgreSQL...
[INFO] ✅ Database connected
[INFO] Connecting to Redis...
[INFO] ✅ Redis connected: redis://default:xxxxx@redis.railway.internal:6379
[INFO] Context caching enabled (TTL: 300s)
[INFO] Smart context loading initialized
[INFO] API server listening on port 8000
```

### In API Responses
```json
{
  "response": "Your battery is at 67%...",
  "query": "What is my battery level?",
  "agent_role": "Energy Systems Monitor",
  "duration_ms": 2847,
  "context_tokens": 2410,        // Down from 5k-8k!
  "cache_hit": false,            // First request
  "query_type": "system",
  "session_id": "abc-123..."
}
```

---

## 🐛 Troubleshooting

### Problem: `railway add --database redis` fails

**Possible causes:**
- Not linked to project
- No Railway account connected

**Solutions:**
```bash
# Check if logged in
railway whoami

# If not logged in
railway login

# Check project linkage
railway status

# If not linked to project
railway link
# Select "CommandCenterProject"
```

### Problem: Redis added but not connecting

**Check logs:**
```bash
railway logs | grep -i redis
```

**Look for errors:**
- "Connection refused" → Redis still provisioning (wait 2 min)
- "Authentication failed" → REDIS_URL might be wrong
- "Timeout" → Network issue

**Fix:**
```bash
# Restart service
railway redeploy

# Check Redis is running
railway variables | grep REDIS_URL
```

### Problem: REDIS_URL variable not showing

**Wait for provisioning:**
```bash
# Check every 30 seconds
watch -n 30 'railway variables | grep -i redis'
```

**After 2-3 minutes, should appear:**
```
REDIS_URL | redis://default:password@redis.railway.internal:6379
```

---

## 📈 Expected Timeline

| Step | Time | What's Happening |
|------|------|------------------|
| Run `railway add --database redis` | 5 sec | CLI sends provisioning request |
| Redis provisioning | 2 min | Railway creates Redis instance |
| Service redeploy | 1 min | Backend restarts with Redis |
| Verification | 1 min | Check logs and test API |
| **Total** | **~4 min** | **Fully operational** |

---

## ✅ Success Checklist

After adding Redis, verify these:

- [ ] `railway variables | grep REDIS_URL` shows Redis URL
- [ ] `railway logs` shows "✅ Redis connected"
- [ ] First API request shows `"cache_hit": false`
- [ ] Second identical request shows `"cache_hit": true`
- [ ] Token usage is 2k-4k (down from 5k-8k)
- [ ] No errors in logs

---

## 🎯 Quick Reference

### Add Redis (CLI)
```bash
railway add --database redis
```

### Check Status
```bash
railway status
railway variables | grep -i redis
railway logs
```

### Test Caching
```bash
# Test query (run twice)
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?", "user_id": "test"}'
```

### Connect to Redis
```bash
railway connect redis
# Opens redis-cli
```

---

## 📞 Next Steps

1. **Add Redis:**
   ```bash
   railway add --database redis
   ```

2. **Wait 2-3 minutes** for provisioning

3. **Verify:**
   ```bash
   railway variables | grep REDIS_URL
   railway logs | grep -i redis
   ```

4. **Test:**
   - Send API request
   - Check for cache_hit metadata
   - Verify token reduction

5. **Monitor:**
   - Watch logs for cache hits
   - Track token usage metrics
   - Verify cost savings

---

## 🎉 Summary

**Current Status:** Redis not yet added
**Recommended Action:** Run `railway add --database redis`
**Time Required:** ~4 minutes total
**Result:** 40-60% cost savings on OpenAI API

**One command to get started:**
```bash
railway add --database redis && railway logs --follow
```

This will:
1. Add Redis to your project
2. Stream logs so you can watch it connect
3. Automatically configure everything

---

**🚀 Ready when you are! Just run the command above. 🚀**
