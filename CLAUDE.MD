# CLAUDE.md

This file defines how Claude/Codex agents work inside this repository. Load it **together with** `.codex/manifest.yaml` and `.codex/agent_roles.yaml` before making changes.

---

## 1. Project Overview

**RAG-Comversa** converts 44 Spanish manager interviews (and new multi-format documents) into structured intelligence used by agentic RAG services.

- **Language:** Spanish only – never translate interview content or responses.
- **Current Datastore:** SQLite (17 entity tables) → migrating to PostgreSQL + pgvector + Neo4j.
- **Models:** OpenAI gpt-4o-mini (primary), six-model fallback chain, Mistral Pixtral OCR.
- **Companies:** Los Tajibos, Comversa, Bolivian Foods.
- **Source Specs:**
  - `.kiro/specs/rag-2.0-enhancement/{requirements,design,tasks}.md`
  - `.kiro/specs/knowledge-graph-consolidation/{requirements,tasks}.md`

---

## 1.5. Quick Start (New Developers)

**First Time Setup:**
```bash
cp .env.example .env          # Add your OpenAI API key
pip install -r intelligence_capture/requirements.txt
python scripts/check_setup.py # Verify setup
```

**Test the System:**
```bash
python scripts/test_single_interview.py  # ~10s, $0.01
```

**Current State:** RAG 2.0 Week 1/5 in progress. See §2 for timeline.
**Critical Constraints:** Spanish-only (NEVER translate), UTF-8 everywhere, cost guardrails active.
**Start Here:** Read [docs/README.md](docs/README.md), then [ARCHITECTURE.md](docs/ARCHITECTURE.md)

---

## 2. Current Focus & Timeline (RAG 2.0) ⚠️ Check `.kiro/specs/*/tasks.md` for current status

| Horizon | Objectives | Key Artifacts |
| --- | --- | --- |
| **Week 1 – Intake & OCR** | Context registry, source connectors, ingestion queue, DocumentProcessor refresh, Mistral Pixtral OCR, Spanish chunking | `.kiro/specs/rag-2.0-enhancement/tasks.md` (tasks 0–5) |
| **Week 2 – Dual Storage** | PostgreSQL+pgvector migrations, embedding pipeline with CostGuard, Neo4j builder | same tasks (6–9) |
| **Week 3 – Agentic RAG & API** | Pydantic AI agent, vector/graph/hybrid tools, FastAPI endpoint, CLI | tasks 10–14 |
| **Week 4 – Quality & Governance** | Retrieval evaluation harness, Spanish optimization, performance tuning, checkpoints & approvals | tasks 15–18 |
| **Week 5 – Consolidation & Automation** | ConsolidationSync ↔ Postgres/Neo4j, ingestion workers, backlog alerts, runbooks & compliance evidence | tasks 19–21 + `.kiro/specs/knowledge-graph-consolidation/*` |

**Week 2 Update (11-nov-2025):** PostgreSQL+pgvector+Neo4j setup complete. Database `comversa_rag` operational with 12 tables, HNSW vector indexing ready. Neo4j knowledge graph operational with 1,743 consolidated entities. Complete data pipeline: SQLite → PostgreSQL → Neo4j working. Next: embedding pipeline (Task 7).

**Semana 5 · Actualización (10-nov-2025):** ConsolidationSync ya fan-out a Postgres/Neo4j (`intelligence_capture/consolidation_sync.py`), CLI operativa `scripts/sync_graph_consolidation.py`, worker + monitor (`intelligence_capture/ingestion_worker.py`, `intelligence_capture/monitoring/backlog_monitor.py`) y pruebas `tests/test_rag2_consolidation_integration.py`.

Always consult `.codex/manifest.yaml` for authoritative phase status before coding.

---

## 2.5. Key Directory Structure

