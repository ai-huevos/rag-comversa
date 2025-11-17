# Data Integrity & Schema Review - Action Plan

**Analysis Date:** November 16, 2025
**Analyst:** Claude (Data Quality Review)
**Status:** 🔴 CRITICAL ISSUES IDENTIFIED

---

## Executive Summary

**Critical Issues Found:**
1. ✅ **Company linkage broken** - All 44 interviews have `company=""` in source data
2. ✅ **3 entity tables empty** - budget_constraints, knowledge_gaps, team_structures (0 records)
3. ✅ **Schema inconsistencies** - Overlapping concepts, inconsistent naming

**Impact:**
- Cannot relate entities to companies (Los Tajibos, Comversa, Bolivian Foods)
- Missing 18% of entity types (3/16 extractors producing zero results)
- Confusing data model (communication_channels vs systems overlap)

**Opportunity:**
- PostgreSQL has employee→company mappings we can leverage
- Can backfill company data for all 44 interviews
- Can normalize schema for clarity and consistency

---

## Issue 1: Missing Company Linkage 🔴 CRITICAL

### Current State

**Source Data Problem:**
```json
{
  "meta": {
    "company": "",  // ← EMPTY for all 44 interviews
    "respondent": "Samuel Doria Medina Auza",
    "role": "Presidente Ejecutivo"
  }
}
```

**Database Impact:**
```sql
-- interviews table: 44 total, 0 with company
SELECT COUNT(*) FROM interviews;  -- 44
SELECT COUNT(*) FROM interviews WHERE LENGTH(company) > 0;  -- 0

-- All entity tables also missing company
SELECT company FROM pain_points;  -- All empty (276 records)
SELECT company FROM processes;    -- All empty (208 records)
```

**Consequences:**
- ❌ Cannot filter entities by company (Los Tajibos vs Comversa vs Bolivian Foods)
- ❌ Cannot do company-specific analysis or reporting
- ❌ Cannot relate entities to organizational structure
- ❌ Neo4j knowledge graph missing company relationships

### Solution Available ✅

**PostgreSQL employees table has mappings:**
```sql
-- Sample employee→company mappings
employee_id                           | full_name                 | company
--------------------------------------+---------------------------+----------------
COMVERSA_Doria_Medina_Auza_Samuel    | Samuel Doria Medina Auza  | COMVERSA
COMVERSA_Loza_Gabriela               | Gabriela Loza             | COMVERSA
LOS_TAJIBOS_Ferrufino_Hurtado_Javier | Ferrufino Hurtado Javier  | LOS TAJIBOS

-- 3 companies total:
- LOS TAJIBOS
- COMVERSA
- BOLIVIAN FOODS
```

**Backfill Strategy:**
1. Create mapping: `respondent → full_name → company`
2. Update SQLite interviews table with company
3. Update all entity tables with company from interview_id FK
4. Verify Neo4j sync picks up company relationships

### Implementation Plan

**Step 1: Create Employee→Company Mapping Script**
```python
# scripts/backfill_company_data.py
import sqlite3
import psycopg2
from fuzzywuzzy import fuzz

# Load employee mappings from PostgreSQL
employees = get_employees_from_postgres()  # {full_name: company}

# Match interview respondents to employees (fuzzy matching)
conn = sqlite3.connect('data/full_intelligence.db')
interviews = conn.execute("SELECT id, respondent FROM interviews").fetchall()

for interview_id, respondent in interviews:
    company = match_respondent_to_company(respondent, employees)
    if company:
        conn.execute(
            "UPDATE interviews SET company = ? WHERE id = ?",
            (company, interview_id)
        )

# Backfill entity tables via interview_id FK
conn.execute("""
    UPDATE pain_points
    SET company = (
        SELECT company FROM interviews
        WHERE interviews.id = pain_points.interview_id
    )
""")
# Repeat for all 16 entity tables...
```

**Step 2: Validation**
```sql
-- Verify company distribution
SELECT company, COUNT(*)
FROM interviews
GROUP BY company;

-- Expected:
-- LOS TAJIBOS: ~15 interviews
-- COMVERSA: ~20 interviews
-- BOLIVIAN FOODS: ~9 interviews

-- Verify entity linkage
SELECT i.company, COUNT(p.id) as pain_points
FROM interviews i
LEFT JOIN pain_points p ON p.interview_id = i.id
GROUP BY i.company;
```

**Step 3: Update Extraction Pipeline**
- Modify processor.py to enrich company field during ingestion
- Add company lookup from employee table during extraction
- Default to "Unknown" if no employee match found

---

## Issue 2: Empty Entity Tables 🟡 IMPORTANT

