"""
Vendor matching and recommendation service.

This module analyzes project characteristics and recommends
ideal vendor profiles based on historical performance data.
"""

import sqlite3
from typing import Dict, Any, List, Optional


def get_ideal_vendor_profile(
    cursor: sqlite3.Cursor,
    project_type: str,
    budget: float,
    complexity: str = 'medium'
) -> Dict[str, Any]:
    """
    Generate ideal vendor profile for a project.

    Args:
        cursor: Database cursor
        project_type: Category of project (e.g., 'New Construction', 'HVAC')
        budget: Project budget amount
        complexity: 'low', 'medium', or 'high'

    Returns:
        Dictionary with recommended vendor characteristics
    """
    # Analyze historical performance for this project type
    cursor.execute('''
        SELECT
            vendor_name,
            vendor_type,
            vendor_size,
            COUNT(*) as projects,
            AVG(CASE WHEN is_delayed = 0 THEN 1.0 ELSE 0.0 END) * 100 as on_time_rate,
            AVG(CASE WHEN is_over_budget = 0 THEN 1.0 ELSE 0.0 END) * 100 as on_budget_rate,
            AVG(percent_complete) as avg_completion,
            SUM(current_amount) as total_value
        FROM contracts
        WHERE is_deleted = 0
        AND surtax_category = ?
        AND vendor_name IS NOT NULL
        GROUP BY vendor_name
        HAVING projects >= 1
        ORDER BY (on_time_rate + on_budget_rate) DESC
    ''', (project_type,))

    top_performers = cursor.fetchall()

    # Determine recommended characteristics
    profile = {
        'project_type': project_type,
        'budget_range': _get_budget_tier(budget),
        'complexity': complexity,
        'recommendations': [],
        'characteristics': {}
    }

    # Size recommendation based on budget
    if budget >= 10_000_000:
        profile['characteristics']['size'] = 'Large or Enterprise'
        profile['characteristics']['bonding_capacity'] = f"Minimum ${budget * 1.25:,.0f}"
        profile['recommendations'].append(
            "Large project - recommend vendors with enterprise-level capacity and bonding"
        )
    elif budget >= 1_000_000:
        profile['characteristics']['size'] = 'Medium to Large'
        profile['characteristics']['bonding_capacity'] = f"Minimum ${budget * 1.5:,.0f}"
        profile['recommendations'].append(
            "Significant project - recommend established vendors with proven track record"
        )
    else:
        profile['characteristics']['size'] = 'Small to Medium'
        profile['characteristics']['bonding_capacity'] = f"Minimum ${budget * 2:,.0f}"
        profile['recommendations'].append(
            "Smaller project - local contractors may offer competitive pricing and responsiveness"
        )

    # Type recommendation based on project category
    category_requirements = {
        'New Construction': {
            'specialization': 'General Contractor with K-12 experience',
            'certifications': ['Licensed General Contractor', 'OSHA certified'],
            'experience': '5+ years school construction'
        },
        'HVAC': {
            'specialization': 'Mechanical/HVAC Contractor',
            'certifications': ['HVAC License', 'EPA 608 Certification'],
            'experience': '3+ years commercial HVAC'
        },
        'Safety & Security': {
            'specialization': 'Security Systems Integrator',
            'certifications': ['Low Voltage License', 'Security clearance preferred'],
            'experience': 'School security systems experience'
        },
        'Renovation': {
            'specialization': 'General Contractor',
            'certifications': ['Licensed General Contractor'],
            'experience': 'Occupied facility renovation experience'
        },
        'Roofing': {
            'specialization': 'Commercial Roofing Contractor',
            'certifications': ['Roofing License', 'Manufacturer certifications'],
            'experience': '5+ years commercial roofing'
        },
        'Technology': {
            'specialization': 'IT Infrastructure/Low Voltage',
            'certifications': ['Low Voltage License', 'Relevant IT certifications'],
            'experience': 'School technology deployments'
        },
        'Site Improvements': {
            'specialization': 'Site Work/Civil Contractor',
            'certifications': ['Licensed Contractor'],
            'experience': 'Site development experience'
        }
    }

    if project_type in category_requirements:
        reqs = category_requirements[project_type]
        profile['characteristics'].update(reqs)
        profile['recommendations'].append(
            f"For {project_type} projects, prioritize vendors with {reqs['specialization']} designation"
        )

    # Local preference recommendation
    profile['characteristics']['location_preference'] = 'Local preferred'
    profile['recommendations'].append(
        "Consider local vendors for economic impact and responsiveness, "
        "but ensure capacity matches project requirements"
    )

    # Add top performers if available
    if top_performers:
        profile['top_performers'] = []
        for vendor in top_performers[:3]:
            profile['top_performers'].append({
                'name': vendor['vendor_name'],
                'projects': vendor['projects'],
                'on_time_rate': vendor['on_time_rate'],
                'on_budget_rate': vendor['on_budget_rate']
            })
        profile['recommendations'].append(
            f"Based on historical data, top performers for {project_type} projects "
            f"achieve {top_performers[0]['on_time_rate']:.0f}% on-time delivery"
        )

    return profile


