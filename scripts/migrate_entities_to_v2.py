#!/usr/bin/env python3
"""Utility script to backfill v2.0 organizational fields on legacy entities."""
from __future__ import annotations

import argparse
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, MutableMapping

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

UNKNOWN_PLACEHOLDER = "Unknown"


def _quote_identifier(identifier: str) -> str:
    """Return an identifier safely quoted for SQLite statements."""
    if not identifier or '"' in identifier or not identifier.replace("_", "").isalnum():
        raise ValueError(f"Identificador inválido: {identifier}")
    return f'"{identifier}"'


def _ensure_valid_table(table: str) -> str:
    if table not in TABLES_TO_ENRICH:
        raise ValueError(f"Tabla no permitida: {table}")
    return table


def _ensure_valid_column(table: str, column: str) -> str:
    allowed_columns = TABLES_TO_ENRICH.get(_ensure_valid_table(table), [])
    if column not in allowed_columns:
        raise ValueError(f"Columna no permitida para {table}: {column}")
    return column


def column_exists(db: EnhancedIntelligenceDB, table: str, column: str) -> bool:
    table_name = _ensure_valid_table(table)
    _ensure_valid_column(table_name, column)

    cursor = db.conn.cursor()
    table_sql = _quote_identifier(table_name)
    cursor.execute(f"PRAGMA table_info({table_sql})")
    return any(row[1] == column for row in cursor.fetchall())


def rows_missing(conn: sqlite3.Connection, table: str, column: str) -> int:
    table_name = _ensure_valid_table(table)
    column_name = _ensure_valid_column(table_name, column)

    cursor = conn.cursor()
    table_sql = _quote_identifier(table_name)
    column_sql = _quote_identifier(column_name)
    cursor.execute(
        f"SELECT COUNT(*) FROM {table_sql} WHERE {column_sql} IS NULL OR TRIM({column_sql}) = ''"
    )
    result = cursor.fetchone()
    return int(result[0]) if result else 0


def backfill_from_interviews(conn: sqlite3.Connection, table: str, column: str) -> int:
    table_name = _ensure_valid_table(table)
    column_name = _ensure_valid_column(table_name, column)

    cursor = conn.cursor()
    table_sql = _quote_identifier(table_name)
    column_sql = _quote_identifier(column_name)
    cursor.execute(
        f"""
        UPDATE {table_sql} AS target
        SET {column_sql} = (
            SELECT COALESCE(i.{column_sql}, ?)
            FROM interviews i
            WHERE i.id = target.interview_id
        )
        WHERE ({column_sql} IS NULL OR TRIM({column_sql}) = '')
          AND EXISTS (
            SELECT 1 FROM interviews i WHERE i.id = target.interview_id
          )
        """,
        (UNKNOWN_PLACEHOLDER,),
    )
    conn.commit()
    return cursor.rowcount


def generate_migration_summary(
    enhanced_db: EnhancedIntelligenceDB, dry_run: bool
) -> Dict[str, Dict[str, int]]:
    summary: Dict[str, Dict[str, int]] = defaultdict(dict)

    for table, columns in TABLES_TO_ENRICH.items():
        for column in columns:
            if not column_exists(enhanced_db, table, column):
                continue

            if dry_run:
                summary[table][column] = rows_missing(enhanced_db.conn, table, column)
            else:
                summary[table][column] = backfill_from_interviews(enhanced_db.conn, table, column)

    return {table: dict(columns) for table, columns in summary.items()}


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


def _render_summary(summary: MutableMapping[str, Dict[str, int]], dry_run: bool, db_path: Path) -> None:
    if dry_run:
        print(f"\n🔍 DRY RUN - Análisis de migración v2.0 para {db_path}")
    else:
        print(f"\n⚙️  Migración v2.0 en curso para {db_path}")

    if not summary:
        print("  - No se encontraron columnas para actualizar.")
        return

    for table, stats in summary.items():
        for column, count in stats.items():
            suffix = "registros serían actualizados" if dry_run else "filas actualizadas"
            print(f"  - {table}.{column}: {count} {suffix}")

    if dry_run:
        print("\nPara ejecutar: python scripts/migrate_entities_to_v2.py (sin --dry-run)")


def main() -> None:
    args = parse_args()
    db_path: Path = args.db

    enhanced_db = EnhancedIntelligenceDB(db_path)
    enhanced_db.connect()
    enhanced_db.init_v2_schema()

    try:
        summary = generate_migration_summary(enhanced_db, args.dry_run)
        _render_summary(summary, args.dry_run, db_path)
    finally:
        enhanced_db.close()


if __name__ == "__main__":
    main()
