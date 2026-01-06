"""
Financial routes: Vendors, Change Orders, Analytics, Budget Performance
"""

from flask import Blueprint, render_template, request
from app.database import get_db

financials_bp = Blueprint('financials', __name__)


@financials_bp.route('/vendors')
def vendors():
    """Vendor Performance tracking with ratings."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            vendor_name,
            COUNT(*) as project_count,
            SUM(current_amount) as total_value,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 100 as overbudget_rate,
            AVG(percent_complete) as avg_completion,
            AVG(cost_performance_index) as avg_cpi,
            -- Performance score: 100 - delay_rate - overbudget_rate + (cpi bonus)
            100 - (AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 50)
                - (AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 50)
                + COALESCE((AVG(cost_performance_index) - 1) * 20, 0) as performance_score,
            GROUP_CONCAT(DISTINCT surtax_category) as categories
        FROM contracts
        WHERE is_deleted = 0 AND vendor_name IS NOT NULL AND vendor_name != ''
        GROUP BY vendor_name
        ORDER BY total_value DESC
    ''')
    vendors_list = cursor.fetchall()

    # Summary stats
    cursor.execute('''
        SELECT
            COUNT(DISTINCT vendor_name) as total_vendors,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as avg_delay_rate,
            AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 100 as avg_overbudget_rate
        FROM contracts
        WHERE is_deleted = 0 AND vendor_name IS NOT NULL AND vendor_name != ''
    ''')
    summary = cursor.fetchone()

    return render_template('financials/vendors.html',
                          title='Vendor Performance',
                          vendors=vendors_list,
                          summary=summary)


@financials_bp.route('/vendor-profile')
def vendor_profile_tool():
    """Ideal Vendor Profile Tool - suggests vendor characteristics based on project type."""
    conn = get_db()
    cursor = conn.cursor()

    # Get project type from query params (if analyzing specific project)
    project_type = request.args.get('category', None)
    budget_range = request.args.get('budget', None)

    # Get category performance stats
    cursor.execute('''
        SELECT
            surtax_category,
            COUNT(*) as project_count,
            AVG(current_amount) as avg_budget,
            MIN(current_amount) as min_budget,
            MAX(current_amount) as max_budget,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            AVG(CASE WHEN is_over_budget = 1 THEN 1.0 ELSE 0.0 END) * 100 as overbudget_rate,
            AVG(cost_performance_index) as avg_cpi
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY project_count DESC
    ''')
    category_stats = cursor.fetchall()

    # Get top performing vendors by category
    cursor.execute('''
        SELECT
            surtax_category,
            vendor_name,
            COUNT(*) as projects,
            AVG(cost_performance_index) as avg_cpi,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            SUM(current_amount) as total_value
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND vendor_name IS NOT NULL AND vendor_name != ''
        GROUP BY surtax_category, vendor_name
        HAVING COUNT(*) >= 2
        ORDER BY surtax_category, avg_cpi DESC
    ''')
    vendor_by_category = cursor.fetchall()

    # Build recommendations by category
    recommendations = {}
    for cat in category_stats:
        cat_name = cat['surtax_category']
        avg_budget = cat['avg_budget'] or 0

        # Determine recommended vendor size based on budget
        if avg_budget < 100000:
            size_rec = 'Small to Medium'
            bonding_rec = '$500K - $1M'
        elif avg_budget < 500000:
            size_rec = 'Medium'
            bonding_rec = '$1M - $5M'
        elif avg_budget < 2000000:
            size_rec = 'Medium to Large'
            bonding_rec = '$5M - $10M'
        else:
            size_rec = 'Large'
            bonding_rec = '$10M+'

        # Category-specific recommendations
        specializations = {
            'HVAC': ['HVAC certification', 'EPA 608 certification', 'Sheet metal experience'],
            'Roofing': ['Licensed roofing contractor', 'Manufacturer certifications', 'Storm damage experience'],
            'Safety & Security': ['Security systems certification', 'Low voltage license', 'Access control experience'],
            'Technology': ['Network infrastructure', 'Structured cabling', 'AV integration'],
            'New Construction': ['General contractor license', 'LEED certification', 'School construction experience'],
            'Renovation': ['Historic preservation (if applicable)', 'Occupied facility experience', 'Phased construction'],
            'Site Improvements': ['Paving license', 'Drainage/stormwater', 'ADA compliance'],
        }

        recommendations[cat_name] = {
            'avg_budget': avg_budget,
            'size_recommendation': size_rec,
            'bonding_recommendation': bonding_rec,
            'delay_rate': cat['delay_rate'],
            'overbudget_rate': cat['overbudget_rate'],
            'specializations': specializations.get(cat_name, ['General contracting']),
            'top_vendors': [v for v in vendor_by_category if v['surtax_category'] == cat_name][:3]
        }

    # Get all categories for dropdown
    categories = [cat['surtax_category'] for cat in category_stats]

    return render_template('financials/vendor_profile.html',
                          title='Ideal Vendor Profile',
                          category_stats=category_stats,
                          recommendations=recommendations,
                          categories=categories,
                          selected_category=project_type)


@financials_bp.route('/change-orders')
def change_orders():
    """Change Order tracking."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            contract_id, title, school_name, vendor_name,
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
            COALESCE(SUM(current_amount), 0) as total_budget,
            COALESCE(SUM(total_paid), 0) as total_spent,
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
    """Budget Performance - Proposed vs Actual vs Progress analysis with Earned Value."""
    conn = get_db()
    cursor = conn.cursor()

    # Get projects with budget, progress, and EVA data
    cursor.execute('''
        SELECT
            contract_id, title, school_name, surtax_category,
            original_amount, current_amount, total_paid,
            percent_complete,
            CASE WHEN original_amount > 0
                THEN (total_paid / original_amount * 100)
                ELSE 0 END as spend_rate,
            CASE WHEN current_amount > 0
                THEN (total_paid / current_amount * 100)
                ELSE 0 END as budget_utilization,
            -- Earned Value Analysis fields
            planned_value, earned_value, actual_cost,
            cost_variance, cost_performance_index,
            -- Spending vs Progress indicator
            CASE
                WHEN percent_complete > 0 AND current_amount > 0
                THEN (total_paid / current_amount * 100) - percent_complete
                ELSE 0
            END as spend_progress_gap
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        ORDER BY current_amount DESC
    ''')
    projects = cursor.fetchall()

    # Summary stats with EVA totals
    cursor.execute('''
        SELECT
            COALESCE(SUM(original_amount), 0) as total_original,
            COALESCE(SUM(current_amount), 0) as total_current,
            COALESCE(SUM(total_paid), 0) as total_spent,
            AVG(percent_complete) as avg_progress,
            -- EVA totals
            COALESCE(SUM(planned_value), 0) as total_pv,
            COALESCE(SUM(earned_value), 0) as total_ev,
            COALESCE(SUM(actual_cost), 0) as total_ac,
            -- Overall CPI (EV/AC)
            CASE WHEN SUM(actual_cost) > 0
                THEN SUM(earned_value) / SUM(actual_cost)
                ELSE NULL END as portfolio_cpi,
            -- Count of projects by health
            SUM(CASE WHEN cost_performance_index >= 1.0 THEN 1 ELSE 0 END) as on_budget_count,
            SUM(CASE WHEN cost_performance_index < 1.0 AND cost_performance_index >= 0.9 THEN 1 ELSE 0 END) as near_budget_count,
            SUM(CASE WHEN cost_performance_index < 0.9 AND cost_performance_index IS NOT NULL THEN 1 ELSE 0 END) as over_budget_count
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
    ''')
    summary = cursor.fetchone()

    # By surtax category with EVA
    cursor.execute('''
        SELECT
            COALESCE(surtax_category, 'Unclassified') as category,
            COUNT(*) as count,
            COALESCE(SUM(current_amount), 0) as budget,
            COALESCE(SUM(total_paid), 0) as spent,
            AVG(percent_complete) as avg_progress,
            AVG(cost_performance_index) as avg_cpi
        FROM contracts
        WHERE is_deleted = 0 AND surtax_category IS NOT NULL
        GROUP BY surtax_category
        ORDER BY budget DESC
    ''')
    by_category = cursor.fetchall()

    # Projects with spending outpacing progress (potential concerns)
    cursor.execute('''
        SELECT
            contract_id, title, school_name,
            percent_complete,
            CASE WHEN current_amount > 0
                THEN (total_paid / current_amount * 100)
                ELSE 0 END as spend_pct,
            cost_performance_index
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category IS NOT NULL
        AND total_paid > 0
        AND cost_performance_index IS NOT NULL
        AND cost_performance_index < 0.9
        ORDER BY cost_performance_index ASC
        LIMIT 10
    ''')
    spending_concerns = cursor.fetchall()

    return render_template('financials/budget_performance.html',
                          title='Budget Performance',
                          projects=projects,
                          summary=summary,
                          by_category=by_category,
                          spending_concerns=spending_concerns)