```
system0/
├── intelligence_capture/     # Core extraction system
│   ├── extractor.py         # 17 entity type extractors
│   ├── processor.py         # Main pipeline orchestrator
│   ├── consolidation_agent.py  # Entity deduplication
│   ├── validation_agent.py  # Quality validation
│   └── database.py          # SQLite schema (17 tables)
├── tests/                    # Pytest test suite
├── scripts/                  # Operational scripts
│   ├── test_*.py           # Legacy test scripts
│   ├── migrations/         # Database migrations
│   └── evaluate_retrieval.py
├── .kiro/specs/             # Requirements & task tracking
│   ├── rag-2.0-enhancement/
│   ├── knowledge-graph-consolidation/
│   ├── extraction-completion/
│   └── ontology-enhancement/
├── data/                    # Interview transcripts & databases
├── reports/                 # Analysis outputs & checkpoints
└── docs/                    # Architecture & decisions
```

---

## 3. Guardrails & Compliance

| Category | Rule |
| --- | --- |
| Language | Never translate interviews or agent responses. Enforce UTF-8 with `ensure_ascii=False`.
| Privacy | All assets must be tagged with Context Registry metadata; no cross-org leakage.
| Cost | Maintain $500–$1,000 USD monthly envelope. CostGuard throttles >$900 and stops >$1,000 without approval.
| Checkpoints | Generate bundles for ingestion, OCR, consolidation, retrieval eval, and pre-prod agent runs under `reports/checkpoints/{org}/{stage}`. Log reviewer decisions in `model_reviews`.
| Safety | No destructive Git or data commands unless explicitly requested. Respect existing uncommitted work.
| Data Handling | Use sanitized fixtures for tests; do not ingest docs lacking consent metadata.

Guardrails duplicated in `.codex/manifest.yaml` for automated agents.

---

## 4. Multi-Agent Roles (see `.codex/agent_roles.yaml` for details)

| Role | Mission | Primary Paths |
| --- | --- | --- |
| Orchestrator | Maintain specs/tasks, enforce guardrails, coordinate approvals | `.kiro/specs`, `.codex`, `docs/` |
| Intake & Processing | Connectors, DocumentProcessor, OCR, Spanish chunker | `intelligence_capture/{connectors,document_processor,ocr,chunking}`, `scripts/watch_inbox.py` |
| Storage & Graph | Postgres migrations, embeddings pipeline, Neo4j builder | `scripts/migrations/`, `intelligence_capture/{database,embeddings}`, `graph/` |
| Agent & API | Pydantic AI agent, retrieval tools, FastAPI, CLI | `agent/`, `api/`, `prompts/`, `tests/test_agent*` |
| Quality & Governance | Evaluation harness, Spanish optimization, CostGuard, checkpoints, approvals | `reports/`, `scripts/evaluate_retrieval.py`, `intelligence_capture/cost_guard.py`, `governance/` |
| Consolidation & Automation | ConsolidationSync ↔ Postgres/Neo4j, ingestion workers, runbooks | `intelligence_capture/consolidation_agent.py`, `intelligence_capture/ingestion_worker.py`, `docs/RAG2_runbook.md` |

Each role has allowed/forbidden paths and approval rules in the YAML file—follow them strictly.

---

## 5. Master Documentation

1. **docs/README.md** – documentation index.
2. **docs/ARCHITECTURE.md** – system diagrams + data model.
3. **docs/DECISIONS.md** – ADRs.
4. **docs/RUNBOOK.md** – operational commands & troubleshooting.
5. **docs/EXPERIMENTS.md** – LLM/architecture experiments.
6. **docs/RAG2_runbook.md** – to capture Week 5 operational handover (in progress).

Older docs live in `docs/archive/2025-11/` for reference only.

---

## 6. System Snapshot

- **Extraction status:** All 17 entity types working with ValidationAgent, ExtractionMonitor, rate limiter, cost estimation.
- **Database status:**
  - ✅ **PostgreSQL 15 + pgvector 0.8.1** operational (2025-11-11)
  - ✅ **12 tables created:** documents, document_chunks, embeddings (HNSW indexed), consolidated_entities (1,743 entities), consolidated_relationships, consolidation_events, context_registry, ingestion_events, ocr_review_queue
  - ✅ **Extensions:** pgvector, pgcrypto, uuid-ossp
  - ✅ **Neo4j 2025.10.1** operational (2025-11-11)
  - ✅ **Knowledge Graph:** 1,743 consolidated entities across 13 types, constraints & indexes active
  - ✅ **Consolidation Sync:** SQLite → PostgreSQL → Neo4j pipeline working
  - 🔄 **SQLite** still active for extraction (17 entity tables) until full cutover