### Current State

**Zero Records in 3 Tables:**
```sql
SELECT COUNT(*) FROM budget_constraints;  -- 0
SELECT COUNT(*) FROM knowledge_gaps;      -- 0
SELECT COUNT(*) FROM team_structures;     -- 0
```

**Comparison to Populated Tables:**
```sql
SELECT COUNT(*) FROM communication_channels;  -- 232 ✓
SELECT COUNT(*) FROM systems;                 -- 214 ✓
SELECT COUNT(*) FROM pain_points;             -- 276 ✓
```

**Coverage:**
- ✅ **Populated:** 13/16 entity types (81%)
- ❌ **Empty:** 3/16 entity types (19%)

### Root Cause Analysis

**Hypothesis 1: Extractors Not Running**
- Check: Extractor initialization logs
- Expected: All 16 extractors loaded
- Actual: Need to verify (may be missing from v2_extractors dict)

**Hypothesis 2: ValidationAgent Rejecting**
- Check: Validation logs for these entity types
- Possible: Strict validation rules causing 100% rejection

**Hypothesis 3: Interview Content Lacks These Concepts**
- Check: Manual review of interview transcripts
- Possible: Interviews don't discuss budgets, knowledge gaps, team structures explicitly
- **Most Likely:** Spanish interviews use different terminology

### Investigation Steps

1. **Check Extractor Configuration**
   ```python
   # In extractor.py, verify all 3 are in v2_extractors dict
   self.v2_extractors = {
       "budget_constraints": BudgetConstraintExtractor(OPENAI_API_KEY),
       "knowledge_gaps": KnowledgeGapExtractor(OPENAI_API_KEY),
       "team_structures": TeamStructureExtractor(OPENAI_API_KEY),
       # ...
   }
   ```

2. **Review Extraction Prompts**
   - Check Spanish terminology in prompts
   - Verify examples are culturally appropriate
   - Adjust for Bolivian business context

3. **Test with Manual Extraction**
   ```python
   # Test single interview for these entity types
   extractor = KnowledgeGapExtractor(OPENAI_API_KEY)
   results = extractor.extract_from_interview(interview_1)
   print(f"Knowledge gaps found: {len(results)}")
   ```

4. **Review Validation Logs**
   ```bash
   grep -i "budget\|knowledge\|team" logs/extraction.log
   grep -i "rejected\|failed" logs/extraction.log | grep -i "budget\|knowledge\|team"
   ```

### Remediation Options

**Option A: Improve Prompts (Spanish Context)**
- Add Bolivian/Spanish business terminology
- Provide local examples in prompts
- Adjust entity definitions for cultural context

**Option B: Relax Validation Rules**
- Review ValidationAgent rules for these types
- May be too strict for Spanish content

**Option C: Manual Seeding**
- Identify obvious examples from interviews
- Manually insert to bootstrap extraction
- Use as training examples for improved prompts

**Option D: Accept Low Coverage**
- Document that these concepts rare in interviews
- Mark as optional entity types
- Focus extraction efforts on high-value types

---

## Issue 3: Schema Inconsistencies 🟡 IMPORTANT

### Identified Overlaps

**1. Communication Channels vs Systems**

**Current State:**
- `communication_channels` table (232 records)
- `systems` table (214 records)
- **Overlap:** Communication systems (email, Slack) appear in both

**Example Confusion:**
```sql
-- Is "email" a communication_channel or a system?
communication_channels: "Email corporativo"
systems: "Microsoft Outlook"

-- Both represent the same underlying technology
```

**Proposed:**
- **Option A:** communication_channels are *instances* of systems
  - Relationship: communication_channel.system_id → systems.id
  - Example: "Email Marketing" channel uses "Mailchimp" system

- **Option B:** Merge into single table with type field
  - systems.type = 'communication' | 'operational' | 'financial' | etc.
  - Simpler schema, less confusion

**Recommendation:** Option A (preserve granularity for analytics)

**2. Department vs Domain vs Business Unit**

**Current Columns:**
```sql
-- Inconsistent terminology across tables
pain_points.department TEXT
pain_points.business_unit TEXT
interviews.business_unit TEXT
interviews.department TEXT  -- (not in schema but should be?)
```

**Questions:**
- Is `department` the same as `domain`?
- Is `business_unit` parent of `department`?
- What's the hierarchy: Company → BU → Department → Team?

**Proposed Hierarchy:**
```
Company (Los Tajibos, Comversa, Bolivian Foods)
  ├─ Business Unit (Operations, Sales, IT)
  │   ├─ Department (Maintenance, Customer Service, Infrastructure)
  │   │   ├─ Team (Team Structures table?)
  ```

