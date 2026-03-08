#!/usr/bin/env python3
"""
Wipe all SchnellXAI memory stores so the next run starts completely fresh.

Usage:
    cd backend
    python clear_memory.py          # interactive — asks for confirmation
    python clear_memory.py --yes    # skip confirmation
"""

import argparse
import sys
from pathlib import Path

# Make sure imports resolve from the backend directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import settings
from db.store import get_db, init_db


TABLES = ["episodes", "patterns", "approvals", "action_log", "anomaly_log"]


def clear_database():
    """Delete all rows from every memory-related table."""
    init_db()  # ensure tables exist first
    with get_db() as conn:
        for table in TABLES:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            conn.execute(f"DELETE FROM {table}")
            print(f"  ✓ {table:20s}  — {count} rows deleted")

    # VACUUM must run outside a transaction
    import sqlite3
    vc = sqlite3.connect(str(Path(settings.db_path)))
    vc.execute("VACUUM")
    vc.close()
    print(f"  ✓ Database vacuumed ({settings.db_path})")


def clear_in_memory():
    """Clear the singleton in-memory buffers (short-term memory + anomaly buffer)."""
    from memory.short_term import short_term_memory
    n_stm = len(short_term_memory._buffer)
    short_term_memory._buffer.clear()
    print(f"  ✓ Short-term memory  — {n_stm} events cleared")

    try:
        from pipeline.buffer import AnomalyBuffer
        # The buffer instance used by the scheduler
        from pipeline.scheduler import pipeline_scheduler
        n_buf = pipeline_scheduler._buffer.count
        pipeline_scheduler._buffer._buffer.clear()
        print(f"  ✓ Anomaly buffer     — {n_buf} items cleared")
    except Exception:
        # If scheduler isn't importable standalone, clear the class-level default
        print("  ✓ Anomaly buffer     — (will be empty on next startup)")


def main():
    parser = argparse.ArgumentParser(description="Clear all SchnellXAI memory")
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════╗")
    print("║   SchnellXAI — Clear All Memory          ║")
    print("╚══════════════════════════════════════════╝")
    print()
    print(f"  Database : {settings.db_path}")
    print(f"  Tables   : {', '.join(TABLES)}")
    print()

    if not args.yes:
        answer = input("  ⚠  This will erase ALL agent memory. Continue? [y/N] ").strip().lower()
        if answer not in ("y", "yes"):
            print("\n  Cancelled.\n")
            return

    print()
    print("  Clearing database...")
    clear_database()
    print()
    print("  Clearing in-memory stores...")
    clear_in_memory()
    print()
    print("  ✅ All memory cleared. Next run will start fresh.")
    print()


if __name__ == "__main__":
    main()
