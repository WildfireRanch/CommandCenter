# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/kb/google_drive.py
# PURPOSE: Google Drive and Docs API integration for KB sync
# ═══════════════════════════════════════════════════════════════════════════

from typing import List, Dict, Optional
import logging
import os
import json

from google.oauth2.credentials import Credentials
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

# Scopes needed for Drive and Docs readonly access
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/documents.readonly'
]


def get_service_account_credentials():
    """
    Get service account credentials from environment or file.

    Returns:
        Service account credentials with Drive/Docs scopes
    """
    # Try to get from environment variable (Railway)
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')

    if service_account_json:
        # Parse JSON from environment variable
        service_account_info = json.loads(service_account_json)
        credentials = service_account.Credentials.from_service_account_info(
            service_account_info,
            scopes=SCOPES
        )
        logger.info("Using service account from environment variable")
        return credentials

    # Fallback to file (local development)
    service_account_file = os.path.join(
        os.path.dirname(__file__),
        '../../../.google-service-account.json'
    )

    if os.path.exists(service_account_file):
        credentials = service_account.Credentials.from_service_account_file(
            service_account_file,
            scopes=SCOPES
        )
        logger.info("Using service account from file")
        return credentials

    raise Exception("No service account credentials found. Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable.")


def get_drive_service_with_service_account():
    """
    Create Google Drive service using service account.

    Returns:
        Google Drive API service instance
    """
    credentials = get_service_account_credentials()
    return build('drive', 'v3', credentials=credentials)


def get_docs_service_with_service_account():
    """
    Create Google Docs service using service account.

    Returns:
        Google Docs API service instance
    """
    credentials = get_service_account_credentials()
    return build('docs', 'v1', credentials=credentials)


def get_drive_service(access_token: str = None):
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


def list_files_recursive(
    drive_service,
    folder_id: str,
    ignore_patterns: Optional[List[str]] = None,
    current_path: str = "COMMAND_CENTER",
    _visited_folders: Optional[set] = None
) -> List[Dict]:
    """
    Recursively list all files in a folder and its subfolders.

    Args:
        drive_service: Google Drive API service
        folder_id: Google Drive folder ID to start from
        ignore_patterns: List of folder name patterns to skip (e.g., ["old.*", "archive"])
        current_path: Current path being traversed (for tracking)
        _visited_folders: Internal set to prevent infinite loops

    Returns:
        List of file metadata dicts with enhanced fields:
            - id: Google Drive file ID
            - name: File name
            - mimeType: MIME type
            - modifiedTime: Last modified timestamp
            - parents: List of parent folder IDs
            - path: Full path (e.g., "COMMAND_CENTER/SolarShack/manual.pdf")
            - folder: Immediate parent folder name (e.g., "SolarShack")
    """
    import re

    if ignore_patterns is None:
        ignore_patterns = ["old.*", "archive", "trash", "backup"]

    if _visited_folders is None:
        _visited_folders = set()

    # Prevent infinite loops from circular references
    if folder_id in _visited_folders:
        logger.warning(f"Circular reference detected for folder {folder_id}, skipping")
        return []

    _visited_folders.add(folder_id)

    all_files = []

    try:
        # Get all items in current folder (both files and subfolders)
        query = f"'{folder_id}' in parents and trashed=false"
        page_token = None

        while True:
            results = drive_service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, parents)",
                pageSize=100,
                pageToken=page_token
            ).execute()

            items = results.get('files', [])

            for item in items:
                item_name = item['name']
                item_path = f"{current_path}/{item_name}"

                # Check if folder should be ignored
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    # Check ignore patterns
                    should_ignore = False
                    for pattern in ignore_patterns:
                        if re.match(pattern, item_name, re.IGNORECASE):
                            logger.info(f"Ignoring folder (matches pattern '{pattern}'): {item_path}")
                            should_ignore = True
                            break

                    if should_ignore:
                        continue

                    # Recurse into subfolder
                    logger.info(f"Entering subfolder: {item_path}")
                    subfolder_files = list_files_recursive(
                        drive_service=drive_service,
                        folder_id=item['id'],
                        ignore_patterns=ignore_patterns,
                        current_path=item_path,
                        _visited_folders=_visited_folders
                    )
                    all_files.extend(subfolder_files)

                else:
                    # It's a file - add it to the list
                    # Enhance with path information
                    item['path'] = item_path
                    item['folder'] = current_path.split('/')[-1]  # Immediate parent folder
                    all_files.append(item)

            # Check for next page
            page_token = results.get('nextPageToken')
            if not page_token:
                break

        logger.info(f"Found {len(all_files)} files in {current_path} (including subfolders)")
        return all_files

    except HttpError as e:
        logger.error(f"Failed to list files recursively in {current_path}: {e}")
        raise Exception(f"Failed to list files in folder {folder_id}: {e}")
