"""
Statistical calculations and aggregations for the dashboard.
"""

from typing import Dict, Any, List
import sqlite3


def get_overview_stats(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """
    Get overview statistics for the dashboard.

    Returns:
        Dictionary with total_projects, total_budget, total_spent,
        active_projects, completed_projects, delayed_projects, etc.
    """
    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_projects,
            SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as completed_projects,
            SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_projects,
            SUM(CASE WHEN is_over_budget = 1 THEN 1 ELSE 0 END) as over_budget_projects,
            AVG(percent_complete) as avg_completion
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')

    row = cursor.fetchone()
    if row:
        return dict(row)
    return {}


def get_spending_by_category(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Get spending breakdown by surtax category.

    Returns:
        List of dictionaries with category, project_count, total_budget, total_spent
    """
    cursor.execute('''
        SELECT
            surtax_category as category,
            COUNT(*) as project_count,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent,
            AVG(percent_complete) as avg_completion
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY total_budget DESC
    ''')

    return [dict(row) for row in cursor.fetchall()]


def get_spending_by_school(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Get spending breakdown by school.

    Returns:
        List of dictionaries with school_name, project_count, total_budget, total_spent
    """
    cursor.execute('''
        SELECT
            school_name,
            COUNT(*) as project_count,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent,
            AVG(percent_complete) as avg_completion
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND school_name IS NOT NULL
        GROUP BY school_name
        ORDER BY total_budget DESC
    ''')

    return [dict(row) for row in cursor.fetchall()]


def get_budget_vs_actual(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """
    Get budget vs actual spending analysis.

    Returns:
        Dictionary with original_budget, current_budget, actual_spent,
        budget_variance, spend_efficiency
    """
    cursor.execute('''
        SELECT
            SUM(original_amount) as original_budget,
            SUM(current_amount) as current_budget,
            SUM(amount_paid) as actual_spent,
            AVG(percent_complete) as avg_progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')

    row = cursor.fetchone()
    if row:
        result = dict(row)
        # Calculate variances
        original = result.get('original_budget') or 0
        current = result.get('current_budget') or 0
        spent = result.get('actual_spent') or 0

        result['budget_change'] = current - original
        result['budget_change_pct'] = ((current - original) / original * 100) if original > 0 else 0
        result['spend_rate'] = (spent / current * 100) if current > 0 else 0

        return result
    return {}


def get_expenditure_type_breakdown(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Get breakdown by expenditure type (Capital vs Operating).

    Returns:
        List of dictionaries with expenditure_type, count, total_budget, total_spent
    """
    cursor.execute('''
        SELECT
            COALESCE(expenditure_type, 'Unclassified') as expenditure_type,
            COUNT(*) as count,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY expenditure_type
        ORDER BY total_budget DESC
    ''')

    return [dict(row) for row in cursor.fetchall()]
