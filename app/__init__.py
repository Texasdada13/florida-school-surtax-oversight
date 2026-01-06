"""
Florida School Surtax Oversight Dashboard
A template-based oversight tool for Florida school district surtax monitoring.

This application uses the Flask App Factory pattern to support:
- Multiple county configurations
- Easy testing
- Flexible deployment options
"""

from flask import Flask
from pathlib import Path
import os


def create_app(county: str = None, config_override: dict = None):
    """
    Application factory for creating Flask app instances.

    Args:
        county: County name (e.g., 'marion'). If None, uses COUNTY env var or defaults to 'marion'
        config_override: Optional dict to override config values (useful for testing)

    Returns:
        Configured Flask application
    """
    app = Flask(__name__,
                template_folder='templates',
                static_folder='static')

    # Determine which county config to load
    county = county or os.environ.get('SURTAX_COUNTY', 'marion')

    # Load configuration
    from app.config import load_config
    config = load_config(county)

    # Apply any overrides
    if config_override:
        config.update(config_override)

    # Store config in app
    app.config.update(config)
    app.config['COUNTY'] = county

    # Set secret key
    app.secret_key = os.environ.get('SECRET_KEY', config.get('app', {}).get('secret_key', 'dev-key-change-in-production'))

    # Initialize extensions
    _init_extensions(app)

    # Register template filters
    _register_filters(app)

    # Register blueprints (routes)
    _register_blueprints(app)

    # Register error handlers
    _register_error_handlers(app)

    return app


def _init_extensions(app):
    """Initialize Flask extensions."""
    # Add extensions here as needed (e.g., Flask-SQLAlchemy, Flask-Login)
    pass


def _register_filters(app):
    """Register Jinja2 template filters."""

    @app.template_filter('currency')
    def currency_filter(value):
        """Format as currency."""
        if value is None:
            return '$0'
        if abs(value) >= 1_000_000:
            return f'${value/1_000_000:,.1f}M'
        elif abs(value) >= 1_000:
            return f'${value/1_000:,.0f}K'
        return f'${value:,.0f}'

    @app.template_filter('currency_full')
    def currency_full_filter(value):
        """Format as full currency (no abbreviation)."""
        if value is None:
            return '$0'
        return f'${value:,.0f}'

    @app.template_filter('percent')
    def percent_filter(value):
        """Format as percentage."""
        if value is None:
            return '0%'
        return f'{value:.1f}%'

    @app.template_filter('date')
    def date_filter(value, format='%b %d, %Y'):
        """Format date string."""
        if value is None:
            return ''
        if isinstance(value, str):
            from datetime import datetime
            try:
                value = datetime.strptime(value, '%Y-%m-%d')
            except ValueError:
                return value
        return value.strftime(format)


def _register_blueprints(app):
    """Register route blueprints."""
    from app.routes.main import main_bp
    from app.routes.monitoring import monitoring_bp
    from app.routes.financials import financials_bp
    from app.routes.documents import documents_bp
    from app.routes.tools import tools_bp
    from app.routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(monitoring_bp)
    app.register_blueprint(financials_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(tools_bp)
    app.register_blueprint(api_bp, url_prefix='/api')


def _register_error_handlers(app):
    """Register error handlers."""
    import traceback
    import sys

    @app.errorhandler(404)
    def not_found_error(error):
        from flask import render_template
        return render_template('errors/404.html', title='Page Not Found'), 404

    @app.errorhandler(500)
    def internal_error(error):
        from flask import render_template
        print(f"500 ERROR: {error}", file=sys.stderr, flush=True)
        traceback.print_exc()
        return render_template('errors/500.html', title='Server Error'), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        from flask import render_template
        print(f"UNHANDLED EXCEPTION: {error}", file=sys.stderr, flush=True)
        traceback.print_exc()
        return render_template('errors/500.html', title='Server Error'), 500
