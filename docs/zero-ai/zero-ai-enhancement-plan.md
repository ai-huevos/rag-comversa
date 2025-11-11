# Zero-AI Enhancement Plan
**Date:** November 10, 2025  
**Status:** Analysis Complete - Ready for Requirements Refinement  
**Based on:** Current system0 codebase + AI Engineering book analysis

---

## Executive Summary

The current zero-ai requirements document is a **good start** but needs significant refinement to meet EARS (Easy Approach to Requirements Syntax) and INCOSE quality standards. This plan outlines gaps between the current requirements and the actual system0 codebase, and provides a roadmap for creating production-ready requirements.

---

## Current State Analysis

### What Exists in Codebase (✅)

1. **Extraction Pipeline** (`intelligence_capture/`)
   - 17 entity type extractors (v1.0 + v2.0)
   - Multi-model fallback chain (6 models)
   - Rate limiting and cost estimation
   - Spanish-first processing with UTF-8 handling
   - ValidationAgent for quality checking
   - ExtractionMonitor for progress tracking

2. **Database Layer** (`intelligence_capture/database.py`)
   - SQLite with WAL mode
   - 17 entity tables + metadata
   - Consolidation support (duplicate detection, entity merging)
   - Relationship and pattern tracking

3. **Quality Assurance**
   - ValidationAgent (completeness, quality, consistency checks)
   - Ensemble validation (multi-model review)
   - Metrics collection and reporting

4. **RAG 2.0 Foundation** (In Progress)
   - Context Registry
   - Multi-format DocumentProcessor
   - Mistral Pixtral OCR
   - Spanish chunking
   - PostgreSQL + pgvector migrations
   - Neo4j knowledge graph (planned)

### What's Missing from Requirements (❌)

1. **No EARS-compliant requirements**
   - Current requirements are narrative/descriptive
   - Missing structured "THE system SHALL" format
   - No clear system boundary definition

2. **No measurable acceptance criteria**
   - "Accurate extraction" is vague
   - No quantitative thresholds (e.g., ≥85% accuracy)
   - No performance benchmarks (e.g., <30s per interview)

3. **No failure mode requirements**
   - What happens when API fails?
   - What happens when extraction quality is low?
   - No rollback/recovery requirements

4. **No security/privacy requirements**
   - PII handling not specified
   - Data retention policies missing
   - Access control requirements absent

5. **No operational requirements**
   - Monitoring and alerting not specified
   - Cost controls not formalized
   - Deployment requirements missing

6. **No user feedback loop requirements**
   - How do users rate extraction quality?
   - How are corrections incorporated?
   - No continuous improvement mechanism

---

## Gap Analysis: Requirements vs. Implementation

| Requirement Area | Current Doc | Codebase Reality | Gap |
|-----------------|-------------|------------------|-----|
| **Extraction Accuracy** | "Accurate extraction" | ValidationAgent checks completeness/quality | Need quantitative thresholds (≥85%) |
| **Performance** | Not specified | ~30s per interview | Need SLA requirements (<30s) |
| **Cost Control** | "Estimate cost" | Cost estimation + confirmation | Need hard limits ($1000/month) |
| **Failure Handling** | Not specified | Multi-model fallback + retries | Need recovery requirements |
| **Spanish Processing** | "Spanish-first" | UTF-8 + ensure_ascii=False | Need encoding requirements |
| **Prompt Versioning** | "v1, v2, v3" | Not implemented | Need version control requirements |
| **Evaluation Pipeline** | "30-sample test set" | Not implemented | Need test harness requirements |
| **Guardrails** | "PII detection" | Not implemented | Need data protection requirements |
| **Caching** | "Cache hits" | Not implemented | Need performance optimization requirements |
| **Monitoring** | "Track accuracy" | ExtractionMonitor exists | Need observability requirements |

---

## Enhancement Roadmap

### Phase 1: Requirements Refinement (This Week)
**Goal:** Create EARS-compliant requirements document

**Tasks:**
1. Define system boundary (what is "system0"?)
2. Create glossary of terms (System, Entity, Extraction, etc.)
3. Convert narrative requirements to EARS format
4. Add measurable acceptance criteria
5. Add failure mode requirements
6. Add security/privacy requirements
7. Add operational requirements

**Deliverable:** `.kiro/specs/zero-ai/requirements.md` (EARS-compliant)

### Phase 2: Design Document (Next Week)
**Goal:** Create detailed design based on refined requirements

**Tasks:**
1. Architecture diagrams (extraction pipeline, RAG 2.0)
2. Component specifications (Extractor, Validator, Monitor)
3. Data models (entities, relationships, patterns)
4. Error handling strategies
5. Testing strategy (unit, integration, evaluation)

**Deliverable:** `.kiro/specs/zero-ai/design.md`

### Phase 3: Implementation Tasks (Week 3)
**Goal:** Create actionable task list

**Tasks:**
1. Break design into discrete coding tasks
2. Prioritize tasks (MVP vs. nice-to-have)
3. Estimate effort per task
4. Define dependencies between tasks

**Deliverable:** `.kiro/specs/zero-ai/tasks.md`

### Phase 4: Implementation (Weeks 4-8)
**Goal:** Build missing components

**Priority 1 (MVP):**
- Prompt versioning system
- 30-sample evaluation pipeline
- Quantitative accuracy metrics
- Cost hard limits

**Priority 2 (Production):**
- PII detection guardrails
- Caching layer
- Enhanced monitoring dashboard
- User feedback loop

**Priority 3 (Optimization):**
- RAG context enhancement
- Advanced consolidation
- Performance tuning

---

## Key Decisions Needed

