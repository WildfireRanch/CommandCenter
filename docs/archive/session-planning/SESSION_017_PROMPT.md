# Session 017: Knowledge Base Testing & Agent Integration

**Date:** October 7, 2025+
**Previous Session:** Session 016 - KB Implementation (COMPLETE ✅)
**Duration:** ~2-3 hours
**Type:** Testing, Integration, Production Polish

---

## 🎯 Session Goals

**Primary Objectives:**
1. ✅ Test KB system end-to-end (Google SSO → Sync → Display)
2. ✅ Integrate KB search with CrewAI agents
3. ✅ Load context files into agent system prompts
4. ✅ Add automatic daily sync (optional)
5. ✅ Production polish and error handling

---

## 📊 What Was Built in Session 016

### **Complete Knowledge Base System:**

**Backend (Railway):**
- ✅ Google Drive/Docs API integration
- ✅ KB sync service (chunk, embed, store)
- ✅ Semantic search with pgvector
- ✅ API endpoints: `/kb/sync`, `/kb/documents`, `/kb/search`, `/kb/stats`

**Frontend (Vercel):**
- ✅ NextAuth.js Google SSO
- ✅ `/kb` page with real-time sync progress
- ✅ Document listing with metadata
- ✅ Protected routes (email-restricted)

**Database:**
- ✅ `kb_documents` - Document metadata and full content
- ✅ `kb_chunks` - Text chunks with embeddings (1536 dimensions)
- ✅ `kb_sync_log` - Sync history tracking

**Status:** Code deployed, waiting for testing!

---

## 🧪 Part 1: End-to-End Testing (45 min)

### **Test 1: Google SSO Authentication**

**Steps:**
1. Visit https://mcp.wildfireranch.us/kb
2. You should see "Sign in with Google" button
3. Click it
4. Sign in with your Google account
5. Should redirect back to /kb page (authenticated)

**Verify:**
- ✅ Only your allowed email can sign in
- ✅ Other emails are rejected with clear error
- ✅ Session persists after page reload
- ✅ Access token is present in session

**If Issues:**
- Check `ALLOWED_EMAIL` matches your actual email
- Verify OAuth redirect URI in Google Cloud Console
- Check Vercel environment variables are set

---

### **Test 2: Manual KB Sync**

**Steps:**
1. On /kb page (authenticated), click "Sync Now"
2. Watch real-time progress updates
3. Wait for sync to complete

**Verify:**
- ✅ Progress updates appear (current file being processed)
- ✅ Document count increases
- ✅ Sync completes successfully
- ✅ Documents appear in the list below
- ✅ Context files have green badge
- ✅ Token counts displayed
- ✅ Last sync timestamp shown

**Expected Results:**
- All documents from your Google Drive folder synced
- Each document chunked (~512 tokens per chunk)
- Embeddings generated for all chunks
- Stored in PostgreSQL with pgvector

**If Issues:**
- Check Google Drive folder ID in Railway env vars
- Verify OAuth scopes include Drive.readonly and Docs.readonly
- Check Railway logs for errors: `railway logs`

---

### **Test 3: KB Search (via API)**

**Test search endpoint directly:**

```bash
# Search for solar-related documents
curl -X POST https://api.wildfireranch.us/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query": "solar battery threshold", "limit": 5}' | jq

# Expected response:
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
    ...
  ],
  "citations": ["solar-shack-context.docx", ...]
}
```

**Verify:**
- ✅ Semantic search works (finds relevant chunks)
- ✅ Similarity scores make sense (0.0-1.0)
- ✅ Citations include source documents
- ✅ Results ranked by relevance
- ✅ Response time < 200ms

---

### **Test 4: KB Stats**

```bash
# Get KB statistics
curl https://api.wildfireranch.us/kb/stats | jq

# Expected:
{
  "status": "success",
  "documents": {
    "total_documents": 20,
    "context_files": 3,
    "searchable_files": 17,
    "total_tokens": 50000,
    "last_sync_time": "2025-10-07T03:00:00"
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

**Verify:**
- ✅ Counts match reality
- ✅ Chunk math makes sense (chunks ≈ total_tokens / 512)
- ✅ All syncs successful

---

## 🤖 Part 2: Agent Integration (60 min)

### **Option A: Add search_kb Tool to CrewAI Agent**

**Create a CrewAI tool wrapper:**

**File:** `railway/src/tools/kb_search.py`

```python
from crewai_tools import tool
from ..kb.sync import search_kb

@tool("Search Knowledge Base")
def search_knowledge_base(query: str) -> str:
    """
    Search the knowledge base for relevant information.

    Use this tool when you need detailed information about:
    - Solar system specifications
    - Battery thresholds and limits
    - Operating procedures
    - Ranch infrastructure
    - Business plans

    Args:
        query: Natural language search query

    Returns:
        Relevant information with source citations
    """
    result = search_kb(query, limit=5)

    if not result.get("success"):
        return f"Search failed: {result.get('error', 'Unknown error')}"

    # Format results with citations
    chunks = result.get("results", [])
    citations = result.get("citations", [])

    if not chunks:
        return "No relevant information found in knowledge base."

    # Build response
    response = "Here's what I found:\n\n"

    for i, chunk in enumerate(chunks, 1):
        response += f"{i}. {chunk['content']}\n"
        response += f"   Source: {chunk['source']} (similarity: {chunk['similarity']:.2f})\n\n"

    response += f"\nSources consulted: {', '.join(citations)}"

    return response
