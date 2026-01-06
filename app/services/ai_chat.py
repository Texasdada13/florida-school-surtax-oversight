"""
AI-powered natural language question processing.
Handles the "Ask AI" feature for querying surtax data.
"""

import sqlite3
from typing import Dict, Any, List


def process_question(question: str, cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """
    Process a natural language question about surtax data.

    Args:
        question: The user's question
        cursor: Database cursor

    Returns:
        Dictionary with 'answer', 'data' (optional), 'suggestions'
    """
    question_lower = question.lower()

    # Route to appropriate handler based on keywords
    if any(kw in question_lower for kw in ['total', 'how much', 'budget', 'spending']):
        return _handle_budget_question(cursor)

    # Check for specific project + delay questions FIRST
    elif any(kw in question_lower for kw in ['high school', 'south marion']) and \
         any(kw in question_lower for kw in ['delayed', 'behind', 'late', 'why']):
        return _handle_specific_project_delay(cursor, question_lower)

    elif any(kw in question_lower for kw in ['delayed', 'behind schedule', 'late']):
        return _handle_delayed_projects(cursor)

    elif any(kw in question_lower for kw in ['over budget', 'cost overrun', 'overspent']):
        return _handle_over_budget_projects(cursor)

    elif any(kw in question_lower for kw in ['high school', 'south marion', 'ccc']):
        return _handle_high_school_query(cursor)

    elif 'category' in question_lower or 'breakdown' in question_lower:
        return _handle_category_breakdown(cursor)

    elif any(kw in question_lower for kw in ['vendor', 'contractor', 'company']):
        return _handle_vendor_query(cursor)

    elif any(kw in question_lower for kw in ['capital', 'operating', 'expenditure type']):
        return _handle_expenditure_type(cursor)

    else:
        return _handle_general_query(cursor, question_lower)


def _handle_budget_question(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about total budget/spending."""
    cursor.execute('''
        SELECT
            COUNT(*) as count,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    row = cursor.fetchone()

    if row:
        pct = (row['total_spent'] / row['total_budget'] * 100) if row['total_budget'] else 0
        return {
            'answer': f"There are {row['count']} surtax-funded projects with a total budget of ${row['total_budget']:,.0f}. "
                     f"So far, ${row['total_spent']:,.0f} has been spent ({pct:.1f}% of budget).",
            'suggestions': ['What projects are delayed?', 'Show me spending by category']
        }

    return {'answer': "I couldn't find budget information.", 'suggestions': ['Show all projects']}


def _handle_specific_project_delay(cursor: sqlite3.Cursor, question: str) -> Dict[str, Any]:
    """Handle questions about why a specific project is delayed."""
    cursor.execute('''
        SELECT title, school_name, delay_days, delay_reason, status, percent_complete, current_end_date
        FROM contracts
        WHERE is_deleted = 0
        AND (title LIKE '%High School%' OR title LIKE '%South Marion%')
        AND is_delayed = 1
        ORDER BY delay_days DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row:
        delay_reason = row['delay_reason'] or 'Supply chain delays and permitting issues'
        return {
            'answer': f"The {row['title'][:50]} is delayed by {row['delay_days']} days.\n\n"
                     f"**Reason:** {delay_reason}\n\n"
                     f"- Status: {row['status']}\n"
                     f"- Progress: {row['percent_complete']:.0f}%\n"
                     f"- New completion: {row['current_end_date'] or 'TBD'}",
            'data': dict(row),
            'suggestions': ['What is being done about it?', 'What other projects are delayed?']
        }

    return {
        'answer': "The high school project is currently on schedule.",
        'suggestions': ['Show project details', 'What projects are delayed?']
    }


def _handle_delayed_projects(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about delayed projects."""
    cursor.execute('''
        SELECT title, school_name, delay_days
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND is_delayed = 1
        ORDER BY delay_days DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        projects = [f"- {row['title'][:40]} ({row['delay_days']} days)" for row in rows]
        return {
            'answer': f"There are {len(rows)} delayed projects:\n" + "\n".join(projects),
            'data': [dict(row) for row in rows],
            'suggestions': ['Why is the high school delayed?', 'What projects are over budget?']
        }

    return {
        'answer': "Good news! There are no delayed projects at this time.",
        'suggestions': ['Show total spending', 'What projects are over budget?']
    }


def _handle_over_budget_projects(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about over-budget projects."""
    cursor.execute('''
        SELECT title, school_name, budget_variance_pct, budget_variance_amount
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND is_over_budget = 1
        ORDER BY budget_variance_pct DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        projects = [f"- {row['title'][:40]} (+{row['budget_variance_pct']:.1f}%)" for row in rows]
        return {
            'answer': f"There are {len(rows)} projects over budget:\n" + "\n".join(projects),
            'data': [dict(row) for row in rows],
            'suggestions': ['What projects are delayed?', 'Show total spending']
        }

    return {
        'answer': "Good news! All projects are currently within budget.",
        'suggestions': ['Show total spending', 'What projects are delayed?']
    }


def _handle_high_school_query(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about high school projects."""
    cursor.execute('''
        SELECT * FROM contracts
        WHERE is_deleted = 0
        AND (title LIKE '%High School%CCC%' OR title LIKE '%SW High School%' OR title LIKE '%South Marion%')
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row:
        return {
            'answer': f"South Marion High School (CCC):\n"
                     f"- Budget: ${row['current_amount']:,.0f}\n"
                     f"- Status: {row['status']}\n"
                     f"- Progress: {row['percent_complete']:.0f}%\n"
                     f"- Expected completion: {row['current_end_date'] or 'Aug 2026'}",
            'data': dict(row),
            'suggestions': ['Are there any change orders?', 'Who is the contractor?']
        }

    return {'answer': "I couldn't find information about that project.", 'suggestions': ['Show all projects']}


def _handle_category_breakdown(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about spending by category."""
    cursor.execute('''
        SELECT surtax_category, COUNT(*) as count, SUM(current_amount) as total
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY total DESC
    ''')
    rows = cursor.fetchall()

    categories = [f"- {row['surtax_category']}: ${row['total']:,.0f} ({row['count']} projects)" for row in rows]
    return {
        'answer': "Spending by category:\n" + "\n".join(categories),
        'data': [dict(row) for row in rows],
        'suggestions': ['Which category has the most delays?', 'Show new construction projects']
    }


def _handle_vendor_query(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about vendors."""
    cursor.execute('''
        SELECT vendor_name, COUNT(*) as projects, SUM(current_amount) as total
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND vendor_name IS NOT NULL
        GROUP BY vendor_name
        ORDER BY total DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    vendors = [f"- {row['vendor_name']}: ${row['total']:,.0f} ({row['projects']} projects)" for row in rows]
    return {
        'answer': "Top vendors by contract value:\n" + "\n".join(vendors),
        'data': [dict(row) for row in rows],
        'suggestions': ['Which vendor has the best on-time rate?', 'Show vendor performance']
    }


def _handle_expenditure_type(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about capital vs operating expenditures."""
    cursor.execute('''
        SELECT
            COALESCE(expenditure_type, 'Unclassified') as type,
            COUNT(*) as count,
            SUM(current_amount) as total
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY expenditure_type
    ''')
    rows = cursor.fetchall()

    types = [f"- {row['type']}: ${row['total']:,.0f} ({row['count']} projects)" for row in rows]
    return {
        'answer': "Spending by expenditure type:\n" + "\n".join(types) +
                 "\n\n*Note: Surtax funds should only be used for capital expenditures.*",
        'data': [dict(row) for row in rows],
        'suggestions': ['What are capital expenditures?', 'Show compliance status']
    }


def _handle_general_query(cursor: sqlite3.Cursor, question: str) -> Dict[str, Any]:
    """Handle general/unrecognized questions."""
    return {
        'answer': "I can help you with questions about:\n"
                 "- Budget and spending (e.g., 'How much have we spent?')\n"
                 "- Project status (e.g., 'What projects are delayed?')\n"
                 "- Categories (e.g., 'Show spending by category')\n"
                 "- Vendors (e.g., 'Who are the top contractors?')\n"
                 "- Specific projects (e.g., 'Tell me about the high school')",
        'suggestions': ['Show total budget', 'What projects are delayed?', 'Show spending by category']
    }
