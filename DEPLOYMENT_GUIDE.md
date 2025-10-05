# 🚀 CommandCenter Deployment Guide

Complete production deployment guide for the CommandCenter solar energy management system.

## 📋 Table of Contents

- [Architecture Overview](#architecture-overview)
- [Services](#services)
- [Deployment Steps](#deployment-steps)
- [Environment Variables](#environment-variables)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     PRODUCTION STACK                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌────────────────┐   ┌────────────────┐ │
│  │   Vercel     │   │  Railway API   │   │  Railway DB    │ │
│  │              │   │                │   │                │ │
│  │  Next.js     │──▶│  FastAPI       │──▶│  PostgreSQL    │ │
│  │  Frontend    │   │  Backend       │   │  TimescaleDB   │ │
│  │              │   │                │   │                │ │
│  └──────────────┘   └────────────────┘   └────────────────┘ │
│         │                    │                               │
│         │                    │                               │
│         ▼                    ▼                               │
│  ┌──────────────┐   ┌────────────────┐                      │
│  │  Railway     │   │  MCP Server    │                      │
│  │  CrewAI      │   │  (Port 8080)   │                      │
│  │  Studio      │   │                │                      │
│  │  (Streamlit) │   │  Claude Tools  │                      │
│  └──────────────┘   └────────────────┘                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Services

### 1. **Next.js Frontend** (Vercel)
- **URL**: https://commandcenter.vercel.app (or custom domain)
- **Framework**: Next.js 14
- **Pages**: Home, Dashboard, Chat, Operator, Energy, Logs, Status
- **Repository**: Auto-deploy from GitHub main branch

### 2. **FastAPI Backend** (Railway)
- **URL**: https://api.wildfireranch.us
- **Framework**: FastAPI + Python
- **Features**: Energy data, Agent API, Conversations
- **Database**: PostgreSQL with TimescaleDB extension

### 3. **CrewAI Studio** (Railway - To Deploy)
- **URL**: TBD (e.g., https://studio.wildfireranch.us)
- **Framework**: Streamlit
- **Purpose**: No-code AI agent and crew management

### 4. **MCP Server** (Local/Railway)
- **Port**: 8080
- **Purpose**: Claude Desktop integration
- **Features**: Energy tools, Agent interaction

---

## 📦 Deployment Steps

### Step 1: Deploy CrewAI Studio to Railway

1. **Create New Railway Service**
   ```bash
   # In Railway dashboard:
   # - Click "New Project"
   # - Select "Deploy from GitHub repo"
   # - Choose: WildfireRanch/CommandCenter
   # - Set Root Directory: /crewai-studio
   ```

2. **Configure Environment Variables**
   ```env
   OPENAI_API_KEY=your-openai-key
   DB_URL=postgresql://user:pass@postgres.railway.internal:5432/commandcenter
   AGENTOPS_ENABLED=False
   PORT=${{PORT}}  # Railway auto-assigns
   ```

3. **Verify Deployment Files**
   - `railway.json` ✅ (configured for production)
   - `Procfile` ✅ (Streamlit command)
   - `.streamlit/config.toml` ✅ (CORS, embedding settings)
   - `requirements.txt` ✅ (all dependencies)

4. **Deploy**
   - Railway will auto-detect Python
   - Uses nixpacks builder
   - Starts with: `streamlit run app/app.py --server.port $PORT`

5. **Get Public URL**
   - Copy the Railway-generated URL (e.g., `https://crewai-studio-production.up.railway.app`)
   - Or configure custom domain

### Step 2: Update Next.js Environment Variables

1. **In Vercel Dashboard**
   - Go to your project settings
   - Navigate to "Environment Variables"
   - Add the following:

   ```env
   NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
   NEXT_PUBLIC_STUDIO_URL=https://your-crewai-studio-url.railway.app
   ```

2. **Redeploy Frontend**
   - Vercel will auto-redeploy on git push
   - Or trigger manual deployment in dashboard

### Step 3: Test the Integration

1. **Frontend Pages**
   - ✅ Home: https://your-app.vercel.app/
   - ✅ Dashboard: https://your-app.vercel.app/dashboard
   - ✅ Chat: https://your-app.vercel.app/chat
   - ✅ Operator: https://your-app.vercel.app/studio
   - ✅ Energy: https://your-app.vercel.app/energy
   - ✅ Logs: https://your-app.vercel.app/logs
   - ✅ Status: https://your-app.vercel.app/status

2. **API Health**
   ```bash
   curl https://api.wildfireranch.us/health
   ```

3. **CrewAI Studio**
   - Visit studio URL directly
   - Should load without errors
   - Test agent creation

---

## 🔐 Environment Variables

### Next.js (Vercel)

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_API_URL` | `https://api.wildfireranch.us` | FastAPI backend |
| `NEXT_PUBLIC_STUDIO_URL` | `https://studio.railway.app` | CrewAI Studio |

### FastAPI (Railway)

| Variable | Value | Description |
|----------|-------|-------------|
| `DATABASE_URL` | Auto-configured by Railway | PostgreSQL connection |
| `SOLARK_API_KEY` | Your SolArk API key | Energy data access |
| `OPENAI_API_KEY` | Your OpenAI key | Agent LLM |

### CrewAI Studio (Railway)

| Variable | Value | Description |
|----------|-------|-------------|
| `OPENAI_API_KEY` | Your OpenAI key | Agent operations |
| `DB_URL` | PostgreSQL URL | Shared database |
| `PORT` | `${{PORT}}` | Railway auto-assigns |
| `AGENTOPS_ENABLED` | `False` | Disable telemetry |

---

## 🧪 Testing

### Automated Health Checks

Create a monitoring script:

```bash
#!/bin/bash
# health-check.sh

echo "🔍 Checking CommandCenter services..."

# Frontend
echo "1. Frontend (Vercel)..."
curl -s -o /dev/null -w "%{http_code}" https://your-app.vercel.app/ || echo "❌ FAILED"

# API
echo "2. Backend API..."
curl -s https://api.wildfireranch.us/health | jq .

# CrewAI Studio
echo "3. CrewAI Studio..."
curl -s -o /dev/null -w "%{http_code}" https://your-studio.railway.app/ || echo "❌ FAILED"

echo "✅ Health check complete!"
```

### Manual Testing Checklist

- [ ] Home page loads with live energy data
- [ ] Dashboard shows energy charts
- [ ] Chat sends/receives agent messages
- [ ] Operator studio loads embedded iframe
- [ ] Energy page displays power flow
- [ ] Logs shows conversations and energy data
- [ ] Status page reports all services healthy

---

## 🐛 Troubleshooting

### Issue: Operator Studio Shows "Not Available"

**Cause**: `NEXT_PUBLIC_STUDIO_URL` not set or CrewAI Studio not deployed

**Solution**:
1. Deploy CrewAI Studio to Railway (see Step 1)
2. Add `NEXT_PUBLIC_STUDIO_URL` to Vercel
3. Redeploy frontend

### Issue: Studio Iframe Blocked by CORS

**Cause**: Streamlit CORS settings

**Solution**:
Verify `.streamlit/config.toml` has:
```toml
[server]
enableCORS = false
enableXsrfProtection = false
```

### Issue: Environment Variables Not Working

**Cause**: Variables not prefixed with `NEXT_PUBLIC_` in client-side code

**Solution**:
- Server-side: Any variable name
- Client-side: Must start with `NEXT_PUBLIC_`

### Issue: Railway Port Binding

**Cause**: Streamlit not using Railway's `$PORT` variable

**Solution**:
Check `railway.json`:
```json
{
  "deploy": {
    "startCommand": "streamlit run app/app.py --server.port $PORT"
  }
}
```

---

## 📊 Monitoring

### Railway Metrics
- View in Railway dashboard
- Monitor CPU, Memory, Request rate
- Set up alerts for downtime

### Vercel Analytics
- Enable Vercel Analytics in project settings
- Track page views, performance
- Monitor build times

### Custom Health Endpoint
Add to FastAPI:
```python
@app.get("/health/full")
async def full_health_check():
    return {
        "api": "healthy",
        "database": await check_db(),
        "studio": await check_studio(),
        "timestamp": datetime.now()
    }
```

---

## 🚀 Production Checklist

- [ ] All environment variables configured
- [ ] CrewAI Studio deployed to Railway
- [ ] Vercel frontend environment updated
- [ ] Health checks passing
- [ ] Error tracking setup (Sentry, etc.)
- [ ] Database backups configured
- [ ] SSL certificates valid
- [ ] Custom domains configured
- [ ] Monitoring/alerts setup
- [ ] Documentation updated

---

## 📝 Notes

1. **Database**: Shared PostgreSQL on Railway with TimescaleDB for time-series data
2. **Secrets**: Never commit API keys - use environment variables
3. **CORS**: Disabled in Streamlit for iframe embedding
4. **Scaling**: Railway auto-scales based on traffic
5. **Costs**: Monitor Railway usage to avoid overages

---

## 🆘 Support

- **Issues**: https://github.com/WildfireRanch/CommandCenter/issues
- **Docs**: See project README.md
- **Railway**: https://railway.app/docs
- **Vercel**: https://vercel.com/docs

---

*Last Updated: 2025-10-05*
*Version: 1.0*