```

**Update agent to use the tool:**

**File:** `railway/src/agents/solar_controller.py`

```python
from ..tools.kb_search import search_knowledge_base

def create_energy_crew(user_query: str, context: dict):
    """Create crew with KB search tool."""

    agent = Agent(
        role="Energy Systems Monitor",
        goal="Monitor and optimize off-grid solar energy system",
        backstory="""
        You are an expert in off-grid energy systems with deep knowledge
        of solar power, battery management, and energy optimization.

        You have access to a knowledge base with detailed information about
        the system specifications, operating procedures, and best practices.

        When you need specific details, use the Search Knowledge Base tool.
        Always cite your sources when referencing information from the KB.
        """,
        tools=[
            get_solark_data,
            search_knowledge_base,  # NEW!
        ],
        verbose=True,
        llm=ChatOpenAI(model="gpt-4o", temperature=0.3)
    )

    # ... rest of crew setup
```

**Test it:**

```bash
# Ask agent a question requiring KB lookup
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum battery SOC threshold and why?"}' | jq

# Expected: Agent uses search_knowledge_base tool, returns answer with citation
```

---

### **Option B: Load Context Files into System Prompt**

**For critical information that should always be available:**

**File:** `railway/src/kb/context.py`

```python
from ..utils.db import get_connection, query_all

def load_context_files() -> str:
    """
    Load all context files into a formatted string.

    Context files are marked with is_context_file=TRUE and contain
    critical information that agents should always have access to.

    Returns:
        Formatted string with all context file content
    """
    conn = get_connection()

    context_docs = query_all(
        conn,
        """
        SELECT title, full_content
        FROM kb_documents
        WHERE is_context_file = TRUE
        ORDER BY title
        """,
        as_dict=True
    )

    conn.close()

    if not context_docs:
        return ""

    # Format as markdown sections
    context = "\n\n## KNOWLEDGE BASE CONTEXT\n\n"
    context += "The following information is critical system knowledge:\n\n"

    for doc in context_docs:
        context += f"### {doc['title']}\n\n"
        context += f"{doc['full_content']}\n\n"
        context += "---\n\n"

    return context
```

**Update agent creation:**

```python
from ..kb.context import load_context_files

def create_energy_crew(user_query: str, context: dict):
    """Create crew with context files loaded."""

    # Load context files once at crew creation
    kb_context = load_context_files()

    agent = Agent(
        role="Energy Systems Monitor",
        goal="Monitor and optimize off-grid solar energy system",
        backstory=f"""
        You are an expert in off-grid energy systems.

        {kb_context}

        Use this information to make informed decisions.
        Always reference specific thresholds and values from the context above.
        """,
        tools=[get_solark_data],
        verbose=True,
        llm=ChatOpenAI(model="gpt-4o", temperature=0.3)
    )

    # ... rest of crew setup
```

**Test it:**

```bash
# Ask agent a question about context info
curl -X POST https://api.wildfireranch.us/ask \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the minimum SOC and target SOC?"}' | jq

# Expected: Agent answers immediately without tool call (info in system prompt)
```

---

## 📅 Part 3: Automatic Daily Sync (Optional, 20 min)

**Add a cron job for daily KB sync:**

**Option A: Railway Cron (Recommended)**

**File:** `railway/src/kb/cron.py`

```python
import schedule
import time
import os
from .sync import sync_knowledge_base

def scheduled_sync():
    """Run KB sync on schedule."""
    folder_id = os.getenv("GOOGLE_DOCS_KB_FOLDER_ID")
    access_token = os.getenv("GOOGLE_SERVICE_ACCOUNT_TOKEN")  # Need service account

    # TODO: Implement service account token refresh
    # For now, manual sync via frontend is sufficient

    print("Scheduled sync triggered")

# Run daily at 3 AM UTC
schedule.every().day.at("03:00").do(scheduled_sync)
```

**Option B: GitHub Actions (Alternative)**

Create `.github/workflows/kb-sync.yml`:

```yaml
name: Daily KB Sync

on:
  schedule:
    - cron: '0 3 * * *'  # 3 AM UTC daily
  workflow_dispatch:  # Allow manual trigger

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger KB Sync
        run: |
          curl -X POST ${{ secrets.RAILWAY_API_URL }}/kb/sync \
            -H "Authorization: Bearer ${{ secrets.GOOGLE_ACCESS_TOKEN }}"
```

**For now:** Manual sync is sufficient. Add automatic sync later when needed.

---

## 🎨 Part 4: Production Polish (30 min)

### **Error Handling Improvements**

**Add better error messages:**

**In:** `railway/src/kb/sync.py`

```python
# Add error handling for common issues
try:
    content = fetch_document_content(docs_service, file_id)
