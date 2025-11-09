#!/usr/bin/env python3
"""
Rollback Consolidation Script

Rolls back a consolidation operation using entity snapshots.
Restores original entities and updates relationships.

Usage:
    python scripts/rollback_consolidation.py --audit-id 123 --reason "Incorrect merge"
    python scripts/rollback_consolidation.py --list  # List recent consolidations
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH


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


def list_consolidations(db: EnhancedIntelligenceDB, limit: int = 20):
    """
    List recent consolidation operations
    
    Args:
        db: Database instance
        limit: Number of records to show
    """
    print_header("RECENT CONSOLIDATION OPERATIONS")
    
    cursor = db.conn.cursor()
    
    cursor.execute("""
        SELECT 
            id,
            entity_type,
            merged_entity_ids,
            resulting_entity_id,
            similarity_score,
            consolidation_timestamp,
            rollback_timestamp,
            rollback_reason
        FROM consolidation_audit
        ORDER BY consolidation_timestamp DESC
        LIMIT ?
    """, (limit,))
    
    records = cursor.fetchall()
    
    if not records:
        print_warning("No consolidation records found")
        return
    
    print(f"Found {len(records)} consolidation operations:\n")
    
    for record in records:
        audit_id, entity_type, merged_ids, result_id, similarity, timestamp, rollback_ts, rollback_reason = record
        
        status = "ROLLED BACK" if rollback_ts else "ACTIVE"
        status_color = Colors.YELLOW if rollback_ts else Colors.GREEN
        
        print(f"{Colors.BOLD}Audit ID: {audit_id}{Colors.END} [{status_color}{status}{Colors.END}]")
        print_info(f"Entity Type: {entity_type}")
        print_info(f"Merged IDs: {merged_ids}")
        print_info(f"Result ID: {result_id}")
        print_info(f"Similarity: {similarity:.3f}")
        print_info(f"Timestamp: {timestamp}")
        
        if rollback_ts:
            print_info(f"Rolled back: {rollback_ts}")
            print_info(f"Reason: {rollback_reason}")
        
        print()


def rollback_consolidation(
    db: EnhancedIntelligenceDB,
    audit_id: int,
    reason: str,
    confirm: bool = True
):
    """
    Rollback a consolidation operation
    
    Args:
        db: Database instance
        audit_id: Audit record ID to rollback
        reason: Reason for rollback
        confirm: Require user confirmation
    """
    print_header(f"ROLLBACK CONSOLIDATION #{audit_id}")
    
    cursor = db.conn.cursor()
    
    # Get audit record details
    cursor.execute("""
        SELECT 
            entity_type,
            merged_entity_ids,
            resulting_entity_id,
            similarity_score,
            consolidation_timestamp,
            rollback_timestamp
        FROM consolidation_audit
        WHERE id = ?
    """, (audit_id,))
    
    record = cursor.fetchone()
    
    if not record:
        print_error(f"Audit record {audit_id} not found")
        return False
    
    entity_type, merged_ids, result_id, similarity, timestamp, rollback_ts = record
    
    if rollback_ts:
        print_error(f"Consolidation {audit_id} has already been rolled back")
        return False
    
    # Display consolidation details
    print("Consolidation Details:")
    print_info(f"Entity Type: {entity_type}")
    print_info(f"Merged IDs: {merged_ids}")
    print_info(f"Result ID: {result_id}")
    print_info(f"Similarity: {similarity:.3f}")
    print_info(f"Timestamp: {timestamp}")
    print_info(f"Reason: {reason}")
    
    # Check if snapshots exist
    cursor.execute("""
        SELECT COUNT(*) FROM entity_snapshots
        WHERE audit_id = ?
    """, (audit_id,))
    
    snapshot_count = cursor.fetchone()[0]
    
    if snapshot_count == 0:
        print_error("No entity snapshots found for this consolidation")
        print_warning("Cannot rollback without snapshots")
        return False
    
    print_info(f"Found {snapshot_count} entity snapshots")
    
    # Confirm rollback
    if confirm:
        print(f"\n{Colors.YELLOW}⚠️  This will restore original entities and may affect relationships{Colors.END}")
        response = input(f"\n{Colors.BOLD}Proceed with rollback? (yes/no): {Colors.END}")
        
        if response.lower() not in ['yes', 'y']:
            print_warning("Rollback cancelled")
            return False
    
    # Perform rollback
    print("\n🔄 Rolling back consolidation...")
    
    success = db.rollback_consolidation(audit_id, reason)
    
    if success:
        print_success("Rollback completed successfully")
        
        # Verify rollback
        cursor.execute("""
            SELECT rollback_timestamp, rollback_reason
            FROM consolidation_audit
            WHERE id = ?
        """, (audit_id,))
        
        rollback_ts, rollback_reason = cursor.fetchone()
        print_info(f"Rolled back at: {rollback_ts}")
        print_info(f"Reason: {rollback_reason}")
        
        return True
    else:
        print_error("Rollback failed")
        return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Rollback consolidation operations"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List recent consolidation operations"
    )
    
    parser.add_argument(
        "--audit-id",
        type=int,
        help="Audit record ID to rollback"
    )
    
    parser.add_argument(
        "--reason",
        type=str,
        help="Reason for rollback"
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(DB_PATH),
        help=f"Database path (default: {DB_PATH})"
    )
    
    parser.add_argument(
        "--no-confirm",
        action="store_true",
        help="Skip confirmation prompt"
    )
    
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Number of records to show when listing (default: 20)"
    )
    
    args = parser.parse_args()
    
    # Connect to database
    db = EnhancedIntelligenceDB(args.db_path)
    db.connect()
    
    # Ensure entity_snapshots table exists
    db.create_entity_snapshots_table()
    
    try:
        if args.list:
            # List consolidations
            list_consolidations(db, args.limit)
        
        elif args.audit_id:
            # Rollback consolidation
            if not args.reason:
                print_error("--reason is required for rollback")
                sys.exit(1)
            
            success = rollback_consolidation(
                db,
                args.audit_id,
                args.reason,
                confirm=not args.no_confirm
            )
            
            sys.exit(0 if success else 1)
        
        else:
            parser.print_help()
            sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
