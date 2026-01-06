"""
Database Migration Script for Florida School Surtax Oversight Dashboard

This script adds new columns and tables needed for enhanced analytics:
1. Enhanced vendor fields
2. Expenditure type (Capital vs Operating)
3. Watchlist support
4. Earned Value Analysis fields

Run this script to upgrade an existing contracts database.
"""

import sqlite3
import sys
from pathlib import Path


def get_db_path():
    """Get the database path from the main project."""
    # The app uses the contract-oversight-system database
    base_path = Path(__file__).parent.parent.parent / 'contract-oversight-system' / 'data' / 'contracts.db'
    if base_path.exists():
        return base_path

    # Fallback to local data directory
    local_path = Path(__file__).parent.parent / 'data' / 'surtax.db'
    return local_path


def column_exists(cursor, table, column):
    """Check if a column exists in a table."""
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row[1] for row in cursor.fetchall()]
    return column in columns


def table_exists(cursor, table):
    """Check if a table exists."""
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,)
    )
    return cursor.fetchone() is not None


def migrate_contracts_table(conn):
    """Add new columns to contracts table."""
    cursor = conn.cursor()

    # Enhanced vendor fields
    vendor_columns = [
        ("vendor_type", "TEXT"),           # Local, Regional, National, Publicly Traded
        ("vendor_size", "TEXT"),           # Small, Medium, Large, Enterprise
        ("vendor_headquarters", "TEXT"),
    ]

    # Expenditure classification
    expenditure_columns = [
        ("expenditure_type", "TEXT DEFAULT 'Capital'"),  # Capital, Operating
    ]

    # Watchlist support
    watchlist_columns = [
        ("is_watchlisted", "INTEGER DEFAULT 0"),
    ]

    # Earned Value Analysis fields
    eva_columns = [
        ("planned_value", "REAL"),         # Budgeted Cost of Work Scheduled (BCWS)
        ("earned_value", "REAL"),          # Budgeted Cost of Work Performed (BCWP)
        ("actual_cost", "REAL"),           # Actual Cost of Work Performed (ACWP)
        ("cost_variance", "REAL"),         # EV - AC
        ("schedule_variance", "REAL"),     # EV - PV
        ("cost_performance_index", "REAL"),  # EV / AC (>1 is good)
        ("schedule_performance_index", "REAL"),  # EV / PV (>1 is good)
    ]

    all_columns = vendor_columns + expenditure_columns + watchlist_columns + eva_columns

    added = []
    skipped = []

    for col_name, col_type in all_columns:
        if not column_exists(cursor, 'contracts', col_name):
            try:
                cursor.execute(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}")
                added.append(col_name)
            except sqlite3.OperationalError as e:
                print(f"  Warning: Could not add {col_name}: {e}")
        else:
            skipped.append(col_name)

    if added:
        print(f"  Added columns: {', '.join(added)}")
    if skipped:
        print(f"  Skipped (already exist): {', '.join(skipped)}")

    return len(added) > 0


