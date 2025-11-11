"""
Pruebas para el backlog monitor y el worker de consolidación.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from intelligence_capture.ingestion_worker import IngestionWorker, WorkerConfig
from intelligence_capture.monitoring import BacklogThresholds, ConsolidationBacklogMonitor


def _build_sqlite_fixture(tmp_path: Path) -> Path:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE pain_points (
                id INTEGER PRIMARY KEY,
                description TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                is_consolidated INTEGER DEFAULT 0
            )
            """
        )
        conn.execute(
            """
            INSERT INTO pain_points (description, is_consolidated, created_at)
            VALUES
                ('Duplicado 1', 0, '2025-01-01T00:00:00'),
                ('Duplicado 2', 1, '2025-01-02T00:00:00'),
                ('Duplicado 3', 0, '2025-01-03T00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


class DummySync:
    def __init__(self, processed: int = 0):
        self.processed = processed
        self.truncated = False
        self.reset_called = False
        self.closed = False

    def truncate_shadow_tables(self, *_args, **_kwargs) -> None:
        self.truncated = True

    def reset_events(self, *_args, **_kwargs) -> None:
        self.reset_called = True

    def sync_pending_events(self, limit: int) -> int:
        return self.processed

    def close(self) -> None:
        self.closed = True


def test_backlog_monitor_counts_entities(tmp_path):
    db_path = _build_sqlite_fixture(tmp_path)
    monitor = ConsolidationBacklogMonitor(
        db_path=db_path,
        thresholds=BacklogThresholds(max_entities=1, max_age_days=1),
        report_path=tmp_path / "backlog.json",
    )
    metrics = monitor.collect_metrics()
    monitor.persist_report(metrics)

    assert metrics.total_unconsolidated == 2
    assert metrics.oldest_entity_timestamp.startswith("2025-01-01")
    assert (tmp_path / "backlog.json").exists()
    assert monitor.should_alert(metrics) is True


def test_ingestion_worker_run_once_writes_status(tmp_path):
    db_path = _build_sqlite_fixture(tmp_path)
    monitor = ConsolidationBacklogMonitor(
        db_path=db_path,
        thresholds=BacklogThresholds(max_entities=10, max_age_days=30),
        report_path=tmp_path / "backlog.json",
    )
    sync = DummySync(processed=5)
    config = WorkerConfig(
        mode="consolidation",
        consolidation_mode="incremental",
        poll_interval_seconds=1,
        batch_size=50,
        status_file=tmp_path / "status.json",
    )
    worker = IngestionWorker(
        backlog_monitor=monitor,
        consolidation_sync=sync,
        config=config,
    )

    result = worker.run_once()
    worker._write_status(result)  # type: ignore[attr-defined]

    assert result.processed_events == 5
    assert (tmp_path / "status.json").exists()


def test_ingestion_worker_full_mode_triggers_reset(tmp_path):
    db_path = _build_sqlite_fixture(tmp_path)
    monitor = ConsolidationBacklogMonitor(
        db_path=db_path,
        thresholds=BacklogThresholds(),
        report_path=tmp_path / "backlog.json",
    )
    sync = DummySync(processed=0)
    config = WorkerConfig(
        mode="consolidation",
        consolidation_mode="full",
        poll_interval_seconds=1,
        batch_size=10,
        status_file=tmp_path / "status.json",
    )
    worker = IngestionWorker(
        backlog_monitor=monitor,
        consolidation_sync=sync,
        config=config,
    )

    worker.run_once()

    assert sync.truncated is True
    assert sync.reset_called is True
