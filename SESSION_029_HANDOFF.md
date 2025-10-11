# Session 029 Handoff

**From**: Session 028 (Complete)
**To**: Session 029 (Ready to Start)
**Date**: October 11, 2025

---

## 🎯 Current Production Status

**Version**: V1.6.1
**Status**: ✅ Stable and Validated
**API**: https://api.wildfireranch.us (Healthy)
**Last Update**: October 11, 2025

### What's Working
- ✅ Context management (24KB embedded in agents)
- ✅ Manager routing (system questions → Solar Controller)
- ✅ KB Fast-Path (refined for system-specific patterns)
- ✅ Multi-turn context preservation
- ✅ All validation tests passing (4/4)

---

## 📋 Session 029 Goal

**Implement V1.7 Research Agent with Tavily MCP Integration**

### What to Build
1. **MCP Client Wrapper** (`railway/src/tools/mcp_client.py`)
   - HTTP client for Tavily MCP remote server
   - Tools: tavily-search, tavily-extract

2. **Research Agent** (`railway/src/agents/research_agent.py`)
   - Generalist with FULL 24KB context
   - Web search capability via Tavily MCP
   - For abstract/research queries

3. **Manager Routing Update** (`railway/src/agents/manager.py`)
   - Add `route_to_research_agent` tool
   - Update routing logic
   - Add to tools list

4. **API Integration** (`railway/src/api/main.py`)
   - Add Research Agent routing case
   - Handle new agent responses

5. **Testing & Validation**
   - Test queries: "What are industry best practices..."
   - Validate web search results
   - Performance benchmarking

---

## 📚 Key Documents to Reference

### Design Specification
**[docs/V1.7_RESEARCH_AGENT_DESIGN.md](docs/V1.7_RESEARCH_AGENT_DESIGN.md)**
- Complete architecture
- Implementation details
- Code examples
- Timeline: 8-12 hours

### Current Architecture
**[docs/status/Context_Docs/CONTEXT_CommandCenter_System.md](docs/status/Context_Docs/CONTEXT_CommandCenter_System.md)**
- Full system context
- Current agent structure
- Tools available

### Session 028 Results
**[docs/sessions/SESSION_028_FINAL.md](docs/sessions/SESSION_028_FINAL.md)**
- What was fixed
- Current state
- Key learnings

---

## 🔑 Environment Setup

### Required Environment Variables
```env
TAVILY_API_KEY=tvly-xxxxx     # Get from app.tavily.com (free tier)
```

### Tavily MCP Details
- **Remote Server**: https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_KEY
- **Free Tier**: 1,000 searches/month
- **Tools**: tavily-search, tavily-extract, tavily-map, tavily-crawl
- **Docs**: https://docs.tavily.com/documentation/mcp

### Python Dependencies to Add
```txt
# Add to railway/requirements.txt
mcp>=0.5.0                    # MCP SDK
httpx>=0.24.0                 # HTTP client for remote MCP
```

---

## 🏗️ Implementation Checklist

### Phase 1: Infrastructure (2-3 hours)
- [ ] Get Tavily API key (app.tavily.com)
- [ ] Add `TAVILY_API_KEY` to Railway env vars
- [ ] Install MCP client library (`pip install mcp`)
- [ ] Create `railway/src/tools/mcp_client.py`
- [ ] Test connection to Tavily MCP server
- [ ] Verify tavily-search tool works

### Phase 2: Research Agent (2-3 hours)
- [ ] Create `railway/src/agents/research_agent.py`
- [ ] Load full 24KB context via `get_context_files()`
- [ ] Add tools: KB search + Tavily search
- [ ] Write comprehensive backstory
- [ ] Create agent factory function
- [ ] Test agent creation (no routing yet)

### Phase 3: Manager Integration (1-2 hours)
- [ ] Add `route_to_research_agent` tool to Manager
- [ ] Update Manager backstory with routing rules
- [ ] Add to Manager tools list
- [ ] Update API routing logic in `main.py`
- [ ] Test routing decisions

### Phase 4: Testing (2-3 hours)
- [ ] Test abstract queries: "What are best practices..."
- [ ] Test comparison queries: "How does my system compare..."
- [ ] Test web search: "What's the latest on LiFePO4..."
- [ ] Verify source citations
- [ ] Performance benchmarking
- [ ] Cost monitoring (Tavily dashboard)

