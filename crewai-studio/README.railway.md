# CrewAI Studio - Railway Deployment

## Quick Deploy to Railway

### Prerequisites
- Railway account with CommandCenter project
- PostgreSQL database already running in project
- OpenAI API key

### Deployment Steps

#### 1. Create Railway Service

In your Railway project dashboard:
1. Click "New Service"
2. Select "GitHub Repo" or "Empty Service"
3. If using GitHub, select your repository
4. Set **Root Directory**: `/crewai-studio` (if monorepo)

#### 2. Configure Build

Set these in Railway service settings:

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
streamlit run app/app.py --server.headless true --server.port $PORT
```

**Watch Paths:**
```
crewai-studio/**
```

#### 3. Environment Variables

Add these variables in Railway service settings:

| Variable | Value | Notes |
|----------|-------|-------|
| `DB_URL` | `${{Postgres.DATABASE_URL}}` | References existing PostgreSQL |
| `OPENAI_API_KEY` | `sk-proj-...` | Your OpenAI API key |
| `AGENTOPS_ENABLED` | `False` | Disable AgentOps |
| `PORT` | `8501` | Streamlit default port |

**Optional Variables:**
- `GROQ_API_KEY` - For Groq LLM provider
- `ANTHROPIC_API_KEY` - For Claude models
- `SERPER_API_KEY` - For web search tools

#### 4. Networking

1. **Expose Port**: 8501
2. **Generate Domain**: Railway will auto-generate a public URL
3. **Custom Domain** (optional): Add your own domain in settings

#### 5. Deploy

1. Click "Deploy"
2. Monitor build logs
3. Wait for deployment to complete
4. Access via provided Railway URL

### Database Connection

The service automatically connects to your existing PostgreSQL database using the internal Railway network:

```
${{Postgres.DATABASE_URL}}
```

This resolves to something like:
```
postgresql://postgres:password@postgres.railway.internal:5432/commandcenter
```

**No additional database setup required!** CrewAI Studio will create its tables automatically on first run.

### Verification

After deployment:

1. **Health Check**: Visit your Railway URL
2. **Database**: Check Railway PostgreSQL for new `entities` table
3. **Create Agent**: Test by creating a simple agent in UI
4. **Run Crew**: Build and execute a basic crew

### Troubleshooting

#### Build Fails
- Check Python version (needs 3.12+)
- Verify `requirements.txt` is present
- Check build logs for specific errors

#### App Won't Start
- Ensure start command includes `--server.port $PORT`
- Verify `DB_URL` is set correctly
- Check Streamlit logs in Railway console

#### Database Connection Issues
- Confirm PostgreSQL service is running
- Verify `DB_URL` variable references PostgreSQL service
- Check database credentials

#### Port Issues
- Ensure PORT=8501 is set
- Verify start command uses `$PORT` variable
- Check Railway networking settings

### Environment Variables Template

Copy this to Railway environment variables:

```env
# Required
DB_URL=${{Postgres.DATABASE_URL}}
OPENAI_API_KEY=your-openai-api-key
AGENTOPS_ENABLED=False

# Optional
# GROQ_API_KEY=your-groq-api-key
# ANTHROPIC_API_KEY=your-anthropic-api-key
# SERPER_API_KEY=your-serper-api-key
# SCRAPFLY_API_KEY=your-scrapfly-api-key
```

### Alternative: Dockerfile Deployment

If you prefer Docker deployment:

1. Use the included `Dockerfile`
2. Railway will auto-detect and use it
3. Set environment variables as above
4. Railway handles the rest

### Resource Recommendations

**Suggested Railway Plan:**
- **Memory**: 2GB minimum (4GB recommended)
- **CPU**: Shared (1x) for basic usage
- **Storage**: Persistent volume not required (uses PostgreSQL)

### Monitoring

**Check Health:**
```bash
curl https://your-railway-url.railway.app
```

**View Logs:**
- Railway Dashboard → Service → Logs
- Real-time Streamlit output
- Database query logs (if enabled)

### Integration with CommandCenter

Once deployed, CrewAI Studio shares the PostgreSQL database with:
- MCP Server (Claude Desktop integration)
- Railway API (FastAPI backend)
- Any other services in your project

All services can access:
- Agent definitions
- Crew configurations
- Execution results
- Energy data
- Conversation history

### Security Notes

1. **API Keys**: Store in Railway environment variables (not in code)
2. **Database**: Uses Railway internal network for security
3. **Public Access**: Anyone with URL can access (add auth if needed)
4. **HTTPS**: Automatically provided by Railway

### Next Steps

After deployment:

1. **Create Solar Controller Agent**
   - Role: Solar energy monitoring and control
   - Tools: API integration, data analysis
   - Goal: Optimize energy usage

2. **Build Monitoring Crew**
   - Agents: Solar Controller, Data Analyst, Reporter
   - Tasks: Fetch data, analyze patterns, generate insights
   - Process: Sequential workflow

3. **Test Automation**
   - Schedule crew runs
   - Monitor results
   - Refine agent configurations

### Support

- [CrewAI Studio GitHub](https://github.com/strnad/CrewAI-Studio)
- [Railway Docs](https://docs.railway.app)
- [Streamlit Docs](https://docs.streamlit.io)
- [CrewAI Docs](https://docs.crewai.com)

### Cost Estimate

**Railway Resources:**
- Service: ~$5-10/month (shared plan)
- Database: Already running (no additional cost)
- Total: Minimal addition to existing infrastructure

**API Costs:**
- OpenAI: Pay-per-use (depends on agent activity)
- Optional providers: As needed

---

**Quick Deploy Checklist:**

- [ ] Railway service created
- [ ] Root directory set to `/crewai-studio`
- [ ] Build command configured
- [ ] Start command configured
- [ ] `DB_URL` environment variable set
- [ ] `OPENAI_API_KEY` set
- [ ] Port 8501 exposed
- [ ] Deployment successful
- [ ] Public URL accessible
- [ ] Database tables created
- [ ] First agent created
- [ ] Test crew run successful

**Deployment Time:** ~10-15 minutes

**Status Indicator:**
- 🟢 Green build badge = Deployed successfully
- 🔴 Red build badge = Check logs for errors
- 🟡 Yellow = Building/deploying in progress
