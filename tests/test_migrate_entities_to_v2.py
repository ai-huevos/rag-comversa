from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts import migrate_entities_to_v2 as migration


@pytest.fixture()
def db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute(
        """
        CREATE TABLE interviews (
            id INTEGER PRIMARY KEY,
            business_unit TEXT,
            department TEXT
        )
        """
    )
    yield conn
    conn.close()


def _db_wrapper(conn: sqlite3.Connection):
    return SimpleNamespace(conn=conn)


def test_dry_run_mode_counts_pending_rows(db_connection: sqlite3.Connection) -> None:
    db_connection.execute(
        """
        CREATE TABLE pain_points (
            id INTEGER PRIMARY KEY,
            interview_id INTEGER,
            business_unit TEXT,
            department TEXT
        )
        """
    )
    db_connection.executemany(
        "INSERT INTO interviews (id, business_unit, department) VALUES (?, ?, ?)",
        [(1, "Holding", "Ventas"), (2, "Operaciones", ""), (3, "Holding", "Compras")],
    )
    db_connection.executemany(
        "INSERT INTO pain_points (id, interview_id, business_unit, department) VALUES (?, ?, ?, ?)",
        [
            (1, 1, None, None),
            (2, 2, "", "Logística"),
            (3, 3, "Backoffice", None),
        ],
    )

    summary = migration.generate_migration_summary(_db_wrapper(db_connection), dry_run=True)

    assert summary["pain_points"]["business_unit"] == 2
    assert summary["pain_points"]["department"] == 2


def test_backfill_logic_updates_missing_values(db_connection: sqlite3.Connection) -> None:
    db_connection.execute(
        """
        CREATE TABLE pain_points (
            id INTEGER PRIMARY KEY,
            interview_id INTEGER,
            business_unit TEXT,
            department TEXT
        )
        """
    )
    db_connection.executemany(
        "INSERT INTO interviews (id, business_unit, department) VALUES (?, ?, ?)",
        [(1, "Holding", "Ventas"), (2, "Operaciones", "Logística")],
    )
    db_connection.execute(
        "INSERT INTO pain_points (id, interview_id, business_unit, department) VALUES (?, ?, ?, ?)",
        (1, 1, None, ""),
    )
    db_connection.execute(
        "INSERT INTO pain_points (id, interview_id, business_unit, department) VALUES (?, ?, ?, ?)",
        (2, 2, "Operaciones", None),
    )

    summary = migration.generate_migration_summary(_db_wrapper(db_connection), dry_run=False)
    rows = db_connection.execute(
        "SELECT business_unit, department FROM pain_points ORDER BY id"
    ).fetchall()

    assert rows == [("Holding", "Ventas"), ("Operaciones", "Logística")]
    assert summary["pain_points"]["business_unit"] == 1
    assert summary["pain_points"]["department"] == 2


def test_missing_columns_are_skipped(db_connection: sqlite3.Connection) -> None:
    db_connection.execute(
        """
        CREATE TABLE processes (
            id INTEGER PRIMARY KEY,
            interview_id INTEGER,
            business_unit TEXT
        )
        """
    )
    db_connection.execute(
        "INSERT INTO interviews (id, business_unit, department) VALUES (?, ?, ?)",
        (1, "Holding", "Operaciones"),
    )
    db_connection.execute(
        "INSERT INTO processes (id, interview_id, business_unit) VALUES (?, ?, ?)",
        (1, 1, None),
    )

    summary = migration.generate_migration_summary(_db_wrapper(db_connection), dry_run=True)

    assert "department" not in summary.get("processes", {})


def test_sql_identifier_validation_blocks_malicious_input(db_connection: sqlite3.Connection) -> None:
    db_connection.execute(
        """
        CREATE TABLE pain_points (
            id INTEGER PRIMARY KEY,
            interview_id INTEGER,
            business_unit TEXT,
            department TEXT
        )
        """
    )

    with pytest.raises(ValueError):
        migration.column_exists(_db_wrapper(db_connection), "pain_points; DROP TABLE interviews; --", "business_unit")

    with pytest.raises(ValueError):
        migration.rows_missing(db_connection, "pain_points", "department; DROP")

    with pytest.raises(ValueError):
        migration.backfill_from_interviews(db_connection, "pain_points", "department; DROP")
