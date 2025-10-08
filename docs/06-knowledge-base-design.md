# Phase 1.5: Knowledge Base Design

**Date:** October 6, 2025
**Project:** CommandCenter V1
**Status:** ✅ **IMPLEMENTED & OPERATIONAL** (October 8, 2025)
**Previous:** Architecture Design Complete
**Implementation:** Sessions 018, 018B, 018C, 018D

---

## 🎉 Implementation Status (Updated October 8, 2025)

**✅ FULLY OPERATIONAL!** All core features implemented and tested in production.

**Current Stats:**
- 15 documents synced from Google Drive
- 141,889 tokens indexed with embeddings
- 4 folders: CONTEXT (Tier 1), Bret-ME, SolarShack, Wildfire.Green
- Real-time sync with progress tracking
- Automatic deletion detection
- Collapsible folder tree UI

**What Works:**
- ✅ Google OAuth authentication (service account + user OAuth)
- ✅ Full sync (all files) and Smart sync (changed only)
- ✅ Real-time progress via Server-Sent Events
- ✅ Deletion handling (removes files deleted from Drive)
- ✅ Multi-format support (Google Docs, PDFs, Sheets)
- ✅ Context file detection (CONTEXT folder)
- ✅ Vector search with pgvector (512-token chunks)
- ✅ Dashboard with Overview, Files, Settings tabs

**See Also:**
- [SESSION_018D_FILES_TAB_COMPLETION.md](SESSION_018D_FILES_TAB_COMPLETION.md) - Latest implementation
- [KB_ROADMAP.md](../KB_ROADMAP.md) - Future enhancements

---

## Executive Summary (Original Design)

CommandCenter's Knowledge Base syncs your Google Docs to provide agents with contextual knowledge about your ranch operations, business plans, and technical documentation. The system uses a **two-tier approach**: context files (always loaded) and searchable full knowledge base (retrieved on demand).

**Key Innovation:** Single Google SSO login provides both frontend authentication AND Google Drive/Docs access for KB sync.

---

## Requirements Summary

### **Must-Have (V1):** ✅ **ALL COMPLETE**
- ✅ Sync Google Drive "COMMAND_CENTER" folder to PostgreSQL
- ✅ Two-tier system: Context files (CONTEXT folder) + Full KB (searchable)
- ✅ Semantic search with pgvector embeddings (OpenAI)
- ✅ Manual Full & Smart sync buttons in frontend
- ✅ File listing with collapsible folder tree
- ✅ Google OAuth authentication with auto-redirect
- ✅ Real-time sync progress with SSE
- ✅ Deletion detection and cleanup
- ✅ Multi-format support (Docs, PDFs, Sheets)
- ⏳ Daily automatic sync (roadmap - Phase 1)
- ⏳ Citations in agent responses (basic search ready)

### **Nice-to-Have (V2):**
- ⏳ Two-way sync (write back to Google Docs)
- ⏳ Document version history
- ⏳ Access control per document
- ⏳ Analytics on most-queried topics

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│  User (Google Account)                              │
│  your-email@gmail.com                               │
└────────────────┬────────────────────────────────────┘
                 │ Google SSO
┌────────────────▼────────────────────────────────────┐
│  Frontend (Vercel - Next.js)                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  NextAuth.js (Google Provider)               │   │
│  │  - Restrict to your email                    │   │
│  │  - Get Drive/Docs access token               │   │
│  │  - Session management                        │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  /kb Page (Protected Route)                  │   │
│  │  - List synced files                         │   │
│  │  - Manual "Sync Now" button                  │   │
│  │  - Real-time progress display                │   │
│  │  - Error reporting                           │   │
│  └──────────────────┬───────────────────────────┘   │
└─────────────────────┼───────────────────────────────┘
                      │ HTTPS API calls
