# Experiments Log

**Purpose**: Track technical experiments, results, and lessons learned
**Format**: Chronological log of experiments with outcomes
**Last Updated**: 2025-11-09

---

## Experiment Index

| ID | Experiment | Status | Date | Outcome |
|----|-----------|--------|------|---------|
| [EXP-001](#exp-001-ensemble-validation-3-model) | Ensemble Validation (3-model) | ✅ Complete | 2025-11-08 | Implemented but disabled |
| [EXP-002](#exp-002-parallel-processing-with-wal) | Parallel Processing with WAL | ❌ Failed | 2025-11-08 | Database locking issues |
| [EXP-003](#exp-003-llm-fallback-chain) | LLM Fallback Chain (6 models) | ✅ Success | 2025-11-07 | In production |
| [EXP-004](#exp-004-17-entity-types) | 17 Entity Types (v1.0 + v2.0) | ✅ Success | 2025-11-07 | In production |
| [EXP-005](#exp-005-rule-based-validation) | Rule-Based Validation | ✅ Success | 2025-11-08 | In production |
| [EXP-006](#exp-006-rag-20-phase-1-qa-validation) | RAG 2.0 Phase 1 QA Validation | ⚠️ CONDITIONAL GO | 2025-11-09 | Remediation required |

---

## Experiments

### EXP-001: Ensemble Validation (3-Model)

**Date**: 2025-11-08
**Status**: ✅ **Complete** (Implemented but disabled)
**Related**: [ADR-006](DECISIONS.md#adr-006-ensemble-validation-decision)

#### Hypothesis
Multiple LLMs cross-validating will improve extraction quality by 30-40%.

#### Setup
```
Interview → Extract with 3 models in parallel
         → GPT-4o-mini → Result A
         → GPT-4o → Result B
         → Claude-3.5 → Result C
         → Compare results → Select consensus or best answer
```

#### Configuration
```json
{
  "ensemble": {
    "enable_ensemble_review": true,
    "models": ["gpt-4o-mini", "gpt-4o", "claude-3-5-sonnet"],
    "comparison_method": "consensus",
    "consensus_threshold": 0.67
  }
}
```

#### Results

**Quality Improvement**:
- ✅ 15-25% better accuracy (measured by manual review of 10 interviews)
- ✅ Fewer empty/placeholder responses
- ✅ More consistent entity formatting

**Cost & Performance**:
- ❌ 3-5x cost increase ($0.50 → $2.50-5.00 for 44 interviews)
- ❌ 3-5x time increase (20 min → 60-100 min)
- ❌ Complex result merging logic

**Comparison Logic Complexity**:
- Consensus method: Simple majority vote
- BUT: Merging different JSON structures is hard
- Edge cases: 3 different answers with no consensus
- Result: Complex code for marginal benefit

#### Decision
**Implemented but disabled by default** (ADR-006)

**Rationale**:
- Quality improvement not worth 3-5x cost
- Single model + ValidationAgent sufficient for most cases
- Leave available for critical extractions only

#### Lessons Learned
1. **Cost-benefit matters**: 25% quality improvement ≠ 300% cost increase
2. **Consensus is hard**: Merging different LLM outputs is complex
3. **Single model + validation**: Simpler, cheaper, good enough
4. **Better approach**: Knowledge Graph consolidation across interviews (not multiple models per interview)

#### Recommendation
**Remove ensemble code in future cleanup** - adds complexity without value.

**Better investment**: Knowledge Graph consolidation for cross-interview validation.

---

### EXP-002: Parallel Processing with WAL

**Date**: 2025-11-08
**Status**: ❌ **Failed** (Database locking issues)
**Related**: [ADR-007](DECISIONS.md#adr-007-parallel-processing)

#### Hypothesis
SQLite WAL mode + ProcessPoolExecutor will enable 2-3x speedup for 44-interview extraction.

#### Setup
```python
# 4 parallel workers, each processing ~11 interviews
with ProcessPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_interview, i)
               for i in interviews]
    results = [f.result() for f in futures]
```

#### Database Configuration
```python
# Enable WAL mode for better concurrency
conn = sqlite3.connect('intelligence.db')
conn.execute('PRAGMA journal_mode=WAL')
conn.execute('PRAGMA foreign_keys=ON')
```

#### Expected Results
- **Sequential**: 20 minutes for 44 interviews
- **Parallel (4 workers)**: 7-8 minutes for 44 interviews
- **Speedup**: 2.5-3x faster

#### Actual Results
```
Error: database is locked
SQLite3.OperationalError: database is locked

Worker 1: Processing interview 3... ✓
Worker 2: Processing interview 5... ❌ Database locked
Worker 3: Processing interview 7... ❌ Database locked
Worker 4: Processing interview 9... ❌ Database locked
```

**Failure Mode**:
- Workers process interviews successfully
- Workers attempt to write to database simultaneously
- SQLite locks database for first writer
- Other writers timeout with "database is locked" error
- Extraction fails

#### Root Cause Analysis
**SQLite Limitation**: SQLite is designed for single-writer, multiple-readers
- WAL mode improves concurrency but doesn't solve parallel writes
- Write Ahead Log allows readers to continue while writer works
- BUT: Still only one writer at a time
- Parallel writers = lock contention = failures

#### Attempted Fixes

**Attempt 1: Increase timeout**
```python
conn = sqlite3.connect('intelligence.db', timeout=30.0)
```
- Result: ❌ Still fails, just takes longer

**Attempt 2: Retry with exponential backoff**
```python
for attempt in range(5):
    try:
        db.insert(entity)
        break
    except sqlite3.OperationalError:
        time.sleep(2 ** attempt)
```
- Result: ❌ Sometimes works, but unreliable

**Attempt 3: Different isolation level**
```python
conn.isolation_level = 'DEFERRED'
```
- Result: ❌ No improvement

#### Why WAL Mode Wasn't Enough

**WAL mode solves**:
- ✅ Readers don't block readers
- ✅ Readers don't block writers
- ✅ Better crash recovery

**WAL mode DOESN'T solve**:
- ❌ Writers don't block writers (still lock)
- ❌ Parallel writes (only one writer at a time)

#### Decision
**Abandon parallel processing** (for now)

**Reasoning**:
- SQLite not suitable for parallel writes
- Sequential mode works reliably (20 min is acceptable)
- Parallel optimization is premature

#### Potential Fixes (Not Implemented)

**Option A: Write Queue** (recommended)
```python
# Single writer thread, multiple worker threads
write_queue = Queue()
writer_thread = Thread(target=db_writer, args=(write_queue,))

# Workers extract entities and queue writes
def worker(interview):
    entities = extract(interview)
    write_queue.put((interview_id, entities))
```
- Pros: Simple, works with SQLite
- Cons: Adds threading complexity

**Option B: Database per Worker**
```python
# Each worker has own database
worker_dbs = [f"intelligence_worker_{i}.db" for i in range(4)]
# Merge databases after completion
```
- Pros: True parallel writes
- Cons: Complex merge logic

**Option C: PostgreSQL**
```python
# Replace SQLite with PostgreSQL
# True parallel write support
```
- Pros: Solves problem completely
- Cons: Adds deployment complexity, overkill for 44 interviews

#### Lessons Learned
1. **SQLite limitations**: WAL mode ≠ parallel write support
2. **Test early**: Should have tested with 2 workers first, not jumped to 4
3. **Don't assume**: "WAL mode enables concurrency" doesn't mean "parallel writes work"
4. **Sequential is OK**: 20 minutes for 44 interviews is acceptable, premature optimization

#### Recommendation
**Fix if needed for scale**: Use write queue if extraction time becomes bottleneck.

**Current priority**: Low (sequential mode works, parallel is optimization)

---

### EXP-003: LLM Fallback Chain

**Date**: 2025-11-07
**Status**: ✅ **Success** (In production)
**Related**: [ADR-004](DECISIONS.md#adr-004-llm-fallback-chain)

#### Hypothesis
6-model fallback chain will make extraction resilient to API failures.

#### Setup
```
Try gpt-4o-mini (3x with exponential backoff)
  ↓ If fails
Try gpt-4o (3x)
  ↓ If fails
Try gpt-3.5-turbo (3x)
  ↓ If fails
Try o1-mini (3x)
  ↓ If fails
Try o1-preview (3x)
  ↓ If fails
Try claude-3-5-sonnet (3x)
  ↓ If all fail
Raise exception
```

#### Test Results

**Success Rate**:
```
gpt-4o-mini: 98% success (first attempt)
gpt-4o: 1.5% needed (after gpt-4o-mini failures)
Other models: 0.5% needed (rare edge cases)
Total success rate: 99.9%
```

**Performance**:
- Average latency: 2-4 seconds (gpt-4o-mini)
- Fallback latency: +10-30 seconds (if needed)
- Worst case: 2-3 minutes (falls through entire chain)

**Cost**:
- 98% of extractions: $0.001-0.002 per entity (gpt-4o-mini)
- 2% of extractions: $0.004-0.006 per entity (gpt-4o or higher)
- Minimal cost increase from fallback

#### Decision
**Adopt 6-model fallback chain** (ADR-004)

#### Benefits
1. **Resilience**: System survives API outages
2. **Cost-optimized**: Starts with cheapest model
3. **Quality guarantee**: Eventually gets response
4. **Multi-provider**: OpenAI + Anthropic redundancy

#### Issues Encountered
1. **Different response formats**: o1 models return different JSON structure
2. **Rate limits differ**: Claude has different limits than OpenAI
3. **API key management**: Need both OpenAI and Anthropic keys

#### Lessons Learned
1. **Fallback chains work**: Dramatically improve reliability
2. **Start cheap**: 98% success with cheapest model is excellent
3. **Test edge cases**: Ensure fallback logic handles all model response formats

---

### EXP-004: 17 Entity Types (v1.0 + v2.0)

**Date**: 2025-11-07
**Status**: ✅ **Success** (In production)
**Related**: [ADR-003](DECISIONS.md#adr-003-17-entity-types)

#### Hypothesis
Adding 11 v2.0 entity types will provide richer context for AI agents at acceptable cost.

#### Setup

**v1.0 (6 types)**:
1. PainPoint
2. Process
3. System
4. KPI
5. AutomationCandidate
6. Inefficiency

**v2.0 (11 new types)**:
7. CommunicationChannel
8. DecisionPoint
9. DataFlow
10. TemporalPattern
11. FailureMode
12. TeamStructure
13. KnowledgeGap
14. SuccessPattern
15. BudgetConstraint
16. ExternalDependency
17. Enhanced v1.0 (sentiment, scoring)

#### Test Results

**Sample Interview Results**:
```
v1.0 extraction (6 types):
  Pain points: 8
  Processes: 12
  Systems: 10
  KPIs: 2
  Automation: 6
  Inefficiency: 4
  ─────────────
  Total: 42 entities
  Time: 15s
  Cost: $0.01

v2.0 extraction (17 types):
  (v1.0 entities: 42)
  Communication: 9
  Decisions: 6
  Data flows: 7
  Temporal: 11
  Failures: 4
  Team: 2
  Knowledge: 1
  Success: 1
  Budget: 1
  External: 2
  ─────────────
  Total: 86 entities (+105%)
  Time: 30s (+100%)
  Cost: $0.03 (+200%)
```

#### Decision
**Adopt 17 entity types** (ADR-003)

#### Benefits
1. **Richer data**: 2x more entities per interview
2. **Better context**: Communication patterns, decision rules, temporal patterns
3. **AI agent readiness**: Agents need this information to automate effectively
4. **Still affordable**: $0.50-1.00 for 44 interviews

#### Trade-offs
- 2x longer extraction time (15s → 30s per interview)
- 3x cost increase ($0.01 → $0.03 per interview)
- BUT: 2x more valuable data

#### Lessons Learned
1. **More entities = more value**: Additional context worth the cost
2. **Spanish extraction works**: No issues with Spanish v2.0 entities
3. **Structured prompts scale**: Same prompt pattern works for all 17 types

---

### EXP-005: Rule-Based Validation

**Date**: 2025-11-08
**Status**: ✅ **Success** (In production)
**Related**: [ADR-005](DECISIONS.md#adr-005-validation-agent-not-llm)

#### Hypothesis
Rule-based validation can catch 80% of quality issues without LLM cost.

#### Setup

**ValidationAgent Checks**:
1. **Completeness**: Minimum entities per interview
2. **Quality**: No empty fields, no placeholders ("N/A", "Unknown")
3. **Encoding**: UTF-8 correct, no escaped characters
4. **Consistency**: Valid companies, business units, departments

**Comparison**:
- **Option A**: LLM validation (ask GPT-4 to review)
- **Option B**: Rule-based validation (heuristics)

#### Test Results

**20-interview test**:
```
Rule-based validation:
  Time: <1s per interview
  Cost: $0 (no API calls)
  Issues caught: 82% of quality problems
  False positives: 5%

LLM validation:
  Time: 5-8s per interview
  Cost: $0.02 per interview
  Issues caught: 95% of quality problems
  False positives: 2%
```

**Issues Caught by Rule-Based**:
- ✅ Empty descriptions (100%)
- ✅ Placeholder values (95%)
- ✅ UTF-8 encoding errors (100%)
- ✅ Invalid companies (100%)
- ❌ Semantic errors (0%) - "wrong answer but well-formatted"

**Issues Caught by LLM**:
- ✅ All rule-based issues
- ✅ Semantic errors (70%)
- ⚠️ BUT: 2x cost, 2x time

#### Decision
**Use rule-based validation, make LLM validation optional** (ADR-005)

**Configuration**:
```json
{
  "validation": {
    "enable_validation_agent": true,   // Rule-based (always on)
    "enable_llm_validation": false     // LLM (disabled by default)
  }
}
```

#### Benefits
1. **Fast**: <1 second per interview
2. **Free**: No API costs
3. **Deterministic**: Same input → same result
4. **Catches most issues**: 80% of problems

#### Trade-offs
- Doesn't catch semantic errors ("Opera is a browser" - wrong but well-formatted)
- Heuristics need tuning (minimum entity thresholds)
- False positives require manual review

#### Lessons Learned
1. **80/20 rule applies**: 80% of issues caught with 0% cost
2. **Rule-based validation sufficient**: LLM validation marginal benefit
3. **Fast feedback valuable**: Immediate validation better than slow comprehensive review

---

### EXP-006: RAG 2.0 Phase 1 QA Validation

**Date**: 2025-11-09
**Status**: ⚠️ **CONDITIONAL GO** (Remediation required)
**Related**: [ADR-010](DECISIONS.md#adr-010-rag-20-phase-1-conditional-go)

#### Hypothesis
Comprehensive QA validation before Week 2 will catch critical issues and prevent technical debt accumulation.

#### Setup

**QA Review Scope**:
- Task 0: Context Registry implementation
- Task 1-2: Source connectors and ingestion queue
- Task 3: Multi-format DocumentProcessor
- Task 4: OCR integration (Mistral Pixtral)
- Task 5: Spanish-aware chunking

**Validation Methodology**:
1. **Dependency Audit**: `pip list` vs `requirements-rag2.txt`
2. **Test Discovery**: `pytest --collect-only`
3. **UTF-8 Compliance**: Grep for `json.dumps` without `ensure_ascii=False`
4. **Code Quality**: Type hints, docstrings, error handling
5. **Implementation Completeness**: Feature-by-feature validation

#### Test Results

**Overall Grade**: C (62/100)
- Implementation Quality: 70/100
- Testing: 0/100 (critical failure)
- Readiness: 85/100

**Critical Issues Discovered**:

1. **Dependencies Not Installed** 🚨
   ```bash
   $ pip list | wc -l
   18  # Only 18 packages installed

   $ wc -l requirements-rag2.txt
   67  # Requirements file has 67 packages

   # Only mistralai installed, missing 66+ packages
   ```
   - Impact: System cannot run at all
   - Severity: BLOCKER

2. **Test Claims Invalid** 🚨
   ```bash
   $ pytest tests/ --collect-only
   collected 0 items

   # Completion report claimed: "103 tests, 85% coverage"
   # Reality: 0 tests, 0% coverage
   ```
   - Impact: No validation that code works
   - Severity: BLOCKER

3. **UTF-8 Violations** 🚨
   ```python
   # intelligence_capture/context_registry.py
   Line 352: json.dumps(context, indent=2)  # Missing ensure_ascii=False
   Line 438: json.dumps(contexts, indent=2)  # Missing ensure_ascii=False
   Line 439: json.dumps(summary, indent=2)   # Missing ensure_ascii=False
   ```
   - Impact: Spanish characters may be escaped
   - Severity: HIGH (violates ADR-001)

4. **Task 4 Incomplete** ⚠️
   - PostgreSQL async integration acknowledged as partial
   - Missing: Connection pooling, transaction management
   - Impact: Cannot proceed to Week 2 (dual storage)

5. **Tasks 1-2 Untested** ⚠️
   - No unit tests for connector implementations
   - Impact: Unknown if connectors work correctly

#### Decision
**CONDITIONAL GO: Proceed to Week 2 ONLY after mandatory remediation** (ADR-010)

#### Remediation Plan

**Mandatory Prerequisites**:
1. Install dependencies: `pip install -r requirements-rag2.txt && python -m spacy download es_core_news_md`
2. Fix UTF-8 violations: Add `ensure_ascii=False` to 3 locations
3. Complete Task 4: Finish PostgreSQL async integration
4. Write missing tests: Unit tests for Tasks 1-2
5. Execute test suite: `pytest tests/ -v --cov` → verify 80%+ coverage
6. Update completion report: Replace false claims with actual metrics

**Estimated Time**: 2-3 days

**Timeline Impact**: Week 1 extends from 7 days → 10 days

#### Why This Experiment Was Valuable

**What We Discovered**:
- ✅ Early QA caught 5 critical issues before Week 2
- ✅ Prevented building Week 2 on broken foundation
- ✅ 2-3 day fix now prevents weeks of rework later
- ✅ Established importance of independent validation

**What Would Have Happened Without QA**:
- ❌ Week 2 work would fail immediately (missing dependencies)
- ❌ Spanish data corruption (UTF-8 violations)
- ❌ No test coverage → production bugs
- ❌ Compound technical debt across 5 weeks

**Cost-Benefit Analysis**:
- QA time investment: 1 day (8 hours)
- Remediation time: 2-3 days
- **Total**: 3-4 days with validation
- **Without QA**: 5+ weeks of compounding issues
- **Net benefit**: ~4 weeks saved

#### Lessons Learned

**1. Test-Driven Development Matters**
- Writing tests after code → easy to skip or fake
- Writing tests first → forces validation
- Pattern: Test → Code → Validate → Complete

**2. Dependency Management Critical**
- Virtual environments can hide missing dependencies
- Always test `pip install -r requirements.txt` in fresh environment
- Document installation steps in RUNBOOK

**3. False Claims Destroy Trust**
- "103 tests, 85% coverage" claim with 0 tests
- Impact: Team confidence damaged
- Prevention: Automated CI checks before claiming completion

**4. UTF-8 Compliance Non-Negotiable**
- Spanish-first principle (ADR-001) requires `ensure_ascii=False`
- Easy to miss, catastrophic impact
- Prevention: Linter rule or pre-commit hook

**5. Independent QA Works**
- Self-review insufficient (bias towards "it works")
- Independent validation catches real issues
- Pattern: Implement → QA → Remediate → Approve

#### Related Experiments

**Comparison to Previous Validation Issues**:
- [EXP-002](#exp-002-parallel-processing-with-wal): Parallel processing broken, discovered too late
- [ADR-009](DECISIONS.md#adr-009-production-bugs-unfixed): Critical bugs documented but not fixed
- **EXP-006**: QA caught issues early, forced remediation before Week 2

**Success Pattern**: Early validation > Late discovery

#### Recommendation

**Adopt QA Gates for All Phases**:
1. **Phase completion checkpoint**: Independent QA review
2. **Prerequisites validation**: Test in clean environment
3. **Test coverage enforcement**: CI blocks merge if <80% coverage
4. **UTF-8 compliance check**: Automated linter rule
5. **Dependency audit**: `pip list` vs `requirements.txt` in CI

**Cost**: 1 day QA per phase
**Benefit**: Prevent weeks of technical debt

---

## Experiments Queue

### Planned Experiments (Not Started)

#### EXP-007: Knowledge Graph Consolidation
**Status**: ⏸️ Postponed (dependencies not met)

**Hypothesis**: Consolidating duplicate entities across interviews provides better quality than ensemble validation per interview.

**Plan**:
1. Extract all 44 interviews normally
2. Run consolidation agent to merge duplicates
3. Track consensus (how many interviews mention each entity)
4. Calculate confidence from consensus
5. Compare quality vs ensemble validation

**Expected Result**: Better quality at lower cost

**Blocked By**: Critical bugs must be fixed first

---

#### EXP-008: GPT-4o-mini-2024 Model
**Status**: ⏸️ Pending model availability

**Hypothesis**: Newer GPT-4o-mini model will improve quality without cost increase.

**Plan**:
1. Test with 10 interviews
2. Compare entity count and quality
3. Measure cost difference
4. If better, switch primary model

---

#### EXP-009: Batch API Calls
**Status**: ⏸️ Low priority

**Hypothesis**: OpenAI Batch API could reduce cost by 50%.

**Plan**:
1. Convert extraction to batch requests
2. Submit 44 interviews as one batch
3. Measure cost and latency
4. Compare with sequential extraction

**Trade-off**: Higher latency (24-hour batch processing) vs lower cost

---

## Experiment Guidelines

### When to Experiment
- ✅ Hypothesis is testable
- ✅ Failure is acceptable
- ✅ Results inform decisions
- ✅ Cost is bounded

### When NOT to Experiment
- ❌ Production system is broken (fix bugs first)
- ❌ Experiment has unbounded cost
- ❌ Experiment doesn't inform a decision
- ❌ Hypothesis already validated/invalidated

### Experiment Template
```markdown
### EXP-XXX: [Name]

**Date**: YYYY-MM-DD
**Status**: [Proposed|In Progress|Complete|Failed]

#### Hypothesis
[What do you expect to happen]

#### Setup
[How the experiment is configured]

#### Test Results
[What actually happened]

#### Decision
[What decision was made based on results]

#### Lessons Learned
[What did we learn]
```

---

## Pattern Analysis

### Successful Experiments
- ✅ LLM fallback chain: High reliability, cost-optimized
- ✅ 17 entity types: More data, acceptable cost
- ✅ Rule-based validation: Fast, free, catches 80% of issues

**Success Pattern**: Start simple, measure impact, validate trade-offs

### Failed Experiments
- ❌ Parallel processing: Didn't test SQLite limitations first
- ⚠️ Ensemble validation: Didn't compare cost vs alternative approaches

**Failure Pattern**: Assume technology solves problem, skip validation

### Abandoned Experiments
- ⏸️ Knowledge Graph: Postponed due to dependencies (correct decision)

**Abandonment Pattern**: Recognize when dependencies not met

---

## References

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Decisions**: [DECISIONS.md](DECISIONS.md)
- **Operations**: [RUNBOOK.md](RUNBOOK.md)

---

**Document Status**: ✅ Master Experiments Log
**Supersedes**: Experiment details scattered across multiple docs
**Last Reviewed**: 2025-11-09
**Next Review**: After running new experiments
