# System0 - Comprehensive Project Index for AI Retrieval

**Generated**: 2025-11-13T17:35:00Z
**Scan Type**: Exhaustive (all source files analyzed)
**Purpose**: Master index for AI agents - current state, target state, optimization roadmap
**Context**: Systematic refactoring and production hardening for Zero-AI compliance

---

## Executive Summary

### Project Identity
- **Name**: System0 - Spanish Interview Intelligence Platform
- **Business Value**: Extract and query actionable intelligence from 44 Spanish manager interviews
- **Primary Use Case**: RAG (Retrieval-Augmented Generation) system for business intelligence
- **Organizations**: Los Tajibos (hotel), Comversa (construction), Bolivian Foods (restaurants)

### Current State (As of November 13, 2025)
- **Phase**: ✅ Phase 12 Complete (Consolidation) | 🟡 RAG 2.0 Week 1/5
- **Quality Score**: 9.5/10 (consolidation system production-ready)
- **Technical Debt**: RAG 2.0 Phase 1 requires 2-3 days remediation (QA Grade: C, 62/100)
- **Codebase**: 188 Python files, 7 TypeScript files, 400+ markdown docs (81 archived)

### Target State (Per Zero-AI Requirements)
- **Production RAG System**: Multi-format ingestion → Dual storage (pgvector + Neo4j) → Agentic layer
- **Quality Gates**: Spanish-first, UTF-8 compliance, <1s response time, 80%+ retrieval precision
- **Cost Management**: $500-1,000/month with CostGuard throttling
- **Governance**: Checkpoint retrieval, privacy compliance (Bolivian Law 164), audit trails

---

## 📁 Project Structure

### Multi-Part Architecture (Not a Monorepo)

```
system0/
├── intelligence_capture/    # 🧠 Backend: Spanish interview extraction (17 entity types)
│   ├── connectors/          # Multi-format source connectors (WhatsApp, PDF, CSV)
│   ├── parsers/             # Document adapters (PDF, DOCX, XLSX, images)
│   ├── ocr/                 # Mistral Pixtral OCR + Tesseract fallback
│   ├── chunking/            # Spanish-aware text chunking (300-500 tokens)
│   ├── embeddings/          # OpenAI text-embedding-3-small pipeline
│   ├── persistence/         # PostgreSQL repository layer
│   ├── queues/              # Redis/SQLite ingestion queue
│   ├── monitoring/          # Backlog alerts and metrics
│   └── migrations/          # Database schema migrations
│
├── agent/                   # 🤖 Agentic RAG: Pydantic AI orchestrator
│   ├── tools/               # Vector, graph, hybrid search tools
│   ├── rag_agent.py         # Main agent with Spanish system prompt
│   ├── cli.py               # Interactive CLI interface
│   └── session.py           # Conversation memory management
│
├── api/                     # 🌐 REST API: FastAPI server for dashboard
│   ├── routers/             # Endpoint definitions (entities, dashboard)
│   ├── models/              # Pydantic schemas and RAG models
│   ├── services/            # PostgreSQL/Neo4j service layer
│   └── server.py            # Main FastAPI application
│
├── dashboard/               # 📊 Frontend: Next.js executive dashboard
│   ├── app/                 # Next.js 14 app router
│   ├── components/          # React components (charts, tables)
│   └── lib/                 # API client and utilities
│
├── scripts/                 # 🛠️ Operations: 54 utility scripts
│   ├── migrations/          # PostgreSQL/Neo4j schema migrations
│   ├── test_*.py            # Integration test runners
│   └── sync_*.py            # Data synchronization scripts
│
├── tests/                   # ✅ Testing: 56 test files (unit + integration)
│   ├── test_consolidation_*.py   # Consolidation system tests
│   ├── test_agent_*.py           # RAG agent tests
│   └── fixtures/                 # Test data and mocks
│
├── .kiro/specs/             # 📋 Requirements & Task Tracking
│   ├── zero-ai/             # Production framework (2400+ lines)
│   ├── rag-2.0-enhancement/ # RAG 2.0 implementation roadmap
│   └── knowledge-graph-consolidation/ # Entity consolidation specs
│
└── docs/                    # 📚 Documentation: 14 active guides + archive
    ├── README.md            # Master index (this file's companion)
    ├── ARCHITECTURE.md      # System architecture deep-dive
    ├── RUNBOOK.md           # Operational procedures
    ├── DECISIONS.md         # 10 Architecture Decision Records (ADRs)
    └── archive/2025-11/     # 81 historical documents (preserved for context)
```

---

## 🎯 Current vs Target State Mapping

### Component Status Matrix

