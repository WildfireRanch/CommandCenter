# Configuration Management

**Purpose:** Master configuration and environment variable management

---

## 🎯 Quick Start

### Step 1: Get Railway Variables
```bash
railway login
railway variables --service CommandCenter
```

### Step 2: Paste into Master Config
Open [`.env.master`](.env.master) and paste the Railway variables

### Step 3: Sync to All Services
```bash
bash docs/configuration/sync-env.sh
```

This will automatically update:
- `railway/.env`
- `vercel/.env.local`
- `dashboards/.env`
- `mcp-server/.env`

### Step 4: Backup to GitHub Codespaces
```bash
bash .devcontainer/backup-env.sh
```

---

## 📁 Files in This Folder

### Master Configuration
- **`.env.master`** - Your master configuration file
  - ⚠️ **Gitignored** - Safe to store secrets
  - All secrets in one place
  - Source of truth for local development

### Sync Script
- **`sync-env.sh`** - Distributes variables from master to all .env files
  - Automatically updates all services
  - Only updates non-empty values
  - Safe to run multiple times

### Documentation
- **`ENV_COMPLETE.md`** - Complete environment variable reference
  - All variables explained
  - How to obtain each secret
  - Service requirements

- **`SERVICE_MATRIX.md`** - Service configuration matrix
  - Which service needs which variables
  - Priority levels
  - Impact analysis

---

## 🔄 Workflow

### Initial Setup
```bash
# 1. Get Railway variables
railway login
railway variables --service CommandCenter > railway-vars.txt

# 2. Open master config
code docs/configuration/.env.master

# 3. Paste Railway variables (keep the ones already there)

# 4. Add any missing values:
#    - GOOGLE_SERVICE_ACCOUNT_JSON (from Google Cloud)
#    - GOOGLE_DOCS_KB_FOLDER_ID (from Drive URL)
#    - ALLOWED_EMAIL (your email)

# 5. Sync to all .env files
bash docs/configuration/sync-env.sh

# 6. Backup to Codespaces
bash .devcontainer/backup-env.sh
```

### Updating Variables
```bash
# 1. Update master config
code docs/configuration/.env.master

# 2. Sync changes
bash docs/configuration/sync-env.sh

# 3. Backup (optional)
bash .devcontainer/backup-env.sh
```

### Adding New Variables
```bash
# 1. Add to master config
echo "NEW_VAR=value" >> docs/configuration/.env.master

# 2. Update sync script to include new variable
code docs/configuration/sync-env.sh

# 3. Sync
bash docs/configuration/sync-env.sh
```

---

## 🔐 Security

### What's Gitignored
- ✅ `.env.master` - **Safe to store secrets**
- ✅ All `.env` files
- ✅ All `.env.local` files

### What's Tracked in Git
- ✅ `.env.example` files - Templates only
- ✅ `sync-env.sh` - Sync script
- ✅ Documentation files

### Best Practices
1. **Never commit** `.env.master` or any `.env` files
2. **Always use** `.env.master` as single source of truth
3. **Backup** to GitHub Codespaces after updates
4. **Rotate secrets** every 90 days

---

## 📊 Variable Sources

### From Railway (Production)
- `DATABASE_URL`
- `REDIS_URL`
- `OPENAI_API_KEY` (if stored there)

### From SESSION_016 (Already Recovered)
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`

### From Google Cloud Console
- `GOOGLE_SERVICE_ACCOUNT_JSON`

### From Google Drive
- `GOOGLE_DOCS_KB_FOLDER_ID`

### From OpenAI (if not in Railway)
- `OPENAI_API_KEY`

### From User
- `ALLOWED_EMAIL`
- `SOLARK_*` (optional)
- `VICTRON_*` (optional)

---

## 🎯 Which Services Get What

### Railway Backend (`railway/.env`)
Gets everything except:
- `NEXTAUTH_*` (frontend only)
- `NEXT_PUBLIC_*` (frontend only)
- `RAILWAY_API_URL` (dashboards/mcp only)

### Vercel Frontend (`vercel/.env.local`)
Gets:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `ALLOWED_EMAIL`
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_STUDIO_URL`

### Dashboards (`dashboards/.env`)
Gets:
- `RAILWAY_API_URL`
- `DATABASE_URL`

### MCP Server (`mcp-server/.env`)
Gets:
- `RAILWAY_API_URL`

---

## 🔗 Related Documentation

- **[ENV_COMPLETE.md](./ENV_COMPLETE.md)** - All variables explained
- **[SERVICE_MATRIX.md](./SERVICE_MATRIX.md)** - Service requirements
- **[/.env-checklist.md](/.env-checklist.md)** - Recovery checklist
- **[../recovery/CODESPACES_RESILIENCE_GUIDE.md](../recovery/CODESPACES_RESILIENCE_GUIDE.md)** - Backup guide

---

## 🆘 Troubleshooting

### Sync Script Fails
```bash
# Check if master file exists
ls -la docs/configuration/.env.master

# Check if script is executable
chmod +x docs/configuration/sync-env.sh

# Run with verbose output
bash -x docs/configuration/sync-env.sh
```

### Variables Not Syncing
```bash
# Check variable has value in master
cat docs/configuration/.env.master | grep VARIABLE_NAME

# Check target file exists
ls -la railway/.env vercel/.env.local dashboards/.env mcp-server/.env
```

### Need to Start Over
```bash
# Re-create from templates
cp railway/.env.example railway/.env
cp vercel/.env.example vercel/.env.local
cp dashboards/.env.example dashboards/.env
cp mcp-server/.env.example mcp-server/.env

# Edit master config
code docs/configuration/.env.master

# Sync
bash docs/configuration/sync-env.sh
```

---

**Last Updated:** 2025-10-17
**Maintained By:** WildfireRanch Team
