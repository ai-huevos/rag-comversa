# RAG-Comversa Project Context

## Project Overview
**Intelligence Extraction System** for Comversa - extracts structured business intelligence from 44 Spanish interview transcripts and stores it in a queryable SQLite database for AI agent use.

**Current Branch:** `claude/create-claude-md-011CUvcCMuPWuxNTxhAq92F1`
**Database:** `intelligence.db` (SQLite with 17 entity types)
**Source Data:** 44 manager interviews in Spanish

---

## Current State

### ✅ What's Complete
- Database schema with 17 entity types defined (`intelligence_capture/database.py`)
- v2.0 extractors for 11 new entity types (`intelligence_capture/extractors.py`)
- v1.0 extraction working for 6 entity types (`intelligence_capture/extractor.py`)
- Ensemble validation system (optional, forensic-grade quality review)
- LLM fallback chain (6 models with rate limit handling)
- Configuration system (`config/companies.json`, `config/ceo_priorities.json`)

### ✅ **Phase 1 COMPLETE** - Core Integration (2-3 hours)

**All 4 tasks completed:**
1. ✅ **Task 1:** Consolidated extraction logic - `extractor.py` now uses all 13 v2.0 extractors
2. ✅ **Task 2:** Updated processor storage - Stores all 17 entity types with error handling
3. ✅ **Task 3:** Added quality validation - Validates required fields, descriptions, encoding
4. ✅ **Task 4:** Added progress tracking - Tracks extraction status with resume capability

**What Changed:**
- `extractor.py` now extracts all 17 entity types (v1.0 + v2.0)
- `processor.py` stores all 17 entity types in database
- `validation.py` validates entity quality (always on)
- `database.py` tracks extraction progress (pending/in_progress/complete/failed)
- Resume capability: Can restart failed extractions without reprocessing

### 🎯 Ready For: Phase 2 - Optimization

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

## Next Steps (Phase 1 Tasks)

### Task 1: Consolidate Extraction Logic
**File:** `intelligence_capture/extractor.py`
- Import all 13 extractor classes from `extractors.py`
- Create extractor instances in `__init__()`
- Update `extract_all()` to call all extractors
- Add error handling per extractor

### Task 2: Update Processor Storage
**File:** `intelligence_capture/processor.py`
- Add storage calls for 11 new v2.0 entity types
- Extract business_unit from meta for hierarchy
- Add error handling per entity type

### Task 3: Quality Validation
**New File:** `intelligence_capture/validation.py`
- Validate required fields populated
- Check description length (min 20 chars)
- Check for placeholders ("unknown", "n/a", "tbd")
- Check for encoding issues

### Task 4: Progress Tracking
**File:** `intelligence_capture/database.py`
- Add `extraction_status`, `extraction_attempts`, `last_extraction_error` columns
- Implement status tracking (pending → in_progress → complete/failed)
- Add resume capability

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
**Session:** Phase 1 - Core Integration
**Progress:** ✅ 4/4 tasks complete - PHASE 1 DONE!
