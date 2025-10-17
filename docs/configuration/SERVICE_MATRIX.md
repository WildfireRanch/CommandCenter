# Service Configuration Matrix

**Version:** 1.8
**Last Updated:** 2025-10-17
**Purpose:** Quick reference for which services need which configuration

---

## 📊 Environment Variable Matrix

### Complete Matrix

| Variable | Railway Backend | Vercel Frontend | Dashboards | MCP Server | Priority |
|----------|----------------|-----------------|------------|------------|----------|
| **Core** |
| `ENV` | ✅ | ❌ | ❌ | ❌ | 🟡 |
| `ALLOWED_ORIGINS` | ✅ | ❌ | ❌ | ❌ | 🟡 |
| **Database** |
| `DATABASE_URL` | ✅ | ❌ | ✅ | ❌ | 🔴 |
| **AI/Embeddings** |
| `OPENAI_API_KEY` | ✅ | ❌ | ❌ | ❌ | 🔴 |
| **Google OAuth** |
| `GOOGLE_CLIENT_ID` | ✅ | ✅ | ❌ | ❌ | 🔴 |
| `GOOGLE_CLIENT_SECRET` | ✅ | ✅ | ❌ | ❌ | 🔴 |
| **NextAuth** |
| `NEXTAUTH_URL` | ❌ | ✅ | ❌ | ❌ | 🔴 |
| `NEXTAUTH_SECRET` | ❌ | ✅ | ❌ | ❌ | 🔴 |
| `ALLOWED_EMAIL` | ❌ | ✅ | ❌ | ❌ | 🟡 |
| **Frontend URLs** |
| `NEXT_PUBLIC_API_URL` | ❌ | ✅ | ❌ | ❌ | 🔴 |
| `NEXT_PUBLIC_STUDIO_URL` | ❌ | ✅ | ❌ | ❌ | 🟡 |
| **Knowledge Base** |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ | ❌ | ❌ | ❌ | 🟡 |
| `GOOGLE_DOCS_KB_FOLDER_ID` | ✅ | ❌ | ❌ | ❌ | 🟡 |
| `INDEX_ROOT` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| **Redis/Caching** |
| `REDIS_URL` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `REDIS_MAX_RETRIES` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `REDIS_TIMEOUT` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `REDIS_SSL` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| **Smart Context (V1.8)** |
| `CONTEXT_CACHE_ENABLED` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `CONTEXT_*_TOKENS` (4 vars) | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `KB_*` (12 vars) | ✅ | ❌ | ❌ | ❌ | 🟢 |
| **SolArk Solar** |
| `SOLARK_EMAIL` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `SOLARK_PASSWORD` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `SOLARK_PLANT_ID` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| **Victron Battery** |
| `VICTRON_VRM_USERNAME` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `VICTRON_VRM_PASSWORD` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `VICTRON_INSTALLATION_ID` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| `VICTRON_API_URL` | ✅ | ❌ | ❌ | ❌ | 🟢 |
| **Dashboard/MCP** |
| `RAILWAY_API_URL` | ❌ | ❌ | ✅ | ✅ | 🟡 |
| `API_KEY` | ❌ | ❌ | ✅ | ✅ | 🟢 |

**Priority Legend:**
- 🔴 **Critical** - Service won't function without
- 🟡 **Important** - Feature degraded without
- 🟢 **Optional** - Feature-specific or has fallback

---

## 🚂 Railway Backend (CommandCenter)

### Critical Variables (Must Have)
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}
OPENAI_API_KEY=sk-proj-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

### Important Variables (For Full Functionality)
```bash
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
GOOGLE_DOCS_KB_FOLDER_ID=1abc123xyz
ALLOWED_ORIGINS=https://mcp.wildfireranch.us,https://dashboard.wildfireranch.us
```

### Optional Variables (Feature-Specific)
```bash
# Redis caching (V1.8)
REDIS_URL=${{Redis.REDIS_URL}}

# SolArk solar (if using)
SOLARK_EMAIL=...
SOLARK_PASSWORD=...
SOLARK_PLANT_ID=146453

# Victron battery (if using)
VICTRON_VRM_USERNAME=...
VICTRON_VRM_PASSWORD=...
VICTRON_INSTALLATION_ID=...

# Smart context tuning (V1.8 - has defaults)
CONTEXT_CACHE_ENABLED=true
CONTEXT_SYSTEM_TOKENS=2000
# ... (see ENV_COMPLETE.md for full list)
```

### What Breaks Without Each Variable

| Missing Variable | Impact | Workaround |
|-----------------|--------|------------|
| `DATABASE_URL` | ❌ Complete failure - API won't start | None - must have |
| `OPENAI_API_KEY` | ❌ AI features fail, KB search broken | None - must have |
| `GOOGLE_CLIENT_ID/SECRET` | ❌ OAuth fails, frontend auth broken | None - must have |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ⚠️ KB sync fails | Can browse existing KB |
| `GOOGLE_DOCS_KB_FOLDER_ID` | ⚠️ KB sync fails | Can browse existing KB |
| `REDIS_URL` | ⚠️ Smart caching disabled | Falls back to direct loading |
| `SOLARK_*` | ⚠️ Solar data unavailable | Other features work |
| `VICTRON_*` | ⚠️ Battery data unavailable | Other features work |

---

## 🌐 Vercel Frontend

### Critical Variables (Must Have)
```bash
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=...
```

### Important Variables (For Full Functionality)
```bash
ALLOWED_EMAIL=your-email@gmail.com
NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us
```

### What Breaks Without Each Variable

