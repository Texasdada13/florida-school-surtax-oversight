#!/usr/bin/env python
"""
Run the Florida School Surtax Oversight Dashboard.

Usage:
    python run.py                    # Run with default county (marion)
    python run.py --county citrus    # Run with specific county
    python run.py --port 8080        # Run on specific port
"""

import argparse
import os
import sys

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    parser = argparse.ArgumentParser(description='Run the Surtax Oversight Dashboard')
    parser.add_argument('--county', default='marion', help='County configuration to use')
    parser.add_argument('--host', default='127.0.0.1', help='Host to bind to')
    parser.add_argument('--port', type=int, default=5847, help='Port to run on')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')

    args = parser.parse_args()

    # Set environment variable for county
    os.environ['SURTAX_COUNTY'] = args.county

    # Create and run the app
    app = create_app(county=args.county)

    print(f"\n{'='*60}")
    print(f"  Florida School Surtax Oversight Dashboard")
    print(f"  County: {args.county.title()}")
    print(f"  URL: http://{args.host}:{args.port}")
    print(f"{'='*60}\n")

    app.run(
        host=args.host,
        port=args.port,
        debug=args.debug or app.config.get('app', {}).get('debug', False)
    )


if __name__ == '__main__':
    main()