┌─────────────────────▼───────────────────────────────┐
│  Backend (Railway - FastAPI)                        │
│  ┌──────────────────────────────────────────────┐   │
│  │  Google Drive Integration                    │   │
│  │  - Use user's OAuth token                    │   │
│  │  - List "command-center" folder              │   │
│  │  - Fetch document content                    │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  KB Sync Service                             │   │
│  │  - Parse documents                           │   │
│  │  - Chunk content (512 tokens)                │   │
│  │  - Generate embeddings (OpenAI)              │   │
│  │  - Detect changes (delta sync)               │   │
│  └──────────────────┬───────────────────────────┘   │
│                     │                                │
│  ┌──────────────────▼───────────────────────────┐   │
│  │  PostgreSQL + pgvector                       │   │
│  │  - kb_documents (file metadata)              │   │
│  │  - kb_chunks (searchable chunks)             │   │
│  │  - kb_sync_log (sync history)                │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                      ↑
┌─────────────────────┴───────────────────────────────┐
│  CrewAI Agents                                      │
│  - Load context files on startup                    │
│  - Search KB when needed                            │
│  - Cite sources in responses                        │
└─────────────────────────────────────────────────────┘
```

---

## Two-Tier Knowledge System

### **Tier 1: Context Files (Always Loaded)**

**Location:** `command-center/context/` folder in Google Drive

**Files:**
- `personal.docx` - Personal info, preferences, contacts
- `solar-shack.docx` - Core solar system facts, thresholds
- `financial.docx` - Budget info, revenue targets, cost constraints

**Behavior:**
- Loaded into agent system prompt on startup
- Always available (no search needed)
- Fast access (no latency)
- Re-synced every 6 hours or on manual trigger
- Size limit: ~10-20 pages total (~5,000-10,000 tokens)

**Use Case:** Facts agents need for every decision
- Example: "Min SOC threshold is 30%"
- Example: "Peak power rates are 4-9pm weekdays"
- Example: "Emergency contact: [phone]"

### **Tier 2: Full Knowledge Base (Searchable)**

**Location:** Entire `command-center/` folder in Google Drive

**Folders:**
- `solar-shack-technical/` - Equipment manuals, configs
- `hvac/` - HVAC specifications
- `orchard/` - Orchard mapping, care schedules
- `irrigation/` - Irrigation specs, schedules
- `future-ranch-plans/` - House plans, expansion docs
- `wildfire-green-business/` - Business plans, projections

**Behavior:**
- Synced to database with embeddings
- Searched semantically when agent needs details
- Citations returned with results
- Re-synced daily at 3am or on manual trigger
- Size: Unlimited (currently ~140+ documents)

**Use Case:** Detailed info retrieved on demand
- Example: "What's the full procedure for SolArk grid charge mode?"
- Example: "Show me the electrical specs from house plans"
- Example: "What was Q3 revenue projection for Wildfire.Green?"

---

## Database Schema

```sql
-- Knowledge base documents table
CREATE TABLE kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    folder VARCHAR(255),              -- e.g., "solar-shack-technical"
    full_content TEXT,                -- Complete document text
    is_context_file BOOLEAN DEFAULT FALSE,  -- Tier 1 vs Tier 2
    token_count INTEGER,              -- For cost tracking
    last_synced TIMESTAMP,
    sync_error TEXT,                  -- Error message if sync failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Searchable chunks with embeddings
CREATE TABLE kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,    -- Position in document (0, 1, 2...)
    token_count INTEGER,
    embedding VECTOR(1536),           -- OpenAI text-embedding-3-small
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sync history log
CREATE TABLE kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50),            -- "full", "context-only", "manual"
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50),               -- "running", "completed", "failed"
    documents_processed INTEGER,
    documents_updated INTEGER,
    documents_failed INTEGER,
    error_message TEXT,
    triggered_by VARCHAR(100)         -- "cron", "user", "api"
);

-- Indexes for fast retrieval
CREATE INDEX idx_kb_documents_folder ON kb_documents(folder);
CREATE INDEX idx_kb_documents_context ON kb_documents(is_context_file);
CREATE INDEX idx_kb_chunks_document ON kb_chunks(document_id);
CREATE INDEX idx_kb_chunks_embedding ON kb_chunks 
    USING ivfflat (embedding vector_cosine_ops);
