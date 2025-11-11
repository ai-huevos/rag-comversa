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


class DummyGraphAdapter:
    def __init__(self):
        self.entities: List[List[Dict[str, Any]]] = []
        self.relationships: List[List[Dict[str, Any]]] = []

    def merge_entities(self, payloads: List[Dict[str, Any]]) -> None:
        self.entities.append(payloads)

    def merge_relationships(self, payloads: List[Dict[str, Any]]) -> None:
        self.relationships.append(payloads)

    def close(self) -> None:
        pass


class DummyEmbeddingPublisher:
    def __init__(self):
        self.payloads: List[Dict[str, Any]] = []

    def enqueue_entity_embedding(self, payload: Dict[str, Any]) -> None:
        self.payloads.append(payload)


def _build_sync(
    fetch_sequences: Optional[List[List[Any]]] = None,
    *,
    config_overrides: Optional[Dict[str, Any]] = None,
    embedding_publisher: Optional[DummyEmbeddingPublisher] = None,
) -> tuple[ConsolidationSync, DummyCursor]:
    cursor = DummyCursor(fetch_sequences)
    connection = DummyConnection(cursor)

    def factory(_dsn: str) -> DummyConnection:
        return connection

    base_config = {"enabled": True, "postgres_dsn": "postgresql://dummy"}
    if config_overrides:
        base_config.update(config_overrides)

    sync = ConsolidationSync(
        sqlite_db=None,
        config=base_config,
        postgres_connection_factory=factory,
        embedding_publisher=embedding_publisher,
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


def test_sync_pending_events_flushes_graph_payloads():
    payload_entity = {
        "sqlite_entity_id": 5,
        "entity_type": "systems",
        "name": "ERP Financiero",
        "org_id": "los_tajibos",
        "source_count": 3,
        "consensus_confidence": 0.82,
        "document_chunk_ids": [],
        "raw_entity": {"id": 5, "name": "ERP Financiero"},
    }
    payload_relationship = {
        "relationship_type": "CAUSES",
        "relationship_id": 9,
        "from_entity_id": 5,
        "to_entity_id": 7,
        "org_id": "los_tajibos",
        "strength": 0.71,
        "consensus_confidence": 0.8,
        "raw_relationship": {"id": 9},
    }
    event_rows = [[(1, "entity_merge", payload_entity), (2, "relationship_update", payload_relationship)]]
    sync, cursor = _build_sync(fetch_sequences=event_rows)
    sync._graph_enabled = True
    adapter = DummyGraphAdapter()
    sync._graph_adapter = adapter

    processed = sync.sync_pending_events(limit=10)

    assert processed == 2
    assert adapter.entities
    assert adapter.entities[0][0]["external_id"] == "5"
    assert adapter.relationships
    assert adapter.relationships[0][0]["relationship_type"] == "CAUSES"


def test_entity_embedding_publisher_called_during_sync():
    publisher = DummyEmbeddingPublisher()
    event_rows = [
        [
            (
                1,
                "entity_merge",
                {
                    "sqlite_entity_id": 99,
                    "entity_type": "pain_points",
                    "name": "Retrabajo en facturación",
                    "org_id": "los_tajibos",
                    "source_count": 4,
                    "consensus_confidence": 0.91,
                    "document_chunk_ids": [],
                    "raw_entity": {"id": 99},
                },
            )
        ]
    ]
    sync, _ = _build_sync(fetch_sequences=event_rows, embedding_publisher=publisher)
    sync.sync_pending_events()

    assert publisher.payloads
    assert publisher.payloads[0]["sqlite_entity_id"] == 99


def test_reset_events_and_truncate_tables_execute_expected_sql():
    sync, cursor = _build_sync()

    updated = sync.reset_events(event_ids=["a", "b"])
    assert any("UPDATE consolidation_events" in q["sql"] and "WHERE id = ANY" in q["sql"] for q in cursor.queries)
    assert updated == 0  # Dummy cursor no conoce rowcount

    cursor.queries.clear()
    sync.truncate_shadow_tables(["consolidated_entities", "unknown"])
    assert any("TRUNCATE TABLE consolidated_entities" in q["sql"] for q in cursor.queries)
