# KB Dashboard Complete Testing Prompt

**Use this prompt to test all features of the KB Dashboard systematically**

---

## 🎯 Testing Session Goal

Walk through the complete Knowledge Base Dashboard at https://mcp.wildfireranch.us/kb and test all functionality end-to-end.

**Expected Duration:** 15-20 minutes
**Prerequisites:** OAuth is working, dashboard is deployed

---

## 📋 Step-by-Step Testing Instructions

### Phase 1: Authentication (2 minutes)

**1. Navigate to KB Dashboard**
- Go to: https://mcp.wildfireranch.us/kb
- Expected: See "Sign in with Google" button

**2. Sign In**
- Click "Sign in with Google"
- Select `bret@westwood5.com`
- Approve access if prompted
- **Success Check:** Redirected to dashboard with 3 tabs visible (📊 Overview, 📁 Files, ⚙️ Settings)

**3. Verify Session**
- Refresh page (F5)
- **Success Check:** Still signed in, no re-authentication needed

---

### Phase 2: Overview Tab - Preview Data (3 minutes)

**4. Check Sync Status Card**
- Should show:
  - ✅ Last Sync time (or "Never")
  - ✅ Document count
  - ✅ Total tokens with cost estimate
  - ✅ Two buttons: "🔄 Full Sync" and "⚡ Smart Sync"

