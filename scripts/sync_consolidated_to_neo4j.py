#!/usr/bin/env python3
"""
Sync consolidated entities from PostgreSQL to Neo4j knowledge graph.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import psycopg2
from graph.knowledge_graph_builder import KnowledgeGraphBuilder, GraphEntity, GraphRelationship

def main():
    # Connect to PostgreSQL
    pg_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")
    print(f"📊 Syncing consolidated entities: PostgreSQL → Neo4j")
    print()

    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cursor = pg_conn.cursor()

        # Get consolidated entities count
        pg_cursor.execute("SELECT COUNT(*) FROM consolidated_entities")
        total_entities = pg_cursor.fetchone()[0]

        if total_entities == 0:
            print("⊘ No consolidated entities found in PostgreSQL")
            print("   Run consolidation first: python scripts/consolidate_existing_entities.py")
            return

        print(f"Found {total_entities} consolidated entities in PostgreSQL")

        # Read all consolidated entities
        pg_cursor.execute("""
            SELECT
                sqlite_entity_id, entity_type, name, org_id,
                source_count, consensus_confidence, payload
            FROM consolidated_entities
            ORDER BY entity_type, name
        """)

        rows = pg_cursor.fetchall()

        # Convert to GraphEntity objects
        entities = []
        for row in rows:
            sqlite_id, entity_type, name, org_id, source_count, confidence, payload_json = row

            # PostgreSQL JSONB is already deserialized by psycopg2
            if isinstance(payload_json, dict):
                properties = payload_json
            else:
                properties = json.loads(payload_json) if payload_json else {}
            properties['source_count'] = source_count
            properties['consensus_confidence'] = confidence

            entities.append(GraphEntity(
                external_id=f"sqlite_{entity_type}_{sqlite_id}",
                entity_type=entity_type,
                name=name,
                org_id=org_id or "unknown",
                properties=properties
            ))

        # Get consolidated relationships
        pg_cursor.execute("SELECT COUNT(*) FROM consolidated_relationships")
        total_relationships = pg_cursor.fetchone()[0]

        relationships = []
        if total_relationships > 0:
            pg_cursor.execute("""
                SELECT
                    relationship_type, from_sqlite_entity_id, to_sqlite_entity_id,
                    org_id, relationship_strength, consensus_confidence, payload
                FROM consolidated_relationships
            """)

            rel_rows = pg_cursor.fetchall()
            for row in rel_rows:
                rel_type, from_id, to_id, org_id, strength, confidence, payload_json = row

                # PostgreSQL JSONB is already deserialized by psycopg2
                if isinstance(payload_json, dict):
                    properties = payload_json
                else:
                    properties = json.loads(payload_json) if payload_json else {}
                properties['relationship_strength'] = strength
                properties['consensus_confidence'] = confidence

                # Get entity types from payload to construct proper external_ids
                from_entity_type = payload_json.get('from_entity_type', 'unknown')
                to_entity_type = payload_json.get('to_entity_type', 'unknown')

                relationships.append(GraphRelationship(
                    start_external_id=f"sqlite_{from_entity_type}_{from_id}",
                    end_external_id=f"sqlite_{to_entity_type}_{to_id}",
                    relationship_type=rel_type,
                    org_id=org_id or "unknown",
                    properties=properties
                ))

        pg_conn.close()

        # Connect to Neo4j and sync
        builder = KnowledgeGraphBuilder.from_config()

        print()
        print(f"Syncing {len(entities)} entities to Neo4j...")
        merged_entities = builder.merge_entities(entities)
        print(f"  ✅ {merged_entities} entities merged")

        if relationships:
            print()
            print(f"Syncing {len(relationships)} relationships to Neo4j...")
            merged_relationships = builder.merge_relationships(relationships)
            print(f"  ✅ {merged_relationships} relationships merged")

        builder.close()

        # Final verification
        print()
        print("✅ Sync complete!")
        print()
        print("📊 Neo4j Summary:")
        print(f"   Entities: {merged_entities}")
        if relationships:
            print(f"   Relationships: {merged_relationships}")

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