| Component | Current State | Target State (Zero-AI) | Gap Analysis | Priority |
|-----------|---------------|------------------------|--------------|----------|
| **Intelligence Extraction** | ✅ Production (17 entity types, 95% cost reduction) | ✅ Maintained | None | N/A |
| **Consolidation System** | ✅ Production (9.5/10 quality score) | ✅ Maintained | None | N/A |
| **Context Registry** | 🟡 Implemented, untested | ✅ Unit tests, multi-org namespacing | Missing tests | **HIGH** |
| **Source Connectors** | 🟡 Implemented, untested | ✅ Unit tests, error handling | Missing tests, async handling | **HIGH** |
| **Document Processor** | 🟡 Partial (PDF/DOCX done) | ✅ All formats (CSV, images, WhatsApp) | Missing parsers, OCR integration | **MEDIUM** |
| **PostgreSQL + pgvector** | 🟡 Schema ready, async incomplete | ✅ Full async integration, HNSW indexes | Async operations, migration testing | **HIGH** |
| **Neo4j + Knowledge Graph** | 🟡 Builder exists, sync pending | ✅ Real-time sync from consolidation | ConsolidationSync integration | **HIGH** |
| **Embedding Pipeline** | 🔴 Not started | ✅ Batch processing, cost tracking, Spanish optimization | Complete implementation needed | **CRITICAL** |
| **Pydantic AI Agent** | 🔴 Scaffold only | ✅ 4 tools (vector/graph/hybrid/checkpoint), session management | Complete implementation needed | **CRITICAL** |
| **FastAPI Server** | 🟡 Basic endpoints | ✅ /chat, /chat/stream (SSE), health checks | SSE streaming, agent integration | **HIGH** |
| **Retrieval Evaluation** | 🔴 Not started | ✅ Spanish test dataset, Precision@5≥0.80, MRR≥0.75 | Complete evaluation harness | **MEDIUM** |
| **CostGuard Integration** | 🔴 Not started | ✅ Per-query tracking, $900 throttle, $1000 hard stop | Budget monitoring system | **MEDIUM** |
| **Governance & Compliance** | 🟡 Partial (checkpoints exist) | ✅ Full audit trail, privacy compliance, checkpoint retrieval | Formal compliance documentation | **LOW** |

**Legend**: ✅ Complete | 🟡 Partial | 🔴 Not Started

---

## 🚨 Critical Issues Requiring Immediate Remediation

### RAG 2.0 Phase 1 QA Findings (November 9, 2025)

**Grade**: C (62/100) - CONDITIONAL GO with mandatory fixes before Week 2

#### 🔴 CRITICAL (Blockers for Week 2)

1. **Dependencies Not Installed** (`requirements-rag2.txt`)
   - **Impact**: 67 missing packages (only `mistralai` installed)
   - **Fix**: `pip install -r requirements-rag2.txt && python -m spacy download es_core_news_md`
   - **Effort**: 10 minutes
   - **Location**: Project root

2. **UTF-8 Violations** (Spanish-first principle breach)
   - **Impact**: 3 locations missing `ensure_ascii=False` → data corruption risk
   - **Fix**: Add `ensure_ascii=False` to JSON dumps in `context_registry.py:352,438,439`
   - **Effort**: 5 minutes
   - **Code**:
   ```python
   # WRONG (current)
   json.dumps(data)

   # RIGHT (required)
   json.dumps(data, ensure_ascii=False, indent=2)
   ```

3. **Test Claims Invalid**
   - **Impact**: Reported "103 tests, 85% coverage" but actual: 0 tests, 0% coverage
   - **Fix**: Write missing unit tests for Tasks 1-2 (connectors, context registry)
   - **Effort**: 4-6 hours
   - **Files**: `tests/test_context_registry.py`, `tests/test_*_connector.py`

4. **PostgreSQL Async Integration Incomplete**
   - **Impact**: Task 4 acknowledged as partial, blocking Week 2 embedding pipeline
   - **Fix**: Complete async operations in `persistence/document_repository.py`
   - **Effort**: 8-12 hours
   - **Dependencies**: `asyncpg`, proper connection pooling

#### ⚠️ IMPORTANT (Should Fix)

5. **ConsolidationSync → PostgreSQL/Neo4j Not Integrated**
   - **Impact**: Knowledge graph not updated with consolidated entities
   - **Fix**: Integrate `consolidation_sync.py` with `intelligence_capture/consolidation_agent.py`
   - **Effort**: 16-24 hours (Week 5 task, can defer)
   - **See**: `docs/CONSOLIDATION_SYNC_ARCHITECTURE.md`

6. **Ingestion Worker Automation Missing**
   - **Impact**: Manual ingestion only, no production automation
   - **Fix**: Complete `intelligence_capture/ingestion_worker.py` with --consolidation mode
   - **Effort**: 8-12 hours (Week 5 task, can defer)

---

## 🏗️ Technology Stack Analysis

### Backend (Python 3.10+)

**Core Libraries:**
```python
# LLM Integration
openai>=1.0.0                    # Primary model: gpt-4o-mini
mistralai                        # OCR: Pixtral-large-2411
pydantic-ai                      # Agent orchestration framework

# Data Processing
rapidfuzz>=3.0.0                 # Fuzzy matching (10-100x faster than difflib)
colorlog>=6.0.0                  # Structured console logging

# Databases
psycopg2-binary==2.9.9           # PostgreSQL driver
neo4j==5.16.0                    # Neo4j driver
# SQLite (built-in)              # Legacy storage, transitioning out

# Web Framework (API)
fastapi==0.109.0                 # REST API framework
uvicorn[standard]==0.27.0        # ASGI server
pydantic==2.5.3                  # Data validation

# NLP & Embedding
# spacy (required but not installed!)  # Spanish NLP
# text-embedding-3-small (OpenAI)     # 1536-dim vectors
```

**Key Patterns:**
- **6-Model Fallback Chain**: gpt-4o-mini → gpt-4o → gpt-3.5-turbo → o1-mini → o1-preview → claude-3-5-sonnet
- **Spanish-First Processing**: No translation, UTF-8 everywhere, `ensure_ascii=False` mandatory
- **WAL Mode SQLite**: Concurrent writes for parallel processing
- **Rate Limiting**: Exponential backoff, shared limiter across extractors

### Frontend (TypeScript + Next.js 14)

**Stack:**
```json
{
  "framework": "Next.js 14.0.4",
  "ui": "React 18.2.0",
  "language": "TypeScript 5.3.3",
  "styling": "Tailwindcss 3.4.0",
  "charts": "Recharts 2.10.3",
  "icons": "lucide-react 0.303.0"
}
```

