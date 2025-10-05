# 🚀 Session 011 Prompt

Copy this to start your next session:

---

Hi Claude! Continuing work on CommandCenter - Session 011.

**Where We Left Off (Session 010):**
- ✅ CrewAI Studio installed and running locally
- ✅ Environment configured for Railway PostgreSQL
- ✅ Docker deployment configuration ready
- ✅ Comprehensive documentation created
- ✅ Local test successful (http://localhost:8501)

**Current Status:**
- API: https://api.wildfireranch.us (healthy ✅)
- Agent: Solar Controller with memory ✅
- Database: PostgreSQL + TimescaleDB ✅
- MCP Server: Ready for Claude Desktop ✅
- **CrewAI Studio: Running locally, ready for Railway deployment** ✅

**Today's Goals: Deploy CrewAI Studio & Create First Crew**

We want to deploy CrewAI Studio to Railway and build our first multi-agent crew.

**What We Need:**
1. Deploy CrewAI Studio to Railway as a service
2. Configure environment variables in Railway
3. Test Railway deployment
4. Create Solar Controller agent in CrewAI Studio GUI
5. Build a simple monitoring crew
6. Test crew execution

**Deployment Plan:**

1. **Railway Service Setup**
   - Create new service in Railway project
   - Connect to GitHub or use Dockerfile
   - Set root directory to `/crewai-studio`
   - Configure port 8501

2. **Environment Variables** (Set in Railway):
   ```
   DB_URL=${{Postgres.DATABASE_URL}}
   OPENAI_API_KEY=sk-proj-...
   AGENTOPS_ENABLED=False
   ```

3. **Build & Start Commands**:
   - Build: `pip install -r requirements.txt`
   - Start: `streamlit run app/app.py --server.headless true --server.port $PORT`

4. **First Crew Design**:
   - **Agents**: Solar Monitor, Data Analyzer, Report Generator
   - **Tasks**: Fetch data, Analyze patterns, Generate report
   - **Process**: Sequential
   - **Goal**: Automated solar monitoring report

**Context:**
- CrewAI Studio location: `/workspaces/CommandCenter/crewai-studio/`
- Documentation: `/docs/CREWAI_STUDIO_SETUP.md`
- Session summary: `/docs/sessions/SESSION_010_SUMMARY.md`
- Railway project: CommandCenter (existing)
- Database: Shared with MCP server

**Architecture Goal:**
```
Claude Desktop → MCP Server ─┐
                             ├─→ Railway API → PostgreSQL
Web Browser → CrewAI Studio ─┘
```

All agents accessible from both interfaces!

Ready to deploy and build our first crew! 🚀

---

## Quick Reference

**Local CrewAI Studio:**
```bash
cd /workspaces/CommandCenter/crewai-studio
source venv/bin/activate
streamlit run app/app.py
# Access: http://localhost:8501
```

**Railway API:** `https://api.wildfireranch.us`
**Database:** PostgreSQL on Railway (TimescaleDB enabled)
**OpenAI Key:** Already configured in .env

**Last Commit:** CrewAI Studio setup and documentation
**Next:** Railway deployment + First crew
