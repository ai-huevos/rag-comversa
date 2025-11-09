# RAG 2.0 Implementation Guide

**Status**: 🟡 Week 1/5 In Progress
**Last Updated**: November 9, 2025
**Target**: Conversational intelligence queries over 44 Spanish interviews + multi-format documents

---

## Business Value Proposition

Enable conversational queries that combine semantic search + graph relationships + consolidated intelligence:

**Example Queries**:
- "¿Qué sistemas causan más puntos de dolor en Los Tajibos?" → Graph: System→CAUSES→PainPoint
- "Busca referencias a 'automatización' en entrevistas" → Vector: Semantic similarity search
- "¿Qué dice el contrato Q4 sobre presupuesto?" → Vector: PDF chunk search with citations
- "Dame oportunidades de automatización con mayor consenso" → Hybrid: Vector + Graph + Consolidation scores

**Key Capabilities**:
1. **Multi-format Intelligence**: Process PDFs, images, CSV, WhatsApp exports, JSON interviews
2. **Dual Storage**: pgvector (semantic) + Neo4j (relationships) + SQLite (audit)
3. **Conversational Interface**: Pydantic AI agent with Spanish system prompt
4. **Governance Integration**: Checkpoints, privacy compliance, cost tracking

---

## 5-Week Implementation Timeline

### Week 1: Intake & OCR (Tasks 0-5)
**Goal**: Multi-format document ingestion with org-level isolation

#### Key Components
1. **Context Registry** (`intelligence_capture/context_registry.py`):
   - Multi-org namespace management (Los Tajibos, Comversa, Bolivian Foods)
   - Consent metadata tracking for privacy compliance (Bolivian Law 164)
   - Org-level isolation enforcement

2. **Source Connectors** (`intelligence_capture/connectors/`):
   - WhatsApp export parser (JSON → structured messages)
   - CSV reader with encoding detection (UTF-8, Latin-1)
   - PDF ingestion (link to DocumentProcessor)
   - Image ingestion (link to OCR pipeline)

3. **Ingestion Queue** (`intelligence_capture/ingestion_queue.py`):
   - Redis Stream OR SQLite jobs table
   - Priority: manual_review > normal > batch
   - Status tracking: pending → processing → completed → failed

4. **DocumentProcessor** (`intelligence_capture/document_processor.py`):
   - PDF: PyPDF2 + pdfplumber (fallback for complex layouts)
   - DOCX: python-docx
   - Images: Route to OCR pipeline
   - CSV/Excel: pandas with Spanish encoding

5. **OCR Pipeline** (`intelligence_capture/ocr/`):
   - Primary: Mistral Pixtral (Spanish-optimized LLM)
   - Fallback: Tesseract with spa trained data
   - Manual review queue for low confidence (<0.7)

