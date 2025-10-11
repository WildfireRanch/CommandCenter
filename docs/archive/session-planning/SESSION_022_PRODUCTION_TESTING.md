# Session 022: Production Testing on Railway

**Environment:** Railway Deployment
**URL:** https://api.wildfireranch.us
**Dashboard:** Your Streamlit dashboard URL

---

## 🎯 Quick Production Test Plan

Since local testing requires database connection only available on Railway, we'll test the **live production system**.

---

## ✅ Test 1: API Health Check

```bash
curl https://api.wildfireranch.us/health
```

**Expected:** `{"status": "healthy", ...}` or `{"status": "degraded", ...}` with details

**What it tells us:** API is accessible and responding

---

## ✅ Test 2: Simple Query via API

```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is my battery level?"}'
```

**Expected:**
- Response with "response" field
- "agent_role" field showing which agent answered
- "session_id" for conversation tracking
- "duration_ms" for performance

**What to check:**
- Does it respond within 30 seconds?
- Is the agent_role correct (Solar Controller)?
- Is there a valid session_id?

---

## ✅ Test 3: Frontend Dashboard Testing

**If you have Streamlit dashboard deployed:**

1. **Access Dashboard:** Go to your dashboard URL
2. **Navigate to Agent Chat:** Click "🤖 Agent Chat"
3. **Verify UI Enhancements:**
   - [ ] See grouped example questions (Status/Planning/KB)
   - [ ] Loading message varies ("Analyzing...", "Routing...", etc.)

4. **Test Query:** "What's my battery level?"
   - [ ] Response appears
   - [ ] Agent icon shown (☀️ for Solar Controller)
   - [ ] "Answered by:" with agent name
   - [ ] Response time displayed (⏱️ X.XXs)
   - [ ] Session ID visible

5. **Test Planning Query:** "Should we run the miners?"
   - [ ] Response appears
   - [ ] Agent icon is ⚡ (Energy Orchestrator)
   - [ ] Includes recommendation/reasoning

6. **Test KB Query:** "What is the minimum SOC threshold?"
   - [ ] Response appears
   - [ ] May show "📚 Knowledge Base Sources" expander
   - [ ] Includes source information if KB has docs

---

## 📊 Performance Quick Check

Run the same query 3 times and note response times:

**Query:** "What's my battery level?"

| Trial | Response Time | Status |
|-------|---------------|--------|
| 1 | ___s | ✅/❌ |
| 2 | ___s | ✅/❌ |
| 3 | ___s | ✅/❌ |

**Target:** All under 30s, preferably under 15s

---

## 🎯 Mini Test Results

```markdown
## Production Test Results

**Date:** __________
**API URL:** https://api.wildfireranch.us
**Dashboard:** __________

### API Tests
- [ ] Health endpoint: ✅/❌
- [ ] /ask endpoint: ✅/❌
- [ ] Response time acceptable: ✅/❌
- [ ] Agent routing working: ✅/❌

### Frontend Tests (if accessible)
- [ ] Dashboard loads: ✅/❌
- [ ] Agent Chat accessible: ✅/❌
- [ ] UI enhancements visible: ✅/❌
  - [ ] Agent icons (☀️ ⚡ 🎯)
  - [ ] Response time shown
  - [ ] Grouped examples
- [ ] Queries work end-to-end: ✅/❌

### Overall Assessment
System Status: OPERATIONAL / DEGRADED / DOWN
Notes: __________
```

---

## 🚀 Simplified Validation

**Minimum tests to validate V1.5:**

1. ✅ **API Health** - `curl https://api.wildfireranch.us/health`
2. ✅ **One Query** - Send "What's my battery level?" via API or dashboard
3. ✅ **Check Response** - Got answer with agent name and session ID?

**If all 3 pass → V1.5 is operational** ✅

---

## 💡 Why This Approach?

**Reality:**
- System is designed for Railway (where database lives)
- Local testing requires database mock/setup (hours of work)
- Production testing validates actual deployment (what users will use)

**Benefits:**
- Tests real environment
- Validates actual deployment
- Quick validation (5-10 minutes)
- Proves system works where it matters

**Trade-offs:**
- Can't test error handling easily (don't want to break production)
- Can't test with mock data
- Limited to what's already deployed

---

## ✅ Quick Win Test (60 seconds)

**Just want to know if it works?**

```bash
# Test 1: Is API alive?
curl https://api.wildfireranch.us/health

# Test 2: Can it answer a question?
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello"}'
```

**If both return JSON responses → System works!** ✅

---

## 🎯 Next Step After Production Test

**If tests pass:**
- ✅ Update SESSION_022_SUMMARY with results
- ✅ Mark V1.5 as production-validated
- ✅ Tag release v1.5.0
- ✅ Celebrate! 🎉

**If tests fail:**
- 📝 Document exact error
- 🐛 Check Railway logs
- 🔧 Fix and redeploy
- 🔄 Retest

---

**Ready to test production? Run the Quick Win Test above!** 🚀
