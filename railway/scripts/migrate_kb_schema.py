#!/usr/bin/env python3
"""
KB Schema Migration Script

Adds folder_path and mime_type columns to kb_documents table if they don't exist.

Usage:
    python3 scripts/migrate_kb_schema.py
"""

import sys
import os

# Add parent directory to path so we can import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.db import get_connection, execute, query_one


def migrate_schema():
    """Add folder_path and mime_type columns to kb_documents table."""

    with get_connection() as conn:
        print("🔍 Checking KB schema...")

        # Check if folder_path column exists
        result = query_one(
            conn,
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'kb_documents'
            AND column_name = 'folder_path'
            """
        )

        if result:
            print("✅ folder_path column already exists")
        else:
            print("📝 Adding folder_path column...")
            execute(
                conn,
                "ALTER TABLE kb_documents ADD COLUMN folder_path VARCHAR(1000)",
                commit=True
            )
            print("✅ folder_path column added")

        # Check if mime_type column exists
        result = query_one(
            conn,
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'kb_documents'
            AND column_name = 'mime_type'
            """
        )

        if result:
            print("✅ mime_type column already exists")
        else:
            print("📝 Adding mime_type column...")
            execute(
                conn,
                "ALTER TABLE kb_documents ADD COLUMN mime_type VARCHAR(200)",
                commit=True
            )
            print("✅ mime_type column added")

        # Create index on folder_path for faster queries
        print("📝 Creating index on folder_path...")
        try:
            execute(
                conn,
                """
                CREATE INDEX IF NOT EXISTS idx_kb_documents_folder_path
                ON kb_documents(folder_path)
                """,
                commit=True
            )
            print("✅ Index created")
        except Exception as e:
            print(f"⚠️  Index may already exist: {e}")

        print("\n✅ Schema migration complete!")


if __name__ == "__main__":
    try:
        migrate_schema()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
