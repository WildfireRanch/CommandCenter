# Knowledge Base User Testing Guide

**Quick reference for testing the KB system after Session 017**

---

## Prerequisites

### 1. Set Environment Variable in Railway

**Required:** `GOOGLE_DOCS_KB_FOLDER_ID`

**How to set it:**
1. Go to Railway dashboard
2. Select CommandCenter project
3. Select "CommandCenter" service (API)
4. Go to Variables tab
5. Add: `GOOGLE_DOCS_KB_FOLDER_ID` = `[your Google Drive folder ID]`

**To find your folder ID:**
1. Open Google Drive
2. Navigate to the folder with your KB documents
3. Look at URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
4. Copy the `FOLDER_ID_HERE` part

### 2. Verify Vercel Environment Variables

Should already be set from Session 016:
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`
- `ALLOWED_EMAIL` (your email address)

---

## Test 1: Google SSO Login

**URL:** https://mcp.wildfireranch.us/kb

**Steps:**
1. Visit the URL
2. Click "Sign in with Google" button
3. Sign in with your Google account
4. Authorize the requested permissions:
   - View your email address
   - View your Google Drive files
   - View your Google Docs
5. Should redirect back to /kb page (authenticated)

**✅ Success Indicators:**
- You're signed in and see the KB management page
- Your name/email appears in the UI
- "Sync Now" button is enabled
- Document list loads (empty at first)

**❌ Failure Modes:**
- **"Access Denied"** → Check `ALLOWED_EMAIL` matches your exact email
- **OAuth Error** → Verify Google Cloud Console OAuth redirect URI
- **Page doesn't load** → Check Vercel deployment logs
- **"Sign in failed"** → Check browser console for errors

---

## Test 2: Manual KB Sync

**Prerequisites:** Signed in via Google SSO

**Steps:**
1. Click "Sync Now" button
2. Watch real-time progress updates in the UI
3. Wait for sync to complete (may take 1-5 minutes depending on document count)

**✅ Success Indicators:**
- Progress bar shows current file being processed
- Document count increases as sync progresses
- Status changes to "Sync completed successfully"
- Documents appear in list below
- Context files have green "CONTEXT" badge
- Token counts are displayed for each document
- Last sync timestamp is shown

**❌ Failure Modes:**
- **"Folder ID not configured"** → Set `GOOGLE_DOCS_KB_FOLDER_ID` in Railway
- **"Permission denied"** → Check OAuth scopes in Google Cloud Console
- **"No documents found"** → Verify folder ID is correct and has documents
- **Sync stalls** → Check Railway logs: `railway logs --service CommandCenter`

**Expected Results:**
```
✅ Found 20 documents
✅ Processed 20 files
✅ Updated 20 documents
✅ 0 failed
✅ Sync completed in 2m 15s
```

---

## Test 3: Verify KB Data

**Check via API:**

### Stats
```bash
curl https://api.wildfireranch.us/kb/stats | jq
```

**Expected Output:**
```json
{
  "status": "success",
  "documents": {
    "total_documents": 20,
    "context_files": 3,
    "searchable_files": 17,
    "total_tokens": 50000,
    "last_sync_time": "2025-10-07T..."
  },
  "chunks": {
    "total_chunks": 150,
    "total_chunk_tokens": 76800
  },
  "syncs": {
    "total_syncs": 1,
    "successful_syncs": 1,
    "failed_syncs": 0
  }
}
```

### Documents
```bash
curl https://api.wildfireranch.us/kb/documents | jq
```

**Expected Output:**
```json
{
  "status": "success",
  "documents": [
    {
      "id": 1,
      "title": "solar-shack-context.docx",
      "is_context_file": true,
      "token_count": 5000,
      "last_synced": "2025-10-07T..."
    },
    ...
  ],
  "count": 20
}
```

---

## Test 4: KB Search

**Test semantic search:**

```bash
curl -X POST https://api.wildfireranch.us/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "solar battery threshold", "limit": 5}' | jq
```

**Expected Output:**
```json
{
  "success": true,
  "query": "solar battery threshold",
  "results": [
    {
      "content": "Minimum SOC: 30% (never go below)...",
      "source": "solar-shack-context.docx",
      "folder": null,
      "similarity": 0.92
    },
    {
      "content": "Target SOC during solar hours: 100%...",
      "source": "battery-guide.docx",
      "folder": null,
      "similarity": 0.87
    },
    ...
  ],
  "citations": ["solar-shack-context.docx", "battery-guide.docx"]
}
```

**✅ Success Indicators:**
- `success: true`
- Results are relevant to query
- Similarity scores > 0.7 for top results
- Citations list source documents
- Response time < 200ms

**Try These Queries:**
- "minimum battery SOC"
- "solar panel specifications"
- "battery charging procedure"
- "grid export settings"
- "maintenance schedule"

---

## Test 5: Agent KB Integration

**Test agent using KB search:**

```bash
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold and why?"}' | jq
```

**Expected Behavior:**
1. Agent receives question
2. Agent uses `search_kb_tool` to search KB
3. Agent finds relevant information
4. Agent formulates answer with citation

**Expected Output:**
```json
{
  "response": "According to the system documentation, the minimum battery SOC threshold is 30%. This is to prevent deep discharge damage to the battery cells and ensure longevity. The system should never allow the battery to discharge below this level.\n\nSource: solar-shack-context.docx",
  "conversation_id": "...",
  "tokens_used": 350
}
```

**✅ Success Indicators:**
- Agent provides accurate answer
- Response includes citation (e.g., "Source: ...")
- Answer matches information in KB documents
- Response is well-formatted and helpful

**Try These Questions:**
- "What is the target battery SOC during the day?"
- "What are the solar panel specifications?"
- "How should I handle low battery situations?"
- "What's the maximum battery charge rate?"
- "When should I run the generator?"

---

## Test 6: Frontend KB Page

**Manual testing on /kb page:**

### View Documents
- ✅ Documents listed in table
- ✅ Context files have green badge
- ✅ Token counts displayed
- ✅ Last synced timestamps shown
- ✅ Can scroll through long lists

### Sync Status
- ✅ Last sync time displayed
- ✅ Sync history available
- ✅ Error messages shown if sync fails
- ✅ Can trigger manual sync

### UI/UX
- ✅ Page loads quickly
- ✅ Responsive on mobile
- ✅ Clear error messages
- ✅ Real-time progress during sync
- ✅ Can sign out

---

## Troubleshooting

### No Documents Syncing

**Check:**
1. `GOOGLE_DOCS_KB_FOLDER_ID` is set correctly
2. Folder has documents in it (not subfolders only)
3. OAuth scopes include Drive and Docs readonly
4. Railway logs for errors: `railway logs --service CommandCenter --lines 50`

### Search Returns No Results

**Check:**
1. Documents are synced (run sync first)
2. Query is at least 3 characters
3. KB has relevant content
4. Database has embeddings: `curl https://api.wildfireranch.us/kb/stats`

