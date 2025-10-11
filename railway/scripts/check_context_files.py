#!/usr/bin/env python3
"""
Check Context Files in Production Database

Verifies if context files exist and are properly marked.
"""
import psycopg2
import os
import sys

def main():
    try:
        conn = psycopg2.connect(os.environ['DATABASE_URL'])
        cur = conn.cursor()

        # Check context files
        print("=" * 70)
        print("CONTEXT FILES CHECK")
        print("=" * 70)

        cur.execute("""
        SELECT id, title, is_context_file, LENGTH(full_content) as size
        FROM kb_documents
        WHERE is_context_file = TRUE
        ORDER BY title
        """)

        results = cur.fetchall()
        print(f"\n✅ Context files found: {len(results)}")

        if results:
            print("\nContext files:")
            for row in results:
                print(f"  - ID {row[0]}: {row[1]} ({row[3]:,} chars)")
        else:
            print("\n❌ NO CONTEXT FILES FOUND!")
            print("\nChecking all documents...")

            cur.execute("""
            SELECT id, title, folder, folder_path, is_context_file
            FROM kb_documents
            ORDER BY created_at DESC
            LIMIT 20
            """)

            all_docs = cur.fetchall()
            print(f"\nTotal documents in KB: (showing last 20)")
            for row in all_docs:
                context_flag = "✅" if row[4] else "❌"
                folder = row[2] or row[3] or "(no folder)"
                print(f"  {context_flag} ID {row[0]}: {row[1]}")
                print(f"      Folder: {folder}")

        cur.close()
        conn.close()

        return 0 if results else 1

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 2

if __name__ == "__main__":
    sys.exit(main())
