"""
Tool routes: Meeting Mode, Compliance, Map View, Public Portal, Alerts
"""

from flask import Blueprint, render_template, current_app
from app.database import get_db

tools_bp = Blueprint('tools', __name__)


@tools_bp.route('/meeting')
def meeting_mode():
    """Meeting Mode - presentation-friendly view."""
    conn = get_db()
    cursor = conn.cursor()

    # Get key stats for presentation
    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            COALESCE(SUM(current_amount), 0) as total_budget,
            COALESCE(SUM(total_paid), 0) as total_spent,
            COUNT(CASE WHEN status = 'Active' THEN 1 END) as active,
            COUNT(CASE WHEN is_delayed = 1 THEN 1 END) as delayed,
            COUNT(CASE WHEN is_over_budget = 1 THEN 1 END) as over_budget
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    stats = cursor.fetchone()

    # Key projects to highlight
    cursor.execute('''
        SELECT contract_id, title, school_name, current_amount, percent_complete, status
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY current_amount DESC
        LIMIT 10
    ''')
    top_projects = cursor.fetchall()

    return render_template('tools/meeting_mode.html',
                          title='Meeting Mode',
                          stats=stats,
                          top_projects=top_projects)


@tools_bp.route('/compliance')
def compliance_dashboard():
    """Compliance Dashboard."""
    conn = get_db()
    cursor = conn.cursor()

    # Budget compliance
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_over_budget = 1 THEN 1 ELSE 0 END) as over_budget,
            AVG(budget_variance_pct) as avg_variance
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    budget_compliance = cursor.fetchone()

    # Schedule compliance
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed,
            AVG(CASE WHEN is_delayed = 1 THEN delay_days ELSE 0 END) as avg_delay
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    schedule_compliance = cursor.fetchone()

    # By surtax category for compliance tracking
    cursor.execute('''
        SELECT
            COALESCE(surtax_category, 'Unclassified') as category,
            COUNT(*) as count,
            SUM(current_amount) as total
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
    ''')
    category_breakdown = cursor.fetchall()

    # Count by category type for the summary cards
    capital_count = sum(c['count'] for c in category_breakdown if c['category'] in ['New Construction', 'Renovation', 'Safety/Security', 'Technology', 'Site Improvements'])
    total_count = sum(c['count'] for c in category_breakdown)
    capital_pct = (capital_count / total_count * 100) if total_count > 0 else 0

    return render_template('tools/compliance.html',
                          title='Compliance',
                          budget_compliance=budget_compliance,
                          schedule_compliance=schedule_compliance,
                          category_breakdown=category_breakdown,
                          capital_count=capital_count,
                          capital_pct=capital_pct,
                          operating_count=0,
                          unclassified_count=total_count - capital_count)


@tools_bp.route('/map')
def map_view():
    """Geographic map view of projects."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT DISTINCT
            school_name,
            COUNT(*) as project_count,
            SUM(current_amount) as total_value
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND school_name IS NOT NULL
        GROUP BY school_name
        ORDER BY total_value DESC
    ''')
    schools = cursor.fetchall()

    return render_template('tools/map_view.html',
                          title='Map View',
                          schools=schools)


@tools_bp.route('/public')
def public_portal():
    """Public transparency portal."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(current_amount) as total_budget,
            SUM(total_paid) as total_spent,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    summary = cursor.fetchone()

    cursor.execute('''
        SELECT title, school_name, current_amount, surtax_category
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND status = 'Completed'
        ORDER BY current_end_date DESC
        LIMIT 10
    ''')
    completed = cursor.fetchall()

    county_config = current_app.config.get('county', {})
    surtax_config = current_app.config.get('surtax', {})

    return render_template('tools/public_portal.html',
                          title='Public Portal',
                          summary=summary,
                          completed=completed,
                          county=county_config,
                          surtax=surtax_config)


@tools_bp.route('/alerts')
def alerts():
    """Alerts and notifications management."""
    conn = get_db()
    cursor = conn.cursor()

    alerts_list = []

    # Delayed projects
    cursor.execute('''
        SELECT contract_id, title, delay_days
        FROM contracts
        WHERE is_deleted = 0 AND is_delayed = 1
        ORDER BY delay_days DESC
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        alerts_list.append({
            'type': 'warning',
            'title': f"Project Delayed: {row['title'][:40]}",
            'message': f"{row['delay_days']} days behind schedule",
            'project_id': row['contract_id']
        })

    # Over budget projects
    cursor.execute('''
        SELECT contract_id, title, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0 AND is_over_budget = 1
        ORDER BY budget_variance_pct DESC
        LIMIT 5
    ''')
    for row in cursor.fetchall():
        alerts_list.append({
            'type': 'danger',
            'title': f"Over Budget: {row['title'][:40]}",
            'message': f"{row['budget_variance_pct']:.1f}% over budget",
            'project_id': row['contract_id']
        })

    return render_template('tools/alerts.html',
                          title='Alerts & Notifications',
                          alerts=alerts_list)
