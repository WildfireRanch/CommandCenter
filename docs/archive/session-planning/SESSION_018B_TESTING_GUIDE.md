# Session 018B Testing Guide - Complete Feature Walkthrough

**Purpose:** Walk through all KB dashboard features and test functionality end-to-end

**Time Required:** 15-20 minutes

**Prerequisites:**
- ✅ OAuth authentication working (Session 018B complete)
- ✅ Google account `bret@westwood5.com` authorized
- ✅ Google Drive folder `COMMAND_CENTER` exists with documents

---

## 🧪 Testing Checklist

Use this guide to systematically test every feature of the KB dashboard.

---

## Part 1: Authentication (5 minutes)

### Test 1.1: Sign In Flow
**Objective:** Verify OAuth authentication works correctly

**Steps:**
1. Open browser (Chrome/Firefox recommended)
2. Navigate to: https://mcp.wildfireranch.us/kb
3. You should see: "Sign in with Google" button

**Expected Result:**
- Clean page loads with no errors
- Button is visible and styled correctly

**Action:**
4. Click "Sign in with Google"

**Expected Result:**
- Redirect to Google OAuth consent screen
- Shows: "Bret Westwood (bret@westwood5.com)"
- May show "to continue to Relay Docs CLI" (cosmetic only)

**Action:**
5. Select your account (bret@westwood5.com)
6. If prompted, approve access to Drive and Docs

**Expected Result:**
- ✅ Redirect back to https://mcp.wildfireranch.us/kb
- ✅ No error message
- ✅ Dashboard loads with 3 tabs visible
- ✅ No "Application error" message

**If Failed:**
- Check browser console (F12) for errors
- Verify Vercel env vars are correct
- See [SESSION_018B_RESOLUTION.md](/workspaces/CommandCenter/docs/SESSION_018B_RESOLUTION.md) for troubleshooting

---

### Test 1.2: Session Persistence
**Objective:** Verify session stays active across page refreshes

**Steps:**
1. After signing in, press F5 to refresh the page

**Expected Result:**
- ✅ Still signed in (no re-authentication required)
- ✅ Dashboard loads immediately
- ✅ No flash of "Sign in with Google" button

**Action:**
2. Close the tab
3. Open new tab and navigate to https://mcp.wildfireranch.us/kb

**Expected Result:**
- ✅ Still signed in
- ✅ Dashboard loads without sign-in prompt

---

## Part 2: Overview Tab (10 minutes)

### Test 2.1: Sync Status Card
**Objective:** Verify sync status displays correctly

**Steps:**
1. Ensure you're on the "📊 Overview" tab (default)
2. Look at the "Sync Status" card at the top

**Expected Result:**
- ✅ Shows "Last Sync: Never" (if first time)
- ✅ Shows "Documents: 0 synced, 0 context files"
- ✅ Shows "Total Tokens: 0 (~$0.00)"
- ✅ Two buttons visible: "🔄 Full Sync" and "⚡ Smart Sync"

**Note:** If you've synced before, it will show:
- Last sync timestamp
- Actual document count
- Actual token count

---

### Test 2.2: Preview Card
**Objective:** Verify preview shows Google Drive folder structure

**Steps:**
1. Scroll down to "Preview (What Will Be Synced)" card

**Expected Result:**
- ✅ Three colored stat boxes showing:
  - **Folders:** [number of folders in COMMAND_CENTER]
  - **Total Files:** [number of files found]
  - **Google Docs:** [number of Google Doc files]

**Action:**
2. Review the folder list below the stats

**Expected Result:**
- ✅ List of folders from your COMMAND_CENTER directory
- ✅ Each folder shows:
  - 📂 Folder name
  - File count in parentheses
  - Full path (e.g., "COMMAND_CENTER/CONTEXT")

**Common Folders to Expect:**
- 📂 CONTEXT (X files)
- 📂 SolarShack (X files)
- 📂 TradingBot (X files)
- 📂 Wildfire.Green (X files)
- 📂 Working Files (X files)

