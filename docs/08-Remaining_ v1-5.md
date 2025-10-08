# CommandCenter V1.5 Execution Plan
**Goal:** Ship a working, intelligent system with KB + agents
**Timeline:** 3 focused sessions (~15-20 hours)
**Approach:** Test, Build, Polish, Ship

---

## 🎯 V1.5 Scope (What We're Finishing)

### ✅ Must Finish:
1. **Test & validate KB system** - Verify everything works
2. **Build Energy Orchestrator agent** - Planning & coordination
3. **Polish chat interface** - Better UX, show sources
4. **End-to-end testing** - Everything working together

### ⏳ Defer to V2:
- Additional hardware tools (Shelly, Miners, Victron)
- Auto-sync scheduler
- Settings backend
- Authentication system
- Real-time WebSocket updates
- Energy charts visualization

---

## 📋 Session-by-Session Breakdown

## **Session 1: KB Testing & Validation** (3-4 hours)

### Part 1: Claude Code Codebase Audit (30 min)
**Objective:** Understand what actually exists in the code

**Instructions for Claude Code:**
```
Hi Claude Code! I need you to audit the entire CommandCenter codebase to understand what's actually implemented.

Repository: /workspaces/CommandCenter (or wherever you have it)

Please walk through and document:

1. **Backend API (Railway):**
   - What endpoints exist in railway/src/api/main.py?
   - What agents exist in railway/src/agents/?
   - What tools exist in railway/src/tools/?
   - What KB endpoints exist?
   - Database schema - what tables?

2. **Frontend (Vercel):**
   - What pages exist in vercel/src/app/?
   - What components in vercel/src/components/?
   - How is KB integrated?
   - What's the chat interface like?

3. **Database:**
   - Check railway/src/utils/db.py - what functions?
   - What's the schema initialization look like?

4. **Configuration:**
   - Environment variables used
   - API keys needed
   - Railway vs Vercel deployment configs

Create a markdown file: `docs/CODEBASE_AUDIT_OCT2025.md` with findings.

Focus on: What exists, what works, what's incomplete.
```

**Expected Output:**
- Complete codebase inventory
- List of working features
- List of incomplete features
- Clear picture of current state

---

### Part 2: KB System Testing (2-3 hours)

**Objective:** Verify KB system works end-to-end

#### Step 1: Test OAuth Flow (30 min)

**Instructions for You:**
1. Open https://mcp.wildfireranch.us/kb
2. Click "Sign in with Google"
3. Verify redirect to Google
4. Verify redirect back to site
5. Verify you're logged in
6. Check browser DevTools Console for errors
7. Screenshot any issues

**If OAuth fails:**
```
Claude Code, the OAuth flow failed. Here's the error: [paste error]

Please:
1. Check vercel/src/app/api/auth/[...nextauth]/route.ts
2. Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in Vercel env
3. Check NEXTAUTH_URL is set correctly
4. Fix any issues found
```

#### Step 2: Test Preview Mode (30 min)

**Instructions for You:**
1. In KB dashboard, click "Preview" button
2. Verify it shows your Google Drive folders
3. Check that CONTEXT folder is marked "Tier 1"
4. Verify file counts and token estimates
5. Screenshot the preview

**Instructions for Claude Code (if needed):**
```
Claude Code, I need to test the preview endpoint manually.

1. Check railway/src/api/kb.py - find the preview endpoint
2. Show me how to call it with curl using my access token
3. Help me extract my access token from browser cookies
4. Run the preview and show me the output
```

#### Step 3: Test Full Sync (1-1.5 hours)

**Instructions for You:**
1. Click "Full Sync" button
2. Watch real-time progress modal
3. Verify:
   - Progress updates in real-time
   - Files being processed shown
   - No errors in console
   - Sync completes successfully
   - Stats update after sync

**If sync fails:**
```
Claude Code, the sync failed with error: [paste error]

Please:
1. Check Railway logs: `railway logs`
2. Find the error in railway/src/api/kb.py
3. Check if GOOGLE_DOCS_KB_FOLDER_ID is set correctly
4. Fix the bug
5. Redeploy: `git add . && git commit -m "Fix: KB sync bug" && git push`
```

#### Step 4: Test Agent KB Search (30 min)

**Instructions for Claude Code:**
```
Claude Code, I need to test if the Solar Controller agent can search the KB.

1. Find the agent file: railway/src/agents/solar_controller.py
2. Verify it has the KB search tool imported
3. Show me how to ask the agent a question that requires KB search
4. Test via the /ask endpoint

Example test:
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the operating procedures for the solar system?"}'

Expected: Agent should search KB, find relevant docs, cite sources in response.
```

