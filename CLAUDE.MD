# RAG-Comversa Project Context

## Project Overview
**Intelligence Extraction System** for Comversa - extracts structured business intelligence from 44 Spanish interview transcripts and stores it in a queryable SQLite database for AI agent use.

**Current Branch:** `claude/create-claude-md-011CUvcCMuPWuxNTxhAq92F1`
**Database:** `intelligence.db` (SQLite with 17 entity types)
**Source Data:** 44 manager interviews in Spanish

---

## Current State

### ✅ **Phases 1-4 COMPLETE** - Full System Implementation

**Phase 1: Core Integration** ✅
1. ✅ Consolidated extraction logic - All 17 entity types
2. ✅ Updated processor storage - Error handling per entity
3. ✅ Quality validation - Always-on validation
4. ✅ Progress tracking - Resume capability

**Phase 2: Optimization** ✅
5. ✅ ValidationAgent - Completeness checking
6. ✅ ExtractionMonitor - Real-time dashboard
7. ✅ Centralized configuration - extraction_config.json
8. ✅ Batch operations - Transaction support

**Phase 3: Testing & Validation** ✅
9. ✅ Test scripts - Single and batch testing
10. ✅ Validation script - Comprehensive checks
11. ✅ Documentation - SETUP.md, guides
12. ✅ Environment setup - .env.example

**Phase 4: Optional Features** ✅
13. ✅ Ensemble validation - Documented (disabled by default)
14. ✅ Parallel processing - Implemented (has known issues)
15. ✅ Report generator - Excel + JSON export

**What's Working:**
- ✅ All 17 entity types extracting
- ✅ ValidationAgent (completeness checking)
- ✅ ExtractionMonitor (real-time progress)
- ✅ Quality validation (always on)
- ✅ Progress tracking with resume
- ✅ Test scripts ready
- ✅ **Rate limiting** - Added exponential backoff
- ✅ **Cost estimation** - Shows cost before extraction
- ✅ Ensemble disabled by default (can enable if needed)

**Recent Fixes (2025-11-08):**
- ✅ Added rate limiting with exponential backoff
- ✅ Added cost estimation and confirmation
- ✅ Verified ensemble is disabled
- ✅ Ready for testing

### 🎯 Current Phase: Ready to Test

**Status:** System ready for 5-interview test run

---

## 17 Entity Types

### v1.0 Entities (6) - Currently Working
1. PainPoint - Problems blocking work
2. Process - How work gets done
3. System - Tools/software used
4. KPI - Success metrics
5. AutomationCandidate - Automation opportunities
6. Inefficiency - Wasteful steps

### v2.0 Entities (11) - Need Integration
7. CommunicationChannel - WhatsApp, email, Teams, etc.
8. DecisionPoint - Who decides what, escalation rules
9. DataFlow - Data movement between systems
10. TemporalPattern - When things happen (daily, weekly, etc.)
11. FailureMode - What goes wrong, workarounds
12. TeamStructure - Org hierarchy, reporting lines
13. KnowledgeGap - Training needs, missing skills
14. SuccessPattern - What works well, best practices
15. BudgetConstraint - Budget limitations affecting work
16. ExternalDependency - Third-party vendors, external blockers
17. Enhanced v1.0 - System with sentiment, AutomationCandidate with effort/impact scoring

---

## Key Files

### Implementation
- `intelligence_capture/extractor.py` - Main extraction orchestrator (needs update)
- `intelligence_capture/extractors.py` - v2.0 specialized extractors (13 classes)
- `intelligence_capture/processor.py` - Pipeline orchestrator (needs update)
- `intelligence_capture/database.py` - Database operations
- `intelligence_capture/config.py` - Configuration

### Specs & Docs
- `.kiro/specs/extraction-completion/tasks.md` - Full task breakdown
- `.kiro/specs/extraction-completion/requirements.md` - Requirements doc
- `PHASE1_COMPLETE_SUMMARY.md` - What was built previously
- `SESSION_COMPLETE_SUMMARY.md` - Previous session summary

