# Session 022: Manual Testing Guide

**Purpose**: Step-by-step instructions for testing the CommandCenter system
**Duration**: 60-90 minutes total
**Status**: Ready to execute

---

## 🚀 Quick Start

### Step 1: Start Backend (Terminal 1)
```bash
cd /workspaces/CommandCenter/railway
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
✅ CommandCenter API initialized
```

**If it fails:** Check for port conflicts, environment variables

---

### Step 2: Start Frontend (Terminal 2)
```bash
cd /workspaces/CommandCenter/dashboards
streamlit run Home.py --server.port 8501
```

**Expected Output:**
```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

---

### Step 3: Access Agent Chat
- Open browser to: `http://localhost:8501`
- Click "🤖 Agent Chat" in sidebar
- You should see the chat interface with example questions

---

## 📋 Phase 1: End-to-End Testing (30 min)

### Test 1: Solar Controller (Status Query)

**Query:** "What's my battery level?"

**Expected Response:**
- ✅ Response within 15 seconds
- ✅ Contains battery percentage OR error about SolArk API
- ✅ Shows agent: "☀️ Answered by: Solar Controller" or "Energy Systems Monitor"
- ✅ Shows response time (e.g., "⏱️ Response time: 8.32s")
- ✅ Session ID displayed at top

**What to Record:**
```
✅ Test 1 - Solar Controller
Query: "What's my battery level?"
Response Time: ____ seconds
Agent: ____
Status: PASS/FAIL
Notes: ____
```

---

### Test 2: Energy Orchestrator (Planning Query)

**Query:** "Should we run the miners right now?"

**Expected Response:**
- ✅ Response within 20 seconds
- ✅ Contains recommendation (yes/no/conditional) with reasoning
- ✅ Shows agent: "⚡ Answered by: Energy Orchestrator" or "Energy Operations Manager"
- ✅ May reference battery SOC, solar production, policies
- ✅ Response time shown

**What to Record:**
```
✅ Test 2 - Energy Orchestrator
Query: "Should we run the miners right now?"
Response Time: ____ seconds
Agent: ____
Status: PASS/FAIL
Notes: ____
```

---

### Test 3: Knowledge Base Search

**Query:** "What is the minimum battery SOC threshold?"

**Expected Response:**
- ✅ Response within 15 seconds
- ✅ Contains SOC information OR "No relevant information found"
- ✅ May show "📚 Knowledge Base Sources" expander
- ✅ Includes source citations if KB has relevant docs
- ✅ Response time shown

**What to Record:**
```
✅ Test 3 - Knowledge Base
Query: "What is the minimum battery SOC threshold?"
Response Time: ____ seconds
Sources Found: YES/NO
Status: PASS/FAIL
Notes: ____
```

---

### Test 4: Multi-Turn Conversation

**First Query:** "What's my battery level?"
**Wait for response**
**Second Query:** "Is that good?"

**Expected Behavior:**
- ✅ Second query uses same session ID
- ✅ Agent can reference "that" from first response
- ✅ Response shows understanding of context
- ✅ Both messages appear in conversation history

**What to Record:**
```
✅ Test 4 - Multi-Turn Context
First: "What's my battery level?"
Second: "Is that good?"
Context Maintained: YES/NO
Status: PASS/FAIL
Notes: ____
```

---

### Test 5: Greeting/Unclear Query

**Query:** "Hello"

**Expected Response:**
- ✅ Friendly greeting response
- ✅ May ask how they can help
- ✅ Response within 10 seconds
- ✅ No crashes or errors

**What to Record:**
```
✅ Test 5 - Greeting
Query: "Hello"
Response Appropriate: YES/NO
Status: PASS/FAIL
Notes: ____
```

---

### Test 6: Edge Case - Empty Query

**Action:** Try to send empty message (if possible)

**Expected Behavior:**
- ✅ Either blocked by UI OR
- ✅ Backend returns validation error
- ✅ No crash, clear error message

---

### Test 7: Error Handling

**Action:** Stop the backend (Ctrl+C in Terminal 1)
**Then:** Try sending a message in frontend

**Expected Behavior:**
- ✅ Clear error message shown
- ✅ Error details expandable
- ✅ Frontend doesn't crash
- ✅ Can recover when backend restarted

**What to Record:**
```
✅ Test 7 - Error Handling
Error Message Clear: YES/NO
Frontend Stable: YES/NO
Status: PASS/FAIL
Notes: ____
```

**After test:** Restart backend!

---

### Test 8: Conversation Persistence

**Action 1:** Send 3-4 messages
**Action 2:** Note your session ID
**Action 3:** Click "🔄 New Session"
**Action 4:** Send 1 new message
**Action 5:** Click "📥 Load Conversation"

**Expected Behavior:**
- ✅ Can see previous conversations
- ✅ Messages persist across page refreshes
- ✅ Session IDs are different
- ✅ Conversation history loads correctly

---

## 📊 Phase 2: Performance Benchmarking (20 min)

### Performance Test Matrix

Run each query type 3 times and record response times:

| Query Type | Trial 1 (s) | Trial 2 (s) | Trial 3 (s) | Average (s) | Status |
|------------|-------------|-------------|-------------|-------------|---------|
| "What's my battery level?" | ___ | ___ | ___ | ___ | ✅/❌ |
| "Should we run miners?" | ___ | ___ | ___ | ___ | ✅/❌ |
| "What is min SOC?" | ___ | ___ | ___ | ___ | ✅/❌ |