def create_vendors_table(conn):
    """Create enhanced vendors master table."""
    cursor = conn.cursor()

    if table_exists(cursor, 'vendors'):
        print("  vendors table already exists")
        return False

    cursor.execute('''
        CREATE TABLE vendors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            dba_name TEXT,
            vendor_type TEXT,           -- Local, Regional, National, Publicly Traded
            vendor_size TEXT,           -- Small (<$1M), Medium, Large, Enterprise
            headquarters_city TEXT,
            headquarters_state TEXT,
            years_in_business INTEGER,
            bonding_capacity REAL,
            certifications TEXT,        -- JSON array: MBE, WBE, DBE, etc.
            license_number TEXT,
            insurance_expiry TEXT,
            performance_rating REAL,    -- Calculated 0-100
            total_projects INTEGER DEFAULT 0,
            total_contract_value REAL DEFAULT 0,
            avg_delay_rate REAL DEFAULT 0,
            avg_budget_variance REAL DEFAULT 0,
            notes TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create index
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendors_name ON vendors(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_vendors_type ON vendors(vendor_type)')

    print("  Created vendors table")
    return True


def create_county_benchmarks_table(conn):
    """Create table for county comparison data."""
    cursor = conn.cursor()

    if table_exists(cursor, 'county_benchmarks'):
        print("  county_benchmarks table already exists")
        return False

    cursor.execute('''
        CREATE TABLE county_benchmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            county_name TEXT NOT NULL,
            fips_code TEXT,
            fiscal_year INTEGER,
            metric_name TEXT NOT NULL,
            metric_value REAL,
            metric_unit TEXT,
            data_source TEXT,
            collection_date TEXT DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(county_name, fiscal_year, metric_name)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmarks_county ON county_benchmarks(county_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_benchmarks_metric ON county_benchmarks(metric_name)')

    print("  Created county_benchmarks table")
    return True


def create_project_milestones_table(conn):
    """Create table for tracking project milestones (for Earned Value Analysis)."""
    cursor = conn.cursor()

    if table_exists(cursor, 'project_milestones'):
        print("  project_milestones table already exists")
        return False

    cursor.execute('''
        CREATE TABLE project_milestones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id TEXT NOT NULL,
            milestone_name TEXT NOT NULL,
            milestone_type TEXT,        -- Design, Permit, Construction, Inspection, Closeout
            planned_date TEXT,
            actual_date TEXT,
            planned_cost REAL,
            actual_cost REAL,
            percent_of_total REAL,      -- What % of project this represents
            status TEXT DEFAULT 'Pending',  -- Pending, In Progress, Complete, Delayed
            notes TEXT,
            created_date TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(contract_id)
        )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_milestones_contract ON project_milestones(contract_id)')

    print("  Created project_milestones table")
    return True


def populate_vendors_from_contracts(conn):
    """Populate vendors table from existing contract data."""
    cursor = conn.cursor()

    # Check if vendors table has data
    cursor.execute("SELECT COUNT(*) FROM vendors")
    if cursor.fetchone()[0] > 0:
        print("  vendors table already has data")
        return False

    # Get unique vendors from contracts
    cursor.execute('''
        SELECT
            vendor_name,
            COUNT(*) as project_count,
            SUM(current_amount) as total_value,
            AVG(CASE WHEN is_delayed = 1 THEN 1.0 ELSE 0.0 END) * 100 as delay_rate,
            AVG(budget_variance_pct) as avg_variance
        FROM contracts
        WHERE vendor_name IS NOT NULL AND vendor_name != '' AND is_deleted = 0
        GROUP BY vendor_name
    ''')

    vendors = cursor.fetchall()

    for v in vendors:
        cursor.execute('''
            INSERT OR IGNORE INTO vendors
            (name, total_projects, total_contract_value, avg_delay_rate, avg_budget_variance)
            VALUES (?, ?, ?, ?, ?)
        ''', (v[0], v[1], v[2] or 0, v[3] or 0, v[4] or 0))

    print(f"  Populated {len(vendors)} vendors from contract data")
    return True


def set_default_expenditure_type(conn):
    """Set expenditure_type to 'Capital' for all surtax projects."""
    cursor = conn.cursor()

    # All surtax projects should be Capital by law
    cursor.execute('''
        UPDATE contracts
        SET expenditure_type = 'Capital'
        WHERE surtax_category IS NOT NULL
        AND (expenditure_type IS NULL OR expenditure_type = '')
    ''')

    updated = cursor.rowcount
    if updated > 0:
        print(f"  Set expenditure_type to 'Capital' for {updated} surtax projects")

    return updated > 0


def calculate_earned_value_metrics(conn):
    """Calculate initial Earned Value metrics for projects."""
    cursor = conn.cursor()

    # For projects with budget and completion data, calculate EV metrics
    # PV = current_amount (total planned budget)
    # EV = current_amount * percent_complete (value of work completed)
    # AC = total_paid (actual cost so far)

    # Note: Database uses start_date and current_end_date (not current_start_date)
    cursor.execute('''
        UPDATE contracts
        SET
            planned_value = current_amount,
            earned_value = current_amount * (percent_complete / 100.0),
            actual_cost = total_paid,
            cost_variance = (current_amount * (percent_complete / 100.0)) - total_paid,
            schedule_variance = (current_amount * (percent_complete / 100.0)) -
                               (current_amount * (CAST(julianday('now') - julianday(start_date) AS REAL) /
                                CAST(julianday(current_end_date) - julianday(start_date) AS REAL))),
            cost_performance_index = CASE
                WHEN total_paid > 0 THEN (current_amount * (percent_complete / 100.0)) / total_paid
                ELSE NULL END,
            schedule_performance_index = CASE
                WHEN start_date IS NOT NULL AND current_end_date IS NOT NULL
                AND julianday(current_end_date) > julianday(start_date)
                AND julianday('now') > julianday(start_date)
                THEN (percent_complete / 100.0) /
                     (CAST(julianday('now') - julianday(start_date) AS REAL) /
                      CAST(julianday(current_end_date) - julianday(start_date) AS REAL))
                ELSE NULL END
        WHERE is_deleted = 0
        AND current_amount > 0
        AND surtax_category IS NOT NULL
    ''')

    updated = cursor.rowcount
    print(f"  Calculated Earned Value metrics for {updated} projects")
    return updated > 0


def run_migration():
    """Run all migrations."""
    db_path = get_db_path()
    print(f"\nMigrating database: {db_path}\n")

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))

    try:
        print("1. Migrating contracts table...")
        migrate_contracts_table(conn)

        print("\n2. Creating vendors table...")
        create_vendors_table(conn)

        print("\n3. Creating county_benchmarks table...")
        create_county_benchmarks_table(conn)

        print("\n4. Creating project_milestones table...")
        create_project_milestones_table(conn)

        print("\n5. Populating vendors from contract data...")
        populate_vendors_from_contracts(conn)

        print("\n6. Setting default expenditure types...")
        set_default_expenditure_type(conn)

        print("\n7. Calculating Earned Value metrics...")
        calculate_earned_value_metrics(conn)

        conn.commit()
        print("\n✓ Migration completed successfully!")

    except Exception as e:
        conn.rollback()
        print(f"\nERROR: Migration failed: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    run_migration()