### Agent Doesn't Use KB

**Check:**
1. KB is populated with data
2. Question requires KB information (not real-time data)
3. Agent has `search_kb_tool` in tools list
4. Railway deployment includes latest code

### OAuth/Login Issues

**Check:**
1. Google Cloud Console OAuth credentials
2. Authorized redirect URIs include Vercel domain
3. `ALLOWED_EMAIL` matches your email exactly
4. Vercel environment variables are set

---

## Useful Commands

### Railway Logs
```bash
# View recent logs
railway logs --service CommandCenter --lines 50

# Follow logs in real-time
railway logs --service CommandCenter --follow

# View logs with timestamps
railway logs --service CommandCenter --timestamps
```

### Database Check
```bash
# Connect to Railway database
railway run psql $DATABASE_URL

# Check KB tables
SELECT COUNT(*) FROM kb_documents;
SELECT COUNT(*) FROM kb_chunks;
SELECT * FROM kb_sync_log ORDER BY started_at DESC LIMIT 5;
```

### API Health Check
```bash
curl https://api.wildfireranch.us/health | jq
```

---

## Success Checklist

After testing, you should have:

- [x] Signed in with Google SSO
- [x] Successfully synced KB documents
- [x] Verified documents in database (stats endpoint)
- [x] Tested KB search with multiple queries
- [x] Asked agent KB-related questions
- [x] Verified agent cites sources
- [x] Confirmed frontend displays documents correctly

---

## Next Steps After Testing

**If everything works:**
1. Document any issues or improvements needed
2. Consider automatic daily sync (GitHub Actions or Railway cron)
3. Add more documents to KB
4. Test with different types of questions
5. Fine-tune chunk size and search parameters

**If something doesn't work:**
1. Check Railway logs for errors
2. Check browser console for frontend errors
3. Verify all environment variables
4. Test individual components (sync, search, agent)
5. Refer to Session 017 completion summary for debugging

---

## Support

**Documentation:**
- Session 017 Completion Summary: `docs/sessions/SESSION_017_COMPLETION_SUMMARY.md`
- KB Design Doc: `docs/06-knowledge-base-design.md`
- Session 016 Summary: `docs/sessions/SESSION_016_COMPLETION_SUMMARY.md`

**Code References:**
- KB Sync: `railway/src/kb/sync.py`
- KB API Routes: `railway/src/api/routes/kb.py`
- KB Search Tool: `railway/src/tools/kb_search.py`
- Agent Integration: `railway/src/agents/solar_controller.py`
- Frontend Page: `vercel/src/app/kb/page.tsx`

---

**Ready to test! Start with Test 1 (Google SSO Login) and work your way through.** 🚀
