# 🚀 Quick Start - Your Dashboards

## ✅ What's Running Now

| Dashboard | Port | URL | Purpose |
|-----------|------|-----|---------|
| **Ops Dashboard** | 8502 | http://localhost:8502 | System monitoring, energy, chat, logs |
| **CrewAI Studio** | 8501 | http://localhost:8501 | Agent management GUI |

## 🎯 First Steps

### 1. Open Ops Dashboard
```bash
# Already running! Just open in browser:
http://localhost:8502
```

**Try This**:
1. Click "🏥 System Health" → See API and database status
2. Click "⚡ Energy Monitor" → View solar production charts
3. Click "🤖 Agent Chat" → Ask: "What's my battery level?"
4. Click "📊 Logs" → Browse recent conversations

### 2. Open CrewAI Studio
```bash
# Already running! Just open in browser:
http://localhost:8501
```

**Try This**:
1. Go to "My Agents" → Create your first agent
2. Go to "My Tasks" → Define a task
3. Go to "My Crews" → Build a crew
4. Run your first multi-agent workflow!

## 🔄 Restart Commands

If you need to restart either dashboard:

```bash
# Stop all Streamlit apps
pkill -f streamlit

# Start Ops Dashboard
cd /workspaces/CommandCenter/dashboards
streamlit run Home.py --server.port 8502 &

# Start CrewAI Studio
cd /workspaces/CommandCenter/crewai-studio
source venv/bin/activate
streamlit run app/app.py --server.port 8501 &
```

## 📚 Full Documentation

- **Ops Dashboard**: `/dashboards/README.md`
- **CrewAI Studio**: `/crewai-studio/QUICKSTART.md`
- **Deployment**: `/docs/DASHBOARD_COMPLETE.md`
- **Frontend Analysis**: `/docs/frontend-analysis/FRONTEND_AUDIT.md`

## 🚀 Deploy to Railway

See: `/dashboards/README.md#railway-deployment`

**Quick version**:
1. Create Railway service
2. Root directory: `/dashboards`
3. Add environment variables
4. Deploy!

## 🎨 Your Character Icons

All preserved in `/dashboards/assets/`:
- WildfireMang.png (logo)
- Hoody.png
- Echo.png
- PigTails.png
- And 11 more!

## 💡 Tips

- **Auto-refresh**: Enable in System Health page for live monitoring
- **Export data**: Use export buttons in Energy Monitor and Logs
- **Chat history**: Each conversation gets a unique session ID
- **Time range**: Adjust in Energy Monitor to see 1-72 hours of data

## 🆘 Troubleshooting

**Dashboard not loading?**
```bash
# Check if it's running
ps aux | grep streamlit

# Restart it
cd /workspaces/CommandCenter/dashboards
streamlit run Home.py
```

**No data showing?**
- Check Railway API is running: `curl https://api.wildfireranch.us/health`
- Verify database connection in System Health page
- Check `.env` file has correct DATABASE_URL

---

**Built**: Session 010
**Status**: ✅ Ready to use!
**Next**: Deploy to Railway (Session 011)
