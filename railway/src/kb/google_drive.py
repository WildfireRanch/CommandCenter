# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/kb/google_drive.py
# PURPOSE: Google Drive and Docs API integration for KB sync
# ═══════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Optional
import logging

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


def get_drive_service(access_token: str):
    """
    Create Google Drive service from OAuth access token.

    Args:
        access_token: OAuth2 access token from NextAuth.js session

    Returns:
        Google Drive API service instance
    """
    creds = Credentials(token=access_token)
    return build('drive', 'v3', credentials=creds)


def get_docs_service(access_token: str):
    """
    Create Google Docs service from OAuth access token.

    Args:
        access_token: OAuth2 access token from NextAuth.js session

    Returns:
        Google Docs API service instance
    """
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
        recursive: Whether to search subfolders (TODO: implement)

    Returns:
        List of file metadata dicts with keys:
            - id: Google Doc ID
            - name: File name
            - modifiedTime: Last modified timestamp
            - parents: List of parent folder IDs
    """
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.document' and trashed=false"

    try:
        files = []
        page_token = None

        while True:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, modifiedTime, parents)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            files.extend(results.get('files', []))

            page_token = results.get('nextPageToken')
            if not page_token:
                break

        logger.info(f"Found {len(files)} documents in folder {folder_id}")
        return files

    except HttpError as e:
        logger.error(f"Failed to list files: {e}")
        raise Exception(f"Failed to list files in folder {folder_id}: {e}")


def get_folder_name(drive_service, folder_id: str) -> str:
    """
    Get folder name from folder ID.

    Args:
        drive_service: Google Drive API service
        folder_id: Google Drive folder ID

    Returns:
        Folder name
    """
    try:
        folder = drive_service.files().get(
            fileId=folder_id,
            fields="name"
        ).execute()

        return folder.get('name', 'unknown')

    except HttpError as e:
        logger.error(f"Failed to get folder name: {e}")
        return 'unknown'


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
                        text = text_run['textRun'].get('content', '')
                        content.append(text)

            elif 'table' in element:
                # Extract text from tables
                for row in element['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        for cell_element in cell.get('content', []):
                            if 'paragraph' in cell_element:
                                for text_run in cell_element['paragraph'].get('elements', []):
                                    if 'textRun' in text_run:
                                        text = text_run['textRun'].get('content', '')
                                        content.append(text)

        full_text = ''.join(content)

        logger.info(f"Fetched document {document_id}: {len(full_text)} characters")
        return full_text

    except HttpError as e:
        logger.error(f"Failed to fetch document {document_id}: {e}")
        raise Exception(f"Failed to fetch document {document_id}: {e}")


def list_subfolders(drive_service, folder_id: str) -> List[Dict]:
    """
    List all subfolders in a folder.

    Args:
        drive_service: Google Drive API service
        folder_id: Google Drive folder ID

    Returns:
        List of folder metadata dicts
    """
    query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false"

    try:
        results = drive_service.files().list(
            q=query,
            fields="files(id, name)",
            pageSize=100
        ).execute()

        folders = results.get('files', [])
        logger.info(f"Found {len(folders)} subfolders in folder {folder_id}")

        return folders

    except HttpError as e:
        logger.error(f"Failed to list subfolders: {e}")
        raise Exception(f"Failed to list subfolders in folder {folder_id}: {e}")
