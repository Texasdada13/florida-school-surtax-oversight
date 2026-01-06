"""
Monitoring routes: Concerns, Watchlist, Risk Dashboard, Audit Trail
"""

from flask import Blueprint, render_template, request, session
from app.database import get_db

monitoring_bp = Blueprint('monitoring', __name__)


@monitoring_bp.route('/concerns')
def concerns():
    """Concerns and issues tracking - shows delayed/over-budget projects."""
    conn = get_db()
    cursor = conn.cursor()

    # Get projects that are delayed or over budget as concerns
    cursor.execute('''
        SELECT
            contract_id, title, school_name, vendor_name, status,
            current_amount, percent_complete,
            is_delayed, delay_days, delay_reason,
            is_over_budget, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND (is_delayed = 1 OR is_over_budget = 1)
        ORDER BY
            CASE
                WHEN is_delayed = 1 AND is_over_budget = 1 THEN 1
                WHEN is_over_budget = 1 THEN 2
                ELSE 3
            END,
            delay_days DESC
    ''')
    concerns_list = cursor.fetchall()

    return render_template('monitoring/concerns.html',
                          title='Concerns',
                          concerns=concerns_list)


@monitoring_bp.route('/watchlist')
def watchlist():
    """User's watchlist of projects to monitor."""
    conn = get_db()
    cursor = conn.cursor()

    # Get watchlisted projects from database
    cursor.execute('''
        SELECT
            contract_id, title, school_name, vendor_name, status,
            current_amount, percent_complete,
            is_delayed, delay_days, is_over_budget, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0 AND is_watchlisted = 1
        ORDER BY is_delayed DESC, is_over_budget DESC
    ''')
    watchlist_projects = cursor.fetchall()

    return render_template('monitoring/watchlist.html',
                          title='Watchlist',
                          watchlist=watchlist_projects)


@monitoring_bp.route('/risk')
def risk_dashboard():
    """Risk Dashboard - flags high-risk projects."""
    conn = get_db()
    cursor = conn.cursor()

    # High risk: delayed AND over budget
    cursor.execute('''
        SELECT contract_id, title, school_name, current_amount, is_delayed, delay_days, is_over_budget
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND is_delayed = 1 AND is_over_budget = 1
    ''')
    high_risk = cursor.fetchall()

    # Medium risk: delayed OR over budget
    cursor.execute('''
        SELECT contract_id, title, school_name, current_amount, is_delayed, delay_days, is_over_budget
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND (is_delayed = 1 OR is_over_budget = 1)
        AND NOT (is_delayed = 1 AND is_over_budget = 1)
    ''')
    medium_risk = cursor.fetchall()

    # Low risk: neither delayed nor over budget
    cursor.execute('''
        SELECT contract_id, title, school_name, current_amount
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND is_delayed = 0 AND is_over_budget = 0
    ''')
    low_risk = cursor.fetchall()

    return render_template('monitoring/risk_dashboard.html',
                          title='Risk Dashboard',
                          high_risk=high_risk,
                          medium_risk=medium_risk,
                          low_risk=low_risk)


@monitoring_bp.route('/audit')
def audit_trail():
    """Audit Trail - track all changes."""
    return render_template('monitoring/audit_trail.html',
                          title='Audit Trail')
