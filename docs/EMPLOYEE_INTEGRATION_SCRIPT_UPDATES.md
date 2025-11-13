# Scripts Requiring Updates for Employee Context

**Goal:** Populate and utilize employee data across the entire system
**Current State:** Employee data in PostgreSQL, 52 entities linked
**Next:** Integrate employee context into extraction, consolidation, and retrieval

---

## 🔄 Required Updates by Priority

### **Priority 1: Data Backfill (Essential)**

#### 1. **`scripts/backfill_sqlite_employees.py`** (NEW - Create This)

**Purpose:** Link existing SQLite consolidated entities to employees

**What It Does:**
```python
#!/usr/bin/env python3
"""
Backfill employee links in SQLite consolidated_entities.

Reads from PostgreSQL employees table and updates SQLite
consolidated_entities with employee_id, employee_name, employee_company.
"""

import sqlite3
import psycopg2
import os

def backfill_sqlite_employees():
    """Copy employee links from PostgreSQL to SQLite."""

    # Connect to both databases
    sqlite_conn = sqlite3.connect('data/full_intelligence.db')
    pg_conn = psycopg2.connect(os.environ['DATABASE_URL'])

    # Add employee columns to SQLite if not exist
    sqlite_conn.execute("""
        ALTER TABLE consolidated_entities
        ADD COLUMN employee_id TEXT
    """)
    sqlite_conn.execute("""
        ALTER TABLE consolidated_entities
        ADD COLUMN employee_name TEXT
    """)
    sqlite_conn.execute("""
        ALTER TABLE consolidated_entities
        ADD COLUMN employee_company TEXT
    """)

    # Get employee links from PostgreSQL
    pg_cur = pg_conn.cursor()
    pg_cur.execute("""
        SELECT
            sqlite_entity_id,
            entity_type,
            employee_id,
            employee_name,
            employee_company
        FROM consolidated_entities
        WHERE employee_id IS NOT NULL
    """)

    # Update SQLite
    sqlite_cur = sqlite_conn.cursor()
    for row in pg_cur.fetchall():
        sqlite_id, entity_type, emp_id, emp_name, emp_company = row
        sqlite_cur.execute("""
            UPDATE consolidated_entities
            SET employee_id = ?,
                employee_name = ?,
                employee_company = ?
            WHERE id = ?
            AND entity_type = ?
        """, (emp_id, emp_name, emp_company, sqlite_id, entity_type))

    sqlite_conn.commit()
    print(f"✅ Backfilled {sqlite_cur.rowcount} entities with employee data")
```

**Why Needed:** SQLite still used for some operations, needs employee context

**Run Once:**
```bash
python3 scripts/backfill_sqlite_employees.py
```

---

### **Priority 2: Extraction Pipeline (For New Interviews)**

#### 2. **`intelligence_capture/extractor.py`** (UPDATE)

**Current:** Extracts 17 entity types, no employee detection

**Update Needed:** Add employee detection to extraction

**Add This Class:**
```python
@dataclass
class EmployeeReference:
    """
    Detected employee reference in interview transcript.

    New entity type (v3.0) for attributing information to specific employees.
    """
    employee_name: str
    company: str
    role: Optional[str] = None
    context: str = ""
    confidence_score: float = 0.0

    # Matched employee data (from database)
    employee_id: Optional[str] = None
    gc_profile: Optional[str] = None
```

**Add This Method to `IntelligenceExtractor`:**
```python
def detect_employee_references(self, text: str) -> List[EmployeeReference]:
    """
    Detect employee mentions in interview text.

    Uses simple pattern matching against employee database.
    Links entities to specific employees for attribution.
    """
    # Load employee data from PostgreSQL
    employees = self._load_employees()

    references = []
    for employee in employees:
        # Check if employee name appears in text
        if employee['full_name'].lower() in text.lower():
            references.append(EmployeeReference(
                employee_name=employee['full_name'],
                company=employee['company'],
                role=employee['role'],
                context=self._extract_context(text, employee['full_name']),
                confidence_score=1.0,
                employee_id=employee['employee_id'],
                gc_profile=employee['gc_profile']
            ))

    return references

def _load_employees(self) -> List[Dict]:
    """Load employee data from PostgreSQL."""
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    cur = conn.cursor()
    cur.execute("SELECT employee_id, full_name, company, role, gc_profile FROM employees")

    employees = []
    for row in cur.fetchall():
        employees.append({
            'employee_id': row[0],
            'full_name': row[1],
            'company': row[2],
            'role': row[3],
            'gc_profile': row[4]
        })
    return employees
```

