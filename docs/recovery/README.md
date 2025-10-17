# Recovery & Resilience Documentation

**Purpose:** Documentation for backup, recovery, and disaster resilience procedures

---

## 📚 Documents in this Folder

### Primary Guides

1. **[CODESPACES_RESILIENCE_GUIDE.md](./CODESPACES_RESILIENCE_GUIDE.md)**
   - Complete guide to automated backup/restore system
   - GitHub Codespaces secrets setup
   - Auto-restore procedures
   - **Status:** ✅ Implemented

2. **[RECOVERY_AUDIT_2025-10-17.md](./RECOVERY_AUDIT_2025-10-17.md)**
   - Audit of 2025-10-17 Codespace corruption
   - Damage assessment
   - Recovery procedures followed
   - **Status:** ✅ Complete

---

## 🚨 Quick Recovery Steps

### If You Lost Your .env Files

1. **Re-run automated setup:**
   ```bash
   bash .devcontainer/setup.sh
   ```

2. **Check what's missing:**
   ```bash
   cat .env-checklist.md
   ```

3. **Get secrets from Railway:**
   ```bash
   railway login
   railway variables --service CommandCenter
   ```

4. **Get secrets from GitHub Codespaces:**
   ```bash
   gh secret list --app codespaces
   ```

5. **Manually fill remaining values** using documentation:
   - [ENV_COMPLETE.md](../configuration/ENV_COMPLETE.md)
   - [SESSION_016_ENV_VARS.md](../sessions/SESSION_016_ENV_VARS.md)

---

## 🛡️ Prevention System

### Automatic Backup/Restore
- **File:** `.devcontainer/devcontainer.json`
- **Setup Script:** `.devcontainer/setup.sh`
- **Backup Script:** `.devcontainer/backup-env.sh`

### How It Works
1. Create .env files from templates
2. Inject secrets from GitHub Codespaces
3. Configure Railway CLI
4. Install dependencies

**Runs automatically on:**
- New Codespace creation
- Container rebuild
- Manual: `bash .devcontainer/setup.sh`

---

## 🔐 Secrets Management

### Storage Locations

**GitHub Codespaces Secrets** (Recommended)
- Encrypted at rest
- Auto-injected into containers
- Managed at: https://github.com/settings/codespaces

**Railway Dashboard**
- Production environment variables
- Auto-injected in Railway services
- Managed at: https://railway.app

**Local .env Files** (Development only)
- ⚠️ Never commit to git
- Use for local development
- Created from templates

---

## 📋 Related Documentation

### Configuration
- [ENV_COMPLETE.md](../configuration/ENV_COMPLETE.md) - All env vars
- [SERVICE_MATRIX.md](../configuration/SERVICE_MATRIX.md) - Which service needs what

### Environment Setup
- [.env-checklist.md](/.env-checklist.md) - Recovery checklist
- [SESSION_016_ENV_VARS.md](../sessions/SESSION_016_ENV_VARS.md) - Original setup

### Deployment
- [RAILWAY_ACCESS_GUIDE.md](../guides/RAILWAY_ACCESS_GUIDE.md) - Railway CLI usage
- [VICTRON_ENV_SETUP.md](../deployment/VICTRON_ENV_SETUP.md) - Victron integration

---

## 🎯 Maintenance

### Regular Tasks

**Weekly:**
- [ ] Verify automated backup is working
- [ ] Test .env restore in new Codespace

**Monthly:**
- [ ] Review and update secrets
- [ ] Test full recovery procedure
- [ ] Update documentation if env vars changed

**Quarterly:**
- [ ] Rotate API keys and secrets
- [ ] Review access controls
- [ ] Audit Codespaces secrets

---

## 🆘 Emergency Contacts

**For Recovery Issues:**
1. Check this documentation first
2. Review [CODESPACES_RESILIENCE_GUIDE.md](./CODESPACES_RESILIENCE_GUIDE.md)
3. Refer to [RECOVERY_AUDIT_2025-10-17.md](./RECOVERY_AUDIT_2025-10-17.md)

**External Services:**
- Railway: https://railway.app/help
- Vercel: https://vercel.com/help
- GitHub: https://support.github.com
- OpenAI: https://help.openai.com
- Google Cloud: https://cloud.google.com/support

---

**Last Updated:** 2025-10-17
**Maintained By:** WildfireRanch Team
