# Implementation Plan: RAG 2.0 Enhancement

## Overview

This plan translates the RAG 2.0 requirements and design blueprint into executable tasks that extend the existing SQLite-based extraction pipeline (see `CLAUDE.md`) and the consolidation work in `.kiro/specs/knowledge-graph-consolidation/*`. Work is organized along the five-week cadence outlined in the design, ensuring multi-format ingestion, dual storage, agentic retrieval, and governance are delivered without breaking current production behavior.

- **Current State Snapshot:** JSON transcript ingestion, 17 entity extraction, and consolidation specs exist, but there is no multi-format intake, OCR, pgvector, Neo4j graph, or agentic API. Data remains siloed in SQLite with 20–30% duplicates.
- **Goals:** Add context-aware ingestion for PDFs/images/CSVs, stand up PostgreSQL + pgvector and Neo4j, wire ConsolidationSync into both stores, layer Pydantic AI agents + FastAPI, enforce Spanish-first quality, and institute checkpoints that satisfy Bolivian privacy plus the $500–$1,000 USD/month spend guardrail.
- **Timeline:** Week 1 (Intake & Ingestion), Week 2 (Dual Storage & Embeddings), Week 3 (Agentic RAG + API), Week 4 (Quality, Spanish optimization, Performance, Governance), Week 5 (ConsolidationSync, automation, launch readiness).
- **Execution Controls:** Every agent must load `CLAUDE.MD`, `.codex/manifest.yaml`, `.codex/agent_roles.yaml`, and this tasks file before starting work (see `.ai/BOOTSTRAP.md`).

---

## Phase 1: Multi-Org Intake & Ingestion Fabric (Week 1)

- [x] 0. Stand up Context Registry & Org Namespace Controls ✅ **COMPLETE** (2025-11-09)
  - ✅ Created Postgres migration `scripts/migrations/2025_01_00_context_registry.sql` with `context_registry`, `context_registry_audit`, and `context_access_log` tables
  - ✅ Implemented `intelligence_capture/context_registry.py` with cached lookups, namespace validation, consent validation, and access logging
  - ✅ Shipped `scripts/context_registry_sync.py` for org onboarding from `config/companies.json` (50 namespaces across 3 orgs)
  - ✅ Created `config/context_registry.yaml` with compliance settings and integration hooks
  - ✅ Added `requirements-rag2.txt` with RAG 2.0 dependencies
  - 📊 **Summary:** [`reports/task_0_implementation_summary.md`](../../../reports/task_0_implementation_summary.md)
  - _Requirements: R0.1–R0.5, R6.3, R9.3_ ✅

- [x] 1. Normalize Source Connectors into Inbox Taxonomy ✅ **COMPLETE** (2025-11-11)
  - ✅ Built connector workers: `email_connector.py`, `whatsapp_connector.py`, `api_connector.py`, `sharepoint_connector.py` (6 files, 1,500+ LOC)
  - ✅ Implemented `base_connector.py` with ConnectorMetadata dataclass, file-size (50 MB) and batch (≤100) limits, consent validation
  - ✅ Created inbox taxonomy: `data/documents/inbox/{connector}/{org}/` with metadata envelopes
  - ✅ Added activity logging to `reports/connector_activity/{date}.jsonl` with Spanish error responses
  - 📊 **Summary:** [`reports/TASKS_1_5_DETAILED_STATUS_20251111.md`](../../../reports/TASKS_1_5_DETAILED_STATUS_20251111.md)
  - _Requirements: R1.1–R1.10, R7.1, R7.2, R0.2_ ✅

- [x] 2. Implement Queue-Based Ingestion Backbone ✅ **COMPLETE** (2025-11-11)
  - ✅ Implemented `intelligence_capture/queues/ingestion_queue.py` with PostgreSQL backend (464 LOC)
  - ✅ Created IngestionQueue class with enqueue/dequeue APIs, visibility timeouts (600s default), IngestionJob dataclass
  - ✅ Integrated with `ingestion_events` PostgreSQL table with job statuses (pending, in_progress, completed, failed, retry)
  - ✅ Added duplicate detection via SHA-256 checksums, backlog monitoring (24h alert threshold), and `data/ingestion_progress.json` tracking
  - ✅ Implemented retry logic (max 3 attempts) and queue statistics API
  - _Requirements: R7.1–R7.10, R0.3, R4.6_ ✅