### Phase 5: Deployment (1 hour)
- [ ] Commit all changes
- [ ] Deploy to Railway (auto-deploy from main)
- [ ] Validate in production
- [ ] Update documentation
- [ ] Create V1.7 release notes

---

## 💡 Implementation Tips

### 1. Start with MCP Client Test
```python
# Quick test script
from tools.mcp_client import tavily_search

result = tavily_search("solar panel best practices 2025")
print(result)
# Should return web search results
```

### 2. Test Agent Without Routing First
```python
# Direct agent test
from agents.research_agent import create_research_agent
agent = create_research_agent()
# Verify context loaded, tools available
```

### 3. Use Tavily Remote Server (Easier)
- No need to run MCP server locally
- Just HTTP client to https://mcp.tavily.com/mcp/
- Add API key as query param

### 4. Keep Specialists Lightweight
- Solar Controller: NO web search (stays fast)
- Energy Orchestrator: NO web search (stays fast)
- Research Agent: Only agent with web search

### 5. Monitor Tavily Usage
- Check Tavily dashboard for API usage
- Free tier: 1,000 searches/month
- Expected usage: 300-600/month (should be fine)

---

## 🚨 Potential Issues & Solutions

### Issue: MCP Connection Fails
**Solution**: Use remote server URL with API key as query param
```
https://mcp.tavily.com/mcp/?tavilyApiKey=YOUR_KEY
```

### Issue: Agent Overuses Web Search
**Solution**: Update backstory with explicit instructions
```
"ONLY use web search when information is NOT in your System Context or KB"
```

### Issue: Slow Response Times
**Expected**: 20-30s for research queries (acceptable)
**If >30s**: Check Tavily API latency, may need caching

### Issue: Cost Concerns
**Monitor**: Tavily dashboard usage
**Limit**: Add query caching to reduce duplicates
**Fallback**: Rate limit web searches if needed

---

## 📊 Success Criteria

### Functional
- [ ] Research Agent routes correctly from Manager
- [ ] Web search returns relevant results
- [ ] Agent combines system context + web search
- [ ] All sources cited properly
- [ ] Response time < 30 seconds

### Quality
- [ ] Answers are accurate and actionable
- [ ] No hallucinations (all facts sourced)
- [ ] Citations include URLs
- [ ] Recommendations are specific

### Performance
- [ ] No impact on specialist agent speed
- [ ] Tavily usage within free tier
- [ ] No errors in production
- [ ] All tests passing

---

## 🎯 Session 029 Deliverables

### Code
1. `railway/src/tools/mcp_client.py` - MCP client wrapper
2. `railway/src/agents/research_agent.py` - Research Agent
3. `railway/src/agents/manager.py` - Updated routing
4. `railway/src/api/main.py` - API routing for Research Agent

### Documentation
1. V1.7 implementation notes
2. V1.7 validation results
3. Session 029 summary
4. Updated README.md

### Deployment
1. V1.7.0 deployed to Railway
2. All tests passing
3. Production validated

---

## 🔗 Quick Links

- **Design Doc**: [V1.7_RESEARCH_AGENT_DESIGN.md](docs/V1.7_RESEARCH_AGENT_DESIGN.md)
- **Session 028 Final**: [SESSION_028_FINAL.md](docs/sessions/SESSION_028_FINAL.md)
- **Project Status**: [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Tavily Docs**: https://docs.tavily.com/documentation/mcp
- **Tavily Dashboard**: https://app.tavily.com

---

## ✅ Ready to Begin

**Current State**: V1.6.1 stable in production
**Next Goal**: V1.7 Research Agent
**Estimated Time**: 8-12 hours
**Documentation**: Complete and ready

**Start Session 029 with:**
```
Implement V1.7 Research Agent as designed in docs/V1.7_RESEARCH_AGENT_DESIGN.md

Current status: V1.6.1 stable in production
Goal: Add generalist Research Agent with Tavily MCP web search
Timeline: 8-12 hours implementation

Phase 1: MCP client for Tavily (2-3h)
Phase 2: Research Agent creation (2-3h)
Phase 3: Manager routing update (1-2h)
Phase 4: Testing & validation (2-3h)
Phase 5: Deployment (1h)

See SESSION_029_HANDOFF.md for complete context.
```

---

*Handoff prepared: October 11, 2025*
*Session 028: COMPLETE ✅*
*Session 029: Ready to start 🚀*
