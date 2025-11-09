# System0 - Spanish Interview Intelligence Platform

**Status**: ✅ Phase 12 Complete (Consolidation Production-Ready) | 🟡 RAG 2.0 in Progress (Week 1/5)
**Last Updated**: November 9, 2025
**Business Value**: Extract and query actionable intelligence from 44 Spanish manager interviews

---

## What Questions Can You Answer?

### ✅ Available Now (Phase 12 - Consolidation)
- **"¿Cuántas veces se menciona Excel en las entrevistas?"**
  → Answer: 25 menciones consolidadas (80-95% duplicate reduction)

- **"¿Qué sistemas tienen el mayor número de puntos de dolor?"**
  → Answer: Excel (25), SAP (12), WhatsApp (8) via SQLite queries

- **"¿Cuáles son los patrones recurrentes identificados?"**
  → Answer: 4 patterns with 3+ mentions across interviews

### 🟡 Coming Soon (Week 3 - RAG 2.0 Agentic Layer)
- **"Busca todas las referencias a 'automatización' en las entrevistas"**
  → Semantic search across document chunks (pgvector)

- **"¿Qué sistemas causan más puntos de dolor en Los Tajibos?"**
  → Graph queries (Neo4j): System→CAUSES→PainPoint relationships

- **"¿Qué dice el contrato Q4 sobre presupuesto de automatización?"**
  → PDF chunk search with source citations

- **"Dame un resumen de oportunidades de automatización con mayor consenso"**
  → Hybrid search (vector + graph) with conversation memory

---

## Quick Start (5 Minutes)

```bash
# 1. Setup environment
cp .env.example .env
pip install -r intelligence_capture/requirements.txt

# 2. Configure OpenAI API key
echo "OPENAI_API_KEY=sk-proj-your-key" >> .env

# 3. Test extraction with single interview
python scripts/test_single_interview.py

# 4. Run consolidation
python scripts/test_consolidation.py

# 5. Check results
sqlite3 data/full_intelligence.db "SELECT COUNT(*) FROM consolidated_entities;"
```

**Expected**: ~30 seconds, $0.03, consolidation of 17 entity types with 80%+ confidence

---

## System Architecture

### Current State (✅ Production Ready)

```
44 Spanish Interviews (JSON)
    ↓
Intelligence Extractor (17 entity types)
    ↓
SQLite Storage (raw entities)
    ↓
Consolidation Agent ✅ (Phase 12 Complete)
├─ Duplicate Detector (fuzzy + semantic, 96x speedup)
├─ Entity Merger (source tracking, consensus scoring)
├─ Relationship Discoverer (4 types)
└─ Pattern Recognizer (recurring themes)
    ↓
Consolidated Entities in SQLite
- 80-95% duplicate reduction
- Consensus confidence scores
- Relationship mapping
- Performance: <5 min for 44 interviews
```

**Key Components**:
- **17 Entity Types**: PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency, CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency
- **Consolidation System**: [docs/CONSOLIDATION_RUNBOOK.md](CONSOLIDATION_RUNBOOK.md)
- **Metrics**: Processing time, confidence scores, relationship counts

### RAG 2.0 Architecture (🟡 Week 1-5 Implementation)

```
Multi-Format Documents (PDF/images/CSV/WhatsApp/JSON)
    ↓
Context Registry (multi-org namespace, privacy compliance)
    ↓
Document Processor + OCR (Mistral Pixtral, Spanish-optimized)
    ↓
Spanish Chunking (300-500 tokens, accent-aware)
    ↓
DUAL STORAGE:
├─ PostgreSQL + pgvector (document chunks + embeddings)
│   - 1536-dim vectors (OpenAI text-embedding-3-small)
│   - HNSW index for <1s semantic search
│   - Use case: "Find all mentions of 'automatización'"
│
└─ Neo4j + Graffiti (consolidated entities + relationships)
    - Graph queries: System→CAUSES→PainPoint
    - Use case: "What systems cause the most pain?"
    ↓
Pydantic AI Agent (Spanish system prompt)
├─ Tool: vector_search (semantic similarity)
├─ Tool: graph_search (relationship traversal)
├─ Tool: hybrid_search (vector + graph fusion)
└─ Tool: checkpoint_lookup (governance artifacts)
    ↓
FastAPI Endpoints
├─ POST /chat (conversational queries)
├─ POST /chat/stream (SSE streaming)
└─ GET /health (system status)
```

