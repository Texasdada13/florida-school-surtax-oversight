"""
County Benchmark Data Import Script

This script imports benchmark data from other Florida counties for comparison analytics.
Data can be sourced from:
- Florida Department of Education (FL DOE)
- County school district websites
- State comptroller reports
- Published surtax oversight reports

Usage:
    python import_county_benchmarks.py --file benchmarks.csv
    python import_county_benchmarks.py --manual  # Enter data manually
    python import_county_benchmarks.py --sample  # Load sample data for testing
"""

import argparse
import csv
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


def get_db_path():
    """Get the database path."""
    # Check for surtax.db first
    surtax_db = Path(__file__).parent.parent / 'data' / 'surtax.db'
    if surtax_db.exists():
        return surtax_db

    # Fallback to contract-oversight-system database
    contracts_db = Path(__file__).parent.parent.parent / 'contract-oversight-system' / 'data' / 'contracts.db'
    if contracts_db.exists():
        return contracts_db

    raise FileNotFoundError("No database found")


def ensure_table_exists(conn):
    """Ensure the county_benchmarks table exists."""
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS county_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            county_name TEXT NOT NULL,
            fips_code TEXT,
            fiscal_year INTEGER,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_unit TEXT,
            data_source TEXT,
            collection_date TEXT DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            UNIQUE(county_name, fiscal_year, metric_name)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmarks_county ON county_benchmarks(county_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmarks_metric ON county_benchmarks(metric_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmarks_year ON county_benchmarks(fiscal_year)')

    conn.commit()
    print("County benchmarks table ready.")


def import_from_csv(conn, filepath):
    """
    Import benchmark data from CSV file.

    Expected CSV format:
    county_name,fips_code,fiscal_year,metric_name,metric_value,metric_unit,data_source,notes
    """
    cursor = conn.cursor()
    imported = 0
    skipped = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO county_benchmarks
                    (county_name, fips_code, fiscal_year, metric_name, metric_value, metric_unit, data_source, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    row['county_name'],
                    row.get('fips_code', ''),
                    int(row['fiscal_year']),
                    row['metric_name'],
                    float(row['metric_value']) if row['metric_value'] else None,
                    row.get('metric_unit', ''),
                    row.get('data_source', 'CSV Import'),
                    row.get('notes', '')
                ))
                imported += 1
            except Exception as e:
                print(f"  Warning: Skipped row - {e}")
                skipped += 1

    conn.commit()
    print(f"Imported {imported} records, skipped {skipped}")


def import_from_json(conn, filepath):
    """
    Import benchmark data from JSON file.

    Expected JSON format:
    [
        {
            "county_name": "Citrus",
            "fips_code": "12017",
            "fiscal_year": 2024,
            "metrics": {
                "total_surtax_revenue": 25000000,
                "total_projects": 35,
                ...
            }
        }
    ]
    """
    cursor = conn.cursor()
    imported = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for county_data in data:
        county_name = county_data['county_name']
        fips_code = county_data.get('fips_code', '')
        fiscal_year = county_data['fiscal_year']
        data_source = county_data.get('data_source', 'JSON Import')

        for metric_name, metric_value in county_data.get('metrics', {}).items():
            try:
                # Determine unit based on metric name
                if 'rate' in metric_name.lower() or 'pct' in metric_name.lower():
                    unit = 'percent'
                elif 'amount' in metric_name.lower() or 'revenue' in metric_name.lower() or 'budget' in metric_name.lower():
                    unit = 'dollars'
                elif 'count' in metric_name.lower() or 'total' in metric_name.lower():
                    unit = 'count'
                elif 'days' in metric_name.lower():
                    unit = 'days'
                else:
                    unit = ''

                cursor.execute('''
                    INSERT OR REPLACE INTO county_benchmarks
                    (county_name, fips_code, fiscal_year, metric_name, metric_value, metric_unit, data_source)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (county_name, fips_code, fiscal_year, metric_name, metric_value, unit, data_source))
                imported += 1
            except Exception as e:
                print(f"  Warning: Skipped {metric_name} - {e}")

    conn.commit()
    print(f"Imported {imported} metrics")


def load_sample_data(conn):
    """
    Load sample benchmark data for testing and demonstration.
    This uses realistic estimates based on typical Florida county surtax programs.
    """
    cursor = conn.cursor()

    # Sample data for comparison counties
    sample_data = [
        # Marion County (our county)
        {
            'county_name': 'Marion',
            'fips_code': '12083',
            'fiscal_year': 2025,
            'metrics': {
                'total_surtax_revenue': 45000000,
                'total_projects': 44,
                'projects_completed': 8,
                'projects_active': 32,
                'projects_delayed': 12,
                'delay_rate': 27.3,
                'projects_over_budget': 5,
                'over_budget_rate': 11.4,
                'avg_project_budget': 1022727,
                'total_budget': 45000000,
                'total_spent': 18500000,
                'avg_completion': 41.0,
                'avg_cpi': 1.05,
                'vendor_count': 28,
                'local_vendor_pct': 65.0,
            }
        },
        # Citrus County (smaller, neighboring)
        {
            'county_name': 'Citrus',
            'fips_code': '12017',
            'fiscal_year': 2025,
            'metrics': {
                'total_surtax_revenue': 25000000,
                'total_projects': 28,
                'projects_completed': 5,
                'projects_active': 20,
                'projects_delayed': 6,
                'delay_rate': 21.4,
                'projects_over_budget': 3,
                'over_budget_rate': 10.7,
                'avg_project_budget': 892857,
                'total_budget': 25000000,
                'total_spent': 9800000,
                'avg_completion': 39.2,
                'avg_cpi': 1.08,
                'vendor_count': 18,
                'local_vendor_pct': 72.0,
            }
        },
        # Alachua County (larger, university town)
        {
            'county_name': 'Alachua',
            'fips_code': '12001',
            'fiscal_year': 2025,
            'metrics': {
                'total_surtax_revenue': 65000000,
                'total_projects': 52,
                'projects_completed': 12,
                'projects_active': 35,
                'projects_delayed': 8,
                'delay_rate': 15.4,
                'projects_over_budget': 4,
                'over_budget_rate': 7.7,
                'avg_project_budget': 1250000,
                'total_budget': 65000000,
                'total_spent': 31200000,
                'avg_completion': 48.0,
                'avg_cpi': 1.12,
                'vendor_count': 35,
                'local_vendor_pct': 58.0,
            }
        },
        # Lake County (similar size)
        {
            'county_name': 'Lake',
            'fips_code': '12069',
            'fiscal_year': 2025,
            'metrics': {
                'total_surtax_revenue': 55000000,
                'total_projects': 48,
                'projects_completed': 10,
                'projects_active': 34,
                'projects_delayed': 14,
                'delay_rate': 29.2,
                'projects_over_budget': 7,
                'over_budget_rate': 14.6,
                'avg_project_budget': 1145833,
                'total_budget': 55000000,
                'total_spent': 22000000,
                'avg_completion': 40.0,
                'avg_cpi': 0.98,
                'vendor_count': 30,
                'local_vendor_pct': 60.0,
            }
        },
        # Sumter County (smaller, retirement community)
        {
            'county_name': 'Sumter',
            'fips_code': '12119',
            'fiscal_year': 2025,
            'metrics': {
                'total_surtax_revenue': 18000000,
                'total_projects': 22,
                'projects_completed': 6,
                'projects_active': 14,
                'projects_delayed': 3,
                'delay_rate': 13.6,
                'projects_over_budget': 2,
                'over_budget_rate': 9.1,
                'avg_project_budget': 818182,
                'total_budget': 18000000,
                'total_spent': 8100000,
                'avg_completion': 45.0,
                'avg_cpi': 1.15,
                'vendor_count': 12,
                'local_vendor_pct': 75.0,
            }
        },
    ]

    imported = 0
    for county_data in sample_data:
        county_name = county_data['county_name']
        fips_code = county_data['fips_code']
        fiscal_year = county_data['fiscal_year']

        for metric_name, metric_value in county_data['metrics'].items():
            # Determine unit
            if 'rate' in metric_name or 'pct' in metric_name:
                unit = 'percent'
            elif 'revenue' in metric_name or 'budget' in metric_name or 'spent' in metric_name:
                unit = 'dollars'
            elif 'count' in metric_name or 'total' in metric_name or 'projects' in metric_name:
                unit = 'count'
            elif 'cpi' in metric_name:
                unit = 'ratio'
            else:
                unit = ''

            cursor.execute('''
                INSERT OR REPLACE INTO county_benchmarks
                (county_name, fips_code, fiscal_year, metric_name, metric_value, metric_unit, data_source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (county_name, fips_code, fiscal_year, metric_name, metric_value, unit, 'Sample Data'))
            imported += 1

    conn.commit()
    print(f"Loaded {imported} sample benchmark metrics for {len(sample_data)} counties")


def manual_entry(conn):
    """Interactive manual entry of benchmark data."""
    cursor = conn.cursor()

    print("\n=== Manual Benchmark Data Entry ===")
    print("Enter 'done' when finished.\n")

    while True:
        county_name = input("County name (or 'done'): ").strip()
        if county_name.lower() == 'done':
            break

        fiscal_year = input("Fiscal year: ").strip()
        if not fiscal_year.isdigit():
            print("Invalid year. Skipping.")
            continue

        print("\nEnter metrics (name=value). Enter blank line when done with this county.")
        print("Examples: total_projects=45, delay_rate=25.5, total_budget=50000000\n")

        while True:
            metric_input = input("  Metric (name=value): ").strip()
            if not metric_input:
                break

            try:
                name, value = metric_input.split('=')
                name = name.strip()
                value = float(value.strip())

                cursor.execute('''
                    INSERT OR REPLACE INTO county_benchmarks
                    (county_name, fiscal_year, metric_name, metric_value, data_source)
                    VALUES (?, ?, ?, ?, ?)
                ''', (county_name, int(fiscal_year), name, value, 'Manual Entry'))
                print(f"    Added: {name} = {value}")
            except Exception as e:
                print(f"    Error: {e}")

        conn.commit()
        print(f"Saved metrics for {county_name}\n")


def show_summary(conn):
    """Show summary of imported benchmark data."""
    cursor = conn.cursor()

    cursor.execute('''
        SELECT
            county_name,
            fiscal_year,
            COUNT(*) as metric_count
        FROM county_benchmarks
        GROUP BY county_name, fiscal_year
        ORDER BY county_name, fiscal_year DESC
    ''')

    print("\n=== Benchmark Data Summary ===")
    print(f"{'County':<15} {'Year':<6} {'Metrics':<10}")
    print("-" * 35)

    for row in cursor.fetchall():
        print(f"{row[0]:<15} {row[1]:<6} {row[2]:<10}")

    cursor.execute('SELECT COUNT(*) FROM county_benchmarks')
    total = cursor.fetchone()[0]
    print("-" * 35)
    print(f"Total records: {total}")


def main():
    parser = argparse.ArgumentParser(description='Import county benchmark data for comparison analytics')
    parser.add_argument('--file', '-f', help='CSV or JSON file to import')
    parser.add_argument('--manual', '-m', action='store_true', help='Manual data entry mode')
    parser.add_argument('--sample', '-s', action='store_true', help='Load sample data for testing')
    parser.add_argument('--summary', action='store_true', help='Show summary of existing data')

    args = parser.parse_args()

    try:
        db_path = get_db_path()
        print(f"Using database: {db_path}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    try:
        ensure_table_exists(conn)

        if args.file:
            filepath = Path(args.file)
            if not filepath.exists():
                print(f"Error: File not found: {filepath}")
                sys.exit(1)

            if filepath.suffix.lower() == '.csv':
                import_from_csv(conn, filepath)
            elif filepath.suffix.lower() == '.json':
                import_from_json(conn, filepath)
            else:
                print(f"Error: Unsupported file format: {filepath.suffix}")
                sys.exit(1)

        elif args.manual:
            manual_entry(conn)

        elif args.sample:
            load_sample_data(conn)

        elif args.summary:
            pass  # Just show summary

        else:
            print("No action specified. Use --help for options.")
            print("\nQuick start:")
            print("  python import_county_benchmarks.py --sample   # Load sample data")
            print("  python import_county_benchmarks.py --summary  # View existing data")

        show_summary(conn)

    finally:
        conn.close()


if __name__ == '__main__':
    main()
