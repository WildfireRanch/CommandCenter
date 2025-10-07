# Session 016: Google SSO + Knowledge Base Implementation
## **ADAPTED FOR CURRENT DIRECTORY STRUCTURE**

**Date:** October 7, 2025
**Type:** Implementation Session
**Duration:** ~4 hours
**Goal:** Build complete Knowledge Base sync system with Google SSO

---

## 🎯 Current Structure Analysis

### **Frontend (Vercel)**
- **Location:** `/workspaces/CommandCenter/vercel/`
- **Framework:** Next.js 14.2.18 with **App Router** ✅
- **Structure:**
  ```
  vercel/
  ├── src/
  │   ├── app/
  │   │   ├── layout.tsx          # Root layout (already exists)
  │   │   ├── page.tsx             # Home page
  │   │   ├── dashboard/page.tsx
  │   │   ├── chat/page.tsx
  │   │   ├── energy/page.tsx
  │   │   ├── logs/page.tsx
  │   │   ├── status/page.tsx
  │   │   └── studio/page.tsx
  │   ├── components/
  │   │   └── Sidebar.tsx
  │   └── (no lib/ or api/ yet - need to create)
  └── package.json
  ```

### **Backend (Railway)**
- **Location:** `/workspaces/CommandCenter/railway/`
- **Framework:** FastAPI
- **Structure:**
  ```
  railway/
  ├── src/
  │   ├── api/
  │   │   ├── main.py              # Main FastAPI app
  │   │   └── routes/              # Empty - ready for KB routes
  │   ├── kb/                      # Empty - ready for KB service
  │   ├── database/                # Has __init__.py only
  │   ├── utils/
  │   │   ├── db.py                # Database utilities
  │   │   └── solark_storage.py
  │   └── (agents, tools, etc.)
  ```

### **Environment Variables**
- ✅ `.env` exists with:
  - `GOOGLE_CLIENT_ID`
  - `GOOGLE_CLIENT_SECRET`
  - `OPENAI_API_KEY`
  - `DATABASE_URL`
  - All other configs

---

## 📝 Adapted Implementation Plan

### **PART 1: Database Schema (15 min)**

**What:** Create KB tables in PostgreSQL

**File:** `railway/src/database/migrations/001_knowledge_base.sql`

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base documents table
CREATE TABLE IF NOT EXISTS kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    folder VARCHAR(255),
    full_content TEXT,
    is_context_file BOOLEAN DEFAULT FALSE,
    token_count INTEGER,
    last_synced TIMESTAMP,
    sync_error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Searchable chunks with embeddings
CREATE TABLE IF NOT EXISTS kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    token_count INTEGER,
    embedding VECTOR(1536),
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sync history log
CREATE TABLE IF NOT EXISTS kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,
    documents_processed INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    error_message TEXT,
    triggered_by VARCHAR(100)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_documents_folder ON kb_documents(folder);
CREATE INDEX IF NOT EXISTS idx_kb_documents_context ON kb_documents(is_context_file);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_document ON kb_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding ON kb_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

**Run Migration:**
```bash
# Use Railway API endpoint (already exists)
curl -X POST https://api.wildfireranch.us/db/init-schema \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY"
```

**Note:** Update `railway/src/utils/db.py` `init_schema()` to include this migration file.

---

### **PART 2: NextAuth.js Setup (45 min)**

#### **Step 1: Install Dependencies**

```bash
cd /workspaces/CommandCenter/vercel
npm install next-auth@^4.24.5
```

#### **Step 2: Create Auth Configuration**

**File:** `vercel/src/lib/auth.ts`

```typescript
import { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      authorization: {
        params: {
          scope: [
            'openid',
            'email',
            'profile',
            'https://www.googleapis.com/auth/drive.readonly',
            'https://www.googleapis.com/auth/documents.readonly'
          ].join(' '),
          access_type: 'offline',
          prompt: 'consent'
        }
      }
    })
  ],

  callbacks: {
    // Restrict to your email only
    async signIn({ user }) {
      const allowedEmail = process.env.ALLOWED_EMAIL;
      if (user.email === allowedEmail) {
        return true;
      }
      return false; // Reject all other emails
    },

    // Include access token in session
    async jwt({ token, account }) {
      if (account) {
        token.accessToken = account.access_token;
        token.refreshToken = account.refresh_token;
      }
      return token;
    },

    async session({ session, token }) {
      session.accessToken = token.accessToken as string;
      return session;
    }
  },

  pages: {
    signIn: '/auth/signin',
    error: '/auth/error'
  }
};
```