def _get_budget_tier(budget: float) -> str:
    """Categorize budget into tier."""
    if budget >= 50_000_000:
        return 'Major ($50M+)'
    elif budget >= 10_000_000:
        return 'Large ($10M-$50M)'
    elif budget >= 1_000_000:
        return 'Medium ($1M-$10M)'
    elif budget >= 100_000:
        return 'Small ($100K-$1M)'
    else:
        return 'Minor (<$100K)'


def evaluate_vendor_fit(
    cursor: sqlite3.Cursor,
    vendor_name: str,
    project_type: str,
    budget: float
) -> Dict[str, Any]:
    """
    Evaluate how well a specific vendor fits a project.

    Args:
        cursor: Database cursor
        vendor_name: Name of vendor to evaluate
        project_type: Category of project
        budget: Project budget

    Returns:
        Dictionary with fit score and analysis
    """
    # Get vendor's historical performance
    cursor.execute('''
        SELECT
            COUNT(*) as total_projects,
            SUM(CASE WHEN surtax_category = ? THEN 1 ELSE 0 END) as category_projects,
            AVG(CASE WHEN is_delayed = 0 THEN 1.0 ELSE 0.0 END) * 100 as on_time_rate,
            AVG(CASE WHEN is_over_budget = 0 THEN 1.0 ELSE 0.0 END) * 100 as on_budget_rate,
            MAX(current_amount) as largest_project,
            AVG(current_amount) as avg_project_size
        FROM contracts
        WHERE is_deleted = 0 AND vendor_name = ?
    ''', (project_type, vendor_name))

    vendor = cursor.fetchone()

    if not vendor or vendor['total_projects'] == 0:
        return {
            'vendor': vendor_name,
            'fit_score': 0,
            'status': 'unknown',
            'message': 'No historical data available for this vendor'
        }

    # Calculate fit score (0-100)
    score = 50  # Base score

    # Experience with project type (+/- 20)
    if vendor['category_projects'] >= 3:
        score += 20
    elif vendor['category_projects'] >= 1:
        score += 10
    else:
        score -= 10

    # On-time performance (+/- 15)
    if vendor['on_time_rate'] >= 90:
        score += 15
    elif vendor['on_time_rate'] >= 70:
        score += 5
    else:
        score -= 10

    # On-budget performance (+/- 15)
    if vendor['on_budget_rate'] >= 90:
        score += 15
    elif vendor['on_budget_rate'] >= 70:
        score += 5
    else:
        score -= 10

    # Capacity for project size
    if vendor['largest_project'] and vendor['largest_project'] >= budget:
        score += 10
    elif vendor['avg_project_size'] and vendor['avg_project_size'] >= budget * 0.5:
        score += 5

    score = max(0, min(100, score))  # Clamp to 0-100

    # Determine status
    if score >= 80:
        status = 'excellent'
    elif score >= 60:
        status = 'good'
    elif score >= 40:
        status = 'fair'
    else:
        status = 'poor'

    return {
        'vendor': vendor_name,
        'fit_score': score,
        'status': status,
        'details': {
            'total_projects': vendor['total_projects'],
            'category_experience': vendor['category_projects'],
            'on_time_rate': vendor['on_time_rate'],
            'on_budget_rate': vendor['on_budget_rate'],
            'largest_project': vendor['largest_project'],
            'avg_project_size': vendor['avg_project_size']
        }
    }
