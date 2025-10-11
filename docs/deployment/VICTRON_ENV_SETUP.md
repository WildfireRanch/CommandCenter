# Victron Environment Variables Setup

**Purpose:** Guide for setting up Victron VRM API credentials in Railway
**Created:** December 10, 2025
**For:** CommandCenter V1.6 Victron Cerbo Integration

---

## 🔑 Required Environment Variables

You need to add **3 required environment variables** to Railway for the Victron integration to work:

```bash
VICTRON_VRM_USERNAME=your-email@example.com
VICTRON_VRM_PASSWORD=your-vrm-password
VICTRON_INSTALLATION_ID=123456
```

---

## 📋 Step-by-Step Setup

### Step 1: Get Your VRM Credentials

**VRM Username (Email):**
- This is the email you use to log into Victron VRM Portal
- Example: `ranch@wildfireranch.us`

**VRM Password:**
- This is your VRM account password
- Keep it secure - it's stored as a Railway secret

### Step 2: Find Your Installation ID

1. **Log in to VRM Portal:**
   - Go to: https://vrm.victronenergy.com
   - Log in with your credentials

2. **Navigate to your installation:**
   - Click on your Cerbo GX installation
   - Look at the URL in your browser

3. **Extract Installation ID:**
   - URL will look like: `https://vrm.victronenergy.com/installation/123456/dashboard`
   - The number `123456` is your **VICTRON_INSTALLATION_ID**
   - Copy this number

### Step 3: Add to Railway Backend

1. **Go to Railway Dashboard:**
   - Open: https://railway.app
   - Navigate to your CommandCenter project
   - Click on your **backend service** (commandcenter-backend)

2. **Open Variables Tab:**
   - Click on "Variables" in the service menu
   - Click "New Variable" or "Raw Editor"

3. **Add the 3 Variables:**

   **Option A: One by One**
   ```
   Variable Name: VICTRON_VRM_USERNAME
   Value: your-email@example.com

   Variable Name: VICTRON_VRM_PASSWORD
   Value: your-password

   Variable Name: VICTRON_INSTALLATION_ID
   Value: 123456
   ```

   **Option B: Raw Editor (Faster)**
   ```bash
   VICTRON_VRM_USERNAME=your-email@example.com
   VICTRON_VRM_PASSWORD=your-password
   VICTRON_INSTALLATION_ID=123456
   ```

4. **Save Variables:**
   - Click "Add" or "Update Variables"
   - Railway will automatically redeploy your service

### Step 4: Optional Variables (Advanced)

You can also set these **optional** variables:

```bash
# Custom API URL (only if using different VRM instance)
VICTRON_API_URL=https://vrmapi.victronenergy.com

# Custom polling interval (default is 180 seconds / 3 minutes)
VICTRON_POLL_INTERVAL=180
```

**Note:** These are not required - the system uses sensible defaults.

---

## ✅ Verify Setup

### Method 1: Check Railway Logs

After deploying, check Railway logs:

```
1. Go to Railway → Your Backend Service → Deployments
2. Click latest deployment → View Logs
3. Look for: "Authenticating with Victron VRM API..."
4. Should see: "Authentication successful. User ID: XXXXX"
```

### Method 2: Test Endpoint

Once deployed, test the connection:

```bash
# Test authentication
curl https://api.wildfireranch.us/victron/health | jq

# Should return:
# {
#   "status": "success",
#   "data": {
#     "poller_running": true,
#     "last_poll": "2025-12-10T12:00:00Z",
#     ...
#   }
# }
```

### Method 3: Check Database

Query the database to see if data is flowing:

```sql
-- In Railway PostgreSQL console
SELECT COUNT(*) FROM victron.battery_readings;
-- Should see increasing number of rows
```

---

## 🚨 Troubleshooting

### Error: "Victron VRM credentials not configured"

**Problem:** Environment variables not set
**Solution:**
1. Check variable names are EXACTLY: `VICTRON_VRM_USERNAME`, `VICTRON_VRM_PASSWORD`, `VICTRON_INSTALLATION_ID`
2. No extra spaces in variable names
3. Redeploy after adding variables

### Error: "Authentication failed"

**Problem:** Invalid credentials
**Solution:**
1. Double-check your VRM Portal login works: https://vrm.victronenergy.com
2. Make sure password is correct (no copy-paste errors)
3. Check if 2FA is enabled (may need app-specific password)

### Error: "Installation ID required"

**Problem:** `VICTRON_INSTALLATION_ID` not set or wrong
**Solution:**
1. Verify you copied the installation ID from the URL correctly
2. It should be just the number, no extra text
3. Example: `123456` NOT `installation/123456`

### Error: "Rate limit exceeded"

**Problem:** Too many API requests
**Solution:**
1. Default polling is every 3 minutes (20 requests/hour)
2. VRM limit is 50 requests/hour
3. Check if multiple services are polling same account
4. Increase `VICTRON_POLL_INTERVAL` if needed

---

## 📍 Where Variables Go

### ✅ Railway Backend (REQUIRED)
**Service:** `commandcenter-backend`
**Location:** Railway → Project → Backend Service → Variables

Add these variables here:
- `VICTRON_VRM_USERNAME`
- `VICTRON_VRM_PASSWORD`
- `VICTRON_INSTALLATION_ID`

### ❌ Railway Dashboard (NOT NEEDED)
**Service:** `commandcenter-dashboard`
**No Victron variables needed** - Dashboard gets data via API

### ❌ Vercel (NOT NEEDED)
**Service:** Frontend (if you have one)
**No Victron variables needed** - Frontend calls backend API

**Why?**
- Victron integration runs on **backend only**
- Dashboard and frontend get data from backend API endpoints
- No direct VRM API calls from frontend

---

## 🔐 Security Best Practices

### DO:
- ✅ Store credentials as Railway environment variables (encrypted)
- ✅ Use strong VRM password
- ✅ Never commit credentials to git
- ✅ Rotate password periodically

### DON'T:
- ❌ Don't put credentials in code files
- ❌ Don't share credentials in chat/email
- ❌ Don't use same password for multiple services
- ❌ Don't store in `.env` file in git repo

---

## 📊 Current Values Needed

**Fill in your actual values:**

```bash
# Copy this template and fill in your values
VICTRON_VRM_USERNAME=________________________
VICTRON_VRM_PASSWORD=________________________
VICTRON_INSTALLATION_ID=____________________
```

---

## 🔗 Related Documentation

- **VRM Portal:** https://vrm.victronenergy.com
- **VRM API Docs:** https://vrm-api-docs.victronenergy.com
- **Railway Docs:** https://docs.railway.app/guides/variables
- **Integration Code:** [railway/src/integrations/victron.py](../../railway/src/integrations/victron.py)

---

**Summary:** Add 3 variables to Railway Backend service, Railway handles the rest! 🚀
