# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# RAG-Comversa Project Context

## Project Overview
**Intelligence Extraction System** for Comversa - extracts structured business intelligence from 44 Spanish interview transcripts and stores it in a queryable SQLite database for AI agent use.

- **Language:** All interviews are in Spanish - never translate
- **Database:** SQLite with 17 entity types
- **AI Models:** OpenAI (gpt-4o-mini primary) with 6-model fallback chain
- **Companies:** Los Tajibos (hotel), Comversa (construction), Bolivian Foods (restaurants)
- **Source Data:** 44 manager interviews in Spanish

---

## 📚 Master Documentation

**Start here**: [docs/README.md](docs/README.md) - Master index to all documentation

### Core Documents
1. **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - System architecture and design
2. **[docs/DECISIONS.md](docs/DECISIONS.md)** - Architecture Decision Records (WHY decisions were made)
3. **[docs/RUNBOOK.md](docs/RUNBOOK.md)** - Operations guide and troubleshooting
4. **[docs/EXPERIMENTS.md](docs/EXPERIMENTS.md)** - Experiment log and lessons learned

### Coding Standards
- **[.ai/CODING_STANDARDS.md](.ai/CODING_STANDARDS.md)** - Unified coding standards for all AI assistants

**Note**: All other documentation has been archived to `docs/archive/2025-11/`. Use the master documents above as the **single source of truth**.

---

## Current State: Honest Assessment

### ⚠️ Status: 80% Complete - 5 Critical Bugs Block Production

#### What's Working ✅
- All 17 entity types extracting correctly
- ValidationAgent (completeness checking)
- ExtractionMonitor (real-time progress)
- LLM fallback chain (99.9% success rate)
- Cost optimization ($0.23 vs $1.50 target)
- Sequential extraction (44 interviews in ~20 minutes)

#### Critical Bugs 🚨
1. **Rate limiting** - No exponential backoff, hits OpenAI rate limits
2. **Database locking** - Parallel processing causes SQLite lock errors
3. **No cost controls** - Missing cost estimation and confirmation
4. **Memory management** - No cleanup of temporary data
5. **Error handling** - Inconsistent error recovery across components

**Verdict**: System works for **single interviews** and **small batches**. Full 44-interview extraction **may fail** due to rate limiting.

**DO NOT**: Run full production extraction until addressing critical bugs above.

**For details**: See [docs/RUNBOOK.md](docs/RUNBOOK.md) Troubleshooting section

---

## Quick Start (5 Minutes)

```bash
# 1. Install dependencies
pip install openai python-dotenv

# 2. Configure API key
cp .env.example .env
echo "OPENAI_API_KEY=sk-proj-your-key-here" >> .env

# 3. Test single interview
python scripts/test_single_interview.py

# 4. See results
sqlite3 intelligence.db "SELECT COUNT(*) FROM pain_points;"
```

**Expected**: ~30 seconds, $0.03, extraction of all 17 entity types

**For complete setup**: See [docs/RUNBOOK.md](docs/RUNBOOK.md) Setup section

---

## 17 Entity Types

**v1.0 Entities (6)**: PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency

**v2.0 Entities (11)**: CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency, Enhanced v1.0

**For details**: See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) Data Model section

---

## Key Architecture Patterns

### Spanish-First Processing (ADR-001)
**NEVER translate** - All content remains in Spanish. UTF-8 encoding everywhere with `ensure_ascii=False`.

**Why**: Translation loses business context critical for AI agents.

**For details**: See [.ai/CODING_STANDARDS.md](.ai/CODING_STANDARDS.md) Spanish Language Patterns

### Multi-Model Fallback Chain (EXP-003)
6-model chain achieves 99.9% success rate:
`gpt-4o-mini → gpt-4o → gpt-3.5-turbo → o1-mini → o1-preview → claude-3-5-sonnet`

**Why**: Graceful degradation with exponential backoff prevents failures.

**For details**: See [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md) EXP-003

### WAL Mode for Parallel Processing (ADR-002, ADR-007)
SQLite WAL mode + shared rate limiter enables concurrent extraction.

**Current status**: ⚠️ Implemented but has bugs - use sequential mode.

**For details**: See [docs/DECISIONS.md](docs/DECISIONS.md) ADR-007

---

## Development Commands

### Testing (ALWAYS test before full extraction)
```bash
# 1. Single interview test (~30s, $0.03)
python scripts/test_single_interview.py

# 2. Batch test - 5 interviews (~3 min, $0.15)
python scripts/test_batch_interviews.py --batch-size 5

# 3. Full extraction - 44 interviews (~20 min, $0.50-1.00)
# ⚠️ WARNING: May fail due to rate limiting bug
python intelligence_capture/run.py
```

### Database Queries
```bash
# Count entities
sqlite3 intelligence.db "SELECT COUNT(*) FROM pain_points;"

# Top systems by usage
sqlite3 intelligence.db "SELECT name, usage_count FROM systems ORDER BY usage_count DESC LIMIT 10;"
```

**For complete commands**: See [docs/RUNBOOK.md](docs/RUNBOOK.md) Common Operations section

---

## Critical Rules

### 🚨 Never Do This
1. **Never translate Spanish content** - Always preserve original Spanish text
2. **Never skip tests** - Always test single → batch → full
3. **Never disable ensemble** unnecessarily - It's already disabled by default (good)
4. **Never build features before fixing bugs** - Fix foundation first (lesson from ADR-009)

### ✅ Always Do This
1. **Always use UTF-8 encoding** - `ensure_ascii=False` in JSON serialization
2. **Always use type hints** - All functions must have type annotations
3. **Always use transactions** - Database operations must be atomic
4. **Always estimate cost** - Show cost before expensive operations
5. **Always check master docs** - Use [docs/](docs/) as single source of truth

**For complete coding standards**: See [.ai/CODING_STANDARDS.md](.ai/CODING_STANDARDS.md)

---

## Next Steps

### Immediate (This Week)
1. **Fix rate limiting bug** - Add exponential backoff (highest priority)
2. **Fix database locking bug** - Investigate WAL mode issues
3. **Add cost controls** - Pre-extraction estimation

### Short-term (Next 2 Weeks)
4. **Fix remaining 2 bugs** - Memory management, error handling
5. **Test full 44-interview extraction** - Verify all bugs fixed
6. **Implement Knowledge Graph consolidation** - Reduce 20-30% duplicates

**For complete roadmap**: See [docs/README.md](docs/README.md) Next Steps section

---

## Configuration

Main config: `config/extraction_config.json`

**Critical settings**:
- `ensemble.enable_ensemble_review`: `false` (KEEP DISABLED - expensive)
- `validation.enable_validation_agent`: `true` (KEEP ENABLED - free quality)
- `performance.parallel_processing`: `true` (⚠️ Has bugs, use sequential)

**For complete configuration**: See [docs/RUNBOOK.md](docs/RUNBOOK.md) Configuration section

---

**Last Updated**: November 9, 2025
**Status**: 🟡 Development (80% complete, 5 critical bugs blocking production)
**Next Milestone**: Fix critical bugs → Full extraction test → Knowledge Graph → Production

**For complete project status**: See [docs/README.md](docs/README.md)