**Validation checklist:**
- [ ] Agent searches KB successfully
- [ ] Agent cites sources (shows document names)
- [ ] Response is relevant to query
- [ ] No errors in Railway logs

---

### Part 3: Document Findings (30 min)

**Instructions for Claude Code:**
```
Claude Code, create a test report:

File: docs/KB_TESTING_RESULTS.md

Document:
1. What was tested
2. What worked perfectly
3. What had issues
4. What needs fixing
5. Overall KB system status

Format as a clear pass/fail report with recommendations.
```

---

## **Session 2: Energy Orchestrator Agent** (6-8 hours)

### Part 1: Design the Agent (1 hour)

**Instructions for Claude Code:**
```
Claude Code, I need to create a new agent: Energy Orchestrator

Requirements:
- Plans energy actions based on SOC, time, weather
- Coordinates with Solar Controller agent
- Makes decisions about miner usage
- Optimizes battery charging/discharging
- Can pause/resume miners during low energy

Create a design document first: docs/ENERGY_ORCHESTRATOR_DESIGN.md

Include:
1. Agent role and backstory
2. Tools needed (what actions can it take?)
3. Integration with Solar Controller
4. Decision-making logic
5. Safety guardrails

Reference the old Relay stack docs if helpful for concepts.
```

**Review the design together before building**

---

### Part 2: Build Required Tools (2-3 hours)

**Instructions for Claude Code:**
```
Claude Code, based on the design doc, create these tools:

1. **Battery Optimizer Tool** (railway/src/tools/battery_optimizer.py)
   - Input: Current SOC, time of day, weather forecast
   - Output: Recommended charge/discharge action
   - Logic: Prioritize battery during peak rates, charge during off-peak

2. **Miner Coordinator Tool** (railway/src/tools/miner_coordinator.py)
   - Input: Available power, current load
   - Output: Miner on/off recommendations
   - Logic: Pause miners when SOC < 40%, resume when SOC > 60%

3. **Energy Planner Tool** (railway/src/tools/energy_planner.py)
   - Input: 24-hour forecast, current state
   - Output: Hour-by-hour action plan
   - Logic: Optimize for cost and battery health

Each tool should:
- Have @tool decorator
- Include dry_run mode
- Have clear docstrings
- Return structured data
- Log all decisions

Test each tool individually before integration.
```

---

### Part 3: Create the Agent (2 hours)

**Instructions for Claude Code:**
```
Claude Code, create the Energy Orchestrator agent:

File: railway/src/agents/energy_orchestrator.py

Based on CrewAI patterns, create an agent with:

1. **Role:** "Energy System Planner and Coordinator"

2. **Backstory:** 
   "You are responsible for optimizing energy usage at a solar-powered 
   off-grid ranch. You coordinate between the solar controller, battery 
   system, and bitcoin miners to maximize efficiency while ensuring 
   reliable power. You make decisions based on current SOC, time of day, 
   weather forecasts, and operational priorities."

3. **Tools:**
   - battery_optimizer
   - miner_coordinator  
   - energy_planner
   - KB search (for learning operational procedures)

4. **Integration:**
   - Can delegate to Solar Controller agent
   - Receives queries from main orchestration layer
   - Logs all decisions to database

5. **Safety:**
   - Never discharge battery below 20%
   - Always confirm before major changes
   - Dry-run mode by default for new actions

Follow the same pattern as solar_controller.py but adapt for orchestrator role.
```

---

### Part 4: Test & Deploy (1-2 hours)

**Instructions for Claude Code:**
```
Claude Code, let's test the Energy Orchestrator:

1. **Unit Test Each Tool:**
   - Test battery_optimizer with various SOC levels
   - Test miner_coordinator with different power scenarios
   - Test energy_planner with sample forecasts

2. **Test Agent Integration:**
   - Ask it: "What's the energy plan for today?"
   - Ask it: "Should we run the miners right now?"
   - Ask it: "Optimize battery charging for tonight"

3. **Test Agent Coordination:**
   - Ask a question that requires both Solar Controller and Orchestrator
   - Example: "Check solar status and create an energy plan"

4. **Deploy to Railway:**
   git add .
   git commit -m "Add: Energy Orchestrator agent with planning tools"
   git push

5. **Verify in production:**
   - Check Railway deployment logs
   - Test via API endpoint
   - Verify database logging

Create: docs/ENERGY_ORCHESTRATOR_TESTING.md with results
```

---

## **Session 3: Frontend Polish & Final Testing** (4-6 hours)