- **RAG 2.0 Progress:**
  - ✅ **Week 1 (Tasks 0-5):** Complete - Intake, OCR, Spanish chunking
  - ✅ **Week 2 (Task 6):** Complete - PostgreSQL+pgvector migrations
  - ✅ **Week 2 (Task 8-9):** Complete - Neo4j setup, consolidation sync backfill
  - ⏳ **Week 2 (Task 7):** Pending - Embedding pipeline
- **Critical issues:** Cost guard for embedding pipeline pending, ingestion automation incomplete.
- **Consolidation:** ✅ **Phase 12 COMPLETE - Production Ready** (77% done - 40/52 tasks)
  - **Phases 1-12 COMPLETE:** Foundation, core components, database integration, relationships & patterns, testing, reporting, security hardening, performance optimization, code quality, final validation
  - Core system production-ready: DuplicateDetector, EntityMerger, ConsensusScorer, RelationshipDiscoverer, PatternRecognizer
  - **Performance:** <5 minutes for 44 interviews, 96x speedup, 95% cost reduction
  - **Security:** SQL injection prevention, transaction management, API retry logic
  - **Quality:** Comprehensive test suite, structured logging, metrics collection, rollback capability
  - **Documentation:** Production runbook (`docs/CONSOLIDATION_RUNBOOK.md`), comprehensive guide (`docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md`)
  - **Validation:** Pilot test (5 interviews) and full test (44 interviews) passed
  - **Pending:** PostgreSQL/Neo4j sync (Week 5 - Phases 13-14), production deployment
  - **See:** `.kiro/specs/knowledge-graph-consolidation/*` for specs and progress

### 17 Entity Types
- **v1.0 (6):** PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency
- **v2.0 (11):** CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency, Enhanced v1.0s

---

## 7. Key Architecture Patterns

- **Spanish-First Processing (ADR-001):** never translate; rely on UTF-8, Spanish stopwords/stemming.
- **Multi-Model Fallback (EXP-003):** `gpt-4o-mini → gpt-4o → gpt-3.5-turbo → o1-mini → o1-preview → claude-3.5-sonnet`.
- **WAL Mode + Rate Limiter (ADR-007):** necessary for concurrent extraction; still under validation.
- **Dual Storage (Design §2):** Document chunks + embeddings in PostgreSQL/pgvector; consolidated entities/relationships in Neo4j via Graffiti.
- **Agentic RAG:** Pydantic AI orchestrator picks vector/graph/hybrid tools; FastAPI `/chat` + CLI.

---

## 8. Key Workflows & Commands

### Environment Setup
```bash
cp .env.example .env
pip install -r intelligence_capture/requirements.txt
```

### Legacy Extraction / Consolidation (JSON transcripts)
```bash
python scripts/test_single_interview.py
python scripts/test_batch_interviews.py --batch-size 5
# Full run (after WAL/rate-limit validation)
python intelligence_capture/run.py
```

### RAG 2.0 Pipeline (in progress)
```bash
python intelligence_capture/ingestion_watcher.py
python intelligence_capture/ingestion_worker.py --concurrency 4
python intelligence_capture/embeddings/run_batch.py --batch-size 100
psql $DATABASE_URL -f scripts/migrations/2025_01_01_pgvector.sql
uvicorn api.server:app --reload
python -m agent.cli --verbose
python scripts/evaluate_retrieval.py
```

### Quick DB Checks
```bash
sqlite3 intelligence.db "SELECT COUNT(*) FROM pain_points;"
psql $DATABASE_URL -c "SELECT COUNT(*) FROM document_chunks;"
```

### Testing

#### Run All Tests
```bash
pytest tests/ -v
```

#### Run Specific Test File
```bash
pytest tests/test_consolidation_agent.py -v
```

