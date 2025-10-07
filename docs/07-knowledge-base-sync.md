# Knowledge Base Sync - Implementation Plan

**Date:** October 7, 2025  
**Status:** Ready to Build  
**User Folder Structure Confirmed:** ✅

---

## 📁 Confirmed Folder Structure

```
COMMAND_CENTER/
├── CONTEXT/              ← Tier 1: Always loaded into agents
├── SolarShack/           ← Tier 2: Full KB (searchable)
├── TradingBot/           ← Tier 2: Full KB
├── Wildfire.Green/       ← Tier 2: Full KB
├── Working Files/        ← Tier 2: Full KB
├── Pictures/             ← Tier 2: Full KB (image text extraction?)
├── old.CommandCenter/    ← IGNORE (starts with "old.")
└── Wildfire.Green Financial Model (Google Sheet)  ← Convert to text
```

---

## 🎯 Implementation Phases

### **Phase 1: Dry Run / Preview Mode** (Build First)
Before syncing anything, show user what WOULD be synced

### **Phase 2: Context Folder Only** (Test with Small Set)
Sync just CONTEXT/ folder to verify everything works

### **Phase 3: Full Sync** (Production Ready)
Sync entire COMMAND_CENTER/ with all file types

---

## 📋 File Type Support

### **Supported File Types:**

| Type | Method | Status |
|------|--------|--------|
| Google Docs | Drive API → export as text | ✅ Easy |
| Google Sheets | Drive API → export as CSV, parse | ✅ Medium |
| PDFs | Drive API → download, extract text | ✅ Medium |
| Word Docs (.docx) | Drive API → convert to text | ✅ Easy |
| Plain Text | Drive API → read directly | ✅ Easy |
| Images (jpg/png) | OCR with Google Vision API? | ⏳ V2 |

### **File Types to Ignore:**
- Folders starting with `old.`
- Images (unless you want OCR?)
- Videos
- Archives (zip, tar)
- Executables

---

## 🔍 Phase 1: Dry Run / Preview Mode

### **What It Does:**
Shows exactly what will be synced WITHOUT actually syncing

### **API Endpoint:**
```
POST /kb/preview
```

### **Response Format:**
```json
{
  "total_folders": 6,
  "total_files": 142,
  "estimated_tokens": 750000,
  "estimated_cost": "$0.075",
  "folders": [
    {
      "name": "CONTEXT",
      "path": "COMMAND_CENTER/CONTEXT",
      "file_count": 3,
      "tier": "context",
      "files": [
        {
          "name": "personal.docx",
          "type": "google_doc",
          "size": "25 KB",
          "estimated_tokens": 5000,
          "last_modified": "2025-10-05T14:30:00Z",
          "status": "ready"
        },
        {
          "name": "solar-shack.docx",
          "type": "google_doc",
          "size": "18 KB",
          "estimated_tokens": 3500,
          "last_modified": "2025-10-04T09:15:00Z",
          "status": "ready"
        }
      ]
    },
    {
      "name": "SolarShack",
      "path": "COMMAND_CENTER/SolarShack",
      "file_count": 23,
      "tier": "full_kb",
      "files": [...]
    }
  ],
  "ignored": [
    {
      "name": "old.CommandCenter",
      "reason": "Starts with 'old.'"
    }
  ],
  "warnings": [
    {
      "file": "huge_manual.pdf",
      "warning": "File exceeds 50k tokens, will be truncated"
    }
  ]
}
```

### **Frontend UI - Preview Mode:**

