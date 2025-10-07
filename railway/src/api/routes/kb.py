# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/api/routes/kb.py
# PURPOSE: Knowledge Base API routes
# ═══════════════════════════════════════════════════════════════════════════

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import StreamingResponse
from typing import Optional
import json
import logging
import os

from ...kb.sync import sync_knowledge_base, search_kb
from ...kb.google_drive import get_drive_service, list_files_recursive
from ...utils.db import get_connection, query_all, query_one

router = APIRouter(prefix="/kb", tags=["knowledge-base"])
logger = logging.getLogger(__name__)


@router.post("/sync")
async def trigger_sync(
    authorization: Optional[str] = Header(None),
    folder_id: Optional[str] = None,
    force: bool = False
):
    """
    Trigger KB sync from Google Drive.

    Requires Google OAuth access token in Authorization header.
    Returns Server-Sent Events stream with progress updates.

    Args:
        authorization: Bearer token from NextAuth session
        folder_id: Google Drive folder ID (optional, uses env var if not provided)
        force: Force re-sync even if files haven't changed

    Returns:
        StreamingResponse with text/event-stream content
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid access token")

    access_token = authorization.replace("Bearer ", "")

    # Use folder ID from env if not provided
    if not folder_id:
        folder_id = os.getenv("GOOGLE_DOCS_KB_FOLDER_ID")
        if not folder_id:
            raise HTTPException(
                status_code=400,
                detail="Folder ID not configured. Set GOOGLE_DOCS_KB_FOLDER_ID environment variable."
            )

    logger.info(f"Starting KB sync for folder {folder_id}, force={force}")

    # Stream progress updates
    async def generate():
        try:
            async for update in sync_knowledge_base(access_token, folder_id, force=force):
                yield f"data: {json.dumps(update)}\n\n"
        except Exception as e:
            logger.exception(f"Sync generator failed: {e}")
            yield f"data: {json.dumps({'status': 'failed', 'error': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/preview")
async def preview_sync(
    authorization: Optional[str] = Header(None),
    folder_id: Optional[str] = None
):
    """
    Preview what would be synced (dry run - no actual syncing).

    Requires Google OAuth access token in Authorization header.
    Returns file structure, counts, and estimates.

    Args:
        authorization: Bearer token from NextAuth session
        folder_id: Google Drive folder ID (optional, uses env var if not provided)

    Returns:
        Dict with:
            - total_files: Total number of files found
            - total_folders: Number of unique folders
            - files_by_folder: Files grouped by folder
            - ignored_folders: List of folders that would be skipped
            - estimated_tokens: Rough token estimate
            - file_types: Breakdown by file type
    """
    # Try to use service account first, fall back to OAuth token
    drive_service = None
    auth_method = "unknown"

    # Use folder ID from env if not provided
    if not folder_id:
        folder_id = os.getenv("GOOGLE_DOCS_KB_FOLDER_ID")
        if not folder_id:
            raise HTTPException(
                status_code=400,
                detail="Folder ID not configured. Set GOOGLE_DOCS_KB_FOLDER_ID environment variable."
            )

    logger.info(f"Previewing KB sync for folder {folder_id}")

    try:
        # Try service account first
        from ...kb.google_drive import get_drive_service_with_service_account
        try:
            drive_service = get_drive_service_with_service_account()
            auth_method = "service_account"
            logger.info("Using service account for preview")
        except Exception as sa_error:
            logger.warning(f"Service account failed: {sa_error}, trying OAuth token")

            # Fall back to OAuth token
            if not authorization or not authorization.startswith("Bearer "):
                raise HTTPException(
                    status_code=401,
                    detail="Service account not configured and no OAuth token provided"
                )

            access_token = authorization.replace("Bearer ", "")
            drive_service = get_drive_service(access_token)
            auth_method = "oauth_token"
            logger.info("Using OAuth token for preview")

        # List files recursively
        files = list_files_recursive(
            drive_service,
            folder_id,
            ignore_patterns=["old.*", "archive", "trash", "backup", "deprecated"]
        )

        # Group by folder
        files_by_folder = {}
        file_types = {}
        ignored_count = 0

        for file in files:
            folder_name = file.get('folder', 'unknown')
            mime_type = file.get('mimeType', 'unknown')
            file_path = file.get('path', file['name'])

            # Count by folder
            if folder_name not in files_by_folder:
                files_by_folder[folder_name] = []
            files_by_folder[folder_name].append({
                'name': file['name'],
                'path': file_path,
                'mimeType': mime_type,
                'modifiedTime': file.get('modifiedTime')
            })

            # Count by file type
            if mime_type not in file_types:
                file_types[mime_type] = 0
            file_types[mime_type] += 1

        # Estimate tokens (very rough: 1 doc ≈ 5000 tokens)
        google_docs_count = file_types.get('application/vnd.google-apps.document', 0)
        estimated_tokens = google_docs_count * 5000

        return {
            "status": "success",
            "auth_method": auth_method,
            "total_files": len(files),
            "total_folders": len(files_by_folder),
            "google_docs_count": google_docs_count,
            "files_by_folder": files_by_folder,
            "file_types": file_types,
            "estimated_tokens": estimated_tokens,
            "estimated_cost": f"${(estimated_tokens / 1000 * 0.0001):.4f}",
            "note": "This is a preview only. No files have been synced."
        }

    except Exception as e:
        logger.exception(f"Preview failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Preview failed: {str(e)}"
        )


@router.get("/documents")
async def list_documents():
    """
    List all synced KB documents.

    Returns:
        Dict with documents list and count
    """
    try:
        with get_connection() as conn:
            docs = query_all(
                conn,
                """
                SELECT
                    id,
                    google_doc_id,
                    title,
                    folder,
                    is_context_file,
                    token_count,
                    last_synced,
                    sync_error,
                    created_at,
                    updated_at
                FROM kb_documents
                ORDER BY is_context_file DESC, title ASC
                """,
                as_dict=True
            )

        return {
            "status": "success",
            "documents": docs,
            "count": len(docs)
        }

    except Exception as e:
        logger.exception(f"Failed to list documents: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/sync-status")
async def get_sync_status():
    """
    Get latest sync status and history.

    Returns:
        Dict with latest sync log entry
    """
    try:
        with get_connection() as conn:
            # Get latest sync
            latest = query_one(
                conn,
                """
                SELECT *
                FROM kb_sync_log
                ORDER BY started_at DESC
                LIMIT 1
                """,
                as_dict=True
            )

            # Get recent syncs
            history = query_all(
                conn,
                """
                SELECT *
                FROM kb_sync_log
                ORDER BY started_at DESC
                LIMIT 10
                """,
                as_dict=True
            )

        return {
            "status": "success",
            "latest": latest,
            "history": history
        }

    except Exception as e:
        logger.exception(f"Failed to get sync status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sync status: {str(e)}"
        )


@router.post("/search")
async def search_knowledge_base(
    query: str,
    limit: int = 5
):
    """
    Search knowledge base using semantic similarity.

    Args:
        query: Natural language search query
        limit: Number of results to return (default 5, max 20)

    Returns:
        Dict with search results and citations
    """
    if not query or len(query.strip()) < 3:
        raise HTTPException(
            status_code=400,
            detail="Query must be at least 3 characters"
        )

    # Limit results
    limit = min(limit, 20)

    try:
        result = search_kb(query, limit=limit)

        if not result.get("success"):
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Search failed")
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/stats")
async def get_kb_stats():
    """
    Get Knowledge Base statistics.

    Returns:
        Dict with document counts, chunk counts, etc.
    """
    try:
        with get_connection() as conn:
            # Document counts
            doc_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total_documents,
                    COUNT(*) FILTER (WHERE is_context_file = TRUE) as context_files,
                    COUNT(*) FILTER (WHERE is_context_file = FALSE) as searchable_files,
                    SUM(token_count) as total_tokens,
                    MAX(last_synced) as last_sync_time
                FROM kb_documents
                """,
                as_dict=True
            )

            # Chunk counts
            chunk_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total_chunks,
                    SUM(token_count) as total_chunk_tokens
                FROM kb_chunks
                """,
                as_dict=True
            )

            # Sync stats
            sync_stats = query_one(
                conn,
                """
                SELECT
                    COUNT(*) as total_syncs,
                    COUNT(*) FILTER (WHERE status = 'completed') as successful_syncs,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed_syncs
                FROM kb_sync_log
                """,
                as_dict=True
            )

        return {
            "status": "success",
            "documents": doc_stats,
            "chunks": chunk_stats,
            "syncs": sync_stats
        }

    except Exception as e:
        logger.exception(f"Failed to get stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stats: {str(e)}"
        )
