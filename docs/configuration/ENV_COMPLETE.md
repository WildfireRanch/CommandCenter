# Complete Environment Variables Reference

**Version:** 1.8
**Last Updated:** 2025-10-17
**Purpose:** Master reference for all environment variables across all services

---

## 📋 Table of Contents

1. [Railway Backend](#railway-backend)
2. [Vercel Frontend](#vercel-frontend)
3. [Streamlit Dashboards](#streamlit-dashboards)
4. [MCP Server](#mcp-server)
5. [Service Matrix](#service-matrix)
6. [Quick Setup](#quick-setup)

---

## 🚂 Railway Backend

**File:** `railway/.env`
**Service:** CommandCenter (FastAPI backend)

### Core Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ENV` | No | `development` | Environment name (development/production) |
| `ALLOWED_ORIGINS` | Yes | - | CORS origins (comma-separated) |

**Example:**
```bash
ENV=production
ALLOWED_ORIGINS=https://mcp.wildfireranch.us,https://dashboard.wildfireranch.us
```

### Database Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |

**Railway deployment:**
```bash
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Auto-provided
```

**Local development:**
```bash
DATABASE_URL=postgresql://user:password@localhost:5432/commandcenter
```

### AI & Embeddings

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes | - | OpenAI API key for GPT-4 and embeddings |

**Get from:** https://platform.openai.com/api-keys

### SolArk Solar Integration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SOLARK_EMAIL` | No | - | SolArk Cloud login email |
| `SOLARK_PASSWORD` | No | - | SolArk Cloud password |
| `SOLARK_PLANT_ID` | No | `146453` | SolArk plant ID |

### Knowledge Base (Google Drive)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_SERVICE_ACCOUNT_JSON` | Yes* | - | Google Cloud service account JSON |
| `GOOGLE_DOCS_KB_FOLDER_ID` | Yes* | - | Google Drive folder ID for KB |
| `INDEX_ROOT` | No | `./data/index` | Local index storage path |

*Required for KB sync functionality

**How to get:**
- Service Account: Google Cloud Console → IAM & Admin → Service Accounts → Create Key
- Folder ID: From Google Drive folder URL: `https://drive.google.com/drive/folders/FOLDER_ID`

### Google OAuth

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | Yes | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | Yes | - | Google OAuth client secret |

**Current values** (from SESSION_016):
```bash
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
```

### Victron VRM Battery Integration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `VICTRON_VRM_USERNAME` | No | - | VRM account email |
| `VICTRON_VRM_PASSWORD` | No | - | VRM account password |
| `VICTRON_INSTALLATION_ID` | No | - | VRM installation ID |
| `VICTRON_API_URL` | No | `https://vrmapi.victronenergy.com` | VRM API base URL |

**Get from:** https://vrm.victronenergy.com

### Redis Caching (V1.8)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `REDIS_URL` | No | `redis://localhost:6379` | Redis connection URL |
| `REDIS_MAX_RETRIES` | No | `3` | Max retry attempts |
| `REDIS_TIMEOUT` | No | `5` | Connection timeout (seconds) |
| `REDIS_SSL` | No | `false` | Enable SSL for Redis |

**Railway deployment:**
```bash
REDIS_URL=${{Redis.REDIS_URL}}  # Auto-provided if Redis service exists
```

### Smart Context Loading (V1.8)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONTEXT_CACHE_ENABLED` | No | `true` | Enable/disable context caching |
| `CONTEXT_CACHE_TTL` | No | `300` | Cache TTL in seconds (5 min) |
| `CONTEXT_SYSTEM_TOKENS` | No | `2000` | Token budget for system queries |
| `CONTEXT_RESEARCH_TOKENS` | No | `4000` | Token budget for research queries |
| `CONTEXT_PLANNING_TOKENS` | No | `3500` | Token budget for planning queries |
| `CONTEXT_GENERAL_TOKENS` | No | `1000` | Token budget for general queries |
| `KB_MIN_SIMILARITY` | No | `0.3` | Minimum KB relevance score (0-1) |
| `KB_MAX_DOCS_SYSTEM` | No | `1` | Max KB docs for system queries |
| `KB_MAX_DOCS_RESEARCH` | No | `5` | Max KB docs for research queries |
| `KB_MAX_DOCS_PLANNING` | No | `3` | Max KB docs for planning queries |
| `KB_MAX_DOCS_GENERAL` | No | `0` | Max KB docs for general queries |
| `KB_MAX_TOKENS_SYSTEM` | No | `500` | Max tokens for KB in system queries |
| `KB_MAX_TOKENS_RESEARCH` | No | `2000` | Max tokens for KB in research |
| `KB_MAX_TOKENS_PLANNING` | No | `1000` | Max tokens for KB in planning |
| `KB_MAX_TOKENS_GENERAL` | No | `0` | Max tokens for KB in general |
| `MAX_CONVERSATION_MESSAGES` | No | `5` | Max conversation messages |
| `MAX_CONVERSATION_TOKENS` | No | `1000` | Max tokens for conversation history |
| `CHARS_PER_TOKEN` | No | `4.0` | Chars per token estimation |
| `ALWAYS_INCLUDE_SYSTEM_CONTEXT` | No | `true` | Always include system specs |
| `SYSTEM_CONTEXT_RESERVED_TOKENS` | No | `1000` | Reserved tokens for system |
| `FALLBACK_ON_CACHE_MISS` | No | `true` | Load direct on cache miss |
| `FALLBACK_ON_ERROR` | No | `true` | Continue without cache on error |
| `TRUNCATE_ON_BUDGET_EXCEEDED` | No | `true` | Truncate intelligently |

---

## 🌐 Vercel Frontend

**File:** `vercel/.env.local`
**Service:** Next.js frontend

### Public API URLs

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | Yes | - | Railway API public URL |
| `NEXT_PUBLIC_STUDIO_URL` | Yes | - | CrewAI Studio URL |

**Production values:**
```bash
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us
```

### Google OAuth (NextAuth.js)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | Yes | - | Google OAuth client ID (same as backend) |
| `GOOGLE_CLIENT_SECRET` | Yes | - | Google OAuth client secret (same as backend) |
| `NEXTAUTH_URL` | Yes | - | Your Vercel deployment URL |
| `NEXTAUTH_SECRET` | Yes | - | NextAuth session encryption key |

**Current values** (from SESSION_016):
```bash
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=bE2tr+Az+/jG23Igu3myX2kdHUo9eJlF2/4OgUUi0B8=
```

**Generate new NEXTAUTH_SECRET:**
```bash
openssl rand -base64 32
```

### Access Control

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ALLOWED_EMAIL` | Yes | - | Email allowed to access dashboard |

**Example:**
```bash
ALLOWED_EMAIL=your-email@gmail.com
```

---

## 📊 Streamlit Dashboards

**File:** `dashboards/.env`
**Service:** Streamlit operational dashboard

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAILWAY_API_URL` | Yes | - | Railway backend API URL |
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `API_KEY` | No | - | API key if backend requires auth |

**Production values:**
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
DATABASE_URL=${{Postgres.DATABASE_URL}}  # Railway auto-provides
```

---

## 🤖 MCP Server

**File:** `mcp-server/.env`
**Service:** Claude Desktop MCP integration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `RAILWAY_API_URL` | Yes | - | Railway backend API URL |
| `API_KEY` | No | - | API key if backend requires auth |

**Production values:**
```bash
RAILWAY_API_URL=https://api.wildfireranch.us
```

---

## 🗂️ Service Matrix

### Which Service Needs What

| Variable | Railway | Vercel | Dashboards | MCP |
|----------|---------|--------|------------|-----|
| `OPENAI_API_KEY` | ✅ | ❌ | ❌ | ❌ |
| `DATABASE_URL` | ✅ | ❌ | ✅ | ❌ |
| `REDIS_URL` | ✅ | ❌ | ❌ | ❌ |
| `GOOGLE_CLIENT_ID` | ✅ | ✅ | ❌ | ❌ |
| `GOOGLE_CLIENT_SECRET` | ✅ | ✅ | ❌ | ❌ |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | ✅ | ❌ | ❌ | ❌ |
| `GOOGLE_DOCS_KB_FOLDER_ID` | ✅ | ❌ | ❌ | ❌ |
| `NEXTAUTH_SECRET` | ❌ | ✅ | ❌ | ❌ |
| `NEXTAUTH_URL` | ❌ | ✅ | ❌ | ❌ |
| `ALLOWED_EMAIL` | ❌ | ✅ | ❌ | ❌ |
| `NEXT_PUBLIC_API_URL` | ❌ | ✅ | ❌ | ❌ |
| `NEXT_PUBLIC_STUDIO_URL` | ❌ | ✅ | ❌ | ❌ |
| `RAILWAY_API_URL` | ❌ | ❌ | ✅ | ✅ |
| `SOLARK_*` | ✅ | ❌ | ❌ | ❌ |
| `VICTRON_*` | ✅ | ❌ | ❌ | ❌ |

### Priority Levels

**🔴 Critical (System won't work without):**
- `OPENAI_API_KEY` - AI/embeddings
- `DATABASE_URL` - Data persistence
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` - OAuth
- `NEXTAUTH_SECRET` - Session security

**🟡 Important (Features degraded without):**
- `GOOGLE_SERVICE_ACCOUNT_JSON` - KB sync won't work
- `GOOGLE_DOCS_KB_FOLDER_ID` - KB sync won't work
- `REDIS_URL` - Smart caching disabled (fallback works)
- `RAILWAY_API_URL` - Dashboard/MCP won't connect

**🟢 Optional (Feature-specific):**
- `SOLARK_*` - Only if using SolArk solar
- `VICTRON_*` - Only if using Victron battery
- `API_KEY` - Only if backend requires auth

---

## 🚀 Quick Setup

### From Railway Variables
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Get all variables
railway variables --service CommandCenter

# Get database URL
railway variables --service CommandCenter | grep DATABASE_URL
```

### From Google Cloud Console

**Service Account JSON:**
1. Go to: https://console.cloud.google.com
2. Navigate to: IAM & Admin → Service Accounts
3. Find: CommandCenter KB service account
4. Click: Keys → Add Key → Create new key (JSON)
5. Download and copy JSON content

**OAuth Credentials:**
1. Go to: https://console.cloud.google.com
2. Navigate to: APIs & Services → Credentials
3. Find: OAuth 2.0 Client ID
4. Copy: Client ID and Client Secret

**Google Drive Folder ID:**
1. Open your KB folder in Google Drive
2. Copy ID from URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`

### Set in Railway (Production)
```bash
# Via Railway CLI
railway variables set OPENAI_API_KEY="sk-..."
railway variables set GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account"...}'

# Or via Railway Dashboard
# https://railway.app → Your Project → Service → Variables
```

### Set in Vercel (Production)
```bash
# Via Vercel CLI
vercel env add GOOGLE_CLIENT_ID production
vercel env add GOOGLE_CLIENT_SECRET production
vercel env add NEXTAUTH_SECRET production

# Or via Vercel Dashboard
# https://vercel.com/your-project/settings/environment-variables
```

### Local Development
```bash
# Create .env files from templates
cp railway/.env.example railway/.env
cp vercel/.env.example vercel/.env.local
cp dashboards/.env.example dashboards/.env
cp mcp-server/.env.example mcp-server/.env

# Fill in values (see .env-checklist.md)
```

---

## 🔗 Related Documentation

- **Environment checklist:** [/.env-checklist.md](/.env-checklist.md)
- **Recovery guide:** [../recovery/CODESPACES_RESILIENCE_GUIDE.md](../recovery/CODESPACES_RESILIENCE_GUIDE.md)
- **Session 016 setup:** [../sessions/SESSION_016_ENV_VARS.md](../sessions/SESSION_016_ENV_VARS.md)
- **Victron setup:** [../deployment/VICTRON_ENV_SETUP.md](../deployment/VICTRON_ENV_SETUP.md)
- **Railway guide:** [../guides/RAILWAY_ACCESS_GUIDE.md](../guides/RAILWAY_ACCESS_GUIDE.md)

---

**Version:** 1.8
**Last Updated:** 2025-10-17
**Maintained By:** WildfireRanch Team
