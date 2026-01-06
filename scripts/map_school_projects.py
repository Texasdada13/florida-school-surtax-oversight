#!/usr/bin/env python3
"""
Script to automatically map school names to surtax projects.

Run this script to populate the school_name field for contracts
that don't have one assigned.

Usage:
    python scripts/map_school_projects.py [--dry-run]
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.school_mapping import auto_map_schools, get_unmapped_contracts


def main():
    parser = argparse.ArgumentParser(
        description="Map school names to surtax projects"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be mapped without making changes"
    )
    parser.add_argument(
        "--db",
        default="data/surtax.db",
        help="Path to database file"
    )
    args = parser.parse_args()

    # Connect to database
    db_path = Path(__file__).parent.parent / args.db
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("=" * 60)
    print("School Name Mapping for Surtax Projects")
    print("=" * 60)
    print()

    if args.dry_run:
        print("[DRY RUN - No changes will be made]")
        print()

        # Just show what would be mapped
        unmapped = get_unmapped_contracts(cursor)
        print(f"Found {len(unmapped)} contracts without school names:")
        print()

        for contract in unmapped[:15]:
            from app.services.school_mapping import map_school_for_contract
            school, confidence = map_school_for_contract(
                contract["title"],
                contract["location"],
                contract["category"]
            )
            status = f"-> {school} ({confidence})" if school else "-> [No match]"
            print(f"  {contract['contract_id'][:20]}: {contract['title'][:40]}...")
            print(f"      {status}")
            print()

        if len(unmapped) > 15:
            print(f"  ... and {len(unmapped) - 15} more")
    else:
        # Actually perform the mapping
        stats = auto_map_schools(cursor)
        conn.commit()

        print("Mapping Results:")
        print(f"  Total unmapped before: {stats['total_unmapped']}")
        print(f"  Mapped (high confidence): {stats['mapped_high']}")
        print(f"  Mapped (medium confidence): {stats['mapped_medium']}")
        print(f"  Still unmapped: {stats['still_unmapped']}")
        print()

        if stats['still_unmapped'] > 0:
            print("Contracts that still need manual mapping:")
            unmapped = get_unmapped_contracts(cursor)
            for contract in unmapped[:10]:
                print(f"  - {contract['contract_id']}: {contract['title'][:50]}...")
            if len(unmapped) > 10:
                print(f"  ... and {len(unmapped) - 10} more")

    conn.close()
    print()
    print("Done!")


if __name__ == "__main__":
    main()
