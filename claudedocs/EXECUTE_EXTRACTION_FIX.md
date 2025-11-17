# EXECUTE EXTRACTION FIX - Quick Start Guide

**READ THIS FIRST**: All fixes are already applied. You just need to test and run full extraction.

---

## 🎯 Your Mission

Verify fixes work, then run full extraction to populate 3 empty tables:
- team_structures (0 → 40-100)
- knowledge_gaps (0 → 5-20)
- budget_constraints (0 → 20-40)

---

## ⚡ Quick Execution (Copy-Paste)

### Test (5 minutes)
```bash
# Step 1: Single interview test
python3 scripts/test_single_interview.py

# Expected: team_structures ≥1, budget_constraints ≥1
# If PASS, continue. If FAIL, check claudedocs/cleanup and data restoration.md

# Step 2: Batch test (5 interviews)
python3 scripts/test_batch_interviews.py --batch-size 5

# Expected: team_structures 5-15, budget_constraints 5-10
```

### Backup & Extract (60 minutes)
```bash
# Step 3: Backup current database
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p data/backups
cp data/full_intelligence.db data/backups/full_intelligence_before_fix_${DATE}.db

# Step 4: Full extraction (44 interviews, ~60 min, ~$3 USD)
rm -f data/full_intelligence.db
python3 intelligence_capture/run.py

# Monitor in separate terminal:
watch -n 10 'sqlite3 data/full_intelligence.db "
SELECT
    (SELECT COUNT(*) FROM interviews) as interviews,
    (SELECT COUNT(*) FROM team_structures) as team_structures,
    (SELECT COUNT(*) FROM budget_constraints) as budget_constraints
"'
```

### Validate (5 minutes)
```bash
# Step 5: Check final counts
sqlite3 data/full_intelligence.db "
SELECT 'team_structures' as table_name, COUNT(*) as count FROM team_structures
UNION ALL
SELECT 'budget_constraints', COUNT(*) FROM budget_constraints
UNION ALL
SELECT 'knowledge_gaps', COUNT(*) FROM knowledge_gaps;
"

# Expected:
# team_structures|40-100
# budget_constraints|20-40
# knowledge_gaps|5-20
```

---

## ✅ Success Criteria

- [ ] Single interview test PASSES
- [ ] Batch test PASSES (5/5 interviews)
- [ ] team_structures: 40-100 entities
- [ ] budget_constraints: 20-40 entities
- [ ] knowledge_gaps: 5-20 entities (0 is acceptable)
- [ ] No extraction errors
- [ ] Backup created before full extraction

---

## 🚨 If Something Fails

1. **Tests fail**: Read full details in [claudedocs/cleanup and data restoration.md](cleanup and data restoration.md)
2. **Extraction errors**: Check logs, verify OpenAI API key
3. **Wrong counts**: Validate fixes in STEP 1 of restoration doc
4. **Rollback needed**: `cp data/backups/full_intelligence_before_fix_*.db data/full_intelligence.db`

---

## 📋 What Was Fixed (FYI)

1. **extractors.py**: Changed 3 prompts from array `[]` to object `{"key": [...]}` format
2. **extractors.py**: Added broader keywords to KnowledgeGapExtractor
3. **database.py**: Added `json_serialize()` for list fields (coordinates_with, affected_roles)

See [claudedocs/cleanup and data restoration.md](cleanup and data restoration.md) for technical details.

---

## ⏱️ Time & Cost Estimate

- Testing: 10 minutes
- Full extraction: 60 minutes
- Validation: 5 minutes
- **Total**: ~75 minutes, ~$3 USD

---

## 🎬 After Completion

1. Update this file with actual counts
2. Mark Issue 2 as RESOLVED
3. Move to Issue 3: Schema normalization
4. Report completion to user

---

**Status**: Ready to execute
**Next Action**: Run tests (Step 1)
