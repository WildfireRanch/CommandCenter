# Railway Database Connection Fix

**Issue:** CrewAI Studio cannot connect to PostgreSQL database
**Error:** `OperationalError: connection to server at "postgresdb-production-e5ae.up.railway.app" failed: Connection timed out`
**Date:** October 6, 2025

---

## Problem

CrewAI Studio (in CrewAI Railway project) cannot connect to PostgreSQL (in CommandCenter Railway project) due to:
1. Missing or incorrect `DATABASE_URL` environment variable
2. Network connectivity between Railway projects
3. Database not allowing external connections

---

## Solution

### Option 1: Manual DATABASE_URL Configuration (Recommended)

#### Step 1: Get Database Credentials

1. **Go to Railway Dashboard**
2. **Navigate to CommandCenter project**
3. **Click PostgreSQL service**
4. **Click "Variables" tab**
5. **Copy these values:**
   ```
   PGHOST = postgresdb-production-e5ae.up.railway.app
   PGPORT = 5432
   PGUSER = postgres
   PGPASSWORD = [copy this password]
   PGDATABASE = commandcenter
   ```

#### Step 2: Construct DATABASE_URL

Format:
```
postgresql://{PGUSER}:{PGPASSWORD}@{PGHOST}:{PGPORT}/{PGDATABASE}
```

Example (with fake password):
```
postgresql://postgres:1tVY3mhx1Xt3d7tvBrDKU0ZC0JO7u010@postgresdb-production-e5ae.up.railway.app:5432/commandcenter
```

#### Step 3: Add to CrewAI Studio

1. **Go to CrewAI project**
2. **Click CrewAI Studio service**
3. **Click "Variables" tab**
4. **Delete old DATABASE_URL** (if exists)
5. **Click "+ New Variable"**
6. **Name:** `DATABASE_URL`
7. **Value:** (paste the constructed URL from Step 2)
8. **Click "Add"**
9. **Click "Redeploy"** button at top

#### Step 4: Verify Deployment

1. **Click "Deployments"** tab
2. **Click latest deployment**
3. **Click "View Logs"**
4. **Look for:**
   ```
   ✅ You can now view your Streamlit app in your browser
   ✅ No database connection errors
   ```

---

### Option 2: Railway Service Reference (Alternative)

**Note:** This only works if both services are in the same Railway project. Since they're in different projects, use Option 1 above.

If services were in same project:
1. CrewAI Studio Variables → "+ New Variable"
2. Select "Add Reference"
3. Choose PostgreSQL service
4. Select `DATABASE_URL`

---

## Verification Steps

### 1. Check Logs for Success

After redeployment, logs should show:
```
=== RAILWAY ENVIRONMENT DEBUG ===
PORT from Railway: 8080
...
You can now view your Streamlit app in your browser.
Network URL: http://0.0.0.0:8080
```

**No errors about:**
- ❌ Connection timed out
- ❌ Could not translate host name
- ❌ password authentication failed

### 2. Test Studio Access

1. **Open browser:** https://studio.wildfireranch.us
2. **Hard refresh:** `Ctrl+Shift+R` (or `Cmd+Shift+R` on Mac)
3. **You should see:**
   - CrewAI logo
   - Left sidebar with pages: Crews, Tools, Agents, Tasks, etc.
   - No "JavaScript required" message

### 3. Verify Database Connection

In Studio:
1. **Go to Agents page**
2. **Click "Create agent"**
3. **Fill in basic info**
4. **Click Save**
5. **Refresh page**
6. **Agent should still be there** (proves database persistence)

---

## Troubleshooting

### Issue: Still seeing "Connection timed out"

**Possible causes:**
1. **DATABASE_URL has typo**
   - Double-check format: `postgresql://user:pass@host:port/database`
   - No extra spaces or quotes

2. **Password has special characters**
   - URL-encode the password if it has special chars
   - Example: `@` becomes `%40`, `#` becomes `%23`

3. **Railway service variables not updated**
   - Delete old variable completely before adding new one
   - Redeploy after changing variables

