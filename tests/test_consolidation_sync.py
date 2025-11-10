"""
Tests for ConsolidationSync event emission and syncing.
"""
from typing import Any, Dict, List, Optional

from intelligence_capture.consolidation_sync import ConsolidationSync


class DummyCursor:
    def __init__(self, fetch_sequences: Optional[List[List[Any]]] = None):
        self.queries: List[Dict[str, Any]] = []
        self.fetch_sequences = fetch_sequences or []
        self._fetch_index = 0

    def execute(self, sql: str, params: Optional[tuple] = None) -> None:
        self.queries.append({"sql": sql.strip(), "params": params})

    def fetchall(self):
        if self._fetch_index < len(self.fetch_sequences):
            result = self.fetch_sequences[self._fetch_index]
            self._fetch_index += 1
            return result
        return []

    def close(self) -> None:
        pass


class DummyConnection:
    def __init__(self, cursor: DummyCursor):
        self.cursor_obj = cursor
        self.closed = False
        self.autocommit = False
        self.commit_count = 0
        self.rollback_count = 0

    def cursor(self) -> DummyCursor:
        return self.cursor_obj

    def commit(self) -> None:
        self.commit_count += 1

    def rollback(self) -> None:
        self.rollback_count += 1

    def close(self) -> None:
        self.closed = True


def _build_sync(fetch_sequences: Optional[List[List[Any]]] = None) -> tuple[ConsolidationSync, DummyCursor]:
    cursor = DummyCursor(fetch_sequences)
    connection = DummyConnection(cursor)

    def factory(_dsn: str) -> DummyConnection:
        return connection

    sync = ConsolidationSync(
        sqlite_db=None,
        config={"enabled": True, "postgres_dsn": "postgresql://dummy"},
        postgres_connection_factory=factory,
    )
    return sync, cursor


def test_emit_entity_event_inserts_consolidation_event():
    sync, cursor = _build_sync()

    entity = {
        "id": 99,
        "name": "Retrabajo en facturación",
        "company": "Los Tajibos",
        "source_count": 4,
        "consensus_confidence": 0.91,
        "is_consolidated": 1,
    }

    sync.emit_entity_event("pain_points", entity, interview_id=10)

    assert any("INSERT INTO consolidation_events" in q["sql"] for q in cursor.queries)


def test_sync_pending_events_processes_entity_payload():
    payload = {
        "sqlite_entity_id": 5,
        "entity_type": "systems",
        "name": "ERP Financiero",
        "org_id": "los_tajibos",
        "source_count": 3,
        "consensus_confidence": 0.82,
        "document_chunk_ids": [],
        "raw_entity": {"id": 5, "name": "ERP Financiero"},
    }
    event_rows = [[(1, "entity_merge", payload)]]
    sync, cursor = _build_sync(fetch_sequences=event_rows)

    processed = sync.sync_pending_events(limit=10)

    assert processed == 1
    assert any("INSERT INTO consolidated_entities" in q["sql"] for q in cursor.queries)
    assert any("UPDATE consolidation_events" in q["sql"] for q in cursor.queries)
