#!/usr/bin/env python3
"""
Production Consolidation Script

Runs full consolidation pipeline on extracted interviews:
1. DuplicateDetector - Find similar entities
2. EntityMerger - Merge duplicates
3. RelationshipDiscoverer - Find co-occurrence patterns
4. PatternRecognizer - Identify recurring themes

Outputs to SQLite (later synced to PostgreSQL/Neo4j).
"""
import sys
import os
import json
import time
import argparse
import shutil
import sqlite3
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
    REPORTS_DIR
)

# Backup directory
BACKUP_DIR = Path(__file__).parent.parent / "data" / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"{title}")
    print(f"{'='*70}\n")


def get_entity_counts(db: EnhancedIntelligenceDB) -> dict:
    """Get entity counts from all tables"""
    cursor = db.conn.cursor()

    tables = [
        'pain_points', 'processes', 'systems', 'kpis',
        'automation_candidates', 'inefficiencies',
        'communication_channels', 'decision_points', 'data_flows',
        'temporal_patterns', 'failure_modes',
        'team_structures', 'knowledge_gaps', 'success_patterns',
        'budget_constraints', 'external_dependencies'
    ]

    counts = {}
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cursor.fetchone()[0]
        except:
            counts[table] = 0

    return counts


def get_relationship_count(db: EnhancedIntelligenceDB) -> int:
    """Get relationship count"""
    cursor = db.conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM relationships")
        return cursor.fetchone()[0]
    except:
        return 0


