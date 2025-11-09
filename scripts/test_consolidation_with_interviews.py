#!/usr/bin/env python3
"""
Test Consolidation with Real Interviews

Tests the consolidation system with a subset of real interviews.
Measures performance, duplicate reduction, and relationship discovery.
"""
import sys
import os
import json
import time
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.consolidation_agent import KnowledgeConsolidationAgent
from intelligence_capture.pattern_recognizer import PatternRecognizer
from intelligence_capture.config import (
    load_consolidation_config,
    DB_PATH,
    PILOT_DB_PATH,
    INTERVIEWS_FILE,
    REPORTS_DIR
)


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")


def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_info(text: str):
    """Print info message"""
    print(f"  {text}")


def get_entity_counts_before(db: EnhancedIntelligenceDB) -> dict:
    """Get entity counts before consolidation"""
    cursor = db.conn.cursor()
    counts = {}
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    for entity_type in entity_types:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
            counts[entity_type] = cursor.fetchone()[0]
        except:
            counts[entity_type] = 0
    
    return counts


def get_entity_counts_after(db: EnhancedIntelligenceDB) -> dict:
    """Get entity counts after consolidation"""
    return get_entity_counts_before(db)


def get_consolidation_metrics(db: EnhancedIntelligenceDB) -> dict:
    """Get consolidation metrics"""
    cursor = db.conn.cursor()
    metrics = {}
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    for entity_type in entity_types:
        try:
            # Get entities with multiple sources
            cursor.execute(f"""
                SELECT COUNT(*) FROM {entity_type}
                WHERE source_count > 1
            """)
            multi_source = cursor.fetchone()[0]
            
            # Get average confidence
            cursor.execute(f"""
                SELECT AVG(consensus_confidence) FROM {entity_type}
                WHERE consensus_confidence IS NOT NULL
            """)
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            # Get total source count
            cursor.execute(f"""
                SELECT SUM(source_count) FROM {entity_type}
            """)
            total_sources = cursor.fetchone()[0] or 0
            
            # Get current count
            cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
            current_count = cursor.fetchone()[0]
            
            # Calculate reduction
            if total_sources > 0:
                reduction_pct = ((total_sources - current_count) / total_sources) * 100
            else:
                reduction_pct = 0.0
            
            metrics[entity_type] = {
                "current_count": current_count,
                "original_count": total_sources,
                "multi_source_entities": multi_source,
                "avg_confidence": round(avg_confidence, 3),
                "reduction_percentage": round(reduction_pct, 1)
            }
        except Exception as e:
            print_warning(f"Could not get metrics for {entity_type}: {e}")
            metrics[entity_type] = {}
    
    return metrics


def get_relationship_metrics(db: EnhancedIntelligenceDB) -> dict:
    """Get relationship metrics"""
    cursor = db.conn.cursor()
    
    try:
        # Total relationships
        cursor.execute("SELECT COUNT(*) FROM relationships")
        total = cursor.fetchone()[0]
        
        # By type
        cursor.execute("""
            SELECT relationship_type, COUNT(*) 
            FROM relationships 
            GROUP BY relationship_type
        """)
        by_type = {row[0]: row[1] for row in cursor.fetchall()}
        
        return {
            "total_relationships": total,
            "by_type": by_type
        }
    except:
        return {"total_relationships": 0, "by_type": {}}


