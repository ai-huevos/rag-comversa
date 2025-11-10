# Week 2 Handoff Package: Dual Storage & Embeddings Foundation

**Handoff Date**: November 9, 2025 (after remediation)
**Source Phase**: Phase 1 (Week 1) - Tasks 0-5
**Target Phase**: Phase 2 (Week 2) - Tasks 6-9
**Agent Handoff**: intake_processing + storage_graph → storage_graph + agent_api

---

## Executive Summary

Phase 1 has delivered the **intake and ingestion fabric** for RAG 2.0. Week 2 will build the **dual storage layer** (PostgreSQL+pgvector + Neo4j) and **embedding pipeline**. This handoff package documents prerequisites, ready files, and integration points for Tasks 6-9.

**Status**: ⚠️ **CONDITIONAL HANDOFF** - Remediation required before Week 2 begins

---

## Prerequisites for Week 2 Tasks

### Task 6: PostgreSQL + pgvector Schema

**Dependencies from Phase 1**:
- ✅ Migration runner: `scripts/run_pg_migrations.py`
- ✅ Database config: `config/database.toml`
- ✅ Context Registry schema: Ready for org_id references
- ✅ Ingestion events schema: Ready for document_id FK

**Required Infrastructure**:
- ❌ PostgreSQL instance (Neon recommended)
  - Action: Provision database
  - Set: `DATABASE_URL="postgresql://user:pass@host:5432/dbname"`
  - Size: Start with 1GB storage, 1 CPU

- ❌ pgvector extension enabled
  - Action: Run `CREATE EXTENSION vector;` after provisioning

**Ready Files**:
```
scripts/run_pg_migrations.py          # Migration runner
config/database.toml                  # Connection config
```

**Integration Points**:
- Connect `documents` table to `context_registry(org_id)` FK
- Connect `document_chunks` table to `documents(document_id)` FK
- Connect `embeddings` table to `document_chunks(chunk_id)` FK

**SQL Schema to Create**:
```sql
-- documents table (source documents)
-- document_chunks table (300-500 token chunks)
-- embeddings table (1536-dim vectors from text-embedding-3-small)
```

---

### Task 7: Embedding Pipeline with CostGuard

**Dependencies from Phase 1**:
- ✅ DocumentPayload dataclass: `intelligence_capture/models/document_payload.py`
- ✅ Spanish chunker: `intelligence_capture/chunking/spanish_chunker.py`
  - Produces 300-500 token chunks
  - 50-token overlap
  - Spanish metadata extracted

- ✅ Chunk metadata: `intelligence_capture/chunking/chunk_metadata.py`
  - `token_count`, `span_offsets`, `section_title`
  - `spanish_features` dict ready for optimization

**Required Infrastructure**:
- ⚠️ OpenAI API key configured
  - Action: Verify `OPENAI_API_KEY` environment variable
  - Model: `text-embedding-3-small` (1536 dimensions)
  - Cost: ~$0.00002 per 1K tokens

- ❌ Redis for caching (optional but recommended)
  - Action: Provision Redis or use in-memory fallback
  - TTL: 24 hours for embedding cache

**Ready Files**:
```
intelligence_capture/models/document_payload.py    # Document structure
intelligence_capture/chunking/spanish_chunker.py   # Chunking engine
intelligence_capture/chunking/chunk_metadata.py    # Metadata tracking
```

**Integration Points**:
- Read chunks from `document_chunks` table
- Batch up to 100 chunks per API call
- Cache embeddings in Redis (key: chunk_checksum)
- Write vectors to `embeddings` table with cost tracking

**CostGuard Requirements**:
- Track cost per chunk: `cost_cents = tokens * 0.00002 / 10`
- Monthly projection: Sum costs, throttle >$900, stop >$1,000
- Log to `intelligence_capture/cost_guard.py` (to be created)

---

### Task 8: Document + Chunk Persistence

**Dependencies from Phase 1**:
- ✅ Context Registry: `intelligence_capture/context_registry.py`
  - Provides org_id validation
  - Access logging for compliance

- ✅ Ingestion Queue: `intelligence_capture/queues/ingestion_queue.py`
  - Job management with status tracking
  - Retry logic (max 3 attempts)

- ✅ DocumentProcessor: `intelligence_capture/document_processor.py`
  - 6 adapters ready (PDF, DOCX, Image, CSV, XLSX, WhatsApp)
  - Produces DocumentPayload with metadata

- ⚠️ OCR Coordinator: `intelligence_capture/ocr/ocr_coordinator.py`
  - **BLOCKER**: Async PostgreSQL integration incomplete
  - **Action**: Complete `_enqueue_for_review()` implementation

**Required Infrastructure**:
- ❌ PostgreSQL connection pool configured
  - Action: Configure asyncpg pool (min=2, max=10 connections)
  - Timeouts: connect=30s, query=60s