```

---

## Sync Pipeline

### **Daily Automatic Sync (3am Railway Cron)**

```python
@cron("0 3 * * *")  # Daily at 3am
async def scheduled_kb_sync():
    """
    Daily sync of entire knowledge base
    """
    await sync_knowledge_base(
        sync_type="full",
        force=False,  # Skip unchanged docs
        triggered_by="cron"
    )
```

### **Manual Sync (Frontend Button)**

```python
@router.post("/kb/sync")
async def trigger_manual_sync(
    sync_type: str = "full",  # "full" or "context-only"
    force: bool = False       # Re-sync even if unchanged
):
    """
    User-triggered sync from frontend
    Returns streaming progress updates
    """
    return StreamingResponse(
        sync_generator(sync_type, force),
        media_type="text/event-stream"
    )
```

### **Sync Process Flow**

```python
async def sync_knowledge_base(sync_type, force, triggered_by):
    """
    Main sync orchestrator
    """
    # 1. Log sync start
    sync_log_id = await log_sync_start(sync_type, triggered_by)
    
    try:
        # 2. Connect to Google Drive
        drive_service = get_drive_service(user_token)
        
        # 3. List files in command-center folder
        if sync_type == "context-only":
            files = list_files_in_folder("command-center/context")
        else:
            files = list_files_in_folder("command-center", recursive=True)
        
        # 4. For each file
        for file in files:
            # Check if changed since last sync (unless force=True)
            if not force and not file_changed_since_last_sync(file.id):
                continue  # Skip unchanged files
            
            # Fetch document content
            content = fetch_google_doc(file.id)
            
            # Parse and chunk
            chunks = chunk_document(content, chunk_size=512)
            
            # Generate embeddings
            embeddings = await generate_embeddings(chunks)
            
            # Store in database
            await store_document(
                google_doc_id=file.id,
                title=file.name,
                folder=file.folder,
                content=content,
                chunks=chunks,
                embeddings=embeddings,
                is_context_file=(file.folder == "context")
            )
            
            # Yield progress (for streaming response)
            yield {
                "current": current_index,
                "total": len(files),
                "current_file": file.name,
                "status": "processing"
            }
        
        # 5. Log sync completion
        await log_sync_complete(sync_log_id, success=True)
        
    except Exception as e:
        # Log sync failure
        await log_sync_complete(sync_log_id, success=False, error=str(e))
        raise
```

---

## Agent Integration

### **Context Files (Tier 1) - Always Available**

```python
# Agent startup loads context files
async def initialize_agent():
    """Load context files into agent system prompt"""
    
    # Fetch context files from database
    context_docs = await db.fetch_all("""
        SELECT title, full_content 
        FROM kb_documents 
        WHERE is_context_file = TRUE
        ORDER BY title
    """)
    
    # Build context string
    context = "\n\n".join([
        f"### {doc['title']}\n{doc['full_content']}"
        for doc in context_docs
    ])
    
    # Add to agent's system prompt
    agent = Agent(
        role="Energy Orchestrator",
        goal="Optimize off-grid energy usage",
        backstory=f"""
        You are an expert in off-grid energy systems.
        
        Here is important context you should always reference:
        
        {context}
        
        Use this information to make informed decisions.
        """,
        tools=[...],
        verbose=True
    )
    
    return agent
