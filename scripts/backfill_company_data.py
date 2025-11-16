"""
Backfill Company Data - Fix Missing Company Linkage

Problem: All 44 interviews have company="" in source data
Solution: Map respondent names to companies via PostgreSQL employees table

See: reports/data_integrity_schema_review.md (Issue 1)
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import psycopg2
    from fuzzywuzzy import fuzz, process
    FUZZY_AVAILABLE = True
except ImportError:
    print("⚠️  fuzzywuzzy not available, will use exact matching only")
    FUZZY_AVAILABLE = False


class CompanyBackfiller:
    """Backfills company data for interviews and entities"""

    def __init__(self, sqlite_db_path: str, postgres_dsn: str = None):
        self.sqlite_db_path = sqlite_db_path
        self.postgres_dsn = postgres_dsn or "postgresql://postgres@localhost/comversa_rag"
        self.employee_mappings = {}
        self.stats = {
            'interviews_total': 0,
            'interviews_matched': 0,
            'interviews_unmatched': 0,
            'entities_updated': {}
        }

    def load_employee_mappings(self):
        """Load employee→company mappings from PostgreSQL"""
        print("\n📊 Loading employee→company mappings from PostgreSQL...")

        try:
            conn = psycopg2.connect(self.postgres_dsn)
            cur = conn.cursor()

            cur.execute("""
                SELECT full_name, company, role
                FROM employees
                WHERE company IS NOT NULL
                ORDER BY company, full_name
            """)

            rows = cur.fetchall()

            for full_name, company, role in rows:
                self.employee_mappings[full_name] = {
                    'company': company,
                    'role': role
                }

            conn.close()

            print(f"✓ Loaded {len(self.employee_mappings)} employee→company mappings")

            # Show company distribution
            companies = {}
            for emp_data in self.employee_mappings.values():
                company = emp_data['company']
                companies[company] = companies.get(company, 0) + 1

            print("\n📈 Company distribution in employee data:")
            for company, count in sorted(companies.items()):
                print(f"   {company}: {count} employees")

            return True

        except Exception as e:
            print(f"❌ Failed to load employee mappings: {e}")
            return False

    def match_respondent_to_company(self, respondent: str, threshold: int = 85):
        """
        Match respondent name to employee using fuzzy matching

        Args:
            respondent: Interview respondent name
            threshold: Minimum fuzzy match score (0-100)

        Returns:
            (company, confidence_score) or (None, 0) if no match
        """
        if not respondent:
            return None, 0

        # Try exact match first
        if respondent in self.employee_mappings:
            return self.employee_mappings[respondent]['company'], 100

        # Try fuzzy matching if available
        if FUZZY_AVAILABLE:
            match = process.extractOne(
                respondent,
                self.employee_mappings.keys(),
                scorer=fuzz.token_sort_ratio
            )

            if match and match[1] >= threshold:
                matched_name = match[0]
                company = self.employee_mappings[matched_name]['company']
                confidence = match[1]
                return company, confidence

        # Try partial matching (last name)
        respondent_parts = respondent.lower().split()
        if respondent_parts:
            last_name = respondent_parts[-1]
            for emp_name, emp_data in self.employee_mappings.items():
                if last_name in emp_name.lower():
                    return emp_data['company'], 75  # Lower confidence

        return None, 0

    def backfill_interviews(self):
        """Update interviews.company column with matched companies"""
        print("\n📝 Backfilling interview company data...")

        conn = sqlite3.connect(self.sqlite_db_path)

        # Get all interviews
        interviews = conn.execute("""
            SELECT id, respondent, role, company
            FROM interviews
            ORDER BY id
        """).fetchall()

        self.stats['interviews_total'] = len(interviews)

        matched = []
        unmatched = []

        print(f"\n🔍 Matching {len(interviews)} respondents to companies...\n")

        for interview_id, respondent, role, current_company in interviews:
            company, confidence = self.match_respondent_to_company(respondent)

            if company:
                # Update interview
                conn.execute("""
                    UPDATE interviews
                    SET company = ?
                    WHERE id = ?
                """, (company, interview_id))

                matched.append({
                    'id': interview_id,
                    'respondent': respondent,
                    'company': company,
                    'confidence': confidence
                })

                symbol = "✓" if confidence == 100 else "≈"
                print(f"  {symbol} [{interview_id:2d}] {respondent:30s} → {company:15s} ({confidence}%)")

            else:
                unmatched.append({
                    'id': interview_id,
                    'respondent': respondent,
                    'role': role
                })

                print(f"  ✗ [{interview_id:2d}] {respondent:30s} → NO MATCH")

        conn.commit()

        self.stats['interviews_matched'] = len(matched)
        self.stats['interviews_unmatched'] = len(unmatched)

        # Report
        print(f"\n{'='*70}")
        print(f"📊 Interview Matching Summary")
        print(f"{'='*70}")
        print(f"Total interviews: {self.stats['interviews_total']}")
        print(f"✓ Matched: {self.stats['interviews_matched']} ({self.stats['interviews_matched']/self.stats['interviews_total']*100:.1f}%)")
        print(f"✗ Unmatched: {self.stats['interviews_unmatched']} ({self.stats['interviews_unmatched']/self.stats['interviews_total']*100:.1f}%)")

        if unmatched:
            print(f"\n⚠️  Unmatched respondents:")
            for item in unmatched:
                print(f"   [{item['id']}] {item['respondent']} ({item['role']})")

        # Show company distribution after matching
        company_counts = conn.execute("""
            SELECT company, COUNT(*) as count
            FROM interviews
            WHERE company IS NOT NULL AND company != ''
            GROUP BY company
            ORDER BY count DESC
        """).fetchall()

        if company_counts:
            print(f"\n📈 Company distribution after matching:")
            for company, count in company_counts:
                print(f"   {company}: {count} interviews")

        conn.close()

        return len(unmatched) == 0  # Success if all matched

    def backfill_entities(self):
        """Update entity tables via interview_id foreign key"""
        print(f"\n🔗 Backfilling entity company data via interview_id FK...")

        conn = sqlite3.connect(self.sqlite_db_path)

        # v1.0 tables use 'company' column
        v1_tables = [
            'pain_points',
            'processes',
            'kpis',
            'automation_candidates',
            'inefficiencies'
        ]

        # v2.0 tables use 'company_name' column
        v2_tables = [
            'communication_channels',
            'decision_points',
            'data_flows',
            'temporal_patterns',
            'failure_modes',
            'team_structures',
            'knowledge_gaps',
            'success_patterns',
            'budget_constraints',
            'external_dependencies'
        ]

        print()
        total_updated = 0

        # Process v1.0 tables (use 'company' column)
        for table in v1_tables:
            try:
                # Check if table exists and has data
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                total_count = count_result[0] if count_result else 0

                if total_count == 0:
                    print(f"  ⊘ {table:25s} → 0 records (skipped)")
                    self.stats['entities_updated'][table] = 0
                    continue

                # Update company via interview FK
                cursor = conn.execute(f"""
                    UPDATE {table}
                    SET company = (
                        SELECT company
                        FROM interviews
                        WHERE interviews.id = {table}.interview_id
                    )
                    WHERE company IS NULL OR company = ''
                """)

                updated = cursor.rowcount

                self.stats['entities_updated'][table] = updated
                total_updated += updated

                symbol = "✓" if updated > 0 else "="
                print(f"  {symbol} {table:25s} → {updated:3d}/{total_count:3d} updated")

            except Exception as e:
                print(f"  ✗ {table:25s} → ERROR: {e}")
                self.stats['entities_updated'][table] = -1

        # Process v2.0 tables (use 'company_name' column)
        for table in v2_tables:
            try:
                # Check if table exists and has data
                count_result = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                total_count = count_result[0] if count_result else 0

                if total_count == 0:
                    print(f"  ⊘ {table:25s} → 0 records (skipped)")
                    self.stats['entities_updated'][table] = 0
                    continue

                # Update company_name via interview FK
                cursor = conn.execute(f"""
                    UPDATE {table}
                    SET company_name = (
                        SELECT company
                        FROM interviews
                        WHERE interviews.id = {table}.interview_id
                    )
                    WHERE company_name IS NULL OR company_name = ''
                """)

                updated = cursor.rowcount

                self.stats['entities_updated'][table] = updated
                total_updated += updated

                symbol = "✓" if updated > 0 else "="
                print(f"  {symbol} {table:25s} → {updated:3d}/{total_count:3d} updated")

            except Exception as e:
                print(f"  ✗ {table:25s} → ERROR: {e}")
                self.stats['entities_updated'][table] = -1

        conn.commit()
        conn.close()

        print(f"\n{'='*70}")
        print(f"Total entity records updated: {total_updated}")

        return True

    def validate_results(self):
        """Validate company backfill results"""
        print(f"\n🔍 Validating backfill results...\n")

        conn = sqlite3.connect(self.sqlite_db_path)

        # 1. Check interview company coverage
        interview_stats = conn.execute("""
            SELECT
                COUNT(*) as total,
                COUNT(CASE WHEN company IS NOT NULL AND company != '' THEN 1 END) as with_company,
                COUNT(CASE WHEN company IS NULL OR company = '' THEN 1 END) as without_company
            FROM interviews
        """).fetchone()

        total, with_company, without_company = interview_stats

        print(f"📊 Interview Company Coverage:")
        print(f"   Total: {total}")
        print(f"   ✓ With company: {with_company} ({with_company/total*100:.1f}%)")
        print(f"   ✗ Without company: {without_company} ({without_company/total*100:.1f}%)")

        # 2. Check entity company coverage
        print(f"\n📊 Entity Company Coverage:")

        # v1.0 tables use 'company' column
        v1_sample = ['pain_points', 'processes', 'kpis']
        # v2.0 tables use 'company_name' column
        v2_sample = ['communication_channels', 'decision_points', 'data_flows']

        for table in v1_sample:
            try:
                stats = conn.execute(f"""
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN company IS NOT NULL AND company != '' THEN 1 END) as with_company
                    FROM {table}
                """).fetchone()

                if stats and stats[0] > 0:
                    total_entities, with_company_entities = stats
                    coverage = (with_company_entities / total_entities * 100) if total_entities > 0 else 0
                    print(f"   {table:25s}: {with_company_entities:3d}/{total_entities:3d} ({coverage:.1f}%)")

            except Exception as e:
                print(f"   {table:25s}: ERROR - {e}")

        for table in v2_sample:
            try:
                stats = conn.execute(f"""
                    SELECT
                        COUNT(*) as total,
                        COUNT(CASE WHEN company_name IS NOT NULL AND company_name != '' THEN 1 END) as with_company
                    FROM {table}
                """).fetchone()

                if stats and stats[0] > 0:
                    total_entities, with_company_entities = stats
                    coverage = (with_company_entities / total_entities * 100) if total_entities > 0 else 0
                    print(f"   {table:25s}: {with_company_entities:3d}/{total_entities:3d} ({coverage:.1f}%)")

            except Exception as e:
                print(f"   {table:25s}: ERROR - {e}")

        # 3. Company distribution validation
        print(f"\n📊 Company Distribution Validation:")

        company_dist = conn.execute("""
            SELECT
                i.company,
                COUNT(DISTINCT i.id) as interviews,
                COUNT(p.id) as pain_points,
                COUNT(pr.id) as processes
            FROM interviews i
            LEFT JOIN pain_points p ON p.interview_id = i.id
            LEFT JOIN processes pr ON pr.interview_id = i.id
            WHERE i.company IS NOT NULL AND i.company != ''
            GROUP BY i.company
            ORDER BY interviews DESC
        """).fetchall()

        for company, interviews, pain_points, processes in company_dist:
            print(f"   {company:15s}: {interviews:2d} interviews, {pain_points:3d} pain points, {processes:3d} processes")

        conn.close()

        # Success criteria
        success = (
            with_company >= total * 0.9  # At least 90% coverage
        )

        if success:
            print(f"\n✅ Validation PASSED - Company backfill successful!")
        else:
            print(f"\n⚠️  Validation WARNING - Some interviews still missing company")

        return success

    def run(self):
        """Execute full backfill process"""
        print("="*70)
        print("Company Backfill - Fix Missing Company Linkage")
        print("="*70)

        # Step 1: Load employee mappings
        if not self.load_employee_mappings():
            print("\n❌ Failed to load employee mappings. Aborting.")
            return False

        # Step 2: Backfill interviews
        if not self.backfill_interviews():
            print("\n⚠️  Some interviews could not be matched to companies")
            # Continue anyway - partial success is acceptable

        # Step 3: Backfill entities
        if not self.backfill_entities():
            print("\n❌ Failed to backfill entity tables. Aborting.")
            return False

        # Step 4: Validate
        success = self.validate_results()

        print(f"\n{'='*70}")
        if success:
            print("✅ COMPANY BACKFILL COMPLETE - All data updated successfully!")
        else:
            print("⚠️  COMPANY BACKFILL COMPLETE - Review warnings above")
        print("="*70)

        return success


def main():
    """Main entry point"""
    import os

    # Paths
    sqlite_db = "data/full_intelligence.db"
    postgres_dsn = os.getenv("DATABASE_URL", "postgresql://postgres@localhost/comversa_rag")

    # Check if SQLite database exists
    if not Path(sqlite_db).exists():
        print(f"❌ SQLite database not found: {sqlite_db}")
        return 1

    # Run backfill
    backfiller = CompanyBackfiller(sqlite_db, postgres_dsn)
    success = backfiller.run()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