### Part 1: Improve Chat Interface (2-3 hours)

**Instructions for Claude Code:**
```
Claude Code, let's polish the chat interface:

File: vercel/src/components/ChatInterface.tsx (or wherever it is)

Improvements needed:

1. **Show Agent Status:**
   - Display which agent is responding
   - Show "thinking..." indicator
   - Show "searching knowledge base..." when KB queried

2. **Display Sources:**
   - When agent cites KB sources, show them as clickable links
   - Format like: "According to [Solar Operations Manual] ..."
   - Add citation tooltip showing exact passage

3. **Better Message Display:**
   - User messages: right-aligned, blue background
   - Agent messages: left-aligned, grey background
   - Sources: below agent message, collapsible section

4. **Loading States:**
   - Skeleton loader while waiting
   - Typing indicator animation
   - Progress bar for long operations

5. **Error Handling:**
   - Clear error messages
   - Retry button for failed queries
   - Helpful suggestions for common errors

Reference modern chat UI patterns (like ChatGPT, Claude.ai) for UX.
```

---

### Part 2: Add Agent Selector (1 hour)

**Instructions for Claude Code:**
```
Claude Code, add an agent selector to the chat interface:

Dropdown or tabs to choose:
- Solar Controller (default)
- Energy Orchestrator  
- Both (auto-route based on query)

Store selection in state, pass to API endpoint.

Update API to handle agent selection:
- POST /ask with "agent": "solar" | "orchestrator" | "auto"
- Auto mode: Classify query and route to appropriate agent
```

---

### Part 3: End-to-End Testing (1-2 hours)

**Instructions for You + Claude Code:**

**Test Scenarios:**

1. **Solar Status Query:**
   - Ask: "What's the current solar system status?"
   - Expected: Solar Controller responds with current data

2. **KB Search Query:**
   - Ask: "What are the maintenance procedures for the solar panels?"
   - Expected: Agent searches KB, cites relevant documents

3. **Planning Query:**
   - Ask: "Should we run the miners tonight?"
   - Expected: Orchestrator analyzes SOC, weather, creates plan

4. **Multi-Agent Query:**
   - Ask: "Check solar status and create an energy plan for today"
   - Expected: Both agents coordinate, provide comprehensive response

5. **Error Handling:**
   - Ask an ambiguous question
   - Expected: Agent asks for clarification

6. **Memory Test:**
   - Ask: "What did we discuss about the solar system yesterday?"
   - Expected: Agent recalls previous conversation

**For each test:**
- [ ] Response is accurate
- [ ] Response time < 5 seconds
- [ ] Sources cited correctly
- [ ] No errors in console
- [ ] Database logging works

**Instructions for Claude Code:**
```
Claude Code, create automated tests for these scenarios:

File: tests/test_integration.py

Use pytest to test:
- Each API endpoint
- Each agent response
- KB search functionality
- Database persistence
- Error handling

Run: pytest tests/test_integration.py -v
```

---

### Part 4: Performance Check (30 min)

**Instructions for Claude Code:**
```
Claude Code, check performance:

1. Response time analysis:
   - Measure time for each endpoint
   - Target: < 3 seconds for simple queries
   - Target: < 10 seconds for KB queries

2. Database query optimization:
   - Check slow queries in logs
   - Add indexes if needed

3. Memory usage:
   - Railway metrics dashboard
   - Should be < 512MB

4. Error rate:
   - Check Railway logs
   - Should be < 1% of requests

Document findings in: docs/PERFORMANCE_METRICS.md
```

---

### Part 5: Final Deployment (30 min)

**Pre-deployment checklist:**
- [ ] All tests passing
- [ ] KB system validated
- [ ] Both agents working
- [ ] Chat interface polished
- [ ] No critical errors in logs
- [ ] Documentation updated

**Instructions for Claude Code:**
```
Claude Code, prepare for V1.5 release:

1. Update version number in package.json and requirements.txt

2. Create comprehensive README updates:
   - What's new in V1.5
   - How to use each feature
   - Troubleshooting guide

3. Create deployment checklist:
   docs/V15_DEPLOYMENT_CHECKLIST.md

4. Tag the release:
   git tag -a v1.5.0 -m "Release V1.5: KB + Energy Orchestrator"
   git push origin v1.5.0

5. Update progress.md:
   - Mark V1.5 complete
   - Document what was achieved
   - Note what's deferred to V2
```

---

## 🎯 Success Criteria for V1.5

**Ship when ALL of these are true:**

