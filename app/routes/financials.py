"""
Financial routes: Vendors, Change Orders, Analytics, Budget Performance
"""

from flask import Blueprint, render_template, request
from app.database import get_db

financials_bp = Blueprint('financials', __name__)


@financials_bp.route('/vendors')
def vendors():
    """Vendor Performance tracking."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            vendor_name,
            COUNT(*) as project_count,
            SUM(current_amount) as total_value,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 100 as overbudget_rate,
            AVG(percent_complete) as avg_completion
        FROM contracts
        WHERE is_deleted = 0 AND vendor_name IS NOT NULL AND vendor_name != ''
        GROUP BY vendor_name
        ORDER BY total_value DESC
    ''')
    vendors_list = cursor.fetchall()

    return render_template('financials/vendors.html',
                          title='Vendor Performance',
                          vendors=vendors_list)


@financials_bp.route('/change-orders')
def change_orders():
    """Change Order tracking."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id, title, school_name, vendor_name,
            original_amount, current_amount,
            (current_amount - original_amount) as change_amount,
            CASE WHEN original_amount > 0
                THEN ((current_amount - original_amount) / original_amount * 100)
                ELSE 0 END as change_pct,
            status
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND original_amount IS NOT NULL
        AND current_amount != original_amount
        ORDER BY ABS(current_amount - original_amount) DESC
    ''')
    change_orders_list = cursor.fetchall()

    cursor.execute('''
        SELECT
            COUNT(*) as total_changes,
            SUM(current_amount - original_amount) as total_change_value,
            SUM(CASE WHEN current_amount > original_amount THEN 1 ELSE 0 END) as increases,
            SUM(CASE WHEN current_amount < original_amount THEN 1 ELSE 0 END) as decreases
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND original_amount IS NOT NULL
        AND current_amount != original_amount
    ''')
    stats = cursor.fetchone()

    return render_template('financials/change_orders.html',
                          title='Change Orders',
                          change_orders=change_orders_list,
                          stats=stats)


@financials_bp.route('/analytics')
def analytics():
    """Analytics and reporting."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            surtax_category,
            COUNT(*) as project_count,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent,
            AVG(percent_complete) as avg_completion
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY total_budget DESC
    ''')
    category_data = cursor.fetchall()

    cursor.execute('''
        SELECT
            status,
            COUNT(*) as count,
            SUM(current_amount) as value
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY status
    ''')
    status_data = cursor.fetchall()

    return render_template('financials/analytics.html',
                          title='Analytics',
                          category_data=category_data,
                          status_data=status_data)


@financials_bp.route('/budget-performance')
def budget_performance():
    """Budget Performance - Proposed vs Actual vs Progress analysis."""
    conn = get_db()
    cursor = conn.cursor()

    # Get projects with budget and progress data
    cursor.execute('''
        SELECT
            id, title, school_name, surtax_category,
            original_amount, current_amount, amount_paid,
            percent_complete,
            CASE WHEN original_amount > 0
                THEN (amount_paid / original_amount * 100)
                ELSE 0 END as spend_rate,
            CASE WHEN current_amount > 0
                THEN (amount_paid / current_amount * 100)
                ELSE 0 END as budget_utilization,
            expenditure_type
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY current_amount DESC
    ''')
    projects = cursor.fetchall()

    # Summary stats
    cursor.execute('''
        SELECT
            SUM(original_amount) as total_original,
            SUM(current_amount) as total_current,
            SUM(amount_paid) as total_spent,
            AVG(percent_complete) as avg_progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    summary = cursor.fetchone()

    # By expenditure type (Capital vs Operating)
    cursor.execute('''
        SELECT
            COALESCE(expenditure_type, 'Unclassified') as exp_type,
            COUNT(*) as count,
            SUM(current_amount) as budget,
            SUM(amount_paid) as spent
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY expenditure_type
    ''')
    by_type = cursor.fetchall()

    return render_template('financials/budget_performance.html',
                          title='Budget Performance',
                          projects=projects,
                          summary=summary,
                          by_type=by_type)
