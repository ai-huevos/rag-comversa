#!/usr/bin/env python3
"""
Test extraction on a batch of interviews (default: 5)
Tests consistency, performance, and resume capability
"""
import sys
import json
import time
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.processor import IntelligenceProcessor
from intelligence_capture.config import DB_PATH, INTERVIEWS_FILE
from intelligence_capture.logging_config import (
    setup_extraction_logging,
    log_extraction_start,
    log_extraction_complete,
    log_interview_start,
    log_interview_complete,
    log_interview_error
)


def test_batch_interviews(batch_size: int = 5, db_path: Path = None, test_resume: bool = False):
    """
    Test extraction on a batch of interviews

    Args:
        batch_size: Number of interviews to process (default: 5)
        db_path: Path to test database (default: test_batch.db)
        test_resume: If True, test resume capability by interrupting and restarting
    """
    # Setup logging
    logger = setup_extraction_logging()

    # Use test database
    if db_path is None:
        db_path = Path(__file__).parent.parent / "data" / "test_batch.db"

    # Delete existing test database (unless testing resume)
    if db_path.exists() and not test_resume:
        db_path.unlink()
        print(f"🗑️  Deleted existing test database")
        logger.info(f"Deleted existing test database: {db_path}")

    # Load interviews
    print(f"\n📂 Loading interviews from: {INTERVIEWS_FILE}")
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        all_interviews = json.load(f)

    # Take first N interviews
    interviews = all_interviews[:batch_size]

    print(f"✓ Loaded {len(interviews)} interviews for testing")

    # Initialize processor
    print(f"\n🔧 Initializing processor with test database: {db_path}")
    logger.info(f"Initializing processor with test database: {db_path}")
    processor = IntelligenceProcessor(db_path=db_path)
    processor.initialize()

    # Process interviews
    print(f"\n🚀 Processing {len(interviews)} interviews...")
    print(f"{'='*70}\n")

    log_extraction_start(logger, len(interviews))

    start_time = time.time()
    success_count = 0
    error_count = 0

    for i, interview in enumerate(interviews, 1):
        meta = interview.get("meta", {})
        company = meta.get('company', 'Unknown')
        respondent = meta.get('respondent', 'Unknown')
        print(f"\n[{i}/{len(interviews)}] Processing {company} / {respondent}")
        log_interview_start(logger, i, len(interviews), company, respondent)

        interview_start = time.time()
        try:
            success = processor.process_interview(interview)
            if success:
                success_count += 1
                interview_duration = time.time() - interview_start
                log_interview_complete(logger, f"{company}/{respondent}", interview_duration, {})
            else:
                error_count += 1
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            log_interview_error(logger, f"{company}/{respondent}", e)
            error_count += 1

    elapsed_time = time.time() - start_time

    print(f"\n{'='*70}")
    print(f"✓ Batch processing complete")
    print(f"  Success: {success_count}/{len(interviews)}")
    print(f"  Errors: {error_count}")
    print(f"  Total time: {elapsed_time:.1f}s")
    print(f"  Avg time per interview: {elapsed_time/len(interviews):.1f}s")
    print(f"{'='*70}\n")

    log_extraction_complete(logger, len(interviews), success_count, error_count, elapsed_time, {})

    # Analyze results
    print(f"📊 Analyzing results...")
    print(f"{'='*70}\n")

    cursor = processor.db.conn.cursor()

    # Check interview counts
    cursor.execute("SELECT COUNT(*) FROM interviews")
    interview_count = cursor.fetchone()[0]
    print(f"Interviews in database: {interview_count}")

    # Check entity counts across all interviews
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

    print(f"\n📊 Entity counts across all interviews:")
    print(f"{'-'*70}")

    total_entities = 0
    entity_counts = {}

    for table, display_name in entity_tables.items():
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            total_entities += count
            entity_counts[table] = count

            avg_per_interview = count / interview_count if interview_count > 0 else 0
            status = "✓" if count > 0 else "⚠"
            print(f"{status} {display_name:30s}: {count:4d} (avg {avg_per_interview:.1f}/interview)")
        except Exception as e:
            print(f"✗ {display_name:30s}: Table not found")
            entity_counts[table] = 0

    print(f"{'-'*70}")
    print(f"Total entities: {total_entities}")
    print(f"Avg per interview: {total_entities/interview_count:.1f}")

    # Check consistency across interviews
    print(f"\n🔍 Consistency check:")
    print(f"{'-'*70}")

    cursor.execute("""
        SELECT i.id, i.company, i.respondent,
               (SELECT COUNT(*) FROM pain_points WHERE interview_id = i.id) as pain_points,
               (SELECT COUNT(*) FROM processes WHERE interview_id = i.id) as processes,
               (SELECT COUNT(*) FROM systems s WHERE s.companies_using LIKE '%' || i.company || '%') as systems
        FROM interviews i
    """)

    interviews_data = cursor.fetchall()
    print(f"\nPer-interview breakdown:")
    print(f"{'Interview':<40s} | PP | Proc | Sys")
    print(f"{'-'*70}")

    for interview_data in interviews_data:
        interview_label = f"{interview_data[1]} / {interview_data[2]}"
        print(f"{interview_label:<40s} | {interview_data[3]:2d} | {interview_data[4]:4d} | {interview_data[5]:3d}")

    # Performance metrics
    print(f"\n⏱️  Performance Metrics:")
    print(f"{'-'*70}")
    print(f"Total processing time: {elapsed_time:.1f}s ({elapsed_time/60:.1f}m)")
    print(f"Avg time per interview: {elapsed_time/interview_count:.1f}s")
    print(f"Entities per second: {total_entities/elapsed_time:.1f}")

    # Estimated time for full 44 interviews
    estimated_full_time = (elapsed_time / interview_count) * 44
    print(f"\nEstimated time for 44 interviews: {estimated_full_time:.1f}s ({estimated_full_time/60:.1f}m)")

    # Check extraction status
    cursor.execute("""
        SELECT extraction_status, COUNT(*)
        FROM interviews
        GROUP BY extraction_status
    """)
    status_counts = dict(cursor.fetchall())

    print(f"\n📋 Extraction Status:")
    print(f"{'-'*70}")
    for status, count in status_counts.items():
        print(f"{status:12s}: {count}")

    # Summary
    print(f"\n{'='*70}")
    print(f"📊 BATCH TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Interviews processed: {success_count}/{len(interviews)}")
    print(f"Total entities: {total_entities}")
    print(f"Avg entities per interview: {total_entities/interview_count:.1f}")
    print(f"Processing time: {elapsed_time:.1f}s (avg {elapsed_time/interview_count:.1f}s per interview)")
    print(f"Extraction success rate: {success_count/len(interviews)*100:.1f}%")

    if success_count == len(interviews) and total_entities > 0:
        print(f"\n✅ BATCH TEST PASSED")
    else:
        print(f"\n⚠️  BATCH TEST WARNINGS")

    print(f"{'='*70}\n")

    print(f"💾 Test database saved at: {db_path}")
    print(f"   You can inspect it with: sqlite3 {db_path}")

    processor.close()

    return {
        "success_count": success_count,
        "total_count": len(interviews),
        "total_entities": total_entities,
        "elapsed_time": elapsed_time,
        "entity_counts": entity_counts
    }


