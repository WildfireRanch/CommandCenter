# Session 014 - Railway PORT Issue Resolution ✅

**Date:** October 6, 2025
**Duration:** ~45 minutes
**Status:** ✅ COMPLETE - CrewAI Studio Deployed Successfully

---

## 🎯 Goal
Fix the persistent Railway PORT error preventing CrewAI Studio deployment:
```
Error: Invalid value for '--server.port' (env var: 'STREAMLIT_SERVER_PORT'): '$PORT' is not a valid integer.
```

---

## 🔍 Root Cause Analysis

### The Problem
Railway had **`STREAMLIT_SERVER_PORT=$PORT`** set as a **service variable** in the dashboard, containing the **literal string** `"$PORT"` instead of an actual port number.

### Why It Was Tricky
1. **Multiple config files** - railway.json, railway.toml, Procfile, start.sh all had different settings
2. **Config merging** - Railway merges service settings with railway.json
3. **Variable precedence** - Service variables set before any script runs
4. **Hidden variable** - `STREAMLIT_SERVER_PORT` wasn't visible in code, only in Railway dashboard

### Failed Attempts (Sessions 012-013)
- ❌ Modified `start.sh` to handle PORT
- ❌ Updated `db_utils.py` to check DATABASE_URL and DB_URL
- ❌ Added `unset STREAMLIT_SERVER_PORT` in bash
- ❌ Tried to override with `export STREAMLIT_SERVER_PORT=$PORT`
- ❌ None worked because Railway service variable was set BEFORE script execution

---

## ✅ Solution

### Step 1: Identified the Culprit
Found `STREAMLIT_SERVER_PORT=$PORT` in Railway service variables (Dashboard → Variables tab)

### Step 2: The Fix
**Deleted the variable** from Railway dashboard completely

### Step 3: Let start.sh Handle It
With the bad variable gone, our `start.sh` script properly sets:
```bash
export STREAMLIT_SERVER_PORT=$ACTUAL_PORT
```

### Final Working Configuration

**crewai-studio/railway.json:**
```json
{
  "deploy": {
    "startCommand": "bash start.sh"
  }
}
```

**crewai-studio/start.sh:**
```bash
#!/bin/bash
# Determine actual port
if [ -z "$PORT" ]; then
  ACTUAL_PORT=8501
else
  ACTUAL_PORT=$PORT
fi

# Set STREAMLIT_SERVER_PORT to numeric value
export STREAMLIT_SERVER_PORT=$ACTUAL_PORT

# Start Streamlit
streamlit run app/app.py --server.address=0.0.0.0 ...
```

**Railway Service Variables:**
- ✅ `DATABASE_URL` (or `DB_URL`)
- ✅ `OPENAI_API_KEY`
- ❌ ~~`STREAMLIT_SERVER_PORT`~~ (DELETED)

---

## 📊 Results

### ✅ Success Metrics
- CrewAI Studio deploys cleanly on Railway
- No more PORT errors
- Streamlit starts on Railway-assigned port
- Service connects to PostgreSQL database
- All 4 production services now operational

### 🟢 Production Status (All Services)
1. **Railway API** - https://api.wildfireranch.us ✅
2. **Vercel Frontend** - Next.js deployment ✅
3. **Vercel MCP Server** - Claude Desktop integration ✅
4. **Railway CrewAI Studio** - Agent management GUI ✅
5. **PostgreSQL Database** - TimescaleDB enabled ✅

---

## 🎓 Key Learnings

### Railway Configuration Priority
1. **Service Variables** (Dashboard) - Highest priority, set before any script
2. **railway.json** - Config file in repo
3. **railway.toml** - Repo root config (if present)
4. **Start command scripts** - Run last, can override env vars set in script

### Environment Variable Best Practices
- ⚠️ **Never set `STREAMLIT_SERVER_PORT` in Railway dashboard**
- ✅ Let Railway auto-set `PORT`
- ✅ Let startup script handle `STREAMLIT_SERVER_PORT`
- ✅ Use bash scripts to properly expand variables

