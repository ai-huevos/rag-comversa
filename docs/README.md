# System0 - Intelligence Extraction System

**Status**: 🟡 Development (80% complete, 5 critical bugs blocking production)
**Last Updated**: November 9, 2025
**Primary Contact**: Development Team

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

---

## What Is This?

**Intelligence Extraction System** that extracts structured business intelligence from 44 Spanish interview transcripts and stores it in a queryable SQLite database for AI agent use.

**Core Capabilities**:
- ✅ Extracts 17 entity types (pain points, processes, systems, KPIs, etc.)
- ✅ Spanish-first processing (no translation)
- ✅ Multi-company support (Los Tajibos, Comversa, Bolivian Foods)
- ✅ 99.9% extraction success with 6-model LLM fallback chain
- ✅ Rule-based quality validation
- ⚠️ Parallel processing (implemented but has bugs)
- ⚠️ Knowledge Graph consolidation (documented but not implemented)

---

## Current Status: Honest Assessment

### What's Working ✅
- All 17 entity types extracting correctly
- ValidationAgent (completeness checking)
- ExtractionMonitor (real-time progress)
- LLM fallback chain (gpt-4o-mini → gpt-4o → ... → claude-3.5-sonnet)
- Cost optimization ($0.23 vs $1.50 target)
- Sequential extraction (44 interviews in ~20 minutes)

### Critical Bugs 🚨
1. **Rate limiting**: No exponential backoff, hits OpenAI rate limits
2. **Database locking**: Parallel processing causes SQLite lock errors
3. **No cost controls**: Missing cost estimation and confirmation
4. **Memory management**: No cleanup of temporary data
5. **Error handling**: Inconsistent error recovery across components

**Verdict**: System works for **single interviews** and **small batches**. Full 44-interview extraction **may fail** due to rate limiting.

**DO NOT**: Run full production extraction until addressing critical bugs above.

---

## Master Documentation

This is the **single source of truth** for the project. All other documentation is archived.

### Core Documents

1. **[ARCHITECTURE.md](ARCHITECTURE.md)** - System Architecture
   - Component overview and data flow
   - Technical patterns and design decisions
   - Performance characteristics
   - Security considerations

2. **[DECISIONS.md](DECISIONS.md)** - Architecture Decision Records (ADRs)
   - 9 ADRs documenting WHY decisions were made
   - Pattern analysis of successful vs failed decisions
   - Lessons learned and recommendations

3. **[RUNBOOK.md](RUNBOOK.md)** - Operations Guide
   - Setup and configuration (5 minutes)
   - Development workflow
   - Testing hierarchy
   - Troubleshooting guide for 5 critical bugs
   - Emergency procedures

4. **[EXPERIMENTS.md](EXPERIMENTS.md)** - Experiment Log
   - 5 completed experiments with results
   - Pattern analysis of what worked vs what didn't
   - Experiment template and guidelines

### Quick Reference

| Need | Document | Section |
|------|----------|---------|
| System overview | [ARCHITECTURE.md](ARCHITECTURE.md) | Overview |
| Setup instructions | [RUNBOOK.md](RUNBOOK.md) | Setup |
| Why was X built this way? | [DECISIONS.md](DECISIONS.md) | ADR-xxx |
| How do I test? | [RUNBOOK.md](RUNBOOK.md) | Testing |
| What experiments were tried? | [EXPERIMENTS.md](EXPERIMENTS.md) | Completed |
| Known issues | [ARCHITECTURE.md](ARCHITECTURE.md) | Known Issues |
| Troubleshooting | [RUNBOOK.md](RUNBOOK.md) | Troubleshooting |

---

## Development Path

### For New Developers

**Path 1: Understand the System (30 minutes)**
1. Read [ARCHITECTURE.md](ARCHITECTURE.md) - Understand components and data flow
2. Run single interview test - See it work
3. Review [DECISIONS.md](DECISIONS.md) - Understand WHY decisions were made
4. Check [RUNBOOK.md](RUNBOOK.md) troubleshooting - Know the bugs

