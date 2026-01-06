"""
Document Manager Service

Handles file uploads, storage, and retrieval for project documents.
Supports various document types including contracts, invoices, photos, and reports.
"""

import os
import uuid
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple, BinaryIO
from werkzeug.utils import secure_filename
from dataclasses import dataclass


# Allowed file extensions and their MIME types
ALLOWED_EXTENSIONS = {
    # Documents
    'pdf': 'application/pdf',
    'doc': 'application/msword',
    'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'xls': 'application/vnd.ms-excel',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'txt': 'text/plain',
    'csv': 'text/csv',

    # Images
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'png': 'image/png',
    'gif': 'image/gif',

    # Other
    'zip': 'application/zip',
}

# Document type categories
DOCUMENT_TYPES = [
    'contract',
    'invoice',
    'change_order',
    'progress_report',
    'inspection_report',
    'photo',
    'correspondence',
    'meeting_minutes',
    'bid_document',
    'insurance_certificate',
    'bond',
    'permit',
    'other',
]

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB


@dataclass
class DocumentInfo:
    """Document metadata."""
    document_id: int
    contract_id: Optional[str]
    vendor_id: Optional[str]
    filename: str
    document_type: str
    description: Optional[str]
    file_path: str
    file_size: int
    mime_type: str
    uploaded_by: Optional[str]
    uploaded_at: str
    is_deleted: bool = False


def get_upload_folder() -> Path:
    """Get the path to the uploads folder."""
    # Try environment variable first
    if 'UPLOAD_FOLDER' in os.environ:
        return Path(os.environ['UPLOAD_FOLDER'])

    # Default to data/uploads relative to project root
    project_root = Path(__file__).parent.parent.parent
    upload_folder = project_root / 'data' / 'uploads'
    upload_folder.mkdir(parents=True, exist_ok=True)
    return upload_folder


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS


def get_file_extension(filename: str) -> str:
    """Get the file extension."""
    if '.' not in filename:
        return ''
    return filename.rsplit('.', 1)[1].lower()


def save_document(
    cursor: sqlite3.Cursor,
    file: BinaryIO,
    filename: str,
    contract_id: Optional[str] = None,
    vendor_id: Optional[str] = None,
    document_type: str = 'other',
    description: Optional[str] = None,
    uploaded_by: Optional[str] = None
) -> Tuple[bool, str, Optional[int]]:
    """
    Save an uploaded document.

    Args:
        cursor: Database cursor
        file: File object to save
        filename: Original filename
        contract_id: Associated contract ID (optional)
        vendor_id: Associated vendor ID (optional)
        document_type: Type of document
        description: Optional description
        uploaded_by: User who uploaded

    Returns:
        Tuple of (success, message, document_id)
    """
    # Validate file
    if not filename:
        return False, "No filename provided", None

    if not allowed_file(filename):
        return False, f"File type not allowed. Allowed: {', '.join(ALLOWED_EXTENSIONS.keys())}", None

    # Secure the filename and generate unique storage name
    safe_filename = secure_filename(filename)
    ext = get_file_extension(safe_filename)
    unique_filename = f"{uuid.uuid4().hex}.{ext}"

    # Determine file path
    upload_folder = get_upload_folder()

    # Organize by year/month for easier management
    date_folder = datetime.now().strftime('%Y/%m')
    target_folder = upload_folder / date_folder
    target_folder.mkdir(parents=True, exist_ok=True)

    file_path = target_folder / unique_filename
    relative_path = f"{date_folder}/{unique_filename}"

    try:
        # Read file content
        content = file.read()
        file_size = len(content)

        # Check file size
        if file_size > MAX_FILE_SIZE:
            return False, f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB", None

        # Save file to disk
        with open(file_path, 'wb') as f:
            f.write(content)

        # Get MIME type
        mime_type = ALLOWED_EXTENSIONS.get(ext, 'application/octet-stream')

        # Insert database record
        cursor.execute('''
            INSERT INTO documents (
                contract_id, vendor_id, filename, document_type,
                description, file_path, file_size, mime_type,
                uploaded_by, uploaded_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ''', (
            contract_id, vendor_id, safe_filename, document_type,
            description, relative_path, file_size, mime_type, uploaded_by
        ))

        document_id = cursor.lastrowid
        return True, "Document uploaded successfully", document_id

    except Exception as e:
        # Clean up file if database insert fails
        if file_path.exists():
            file_path.unlink()
        return False, f"Error saving document: {str(e)}", None