#### **Step 3: Create NextAuth API Route**

**File:** `vercel/src/app/api/auth/[...nextauth]/route.ts`

```typescript
import NextAuth from "next-auth";
import { authOptions } from "@/lib/auth";

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
```

#### **Step 4: Create Session Provider**

**File:** `vercel/src/lib/providers.tsx`

```typescript
'use client';

import { SessionProvider } from 'next-auth/react';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  return <SessionProvider>{children}</SessionProvider>;
}
```

#### **Step 5: Update Root Layout**

**File:** `vercel/src/app/layout.tsx` (update existing)

```typescript
import type { Metadata } from 'next'
import Sidebar from '@/components/Sidebar'
import { AuthProvider } from '@/lib/providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'CommandCenter | Wildfire Ranch',
  description: 'Solar energy management and monitoring',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="min-h-screen font-sans bg-background text-foreground">
        <AuthProvider>
          <div className="flex h-screen">
            <Sidebar />
            <main className="flex-1 overflow-auto p-6 bg-gray-50">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  )
}
```

#### **Step 6: Add Environment Variables to Vercel**

```bash
# Via Vercel Dashboard or CLI:
GOOGLE_CLIENT_ID=643270983147-790kqhno93gfedc6i348flfe1ln72gsc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-dEpzFulFlcKq8k3SWd3Ji651cNj
ALLOWED_EMAIL=your-email@gmail.com
NEXTAUTH_URL=https://mcp.wildfireranch.us
NEXTAUTH_SECRET=$(openssl rand -base64 32)
```

---

### **PART 3: Railway KB Backend (1.5 hours)**

#### **Step 1: Google Drive Integration**

**File:** `railway/src/kb/google_drive.py`

```python
"""
Google Drive integration for fetching documents.
"""
from typing import List, Dict, Optional
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def get_drive_service(access_token: str):
    """Create Google Drive service from access token."""
    creds = Credentials(token=access_token)
    return build('drive', 'v3', credentials=creds)

def get_docs_service(access_token: str):
    """Create Google Docs service from access token."""
    creds = Credentials(token=access_token)
    return build('docs', 'v1', credentials=creds)

def list_files_in_folder(
    drive_service,
    folder_id: str,
    recursive: bool = True
) -> List[Dict]:
    """
    List all Google Docs in a folder.

    Args:
        drive_service: Google Drive API service
        folder_id: Google Drive folder ID
        recursive: Whether to search subfolders

    Returns:
        List of file metadata dicts
    """
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document'"

    try:
        results = drive_service.files().list(
            q=query,
            fields="files(id, name, modifiedTime, parents)",
            pageSize=1000
        ).execute()

        files = results.get('files', [])

        # TODO: Add recursive folder search if needed

        return files

    except HttpError as e:
        raise Exception(f"Failed to list files: {e}")

def fetch_document_content(docs_service, document_id: str) -> str:
    """
    Fetch full text content from a Google Doc.

    Args:
        docs_service: Google Docs API service
        document_id: Google Docs document ID

    Returns:
        Full document text content
    """
    try:
        doc = docs_service.documents().get(documentId=document_id).execute()

        # Extract text from document structure
        content = []
        for element in doc.get('body', {}).get('content', []):
            if 'paragraph' in element:
                for text_run in element['paragraph'].get('elements', []):
                    if 'textRun' in text_run:
                        content.append(text_run['textRun'].get('content', ''))

        return ''.join(content)

    except HttpError as e:
        raise Exception(f"Failed to fetch document {document_id}: {e}")
```

#### **Step 2: KB Sync Service**

**File:** `railway/src/kb/sync.py`