**5. Check Preview Card**
- Scroll to "Preview (What Will Be Synced)"
- **Success Check:**
  - Shows 3 colored stats boxes (Folders, Total Files, Google Docs)
  - Lists all folders from COMMAND_CENTER with file counts
  - Expected folders: CONTEXT, SolarShack, TradingBot, Wildfire.Green, Working Files
  - `old.CommandCenter` should NOT appear (it's ignored)

**6. Check Sync History**
- Scroll to "Recent Sync History (Last 5)"
- **Success Check:** Shows "No sync history yet" (if first time)

---

### Phase 3: Full Sync Test (8 minutes)

**7. Trigger Full Sync**
- Click "🔄 Full Sync" button
- **Success Check:** Modal appears with "🔄 Syncing Knowledge Base..."

**8. Watch Progress Updates**
- Observe the sync progress in real-time
- **Success Check:**
  - Progress bar updates continuously
  - Shows "Progress: X / Y documents"
  - Shows percentage (e.g., "33%")
  - Shows "Currently processing: [filename]"
  - Updates happen every few seconds

**9. Wait for Completion**
- Do not close modal or navigate away
- Expected duration: 1-15 minutes depending on document count
- **Success Check:** Modal title changes to "✅ Sync Complete!"

**10. Review Summary**
- Check the completion stats:
  - **Processed:** [number] in green
  - **Updated:** [number] in blue
  - **Failed:** Should be 0 (in red)
- Click "✅ Close" button

**11. Verify Stats Updated**
- Sync Status card should now show:
  - ✅ Last Sync: Current timestamp
  - ✅ Documents: Increased count
  - ✅ Total Tokens: Increased count

**12. Check Sync History**
- Scroll to "Recent Sync History"
- **Success Check:** New entry at top showing your sync with ✅ Success badge

---

### Phase 4: Files Tab (3 minutes)

**13. Browse Documents**
- Click "📁 Files" tab
- **Success Check:** Documents grouped by folder

**14. Review Folder Structure**
- Each folder should display as a card showing:
  - 📂 Folder name
  - File count (e.g., "- 3 files")
  - "(Tier 1: Context Files)" for CONTEXT folder

**15. Check Document Details**
- Expand each folder and review documents
- Each document should show:
  - ✅ Document title (filename)
  - ✅ Full folder path
  - ✅ Token count (right side)
  - ✅ Last synced date
  - ✅ Green "Context File (Always Loaded)" badge for CONTEXT files

**16. Verify CONTEXT Folder**
- Find CONTEXT folder
- **Success Check:** All files have green "Context File" badge

---

### Phase 5: Settings Tab (1 minute)

**17. Review Settings**
- Click "⚙️ Settings" tab
- **Success Check:** Three sections visible:
  1. **Automatic Sync:** Checkbox, time picker (03:00), dropdown (Smart Sync)
  2. **Folder Configuration:** COMMAND_CENTER, COMMAND_CENTER/CONTEXT, ignore patterns
  3. **Advanced Options:** Chunk size (512), model (text-embedding-3-small), etc.

**Note:** Settings are display-only (grayed out). Editing will be implemented in future.

---

### Phase 6: Smart Sync Test (Optional - 2 minutes)

**18. Trigger Smart Sync**
- Go back to "📊 Overview" tab
- Click "⚡ Smart Sync" button

**19. Observe Smart Sync**
- **Success Check:**
  - Modal appears
  - Completes much faster than Full Sync
  - If no files changed: Shows 0 / 0 or immediate completion
  - "Updated" count is 0 or very low

---

## ✅ Success Criteria

### Must Pass:
- [ ] Can sign in with Google (no OAuth errors)
- [ ] All 3 tabs load without errors
- [ ] Preview shows folder structure from Google Drive
- [ ] Full Sync completes successfully
- [ ] Progress modal shows real-time updates
- [ ] Documents appear in Files tab grouped by folder
- [ ] CONTEXT files marked with green badge
- [ ] Settings tab displays configuration

### Should Pass:
- [ ] Session persists across refreshes
- [ ] Sync History updates after sync
- [ ] Smart Sync works correctly
- [ ] No "Application error" messages
- [ ] No browser console errors

---

## 🐛 Common Issues & Solutions

### "Application error: a client-side exception has occurred"
**Solution:** Hard refresh (Ctrl+Shift+R) or try incognito mode

### OAuth callback error
**Solution:** Verify GOOGLE_CLIENT_SECRET in Vercel matches Google Cloud Console

### Preview shows 0 folders
**Solution:**
- Verify COMMAND_CENTER folder has documents
- Check GOOGLE_DOCS_KB_FOLDER_ID in Railway
- Test: `curl -X POST https://api.wildfireranch.us/kb/preview`

### Sync fails or times out
**Solution:**
- Check error message in modal
- Verify Google Drive permissions
- Check Railway logs for backend errors

### Documents not in Files tab
**Solution:**
- Wait for sync to complete
- Refresh page (F5)
- Check: `curl https://api.wildfireranch.us/kb/documents`

---

## 📊 Testing Checklist

Copy this checklist and mark off as you test:

```
Authentication:
[ ] Sign in works
[ ] Session persists
[ ] No OAuth errors

Overview Tab:
[ ] Sync Status card displays
[ ] Preview card shows folders
[ ] Sync buttons work
[ ] Full Sync completes
[ ] Progress modal works
[ ] Sync History updates

Files Tab:
[ ] Documents grouped by folder
[ ] Document details correct
[ ] CONTEXT files badged
[ ] All synced docs visible

Settings Tab:
[ ] Auto-sync section displays
[ ] Folder config displays
[ ] Advanced options display

Optional Tests:
[ ] Smart Sync works
[ ] No errors in browser console
[ ] Session expires gracefully
```

---

## 🎉 Expected Results

### After Full Testing:
- ✅ All features working
- ✅ No errors or crashes
- ✅ Documents synced and browsable
- ✅ Real-time progress tracking
- ✅ Clean, intuitive UI

### You Should Have:
- **Authenticated session** with Google
- **Synced knowledge base** with all your documents
- **Browsable document library** organized by folder
- **Working sync buttons** for future updates
- **Preview capability** to see what will sync

---

## 📚 Reference Documentation

If you encounter issues or want more details:

- **[SESSION_018B_TESTING_GUIDE.md](/workspaces/CommandCenter/docs/SESSION_018B_TESTING_GUIDE.md)** - Detailed testing guide with troubleshooting
- **[SESSION_018B_FINAL_SUMMARY.md](/workspaces/CommandCenter/docs/SESSION_018B_FINAL_SUMMARY.md)** - Complete session summary
- **[SESSION_018B_RESOLUTION.md](/workspaces/CommandCenter/docs/SESSION_018B_RESOLUTION.md)** - OAuth debugging details

---

## 🚀 Next Steps After Testing

Once all tests pass:

1. **Use your KB!**
   - Ask agents questions about your documents
   - Agents will automatically search the KB

2. **Add more documents**
   - Add files to COMMAND_CENTER in Google Drive
   - Click "Smart Sync" to sync just the new/changed files

3. **Future enhancements** (planned):
   - Auto-sync cron job (3am MT)
   - Settings save functionality
   - Document preview/view
   - Search/filter in Files tab
   - Support for PDFs and Google Sheets

---

## 🍻 Celebrate!

If everything works, you have:
- ✅ Production-ready KB sync system
- ✅ Beautiful, functional dashboard
- ✅ Automated document ingestion
- ✅ Real-time progress tracking
- ✅ Organized document library

**Enjoy your new knowledge base system!** 🎊

---

**Last Updated:** Session 018B (October 8, 2025)
**Status:** All features deployed and functional
**User Feedback:** "It's totally working and it looks awesome!" ✨
