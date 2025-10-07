# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/kb/sync.py
# PURPOSE: Knowledge Base sync service - Google Docs to PostgreSQL
# ═══════════════════════════════════════════════════════════════════════════

import logging
from typing import List, Dict, AsyncGenerator
from datetime import datetime
import openai
import os

from .google_drive import (
    get_drive_service,
    get_docs_service,
    list_files_in_folder,
    fetch_document_content,
    get_folder_name
)
from ..utils.db import get_connection, query_one, query_all, execute

logger = logging.getLogger(__name__)

# Chunking parameters
CHUNK_SIZE = 512  # tokens (approximate)
CHUNK_OVERLAP = 50  # tokens overlap between chunks


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Split text into chunks of approximately chunk_size tokens.

    Simple implementation using character approximation.
    Production: Use tiktoken for accurate token-based chunking.

    Args:
        text: Text to chunk
        chunk_size: Approximate tokens per chunk
        overlap: Approximate tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    # Approximate: 1 token ≈ 4 characters
    char_limit = chunk_size * 4
    char_overlap = overlap * 4

    if len(text) <= char_limit:
        return [text]

    chunks = []
    start = 0

    while start < len(text):
        end = start + char_limit

        # Try to break at paragraph boundary
        if end < len(text):
            # Look for paragraph break within next 200 chars
            next_para = text.find('\n\n', end, end + 200)
            if next_para != -1:
                end = next_para

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position (with overlap)
        start = end - char_overlap

    logger.info(f"Chunked text into {len(chunks)} chunks")
    return chunks


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Generate OpenAI embeddings for text chunks.

    Args:
        texts: List of text strings to embed

    Returns:
        List of embedding vectors (1536 dimensions each)
    """
    if not texts:
        return []

    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    try:
        response = client.embeddings.create(
            model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        logger.info(f"Generated {len(embeddings)} embeddings")

        return embeddings

    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}")
        raise


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
        Progress update dicts with keys:
            - status: "started", "processing", "completed", "failed"
            - current: Current file index
            - total: Total files to process
            - current_file: Name of file being processed
            - processed: Files processed so far
            - updated: Files updated
            - failed: Files that failed
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
        (sync_type,),
        commit=True
    )

    # Get the ID from the insert
    log_result = query_one(
        conn,
        "SELECT id FROM kb_sync_log WHERE sync_type = %s ORDER BY started_at DESC LIMIT 1",
        (sync_type,)
    )
    sync_log_id = log_result['id'] if log_result else None

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
                file_id = file['id']
                file_name = file['name']

                # Check if changed (unless force=True)
                if not force:
                    existing = query_one(
                        conn,
                        "SELECT last_synced, updated_at FROM kb_documents WHERE google_doc_id = %s",
                        (file_id,)
                    )

                    if existing and existing.get('last_synced'):
                        last_synced = existing['last_synced']
                        modified_time = datetime.fromisoformat(file['modifiedTime'].replace('Z', '+00:00'))

                        if last_synced.replace(tzinfo=None) >= modified_time.replace(tzinfo=None):
                            processed += 1
                            logger.info(f"Skipping unchanged file: {file_name}")
                            continue

                # Fetch document content
                logger.info(f"Syncing {idx + 1}/{total_files}: {file_name}")
                content = fetch_document_content(docs_service, file_id)

                if not content or len(content.strip()) < 10:
                    logger.warning(f"Skipping empty document: {file_name}")
                    processed += 1
                    continue

                # Chunk content
                chunks = chunk_text(content)

                # Generate embeddings
                embeddings = generate_embeddings(chunks)

                # Determine if context file (in "context" subfolder)
                # For now, mark as context file if "context" is in the name
                is_context = "context" in file_name.lower()

                # Store document
                execute(
                    conn,
                    """
                    INSERT INTO kb_documents (google_doc_id, title, full_content, token_count, last_synced, is_context_file)
                    VALUES (%s, %s, %s, %s, NOW(), %s)
                    ON CONFLICT (google_doc_id) DO UPDATE
                    SET title = EXCLUDED.title,
                        full_content = EXCLUDED.full_content,
                        token_count = EXCLUDED.token_count,
                        last_synced = NOW(),
                        is_context_file = EXCLUDED.is_context_file,
                        updated_at = NOW()
                    """,
                    (file_id, file_name, content, len(content) // 4, is_context),
                    commit=True
                )

                # Get document ID
                doc = query_one(
                    conn,
                    "SELECT id FROM kb_documents WHERE google_doc_id = %s",
                    (file_id,)
                )
                doc_id = doc['id'] if doc else None

                if not doc_id:
                    logger.error(f"Failed to get document ID for {file_name}")
                    failed += 1
                    continue

                # Delete old chunks
                execute(conn, "DELETE FROM kb_chunks WHERE document_id = %s", (doc_id,), commit=True)

                # Store chunks with embeddings
                for chunk_idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                    execute(
                        conn,
                        """
                        INSERT INTO kb_chunks (document_id, chunk_text, chunk_index, token_count, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (doc_id, chunk, chunk_idx, len(chunk) // 4, embedding),
                        commit=True
                    )

                processed += 1
                updated += 1

                yield {
                    "status": "processing",
                    "current": idx + 1,
                    "total": total_files,
                    "current_file": file_name,
                    "processed": processed,
                    "updated": updated
                }

            except Exception as e:
                logger.error(f"Failed to sync {file.get('name', 'unknown')}: {e}")
                failed += 1
                continue

        # Update sync log
        if sync_log_id:
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
                (processed, updated, failed, sync_log_id),
                commit=True
            )

        yield {
            "status": "completed",
            "total": total_files,
            "processed": processed,
            "updated": updated,
            "failed": failed
        }

    except Exception as e:
        logger.exception(f"Sync failed: {e}")

        # Log failure
        if sync_log_id:
            execute(
                conn,
                """
                UPDATE kb_sync_log
                SET completed_at = NOW(),
                    status = 'failed',
                    error_message = %s
                WHERE id = %s
                """,
                (str(e), sync_log_id),
                commit=True
            )

        yield {
            "status": "failed",
            "error": str(e)
        }

    finally:
        conn.close()


def search_kb(query: str, limit: int = 5) -> Dict:
    """
    Search knowledge base using semantic similarity.

    Args:
        query: Natural language search query
        limit: Number of results to return

    Returns:
        Dict with:
            - success: bool
            - query: str
            - results: List of matching chunks with metadata
            - citations: List of source document titles
    """
    try:
        # Generate query embedding
        query_embeddings = generate_embeddings([query])
        if not query_embeddings:
            return {"success": False, "error": "Failed to generate query embedding"}

        query_embedding = query_embeddings[0]

        # Search using pgvector
        conn = get_connection()

        results = query_all(
            conn,
            """
            SELECT
                kc.chunk_text,
                kd.title,
                kd.folder,
                1 - (kc.embedding <=> %s::vector) AS similarity
            FROM kb_chunks kc
            JOIN kb_documents kd ON kc.document_id = kd.id
            ORDER BY similarity DESC
            LIMIT %s
            """,
            (query_embedding, limit),
            as_dict=True
        )

        conn.close()

        return {
            "success": True,
            "query": query,
            "results": [
                {
                    "content": r["chunk_text"],
                    "source": r["title"],
                    "folder": r["folder"],
                    "similarity": float(r["similarity"])
                }
                for r in results
            ],
            "citations": list(set(r["title"] for r in results))
        }

    except Exception as e:
        logger.error(f"KB search failed: {e}")
        return {"success": False, "error": str(e)}
