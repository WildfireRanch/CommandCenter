# ⚡ CommandCenter Quick Start

## 🚀 Deploy to Production (5 Minutes)

### Step 1: Deploy CrewAI Studio to Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Choose: `WildfireRanch/CommandCenter`
5. Set **Root Directory**: `/crewai-studio`
6. Add Environment Variables:
   ```env
   OPENAI_API_KEY=your-openai-api-key
   DB_URL=${{Postgres.DATABASE_URL}}
   PORT=${{PORT}}
   AGENTOPS_ENABLED=False
   ```
7. Click **"Deploy"**
8. Wait for deployment (~2 minutes)
9. Copy the generated URL (e.g., `https://crewai-studio-production.up.railway.app`)

### Step 2: Update Vercel Environment

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Select your **CommandCenter** project
3. Go to **Settings** → **Environment Variables**
4. Add/Update:
   ```env
   NEXT_PUBLIC_STUDIO_URL=https://your-crewai-studio-url.railway.app
   ```
5. Trigger **Redeploy** (or it will auto-deploy on next git push)

### Step 3: Verify

```bash
# Test all services
./scripts/health-check.sh

# Run integration tests
./scripts/test-integration.sh
```

Done! 🎉

---

## 🏠 Local Development

### Start All Services

```bash
# Terminal 1: CrewAI Studio
cd crewai-studio
streamlit run app/app.py --server.port 8501

# Terminal 2: Streamlit Ops Dashboard
cd dashboards
streamlit run Home.py --server.port 8502

# Terminal 3: Next.js Frontend
cd vercel
npm run dev

# Terminal 4: MCP Server (if needed)
cd mcp-server
python server.py
```

### Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Next.js Frontend | http://localhost:3001 | Main UI |
| CrewAI Studio | http://localhost:8501 | Agent builder |
| Ops Dashboard | http://localhost:8502 | Admin panel |
| FastAPI Backend | https://api.wildfireranch.us | API |
| MCP Server | http://localhost:8080 | Claude tools |

---

## 📋 Quick Commands

### Health Checks
```bash
# Check all services
./scripts/health-check.sh

# Test API only
curl https://api.wildfireranch.us/health | jq

# Test energy data
curl https://api.wildfireranch.us/energy/latest | jq
```

### Development
```bash
# Build frontend
cd vercel && npm run build

# Run tests
./scripts/test-integration.sh

# Check git status
git status

# Deploy
git add . && git commit -m "Update" && git push
```

### Database
```bash
# Connect to Railway PostgreSQL
railway run psql $DATABASE_URL

# Run migrations
cd railway && python run_migration.py
```

---

## 🔐 Environment Variables

### Required for Production

**Vercel (Next.js):**
```env
NEXT_PUBLIC_API_URL=https://api.wildfireranch.us
NEXT_PUBLIC_STUDIO_URL=https://studio.railway.app
```

**Railway (FastAPI):**
```env
DATABASE_URL=postgresql://...  # Auto-configured
SOLARK_API_KEY=your-solark-key
OPENAI_API_KEY=your-openai-key
```

**Railway (CrewAI Studio):**
```env
OPENAI_API_KEY=your-openai-key
DB_URL=${{Postgres.DATABASE_URL}}
PORT=${{PORT}}
AGENTOPS_ENABLED=False
```

---

## 🧪 Testing Checklist

- [ ] Frontend home page loads with energy data
- [ ] Dashboard shows energy charts
- [ ] Chat interface sends/receives messages
- [ ] Operator studio loads (iframe)
- [ ] Energy page displays power flow
- [ ] Logs show conversations and data
- [ ] Status page reports all services healthy
- [ ] Health check script passes
- [ ] Integration tests pass

---

## 🐛 Quick Troubleshooting

### Operator Studio shows "Not Available"
**Fix:** Deploy CrewAI Studio to Railway and set `NEXT_PUBLIC_STUDIO_URL`

### API returning 500 errors
**Fix:** Check Railway logs, verify DATABASE_URL is set

### Frontend not showing data
**Fix:** Verify `NEXT_PUBLIC_API_URL` is correct in Vercel

### Build failing
**Fix:** Run `npm run build` locally to see errors

### Railway deployment failing
**Fix:** Check `railway.json` and `Procfile` are correct

---

## 📚 Documentation

- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Complete deployment steps
- **[Architecture](ARCHITECTURE.md)** - System architecture
- **[Session Summary](SESSION_011_SUMMARY.md)** - What we built
- **[Session Prompt](docs/sessions/SESSION_011_PROMPT.md)** - Next session starter

---

## 🆘 Emergency Commands

```bash
# Restart Next.js dev server
cd vercel && npm run dev

# Restart CrewAI Studio
cd crewai-studio && streamlit run app/app.py --server.port 8501

# Check Railway services
railway status

# View Railway logs
railway logs

# Force Vercel redeploy
vercel --prod --force
```

---

## 🎯 Production Checklist

- [x] All 7 Next.js pages built
- [x] CrewAI Studio configured for Railway
- [x] Environment variables documented
- [x] Health check scripts created
- [x] Integration tests written
- [x] Documentation complete
- [ ] CrewAI Studio deployed to Railway
- [ ] Vercel environment updated
- [ ] Production health checks passing
- [ ] Monitoring alerts configured

---

## 🔗 Useful Links

- **Railway**: https://railway.app/dashboard
- **Vercel**: https://vercel.com/dashboard
- **API Docs**: https://api.wildfireranch.us/docs
- **GitHub**: https://github.com/WildfireRanch/CommandCenter
- **Issues**: https://github.com/WildfireRanch/CommandCenter/issues

---

*Quick Start Guide - Last Updated: 2025-10-05*
