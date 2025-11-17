# Cleanup and Data Restoration Plan - Issue 2: Empty/Sparse Tables

**Status**: Ready for execution
**Date**: 2025-11-16
**Issue**: 3 entity types not extracting (team_structures, knowledge_gaps, budget_constraints)
**Root Cause**: JSON format mismatch between prompts and response format

---

## Fixes Applied

### 1. JSON Format Alignment (extractors.py)
**Files Modified**: `intelligence_capture/extractors.py`

**Problem**: Prompts requested JSON arrays `[]` but `response_format={"type": "json_object"}` forces object `{}` format

**Fixed Extractors**:
- TeamStructureExtractor (line ~3051-3066)
- BudgetConstraintExtractor (line ~3359-3374)
- KnowledgeGapExtractor (line ~3160-3174)

**Changes**:
```python
# BEFORE (incorrect - array format)
Return as JSON array:
[{...}]
If no data found, return empty array [].

# AFTER (correct - object format)
Return as JSON object with this structure:
{
  "entity_type": [
    {...}
  ]
}
If no data found, return {"entity_type": []}.
```

**Also Added**: Defensive parsing to handle both formats:
```python
result if isinstance(result, list) else result.get("team_structures", [])
```

### 2. Broader Keywords (KnowledgeGapExtractor)
**Line**: ~3093-3102

**Added Keywords**:
```python
# Broader terms to catch implicit gaps
"problema", "dificultad", "no funciona", "difícil",
"complicado", "no me queda claro", "me cuesta"
```

### 3. Database Serialization Fix (database.py)
**Files Modified**: `intelligence_capture/database.py`

**Problem**: Lists not converted to JSON strings before database insert

**Fixed Methods**:
- `insert_team_structure()` (line ~2257-2258)
- `insert_knowledge_gap()` (line ~2282)

**Changes**:
```python
# BEFORE (incorrect - inserts Python list object)
team.get("coordinates_with", "")
gap.get("affected_roles", "")

# AFTER (correct - JSON serialization)
json_serialize(team.get("coordinates_with", []))
json_serialize(gap.get("affected_roles", []))
```

---

## Execution Plan for Claude Agent

### STEP 1: Verify Fixes Are Applied

```bash
# Check extractors.py changes
grep -A 5 "Return as JSON object with this structure" intelligence_capture/extractors.py | head -30

# Expected: Should see 3 occurrences (team_structures, knowledge_gaps, budget_constraints)
# Each should show {"entity_type": [...]} format

# Check database.py changes
grep "json_serialize.*coordinates_with\|json_serialize.*affected_roles" intelligence_capture/database.py

# Expected output:
# json_serialize(team.get("coordinates_with", []))
# json_serialize(gap.get("affected_roles", []))
```

**Validation**: If grep returns no results, fixes need to be re-applied from this document.

---

### STEP 2: Single Interview Test

```bash
# Delete existing test database
rm -f data/test_single.db

# Run single interview test
python3 scripts/test_single_interview.py

# Expected output:
#  Team Structures: 1-3
#  Knowledge Gaps: 0-3 (rare, depends on interview)
#  Budget Constraints: 1-2
# Total entities: 68-75
```

**Success Criteria**:
- team_structures: e1 entity
- budget_constraints: e1 entity
- knowledge_gaps: e0 entities (acceptable to be 0, this is rare)
- NO errors during extraction

**If Failed**:
```bash
# Check for errors
python3 scripts/test_single_interview.py 2>&1 | grep -i "error\|exception\|traceback"

# Verify database schema
sqlite3 data/test_single.db ".schema team_structures"
sqlite3 data/test_single.db ".schema knowledge_gaps"
```

---

### STEP 3: Batch Test (5 Interviews)

```bash
# Run batch test
python3 scripts/test_batch_interviews.py --batch-size 5

# Expected output:
#  Team Structures: 5-15 entities
#  Knowledge Gaps: 0-5 entities
#  Budget Constraints: 5-10 entities
# Success rate: 100% (5/5 interviews)
```

**Success Criteria**:
- All 5 interviews process successfully
- team_structures: 5-15 total
- budget_constraints: 5-10 total
- No database errors

