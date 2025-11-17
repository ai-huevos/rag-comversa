#!/usr/bin/env python3
"""
Sync consolidated entities from PostgreSQL to Neo4j knowledge graph.
"""
import argparse
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import psycopg2
from graph.knowledge_graph_builder import KnowledgeGraphBuilder, GraphEntity, GraphRelationship
from scripts import infer_entity_relationships as relationship_inference


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync consolidated entities and inferred relationships to Neo4j.")
    parser.add_argument(
        "--skip-inferred-relationships",
        action="store_true",
        help="Only sync stored relationships; skip property-based inference.",
    )
    parser.add_argument(
        "--inference-limit",
        type=int,
        default=None,
        help="Cap the number of inferred relationships (debugging).",
    )
    parser.add_argument(
        "--inference-dry-run",
        action="store_true",
        help="Preview the inference summary but skip merging those edges.",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL when reading consolidated_entities.",
    )
    return parser.parse_args()


def load_consolidated_entities(pg_cursor):
    pg_cursor.execute("""
        SELECT
            sqlite_entity_id, entity_type, name, org_id,
            source_count, consensus_confidence, payload
        FROM consolidated_entities
        ORDER BY entity_type, name
    """)
    rows = pg_cursor.fetchall()
    entities = []
    for row in rows:
        sqlite_id, entity_type, name, org_id, source_count, confidence, payload_json = row
        if isinstance(payload_json, dict):
            properties = payload_json
        else:
            properties = json.loads(payload_json) if payload_json else {}
        properties["source_count"] = source_count
        properties["consensus_confidence"] = confidence
        entities.append(
            GraphEntity(
                external_id=f"sqlite_{entity_type}_{sqlite_id}",
                entity_type=entity_type,
                name=name,
                org_id=org_id or "unknown",
                properties=properties,
            )
        )
    return entities


def load_stored_relationships(pg_cursor):
    pg_cursor.execute("SELECT COUNT(*) FROM consolidated_relationships")
    total_relationships = pg_cursor.fetchone()[0]
    relationships = []
    if total_relationships == 0:
        return relationships

    pg_cursor.execute("""
        SELECT
            relationship_type, from_sqlite_entity_id, to_sqlite_entity_id,
            org_id, relationship_strength, consensus_confidence, payload
        FROM consolidated_relationships
    """)
    rel_rows = pg_cursor.fetchall()
    for row in rel_rows:
        rel_type, from_id, to_id, org_id, strength, confidence, payload_json = row
        if isinstance(payload_json, dict):
            properties = dict(payload_json)
        else:
            properties = json.loads(payload_json) if payload_json else {}
        properties["relationship_strength"] = strength
        properties["consensus_confidence"] = confidence

        from_entity_type = properties.get("from_entity_type", "unknown")
        to_entity_type = properties.get("to_entity_type", "unknown")

        relationships.append(
            GraphRelationship(
                start_external_id=f"sqlite_{from_entity_type}_{from_id}",
                end_external_id=f"sqlite_{to_entity_type}_{to_id}",
                relationship_type=rel_type,
                org_id=org_id or "unknown",
                properties=properties,
            )
        )
    return relationships


def main():
    args = parse_args()
    pg_url = args.database_url or os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")
    print("📊 Syncing consolidated entities: PostgreSQL → Neo4j")
    print(f"   Source: {pg_url}")
    print()

    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cursor = pg_conn.cursor()
        pg_cursor.execute("SELECT COUNT(*) FROM consolidated_entities")
        total_entities = pg_cursor.fetchone()[0]
        if total_entities == 0:
            print("⊘ No consolidated entities found in PostgreSQL")
            print("   Run consolidation first: python scripts/consolidate_existing_entities.py")
            return

        print(f"Found {total_entities} consolidated entities in PostgreSQL")
        entities = load_consolidated_entities(pg_cursor)
        relationships = load_stored_relationships(pg_cursor)
        pg_conn.close()

        builder = KnowledgeGraphBuilder.from_config()
        try:
            print()
            print(f"Syncing {len(entities)} entities to Neo4j...")
            merged_entities = builder.merge_entities(entities)
            print(f"  ✅ {merged_entities} entities merged")

            merged_relationships = 0
            if relationships:
                print()
                print(f"Syncing {len(relationships)} stored relationships to Neo4j...")
                merged_relationships = builder.merge_relationships(relationships)
                print(f"  ✅ {merged_relationships} stored relationships merged")

            if not args.skip_inferred_relationships:
                print()
                print("🤖 Inferring additional relationships from entity payloads...")
                relationship_inference.run_inference(
                    pg_url=pg_url,
                    dry_run=args.inference_dry_run,
                    limit=args.inference_limit,
                    builder=builder if not args.inference_dry_run else None,
                    verbose=True,
                )
                if args.inference_dry_run:
                    print("   ℹ️ Inference dry-run complete (no writes)")

        finally:
            builder.close()

        print()
        print("✅ Sync complete!")
        print()
        print("📊 Neo4j Summary:")
        print(f"   Entities synced: {merged_entities}")
        if relationships:
            print(f"   Stored relationships synced: {merged_relationships}")

        print()
        print("🔗 Access Neo4j Browser: http://localhost:7474")
        print("   Username: neo4j")
        print("   Password: comversa_neo4j_2025")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