### Debugging Railway Issues
1. Check service variables in Dashboard first
2. Use inline debug commands: `pwd && ls -la && env | grep PORT`
3. Look for config merging messages in logs
4. Remember: JSON doesn't expand `$VARIABLES` like bash does

---

## 📝 Files Modified This Session

1. **crewai-studio/start.sh** - Enhanced PORT handling with debug output
2. **crewai-studio/railway.json** - Fixed startCommand to use bash start.sh
3. **crewai-studio/db_utils.py** - Support both DB_URL and DATABASE_URL
4. **docs/progress.md** - Updated with Session 13 and deployment status
5. **docs/00-project-summary.md** - Updated with production completion

---

## 🚀 Git Commits

1. `f33271d4` - Fix STREAMLIT_SERVER_PORT by explicitly exporting numeric value
2. `855afc19` - Fix railway.json to use start.sh instead of direct streamlit command
3. `a241324c` - Add environment diagnostic script
4. `b099c35d` - Fix debug commands in railway.json
5. `db update` - Support DATABASE_URL in addition to DB_URL

---

## 🎉 What's Working Now

### Complete Production Stack
```
┌─────────────────────────────────────────┐
│         PRODUCTION ARCHITECTURE          │
├─────────────────────────────────────────┤
│                                          │
│  Vercel (Frontend + MCP)                │
│  ├─ Next.js App (7 pages)               │
│  └─ MCP Server (Claude Desktop)         │
│         │                                │
│         ├──→ Railway API                 │
│         │    └─ FastAPI + CrewAI         │
│         │                                │
│         └──→ Railway CrewAI Studio ✅    │
│              └─ Streamlit GUI            │
│                                          │
│  Railway PostgreSQL + TimescaleDB        │
│  └─ Shared across all services          │
│                                          │
└─────────────────────────────────────────┘
```

### All Services Healthy ✅
- API responding: https://api.wildfireranch.us
- Database connected
- Agent memory working
- Energy tracking operational
- Frontend live on Vercel
- MCP Server active
- CrewAI Studio deployed 🎉

---

## 📋 Next Steps

### Immediate
- [x] CrewAI Studio successfully deployed
- [ ] Add studio URL to Vercel environment variables
- [ ] Test studio page in production frontend

### Short-term
- [ ] Frontend enhancements (charts, advanced chat)
- [ ] Authentication system
- [ ] Real-time WebSocket updates
- [ ] Mobile responsiveness

### Long-term
- [ ] Additional agents
- [ ] Advanced analytics
- [ ] Mobile app
- [ ] Multi-tenant support

---

## 💡 Troubleshooting Guide for Future

### If You See PORT Errors Again:

1. **Check Railway Service Variables First:**
   ```
   Dashboard → Service → Variables → Look for STREAMLIT_SERVER_PORT
   ```

2. **If STREAMLIT_SERVER_PORT exists:**
   - Delete it completely
   - Let start.sh handle it

3. **Verify railway.json:**
   ```json
   {
     "deploy": {
       "startCommand": "bash start.sh"
     }
   }
   ```

4. **Check start.sh has:**
   ```bash
   export STREAMLIT_SERVER_PORT=$ACTUAL_PORT
   ```

5. **Redeploy and check logs for:**
   ```
   Starting Streamlit on port XXXX...
   You can now view your Streamlit app
   ```

---

## 🏆 Session Success

**Problem:** 3 sessions trying to fix PORT error
**Root Cause:** Hidden Railway service variable with literal `$PORT` string
**Solution:** Delete the variable, let script handle it
**Result:** ✅ Clean deployment, all services operational

**Time to Resolution:** Multiple sessions (valuable learning experience!)
**Production Status:** 🟢 100% OPERATIONAL

---

*Session 014 Complete - All Production Services Deployed Successfully! 🎉*