- [x] 3. Extend DocumentProcessor for Multi-Format Parsing ✅ **COMPLETE** (2025-11-11)
  - ✅ Refactored `intelligence_capture/document_processor.py` with MIME type detection (python-magic) and adapter routing (1,800+ LOC across 8 files)
  - ✅ Implemented format adapters: `pdf_adapter.py`, `docx_adapter.py`, `csv_adapter.py`, `xlsx_adapter.py`, `image_adapter.py`, `whatsapp_adapter.py`, `base_adapter.py`
  - ✅ Created DocumentPayload dataclass with page_count, language, sections, tables, images, context_tags, and metadata
  - ✅ Built state directory management: `originals/`, `processing/`, `processed/`, `failed/` with checksum verification
  - ✅ All parsers preserve metadata, sections, and tables per requirements
  - _Requirements: R1.1–R1.10, R7.2, R11.2_ ✅

- [x] 4. Wire OCR Engine & Review Queue ✅ **COMPLETE** (2025-11-11)
  - ✅ Implemented `intelligence_capture/ocr/mistral_pixtral_client.py` with Spanish parameters and Mistral Pixtral API integration
  - ✅ Created `intelligence_capture/ocr/tesseract_fallback.py` for fallback OCR with Spanish language model
  - ✅ Built `intelligence_capture/ocr/ocr_coordinator.py` with rate limiter (max 5 concurrent), dual-engine orchestration, and retry logic
  - ✅ Added `ocr_review_queue` PostgreSQL table with confidence thresholds (0.70 handwriting, 0.90 printed)
  - ✅ Developed `intelligence_capture/ocr/ocr_reviewer_cli.py` for manual review with cropped image evidence
  - ✅ Capture bounding boxes, confidence scores, and document references in OCR output
  - _Requirements: R2.1–R2.7, R7.6_ ✅

- [x] 5. Implement Spanish-Aware Chunking & Metadata ✅ **COMPLETE** (2025-11-11)
  - ✅ Implemented `intelligence_capture/chunking/spanish_chunker.py` with spaCy (es_core_news_md) tokenization (500+ LOC)
  - ✅ Configured 300–500 token windows with 50-token overlap and sentence boundary alignment
  - ✅ Created `intelligence_capture/chunking/spanish_text_utils.py` with stopword removal, Snowball stemming, accent normalization
  - ✅ Built ChunkMetadata dataclass with document_id, chunk_index, section_title, page_number, token_count, span_offsets
  - ✅ Added SpanishFeatures tracking (stopwords, stemming, accents, tildes, formality, bilingual_score) in chunk metadata
  - ✅ Markdown structure preservation with heading levels, tables, and lists maintained
  - ✅ Language detection support (Spanish vs bilingual) with per-chunk language tracking
  - _Requirements: R1.5, R3.1–R3.7, R15.1_ ✅

---

## Phase 2: Dual Storage & Embeddings Foundation (Week 2)

- [x] 6. Create PostgreSQL + pgvector Schema & Migration Scripts ✅ (2025-11-10)
  - Author `scripts/migrations/2025_01_01_pgvector.sql` to create `documents`, `document_chunks`, `embeddings`, `ingestion_events`, and `ocr_review_queue` tables plus HNSW index (`m=16`, `ef_construction=200`) and pgvector extension enablement.
  - Add `config/database.toml` entries for Neon (read/write URIs, pool sizes) and integrate migration runner (`scripts/run_pg_migrations.py`) into CI so schema stays versioned.
  - Update `intelligence_capture/database.py` with Postgres repositories while keeping SQLite for consolidation history until cutover.
  - _Requirements: R4.1–R4.7, R7.5_

- [x] 7. Build Embedding Pipeline with Cost Tracking ✅ (2025-11-10)
  - Implement `intelligence_capture/embeddings/pipeline.py` to batch up to 100 chunks/call against `text-embedding-3-small`, cache results for 24 h (Redis or on-disk), and write vectors + metadata into the `embeddings` table.
  - Capture API spend per chunk (cost_cents) and expose hooks for `CostGuard` to throttle ingestion when monthly projections exceed $900 USD.
  - Provide retries/backoff and dead-letter logic so embedding failures don’t block non-affected documents.
  - _Requirements: R4.2–R4.7, R14.1, R7.8_

- [x] 8. Persist Document + Chunk Records Atomically ✅ (2025-11-10)
  - Create `intelligence_capture/persistence/document_repository.py` that wraps Postgres inserts for `documents`, `document_chunks`, and `embeddings` within a transaction; ensure failures roll files back to `data/documents/failed/` with detailed logs.
  - Update ingestion workers to acknowledge queue jobs only after Postgres write success and to update `ingestion_progress.json`/`ingestion_events` stages for resume support.
  - Add unit tests covering 10-page PDF ingestion (<2 min SLA) and CSV edge cases to de-risk batch uploads.
  - _Requirements: R1.4, R1.6–R1.8, R7.2–R7.7_

