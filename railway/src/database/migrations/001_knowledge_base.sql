-- ═══════════════════════════════════════════════════════════════════════════
-- FILE: railway/src/database/migrations/001_knowledge_base.sql
-- PURPOSE: Knowledge Base schema for Google Docs sync
-- CREATED: Session 016 - October 7, 2025
-- ═══════════════════════════════════════════════════════════════════════════

-- Enable pgvector extension for embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- Knowledge base documents table
-- Stores metadata and full content of synced Google Docs
CREATE TABLE IF NOT EXISTS kb_documents (
    id SERIAL PRIMARY KEY,
    google_doc_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(500) NOT NULL,
    folder VARCHAR(255),                      -- Subfolder path (e.g., "context", "solar-shack-technical")
    folder_path VARCHAR(1000),                -- Full folder path from Drive
    mime_type VARCHAR(100),                   -- File type (Google Doc, PDF, Spreadsheet)
    full_content TEXT,                        -- Complete document text
    is_context_file BOOLEAN DEFAULT FALSE,    -- Tier 1 (always loaded) vs Tier 2 (searchable)
    token_count INTEGER,                      -- Approximate token count for cost tracking
    last_synced TIMESTAMP,                    -- Last successful sync timestamp
    sync_error TEXT,                          -- Error message if sync failed
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Searchable chunks with embeddings
-- Each document is split into chunks for semantic search
CREATE TABLE IF NOT EXISTS kb_chunks (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES kb_documents(id) ON DELETE CASCADE,
    chunk_text TEXT NOT NULL,                -- Chunk content
    chunk_index INTEGER NOT NULL,            -- Position in document (0, 1, 2...)
    token_count INTEGER,                     -- Approximate tokens in this chunk
    embedding VECTOR(1536),                  -- OpenAI text-embedding-3-small (1536 dimensions)
    created_at TIMESTAMP DEFAULT NOW()
);

-- Sync history log
-- Tracks all sync operations for debugging and monitoring
CREATE TABLE IF NOT EXISTS kb_sync_log (
    id SERIAL PRIMARY KEY,
    sync_type VARCHAR(50) NOT NULL,          -- "full", "context-only", "manual"
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(50) NOT NULL,             -- "running", "completed", "failed"
    documents_processed INTEGER DEFAULT 0,
    documents_updated INTEGER DEFAULT 0,
    documents_failed INTEGER DEFAULT 0,
    error_message TEXT,
    triggered_by VARCHAR(100)                -- "cron", "user", "api"
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_kb_documents_folder ON kb_documents(folder);
CREATE INDEX IF NOT EXISTS idx_kb_documents_context ON kb_documents(is_context_file);
CREATE INDEX IF NOT EXISTS idx_kb_documents_synced ON kb_documents(last_synced);
CREATE INDEX IF NOT EXISTS idx_kb_documents_mime_type ON kb_documents(mime_type);
CREATE INDEX IF NOT EXISTS idx_kb_chunks_document ON kb_chunks(document_id);

-- IVFFlat index for fast vector similarity search
-- lists=100 is good for up to 10,000 chunks (we expect ~1,000-5,000)
CREATE INDEX IF NOT EXISTS idx_kb_chunks_embedding ON kb_chunks
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Sync log indexes
CREATE INDEX IF NOT EXISTS idx_kb_sync_log_started ON kb_sync_log(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_kb_sync_log_status ON kb_sync_log(status);

-- ═══════════════════════════════════════════════════════════════════════════
-- Schema created successfully
-- ═══════════════════════════════════════════════════════════════════════════