except HttpError as e:
    if e.status_code == 403:
        error_msg = f"Permission denied for {file_name}. Check OAuth scopes."
    elif e.status_code == 404:
        error_msg = f"Document {file_name} not found or deleted."
    else:
        error_msg = f"Failed to fetch {file_name}: {str(e)}"

    # Store error in kb_documents
    execute(
        conn,
        """
        UPDATE kb_documents
        SET sync_error = %s, updated_at = NOW()
        WHERE google_doc_id = %s
        """,
        (error_msg, file_id)
    )

    yield {
        "status": "processing",
        "current": idx + 1,
        "total": total_files,
        "current_file": file_name,
        "error": error_msg
    }

    failed += 1
    continue
```

### **Frontend Improvements**

**Add retry button for failed syncs:**

**In:** `vercel/src/app/kb/page.tsx`

```tsx
{progress?.status === 'failed' && (
  <button
    onClick={triggerSync}
    className="mt-2 bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
  >
    Retry Sync
  </button>
)}
```

**Add refresh button:**

```tsx
<button
  onClick={fetchDocuments}
  disabled={loading}
  className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700"
>
  {loading ? 'Loading...' : 'Refresh'}
</button>
```

---

## ✅ Session Completion Checklist

**Testing:**
- [ ] Google SSO login works
- [ ] Manual sync completes successfully
- [ ] Documents display correctly
- [ ] Context files have badges
- [ ] KB search API works
- [ ] KB stats endpoint works
- [ ] Error handling graceful

**Agent Integration:**
- [ ] search_kb tool created
- [ ] Agent can use KB search tool
- [ ] Agent cites sources in responses
- [ ] OR: Context files loaded into system prompt
- [ ] Agent references context correctly

**Production:**
- [ ] All endpoints returning valid responses
- [ ] No errors in Railway logs
- [ ] No errors in Vercel logs
- [ ] Embeddings cost tracking set up
- [ ] Documentation updated

---

## 📝 Deliverables

**By end of Session 017:**

1. **Test Report**
   - Google SSO: ✅/❌
   - KB Sync: ✅/❌
   - Search: ✅/❌
   - Agent Integration: ✅/❌

2. **Working Agent**
   - Agent with KB search tool OR context files loaded
   - Example query demonstrating KB usage
   - Source citations in responses

3. **Documentation**
   - SESSION_017_COMPLETION_SUMMARY.md
   - Update progress.md to Phase 6 complete
   - Screenshots of working system

4. **Next Steps Identified**
   - Optimization opportunities
   - Additional features to build
   - Known issues to fix

---

## 🚀 Getting Started

**First Steps:**

1. **Check Deployments:**
   ```bash
   # Railway API
   curl https://api.wildfireranch.us/health | jq

   # Verify KB routes
   curl https://api.wildfireranch.us/kb/documents | jq
   ```

2. **Visit Frontend:**
   - Go to https://mcp.wildfireranch.us/kb
   - Sign in with Google
   - Trigger sync

3. **Monitor Logs:**
   ```bash
   railway logs --service "CommandCenter" --lines 50
   ```

4. **Test Search:**
   ```bash
   curl -X POST https://api.wildfireranch.us/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query": "your search query"}' | jq
   ```

---

## 📚 Reference Documents

**Session 016 Docs:**
- [SESSION_016_COMPLETION_SUMMARY.md](SESSION_016_COMPLETION_SUMMARY.md) - Complete implementation details
- [SESSION_016_ADAPTED_PLAN.md](SESSION_016_ADAPTED_PLAN.md) - Implementation guide
- [docs/06-knowledge-base-design.md](../06-knowledge-base-design.md) - Architecture

**Code Files:**
- `railway/src/kb/google_drive.py` - Google Drive/Docs integration
- `railway/src/kb/sync.py` - Sync service with embeddings
- `railway/src/api/routes/kb.py` - API endpoints
- `vercel/src/app/kb/page.tsx` - KB management page

**Environment:**
- Vercel env vars: See SESSION_016_VERCEL_ENV_SETUP.md
- Railway env vars: GOOGLE_DOCS_KB_FOLDER_ID set
- Google Cloud: OAuth configured

---

## 💡 Tips

**For Testing:**
- Use curl with `| jq` for pretty JSON output
- Check Railway logs for backend errors
- Check browser console for frontend errors
- Test with small folder first (3-5 docs)

**For Agent Integration:**
- Start with context files (simpler)
- Add search tool later (more flexible)
- Test with specific queries
- Verify citations are included

**For Debugging:**
- Check `/kb/stats` to verify sync worked
- Use `/kb/sync-status` to see sync history
- Look for sync_error column in kb_documents
- Test search with known document content

---

## 🎯 Success Criteria

**Session 017 is complete when:**

✅ KB system tested end-to-end
✅ Google SSO working
✅ Sync successful (at least one run)
✅ Documents displaying correctly
✅ Search working (tested via API)
✅ Agent integrated with KB (tool OR context)
✅ Agent provides citations
✅ Error handling improved
✅ Documentation complete

---

**Let's test and integrate! Time to see the KB system in action!** 🚀

**Start with:** "Let's test the KB system! First, check if deployments are ready, then we'll test Google SSO login."
