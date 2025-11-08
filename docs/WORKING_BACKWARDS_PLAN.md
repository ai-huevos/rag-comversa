# Working Backwards Plan: Fix & Complete Extraction

## Goal
**One complete database with all 17 entity types, quality data, validated and ready for use.**

---

## Current State Analysis

### What We Have ✅
- ✅ Robust architecture (database schema, config, documentation)
- ✅ 44 interviews ready to process
- ✅ UTF-8 handling fixed
- ✅ Database migration complete (review fields added)

### What's Broken ❌
- ❌ Extractor only extracts 6/17 entity types
- ❌ Ensemble adds complexity without solving core problem
- ❌ No validation queries to check completeness
- ❌ Two databases (full_intelligence.db and intelligence.db) causing confusion

### What's Missing 🔍
- 🔍 Extraction for 11 entity types (v2.0 entities)
- 🔍 Quality validation queries
- 🔍 Completeness checks
- 🔍 Single source of truth database

---

## Working Backwards from Task 16

### Task 16: End-to-End Extraction Pipeline ✅ (Partially Complete)
**Status**: Pipeline exists but incomplete

**What works**:
- ✅ Processes 44 interviews
- ✅ Stores in database
- ✅ Generates reports

**What's broken**:
- ❌ Only extracts 6 entity types
- ❌ Ensemble adds unnecessary complexity

**Fix needed**: Disable ensemble, complete extraction

---

### Task 15: Extraction Quality Validation ❌ (Not Implemented)
**Status**: Ensemble validation exists but wrong approach

**What we need instead**:
1. **Completeness validation**: Check all 17 entity types extracted
2. **Quality queries**: Verify data makes sense
3. **Consistency checks**: Cross-entity validation
4. **Conflict detection**: Find contradictions

**Action**: Create validation queries (not ensemble models)

---

### Tasks 14: Remaining v2.0 Entities ❌ (Not Extracted)
**Status**: Database schema exists, extraction doesn't

**Missing extractions**:
- TeamStructure
- KnowledgeGap
- SuccessPattern
- BudgetConstraint
- ExternalDependency

**Action**: Add extraction methods to extractor.py

---

### Tasks 2-6: Core v2.0 Entities ❌ (Not Extracted)
**Status**: Database schema exists, extraction doesn't

**Missing extractions**:
- CommunicationChannel
- DecisionPoint
- DataFlow
- TemporalPattern
- FailureMode

**Action**: Add extraction methods to extractor.py

---

## The Fix Plan (Working Backwards)

### Phase 1: Disable Ensemble ⏱️ 5 minutes

**Why**: Remove complexity, focus on completeness

**Actions**:
1. Edit `.env`: `ENABLE_ENSEMBLE_REVIEW=false`
2. Verify config loads correctly
3. Test with single interview

**Expected result**: Fast, simple extraction (30s per interview)

---

### Phase 2: Complete the Extractor ⏱️ 2-3 hours

**Goal**: Extract ALL 17 entity types

**Current state** (`extractor.py`):
```python
def extract_all(self, meta, qa_pairs):
    results["pain_points"] = self._extract_pain_points(...)
    results["processes"] = self._extract_processes(...)
    results["systems"] = self._extract_systems(...)
    results["kpis"] = self._extract_kpis(...)
    results["automation_candidates"] = self._extract_automation_candidates(...)
    results["inefficiencies"] = self._extract_inefficiencies(...)
    return results  # Only 6 types!
```

**Target state**:
```python
def extract_all(self, meta, qa_pairs):
    # v1.0 entities (existing)
    results["pain_points"] = self._extract_pain_points(...)
    results["processes"] = self._extract_processes(...)
    results["systems"] = self._extract_systems(...)
    results["kpis"] = self._extract_kpis(...)
    results["automation_candidates"] = self._extract_automation_candidates(...)
    results["inefficiencies"] = self._extract_inefficiencies(...)
    
    # v2.0 entities (ADD THESE)
    results["communication_channels"] = self._extract_communication_channels(...)
    results["decision_points"] = self._extract_decision_points(...)
    results["data_flows"] = self._extract_data_flows(...)
    results["temporal_patterns"] = self._extract_temporal_patterns(...)
    results["failure_modes"] = self._extract_failure_modes(...)
    results["team_structures"] = self._extract_team_structures(...)
    results["knowledge_gaps"] = self._extract_knowledge_gaps(...)
    results["success_patterns"] = self._extract_success_patterns(...)
    results["budget_constraints"] = self._extract_budget_constraints(...)
    results["external_dependencies"] = self._extract_external_dependencies(...)
    
    return results  # All 17 types!
```

**Sub-tasks**:
1. Add `_extract_communication_channels()` method
2. Add `_extract_decision_points()` method
3. Add `_extract_data_flows()` method
4. Add `_extract_temporal_patterns()` method
5. Add `_extract_failure_modes()` method
6. Add `_extract_team_structures()` method
7. Add `_extract_knowledge_gaps()` method
8. Add `_extract_success_patterns()` method
9. Add `_extract_budget_constraints()` method
10. Add `_extract_external_dependencies()` method

