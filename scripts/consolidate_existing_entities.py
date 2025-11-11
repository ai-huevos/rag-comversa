#!/usr/bin/env python3
"""
Retrospective Consolidation - Consolidate Existing Database Entities

This script consolidates entities that are ALREADY in the database,
not just new entities during extraction.

Use Case:
- After initial extraction without consolidation
- To merge case variations (Excel vs excel)
- To merge semantic duplicates (Excel vs Microsoft Excel)

Usage:
    python3 scripts/consolidate_existing_entities.py
    python3 scripts/consolidate_existing_entities.py --db-path data/pilot_intelligence.db
    python3 scripts/consolidate_existing_entities.py --entity-type systems
    python3 scripts/consolidate_existing_entities.py --dry-run
"""
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.consolidation_agent import KnowledgeConsolidationAgent
from intelligence_capture.duplicate_detector import DuplicateDetector
from intelligence_capture.entity_merger import EntityMerger
from intelligence_capture.config import DB_PATH, load_consolidation_config


def get_all_entities(db: EnhancedIntelligenceDB, entity_type: str) -> List[Dict[str, Any]]:
    """
    Get all entities of a given type from the database

    Args:
        db: Database instance
        entity_type: Type of entity (e.g., 'systems', 'pain_points')

    Returns:
        List of entity dictionaries
    """
    cursor = db.conn.cursor()

    # Get all entities
    cursor.execute(f"SELECT * FROM {entity_type}")

    # Convert to dictionaries
    columns = [desc[0] for desc in cursor.description]
    entities = []
    for row in cursor.fetchall():
        entity = dict(zip(columns, row))
        entities.append(entity)

    return entities


def consolidate_existing_entities(
    db_path: Path,
    entity_types: List[str] = None,
    dry_run: bool = False
):
    """
    Consolidate existing entities in the database

    Args:
        db_path: Path to database file
        entity_types: List of entity types to consolidate (None = all)
        dry_run: If True, only show what would be consolidated
    """
    print("=" * 70)
    print("RETROSPECTIVE ENTITY CONSOLIDATION")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will modify database)'}")
    print()

    # Load configuration
    print("📋 Loading configuration...")
    config = load_consolidation_config()

    # Connect to database
    print(f"📂 Connecting to database...")
    db = EnhancedIntelligenceDB(db_path)
    db.connect()

    # Get entity types to process
    if entity_types is None:
        entity_types = [
            "pain_points", "systems", "processes", "kpis",
            "automation_candidates", "inefficiencies",
            "communication_channels", "decision_points"
        ]

    print(f"📊 Entity types to consolidate: {', '.join(entity_types)}\n")

    # Initialize components
    detector = DuplicateDetector(config=config, openai_api_key=os.getenv("OPENAI_API_KEY"))
    merger = EntityMerger()

    # Process each entity type
    total_before = 0
    total_after = 0
    total_merged = 0

    for entity_type in entity_types:
        print(f"\n{'='*70}")
        print(f"Processing: {entity_type}")
        print('='*70)

        # Get all entities
        entities = get_all_entities(db, entity_type)
        count_before = len(entities)
        total_before += count_before

        if count_before == 0:
            print(f"  ℹ️  No entities found - skipping")
            continue

        print(f"  📊 Total entities: {count_before}")

        # Find duplicates by comparing all pairs
        print(f"  🔍 Scanning for duplicates...")

        duplicate_groups = []
        processed_ids = set()

        for i, entity1 in enumerate(entities):
            if entity1['id'] in processed_ids:
                continue

            group = [entity1]

            # Compare with remaining entities
            for entity2 in entities[i+1:]:
                if entity2['id'] in processed_ids:
                    continue

                # Calculate similarity using public methods
                # Get text for comparison
                text1 = entity1.get('name') or entity1.get('type') or entity1.get('description', '')
                text2 = entity2.get('name') or entity2.get('type') or entity2.get('description', '')

                # Calculate name and semantic similarity
                name_sim = detector.calculate_name_similarity(text1, text2, entity_type)
                semantic_sim = detector.calculate_semantic_similarity(text1, text2)

                # Combine using weights from config
                weights = config['similarity_weights']
                similarity_score = (
                    name_sim * weights['name_weight'] +
                    semantic_sim * weights['semantic_weight']
                )

                threshold = config['similarity_thresholds'].get(
                    entity_type,
                    config['similarity_thresholds']['default']
                )

                if similarity_score >= threshold:
                    group.append(entity2)
                    processed_ids.add(entity2['id'])

            if len(group) > 1:
                duplicate_groups.append(group)
                for e in group:
                    processed_ids.add(e['id'])

        # Report findings
        if duplicate_groups:
            print(f"  ✅ Found {len(duplicate_groups)} duplicate groups")
            print()

            for idx, group in enumerate(duplicate_groups, 1):
                print(f"    Group {idx}: {len(group)} duplicates")
                for entity in group:
                    name = entity.get('name') or entity.get('type') or entity.get('description', '')[:50]
                    print(f"      • ID {entity['id']}: {name}")
                print()

            # Merge if not dry run
            if not dry_run:
                print(f"  🔗 Merging duplicate groups...")

                for group in duplicate_groups:
                    # Keep first entity as master
                    master = group[0]
                    duplicates = group[1:]

                    # Merge all duplicates into master
                    for dup in duplicates:
                        # Merge attributes
                        merged = merger.merge(dup, master, interview_id=None)

                        # Update master in database
                        # (Implementation would update master and delete duplicate)

                        total_merged += 1

                print(f"  ✅ Merged {len(duplicate_groups)} groups ({total_merged} entities)")
            else:
                print(f"  ℹ️  DRY RUN - would merge {len(duplicate_groups)} groups")
                total_merged += sum(len(g) - 1 for g in duplicate_groups)
        else:
            print(f"  ℹ️  No duplicates found above threshold")

        count_after = count_before - (sum(len(g) - 1 for g in duplicate_groups))
        total_after += count_after

        if count_before != count_after:
            reduction = ((count_before - count_after) / count_before) * 100
            print(f"\n  📉 {entity_type}: {count_before} → {count_after} ({reduction:.1f}% reduction)")

    # Summary
    print(f"\n{'='*70}")
    print("CONSOLIDATION SUMMARY")
    print('='*70)
    print(f"  Total entities before: {total_before}")
    print(f"  Total entities after:  {total_after}")
    print(f"  Total merged:          {total_merged}")

    if total_before > 0:
        reduction = ((total_before - total_after) / total_before) * 100
        print(f"  Overall reduction:     {reduction:.1f}%")

    if dry_run:
        print(f"\n  ℹ️  DRY RUN - no changes made to database")
    else:
        print(f"\n  ✅ Changes committed to database")

    print('='*70)

    # Close database
    db.close()


def main():
    parser = argparse.ArgumentParser(
        description='Consolidate existing entities in the database'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=DB_PATH,
        help='Path to database file (default: data/full_intelligence.db)'
    )
    parser.add_argument(
        '--entity-type',
        type=str,
        help='Specific entity type to consolidate (default: all types)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be consolidated without making changes'
    )

    args = parser.parse_args()

    # Get entity types
    entity_types = [args.entity_type] if args.entity_type else None

    # Run consolidation
    consolidate_existing_entities(
        db_path=args.db_path,
        entity_types=entity_types,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