**Validation Query**:
```bash
sqlite3 data/test_batch.db "
SELECT
    'team_structures' as table_name,
    COUNT(*) as count,
    COUNT(DISTINCT interview_id) as interviews
FROM team_structures
UNION ALL
SELECT 'budget_constraints', COUNT(*), COUNT(DISTINCT interview_id)
FROM budget_constraints
UNION ALL
SELECT 'knowledge_gaps', COUNT(*), COUNT(DISTINCT interview_id)
FROM knowledge_gaps;
"
```

**Expected**:
```
team_structures|5-15|3-5
budget_constraints|5-10|3-5
knowledge_gaps|0-5|0-3
```

---

### STEP 4: Data Restoration - Backup Current Database

```bash
# Create backup before full extraction
DATE=$(date +%Y%m%d_%H%M%S)
cp data/full_intelligence.db data/backups/full_intelligence_before_fix_${DATE}.db

# Verify backup
sqlite3 data/backups/full_intelligence_before_fix_${DATE}.db "SELECT COUNT(*) FROM interviews"

# Expected: 44 (all interviews)
```

---

### STEP 5: Full Extraction (44 Interviews)

**  CRITICAL**: This will take ~30-60 minutes and cost ~$2-5 USD

```bash
# Clear existing database (AFTER backup in Step 4)
rm -f data/full_intelligence.db

# Run full extraction
python3 intelligence_capture/run.py

# Monitor progress (in separate terminal)
watch -n 10 'sqlite3 data/full_intelligence.db "
SELECT
    (SELECT COUNT(*) FROM interviews) as interviews_processed,
    (SELECT COUNT(*) FROM team_structures) as team_structures,
    (SELECT COUNT(*) FROM knowledge_gaps) as knowledge_gaps,
    (SELECT COUNT(*) FROM budget_constraints) as budget_constraints
"'
```

**Expected Final Counts** (44 interviews):
```
interviews_processed: 44
team_structures: 40-100
knowledge_gaps: 5-20
budget_constraints: 20-40
```

**Success Criteria**:
- All 44 interviews processed
- team_structures: 40-100 entities
- budget_constraints: 20-40 entities
- knowledge_gaps: 5-20 entities (acceptable lower bound: 0)

---

### STEP 6: Data Quality Validation

```bash
# Run comprehensive validation
sqlite3 data/full_intelligence.db << 'EOF'
-- Entity counts by type
SELECT
    'Pain Points' as entity_type, COUNT(*) as count FROM pain_points
UNION ALL SELECT 'Processes', COUNT(*) FROM processes
UNION ALL SELECT 'Systems', COUNT(*) FROM systems
UNION ALL SELECT 'KPIs', COUNT(*) FROM kpis
UNION ALL SELECT 'Automation Candidates', COUNT(*) FROM automation_candidates
UNION ALL SELECT 'Inefficiencies', COUNT(*) FROM inefficiencies
UNION ALL SELECT 'Communication Channels', COUNT(*) FROM communication_channels
UNION ALL SELECT 'Decision Points', COUNT(*) FROM decision_points
UNION ALL SELECT 'Data Flows', COUNT(*) FROM data_flows
UNION ALL SELECT 'Temporal Patterns', COUNT(*) FROM temporal_patterns
UNION ALL SELECT 'Failure Modes', COUNT(*) FROM failure_modes
UNION ALL SELECT 'Team Structures', COUNT(*) FROM team_structures
UNION ALL SELECT 'Knowledge Gaps', COUNT(*) FROM knowledge_gaps
UNION ALL SELECT 'Success Patterns', COUNT(*) FROM success_patterns
UNION ALL SELECT 'Budget Constraints', COUNT(*) FROM budget_constraints
UNION ALL SELECT 'External Dependencies', COUNT(*) FROM external_dependencies
ORDER BY entity_type;

-- Check JSON serialization for arrays
.mode column
.headers on
SELECT
    id,
    role,
    coordinates_with,
    external_dependencies
FROM team_structures
LIMIT 3;

-- Verify arrays are JSON strings, not Python repr
-- Expected: ["role1", "role2"] format
-- NOT: ['role1', 'role2'] or role1, role2
EOF
```

**Quality Checks**:
1. **No Python list repr**: `coordinates_with` should be `["x","y"]` NOT `['x','y']`
2. **UTF-8 encoding**: No mojibake (Ã¡, Ã©, etc.)
3. **Confidence scores**: Most entities should have confidence e0.7
4. **No NULL required fields**: role, area, etc. should not be NULL

---

### STEP 7: Compare Before/After