6. **Spanish Chunking** (`intelligence_capture/chunking/spanish_chunker.py`):
   - Target: 300-500 tokens per chunk
   - Strategy: Sentence boundaries with semantic coherence
   - Accent-aware splitting (don't break on á, é, í, ó, ú, ñ)
   - Overlap: 50 tokens for context continuity

**Acceptance Criteria**:
- ✅ Context Registry stores 3 orgs with consent flags
- ✅ WhatsApp connector parses 10-message export
- ✅ OCR processes scanned Spanish document with >90% accuracy
- ✅ Chunking produces 300-500 token chunks with <10% variance

**Detailed Specs**: [.kiro/specs/rag-2.0-enhancement/tasks.md](.../.kiro/specs/rag-2.0-enhancement/tasks.md) (Tasks 0-5)

---

### Week 2: Dual Storage (Tasks 6-9)
**Goal**: Set up PostgreSQL+pgvector and Neo4j for semantic + graph queries

#### PostgreSQL + pgvector Schema
```sql
-- Document chunks with embeddings
CREATE TABLE document_chunks (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(50) NOT NULL,
    document_id VARCHAR(100) NOT NULL,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536), -- OpenAI text-embedding-3-small
    metadata JSONB, -- {source, page_num, confidence}
    created_at TIMESTAMP DEFAULT NOW()
);

-- HNSW index for <1s similarity search
CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);

-- B-tree indexes for filtering
CREATE INDEX ON document_chunks(org_id);
CREATE INDEX ON document_chunks(document_id);
```

#### Embedding Pipeline (`intelligence_capture/embeddings/pipeline.py`)
```python
def generate_embeddings_batch(chunks: List[str], batch_size=100):
    """
    Generate embeddings with cost tracking

    Cost: ~$0.10 per 1M tokens (text-embedding-3-small)
    Rate limit: 3,000 RPM, 1M TPM
    """
    # Batch chunks into groups of 100
    # Call OpenAI API with exponential backoff
    # Store in PostgreSQL with document_id
    # Update CostGuard metrics
    pass
```

#### Neo4j + Graffiti Setup
**Schema** (from consolidation → graph):
```cypher
// Nodes
(:System {name, org_id, source_count, consensus_confidence})
(:PainPoint {description, severity, org_id, source_count})
(:Process {name, department, org_id})
(:AutomationCandidate {description, effort_score, impact_score})

// Relationships
(System)-[:CAUSES {confidence: float}]->(PainPoint)
(Process)-[:USES {frequency: str}]->(System)
(AutomationCandidate)-[:ADDRESSES {impact: float}]->(PainPoint)
(KPI)-[:MEASURES]->(Process)
```

**Graph Builder** (`graph/knowledge_graph_builder.py`):
- Sync from `consolidated_entities` table (SQLite)
- Map 17 entity types to Neo4j node labels
- Create relationships from `entity_relationships` table
- Incremental sync (upsert on entity_id)

**Acceptance Criteria**:
- ✅ PostgreSQL stores 1,000 chunks with embeddings
- ✅ Vector search returns top-5 results in <1s
- ✅ Neo4j contains consolidated entities from Phase 12
- ✅ Graph query finds System→PainPoint relationships

**Detailed Specs**: [.kiro/specs/rag-2.0-enhancement/tasks.md](.../.kiro/specs/rag-2.0-enhancement/tasks.md) (Tasks 6-9)

---

### Week 3: Agentic RAG & API (Tasks 10-14)
**Goal**: Pydantic AI agent with conversational interface via FastAPI

#### Pydantic AI Agent Setup (`agent/rag_agent.py`)
```python
from pydantic_ai import Agent, RunContext
from pydantic_ai.models import OpenAIModel

# Spanish system prompt
system_prompt = """
Eres el Director de Inteligencia de Comversa.
Respondes preguntas sobre las 44 entrevistas en ESPAÑOL.

Herramientas disponibles:
- vector_search: Busca en documentos por similitud semántica
- graph_search: Consulta relaciones entre entidades (Sistema→PuntosDolor)
- hybrid_search: Combina vector + grafo
- checkpoint_lookup: Recupera artefactos de gobernanza

Formato de respuesta:
**Respuesta**: [2-3 frases en español]
**Fuentes**: [doc_id, interview_id, checkpoint_id]
**Recomendaciones**: [1-3 puntos accionables]
"""

agent = Agent(
    model=OpenAIModel('gpt-4o-mini'),
    system_prompt=system_prompt,
    deps_type=AgentDeps, # Includes pg_conn, neo4j_conn, context_registry
)

@agent.tool
async def vector_search(ctx: RunContext[AgentDeps], query: str, org_id: str, top_k: int = 5):
    """Search document chunks by semantic similarity"""
    # Generate query embedding
    # Query pgvector with org_id filter
    # Return top_k chunks with metadata
    pass

@agent.tool
async def graph_search(ctx: RunContext[AgentDeps], org_id: str, relationship_types: List[str]):
    """Query Neo4j for entity relationships"""
    # Build Cypher query
    # Execute on Neo4j with org filter
    # Return nodes + relationships
    pass
```

#### FastAPI Endpoints (`api/server.py`)
```python
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

app = FastAPI()

class ChatRequest(BaseModel):
    query: str
    org_id: str
    session_id: Optional[str] = None

@app.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint"""
    # Validate org_id via Context Registry
    # Run Pydantic AI agent
    # Return response with sources
    pass

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """SSE streaming endpoint"""
    # Stream tool calls + chunks as they arrive
    # Format: data: {"type": "tool_call|chunk|done", "content": ...}
    pass

@app.get("/health")
async def health():
    """Health check with dependency status"""
    return {
        "status": "healthy",
        "postgres": check_postgres(),
        "neo4j": check_neo4j(),
        "openai": check_openai_quota()
    }
```

**Acceptance Criteria**:
- ✅ Agent routes vector vs graph vs hybrid based on query
- ✅ Spanish responses with proper accents (á, é, í, ó, ú, ñ)
- ✅ /chat endpoint returns response in <3s
- ✅ /chat/stream streams tool reasoning in real-time
- ✅ Session memory persists across multi-turn conversations

**Detailed Specs**: [.kiro/specs/rag-2.0-enhancement/tasks.md](.../.kiro/specs/rag-2.0-enhancement/tasks.md) (Tasks 10-14)

---

### Week 4: Quality & Governance (Tasks 15-18)
**Goal**: Evaluation harness + Spanish optimization + cost controls

#### Spanish Evaluation Dataset
**50 Questions Across Categories**:
1. **Factual** (20): "¿Cuántas veces se menciona Excel?"
2. **Relational** (15): "¿Qué sistemas causan más puntos de dolor?"
3. **Semantic** (10): "Busca referencias a procesos manuales"
4. **Multi-hop** (5): "¿Qué oportunidades de automatización abordan los mayores puntos de dolor?"

**Golden Answers**: Human-annotated with:
- Expected answer text
- Relevant source IDs (document_id, interview_id)
- Acceptable variations (synonyms, paraphrasing)

#### Retrieval Evaluation (`scripts/evaluate_retrieval.py`)
```python
def evaluate_retrieval(questions, golden_answers):
    """
    Metrics:
    - Precision@5: % of top-5 results that are relevant
    - Recall@5: % of relevant docs in top-5
    - MRR (Mean Reciprocal Rank): 1/rank_of_first_relevant
    - Response Time: p50, p95, p99
    """
    # Target: Precision@5 ≥0.80, MRR ≥0.75, p95 <3s
    pass
```

#### CostGuard Integration
- Track embeddings generation cost (per chunk)
- Track LLM calls (per query)
- Alert at $900/month (90% of budget)
- Block at $1,000/month (hard limit)

**Acceptance Criteria**:
- ✅ Evaluation harness runs 50 questions in <10 min
- ✅ Precision@5 ≥0.80 on factual queries
- ✅ MRR ≥0.75 on all query types
- ✅ CostGuard alerts trigger at 90% budget

**Detailed Specs**: [.kiro/specs/rag-2.0-enhancement/tasks.md](.../.kiro/specs/rag-2.0-enhancement/tasks.md) (Tasks 15-18)

---

### Week 5: Consolidation & Automation (Tasks 19-21)
**Goal**: Sync consolidation system to Postgres/Neo4j, automate ingestion

#### ConsolidationSync Architecture
```
SQLite (consolidation_agent output)
    ↓
ConsolidationSync
├─→ PostgreSQL: Update consensus scores on chunks
└─→ Neo4j: Upsert consolidated entities + relationships
```

**Sync Strategy**:
- Incremental: Process entities updated since last sync
- Conflict resolution: PostgreSQL/Neo4j wins on manual edits
- Audit trail: Log all syncs to `consolidation_sync_log` table

#### Ingestion Worker (`intelligence_capture/ingestion_worker.py`)
```python
async def process_ingestion_queue(concurrency=4):
    """
    Poll queue for new documents
    - Extract text (DocumentProcessor/OCR)
    - Chunk text (Spanish chunker)
    - Generate embeddings (batch)
    - Store in PostgreSQL
    - Trigger consolidation if entity-like
    """
    pass
```

**Acceptance Criteria**:
- ✅ ConsolidationSync syncs 295 entities to Neo4j
- ✅ Ingestion worker processes 10 PDFs in <5 min
- ✅ Backlog alert fires when queue >100 items
- ✅ RAG2 operational runbook complete

**Detailed Specs**: [.kiro/specs/rag-2.0-enhancement/tasks.md](.../.kiro/specs/rag-2.0-enhancement/tasks.md) (Tasks 19-21)

---

## Key Design Decisions

### 1. Why Dual Storage? (ADR-010)
**PostgreSQL + pgvector**:
- ✅ Semantic search on document chunks (300-500 tokens)
- ✅ HNSW index for <1s retrieval at 100K+ chunks
- ✅ JSON metadata for flexible filtering

**Neo4j + Graffiti**:
- ✅ Graph traversal for "System CAUSES PainPoint" queries
- ✅ Relationship discovery (4 types from consolidation)
- ✅ Pattern queries (3+ hop traversals)

**SQLite (retained)**:
- ✅ Extraction history and consolidation audit trail
- ✅ Rollback capability (entity snapshots)
- ✅ Governance checkpoints

### 2. Why Pydantic AI?
- Type safety with Pydantic models
- Tool routing with intelligent fallback
- Spanish system prompt support
- Streaming responses (SSE)
- Session memory management

### 3. Why Consolidation Before RAG?
- 80-95% duplicate reduction reduces storage costs
- Consensus confidence improves retrieval quality
- Relationship discovery enables graph queries
- Pattern recognition identifies high-value entities

---

## Testing Strategy

### Unit Tests
```bash
# Week 1: Intake components
pytest tests/test_context_registry.py -v
pytest tests/test_document_processor.py -v
pytest tests/test_spanish_chunker.py -v

# Week 2: Storage layer
pytest tests/test_embeddings_pipeline.py -v
pytest tests/test_graph_builder.py -v

# Week 3: Agent & API
pytest tests/test_agent_tools.py -v
pytest tests/test_api_endpoints.py -v
```

### Integration Tests
```bash
# End-to-end: Ingest PDF → Chunk → Embed → Query
pytest tests/test_e2e_pdf_ingestion.py -v

# Agent flow: Query → Tool selection → Response
pytest tests/test_agent_flow.py -v

# Multi-org: Verify namespace isolation
pytest tests/test_multi_org_isolation.py -v
```

### Evaluation
```bash
# Retrieval quality (50 questions)
python scripts/evaluate_retrieval.py

# Expected output:
# Precision@5: 0.82 (target: ≥0.80) ✅
# MRR: 0.78 (target: ≥0.75) ✅
# Response time p95: 2.1s (target: <3s) ✅
```

---

## Development Best Practices

### Spanish-First (Critical)
```python
# ✅ CORRECT
json.dumps(obj, ensure_ascii=False)  # Preserves á, é, í, ó, ú, ñ
with open(file, 'r', encoding='utf-8') as f:
    content = f.read()

# ❌ WRONG
json.dumps(obj)  # Escapes to \u00e1
with open(file, 'r') as f:  # May use wrong encoding
```

### Type Hints (Required)
```python
# ✅ CORRECT
def chunk_text(text: str, target_length: int = 400) -> List[str]:
    """Chunk Spanish text into semantic units"""
    pass

# ❌ WRONG
def chunk_text(text, target_length=400):  # No types
```

### Cost Tracking (Always)
```python
# Before expensive operation
cost_estimate = estimate_embedding_cost(num_chunks=1000)
logger.info(f"Estimated cost: ${cost_estimate:.2f}")

# After operation
CostGuard.record_cost(operation='embeddings', cost=actual_cost)
```

---

## References

- **Detailed Requirements**: [.kiro/specs/rag-2.0-enhancement/requirements.md](../.kiro/specs/rag-2.0-enhancement/requirements.md)
- **Design Spec**: [.kiro/specs/rag-2.0-enhancement/design.md](../.kiro/specs/rag-2.0-enhancement/design.md)
- **Task Breakdown**: [.kiro/specs/rag-2.0-enhancement/tasks.md](../.kiro/specs/rag-2.0-enhancement/tasks.md)
- **Consolidation System**: [CONSOLIDATION_RUNBOOK.md](CONSOLIDATION_RUNBOOK.md)
- **Agent Architecture**: [AGENT_ARCHITECTURE.md](AGENT_ARCHITECTURE.md) (Week 3)
- **API Contract**: [API_CONTRACT.md](API_CONTRACT.md) (Week 3)
- **Coding Standards**: [.ai/CODING_STANDARDS.md](../.ai/CODING_STANDARDS.md)

---

**Last Updated**: November 9, 2025
**Status**: 🟡 Week 1/5
**Next Milestone**: Context Registry + DocumentProcessor + OCR pipeline