**Path 2: Fix Critical Bugs (1-2 days)**
1. Read [RUNBOOK.md](RUNBOOK.md) - Understand the 5 critical bugs
2. Pick one bug to fix (start with rate limiting)
3. Document your fix in [DECISIONS.md](DECISIONS.md) as new ADR
4. Test with batch of 5 interviews
5. Move to next bug

**Path 3: Implement Knowledge Graph (1 week)**
1. Read `.kiro/specs/knowledge-graph-consolidation/` - Understand consolidation system
2. Review [DECISIONS.md](DECISIONS.md) ADR-008 - Why was this postponed?
3. Implement Tasks 1-18 from consolidation spec
4. Document experiment in [EXPERIMENTS.md](EXPERIMENTS.md)

### For Production Deployment

**DO NOT deploy until**:
- ✅ All 5 critical bugs are fixed
- ✅ Full 44-interview extraction completes successfully
- ✅ Quality validation shows >85% high confidence
- ✅ Cost controls are working correctly
- ✅ Knowledge Graph consolidation is implemented

**Current estimate**: 1-2 weeks of bug fixes + 1 week for Knowledge Graph

---

## Key Technical Decisions

### Spanish-First Processing (ADR-001)
**Decision**: Extract directly from Spanish interviews, never translate
**Rationale**: Preserves context, reduces cost, maintains accuracy
**Status**: ✅ Implemented, correct decision

### Multi-Model Fallback Chain (from EXP-003)
**Decision**: 6-model chain with exponential backoff
**Rationale**: 99.9% success rate with negligible cost increase
**Status**: ✅ Implemented, highly successful

### Ensemble Validation Disabled (ADR-006)
**Decision**: Built ensemble but disabled by default
**Rationale**: 3-5x cost not justified for quality gain
**Status**: ⚠️ Implemented but disabled, correct decision

### Knowledge Graph Postponed (ADR-008)
**Decision**: Defer consolidation until after bug fixes
**Rationale**: 20-30% duplicate data, but extraction bugs take priority
**Status**: ⏸️ Deferred, spec complete but not implemented

### Feature Before Bugs (ADR-009)
**Decision**: Build Phases 2-4 before fixing Phase 1 bugs
**Rationale**: Excitement about features > fixing foundation
**Status**: 🚨 **Critical mistake** - Created technical debt

**Lesson learned**: Fix bugs before building features.

---

## Quick Commands

### Testing
```bash
# Single interview test (~30s, $0.03)
python scripts/test_single_interview.py

# Batch test - 5 interviews (~3 min, $0.15)
python scripts/test_batch_interviews.py --batch-size 5

# Validate extraction results
python scripts/validate_extraction.py --db data/test_batch.db
```

### Extraction
```bash
# Full extraction - 44 interviews (~20 min, $0.50-1.00)
# ⚠️ WARNING: May fail due to rate limiting bug
python intelligence_capture/run.py

# Resume interrupted extraction
python intelligence_capture/run.py --resume
```

### Database
```bash
# Open database
sqlite3 intelligence.db

# Count entities
SELECT COUNT(*) FROM pain_points;

# Top systems by usage
SELECT name, usage_count FROM systems
ORDER BY usage_count DESC LIMIT 10;
```

---

## Performance Characteristics

### Single Interview
- **Time**: 10-30 seconds
- **Cost**: $0.01-0.03
- **Success Rate**: 99.9%
- **Entities**: ~40-60 entities across 17 types

### Batch (5 interviews)
- **Time**: 2-4 minutes
- **Cost**: $0.05-0.15
- **Success Rate**: 80-100% (depends on rate limiting)
- **Entities**: ~200-300 entities