**Architecture**: App Router, Server Components, client-side data fetching to `/api`

### Databases

| Database | Version | Purpose | Status | Migration Path |
|----------|---------|---------|--------|----------------|
| SQLite | 3.x (WAL mode) | Legacy extraction storage | ✅ Production | Maintain for extraction, phase out for RAG |
| PostgreSQL | 15 with pgvector 0.8.1 | Document chunks + embeddings | 🟡 Schema ready | Complete async integration |
| Neo4j | 2025.10.1 | Consolidated knowledge graph | 🟡 Builder exists | Integrate ConsolidationSync |

### LLM Models & Cost Structure

| Model | Purpose | Cost | Performance |
|-------|---------|------|-------------|
| gpt-4o-mini | Primary extraction (17 entity types) | $0.15/1M tokens in, $0.60/1M out | 99.9% success, <2s/entity |
| text-embedding-3-small | Vector embeddings | $0.02/1M tokens | 1536-dim, <100ms |
| Mistral Pixtral-large-2411 | OCR (scanned Spanish docs) | $0.25/1K images | High accuracy on handwriting |

**Monthly Budget**: $500-1,000 (CostGuard throttles at $900, hard stop at $1,000)

---

## 🔍 17 Entity Types (Business Intelligence Schema)

### v1.0 Entities (Original 6)
1. **PainPoint** - Business problems blocking work
2. **Process** - How work gets done
3. **System** - Tools and software used
4. **KPI** - Success metrics
5. **AutomationCandidate** - Automation opportunities
6. **Inefficiency** - Redundant or wasteful steps

### v2.0 Entities (Enhanced 11)
7. **CommunicationChannel** - How teams interact (WhatsApp, email, meetings)
8. **DecisionPoint** - Where decisions are made and who makes them
9. **DataFlow** - How information moves between systems/people
10. **TemporalPattern** - Time-based patterns (daily, weekly, monthly cycles)
11. **FailureMode** - Common failure patterns and workarounds
12. **TeamStructure** - Organizational hierarchies and roles
13. **KnowledgeGap** - Missing skills or information
14. **SuccessPattern** - What works well (best practices)
15. **BudgetConstraint** - Financial limitations affecting decisions
16. **ExternalDependency** - Third-party dependencies (vendors, regulators)
17. **Enhanced v1.0** - Original 6 types with richer metadata

**Consolidation Results** (Phase 12):
- 80-95% duplicate reduction (e.g., 25 "Excel" mentions → 1 consolidated entity)
- Consensus confidence averaging 0.75+
- Source tracking to original interviews
- Relationship discovery (CAUSES, USES, REQUIRES, MENTIONS)

---

## 🗺️ Data Flow Architecture

### Current System (Legacy Extraction)

```
44 Spanish Interviews (JSON)
    ↓
IntelligenceExtractor (17 entity types)
    ├─ Multi-model fallback chain (6 models)
    ├─ ValidationAgent (quality checks)
    └─ ExtractionMonitor (progress tracking)
    ↓
SQLite Storage (17 tables + metadata)
    ↓
ConsolidationAgent ✅ (Phase 12 Complete)
    ├─ DuplicateDetector (fuzzy + semantic, 96x speedup)
    ├─ EntityMerger (source tracking, consensus scoring)
    ├─ RelationshipDiscoverer (4 types)
    └─ PatternRecognizer (recurring themes)
    ↓
Consolidated Entities (SQLite)
- 80-95% duplicate reduction
- Consensus confidence scores
- Relationship mapping
```

### Target System (RAG 2.0 - Week 5)

```
Multi-Format Documents (PDF, images, CSV, WhatsApp, JSON)
    ↓
ContextRegistry (multi-org namespace, privacy compliance)
    ↓
SourceConnectors (WhatsApp, CSV, PDF, API, email, SharePoint)
    ↓
IngestionQueue (Redis/SQLite jobs with priority)
    ↓
DocumentProcessor
    ├─ Format Detection
    ├─ OCR (Mistral Pixtral for images, Tesseract fallback)
    ├─ Parsing (PDF, DOCX, XLSX, WhatsApp chat)
    └─ Validation
    ↓
SpanishChunker (300-500 tokens, accent-aware, sentence boundaries)
    ↓
DUAL STORAGE (Parallel Fan-Out):
    │
    ├─ PostgreSQL + pgvector
    │   ├─ documents (metadata, org_id, source)
    │   ├─ document_chunks (text, position, metadata)
    │   └─ embeddings (1536-dim, HNSW index, cosine similarity)
    │   Use case: "Find all mentions of 'automatización'"
    │
    └─ Neo4j + Graffiti
        ├─ Entity nodes (consolidated from SQLite)
        ├─ Relationship edges (CAUSES, USES, REQUIRES, MENTIONS)
        └─ Document chunk links (provenance)
        Use case: "What systems cause pain in Finance?"
    ↓
PydanticAI Agent (Spanish system prompt)
    ├─ Tool: vector_search (semantic similarity, pgvector)
    ├─ Tool: graph_search (relationship traversal, Neo4j)
    ├─ Tool: hybrid_search (vector + graph fusion)
    └─ Tool: checkpoint_lookup (governance artifacts)
    ↓
FastAPI Server
    ├─ POST /chat (conversational queries)
    ├─ POST /chat/stream (SSE streaming)
    └─ GET /health (system status)
    ↓
Next.js Executive Dashboard
- Conversational interface
- Source citations
- Multi-turn memory
- Cost tracking per query
```

---

## 🧪 Testing Strategy

### Current Test Coverage

