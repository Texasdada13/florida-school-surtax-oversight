"""
Document routes: Document Library, Meeting Minutes, Annual Report
"""

from flask import Blueprint, render_template, current_app, request, jsonify, send_file, abort
from app.database import get_db
from app.services.document_manager import (
    save_document, get_document, get_document_file_path,
    get_documents_for_contract, get_all_documents, delete_document,
    format_file_size, DOCUMENT_TYPES, ALLOWED_EXTENSIONS
)

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/documents')
def documents():
    """Document Library with upload functionality."""
    conn = get_db()
    cursor = conn.cursor()

    # Get filter parameter
    doc_type = request.args.get('type')

    # Get documents
    docs = get_all_documents(cursor, document_type=doc_type)

    # Get document counts by type
    cursor.execute('''
        SELECT document_type, COUNT(*) as count
        FROM documents
        WHERE is_deleted = 0
        GROUP BY document_type
    ''')
    type_counts = {row[0]: row[1] for row in cursor.fetchall()}

    return render_template('documents/documents.html',
                          title='Document Library',
                          documents=docs,
                          type_counts=type_counts,
                          document_types=DOCUMENT_TYPES,
                          allowed_extensions=list(ALLOWED_EXTENSIONS.keys()),
                          current_type=doc_type,
                          format_file_size=format_file_size)


@documents_bp.route('/minutes')
def meeting_minutes():
    """Meeting Minutes archive."""
    county_config = current_app.config.get('oversight_committee', {})

    return render_template('documents/meeting_minutes.html',
                          title='Meeting Minutes',
                          committee=county_config)


@documents_bp.route('/report')
def annual_report():
    """Annual Report generator."""
    conn = get_db()
    cursor = conn.cursor()

    # Get comprehensive stats for report
    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(current_amount) as total_budget,
            SUM(total_paid) as total_spent,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
            AVG(percent_complete) as avg_progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    summary = cursor.fetchone()

    # By category
    cursor.execute('''
        SELECT
            surtax_category,
            COUNT(*) as count,
            SUM(current_amount) as budget,
            SUM(total_paid) as spent
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY budget DESC
    ''')
    by_category = cursor.fetchall()

    county_config = current_app.config.get('county', {})
    surtax_config = current_app.config.get('surtax', {})

    return render_template('documents/annual_report.html',
                          title='Annual Report',
                          summary=summary,
                          by_category=by_category,
                          county=county_config,
                          surtax=surtax_config)


# Document upload/download API endpoints
@documents_bp.route('/documents/upload', methods=['POST'])
def upload_document():
    """Upload a new document."""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'}), 400

    conn = get_db()
    cursor = conn.cursor()

    success, message, doc_id = save_document(
        cursor=cursor,
        file=file,
        filename=file.filename,
        contract_id=request.form.get('contract_id'),
        vendor_id=request.form.get('vendor_id'),
        document_type=request.form.get('document_type', 'other'),
        description=request.form.get('description'),
        uploaded_by=request.form.get('uploaded_by', 'system')
    )

    if success:
        conn.commit()
        return jsonify({
            'success': True,
            'message': message,
            'document_id': doc_id
        })
    else:
        return jsonify({'success': False, 'error': message}), 400


@documents_bp.route('/documents/download/<int:document_id>')
def download_document(document_id):
    """Download a document by ID."""
    conn = get_db()
    cursor = conn.cursor()

    doc = get_document(cursor, document_id)
    if not doc:
        abort(404)

    file_path = get_document_file_path(doc)
    if not file_path.exists():
        abort(404)

    return send_file(
        file_path,
        download_name=doc.filename,
        mimetype=doc.mime_type,
        as_attachment=True
    )


@documents_bp.route('/documents/view/<int:document_id>')
def view_document(document_id):
    """View a document inline (for PDFs and images)."""
    conn = get_db()
    cursor = conn.cursor()

    doc = get_document(cursor, document_id)
    if not doc:
        abort(404)

    file_path = get_document_file_path(doc)
    if not file_path.exists():
        abort(404)

    return send_file(
        file_path,
        download_name=doc.filename,
        mimetype=doc.mime_type,
        as_attachment=False
    )


@documents_bp.route('/documents/delete/<int:document_id>', methods=['POST'])
def delete_document_route(document_id):
    """Delete a document (soft delete)."""
    conn = get_db()
    cursor = conn.cursor()

    success = delete_document(cursor, document_id)
    conn.commit()

    return jsonify({
        'success': success,
        'message': 'Document deleted' if success else 'Document not found'
    })


@documents_bp.route('/documents/for-contract/<contract_id>')
def documents_for_contract(contract_id):
    """Get all documents for a specific contract."""
    conn = get_db()
    cursor = conn.cursor()

    docs = get_documents_for_contract(cursor, contract_id)

    return jsonify({
        'documents': [
            {
                'document_id': d.document_id,
                'filename': d.filename,
                'document_type': d.document_type,
                'description': d.description,
                'file_size': d.file_size,
                'file_size_formatted': format_file_size(d.file_size),
                'mime_type': d.mime_type,
                'uploaded_at': d.uploaded_at,
                'download_url': f'/documents/download/{d.document_id}',
                'view_url': f'/documents/view/{d.document_id}'
            }
            for d in docs
        ],
        'count': len(docs)
    })