**Integration Point:**
```python
# In extract_intelligence() method, add:
employee_refs = self.detect_employee_references(interview_text)

# Then link entities to employees
for entity in all_entities:
    # Find employee who mentioned this entity
    entity.mentioned_by = self._find_mentioning_employee(
        entity, employee_refs, interview_text
    )
```

**Why Needed:** Automatically attribute entities to employees during extraction

**Timeline:** 1-2 days for new interviews

---

#### 3. **`intelligence_capture/processor.py`** (UPDATE)

**Current:** Orchestrates extraction, validation, consolidation

**Update Needed:** Add employee linking step

**Add After Entity Extraction:**
```python
def process_interview(self, interview_path: str) -> ProcessingResult:
    """Process interview with employee attribution."""

    # Existing extraction
    entities = self.extractor.extract_intelligence(interview_text)

    # NEW: Detect employee references
    employee_refs = self.extractor.detect_employee_references(interview_text)

    # NEW: Link entities to employees
    for entity in entities:
        entity.employee_id = self._match_employee(entity, employee_refs)
        entity.employee_name = self._get_employee_name(entity.employee_id)
        entity.employee_company = self._get_employee_company(entity.employee_id)

    # Continue with validation and consolidation
    validated = self.validator.validate(entities)
    consolidated = self.consolidator.consolidate(validated)

    return ProcessingResult(
        entities=consolidated,
        employee_refs=employee_refs,
        stats=self._calculate_stats()
    )
```

**Why Needed:** Ensure all new extractions have employee context

**Timeline:** 1 day

---

### **Priority 3: Consolidation Enhancement (Better Grouping)**

#### 4. **`intelligence_capture/consolidation_agent.py`** (UPDATE)

**Current:** Groups entities by name/description similarity

**Update Needed:** Consider employee attribution in consolidation

**Add Employee-Aware Grouping:**
```python
class EmployeeAwareConsolidation:
    """
    Enhanced consolidation that considers who mentioned entities.

    Strategy:
    - If multiple employees mention same entity → High confidence
    - If same employee mentions contradictory info → Flag for review
    - Group by employee for attribution tracking
    """

    def calculate_consensus_with_employee_context(
        self,
        duplicates: List[Entity]
    ) -> float:
        """
        Calculate consensus considering employee sources.

        More employees mentioning = higher confidence
        Same employee repeating = normal confidence
        Contradictions from different employees = flag
        """
        unique_employees = set(e.employee_id for e in duplicates if e.employee_id)

        # Base consensus score
        base_score = self._calculate_base_consensus(duplicates)

        # Boost if mentioned by multiple employees
        if len(unique_employees) >= 3:
            base_score *= 1.2  # High confidence boost
        elif len(unique_employees) >= 2:
            base_score *= 1.1  # Medium confidence boost

        # Cap at 1.0
        return min(base_score, 1.0)

    def group_by_employee(self, entities: List[Entity]) -> Dict[str, List[Entity]]:
        """Group entities by employee for attribution analysis."""
        by_employee = defaultdict(list)

        for entity in entities:
            if entity.employee_id:
                by_employee[entity.employee_id].append(entity)
            else:
                by_employee['unattributed'].append(entity)

        return dict(by_employee)
```

**Why Needed:** Better consolidation decisions using employee context

**Timeline:** 2 days

---

### **Priority 4: Database Schema Updates**

#### 5. **`intelligence_capture/database.py`** (UPDATE - SQLite Schema)