- [x] 9. Bootstrap Neo4j + Graffiti Knowledge Graph Builder ✅ (2025-11-10)
  - Stand up `graph/knowledge_graph_builder.py` using Graffiti episodes (one per document) to MERGE nodes (`System`, `Process`, `PainPoint`, etc.) and relationships (CAUSES, USES, HAS) with `org_id` namespaces and strength weighting.
  - Create bootstrapping script `scripts/graph/bootstrap_neo4j.py` that provisions indexes/constraints and validates Cypher queries required for hybrid retrieval.
  - Establish contract for ConsolidationSync to feed consolidated entities/relationships into Neo4j while writing back `neo4j_relationship_id` to SQLite for audit.
  - _Requirements: R5.1–R5.7, R12.2, R12.6_

---

## Phase 3: Agentic RAG & API Delivery (Week 3)

- [ ] 10. Implement Pydantic AI Agent Orchestrator
  - Create `agent/rag_agent.py` built on Pydantic AI with Spanish system prompt (from `prompts/system_agent_prompt.md`), context registry lookups, and conversation memory keyed by `session_id`.
  - Configure tool routing guidelines (vector vs graph vs hybrid) and ensure tool-call telemetry is logged for governance analysis.
  - Add fallbacks (gpt-4o as backup) without translating Spanish queries per requirements.
  - _Requirements: R6.1–R6.7, R0.3_

- [ ] 11. Ship Retrieval Tool Adapters & Hybrid Search
  - Implement `agent/tools/vector_search.py`, `agent/tools/graph_search.py`, and `agent/tools/hybrid_search.py` to query pgvector, Neo4j, or both in parallel, merge results (reciprocal rank fusion), and cache for 5 minutes.
  - Include deduplication logic, overrideable weighting (default 50/50), and structured source payloads for downstream API responses.
  - Instrument tool invocations to feed evaluation metrics and debugging dashboards.
  - _Requirements: R6.2–R6.6, R8.1–R8.7_

- [ ] 12. Expose FastAPI Endpoints & Health Checks
  - Build `api/server.py` with `/chat`, `/chat/stream` (SSE), `/health`, `/review/checkpoint`, and `/evaluate` endpoints; include API-key auth, 60 req/min rate limiting, and org-aware middleware.
  - Stream tool-call reasoning chunks to clients, return structured `{answer, sources, tool_calls}` payloads, and wire `/health` to check Postgres, Neo4j, OCR, and LLM readiness.
  - Log requests to `reports/api_usage/{date}.json` for compliance and cost tracking.
  - _Requirements: R9.1–R9.7, R16.4, R13.7_

- [ ] 13. Deliver Developer CLI for Interactive Testing
  - Create `agent/cli.py` (invoked via `python -m agent.cli`) that calls the FastAPI endpoints, colorizes user/agent/tool output, and supports `/reset`, `/sources`, `/stats`, `--verbose`, and `--log-file` flags.
  - Persist CLI sessions to `data/cli_sessions/{session_id}.jsonl` and expose similarity scores plus tool breakdowns per interaction.
  - _Requirements: R10.1–R10.7_

- [ ] 14. Add Session Storage, Telemetry & Cost Dashboards
  - Implement `chat_sessions` Postgres table plus `tool_usage_logs` capturing query text, selected tool, latency, and cost; update agent/API layers to persist multi-turn context here.
  - Feed telemetry into `reports/agent_usage/{org}/{date}.json` and alert when tool mis-selection exceeds 15% (per success criteria).
  - _Requirements: R6.4, R6.7, R9.3, R9.5_

---

## Phase 4: Quality, Spanish Optimization & Governance (Week 4)

- [ ] 15. Build Retrieval Evaluation Harness
  - Curate 50-question Spanish benchmark dataset (`tests/data/rag_eval/es_queries.json`) with ground-truth references mapped to document chunks and graph entities.
  - Implement `scripts/evaluate_retrieval.py` to run vector-only, graph-only, and hybrid modes, computing Precision@5, Recall@10, MRR, and NDCG, outputting `reports/retrieval_evaluation.json`.
  - Wire nightly CI job plus `/evaluate` API to block promotions when metrics regress relative to the latest approved checkpoint.
  - _Requirements: R13.1–R13.7, R16.5_

- [ ] 16. Complete Spanish Language Optimization
  - Add stopword removal, Snowball stemming, and accent-aware normalization utilities under `intelligence_capture/spanish_text/` and integrate them into chunking, vector search preprocessing, and agent prompts.
  - Maintain synonym dictionaries for business terms (e.g., “sistema” ↔ “herramienta”) and ensure all validation/API errors return Spanish text referencing Bolivian privacy obligations.
  - _Requirements: R15.1–R15.7, R3.5_