@financials_bp.route('/county-comparison')
def county_comparison():
    """County Comparison Analytics - compare Marion County against neighboring counties."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if county_benchmarks table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='county_benchmarks'")
    if not cursor.fetchone():
        return render_template('financials/county_comparison.html',
                              title='County Comparison',
                              has_data=False,
                              counties=[],
                              metrics={},
                              our_county='Marion')

    # Get all counties with data
    cursor.execute('''
        SELECT DISTINCT county_name, fips_code, fiscal_year
        FROM county_benchmarks
        ORDER BY county_name
    ''')
    county_list = cursor.fetchall()

    # Get all metrics for comparison
    cursor.execute('''
        SELECT county_name, metric_name, metric_value, metric_unit
        FROM county_benchmarks
        WHERE fiscal_year = (SELECT MAX(fiscal_year) FROM county_benchmarks)
        ORDER BY county_name, metric_name
    ''')
    raw_metrics = cursor.fetchall()

    # Organize metrics by county
    metrics_by_county = {}
    all_metric_names = set()
    for row in raw_metrics:
        county = row['county_name']
        metric = row['metric_name']
        value = row['metric_value']

        if county not in metrics_by_county:
            metrics_by_county[county] = {}
        metrics_by_county[county][metric] = value
        all_metric_names.add(metric)

    # Calculate rankings for each metric
    rankings = {}
    for metric in all_metric_names:
        values = [(county, data.get(metric)) for county, data in metrics_by_county.items() if data.get(metric) is not None]

        # Determine if higher or lower is better
        lower_is_better = any(x in metric.lower() for x in ['delay', 'over_budget', 'rate'])

        if lower_is_better:
            values.sort(key=lambda x: x[1])  # Lower first = rank 1
        else:
            values.sort(key=lambda x: x[1], reverse=True)  # Higher first = rank 1

        rankings[metric] = {county: rank + 1 for rank, (county, _) in enumerate(values)}

    # Key metrics to highlight
    key_metrics = [
        ('total_projects', 'Total Projects', 'count', False),
        ('total_surtax_revenue', 'Surtax Revenue', 'currency', False),
        ('delay_rate', 'Delay Rate', 'percent', True),
        ('over_budget_rate', 'Over Budget Rate', 'percent', True),
        ('avg_completion', 'Avg Completion', 'percent', False),
        ('avg_cpi', 'Avg CPI', 'ratio', False),
        ('local_vendor_pct', 'Local Vendor %', 'percent', False),
    ]

    return render_template('financials/county_comparison.html',
                          title='County Comparison',
                          has_data=len(metrics_by_county) > 0,
                          counties=list(metrics_by_county.keys()),
                          metrics=metrics_by_county,
                          rankings=rankings,
                          key_metrics=key_metrics,
                          our_county='Marion')
