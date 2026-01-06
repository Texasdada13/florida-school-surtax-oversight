"""
AI-powered natural language question processing.
Handles the "Ask AI" feature for querying surtax data.

Style Guide (Executive Persona):
1. Lead with numbers - dollar amounts and percentages first
2. Plain English - no jargon or technical terms
3. Name names - specific vendors, projects, schools
4. One screen max - concise answers that fit without scrolling
5. Flag follow-up items - mark things that need staff attention
6. Include next steps when actionable
7. Note data caveats when relevant
"""

import sqlite3
from typing import Dict, Any, List
from datetime import datetime, timedelta


def process_question(question: str, cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """
    Process a natural language question about surtax data.

    Args:
        question: The user's question
        cursor: Database cursor

    Returns:
        Dictionary with:
        - answer: Main response text
        - data: Optional list of data rows
        - suggestions: Follow-up question suggestions
        - ask_staff: Boolean flag for items needing staff follow-up
        - next_step: Suggested next action
        - data_note: Data quality/currency caveat
    """
    question_lower = question.lower()

    # Route to appropriate handler based on keywords
    # Risk/Warning questions (red chips)
    if any(kw in question_lower for kw in ['schedule risk', 'behind schedule', 'delayed', '30 days']):
        return _handle_schedule_risks(cursor)

    elif any(kw in question_lower for kw in ['over budget', 'budget alert', 'cost overrun']):
        return _handle_over_budget_alerts(cursor)

    elif any(kw in question_lower for kw in ['vendor red flag', 'change order', 'vendor problem', 'struggling']):
        return _handle_vendor_red_flags(cursor)

    elif any(kw in question_lower for kw in ['worried', 'concern', 'risk', 'problem']):
        return _handle_concerns(cursor)

    # Financial questions (blue/green chips)
    elif any(kw in question_lower for kw in ['remaining', 'left to spend', 'unspent']):
        return _handle_remaining_budget(cursor)

    elif any(kw in question_lower for kw in ['largest', 'biggest', 'top 5', 'top five']):
        return _handle_largest_projects(cursor)

    elif any(kw in question_lower for kw in ['total', 'summary', 'where we stand', 'spent vs budget']):
        return _handle_budget_summary(cursor)

    # Category/Analysis questions (purple/gray chips)
    elif any(kw in question_lower for kw in ['top vendor', 'highest contract', 'biggest vendor']):
        return _handle_top_vendor(cursor)

    elif any(kw in question_lower for kw in ['school', 'most project']):
        return _handle_schools_by_projects(cursor)

    elif any(kw in question_lower for kw in ['category', 'split', 'construction', 'renovation']):
        return _handle_category_split(cursor)

    elif any(kw in question_lower for kw in ['completing', 'next 90', 'upcoming']):
        return _handle_upcoming_completions(cursor)

    # Vendor queries
    elif any(kw in question_lower for kw in ['vendor', 'contractor', 'company']):
        return _handle_vendor_query(cursor)

    # Specific project queries
    elif any(kw in question_lower for kw in ['high school', 'south marion', 'ccc']):
        return _handle_specific_project(cursor, question_lower)

    else:
        return _handle_general_query(cursor, question_lower)


def _handle_schedule_risks(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about schedule risks and delayed projects."""
    cursor.execute('''
        SELECT title, school_name, delay_days, vendor_name, current_amount
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND is_delayed = 1 AND delay_days > 30
        ORDER BY delay_days DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        total_value = sum(row['current_amount'] or 0 for row in rows)
        lines = []
        for row in rows:
            lines.append(f"- **{row['title'][:35]}** at {row['school_name'] or 'N/A'}: {row['delay_days']} days late (Vendor: {row['vendor_name'] or 'TBD'})")

        return {
            'answer': f"**{len(rows)} projects** are 30+ days behind schedule, totaling **${total_value:,.0f}** at risk.\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Why is the most delayed project late?', 'Which vendors have delays?', 'Show all delayed projects'],
            'ask_staff': True,
            'next_step': 'Request status update from contractors on these projects',
            'data_note': 'Delay days calculated from original completion date'
        }

    return {
        'answer': "**No projects** are currently more than 30 days behind schedule. All major milestones on track.",
        'suggestions': ['Show budget status', 'Any over budget projects?', 'Top 5 largest projects']
    }


def _handle_over_budget_alerts(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about over-budget projects."""
    cursor.execute('''
        SELECT title, school_name, budget_variance_pct,
               (current_amount - original_amount) as over_amount,
               vendor_name, current_amount
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND is_over_budget = 1
        ORDER BY budget_variance_pct DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        total_overage = sum(row['over_amount'] or 0 for row in rows)
        lines = []
        for row in rows:
            over_amt = row['over_amount'] or 0
            lines.append(f"- **{row['title'][:35]}**: +{row['budget_variance_pct']:.1f}% (${over_amt:,.0f} over)")

        return {
            'answer': f"**{len(rows)} projects** are over budget by a combined **${total_overage:,.0f}**.\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['What caused the overruns?', 'Which vendors are over budget?', 'Show change orders'],
            'ask_staff': True,
            'next_step': 'Review change orders and approve/deny pending requests',
            'data_note': 'Variance calculated against original contract amount'
        }

    return {
        'answer': "**All projects** are currently within budget. No cost overruns to report.",
        'suggestions': ['Show schedule risks', 'Budget summary', 'Upcoming completions']
    }


def _handle_vendor_red_flags(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about vendor red flags."""
    cursor.execute('''
        SELECT vendor_name,
               COUNT(*) as project_count,
               SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_count,
               SUM(CASE WHEN is_over_budget = 1 THEN 1 ELSE 0 END) as over_budget_count,
               SUM(current_amount) as total_value
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND vendor_name IS NOT NULL
        GROUP BY vendor_name
        HAVING delayed_count > 0 OR over_budget_count > 0
        ORDER BY (delayed_count + over_budget_count) DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        lines = []
        for row in rows:
            issues = []
            if row['delayed_count'] > 0:
                issues.append(f"{row['delayed_count']} delayed")
            if row['over_budget_count'] > 0:
                issues.append(f"{row['over_budget_count']} over budget")
            lines.append(f"- **{row['vendor_name']}**: {', '.join(issues)} out of {row['project_count']} projects (${row['total_value']:,.0f} total)")

        return {
            'answer': f"**{len(rows)} vendors** have performance issues:\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Show vendor details', 'Which projects are affected?', 'Vendor performance history'],
            'ask_staff': True,
            'next_step': 'Schedule performance review meetings with flagged vendors'
        }

    return {
        'answer': "**No vendor red flags** at this time. All contractors performing within acceptable parameters.",
        'suggestions': ['Top vendors by value', 'Show all vendors', 'Budget summary']
    }


def _handle_concerns(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle general concerns/worry questions."""
    # Get delayed projects
    cursor.execute('''
        SELECT COUNT(*) as count, SUM(current_amount) as value
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND is_delayed = 1
    ''')
    delayed = cursor.fetchone()

    # Get over budget projects
    cursor.execute('''
        SELECT COUNT(*) as count, SUM(current_amount - original_amount) as overage
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND is_over_budget = 1
    ''')
    over_budget = cursor.fetchone()

    issues = []
    if delayed['count'] > 0:
        issues.append(f"- **{delayed['count']} delayed projects** worth ${delayed['value']:,.0f}")
    if over_budget['count'] > 0:
        issues.append(f"- **{over_budget['count']} over budget** by ${over_budget['overage'] or 0:,.0f} combined")

    if issues:
        return {
            'answer': "**Items requiring attention:**\n\n" + "\n".join(issues),
            'suggestions': ['Show delayed projects', 'Show over budget projects', 'Vendor red flags'],
            'ask_staff': True,
            'next_step': 'Review flagged items before next committee meeting'
        }

    return {
        'answer': "**Portfolio looks healthy.** No major delays or budget overruns to report.",
        'suggestions': ['Budget summary', 'Upcoming completions', 'Top vendors']
    }


def _handle_remaining_budget(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about remaining/unspent budget."""
    cursor.execute('''
        SELECT
            SUM(current_amount) as total_budget,
            SUM(total_paid) as total_spent
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    row = cursor.fetchone()

    if row and row['total_budget']:
        remaining = row['total_budget'] - (row['total_spent'] or 0)
        pct_remaining = (remaining / row['total_budget'] * 100)
        pct_spent = 100 - pct_remaining

        return {
            'answer': f"**${remaining:,.0f}** remaining to spend ({pct_remaining:.1f}% of total budget).\n\n"
                     f"- Total Budget: ${row['total_budget']:,.0f}\n"
                     f"- Spent to Date: ${row['total_spent'] or 0:,.0f} ({pct_spent:.1f}%)",
            'suggestions': ['Spending by category', 'Upcoming completions', 'Show largest projects'],
            'data_note': 'Based on contract values and payment records'
        }

    return {'answer': "Unable to calculate remaining budget.", 'suggestions': ['Show all projects']}


def _handle_largest_projects(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about largest projects."""
    cursor.execute('''
        SELECT title, school_name, current_amount, vendor_name, status, percent_complete
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY current_amount DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        total = sum(row['current_amount'] or 0 for row in rows)
        lines = []
        for i, row in enumerate(rows, 1):
            status_emoji = "" if row['status'] == 'Active' else ""
            lines.append(f"{i}. **{row['title'][:40]}**: ${row['current_amount']:,.0f} ({row['percent_complete']:.0f}% complete)")

        return {
            'answer': f"**Top 5 projects** total **${total:,.0f}**:\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Show project details', 'Any of these delayed?', 'Show by category']
        }

    return {'answer': "No projects found.", 'suggestions': ['Show all projects']}


def _handle_budget_summary(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle budget summary questions."""
    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            COUNT(CASE WHEN status = 'Active' THEN 1 END) as active,
            COUNT(CASE WHEN status = 'Completed' THEN 1 END) as completed,
            SUM(current_amount) as total_budget,
            SUM(total_paid) as total_spent,
            COUNT(CASE WHEN is_delayed = 1 THEN 1 END) as delayed,
            COUNT(CASE WHEN is_over_budget = 1 THEN 1 END) as over_budget
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    row = cursor.fetchone()

    if row:
        spent_pct = (row['total_spent'] or 0) / row['total_budget'] * 100 if row['total_budget'] else 0

        return {
            'answer': f"**Surtax Program Summary**\n\n"
                     f"- **${row['total_budget']:,.0f}** total budget across **{row['total_projects']}** projects\n"
                     f"- **${row['total_spent'] or 0:,.0f}** spent ({spent_pct:.1f}%)\n"
                     f"- **{row['active']}** active, **{row['completed']}** completed\n"
                     f"- **{row['delayed']}** delayed, **{row['over_budget']}** over budget",
            'suggestions': ['Show delayed projects', 'Show over budget', 'Spending by category']
        }

    return {'answer': "No budget data available.", 'suggestions': ['Show all projects']}


def _handle_top_vendor(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about top vendor."""
    cursor.execute('''
        SELECT vendor_name,
               COUNT(*) as project_count,
               SUM(current_amount) as total_value,
               SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_count,
               AVG(percent_complete) as avg_progress
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND vendor_name IS NOT NULL
        GROUP BY vendor_name
        ORDER BY total_value DESC
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row:
        status = "on track" if row['delayed_count'] == 0 else f"with {row['delayed_count']} delayed"
        return {
            'answer': f"**{row['vendor_name']}** has the highest contract value:\n\n"
                     f"- **${row['total_value']:,.0f}** across **{row['project_count']}** projects\n"
                     f"- Average progress: {row['avg_progress']:.0f}%\n"
                     f"- Status: {status}",
            'suggestions': ['Show all vendors', 'Vendor red flags', 'Top 5 vendors']
        }

    return {'answer': "No vendor data available.", 'suggestions': ['Show all projects']}


def _handle_schools_by_projects(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about schools by project count."""
    cursor.execute('''
        SELECT school_name,
               COUNT(*) as project_count,
               SUM(current_amount) as total_value
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND school_name IS NOT NULL
        GROUP BY school_name
        ORDER BY project_count DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        lines = [f"- **{row['school_name']}**: {row['project_count']} projects (${row['total_value']:,.0f})" for row in rows]
        return {
            'answer': f"**Schools with most surtax projects:**\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Show school details', 'Which schools have delays?', 'Category breakdown']
        }

    return {'answer': "No school data available.", 'suggestions': ['Show all projects']}


def _handle_category_split(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about category/type split."""
    cursor.execute('''
        SELECT surtax_category,
               COUNT(*) as count,
               SUM(current_amount) as total
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY total DESC
    ''')
    rows = cursor.fetchall()

    if rows:
        grand_total = sum(row['total'] or 0 for row in rows)
        lines = []
        for row in rows:
            pct = (row['total'] or 0) / grand_total * 100 if grand_total else 0
            lines.append(f"- **{row['surtax_category']}**: ${row['total']:,.0f} ({pct:.0f}%) - {row['count']} projects")

        return {
            'answer': f"**Spending by Category:**\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['New construction details', 'Renovation projects', 'Safety/security spending']
        }

    return {'answer': "No category data available.", 'suggestions': ['Show all projects']}


def _handle_upcoming_completions(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle questions about upcoming completions."""
    today = datetime.now()
    ninety_days = today + timedelta(days=90)

    cursor.execute('''
        SELECT title, school_name, current_end_date, percent_complete, current_amount
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        AND status = 'Active'
        AND current_end_date IS NOT NULL
        AND current_end_date <= ?
        AND current_end_date >= ?
        ORDER BY current_end_date ASC
        LIMIT 5
    ''', (ninety_days.strftime('%Y-%m-%d'), today.strftime('%Y-%m-%d')))
    rows = cursor.fetchall()

    if rows:
        total_value = sum(row['current_amount'] or 0 for row in rows)
        lines = []
        for row in rows:
            lines.append(f"- **{row['title'][:35]}**: {row['current_end_date']} ({row['percent_complete']:.0f}% done)")

        return {
            'answer': f"**{len(rows)} projects** completing in next 90 days (${total_value:,.0f}):\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Any at risk of delay?', 'Show project details', 'Budget summary'],
            'next_step': 'Schedule final inspections for projects near completion'
        }

    return {
        'answer': "**No projects** scheduled to complete in the next 90 days.",
        'suggestions': ['Show active projects', 'Budget summary', 'Delayed projects']
    }


def _handle_vendor_query(cursor: sqlite3.Cursor) -> Dict[str, Any]:
    """Handle general vendor questions."""
    cursor.execute('''
        SELECT vendor_name,
               COUNT(*) as projects,
               SUM(current_amount) as total,
               SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND vendor_name IS NOT NULL
        GROUP BY vendor_name
        ORDER BY total DESC
        LIMIT 5
    ''')
    rows = cursor.fetchall()

    if rows:
        lines = []
        for row in rows:
            status = f" ({row['delayed']} delayed)" if row['delayed'] > 0 else ""
            lines.append(f"- **{row['vendor_name']}**: ${row['total']:,.0f} ({row['projects']} projects){status}")

        return {
            'answer': "**Top Vendors by Contract Value:**\n\n" + "\n".join(lines),
            'data': [dict(row) for row in rows],
            'suggestions': ['Vendor red flags', 'Vendor performance', 'Show all vendors']
        }

    return {'answer': "No vendor data available.", 'suggestions': ['Show all projects']}


def _handle_specific_project(cursor: sqlite3.Cursor, question: str) -> Dict[str, Any]:
    """Handle questions about specific projects."""
    cursor.execute('''
        SELECT * FROM contracts
        WHERE is_deleted = 0
        AND (title LIKE '%High School%' OR title LIKE '%South Marion%' OR title LIKE '%CCC%')
        LIMIT 1
    ''')
    row = cursor.fetchone()

    if row:
        status_note = ""
        if row['is_delayed']:
            status_note = f"\n- **DELAYED** by {row['delay_days']} days"
        if row['is_over_budget']:
            status_note += f"\n- **OVER BUDGET** by {row['budget_variance_pct']:.1f}%"

        return {
            'answer': f"**{row['title'][:50]}**\n\n"
                     f"- Budget: **${row['current_amount']:,.0f}**\n"
                     f"- Vendor: {row['vendor_name'] or 'TBD'}\n"
                     f"- Progress: {row['percent_complete']:.0f}%\n"
                     f"- Status: {row['status']}"
                     f"{status_note}",
            'data': dict(row),
            'suggestions': ['Change orders for this project', 'Vendor performance', 'Similar projects']
        }

    return {'answer': "Project not found.", 'suggestions': ['Show all projects', 'Search by school']}


def _handle_general_query(cursor: sqlite3.Cursor, question: str) -> Dict[str, Any]:
    """Handle general/unrecognized questions."""
    return {
        'answer': "I can answer questions like:\n\n"
                 "- **Budget**: \"How much is left to spend?\" \"Total budget?\"\n"
                 "- **Risks**: \"What projects are delayed?\" \"Any over budget?\"\n"
                 "- **Vendors**: \"Who are our top vendors?\" \"Any vendor issues?\"\n"
                 "- **Projects**: \"Top 5 largest projects\" \"Upcoming completions\"\n\n"
                 "Try clicking one of the quick question chips above!",
        'suggestions': ['Budget summary', 'Schedule risks', 'Vendor red flags']
    }