**Current:** 17 entity tables + consolidated_entities

**Update Needed:** Add employee columns to all entity tables

**Add to Schema:**
```python
# In create_tables() method, add to each entity table:

CREATE TABLE IF NOT EXISTS pain_points (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    severity TEXT,
    frequency TEXT,
    impact_area TEXT,
    affected_roles TEXT,
    current_workarounds TEXT,
    context TEXT,

    # NEW: Employee attribution
    employee_id TEXT,
    employee_name TEXT,
    employee_company TEXT,
    employee_gc_profile TEXT,

    confidence_score REAL DEFAULT 0.0,
    source TEXT,
    raw_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Apply to All 17 Entity Tables:**
- pain_points
- processes
- systems
- kpis
- automation_candidates
- inefficiencies
- communication_channels
- decision_points
- data_flows
- temporal_patterns
- failure_modes
- team_structures
- knowledge_gaps
- success_patterns
- budget_constraints
- external_dependencies

**Migration Script Needed:**
```python
def migrate_add_employee_columns():
    """Add employee columns to all entity tables."""
    entity_tables = [
        'pain_points', 'processes', 'systems', 'kpis',
        'automation_candidates', 'inefficiencies',
        # ... all 17 tables
    ]

    for table in entity_tables:
        conn.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN employee_id TEXT
        """)
        conn.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN employee_name TEXT
        """)
        conn.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN employee_company TEXT
        """)
        conn.execute(f"""
            ALTER TABLE {table}
            ADD COLUMN employee_gc_profile TEXT
        """)
```

**Why Needed:** Store employee attribution at entity level

**Timeline:** 1 hour (simple ALTER TABLE statements)

---

#### 6. **`scripts/migrations/2025_11_12_sqlite_employee_columns.sql`** (NEW)

**Purpose:** Migration script for SQLite schema updates

```sql
-- Add employee columns to all entity tables
BEGIN TRANSACTION;

-- Pain Points
ALTER TABLE pain_points ADD COLUMN employee_id TEXT;
ALTER TABLE pain_points ADD COLUMN employee_name TEXT;
ALTER TABLE pain_points ADD COLUMN employee_company TEXT;
ALTER TABLE pain_points ADD COLUMN employee_gc_profile TEXT;

-- Processes
ALTER TABLE processes ADD COLUMN employee_id TEXT;
ALTER TABLE processes ADD COLUMN employee_name TEXT;
ALTER TABLE processes ADD COLUMN employee_company TEXT;
ALTER TABLE processes ADD COLUMN employee_gc_profile TEXT;

-- ... repeat for all 17 tables ...

-- Create indices for employee filtering
CREATE INDEX IF NOT EXISTS idx_pain_points_employee ON pain_points(employee_id);
CREATE INDEX IF NOT EXISTS idx_processes_employee ON processes(employee_id);
-- ... repeat for all tables ...

COMMIT;
```

**Run Once:**
```bash
sqlite3 data/full_intelligence.db < scripts/migrations/2025_11_12_sqlite_employee_columns.sql
```

---

### **Priority 5: Sync Scripts (Keep Systems in Sync)**

#### 7. **`scripts/sync_consolidated_to_neo4j.py`** (UPDATE)

**Current:** Syncs consolidated entities to Neo4j

**Update Needed:** Include employee data in sync

**Add Employee Context:**
```python
def sync_entity_to_neo4j(entity: Dict) -> None:
    """Sync entity with employee context to Neo4j."""

    with driver.session() as session:
        session.run("""
            MERGE (e:Entity {entity_id: $entity_id})
            SET e.name = $name,
                e.entity_type = $entity_type,
                e.consensus_confidence = $confidence,

                // NEW: Employee attribution
                e.employee_id = $employee_id,
                e.employee_name = $employee_name,
                e.employee_company = $employee_company
        """, {
            'entity_id': entity['id'],
            'name': entity['name'],
            'entity_type': entity['entity_type'],
            'confidence': entity['consensus_confidence'],
            'employee_id': entity.get('employee_id'),
            'employee_name': entity.get('employee_name'),
            'employee_company': entity.get('employee_company')
        })

        # NEW: Create relationship to employee if exists
        if entity.get('employee_id'):
            session.run("""
                MATCH (entity:Entity {entity_id: $entity_id})
                MATCH (emp:Employee {employee_id: $employee_id})
                MERGE (emp)-[:MENTIONED]->(entity)
            """, {
                'entity_id': entity['id'],
                'employee_id': entity['employee_id']
            })
```

**Why Needed:** Keep Neo4j graph up to date with employee links

**Timeline:** 1 hour

---

#### 8. **`scripts/sync_employees_to_neo4j.py`** (NEW - If Using Neo4j)

**Purpose:** Create Employee nodes in Neo4j

```python
#!/usr/bin/env python3
"""
Sync employees from PostgreSQL to Neo4j.

