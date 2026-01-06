"""
Main routes: Overview, Projects, Schools, Ask AI
"""

from flask import Blueprint, render_template, request, current_app
from app.database import get_db
from app.services.stats import get_overview_stats, get_spending_by_category

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Dashboard overview page."""
    conn = get_db()
    cursor = conn.cursor()

    stats = get_overview_stats(cursor)
    spending = get_spending_by_category(cursor)

    # Get concerns count (delayed + over budget projects)
    cursor.execute('''
        SELECT
            COUNT(CASE WHEN is_delayed = 1 THEN 1 END) +
            COUNT(CASE WHEN is_over_budget = 1 THEN 1 END) as count
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    concerns_row = cursor.fetchone()
    concerns_count = concerns_row['count'] if concerns_row else 0

    county_config = current_app.config.get('county', {})

    return render_template('main/overview.html',
                          title='Overview',
                          stats=stats,
                          spending=spending,
                          concerns_count=concerns_count,
                          county=county_config)


@main_bp.route('/projects')
def projects():
    """Projects listing page."""
    conn = get_db()
    cursor = conn.cursor()

    # Get filter parameters
    status = request.args.get('status', 'all')
    category = request.args.get('category', 'all')
    sort = request.args.get('sort', 'value')

    # Build query
    query = '''
        SELECT
            contract_id, title, school_name, vendor_name, status,
            surtax_category, current_amount, percent_complete,
            is_delayed, delay_days, is_over_budget, budget_variance_pct
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    '''
    params = []

    if status != 'all':
        query += ' AND status = ?'
        params.append(status)

    if category != 'all':
        query += ' AND surtax_category = ?'
        params.append(category)

    # Sort options
    if sort == 'value':
        query += ' ORDER BY current_amount DESC'
    elif sort == 'progress':
        query += ' ORDER BY percent_complete DESC'
    elif sort == 'risk':
        query += ' ORDER BY is_delayed DESC, delay_days DESC'
    elif sort == 'name':
        query += ' ORDER BY title ASC'

    cursor.execute(query, params)
    projects_list = cursor.fetchall()

    # Get categories for filter dropdown
    cursor.execute('''
        SELECT DISTINCT surtax_category
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY surtax_category
    ''')
    categories = [row['surtax_category'] for row in cursor.fetchall()]

    return render_template('main/projects.html',
                          title='Projects',
                          projects=projects_list,
                          categories=categories,
                          current_status=status,
                          current_category=category,
                          current_sort=sort)


@main_bp.route('/project/<contract_id>')
def project_detail(contract_id):
    """Project detail page."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM contracts WHERE contract_id = ?', (contract_id,))
    project = cursor.fetchone()

    if not project:
        return render_template('errors/404.html', title='Project Not Found'), 404

    return render_template('main/project_detail.html',
                          title=project['title'],
                          project=project)


@main_bp.route('/schools')
def schools():
    """Schools listing page."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            school_name,
            COUNT(*) as project_count,
            COALESCE(SUM(current_amount), 0) as total_value,
            COALESCE(SUM(total_paid), 0) as total_spent,
            AVG(percent_complete) as avg_completion,
            COUNT(CASE WHEN is_delayed = 1 THEN 1 END) as delayed_count
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL AND school_name IS NOT NULL
        GROUP BY school_name
        ORDER BY total_value DESC
    ''')
    schools_list = cursor.fetchall()

    return render_template('main/schools.html',
                          title='Schools',
                          schools=schools_list)


@main_bp.route('/ask')
def ask():
    """AI-powered question interface."""
    return render_template('main/ask.html',
                          title='Ask AI')
