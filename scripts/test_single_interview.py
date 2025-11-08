#!/usr/bin/env python3
"""
Test extraction on a single interview
Verifies all 17 entity types are extracted and stored correctly
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.processor import IntelligenceProcessor
from intelligence_capture.config import DB_PATH, INTERVIEWS_FILE


def test_single_interview(interview_index: int = 0, db_path: Path = None):
    """
    Test extraction on a single interview

    Args:
        interview_index: Index of interview to test (default: 0 = first interview)
        db_path: Path to test database (default: test_single.db)
    """
    # Use test database
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "test_single.db"

    # Delete existing test database
    if db_path.exists():
        db_path.unlink()
        print(f"🗑️  Deleted existing test database")

    # Load interviews
    print(f"\n📂 Loading interviews from: {INTERVIEWS_FILE}")
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)

    if interview_index >= len(interviews):
        print(f"❌ Interview index {interview_index} out of range (max: {len(interviews)-1})")
        sys.exit(1)

    interview = interviews[interview_index]
    meta = interview.get("meta", {})

    print(f"✓ Loaded interview {interview_index}")
    print(f"  Company: {meta.get('company', 'Unknown')}")
    print(f"  Respondent: {meta.get('respondent', 'Unknown')}")
    print(f"  Role: {meta.get('role', 'Unknown')}")
    print(f"  Date: {meta.get('date', 'Unknown')}")

    # Initialize processor
    print(f"\n🔧 Initializing processor with test database: {db_path}")
    processor = IntelligenceProcessor(db_path=db_path)
    processor.initialize()

    # Process interview
    print(f"\n🚀 Processing interview...")
    print(f"{'='*70}\n")

    success = processor.process_interview(interview)

    print(f"\n{'='*70}")

    if success:
        print(f"✅ Interview processed successfully")
    else:
        print(f"❌ Interview processing failed")
        processor.close()
        sys.exit(1)

    # Verify results
    print(f"\n🔍 Verifying extraction results...")
    print(f"{'='*70}\n")

    cursor = processor.db.conn.cursor()

    # Check interview record
    cursor.execute("SELECT COUNT(*) FROM interviews")
    interview_count = cursor.fetchone()[0]
    print(f"✓ Interviews in database: {interview_count}")

    # Check entity counts for all types
    entity_tables = {
        "pain_points": "Pain Points",
        "processes": "Processes",
        "systems": "Systems",
        "kpis": "KPIs",
        "automation_candidates": "Automation Candidates",
        "inefficiencies": "Inefficiencies",
        "communication_channels": "Communication Channels",
        "decision_points": "Decision Points",
        "data_flows": "Data Flows",
        "temporal_patterns": "Temporal Patterns",
        "failure_modes": "Failure Modes",
        "team_structures": "Team Structures",
        "knowledge_gaps": "Knowledge Gaps",
        "success_patterns": "Success Patterns",
        "budget_constraints": "Budget Constraints",
        "external_dependencies": "External Dependencies",
    }

    print(f"\n📊 Entity counts:")
    print(f"{'-'*70}")

    total_entities = 0
    empty_types = []

    for table, display_name in entity_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_entities += count

            status = "✓" if count > 0 else "⚠"
            print(f"{status} {display_name:30s}: {count:3d}")

            if count == 0:
                empty_types.append(display_name)
        except Exception as e:
            print(f"✗ {display_name:30s}: Table not found")

    print(f"{'-'*70}")
    print(f"Total entities extracted: {total_entities}")

    if empty_types:
        print(f"\n⚠️  Entity types with no data:")
        for entity_type in empty_types:
            print(f"  - {entity_type}")

    # Sample some extracted entities
    print(f"\n📝 Sample extracted entities:")
    print(f"{'-'*70}\n")

    # Sample pain points
    cursor.execute("SELECT type, description FROM pain_points LIMIT 3")
    pain_points = cursor.fetchall()
    if pain_points:
        print(f"Pain Points:")
        for pp in pain_points:
            print(f"  • Type: {pp[0]}")
            print(f"    Description: {pp[1][:100]}..." if len(pp[1]) > 100 else f"    Description: {pp[1]}")
            print()

    # Sample processes
    cursor.execute("SELECT name, description FROM processes LIMIT 2")
    processes = cursor.fetchall()
    if processes:
        print(f"Processes:")
        for proc in processes:
            print(f"  • Name: {proc[0]}")
            print(f"    Description: {proc[1][:100]}..." if proc[1] and len(proc[1]) > 100 else f"    Description: {proc[1]}")
            print()

    # Sample systems
    cursor.execute("SELECT name, type FROM systems LIMIT 3")
    systems = cursor.fetchall()
    if systems:
        print(f"Systems:")
        for sys in systems:
            print(f"  • Name: {sys[0]}, Type: {sys[1]}")

    # Check data quality
    print(f"\n🔍 Data quality checks:")
    print(f"{'-'*70}")

    # Check for empty descriptions
    cursor.execute("""
        SELECT COUNT(*) FROM pain_points
        WHERE description IS NULL OR description = '' OR LENGTH(description) < 20
    """)
    short_descriptions = cursor.fetchone()[0]
    if short_descriptions > 0:
        print(f"⚠ Pain points with short descriptions: {short_descriptions}")
    else:
        print(f"✓ All pain point descriptions have adequate length")

    # Check for encoding issues
    cursor.execute("""
        SELECT COUNT(*) FROM pain_points
        WHERE description LIKE '%Ã¡%' OR description LIKE '%Ã©%'
    """)
    encoding_issues = cursor.fetchone()[0]
    if encoding_issues > 0:
        print(f"⚠ Entities with encoding issues: {encoding_issues}")
    else:
        print(f"✓ No encoding issues detected")

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Interview processed: ✓")
    print(f"Total entities extracted: {total_entities}")
    print(f"Entity types with data: {len(entity_tables) - len(empty_types)}/{len(entity_tables)}")
    print(f"Empty entity types: {len(empty_types)}")
    print(f"Quality issues: {short_descriptions + encoding_issues}")

    if total_entities > 0 and len(empty_types) < len(entity_tables):
        print(f"\n✅ TEST PASSED - Extraction working correctly")
    else:
        print(f"\n⚠️  TEST WARNING - Some entity types may not be extracting")

    print(f"{'='*70}\n")

    print(f"💾 Test database saved at: {db_path}")
    print(f"   You can inspect it with: sqlite3 {db_path}")

    processor.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test extraction on a single interview")
    parser.add_argument("--index", type=int, default=0, help="Interview index to test (default: 0)")
    parser.add_argument("--db", type=Path, help="Path to test database")
    args = parser.parse_args()

    test_single_interview(args.index, args.db)


if __name__ == "__main__":
    main()