### 1. Data Model Choice
**Question:** Relational (SQLite/Postgres) vs. Document (MongoDB) vs. Graph (Neo4j)?

**Current:** Hybrid (SQLite for entities, Neo4j for relationships)

**Recommendation:** Keep hybrid approach
- SQLite for structured entities (fast queries)
- Neo4j for relationship discovery (graph traversal)
- PostgreSQL + pgvector for RAG embeddings

### 2. Ensemble vs. Knowledge Graph Priority
**Question:** Which to implement first?

**Current:** Both partially implemented

**Recommendation:** Knowledge Graph first
- Consolidation is 77% complete (40/52 tasks)
- Ensemble is expensive (3x API cost)
- Knowledge Graph provides more value (deduplication, relationships)

### 3. Prompt Engineering Strategy
**Question:** How to version and evaluate prompts?

**Current:** Prompts hardcoded in extractor.py

**Recommendation:** Implement prompt versioning
- Store prompts in `prompts/` directory
- Version control (v1, v2, v3)
- A/B testing framework
- Evaluation pipeline with 30-sample test set

### 4. Evaluation Metrics
**Question:** What defines "good enough" extraction?

**Current:** No quantitative thresholds

**Recommendation:** Define metrics
- Entity Extraction Accuracy: ≥85%
- Sentiment F1 Score: ≥80%
- Fact Completeness: ≥75%
- Processing Time: <30s per interview
- Cost: <$0.03 per interview

---

## Production Readiness Checklist

Based on AI Engineering Chapter 10 (Production Architecture):

### Reliability
- [ ] Multi-model fallback chain (✅ Implemented)
- [ ] Retry logic with exponential backoff (✅ Implemented)
- [ ] Graceful degradation (⚠️ Partial)
- [ ] Circuit breaker pattern (❌ Missing)
- [ ] Health checks (❌ Missing)

### Scalability
- [ ] Rate limiting (✅ Implemented)
- [ ] Parallel processing (❌ Broken - WAL mode issues)
- [ ] Batch processing (✅ Implemented)
- [ ] Queue-based architecture (⚠️ Partial - RAG 2.0)
- [ ] Horizontal scaling (❌ Not designed for)

### Maintainability
- [ ] Comprehensive logging (✅ Implemented)
- [ ] Metrics collection (✅ Implemented)
- [ ] Error tracking (✅ Implemented)
- [ ] Documentation (⚠️ Partial)
- [ ] Code quality (✅ Good - type hints, docstrings)

### Security
- [ ] PII detection (❌ Missing)
- [ ] Data encryption (❌ Missing)
- [ ] Access control (❌ Missing)
- [ ] Audit logging (⚠️ Partial)
- [ ] SQL injection prevention (✅ Implemented)

### Observability
- [ ] Real-time monitoring (✅ ExtractionMonitor)
- [ ] Alerting (❌ Missing)
- [ ] Dashboards (❌ Missing)
- [ ] Tracing (❌ Missing)
- [ ] Cost tracking (✅ Implemented)

### User Feedback
- [ ] Rating system (❌ Missing)
- [ ] Correction mechanism (❌ Missing)
- [ ] Feedback loop (❌ Missing)
- [ ] A/B testing (❌ Missing)
- [ ] Continuous improvement (❌ Missing)

---

## Recommended Next Steps

### Immediate (This Week)
1. **Generate EARS-compliant requirements** using the prompt below
2. **Review with domain expert** (Daniel + Comversa stakeholder)
3. **Create 30-sample test set** from existing interviews
4. **Define success metrics** (accuracy thresholds)

### Short-term (Next 2 Weeks)
1. **Implement prompt versioning** system
2. **Build evaluation pipeline** with test set
3. **Add PII detection** guardrails
4. **Implement cost hard limits**

### Medium-term (Weeks 3-4)
1. **Complete Knowledge Graph consolidation** (remaining 12 tasks)
2. **Add caching layer** for performance
3. **Build monitoring dashboard**
4. **Implement user feedback loop**

### Long-term (Weeks 5-8)
1. **Complete RAG 2.0 migration** (PostgreSQL + Neo4j)
2. **Optimize performance** (parallel processing fix)
3. **Production deployment** (January 15, 2026)
4. **Continuous improvement** based on user feedback

---

## Success Criteria

### Requirements Document Quality
- ✅ All requirements follow EARS patterns
- ✅ All requirements have measurable acceptance criteria
- ✅ Glossary defines all technical terms
- ✅ No vague terms ("quickly", "adequate")
- ✅ No escape clauses ("where possible")
- ✅ Active voice throughout

### Implementation Readiness
- ✅ All requirements are testable
- ✅ All requirements are implementable
- ✅ Dependencies are clear
- ✅ Priorities are defined
- ✅ Effort estimates are reasonable

### Production Readiness
- ✅ Reliability: 99.9% uptime
- ✅ Scalability: 100+ interviews/hour
- ✅ Maintainability: <1 hour MTTR
- ✅ Security: PII protected
- ✅ Observability: Real-time monitoring
- ✅ User Satisfaction: ≥4.5/5 rating

---

## References

- **Current Requirements:** `.kiro/specs/zero-ai/requirements.md`
- **Codebase:** `intelligence_capture/`
- **Architecture:** `docs/ARCHITECTURE.md`
- **Coding Standards:** `.ai/CODING_STANDARDS.md`
- **AI Engineering Book:** Chip Huyen, Chapter 4 (Evaluation), Chapter 5 (Prompting), Chapter 6 (RAG), Chapter 10 (Production)

---

**Next Action:** Use the prompt below to generate EARS-compliant requirements in another LLM session.