def test_resume_capability(batch_size: int = 5):
    """Test resume capability"""
    print(f"\n{'='*70}")
    print(f"🔄 TESTING RESUME CAPABILITY")
    print(f"{'='*70}\n")

    db_path = Path(__file__).parent.parent / "data" / "test_resume.db"

    # Delete existing database
    if db_path.exists():
        db_path.unlink()

    # Process first half
    half_size = batch_size // 2
    print(f"Step 1: Processing first {half_size} interviews...")

    processor = IntelligenceProcessor(db_path=db_path)
    processor.initialize()

    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)[:batch_size]

    for i, interview in enumerate(interviews[:half_size]):
        meta = interview.get("meta", {})
        print(f"  [{i+1}/{half_size}] {meta.get('company')} / {meta.get('respondent')}")
        processor.process_interview(interview)

    processor.close()
    print(f"✓ First batch complete\n")

    # Process remaining with resume
    print(f"Step 2: Resuming and processing remaining {batch_size - half_size} interviews...")

    processor = IntelligenceProcessor(db_path=db_path)
    processor.initialize()

    # This simulates resume - it should skip already completed interviews
    success_count = 0
    for i, interview in enumerate(interviews):
        meta = interview.get("meta", {})
        result = processor.process_interview(interview)
        if result:
            success_count += 1
            print(f"  ✓ Processed: {meta.get('company')} / {meta.get('respondent')}")
        else:
            print(f"  ⊘ Skipped (already complete): {meta.get('company')} / {meta.get('respondent')}")

    processor.close()

    print(f"\n✓ Resume test complete")
    print(f"  New interviews processed: {success_count}")
    print(f"  Already completed (skipped): {batch_size - success_count}")

    if success_count == batch_size - half_size:
        print(f"\n✅ RESUME CAPABILITY TEST PASSED")
    else:
        print(f"\n⚠️  RESUME CAPABILITY TEST FAILED")

    print(f"{'='*70}\n")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Test extraction on a batch of interviews")
    parser.add_argument("--batch-size", type=int, default=5, help="Number of interviews to process (default: 5)")
    parser.add_argument("--db", type=Path, help="Path to test database")
    parser.add_argument("--test-resume", action="store_true", help="Test resume capability")
    args = parser.parse_args()

    if args.test_resume:
        test_resume_capability(args.batch_size)
    else:
        test_batch_interviews(args.batch_size, args.db)


if __name__ == "__main__":
    main()