**Each method needs**:
- System prompt (what to extract)
- User prompt (interview text)
- JSON schema (expected output)
- Error handling

---

### Phase 3: Update Processor ⏱️ 30 minutes

**Goal**: Store all 17 entity types

**Current state** (`processor.py`):
```python
def process_interview(self, interview):
    entities = self.extractor.extract_all(meta, qa_pairs)
    
    # Store only 6 types
    for pain_point in entities.get("pain_points", []):
        self.db.insert_pain_point(...)
    # ... only 6 types stored
```

**Target state**:
```python
def process_interview(self, interview):
    entities = self.extractor.extract_all(meta, qa_pairs)
    
    # Store all 17 types
    for entity_type, entity_list in entities.items():
        self._store_entities(entity_type, entity_list, interview_id)
```

**Sub-tasks**:
1. Create generic `_store_entities()` method
2. Map entity types to database insert methods
3. Handle errors gracefully
4. Log what was stored

---

### Phase 4: Create Validation Queries ⏱️ 1 hour

**Goal**: Verify extraction completeness and quality

**Create**: `scripts/validate_extraction.py`

**Validation checks**:

1. **Completeness Check**:
```sql
-- All 17 entity types should have data
SELECT 
    'pain_points' as type, COUNT(*) as count FROM pain_points
UNION ALL SELECT 'processes', COUNT(*) FROM processes
-- ... all 17 types
```

Expected: All counts > 0

2. **Quality Check**:
```sql
-- Check for empty descriptions
SELECT COUNT(*) FROM pain_points WHERE description = '' OR description IS NULL;
```

Expected: 0

3. **Consistency Check**:
```sql
-- All entities should link to valid interviews
SELECT COUNT(*) FROM pain_points WHERE interview_id NOT IN (SELECT id FROM interviews);
```

Expected: 0

4. **Spanish Character Check**:
```sql
-- No escape sequences
SELECT COUNT(*) FROM pain_points WHERE description LIKE '%\\u00%';
```

Expected: 0

5. **Company Distribution**:
```sql
-- All companies should have data
SELECT company, COUNT(*) FROM pain_points GROUP BY company;
```

Expected: 3 companies with data

---

### Phase 5: Clean Database Strategy ⏱️ 15 minutes

**Goal**: One clean database, no confusion

**Options**:

**Option A: Fresh Start** (Recommended)
```bash
# Backup old databases
mv data/full_intelligence.db data/archive/full_intelligence_old.db
mv data/intelligence.db data/archive/intelligence_old.db

# Create fresh database
# Run extraction with complete extractor
# Result: One clean database with all 17 entity types
```

**Option B: Merge**
```bash
# Keep full_intelligence.db
# Add missing entity types
# Result: Updated database
```

**Recommendation**: Option A (fresh start) - cleaner, no legacy issues

---

### Phase 6: Test Extraction ⏱️ 5 minutes

**Goal**: Verify one interview extracts all entity types

```bash
cd intelligence_capture
python3 run.py --test
```

**Expected output**:
```
🔍 Extracting from: [Name] ([Role])
  ✓ Pain points: X
  ✓ Processes: X
  ✓ Systems: X
  ✓ KPIs: X
  ✓ Automation candidates: X
  ✓ Inefficiencies: X
  ✓ Communication channels: X  ← NEW!
  ✓ Decision points: X  ← NEW!
  ✓ Data flows: X  ← NEW!
  ✓ Temporal patterns: X  ← NEW!
  ✓ Failure modes: X  ← NEW!
  ✓ Team structures: X  ← NEW!
  ✓ Knowledge gaps: X  ← NEW!
  ✓ Success patterns: X  ← NEW!
  ✓ Budget constraints: X  ← NEW!
  ✓ External dependencies: X  ← NEW!
  ✓ Stored all entities
```

---

### Phase 7: Run Validation ⏱️ 2 minutes

**Goal**: Verify test extraction is complete

```bash
python3 scripts/validate_extraction.py
```

**Expected output**:
```
✅ Completeness: All 17 entity types have data
✅ Quality: No empty descriptions
✅ Consistency: All entities link to valid interviews
✅ UTF-8: No escape sequences
✅ Distribution: All companies represented
```

---

### Phase 8: Full Extraction ⏱️ 22 minutes

**Goal**: Process all 44 interviews with complete extractor

```bash
# Backup (if keeping old data)
cp data/full_intelligence.db data/full_intelligence_backup_$(date +%Y%m%d).db

# Run full extraction
cd intelligence_capture
python3 run.py
```

**Expected**:
- Time: ~22 minutes (30s per interview)
- Cost: ~$1.32 (vs $6.60 with ensemble)
- Result: Complete database with all 17 entity types

---

### Phase 9: Final Validation ⏱️ 5 minutes