```python
"""
Knowledge Base sync service.
"""
import logging
from typing import List, Dict, AsyncGenerator
from datetime import datetime
import openai
import os

from .google_drive import (
    get_drive_service,
    get_docs_service,
    list_files_in_folder,
    fetch_document_content
)
from ..utils.db import get_connection, query_one, query_all, execute

logger = logging.getLogger(__name__)

# Chunking parameters
CHUNK_SIZE = 512  # tokens
CHUNK_OVERLAP = 50  # tokens

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Split text into chunks of approximately chunk_size tokens.

    Simple implementation: Split by paragraphs/sentences.
    Production: Use tiktoken for accurate token counting.
    """
    # TODO: Use tiktoken for accurate token-based chunking
    # For now, approximate: 1 token ≈ 4 characters
    char_limit = chunk_size * 4

    chunks = []
    current_chunk = ""

    for paragraph in text.split('\n\n'):
        if len(current_chunk) + len(paragraph) < char_limit:
            current_chunk += paragraph + "\n\n"
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = paragraph + "\n\n"

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate OpenAI embeddings for text chunks."""
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )

    return [item.embedding for item in response.data]

async def sync_knowledge_base(
    access_token: str,
    folder_id: str,
    sync_type: str = "full",
    force: bool = False
) -> AsyncGenerator[Dict, None]:
    """
    Sync Google Docs to database with progress updates.

    Args:
        access_token: Google OAuth access token
        folder_id: Google Drive folder ID to sync
        sync_type: "full" or "context-only"
        force: Re-sync even if unchanged

    Yields:
        Progress update dicts
    """
    conn = get_connection()

    # Log sync start
    sync_log_id = execute(
        conn,
        """
        INSERT INTO kb_sync_log (sync_type, started_at, status, triggered_by)
        VALUES (%s, NOW(), 'running', 'manual')
        RETURNING id
        """,
        (sync_type,)
    )

    try:
        # Get Google Drive service
        drive_service = get_drive_service(access_token)
        docs_service = get_docs_service(access_token)

        # List files
        files = list_files_in_folder(drive_service, folder_id)
        total_files = len(files)

        yield {
            "status": "started",
            "total": total_files,
            "message": f"Found {total_files} documents"
        }

        processed = 0
        updated = 0
        failed = 0

        for idx, file in enumerate(files):
            try:
                # Check if changed (unless force=True)
                if not force:
                    existing = query_one(
                        conn,
                        "SELECT last_synced FROM kb_documents WHERE google_doc_id = %s",
                        (file['id'],)
                    )
                    if existing and existing['last_synced'] >= file['modifiedTime']:
                        processed += 1
                        continue  # Skip unchanged

                # Fetch document content
                content = fetch_document_content(docs_service, file['id'])

                # Chunk content
                chunks = chunk_text(content)

                # Generate embeddings
                embeddings = generate_embeddings(chunks)

                # Store document
                execute(
                    conn,
                    """
                    INSERT INTO kb_documents (google_doc_id, title, full_content, token_count, last_synced)
                    VALUES (%s, %s, %s, %s, NOW())
                    ON CONFLICT (google_doc_id) DO UPDATE
                    SET title = EXCLUDED.title,
                        full_content = EXCLUDED.full_content,
                        token_count = EXCLUDED.token_count,
                        last_synced = NOW()
                    RETURNING id
                    """,
                    (file['id'], file['name'], content, len(content) // 4)  # Approx tokens
                )

                doc_id = query_one(conn, "SELECT id FROM kb_documents WHERE google_doc_id = %s", (file['id'],))['id']

                # Delete old chunks
                execute(conn, "DELETE FROM kb_chunks WHERE document_id = %s", (doc_id,))

                # Store chunks with embeddings
                for chunk_idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    execute(
                        conn,
                        """
                        INSERT INTO kb_chunks (document_id, chunk_text, chunk_index, token_count, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (doc_id, chunk, chunk_idx, len(chunk) // 4, embedding)
                    )

                processed += 1
                updated += 1

                yield {
                    "status": "processing",
                    "current": idx + 1,
                    "total": total_files,
                    "current_file": file['name'],
                    "processed": processed,
                    "updated": updated
                }

            except Exception as e:
                logger.error(f"Failed to sync {file['name']}: {e}")
                failed += 1
                continue

        # Update sync log
        execute(
            conn,
            """
            UPDATE kb_sync_log
            SET completed_at = NOW(),
                status = 'completed',
                documents_processed = %s,
                documents_updated = %s,
                documents_failed = %s
            WHERE id = %s
            """,
            (processed, updated, failed, sync_log_id)
        )

        yield {
            "status": "completed",
            "total": total_files,
            "processed": processed,
            "updated": updated,
            "failed": failed
        }

    except Exception as e:
        # Log failure
        execute(
            conn,
            """
            UPDATE kb_sync_log
            SET completed_at = NOW(),
                status = 'failed',
                error_message = %s
            WHERE id = %s
            """,
            (str(e), sync_log_id)
        )

        yield {
            "status": "failed",
            "error": str(e)
        }

    finally:
        conn.close()
```

