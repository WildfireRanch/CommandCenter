# Session 018: Testing Guide - KB Recursive Sync

**Date:** October 7, 2025
**Feature:** Recursive subfolder support + Preview mode
**API:** https://api.wildfireranch.us

---

## 🎯 What Was Built

### New Features:
1. **Recursive Folder Scanning** - Scans all subfolders in COMMAND_CENTER
2. **Folder Path Tracking** - Stores `folder` and `folder_path` for each document
3. **Preview Mode** - `/kb/preview` endpoint for dry-run analysis
4. **Ignore Patterns** - Skips folders like `old.*`, `archive`, etc.
5. **Better Context Detection** - Uses folder location, not filename

---

## 📋 Pre-Testing Checklist

### 1. Verify Railway Deployment
```bash
# Check Railway deployment status
railway status

# View recent logs
railway logs
```

**Expected:** Deployment successful, no errors in logs

### 2. Run Schema Migration
```bash
# Connect to Railway and run migration
cd railway
railway run python3 scripts/migrate_kb_schema.py
```

**Expected Output:**
```
🔍 Checking KB schema...
📝 Adding folder_path column...
✅ folder_path column added
📝 Creating index on folder_path...
✅ Index created
✅ Schema migration complete!
```

### 3. Get Access Token

**Option A: From Frontend (Recommended)**
1. Go to https://mcp.wildfireranch.us
2. Sign in with Google SSO
3. Open browser DevTools → Application → Cookies
4. Find `next-auth.session-token`
5. Decode the JWT to get `accessToken`

**Option B: Direct OAuth (Advanced)**
```bash
# Use Google OAuth 2.0 Playground
# https://developers.google.com/oauthplayground
# Scopes needed:
# - https://www.googleapis.com/auth/drive.readonly
# - https://www.googleapis.com/auth/documents.readonly
```

**Save your token:**
```bash
export ACCESS_TOKEN="ya29.a0AfB_by..."
```

---

## 🧪 Test 1: Preview Mode (Dry Run)

**Purpose:** See what would be synced WITHOUT actually syncing

### Test Command:
```bash
curl -X POST https://api.wildfireranch.us/kb/preview \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  | jq .
```

### Expected Response:
```json
{
  "status": "success",
  "total_files": 142,
  "total_folders": 6,
  "google_docs_count": 89,
  "files_by_folder": {
    "CONTEXT": [
      {
        "name": "solar-context.docx",
        "path": "COMMAND_CENTER/CONTEXT/solar-context.docx",
        "mimeType": "application/vnd.google-apps.document",
        "modifiedTime": "2025-10-06T10:30:00.000Z"
      }
    ],
    "SolarShack": [
      {
        "name": "SolArk Manual.docx",
        "path": "COMMAND_CENTER/SolarShack/SolArk Manual.docx",
        "mimeType": "application/vnd.google-apps.document",
        "modifiedTime": "2025-09-15T14:22:00.000Z"
      }
    ],
    "TradingBot": [...],
    "Wildfire.Green": [...]
  },
  "file_types": {
    "application/vnd.google-apps.document": 89,
    "application/pdf": 23,
    "application/vnd.google-apps.spreadsheet": 15,
    "image/png": 15
  },
  "estimated_tokens": 445000,
  "estimated_cost": "$0.0445",
  "note": "This is a preview only. No files have been synced."
}
```

### ✅ Success Criteria:
- [ ] Request returns 200 OK
- [ ] Shows all subfolders (CONTEXT, SolarShack, TradingBot, Wildfire.Green)
- [ ] `old.CommandCenter` is NOT in the folder list (ignored)
- [ ] Total files count looks correct (~142)
- [ ] Google Docs count looks reasonable (~89)
- [ ] File types breakdown includes docs, PDFs, sheets

### ❌ Troubleshooting:
**401 Unauthorized:**
- Access token expired (get new one)
- Token doesn't have Drive/Docs permissions

**Empty folder list:**
- Folder ID incorrect
- Permissions issue with Google Drive

---

## 🧪 Test 2: Database Schema Verification

### Check Schema:
```bash
railway run psql -c "\d kb_documents"
```