**Ready Files**:
```
intelligence_capture/context_registry.py          # Org validation
intelligence_capture/queues/ingestion_queue.py    # Job tracking
intelligence_capture/document_processor.py        # Multi-format parsing
intelligence_capture/chunking/spanish_chunker.py  # Chunk generation
```

**Integration Points**:
- Transaction: Insert document → Insert chunks → Insert embeddings (atomic)
- Rollback: Move file to `failed/` directory on transaction failure
- Progress: Update `ingestion_events` stages (parsing → chunking → embedding → completed)

**Error Handling**:
```python
try:
    async with conn.transaction():
        doc_id = await insert_document(...)
        chunk_ids = await insert_chunks(doc_id, ...)
        await insert_embeddings(chunk_ids, ...)
        await queue.ack_job(job_id)
except Exception as e:
    await queue.retry_job(job_id, error=str(e))
    shutil.move(file, failed_dir)
```

---

### Task 9: Neo4j + Graffiti Knowledge Graph Builder

**Dependencies from Phase 1**:
- ✅ Consolidated entities: `intelligence_capture/consolidation_agent.py`
  - 17 entity types already consolidated
  - `consolidated_entities` table in SQLite
  - Relationships tracked in `entity_relationships`

- ✅ Context Registry: Provides org_id for namespace isolation

**Required Infrastructure**:
- ❌ Neo4j instance (Aura recommended)
  - Action: Provision Neo4j Aura or Desktop
  - Set: `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`
  - Min size: 1GB memory

- ❌ Graffiti library
  - Action: `pip install graffiti-ml`
  - Version: >=0.5.0

**Ready Files**:
```
intelligence_capture/consolidation_agent.py    # Consolidated entities
data/full_intelligence.db                      # SQLite with entities
```

**Integration Points**:
- Read consolidated entities from SQLite `consolidated_entities` table
- Create Graffiti episodes (one per document)
- MERGE nodes: `System`, `Process`, `PainPoint`, `KPI`, etc.
- MERGE relationships: `CAUSES`, `USES`, `HAS`, `DEPENDS_ON`
- Add org_id property to all nodes for namespace isolation
- Store `neo4j_node_id` back to SQLite for audit

**Graph Schema**:
```cypher
// Node labels (17 entity types)
CREATE CONSTRAINT org_system_unique IF NOT EXISTS
FOR (s:System) REQUIRE (s.org_id, s.name) IS UNIQUE;

// Relationships with strength
(:PainPoint)-[:CAUSES {strength: 0.8}]->(:Inefficiency)
(:System)-[:USED_IN]->(:Process)
```

---

## Dependency Installation Checklist

### Python Dependencies

```bash
# All requirements from requirements-rag2.txt
pip install -r requirements-rag2.txt

# Verify critical packages
pip list | grep -E "asyncpg|openai|neo4j|pgvector|spacy|nltk"

# Expected output
asyncpg         0.29.0
neo4j           5.14.0
openai          1.3.0
spacy           3.7.2
nltk            3.8.1
```

### spaCy Spanish Model

```bash
# Download Spanish model (required for Task 5 integration)
python -m spacy download es_core_news_md

# Verify installation
python -c "import spacy; nlp = spacy.load('es_core_news_md'); print('✓ Model loaded')"
```

### Tesseract OCR

```bash
# macOS
brew install tesseract tesseract-lang

# Ubuntu
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Verify
tesseract --version
# Expected: Tesseract 5.x
```

### Database Clients

```bash
# PostgreSQL client
brew install postgresql@15  # macOS
# OR
sudo apt-get install postgresql-client-15  # Ubuntu

# Neo4j Desktop (optional, for local development)
# Download from: https://neo4j.com/download/
```

---

## Environment Variables Required

### Week 2 Essential

```bash
# PostgreSQL (Task 6, 7, 8)
export DATABASE_URL="postgresql://user:pass@host.neon.tech:5432/rag2_db?sslmode=require"

# OpenAI Embeddings (Task 7)
export OPENAI_API_KEY="sk-..."

# Mistral OCR (Task 4 completion)
export MISTRAL_API_KEY="..."

# Neo4j (Task 9)
export NEO4J_URI="neo4j+s://xxxx.databases.neo4j.io"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="..."

# Redis (Task 7 caching - optional)
export REDIS_URL="redis://localhost:6379/0"
# OR leave unset to use in-memory cache
```

### Week 2 Optional

```bash
# Cost controls
export MAX_MONTHLY_COST_USD="1000"
export COST_WARNING_THRESHOLD_USD="900"

# Performance tuning
export EMBEDDING_BATCH_SIZE="100"
export POSTGRES_POOL_MIN="2"
export POSTGRES_POOL_MAX="10"

# Logging
export LOG_LEVEL="INFO"
export LOG_FILE="logs/rag2_week2.log"
```