def create_backup(db_path: str) -> str:
    """
    Create timestamped backup of database

    Returns:
        Path to backup file
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    db_name = Path(db_path).stem
    backup_path = BACKUP_DIR / f"{db_name}_pre_consolidation_{timestamp}.db"

    print(f"\n💾 Creating backup...")
    print(f"   Source: {db_path}")
    print(f"   Backup: {backup_path}")

    try:
        shutil.copy2(db_path, backup_path)
        backup_size = os.path.getsize(backup_path) / (1024 * 1024)  # MB
        print(f"   ✓ Backup created ({backup_size:.1f} MB)")
        return str(backup_path)
    except Exception as e:
        print(f"   ❌ Backup failed: {e}")
        raise


def validate_pre_consolidation(db: EnhancedIntelligenceDB) -> tuple[bool, list]:
    """
    Run pre-consolidation validation checks

    Returns:
        (success, issues_found)
    """
    print("\n🔍 Running pre-consolidation validation...")
    cursor = db.conn.cursor()
    issues = []

    # Check 1: Database has interviews
    cursor.execute("SELECT COUNT(*) FROM interviews")
    interview_count = cursor.fetchone()[0]
    if interview_count == 0:
        issues.append("No interviews found in database")
    else:
        print(f"   ✓ Found {interview_count} interviews")

    # Check 2: Database has extractable entities
    cursor.execute("SELECT COUNT(*) FROM pain_points")
    entity_count = cursor.fetchone()[0]
    if entity_count == 0:
        issues.append("No entities found - run extraction first")
    else:
        print(f"   ✓ Found {entity_count} pain_points")

    # Check 3: No null interview IDs
    cursor.execute("SELECT COUNT(*) FROM pain_points WHERE interview_id IS NULL")
    null_interviews = cursor.fetchone()[0]
    if null_interviews > 0:
        issues.append(f"Found {null_interviews} entities with NULL interview_id")
        print(f"   ⚠️  Warning: {null_interviews} entities missing interview_id")
    else:
        print(f"   ✓ All entities have interview_id")

    # Check 4: Required tables exist
    required_tables = ['interviews', 'pain_points', 'processes', 'systems']
    for table in required_tables:
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
        if not cursor.fetchone():
            issues.append(f"Required table '{table}' not found")
        else:
            print(f"   ✓ Table '{table}' exists")

    success = len(issues) == 0
    if not success:
        print("\n❌ Pre-consolidation validation FAILED:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   ✓ All pre-consolidation checks passed")

    return success, issues


def validate_post_consolidation(db: EnhancedIntelligenceDB, counts_before: dict) -> tuple[bool, list]:
    """
    Run post-consolidation validation checks

    Returns:
        (success, issues_found)
    """
    print("\n🔍 Running post-consolidation validation...")
    cursor = db.conn.cursor()
    issues = []

    # Check 1: Entities weren't accidentally deleted (should only reduce, not disappear)
    counts_after = get_entity_counts(db)
    total_before = sum(counts_before.values())
    total_after = sum(counts_after.values())

    if total_after > total_before:
        issues.append(f"Entity count INCREASED ({total_before} → {total_after}) - unexpected!")
    elif total_after == 0:
        issues.append("All entities were deleted - CRITICAL ERROR!")
    else:
        reduction_pct = ((total_before - total_after) / total_before * 100) if total_before > 0 else 0
        print(f"   ✓ Entity reduction: {reduction_pct:.1f}% ({total_before} → {total_after})")

    # Check 2: All consolidated entities have valid source_count (if column exists)
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE source_count IS NULL OR source_count < 1
        """)
        invalid_sources = cursor.fetchone()[0]
        if invalid_sources > 0:
            issues.append(f"Found {invalid_sources} entities with invalid source_count")
        else:
            print(f"   ✓ All entities have valid source_count")
    except sqlite3.OperationalError:
        # Column doesn't exist - consolidation may not add it to all tables
        print(f"   ⚠️  Note: source_count column not found (may be expected)")

    # Check 3: All consolidated entities have valid consensus_confidence (if column exists)
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE consensus_confidence IS NULL
               OR consensus_confidence < 0.0
               OR consensus_confidence > 1.0
        """)
        invalid_confidence = cursor.fetchone()[0]
        if invalid_confidence > 0:
            issues.append(f"Found {invalid_confidence} entities with invalid consensus_confidence")
        else:
            print(f"   ✓ All entities have valid consensus_confidence")
    except sqlite3.OperationalError:
        # Column doesn't exist - consolidation may not add it to all tables
        print(f"   ⚠️  Note: consensus_confidence column not found (may be expected)")

    # Check 4: Relationships were created
    rel_count = get_relationship_count(db)
    if rel_count == 0:
        print(f"   ⚠️  Warning: No relationships discovered")
    else:
        print(f"   ✓ Created {rel_count} relationships")

    success = len(issues) == 0
    if not success:
        print("\n❌ Post-consolidation validation FAILED:")
        for issue in issues:
            print(f"   - {issue}")
    else:
        print("   ✓ All post-consolidation checks passed")

    return success, issues


def confirm_consolidation(total_interviews: int, total_entities: int, backup_path: str) -> bool:
    """
    Ask user to confirm consolidation run

    Returns:
        True if user confirms, False otherwise
    """
    print("\n" + "="*70)
    print("⚠️  CONSOLIDATION CONFIRMATION")
    print("="*70)
    print(f"\nAbout to consolidate:")
    print(f"  - {total_interviews} interviews")
    print(f"  - {total_entities:,} entities")
    print(f"\nBackup created at:")
    print(f"  {backup_path}")
    print(f"\nThis will:")
    print(f"  ✓ Merge duplicate entities")
    print(f"  ✓ Update source_count and consensus_confidence")
    print(f"  ✓ Create relationship mappings")
    print(f"  ✓ Modify database in-place")
    print("\n" + "="*70)

    response = input("\nProceed with consolidation? [y/N]: ").strip().lower()
    return response in ['y', 'yes']


def run_consolidation(db_path: str = None, verbose: bool = False, dry_run: bool = False,
                     skip_backup: bool = False, skip_confirmation: bool = False):
    """
    Run consolidation on all interviews in database

    Args:
        db_path: Path to SQLite database (default: data/full_intelligence.db)
        verbose: Print detailed progress
        dry_run: Preview changes without modifying database
        skip_backup: Skip automatic backup (NOT RECOMMENDED)
        skip_confirmation: Skip confirmation prompt (use with caution)
    """
    print_section("PRODUCTION CONSOLIDATION" + (" [DRY RUN]" if dry_run else ""))

    # Use default database path if not specified
    if db_path is None:
        db_path = DB_PATH

    print(f"📂 Database: {db_path}")

    # Check database exists
    if not os.path.exists(db_path):
        print(f"❌ ERROR: Database not found at {db_path}")
        print("   Run extraction first: python3 intelligence_capture/run.py")
        sys.exit(1)

    # Create backup (unless explicitly skipped or dry-run)
    backup_path = None
    if not dry_run and not skip_backup:
        try:
            backup_path = create_backup(db_path)
        except Exception as e:
            print(f"\n❌ FATAL: Backup failed - {e}")
            print("   Aborting consolidation for data safety")
            print("   Use --skip-backup to override (NOT RECOMMENDED)")
            sys.exit(1)
    elif dry_run:
        print("\n💾 Backup skipped (dry-run mode)")
    else:
        print("\n⚠️  WARNING: Backup skipped (--skip-backup flag)")

    # Load configuration
    print("\n📋 Loading consolidation configuration...")
    config = load_consolidation_config()
    print("   ✓ Configuration loaded")

    # Connect to database
    print("\n📂 Connecting to database...")
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    print("   ✓ Database connected")

    # Run pre-consolidation validation
    validation_ok, validation_issues = validate_pre_consolidation(db)
    if not validation_ok:
        print("\n❌ FATAL: Pre-consolidation validation failed")
        db.close()
        sys.exit(1)

    # Check interviews
    cursor = db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM interviews")
    total_interviews = cursor.fetchone()[0]

    print(f"\n📊 Database statistics:")
    print(f"   Interviews: {total_interviews}")

    # Get entity counts before
    counts_before = get_entity_counts(db)
    total_before = sum(counts_before.values())
    print(f"   Total entities: {total_before:,}")

    if verbose:
        for entity_type, count in counts_before.items():
            if count > 0:
                print(f"   - {entity_type}: {count:,}")

    # Dry-run mode - show what would happen and exit
    if dry_run:
        print("\n" + "="*70)
        print("DRY RUN MODE - Preview Only")
        print("="*70)
        print("\nWould consolidate:")
        print(f"  - {total_interviews} interviews")
        print(f"  - {total_before:,} entities")
        print(f"\nExpected reduction: 70-90%")
        print(f"Expected output: ~{int(total_before * 0.25)}-{int(total_before * 0.30)} consolidated entities")
        print(f"\nNo changes made to database.")
        print("\nTo run for real:")
        print(f"  python3 scripts/run_consolidation.py")
        db.close()
        return

    # Confirmation prompt (unless skipped)
    if not skip_confirmation:
        if not confirm_consolidation(total_interviews, total_before, backup_path or "None"):
            print("\n⚠️  Consolidation cancelled by user")
            db.close()
            sys.exit(0)

    # Initialize consolidation agent
    print("\n🔗 Initializing consolidation agent...")
    agent = KnowledgeConsolidationAgent(
        db=db,
        config=config,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    print("   ✓ Agent initialized")

    # Get all interviews
    cursor.execute("SELECT id, company, respondent FROM interviews ORDER BY id")
    interviews = cursor.fetchall()

    print(f"\n🚀 Running consolidation on {len(interviews)} interviews...")
    print(f"   Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Entity types to consolidate
    entity_types = [
        'pain_points', 'processes', 'systems', 'kpis',
        'automation_candidates', 'inefficiencies',
        'communication_channels', 'decision_points', 'data_flows',
        'temporal_patterns', 'failure_modes',
        'team_structures', 'knowledge_gaps', 'success_patterns',
        'budget_constraints', 'external_dependencies'
    ]

    # Run consolidation
    start_time = time.time()
    processed = 0
    failed = 0

    try:
        # Process each interview
        for interview_id, company, respondent in interviews:
            try:
                if verbose:
                    print(f"\n  Processing interview {interview_id}: {company} - {respondent}")

                # Get entities for this interview
                entities = {}

                for entity_type in entity_types:
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
                    except Exception as e:
                        if verbose:
                            print(f"    Warning: Could not get {entity_type}: {e}")
                        pass

                if not entities:
                    if verbose:
                        print(f"    No entities found for interview {interview_id}")
                    continue

                # Consolidate entities for this interview
                consolidated = agent.consolidate_entities(entities, interview_id)

                processed += 1
                if verbose:
                    total_entities = sum(len(e) for e in entities.values())
                    print(f"    ✓ Consolidated {total_entities} entities")

            except Exception as e:
                failed += 1
                print(f"    ❌ Failed to process interview {interview_id}: {e}")
                if verbose:
                    import traceback
                    traceback.print_exc()

        duration = time.time() - start_time

        print(f"\n✅ Processing complete:")
        print(f"   Processed: {processed}/{len(interviews)} interviews")
        if failed > 0:
            print(f"   ⚠️  Failed: {failed} interviews")

        print(f"   ✓ Completed in {duration:.2f}s ({duration/60:.1f} minutes)")

        # Run post-consolidation validation
        validation_ok, validation_issues = validate_post_consolidation(db, counts_before)
        if not validation_ok:
            print("\n❌ ERROR: Post-consolidation validation failed!")
            print(f"\n💾 Restore from backup:")
            print(f"   cp {backup_path} {db_path}")
            db.close()
            sys.exit(1)

        # Get entity counts after
        print("\n📊 Entity counts AFTER consolidation:")
        counts_after = get_entity_counts(db)
        total_after = sum(counts_after.values())
        print(f"   Total entities: {total_after:,}")

        if verbose:
            for entity_type, count in counts_after.items():
                if count > 0:
                    before = counts_before.get(entity_type, 0)
                    change = count - before
                    symbol = "+" if change > 0 else ""
                    print(f"   - {entity_type}: {count:,} ({symbol}{change})")

        # Calculate reduction
        entities_removed = total_before - total_after
        reduction_pct = (entities_removed / total_before * 100) if total_before > 0 else 0

        print(f"\n🎯 Consolidation results:")
        print(f"   Entities before: {total_before:,}")
        print(f"   Entities after:  {total_after:,}")
        print(f"   Removed:         {entities_removed:,}")
        print(f"   Reduction:       {reduction_pct:.1f}%")

        # Get relationship count
        rel_count = get_relationship_count(db)
        print(f"   Relationships:   {rel_count:,}")

        # Get agent statistics
        print("\n📊 Consolidation statistics:")
        stats = agent.get_statistics()
        print(f"   Entities processed: {stats.get('entities_processed', 0):,}")
        print(f"   Duplicates found: {stats.get('duplicates_found', 0):,}")
        print(f"   Entities merged: {stats.get('entities_merged', 0):,}")

        # Run pattern recognition
        print("\n🔍 Running pattern recognition...")
        pattern_recognizer = PatternRecognizer(db, config)
        patterns = pattern_recognizer.identify_patterns()
        print(f"   ✓ Identified {len(patterns)} patterns")

        if verbose and patterns:
            print("\n   Top patterns:")
            for i, pattern in enumerate(patterns[:5], 1):
                print(f"   {i}. {pattern.get('pattern_type', 'unknown')}: {pattern.get('description', 'N/A')}")

        # Save report
        report_path = REPORTS_DIR / f"consolidation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "database": str(db_path),
            "interviews_total": total_interviews,
            "interviews_processed": processed,
            "interviews_failed": failed,
            "duration_seconds": duration,
            "entities_before": total_before,
            "entities_after": total_after,
            "entities_removed": entities_removed,
            "reduction_percentage": reduction_pct,
            "relationships_discovered": rel_count,
            "patterns_identified": len(patterns),
            "agent_statistics": stats,
            "entity_counts_before": counts_before,
            "entity_counts_after": counts_after,
            "patterns": patterns
        }

        # Add backup info to report
        report_data["backup_path"] = backup_path
        report_data["validation_passed"] = True

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

        print(f"\n📄 Report saved: {report_path}")

        print_section("✅ CONSOLIDATION COMPLETE")

        print("\n📋 Summary:")
        print(f"   Interviews:      {processed}/{total_interviews} processed")
        if failed > 0:
            print(f"   ⚠️  Failed:      {failed}")
        print(f"   Duration:        {duration/60:.1f} minutes")
        print(f"   Reduction:       {reduction_pct:.1f}%")
        print(f"   Relationships:   {rel_count:,}")
        print(f"   Patterns:        {len(patterns)}")
        print(f"   Duplicates:      {stats.get('duplicates_found', 0):,} found")

        if backup_path:
            print(f"\n💾 Backup location:")
            print(f"   {backup_path}")

        print("\n🎯 Next step:")
        print("   Sync to PostgreSQL/Neo4j:")
        print("   python3 scripts/sync_consolidated_to_neo4j.py")

    except Exception as e:
        print(f"\n❌ ERROR during consolidation:")
        print(f"   {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        db.close()
        sys.exit(1)

    # Close database
    db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run production consolidation on extracted interviews",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run consolidation on default database
  python3 scripts/run_consolidation.py

  # Run with verbose output
  python3 scripts/run_consolidation.py --verbose

  # Run on specific database
  python3 scripts/run_consolidation.py --db data/pilot_intelligence.db
        """
    )
    parser.add_argument(
        "--db",
        type=str,
        help="Path to SQLite database (default: data/full_intelligence.db)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed progress and entity counts"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would happen without making changes"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip automatic backup (NOT RECOMMENDED - use only for testing)"
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (use with caution)"
    )

    args = parser.parse_args()

    try:
        run_consolidation(
            db_path=args.db,
            verbose=args.verbose,
            dry_run=args.dry_run,
            skip_backup=args.skip_backup,
            skip_confirmation=args.yes
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(130)


if __name__ == "__main__":
    main()