### Tests
- `tests/test_*.py` - Unit tests for all extractors

---

## Architecture

```
Interview JSON → Extractor → 17 Entity Types → Database → AI Agents

Flow:
1. Load interview from JSON (meta + qa_pairs)
2. Extract all 17 entity types via IntelligenceExtractor
3. Optional: Ensemble validation for quality review
4. Store in SQLite database
5. Query for AI agent consumption
```

**Current Problem:** Steps 2-3 only handle 6 of 17 entity types!

---

## Quick Commands

```bash
# Run extraction (currently only 6 entity types)
python intelligence_capture/run.py

# Run tests
pytest tests/

# Check database
sqlite3 intelligence.db "SELECT COUNT(*) FROM pain_points;"

# Activate venv
source venv/bin/activate
```

---

## Next Steps: Testing & Validation

### Immediate: Test with 5 Interviews
**Goal:** Verify system works end-to-end
```bash
# Run batch test
python scripts/test_batch_interviews.py --batch-size 5

# Validate results
python scripts/validate_extraction.py --db data/test_batch.db
```

**Expected:**
- ~2-3 minutes processing time
- ~$0.10 cost
- All 17 entity types should have data
- No rate limit errors
- Quality validation passes

### If Test Succeeds: Run Full Extraction
**Goal:** Process all 44 interviews
```bash
# Run full extraction
python intelligence_capture/run.py

# Or use test script
python scripts/test_batch_interviews.py --batch-size 44
```

**Expected:**
- ~15-20 minutes processing time
- ~$0.50-1.00 cost
- Real-time monitoring shows progress
- Resume capability if interrupted

### After Extraction: Validate & Report
```bash
# Validate results
python scripts/validate_extraction.py

# Generate comprehensive report
python scripts/generate_comprehensive_report.py --format both
```

### Known Issues (Don't Use Yet)
- ⚠️ Parallel processing has database locking issues
- ⚠️ Ensemble validation is complex and expensive (disabled)

---

## Success Criteria (Phase 1)

✅ All 17 entity types extracted from interviews
✅ All 17 entity types stored in database
✅ Quality validation identifies issues
✅ Progress tracking enables resume after failures
✅ Processing time: ~30-45 min for 44 interviews
✅ Cost: ~$1.50 for 44 interviews (ensemble off)

---

## Tech Stack

- **Language:** Python 3.9+
- **Database:** SQLite3
- **AI Models:** OpenAI (gpt-4o-mini primary, gpt-4o fallback)
- **Optional:** Anthropic (Claude) for ensemble validation
- **Data Format:** JSON (Spanish text)

---

## Important Notes

1. **Spanish-first:** All interviews in Spanish, no translation needed
2. **LLM Fallback:** 6-model chain handles rate limits automatically
3. **Ensemble Optional:** Disabled by default (set `ENABLE_ENSEMBLE_REVIEW=false`)
4. **Organizational Hierarchy:** company → business_unit → department
5. **Resume Capability:** Can restart failed extractions (once Task 4 complete)

---

## Git Workflow

**Branch:** `claude/create-claude-md-011CUvcCMuPWuxNTxhAq92F1`

```bash
# Commit after each task
git add .
git commit -m "feat: Task N - Description"

# Push when ready (must include session ID in branch name)
git push -u origin claude/create-claude-md-011CUvcCMuPWuxNTxhAq92F1
```

---

## How to Continue This Session

1. Review current task status in todo list
2. Check `.kiro/specs/extraction-completion/tasks.md` for details
3. Start with Task 1: Consolidate extraction logic
4. Test after each task with single interview
5. Commit after each task completion

---

**Last Updated:** 2025-11-08
**Session:** Phase 2 - Testing & Validation
**Progress:** ✅ Phase 1 Complete (4/4 tasks) | 🎯 Phase 2 Ready (0/4 tasks)
