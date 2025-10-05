# CommandCenter Operations Dashboard

Streamlit-based multi-page dashboard for monitoring and managing your solar energy system.

## 🎯 Features

- **🏥 System Health** - Monitor API status, database connections, service uptime
- **⚡ Energy Monitor** - Real-time solar production, battery SOC, historical charts
- **🤖 Agent Chat** - Interactive chat with your Solar Controller agent
- **📊 Logs Viewer** - View conversations, energy logs, and system activity

## 🚀 Quick Start

### Local Development

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your Railway API URL and database credentials
   ```

3. **Run the dashboard**:
   ```bash
   streamlit run Home.py
   ```

4. **Access**: http://localhost:8502

### Railway Deployment

1. **Create Railway service**:
   - New Service → GitHub Repo
   - Root Directory: `/dashboards`

2. **Set environment variables**:
   ```
   RAILWAY_API_URL=https://api.wildfireranch.us
   API_KEY=your-api-key
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   ```

3. **Configure build**:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run Home.py --server.port $PORT --server.headless true`

4. **Deploy!**

## 📂 Structure

```
dashboards/
├── Home.py                    # Main dashboard/landing page
├── pages/
│   ├── 1_🏥_System_Health.py   # System monitoring
│   ├── 2_⚡_Energy_Monitor.py  # Energy visualization
│   ├── 3_🤖_Agent_Chat.py      # Agent interaction
│   └── 4_📊_Logs_Viewer.py     # Activity logs
├── components/
│   ├── api_client.py          # Railway API client
│   └── db_client.py           # PostgreSQL client
├── assets/                    # Character icons & images
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── requirements.txt           # Python dependencies
└── .env                       # Environment variables
```

## 🎨 Design

This dashboard mimics the design of your existing Next.js frontend:
- **Sidebar navigation** with character icons
- **Card-based layouts** for clean visual hierarchy
- **Real-time updates** with refresh buttons
- **Wildfire Ranch branding** consistent across pages

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `RAILWAY_API_URL` | CommandCenter API endpoint | Yes |
| `API_KEY` | API authentication key | No |
| `DATABASE_URL` | PostgreSQL connection string | Yes (for charts) |

### Database Connection

**For Railway deployment**: Use internal URL
```
DATABASE_URL=postgresql://...@postgres.railway.internal:5432/commandcenter
```

**For local development**: Use public Railway URL
```
DATABASE_URL=postgresql://...@containers-us-west-xyz.railway.app:1234/commandcenter
```

Get the public URL from: Railway Dashboard → PostgreSQL → Connect → External URL

## 📊 Pages

### 1. System Health

- API health check
- Database connection status
- Service monitoring
- Environment configuration
- Auto-refresh every 10s (optional)

### 2. Energy Monitor

- Current battery SOC, solar power, load
- Historical charts (configurable time range)
- Power flow visualization
- Energy statistics
- Insights and recommendations

### 3. Agent Chat

- Interactive chat with Solar Controller
- Session management
- Message history
- Conversation export
- Example questions

### 4. Logs Viewer

- Recent conversations
- Energy data logs
- System activity
- Database statistics
- Export functionality

## 🎯 Usage Examples

**Check System Status**:
1. Navigate to System Health
2. Verify API and database are online
3. Review service statuses

**Monitor Energy**:
1. Go to Energy Monitor
2. View current battery SOC and solar production
3. Explore historical trends (1-72 hours)
4. Check insights for recommendations

**Talk to Agent**:
1. Open Agent Chat
2. Ask: "What's my current battery level?"
3. Review response and continue conversation
4. Export chat if needed

**View Activity**:
1. Navigate to Logs Viewer
2. Select "Conversations" view
3. Browse recent sessions
4. Click a conversation to view details
5. Export data as needed

## 🚀 Deployment Options

### Option 1: Railway (Recommended)

**Pros**:
- Same platform as API and database
- Internal network access (faster, more secure)
- Auto-deploy on git push
- Easy environment variable management

**Cons**:
- Costs ~$5-10/month

### Option 2: Streamlit Cloud

**Pros**:
- Free tier available
- Streamlit-optimized hosting
- Easy deployment

**Cons**:
- Needs public database URL
- Slower database access
- Limited resources on free tier

### Option 3: Docker Local

**Pros**:
- Full control
- No hosting costs
- Good for development

**Cons**:
- Manual maintenance
- Not accessible externally

## 🔐 Security Notes

1. **API Keys**: Never commit `.env` to git
2. **Database**: Use internal Railway URL when deployed
3. **Public Access**: Anyone with URL can access (add auth if needed)
4. **HTTPS**: Automatically provided by Railway

## 🎨 Customization

### Change Colors

Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#your-color"
backgroundColor = "#your-bg"
```

### Add Pages

Create new file in `pages/`:
```python
# pages/5_🔧_New_Feature.py
import streamlit as st

st.title("🔧 New Feature")
# Your code here
```

### Modify Sidebar

Edit `Home.py` sidebar section to add/remove items

## 🐛 Troubleshooting

**Dashboard won't start**:
- Check Python version (needs 3.12+)
- Install dependencies: `pip install -r requirements.txt`
- Verify `.env` file exists

**API not connecting**:
- Verify `RAILWAY_API_URL` in `.env`
- Check Railway API is running
- Test with: `curl https://api.wildfireranch.us/health`

**Database not connecting**:
- For local dev: Use public Railway URL
- For Railway deploy: Use internal URL (`postgres.railway.internal`)
- Check PostgreSQL service is running

**No data showing**:
- Verify database has energy_snapshots table
- Check conversations exist in database
- Review Railway API logs

## 📝 Future Enhancements

- [ ] User authentication
- [ ] WebSocket real-time updates
- [ ] Custom alert configuration
- [ ] Email/SMS notifications
- [ ] Mobile-responsive improvements
- [ ] Dark mode toggle
- [ ] More chart types (Gantt, Sankey, etc.)
- [ ] Export to PDF
- [ ] Scheduled reports

## 🆘 Support

**Issues**: Create issue in CommandCenter repo
**Questions**: See main CommandCenter documentation
**Updates**: Check Railway deployment logs

---

Built with ❤️ for Wildfire Ranch