Creates Employee nodes and links them to mentioned entities.
"""

import psycopg2
import os
from neo4j import GraphDatabase

def sync_employees_to_neo4j():
    """Sync all employees to Neo4j as nodes."""

    # Load employees from PostgreSQL
    pg_conn = psycopg2.connect(os.environ['DATABASE_URL'])
    pg_cur = pg_conn.cursor()
    pg_cur.execute("""
        SELECT
            employee_id, full_name, first_name, last_name,
            role, company, gc_profile, gc_description,
            score_game_changer, score_strategist, score_implementer,
            score_polisher, score_play_maker
        FROM employees
    """)

    # Connect to Neo4j
    neo4j_uri = os.environ['NEO4J_URI']
    neo4j_user = os.environ['NEO4J_USER']
    neo4j_password = os.environ['NEO4J_PASSWORD']
    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))

    with driver.session() as session:
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (e:Employee {employee_id: $employee_id})
                SET e.full_name = $full_name,
                    e.first_name = $first_name,
                    e.last_name = $last_name,
                    e.role = $role,
                    e.company = $company,
                    e.gc_profile = $gc_profile,
                    e.gc_description = $gc_description,
                    e.score_game_changer = $score_game_changer,
                    e.score_strategist = $score_strategist,
                    e.score_implementer = $score_implementer,
                    e.score_polisher = $score_polisher,
                    e.score_play_maker = $score_play_maker
            """, {
                'employee_id': row[0],
                'full_name': row[1],
                'first_name': row[2],
                'last_name': row[3],
                'role': row[4],
                'company': row[5],
                'gc_profile': row[6],
                'gc_description': row[7],
                'score_game_changer': row[8],
                'score_strategist': row[9],
                'score_implementer': row[10],
                'score_polisher': row[11],
                'score_play_maker': row[12]
            })

    print(f"✅ Synced {pg_cur.rowcount} employees to Neo4j")

if __name__ == '__main__':
    sync_employees_to_neo4j()
```

**When to Build:** Only if using Neo4j for graph queries

**Timeline:** 2 hours

---

### **Priority 6: RAG/Retrieval Enhancement**

#### 9. **`intelligence_capture/embeddings/retrieval.py`** (NEW/UPDATE)

**Purpose:** Add employee filtering to vector search

**Create/Update:**
```python
async def retrieve_with_employee_context(
    query: str,
    company: Optional[str] = None,
    employee_name: Optional[str] = None,
    gc_profile: Optional[str] = None,
    k: int = 5
) -> List[DocumentChunk]:
    """
    Retrieve chunks with employee filtering.

    Args:
        query: User query
        company: Filter by company (COMVERSA, BOLIVIAN FOODS, LOS TAJIBOS)
        employee_name: Filter by employee name (fuzzy match)
        gc_profile: Filter by GC profile (Strategist, Implementer, etc.)
        k: Number of results

    Returns:
        Ranked document chunks with employee context
    """
    # Embed query
    query_embedding = await embed(query)

    # Build WHERE clause with employee filters
    where_conditions = []
    params = {'query_embedding': query_embedding, 'k': k}

    if company:
        where_conditions.append("ce.employee_company = %(company)s")
        params['company'] = company

    if employee_name:
        where_conditions.append("ce.employee_name ILIKE %(employee_name)s")
        params['employee_name'] = f"%{employee_name}%"

    if gc_profile:
        where_conditions.append("""
            ce.employee_id IN (
                SELECT employee_id FROM employees
                WHERE gc_profile ILIKE %(gc_profile)s
            )
        """)
        params['gc_profile'] = f"%{gc_profile}%"

    where_clause = " AND ".join(where_conditions) if where_conditions else "TRUE"

    # Execute vector search with filters
    query = f"""
        SELECT
            dc.id,
            dc.content,
            dc.metadata,
            ce.employee_name,
            ce.employee_company,
            e.gc_profile,
            (dc.embedding <-> %(query_embedding)s) as distance
        FROM document_chunks dc
        JOIN consolidated_entities ce ON dc.entity_id = ce.id
        LEFT JOIN employees e ON ce.employee_id = e.employee_id
        WHERE {where_clause}
        ORDER BY distance
        LIMIT %(k)s
    """

    results = await execute_async(query, params)
    return [DocumentChunk.from_row(r) for r in results]
