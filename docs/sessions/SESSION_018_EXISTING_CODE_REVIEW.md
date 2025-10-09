# Session 018: Existing Code Review

**Date:** October 7, 2025
**Goal:** Understand existing KB sync code before adding recursive subfolder support
**Previous Session:** 017 (KB system implementation)

---

## 📁 File Locations

### Core KB Files:
1. **`railway/src/kb/google_drive.py`** - Google Drive/Docs API integration
2. **`railway/src/kb/sync.py`** - Main sync orchestration and search
3. **`railway/src/api/routes/kb.py`** - FastAPI endpoints
4. **`railway/src/tools/kb_search.py`** - CrewAI agent tool wrapper

---

## 🔍 Current Functionality

### What Works (From Session 017):

✅ **Google Drive Connection**
- Uses OAuth access token from NextAuth session
- Creates Drive API v3 and Docs API v1 services
- File: `railway/src/kb/google_drive.py`

✅ **File Listing (Non-Recursive)**
- Function: `list_files_in_folder(drive_service, folder_id, recursive=True)`
- **LIMITATION**: `recursive` parameter exists but is **NOT IMPLEMENTED**
- Currently only lists files in the **main folder** (direct children)
- Query: `'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'`
- Only fetches Google Docs, not subfolders

✅ **Document Fetching**
- Function: `fetch_document_content(docs_service, document_id)`
- Extracts text from Google Docs (paragraphs + tables)
- Returns full document content as string

✅ **Sync Pipeline**
- Function: `sync_knowledge_base(access_token, folder_id, sync_type, force)`
- Async generator that yields progress updates
- Checks if files changed since last sync (unless `force=True`)
- Chunks documents (512 tokens, 50 token overlap)
- Generates OpenAI embeddings
- Stores in PostgreSQL

✅ **Database Storage**
- Tables: `kb_documents`, `kb_chunks`, `kb_sync_log`
- Columns in `kb_documents`:
  - `id`, `google_doc_id`, `title`, `folder`
  - `full_content`, `is_context_file`, `token_count`
  - `last_synced`, `sync_error`, `created_at`, `updated_at`
- **NOTE**: `folder` column exists but is **NOT POPULATED** (missing in sync code)

✅ **Context File Detection**
- Currently checks if "context" is in filename: `is_context = "context" in file_name.lower()`
- **LIMITATION**: Should check folder path instead

✅ **Semantic Search**
- Function: `search_kb(query, limit)`
- Uses pgvector for similarity search
- Returns chunks with citations and folder info
- Works with existing data

---

## ⚠️ Current Limitations (The Gap)

### 1. **No Recursive Subfolder Support**

**Problem:**
```python
# railway/src/kb/google_drive.py:44-90
def list_files_in_folder(drive_service, folder_id, recursive: bool = True):
    """
    List all Google Docs in a folder.

    Args:
        recursive: Whether to search subfolders (TODO: implement)  # ← NOT IMPLEMENTED!
    """
    # Only lists files in main folder:
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"
```

**Impact:**
- User's folder structure:
  ```
  COMMAND_CENTER/
  ├── CONTEXT/              ← NOT synced (subfolder)
  ├── SolarShack/           ← NOT synced (subfolder)
  ├── TradingBot/           ← NOT synced (subfolder)
  ├── Wildfire.Green/       ← NOT synced (subfolder)
  └── [root docs]           ← WORKS (but user has none)
  ```
- Only files in root `COMMAND_CENTER/` folder are synced
- All subfolders (where actual docs are) are ignored

### 2. **Folder Path Not Tracked**

**Problem:**
```python
# railway/src/kb/sync.py:207-227
# Determine if context file (in "context" subfolder)
# For now, mark as context file if "context" is in the name
is_context = "context" in file_name.lower()  # ← Wrong approach!

# Store document
execute(conn, """
    INSERT INTO kb_documents (google_doc_id, title, full_content, token_count, last_synced, is_context_file)
    VALUES (%s, %s, %s, %s, NOW(), %s)
    ...
""", (file_id, file_name, content, len(content) // 4, is_context))
```

**Missing:**
- No folder path stored (e.g., `COMMAND_CENTER/SolarShack/manual.pdf`)
- No parent folder tracked (e.g., `SolarShack`)
- Context file detection uses filename, not folder location

**Database Impact:**
- `folder` column exists in schema but is **never populated**
- Can't group files by subfolder
- Can't filter by folder in search results

### 3. **No Ignore Pattern Support**

**Problem:**
- No way to skip folders like `old.CommandCenter`
- Would sync everything, including archived/unwanted files

### 4. **No Preview/Dry-Run Mode**

**Problem:**
- Can't see what WOULD be synced before actually syncing
- Risky for large folder structures (142 files)

---

## 🛠️ What Needs to Change

### Enhancement 1: Recursive Folder Traversal

**File:** `railway/src/kb/google_drive.py`

