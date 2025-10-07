# Session 018: KB Sync Testing & Optional Subfolder Support

**Date:** TBD
**Previous Session:** Session 017 - KB Integration & Testing (COMPLETE ✅)
**Duration:** ~1-2 hours
**Type:** Testing & Optional Enhancement

---

## 🎯 Session Goals

**Primary Objectives:**
1. ⏳ Organize KB documents in Google Drive
2. ⏳ Test manual KB sync
3. ⏳ Verify semantic search works with real data
4. ⏳ Test agent KB integration with real queries
5. ⏳ (Optional) Add recursive subfolder support

---

## 📊 Where We Left Off (Session 017)

**Completed in Session 017:**
- ✅ Fixed critical database connection bug
- ✅ Created KB search tool for agents
- ✅ Integrated KB search with solar_controller agent
- ✅ Fixed TypeScript build error in Vercel
- ✅ Fixed OAuth redirect URI in Google Cloud
- ✅ Deployed to Railway & Vercel
- ✅ **Google SSO tested and working!**

**Current Status:**
- ✅ All systems deployed and operational
- ✅ User signed in at https://mcp.wildfireranch.us/kb
- ⏳ Ready for KB sync (pending doc organization)

**Discovery:**
- Current code only syncs Google Docs in the main folder (NOT subfolders)
- Folder ID configured: `1P6Dez9BRnIxnt-UNJzC4Iwl4AXF5H5DB`

---

## 🚀 Part 1: Document Organization (5-10 min)

### Decision: Main Folder vs Subfolders?

**Option A: Keep It Simple (Recommended)**
- Place all KB documents directly in the "commandcenter" folder
- No subfolders needed
- Works with current code
- Organize with naming conventions:
  - `context-solar-shack.docx`
  - `context-battery-guide.docx`
  - `specs-panels.docx`
  - `procedures-maintenance.docx`

**Option B: Add Subfolder Support**
- Modify code to recursively scan subfolders
- More flexible organization
- Takes ~30 min to implement and test

**User Choice:** Pick one before proceeding!

---

## 🧪 Part 2: Test KB Sync (15-30 min)

### Prerequisites:
- ✅ Documents organized in Google Drive (Option A or B above)
- ✅ Signed in at https://mcp.wildfireranch.us/kb
- ✅ Folder ID set in Railway: `1P6Dez9BRnIxnt-UNJzC4Iwl4AXF5H5DB`

### Test Steps:

**1. Click "Sync Now"**
- Watch real-time progress updates
- Should show: "Processing X/Y: filename.docx"
- Wait for completion

**Expected Results:**
```
✅ Found [N] documents
✅ Processed [N] files
✅ Updated [N] documents
✅ 0 failed
✅ Sync completed in [time]
```

**2. Verify Documents List**
- Documents appear in table below
- Context files have green "CONTEXT" badge
- Token counts displayed
- Last synced timestamp shown

**3. Check Stats API**
```bash
curl https://api.wildfireranch.us/kb/stats | jq
```

**Expected:**
```json
{
  "status": "success",
  "documents": {
    "total_documents": 10,
    "context_files": 2,
    "searchable_files": 8,
    "total_tokens": 25000
  },
  "chunks": {
    "total_chunks": 75
  }
}
```

---

## 🔍 Part 3: Test Semantic Search (10 min)

### Test Search API:

```bash
curl -X POST https://api.wildfireranch.us/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "minimum battery SOC", "limit": 5}' | jq
```

**Expected:**
- Results relevant to query
- Similarity scores > 0.7 for top results
- Source citations included
- Response time < 200ms

**Try Multiple Queries:**
- "solar panel specifications"
- "battery charging procedure"
- "maintenance schedule"
- "grid export settings"
- "minimum SOC threshold"

**Verify:**
- ✅ Semantic search works (finds relevant content)
- ✅ Results ranked by relevance
- ✅ Citations accurate
- ✅ No errors

---

## 🤖 Part 4: Test Agent Integration (20 min)

### Ask Agent KB Questions:

```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold and why?"}' | jq
```

**Expected Behavior:**
1. Agent uses `search_kb_tool` to search KB
2. Agent finds relevant information
3. Agent formulates answer with citation
4. Response includes source document

**Example Expected Response:**
```json
{
  "response": "According to the system documentation, the minimum battery SOC threshold is 30%. This is to prevent deep discharge damage to the battery cells and ensure longevity. The system should never allow the battery to discharge below this level.\n\nSource: solar-shack-context.docx",
  "conversation_id": "...",
  "tokens_used": 350
}
```