| Component | Test Files | Coverage | Status |
|-----------|------------|----------|--------|
| Consolidation System | 7 files (`test_consolidation_*.py`) | 85% | ✅ Production |
| Extraction System | 12 files (`test_*_extraction.py`) | 75% | ✅ Stable |
| Context Registry | 0 files | 0% | 🔴 **Missing** |
| Source Connectors | 0 files | 0% | 🔴 **Missing** |
| Document Processor | 0 files | 0% | 🔴 **Missing** |
| Agent Tools | 0 files | 0% | 🔴 **Missing** |
| API Endpoints | 0 files | 0% | 🔴 **Missing** |

**Total**: 19 test files, ~50% overall coverage (misleading - critical RAG 2.0 components untested)

### Required Test Suite (Zero-AI Standard)

#### Unit Tests (Target: 80%+ coverage)
```bash
# Context Registry & Connectors (HIGH PRIORITY)
tests/test_context_registry.py              # Multi-org namespacing, validation
tests/test_whatsapp_connector.py            # Chat parsing, media handling
tests/test_csv_connector.py                 # Delimiter detection, encoding
tests/test_pdf_connector.py                 # Text extraction, error handling

# Document Processing (MEDIUM PRIORITY)
tests/test_document_processor.py            # Format detection, validation
tests/test_spanish_chunker.py               # Chunk boundaries, token limits
tests/test_ocr_coordinator.py               # Mistral/Tesseract routing

# Embedding Pipeline (CRITICAL)
tests/test_embedding_pipeline.py            # Batch processing, cost tracking
tests/test_postgres_service.py              # Async operations, connection pooling

# Agent & Tools (CRITICAL)
tests/test_rag_agent.py                     # Tool orchestration, Spanish prompts
tests/test_vector_search.py                 # pgvector queries, similarity thresholds
tests/test_graph_search.py                  # Neo4j traversal, relationship filtering
tests/test_hybrid_search.py                 # Vector+graph fusion, ranking
```

#### Integration Tests
```bash
# End-to-End Workflows
tests/test_ingestion_workflow.py            # Source → Postgres → Neo4j
tests/test_retrieval_workflow.py            # Query → Tools → Response
tests/test_consolidation_sync.py            # SQLite → Postgres → Neo4j

# Performance & Load
tests/test_response_time.py                 # <1s for vector, <2s for graph
tests/test_concurrent_queries.py            # 10 concurrent users
```

#### Retrieval Evaluation (Spanish Test Dataset)
```bash
# Quality Metrics (Week 4)
scripts/evaluate_retrieval.py
- 50 curated Spanish questions
- Precision@5 ≥ 0.80
- MRR (Mean Reciprocal Rank) ≥ 0.75
- Response time monitoring
```

---

## 📋 Systematic Refactoring Roadmap

### Phase 1: Remediation & Stabilization (2-3 days)

**Objective**: Fix RAG 2.0 Phase 1 blocking issues

#### Day 1: Dependencies & UTF-8
- [ ] Install all dependencies: `pip install -r requirements-rag2.txt`
- [ ] Download Spanish NLP model: `python -m spacy download es_core_news_md`
- [ ] Fix 3 UTF-8 violations in `context_registry.py`
- [ ] Run existing tests to establish baseline: `pytest tests/ -v`

#### Day 2: PostgreSQL Async Integration
- [ ] Complete async operations in `persistence/document_repository.py`
- [ ] Implement connection pooling (asyncpg)
- [ ] Write integration tests for async database operations
- [ ] Verify all database operations are non-blocking

#### Day 3: Missing Unit Tests
- [ ] Write `tests/test_context_registry.py` (multi-org validation)
- [ ] Write connector tests (WhatsApp, CSV, PDF - 3 files)
- [ ] Achieve 80%+ coverage on Tasks 1-2 components
- [ ] Update completion report with actual test metrics

**Success Criteria**:
- ✅ All dependencies installed
- ✅ Zero UTF-8 violations
- ✅ PostgreSQL fully async with tests
- ✅ 80%+ coverage on Context Registry + Connectors
- ✅ Ready for Week 2 (embedding pipeline implementation)

---

### Phase 2: RAG 2.0 Week 2-3 (Embedding & Agent) (10-14 days)

**Objective**: Complete dual storage and agentic layer

#### Week 2: Embedding Pipeline
- [ ] Task 7: Implement batch embedding pipeline with CostGuard
- [ ] Task 7.1: Spanish text preprocessing (accent normalization, stopword removal)
- [ ] Task 7.2: OpenAI text-embedding-3-small integration
- [ ] Task 7.3: Batch processing (100 chunks/batch, progress tracking)
- [ ] Task 7.4: Cost estimation and monthly budget enforcement
- [ ] Task 8: Neo4j knowledge graph builder
- [ ] Task 8.1: Consolidation → Neo4j sync (ConsolidationSync integration)
- [ ] Task 8.2: Document chunk → entity linking
- [ ] Task 8.3: Relationship creation from consolidation data
- [ ] Task 9: Complete any remaining dual storage tasks

**Deliverables**:
- PostgreSQL embeddings table populated
- Neo4j graph with consolidated entities and relationships
- Cost tracking per batch run

#### Week 3: Pydantic AI Agent & API
- [ ] Task 10: Implement 4 retrieval tools
  - [ ] Tool 1: vector_search (pgvector cosine similarity)
  - [ ] Tool 2: graph_search (Neo4j Cypher traversal)
  - [ ] Tool 3: hybrid_search (vector + graph fusion with ranking)
  - [ ] Tool 4: checkpoint_lookup (governance artifact retrieval)
- [ ] Task 11: Pydantic AI agent with Spanish system prompt
- [ ] Task 12: FastAPI endpoints (/chat, /chat/stream with SSE, /health)
- [ ] Task 13: CLI for interactive testing
- [ ] Task 14: Session management with conversation memory