---

## Handoff Notes by Task

### Task 6: PostgreSQL Schema (storage_graph agent)

**From Phase 1**:
- Migration runner ready
- Database config documented
- Indexes planned for org_id, document_id, chunk_id

**To Implement**:
1. Create `documents` table (metadata, content, org_id FK to context_registry)
2. Create `document_chunks` table (chunks, token_count, document_id FK)
3. Create `embeddings` table (vector[1536], chunk_id FK)
4. Create HNSW index on embeddings.vector (m=16, ef_construction=200)
5. Test migration with `run_pg_migrations.py --dry-run`
6. Apply migration and verify indexes created

**Integration Test**:
```python
# Insert test document
doc_id = await insert_document(
    org_id='los_tajibos',
    checksum='abc123',
    content='Test content'
)

# Insert test chunk
chunk_id = await insert_chunk(
    document_id=doc_id,
    content='Test chunk',
    token_count=10
)

# Insert test embedding
await insert_embedding(
    chunk_id=chunk_id,
    vector=[0.1] * 1536
)

# Verify FK constraints work
```

---

### Task 7: Embedding Pipeline (intake_processing agent)

**From Phase 1**:
- Chunker produces 300-500 token windows ✅
- Chunk metadata includes token_count, span_offsets ✅
- Spanish features extracted for optimization ✅

**To Implement**:
1. Create `intelligence_capture/embeddings/pipeline.py`
2. Batch chunks (up to 100 per call)
3. Call OpenAI `text-embedding-3-small` API
4. Cache results in Redis (24h TTL)
5. Write vectors to `embeddings` table
6. Track cost per chunk and monthly projection
7. Implement CostGuard throttling (>$900 USD)

**Integration Test**:
```python
# Process 10-page PDF
chunks = chunker.chunk_document(payload)
# Expected: ~40-60 chunks

# Generate embeddings
embeddings = await pipeline.embed_chunks(chunks)
# Expected: 40-60 vectors of dim 1536

# Verify cost tracking
cost = pipeline.get_total_cost()
# Expected: ~$0.01 for 10-page PDF
```

---

### Task 8: Document Persistence (storage_graph agent)

**From Phase 1**:
- Context Registry provides org validation ✅
- Ingestion queue tracks job status ✅
- DocumentProcessor produces normalized payloads ✅
- ⚠️ **BLOCKER**: OCR integration incomplete

**To Implement**:
1. Create `intelligence_capture/persistence/document_repository.py`
2. Implement atomic transaction: document → chunks → embeddings
3. Update `ingestion_events` stages (8 stages total)
4. Handle rollback on failure (move to failed/)
5. Resume support (check existing documents by checksum)

**Integration Test**:
```python
# End-to-end test
job = await queue.dequeue()
payload = processor.process(job.storage_path)
chunks = chunker.chunk_document(payload)
embeddings = await pipeline.embed_chunks(chunks)

async with conn.transaction():
    doc_id = await repo.insert_document(payload)
    chunk_ids = await repo.insert_chunks(doc_id, chunks)
    await repo.insert_embeddings(chunk_ids, embeddings)
    await queue.complete_job(job.id)

# Verify atomic commit
assert await repo.document_exists(doc_id)
assert len(await repo.get_chunks(doc_id)) == len(chunks)
```

---

### Task 9: Neo4j Graph Builder (storage_graph agent)

**From Phase 1**:
- Consolidated entities ready in SQLite ✅
- Entity relationships tracked ✅
- Org namespace isolation via org_id ✅

**To Implement**:
1. Create `graph/knowledge_graph_builder.py`
2. Read consolidated entities from SQLite
3. Create Graffiti episodes (one per document)
4. MERGE nodes with org_id namespaces
5. MERGE relationships with strength weights
6. Write `neo4j_node_id` back to SQLite
7. Bootstrap indexes and constraints

**Integration Test**:
```cypher
// Verify graph structure
MATCH (s:System {org_id: 'los_tajibos'})
RETURN count(s);
// Expected: >0 systems

// Verify relationships
MATCH (p:PainPoint)-[r:CAUSES]->(i:Inefficiency)
WHERE p.org_id = 'los_tajibos'
RETURN count(r);
// Expected: >0 relationships

// Verify namespace isolation
MATCH (n {org_id: 'comversa'})
RETURN count(n);
// Expected: 0 (different org)
```

---

## Handoff Artifacts

### Ready for Week 2