```

### **Full KB (Tier 2) - Search When Needed**

```python
# Agent tool for searching knowledge base
@tool("Search Knowledge Base")
def search_kb(query: str, limit: int = 5) -> dict:
    """
    Search knowledge base for relevant information
    
    Args:
        query: Natural language search query
        limit: Number of results to return (default 5)
    
    Returns:
        dict with results and citations
    """
    # Generate query embedding
    query_embedding = generate_embedding(query)
    
    # Semantic search in pgvector
    results = db.query("""
        SELECT 
            kc.chunk_text,
            kd.title,
            kd.folder,
            1 - (kc.embedding <=> %s) AS similarity
        FROM kb_chunks kc
        JOIN kb_documents kd ON kc.document_id = kd.id
        ORDER BY similarity DESC
        LIMIT %s
    """, query_embedding, limit)
    
    # Format response with citations
    return {
        "success": True,
        "query": query,
        "results": [
            {
                "content": r["chunk_text"],
                "source": r["title"],
                "folder": r["folder"],
                "similarity": r["similarity"]
            }
            for r in results
        ],
        "citations": [r["title"] for r in results]
    }
```

### **Agent Using KB Search**

```python
# Example: Agent needs procedure details
user_query = "How do I manually switch SolArk to battery mode?"

# Agent checks Tier 1 (context files)
# → Not in context files (too detailed)

# Agent searches Tier 2 (full KB)
kb_results = search_kb("SolArk battery mode manual procedure")

# Results returned:
# 1. "SolArk Controller Manual" (similarity: 0.92)
#    Content: "To switch to battery priority mode: 
#              1. Press Settings button...
#              2. Navigate to Operating Mode...
#              3. Select 'Battery Priority'..."
#
# 2. "Operating Modes Overview" (similarity: 0.87)
#    Content: "Battery mode uses battery first, grid backup..."

# Agent responds with context + citations
response = f"""
To manually switch your SolArk to battery mode:

1. Press the Settings button
2. Navigate to Operating Mode menu
3. Select 'Battery Priority'

This will prioritize battery discharge over grid usage. The system will 
still pull from grid if battery drops below your minimum SOC threshold (30%).

(Sources: SolArk Controller Manual, Operating Modes Overview)
"""
```

---

## Frontend: KB Sync Page

### **Page Location**
`vercel/app/kb/page.tsx` (protected route, requires Google SSO)

### **Features**

**1. Sync Status Overview**
- Last sync timestamp
- Total documents synced
- Context files count
- Full KB document count
- Error count (if any)

**2. Manual Sync Button**
- Trigger immediate sync
- Real-time progress bar
- Current file being processed
- Estimated time remaining
- Pause/Cancel options

**3. File Listing**
- Group by folder
- Show sync status per file (✅ synced, ⚠️ error)
- Last sync timestamp
- Token count (cost tracking)
- Click to view sync errors

**4. Search Preview**
- Test KB search directly from UI
- See what results agents would get
- Verify embeddings are working
- Debug retrieval quality

---

## Google SSO Implementation

### **NextAuth.js Configuration**

```typescript
// vercel/lib/auth.ts
import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
      authorization: {
        params: {
          scope: [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/documents.readonly'
          ].join(' ')
        }
      }
    })
  ],
  
  callbacks: {
    // Restrict to your email only
    async signIn({ user }) {
      const allowedEmail = process.env.ALLOWED_EMAIL;
      return user.email === allowedEmail;
    },
    
    // Include access token in session
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
      }
      return token;
    },
    
    async session({ session, token }) {
      session.accessToken = token.accessToken;
      return session;
    }
  }
};
```

### **Environment Variables**

```env
# Vercel (Frontend)
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
ALLOWED_EMAIL=your-email@gmail.com
NEXTAUTH_URL=https://your-frontend.vercel.app
NEXTAUTH_SECRET=random-secret-string

