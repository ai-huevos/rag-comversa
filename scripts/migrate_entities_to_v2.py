#!/usr/bin/env python3
"""Utility script to backfill v2.0 organizational fields on legacy entities."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Dict, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from intelligence_capture.config import DB_PATH
from intelligence_capture.database import EnhancedIntelligenceDB


TABLES_TO_ENRICH: Dict[str, List[str]] = {
    "pain_points": ["business_unit", "department"],
    "processes": ["business_unit", "department"],
    "automation_candidates": ["business_unit", "department"],
}


def column_exists(db, table: str, column: str) -> bool:
    cursor = db.conn.cursor()
    cursor.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cursor.fetchall())


def rows_missing(conn, table: str, column: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT COUNT(*) FROM {table} WHERE {column} IS NULL OR TRIM({column}) = ''"
    )
    return cursor.fetchone()[0]


def backfill_from_interviews(conn, table: str, column: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE {table}
        SET {column} = (
            SELECT COALESCE({column}, 'Unknown')
            FROM interviews i
            WHERE i.id = {table}.interview_id
        )
        WHERE ({column} IS NULL OR TRIM({column}) = '')
          AND EXISTS (
            SELECT 1 FROM interviews i WHERE i.id = {table}.interview_id
          )
        """
    )
    conn.commit()
    return cursor.rowcount


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--db",
        type=Path,
        default=DB_PATH,
        help="Ruta al archivo SQLite (default: data/full_intelligence.db)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Solo mostrar cuántos registros serían actualizados",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    db_path: Path = args.db

    enhanced_db = EnhancedIntelligenceDB(db_path)
    enhanced_db.connect()
    enhanced_db.init_v2_schema()

    summary = {}

    for table, columns in TABLES_TO_ENRICH.items():
        for column in columns:
            if not column_exists(enhanced_db, table, column):
                continue

            if args.dry_run:
                summary.setdefault(table, {})[column] = rows_missing(enhanced_db.conn, table, column)
            else:
                updated = backfill_from_interviews(enhanced_db.conn, table, column)
                summary.setdefault(table, {})[column] = updated

    mode = "Plan" if args.dry_run else "Actualización"
    print(f"\n{mode} de migración v2.0 para {db_path}")
    for table, stats in summary.items():
        for column, count in stats.items():
            suffix = "registros pendientes" if args.dry_run else "filas actualizadas"
            print(f"  - {table}.{column}: {count} {suffix}")

    enhanced_db.close()


if __name__ == "__main__":
    main()