### KB System:
- [ ] ✅ OAuth login works
- [ ] ✅ Full sync completes without errors
- [ ] ✅ Smart sync detects changes correctly
- [ ] ✅ Agent can search KB successfully
- [ ] ✅ Sources are cited in responses
- [ ] ✅ All files in CONTEXT folder loaded

### Agents:
- [ ] ✅ Solar Controller responds accurately
- [ ] ✅ Energy Orchestrator makes sensible plans
- [ ] ✅ Agents can coordinate when needed
- [ ] ✅ KB search integrated with agents
- [ ] ✅ Agents remember conversation context

### Frontend:
- [ ] ✅ Chat interface is polished
- [ ] ✅ Agent status shown clearly
- [ ] ✅ Sources displayed and clickable
- [ ] ✅ Loading states work smoothly
- [ ] ✅ Error messages are helpful
- [ ] ✅ Agent selector works

### Technical:
- [ ] ✅ All tests passing
- [ ] ✅ Response times acceptable
- [ ] ✅ Database logging working
- [ ] ✅ No memory leaks
- [ ] ✅ Error rate < 1%
- [ ] ✅ Documentation complete

### User Experience:
- [ ] ✅ Can have natural conversation with agents
- [ ] ✅ Agents provide helpful, accurate responses
- [ ] ✅ Sources make responses trustworthy
- [ ] ✅ System is reliable and fast
- [ ] ✅ Easy to use without technical knowledge

---

## 📝 Session Format

### At Start of Each Session:

**Prompt for Claude Code:**
```
Hi Claude Code! I'm working on CommandCenter V1.5 - Session [X] of 3.

Current status: [paste relevant section from this plan]

Today's goal: [specific goal from plan]

Repository: /workspaces/commandcenter

Please start by:
1. Checking current git status
2. Confirming all services are running
3. Reviewing what we're building today

Ready? Let's build!
```

### During Session:

- Work through the plan step-by-step
- Test as you go (don't build everything then test)
- Commit after each working feature
- Document issues immediately
- Ask Claude Code to explain anything unclear

### At End of Each Session:

**Prompt for Claude Code:**
```
Claude Code, session wrap-up:

1. What did we accomplish today?
2. What's working perfectly?
3. What needs more work?
4. Any blockers for next session?

Create session summary: docs/sessions/SESSION_V15_[X]_SUMMARY.md

Also update: docs/progress.md with latest status
```

---

## 🆘 If You Get Stuck

### Issue: KB OAuth Not Working
```
Claude Code, OAuth is broken. Steps taken: [describe]
Error: [paste error]

Please:
1. Check Vercel environment variables
2. Verify Google Cloud Console settings
3. Check callback URLs match
4. Test locally first if possible
```

### Issue: Agent Not Responding
```
Claude Code, the [agent name] isn't responding.

What I tried: [describe]
Error in logs: [paste]

Please debug:
1. Check agent definition
2. Verify tools are imported
3. Check API endpoint routing
4. Test tools individually
```

### Issue: KB Search Returns Nothing
```
Claude Code, KB search is returning no results.

Query tested: [paste query]
Expected: [what should be found]

Please check:
1. Are documents actually in database?
2. Are embeddings generated correctly?
3. Is search logic working?
4. Test with direct database query
```

---

## 📊 Progress Tracking

### Session 1: KB Testing
- [ ] Codebase audit complete
- [ ] OAuth flow validated
- [ ] Preview mode tested
- [ ] Full sync successful
- [ ] Agent KB search working
- [ ] Test report created

### Session 2: Energy Orchestrator
- [ ] Design document created
- [ ] Battery optimizer tool built
- [ ] Miner coordinator tool built
- [ ] Energy planner tool built
- [ ] Agent created and configured
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Deployed to production

### Session 3: Polish & Ship
- [ ] Chat interface improved
- [ ] Agent selector added
- [ ] End-to-end tests passing
- [ ] Performance validated
- [ ] Documentation updated
- [ ] V1.5 deployed
- [ ] Release tagged

---

## 🎉 What Happens After V1.5

Once shipped, you'll have:

✅ **Working KB System** - Your Google Docs synced and searchable
✅ **Two Smart Agents** - Solar Controller + Energy Orchestrator
✅ **Good Chat Interface** - Easy to interact with agents
✅ **Reliable Infrastructure** - Everything deployed and stable

**Then you can:**
1. **Use it daily** - Get real feedback
2. **Monitor performance** - See what works/breaks
3. **Plan V2** - Based on actual usage
4. **Add hardware tools** - When you need them
5. **Build more agents** - As needs arise

---

**Ready to start Session 1? Let me know and I'll give you the exact prompt to give Claude Code!**