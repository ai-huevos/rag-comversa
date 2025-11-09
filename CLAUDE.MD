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

## 2. Current Focus & Timeline (RAG 2.0)

| Horizon | Objectives | Key Artifacts |
| --- | --- | --- |
| **Week 1 – Intake & OCR** | Context registry, source connectors, ingestion queue, DocumentProcessor refresh, Mistral Pixtral OCR, Spanish chunking | `.kiro/specs/rag-2.0-enhancement/tasks.md` (tasks 0–5) |
| **Week 2 – Dual Storage** | PostgreSQL+pgvector migrations, embedding pipeline with CostGuard, Neo4j builder | same tasks (6–9) |
| **Week 3 – Agentic RAG & API** | Pydantic AI agent, vector/graph/hybrid tools, FastAPI endpoint, CLI | tasks 10–14 |
| **Week 4 – Quality & Governance** | Retrieval evaluation harness, Spanish optimization, performance tuning, checkpoints & approvals | tasks 15–18 |
| **Week 5 – Consolidation & Automation** | ConsolidationSync ↔ Postgres/Neo4j, ingestion workers, backlog alerts, runbooks & compliance evidence | tasks 19–21 + `.kiro/specs/knowledge-graph-consolidation/*` |

Always consult `.codex/manifest.yaml` for authoritative phase status before coding.

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
- **Critical issues:** WAL/parallelism needs retest, cost guard for new pipelines pending, entity consolidation not yet synced to Neo4j, ingestion automation incomplete.
- **Consolidation:** ✅ **Phases 1-6 COMPLETE** (50% done - 26/52 tasks)
  - Core system production-ready: DuplicateDetector, EntityMerger, ConsensusScorer, RelationshipDiscoverer, PatternRecognizer
  - Comprehensive testing suite with integration tests
  - Validation scripts and HTML dashboard generator
  - Full documentation in `docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md`
  - **Pending:** PostgreSQL/Neo4j sync (Week 5), production hardening (Phases 7-12)
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
pip install -r requirements.txt
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
- `docs/RAG2_runbook.md` – operational procedures (Week 5 deliverable).

**Last Updated:** November 9, 2025  
**Status:** 🟡 RAG 2.0 enhancement in progress (Week 1/5)