**Test Questions:**
- "What is the minimum battery SOC threshold?"
- "What are the solar panel specifications?"
- "How should I handle low battery situations?"
- "What's the maximum battery charge rate?"
- "When should I run the generator?"

**Verify:**
- ✅ Agent uses KB search tool
- ✅ Answers are accurate (match KB docs)
- ✅ Sources are cited
- ✅ Responses are helpful and clear

---

## 🔧 Part 5: Optional - Add Subfolder Support (30 min)

**Only if user wants subfolder scanning!**

### Modification Needed:

**File:** `railway/src/kb/google_drive.py`

**Current code (line 64):**
```python
query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
```

**New approach:**
1. Add recursive function to list all subfolders
2. Scan each subfolder for Google Docs
3. Track folder path for organization
4. Update `kb_documents` table to include folder path

**Implementation:**
- Add `list_subfolders()` function
- Modify `list_files_in_folder()` to accept `recursive=True` parameter
- Update sync service to handle folder hierarchy
- Add folder column to UI display

**Testing:**
- Create subfolder structure in Drive
- Run sync
- Verify all docs found
- Check folder paths in UI

---

## ✅ Session Completion Checklist

**Part 1: Document Organization**
- [ ] Decided on main folder vs subfolders
- [ ] Documents organized in Google Drive
- [ ] Ready to sync

**Part 2: KB Sync**
- [ ] Clicked "Sync Now"
- [ ] Sync completed successfully
- [ ] Documents visible in UI
- [ ] Stats API shows correct counts

**Part 3: Semantic Search**
- [ ] Tested multiple search queries
- [ ] Results are relevant and accurate
- [ ] Citations working
- [ ] No errors

**Part 4: Agent Integration**
- [ ] Agent answers KB questions correctly
- [ ] Agent cites sources
- [ ] Responses are helpful
- [ ] Multiple questions tested

**Part 5: Optional Enhancements**
- [ ] Subfolder support added (if requested)
- [ ] OR: Skipped (using main folder only)

---

## 📝 Deliverables

**By end of Session 018:**

1. **Working KB System**
   - ✅ Documents synced
   - ✅ Search working
   - ✅ Agent integration tested

2. **Test Report**
   - Results of sync test
   - Search test results
   - Agent test results
   - Any issues encountered

3. **Documentation**
   - SESSION_018_COMPLETION_SUMMARY.md
   - Update progress.md
   - Screenshots of working system

4. **Optional: Subfolder Support**
   - Code modifications (if implemented)
   - Testing results
   - Documentation update

---

## 🚦 Getting Started

**First Steps:**

1. **Check Current Status:**
   ```bash
   curl https://api.wildfireranch.us/kb/stats | jq
   ```

2. **Verify Still Signed In:**
   - Visit: https://mcp.wildfireranch.us/kb
   - Should still be authenticated
   - If not, sign in again

3. **Decide on Organization:**
   - Main folder only? → Proceed with sync
   - Want subfolders? → Request implementation first

4. **Organize Documents:**
   - Place Google Docs in folder `1P6Dez9BRnIxnt-UNJzC4Iwl4AXF5H5DB`
   - Mark context files with "context" in filename (optional)

5. **Start Sync!**
   - Click "Sync Now"
   - Watch progress
   - Verify completion

---

## 📚 Reference Documents

**Session 017 (Previous):**
- [SESSION_017_COMPLETION_SUMMARY.md](SESSION_017_COMPLETION_SUMMARY.md)
- [KB_USER_TESTING_GUIDE.md](../KB_USER_TESTING_GUIDE.md)

**Architecture:**
- [06-knowledge-base-design.md](../06-knowledge-base-design.md)

**Code Files:**
- `railway/src/kb/google_drive.py` - Drive/Docs API integration
- `railway/src/kb/sync.py` - Sync service
- `railway/src/tools/kb_search.py` - KB search tool
- `railway/src/agents/solar_controller.py` - Agent with KB
- `vercel/src/app/kb/page.tsx` - KB UI

---

## 💡 Tips

**For Successful Sync:**
- Ensure documents are Google Docs (not Word files)
- Check documents are not in trash
- Verify folder ID is correct
- Documents should have some content (not empty)

**For Good Search Results:**
- Use natural language queries
- Try different phrasings if results aren't good
- Check document content matches what you're searching for

**For Agent Testing:**
- Ask specific questions that require KB info
- Don't ask about real-time data (use SolArk questions for that)
- Verify agent cites sources correctly

---

**Ready to test the KB system with real data!** 🚀

**Start with:** "Let's test the KB sync! Do you want to use the main folder only, or should we add subfolder support first?"
