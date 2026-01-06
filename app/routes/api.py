"""
API routes: JSON endpoints for AJAX calls and integrations
"""

from flask import Blueprint, jsonify, request, session
from app.database import get_db
from app.services.ai_chat import process_question

api_bp = Blueprint('api', __name__)


@api_bp.route('/ask', methods=['POST'])
def api_ask():
    """Process natural language questions about surtax data."""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': 'No question provided'}), 400

    conn = get_db()
    cursor = conn.cursor()

    result = process_question(question, cursor)

    return jsonify(result)


@api_bp.route('/projects')
def api_projects():
    """Get projects as JSON."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            id, title, school_name, vendor_name, status,
            surtax_category, current_amount, percent_complete,
            is_delayed, delay_days, is_over_budget, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY current_amount DESC
    ''')

    projects = [dict(row) for row in cursor.fetchall()]
    return jsonify({'projects': projects})


@api_bp.route('/stats')
def api_stats():
    """Get summary statistics as JSON."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(current_amount) as total_budget,
            SUM(amount_paid) as total_spent,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'Complete' THEN 1 ELSE 0 END) as completed,
            SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed,
            SUM(CASE WHEN is_over_budget = 1 THEN 1 ELSE 0 END) as over_budget
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')

    stats = dict(cursor.fetchone())
    return jsonify(stats)


# Watchlist API endpoints
@api_bp.route('/watchlist')
def api_watchlist():
    """Get current watchlist."""
    watched_ids = session.get('watchlist', [])
    return jsonify({'watchlist': watched_ids, 'count': len(watched_ids)})


@api_bp.route('/watchlist/add/<contract_id>', methods=['POST'])
def add_to_watchlist(contract_id):
    """Add project to watchlist."""
    watchlist = session.get('watchlist', [])
    if contract_id not in watchlist:
        watchlist.append(contract_id)
        session['watchlist'] = watchlist
    return jsonify({'success': True, 'count': len(watchlist)})


@api_bp.route('/watchlist/remove/<contract_id>', methods=['POST'])
def remove_from_watchlist(contract_id):
    """Remove project from watchlist."""
    watchlist = session.get('watchlist', [])
    if contract_id in watchlist:
        watchlist.remove(contract_id)
        session['watchlist'] = watchlist
    return jsonify({'success': True, 'count': len(watchlist)})


@api_bp.route('/watchlist/toggle/<contract_id>', methods=['POST'])
def toggle_watchlist(contract_id):
    """Toggle project in watchlist."""
    watchlist = session.get('watchlist', [])
    if contract_id in watchlist:
        watchlist.remove(contract_id)
        is_watched = False
    else:
        watchlist.append(contract_id)
        is_watched = True
    session['watchlist'] = watchlist
    return jsonify({'success': True, 'is_watched': is_watched, 'count': len(watchlist)})


@api_bp.route('/watchlist/clear', methods=['POST'])
def clear_watchlist():
    """Clear all items from watchlist."""
    session['watchlist'] = []
    return jsonify({'success': True, 'count': 0})