**Recommended Changes:**
- Standardize on: `business_unit`, `department`, `team_name`
- Remove ambiguous `domain` references
- Add hierarchy constraints/foreign keys

**3. Multiple "Name" Fields**

**Current State:**
```sql
pain_points.description TEXT  -- What is the pain point?
systems.name TEXT             -- What is the system?
systems.description TEXT      -- Additional details
processes.name TEXT           -- What is the process?
```

**Inconsistency:**
- Some entities use `name` (concise identifier)
- Others use `description` (detailed explanation)
- No clear standard on which to use when

**Proposed Standard:**
```sql
-- All entities should have:
name TEXT NOT NULL           -- Short identifier (e.g., "Inventory Management")
description TEXT             -- Detailed explanation (e.g., "Manual tracking...")
category TEXT                -- Type/classification
```

### Schema Normalization Recommendations

**Phase 1: Add Missing Relationships**
```sql
-- 1. Add company hierarchy table
CREATE TABLE organizational_hierarchy (
    id INTEGER PRIMARY KEY,
    company TEXT NOT NULL,
    business_unit TEXT,
    department TEXT,
    team_name TEXT,
    parent_id INTEGER REFERENCES organizational_hierarchy(id)
);

-- 2. Link communication_channels to systems
ALTER TABLE communication_channels
ADD COLUMN system_id INTEGER REFERENCES systems(id);

-- 3. Add standardized naming
-- (Apply to all entity tables that lack it)
ALTER TABLE budget_constraints ADD COLUMN name TEXT;
ALTER TABLE knowledge_gaps ADD COLUMN name TEXT;
```

**Phase 2: Standardize Column Names**
```sql
-- Rename for consistency
ALTER TABLE pain_points RENAME COLUMN department TO team_name;
-- Update all tables to use: company, business_unit, department, team_name

-- Add missing columns
ALTER TABLE interviews ADD COLUMN department TEXT;
ALTER TABLE interviews ADD COLUMN team_name TEXT;
```

**Phase 3: Add Constraints**
```sql
-- Enforce data quality
ALTER TABLE interviews
ADD CONSTRAINT chk_company
CHECK (company IN ('LOS TAJIBOS', 'COMVERSA', 'BOLIVIAN FOODS'));

-- Foreign key from entities to organizational hierarchy
ALTER TABLE pain_points
ADD COLUMN org_id INTEGER REFERENCES organizational_hierarchy(id);
```

---

## Proposed Schema Changes

### High Priority (Data Integrity)

**1. Backfill Company Data**
- **Impact:** Enables company-based filtering and analysis
- **Effort:** 4-6 hours (scripting + validation)
- **Risk:** Low (read from PostgreSQL, write to SQLite)
- **Dependencies:** None

**2. Fix Empty Entity Tables**
- **Impact:** Improves extraction coverage from 81% to 100%
- **Effort:** 8-12 hours (investigation + prompt improvement)
- **Risk:** Medium (may require prompt engineering)
- **Dependencies:** Phase 3 safeguards (for validation)

### Medium Priority (Schema Normalization)

**3. Standardize Organizational Hierarchy**
- **Impact:** Clear company → BU → dept → team structure
- **Effort:** 6-8 hours (schema design + migration)
- **Risk:** Medium (requires data migration)
- **Dependencies:** Company backfill complete

**4. Define Communication Channels ↔ Systems Relationship**
- **Impact:** Clarifies overlap, enables better analysis
- **Effort:** 4-6 hours (relationship modeling)
- **Risk:** Low (additive change, no breaking)
- **Dependencies:** None

### Low Priority (Quality of Life)

**5. Standardize Entity Naming (name vs description)**
- **Impact:** Consistent API and query patterns
- **Effort:** 2-4 hours (add missing columns)
- **Risk:** Low (additive)
- **Dependencies:** None

**6. Add Data Quality Constraints**
- **Impact:** Prevents future data integrity issues
- **Effort:** 2-3 hours (constraint definition)
- **Risk:** Low (validates existing data first)
- **Dependencies:** Company backfill, normalization complete

---

## Implementation Roadmap

### Week 1: Critical Data Integrity

**Day 1-2: Company Backfill**
- [ ] Write employee→company mapping script
- [ ] Fuzzy match respondents to employee full_names
- [ ] Update SQLite interviews.company column
- [ ] Backfill all entity tables via interview_id FK
- [ ] Validate company distribution (3 companies, ~44 interviews)
- [ ] Test Neo4j sync picks up company relationships