# Railway (Backend)
OPENAI_API_KEY=sk-...  # For embeddings
```

---

## Cost Estimation

### **One-Time Costs:**
- Initial sync of 140 documents
- Average 5,000 tokens per doc = 700,000 tokens
- Embedding cost: $0.0001 per 1K tokens
- **Total: ~$0.07** for initial sync

### **Ongoing Costs:**
- Daily sync of changed docs (~5-10 docs/day)
- 50,000 tokens/day = $0.005/day
- **Total: ~$0.15/month** for embeddings

### **Search Costs:**
- 100 searches/day
- Query embedding: 50 tokens each
- 5,000 tokens/day = $0.0005/day
- **Total: ~$0.015/month** for searches

### **Grand Total: <$1/month** for KB operations

---

## Security & Privacy

### **Access Control:**
- ✅ Google SSO restricts frontend to your email only
- ✅ OAuth token used for Drive/Docs access
- ✅ No API keys stored in Google Docs
- ✅ Database is private (Railway internal network)
- ✅ Session-based authentication

### **Data Handling:**
- ✅ Documents stored in your private PostgreSQL
- ✅ Embeddings are vectors (not readable text)
- ✅ Full content stored but only accessible via your account
- ✅ No external sharing or API exposure

### **Best Practices:**
- ⚠️ Don't store API keys in Google Docs (use Railway env vars)
- ⚠️ Don't store passwords in Google Docs (use secrets manager)
- ✅ Business/personal info is fine (private system)
- ✅ Consider encryption for highly sensitive docs (V2 feature)

---

## Testing Strategy

### **Unit Tests:**
- Google Drive file listing
- Document parsing
- Chunking logic (512 tokens)
- Embedding generation
- Database storage

### **Integration Tests:**
- Full sync pipeline
- Context file loading
- Semantic search accuracy
- Citation extraction
- Error handling

### **Manual Testing:**
- Sync from frontend button
- Verify all files synced
- Test search queries
- Check agent responses include citations
- Verify error reporting

---

## Success Metrics

**Technical:**
- [ ] 100% of docs synced without errors
- [ ] Sync completes in <10 minutes for 140 docs
- [ ] Search returns results in <200ms
- [ ] Embeddings cost <$1/month
- [ ] Zero data loss

**User Experience:**
- [ ] Can trigger sync with one click
- [ ] See sync progress in real-time
- [ ] Find any document via search
- [ ] Agents cite sources accurately
- [ ] No manual database work needed

---

## Next Steps

**Session 016 Implementation Plan:**

**Part 1: Google OAuth Setup** (45 min)
- Set up Google Cloud project
- Enable Drive + Docs APIs
- Configure NextAuth.js
- Test SSO login flow

**Part 2: KB Sync Backend** (1.5 hours)
- Google Drive integration
- Document fetching and parsing
- Chunking and embedding pipeline
- Database storage
- Streaming progress API

**Part 3: KB Sync Frontend** (1.5 hours)
- Protected /kb route
- File listing UI
- Manual sync button
- Real-time progress display
- Error handling and display

**Part 4: Agent Integration** (30 min)
- Load context files on agent startup
- Add search_kb tool
- Test agent queries
- Verify citations

**Total Time: ~4 hours**

---

## Appendix: Sample Context File

**Example: `context/solar-shack.docx`**

```
# Solar Shack Context

## System Overview
- Location: Utah ranch, off-grid
- Solar Array: 15kW capacity
- Battery: 40kWh total capacity
- Inverter: SolArk 15K

## Critical Thresholds
- Minimum SOC: 30% (never go below)
- Comfort SOC: 50% (normal operations)
- Target SOC: 80% (optimal)

## Operating Modes
- Battery Priority: Use battery first, grid backup
- Grid Priority: Use grid first, battery backup
- Off-Grid: Battery only, no grid

## Power Rates
- Peak: 4-9pm weekdays ($0.32/kWh)
- Off-Peak: All other times ($0.12/kWh)

## Key Loads
- Bitcoin Miners: 3kW (pausable)
- HVAC: 2.5kW (critical)
- House Base: 1.5kW (critical)

## Contacts
- Emergency: [your phone]
- Solar Installer: [contact]
- Utility: [contact]

## Preferences
- Prefer battery power during peak rates
- OK to use grid off-peak if SOC low
- Pause miners if SOC drops below 40%
- Never turn off HVAC (critical)
```

This context is always available to agents for instant reference.

---

**Knowledge Base Design Complete. Ready for Implementation in Session 016.**