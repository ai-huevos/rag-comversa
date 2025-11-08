"""
Migration Script: Add Ensemble Review Fields to Existing Database
Run this to add ensemble validation tracking fields to an existing intelligence.db
"""
import sys
from pathlib import Path
from database import IntelligenceDB, EnhancedIntelligenceDB
from config import DB_PATH


def migrate_database(db_path: Path = DB_PATH):
    """
    Add ensemble review fields to existing database

    This migration:
    1. Connects to existing database
    2. Adds review tracking fields to all entity tables
    3. Preserves all existing data
    4. Is idempotent (safe to run multiple times)
    """
    print("=" * 60)
    print("ENSEMBLE REVIEW FIELDS MIGRATION")
    print("=" * 60)
    print(f"Database: {db_path}")
    print()

    # Check if database exists
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print(f"   Run the main processor first to create the database")
        return False

    # Connect to database
    print("📂 Connecting to database...")
    db = EnhancedIntelligenceDB(db_path)
    db.connect()

    # Run migration
    try:
        print("\n🔧 Adding ensemble review fields...")
        db.add_ensemble_review_fields()

        print("\n✅ Migration completed successfully!")
        print()
        print("Next steps:")
        print("1. Set ENABLE_ENSEMBLE_REVIEW=true in your .env file")
        print("2. Set ENSEMBLE_MODE=basic or full in your .env file")
        print("3. Optionally add ANTHROPIC_API_KEY for Claude synthesis")
        print("4. Run processor to start using ensemble validation")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    # Allow custom database path via command line
    if len(sys.argv) > 1:
        db_path = Path(sys.argv[1])
    else:
        db_path = DB_PATH

    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
