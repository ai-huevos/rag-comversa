"""
Prueba de integración simplificada para el flujo de consolidación RAG 2.0.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from intelligence_capture.consolidation_sync import ConsolidationSync
from intelligence_capture.ingestion_worker import IngestionWorker, WorkerConfig
from intelligence_capture.monitoring import BacklogThresholds, ConsolidationBacklogMonitor


class StubCursor:
    def __init__(self, fetch_sequences: Optional[List[List[Any]]] = None):
        self.queries: List[Dict[str, Any]] = []
        self.fetch_sequences = fetch_sequences or []
        self._fetch_index = 0
        self.rowcount = 0

    def execute(self, sql: str, params: Optional[Sequence[Any]] = None) -> None:
        self.queries.append({"sql": sql.strip(), "params": params})
        if sql.strip().startswith("UPDATE consolidation_events"):
            self.rowcount = len(params[0]) if params and isinstance(params[0], list) else 1

    def fetchall(self):
        if self._fetch_index < len(self.fetch_sequences):
            result = self.fetch_sequences[self._fetch_index]
            self._fetch_index += 1
            return result
        return []

    def close(self) -> None:
        pass


class StubConnection:
    def __init__(self, cursor: StubCursor):
        self.cursor_obj = cursor
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self) -> StubCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.closed = True


class StubGraphAdapter:
    def __init__(self):
        self.entities: List[List[Dict[str, Any]]] = []
        self.relationships: List[List[Dict[str, Any]]] = []

    def merge_entities(self, payloads: List[Dict[str, Any]]) -> None:
        self.entities.append(payloads)

    def merge_relationships(self, payloads: List[Dict[str, Any]]) -> None:
        self.relationships.append(payloads)

    def close(self) -> None:
        pass


class StubEmbeddingPublisher:
    def __init__(self):
        self.payloads: List[Dict[str, Any]] = []

    def enqueue_entity_embedding(self, payload: Dict[str, Any]) -> None:
        self.payloads.append(payload)


class DummySync:
    def __init__(self, processed: int = 3):
        self.processed = processed
        self.truncated = False
        self.reset_called = False

    def truncate_shadow_tables(self) -> None:
        self.truncated = True

    def reset_events(self) -> None:
        self.reset_called = True

    def sync_pending_events(self, limit: int) -> int:
        return self.processed

    def close(self) -> None:
        pass


def _build_sync(fetch_sequences: Optional[List[List[Any]]] = None, publisher=None) -> tuple[ConsolidationSync, StubCursor, StubGraphAdapter]:
    cursor = StubCursor(fetch_sequences)
    connection = StubConnection(cursor)

    def factory(_dsn: str) -> StubConnection:
        return connection

    sync = ConsolidationSync(
        sqlite_db=None,
        config={"enabled": True, "postgres_dsn": "postgresql://dummy"},
        postgres_connection_factory=factory,
        embedding_publisher=publisher,
    )
    adapter = StubGraphAdapter()
    sync._graph_enabled = True  # type: ignore[attr-defined]
    sync._graph_adapter = adapter  # type: ignore[attr-defined]
    return sync, cursor, adapter


def _build_sqlite_fixture(tmp_path: Path) -> Path:
    db_path = tmp_path / "integration.db"
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
            VALUES ('Pendiente', 0, '2025-01-01T00:00:00')
            """
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def test_rag2_consolidation_flow(tmp_path):
    entity_payload = {
        "sqlite_entity_id": 42,
        "entity_type": "systems",
        "name": "ERP Hotelero",
        "org_id": "los_tajibos",
        "source_count": 5,
        "consensus_confidence": 0.9,
        "document_chunk_ids": ["1111-2222"],
        "raw_entity": {"id": 42, "name": "ERP Hotelero"},
    }
    relationship_payload = {
        "relationship_type": "CAUSES",
        "relationship_id": 99,
        "from_entity_id": 42,
        "to_entity_id": 7,
        "org_id": "los_tajibos",
        "strength": 0.8,
        "consensus_confidence": 0.85,
        "raw_relationship": {"id": 99},
    }
    publisher = StubEmbeddingPublisher()
    event_rows = [[("evt-1", "entity_merge", entity_payload), ("evt-2", "relationship_update", relationship_payload)]]
    sync, cursor, adapter = _build_sync(fetch_sequences=event_rows, publisher=publisher)

    processed = sync.sync_pending_events(limit=10)

    assert processed == 2
    assert any("INSERT INTO consolidated_entities" in q["sql"] for q in cursor.queries)
    assert publisher.payloads and publisher.payloads[0]["sqlite_entity_id"] == 42
    assert adapter.entities and adapter.relationships

    db_path = _build_sqlite_fixture(tmp_path)
    monitor = ConsolidationBacklogMonitor(
        db_path=db_path,
        thresholds=BacklogThresholds(max_entities=1, max_age_days=1),
        report_path=tmp_path / "backlog.json",
    )
    metrics = monitor.collect_metrics()
    assert metrics.total_unconsolidated == 1

    dummy_sync = DummySync(processed=3)
    config = WorkerConfig(
        mode="consolidation",
        consolidation_mode="incremental",
        poll_interval_seconds=1,
        batch_size=10,
        status_file=tmp_path / "status.json",
    )
    worker = IngestionWorker(
        backlog_monitor=monitor,
        consolidation_sync=dummy_sync,
        config=config,
    )
    result = worker.run_once()
    assert result.processed_events == 3