#### **Step 3: API Routes**

**File:** `railway/src/api/routes/kb.py`

```python
"""
Knowledge Base API routes.
"""
from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import logging

from ...kb.sync import sync_knowledge_base
from ...utils.db import get_connection, query_all

router = APIRouter(prefix="/kb", tags=["knowledge-base"])
logger = logging.getLogger(__name__)

@router.post("/sync")
async def trigger_sync(
    authorization: Optional[str] = Header(None),
    folder_id: str = None,
    force: bool = False
):
    """
    Trigger KB sync from Google Drive.

    Requires Google OAuth access token in Authorization header.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing access token")

    access_token = authorization.replace("Bearer ", "")

    # Use folder ID from env if not provided
    if not folder_id:
        import os
        folder_id = os.getenv("GOOGLE_DOCS_KB_FOLDER_ID")
        if not folder_id:
            raise HTTPException(status_code=400, detail="Folder ID not configured")

    # Stream progress updates
    async def generate():
        async for update in sync_knowledge_base(access_token, folder_id, force=force):
            yield f"data: {json.dumps(update)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")

@router.get("/documents")
async def list_documents():
    """List all synced KB documents."""
    conn = get_connection()

    docs = query_all(
        conn,
        """
        SELECT id, title, folder, is_context_file, token_count, last_synced
        FROM kb_documents
        ORDER BY is_context_file DESC, title
        """,
        as_dict=True
    )

    conn.close()

    return {"documents": docs, "count": len(docs)}

@router.get("/sync-status")
async def get_sync_status():
    """Get latest sync status."""
    conn = get_connection()

    status = query_all(
        conn,
        """
        SELECT * FROM kb_sync_log
        ORDER BY started_at DESC
        LIMIT 1
        """,
        as_dict=True
    )

    conn.close()

    return {"status": status[0] if status else None}
```

**Update:** `railway/src/api/main.py` to include KB routes

```python
# Add to imports section
from .routes import kb

# Add after health endpoints (around line 445)
app.include_router(kb.router)
```

---

### **PART 4: Frontend KB Page (1 hour)**

**File:** `vercel/src/app/kb/page.tsx`