**Deliverables**:
- Working agent with 4 tools
- REST API with SSE streaming
- CLI for manual testing
- Spanish conversational responses with source citations

---

### Phase 3: Quality & Production Hardening (Week 4-5) (7-10 days)

**Objective**: Achieve production-ready quality gates

#### Week 4: Retrieval Quality
- [ ] Task 15: Create 50-question Spanish evaluation dataset
  - [ ] 10 factual questions (single-entity retrieval)
  - [ ] 15 relationship questions (graph traversal)
  - [ ] 10 multi-hop questions (hybrid search)
  - [ ] 10 open-ended questions (summarization)
  - [ ] 5 edge cases (ambiguity, negation, temporal)
- [ ] Task 16: Evaluation harness
  - [ ] Precision@5 ≥ 0.80
  - [ ] MRR ≥ 0.75
  - [ ] Response time <1s (vector), <2s (graph)
- [ ] Task 17: Spanish optimization
  - [ ] Accent-aware chunking refinement
  - [ ] Spanish stopword filtering
  - [ ] Query preprocessing (synonyms, stemming)
- [ ] Task 18: Performance tuning
  - [ ] HNSW index optimization (pgvector)
  - [ ] Neo4j query optimization
  - [ ] Caching strategy (Redis for hot queries)

**Deliverables**:
- Evaluation report with metrics
- Performance baselines documented
- Spanish-specific optimizations validated

#### Week 5: Consolidation & Automation
- [ ] Task 19: ConsolidationSync → PostgreSQL integration
- [ ] Task 20: ConsolidationSync → Neo4j integration
- [ ] Task 21: Ingestion worker automation
  - [ ] --consolidation mode (extract → consolidate → sync)
  - [ ] Scheduled batch processing (cron/systemd)
  - [ ] Backlog monitoring and alerts
- [ ] Task 22: RAG2 operational runbook
- [ ] Task 23: Compliance evidence bundle

**Deliverables**:
- Automated end-to-end pipeline
- Operational runbook for production
- Compliance documentation

---

### Phase 4: Zero-AI Compliance & Production Deployment (3-5 days)

**Objective**: Full production readiness per Zero-AI requirements

#### Compliance Checklist

**Spanish-First Compliance**:
- [ ] All JSON dumps use `ensure_ascii=False`
- [ ] All file I/O uses UTF-8 encoding explicitly
- [ ] No automatic translation anywhere in codebase
- [ ] Spanish stopwords and stemming in NLP pipeline
- [ ] Accent preservation in chunking and embedding

**Performance Compliance**:
- [ ] Vector search <1s (measured via evaluation harness)
- [ ] Graph search <2s (measured via evaluation harness)
- [ ] Concurrent query handling (10+ users, load testing)
- [ ] HNSW index tuned for <100ms avg retrieval

**Cost Compliance**:
- [ ] CostGuard integrated with per-query tracking
- [ ] $900 monthly throttle configured
- [ ] $1,000 monthly hard stop configured
- [ ] Cost dashboard in FastAPI /health endpoint

**Governance Compliance**:
- [ ] Checkpoint retrieval functional (Task 10.4 complete)
- [ ] Audit trail for all data operations (Postgres `audit_log` table)
- [ ] Privacy compliance documented (Bolivian Law 164, Constitution Art. 21)
- [ ] Multi-org namespace enforced (ContextRegistry validation)

**Quality Compliance**:
- [ ] 80%+ test coverage (pytest --cov)
- [ ] Precision@5 ≥ 0.80 (evaluation harness)
- [ ] MRR ≥ 0.75 (evaluation harness)
- [ ] Zero UTF-8 violations (linter check)
- [ ] Type hints on all functions (mypy validation)

**Documentation Compliance**:
- [ ] Architecture diagrams current (docs/ARCHITECTURE.md)
- [ ] API contracts documented (docs/API_CONTRACT.md)
- [ ] Operational runbook complete (docs/RAG2_runbook.md)
- [ ] ADRs for all major decisions (docs/DECISIONS.md)

---

## 🧹 Cleanup & Optimization Opportunities

### Code Quality Improvements

#### High Priority (Immediate Cleanup)

1. **Remove Ensemble Validation System** (Deprecated)
   - **Reason**: 3x cost, 3x time, not justified for value delivered (per ADR-008)
   - **Files to Remove**:
     - `intelligence_capture/reviewer.py`
     - `tests/test_ensemble_*.py`
     - `docs/ENSEMBLE_*.md` (move to archive)
   - **Effort**: 2 hours
   - **Benefit**: Code clarity, reduced maintenance burden

2. **Consolidate Redundant Documentation**
   - **Issue**: 81 archived files but some contain unique insights not in master docs
   - **Action**: Extract unique content from archive, update master docs, delete redundant files
   - **Files**: `docs/archive/2025-11/*.md`
   - **Effort**: 4-6 hours
   - **Benefit**: Single source of truth, easier navigation

3. **Standardize Error Handling**
   - **Issue**: Inconsistent exception handling across connectors and parsers
   - **Action**:
     - Create `intelligence_capture/exceptions.py` with custom exception hierarchy
     - Standardize try/except blocks with structured logging
     - Add retry logic where appropriate
   - **Effort**: 6-8 hours
   - **Benefit**: Predictable error behavior, easier debugging

4. **Type Hint Completeness**
   - **Issue**: Some functions lack type hints (especially in older extraction code)
   - **Action**: Add type hints to all public functions, enable mypy strict mode
   - **Tool**: `mypy --strict intelligence_capture/ agent/ api/`
   - **Effort**: 8-10 hours
   - **Benefit**: Better IDE support, catch bugs at development time

