#!/usr/bin/env python3
"""
Backfill PostgreSQL consolidated_relationships from SQLite relationships table.

This migrates the 64 relationships discovered during consolidation from SQLite
to PostgreSQL, making them available for Neo4j sync.
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from psycopg2.extras import Json

def get_entity_type_from_table(table_name: str) -> str:
    """Convert plural table name to singular entity type."""
    mapping = {
        'pain_points': 'pain_point',
        'processes': 'process',
        'systems': 'system',
        'kpis': 'kpi',
        'automation_candidates': 'automation_candidate',
        'inefficiencies': 'inefficiency',
        'communication_channels': 'communication_channel',
        'decision_points': 'decision_point',
        'data_flows': 'data_flow',
        'temporal_patterns': 'temporal_pattern',
        'failure_modes': 'failure_mode',
        'team_structures': 'team_structure',
        'knowledge_gaps': 'knowledge_gap',
        'success_patterns': 'success_pattern',
        'budget_constraints': 'budget_constraint',
        'external_dependencies': 'external_dependency'
    }
    return mapping.get(table_name, table_name.rstrip('s'))

def backfill_relationships():
    """Read SQLite relationships and populate PostgreSQL consolidated_relationships."""
    sqlite_path = Path("data/full_intelligence.db")
    pg_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")

    if not sqlite_path.exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        return

    print("=" * 70)
    print("BACKFILL RELATIONSHIPS TO POSTGRESQL")
    print("=" * 70)
    print(f"Source: {sqlite_path}")
    print(f"Target: {pg_url}")
    print()

    # Connect to databases
    sqlite_conn = sqlite3.connect(str(sqlite_path))
    sqlite_conn.row_factory = sqlite3.Row

    try:
        pg_conn = psycopg2.connect(pg_url)
        pg_cursor = pg_conn.cursor()
        print("✅ Connected to PostgreSQL")
    except Exception as e:
        print(f"❌ Failed to connect to PostgreSQL: {e}")
        sqlite_conn.close()
        return

    # Check if relationships table exists in SQLite
    sqlite_cursor = sqlite_conn.cursor()
    sqlite_cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='relationships'
    """)
    if not sqlite_cursor.fetchone():
        print("❌ No 'relationships' table found in SQLite")
        sqlite_conn.close()
        pg_conn.close()
        return

    # Get all relationships from SQLite
    print("\n🔍 Reading relationships from SQLite...")
    sqlite_cursor.execute("""
        SELECT
            id,
            source_entity_id,
            source_entity_type,
            relationship_type,
            target_entity_id,
            target_entity_type,
            strength,
            mentioned_in_interviews,
            created_at,
            updated_at
        FROM relationships
        ORDER BY id
    """)

    sqlite_relationships = sqlite_cursor.fetchall()
    total_relationships = len(sqlite_relationships)

    print(f"   Found {total_relationships} relationships in SQLite")

    if total_relationships == 0:
        print("⚠️  No relationships to backfill")
        sqlite_conn.close()
        pg_conn.close()
        return

    # Show breakdown by relationship type
    type_counts = {}
    for rel in sqlite_relationships:
        rel_type = rel['relationship_type']
        type_counts[rel_type] = type_counts.get(rel_type, 0) + 1

    print("\n📊 Relationship breakdown:")
    for rel_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"   {rel_type}: {count}")

    print("\n🔄 Inserting relationships into PostgreSQL...")
    inserted = 0
    skipped = 0
    errors = 0

    for rel in sqlite_relationships:
        try:
            # Get entity types (convert plural table names to singular)
            source_type = get_entity_type_from_table(rel['source_entity_type'])
            target_type = get_entity_type_from_table(rel['target_entity_type'])

            # Parse mentioned_in_interviews (stored as JSON string)
            interviews_json = rel['mentioned_in_interviews']
            if interviews_json:
                try:
                    interviews = json.loads(interviews_json)
                except:
                    interviews = []
            else:
                interviews = []

            # Build payload with all metadata
            payload = {
                'from_entity_type': source_type,
                'to_entity_type': target_type,
                'mentioned_in_interviews': interviews,
                'source_count': len(interviews) if interviews else 1,
                'created_at': rel['created_at'],
                'updated_at': rel['updated_at']
            }

            # Default org_id (relationships in SQLite don't have org_id)
            org_id = 'comversa'  # Default organization

            # Calculate consensus confidence based on source count
            source_count = len(interviews) if interviews else 1
            consensus_confidence = min(source_count / 3.0, 1.0)  # Scale to 0-1

            # Insert into PostgreSQL
            pg_cursor.execute("""
                INSERT INTO consolidated_relationships (
                    sqlite_relationship_id,
                    relationship_type,
                    from_sqlite_entity_id,
                    to_sqlite_entity_id,
                    org_id,
                    relationship_strength,
                    consensus_confidence,
                    payload
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (relationship_type, from_sqlite_entity_id, to_sqlite_entity_id)
                DO NOTHING
                RETURNING id
            """, (
                rel['id'],
                rel['relationship_type'],
                rel['source_entity_id'],
                rel['target_entity_id'],
                org_id,
                rel['strength'],
                consensus_confidence,
                Json(payload)
            ))

            result = pg_cursor.fetchone()
            if result:
                inserted += 1
                if inserted % 10 == 0:
                    print(f"   Inserted {inserted}/{total_relationships}...")
            else:
                skipped += 1

        except Exception as e:
            errors += 1
            print(f"   ⚠️  Error inserting relationship {rel['id']}: {e}")
            continue

    # Commit transaction
    try:
        pg_conn.commit()
        print(f"\n✅ Transaction committed")
    except Exception as e:
        print(f"\n❌ Failed to commit transaction: {e}")
        pg_conn.rollback()
        sqlite_conn.close()
        pg_conn.close()
        return

    # Final statistics
    print("\n" + "=" * 70)
    print("BACKFILL COMPLETE")
    print("=" * 70)
    print(f"Total relationships in SQLite: {total_relationships}")
    print(f"Successfully inserted: {inserted}")
    print(f"Skipped (duplicates): {skipped}")
    print(f"Errors: {errors}")

    # Verify PostgreSQL count
    pg_cursor.execute("SELECT COUNT(*) FROM consolidated_relationships")
    pg_count = pg_cursor.fetchone()[0]
    print(f"\nPostgreSQL consolidated_relationships count: {pg_count}")

    # Show breakdown by type
    pg_cursor.execute("""
        SELECT relationship_type, COUNT(*) as count
        FROM consolidated_relationships
        GROUP BY relationship_type
        ORDER BY count DESC
    """)
    print("\n📊 PostgreSQL relationship breakdown:")
    for row in pg_cursor.fetchall():
        print(f"   {row[0]}: {row[1]}")

    # Cleanup
    sqlite_conn.close()
    pg_conn.close()

    print("\n✅ Backfill complete! Ready for Neo4j sync.")

if __name__ == "__main__":
    backfill_relationships()
