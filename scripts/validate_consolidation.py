#!/usr/bin/env python3
"""
Consolidation Validation Script

Validates the Knowledge Graph consolidation system by running comprehensive checks:
- All entities have valid source_count >= 1
- All entities have consensus_confidence between 0.0 and 1.0
- mentioned_in_interviews contains valid interview IDs
- No orphaned relationships (all targets exist)
- Duplicate reduction achieved
- Generates consolidation_report.json with metrics
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH, REPORTS_DIR


# ANSI color codes for terminal output
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


def validate_source_counts(db: EnhancedIntelligenceDB) -> Tuple[bool, Dict]:
    """
    Validate that all entities have source_count >= 1
    
    Returns:
        (passed, metrics)
    """
    print(f"\n{Colors.BOLD}1. Validating Source Counts{Colors.END}")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    cursor = db.conn.cursor()
    passed = True
    metrics = {}
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Check for invalid source counts
        cursor.execute(f"""
            SELECT COUNT(*) FROM {entity_type}
            WHERE source_count IS NULL OR source_count < 1
        """)
        invalid_count = cursor.fetchone()[0]
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
        total_count = cursor.fetchone()[0]
        
        metrics[entity_type] = {
            "total": total_count,
            "invalid_source_count": invalid_count
        }
        
        if invalid_count > 0:
            print_error(f"{entity_type}: {invalid_count}/{total_count} entities have invalid source_count")
            passed = False
        else:
            print_success(f"{entity_type}: All {total_count} entities have valid source_count")
    
    return passed, metrics


def validate_consensus_confidence(db: EnhancedIntelligenceDB) -> Tuple[bool, Dict]:
    """
    Validate that all entities have consensus_confidence between 0.0 and 1.0
    
    Returns:
        (passed, metrics)
    """
    print(f"\n{Colors.BOLD}2. Validating Consensus Confidence{Colors.END}")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    cursor = db.conn.cursor()
    passed = True
    metrics = {}
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Check for invalid confidence scores
        cursor.execute(f"""
            SELECT COUNT(*) FROM {entity_type}
            WHERE consensus_confidence IS NULL 
               OR consensus_confidence < 0.0 
               OR consensus_confidence > 1.0
        """)
        invalid_count = cursor.fetchone()[0]
        
        # Get average confidence
        cursor.execute(f"""
            SELECT AVG(consensus_confidence) FROM {entity_type}
            WHERE consensus_confidence IS NOT NULL
        """)
        avg_confidence = cursor.fetchone()[0] or 0.0
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
        total_count = cursor.fetchone()[0]
        
        metrics[entity_type] = {
            "total": total_count,
            "invalid_confidence": invalid_count,
            "avg_confidence": round(avg_confidence, 3)
        }
        
        if invalid_count > 0:
            print_error(f"{entity_type}: {invalid_count}/{total_count} entities have invalid consensus_confidence")
            passed = False
        else:
            print_success(f"{entity_type}: All {total_count} entities have valid confidence (avg: {avg_confidence:.3f})")
    
    return passed, metrics


def validate_interview_references(db: EnhancedIntelligenceDB) -> Tuple[bool, Dict]:
    """
    Validate that mentioned_in_interviews contains valid interview IDs
    
    Returns:
        (passed, metrics)
    """
    print(f"\n{Colors.BOLD}3. Validating Interview References{Colors.END}")
    
    # Get all valid interview IDs
    cursor = db.conn.cursor()
    cursor.execute("SELECT id FROM interviews")
    valid_interview_ids = set(row[0] for row in cursor.fetchall())
    
    if not valid_interview_ids:
        print_warning("No interviews found in database")
        return True, {"valid_interview_ids": 0}
    
    print_info(f"Found {len(valid_interview_ids)} valid interview IDs")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    passed = True
    metrics = {"valid_interview_ids": len(valid_interview_ids)}
    invalid_references = []
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Check mentioned_in_interviews field
        cursor.execute(f"""
            SELECT id, mentioned_in_interviews FROM {entity_type}
            WHERE mentioned_in_interviews IS NOT NULL
        """)
        
        for entity_id, mentioned_in_str in cursor.fetchall():
            try:
                mentioned_in = json.loads(mentioned_in_str)
                for interview_id in mentioned_in:
                    if interview_id not in valid_interview_ids:
                        invalid_references.append({
                            "entity_type": entity_type,
                            "entity_id": entity_id,
                            "invalid_interview_id": interview_id
                        })
                        passed = False
            except json.JSONDecodeError:
                invalid_references.append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": "Invalid JSON"
                })
                passed = False
    
    metrics["invalid_references"] = len(invalid_references)
    
    if invalid_references:
        print_error(f"Found {len(invalid_references)} invalid interview references")
        for ref in invalid_references[:5]:  # Show first 5
            print_info(f"  {ref}")
    else:
        print_success("All interview references are valid")
    
    return passed, metrics


def validate_relationships(db: EnhancedIntelligenceDB) -> Tuple[bool, Dict]:
    """
    Validate that no orphaned relationships exist (all targets point to existing entities)
    
    Returns:
        (passed, metrics)
    """
    print(f"\n{Colors.BOLD}4. Validating Relationships{Colors.END}")
    
    cursor = db.conn.cursor()
    
    # Check if relationships table exists
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='relationships'"
    )
    if not cursor.fetchone():
        print_warning("Relationships table does not exist")
        return True, {"relationships_table_exists": False}
    
    # Get total relationship count
    cursor.execute("SELECT COUNT(*) FROM relationships")
    total_relationships = cursor.fetchone()[0]
    
    if total_relationships == 0:
        print_warning("No relationships found in database")
        return True, {"total_relationships": 0}
    
    print_info(f"Found {total_relationships} relationships")
    
    # Check for orphaned relationships
    cursor.execute("""
        SELECT 
            r.id,
            r.source_entity_type,
            r.source_entity_id,
            r.target_entity_type,
            r.target_entity_id
        FROM relationships r
    """)
    
    orphaned = []
    for rel_id, source_type, source_id, target_type, target_id in cursor.fetchall():
        # Check if source entity exists
        try:
            cursor.execute(f"SELECT id FROM {source_type} WHERE id = ?", (source_id,))
            if not cursor.fetchone():
                orphaned.append({
                    "relationship_id": rel_id,
                    "issue": "source_missing",
                    "entity_type": source_type,
                    "entity_id": source_id
                })
        except Exception as e:
            orphaned.append({
                "relationship_id": rel_id,
                "issue": "source_table_missing",
                "entity_type": source_type
            })
        
        # Check if target entity exists
        try:
            cursor.execute(f"SELECT id FROM {target_type} WHERE id = ?", (target_id,))
            if not cursor.fetchone():
                orphaned.append({
                    "relationship_id": rel_id,
                    "issue": "target_missing",
                    "entity_type": target_type,
                    "entity_id": target_id
                })
        except Exception as e:
            orphaned.append({
                "relationship_id": rel_id,
                "issue": "target_table_missing",
                "entity_type": target_type
            })
    
    metrics = {
        "total_relationships": total_relationships,
        "orphaned_relationships": len(orphaned)
    }
    
    if orphaned:
        print_error(f"Found {len(orphaned)} orphaned relationships")
        for orph in orphaned[:5]:  # Show first 5
            print_info(f"  {orph}")
        return False, metrics
    else:
        print_success(f"All {total_relationships} relationships are valid")
        return True, metrics


def calculate_duplicate_reduction(db: EnhancedIntelligenceDB) -> Dict:
    """
    Calculate duplicate reduction metrics
    
    Returns:
        metrics dict
    """
    print(f"\n{Colors.BOLD}5. Calculating Duplicate Reduction{Colors.END}")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    cursor = db.conn.cursor()
    metrics = {}
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Get total entities
        cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
        total_entities = cursor.fetchone()[0]
        
        # Get consolidated entities (source_count > 1)
        cursor.execute(f"""
            SELECT COUNT(*) FROM {entity_type}
            WHERE source_count > 1
        """)
        consolidated_entities = cursor.fetchone()[0]
        
        # Calculate original count (sum of all source_counts)
        cursor.execute(f"""
            SELECT SUM(source_count) FROM {entity_type}
        """)
        original_count = cursor.fetchone()[0] or total_entities
        
        # Calculate reduction
        if original_count > 0:
            reduction_pct = ((original_count - total_entities) / original_count) * 100
        else:
            reduction_pct = 0.0
        
        metrics[entity_type] = {
            "original_count": original_count,
            "current_count": total_entities,
            "consolidated_entities": consolidated_entities,
            "reduction_percentage": round(reduction_pct, 1)
        }
        
        if reduction_pct > 0:
            print_success(f"{entity_type}: {reduction_pct:.1f}% reduction ({original_count} → {total_entities})")
        else:
            print_info(f"{entity_type}: No reduction ({total_entities} entities)")
    
    return metrics


def get_top_entities(db: EnhancedIntelligenceDB, limit: int = 10) -> Dict:
    """
    Get top entities by source_count
    
    Returns:
        dict of entity_type -> list of top entities
    """
    print(f"\n{Colors.BOLD}6. Top {limit} Most-Mentioned Entities{Colors.END}")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    cursor = db.conn.cursor()
    top_entities = {}
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Get name field (varies by entity type)
        name_field = "name" if entity_type in ["systems", "processes"] else "type"
        
        try:
            cursor.execute(f"""
                SELECT {name_field}, source_count, consensus_confidence
                FROM {entity_type}
                WHERE source_count > 1
                ORDER BY source_count DESC
                LIMIT ?
            """, (limit,))
            
            entities = []
            for row in cursor.fetchall():
                entities.append({
                    "name": row[0],
                    "source_count": row[1],
                    "consensus_confidence": round(row[2], 3) if row[2] else None
                })
            
            if entities:
                top_entities[entity_type] = entities
                print(f"\n  {Colors.BOLD}{entity_type}:{Colors.END}")
                for i, entity in enumerate(entities[:5], 1):  # Show top 5
                    print_info(f"    {i}. {entity['name']} (sources: {entity['source_count']}, confidence: {entity['consensus_confidence']})")
        except Exception as e:
            print_warning(f"Could not query {entity_type}: {e}")
    
    return top_entities


def get_contradictions(db: EnhancedIntelligenceDB) -> List[Dict]:
    """
    Get all entities with contradictions
    
    Returns:
        list of entities with contradictions
    """
    print(f"\n{Colors.BOLD}7. Entities with Contradictions{Colors.END}")
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    cursor = db.conn.cursor()
    contradictions = []
    
    for entity_type in entity_types:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (entity_type,)
        )
        if not cursor.fetchone():
            continue
        
        # Get name field
        name_field = "name" if entity_type in ["systems", "processes"] else "type"
        
        try:
            cursor.execute(f"""
                SELECT {name_field}, contradiction_details
                FROM {entity_type}
                WHERE has_contradictions = 1
            """)
            
            for row in cursor.fetchall():
                contradictions.append({
                    "entity_type": entity_type,
                    "name": row[0],
                    "details": json.loads(row[1]) if row[1] else []
                })
        except Exception as e:
            print_warning(f"Could not query {entity_type}: {e}")
    
    if contradictions:
        print_warning(f"Found {len(contradictions)} entities with contradictions")
        for i, entity in enumerate(contradictions[:5], 1):  # Show first 5
            print_info(f"  {i}. {entity['entity_type']}: {entity['name']}")
            if entity['details']:
                for detail in entity['details'][:2]:  # Show first 2 details
                    print_info(f"     - {detail}")
    else:
        print_success("No contradictions found")
    
    return contradictions


def generate_report(
    db_path: Path,
    validation_results: Dict,
    output_path: Path
):
    """
    Generate consolidation report JSON
    
    Args:
        db_path: Path to database
        validation_results: Dict with all validation results
        output_path: Path to output JSON file
    """
    report = {
        "timestamp": datetime.now().isoformat(),
        "database": str(db_path),
        "validation_results": validation_results,
        "summary": {
            "all_checks_passed": all(
                validation_results.get(check, {}).get("passed", False)
                for check in ["source_counts", "consensus_confidence", "interview_references", "relationships"]
            )
        }
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n{Colors.BOLD}Report saved to: {output_path}{Colors.END}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Validate Knowledge Graph consolidation"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help=f"Path to database file (default: {DB_PATH})"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPORTS_DIR / "consolidation_report.json",
        help="Path to output report JSON"
    )
    
    args = parser.parse_args()
    
    print_header("KNOWLEDGE GRAPH CONSOLIDATION VALIDATION")
    print(f"Database: {args.db_path}")
    print(f"Report: {args.output}")
    
    # Check if database exists
    if not args.db_path.exists():
        print_error(f"Database not found: {args.db_path}")
        sys.exit(1)
    
    # Connect to database
    db = EnhancedIntelligenceDB(args.db_path)
    db.connect()
    
    # Run validations
    validation_results = {}
    
    # 1. Source counts
    passed, metrics = validate_source_counts(db)
    validation_results["source_counts"] = {"passed": passed, "metrics": metrics}
    
    # 2. Consensus confidence
    passed, metrics = validate_consensus_confidence(db)
    validation_results["consensus_confidence"] = {"passed": passed, "metrics": metrics}
    
    # 3. Interview references
    passed, metrics = validate_interview_references(db)
    validation_results["interview_references"] = {"passed": passed, "metrics": metrics}
    
    # 4. Relationships
    passed, metrics = validate_relationships(db)
    validation_results["relationships"] = {"passed": passed, "metrics": metrics}
    
    # 5. Duplicate reduction
    metrics = calculate_duplicate_reduction(db)
    validation_results["duplicate_reduction"] = {"metrics": metrics}
    
    # 6. Top entities
    top_entities = get_top_entities(db)
    validation_results["top_entities"] = top_entities
    
    # 7. Contradictions
    contradictions = get_contradictions(db)
    validation_results["contradictions"] = contradictions
    
    # Generate report
    generate_report(args.db_path, validation_results, args.output)
    
    # Print summary
    print_header("VALIDATION SUMMARY")
    
    all_passed = all(
        validation_results.get(check, {}).get("passed", False)
        for check in ["source_counts", "consensus_confidence", "interview_references", "relationships"]
    )
    
    if all_passed:
        print_success("All validation checks passed!")
    else:
        print_error("Some validation checks failed. See report for details.")
    
    # Close database
    db.close()
    
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