def get_document(cursor: sqlite3.Cursor, document_id: int) -> Optional[DocumentInfo]:
    """Get document metadata by ID."""
    cursor.execute('''
        SELECT document_id, contract_id, vendor_id, filename, document_type,
               description, file_path, file_size, mime_type, uploaded_by,
               uploaded_at, is_deleted
        FROM documents
        WHERE document_id = ? AND is_deleted = 0
    ''', (document_id,))

    row = cursor.fetchone()
    if not row:
        return None

    return DocumentInfo(
        document_id=row[0],
        contract_id=row[1],
        vendor_id=row[2],
        filename=row[3],
        document_type=row[4],
        description=row[5],
        file_path=row[6],
        file_size=row[7],
        mime_type=row[8],
        uploaded_by=row[9],
        uploaded_at=row[10],
        is_deleted=bool(row[11])
    )


def get_document_file_path(document: DocumentInfo) -> Path:
    """Get the full file path for a document."""
    upload_folder = get_upload_folder()
    return upload_folder / document.file_path


def get_documents_for_contract(
    cursor: sqlite3.Cursor,
    contract_id: str
) -> List[DocumentInfo]:
    """Get all documents for a contract."""
    cursor.execute('''
        SELECT document_id, contract_id, vendor_id, filename, document_type,
               description, file_path, file_size, mime_type, uploaded_by,
               uploaded_at, is_deleted
        FROM documents
        WHERE contract_id = ? AND is_deleted = 0
        ORDER BY uploaded_at DESC
    ''', (contract_id,))

    return [
        DocumentInfo(
            document_id=row[0],
            contract_id=row[1],
            vendor_id=row[2],
            filename=row[3],
            document_type=row[4],
            description=row[5],
            file_path=row[6],
            file_size=row[7],
            mime_type=row[8],
            uploaded_by=row[9],
            uploaded_at=row[10],
            is_deleted=bool(row[11])
        )
        for row in cursor.fetchall()
    ]


def get_all_documents(
    cursor: sqlite3.Cursor,
    document_type: Optional[str] = None,
    limit: int = 50
) -> List[DocumentInfo]:
    """Get recent documents, optionally filtered by type."""
    if document_type:
        cursor.execute('''
            SELECT document_id, contract_id, vendor_id, filename, document_type,
                   description, file_path, file_size, mime_type, uploaded_by,
                   uploaded_at, is_deleted
            FROM documents
            WHERE is_deleted = 0 AND document_type = ?
            ORDER BY uploaded_at DESC
            LIMIT ?
        ''', (document_type, limit))
    else:
        cursor.execute('''
            SELECT document_id, contract_id, vendor_id, filename, document_type,
                   description, file_path, file_size, mime_type, uploaded_by,
                   uploaded_at, is_deleted
            FROM documents
            WHERE is_deleted = 0
            ORDER BY uploaded_at DESC
            LIMIT ?
        ''', (limit,))

    return [
        DocumentInfo(
            document_id=row[0],
            contract_id=row[1],
            vendor_id=row[2],
            filename=row[3],
            document_type=row[4],
            description=row[5],
            file_path=row[6],
            file_size=row[7],
            mime_type=row[8],
            uploaded_by=row[9],
            uploaded_at=row[10],
            is_deleted=bool(row[11])
        )
        for row in cursor.fetchall()
    ]


def delete_document(cursor: sqlite3.Cursor, document_id: int) -> bool:
    """Soft delete a document."""
    cursor.execute('''
        UPDATE documents SET is_deleted = 1
        WHERE document_id = ?
    ''', (document_id,))
    return cursor.rowcount > 0


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_document_type_icon(document_type: str) -> str:
    """Get an icon class for document type."""
    icons = {
        'contract': 'file-text',
        'invoice': 'file-invoice',
        'change_order': 'file-edit',
        'progress_report': 'chart-line',
        'inspection_report': 'clipboard-check',
        'photo': 'image',
        'correspondence': 'mail',
        'meeting_minutes': 'users',
        'bid_document': 'gavel',
        'insurance_certificate': 'shield',
        'bond': 'lock',
        'permit': 'stamp',
    }
    return icons.get(document_type, 'file')
