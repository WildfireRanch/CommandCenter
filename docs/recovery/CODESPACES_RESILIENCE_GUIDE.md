# Codespaces Resilience & Backup Guide

**Created:** 2025-10-17
**Purpose:** Prevent future .env loss and enable automatic recovery
**Status:** ✅ Implemented

---

## 🎯 Overview

This guide documents the automated backup and restore system for CommandCenter in GitHub Codespaces, ensuring you never lose your environment configuration again.

---

## 🔐 Secret Management Strategy

### GitHub Codespaces Secrets (Recommended)
Codespaces secrets are:
- ✅ **Encrypted at rest** - Stored securely by GitHub
- ✅ **Auto-injected** - Available as environment variables on container create
- ✅ **Repository-scoped** - Only accessible in your Codespaces
- ✅ **Never in git** - No risk of committing secrets

### What Gets Backed Up
The following secrets are automatically backed up and restored:

| Secret | Purpose | Priority |
|--------|---------|----------|
| `OPENAI_API_KEY` | AI/embeddings | 🔴 Critical |
| `GOOGLE_CLIENT_ID` | OAuth | 🔴 Critical |
| `GOOGLE_CLIENT_SECRET` | OAuth | 🔴 Critical |
| `NEXTAUTH_SECRET` | Session encryption | 🔴 Critical |
| `RAILWAY_TOKEN` | Railway CLI auth | 🟡 Important |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | KB sync | 🟡 Important |
| `GOOGLE_DOCS_KB_FOLDER_ID` | KB sync | 🟡 Important |
| `SOLARK_EMAIL` | Solar integration | 🟢 Optional |
| `SOLARK_PASSWORD` | Solar integration | 🟢 Optional |
| `VICTRON_VRM_USERNAME` | Battery integration | 🟢 Optional |
| `VICTRON_VRM_PASSWORD` | Battery integration | 🟢 Optional |
| `VICTRON_INSTALLATION_ID` | Battery integration | 🟢 Optional |
| `ALLOWED_EMAIL` | Access control | 🟡 Important |

---

## 🚀 How It Works

### 1. Auto-Restore on Container Creation
When you create a new Codespace:

```
1. Container starts
2. .devcontainer/setup.sh runs automatically
3. .env files are created from templates
4. Secrets from Codespaces are injected
5. Railway CLI is configured
6. Dependencies are installed
```

**Files involved:**
- `.devcontainer/devcontainer.json` - Container config
- `.devcontainer/setup.sh` - Auto-restore script
- `*/.env.example` - Templates for restoration

### 2. Manual Backup
You can backup your current .env files at any time:

```bash
# Run backup script
bash .devcontainer/backup-env.sh

# This will:
# 1. Extract non-placeholder values from .env files
# 2. Upload to GitHub Codespaces secrets
# 3. Confirm success
```

### 3. Manual Restore
If secrets weren't auto-restored:

```bash
# Re-run setup
bash .devcontainer/setup.sh

# Or manually set env vars
export OPENAI_API_KEY=$(gh secret list --app codespaces | grep OPENAI | ...)
```

---

## 📦 Setup Instructions

### Initial Setup (One-Time)

#### Step 1: Install GitHub CLI
```bash
# Already installed in Codespaces
gh auth login
```

#### Step 2: Backup Current Secrets
```bash
# Make scripts executable
chmod +x .devcontainer/backup-env.sh
chmod +x .devcontainer/setup.sh

# Backup all .env files to Codespaces secrets
bash .devcontainer/backup-env.sh
```

#### Step 3: Verify Secrets
```bash
# List all Codespaces secrets
gh secret list --app codespaces

# Should see:
# OPENAI_API_KEY
# GOOGLE_CLIENT_ID
# GOOGLE_CLIENT_SECRET
# NEXTAUTH_SECRET
# ... etc
```

#### Step 4: Test Auto-Restore
```bash
# Delete a .env file
rm railway/.env

# Re-run setup
bash .devcontainer/setup.sh

# Verify it was restored
cat railway/.env | grep OPENAI_API_KEY
```

---

## 🔄 Recovery Procedures

### Scenario 1: Lost .env Files (Container Corruption)
**What happened:** Container crashed, .env files lost

**Recovery:**
```bash
# 1. Re-run setup (usually auto-runs on create)
bash .devcontainer/setup.sh

# 2. Verify .env files exist
ls -la railway/.env vercel/.env.local dashboards/.env mcp-server/.env

# 3. Check for missing values
bash .env-checklist.md  # Review checklist

# 4. Manually add any missing secrets
# See "Adding Secrets Manually" below
```

### Scenario 2: Forgot to Backup
**What happened:** Created .env files but never backed up

**Recovery:**
```bash
# 1. If you still have .env files, backup NOW
bash .devcontainer/backup-env.sh

# 2. If lost, retrieve from Railway
railway variables --service CommandCenter > railway-vars.txt

# 3. Manually reconstruct .env files
# Use .env-checklist.md as guide
```

### Scenario 3: Secrets Compromised
**What happened:** API keys leaked, need to rotate

**Recovery:**
```bash
# 1. Generate new secrets from providers
# - OpenAI: https://platform.openai.com/api-keys
# - Google: https://console.cloud.google.com
# - NextAuth: openssl rand -base64 32

# 2. Update .env files locally

# 3. Backup new secrets
bash .devcontainer/backup-env.sh

# 4. Update Railway
railway variables --service CommandCenter
# Manually update vars in Railway dashboard

# 5. Update Vercel
vercel env add GOOGLE_CLIENT_SECRET production
```

