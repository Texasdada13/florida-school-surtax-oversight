"""
API routes: JSON endpoints for AJAX calls and integrations
"""

from flask import Blueprint, jsonify, request, session
from app.database import get_db
from app.services.ai_chat import process_question
from app.services.email_alerts import EmailAlertService, check_and_send_alerts

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
    """Get summary statistics as JSON for the Ask AI context sidebar."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(current_amount) as total_budget,
            SUM(total_paid) as total_spent,
            SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) as active_projects,
            SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) as completed_projects,
            SUM(CASE WHEN is_delayed = 1 THEN 1 ELSE 0 END) as delayed_projects,
            SUM(CASE WHEN is_over_budget = 1 THEN 1 ELSE 0 END) as over_budget_projects
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


# Email Alert API endpoints
@api_bp.route('/alerts/status')
def alert_status():
    """Get email alert configuration status."""
    service = EmailAlertService()
    return jsonify({
        'enabled': service.is_enabled(),
        'configured': bool(service.config.smtp_host),
        'recipients': len(service.config.to_emails) if service.config.to_emails else 0
    })


@api_bp.route('/alerts/check', methods=['POST'])
def check_alerts():
    """Manually trigger alert check (for testing/admin use)."""
    conn = get_db()
    cursor = conn.cursor()

    result = check_and_send_alerts(cursor)
    conn.commit()

    return jsonify(result)


@api_bp.route('/alerts/test', methods=['POST'])
def test_alert():
    """Send a test alert email."""
    service = EmailAlertService()

    if not service.is_enabled():
        return jsonify({
            'success': False,
            'error': 'Email alerts not configured. Set SMTP_HOST and ALERT_EMAIL_TO environment variables.'
        }), 400

    html_body = """
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <div style="background: #22C55E; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
            <h2 style="margin: 0;">Test Alert - Success!</h2>
        </div>
        <div style="padding: 20px; background: #F0FDF4; border: 1px solid #BBF7D0;">
            <p>This is a test email from the Florida School Surtax Oversight Dashboard.</p>
            <p>If you received this email, your alert configuration is working correctly.</p>
        </div>
        <div style="padding: 15px; background: #F3F4F6; color: #666; font-size: 12px; text-align: center;">
            Florida School Surtax Oversight Dashboard
        </div>
    </body>
    </html>
    """

    success = service.send_email("Test Alert", html_body, "This is a test alert email.")

    return jsonify({
        'success': success,
        'message': 'Test email sent successfully!' if success else 'Failed to send test email.'
    })