**Code Modules**:
```
intelligence_capture/
├── context_registry.py             # ✅ Org validation
├── models/document_payload.py      # ✅ Document structure
├── chunking/spanish_chunker.py     # ✅ Chunking engine
├── queues/ingestion_queue.py       # ✅ Job tracking
├── document_processor.py           # ✅ Multi-format parsing
├── connectors/                     # ✅ 4 source connectors
├── parsers/                        # ✅ 6 document adapters
└── ocr/                            # ⚠️ Partial (PostgreSQL integration)
```

**Database Schemas**:
```
scripts/migrations/
├── 2025_01_00_context_registry.sql     # ✅ Applied
├── 2025_01_01_ingestion_queue.sql      # ✅ Applied
└── 2025_01_02_ocr_review_queue.sql     # ✅ Applied
```

**Configuration**:
```
config/
├── database.toml                   # ✅ Connection config
└── context_registry.yaml           # ✅ Org settings
```

### To Be Created in Week 2

**New Modules**:
```
intelligence_capture/
├── embeddings/
│   └── pipeline.py                 # Task 7
├── persistence/
│   └── document_repository.py      # Task 8
└── cost_guard.py                   # Task 7

graph/
└── knowledge_graph_builder.py      # Task 9

scripts/
└── migrations/
    └── 2025_01_03_documents_embeddings.sql  # Task 6
```

---

## Integration Validation Checklist

### Pre-Week 2 Validation

- [ ] All dependencies installed (`pip list` shows 67 packages)
- [ ] spaCy Spanish model downloaded and loadable
- [ ] PostgreSQL instance provisioned and accessible
- [ ] DATABASE_URL environment variable set
- [ ] OpenAI API key configured and working
- [ ] Neo4j instance provisioned (or Desktop running)
- [ ] Phase 1 tests passing (>80% coverage)
- [ ] Task 4 OCR PostgreSQL integration complete
- [ ] UTF-8 encoding issues fixed (3 locations)

### Week 2 Milestone Validation

**After Task 6**:
- [ ] 3 new PostgreSQL tables created
- [ ] pgvector extension enabled
- [ ] HNSW index on embeddings.vector working
- [ ] Migration applied successfully

**After Task 7**:
- [ ] Embedding pipeline generates 1536-dim vectors
- [ ] Cost tracking logs to CostGuard
- [ ] Redis cache working (or in-memory fallback)
- [ ] Batch processing (100 chunks) works

**After Task 8**:
- [ ] Document + chunks + embeddings inserted atomically
- [ ] Rollback on failure works correctly
- [ ] Ingestion queue updates all 8 stages
- [ ] 10-page PDF processes in <2 minutes

**After Task 9**:
- [ ] Neo4j nodes created with org_id namespaces
- [ ] Relationships have strength weights
- [ ] Graffiti episodes working
- [ ] Cross-org isolation verified

---

## Critical Success Factors

### Week 2 Must-Haves

1. **Atomic Transactions**: Document + chunks + embeddings must commit together
2. **Cost Controls**: CostGuard must throttle at $900, stop at $1,000
3. **Performance**: 10-page PDF must process in <2 minutes
4. **Namespace Isolation**: No cross-org data leakage (verify with tests)
5. **Error Recovery**: Failed documents must rollback cleanly

### Week 2 Should-Haves

1. Embedding cache reduces duplicate API calls
2. Neo4j indexes speed up graph queries
3. Integration tests cover happy path + error cases
4. Documentation updated with connection diagrams
5. Runbook drafted for operations team

---

## Risks & Mitigation

| Risk | Mitigation |
|------|------------|
| PostgreSQL not provisioned in time | Use local PostgreSQL for development, Neon for production |
| OpenAI rate limits hit | Implement exponential backoff, batch smaller chunks |
| Neo4j provisioning delayed | Use Neo4j Desktop for Week 2, migrate to Aura later |
| Task 4 OCR blocker | Complete async integration in parallel with Task 6 |
| Cost overruns in testing | Use small test documents, implement CostGuard early |

---

## Contact & Support

**Phase 1 Agents (for questions)**:
- Context Registry (Task 0): storage_graph agent
- Connectors/Queue (Tasks 1-2): intake_processing agent
- DocumentProcessor (Task 3): intake_processing agent
- OCR Engine (Task 4): intake_processing agent
- Spanish Chunking (Task 5): intake_processing agent

**Phase 2 Agents (Week 2)**:
- PostgreSQL Schema (Task 6): storage_graph agent
- Embedding Pipeline (Task 7): intake_processing agent
- Document Persistence (Task 8): storage_graph agent
- Neo4j Graph (Task 9): storage_graph agent

---

## Approval

**Handoff Approved By**: quality_governance agent
**Date**: November 9, 2025 (pending remediation)
**Next Checkpoint**: After Task 9 completion (end of Week 2)

**Status**: ⚠️ **CONDITIONAL HANDOFF** - Complete remediation before beginning Week 2

---

**END OF HANDOFF PACKAGE**
