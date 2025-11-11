#!/usr/bin/env python3
"""
CLI operativo para sincronizar eventos de consolidación hacia PostgreSQL y Neo4j.

Modos disponibles:
- incremental: procesa eventos pendientes hasta agotar el backlog.
- full: reinicia tablas shadow y reprocesa todo el historial.
- rollback: revierte los últimos eventos procesados y los marca para reejecución.
- dry-run: solo muestra el estado actual sin ejecutar cambios.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("OPENAI_API_KEY", "local-sync-placeholder")

from intelligence_capture.config import load_consolidation_config  # noqa: E402
from intelligence_capture.consolidation_sync import ConsolidationSync  # noqa: E402
from intelligence_capture.logger import get_logger  # noqa: E402

logger = get_logger("sync_graph_consolidation")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sincroniza ConsolidationSync con Postgres/Neo4j.")
    parser.add_argument(
        "--mode",
        choices=["incremental", "full", "rollback", "dry-run"],
        default="incremental",
        help="Modo de ejecución del sincronizador (default: incremental).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Cantidad de eventos por lote al procesar (default: 250).",
    )
    parser.add_argument(
        "--postgres-dsn",
        type=str,
        help="DSN explícito para PostgreSQL. Sobrescribe config/database.toml.",
    )
    parser.add_argument(
        "--neo4j-config",
        type=str,
        help="Ruta opcional a config/database.toml alterno para Neo4j.",
    )
    parser.add_argument(
        "--graph-batch-size",
        type=int,
        help="Tamaño de lote para merges en Neo4j.",
    )
    parser.add_argument(
        "--rollback-count",
        type=int,
        default=25,
        help="Cantidad de eventos a revertir cuando mode=rollback (default: 25).",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        help="Ruta para guardar el resumen en formato JSON.",
    )
    return parser.parse_args()


def build_sync(args: argparse.Namespace) -> ConsolidationSync:
    config = load_consolidation_config()
    sync_config = dict(config.get("consolidation_sync", {}))
    sync_config.setdefault("enabled", True)

    if args.postgres_dsn:
        sync_config["postgres_dsn"] = args.postgres_dsn
    if args.neo4j_config:
        sync_config["neo4j_enabled"] = True
        sync_config["neo4j_config_path"] = args.neo4j_config
    if args.graph_batch_size:
        sync_config["graph_batch_size"] = args.graph_batch_size

    logger.info("ConsolidationSync config: %s", json.dumps(sync_config, ensure_ascii=False))
    return ConsolidationSync(sqlite_db=None, config=sync_config)


def drain_pending_events(sync: ConsolidationSync, batch_size: int) -> int:
    total_processed = 0
    while True:
        processed = sync.sync_pending_events(limit=batch_size)
        if processed == 0:
            break
        total_processed += processed
    return total_processed


def run_full(sync: ConsolidationSync, batch_size: int) -> Dict[str, Any]:
    sync.truncate_shadow_tables()
    sync.reset_events()
    processed = drain_pending_events(sync, batch_size)
    return {"processed_events": processed, "mode": "full", "status": "completed"}


def run_incremental(sync: ConsolidationSync, batch_size: int) -> Dict[str, Any]:
    processed = drain_pending_events(sync, batch_size)
    return {"processed_events": processed, "mode": "incremental", "status": "completed"}


def run_dry_run(sync: ConsolidationSync) -> Dict[str, Any]:
    conn = sync.get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT COUNT(*) AS pending,
                   MIN(created_at) AS oldest
              FROM consolidation_events
             WHERE processed = false
            """
        )
        pending_count, oldest = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) FROM consolidated_entities")
        entity_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM consolidated_relationships")
        relationship_count = cursor.fetchone()[0]

        summary = {
            "mode": "dry-run",
            "pending_events": int(pending_count or 0),
            "oldest_event": oldest.isoformat() if isinstance(oldest, datetime) else None,
            "shadow_entities": int(entity_count),
            "shadow_relationships": int(relationship_count),
        }
        return summary
    finally:
        cursor.close()


def run_rollback(sync: ConsolidationSync, rollback_count: int) -> Dict[str, Any]:
    if rollback_count <= 0:
        raise ValueError("rollback-count debe ser mayor que cero.")

    conn = sync.get_postgres_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT id, event_type, payload
              FROM consolidation_events
             WHERE processed = true
             ORDER BY processed_at DESC NULLS LAST
             LIMIT %s
            """,
            (rollback_count,),
        )
        rows = cursor.fetchall()
        affected_ids: List[str] = []

        for event_id, event_type, payload in rows:
            if event_type == "entity_merge":
                cursor.execute(
                    """
                    DELETE FROM consolidated_entities
                     WHERE sqlite_entity_id = %s
                       AND entity_type = %s
                    """,
                    (payload.get("sqlite_entity_id"), payload.get("entity_type")),
                )
            elif event_type == "relationship_update":
                cursor.execute(
                    """
                    DELETE FROM consolidated_relationships
                     WHERE relationship_type = %s
                       AND from_sqlite_entity_id = %s
                       AND to_sqlite_entity_id = %s
                    """,
                    (
                        payload.get("relationship_type"),
                        payload.get("from_entity_id"),
                        payload.get("to_entity_id"),
                    ),
                )
            elif event_type == "pattern_update":
                cursor.execute(
                    """
                    DELETE FROM consolidated_patterns
                     WHERE sqlite_pattern_id = %s
                        OR description = %s
                    """,
                    (payload.get("pattern_id"), payload.get("description")),
                )
            affected_ids.append(str(event_id))

        conn.commit()
        if affected_ids:
            sync.reset_events(event_ids=affected_ids)
        return {
            "mode": "rollback",
            "status": "completed",
            "rolled_back_events": len(affected_ids),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()


def persist_summary(summary: Dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, ensure_ascii=False)


def main() -> None:
    args = parse_args()
    sync = build_sync(args)

    try:
        if args.mode == "dry-run":
            summary = run_dry_run(sync)
        elif args.mode == "full":
            summary = run_full(sync, args.batch_size)
        elif args.mode == "rollback":
            summary = run_rollback(sync, args.rollback_count)
        else:
            summary = run_incremental(sync, args.batch_size)

        print(json.dumps(summary, indent=2, ensure_ascii=False))
        if args.output_json:
            persist_summary(summary, Path(args.output_json))
    finally:
        sync.close()


if __name__ == "__main__":
    main()
