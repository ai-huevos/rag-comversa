"""
ConsolidationSync: conecta las fusiones de SQLite con PostgreSQL y Neo4j.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Protocol

try:  # pragma: no cover - dependencia externa
    import psycopg2
    from psycopg2.extras import Json
except ImportError:  # pragma: no cover - entornos sin psycopg2 (tests rápidos)
    psycopg2 = None  # type: ignore

    class Json:  # type: ignore
        def __init__(self, value: Any):
            self.value = value

from intelligence_capture.database import load_postgres_config
from intelligence_capture.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsolidationSyncConfig:
    """
    Configuración básica para ConsolidationSync.
    """

    enabled: bool = False
    batch_size: int = 250
    default_org_id: Optional[str] = None
    postgres_dsn: Optional[str] = None
    neo4j_enabled: bool = False
    neo4j_config_path: Optional[str] = None
    graph_batch_size: int = 100


@dataclass
class ConsolidationEvent:
    """
    Evento serializado para la tabla consolidation_events.
    """

    event_type: str
    entity_type: str
    entity_id: int
    payload: Dict[str, Any]


@dataclass
class GraphFanoutResult:
    """
    Resultado parcial de fan-out hacia Neo4j.
    """

    entities: List[Dict[str, Any]] = field(default_factory=list)
    relationships: List[Dict[str, Any]] = field(default_factory=list)


class EmbeddingPublisherProtocol(Protocol):
    """
    Contrato mínimo para productores de embeddings de entidades consolidadas.
    """

    def enqueue_entity_embedding(self, payload: Dict[str, Any]) -> None:
        """
        Recibe el payload de una entidad consolidada para generar embeddings en background.
        """


class GraphSyncAdapter:
    """
    Adaptador ligero que delega en KnowledgeGraphBuilder (u objeto compatible).
    """

    def __init__(self, builder: Any):
        self._builder = builder

    def merge_entities(self, payloads: Sequence[Dict[str, Any]]) -> None:
        if not payloads:
            return
        try:
            from graph.knowledge_graph_builder import GraphEntity  # type: ignore

            entities = [
                GraphEntity(
                    external_id=item["external_id"],
                    entity_type=item["entity_type"],
                    name=item["name"],
                    org_id=item["org_id"],
                    properties=item["properties"],
                )
                for item in payloads
            ]
            self._builder.merge_entities(entities)
        except ImportError:
            # Entorno sin dependencias de Neo4j (tests); delega payload crudo.
            self._builder.merge_entities(payloads)

    def merge_relationships(self, payloads: Sequence[Dict[str, Any]]) -> None:
        if not payloads:
            return
        try:
            from graph.knowledge_graph_builder import GraphRelationship  # type: ignore

            relationships = [
                GraphRelationship(
                    start_external_id=item["start_external_id"],
                    end_external_id=item["end_external_id"],
                    relationship_type=item["relationship_type"],
                    org_id=item["org_id"],
                    properties=item["properties"],
                )
                for item in payloads
            ]
            self._builder.merge_relationships(relationships)
        except ImportError:
            self._builder.merge_relationships(payloads)

    def close(self) -> None:
        close_method = getattr(self._builder, "close", None)
        if callable(close_method):
            close_method()


class ConsolidationSyncError(RuntimeError):
    """Error genérico del subsistema ConsolidationSync."""


class ConsolidationSync:
    """
    Maneja la replicación de entidades consolidadas hacia Postgres y Neo4j.
    """

    def __init__(
        self,
        sqlite_db: Any,
        config: Optional[Dict[str, Any]] = None,
        postgres_connection_factory=None,
        neo4j_builder: Optional[Any] = None,
        embedding_publisher: Optional[EmbeddingPublisherProtocol] = None,
    ) -> None:
        self.sqlite_db = sqlite_db
        self.config = self._load_config(config)
        if postgres_connection_factory:
            self._postgres_factory = postgres_connection_factory
        else:
            if psycopg2 is None:
                raise ConsolidationSyncError(
                    "psycopg2 no está instalado. Ejecuta `pip install psycopg2-binary` "
                    "o provee un postgres_connection_factory personalizado."
                )
            self._postgres_factory = lambda dsn: psycopg2.connect(dsn)
        self._pg_conn = None
        self.embedding_publisher = embedding_publisher
        self._neo4j_builder = neo4j_builder
        self._graph_adapter = GraphSyncAdapter(neo4j_builder) if neo4j_builder else None
        self._graph_enabled = bool(neo4j_builder) or self.config.neo4j_enabled

    @staticmethod
    def _load_config(config: Optional[Dict[str, Any]]) -> ConsolidationSyncConfig:
        if not config:
            return ConsolidationSyncConfig()
        return ConsolidationSyncConfig(
            enabled=config.get("enabled", False),
            batch_size=config.get("batch_size", 250),
            default_org_id=config.get("default_org_id"),
            postgres_dsn=config.get("postgres_dsn"),
            neo4j_enabled=config.get("neo4j_enabled", False),
            neo4j_config_path=config.get("neo4j_config_path"),
            graph_batch_size=config.get("graph_batch_size", 100),
        )

    def _ensure_pg_conn(self):
        """Obtiene o crea la conexión Postgres."""
        if self._pg_conn and getattr(self._pg_conn, "closed", True) is False:
            return self._pg_conn

        dsn = self.config.postgres_dsn
        if not dsn:
            pg_conf = load_postgres_config()
            dsn = pg_conf.writer_dsn
        try:
            self._pg_conn = self._postgres_factory(dsn)
            self._pg_conn.autocommit = False
            return self._pg_conn
        except Exception as exc:  # pragma: no cover - depende del entorno
            raise ConsolidationSyncError(f"No se pudo conectar a PostgreSQL: {exc}") from exc

    def close(self) -> None:
        """Cierra la conexión Postgres si existe."""
        if self._pg_conn and getattr(self._pg_conn, "closed", True) is False:
            self._pg_conn.close()
            self._pg_conn = None
        if self._graph_adapter:
            self._graph_adapter.close()
            self._graph_adapter = None
            self._neo4j_builder = None

    # ------------------------------------------------------------------
    # Emisión de eventos
    # ------------------------------------------------------------------

    def emit_entity_event(
        self,
        entity_type: str,
        entity: Dict[str, Any],
        interview_id: Optional[int] = None,
        document_chunk_ids: Optional[Sequence[str]] = None,
    ) -> None:
        """
        Registra un merge de entidad consolidada.
        """
        if not self.config.enabled:
            return

        payload = {
            "sqlite_entity_id": entity.get("id"),
            "entity_type": entity_type,
            "interview_id": interview_id,
            "name": entity.get("name") or entity.get("description"),
            "org_id": self._resolve_org_id(entity),
            "source_count": entity.get("source_count"),
            "consensus_confidence": entity.get("consensus_confidence"),
            "document_chunk_ids": list(document_chunk_ids or []),
            "raw_entity": entity,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._enqueue_event(
            ConsolidationEvent(
                event_type="entity_merge",
                entity_type=entity_type,
                entity_id=entity.get("id") or 0,
                payload=payload,
            )
        )

    def emit_relationship_event(
        self,
        relationship: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> None:
        """
        Registra una relación consolidada.
        """
        if not self.config.enabled:
            return

        payload = {
            "relationship_type": relationship.get("type"),
            "relationship_id": relationship.get("id"),
            "from_entity_id": relationship.get("source_id"),
            "to_entity_id": relationship.get("target_id"),
            "strength": relationship.get("strength"),
            "consensus_confidence": relationship.get("consensus_confidence"),
            "org_id": org_id or self._resolve_org_id(relationship),
            "raw_relationship": relationship,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._enqueue_event(
            ConsolidationEvent(
                event_type="relationship_update",
                entity_type="relationship",
                entity_id=relationship.get("id") or 0,
                payload=payload,
            )
        )

    def emit_pattern_event(
        self,
        pattern: Dict[str, Any],
        org_id: Optional[str] = None,
    ) -> None:
        """
        Registra un patrón consolidado.
        """
        if not self.config.enabled:
            return

        payload = {
            "pattern_type": pattern.get("pattern_type"),
            "pattern_id": pattern.get("id"),
            "description": pattern.get("description"),
            "support_count": pattern.get("support_count"),
            "org_id": org_id or self._resolve_org_id(pattern),
            "raw_pattern": pattern,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._enqueue_event(
            ConsolidationEvent(
                event_type="pattern_update",
                entity_type="pattern",
                entity_id=pattern.get("id") or 0,
                payload=payload,
            )
        )

    def _enqueue_event(self, event: ConsolidationEvent) -> None:
        """Inserta un evento en Postgres."""
        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO consolidation_events (
                    event_type,
                    entity_type,
                    entity_id,
                    payload
                ) VALUES (%s, %s, %s, %s::jsonb)
                """,
                (
                    event.event_type,
                    event.entity_type,
                    event.entity_id,
                    json.dumps(event.payload, ensure_ascii=False),
                ),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            logger.error("No se pudo registrar evento de consolidación: %s", exc, exc_info=True)
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # Procesamiento de eventos -> Postgres
    # ------------------------------------------------------------------

    def sync_pending_events(self, limit: Optional[int] = None) -> int:
        """
        Procesa eventos pendientes y los replica en las tablas shadow.
        """
        if not self.config.enabled:
            return 0

        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        processed = 0
        limit = limit or self.config.batch_size
        graph_entities: List[Dict[str, Any]] = []
        graph_relationships: List[Dict[str, Any]] = []

        try:
            cursor.execute(
                """
                SELECT id, event_type, payload
                  FROM consolidation_events
                 WHERE processed = false
                 ORDER BY created_at ASC
                 LIMIT %s
                """,
                (limit,),
            )
            events = cursor.fetchall()

            for event_id, event_type, payload in events:
                try:
                    graph_result = self._dispatch_event(event_type, payload)
                    if self._graph_enabled and graph_result.entities:
                        graph_entities.extend(graph_result.entities)
                    if self._graph_enabled and graph_result.relationships:
                        graph_relationships.extend(graph_result.relationships)
                    cursor.execute(
                        """
                        UPDATE consolidation_events
                           SET processed = true,
                               processed_at = NOW(),
                               error_message = NULL
                         WHERE id = %s
                        """,
                        (event_id,),
                    )
                    processed += 1
                except Exception as exc:  # pragma: no cover - errores reales
                    logger.error("Error al procesar evento %s: %s", event_id, exc, exc_info=True)
                    cursor.execute(
                        """
                        UPDATE consolidation_events
                           SET error_message = %s
                         WHERE id = %s
                        """,
                        (str(exc), event_id),
                    )
            if self._graph_enabled:
                self._flush_graph_updates(graph_entities, graph_relationships)
            conn.commit()
            return processed
        except Exception as exc:
            conn.rollback()
            logger.error("sync_pending_events falló: %s", exc, exc_info=True)
            raise
        finally:
            cursor.close()

    def _dispatch_event(self, event_type: str, payload: Dict[str, Any]) -> GraphFanoutResult:
        result = GraphFanoutResult()
        if event_type == "entity_merge":
            self._upsert_consolidated_entity(payload)
            self._maybe_enqueue_embedding(payload)
            if self._graph_enabled:
                entity_node = self._build_graph_entity_payload(payload)
                if entity_node:
                    result.entities.append(entity_node)
        elif event_type == "relationship_update":
            self._upsert_consolidated_relationship(payload)
            if self._graph_enabled:
                relationship = self._build_graph_relationship_payload(payload)
                if relationship:
                    result.relationships.append(relationship)
        elif event_type == "pattern_update":
            self._upsert_consolidated_pattern(payload)
        else:
            raise ConsolidationSyncError(f"Evento no soportado: {event_type}")
        return result

    def _upsert_consolidated_entity(self, payload: Dict[str, Any]) -> None:
        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO consolidated_entities (
                    sqlite_entity_id,
                    entity_type,
                    name,
                    org_id,
                    source_count,
                    consensus_confidence,
                    payload,
                    related_chunk_ids,
                    last_synced_at
                )
                VALUES (%(sqlite_entity_id)s, %(entity_type)s, %(name)s, %(org_id)s,
                        %(source_count)s, %(consensus_confidence)s,
                        %(payload_json)s, %(related_chunk_ids)s::uuid[],
                        NOW())
                ON CONFLICT (sqlite_entity_id, entity_type)
                DO UPDATE SET
                    name = EXCLUDED.name,
                    org_id = EXCLUDED.org_id,
                    source_count = EXCLUDED.source_count,
                    consensus_confidence = EXCLUDED.consensus_confidence,
                    payload = EXCLUDED.payload,
                    related_chunk_ids = EXCLUDED.related_chunk_ids,
                    last_synced_at = NOW()
                """,
                {
                    "sqlite_entity_id": payload.get("sqlite_entity_id"),
                    "entity_type": payload.get("entity_type"),
                    "name": payload.get("name"),
                    "org_id": payload.get("org_id"),
                    "source_count": payload.get("source_count"),
                    "consensus_confidence": payload.get("consensus_confidence"),
                    "payload_json": Json(payload.get("raw_entity", {})),
                    "related_chunk_ids": self._format_uuid_array(payload.get("document_chunk_ids")),
                },
            )
        finally:
            cursor.close()

    def _upsert_consolidated_relationship(self, payload: Dict[str, Any]) -> None:
        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO consolidated_relationships (
                    sqlite_relationship_id,
                    relationship_type,
                    from_sqlite_entity_id,
                    to_sqlite_entity_id,
                    org_id,
                    relationship_strength,
                    consensus_confidence,
                    payload,
                    last_synced_at
                )
                VALUES (%(rel_id)s, %(relationship_type)s, %(from_id)s, %(to_id)s,
                        %(org_id)s, %(strength)s, %(confidence)s,
                        %(payload_json)s, NOW())
                ON CONFLICT (relationship_type, from_sqlite_entity_id, to_sqlite_entity_id)
                DO UPDATE SET
                    org_id = EXCLUDED.org_id,
                    relationship_strength = EXCLUDED.relationship_strength,
                    consensus_confidence = EXCLUDED.consensus_confidence,
                    payload = EXCLUDED.payload,
                    last_synced_at = NOW()
                """,
                {
                    "rel_id": payload.get("relationship_id"),
                    "relationship_type": payload.get("relationship_type"),
                    "from_id": payload.get("from_entity_id"),
                    "to_id": payload.get("to_entity_id"),
                    "org_id": payload.get("org_id"),
                    "strength": payload.get("strength"),
                    "confidence": payload.get("consensus_confidence"),
                    "payload_json": Json(payload.get("raw_relationship", {})),
                },
            )
        finally:
            cursor.close()

    def _upsert_consolidated_pattern(self, payload: Dict[str, Any]) -> None:
        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO consolidated_patterns (
                    sqlite_pattern_id,
                    pattern_type,
                    description,
                    org_id,
                    support_count,
                    payload,
                    last_synced_at
                )
                VALUES (%(pattern_id)s, %(pattern_type)s, %(description)s,
                        %(org_id)s, %(support_count)s,
                        %(payload_json)s, NOW())
                ON CONFLICT (pattern_type, description)
                DO UPDATE SET
                    org_id = EXCLUDED.org_id,
                    support_count = EXCLUDED.support_count,
                    payload = EXCLUDED.payload,
                    last_synced_at = NOW()
                """,
                {
                    "pattern_id": payload.get("pattern_id"),
                    "pattern_type": payload.get("pattern_type"),
                    "description": payload.get("description"),
                    "org_id": payload.get("org_id"),
                    "support_count": payload.get("support_count"),
                    "payload_json": Json(payload.get("raw_pattern", {})),
                },
            )
        finally:
            cursor.close()

    # ------------------------------------------------------------------
    # Fan-out helpers
    # ------------------------------------------------------------------

    def _maybe_enqueue_embedding(self, payload: Dict[str, Any]) -> None:
        if not self.embedding_publisher:
            return
        try:
            self.embedding_publisher.enqueue_entity_embedding(payload)
        except Exception as exc:  # pragma: no cover - depende del handler
            logger.error(
                "No se pudo encolar embedding para entidad %s: %s",
                payload.get("sqlite_entity_id"),
                exc,
                exc_info=True,
            )
            raise

    def _build_graph_entity_payload(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        sqlite_id = payload.get("sqlite_entity_id")
        org_id = payload.get("org_id")
        name = payload.get("name")
        entity_type = payload.get("entity_type")
        if not all([sqlite_id, org_id, name, entity_type]):
            return None

        normalized_org_id = self._normalize_org_id(str(org_id))
        properties = {
            "source_count": payload.get("source_count"),
            "consensus_confidence": payload.get("consensus_confidence"),
            "document_chunk_ids": payload.get("document_chunk_ids") or [],
            "raw_entity": payload.get("raw_entity") or {},
            "synced_at": datetime.utcnow().isoformat(),
        }
        return {
            "external_id": str(sqlite_id),
            "entity_type": entity_type,
            "name": name,
            "org_id": normalized_org_id,
            "properties": properties,
        }

    def _build_graph_relationship_payload(
        self, payload: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        rel_type = payload.get("relationship_type")
        org_id = payload.get("org_id")
        from_id = payload.get("from_entity_id")
        to_id = payload.get("to_entity_id")
        if not all([rel_type, org_id, from_id, to_id]):
            return None

        normalized_org_id = self._normalize_org_id(str(org_id))
        properties = {
            "strength": payload.get("strength"),
            "consensus_confidence": payload.get("consensus_confidence"),
            "raw_relationship": payload.get("raw_relationship") or {},
            "synced_at": datetime.utcnow().isoformat(),
        }

        return {
            "relationship_type": rel_type,
            "org_id": normalized_org_id,
            "start_external_id": str(from_id),
            "end_external_id": str(to_id),
            "properties": properties,
        }

    def _flush_graph_updates(
        self,
        entity_payloads: Sequence[Dict[str, Any]],
        relationship_payloads: Sequence[Dict[str, Any]],
    ) -> None:
        adapter = self._ensure_graph_adapter()
        if not adapter:
            return

        batch_size = max(1, self.config.graph_batch_size or 1)
        for batch in self._chunk_sequence(entity_payloads, batch_size):
            adapter.merge_entities(batch)
        for batch in self._chunk_sequence(relationship_payloads, batch_size):
            adapter.merge_relationships(batch)

    def _ensure_graph_adapter(self) -> Optional[GraphSyncAdapter]:
        if not self._graph_enabled:
            return None
        if self._graph_adapter:
            return self._graph_adapter

        builder = self._create_neo4j_builder()
        if not builder:
            return None
        self._neo4j_builder = builder
        self._graph_adapter = GraphSyncAdapter(builder)
        return self._graph_adapter

    def _create_neo4j_builder(self):
        if not self.config.neo4j_enabled:
            return None
        try:
            from graph.knowledge_graph_builder import KnowledgeGraphBuilder, load_neo4j_config  # type: ignore
        except ImportError as exc:  # pragma: no cover - entorno sin neo4j
            raise ConsolidationSyncError(
                "Neo4j builder no disponible. Instala neo4j-driver para habilitar sync."
            ) from exc

        config_path = Path(self.config.neo4j_config_path) if self.config.neo4j_config_path else None
        neo4j_config = load_neo4j_config(config_path)
        builder = KnowledgeGraphBuilder(neo4j_config)
        builder.ensure_constraints()
        return builder

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------

    def get_postgres_connection(self):
        """
        Expone la conexión Postgres para herramientas operativas.
        """
        return self._ensure_pg_conn()

    def reset_events(self, event_ids: Optional[Sequence[str]] = None) -> int:
        """
        Marca eventos como no procesados para replays idempotentes.
        """
        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            if event_ids:
                event_list = [str(event_id) for event_id in event_ids]
                cursor.execute(
                    """
                    UPDATE consolidation_events
                       SET processed = false,
                           processed_at = NULL,
                           error_message = NULL
                     WHERE id = ANY(%s)
                    """,
                    (event_list,),
                )
            else:
                cursor.execute(
                    """
                    UPDATE consolidation_events
                       SET processed = false,
                           processed_at = NULL,
                           error_message = NULL
                    """
                )
            conn.commit()
            return getattr(cursor, "rowcount", 0)
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def truncate_shadow_tables(self, tables: Optional[Sequence[str]] = None) -> None:
        """
        Limpia las tablas shadow para replays completos.
        """
        allowed = {
            "consolidated_entities",
            "consolidated_relationships",
            "consolidated_patterns",
        }
        target_tables = allowed if not tables else set(tables).intersection(allowed)
        if not target_tables:
            return

        conn = self._ensure_pg_conn()
        cursor = conn.cursor()
        try:
            for table in target_tables:
                cursor.execute(f"TRUNCATE TABLE {table}")
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()

    def _resolve_org_id(self, payload: Dict[str, Any]) -> Optional[str]:
        org_from_payload = payload.get("org_id") or payload.get("company")
        if org_from_payload:
            return self._normalize_org_id(str(org_from_payload))
        return self.config.default_org_id

    @staticmethod
    def _normalize_org_id(value: str) -> str:
        return value.strip().lower().replace(" ", "_")

    @staticmethod
    def _format_uuid_array(ids: Optional[Sequence[str]]) -> Optional[List[str]]:
        if not ids:
            return None
        return [str(item) for item in ids]

    @staticmethod
    def _chunk_sequence(
        items: Sequence[Dict[str, Any]],
        chunk_size: int,
    ) -> Iterable[List[Dict[str, Any]]]:
        if chunk_size <= 0:
            chunk_size = 1
        for index in range(0, len(items), chunk_size):
            yield list(items[index : index + chunk_size])


__all__ = ["ConsolidationSync", "ConsolidationSyncConfig", "ConsolidationSyncError"]