**Implementation Guide**: [docs/RAG2_IMPLEMENTATION.md](RAG2_IMPLEMENTATION.md)

---

## Documentation Map

### Getting Started
- **[This README]** - Project overview and quick start
- **[CLAUDE.md](../CLAUDE.md)** - Master project guide for AI agents

### Current System (Phase 12 Complete)
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and components
- **[CONSOLIDATION_RUNBOOK.md](CONSOLIDATION_RUNBOOK.md)** - Consolidation operations
- **[QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md)** - Production readiness status (Phase 12: 9.5/10)
- **[RUNBOOK.md](RUNBOOK.md)** - Operational procedures

### RAG 2.0 Implementation (Week 1-5)
- **[RAG2_IMPLEMENTATION.md](RAG2_IMPLEMENTATION.md)** - Week-by-week build guide
- **[AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md)** - Pydantic AI deep dive (Week 3)
- **[API_CONTRACT.md](API_CONTRACT.md)** - FastAPI endpoint specifications (Week 3)
- **[TOOL_DEVELOPMENT.md](TOOL_DEVELOPMENT.md)** - Add retrieval tools (Week 3+)

### Design & Decisions
- **[DECISIONS.md](DECISIONS.md)** - Architecture Decision Records (10 ADRs)
- **[EXPERIMENTS.md](EXPERIMENTS.md)** - Experiment log (6 experiments)
- **[.kiro/specs/](../.kiro/specs/)** - Detailed requirements and tasks

### Development
- **[.ai/CODING_STANDARDS.md](../.ai/CODING_STANDARDS.md)** - Spanish-first, UTF-8, type hints
- **[.codex/agent_roles.yaml](../.codex/agent_roles.yaml)** - Development agent roles

---

## Key Metrics & Achievements

### Phase 12 Complete (Consolidation - Production Ready)
- ✅ **Overall Score**: 9.5/10 (+46% from Phase 9)
- ✅ **Tasks Complete**: 40/52 (77%)
- ✅ **Performance**: <5 minutes for 44 interviews (96x speedup)
- ✅ **Cost Reduction**: 95% API calls saved (fuzzy-first filtering)
- ✅ **Duplicate Reduction**: 80-95% (e.g., 25 Excel mentions → 1 entity)
- ✅ **Consensus Confidence**: Average 0.75+ across all entity types
- ✅ **Test Results**: Pilot ✅, Full (44 interviews) ✅

### RAG 2.0 Target Metrics (Week 5)
- 🎯 **Query Response Time**: <1s for vector search, <2s for graph queries
- 🎯 **Retrieval Quality**: Precision@5 ≥0.80, MRR ≥0.75
- 🎯 **Monthly Cost**: $500-$1,000 USD (CostGuard throttles at $900)
- 🎯 **Multi-format Support**: PDF, images, CSV, WhatsApp, JSON
- 🎯 **Spanish Accuracy**: 95%+ for OCR and chunking

---

## Business Value Delivered

### Current Capabilities (Phase 12)
1. **Consolidated Intelligence**:
   - 25 "Excel" mentions → 1 entity with source_count=25, consensus_confidence=0.95
   - Query: "How many times is SAP mentioned?" Answer: 12 interviews, confidence 0.88

2. **Relationship Mapping**:
   - System→CAUSES→PainPoint: "Excel causes manual data entry pain"
   - Process→USES→System: "Invoicing process uses SAP"
   - 4 relationship types discovered across 44 interviews

3. **Pattern Recognition**:
   - Recurring pain points (3+ mentions): Manual processes, system disconnects
   - Problematic systems (5+ mentions): Excel, SAP, WhatsApp
   - 4 high-priority patterns identified