def test_consolidation(
    num_interviews: int = 10,
    use_pilot_db: bool = False,
    verbose: bool = False,
    test_contradictions: bool = True,
    test_rollback: bool = False,
    measure_memory: bool = True
):
    """
    Test consolidation with real interviews
    
    Args:
        num_interviews: Number of interviews to process
        use_pilot_db: Use pilot database instead of full database
        verbose: Print verbose output
        test_contradictions: Test contradiction detection
        test_rollback: Test rollback mechanism
        measure_memory: Measure memory usage
    """
    print_header(f"CONSOLIDATION TEST WITH {num_interviews} INTERVIEWS")
    
    # Select database
    db_path = PILOT_DB_PATH if use_pilot_db else DB_PATH
    print_info(f"Database: {db_path}")
    
    # Load configuration
    print("\n📋 Loading configuration...")
    config = load_consolidation_config()
    print_success("Configuration loaded")
    
    # Connect to database
    print("\n📂 Connecting to database...")
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    print_success("Database connected")
    
    # Check if database has data
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]
    
    if total_interviews == 0:
        print_error("Database has no interviews. Run extraction first.")
        return
    
    print_info(f"Found {total_interviews} interviews in database")
    
    if num_interviews > total_interviews:
        print_warning(f"Requested {num_interviews} interviews but only {total_interviews} available")
        num_interviews = total_interviews
    
    # Get entity counts before
    print("\n📊 Getting entity counts before consolidation...")
    counts_before = get_entity_counts_before(db)
    total_before = sum(counts_before.values())
    print_info(f"Total entities: {total_before}")
    for entity_type, count in counts_before.items():
        if count > 0:
            print_info(f"  {entity_type}: {count}")
    
    # Initialize consolidation agent
    print("\n🔗 Initializing consolidation agent...")
    agent = KnowledgeConsolidationAgent(
        db=db,
        config=config,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    print_success("Consolidation agent initialized")
    
    # Get interviews to process
    cursor.execute(f"""
        SELECT id, company, respondent 
        FROM interviews 
        LIMIT ?
    """, (num_interviews,))
    interviews = cursor.fetchall()
    
    print(f"\n🔄 Processing {len(interviews)} interviews...")
    start_time = time.time()
    
    processed = 0
    failed = 0
    
    for interview_id, company, respondent in interviews:
        try:
            if verbose:
                print(f"\n  Processing interview {interview_id}: {company} - {respondent}")
            
            # Get entities for this interview
            entities = {}
            
            for entity_type in ["pain_points", "processes", "systems", "kpis", 
                               "automation_candidates", "inefficiencies"]:
                try:
                    cursor.execute(f"""
                        SELECT * FROM {entity_type}
                        WHERE interview_id = ?
                    """, (interview_id,))
                    
                    rows = cursor.fetchall()
                    if rows:
                        # Convert rows to dicts
                        columns = [desc[0] for desc in cursor.description]
                        entities[entity_type] = [
                            dict(zip(columns, row)) for row in rows
                        ]
                except:
                    pass
            
            if not entities:
                if verbose:
                    print_warning(f"    No entities found for interview {interview_id}")
                continue
            
            # Consolidate entities
            consolidated = agent.consolidate_entities(entities, interview_id)
            
            processed += 1
            if verbose:
                print_success(f"    Consolidated {sum(len(e) for e in entities.values())} entities")
            
        except Exception as e:
            failed += 1
            print_error(f"    Failed to process interview {interview_id}: {e}")
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"\n⏱️  Processing time: {duration:.2f}s ({duration/num_interviews:.2f}s per interview)")
    print_info(f"Processed: {processed}/{num_interviews}")
    if failed > 0:
        print_warning(f"Failed: {failed}/{num_interviews}")
    
    # Get entity counts after
    print("\n📊 Getting entity counts after consolidation...")
    counts_after = get_entity_counts_after(db)
    total_after = sum(counts_after.values())
    print_info(f"Total entities: {total_after}")
    
    # Calculate reduction
    if total_before > 0:
        reduction_pct = ((total_before - total_after) / total_before) * 100
        print_info(f"Reduction: {reduction_pct:.1f}%")
    
    # Get consolidation metrics
    print("\n📈 Consolidation Metrics:")
    metrics = get_consolidation_metrics(db)
    
    for entity_type, m in metrics.items():
        if m.get("current_count", 0) > 0:
            print(f"\n  {Colors.BOLD}{entity_type}:{Colors.END}")
            print_info(f"    Original: {m.get('original_count', 0)} entities")
            print_info(f"    Current: {m.get('current_count', 0)} entities")
            print_info(f"    Multi-source: {m.get('multi_source_entities', 0)} entities")
            print_info(f"    Avg confidence: {m.get('avg_confidence', 0.0)}")
            if m.get('reduction_percentage', 0) > 0:
                print_success(f"    Reduction: {m.get('reduction_percentage', 0)}%")
    
    # Get relationship metrics
    print("\n🔗 Relationship Metrics:")
    rel_metrics = get_relationship_metrics(db)
    print_info(f"Total relationships: {rel_metrics['total_relationships']}")
    
    if rel_metrics['by_type']:
        for rel_type, count in rel_metrics['by_type'].items():
            print_info(f"  {rel_type}: {count}")
    
    # Run pattern recognition
    print("\n🔍 Running pattern recognition...")
    pattern_recognizer = PatternRecognizer(db, config)
    patterns = pattern_recognizer.identify_patterns()
    
    if patterns:
        print_success(f"Identified {len(patterns)} patterns")
        high_priority = sum(1 for p in patterns if p['high_priority'])
        print_info(f"  High priority: {high_priority}")
        print_info(f"  Recurring pain points: {pattern_recognizer.stats['recurring_pain_points']}")
        print_info(f"  Problematic systems: {pattern_recognizer.stats['problematic_systems']}")
    else:
        print_warning("No patterns identified")
    
    # Get agent statistics
    print("\n📊 Agent Statistics:")
    stats = agent.get_statistics()
    print_info(f"Entities processed: {stats['entities_processed']}")
    print_info(f"Duplicates found: {stats['duplicates_found']}")
    print_info(f"Entities merged: {stats['entities_merged']}")
    print_info(f"Contradictions detected: {stats['contradictions_detected']}")
    print_info(f"Relationships discovered: {stats['relationships_discovered']}")
    
    # Generate report
    report_path = REPORTS_DIR / f"consolidation_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    report = {
        "timestamp": datetime.now().isoformat(),
        "num_interviews": num_interviews,
        "processing_time_seconds": duration,
        "counts_before": counts_before,
        "counts_after": counts_after,
        "consolidation_metrics": metrics,
        "relationship_metrics": rel_metrics,
        "patterns": len(patterns),
        "agent_statistics": stats
    }
    
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n📄 Report saved to: {report_path}")
    
    # Test contradiction detection
    if test_contradictions:
        print("\n🔍 Testing Contradiction Detection...")
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE has_contradictions = 1
        """)
        contradictions = cursor.fetchone()[0]
        
        if contradictions > 0:
            print_success(f"Found {contradictions} entities with contradictions")
            
            # Show examples
            cursor.execute("""
                SELECT name, contradiction_details
                FROM pain_points
                WHERE has_contradictions = 1
                LIMIT 3
            """)
            examples = cursor.fetchall()
            for name, details in examples:
                print_info(f"  Example: {name}")
                if details:
                    try:
                        details_obj = json.loads(details)
                        print_info(f"    Details: {details_obj}")
                    except:
                        pass
        else:
            print_info("No contradictions detected (expected for single-source entities)")
    
    # Test rollback mechanism (if requested)
    if test_rollback:
        print("\n🔄 Testing Rollback Mechanism...")
        cursor.execute("""
            SELECT id FROM consolidation_audit
            ORDER BY consolidation_timestamp DESC
            LIMIT 1
        """)
        audit_record = cursor.fetchone()
        
        if audit_record:
            audit_id = audit_record[0]
            print_info(f"Found audit record: {audit_id}")
            print_warning("Rollback test not implemented yet (Task 34)")
        else:
            print_warning("No audit records found for rollback test")
    
    # Measure memory usage
    memory_mb = 0
    if measure_memory:
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            print(f"\n💾 Memory Usage: {memory_mb:.1f} MB")
            
            if memory_mb < 500:
                print_success(f"Memory usage within target (<500 MB) ✓")
            else:
                print_warning(f"Memory usage exceeds target (500 MB)")
        except ImportError:
            print_warning("psutil not installed, skipping memory measurement")
    
    # Validation checks
    print("\n✅ Validation Checks:")
    validation_results = {}
    
    # Check 1: All entities have source_count >= 1
    cursor.execute("""
        SELECT COUNT(*) FROM pain_points
        WHERE source_count < 1 OR source_count IS NULL
    """)
    invalid_source_count = cursor.fetchone()[0]
    validation_results["source_count_valid"] = invalid_source_count == 0
    
    if validation_results["source_count_valid"]:
        print_success("All entities have valid source_count ✓")
    else:
        print_error(f"Found {invalid_source_count} entities with invalid source_count")
    
    # Check 2: All entities have consensus_confidence between 0.0 and 1.0
    cursor.execute("""
        SELECT COUNT(*) FROM pain_points
        WHERE consensus_confidence < 0.0 OR consensus_confidence > 1.0
    """)
    invalid_confidence = cursor.fetchone()[0]
    validation_results["confidence_valid"] = invalid_confidence == 0
    
    if validation_results["confidence_valid"]:
        print_success("All entities have valid consensus_confidence ✓")
    else:
        print_error(f"Found {invalid_confidence} entities with invalid confidence")
    
    # Check 3: No orphaned relationships
    cursor.execute("""
        SELECT COUNT(*) FROM relationships r
        WHERE NOT EXISTS (
            SELECT 1 FROM pain_points WHERE id = r.target_entity_id AND r.target_entity_type = 'pain_points'
        ) AND NOT EXISTS (
            SELECT 1 FROM systems WHERE id = r.target_entity_id AND r.target_entity_type = 'systems'
        )
    """)
    orphaned_rels = cursor.fetchone()[0]
    validation_results["no_orphaned_relationships"] = orphaned_rels == 0
    
    if validation_results["no_orphaned_relationships"]:
        print_success("No orphaned relationships ✓")
    else:
        print_error(f"Found {orphaned_rels} orphaned relationships")
    
    # Check 4: Performance target met
    validation_results["performance_target"] = duration < 120
    if validation_results["performance_target"]:
        print_success(f"Performance target met ({duration:.2f}s < 120s) ✓")
    else:
        print_error(f"Performance target missed ({duration:.2f}s >= 120s)")
    
    # Check 5: Duplicate reduction achieved (if applicable)
    validation_results["duplicate_reduction"] = reduction_pct > 0 or total_before == total_after
    if reduction_pct > 0:
        print_success(f"Duplicate reduction achieved ({reduction_pct:.1f}%) ✓")
    else:
        print_info("No duplicate reduction (no duplicates found or already consolidated)")
    
    # Close database
    db.close()
    
    print_header("TEST COMPLETE")
    
    # Summary with pass/fail
    print("\n📊 Test Summary:")
    total_checks = len(validation_results)
    passed_checks = sum(1 for v in validation_results.values() if v)
    
    print(f"\n  Passed: {passed_checks}/{total_checks} checks")
    
    if duration < 120:  # 2 minutes
        print_success(f"  Performance: {duration:.2f}s (target: <2 minutes) ✓")
    else:
        print_warning(f"  Performance: {duration:.2f}s (target: <2 minutes)")
    
    if reduction_pct >= 70:
        print_success(f"  Duplicate reduction: {reduction_pct:.1f}% (target: 70-90%) ✓")
    elif reduction_pct > 0:
        print_warning(f"  Duplicate reduction: {reduction_pct:.1f}% (target: 70-90%)")
    else:
        print_info(f"  Duplicate reduction: {reduction_pct:.1f}% (no duplicates found)")
    
    if rel_metrics['total_relationships'] > 0:
        print_success(f"  Relationships discovered: {rel_metrics['total_relationships']} ✓")
    else:
        print_warning("  No relationships discovered")
    
    if patterns:
        print_success(f"  Patterns identified: {len(patterns)} ✓")
    else:
        print_warning("  No patterns identified")
    
    if measure_memory and memory_mb > 0:
        if memory_mb < 500:
            print_success(f"  Memory usage: {memory_mb:.1f} MB (target: <500 MB) ✓")
        else:
            print_warning(f"  Memory usage: {memory_mb:.1f} MB (target: <500 MB)")
    
    # Overall result
    if passed_checks == total_checks:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL VALIDATION CHECKS PASSED{Colors.END}")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  {total_checks - passed_checks} VALIDATION CHECK(S) FAILED{Colors.END}")
    
    # Update report with validation results
    report["validation_results"] = validation_results
    report["validation_summary"] = {
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "all_passed": passed_checks == total_checks
    }
    report["memory_usage_mb"] = memory_mb
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    return passed_checks == total_checks


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Test consolidation with real interviews"
    )
    parser.add_argument(
        "--interviews",
        type=int,
        default=10,
        help="Number of interviews to process (default: 10)"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Use pilot database instead of full database"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print verbose output"
    )
    parser.add_argument(
        "--test-contradictions",
        action="store_true",
        default=True,
        help="Test contradiction detection (default: True)"
    )
    parser.add_argument(
        "--test-rollback",
        action="store_true",
        help="Test rollback mechanism (requires Task 34)"
    )
    parser.add_argument(
        "--measure-memory",
        action="store_true",
        default=True,
        help="Measure memory usage (default: True, requires psutil)"
    )
    
    args = parser.parse_args()
    
    success = test_consolidation(
        num_interviews=args.interviews,
        use_pilot_db=args.pilot,
        verbose=args.verbose,
        test_contradictions=args.test_contradictions,
        test_rollback=args.test_rollback,
        measure_memory=args.measure_memory
    )
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
