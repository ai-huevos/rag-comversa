# ConsolidationSync Architecture (Phase 13 Tasks 41‑42)

> _SQLite = source of truth · PostgreSQL = vector + analytics store · Neo4j = relationship explorer_

## Objetivos

1. Emitir eventos cada vez que el agente de consolidación fusiona entidades, descubre relaciones o patrones.
2. Propagar esas fusiones hacia PostgreSQL (pgvector) y Neo4j sin romper el flujo actual basado en SQLite.
3. Mantener trazabilidad: cada entidad consolidada debe enlazar a los fragmentos de documento (document_chunks) que le dieron origen y conservar metadatos de consenso.

## Componentes

| Componente | Archivo | Rol |
| --- | --- | --- |
| `KnowledgeConsolidationAgent` | `intelligence_capture/consolidation_agent.py` | Detecta duplicados en SQLite y llama a `ConsolidationSync` tras cada merge. |
| `ConsolidationSync` | `intelligence_capture/consolidation_sync.py` | Abstrae la lógica de eventos, escribe en `consolidation_events` y sincroniza con PostgreSQL/Neo4j. |
| Eventos persistentes | `scripts/migrations/2025_01_01_pgvector.sql` | Tablas `consolidation_events`, `consolidated_entities`, `consolidated_relationships`, `consolidated_patterns`. |
| Shadow store Postgres | `consolidated_entities*` | Contiene snapshots consolidados para vector search/reporting. |
| Neo4j builder | `graph/knowledge_graph_builder.py` | Inserta nodos/relaciones con métricas consolidadas. |

## Flujo

```
SQLite (consolidation_agent)
    │
    ├── 1. Entity merge → ConsolidationSync.emit_entity_event()
    │         │
    │         └─ Writes JSON payload to consolidation_events (Postgres)
    │
    ├── 2. Relationship discovery → emit_relationship_event()
    │
    └── 3. Pattern recognition → emit_pattern_event()

Background Sync (ConsolidationSync.sync_pending_events)
    │
    ├── Load events → upsert consolidated_entities / relationships / patterns
    ├── Link to document_chunks via metadata (chunk UUIDs, interview ids)
    ├── Trigger embeddings (later via EmbeddingPipeline) for consolidated payloads
    └── Fan‑out to Neo4j through KnowledgeGraphBuilder
```

### Por qué eventos primero

- SQLite continúa siendo la base operativa. Si Postgres/Neo4j fallan, el merge no se pierde porque queda registrado en `consolidation_events`.
- Permite replays completos (`scripts/sync_graph_consolidation.py`) y conciliaciones nocturnas sin bloquear el procesamiento de entrevistas.

## Contratos de datos

- **Entity payload**
  ```json
  {
    "sqlite_entity_id": 42,
    "entity_type": "pain_points",
    "name": "Retrabajo en facturación",
    "org_id": "los_tajibos",
    "source_count": 5,
    "consensus_confidence": 0.87,
    "document_chunk_ids": ["bd1d...", "f9aa..."],
    "raw_entity": {...},
    "interview_ids": [11, 14]
  }
  ```
- **Relationship payload**
  ```json
  {
    "relationship_type": "CAUSES",
    "from_entity_id": 42,
    "to_entity_id": 77,
    "strength": 0.72,
    "mentioned_in": 4,
    "org_id": "los_tajibos",
    "raw_relationship": {...}
  }
  ```

## Frecuencia & Modo

- **Tiempo real:** `KnowledgeConsolidationAgent` emite eventos inmediatamente (latencia < 1s).
- **Batch incremental:** `ConsolidationSync.sync_pending_events(limit=500)` corre cada 5 minutos desde ingestion worker o cron para poblar Postgres/Neo4j.
- **Full replay:** `scripts/sync_graph_consolidation.py --mode full` limpia tablas shadow y reejecuta todo el historial desde `consolidation_events`.

## Resolución de conflictos

1. **SQLite → Postgres:** `consolidated_entities` usa `UNIQUE (sqlite_entity_id, entity_type)`. Siempre gana la versión más reciente (`updated_at`).
2. **Postgres → Neo4j:** `MERGE` por `org_id + external_id`. Se actualizan métricas (`source_count`, `consensus_confidence`) si ya existen.
3. **Rollback:** marcar `consolidation_events.processed=false` + eliminar shadow rows permite reejecutar cualquier rango temporal.

## Seguridad & Auditoría

- Cada evento guarda `created_at`, `processed`, `error_message`.
- Tabla shadow sirve como bitácora auditable (quién consolidó, cuándo, qué fuentes).
- Enlaces a `document_chunk_ids` preservan trazabilidad al documento original, cumpliendo Ley 164.

## Próximos pasos (Tasks 42‑44)

- **PostgreSQL Sync:** completar `sync_consolidated_entities/relationships/patterns` para poblar las tablas shadow y disparar embeddings.
- **Neo4j Sync:** usar `KnowledgeGraphBuilder` para crear nodos/relaciones con org namespaces y métricas consolidadas.
- **Ingestion Worker:** añadir modo `--consolidation` que orquesta extracción → consolidación → `ConsolidationSync`.

Con esta arquitectura podemos avanzar de manera incremental: primero registrar eventos, luego procesarlos en batch y finalmente habilitar la reproducción total hacia Neo4j.***
