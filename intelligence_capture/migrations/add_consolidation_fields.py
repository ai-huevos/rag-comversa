#!/usr/bin/env python3
"""
Migration: Add Knowledge Graph Consolidation Fields

This migration adds consolidation tracking columns to all entity tables
and creates new tables for relationships, audit trail, and pattern recognition.

Enables:
- Duplicate entity detection and merging
- Source tracking across interviews
- Consensus confidence scoring
- Relationship discovery between entities
- Pattern recognition across interviews

Usage:
    python3 intelligence_capture/migrations/add_consolidation_fields.py
    python3 intelligence_capture/migrations/add_consolidation_fields.py --db-path data/pilot_intelligence.db
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH


def backup_database(db_path: Path) -> Path:
    """
    Create a backup of the database before migration
    
    Args:
        db_path: Path to database file
        
    Returns:
        Path to backup file
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Database not found: {db_path}")
    
    # Create backup with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = db_path.parent / f"{db_path.stem}_backup_{timestamp}{db_path.suffix}"
    
    print(f"📦 Creating backup: {backup_path.name}")
    shutil.copy2(db_path, backup_path)
    print(f"   ✓ Backup created successfully")
    
    return backup_path


def validate_migration(db: EnhancedIntelligenceDB) -> bool:
    """
    Validate that migration was successful
    
    Args:
        db: Database instance
        
    Returns:
        True if validation passes, False otherwise
    """
    print("\n🔍 Validating migration...")
    cursor = db.conn.cursor()
    
    # Check that consolidation fields were added to entity tables
    entity_tables = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    required_fields = [
        "mentioned_in_interviews", "source_count", "consensus_confidence",
        "is_consolidated", "has_contradictions", "consolidated_at"
    ]
    
    for table in entity_tables:
        # Check if table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            continue  # Skip tables that don't exist
        
        # Check columns
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in cursor.fetchall()]
        
        for field in required_fields:
            if field not in columns:
                print(f"   ❌ Missing field {field} in {table}")
                return False
    
    # Check that new tables were created
    new_tables = ["relationships", "consolidation_audit", "patterns"]
    for table in new_tables:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        if not cursor.fetchone():
            print(f"   ❌ Missing table {table}")
            return False
    
    # Check that indexes were created
    required_indexes = [
        "idx_relationships_source",
        "idx_relationships_target",
        "idx_audit_entity_type",
        "idx_patterns_type"
    ]
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = [row[0] for row in cursor.fetchall()]
    
    for index in required_indexes:
        if index not in indexes:
            print(f"   ⚠️  Missing index {index} (non-critical)")
    
    print("   ✓ All validation checks passed")
    return True


def run_migration(db_path: Path = DB_PATH, skip_backup: bool = False):
    """
    Run the consolidation fields migration
    
    Args:
        db_path: Path to database file
        skip_backup: Skip backup creation (for testing only)
    """
    print("=" * 70)
    print("KNOWLEDGE GRAPH CONSOLIDATION MIGRATION")
    print("=" * 70)
    print(f"Database: {db_path}")
    print()
    
    # Check if database exists
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print(f"   Run the extraction pipeline first to create the database")
        return False
    
    # Create backup
    if not skip_backup:
        try:
            backup_path = backup_database(db_path)
            print(f"   Backup location: {backup_path}")
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            print(f"   Migration aborted for safety")
            return False
    else:
        print("⚠️  Skipping backup (testing mode)")
    
    # Connect to database
    print("\n📂 Connecting to database...")
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    
    # Run migration
    try:
        print("\n🔧 Running migration...")
        db.add_consolidation_schema()
        
        # Validate migration
        if not validate_migration(db):
            print("\n❌ Migration validation failed")
            print(f"   Database may be in inconsistent state")
            print(f"   Restore from backup: {backup_path if not skip_backup else 'N/A'}")
            return False
        
        print("\n✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Create config/consolidation_config.json with similarity thresholds")
        print("2. Implement consolidation agent for duplicate detection")
        print("3. Run consolidation on existing data")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        
        if not skip_backup:
            print(f"\n⚠️  Restore from backup: {backup_path}")
            print(f"   cp {backup_path} {db_path}")
        
        return False
        
    finally:
        db.close()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Add Knowledge Graph consolidation fields to database"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help=f"Path to database file (default: {DB_PATH})"
    )
    parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup creation (for testing only)"
    )
    
    args = parser.parse_args()
    
    success = run_migration(args.db_path, args.skip_backup)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