#### Run Single Test Function
```bash
pytest tests/test_duplicate_detector.py::TestDuplicateDetector::test_exact_match -v
```

#### Run Tests with Coverage
```bash
pytest tests/ --cov=intelligence_capture --cov-report=html
```

#### Common Test Scripts (Legacy)
```bash
# Single interview extraction test
python scripts/test_single_interview.py

# Batch interview tests
python scripts/test_batch_interviews.py --batch-size 5

# Consolidation system test
python scripts/test_consolidation.py
```

### Database Operations

⚠️ **IMPORTANT:** Three database systems in use:
- **SQLite** (current/legacy): 17 entity tables, local `data/full_intelligence.db`
- **PostgreSQL+pgvector** (RAG 2.0, ✅ operational): Document chunks + embeddings + consolidated entities, 12 tables
- **Neo4j** (RAG 2.0, ✅ operational): Consolidated knowledge graph, 1,743 entities

#### PostgreSQL Setup (✅ Complete - 2025-11-11)
```bash
# Connection details (from .env)
DATABASE_URL=postgresql://postgres@localhost:5432/comversa_rag
DB_TYPE=postgresql

# psql is in PATH (added to ~/.zshrc)
psql -U postgres -d comversa_rag

# List all tables
psql -U postgres -d comversa_rag -c "\dt"

# Check extensions
psql -U postgres -d comversa_rag -c "SELECT extname, extversion FROM pg_extension;"

# Verify embeddings table
psql -U postgres -d comversa_rag -c "\d embeddings"

# Check table counts
psql -U postgres -d comversa_rag -c "
SELECT
    schemaname, tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

#### SQLite Operations (Legacy)
```bash
# Switch to SQLite mode
export DB_TYPE=sqlite

# List all tables
sqlite3 data/full_intelligence.db ".tables"

# Show table schema
sqlite3 data/full_intelligence.db ".schema pain_points"

# Check consolidation status
sqlite3 data/full_intelligence.db "SELECT entity_type, COUNT(*) FROM consolidated_entities GROUP BY entity_type;"
```

#### Neo4j Operations (✅ Complete - 2025-11-11)
```bash
# Connection details (from .env)
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=comversa_neo4j_2025

# Access Neo4j Browser (visual query interface)
# URL: http://localhost:7474
# Username: neo4j
# Password: comversa_neo4j_2025

# Command-line cypher-shell
export NEO4J_PASSWORD=comversa_neo4j_2025
cypher-shell -u neo4j -p "$NEO4J_PASSWORD"

# Count all entities
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) RETURN count(n) as total_nodes"

# Entity breakdown by type
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) RETURN n.entity_type as type, count(n) as count ORDER BY count DESC"

# High-confidence entities
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) WHERE n.consensus_confidence > 0.85 RETURN n.entity_type, n.name, n.source_count LIMIT 10"

# Clear all data (use with caution)
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n) DETACH DELETE n"
```

#### Consolidation Sync Pipeline
```bash
# Backfill PostgreSQL from SQLite consolidated entities (one-time)
python scripts/backfill_consolidated_entities.py

# Sync PostgreSQL consolidated entities to Neo4j
export NEO4J_PASSWORD=comversa_neo4j_2025
python scripts/sync_consolidated_to_neo4j.py

# Sync using ConsolidationSync event-driven pipeline
python scripts/sync_graph_consolidation.py --mode full

# Check sync status
python scripts/sync_graph_consolidation.py --mode dry-run
```

#### Migration Scripts
```bash
# PostgreSQL migrations (executed in order)
psql -U postgres -d comversa_rag -f scripts/migrations/2025_01_00_context_registry.sql
psql -U postgres -d comversa_rag -f scripts/migrations/2025_01_01_ingestion_queue.sql
psql -U postgres -d comversa_rag -f scripts/migrations/2025_01_01_pgvector.sql
psql -U postgres -d comversa_rag -f scripts/migrations/2025_01_02_ocr_review_queue.sql

