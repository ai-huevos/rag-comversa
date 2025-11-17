#!/usr/bin/env python3
"""
Sync employee data from PostgreSQL to Neo4j knowledge graph.

Creates:
- Employee nodes with GC Index profiles
- MENTIONED relationships to entities
- COLLABORATES_WITH relationships (based on shared entity mentions)
- WORKS_FOR relationships to organization nodes
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg2
from neo4j import GraphDatabase

def main():
    # Connection strings
    pg_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")
    neo4j_uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password = os.getenv("NEO4J_PASSWORD", "comversa_neo4j_2025")

    print(f"👥 Syncing employees: PostgreSQL → Neo4j")
    print()

    # Connect to PostgreSQL
    pg_conn = psycopg2.connect(pg_url)
    pg_cursor = pg_conn.cursor()

    # Connect to Neo4j
    neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    try:
        # Get employee count
        pg_cursor.execute("SELECT COUNT(*) FROM employees")
        total_employees = pg_cursor.fetchone()[0]

        if total_employees == 0:
            print("⊘ No employees found in PostgreSQL")
            return

        print(f"Found {total_employees} employees in PostgreSQL")

        # Read all employees
        pg_cursor.execute("""
            SELECT
                employee_id,
                full_name,
                role,
                company,
                gc_profile,
                score_game_changer,
                score_strategist,
                score_implementer,
                score_polisher,
                score_play_maker
            FROM employees
            ORDER BY company, full_name
        """)

        employees = []
        for row in pg_cursor.fetchall():
            employees.append({
                'employee_id': row[0],
                'full_name': row[1],
                'role': row[2],
                'company': row[3],
                'gc_profile': row[4],
                'score_game_changer': row[5],
                'score_strategist': row[6],
                'score_implementer': row[7],
                'score_polisher': row[8],
                'score_play_maker': row[9]
            })

        # Create Employee nodes in Neo4j
        print(f"\n📦 Creating {len(employees)} Employee nodes...")
        with neo4j_driver.session() as session:
            # Create constraint on employee_id
            try:
                session.run("CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.employee_id IS UNIQUE")
            except:
                pass  # Constraint might already exist

            for emp in employees:
                session.run("""
                    MERGE (e:Employee {employee_id: $employee_id})
                    SET
                        e.full_name = $full_name,
                        e.role = $role,
                        e.company = $company,
                        e.gc_profile = $gc_profile,
                        e.score_game_changer = $score_game_changer,
                        e.score_strategist = $score_strategist,
                        e.score_implementer = $score_implementer,
                        e.score_polisher = $score_polisher,
                        e.score_play_maker = $score_play_maker,
                        e.last_synced_at = datetime()
                """, **emp)

        print(f"✅ Created {len(employees)} Employee nodes")

        # Create Organization nodes and WORKS_FOR relationships
        print(f"\n🏢 Creating organization relationships...")
        with neo4j_driver.session() as session:
            companies = set(emp['company'] for emp in employees if emp['company'])
            for company in companies:
                # Create Organization node
                session.run("""
                    MERGE (o:Organization {name: $company})
                    SET o.last_synced_at = datetime()
                """, company=company)

            # Link employees to organizations
            for emp in employees:
                if emp['company']:
                    session.run("""
                        MATCH (e:Employee {employee_id: $employee_id})
                        MATCH (o:Organization {name: $company})
                        MERGE (e)-[:WORKS_FOR]->(o)
                    """, employee_id=emp['employee_id'], company=emp['company'])

        print(f"✅ Created {len(companies)} organizations and relationships")

        # Link employees to entities they mentioned
        print(f"\n🔗 Creating MENTIONED relationships to entities...")
        pg_cursor.execute("""
            SELECT
                ce.employee_id,
                ce.sqlite_entity_id,
                ce.entity_type,
                ce.name
            FROM consolidated_entities ce
            WHERE ce.employee_id IS NOT NULL
        """)

        mentions = []
        for row in pg_cursor.fetchall():
            mentions.append({
                'employee_id': row[0],
                'entity_external_id': f"sqlite_{row[2]}_{row[1]}",  # sqlite_{type}_{id}
                'entity_name': row[3]
            })

        with neo4j_driver.session() as session:
            for mention in mentions:
                session.run("""
                    MATCH (emp:Employee {employee_id: $employee_id})
                    MATCH (entity:Entity {external_id: $entity_external_id})
                    MERGE (emp)-[:MENTIONED]->(entity)
                """, **mention)

        print(f"✅ Created {len(mentions)} MENTIONED relationships")

        # Discover collaboration patterns (employees who mention same entities)
        print(f"\n🤝 Discovering collaboration patterns...")
        with neo4j_driver.session() as session:
            result = session.run("""
                // Find employees who mentioned the same entities
                MATCH (e1:Employee)-[:MENTIONED]->(entity:Entity)<-[:MENTIONED]-(e2:Employee)
                WHERE e1.employee_id < e2.employee_id  // Avoid duplicates
                WITH e1, e2, count(DISTINCT entity) as shared_contexts
                WHERE shared_contexts >= 2  // At least 2 shared entities
                MERGE (e1)-[c:COLLABORATES_WITH]-(e2)
                SET
                    c.shared_contexts = shared_contexts,
                    c.confidence = CASE
                        WHEN shared_contexts >= 5 THEN 0.9
                        WHEN shared_contexts >= 3 THEN 0.8
                        ELSE 0.7
                    END,
                    c.last_updated = datetime()
                RETURN count(c) as collaboration_count
            """)
            collab_count = result.single()['collaboration_count']

        print(f"✅ Created {collab_count} COLLABORATES_WITH relationships")

        # Summary statistics
        print(f"\n📊 Neo4j Summary:")
        with neo4j_driver.session() as session:
            # Employee count
            emp_count = session.run("MATCH (e:Employee) RETURN count(e) as count").single()['count']
            print(f"   Employees: {emp_count}")

            # Organization count
            org_count = session.run("MATCH (o:Organization) RETURN count(o) as count").single()['count']
            print(f"   Organizations: {org_count}")

            # MENTIONED relationships
            mentioned_count = session.run("MATCH ()-[r:MENTIONED]->() RETURN count(r) as count").single()['count']
            print(f"   MENTIONED relationships: {mentioned_count}")

            # COLLABORATES_WITH relationships
            collab_count = session.run("MATCH ()-[r:COLLABORATES_WITH]-() RETURN count(r) as count").single()['count']
            print(f"   COLLABORATES_WITH relationships: {collab_count}")

            # WORKS_FOR relationships
            works_for_count = session.run("MATCH ()-[r:WORKS_FOR]->() RETURN count(r) as count").single()['count']
            print(f"   WORKS_FOR relationships: {works_for_count}")

        print(f"\n✅ Employee sync complete!")
        print(f"\n🌐 Open Neo4j Browser: http://localhost:7474")
        print(f"   Try this query to see employees and their networks:")
        print(f"   MATCH (e:Employee)-[r]-(related) RETURN e, r, related LIMIT 50")

    finally:
        pg_cursor.close()
        pg_conn.close()
        neo4j_driver.close()

if __name__ == "__main__":
    main()
