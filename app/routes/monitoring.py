"""
Monitoring routes: Concerns, Watchlist, Risk Dashboard, Audit Trail
"""

from flask import Blueprint, render_template, request, session
from app.database import get_db

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/concerns')
def concerns():
    """Concerns and issues tracking."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if concerns table exists
    cursor.execute('''
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='concerns'
    ''')
    if not cursor.fetchone():
        # Return empty if table doesn't exist
        return render_template('monitoring/concerns.html',
                              title='Concerns',
                              concerns=[],
                              stats={'open': 0, 'under_review': 0, 'resolved': 0})

    cursor.execute('''
        SELECT * FROM concerns
        ORDER BY
            CASE status
                WHEN 'Open' THEN 1
                WHEN 'Under Review' THEN 2
                ELSE 3
            END,
            created_date DESC
    ''')
    concerns_list = cursor.fetchall()

    # Get stats
    cursor.execute('''
        SELECT
            SUM(CASE WHEN status = 'Open' THEN 1 ELSE 0 END) as open,
            SUM(CASE WHEN status = 'Under Review' THEN 1 ELSE 0 END) as under_review,
            SUM(CASE WHEN status = 'Resolved' THEN 1 ELSE 0 END) as resolved
        FROM concerns
    ''')
    stats = cursor.fetchone()

    return render_template('monitoring/concerns.html',
                          title='Concerns',
                          concerns=concerns_list,
                          stats=stats)


@monitoring_bp.route('/watchlist')
def watchlist():
    """User's watchlist of projects to monitor."""
    conn = get_db()
    cursor = conn.cursor()

    # Get watchlist from session
    watched_ids = session.get('watchlist', [])

    if watched_ids:
        placeholders = ','.join(['?' for _ in watched_ids])
        cursor.execute(f'''
            SELECT
                id, title, school_name, vendor_name, status,
                current_amount, percent_complete,
                is_delayed, delay_days, is_over_budget, budget_variance_pct
            FROM contracts
            WHERE id IN ({placeholders})
            ORDER BY is_delayed DESC, is_over_budget DESC
        ''', watched_ids)
        projects = cursor.fetchall()
    else:
        projects = []

    return render_template('monitoring/watchlist.html',
                          title='Watchlist',
                          projects=projects)


@monitoring_bp.route('/risk')
def risk_dashboard():
    """Risk Dashboard - flags high-risk projects."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id, title, school_name, vendor_name, status,
            current_amount, percent_complete,
            is_delayed, delay_days,
            is_over_budget, budget_variance_pct,
            CASE
                WHEN is_delayed = 1 AND is_over_budget = 1 THEN 'Critical'
                WHEN is_delayed = 1 OR is_over_budget = 1 THEN 'High'
                WHEN delay_days > 0 OR budget_variance_pct > 5 THEN 'Medium'
                ELSE 'Low'
            END as risk_level
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY
            CASE
                WHEN is_delayed = 1 AND is_over_budget = 1 THEN 1
                WHEN is_delayed = 1 OR is_over_budget = 1 THEN 2
                ELSE 3
            END,
            delay_days DESC
    ''')
    projects = cursor.fetchall()

    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_delayed = 1 AND is_over_budget = 1 THEN 1 ELSE 0 END) as critical,
            SUM(CASE WHEN (is_delayed = 1 OR is_over_budget = 1) AND NOT (is_delayed = 1 AND is_over_budget = 1) THEN 1 ELSE 0 END) as high,
            SUM(CASE WHEN is_delayed = 0 AND is_over_budget = 0 THEN 1 ELSE 0 END) as low
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    risk_summary = cursor.fetchone()

    return render_template('monitoring/risk_dashboard.html',
                          title='Risk Dashboard',
                          projects=projects,
                          risk_summary=risk_summary)


@monitoring_bp.route('/audit')
def audit_trail():
    """Audit Trail - track all changes."""
    return render_template('monitoring/audit_trail.html',
                          title='Audit Trail')