---

## 🛠️ Adding Secrets Manually

### Via GitHub CLI
```bash
# Add a single secret
echo "your-secret-value" | gh secret set SECRET_NAME --app codespaces

# Add from file
gh secret set GOOGLE_SERVICE_ACCOUNT_JSON --app codespaces < service-account.json

# Add interactively
gh secret set API_KEY --app codespaces
# (paste value, press Ctrl+D)
```

### Via GitHub Web UI
1. Go to: https://github.com/settings/codespaces
2. Click "New secret"
3. Enter name and value
4. Select repository: `WildfireRanch/CommandCenter`
5. Click "Add secret"

### Using Railway Token
```bash
# Get Railway token
railway whoami --token

# Save as Codespaces secret
echo "YOUR_RAILWAY_TOKEN" | gh secret set RAILWAY_TOKEN --app codespaces
```

---

## 🔍 Verification & Testing

### Verify Secrets Are Set
```bash
# List all secrets
gh secret list --app codespaces

# Check if secret exists
gh secret list --app codespaces | grep OPENAI_API_KEY
```

### Test Auto-Restore
```bash
# 1. Create test Codespace
gh codespace create

# 2. Connect to it
gh codespace ssh

# 3. Check if .env files exist
ls -la railway/.env vercel/.env.local

# 4. Verify secrets were injected
cat railway/.env | grep OPENAI_API_KEY
```

### Test Manual Restore
```bash
# Delete .env files
rm railway/.env vercel/.env.local dashboards/.env mcp-server/.env

# Run setup
bash .devcontainer/setup.sh

# Verify restoration
cat railway/.env
```

---

## 📊 Backup Schedule

### Automated (Recommended)
The devcontainer setup runs automatically on:
- New Codespace creation
- Container rebuild
- Manual trigger: `bash .devcontainer/setup.sh`

### Manual (For Updates)
Run backup when you:
- Add new API keys
- Change credentials
- Update configuration

```bash
# Backup after changes
bash .devcontainer/backup-env.sh
```

---

## 🚨 Security Best Practices

### DO ✅
- ✅ Use GitHub Codespaces secrets for sensitive values
- ✅ Rotate API keys every 90 days
- ✅ Use different keys for dev/staging/production
- ✅ Review `.gitignore` to ensure .env files are excluded
- ✅ Enable 2FA on GitHub, Railway, Google Cloud, OpenAI
- ✅ Use Railway's secret management for production

### DON'T ❌
- ❌ Commit .env files to git
- ❌ Share API keys in chat/email
- ❌ Use production keys in Codespaces
- ❌ Store secrets in code comments
- ❌ Use same password for multiple services
- ❌ Push secrets to public repositories

---

## 🔗 Related Documentation

- **Environment setup:** [.env-checklist.md](/.env-checklist.md)
- **Recovery audit:** [RECOVERY_AUDIT_2025-10-17.md](./RECOVERY_AUDIT_2025-10-17.md)
- **Railway guide:** [../guides/RAILWAY_ACCESS_GUIDE.md](../guides/RAILWAY_ACCESS_GUIDE.md)
- **Session 016:** [../sessions/SESSION_016_ENV_VARS.md](../sessions/SESSION_016_ENV_VARS.md)

---

## 📞 Troubleshooting

### Secret Not Auto-Injected
**Problem:** .env file created but secret still has placeholder

**Solution:**
```bash
# 1. Check if secret exists
gh secret list --app codespaces | grep SECRET_NAME

# 2. If not found, add it
echo "value" | gh secret set SECRET_NAME --app codespaces

# 3. Rebuild container
# In VS Code: Ctrl+Shift+P → "Codespaces: Rebuild Container"

# 4. Re-run setup
bash .devcontainer/setup.sh
```

### Railway CLI Not Authenticated
**Problem:** `railway` commands fail with "not authenticated"

**Solution:**
```bash
# Option 1: Use RAILWAY_TOKEN secret
echo "YOUR_TOKEN" | gh secret set RAILWAY_TOKEN --app codespaces
# Rebuild container

# Option 2: Manual login
railway login
# This will open browser for OAuth
```

### Backup Script Fails
**Problem:** `backup-env.sh` errors

**Solution:**
```bash
# 1. Check GitHub CLI is authenticated
gh auth status

# 2. If not, login
gh auth login

# 3. Retry backup
bash .devcontainer/backup-env.sh
```

---

## 🎯 Success Metrics

After implementing this system, you should have:

- ✅ Zero manual intervention on Codespace creation
- ✅ .env files auto-restored from templates + secrets
- ✅ All secrets safely backed up to GitHub
- ✅ Railway CLI auto-authenticated (if token provided)
- ✅ Dependencies auto-installed
- ✅ Clear documentation for recovery

---

## 📈 Future Enhancements

### Planned Improvements
- [ ] Automated secret rotation reminders (90-day)
- [ ] Encrypted local backup to private git repo
- [ ] Hashicorp Vault integration for secrets
- [ ] Automated health checks after restore
- [ ] Secret audit logging (who accessed what)
- [ ] Multi-environment support (dev/staging/prod)

### Advanced Options
- [ ] Use Railway's secret sync API
- [ ] Implement AWS Secrets Manager
- [ ] Setup HashiCorp Vault
- [ ] Create disaster recovery playbook
- [ ] Automated DR testing

---

**Last Updated:** 2025-10-17
**Maintained By:** WildfireRanch Team
**Status:** ✅ Production Ready