### Expected Output:
```
                                     Table "public.kb_documents"
     Column      |            Type             | Collation | Nullable |                  Default
-----------------+-----------------------------+-----------+----------+--------------------------------------------
 id              | integer                     |           | not null | nextval('kb_documents_id_seq'::regclass)
 google_doc_id   | character varying(255)      |           | not null |
 title           | character varying(500)      |           | not null |
 folder          | character varying(255)      |           |          |   ← Should exist
 folder_path     | character varying(1000)     |           |          |   ← Newly added
 full_content    | text                        |           |          |
 is_context_file | boolean                     |           |          | false
 token_count     | integer                     |           |          |
 last_synced     | timestamp without time zone |           |          |
 sync_error      | text                        |           |          |
 created_at      | timestamp without time zone |           |          | now()
 updated_at      | timestamp without time zone |           |          | now()
```

### ✅ Success Criteria:
- [ ] `folder` column exists
- [ ] `folder_path` column exists
- [ ] Both are VARCHAR (can store text)

---

## 🧪 Test 3: Sync CONTEXT Folder (Small Test)

**Purpose:** Test sync with just 3 files before doing full 142-file sync

### Test Command:
```bash
# Start sync (streaming response)
curl -X POST https://api.wildfireranch.us/kb/sync \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": true}' \
  --no-buffer
```

### Expected Output (Streaming):
```
data: {"status":"started","total":89,"message":"Found 89 documents across all folders"}

data: {"status":"processing","current":1,"total":89,"current_file":"COMMAND_CENTER/CONTEXT/solar-context.docx","processed":1,"updated":1}

data: {"status":"processing","current":2,"total":89,"current_file":"COMMAND_CENTER/SolarShack/manual.docx","processed":2,"updated":2}

...

data: {"status":"completed","total":89,"processed":89,"updated":89,"failed":0}
```

### Verify in Database:
```bash
railway run psql -c "SELECT title, folder, folder_path, is_context_file FROM kb_documents WHERE folder = 'CONTEXT';"
```

### Expected Output:
```
           title            | folder  |                folder_path                  | is_context_file
----------------------------+---------+--------------------------------------------+-----------------
 solar-context.docx         | CONTEXT | COMMAND_CENTER/CONTEXT/solar-context.docx  | t
 personal-context.docx      | CONTEXT | COMMAND_CENTER/CONTEXT/personal-context.docx| t
 business-context.docx      | CONTEXT | COMMAND_CENTER/CONTEXT/business-context.docx| t
```

### ✅ Success Criteria:
- [ ] Sync completes without errors
- [ ] CONTEXT files marked as `is_context_file = true`
- [ ] `folder` column populated correctly
- [ ] `folder_path` shows full path
- [ ] Files from other folders also synced

---

## 🧪 Test 4: Full Recursive Sync

**Purpose:** Sync all 142 files from all subfolders

### Test Command:
```bash
# Full sync
curl -X POST https://api.wildfireranch.us/kb/sync \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"force": false}' \
  --no-buffer
```

**Note:** `force: false` will skip unchanged files (faster)

### Monitor Progress:
Watch the streaming output for:
- Files from different folders being processed
- No errors
- Final count matches preview

### Verify All Folders Synced:
```bash
railway run psql -c "SELECT folder, COUNT(*) as count FROM kb_documents GROUP BY folder ORDER BY count DESC;"
```

### Expected Output:
```
     folder      | count
-----------------+-------
 Wildfire.Green  | 48
 SolarShack      | 23
 TradingBot      | 12
 CONTEXT         | 3
 Working Files   | 3
```

### ✅ Success Criteria:
- [ ] All major folders present (CONTEXT, SolarShack, TradingBot, Wildfire.Green)
- [ ] Total document count ≈ 89 (Google Docs only)
- [ ] No folder named `old.CommandCenter` (ignored)
- [ ] `failed` count is 0

---

## 🧪 Test 5: Search Across Folders

**Purpose:** Verify semantic search works with new folder structure

### Test Query 1: SolArk Battery Mode
```bash
curl -X POST https://api.wildfireranch.us/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "SolArk battery mode", "limit": 5}' \
  | jq .
```

### Expected Response:
```json
{
  "success": true,
  "query": "SolArk battery mode",
  "results": [
    {
      "content": "To switch to battery priority mode: 1. Press Settings...",
      "source": "SolArk Manual.docx",
      "folder": "SolarShack",
      "similarity": 0.92
    }
  ],
  "citations": ["SolArk Manual.docx"]
}
```

### Test Query 2: Trading Strategy
```bash
curl -X POST https://api.wildfireranch.us/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "trading bot strategy", "limit": 3}' \
  | jq .
```

### Expected Response:
```json
{
  "success": true,
  "query": "trading bot strategy",
  "results": [
    {
      "content": "Our trading strategy uses...",
      "source": "Trading Strategy.docx",
      "folder": "TradingBot",
      "similarity": 0.88
    }
  ],
  "citations": ["Trading Strategy.docx"]
}
```

