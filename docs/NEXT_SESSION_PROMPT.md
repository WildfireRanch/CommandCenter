# Next Session Prompt - Session 015

Copy and paste this to start your next session with Claude:

---

Hi Claude! Continuing work on **CommandCenter** - Session 015.

## Where We Left Off (Session 014 - Oct 6, 2025)

**MAJOR WINS:** 🎉
- ✅ **CrewAI Studio deployed to Railway** at https://studio.wildfireranch.us
- ✅ **Railway PORT issue resolved** (hidden service variable was the culprit)
- ✅ **embedchain dependency fixed** (pinned to >=0.1.100)
- ✅ **Cross-project database access configured** (PostgreSQL public hostname)
- ✅ **Dockerfile moved to repo root** for reliable Railway builds

**What's Working:**
- API: https://api.wildfireranch.us ✅
- Frontend: Vercel deployment ✅
- MCP Server: Vercel deployment ✅
- CrewAI Studio: https://studio.wildfireranch.us ✅
- Database: PostgreSQL + TimescaleDB (cross-project access working) ✅

**What's Almost Done:**
- Frontend `/studio` page is built and ready
- Just needs `NEXT_PUBLIC_STUDIO_URL` environment variable in Vercel
- Then redeploy and test!

## Session 015 Goals: Complete Integration & Testing 🚀

**Primary Objectives:**

### 1. Complete Frontend Integration (15 min)
- Add `NEXT_PUBLIC_STUDIO_URL=https://studio.wildfireranch.us` to Vercel
- Redeploy frontend
- Verify `/studio` page loads CrewAI Studio iframe

### 2. Comprehensive Testing (30 min)
**CrewAI Installation & Studio:**
- [ ] Test CrewAI Studio loads at https://studio.wildfireranch.us
- [ ] Verify database connectivity (PostgreSQL cross-project access)
- [ ] Test creating agents in Studio
- [ ] Test creating crews in Studio
- [ ] Verify data persistence (refresh page, data should remain)

**Frontend Accessibility:**
- [ ] Visit frontend `/studio` page
- [ ] Verify iframe embedding works
- [ ] Test "Open in New Tab" button
- [ ] Test fullscreen mode
- [ ] Confirm green "Studio Connected" banner shows

**Database Integration:**
- [ ] Check PostgreSQL for stored crew/agent data
- [ ] Verify TimescaleDB hypertables are working
- [ ] Test cross-project access from CrewAI Studio

### 3. CrewAI Studio Walkthrough (45 min)
**Guide me through:**
- Overview of CrewAI Studio interface
- How to create an agent (roles, goals, backstory, tools)
- How to create a crew (process types, agents, tasks)
- How to configure tasks and workflows
- Available tools and integrations
- LLM provider configuration (OpenAI, Anthropic, Ollama, etc.)
- Knowledge base features
- Running crews and viewing results
- Best practices for agent/crew design

**Hands-On Demo:**
- Walk me through creating a simple crew from scratch
- Explain each step and what options mean
- Show me how to run it and interpret results
- Tips for effective agent design

## Context

**Repository:** https://github.com/WildfireRanch/CommandCenter
**Documentation:** All docs in `/docs`, session summaries in `/docs/sessions/`
**Latest Session:** SESSION_014_FINAL_SUMMARY.md (comprehensive 500+ line deep-dive)

**Current Production Stack:**
- Backend: FastAPI on Railway (https://api.wildfireranch.us)
- Frontend: Next.js on Vercel
- MCP Server: Vercel deployment
- CrewAI Studio: Streamlit on Railway (https://studio.wildfireranch.us)
- Database: PostgreSQL + TimescaleDB on Railway
  - Public hostname: `postgresdb-production-e5ae.up.railway.app:5432`
  - Used for cross-project access from CrewAI Studio

**Key Learnings from Session 014:**
1. Railway service variables override everything - check dashboard first!
2. Internal hostnames (`.railway.internal`) only work within same project
3. Cross-project database requires public hostname
4. Always pin dependencies with version constraints
5. Dockerfile at repo root is safest for Railway

## Expected Deliverables

1. **Completed Integration:**
   - `NEXT_PUBLIC_STUDIO_URL` set in Vercel
   - Frontend `/studio` page fully functional
   - End-to-end testing complete

2. **Test Results:**
   - Document all test results (pass/fail)
   - Screenshot evidence of working features
   - Any issues discovered and resolved

3. **CrewAI Studio Documentation:**
   - Create user guide for CrewAI Studio features
   - Document agent/crew creation process
   - Best practices and tips
   - Example workflows

4. **Session Documentation:**
   - Session 015 summary
   - Updated progress.md (mark Phase 4 COMPLETE!)
   - Screenshots of working system

## Quick Reference

**Production URLs:**
- API: https://api.wildfireranch.us
- CrewAI Studio: https://studio.wildfireranch.us
- Frontend: (Vercel URL - will test `/studio` page)

**Database Connection String (for Studio):**
```
postgresql://postgres:1tVY3mhx1Xt3d7tvBrDKU0ZC0JO7u010bcisH25jNkg@postgresdb-production-e5ae.up.railway.app:5432/commandcenter
```

**Files to Reference:**
- [vercel/src/app/studio/page.tsx](vercel/src/app/studio/page.tsx) - Frontend Studio page
- [crewai-studio/.env](crewai-studio/.env) - Database configuration docs
- [docs/sessions/SESSION_014_FINAL_SUMMARY.md](docs/sessions/SESSION_014_FINAL_SUMMARY.md) - Comprehensive troubleshooting guide

## My Questions

I'm ready to complete the integration and learn CrewAI Studio!

**First, let's:**
1. Add the Vercel environment variable and test the integration
2. Run comprehensive tests on all components
3. Then walk me through CrewAI Studio - I want to understand how to use it effectively!

**Specific things I want to learn:**
- How do I create effective agents? What makes a good agent?
- What are the different process types for crews?
- How do I add tools to my agents?
- What LLM providers work best for different use cases?
- How does the knowledge base feature work?
- Any tips for debugging crews that don't work as expected?

Let's finish Phase 4 strong! 🚀

---

**Note:** I prefer hands-on learning with clear explanations. Show me examples and let's build something together!