### Issue: "password authentication failed"

**Fix:**
1. Get fresh password from PostgreSQL service variables
2. Verify it's the `PGPASSWORD` value (not `PGPASS` or other variant)
3. Update DATABASE_URL with correct password
4. Redeploy

### Issue: "database does not exist"

**Fix:**
1. Verify database name is `commandcenter` (not `postgres`)
2. Check `PGDATABASE` variable in PostgreSQL service
3. Update DATABASE_URL with correct database name

### Issue: "could not translate host name"

**Fix:**
1. Don't use `.railway.internal` hostname (only works within same project)
2. Use public hostname: `postgresdb-production-e5ae.up.railway.app`
3. Get correct hostname from PostgreSQL service `PGHOST` variable

---

## Railway Service Configuration Checklist

### PostgreSQL Service (CommandCenter Project)
- [x] Service is running
- [x] Public hostname enabled: `postgresdb-production-e5ae.up.railway.app`
- [x] Port 5432 exposed
- [x] Database `commandcenter` exists
- [x] Password in `PGPASSWORD` variable

### CrewAI Studio Service (CrewAI Project)
- [ ] `DATABASE_URL` set correctly
- [ ] No `STREAMLIT_SERVER_PORT=$PORT` variable (delete if exists)
- [ ] `OPENAI_API_KEY` set
- [ ] `PORT` variable **not set** (let Railway auto-assign)
- [ ] Service redeployed after variable changes

---

## Database URL Format Reference

### PostgreSQL (Production - Cross-Project)
```
postgresql://postgres:PASSWORD@postgresdb-production-XXXX.up.railway.app:5432/commandcenter
```

### PostgreSQL (Same Project - Internal)
```
postgresql://postgres:PASSWORD@postgres.railway.internal:5432/commandcenter
```

### SQLite (Local Development)
```
sqlite:///crewai.db
```

---

## Expected Behavior After Fix

1. **Railway Logs:**
   ```
   ✅ Using Railway PORT: 8080
   ✅ Starting Streamlit...
   ✅ You can now view your Streamlit app in your browser
   ```

2. **Studio UI:**
   - Loads immediately
   - Shows CrewAI branding
   - All 8 pages accessible
   - Can create/edit agents, crews, tasks

3. **Database:**
   - Data persists across page refreshes
   - Agents/crews/tasks saved to PostgreSQL
   - Can query data from API or MCP server

4. **Frontend Integration:**
   - `/studio` page shows green "Studio Connected" banner
   - Iframe loads Studio correctly
   - "Open in New Tab" button works

---

## Quick Copy-Paste Commands

### Get PostgreSQL Password from Railway
```bash
# In local terminal (if Railway CLI installed)
railway link
railway run printenv PGPASSWORD
```

### Test Database Connection Locally
```bash
# Replace PASSWORD, HOST, PORT, DATABASE with actual values
psql "postgresql://postgres:PASSWORD@postgresdb-production-e5ae.up.railway.app:5432/commandcenter"

# If successful, you'll see:
# psql (14.x)
# Type "help" for help.
# commandcenter=#
```

### Verify DATABASE_URL Format
```bash
# In CrewAI Studio service logs, should see:
export DATABASE_URL="postgresql://postgres:****@postgresdb-production-e5ae.up.railway.app:5432/commandcenter"
```

---

## Next Steps After Fix

Once database connection is working:

1. **Complete Testing Checklist:**
   - See `/docs/SESSION_015_TESTING_CHECKLIST.md`
   - Test agent creation
   - Test crew execution
   - Verify data persistence

2. **Update Frontend:**
   - Ensure `NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us` in Vercel
   - Redeploy Vercel
   - Test `/studio` page

3. **Document Success:**
   - Take screenshots
   - Update session summary
   - Mark Phase 4 COMPLETE in progress.md

---

**Status:** 🔴 IN PROGRESS - Awaiting database configuration fix
**Last Updated:** October 6, 2025
**Session:** 015