4. **Source Tracking**:
   - Every entity tracked to source interviews
   - Consensus scoring for multi-source validation
   - Contradiction detection for human review

### Future Capabilities (RAG 2.0 - Week 5)
1. **Conversational Queries**:
   - Natural language: "¿Qué sistemas causan más problemas en Los Tajibos?"
   - Spanish-first responses with source citations
   - Multi-turn conversations with memory

2. **Multi-Format Intelligence**:
   - Process PDFs: contracts, reports, invoices
   - OCR scanned documents: forms, handwritten notes
   - Parse spreadsheets: KPI data, budgets

3. **Semantic Search**:
   - Vector similarity: "Find all mentions of 'automatización'"
   - Graph traversal: "Show all systems used by Finance"
   - Hybrid queries: Combine semantic + relational context

4. **Governance Integration**:
   - Checkpoint retrieval: Approved extraction artifacts
   - Privacy compliance: Bolivian Constitution Art. 21, Law 164
   - Cost tracking: Per-query budget monitoring

---

## Companies & Organizational Structure

### Three Bolivian Companies
- **Los Tajibos** - Hotel operations (15 interviews)
- **Comversa** - Construction & real estate (15 interviews)
- **Bolivian Foods** - Restaurant franchises (14 interviews)

### Multi-Org Namespace (RAG 2.0)
- Context Registry enforces org-level isolation
- Each org has separate: embeddings, graph, checkpoints
- Privacy compliance: No cross-org data leakage

---

## Development Workflow

### Current Operations (Phase 12)
```bash
# Run full extraction (44 interviews)
python intelligence_capture/run.py

# Run consolidation
python scripts/test_consolidation.py

# Check consolidation results
sqlite3 data/full_intelligence.db
> SELECT entity_type, COUNT(*) FROM consolidated_entities GROUP BY entity_type;

# Generate HTML dashboard
python intelligence_capture/consolidation_agent.py --dashboard
# View: reports/consolidation_dashboard_YYYYMMDD_HHMMSS.html
```

### RAG 2.0 Operations (Week 5)
```bash
# Start ingestion watcher (Week 1)
python intelligence_capture/ingestion_watcher.py

# Run embedding pipeline (Week 2)
python intelligence_capture/embeddings/run_batch.py --batch-size 100

# Start FastAPI server (Week 3)
uvicorn api.server:app --reload

# Test agent CLI (Week 3)
python -m agent.cli --verbose

# Evaluate retrieval quality (Week 4)
python scripts/evaluate_retrieval.py
```

---

## Testing

### Current Tests (Phase 12)
```bash
# Run all tests
pytest tests/ -v

# Test consolidation system
pytest tests/test_consolidation_agent.py -v
pytest tests/test_duplicate_detector.py -v
pytest tests/test_entity_merger.py -v

# Test with coverage
pytest tests/ --cov=intelligence_capture --cov-report=html
```

### RAG 2.0 Tests (Week 3-4)
```bash
# Test Pydantic AI agent
pytest tests/test_agent_tools.py -v

# Test FastAPI endpoints
pytest tests/test_api_endpoints.py -v

# Test retrieval quality
python scripts/evaluate_retrieval.py
# Metrics: Precision@5, MRR, response time
```

---

## Next Steps

### Week 1: Intake & OCR (Tasks 0-5)
- [ ] Context Registry for multi-org namespacing
- [ ] Source connectors (WhatsApp, CSV, PDF)
- [ ] Ingestion queue (Redis Stream or SQLite jobs)
- [ ] DocumentProcessor for multi-format parsing
- [ ] Mistral Pixtral OCR integration
- [ ] Spanish chunking strategy (300-500 tokens)

### Week 2: Dual Storage (Tasks 6-9)
- [ ] PostgreSQL + pgvector schema and migrations
- [ ] Embedding pipeline with cost tracking
- [ ] Neo4j + Graffiti setup
- [ ] Knowledge Graph Builder (consolidation → Neo4j)