**Acceptance Criteria:**
- ✅ Status queries: < 15s average
- ✅ Planning queries: < 25s average
- ✅ KB queries: < 20s average
- ❌ Any query > 60s is FAIL

### Performance Red Flags
- ⚠️ Response time increasing with each query (memory leak?)
- ⚠️ First query much slower than subsequent (cold start OK)
- ⚠️ Inconsistent times (e.g., 5s then 45s then 8s)

---

## ✅ Phase 3: UI Polish Verification (10 min)

### Visual Elements to Verify

**Enhanced Features (Post-Session 021):**
- [ ] Variable loading messages ("Analyzing...", "Routing...", etc.)
- [ ] Agent icons next to "Answered by" (☀️, ⚡, 🎯)
- [ ] Response time displayed
- [ ] Knowledge Base Sources expander (when KB used)
- [ ] Better example questions (grouped by agent type)

**Existing Features:**
- [ ] Chat messages display correctly
- [ ] Session ID shown
- [ ] Clear Chat button works
- [ ] Export Chat button works
- [ ] New Session button works

---

## 🎯 Success Criteria Summary

### Must Pass (Critical)
- [ ] All 3 agent types respond correctly
- [ ] No crashes or unhandled exceptions
- [ ] Error handling works gracefully
- [ ] Response times < 30s for all query types
- [ ] Agent metadata displays correctly
- [ ] Conversation persistence works

### Should Pass (Important)
- [ ] Multi-turn conversations maintain context
- [ ] UI enhancements visible and working
- [ ] Performance consistent across trials
- [ ] KB sources detected and highlighted

### Nice to Have
- [ ] All response times < 15s
- [ ] Context perfectly maintained in follow-ups
- [ ] No warning messages in logs

---

## 🐛 Common Issues & Solutions

### Issue: Backend won't start
**Symptoms:** Import errors, module not found
**Solution:**
```bash
cd /workspaces/CommandCenter/railway
pip install -r requirements.txt
```

### Issue: "Connection refused" in frontend
**Symptoms:** 404 errors, can't connect to API
**Solution:**
- Check backend is running on port 8000
- Check `RAILWAY_API_URL` in dashboards .env
- Try: `export RAILWAY_API_URL=http://localhost:8000`

### Issue: Agents take too long (>60s)
**Symptoms:** Timeouts, very slow responses
**Possible Causes:**
- OpenAI API slow
- Database queries slow
- Network issues
**Check:** Backend logs for bottlenecks

### Issue: Wrong agent answering
**Symptoms:** Status query goes to Orchestrator
**Check:**
- Manager routing logic in manager.py
- Look for JSON metadata in response

### Issue: No sources shown even with KB query
**Symptoms:** KB query works but no "Sources" expander
**Reason:** Detection keywords not in response
**Fix:** Expected - only shows if response contains "source:" or "citation"

---

## 📝 Test Results Template

Copy this to record your results:

```markdown
# Session 022 Test Results
Date: ___________
Tester: __________

## Phase 1: End-to-End Tests
- Test 1 (Solar Controller): ✅/❌ - Notes: ____
- Test 2 (Energy Orchestrator): ✅/❌ - Notes: ____
- Test 3 (Knowledge Base): ✅/❌ - Notes: ____
- Test 4 (Multi-Turn): ✅/❌ - Notes: ____
- Test 5 (Greeting): ✅/❌ - Notes: ____
- Test 6 (Empty Query): ✅/❌ - Notes: ____
- Test 7 (Error Handling): ✅/❌ - Notes: ____
- Test 8 (Persistence): ✅/❌ - Notes: ____

## Phase 2: Performance
Average Response Times:
- Status queries: ___s (Target: <15s)
- Planning queries: ___s (Target: <25s)
- KB queries: ___s (Target: <20s)

All under 30s: YES/NO

## Phase 3: UI Polish
- Enhanced loading messages: ✅/❌
- Agent icons displayed: ✅/❌
- Response time shown: ✅/❌
- KB sources expander: ✅/❌
- Grouped example questions: ✅/❌

## Overall Assessment
System Status: PRODUCTION READY / NEEDS FIXES
Issues Found: ____
Recommendations: ____
```

---

## 🎉 After Testing

### If All Tests Pass:
1. ✅ System is production ready
2. ✅ Can tag v1.5.0 release
3. ✅ Start using daily
4. ✅ Document any minor improvements for later

### If Tests Fail:
1. 📝 Document exact failure
2. 🐛 Create bug report
3. 🔧 Fix issues
4. 🔄 Retest

### Next Steps:
- Create SESSION_022_SUMMARY.md
- Update system status docs
- Plan V2.0 features (if ready to ship)

---

## 💡 Testing Tips

**Best Practices:**
- Test one thing at a time
- Record actual vs expected results
- Take screenshots of UI enhancements
- Check backend logs for errors
- Note any unusual behavior (even if it works)

**What Good Looks Like:**
- Responses in 5-15 seconds
- Clear agent attribution
- Helpful error messages
- Smooth user experience
- No console errors

**What Bad Looks Like:**
- Timeouts or hangs
- Wrong agent answering
- Silent failures
- Confusing error messages
- UI glitches

---

**Ready to test? Start with Step 1: Start Backend!** 🚀