**Day 3: Empty Table Investigation**
- [ ] Check extractor initialization for 3 empty types
- [ ] Review extraction logs for validation rejections
- [ ] Manual test extraction for these types
- [ ] Document findings (prompt issue vs data issue vs config)

**Day 4-5: Empty Table Remediation**
- [ ] Improve Spanish prompts if needed
- [ ] Adjust validation rules if too strict
- [ ] Re-run extraction for affected interviews
- [ ] Validate entity counts > 0 for all 16 types

### Week 2: Schema Normalization

**Day 1-2: Organizational Hierarchy**
- [ ] Design org hierarchy table schema
- [ ] Extract unique company/BU/dept/team combinations
- [ ] Create organizational_hierarchy table
- [ ] Populate from existing data
- [ ] Add FK constraints to entity tables

**Day 3: Relationship Modeling**
- [ ] Define communication_channels ↔ systems relationship
- [ ] Add system_id to communication_channels
- [ ] Populate based on name matching
- [ ] Document relationship semantics

**Day 4-5: Naming Standardization**
- [ ] Add missing `name` columns to all entity tables
- [ ] Backfill `name` from `description` (truncate to first sentence)
- [ ] Update extraction prompts to populate both fields
- [ ] Add constraints (name NOT NULL)

### Week 3: Validation & Documentation

**Day 1-2: Data Quality Validation**
- [ ] Run comprehensive data quality checks
- [ ] Verify all 16 entity types have records
- [ ] Verify all interviews have company
- [ ] Check entity→company distribution makes sense

**Day 3: Schema Documentation**
- [ ] Update ARCHITECTURE.md with new schema
- [ ] Create ERD diagram showing relationships
- [ ] Document company/BU/dept/team hierarchy
- [ ] Update API docs with new query patterns

**Day 4-5: Neo4j Sync Verification**
- [ ] Verify consolidated_entities has company
- [ ] Check Neo4j graph includes company nodes
- [ ] Validate company→entity relationships
- [ ] Test company-based queries work correctly

---

## Migration Scripts Needed

### 1. Backfill Company Data

**File:** `scripts/backfill_company_data.py`

```python
"""
Backfill company data for all interviews and entities
Maps respondent names to companies via PostgreSQL employees table
"""

import sqlite3
import psycopg2
from fuzzywuzzy import fuzz, process

def get_employee_mappings():
    """Load employee→company mappings from PostgreSQL"""
    conn = psycopg2.connect(
        dbname="comversa_rag",
        user="postgres",
        host="localhost"
    )

    cur = conn.cursor()
    cur.execute("SELECT full_name, company FROM employees")
    mappings = {row[0]: row[1] for row in cur.fetchall()}

    return mappings

def match_respondent_to_company(respondent, employees, threshold=85):
    """Fuzzy match respondent name to employee full_name"""
    match = process.extractOne(
        respondent,
        employees.keys(),
        scorer=fuzz.token_sort_ratio
    )

    if match and match[1] >= threshold:
        return employees[match[0]]
    return None

def backfill_interviews(db_path):
    """Update interviews.company column"""
    employees = get_employee_mappings()
    conn = sqlite3.connect(db_path)

    interviews = conn.execute(
        "SELECT id, respondent FROM interviews"
    ).fetchall()

    updated = 0
    unmatched = []

    for interview_id, respondent in interviews:
        company = match_respondent_to_company(respondent, employees)

        if company:
            conn.execute(
                "UPDATE interviews SET company = ? WHERE id = ?",
                (company, interview_id)
            )
            updated += 1
        else:
            unmatched.append(respondent)

    conn.commit()

    print(f"Updated: {updated}/{len(interviews)}")
    if unmatched:
        print(f"Unmatched: {unmatched}")

def backfill_entities(db_path):
    """Update entity tables via interview_id FK"""
    conn = sqlite3.connect(db_path)

    entity_tables = [
        'pain_points', 'processes', 'systems', 'kpis',
        'automation_candidates', 'inefficiencies',
        'communication_channels', 'decision_points', 'data_flows',
        'temporal_patterns', 'failure_modes', 'team_structures',
        'knowledge_gaps', 'success_patterns', 'budget_constraints',
        'external_dependencies'
    ]

    for table in entity_tables:
        result = conn.execute(f"""
            UPDATE {table}
            SET company = (
                SELECT company FROM interviews
                WHERE interviews.id = {table}.interview_id
            )
            WHERE company IS NULL OR company = ''
        """)

        print(f"{table}: {result.rowcount} rows updated")

    conn.commit()

if __name__ == "__main__":
    backfill_interviews("data/full_intelligence.db")
    backfill_entities("data/full_intelligence.db")
```

### 2. Create Organizational Hierarchy