### ✅ Success Criteria:
- [ ] Search returns results
- [ ] `folder` field is populated
- [ ] Results come from correct folders
- [ ] Similarity scores > 0.7
- [ ] Citations list is correct

---

## 🧪 Test 6: Agent KB Search Integration

**Purpose:** Verify agents can query KB and get folder context

### Test Agent Query:
```bash
curl -X POST https://api.wildfireranch.us/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the SolArk operating modes?",
    "session_id": "test-session-001"
  }' \
  | jq .
```

### Expected Response:
Agent response should:
- Reference KB search results
- Cite source documents
- Include folder context if available

### ✅ Success Criteria:
- [ ] Agent uses kb_search tool
- [ ] Response includes citations
- [ ] Sources from correct folders

---

## 🧪 Test 7: Sync Status & Stats

### Check Sync Log:
```bash
curl -X GET https://api.wildfireranch.us/kb/sync-status | jq .
```

### Expected Response:
```json
{
  "status": "success",
  "latest": {
    "id": 5,
    "sync_type": "full",
    "started_at": "2025-10-07T19:30:00.000Z",
    "completed_at": "2025-10-07T19:35:00.000Z",
    "status": "completed",
    "documents_processed": 89,
    "documents_updated": 89,
    "documents_failed": 0,
    "error_message": null
  },
  "history": [...]
}
```

### Check KB Stats:
```bash
curl -X GET https://api.wildfireranch.us/kb/stats | jq .
```

### Expected Response:
```json
{
  "status": "success",
  "documents": {
    "total_documents": 89,
    "context_files": 3,
    "searchable_files": 86,
    "total_tokens": 445000,
    "last_sync_time": "2025-10-07T19:35:00.000Z"
  },
  "chunks": {
    "total_chunks": 2340,
    "total_chunk_tokens": 445000
  },
  "syncs": {
    "total_syncs": 5,
    "successful_syncs": 5,
    "failed_syncs": 0
  }
}
```

### ✅ Success Criteria:
- [ ] Latest sync shows "completed"
- [ ] Documents processed count correct
- [ ] No failed syncs
- [ ] Context files count = 3
- [ ] Chunk count > 0

---

## 🚨 Common Issues & Fixes

### Issue: "folder_path column does not exist"
**Fix:** Run schema migration:
```bash
railway run python3 scripts/migrate_kb_schema.py
```

### Issue: Empty preview results
**Fix:** Check folder ID and permissions:
```bash
echo $GOOGLE_DOCS_KB_FOLDER_ID
# Should be: 1P6Dez9BRnIxnt-UNJzC4Iwl4AXF5H5DB
```

### Issue: "old.CommandCenter" showing up
**Fix:** Check ignore patterns in code (should be working)

### Issue: Context files not marked correctly
**Fix:** Check folder names are exactly "CONTEXT" (case-insensitive)

### Issue: 401 Unauthorized
**Fix:** Get fresh access token (they expire after 1 hour)

---

## 📊 Success Summary Checklist

### Code Deployment:
- [ ] Code pushed to GitHub
- [ ] Railway deployment successful
- [ ] No errors in Railway logs

### Schema Migration:
- [ ] Migration script ran successfully
- [ ] `folder_path` column added
- [ ] Index created

### Preview Mode:
- [ ] `/kb/preview` returns folder structure
- [ ] All subfolders detected
- [ ] `old.CommandCenter` ignored
- [ ] File counts accurate

### Sync:
- [ ] Recursive sync works
- [ ] All folders synced
- [ ] `folder` and `folder_path` populated
- [ ] CONTEXT files marked correctly
- [ ] No failed documents

### Search:
- [ ] Semantic search works
- [ ] Results include folder info
- [ ] Citations correct
- [ ] Agent integration works

### Performance:
- [ ] Sync completes in < 10 minutes
- [ ] Search responds in < 200ms
- [ ] No timeout errors

---

## 🎯 Next Steps After Testing

If all tests pass:
1. ✅ Mark Session 018 as complete
2. ✅ Document any issues found
3. ✅ Create Session 018 completion summary
4. ✅ Plan Session 019 (Frontend KB dashboard)

If tests fail:
1. 🔍 Document exact error
2. 🔧 Fix issue
3. 🔄 Re-test
4. 📝 Update documentation

---

**Ready to test!** Start with Test 1 (Preview Mode) and work through the checklist.