**Goal**: Verify complete extraction

```bash
# Run validation
python3 scripts/validate_extraction.py

# Check counts
sqlite3 data/full_intelligence.db "
SELECT 
    'pain_points' as type, COUNT(*) FROM pain_points
UNION ALL SELECT 'processes', COUNT(*) FROM processes
UNION ALL SELECT 'systems', COUNT(*) FROM systems
UNION ALL SELECT 'kpis', COUNT(*) FROM kpis
UNION ALL SELECT 'automation_candidates', COUNT(*) FROM automation_candidates
UNION ALL SELECT 'inefficiencies', COUNT(*) FROM inefficiencies
UNION ALL SELECT 'communication_channels', COUNT(*) FROM communication_channels
UNION ALL SELECT 'decision_points', COUNT(*) FROM decision_points
UNION ALL SELECT 'data_flows', COUNT(*) FROM data_flows
UNION ALL SELECT 'temporal_patterns', COUNT(*) FROM temporal_patterns
UNION ALL SELECT 'failure_modes', COUNT(*) FROM failure_modes
UNION ALL SELECT 'team_structures', COUNT(*) FROM team_structures
UNION ALL SELECT 'knowledge_gaps', COUNT(*) FROM knowledge_gaps
UNION ALL SELECT 'success_patterns', COUNT(*) FROM success_patterns
UNION ALL SELECT 'budget_constraints', COUNT(*) FROM budget_constraints
UNION ALL SELECT 'external_dependencies', COUNT(*) FROM external_dependencies;
"
```

**Expected counts** (approximate):
- pain_points: 100-150
- processes: 150-250
- systems: 150-200
- kpis: 40-60
- automation_candidates: 120-160
- inefficiencies: 80-120
- communication_channels: 200-250
- decision_points: 100-150
- data_flows: 120-160
- temporal_patterns: 150-200
- failure_modes: 40-60
- team_structures: 15-30
- knowledge_gaps: 5-15
- success_patterns: 10-20
- budget_constraints: 5-15
- external_dependencies: 15-30

---

## Quality Over Quantity

### Instead of Ensemble (4 models), Use:

**1. Single Best Model**
- gpt-4o-mini: Fast, cheap, good quality
- OR gpt-4o: Slower, more expensive, better quality

**2. Validation Queries**
- Check completeness
- Check consistency
- Check quality

**3. Spot Checks**
- Manually review 5-10 entities per type
- Verify they make sense
- Adjust prompts if needed

**4. Iterative Improvement**
- Run extraction
- Validate
- Fix prompts
- Re-run if needed

---

## Timeline Summary

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 1 | Disable ensemble | 5 min | Ready |
| 2 | Complete extractor | 2-3 hours | Need to do |
| 3 | Update processor | 30 min | Need to do |
| 4 | Create validation | 1 hour | Need to do |
| 5 | Clean database | 15 min | Ready |
| 6 | Test extraction | 5 min | Ready |
| 7 | Run validation | 2 min | Ready |
| 8 | Full extraction | 22 min | Ready |
| 9 | Final validation | 5 min | Ready |
| **Total** | | **~5 hours** | |

**Breakdown**:
- Development: 3.5 hours (phases 2-4)
- Execution: 30 minutes (phases 6-9)
- Testing: 1 hour (validation and fixes)

---

## Success Criteria

### ✅ Complete
- All 17 entity types extracted
- All 44 interviews processed
- One clean database
- No missing data

### ✅ Quality
- No empty descriptions
- Spanish characters correct
- All entities link to interviews
- Data makes sense

### ✅ Validated
- Completeness checks pass
- Quality checks pass
- Consistency checks pass
- Manual spot checks pass

### ✅ Simple
- Single model extraction
- No ensemble complexity
- Fast processing (22 min)
- Low cost ($1.32)

---

## Next Steps

### Immediate (Now)
1. **Disable ensemble**: Edit `.env`
2. **Review plan**: Confirm approach
3. **Start Phase 2**: Complete the extractor

### Short-term (Today)
1. Add 11 extraction methods to extractor.py
2. Update processor to store all types
3. Create validation queries
4. Test with single interview

### Medium-term (This Week)
1. Run full extraction (44 interviews)
2. Validate results
3. Fix any issues
4. Document final database

---

## Questions to Confirm

1. **Ensemble**: Disable? ✅ Yes - too complex, not worth it
2. **Database**: Fresh start or merge? → Your choice
3. **Model**: gpt-4o-mini (fast/cheap) or gpt-4o (better quality)? → Your choice
4. **Timeline**: 5 hours of work acceptable? → Your choice

---

## The Bottom Line

**Current**: 6 entity types, 4 models, 66 minutes, $6.60, complex
**Target**: 17 entity types, 1 model, 22 minutes, $1.32, simple

**Trade-off**: Less "validation theater", more actual completeness

**Result**: One complete, quality database ready for use

---

Ready to proceed with Phase 1 (disable ensemble)?