**File:** `scripts/create_org_hierarchy.py`

```python
"""
Create organizational hierarchy table
Extract unique company/BU/dept/team combinations
"""

import sqlite3

def create_hierarchy_table(db_path):
    conn = sqlite3.connect(db_path)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS organizational_hierarchy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL,
            business_unit TEXT,
            department TEXT,
            team_name TEXT,
            parent_id INTEGER REFERENCES organizational_hierarchy(id),
            level INTEGER NOT NULL,  -- 0=company, 1=BU, 2=dept, 3=team
            full_path TEXT NOT NULL,  -- "COMVERSA > Operations > Maintenance"
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(company, business_unit, department, team_name)
        )
    """)

    # Create indexes
    conn.execute("CREATE INDEX idx_org_company ON organizational_hierarchy(company)")
    conn.execute("CREATE INDEX idx_org_path ON organizational_hierarchy(full_path)")

    conn.commit()

def populate_hierarchy(db_path):
    """Extract unique org combinations from existing data"""
    conn = sqlite3.connect(db_path)

    # Get unique company/BU/dept combinations
    orgs = conn.execute("""
        SELECT DISTINCT
            company,
            business_unit,
            department
        FROM pain_points
        WHERE company IS NOT NULL
        ORDER BY company, business_unit, department
    """).fetchall()

    for company, bu, dept in orgs:
        # Build hierarchy path
        path_parts = [company]
        if bu: path_parts.append(bu)
        if dept: path_parts.append(dept)

        full_path = " > ".join(path_parts)
        level = len(path_parts) - 1

        conn.execute("""
            INSERT OR IGNORE INTO organizational_hierarchy
            (company, business_unit, department, level, full_path)
            VALUES (?, ?, ?, ?, ?)
        """, (company, bu, dept, level, full_path))

    conn.commit()

    # Report
    count = conn.execute(
        "SELECT COUNT(*) FROM organizational_hierarchy"
    ).fetchone()[0]

    print(f"Created {count} organizational units")

if __name__ == "__main__":
    create_hierarchy_table("data/full_intelligence.db")
    populate_hierarchy("data/full_intelligence.db")
```

---

## Validation Queries

After implementing changes, run these to validate:

```sql
-- 1. Verify all interviews have company
SELECT
    COUNT(*) as total,
    COUNT(CASE WHEN company IS NOT NULL AND company != '' THEN 1 END) as with_company
FROM interviews;
-- Expected: 44, 44

-- 2. Verify company distribution
SELECT company, COUNT(*) as interviews
FROM interviews
GROUP BY company
ORDER BY interviews DESC;
-- Expected: 3 companies (LOS TAJIBOS, COMVERSA, BOLIVIAN FOODS)

-- 3. Verify entity linkage
SELECT
    i.company,
    COUNT(DISTINCT i.id) as interviews,
    COUNT(p.id) as pain_points,
    COUNT(pr.id) as processes,
    COUNT(s.id) as systems
FROM interviews i
LEFT JOIN pain_points p ON p.interview_id = i.id
LEFT JOIN processes pr ON pr.interview_id = i.id
LEFT JOIN systems s ON s.company = i.company
GROUP BY i.company;

-- 4. Verify empty tables are now populated
SELECT
    'budget_constraints' as table_name, COUNT(*) as count FROM budget_constraints
UNION ALL SELECT 'knowledge_gaps', COUNT(*) FROM knowledge_gaps
UNION ALL SELECT 'team_structures', COUNT(*) FROM team_structures;
-- Expected: All > 0

-- 5. Check organizational hierarchy
SELECT level, COUNT(*) as units
FROM organizational_hierarchy
GROUP BY level
ORDER BY level;
-- Expected:
-- 0 (company): 3
-- 1 (business_unit): ~10-15
-- 2 (department): ~20-30
```

---

## Next Steps

**Immediate (This Week):**
1. ✅ Review this document with team
2. ⏳ Decide on implementation priority
3. ⏳ Create tickets for each migration script
4. ⏳ Begin company backfill implementation

**Short-term (Next 2 Weeks):**
1. ⏳ Complete company backfill
2. ⏳ Investigate empty entity tables
3. ⏳ Design organizational hierarchy schema
4. ⏳ Begin schema normalization

**Long-term (Next Month):**
1. ⏳ Complete all schema migrations
2. ⏳ Update Neo4j sync with new relationships
3. ⏳ Document final schema in ARCHITECTURE.md
4. ⏳ Add data quality constraints

---

**Status:** Ready for review and prioritization
**Owner:** TBD
**Estimated Total Effort:** 40-60 hours (2-3 weeks)