#### Medium Priority (Technical Debt Reduction)

5. **SQLite → PostgreSQL Migration Plan**
   - **Issue**: Dual database system (SQLite for extraction, PostgreSQL for RAG) is confusing
   - **Long-term Goal**: PostgreSQL as single source of truth
   - **Migration Path**:
     - Phase 1: Keep SQLite for extraction (current, stable)
     - Phase 2: Write new extractions to both SQLite + PostgreSQL (parallel validation)
     - Phase 3: Read from PostgreSQL, fallback to SQLite (transition period)
     - Phase 4: Decommission SQLite (6+ months out)
   - **Effort**: 40-60 hours over 3-6 months
   - **Benefit**: Unified data model, simplified architecture

6. **Refactor Model Router**
   - **Issue**: `intelligence_capture/model_router.py` is complex, hard to test
   - **Action**: Extract model selection logic to separate strategy classes
   - **Pattern**: Strategy pattern for model selection, Factory for client creation
   - **Effort**: 8-12 hours
   - **Benefit**: Testable model selection, easier to add new models

7. **Dashboard API Client Optimization**
   - **Issue**: Frontend makes multiple sequential API calls (waterfall effect)
   - **Action**: Implement GraphQL or batch REST endpoint for dashboard data
   - **Effort**: 10-15 hours
   - **Benefit**: Faster dashboard load times, reduced server load

#### Low Priority (Nice to Have)

8. **Logging Standardization**
   - **Issue**: Mix of `print()`, `logging`, and `colorlog`
   - **Action**: Standardize on structured logging (JSON format for production)
   - **Tool**: `structlog` or `python-json-logger`
   - **Effort**: 6-8 hours
   - **Benefit**: Better log aggregation, easier debugging

9. **Configuration Management**
   - **Issue**: `.env` files are error-prone, no validation
   - **Action**: Migrate to Pydantic Settings with validation
   - **Pattern**: `config/settings.py` with BaseSettings
   - **Effort**: 4-6 hours
   - **Benefit**: Type-safe config, startup validation

10. **Docker Compose for Local Development**
    - **Issue**: Manual PostgreSQL and Neo4j setup is cumbersome
    - **Action**: Complete `docker-compose.yml` with all services
    - **Services**: PostgreSQL, Neo4j, Redis, FastAPI, Next.js
    - **Effort**: 4-6 hours
    - **Benefit**: One-command local environment setup

---

## 🎯 Quick Reference for AI Agents

### Key Files to Read First

When analyzing this codebase, AI agents should read in this order:

1. **Project Context**:
   - `CLAUDE.md` - Master project guide (guardrails, workflows, specs)
   - `docs/README.md` - Current status, quick start, architecture overview
   - `docs/bmm-index.md` (this file) - Comprehensive index and roadmap

2. **Architecture Understanding**:
   - `docs/ARCHITECTURE.md` - System components and data flow
   - `docs/CONSOLIDATION_SYNC_ARCHITECTURE.md` - Event-driven sync design
   - `docs/DECISIONS.md` - 10 ADRs explaining why decisions were made

3. **Implementation Details**:
   - `intelligence_capture/processor.py` - Main extraction orchestrator
   - `intelligence_capture/consolidation_agent.py` - Duplicate detection and merging
   - `agent/rag_agent.py` - Pydantic AI agent (scaffold, incomplete)
   - `api/server.py` - FastAPI main application

4. **Specifications**:
   - `.kiro/specs/zero-ai/requirements.md` - Production requirements (2400+ lines)
   - `.kiro/specs/rag-2.0-enhancement/tasks.md` - Week-by-week implementation tasks
   - `.kiro/specs/knowledge-graph-consolidation/` - Consolidation specs

### Critical Constraints (Never Violate)

1. **Spanish-First**: Never translate content, always `ensure_ascii=False` in JSON
2. **UTF-8 Everywhere**: Explicit encoding in all file I/O
3. **Cost Guardrails**: Never exceed $1,000/month without approval
4. **Privacy**: Respect multi-org namespacing, no cross-org data leakage
5. **Existing Tests**: Never skip, disable, or comment out tests to make builds pass

### Common Operations

```bash
# Test single interview extraction
python scripts/test_single_interview.py

# Run consolidation
python scripts/test_consolidation.py

# Check database status
sqlite3 data/full_intelligence.db "SELECT entity_type, COUNT(*) FROM consolidated_entities GROUP BY entity_type;"

# Run test suite
pytest tests/ -v --cov

# Start API server (when complete)
uvicorn api.server:app --reload

# Start dashboard (requires API running)
cd dashboard && npm run dev

# Evaluate retrieval quality (when complete)
python scripts/evaluate_retrieval.py
```

### Where to Find Information

