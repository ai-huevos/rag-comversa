#!/usr/bin/env python3
"""
Test script for MetaOrchestrator multi-agent workflow
Tests complete workflow: extraction → validation → re-extraction → storage
"""
import sys
import json
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.extractor import IntelligenceExtractor
from intelligence_capture.validation_agent import ValidationAgent
from intelligence_capture.storage_agent import StorageAgent
from intelligence_capture.meta_orchestrator import MetaOrchestrator
from intelligence_capture.config import DB_PATH, INTERVIEWS_FILE, load_extraction_config


def test_single_interview():
    """Test MetaOrchestrator with a single interview"""

    print(f"\n{'='*70}")
    print(f"🧪 TESTING META-ORCHESTRATOR")
    print(f"{'='*70}\n")

    # Load configuration
    config = load_extraction_config()

    # Load interviews
    print(f"📂 Loading interviews from: {INTERVIEWS_FILE}")
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)

    print(f"✓ Found {len(interviews)} interviews")

    # Use test database
    test_db_path = Path("data/test_meta_orchestrator.db")
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"🗑️  Removed old test database")

    # Initialize components
    print(f"\n🔧 Initializing components...")
    db = EnhancedIntelligenceDB(test_db_path)
    db.connect()
    db.init_v2_schema()
    print(f"✓ Database initialized: {test_db_path}")

    extractor = IntelligenceExtractor()
    print(f"✓ Extractor initialized")

    validation_agent = ValidationAgent(
        enable_llm_validation=False,  # Use rule-based only for speed
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    print(f"✓ ValidationAgent initialized (rule-based)")

    storage_agent = StorageAgent(db)
    print(f"✓ StorageAgent initialized")

    # Initialize MetaOrchestrator
    orchestrator = MetaOrchestrator(
        db=db,
        extractor=extractor,
        validation_agent=validation_agent,
        storage_agent=storage_agent,
        config=config
    )
    print(f"✓ MetaOrchestrator initialized")

    # Process first interview as test
    interview = interviews[0]
    meta = interview.get("meta", {})
    company = meta.get("company", "Unknown")
    respondent = meta.get("respondent", "Unknown")

    print(f"\n{'='*70}")
    print(f"📋 Testing with: {respondent} ({company})")
    print(f"{'='*70}")

    # Process interview
    result = orchestrator.process_interview(interview, enable_iterative_refinement=True)

    # Print results
    print(f"\n{'='*70}")
    print(f"📊 TEST RESULTS")
    print(f"{'='*70}")
    print(f"Success: {'✅' if result.success else '❌'}")
    print(f"Interview ID: {result.interview_id}")
    print(f"Entities Extracted: {result.entity_count}")
    print(f"Quality Score: {result.quality_score:.2%}")
    print(f"Validation Passed: {'✅' if result.validation_passed else '❌'}")
    print(f"Iterations: {result.iterations}")
    print(f"Processing Time: {result.processing_time:.1f}s")

    if result.missing_entities:
        print(f"\n⚠️  Missing Entity Types:")
        for entity_type in result.missing_entities:
            print(f"   - {entity_type}")

    if result.consistency_issues > 0:
        print(f"\n🔗 Consistency Issues: {result.consistency_issues}")

    if result.hallucination_issues > 0:
        print(f"🎭 Hallucination Issues: {result.hallucination_issues}")

    if result.error:
        print(f"\n❌ Error: {result.error}")

    # Verify storage
    print(f"\n{'='*70}")
    print(f"🔍 VERIFYING STORAGE")
    print(f"{'='*70}")

    verification = storage_agent.verify_storage(result.interview_id)
    print(f"Interview Exists: {'✅' if verification['interview_exists'] else '❌'}")
    print(f"Total Entities Stored: {verification['total_entities']}")

    if verification['missing_types']:
        print(f"\n⚠️  Entity Types with 0 Entities:")
        for entity_type in verification['missing_types']:
            print(f"   - {entity_type}")

    print(f"\n📈 Entity Counts by Type:")
    for entity_type, count in verification['entity_counts'].items():
        if isinstance(count, int) and count > 0:
            print(f"   {entity_type}: {count}")

    # Test rollback capability
    print(f"\n{'='*70}")
    print(f"🔄 TESTING ROLLBACK")
    print(f"{'='*70}")

    rollback_result = storage_agent.rollback_interview(result.interview_id)
    if rollback_result['success']:
        print(f"✅ Rollback successful: {rollback_result['entities_deleted']} entities deleted")

        # Verify rollback
        verification_after = storage_agent.verify_storage(result.interview_id)
        print(f"Entities After Rollback: {verification_after['total_entities']}")
    else:
        print(f"❌ Rollback failed: {rollback_result['errors']}")

    # Cleanup
    db.close()
    print(f"\n✓ Test complete")


def test_batch_interviews(num_interviews: int = 5):
    """Test MetaOrchestrator with multiple interviews"""

    print(f"\n{'='*70}")
    print(f"🧪 BATCH TEST: {num_interviews} INTERVIEWS")
    print(f"{'='*70}\n")

    # Load configuration
    config = load_extraction_config()

    # Load interviews
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)[:num_interviews]

    # Use test database
    test_db_path = Path("data/test_meta_batch.db")
    if test_db_path.exists():
        test_db_path.unlink()

    # Initialize components
    db = EnhancedIntelligenceDB(test_db_path)
    db.connect()
    db.init_v2_schema()

    extractor = IntelligenceExtractor()
    validation_agent = ValidationAgent(enable_llm_validation=False)
    storage_agent = StorageAgent(db)

    orchestrator = MetaOrchestrator(
        db=db,
        extractor=extractor,
        validation_agent=validation_agent,
        storage_agent=storage_agent,
        config=config
    )

    # Process all interviews
    results = []
    for i, interview in enumerate(interviews, 1):
        meta = interview.get("meta", {})
        print(f"\n[{i}/{num_interviews}] Processing {meta.get('respondent', 'Unknown')}...")

        result = orchestrator.process_interview(interview)
        results.append(result)

    # Summary statistics
    print(f"\n{'='*70}")
    print(f"📊 BATCH TEST SUMMARY")
    print(f"{'='*70}")

    successful = sum(1 for r in results if r.success)
    total_entities = sum(r.entity_count for r in results)
    avg_quality = sum(r.quality_score for r in results) / len(results) if results else 0
    total_time = sum(r.processing_time for r in results)
    total_iterations = sum(r.iterations for r in results)

    print(f"Successful: {successful}/{len(results)}")
    print(f"Total Entities: {total_entities}")
    print(f"Avg Quality Score: {avg_quality:.2%}")
    print(f"Total Time: {total_time:.1f}s")
    print(f"Avg Time per Interview: {total_time/len(results):.1f}s")
    print(f"Total Iterations: {total_iterations}")
    print(f"Avg Iterations: {total_iterations/len(results):.1f}")

    # Consistency and hallucination stats
    total_consistency_issues = sum(r.consistency_issues for r in results)
    total_hallucination_issues = sum(r.hallucination_issues for r in results)

    print(f"\nConsistency Issues: {total_consistency_issues}")
    print(f"Hallucination Issues: {total_hallucination_issues}")

    # Cleanup
    db.close()
    print(f"\n✓ Batch test complete")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MetaOrchestrator workflow")
    parser.add_argument("--batch", type=int, help="Test with N interviews", metavar="N")
    args = parser.parse_args()

    if args.batch:
        test_batch_interviews(args.batch)
    else:
        test_single_interview()
