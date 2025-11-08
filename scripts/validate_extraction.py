#!/usr/bin/env python3
"""
Comprehensive validation script for extraction results
Checks completeness, quality, and referential integrity
Generates detailed validation report
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import IntelligenceDB
from intelligence_capture.config import DB_PATH


class ExtractionValidator:
    """Validates extraction results for completeness and quality"""

    def __init__(self, db_path: Path = DB_PATH):
        self.db = IntelligenceDB(db_path)
        self.db.connect()
        self.results = {
            "completeness": {},
            "quality": {},
            "integrity": {},
            "summary": {}
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """Run all validation checks"""
        print(f"\n{'='*70}")
        print(f"🔍 EXTRACTION VALIDATION REPORT")
        print(f"{'='*70}")
        print(f"Database: {self.db.db_path}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"{'='*70}\n")

        # Run completeness checks
        print("🔎 Running completeness checks...")
        self.check_entity_counts()
        self.check_interview_coverage()

        # Run quality checks
        print("\n✅ Running quality checks...")
        self.check_data_quality()

        # Run integrity checks
        print("\n🔗 Running referential integrity checks...")
        self.check_referential_integrity()

        # Generate summary
        self.generate_summary()

        return self.results

    def check_entity_counts(self):
        """Check entity counts for all 17 types"""
        cursor = self.db.conn.cursor()

        # Define all entity types
        entity_tables = {
            # v1.0 entities
            "pain_points": "Pain Points",
            "processes": "Processes",
            "systems": "Systems",
            "kpis": "KPIs",
            "automation_candidates": "Automation Candidates",
            "inefficiencies": "Inefficiencies",

            # v2.0 entities
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

            # Enhanced v1.0 entities
            "enhanced_pain_points": "Enhanced Pain Points",
        }

        counts = {}
        missing_types = []

        print(f"\n  Entity Counts:")
        print(f"  {'-'*60}")

        for table, display_name in entity_tables.items():
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                counts[table] = count

                status = "✓" if count > 0 else "✗"
                print(f"  {status} {display_name:30s}: {count:4d}")

                if count == 0:
                    missing_types.append(display_name)
            except Exception as e:
                # Table might not exist
                counts[table] = 0
                print(f"  ⚠ {display_name:30s}: Table not found")
                missing_types.append(display_name)

        self.results["completeness"]["entity_counts"] = counts
        self.results["completeness"]["missing_types"] = missing_types
        self.results["completeness"]["total_entities"] = sum(counts.values())

        print(f"  {'-'*60}")
        print(f"  Total entities: {sum(counts.values())}")

        if missing_types:
            print(f"\n  ⚠️  Missing entity types: {', '.join(missing_types)}")

    def check_interview_coverage(self):
        """Check all interviews are processed"""
        cursor = self.db.conn.cursor()

        # Count interviews by status
        cursor.execute("""
            SELECT extraction_status, COUNT(*)
            FROM interviews
            GROUP BY extraction_status
        """)
        status_counts = dict(cursor.fetchall())

        # Get total
        cursor.execute("SELECT COUNT(*) FROM interviews")
        total_interviews = cursor.fetchone()[0]

        # Get companies
        cursor.execute("""
            SELECT company, COUNT(*)
            FROM interviews
            GROUP BY company
        """)
        company_counts = dict(cursor.fetchall())

        print(f"\n  Interview Coverage:")
        print(f"  {'-'*60}")
        print(f"  Total interviews: {total_interviews}")
        print(f"  By status:")
        for status, count in status_counts.items():
            status_icon = "✓" if status == "complete" else "⚠"
            print(f"    {status_icon} {status:12s}: {count}")

        print(f"\n  By company:")
        for company, count in company_counts.items():
            print(f"    • {company:20s}: {count}")

        self.results["completeness"]["total_interviews"] = total_interviews
        self.results["completeness"]["status_counts"] = status_counts
        self.results["completeness"]["company_counts"] = company_counts

        # Check expected count (44 interviews)
        expected_count = 44
        if total_interviews < expected_count:
            print(f"\n  ⚠️  Expected {expected_count} interviews, found {total_interviews}")

    def check_data_quality(self):
        """Check for empty fields and encoding issues"""
        cursor = self.db.conn.cursor()

        quality_issues = []

        # Check pain_points for empty descriptions
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE description IS NULL OR description = '' OR LENGTH(description) < 20
        """)
        empty_pain_point_descriptions = cursor.fetchone()[0]
        if empty_pain_point_descriptions > 0:
            quality_issues.append(f"Pain points with empty/short descriptions: {empty_pain_point_descriptions}")

        # Check processes for empty descriptions
        cursor.execute("""
            SELECT COUNT(*) FROM processes
            WHERE description IS NULL OR description = ''
        """)
        empty_process_descriptions = cursor.fetchone()[0]
        if empty_process_descriptions > 0:
            quality_issues.append(f"Processes with empty descriptions: {empty_process_descriptions}")

        # Check for encoding issues (mojibake patterns)
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE description LIKE '%Ã¡%' OR description LIKE '%Ã©%'
               OR description LIKE '%Ã­%' OR description LIKE '%Ã³%'
        """)
        encoding_issues = cursor.fetchone()[0]
        if encoding_issues > 0:
            quality_issues.append(f"Entities with encoding issues: {encoding_issues}")

        # Check for orphaned entities (invalid interview_id)
        cursor.execute("""
            SELECT COUNT(*) FROM pain_points
            WHERE interview_id NOT IN (SELECT id FROM interviews)
        """)
        orphaned_pain_points = cursor.fetchone()[0]
        if orphaned_pain_points > 0:
            quality_issues.append(f"Orphaned pain points: {orphaned_pain_points}")

        cursor.execute("""
            SELECT COUNT(*) FROM processes
            WHERE interview_id NOT IN (SELECT id FROM interviews)
        """)
        orphaned_processes = cursor.fetchone()[0]
        if orphaned_processes > 0:
            quality_issues.append(f"Orphaned processes: {orphaned_processes}")

        print(f"\n  Data Quality:")
        print(f"  {'-'*60}")

        if quality_issues:
            for issue in quality_issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"  ✓ No quality issues found")

        self.results["quality"]["issues"] = quality_issues
        self.results["quality"]["issue_count"] = len(quality_issues)

    def check_referential_integrity(self):
        """Check referential integrity between tables"""
        cursor = self.db.conn.cursor()

        integrity_issues = []

        # Check all entities reference valid interviews
        tables_to_check = [
            "pain_points", "processes", "kpis",
            "automation_candidates", "inefficiencies"
        ]

        for table in tables_to_check:
            try:
                cursor.execute(f"""
                    SELECT COUNT(*) FROM {table}
                    WHERE interview_id NOT IN (SELECT id FROM interviews)
                """)
                orphaned = cursor.fetchone()[0]
                if orphaned > 0:
                    integrity_issues.append(f"{table}: {orphaned} orphaned records")
            except Exception as e:
                # Table might not exist
                pass

        # Check for duplicate interviews
        cursor.execute("""
            SELECT respondent, company, date, COUNT(*) as count
            FROM interviews
            GROUP BY respondent, company, date
            HAVING count > 1
        """)
        duplicates = cursor.fetchall()
        if duplicates:
            integrity_issues.append(f"Duplicate interviews: {len(duplicates)}")

        print(f"\n  Referential Integrity:")
        print(f"  {'-'*60}")

        if integrity_issues:
            for issue in integrity_issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"  ✓ No integrity issues found")

        self.results["integrity"]["issues"] = integrity_issues
        self.results["integrity"]["issue_count"] = len(integrity_issues)

    def generate_summary(self):
        """Generate overall summary"""
        total_entities = self.results["completeness"]["total_entities"]
        total_interviews = self.results["completeness"]["total_interviews"]
        missing_types = len(self.results["completeness"]["missing_types"])
        quality_issues = self.results["quality"]["issue_count"]
        integrity_issues = self.results["integrity"]["issue_count"]

        # Calculate pass/fail
        all_checks_passed = (
            missing_types == 0 and
            quality_issues == 0 and
            integrity_issues == 0
        )

        print(f"\n{'='*70}")
        print(f"📊 VALIDATION SUMMARY")
        print(f"{'='*70}")
        print(f"Total interviews: {total_interviews}")
        print(f"Total entities: {total_entities}")
        print(f"Avg entities per interview: {total_entities/total_interviews:.1f}" if total_interviews > 0 else "N/A")
        print(f"\nIssues found:")
        print(f"  Missing entity types: {missing_types}")
        print(f"  Quality issues: {quality_issues}")
        print(f"  Integrity issues: {integrity_issues}")

        if all_checks_passed:
            print(f"\n✅ ALL VALIDATION CHECKS PASSED")
        else:
            print(f"\n⚠️  VALIDATION ISSUES DETECTED")

        print(f"{'='*70}\n")

        self.results["summary"] = {
            "total_entities": total_entities,
            "total_interviews": total_interviews,
            "avg_entities_per_interview": total_entities / total_interviews if total_interviews > 0 else 0,
            "missing_entity_types": missing_types,
            "quality_issues": quality_issues,
            "integrity_issues": integrity_issues,
            "all_checks_passed": all_checks_passed
        }

    def export_report(self, output_path: Path):
        """Export validation report to JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "database": str(self.db.db_path),
            "results": self.results
        }

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"📄 Validation report exported to: {output_path}")

    def close(self):
        """Close database connection"""
        self.db.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Validate extraction results")
    parser.add_argument("--db", type=Path, default=DB_PATH, help="Path to database")
    parser.add_argument("--export", type=Path, help="Export report to JSON file")
    args = parser.parse_args()

    validator = ExtractionValidator(args.db)

    try:
        results = validator.run_all_checks()

        if args.export:
            validator.export_report(args.export)

        # Exit with error code if validation failed
        if not results["summary"]["all_checks_passed"]:
            sys.exit(1)

    finally:
        validator.close()


if __name__ == "__main__":
    main()