| Question | Where to Look |
|----------|---------------|
| Why was decision X made? | `docs/DECISIONS.md` (ADR-### section) |
| How do I run the system? | `docs/RUNBOOK.md` or `CLAUDE.md` |
| What's the current status? | `docs/README.md` (top section) |
| What needs to be implemented? | `.kiro/specs/rag-2.0-enhancement/tasks.md` |
| How does consolidation work? | `docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md` |
| How do I add a new entity type? | `docs/ARCHITECTURE.md` (Entity Types section) |
| What are the API endpoints? | `api/routers/*.py` or `docs/API_CONTRACT.md` (when created) |
| How do I optimize costs? | `CLAUDE.md` (Cost Guardrails section) |

---

## 📊 Key Metrics & Performance Baselines

### Current System (Phase 12 - Consolidation)

**Processing Performance**:
- Single interview extraction: ~10 seconds, ~$0.01
- Batch extraction (44 interviews): ~5-8 minutes, ~$0.50-1.00
- Consolidation (44 interviews): <5 minutes, $0 (fuzzy-first, 95% cost reduction)
- Total end-to-end: ~10-13 minutes, ~$0.50-1.00

**Quality Metrics**:
- Duplicate reduction: 80-95% (25 Excel mentions → 1 entity)
- Consensus confidence: 0.75+ average across all entity types
- Source tracking: 100% (every entity linked to source interviews)
- Relationship discovery: 4 types (CAUSES, USES, REQUIRES, MENTIONS)

### Target System (RAG 2.0 - Week 5)

**Query Response Time** (per Zero-AI requirements):
- Vector search (pgvector): <1s for top-5 results
- Graph search (Neo4j): <2s for relationship traversal
- Hybrid search: <3s for fused ranking
- Checkpoint lookup: <500ms (cached governance artifacts)

**Retrieval Quality** (per Zero-AI requirements):
- Precision@5: ≥0.80 (80% of top-5 results relevant)
- MRR (Mean Reciprocal Rank): ≥0.75 (first relevant result in top 2 on average)
- Spanish accuracy: 95%+ for OCR and chunking

**Cost Tracking**:
- Per-query cost: $0.001-0.01 (embedding + LLM generation)
- Monthly budget: $500-1,000
- CostGuard throttle: $900 (slow down operations)
- CostGuard hard stop: $1,000 (reject new queries)

**Scalability**:
- Concurrent queries: 10+ users
- Document corpus: 10,000+ documents
- Embedding index size: 1M+ vectors
- Graph database: 100K+ nodes, 500K+ relationships

---

## 🛠️ Development Workflow

### Daily Development Commands

```bash
# 1. Environment Setup (first time)
cp .env.example .env
pip install -r requirements-rag2.txt
python -m spacy download es_core_news_md

# 2. PostgreSQL/Neo4j Setup (Docker)
docker-compose up -d postgres neo4j

# 3. Run Migrations
psql $DATABASE_URL -f scripts/migrations/2025_01_01_pgvector.sql

# 4. Test Extraction
python scripts/test_single_interview.py

# 5. Run Consolidation
python scripts/test_consolidation.py

# 6. Start API Server (when complete)
uvicorn api.server:app --reload --port 8000

# 7. Start Dashboard (when complete)
cd dashboard && npm run dev

# 8. Run Tests
pytest tests/ -v --cov=intelligence_capture --cov=agent --cov=api

# 9. Check Retrieval Quality (when complete)
python scripts/evaluate_retrieval.py
```

### Pre-Commit Checklist

Before committing code, verify:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] No UTF-8 violations: `grep -r "json.dumps" --include="*.py" | grep -v "ensure_ascii=False"`
- [ ] Type hints present: `mypy intelligence_capture/ agent/ api/ --check-untyped-defs`
- [ ] Linting clean: `flake8 intelligence_capture/ agent/ api/`
- [ ] Spanish content not translated: `grep -r "translate" --include="*.py"` (should be empty)

### Git Workflow

```bash
# 1. Start new feature
git checkout development
git pull
git checkout -b feat/your-feature

# 2. Make changes, test locally

# 3. Commit with descriptive message
git add .
git commit -m "feat(component): description of change

- Detail 1
- Detail 2

Refs: .kiro/specs/rag-2.0-enhancement/tasks.md Task 7"

# 4. Push and create PR
git push -u origin feat/your-feature
# Create PR on GitHub targeting `development` branch

# 5. After approval, merge to development
# Production deployment from `main` branch only
```

---

## 🔐 Security & Privacy

### Data Privacy Compliance

**Bolivian Legal Framework**:
- Constitution Article 21: Right to privacy and data protection
- Law 164 (Ley General de Telecomunicaciones): Telecommunications data protection

**Implementation**:
- Multi-org namespacing (ContextRegistry enforces org_id isolation)
- No cross-org data leakage (queries filtered by org_id)
- Audit trail for all data access (PostgreSQL audit_log table)
- Consent metadata required for document ingestion

### Security Best Practices

**API Security**:
- CORS configuration (production: specific domains only)
- Rate limiting on /chat endpoints (10 queries/minute per user)
- Input validation (Pydantic schemas for all requests)
- Output sanitization (prevent SQL injection in graph queries)

**Data Security**:
- Environment variables for secrets (never commit to git)
- Database connection pooling with timeout (prevent connection exhaustion)
- SQL injection prevention (parameterized queries only)
- Embedding PII detection (optional: scan for SSN, emails, phone numbers before embedding)

**Infrastructure Security**:
- Docker container isolation
- PostgreSQL user roles (app_read, app_write, admin)
- Neo4j authentication required
- Redis password protection (if used for caching)

---

## 📞 Support & Escalation

### When Things Go Wrong

**Database Issues**:
1. Check `logs/` directory for error messages
2. Review `docs/RUNBOOK.md` troubleshooting section
3. Verify database migrations ran successfully
4. Check connection strings in `.env`

**Extraction Failures**:
1. Test with single interview: `python scripts/test_single_interview.py`
2. Check OpenAI API key is valid
3. Review `intelligence_capture/logging_config.py` for error logs
4. Verify Spanish encoding (UTF-8) in source files

**RAG Agent Issues**:
1. Check Pydantic AI agent logs
2. Verify vector/graph databases are populated
3. Test individual tools in isolation
4. Review Spanish system prompt effectiveness

**Cost Overruns**:
1. Check CostGuard settings
2. Review per-query costs in `/health` endpoint
3. Audit LLM model selection (ensure gpt-4o-mini is primary)
4. Consider rate limiting or query caching