### Full Extraction (44 interviews)
- **Time**: 15-20 minutes
- **Cost**: $0.50-1.00
- **Success Rate**: ⚠️ **60-80%** (rate limiting issues)
- **Entities**: ~1,600-2,000 entities (20-30% duplicates)

---

## Data Model

### 17 Entity Types

**v1.0 Entities (6)** - Working:
1. **PainPoint** - Problems blocking work
2. **Process** - How work gets done
3. **System** - Tools/software used
4. **KPI** - Success metrics
5. **AutomationCandidate** - Automation opportunities
6. **Inefficiency** - Wasteful steps

**v2.0 Entities (11)** - Integrated:
7. **CommunicationChannel** - WhatsApp, email, Teams
8. **DecisionPoint** - Who decides what
9. **DataFlow** - Data movement between systems
10. **TemporalPattern** - When things happen
11. **FailureMode** - What goes wrong
12. **TeamStructure** - Org hierarchy
13. **KnowledgeGap** - Training needs
14. **SuccessPattern** - What works well
15. **BudgetConstraint** - Budget limitations
16. **ExternalDependency** - Third-party vendors
17. **Enhanced v1.0** - System sentiment, AutomationCandidate scoring

### Organizational Hierarchy

All entities linked to: **company → business_unit → department**

**Companies**:
- Los Tajibos (hotel)
- Comversa (construction)
- Bolivian Foods (restaurants)

---

## Known Issues & Limitations

### Critical Bugs (Block Production)
1. ❌ **Rate limiting** - No exponential backoff
2. ❌ **Database locking** - Parallel processing fails
3. ❌ **Cost controls** - Missing estimation/confirmation
4. ❌ **Memory management** - No cleanup
5. ❌ **Error handling** - Inconsistent recovery

### Design Limitations
1. **Duplicate entities**: 20-30% of extracted data is duplicated
   - "Excel" appears 25 times as separate entries
   - "SAP" appears 12 times as separate entries
   - **Solution**: Knowledge Graph consolidation (documented but not implemented)

2. **No relationships**: Cannot query "Which departments coordinate?"
   - **Solution**: Relationship discovery in Knowledge Graph (not implemented)

3. **No patterns**: Cannot identify "What pain points affect most interviews?"
   - **Solution**: Pattern recognition in Knowledge Graph (not implemented)

### Performance Limitations
1. **Sequential only**: Parallel processing has bugs
2. **Rate limited**: Full extraction may fail
3. **Memory intensive**: No streaming for large batches

---

## Success Metrics

### Current Achievement
- ✅ **Extraction accuracy**: 99.9% success rate
- ✅ **Cost optimization**: $0.23 vs $1.50 target (85% reduction)
- ✅ **Entity coverage**: All 17 types extracting
- ✅ **Quality validation**: 80% automated validation working
- ⚠️ **Production readiness**: 80% complete (5 bugs blocking)

### Production Goals
- 🎯 **Extraction success**: >95% for full 44 interviews
- 🎯 **Quality confidence**: >85% high confidence entities
- 🎯 **Cost per interview**: <$0.05
- 🎯 **Processing time**: <15 minutes for 44 interviews
- 🎯 **Duplicate rate**: <10% after Knowledge Graph consolidation

---

## Next Steps

### Immediate (This Week)
1. **Fix rate limiting bug** (highest priority)
   - Add exponential backoff to `_call_gpt4()`
   - Test with batch of 10 interviews
   - Document in [DECISIONS.md](DECISIONS.md)

2. **Fix database locking bug**
   - Investigate SQLite WAL mode issues
   - Test parallel processing with 5 workers
   - Document in [DECISIONS.md](DECISIONS.md)

3. **Add cost controls**
   - Pre-extraction cost estimation
   - User confirmation before expensive operations
   - Document in [DECISIONS.md](DECISIONS.md)

### Short-term (Next 2 Weeks)
4. **Fix remaining 2 bugs** (memory, error handling)
5. **Test full 44-interview extraction** (verify all bugs fixed)
6. **Implement Knowledge Graph consolidation** (reduce duplicates)