```
┌─────────────────────────────────────────────────────────┐
│  📊 Knowledge Base Sync Preview                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📁 Folders: 6    📄 Files: 142                        │
│  💰 Estimated Cost: $0.075                             │
│  ⏱️  Estimated Time: ~8 minutes                        │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  📂 CONTEXT/ (3 files) - Tier 1: Context Files         │
│     ✅ personal.docx (5,000 tokens)                    │
│     ✅ solar-shack.docx (3,500 tokens)                 │
│     ✅ financial.docx (4,200 tokens)                   │
│                                                         │
│  📂 SolarShack/ (23 files) - Tier 2: Full KB          │
│     ✅ Controller_Manual.pdf (8,500 tokens)            │
│     ✅ Wiring_Diagram.docx (2,300 tokens)              │
│     ... (21 more files)                                │
│                                                         │
│  📂 TradingBot/ (12 files) - Tier 2: Full KB          │
│     ✅ Strategy_Overview.docx (3,200 tokens)           │
│     ... (11 more files)                                │
│                                                         │
│  🚫 Ignored:                                           │
│     ❌ old.CommandCenter/ (starts with 'old.')        │
│                                                         │
│  ⚠️  Warnings:                                          │
│     ⚠️  huge_manual.pdf exceeds 50k tokens             │
│                                                         │
│  [🔄 Run Sync]  [❌ Cancel]                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 Phase 2: Sync Execution

### **Sync Options:**

**1. Full Sync (All Files)**
- Re-syncs everything, even unchanged files
- Use case: First sync, or major changes
- Button: "🔄 Full Sync"

**2. Smart Sync (Changed Only)**
- Only syncs files that changed since last sync
- Use case: Nightly auto-sync, quick updates
- Button: "⚡ Smart Sync"

**3. Error Recovery Sync**
- Only re-syncs files that had errors last time
- Use case: Fix failed files without full re-sync
- Button: "🔧 Retry Failed"

### **Sync Process Flow:**

```python
async def sync_knowledge_base(
    sync_type: str,  # "full", "smart", "error_only"
    folder_filter: str = None,  # Optional: "CONTEXT" for testing
    triggered_by: str = "manual"  # "manual", "cron", "api"
):
    # 1. Create sync log entry
    sync_id = await create_sync_log(sync_type, triggered_by)
    
    # 2. List all files from Google Drive
    all_files = await list_drive_files("COMMAND_CENTER")
    
    # 3. Filter out ignored folders
    files = filter_files(all_files, ignore_patterns=["old.*"])
    
    # 4. Filter based on sync type
    if sync_type == "smart":
        files = [f for f in files if file_changed_since_last_sync(f)]
    elif sync_type == "error_only":
        files = [f for f in files if file_had_error_last_sync(f)]
    
    # 5. If folder_filter specified (testing), filter to that folder
    if folder_filter:
        files = [f for f in files if f.path.startswith(folder_filter)]
    
    # 6. Process each file
    for i, file in enumerate(files):
        try:
            # Yield progress for streaming UI
            yield {
                "status": "processing",
                "current": i + 1,
                "total": len(files),
                "file": file.name,
                "folder": file.folder,
                "step": "fetching"
            }
            
            # Fetch content based on file type
            content = await fetch_file_content(file)
            
            yield {"step": "chunking"}
            chunks = chunk_content(content, chunk_size=512)
            
            yield {"step": "embedding"}
            embeddings = await generate_embeddings(chunks)
            
            yield {"step": "storing"}
            await store_in_database(file, content, chunks, embeddings)
            
            yield {"step": "complete", "status": "success"}
            
        except Exception as e:
            # Log error but continue with next file
            await log_file_error(sync_id, file.id, str(e))
            yield {"step": "error", "error": str(e)}
            continue
    
    # 7. Finalize sync log
    await finalize_sync_log(sync_id)
