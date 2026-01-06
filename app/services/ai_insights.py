"""
AI-powered insights and predictions.

This module will contain ML-based analysis for:
- Trend analysis and forecasting
- Anomaly detection
- Risk prediction
- Vendor performance correlation
- Budget efficiency metrics

For advanced analytics, this would integrate with:
- TensorFlow/PyTorch for neural networks
- scikit-learn for traditional ML
- Prophet for time series forecasting
"""

import sqlite3
from typing import Dict, Any, List
from datetime import datetime, timedelta


def get_ai_insights(cursor: sqlite3.Cursor) -> List[Dict[str, Any]]:
    """
    Generate AI-powered insights from project data.

    Returns:
        List of insight dictionaries with type, title, description, severity
    """
    insights = []

    # Insight 1: Budget trend analysis
    budget_insight = _analyze_budget_trends(cursor)
    if budget_insight:
        insights.append(budget_insight)

    # Insight 2: Delay patterns
    delay_insight = _analyze_delay_patterns(cursor)
    if delay_insight:
        insights.append(delay_insight)

    # Insight 3: Vendor performance
    vendor_insight = _analyze_vendor_performance(cursor)
    if vendor_insight:
        insights.append(vendor_insight)

    # Insight 4: Category efficiency
    category_insight = _analyze_category_efficiency(cursor)
    if category_insight:
        insights.append(category_insight)

    # Insight 5: Spending rate vs progress
    efficiency_insight = _analyze_spending_efficiency(cursor)
    if efficiency_insight:
        insights.append(efficiency_insight)

    return insights


def _analyze_budget_trends(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Analyze budget change trends."""
    cursor.execute('''
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN current_amount > original_amount THEN 1 ELSE 0 END) as increased,
            AVG(CASE WHEN original_amount > 0
                THEN ((current_amount - original_amount) / original_amount * 100)
                ELSE 0 END) as avg_change
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND original_amount IS NOT NULL AND original_amount > 0
    ''')
    row = cursor.fetchone()

    if row and row['total'] > 0:
        pct_increased = (row['increased'] / row['total']) * 100
        avg_change = row['avg_change'] or 0

        if pct_increased > 50:
            return {
                'type': 'trend',
                'icon': 'trending-up',
                'title': 'Budget Increases Common',
                'description': f"{pct_increased:.0f}% of projects have seen budget increases, "
                              f"averaging {avg_change:.1f}% above original estimates. "
                              f"Consider building larger contingencies into initial budgets.",
                'severity': 'warning' if avg_change > 10 else 'info'
            }

    return None


def _analyze_delay_patterns(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Analyze delay patterns by category or vendor."""
    cursor.execute('''
        SELECT
            surtax_category,
            COUNT(*) as total,
            SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed,
            AVG(CASE WHEN is_delayed = 1 THEN delay_days ELSE 0 END) as avg_delay
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        HAVING total >= 2
        ORDER BY (delayed * 1.0 / total) DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row and row['delayed'] > 0:
        delay_rate = (row['delayed'] / row['total']) * 100
        if delay_rate > 30:
            return {
                'type': 'pattern',
                'icon': 'clock',
                'title': f"Delays Common in {row['surtax_category']}",
                'description': f"{delay_rate:.0f}% of {row['surtax_category']} projects are delayed, "
                              f"averaging {row['avg_delay']:.0f} days. "
                              f"Consider additional schedule buffer for this category.",
                'severity': 'warning'
            }

    return None


def _analyze_vendor_performance(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Identify top and bottom performing vendors."""
    cursor.execute('''
        SELECT
            vendor_name,
            COUNT(*) as projects,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 100 as overbudget_rate
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND vendor_name IS NOT NULL AND vendor_name != ''
        GROUP BY vendor_name
        HAVING projects >= 2
        ORDER BY (delay_rate + overbudget_rate) DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row and (row['delay_rate'] > 50 or row['overbudget_rate'] > 50):
        return {
            'type': 'vendor',
            'icon': 'alert-triangle',
            'title': f"Vendor Performance Concern",
            'description': f"{row['vendor_name']} has a {row['delay_rate']:.0f}% delay rate "
                          f"and {row['overbudget_rate']:.0f}% over-budget rate across {row['projects']} projects. "
                          f"Review performance before future awards.",
            'severity': 'critical'
        }

    return None


def _analyze_category_efficiency(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Analyze spending efficiency by category."""
    cursor.execute('''
        SELECT
            surtax_category,
            SUM(current_amount) as budget,
            SUM(amount_paid) as spent,
            AVG(percent_complete) as progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        HAVING budget > 0
    ''')

    best_category = None
    best_efficiency = 0

    for row in cursor.fetchall():
        spend_rate = (row['spent'] or 0) / row['budget'] * 100 if row['budget'] else 0
        progress = row['progress'] or 0

        # Efficiency = progress per dollar spent (higher is better)
        if spend_rate > 10:  # Only consider categories with significant spending
            efficiency = progress / spend_rate if spend_rate > 0 else 0
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                best_category = row

    if best_category and best_efficiency > 1.2:
        return {
            'type': 'efficiency',
            'icon': 'zap',
            'title': f"{best_category['surtax_category']} Most Efficient",
            'description': f"{best_category['surtax_category']} projects show the best efficiency, "
                          f"achieving {best_category['progress']:.0f}% completion with "
                          f"{((best_category['spent'] or 0) / best_category['budget'] * 100):.0f}% budget spent.",
            'severity': 'success'
        }

    return None


def _analyze_spending_efficiency(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Analyze overall spending rate vs progress."""
    cursor.execute('''
        SELECT
            SUM(current_amount) as budget,
            SUM(amount_paid) as spent,
            AVG(percent_complete) as progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND status = 'Active'
    ''')
    row = cursor.fetchone()

    if row and row['budget'] and row['budget'] > 0:
        spend_rate = (row['spent'] or 0) / row['budget'] * 100
        progress = row['progress'] or 0

        # Flag if spending significantly outpaces progress
        if spend_rate > progress + 20:
            return {
                'type': 'efficiency',
                'icon': 'alert-circle',
                'title': 'Spending Outpacing Progress',
                'description': f"Active projects are {spend_rate:.0f}% through budget "
                              f"but only {progress:.0f}% complete. "
                              f"This may indicate cost overruns developing.",
                'severity': 'warning'
            }
        elif progress > spend_rate + 10:
            return {
                'type': 'efficiency',
                'icon': 'check-circle',
                'title': 'Good Cost Control',
                'description': f"Active projects are {progress:.0f}% complete "
                              f"with only {spend_rate:.0f}% of budget spent. "
                              f"Projects are tracking efficiently.",
                'severity': 'success'
            }

    return None
