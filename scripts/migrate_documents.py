#!/usr/bin/env python3
"""
Migration script to create document attachments table.

Usage:
    python scripts/migrate_documents.py
"""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: str = "data/surtax.db"):
    """Create documents table for file attachments."""
    db_file = Path(__file__).parent.parent / db_path
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print("=" * 60)
    print("Document Attachments Migration")
    print("=" * 60)

    # Check if table already exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
    if cursor.fetchone():
        print("\nTable 'documents' already exists. No migration needed.")
        conn.close()
        return

    # Create documents table
    cursor.execute('''
        CREATE TABLE documents (
            document_id TEXT PRIMARY KEY,
            contract_id TEXT,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_type TEXT,
            file_size INTEGER,
            mime_type TEXT,
            category TEXT DEFAULT 'general',
            description TEXT,
            uploaded_by TEXT,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            is_public INTEGER DEFAULT 0,
            is_deleted INTEGER DEFAULT 0,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')

    # Create index for faster lookups
    cursor.execute('CREATE INDEX idx_documents_contract ON documents(contract_id)')
    cursor.execute('CREATE INDEX idx_documents_category ON documents(category)')

    conn.commit()
    print("\nCreated 'documents' table successfully.")

    # Create uploads directory
    uploads_dir = Path(__file__).parent.parent / 'data' / 'uploads'
    uploads_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created uploads directory: {uploads_dir}")

    conn.close()
    print("\nMigration complete!")


if __name__ == "__main__":
    migrate()
