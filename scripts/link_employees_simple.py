#!/usr/bin/env python3
"""
Simple employee-to-entity linking script.

Uses basic pattern matching (no LLM, no fuzzy matching) to link
employees to consolidated entities based on name mentions.

Strategy:
1. Exact full name match in context
2. Last name match (if unambiguous)
3. Done.

Expected coverage: 85-90% of linkable entities.
Time to run: ~30 seconds
Cost: $0
"""

import os
import sys
import csv
from pathlib import Path
from typing import Dict, List, Tuple
import psycopg2
from psycopg2.extras import execute_values


def load_employees_from_csv(csv_path: Path) -> List[Dict]:
    """Load cleaned employee data from CSV."""
    employees = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Generate employee_id
            company = row['Empresa'].strip().upper().replace(' ', '_')
            lname = row['lname'].strip().replace(' ', '_')
            fname = row['fname'].strip().replace(' ', '_')
            employee_id = f"{company}_{lname}_{fname}"

            employees.append({
                'employee_id': employee_id,
                'first_name': row['fname'].strip(),
                'last_name': row['lname'].strip(),
                'full_name': f"{row['fname'].strip()} {row['lname'].strip()}",
                'role': row.get('Cargo', '').strip(),
                'company': row['Empresa'].strip(),
                'gc_profile': row.get('Perfil_Hipotetico_GC_Index', '').strip(),
                'gc_description': row.get('Descripcion_Perfil', '').strip(),
                'score_game_changer': int(row.get('Score_Game_Changer', 0) or 0),
                'score_strategist': int(row.get('Score_Strategist', 0) or 0),
                'score_implementer': int(row.get('Score_Implementer', 0) or 0),
                'score_polisher': int(row.get('Score_Polisher', 0) or 0),
                'score_play_maker': int(row.get('Score_Play_Maker', 0) or 0),
            })

    return employees


def insert_employees(conn, employees: List[Dict]) -> int:
    """Insert employees into database."""
    cur = conn.cursor()

    # Clear existing data
    cur.execute("DELETE FROM employees")

    # Insert employees
    insert_query = """
        INSERT INTO employees (
            employee_id, first_name, last_name, full_name,
            role, company, gc_profile, gc_description,
            score_game_changer, score_strategist, score_implementer,
            score_polisher, score_play_maker
        ) VALUES %s
        ON CONFLICT (employee_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            full_name = EXCLUDED.full_name,
            role = EXCLUDED.role,
            company = EXCLUDED.company,
            gc_profile = EXCLUDED.gc_profile,
            gc_description = EXCLUDED.gc_description,
            score_game_changer = EXCLUDED.score_game_changer,
            score_strategist = EXCLUDED.score_strategist,
            score_implementer = EXCLUDED.score_implementer,
            score_polisher = EXCLUDED.score_polisher,
            score_play_maker = EXCLUDED.score_play_maker
    """

    values = [
        (
            emp['employee_id'], emp['first_name'], emp['last_name'], emp['full_name'],
            emp['role'], emp['company'], emp['gc_profile'], emp['gc_description'],
            emp['score_game_changer'], emp['score_strategist'], emp['score_implementer'],
            emp['score_polisher'], emp['score_play_maker']
        )
        for emp in employees
    ]

    execute_values(cur, insert_query, values)
    conn.commit()

    return len(employees)


def link_employees_to_entities(conn) -> Dict[str, int]:
    """
    Link employees to entities using simple pattern matching.

    Returns:
        Statistics on linking results
    """
    cur = conn.cursor()

    # Reset existing links
    cur.execute("""
        UPDATE consolidated_entities
        SET employee_id = NULL,
            employee_name = NULL,
            employee_company = NULL
    """)

    # Get all employees
    cur.execute("""
        SELECT employee_id, full_name, last_name, first_name, company
        FROM employees
        ORDER BY LENGTH(full_name) DESC
    """)
    employees = cur.fetchall()

    stats = {
        'exact_full_name': 0,
        'exact_last_name': 0,
        'first_last_combo': 0,
        'skipped': 0,
        'total_entities_linked': 0
    }

    for emp_id, full_name, last_name, first_name, company in employees:

        # Strategy 1: Exact full name match (case-insensitive)
        # Search in: name field + payload JSONB (which may contain description, context, etc.)
        cur.execute("""
            UPDATE consolidated_entities
            SET employee_id = %s,
                employee_name = %s,
                employee_company = %s
            WHERE (
                name ILIKE %s OR
                payload::text ILIKE %s
            )
            AND employee_id IS NULL
        """, (
            emp_id, full_name, company,
            f'%{full_name}%',
            f'%{full_name}%'
        ))

        matched = cur.rowcount
        if matched > 0:
            stats['exact_full_name'] += matched
            continue

        # Strategy 2: Last name only (if unambiguous)
        cur.execute("""
            SELECT COUNT(*) FROM employees WHERE last_name = %s
        """, (last_name,))

        lastname_count = cur.fetchone()[0]

        if lastname_count == 1:  # Unambiguous last name
            cur.execute("""
                UPDATE consolidated_entities
                SET employee_id = %s,
                    employee_name = %s,
                    employee_company = %s
                WHERE (
                    name ILIKE %s OR
                    payload::text ILIKE %s
                )
                AND employee_id IS NULL
                RETURNING id
            """, (
                emp_id, full_name, company,
                f'%{last_name}%',
                f'%{last_name}%'
            ))

            matched = cur.rowcount
            if matched > 0:
                stats['exact_last_name'] += matched
                continue

        # Strategy 3: First + Last name parts (for compound names)
        # Example: "Doria Medina" + "Samuel" or "Mejia Mangudo" + "Pamela"
        if ' ' in last_name or ' ' in first_name:
            # Try matching both parts separately in same entity
            first_part = first_name.split()[0] if first_name else ''
            last_part = last_name.split()[0] if last_name else ''

            if first_part and last_part:
                cur.execute("""
                    UPDATE consolidated_entities
                    SET employee_id = %s,
                        employee_name = %s,
                        employee_company = %s
                    WHERE (
                        (name ILIKE %s AND name ILIKE %s) OR
                        (payload::text ILIKE %s AND payload::text ILIKE %s)
                    )
                    AND employee_id IS NULL
                """, (
                    emp_id, full_name, company,
                    f'%{first_part}%', f'%{last_part}%',
                    f'%{first_part}%', f'%{last_part}%'
                ))

                matched = cur.rowcount
                if matched > 0:
                    stats['first_last_combo'] += matched
                    continue

        # If we get here, couldn't link this employee
        stats['skipped'] += 1

    # Calculate total entities linked
    cur.execute("""
        SELECT COUNT(DISTINCT id)
        FROM consolidated_entities
        WHERE employee_id IS NOT NULL
    """)
    stats['total_entities_linked'] = cur.fetchone()[0]

    conn.commit()
    return stats


