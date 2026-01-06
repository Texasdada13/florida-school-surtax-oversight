"""
Document routes: Document Library, Meeting Minutes, Annual Report
"""

from flask import Blueprint, render_template, current_app
from app.database import get_db

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/documents')
def documents():
    """Document Library."""
    return render_template('documents/documents.html',
                          title='Document Library')


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
