#!/usr/bin/env python3
"""
Backfill PostgreSQL consolidated_entities from SQLite post-consolidation.

This script reads the 17 entity tables from SQLite (after consolidation)
and populates PostgreSQL consolidated_entities table.
"""
import os
import sys
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from psycopg2.extras import Json

# Entity types mapping
ENTITY_TYPES = [
    'pain_points',
    'processes',
    'systems',
    'kpis',
    'automation_candidates',
    'inefficiencies',
    'communication_channels',
    'decision_points',
    'data_flows',
    'temporal_patterns',
    'failure_modes',
    'team_structures',
    'knowledge_gaps',
    'success_patterns',
    'budget_constraints',
    'external_dependencies'
]

def get_entity_type_singular(plural: str) -> str:
    """Convert table name to entity type."""
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
    return mapping.get(plural, plural.rstrip('s'))

def backfill_from_sqlite():
    """Read SQLite entities and populate PostgreSQL."""
    sqlite_path = Path("data/full_intelligence.db")
    pg_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")

    if not sqlite_path.exists():
        print(f"❌ SQLite database not found: {sqlite_path}")
        return

    print("=" * 70)
    print("BACKFILL CONSOLIDATED ENTITIES TO POSTGRESQL")
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

    total_inserted = 0

    print()
    print("🔄 Processing entity tables...")
    print()

    for table_name in ENTITY_TYPES:
        entity_type = get_entity_type_singular(table_name)

        # Get all entities from this table
        cursor = sqlite_conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()

        if not rows:
            print(f"  ⊘ {table_name}: skipped (empty)")
            continue

        print(f"  📦 {table_name}: processing {len(rows)} entities...")

        inserted_count = 0
        for row in rows:
            # Convert row to dict
            entity_dict = dict(row)
            entity_id = entity_dict.get('id')

            # Extract core fields
            name = entity_dict.get('name') or entity_dict.get('type') or entity_dict.get('description', '')
            org_id = entity_dict.get('org_id', 'default')

            # Build payload with all entity data
            payload = {k: v for k, v in entity_dict.items() if k not in ['id']}

            # Calculate source_count and confidence
            # Since consolidation already merged, each remaining entity represents merged sources
            source_count = entity_dict.get('source_count', 1)
            consensus_confidence = entity_dict.get('consensus_confidence', 0.8)

            # Insert into PostgreSQL
            try:
                pg_cursor.execute("""
                    INSERT INTO consolidated_entities (
                        sqlite_entity_id,
                        entity_type,
                        name,
                        org_id,
                        source_count,
                        consensus_confidence,
                        payload,
                        created_at,
                        updated_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (sqlite_entity_id, entity_type) DO UPDATE SET
                        name = EXCLUDED.name,
                        source_count = EXCLUDED.source_count,
                        consensus_confidence = EXCLUDED.consensus_confidence,
                        payload = EXCLUDED.payload,
                        updated_at = EXCLUDED.updated_at
                """, (
                    entity_id,
                    entity_type,
                    name[:500] if name else '',  # Limit name length
                    org_id,
                    source_count,
                    consensus_confidence,
                    Json(payload),
                    datetime.now(),
                    datetime.now()
                ))
                inserted_count += 1
            except Exception as e:
                print(f"    ⚠️  Error inserting entity {entity_id}: {str(e)[:100]}")
                continue

        pg_conn.commit()
        total_inserted += inserted_count
        print(f"    ✅ {inserted_count} entities inserted/updated")

    print()
    print("=" * 70)
    print(f"✅ Backfill complete: {total_inserted} total entities")
    print("=" * 70)
    print()

    # Verify PostgreSQL state
    pg_cursor.execute("SELECT COUNT(*) FROM consolidated_entities")
    pg_count = pg_cursor.fetchone()[0]
    print(f"📊 PostgreSQL consolidated_entities: {pg_count} rows")

    pg_cursor.execute("""
        SELECT entity_type, COUNT(*) as count
        FROM consolidated_entities
        GROUP BY entity_type
        ORDER BY count DESC
    """)

    print()
    print("📋 Breakdown by entity type:")
    for entity_type, count in pg_cursor.fetchall():
        print(f"  {entity_type}: {count}")

    print()
    print("🔗 Next steps:")
    print("  1. Run: python scripts/sync_consolidated_to_neo4j.py")
    print("  2. Access Neo4j Browser: http://localhost:7474")
    print()

    sqlite_conn.close()
    pg_conn.close()

if __name__ == "__main__":
    backfill_from_sqlite()