### Week 3: Agentic RAG & API (Tasks 10-14)
- [ ] Pydantic AI agent with Spanish system prompt
- [ ] 4 retrieval tools (vector, graph, hybrid, checkpoint)
- [ ] FastAPI server (/chat, /chat/stream, /health)
- [ ] CLI for interactive testing
- [ ] Session management and memory

### Week 4: Quality & Governance (Tasks 15-18)
- [ ] Spanish evaluation dataset (50 questions)
- [ ] Retrieval quality harness (Precision@5, MRR)
- [ ] CostGuard integration and alerting
- [ ] Checkpoint manager for governance

### Week 5: Consolidation & Automation (Tasks 19-21)
- [ ] ConsolidationSync → PostgreSQL
- [ ] ConsolidationSync → Neo4j
- [ ] Ingestion worker with consolidation mode
- [ ] Backlog alert system
- [ ] RAG2 operational runbook
- [ ] Compliance evidence bundle

**Detailed Timeline**: [.kiro/specs/rag-2.0-enhancement/tasks.md](../.kiro/specs/rag-2.0-enhancement/tasks.md)

---

## Support & Contributing

### Questions?
1. Check **[RUNBOOK.md](RUNBOOK.md)** for operational procedures
2. Review **[DECISIONS.md](DECISIONS.md)** for design rationale
3. Read **[ARCHITECTURE.md](ARCHITECTURE.md)** for technical details
4. Consult **[.kiro/specs/](../.kiro/specs/)** for detailed requirements

### Found a Bug?
1. Check **[QUALITY_ASSURANCE.md](QUALITY_ASSURANCE.md)** - is it a known issue?
2. Review **[ARCHITECTURE.md](ARCHITECTURE.md)** Known Issues section
3. Document in **[DECISIONS.md](DECISIONS.md)** as new ADR if significant
4. Create GitHub issue with reproduction steps

### Want to Contribute?
1. Read **[.ai/CODING_STANDARDS.md](../.ai/CODING_STANDARDS.md)** - Spanish-first, UTF-8, type hints
2. Review **[.codex/agent_roles.yaml](../.codex/agent_roles.yaml)** - development roles
3. Check **[.kiro/specs/](../.kiro/specs/)** for open tasks
4. Test with single interview before batch operations

---

## Project History

### Timeline
- **Oct 22-23, 2025**: Initial extraction system (v1.0 - 6 entity types)
- **Oct 24-25, 2025**: Added v2.0 entities (11 new types)
- **Oct 26-28, 2025**: ValidationAgent, ExtractionMonitor, multi-model fallback
- **Nov 7-8, 2025**: Knowledge Graph consolidation implementation
- **Nov 9, 2025**: Phase 12 complete - consolidation production-ready (9.5/10)
- **Nov 9, 2025**: RAG 2.0 architecture defined, Week 1 starting

### Key Lessons Learned
**What Worked**:
- ✅ Spanish-first processing (preserved context, reduced cost)
- ✅ Multi-model fallback chain (99.9% success rate)
- ✅ Fuzzy-first filtering (96x speedup, 95% cost reduction)
- ✅ Consolidation before RAG (80-95% duplicate reduction)

**What to Avoid**:
- ❌ Building features before fixing foundation (created technical debt)
- ❌ Parallel processing without proper testing (database locking)
- ❌ Over-engineering validation (ensemble not justified for cost)

---

## License

[Add license information]

---

## Archived Documentation

Previous documentation (81 files) archived to `docs/archive/2025-11/`.

**Reason for consolidation**: Multiple conflicting documents, unclear source of truth, documentation vs reality gap.

**Master documents** (this folder) are now the **single source of truth**.

---

**Last Updated**: November 9, 2025
**Status**: ✅ Phase 12 Complete (Consolidation Production-Ready) | 🟡 RAG 2.0 Week 1/5
**Next Milestone**: Multi-format ingestion → Dual storage → Agentic layer → Production