### Medium-term (Next Month)
7. **Deploy to production** (after all bugs fixed)
8. **Build AI agents** (use consolidated data)
9. **Generate insights** (patterns, relationships, recommendations)

---

## Contributing

### Before Making Changes

1. **Read the docs**:
   - [ARCHITECTURE.md](ARCHITECTURE.md) - Understand the system
   - [DECISIONS.md](DECISIONS.md) - Understand WHY things are this way
   - [RUNBOOK.md](RUNBOOK.md) - Know the bugs and procedures

2. **Test your changes**:
   - Always test with single interview first
   - Then test with batch of 5 interviews
   - Document any new patterns in [EXPERIMENTS.md](EXPERIMENTS.md)

3. **Document your decisions**:
   - Add new ADR to [DECISIONS.md](DECISIONS.md) for significant changes
   - Update [EXPERIMENTS.md](EXPERIMENTS.md) if you tried something new
   - Update [RUNBOOK.md](RUNBOOK.md) if you changed operations

### Coding Standards

See `.ai/CODING_STANDARDS.md` for unified coding standards that work across Cursor, Kiro, and Claude Code.

---

## Project History

### Timeline
- **Oct 22-23, 2025**: Initial extraction system (v1.0 - 6 entity types)
- **Oct 24-25, 2025**: Added v2.0 entities (11 new types)
- **Oct 26-28, 2025**: Built ValidationAgent, ExtractionMonitor, ensemble
- **Oct 29-30, 2025**: Discovered bugs, began troubleshooting
- **Nov 7, 2025**: QA review - rated 4.25/5.0 (80% production ready)
- **Nov 8, 2025**: Truth audit - identified 5 critical bugs
- **Nov 9, 2025**: Documentation consolidation, ADR creation

### Key Lessons

**What Worked**:
- ✅ Starting simple (6 entity types) then expanding
- ✅ Multi-model fallback chain (99.9% success)
- ✅ Rule-based validation (80% quality at 0% cost)
- ✅ Spanish-first processing (preserved context)

**What Didn't**:
- ❌ Building features before fixing bugs (created technical debt)
- ❌ Ensemble validation (3-5x cost, not justified)
- ❌ Parallel processing without proper testing (database locking)
- ❌ Skipping cost controls (risky for production)

**Pattern to Avoid**:
> "Build Phase 1 → Discover bugs → Skip fixes → Build Phase 2"

**Better Pattern**:
> "Build Phase 1 → Test → Fix bugs → Then Phase 2"

---

## Support

### Questions?
1. Check [RUNBOOK.md](RUNBOOK.md) troubleshooting section
2. Review [DECISIONS.md](DECISIONS.md) for context on decisions
3. Read [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
4. Check [EXPERIMENTS.md](EXPERIMENTS.md) for similar attempts

### Found a Bug?
1. Check [ARCHITECTURE.md](ARCHITECTURE.md) Known Issues - is it documented?
2. Check [RUNBOOK.md](RUNBOOK.md) Troubleshooting - known workaround?
3. Document in [DECISIONS.md](DECISIONS.md) as new ADR if significant
4. Create GitHub issue with reproduction steps

### Have an Idea?
1. Document as experiment in [EXPERIMENTS.md](EXPERIMENTS.md)
2. Test with single interview first
3. Measure impact (cost, time, quality)
4. Document results before moving to production

---

## License

[Add license information]

---

## Archived Documentation

All previous documentation (81 files) has been archived to `docs/archive/2025-11/`.

**Reason for consolidation**: Multiple conflicting documents, unclear source of truth, documentation vs reality gap.

**Master documents** (this folder) are now the **single source of truth**.

---

**Last Updated**: November 9, 2025
**Status**: 🟡 Development (80% complete, 5 critical bugs blocking production)
**Next Milestone**: Fix critical bugs → Full extraction test → Knowledge Graph → Production