```

---

## 🎨 Frontend: Single-Page KB Dashboard

### **Page Layout: `/kb`**

```
┌────────────────────────────────────────────────────────────────┐
│  📚 Knowledge Base                                             │
│  ┌─────────────┬─────────────┬─────────────┐                  │
│  │ 📊 Overview │ 📁 Files    │ ⚙️  Settings │                  │
│  └─────────────┴─────────────┴─────────────┘                  │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  📊 OVERVIEW TAB                                               │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Sync Status                                             │ │
│  │  ✅ Last Sync: Oct 7, 2025 3:00 AM MT (4 hours ago)     │ │
│  │  📄 Documents: 142 synced, 3 context files              │ │
│  │  💰 Total Tokens: 750,000 (~$0.08 embeddings)           │ │
│  │                                                          │ │
│  │  [🔄 Full Sync]  [⚡ Smart Sync]  [🔧 Retry Failed]     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  Recent Sync History (Last 5)                            │ │
│  │  ┌────────────────────────────────────────────────────┐ │ │
│  │  │ Oct 7, 3:00 AM  │ Auto    │ ✅ Success │ 5 updated │ │ │
│  │  │ Oct 6, 3:00 AM  │ Auto    │ ✅ Success │ 2 updated │ │ │
│  │  │ Oct 5, 9:45 PM  │ Manual  │ ✅ Success │ 142 new   │ │ │
│  │  │ Oct 5, 9:30 PM  │ Manual  │ ⚠️  Partial│ 3 errors  │ │ │
│  │  │ Oct 5, 9:15 PM  │ Manual  │ ❌ Failed  │ View log  │ │ │
│  │  └────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

### **Files Tab:**

