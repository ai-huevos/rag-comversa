#!/usr/bin/env python3
"""
PostgreSQL Migration Runner for RAG 2.0
Executes migration scripts in order and tracks migration history

Usage:
    python scripts/run_pg_migrations.py                    # Run all pending migrations
    python scripts/run_pg_migrations.py --rollback YYYYMMDD # Rollback specific migration
    python scripts/run_pg_migrations.py --status           # Show migration status
    python scripts/run_pg_migrations.py --dry-run          # Preview migrations without executing

Author: storage_graph agent
Created: 2025-11-09
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import psycopg2
from psycopg2 import sql
import argparse

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class MigrationRunner:
    """PostgreSQL migration runner with history tracking"""

    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize migration runner

        Args:
            database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        """
        self.database_url = database_url or os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Example: postgresql://user:pass@host:5432/dbname"
            )

        self.migrations_dir = Path(__file__).parent / 'migrations'
        self.rollback_dir = self.migrations_dir / 'rollback'
        self.conn = None

    def connect(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = False  # Use transactions
            print(f"✓ Connected to PostgreSQL database")
        except Exception as e:
            raise ConnectionError(f"Failed to connect to database: {e}")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")

    def ensure_migration_table(self):
        """Create migration history table if not exists"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migration_history (
            id SERIAL PRIMARY KEY,
            migration_name VARCHAR(255) NOT NULL UNIQUE,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rollback_available BOOLEAN DEFAULT TRUE,
            checksum VARCHAR(64),
            execution_time_seconds FLOAT
        );

        CREATE INDEX IF NOT EXISTS idx_migration_name ON migration_history(migration_name);
        CREATE INDEX IF NOT EXISTS idx_applied_at ON migration_history(applied_at DESC);
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                self.conn.commit()
                print("✓ Migration history table ready")
        except Exception as e:
            self.conn.rollback()
            raise RuntimeError(f"Failed to create migration history table: {e}")

    def get_applied_migrations(self) -> List[str]:
        """Get list of already applied migrations"""
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT migration_name FROM migration_history ORDER BY applied_at"
                )
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            raise RuntimeError(f"Failed to query migration history: {e}")

    def get_pending_migrations(self) -> List[Path]:
        """Get list of pending migration files"""
        applied = set(self.get_applied_migrations())

        # Find all .sql files in migrations directory (excluding rollback subdirectory)
        all_migrations = sorted(
            [f for f in self.migrations_dir.glob('*.sql')],
            key=lambda x: x.name
        )

        # Filter to pending only
        pending = [m for m in all_migrations if m.stem not in applied]

        return pending

    def execute_migration(self, migration_file: Path, dry_run: bool = False) -> bool:
        """
        Execute a single migration file

        Args:
            migration_file: Path to migration SQL file
            dry_run: If True, only preview without executing

        Returns:
            True if successful, False otherwise
        """
        migration_name = migration_file.stem

        print(f"\n{'='*70}")
        print(f"Migration: {migration_name}")
        print(f"File: {migration_file.name}")
        print(f"{'='*70}")

        # Read migration SQL
        try:
            sql_content = migration_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"✗ Failed to read migration file: {e}")
            return False

        if dry_run:
            print("📋 DRY RUN - Migration SQL Preview:")
            print(f"\n{sql_content[:500]}...\n")
            print("✓ Dry run complete (no changes made)")
            return True

        # Execute migration
        try:
            start_time = datetime.now()

            with self.conn.cursor() as cursor:
                cursor.execute(sql_content)

            # Record in migration history
            execution_time = (datetime.now() - start_time).total_seconds()

            with self.conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO migration_history (migration_name, execution_time_seconds)
                    VALUES (%s, %s)
                    """,
                    (migration_name, execution_time)
                )

            self.conn.commit()

            print(f"✓ Migration applied successfully in {execution_time:.2f}s")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"✗ Migration failed: {e}")
            return False

    def rollback_migration(self, migration_name: str, dry_run: bool = False) -> bool:
        """
        Rollback a specific migration

        Args:
            migration_name: Name of migration to rollback (e.g., "2025_01_01_ingestion_queue")
            dry_run: If True, only preview without executing

        Returns:
            True if successful, False otherwise
        """
        rollback_file = self.rollback_dir / f"{migration_name}_rollback.sql"

        if not rollback_file.exists():
            print(f"✗ Rollback script not found: {rollback_file}")
            return False

        print(f"\n{'='*70}")
        print(f"Rollback: {migration_name}")
        print(f"File: {rollback_file.name}")
        print(f"{'='*70}")

        # Read rollback SQL
        try:
            sql_content = rollback_file.read_text(encoding='utf-8')
        except Exception as e:
            print(f"✗ Failed to read rollback file: {e}")
            return False

        if dry_run:
            print("📋 DRY RUN - Rollback SQL Preview:")
            print(f"\n{sql_content[:500]}...\n")
            print("✓ Dry run complete (no changes made)")
            return True

        # Execute rollback
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql_content)

            # Remove from migration history
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM migration_history WHERE migration_name = %s",
                    (migration_name,)
                )

            self.conn.commit()

            print(f"✓ Migration rolled back successfully")
            return True

        except Exception as e:
            self.conn.rollback()
            print(f"✗ Rollback failed: {e}")
            return False

    def show_status(self):
        """Display migration status"""
        applied = self.get_applied_migrations()
        pending = self.get_pending_migrations()

        print(f"\n{'='*70}")
        print("MIGRATION STATUS")
        print(f"{'='*70}")

        print(f"\n✓ Applied Migrations ({len(applied)}):")
        if applied:
            for migration in applied:
                print(f"  - {migration}")
        else:
            print("  (none)")

        print(f"\n⏳ Pending Migrations ({len(pending)}):")
        if pending:
            for migration_file in pending:
                print(f"  - {migration_file.stem}")
        else:
            print("  (none)")

        # Check rollback availability
        print(f"\n🔄 Rollback Scripts Available:")
        rollback_files = sorted(self.rollback_dir.glob('*_rollback.sql'))
        if rollback_files:
            for rollback_file in rollback_files:
                migration_name = rollback_file.stem.replace('_rollback', '')
                is_applied = migration_name in applied
                status = "✓ (applied)" if is_applied else "⊗ (not applied)"
                print(f"  - {migration_name} {status}")
        else:
            print("  (none)")

    def run_all_pending(self, dry_run: bool = False):
        """Run all pending migrations"""
        pending = self.get_pending_migrations()

        if not pending:
            print("\n✓ No pending migrations - database is up to date")
            return True

        print(f"\n📋 Found {len(pending)} pending migration(s)")

        success_count = 0
        for migration_file in pending:
            if self.execute_migration(migration_file, dry_run=dry_run):
                success_count += 1
            else:
                print(f"\n✗ Migration failed, stopping execution")
                break

        if not dry_run:
            print(f"\n{'='*70}")
            print(f"MIGRATION SUMMARY")
            print(f"{'='*70}")
            print(f"✓ Successful: {success_count}/{len(pending)}")
            print(f"✗ Failed: {len(pending) - success_count}/{len(pending)}")

        return success_count == len(pending)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='PostgreSQL Migration Runner for RAG 2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_pg_migrations.py                           # Run all pending
  python scripts/run_pg_migrations.py --status                  # Show status
  python scripts/run_pg_migrations.py --dry-run                 # Preview migrations
  python scripts/run_pg_migrations.py --rollback 2025_01_01_ingestion_queue
        """
    )

    parser.add_argument(
        '--status',
        action='store_true',
        help='Show migration status (applied vs pending)'
    )

    parser.add_argument(
        '--rollback',
        metavar='MIGRATION_NAME',
        help='Rollback specific migration (e.g., 2025_01_01_ingestion_queue)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview migrations without executing'
    )

    parser.add_argument(
        '--database-url',
        help='PostgreSQL connection string (defaults to DATABASE_URL env var)'
    )

    args = parser.parse_args()

    # Initialize runner
    try:
        runner = MigrationRunner(database_url=args.database_url)
        runner.connect()
        runner.ensure_migration_table()

        # Execute requested action
        if args.status:
            runner.show_status()
        elif args.rollback:
            success = runner.rollback_migration(args.rollback, dry_run=args.dry_run)
            sys.exit(0 if success else 1)
        else:
            success = runner.run_all_pending(dry_run=args.dry_run)
            sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
    finally:
        if runner and runner.conn:
            runner.close()


if __name__ == '__main__':
    main()