# Rollback scripts available in scripts/migrations/rollback/
```

---

## 9. Testing & Quality Gates

| Stage | Requirement |
| --- | --- |
| Parsers/OCR/Chunking | Unit tests with sanitized fixtures. No real client data in tests. |
| Consolidation | Integration tests verifying mergers, consensus, rollback (`tests/test_consolidation_*.py`). |
| Postgres/Neo4j | Migration dry-run + rollback plan; Cypher smoke tests. |
| Agent/API | Contract tests for tools and FastAPI endpoints; CLI transcripts stored in `data/cli_sessions/`. |
| Retrieval Quality | `scripts/evaluate_retrieval.py` → `reports/retrieval_evaluation.json` (Precision@5 ≥0.80, MRR ≥0.75). |
| Governance | Checkpoint bundles archived; approvals recorded in `model_reviews`. No prod toggle without approval. |

CI must run relevant tests before merge; Orchestrator/Governance agents gate releases.

---

## 9.5. Development Workflow

### Starting New Work
1. `git checkout development && git pull`
2. `git checkout -b feat/your-feature`
3. Check `.kiro/specs/*/tasks.md` for current priorities
4. Review relevant agent role in `.codex/agent_roles.yaml`

### Before Committing
1. Run relevant tests: `pytest tests/test_your_feature.py -v`
2. Check code follows `.ai/CODING_STANDARDS.md`
3. Update task status in `.kiro/specs/*/tasks.md`
4. Generate checkpoint if required (see Guardrails §3)

### Code Review Checklist
- [ ] Spanish content not translated (`ensure_ascii=False` in JSON)
- [ ] Type hints on all function signatures
- [ ] UTF-8 encoding explicit in file operations
- [ ] Tests pass with sanitized fixtures (no real client data)
- [ ] Cost estimate logged if using LLM APIs

### Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| `Database is locked` | Enable WAL mode: `PRAGMA journal_mode=WAL` |
| `mojibake` (corrupted Spanish) | Verify `ensure_ascii=False` in json.dumps() |
| Rate limit errors | Check rate_limiter.py is being used |
| Missing API key | Check `.env` has `OPENAI_API_KEY=sk-...` |
| Import errors | Run from project root, activate venv |
| Cost overrun | Review CostGuard settings, check monthly budget |

---

## 10. Rules of Engagement

### Never
1. Translate Spanish content.
2. Skip tests or evaluations.
3. Disable cost or checkpoint guardrails without sign-off.
4. Introduce destructive Git commands.
5. Process documents lacking registry consent metadata.

### Always
1. Use UTF-8 + `ensure_ascii=False`.
2. Add type hints and transactions.
3. Estimate/record costs before expensive jobs.
4. Update specs/tasks when scope changes.
5. Log activity and metrics in `reports/` (status, performance, checkpoints).

---

## 11. Next Steps (from `.kiro/specs/rag-2.0-enhancement/tasks.md`)

1. Stand up Context Registry + connectors + ingestion queue (Tasks 0–2).
2. Implement multi-format DocumentProcessor, OCR pipeline, Spanish chunking (Tasks 3–5).
3. Apply PostgreSQL/pgvector migrations, embedding pipeline, Neo4j builder (Tasks 6–9).
4. Build Pydantic agent, retrieval tools, FastAPI endpoints, CLI (Tasks 10–14).
5. Ship evaluation harness, Spanish optimizations, CostGuard, checkpoint manager (Tasks 15–18).
6. Complete ConsolidationSync, ingestion workers, runbooks, compliance evidence (Tasks 19–21 & consolidation spec).

Track progress using `.kiro/specs/*/tasks.md` and report status in `reports/agent_status/`.

---

## 12. References

- `.codex/manifest.yaml` – initiatives, guardrails, checkpoints.
- `.codex/agent_roles.yaml` – responsibilities & approvals.
- `.kiro/specs/` – authoritative requirements, designs, tasks.
- **`.ai/CODING_STANDARDS.md`** – **Python coding standards (Spanish-first, UTF-8, type hints, docstrings)**
- `docs/RAG2_runbook.md` – operational procedures (Week 5 deliverable).

**Last Updated:** November 11, 2025  
**Status:** 🟡 RAG 2.0 enhancement in progress (Week 1/5)
