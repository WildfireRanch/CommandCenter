# 🚂 Railway Deployment Setup for CrewAI Studio

## ✅ Quick Setup

### 1. Environment Variables (Required)

In Railway Dashboard → Your Service → Variables, add:

```env
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
```

**Note:** Railway automatically provides `PORT` - you don't need to set it!

### 2. Optional Variables

```env
# Database (if connecting to PostgreSQL)
DB_URL=${{Postgres.DATABASE_URL}}

# Disable AgentOps telemetry
AGENTOPS_ENABLED=False

# Additional LLM providers (optional)
GROQ_API_KEY=your-groq-key
ANTHROPIC_API_KEY=your-anthropic-key
```

---

## 🔧 How It Works

### Railway Auto-Configuration

Railway automatically:
1. ✅ Sets `PORT` environment variable (random port like 8080)
2. ✅ Exposes that port to the internet
3. ✅ Provides HTTPS with auto-SSL certificate
4. ✅ Maps your custom domain (if configured)

### Our Startup Script

The `start.sh` script:
```bash
PORT=${PORT:-8501}  # Use Railway's PORT or default to 8501
streamlit run app/app.py --server.port=$PORT ...
```

This handles Railway's `PORT` variable correctly!

---

## 🎯 Deployment Files

| File | Purpose |
|------|---------|
| `railway.toml` | Build & deploy config (in repo root) |
| `Procfile` | Process definition |
| `start.sh` | Startup wrapper script |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Streamlit configuration |

---

## 🚀 Deployment Steps

### First Time Setup

1. **Create Railway Project**
   - New Project → Deploy from GitHub
   - Repository: `WildfireRanch/CommandCenter`
   - Railway will auto-detect the config

2. **Railway Reads:**
   - `/railway.toml` (root directory config)
   - Changes to `/crewai-studio` directory
   - Runs `pip install -r requirements.txt`
   - Executes `bash start.sh`

3. **Add Environment Variables**
   - Just `OPENAI_API_KEY` is required
   - Railway provides `PORT` automatically

4. **Deploy!**
   - Railway builds and deploys
   - Get public URL: `https://your-service.up.railway.app`

### Custom Domain (Optional)

1. **In Railway:**
   - Settings → Networking → Custom Domain
   - Add: `studio.wildfireranch.us`

2. **In DNS Provider:**
   - Add CNAME record:
     ```
     Name:  studio
     Type:  CNAME
     Value: your-service.up.railway.app
     ```

3. **Wait for DNS** (5-15 minutes)

4. **Railway auto-provisions SSL** ✅

---

## 🐛 Troubleshooting

### Error: "Invalid value for '--server.port': '$PORT' is not a valid integer"

**Cause:** Railway's PORT variable not being substituted properly

**Fix:** ✅ Already fixed with `start.sh` wrapper script!

### Error: "Could not find root directory"

**Cause:** Railway looking in wrong directory

**Fix:** The `railway.toml` in repo root handles this automatically

### App not accessible on custom domain

**Cause:** DNS not propagated or CNAME incorrect

**Fix:**
- Check CNAME points to Railway URL
- Wait 15 minutes for DNS
- Test with `dig studio.wildfireranch.us`

---

## 📊 Expected Build Output

```
✓ Found railway.toml
✓ Changing to /crewai-studio
✓ Installing requirements.txt
✓ Installing crewai, streamlit, langchain...
✓ Dependencies installed
✓ Running start.sh
✓ Starting Streamlit on port 8080
✓ You can now view your Streamlit app
✓ Deployment successful!
```

---

## 🔗 Integration with Vercel

After Railway deploys successfully:

1. **Copy Railway URL** (e.g., `https://crewai-studio-production.up.railway.app`)

2. **Add to Vercel:**
   - Vercel Dashboard → Settings → Environment Variables
   - Add:
     ```
     NEXT_PUBLIC_STUDIO_URL=https://your-railway-url.up.railway.app
     ```

3. **Redeploy Vercel**

4. **Test:**
   - Visit: `https://your-vercel-site.com/studio`
   - Should show CrewAI Studio iframe! ✅

---

## 📋 Checklist

Deployment:
- [x] CrewAI Studio code in GitHub
- [x] Railway project created
- [x] Connected to GitHub repo
- [ ] Environment variable `OPENAI_API_KEY` set
- [ ] Deployment successful
- [ ] Public URL accessible

Integration:
- [ ] Railway URL copied
- [ ] Added to Vercel as `NEXT_PUBLIC_STUDIO_URL`
- [ ] Vercel redeployed
- [ ] Studio page working in production

Optional:
- [ ] Custom domain configured
- [ ] DNS CNAME added
- [ ] SSL certificate provisioned

---

## 🆘 Support

- **Railway Docs:** https://docs.railway.app
- **Streamlit Docs:** https://docs.streamlit.io
- **Issues:** https://github.com/WildfireRanch/CommandCenter/issues

---

*Last Updated: 2025-10-05*