def print_linking_report(stats: Dict[str, int], employee_count: int):
    """Print human-readable linking report."""
    print("\n" + "="*70)
    print("📊 EMPLOYEE LINKING REPORT")
    print("="*70)

    print(f"\n✅ Loaded {employee_count} employees into database")

    print(f"\n🔗 Linking Statistics:")
    print(f"   Exact full name matches: {stats['exact_full_name']}")
    print(f"   Last name matches: {stats['exact_last_name']}")
    print(f"   First+Last combo matches: {stats['first_last_combo']}")
    print(f"   Employees not linked: {stats['skipped']}")

    total_matched = (stats['exact_full_name'] +
                    stats['exact_last_name'] +
                    stats['first_last_combo'])

    print(f"\n📈 Coverage:")
    print(f"   Total entities linked: {stats['total_entities_linked']}")
    print(f"   Employee coverage: {(employee_count - stats['skipped'])/employee_count*100:.1f}%")

    if stats['skipped'] > 0:
        print(f"\n⚠️  {stats['skipped']} employees had no entity mentions")
        print("   (This is normal - not all employees may be mentioned)")

    print("\n✅ Linking complete!")
    print("="*70 + "\n")


def verify_results(conn):
    """Print verification queries."""
    cur = conn.cursor()

    print("🔍 Verification Queries:\n")

    # Entities by company
    cur.execute("""
        SELECT employee_company, COUNT(*) as count
        FROM consolidated_entities
        WHERE employee_id IS NOT NULL
        GROUP BY employee_company
        ORDER BY count DESC
    """)

    print("   Linked entities by company:")
    for company, count in cur.fetchall():
        print(f"      {company}: {count} entities")

    # Top employees by mentions
    cur.execute("""
        SELECT
            e.full_name,
            e.role,
            e.company,
            COUNT(ce.id) as mention_count
        FROM employees e
        LEFT JOIN consolidated_entities ce ON e.employee_id = ce.employee_id
        GROUP BY e.employee_id, e.full_name, e.role, e.company
        ORDER BY mention_count DESC
        LIMIT 10
    """)

    print("\n   Top 10 employees by entity mentions:")
    for full_name, role, company, count in cur.fetchall():
        print(f"      {full_name} ({role}, {company}): {count} mentions")

    # Entity types by GC profile
    cur.execute("""
        SELECT
            e.gc_profile,
            ce.entity_type,
            COUNT(*) as count
        FROM consolidated_entities ce
        JOIN employees e ON ce.employee_id = e.employee_id
        GROUP BY e.gc_profile, ce.entity_type
        ORDER BY count DESC
        LIMIT 10
    """)

    print("\n   Top entity types by GC profile:")
    for gc_profile, entity_type, count in cur.fetchall():
        print(f"      {gc_profile} → {entity_type}: {count}")

    print()


def main():
    """Main entry point."""
    # Paths
    base_dir = Path(__file__).parent.parent
    csv_path = base_dir / 'data' / 'company_info' / 'Complete Reports' / 'perfiles_gc_index_completo_44_empleados_cleaned.csv'

    # Check CSV exists
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        print("   Run clean_employee_names.py first.")
        sys.exit(1)

    # Get database URL
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Error: DATABASE_URL environment variable not set")
        sys.exit(1)

    print("🔄 Starting employee linking process...")
    print(f"📂 CSV: {csv_path.name}")
    print(f"🗄️  Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")

    try:
        # Connect to database
        conn = psycopg2.connect(database_url)

        # Load employees from CSV
        print("\n📥 Loading employees from CSV...")
        employees = load_employees_from_csv(csv_path)

        # Insert into database
        print(f"💾 Inserting {len(employees)} employees into database...")
        employee_count = insert_employees(conn, employees)

        # Link to entities
        print("🔗 Linking employees to entities...")
        stats = link_employees_to_entities(conn)

        # Print report
        print_linking_report(stats, employee_count)

        # Verify
        verify_results(conn)

        # Close connection
        conn.close()

        print("✅ Done! Employee data ready for queries.")
        print("\n💡 Try these queries:")
        print("   SELECT * FROM employees WHERE company = 'COMVERSA';")
        print("   SELECT * FROM consolidated_entities WHERE employee_company = 'LOS TAJIBOS' LIMIT 10;")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
