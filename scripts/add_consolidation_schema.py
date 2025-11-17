#!/usr/bin/env python3
"""
Add Consolidation Schema to SQLite Database

Adds consolidation tracking fields to all entity tables:
- source_count
- consensus_confidence
- is_consolidated
- has_contradictions
- And creates relationships, audit tables

Run this BEFORE running consolidation for the first time.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH

def main():
    """Add consolidation schema to database"""
    print("="*70)
    print("ADD CONSOLIDATION SCHEMA TO SQLITE")
    print("="*70)

    print(f"\n📂 Database: {DB_PATH}")

    # Connect to database
    print("\n📂 Connecting to database...")
    db = EnhancedIntelligenceDB(DB_PATH)
    db.connect()
    print("   ✓ Connected")

    # Add consolidation schema
    print("\n🔗 Adding consolidation schema...")
    try:
        db.add_consolidation_schema()

        print("\n" + "="*70)
        print("✅ CONSOLIDATION SCHEMA ADDED SUCCESSFULLY")
        print("="*70)

        print("\n📋 What was added:")
        print("   ✓ Consolidation tracking columns to all 16 entity tables")
        print("   ✓ relationships table")
        print("   ✓ consolidation_audit table")
        print("   ✓ patterns table")
        print("   ✓ All necessary indexes")

        print("\n🎯 Next step:")
        print("   python3 scripts/run_consolidation.py --verbose")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