**Add new function:**
```python
async def list_files_recursive(
    drive_service,
    folder_id: str,
    ignore_patterns: list[str] = ["old.*"],
    current_path: str = "COMMAND_CENTER"
) -> list[dict]:
    """
    Recursively list all files in folder and subfolders.

    Returns:
        List of file dicts with metadata including:
        - id, name, mimeType, modifiedTime, parents
        - path: Full path (e.g., "COMMAND_CENTER/SolarShack/manual.pdf")
        - folder: Immediate parent folder (e.g., "SolarShack")
    """
    # 1. List all items (files + folders)
    # 2. For each folder, recurse into it
    # 3. Track full path as we descend
    # 4. Skip folders matching ignore patterns
    # 5. Return all files with their paths
```

**Key changes:**
- Support all file types (not just Google Docs)
- Track full path
- Skip ignored folders
- Handle pagination

### Enhancement 2: Store Folder Paths

**File:** `railway/src/kb/sync.py`

**Update sync to store paths:**
```python
# Get folder name from path
folder_name = file.get('folder', 'unknown')  # From enhanced list function
folder_path = file.get('path', file_name)   # Full path

# Detect context files by folder path
is_context = '/CONTEXT/' in folder_path.upper() or folder_name.upper() == 'CONTEXT'

# Store with folder info
execute(conn, """
    INSERT INTO kb_documents (
        google_doc_id, title, folder, folder_path,
        full_content, token_count, last_synced, is_context_file
    )
    VALUES (%s, %s, %s, %s, %s, %s, NOW(), %s)
    ...
""", (file_id, file_name, folder_name, folder_path, content, token_count, is_context))
```

### Enhancement 3: Database Schema Updates

**File:** Database migration (via psql)

**Add missing columns:**
```sql
-- Add folder_path if it doesn't exist
ALTER TABLE kb_documents ADD COLUMN IF NOT EXISTS folder_path VARCHAR(1000);

-- Update existing records to mark context files correctly
UPDATE kb_documents
SET is_context_file = TRUE
WHERE folder = 'CONTEXT' OR folder_path LIKE '%/CONTEXT/%';
```

**NOTE:** `folder` column already exists in schema, just needs to be populated!

### Enhancement 4: Preview Mode Endpoint

**File:** `railway/src/api/routes/kb.py`

**Add new endpoint:**
```python
@router.post("/preview")
async def preview_sync(authorization: str = Header(None)):
    """
    Dry run - shows what WOULD be synced without actually syncing.

    Returns:
        - Folder structure
        - File list with estimates
        - Token estimates
        - Ignored folders
    """
    # Reuse enhanced recursive list function
    # Analyze files (estimate tokens, calculate costs)
    # Group by folder
    # Return summary (don't actually sync)
```

---

## 📊 Database Schema (Current)

From Session 017 implementation:

```sql
CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    folder VARCHAR(255),              -- ✅ Exists but NOT POPULATED
    full_content TEXT,
    is_context_file BOOLEAN DEFAULT FALSE,
    token_count INTEGER,
    last_synced TIMESTAMP,
    sync_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50),
    documents_processed INTEGER,
    documents_updated INTEGER,
    documents_failed INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(100)
);
```

**Schema Enhancement Needed:**
- ✅ `folder` column exists (just needs to be populated)
- ⚠️ Need to add `folder_path` column for full paths

---

## 🎯 Implementation Strategy

### Phase 1: Enhance Google Drive Integration (30 min)
1. Create `list_files_recursive()` function
2. Support all file types (not just Google Docs)
3. Track full paths and parent folders
4. Implement ignore patterns

### Phase 2: Update Sync Pipeline (30 min)
1. Use new recursive list function
2. Store `folder` and `folder_path` in database
3. Fix context file detection (use folder path)
4. Handle different file types (PDF, Sheets, etc.)

### Phase 3: Add Preview Mode (30 min)
1. Create `/kb/preview` endpoint
2. Analyze files without syncing
3. Return folder structure and estimates
4. Show what would be ignored

### Phase 4: Database Migration (15 min)
1. Add `folder_path` column
2. Update existing records with folder info
3. Create indexes if needed

### Phase 5: Testing (45 min)
1. Test preview mode
2. Test CONTEXT folder sync (small test)
3. Test full recursive sync
4. Verify all folders synced
5. Test search across folders

---

## ✅ Verification Checklist

Before starting enhancement:
- [x] Found all KB-related files
- [x] Understood current sync flow
- [x] Identified exact limitation (no recursive support)
- [x] Confirmed database schema
- [x] Documented what needs to change

After enhancement:
- [ ] Recursive folder traversal works
- [ ] All subfolders detected (CONTEXT, SolarShack, etc.)
- [ ] `folder` and `folder_path` columns populated
- [ ] `old.CommandCenter` ignored
- [ ] Preview mode returns accurate file list
- [ ] Search works across folders
- [ ] Agent can cite sources from subfolders

---

## 🚀 Ready to Implement

**Key Insight:** The infrastructure is already there! We just need to:
1. Make the recursive listing actually work (currently stubbed out)
2. Populate the `folder` column (already exists in schema)
3. Add `folder_path` column for full paths
4. Fix context file detection to use folder location

**Risk Level:** Low
- Not breaking existing functionality
- Database schema mostly supports it
- Just enhancing existing code

**Estimated Time:** 2-3 hours (including testing)

---

**Next Step:** Begin implementation with recursive folder traversal enhancement.