```

**Why Needed:** Enable employee-filtered RAG queries

**Timeline:** 1-2 days

---

#### 10. **`agent/tools/employee_lookup.py`** (NEW)

**Purpose:** RAG agent tool for employee lookups

```python
from pydantic import BaseModel, Field
from typing import Optional, List

class EmployeeLookupTool(BaseModel):
    """Tool for looking up employee information."""

    name: str = Field(default=None, description="Employee name (full or partial)")
    role: Optional[str] = Field(default=None, description="Job title/role")
    company: Optional[str] = Field(default=None, description="Company name")
    gc_profile: Optional[str] = Field(default=None, description="GC Index profile type")

async def lookup_employee(
    name: Optional[str] = None,
    role: Optional[str] = None,
    company: Optional[str] = None,
    gc_profile: Optional[str] = None
) -> str:
    """
    Look up employee information from the database.

    Returns formatted employee info with GC profile.
    """
    # Build query
    conditions = []
    params = {}

    if name:
        conditions.append("full_name ILIKE %(name)s")
        params['name'] = f"%{name}%"
    if role:
        conditions.append("role ILIKE %(role)s")
        params['role'] = f"%{role}%"
    if company:
        conditions.append("company = %(company)s")
        params['company'] = company
    if gc_profile:
        conditions.append("gc_profile ILIKE %(gc_profile)s")
        params['gc_profile'] = f"%{gc_profile}%"

    where_clause = " AND ".join(conditions) if conditions else "TRUE"

    # Execute
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT
            full_name, role, company, gc_profile,
            gc_description,
            score_game_changer, score_strategist,
            score_implementer, score_polisher, score_play_maker
        FROM employees
        WHERE {where_clause}
        LIMIT 10
    """, params)

    # Format results
    results = []
    for row in cur.fetchall():
        results.append(f"""