**Note:** `old.CommandCenter` should NOT appear (it's ignored)

---

### Test 2.3: Sync History Card
**Objective:** Verify sync history displays (or shows "no history" message)

**Steps:**
1. Scroll down to "Recent Sync History (Last 5)" card

**Expected Result (First Time):**
- ✅ Shows message: "No sync history yet"

**Expected Result (After Syncs):**
- ✅ Shows last 5 sync operations
- ✅ Each entry shows:
  - Date/time
  - Sync type (full / smart)
  - Triggered by (manual / auto)
  - Status badge (✅ Success / ❌ Failed / ⚠️ Partial)
  - File count

---

### Test 2.4: Trigger Full Sync
**Objective:** Test the complete sync flow with real-time progress

**IMPORTANT:** This will actually sync your Google Docs! Make sure you're ready.

**Steps:**
1. Click "🔄 Full Sync" button

**Expected Result:**
- ✅ Button becomes disabled (grayed out)
- ✅ Modal appears: "🔄 Syncing Knowledge Base..."
- ✅ Progress bar appears showing 0%

**Action:**
2. Watch the sync progress

**Expected Result During Sync:**
- ✅ Progress bar updates in real-time
- ✅ Shows: "Progress: X / Y documents"
- ✅ Shows percentage (e.g., "33%")
- ✅ Shows "Currently processing: [filename]"
- ✅ Progress updates every few seconds
- ✅ Cancel button is visible

**What's Happening:**
- Backend is:
  1. Listing all files from Google Drive
  2. Downloading content for each Google Doc
  3. Chunking text into 512-token pieces
  4. Generating embeddings via OpenAI
  5. Storing in PostgreSQL database

**Expected Duration:**
- Small KB (10 docs): 1-2 minutes
- Medium KB (50 docs): 5-7 minutes
- Large KB (100+ docs): 10-15 minutes

**Action:**
3. Wait for sync to complete (do not close modal or navigate away)

**Expected Result on Completion:**
- ✅ Modal title changes to: "✅ Sync Complete!"
- ✅ Shows summary statistics:
  - **Processed:** [number] (in green)
  - **Updated:** [number] (in blue)
  - **Failed:** [number, should be 0] (in red)
- ✅ Shows "✅ Close" button

**If Errors Occur:**
- Review error message in modal
- Common issues:
  - Permission denied (check Google Drive sharing)
  - Rate limit (too many files at once)
  - Network timeout

**Action:**
4. Click "✅ Close" button

**Expected Result:**
- ✅ Modal closes
- ✅ Sync Status card updates with new stats
- ✅ "Documents" count increases
- ✅ "Total Tokens" count increases
- ✅ "Last Sync" shows current time

---

### Test 2.5: Verify Sync History Updated
**Objective:** Confirm sync was logged in history

**Steps:**
1. Scroll to "Recent Sync History" card
2. Refresh page if needed (F5)

**Expected Result:**
- ✅ New entry at the top showing:
  - Current timestamp
  - "full | manual"
  - ✅ Success badge
  - File count matching sync summary

---

## Part 3: Files Tab (5 minutes)

### Test 3.1: Browse Synced Documents
**Objective:** Verify documents are displayed grouped by folder

**Steps:**
1. Click "📁 Files" tab

**Expected Result:**
- ✅ Documents grouped by folder
- ✅ Each folder shows as a card with:
  - 📂 Folder name
  - "(Tier 1: Context Files)" label for CONTEXT folder
  - File count (e.g., "- 3 files")

**Common Folders:**
- 📂 CONTEXT (Tier 1: Context Files) - X files
- 📂 SolarShack - X files
- 📂 TradingBot - X files
- 📂 Wildfire.Green - X files
- 📂 Working Files - X files

---

### Test 3.2: Review Document Details
**Objective:** Verify individual document information displays correctly

**Steps:**
1. Expand any folder card
2. Review the list of documents inside

**Expected Result for Each Document:**
- ✅ Document title (filename)
- ✅ Full folder path (e.g., "COMMAND_CENTER/SolarShack/manual.docx")
- ✅ Token count on the right
- ✅ Last synced date
- ✅ Green "Context File (Always Loaded)" badge for CONTEXT folder files

---

### Test 3.3: Verify Context Files
**Objective:** Confirm CONTEXT folder files are marked as Tier 1

**Steps:**
1. Find the CONTEXT folder card
2. Look at the files inside

**Expected Result:**
- ✅ Each file has green badge: "Context File (Always Loaded)"
- ✅ Folder shows "(Tier 1: Context Files)" label

**Why This Matters:**
- Context files are automatically loaded into every agent conversation
- They provide background knowledge about your setup
- Should be small, high-value documents

---

## Part 4: Settings Tab (2 minutes)

### Test 4.1: Review Configuration
**Objective:** Verify settings display correctly (note: not editable yet)

**Steps:**
1. Click "⚙️ Settings" tab

**Expected Result - Automatic Sync Section:**
- ✅ Checkbox for "Enable nightly auto-sync" (not functional yet)
- ✅ Time picker showing "03:00"
- ✅ Dropdown showing "Smart Sync (changed only)"

**Expected Result - Folder Configuration:**
- ✅ Root folder: COMMAND_CENTER (grayed out)
- ✅ Context folder: COMMAND_CENTER/CONTEXT (grayed out)
- ✅ Ignore patterns: old.*, archive/*, temp/* (grayed out)

**Expected Result - Advanced Options:**
- ✅ Chunk size: 512 tokens (grayed out)
- ✅ Embedding model: text-embedding-3-small (grayed out)
- ✅ Max file size: 50,000 tokens (grayed out)
- ✅ Concurrent uploads: 5 files (grayed out)

**Expected Result - Save Button:**
- ✅ "💾 Save Settings" button visible
- ✅ Button is enabled (but won't do anything yet - backend pending)

**Note:** Settings are display-only in this version. Editing will be implemented in future session.

---

## Part 5: Smart Sync Test (Optional - 5 minutes)

### Test 5.1: Trigger Smart Sync
**Objective:** Verify Smart Sync only syncs changed files

**Prerequisites:**
- Full Sync already completed (from Test 2.4)

**Steps:**
1. Go back to "📊 Overview" tab
2. Click "⚡ Smart Sync" button

**Expected Result:**
- ✅ Modal appears: "🔄 Syncing Knowledge Base..."
- ✅ Progress shows much faster (only changed files)
- ✅ If no files changed: "0 / 0 documents" or immediate completion
- ✅ Completion summary shows:
  - **Processed:** 0 or small number
  - **Updated:** 0 (if nothing changed)
  - **Failed:** 0

**To Test With Changes:**
1. Before clicking Smart Sync:
   - Edit a Google Doc in your COMMAND_CENTER folder
   - Save the changes
2. Click "⚡ Smart Sync"

**Expected Result:**
- ✅ Only the changed file(s) are synced
- ✅ Much faster than Full Sync
- ✅ "Updated" count matches files you changed

---

## Part 6: Error Handling Tests (Optional - 5 minutes)

### Test 6.1: Network Error
**Objective:** Verify graceful handling of network issues

**Steps:**
1. Open browser DevTools (F12)
2. Go to Network tab
3. Enable "Offline" mode
4. Try to click "Full Sync"

**Expected Result:**
- ✅ Modal appears but sync fails
- ✅ Error message displayed: "Sync failed: [error]"
- ✅ No crash or "Application error"
- ✅ Can close modal and try again

---

### Test 6.2: Session Expiry
**Objective:** Verify behavior when OAuth token expires

**Steps:**
1. Leave the page open for 1+ hour
2. Try to trigger sync

**Expected Result:**
- ✅ Either: Sync works (token auto-refreshed)
- ✅ Or: Prompted to sign in again
- ✅ No "Application error" or crash

---

## 📊 Test Results Summary

Use this checklist to track your testing progress:

### Authentication
- [ ] Sign in with Google works
- [ ] Session persists across refreshes
- [ ] Session persists across new tabs

### Overview Tab
- [ ] Sync Status card displays correctly
- [ ] Preview card shows folder structure
- [ ] Sync History shows (or "no history" message)
- [ ] Full Sync completes successfully
- [ ] Progress modal shows real-time updates
- [ ] Sync History updates after sync

### Files Tab
- [ ] Documents grouped by folder
- [ ] Document details display correctly
- [ ] Context files marked with badge
- [ ] All synced documents visible

### Settings Tab
- [ ] Automatic sync settings display
- [ ] Folder configuration displays
- [ ] Advanced options display
- [ ] Save button visible

### Smart Sync (Optional)
- [ ] Smart Sync completes quickly
- [ ] Only changed files synced
- [ ] Completion stats accurate

### Error Handling (Optional)
- [ ] Network errors handled gracefully
- [ ] Session expiry handled correctly

---

## 🎯 Success Criteria

**Minimum Success (Must Pass):**
- ✅ Can sign in with Google OAuth
- ✅ Overview tab loads without errors
- ✅ Preview shows folder structure
- ✅ Full Sync completes successfully
- ✅ Files tab shows synced documents

**Full Success (Should Pass):**
- ✅ All tabs work correctly
- ✅ Real-time progress updates during sync
- ✅ Documents grouped by folder in Files tab
- ✅ Context files marked correctly
- ✅ No client-side errors or crashes

---

## 🐛 Troubleshooting

### Issue: "Application error: a client-side exception has occurred"

**Solution:**
1. Hard refresh: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)
2. Clear browser cache
3. Try incognito/private mode
4. Check browser console (F12) for exact error

### Issue: OAuth callback error

**Solution:**
1. Verify Vercel environment variables are set correctly
2. Check Google Cloud Console redirect URI
3. See [SESSION_018B_RESOLUTION.md](/workspaces/CommandCenter/docs/SESSION_018B_RESOLUTION.md)

### Issue: Preview shows 0 folders/files

**Possible Causes:**
1. COMMAND_CENTER folder is empty
2. Service account doesn't have access
3. GOOGLE_DOCS_KB_FOLDER_ID incorrect in Railway

**Solution:**
1. Verify COMMAND_CENTER folder has documents
2. Check folder ID matches in Railway env vars
3. Test preview endpoint: `curl -X POST https://api.wildfireranch.us/kb/preview`

### Issue: Sync fails or times out

**Possible Causes:**
1. Too many files to sync at once
2. Network timeout
3. Rate limiting from Google or OpenAI
4. Permission issues

**Solution:**
1. Check error message in modal
2. Try syncing CONTEXT folder first (smaller)
3. Check Railway logs for backend errors
4. Verify Google Drive sharing permissions

### Issue: Documents not appearing in Files tab

**Possible Causes:**
1. Sync hasn't completed yet
2. Database connection issue
3. Frontend not fetching correctly

**Solution:**
1. Wait for sync to complete fully
2. Refresh page (F5)
3. Check browser console for API errors
4. Verify `/kb/documents` endpoint: `curl https://api.wildfireranch.us/kb/documents`

---

## 📞 Getting Help

If you encounter issues not covered in this guide:

1. **Check Documentation:**
   - [SESSION_018B_RESOLUTION.md](/workspaces/CommandCenter/docs/SESSION_018B_RESOLUTION.md) - OAuth troubleshooting
   - [SESSION_018_COMPLETION_SUMMARY.md](/workspaces/CommandCenter/docs/SESSION_018_COMPLETION_SUMMARY.md) - Backend details

2. **Check Logs:**
   - **Vercel:** Dashboard → Deployments → Latest → Runtime Logs
   - **Railway:** Dashboard → Deployments → Logs

3. **Verify Endpoints:**
   ```bash
   # Preview
   curl -X POST https://api.wildfireranch.us/kb/preview

   # Documents
   curl https://api.wildfireranch.us/kb/documents

   # Health check
   curl https://api.wildfireranch.us/health
   ```

4. **Browser Console:**
   - Press F12
   - Look for red errors in Console tab
   - Check Network tab for failed requests

---

## 🎉 Testing Complete!

Once all tests pass, you have:
- ✅ Fully functional KB dashboard
- ✅ Working OAuth authentication
- ✅ Real-time sync with progress tracking
- ✅ Document browsing by folder
- ✅ Preview of Google Drive structure

**Next Steps:**
- Use the KB! Query documents through your agents
- Set up auto-sync (future session)
- Add more documents to COMMAND_CENTER folder
- Explore advanced features (coming soon)

---

**Happy Testing! 🚀**

If everything works as expected, celebrate with a coffee - you've got a production-ready knowledge base sync system! ☕️