```typescript
'use client';

import { useSession, signIn } from 'next-auth/react';
import { useState, useEffect } from 'react';

export default function KnowledgeBasePage() {
  const { data: session, status } = useSession();
  const [documents, setDocuments] = useState([]);
  const [syncing, setSyncing] = useState(false);
  const [progress, setProgress] = useState(null);

  useEffect(() => {
    if (session) {
      fetchDocuments();
    }
  }, [session]);

  const fetchDocuments = async () => {
    const res = await fetch('https://api.wildfireranch.us/kb/documents');
    const data = await res.json();
    setDocuments(data.documents);
  };

  const triggerSync = async () => {
    if (!session?.accessToken) return;

    setSyncing(true);
    setProgress({ status: 'starting', current: 0, total: 0 });

    const eventSource = new EventSource(
      `https://api.wildfireranch.us/kb/sync?force=false`,
      {
        headers: {
          'Authorization': `Bearer ${session.accessToken}`
        }
      }
    );

    eventSource.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setProgress(update);

      if (update.status === 'completed' || update.status === 'failed') {
        eventSource.close();
        setSyncing(false);
        fetchDocuments();
      }
    };

    eventSource.onerror = () => {
      eventSource.close();
      setSyncing(false);
      setProgress({ status: 'failed', error: 'Connection lost' });
    };
  };

  if (status === 'loading') {
    return <div>Loading...</div>;
  }

  if (status === 'unauthenticated') {
    return (
      <div className="max-w-md mx-auto mt-20 text-center">
        <h1 className="text-2xl font-bold mb-4">Knowledge Base</h1>
        <p className="mb-6">Sign in with Google to manage your knowledge base</p>
        <button
          onClick={() => signIn('google')}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
        >
          Sign in with Google
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Knowledge Base</h1>
        <button
          onClick={triggerSync}
          disabled={syncing}
          className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 disabled:bg-gray-400"
        >
          {syncing ? 'Syncing...' : 'Sync Now'}
        </button>
      </div>

      {progress && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="font-semibold">
            {progress.status === 'completed' ? '✅ Sync Complete' :
             progress.status === 'failed' ? '❌ Sync Failed' :
             `🔄 Syncing: ${progress.current || 0} / ${progress.total || 0}`}
          </p>
          {progress.current_file && (
            <p className="text-sm text-gray-600">Current: {progress.current_file}</p>
          )}
          {progress.error && (
            <p className="text-sm text-red-600">Error: {progress.error}</p>
          )}
        </div>
      )}

      <div className="bg-white rounded-lg shadow">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold">Synced Documents ({documents.length})</h2>
        </div>
        <div className="divide-y">
          {documents.map((doc: any) => (
            <div key={doc.id} className="p-4 hover:bg-gray-50">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{doc.title}</h3>
                  {doc.folder && (
                    <p className="text-sm text-gray-500">📁 {doc.folder}</p>
                  )}
                </div>
                <div className="text-right text-sm text-gray-500">
                  <p>{doc.token_count?.toLocaleString()} tokens</p>
                  <p>{new Date(doc.last_synced).toLocaleDateString()}</p>
                </div>
              </div>
              {doc.is_context_file && (
                <span className="inline-block mt-2 bg-green-100 text-green-800 text-xs px-2 py-1 rounded">
                  Context File
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
```

**Update Sidebar** to include KB link:

**File:** `vercel/src/components/Sidebar.tsx` (add to nav items)

```tsx
<Link href="/kb">
  <img src="/SomeIcon.png" alt="KB" width={36} height={36} />
  Knowledge
</Link>
```

---

## 📋 Deployment Checklist

### **1. Update Vercel Environment Variables**
```bash
vercel env add GOOGLE_CLIENT_ID
vercel env add GOOGLE_CLIENT_SECRET
vercel env add ALLOWED_EMAIL
vercel env add NEXTAUTH_URL
vercel env add NEXTAUTH_SECRET
```

### **2. Update Railway Environment**
- Already has Google credentials ✅
- Add `GOOGLE_DOCS_KB_FOLDER_ID` if needed

### **3. Run Database Migration**
```bash
# Update railway/src/utils/db.py init_schema() to include new migration
# Then run:
curl -X POST https://api.wildfireranch.us/db/init-schema \
  -H "Content-Type: application/json"
```

### **4. Deploy**
```bash
# Vercel auto-deploys on push
# Railway auto-deploys on push
git add .
git commit -m "Session 016: Google SSO + Knowledge Base"
git push
```

---

## ✅ Testing Steps

1. **Test Google SSO:**
   - Visit https://mcp.wildfireranch.us/kb
   - Click "Sign in with Google"
   - Verify only your email works

2. **Test KB Sync:**
   - Click "Sync Now"
   - Watch progress updates
   - Verify documents appear in list

3. **Test Database:**
   - Check `kb_documents` table has rows
   - Check `kb_chunks` has embeddings
   - Check `kb_sync_log` records sync

---

## 🎯 File Summary

**New Files to Create:**

**Vercel Frontend:**
- `vercel/src/lib/auth.ts`
- `vercel/src/lib/providers.tsx`
- `vercel/src/app/api/auth/[...nextauth]/route.ts`
- `vercel/src/app/kb/page.tsx`

**Railway Backend:**
- `railway/src/database/migrations/001_knowledge_base.sql`
- `railway/src/kb/google_drive.py`
- `railway/src/kb/sync.py`
- `railway/src/api/routes/kb.py`

**Files to Update:**
- `vercel/src/app/layout.tsx` (add AuthProvider)
- `vercel/src/components/Sidebar.tsx` (add KB link)
- `railway/src/api/main.py` (include KB router)
- `railway/src/utils/db.py` (add migration to init_schema)

**Total:** 8 new files, 4 updates

---

Ready to implement? Let me know which part you want to start with!
