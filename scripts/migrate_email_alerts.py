#!/usr/bin/env python3
"""
Migration script to add email alert tracking columns.

Run this script to add columns for tracking when alerts were sent.

Usage:
    python scripts/migrate_email_alerts.py
"""

import sqlite3
import sys
from pathlib import Path


def migrate(db_path: str = "data/surtax.db"):
    """Add email alert columns to contracts table."""
    db_file = Path(__file__).parent.parent / db_path
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    print("=" * 60)
    print("Email Alert Migration")
    print("=" * 60)

    # Check if columns already exist
    cursor.execute("PRAGMA table_info(contracts)")
    columns = {row[1] for row in cursor.fetchall()}

    new_columns = [
        ("last_delay_alert_date", "TEXT", None),
        ("last_budget_alert_date", "TEXT", None),
        ("alert_email_sent", "INTEGER", "0"),
    ]

    added = []
    for col_name, col_type, default in new_columns:
        if col_name not in columns:
            default_clause = f" DEFAULT {default}" if default else ""
            cursor.execute(f"ALTER TABLE contracts ADD COLUMN {col_name} {col_type}{default_clause}")
            added.append(col_name)
            print(f"  Added column: {col_name}")

    if added:
        conn.commit()
        print(f"\nMigration complete. Added {len(added)} columns.")
    else:
        print("\nNo migration needed. All columns already exist.")

    conn.close()


if __name__ == "__main__":
    migrate()