```bash
# Generate comparison report
python3 << 'EOF'
import sqlite3
from datetime import datetime

# Old database (backup)
old_db = sqlite3.connect('data/backups/full_intelligence_before_fix_*.db')
# New database (after fix)
new_db = sqlite3.connect('data/full_intelligence.db')

tables = ['team_structures', 'knowledge_gaps', 'budget_constraints']

print("=" * 70)
print(f"EXTRACTION COMPARISON REPORT - {datetime.now()}")
print("=" * 70)

for table in tables:
    old_count = old_db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    new_count = new_db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    delta = new_count - old_count
    pct = ((new_count / old_count - 1) * 100) if old_count > 0 else float('inf')

    print(f"\n{table.upper()}:")
    print(f"  Before: {old_count:4d}")
    print(f"  After:  {new_count:4d}")
    print(f"  Delta:  {delta:+4d} ({pct:+.1f}%)")

old_db.close()
new_db.close()
EOF
```

**Expected Output**:
```
TEAM_STRUCTURES:
  Before:    0
  After:    55
  Delta:  +55 (+inf%)

KNOWLEDGE_GAPS:
  Before:    0
  After:    12
  Delta:  +12 (+inf%)

BUDGET_CONSTRAINTS:
  Before:    0
  After:    28
  Delta:  +28 (+inf%)
```

---

### STEP 8: Update Documentation

```bash
# Update data integrity report
cat > reports/data_integrity_post_fix.md << 'EOF'
# Data Integrity Report - Post Issue 2 Fix

**Date**: $(date +%Y-%m-%d)
**Status**:  COMPLETE

## Fixed Entity Types
- team_structures: 0 ’ XX entities
- knowledge_gaps: 0 ’ XX entities
- budget_constraints: 0 ’ XX entities

## Root Causes Fixed
1. JSON format mismatch (prompts vs response_format)
2. Missing JSON serialization for array fields
3. Overly strict keywords (knowledge_gaps)

## Next Steps
- Move to Issue 3: Schema normalization
- Continue to Issue 4: Consolidation review
EOF

# Fill in actual counts
sqlite3 data/full_intelligence.db "
SELECT '- team_structures: 0 ’ ' || COUNT(*) || ' entities'
FROM team_structures
UNION ALL
SELECT '- knowledge_gaps: 0 ’ ' || COUNT(*) || ' entities'
FROM knowledge_gaps
UNION ALL
SELECT '- budget_constraints: 0 ’ ' || COUNT(*) || ' entities'
FROM budget_constraints
" >> reports/data_integrity_post_fix.md
```

---

## Rollback Plan (If Issues Occur)

```bash
# Restore backup
DATE=20251116_HHMMSS  # Use actual backup timestamp
cp data/backups/full_intelligence_before_fix_${DATE}.db data/full_intelligence.db

# Verify restoration
sqlite3 data/full_intelligence.db "
SELECT COUNT(*) FROM interviews;
SELECT COUNT(*) FROM team_structures;
SELECT COUNT(*) FROM knowledge_gaps;
"
```

---

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Single interview test | PASS | ó |
| Batch test (5) | 100% success | ó |
| team_structures | 40-100 entities | ó |
| knowledge_gaps | 5-20 entities | ó |
| budget_constraints | 20-40 entities | ó |
| No extraction errors | 0 errors | ó |
| UTF-8 encoding | No mojibake | ó |
| JSON serialization | Correct format | ó |

---

## Estimated Resources

- **Time**: 60-90 minutes total
  - Testing: 15 minutes
  - Full extraction: 45-60 minutes
  - Validation: 15 minutes
- **Cost**: $2-5 USD (44 interviews × 17 extractors × OpenAI API)
- **Disk**: ~50MB additional (new database)

---

## Next Actions After Completion

1.  Mark Issue 2 as RESOLVED in data integrity report
2. =Ë Move to Issue 3: Schema normalization (communication_channels overlap, naming inconsistencies)
3. = Continue to Issue 4: Consolidation review and Neo4j sync
4. =Ê Generate final data quality dashboard

---

## Emergency Contacts

- **Rollback**: See Rollback Plan section above
- **Cost overrun**: Check CostGuard settings in `.env`
- **Rate limits**: Reduce concurrency or add delays in rate_limiter.py

---

**Document Status**: Ready for execution
**Last Updated**: 2025-11-16
**Next Review**: After Step 8 completion