### Escalation Path

1. **Documentation**: Check `docs/` directory first
2. **Specifications**: Review `.kiro/specs/` for detailed requirements
3. **Decisions**: Check `docs/DECISIONS.md` for ADRs
4. **Issues**: Create GitHub issue with reproduction steps
5. **Emergency**: Contact project owner with incident details

---

## 📅 Timeline Summary

### Completed Milestones

- **Oct 22-23, 2025**: Initial extraction system (v1.0 - 6 entity types)
- **Oct 24-25, 2025**: Added v2.0 entities (11 new types, 17 total)
- **Oct 26-28, 2025**: ValidationAgent, ExtractionMonitor, multi-model fallback
- **Nov 7-8, 2025**: Knowledge Graph consolidation implementation (DuplicateDetector, EntityMerger, ConsensusScorer)
- **Nov 9, 2025**: ✅ Phase 12 Complete - Consolidation production-ready (9.5/10 quality score)
- **Nov 9-13, 2025**: 🟡 RAG 2.0 Week 1/5 - Context Registry, connectors, partial document processor

### Immediate Next Steps (2-3 days)

- **Day 1**: Fix dependencies, UTF-8 violations, establish test baseline
- **Day 2**: Complete PostgreSQL async integration
- **Day 3**: Write missing unit tests (Context Registry + Connectors)

### Short-Term Goals (Week 2-3, 10-14 days)

- **Week 2**: Embedding pipeline with CostGuard, Neo4j knowledge graph builder
- **Week 3**: Pydantic AI agent with 4 tools, FastAPI endpoints, CLI

### Medium-Term Goals (Week 4-5, 7-10 days)

- **Week 4**: Spanish evaluation dataset, retrieval quality harness, performance tuning
- **Week 5**: ConsolidationSync integration, ingestion worker automation, operational runbook

### Long-Term Vision (3-6 months)

- **Month 2**: Production deployment with monitoring and alerting
- **Month 3**: Multi-tenant expansion (additional organizations)
- **Month 4-6**: Advanced features (summarization, question generation, trend analysis)

---

## 🎓 Lessons Learned

### What Worked Well

1. **Spanish-First Processing**: No translation preserved context, reduced cost, maintained accuracy
2. **Multi-Model Fallback Chain**: 99.9% success rate despite individual model failures
3. **Fuzzy-First Filtering**: 96x speedup, 95% cost reduction in consolidation
4. **Consolidation Before RAG**: 80-95% duplicate reduction creates cleaner knowledge graph
5. **Comprehensive Documentation**: 14 master docs + 81 archived provide complete context
6. **Systematic Task Tracking**: .kiro/specs/ structure keeps requirements aligned with implementation

### What to Avoid (Future Projects)

1. **Building Features Before Foundation**: RAG 2.0 attempted before consolidation was production-ready created technical debt
2. **Parallel Processing Without Testing**: Database locking issues could have been caught earlier with proper load testing
3. **Over-Engineering Validation**: Ensemble validation (3x cost, 3x time) not justified for value delivered (ADR-008)
4. **False Completion Claims**: Reporting "103 tests, 85% coverage" when actual was 0 tests eroded trust (QA review Nov 9)
5. **Ignoring Dependencies**: 67 missing packages should have been caught by CI/CD before QA review

### Best Practices Established

1. **UTF-8 Everywhere**: All JSON dumps with `ensure_ascii=False`, explicit encoding in file I/O
2. **Type Hints Mandatory**: Catch bugs at development time, improve IDE support
3. **Test-Driven Development**: Write tests before implementation (learning from RAG 2.0 Phase 1 mistakes)
4. **Progressive Documentation**: Update docs as code changes, not after
5. **Cost Estimation First**: Calculate costs before running expensive operations
6. **Checkpoint Validation**: Generate governance artifacts for approval before proceeding

---

## 📖 Glossary

**ADR (Architecture Decision Record)**: Documented design decision with context, decision, and consequences

**CostGuard**: Budget enforcement system that throttles at $900/month, hard stops at $1,000/month

**Consolidation**: Process of deduplicating and merging similar entities across interviews (80-95% reduction)

**Dual Storage**: Parallel fan-out to PostgreSQL (vectors) and Neo4j (graph) for different query types

**Ensemble Validation**: Deprecated multi-model validation system (3x cost, not justified - ADR-008)

**Entity Types**: 17 categories of business intelligence (PainPoint, Process, System, KPI, etc.)

**HNSW (Hierarchical Navigable Small World)**: Vector index algorithm for fast similarity search (<100ms)

**MRR (Mean Reciprocal Rank)**: Retrieval quality metric, average position of first relevant result

**pgvector**: PostgreSQL extension for vector similarity search

**Precision@5**: Percentage of top-5 results that are relevant to the query

**RAG (Retrieval-Augmented Generation)**: LLM + retrieval system for grounded, fact-based responses

**Spanish-First**: Design principle: no translation, UTF-8 everywhere, Spanish stopwords/stemming

**Zero-AI Requirements**: Production framework (2400+ lines) in `.kiro/specs/zero-ai/requirements.md`

---

**Generated by**: BMad Method document-project workflow (exhaustive scan)
**For**: Danny Gonzales (Comversa)
**Purpose**: Systematic refactoring and production hardening
**Next Steps**: Follow Phases 1-4 of the Systematic Refactoring Roadmap
**Contact**: See `CLAUDE.md` for project governance and agent roles

---

_This document is the master AI-retrieval index. Update it as the codebase evolves. Archive old versions to `docs/archive/YYYY-MM/` with timestamp._