**{row[0]}**
- Rol: {row[1]}
- Empresa: {row[2]}
- Perfil GC: {row[3]}
- Descripción: {row[4]}
- Puntuaciones: GC={row[5]}, Str={row[6]}, Imp={row[7]}, Pol={row[8]}, PM={row[9]}
        """)

    return "\n\n".join(results) if results else "No se encontraron empleados."
```

**Why Needed:** Allow RAG agent to look up employee info

**Timeline:** 1 day

---

## 📋 Implementation Checklist

### **Phase 1: Foundation** ✅ **DONE**
- [x] Create `employees` table in PostgreSQL
- [x] Load 44 employees with GC profiles
- [x] Link 52 entities to employees
- [x] Basic query capabilities working

### **Phase 2: Data Sync** (1-2 days)
- [ ] Create `scripts/backfill_sqlite_employees.py`
- [ ] Run backfill to sync PostgreSQL → SQLite
- [ ] Add employee columns to SQLite entity tables
- [ ] Create migration script for schema updates
- [ ] Verify sync worked correctly

### **Phase 3: Extraction Enhancement** (2-3 days)
- [ ] Update `intelligence_capture/extractor.py` with employee detection
- [ ] Update `intelligence_capture/processor.py` with employee linking
- [ ] Test on sample interview to verify attribution works
- [ ] Run on full dataset to populate employee links

### **Phase 4: Consolidation Enhancement** (2 days)
- [ ] Update `intelligence_capture/consolidation_agent.py`
- [ ] Add employee-aware consensus scoring
- [ ] Test consolidation with employee context
- [ ] Verify improved grouping

### **Phase 5: RAG Integration** (2-3 days)
- [ ] Create `intelligence_capture/embeddings/retrieval.py` with filters
- [ ] Create `agent/tools/employee_lookup.py`
- [ ] Update agent prompts to use employee context
- [ ] Test employee-filtered queries

### **Phase 6: Neo4j (Optional)** (2-3 days)
- [ ] Create `scripts/sync_employees_to_neo4j.py`
- [ ] Update `scripts/sync_consolidated_to_neo4j.py`
- [ ] Run initial sync
- [ ] Test graph queries with employee nodes

---

## 🎯 Quick Start (Minimum Viable)

**If you only want to do the essentials:**

```bash
# 1. Backfill SQLite (30 min)
python3 scripts/backfill_sqlite_employees.py

# 2. Update schema (15 min)
sqlite3 data/full_intelligence.db < scripts/migrations/2025_11_12_sqlite_employee_columns.sql

# 3. Test queries (5 min)
sqlite3 data/full_intelligence.db "SELECT * FROM consolidated_entities WHERE employee_id IS NOT NULL LIMIT 5"

# Done! Existing data now has employee context.
```

**For new interviews:**

```bash
# 4. Update extractor (2 hours coding)
# Add employee detection to intelligence_capture/extractor.py

# 5. Test on new interview (10 min)
python3 scripts/test_single_interview.py data/interviews/new_interview_45.json

# Done! New extractions will have employee attribution.
```

---

## 💡 Priority Recommendations

### **Do Now (Essential):**
1. ✅ `scripts/backfill_sqlite_employees.py` - Sync existing data
2. ✅ `scripts/migrations/2025_11_12_sqlite_employee_columns.sql` - Schema update

### **Do Soon (High Value):**
3. 🟡 `intelligence_capture/extractor.py` - Enable attribution for new interviews
4. 🟡 `intelligence_capture/retrieval.py` - Employee-filtered RAG queries

### **Do Later (Nice to Have):**
5. 🟢 `intelligence_capture/consolidation_agent.py` - Better grouping
6. 🟢 `scripts/sync_employees_to_neo4j.py` - Graph capabilities
7. 🟢 `agent/tools/employee_lookup.py` - Agent tool

---

## ⏱️ Time Estimates

| Task | Effort | Value | When |
|------|--------|-------|------|
| Backfill SQLite | 1 hour | High | Now |
| Schema updates | 30 min | High | Now |
| Extraction updates | 1 day | High | When processing new interviews |
| RAG integration | 2 days | High | When building RAG agent |
| Consolidation updates | 2 days | Medium | Later |
| Neo4j sync | 2 days | Low | Only if needed |

**Total for essentials:** ~2 hours
**Total for full integration:** ~8-10 days

---

## 🎁 What You Get

### **After Backfill (2 hours):**
- All SQLite data has employee attribution
- Existing queries can filter by employee
- Ready for analytics

### **After Extraction Updates (1 day):**
- New interviews automatically attribute to employees
- Entity mentions tracked by person
- No manual linking needed

### **After RAG Integration (2 days):**
- Queries like "pain points from COMVERSA Strategists" work
- Personalized responses based on GC profile
- Employee context in all results

### **After Full Integration (10 days):**
- Complete employee attribution across all systems
- Neo4j collaboration graphs
- Advanced organizational analytics
- Full employee intelligence platform

---

**Recommendation:** Start with backfill (2 hours), then add features as needed. Don't build what you don't use yet! 🎯