- [ ] 17. Implement Performance, Caching & CostGuard Controls
  - Introduce `intelligence_capture/cost_guard.py` that projects OCR/LLM/embedding spend, throttles ingestion to 2 concurrent workers >$900 USD, and hard-stops >$1,000 USD until override approval.
  - Configure Redis (or in-memory) caches for embeddings (24 h TTL) and hybrid search (5 min TTL), plus async connection pools (`asyncpg`, `neo4j.AsyncGraphDatabase`) sized per design.
  - Measure query SLAs (<1 s vector, <2 s graph, <2.5 s hybrid) and record in `reports/performance/{date}.json`.
  - _Requirements: R14.1–R14.7, cost guardrail_

- [ ] 18. Establish Governance Checkpoints & Approval Flow
  - Build `governance/checkpoint_manager.py` to package ingestion, OCR, consolidation, evaluation, and pre-production agent outputs into `reports/checkpoints/{org_id}/{stage}/{timestamp}`.
  - Add `model_reviews` table and `/review/checkpoint` endpoint/CLI for designated reviewers (Patricia, Samuel, Armando) to approve/reject bundles; block deployments until approvals recorded.
  - Automate rollback triggers when evaluation metrics drop or checkpoints regress, tying into ConsolidationSync + agent configs.
  - _Requirements: R16.1–R16.6, R13.5_

---

## Phase 5: ConsolidationSync, Automation & Launch Readiness (Week 5)

- [ ] 19. Wire ConsolidationSync into Postgres & Neo4j
  - Extend `intelligence_capture/consolidation_agent.py` and `ConsolidationSync` to emit events when entities merge, linking SQLite IDs to Postgres `documents/document_chunks` and Neo4j node IDs (`MENTIONED_IN`, `DERIVED_FROM` relationships).
  - Implement `scripts/sync_graph_consolidation.py` for manual replays and nightly reconciliation between SQLite (source of truth) and Neo4j.
  - Update Neo4j builder to ingest consolidated metrics (`source_count`, `consensus_confidence`) and transfer relationships during merges without data loss.
  - _Requirements: R11.1–R11.7, R12.1–R12.7_

- [ ] 20. Automate End-to-End Ingestion Workers & Backlog Alerts
  - Build `intelligence_capture/ingestion_worker.py` that consumes queue jobs, orchestrates DocumentProcessor → OCR → chunking → embeddings → entity extraction → ConsolidationSync → graph writes, ensuring ≤4 concurrent workers with shared rate limiter.
  - Emit ingestion reports summarizing docs processed, chunks, entities, relationships, and throughput, and page operations staff when backlog exceeds 24 h of capacity.
  - Demonstrate 10-page PDF ingestion <2 minutes and show scaling path from 10 docs/week to ≥10 docs/day via synthetic load test script.
  - _Requirements: R7.2–R7.10, R14.5_

- [ ] 21. Finalize Runbooks, Compliance Evidence & Release Readiness
  - Document operations in `docs/RAG2_runbook.md`, covering queue recovery, OCR manual review, context registry onboarding, checkpoint approvals, and rollback flows.
  - Capture Bolivian privacy compliance evidence (Law 164, Habeas Data retention) in `reports/compliance/{org}/{stage}.md` and link to checkpoint artifacts.
  - Host go/no-go review summarizing performance, cost adherence, and outstanding risks before enabling the FastAPI/agent endpoints for production orgs.
  - _Requirements: Success criteria, R16.3, cost/compliance guardrail_

---

## Dependencies, Guardrails & Approvals

- **Core Services:** Neon PostgreSQL (pgvector), Neo4j Aura/Desktop, Redis (caching/queue), OpenAI (text-embedding-3-small, gpt-4o-mini), and Mistral Pixtral OCR must be provisioned with environment-specific secrets before Phases 2–3 begin.
- **Operational Dependencies:** Existing consolidation components (`intelligence_capture/consolidation_agent.py`, `.kiro/specs/knowledge-graph-consolidation/*`) remain the source for merged entities; all new pipelines consume their events instead of re-implementing business logic.
- **Cost Guardrails:** `CostGuard` enforces the $500–$1,000 USD/month spend band from `docs/business_validation_objectives.md`; overruns trigger ingestion throttling and require Delivery Lead approval before resuming.
- **Compliance Constraints:** Context registry + API stack must enforce per-org isolation, Spanish-language notices, and 12-month checkpoint retention to satisfy Bolivian Habeas Data obligations.
- **Approval Checkpoints:** Promotion of new orgs, OCR low-confidence overrides, retrieval evaluation regressions, and production API enablement all require recorded approvals in `model_reviews` (Tasks 18 & 21) before deployment toggles can be flipped.