| Missing Variable | Impact | Workaround |
|-----------------|--------|------------|
| `NEXT_PUBLIC_API_URL` | ❌ Complete failure - can't connect to backend | None - must have |
| `GOOGLE_CLIENT_ID/SECRET` | ❌ OAuth fails, can't login | None - must have |
| `NEXTAUTH_URL` | ❌ Auth redirect fails | None - must have |
| `NEXTAUTH_SECRET` | ❌ Session encryption fails | None - must have |
| `ALLOWED_EMAIL` | ⚠️ Anyone with Google can login | Security risk |
| `NEXT_PUBLIC_STUDIO_URL` | ⚠️ Studio page broken | Other pages work |

---

## 📊 Streamlit Dashboards

### Critical Variables (Must Have)
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

### Optional Variables
```bash
API_KEY=...  # Only if backend requires authentication
```

### What Breaks Without Each Variable

| Missing Variable | Impact | Workaround |
|-----------------|--------|------------|
| `RAILWAY_API_URL` | ❌ Can't connect to backend | None - must have |
| `DATABASE_URL` | ❌ Direct DB queries fail | Can use API only |
| `API_KEY` | ⚠️ Auth fails if backend requires | Only if enabled |

---

## 🤖 MCP Server (Claude Desktop)

### Critical Variables (Must Have)
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
```

### Optional Variables
```bash
API_KEY=...  # Only if backend requires authentication
```

### What Breaks Without Each Variable

| Missing Variable | Impact | Workaround |
|-----------------|--------|------------|
| `RAILWAY_API_URL` | ❌ Can't connect to backend | None - must have |
| `API_KEY` | ⚠️ Auth fails if backend requires | Only if enabled |

---

## 🔄 Deployment Scenarios

### Scenario 1: Full Production Deployment

**Services:** Railway Backend + Vercel Frontend + Dashboards + MCP

**Railway Backend:**
```bash
# Critical (from Railway auto-config)
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Critical (add manually)
OPENAI_API_KEY=sk-proj-...
GOOGLE_CLIENT_ID=643270983147-...
GOOGLE_CLIENT_SECRET=GOCSPX-...

# Important (KB functionality)
GOOGLE_SERVICE_ACCOUNT_JSON={"type":"service_account"...}
GOOGLE_DOCS_KB_FOLDER_ID=1abc123xyz

# Optional (if using)
SOLARK_EMAIL=...
VICTRON_VRM_USERNAME=...
```

**Vercel Frontend:**
```bash
# All critical
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us
GOOGLE_CLIENT_ID=643270983147-...
GOOGLE_CLIENT_SECRET=GOCSPX-...
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=bE2tr+Az+...
ALLOWED_EMAIL=your@email.com
```

### Scenario 2: Local Development

**Railway Backend (Local):**
```bash
# Get from Railway
DATABASE_URL=postgresql://...  # From railway variables
REDIS_URL=redis://localhost:6379  # Local Redis

# Add your keys
OPENAI_API_KEY=sk-proj-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_SERVICE_ACCOUNT_JSON=...
GOOGLE_DOCS_KB_FOLDER_ID=...

# Local settings
ENV=development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

**Vercel Frontend (Local):**
```bash
# Point to local backend
NEXT_PUBLIC_API_URL=http://localhost:8000

# Or point to Railway backend
# NEXT_PUBLIC_API_URL=https://api.wildfireranch.us

# OAuth (same as production)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=...
ALLOWED_EMAIL=your@email.com
```

### Scenario 3: Minimal Setup (Backend Only)

**Use case:** Testing API without frontend

**Railway Backend:**
```bash
# Absolute minimum
DATABASE_URL=${{Postgres.DATABASE_URL}}
OPENAI_API_KEY=sk-proj-...

# Optional (for KB)
GOOGLE_SERVICE_ACCOUNT_JSON=...
GOOGLE_DOCS_KB_FOLDER_ID=...
```

**Result:**
- ✅ API endpoints work
- ✅ Agent chat works (via API)
- ✅ Energy data works
- ❌ No frontend UI
- ❌ No OAuth
- ⚠️ KB sync works if Google vars provided

---

## 🎯 Quick Validation

### Check Railway Backend
```bash
# Health check
curl https://api.wildfireranch.us/health

# Should return:
# {"status":"healthy","checks":{
#   "api":"ok",
#   "openai_configured":true,
#   "solark_configured":true/false,
#   "database_configured":true,
#   "database_connected":true
# }}
```

### Check Vercel Frontend
```bash
# Health check
curl -I https://mcp.wildfireranch.us

# Should return: 200 OK

# Test OAuth (browser)
# Visit: https://mcp.wildfireranch.us
# Should redirect to Google login
```

### Check Dashboards
```bash
# Health check
curl -I https://dashboard.wildfireranch.us

# Should return: 200 OK
```

### Check MCP Server
```bash
# Test in Claude Desktop
# Use command: /ask what's my battery level?
# Should return response from Railway backend
```

---

## 🔗 Related Documentation

- **Complete env reference:** [ENV_COMPLETE.md](./ENV_COMPLETE.md)
- **Environment checklist:** [/.env-checklist.md](/.env-checklist.md)
- **Recovery guide:** [../recovery/CODESPACES_RESILIENCE_GUIDE.md](../recovery/CODESPACES_RESILIENCE_GUIDE.md)
- **Railway guide:** [../guides/RAILWAY_ACCESS_GUIDE.md](../guides/RAILWAY_ACCESS_GUIDE.md)

---

**Version:** 1.8
**Last Updated:** 2025-10-17
**Maintained By:** WildfireRanch Team
