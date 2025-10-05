# 🔧 Session 013 Prompt - Fix CrewAI Studio Railway PORT Issue

Copy this to start your next session:

---

Hi Claude! Continuing work on CommandCenter - Session 013 (CrewAI Studio Fix).

**Critical Issue from Session 012:**
CrewAI Studio deployment is failing on Railway with PORT error:
```
Error: Invalid value for '--server.port' (env var: 'STREAMLIT_SERVER_PORT'): '$PORT' is not a valid integer.
```

**What We Tried (Session 012):**
- ✅ Created `start.sh` wrapper script with `${PORT:-8501}`
- ✅ Updated `railway.toml` to use `bash start.sh`
- ✅ Updated `Procfile` to use `bash start.sh`
- ❌ **Still getting the error** - Railway not setting PORT or script not executing

**Root Cause Analysis Needed:**
The `$PORT` variable is being passed as a literal string instead of being expanded. This means:
1. Railway might not be setting the `PORT` environment variable at all
2. The start.sh script might not be executing
3. Railway might be using a different config file (Procfile vs railway.toml)
4. The working directory might be wrong

**Current File Structure:**
```
/workspaces/CommandCenter/
├── railway.toml (repo root)
│   └── Points to /crewai-studio directory
└── crewai-studio/
    ├── start.sh (wrapper script)
    ├── Procfile (process definition)
    ├── railway.json (service config)
    ├── requirements.txt
    └── app/app.py (main Streamlit app)
```

**Files to Review:**
1. `/workspaces/CommandCenter/railway.toml`
2. `/workspaces/CommandCenter/crewai-studio/start.sh`
3. `/workspaces/CommandCenter/crewai-studio/Procfile`
4. `/workspaces/CommandCenter/crewai-studio/railway.json`

**Investigation Steps:**

1. **Check Railway Configuration Priority:**
   - Railway reads configs in order: `railway.toml` → `Procfile` → `railway.json`
   - Multiple configs might be conflicting
   - Need to consolidate to ONE config method

2. **Verify Environment Variables:**
   - Check if Railway actually sets `PORT` automatically
   - May need to manually set `PORT` in Railway dashboard
   - Check Railway documentation for PORT handling

3. **Debug the Start Command:**
   - Add echo statements to start.sh for debugging
   - Check Railway logs to see which command is executing
   - Verify bash is available in Railway environment

4. **Alternative Solutions:**
   - Use Railway's native PORT if available
   - Hardcode a port and let Railway proxy it
   - Use environment variable directly in Streamlit
   - Switch to using only `railway.json` (remove railway.toml and Procfile)

**Recommended Fix Strategy:**

### Option 1: Simplify to Single Config (RECOMMENDED)
Remove `railway.toml` from repo root and use only `railway.json` in crewai-studio:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "bash start.sh",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Option 2: Set PORT Manually in Railway
If Railway doesn't auto-set PORT:
1. Go to Railway Dashboard → Variables
2. Add: `PORT=8080` (or any port)
3. Redeploy

### Option 3: Use Nixpacks Detection
Let Nixpacks auto-detect Python and handle PORT:
- Remove all config files
- Add `.nixpacks` file with Python configuration
- Let Railway handle port automatically

### Option 4: Modify start.sh to Handle Missing PORT
```bash
#!/bin/bash
# Check if PORT is set, if not use default
if [ -z "$PORT" ]; then
  echo "WARNING: PORT not set by Railway, using default 8080"
  export PORT=8080
fi

echo "Starting Streamlit on port $PORT..."
streamlit run app/app.py \
  --server.address=0.0.0.0 \
  --server.port=$PORT \
  --server.headless=true \
  --server.fileWatcherType=none \
  --browser.gatherUsageStats=false \
  --client.toolbarMode=minimal \
  --server.enableXsrfProtection=false \
  --server.enableCORS=false
```

**Today's Tasks:**

1. **Read Railway Logs Carefully:**
   - Check which config file Railway is using
   - Look for error messages about PORT
   - See if start.sh is executing at all
   - Check for permission errors

2. **Verify Railway Settings:**
   - Check root directory is set to `/crewai-studio`
   - Check if PORT variable exists in Railway dashboard
   - Verify service settings in Railway

3. **Implement Fix:**
   - Choose one of the 4 options above
   - Test locally first if possible
   - Deploy and verify in Railway logs
   - Confirm Streamlit starts successfully

4. **Verify Success:**
   - See "Starting Streamlit on port XXXX" in logs
   - Service status shows "Running"
   - URL is accessible
   - No more PORT errors

**Quick Reference:**

**Railway Dashboard Checks:**
- Settings → Root Directory → Should be empty OR `/crewai-studio`
- Variables → Check if `PORT` exists
- Deployments → Logs → Look for startup messages
- Settings → Service → Check start command

**Files That Might Conflict:**
- `/railway.toml` (repo root) ← May need to remove
- `/crewai-studio/Procfile` ← Railway might ignore this
- `/crewai-studio/railway.json` ← Railway might prioritize this

**Expected Working State:**
```
Railway Logs Should Show:
✓ Building with Nixpacks
✓ Installing Python dependencies
✓ Running start.sh
✓ Starting Streamlit on port 8080 (or similar)
✓ You can now view your Streamlit app
✓ Deployment successful
```

**Resources:**
- [Railway Docs - Configuration](https://docs.railway.app/deploy/config-as-code)
- [Railway Docs - Environment Variables](https://docs.railway.app/develop/variables)
- [Streamlit Docs - Configuration](https://docs.streamlit.io/library/advanced-features/configuration)
- [Session 012 Summary](SESSION_012_SUMMARY.md) - What we tried

**Debug Commands (if testing locally):**
```bash
# Test start.sh locally
cd /workspaces/CommandCenter/crewai-studio
PORT=8080 bash start.sh

# Check if PORT is being set
echo "PORT is: $PORT"

# Test Streamlit directly
streamlit run app/app.py --server.port 8080
```

**Success Criteria:**
- ✅ No more "$PORT is not a valid integer" errors
- ✅ Railway logs show "Starting Streamlit on port XXXX"
- ✅ Service status is "Running" not "Crashed"
- ✅ Studio URL is accessible
- ✅ Can add `NEXT_PUBLIC_STUDIO_URL` to Vercel

**After This Is Fixed:**
1. Copy the working Railway URL
2. Add `NEXT_PUBLIC_STUDIO_URL` to Vercel
3. Test `/studio` page in production
4. Run health checks
5. Session complete! ✅

---

**Priority:** HIGH - This is blocking production completion
**Estimated Time:** 30-60 minutes (depending on which fix works)
**Difficulty:** Medium (configuration debugging)

Ready to fix the Railway PORT issue and get CrewAI Studio live! 🔧

---

**TL;DR:**
Railway isn't setting/expanding `$PORT` properly. Need to:
1. Check Railway logs to see what's happening
2. Simplify config (remove conflicting files)
3. Either set PORT manually or fix start.sh to handle missing PORT
4. Verify deployment succeeds
5. Add studio URL to Vercel