```
┌────────────────────────────────────────────────────────────────┐
│  📁 FILES TAB                                                  │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 🔍 Search files...                          [Filter ▼]   │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📂 CONTEXT/ (Tier 1: Context Files) - 3 files               │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ✅ personal.docx          Oct 5, 2:30 PM  │ 5,000 tokens│   │
│  │ ✅ solar-shack.docx       Oct 4, 9:15 AM  │ 3,500 tokens│   │
│  │ ✅ financial.docx         Oct 3, 4:20 PM  │ 4,200 tokens│   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  📂 SolarShack/ (Tier 2: Full KB) - 23 files                 │
│  ┌────────────────────────────────────────────────────────┐   │
│  │ ✅ Controller_Manual.pdf  Oct 1, 8:00 AM  │ 8,500 tokens│   │
│  │ ✅ Wiring_Diagram.docx    Sep 28, 3:45 PM │ 2,300 tokens│   │
│  │ ... (collapsed, click to expand)                        │   │
│  └────────────────────────────────────────────────────────┘   │
│                                                                │
│  📂 TradingBot/ (Tier 2: Full KB) - 12 files                 │
│  📂 Wildfire.Green/ (Tier 2: Full KB) - 48 files             │
│  📂 Working Files/ (Tier 2: Full KB) - 56 files              │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Sync Progress Modal (Popup)

When user clicks "Full Sync" or "Smart Sync", show this popup:

```
┌─────────────────────────────────────────────────────┐
│  🔄 Syncing Knowledge Base...                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Progress: 47 / 142 documents (33%)                │
│  ████████░░░░░░░░░░░░                              │
│                                                     │
│  Currently processing:                             │
│  📄 SolarShack/Apple_Tree_Mapping.docx             │
│     ✅ Fetching content... Done                    │
│     ✅ Chunking... Done (12 chunks)                │
│     ✅ Generating embeddings... Done               │
│     🔄 Storing in database...                      │
│                                                     │
│  Completed Folders:                                │
│  ✅ CONTEXT/ (3 docs)                              │
│  ✅ SolarShack/ (23 docs)                          │
│  🔄 TradingBot/ (5 of 12 docs)                     │
│  ⏳ Wildfire.Green/ (queued)                       │
│  ⏳ Working Files/ (queued)                        │
│                                                     │
│  ⏱️  Elapsed: 2m 15s  |  ETA: 4m 30s              │
│                                                     │
│  [⏸️  Pause] [❌ Cancel]                           │
└─────────────────────────────────────────────────────┘
```

### **After Completion:**

```
┌─────────────────────────────────────────────────────┐
│  ✅ Sync Complete!                                  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  📊 Summary:                                        │
│  ✅ Successfully synced: 139 documents             │
│  ⚠️  Warnings: 2 files                             │
│  ❌ Errors: 1 file                                 │
│                                                     │
│  ⏱️  Total Time: 6m 45s                            │
│  💰 Embedding Cost: $0.073                         │
│                                                     │
│  ⚠️  Warnings:                                      │
│  • huge_manual.pdf: Truncated (exceeded 50k tokens)│
│  • old_diagram.jpg: Skipped (image files not       │
│    supported yet)                                  │
│                                                     │
│  ❌ Errors:                                         │
│  • corrupted_file.docx: Failed to parse            │
│    (retry individually?)                           │
│                                                     │
│  [📋 View Detailed Log]  [✅ Close]                │
└─────────────────────────────────────────────────────┘
```

---

## ⚙️ Settings & Configuration

### **Settings Tab:**

```
┌────────────────────────────────────────────────────────────────┐
│  ⚙️  SETTINGS TAB                                              │
│                                                                │
│  🔄 Automatic Sync                                             │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ ☑️  Enable nightly auto-sync                             │ │
│  │ ⏰ Time: [3:00 AM] [Mountain Time ▼]                     │ │
│  │ 📋 Sync type: [Smart Sync (changed only) ▼]             │ │
│  │ 📧 Notify on errors: [✅ Email] [✅ In-app]              │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📁 Folder Configuration                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 📂 Root folder: COMMAND_CENTER                           │ │
│  │ 🏷️  Context folder: COMMAND_CENTER/CONTEXT              │ │
│  │ 🚫 Ignore patterns: old.*, archive/*, temp/*            │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  🎛️  Advanced Options                                         │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │ 📏 Chunk size: [512] tokens                              │ │
│  │ 🤖 Embedding model: [text-embedding-3-small ▼]          │ │
│  │ ⚠️  Max file size: [50,000] tokens                       │ │
│  │ 🔄 Concurrent uploads: [5] files at once                │ │
│  │ ⏱️  Rate limit: [10] requests/second                     │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  [💾 Save Settings]                                            │
└────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Rate Limiting & Safety

### **Google Drive API Limits:**
- User quota: 1,000 requests per 100 seconds
- Our limit: 10 requests/second = 600/minute (well under quota)
- Conservative: 5 files processed concurrently

### **OpenAI Embedding API Limits:**
- Tier 1: 3,000 requests/minute, 1M tokens/minute
- Our usage: ~150 files/sync = ~150 requests/minute (safe)
- Batching: Process 10 chunks at once

### **Error Handling:**
```python
# Google Drive rate limit (429)
if response.status == 429:
    retry_after = int(response.headers.get('Retry-After', 60))
    await asyncio.sleep(retry_after)
    return await retry_request()

# OpenAI rate limit (429)
if response.status == 429:
    await asyncio.sleep(60)  # Wait 1 minute
    return await retry_request()

# Connection timeout
try:
    response = await asyncio.wait_for(request(), timeout=30)
except asyncio.TimeoutError:
    log_error("timeout")
    return {"error": "timeout"}
```

---

## 🗄️ Database Updates

### **New Tables:**

```sql
-- Sync configuration (stored in DB, editable via UI)
CREATE TABLE kb_sync_config (
    id SERIAL PRIMARY KEY,
    auto_sync_enabled BOOLEAN DEFAULT TRUE,
    auto_sync_time TIME DEFAULT '03:00:00',
    auto_sync_timezone VARCHAR(50) DEFAULT 'America/Denver',
    sync_type VARCHAR(20) DEFAULT 'smart',  -- 'full', 'smart', 'error_only'
    root_folder VARCHAR(255) DEFAULT 'COMMAND_CENTER',
    context_folder VARCHAR(255) DEFAULT 'COMMAND_CENTER/CONTEXT',
    ignore_patterns TEXT[],  -- ['old.*', 'archive/*']
    chunk_size INTEGER DEFAULT 512,
    max_file_tokens INTEGER DEFAULT 50000,
    concurrent_uploads INTEGER DEFAULT 5,
    rate_limit_per_second INTEGER DEFAULT 10,
    notify_on_errors BOOLEAN DEFAULT TRUE,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Sync history (keep last 50 syncs)
CREATE TABLE kb_sync_history (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),
    triggered_by VARCHAR(100),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50),  -- 'running', 'completed', 'partial', 'failed'
    total_files INTEGER,
    files_processed INTEGER,
    files_succeeded INTEGER,
    files_failed INTEGER,
    files_skipped INTEGER,
    total_tokens INTEGER,
    estimated_cost DECIMAL(10,6),
    error_summary TEXT
);

-- Per-file sync details
CREATE TABLE kb_file_sync_details (
    id SERIAL PRIMARY KEY,
    sync_id INTEGER REFERENCES kb_sync_history(id),
    file_id VARCHAR(255),
    file_name VARCHAR(500),
    file_path VARCHAR(1000),
    status VARCHAR(50),  -- 'success', 'error', 'skipped'
    error_message TEXT,
    tokens_processed INTEGER,
    processing_time_ms INTEGER,
    synced_at TIMESTAMP DEFAULT NOW()
);
```

---

## 🚀 Implementation Order

### **Session 1: Backend Foundation** (2 hours)
1. Google Drive API integration
   - List files recursively
   - Filter by ignore patterns
   - Detect file type (Docs, Sheets, PDFs)
2. File content fetching
   - Google Docs → text
   - Google Sheets → CSV → text
   - PDFs → text extraction
3. Preview mode endpoint
   - Return file list with estimates
   - No actual syncing yet

### **Session 2: Frontend Dashboard** (2 hours)
1. Create `/kb` page with three tabs
2. Overview tab with stats and sync buttons
3. Files tab with folder tree view
4. Settings tab with configuration
5. Connect to backend preview endpoint

### **Session 3: Sync Pipeline** (2 hours)
1. Implement sync logic
   - Chunking (512 tokens)
   - Embedding generation (OpenAI)
   - Database storage
2. Streaming progress updates (SSE)
3. Error handling and logging

### **Session 4: Sync UI & Testing** (1.5 hours)
1. Implement sync progress modal
2. Real-time progress updates
3. Test with CONTEXT folder only
4. Verify preview → sync → verify flow

### **Session 5: Auto-Sync & Polish** (1 hour)
1. Railway cron job setup (3am MT)
2. Error notifications
3. Sync history display
4. Final testing with full folder

---

## ✅ Testing Checklist

### **Phase 1: Dry Run**
- [ ] Preview shows all folders correctly
- [ ] CONTEXT/ marked as Tier 1
- [ ] old.CommandCenter ignored
- [ ] Token estimates accurate
- [ ] Cost estimates reasonable

### **Phase 2: Context Folder Only**
- [ ] Sync 3 files from CONTEXT/
- [ ] All files stored in database
- [ ] Embeddings generated
- [ ] Searchable via pgvector
- [ ] No errors logged

### **Phase 3: Full Sync**
- [ ] All 142 files synced
- [ ] Different file types handled (Docs, Sheets, PDFs)
- [ ] Progress updates work
- [ ] Errors logged but don't stop sync
- [ ] Final summary accurate

### **Phase 4: Smart Sync**
- [ ] Only changed files re-synced
- [ ] Unchanged files skipped
- [ ] Deleted files removed from DB
- [ ] Faster than full sync

### **Phase 5: Auto Sync**
- [ ] Runs at 3am MT
- [ ] Uses smart sync by default
- [ ] Logs to sync history
- [ ] Notifications sent on errors

---

## 💡 Future Enhancements (V2)

- [ ] OCR for images (Google Vision API)
- [ ] Two-way sync (write back to Google Docs)
- [ ] Document version history
- [ ] Access control per document
- [ ] Analytics on most-queried topics
- [ ] Collaborative editing notifications
- [ ] Export KB to other formats

---

**Ready to start building? Let's begin with Session 1: Backend Foundation + Preview Mode!**