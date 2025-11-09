# Requirements Document: RAG 2.0 Enhancement - Document Ingestion & Agentic Retrieval

## Executive Summary

This document defines requirements for enhancing the Comversa Intelligence Extraction System from a JSON-based extraction pipeline to a comprehensive RAG 2.0 system supporting multi-format document ingestion (PDFs, images, scanned documents), OCR processing, and agentic retrieval combining vector databases with knowledge graphs.

### Current System vs Target System

**Current State:**
- ✅ Processes 44 JSON interview transcripts
- ✅ Extracts 17 entity types with LLM
- ✅ Stores in SQLite with 20-30% duplicates
- ❌ Cannot process PDFs, images, or scanned documents
- ❌ No OCR capability for handwritten/printed documents
- ❌ No vector database for semantic search
- ❌ No knowledge graph for relational queries
- ❌ No agentic RAG for intelligent retrieval

**Target State (RAG 2.0):**
- ✅ Multi-format ingestion (PDF, DOCX, images, scans)
- ✅ Mistral OCR for Spanish document recognition
- ✅ PostgreSQL + pgvector for vector embeddings
- ✅ Neo4j knowledge graph for entity relationships
- ✅ Agentic RAG with tool selection (vector vs graph)
- ✅ Pydantic AI agent framework for intelligent retrieval
- ✅ Consolidated entities with consensus tracking
- ✅ Can answer: "¿Qué sistemas causan más puntos de dolor?" (What systems cause the most pain?)

## Architecture Overview

```
Document Sources → Document Processor → Chunking → Dual Storage → Agentic Retrieval → AI Agents
                       ↓                    ↓           ↓              ↓
                   OCR/Parser          Embeddings   Vector DB    Tool Selection
                   (Mistral)          (text-embed)  (pgvector)   (Pydantic AI)
                                                    Knowledge Graph
                                                      (Neo4j)
```

### Technology Stack (Based on RAG 2.0 Video)

- **Agent Framework**: Pydantic AI (agentic RAG orchestration)
- **Vector Database**: PostgreSQL + pgvector extension (Neon platform)
- **Knowledge Graph**: Neo4j + Graffiti (Python library)
- **OCR Engine**: Mistral Pixtral (multilingual OCR with Spanish support)
- **Embedding Model**: OpenAI text-embedding-3-small (1536 dimensions)
- **LLM**: OpenAI gpt-4o-mini (primary), gpt-4o (fallback)
- **API Framework**: FastAPI (agent API endpoint)
- **Document Processing**: PyPDF2, python-docx, Pillow, pytesseract

## Requirements

### R1: Multi-Format Document Ingestion Pipeline

**User Story**: As a Knowledge Manager, I want to upload PDFs, Word documents, images, and scanned documents, so that all company knowledge is accessible to AI agents regardless of format.

#### Acceptance Criteria

1. **R1.1** WHEN a user uploads a PDF document, THE System SHALL extract text using PyPDF2 and preserve document metadata (title, author, creation date, page count)

2. **R1.2** WHEN a user uploads a DOCX file, THE System SHALL extract formatted text while preserving section headings, lists, and tables

3. **R1.3** WHEN a user uploads an image (PNG, JPG, TIFF), THE System SHALL detect if it contains text and route to OCR pipeline

4. **R1.4** THE System SHALL support batch upload of up to 100 documents per operation with progress tracking

5. **R1.5** THE System SHALL detect document language (Spanish/English) and apply appropriate text processing

6. **R1.6** THE System SHALL store original documents in `data/documents/originals/` with unique IDs and metadata in `documents` table

7. **R1.7** THE System SHALL handle documents up to 50MB with appropriate error messages for oversized files

### R2: Mistral OCR Integration for Spanish Documents

**User Story**: As a Document Processor, I want scanned Spanish documents automatically converted to text, so that handwritten forms and printed reports are searchable.

#### Acceptance Criteria

1. **R2.1** WHEN a document image is detected, THE System SHALL use Mistral Pixtral API for OCR with Spanish language parameter

2. **R2.2** THE System SHALL detect handwritten vs printed text and apply appropriate OCR confidence thresholds (handwritten: 0.70, printed: 0.90)

3. **R2.3** WHEN OCR confidence is below threshold, THE System SHALL flag the document for manual review in `ocr_review_queue` table

4. **R2.4** THE System SHALL preserve OCR metadata including confidence scores, bounding boxes, and detected text regions

5. **R2.5** THE System SHALL handle common Spanish document types: forms, invoices, reports, handwritten notes

6. **R2.6** THE System SHALL process OCR in parallel using rate-limited API calls (max 5 concurrent requests)

7. **R2.7** WHEN OCR completes, THE System SHALL store extracted text with Spanish encoding (UTF-8) validation

### R3: Intelligent Document Chunking Strategy

**User Story**: As an AI Engineer, I want documents intelligently chunked for optimal retrieval, so that vector search returns coherent, relevant passages.

#### Acceptance Criteria

1. **R3.1** WHEN chunking Spanish text, THE System SHALL use semantic chunking with paragraph boundaries as preferred split points

2. **R3.2** THE System SHALL create chunks of 300-500 tokens with 50-token overlap to preserve context

3. **R3.3** WHEN a document has clear section headings, THE System SHALL respect section boundaries and include headings in chunk metadata

4. **R3.4** THE System SHALL create chunk metadata including: document_id, page_number, section_title, chunk_index, token_count

5. **R3.5** THE System SHALL handle Spanish-specific considerations: preserve whole sentences, don't split mid-word with accents

6. **R3.6** WHEN tables are detected, THE System SHALL create separate chunks preserving table structure with markdown formatting

7. **R3.7** THE System SHALL store chunks in `document_chunks` table with embeddings in pgvector column

### R4: PostgreSQL + pgvector Vector Database Setup

**User Story**: As a System Architect, I want PostgreSQL with pgvector for scalable vector storage, so that semantic search performs efficiently at scale.

#### Acceptance Criteria

1. **R4.1** THE System SHALL use Neon PostgreSQL platform with pgvector extension enabled

2. **R4.2** THE System SHALL create vector embeddings using OpenAI text-embedding-3-small model (1536 dimensions)

3. **R4.3** THE System SHALL store embeddings in `document_chunks` table with column type `vector(1536)`

4. **R4.4** THE System SHALL create HNSW index on embedding column for fast similarity search: `CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops)`

5. **R4.5** THE System SHALL support vector similarity search using cosine distance with configurable top-k results (default: 5)

6. **R4.6** THE System SHALL batch embed chunks in groups of 100 to optimize API usage and processing time

7. **R4.7** THE System SHALL store embedding metadata: model version, dimensions, creation timestamp for version tracking

### R5: Neo4j Knowledge Graph Construction

**User Story**: As a Business Analyst, I want entity relationships stored in a knowledge graph, so that I can query how systems, processes, and pain points interconnect.

#### Acceptance Criteria

1. **R5.1** THE System SHALL use Neo4j database with Graffiti Python library for graph construction

2. **R5.2** WHEN entities are extracted, THE System SHALL create nodes with properties: id, name, type, description, source_count, consensus_confidence

3. **R5.3** THE System SHALL create relationship edges when entities co-occur in same document chunk:
   - System → CAUSES → PainPoint
   - Process → USES → System
   - Department → HAS → Process

4. **R5.4** THE System SHALL weight relationships by co-occurrence frequency (mentioned together in N chunks → relationship strength = min(N/10, 1.0))

5. **R5.5** THE System SHALL use Graffiti's episode-based ingestion: one episode per document for efficient graph construction

6. **R5.6** THE System SHALL create graph indexes on node labels and relationship types for fast query performance

7. **R5.7** THE System SHALL support Cypher queries for relationship traversal (e.g., "Find all Systems causing Pain Points in Los Tajibos")

### R6: Agentic RAG with Pydantic AI Framework

**User Story**: As an AI Agent Developer, I want agents to intelligently choose between vector search and graph queries, so that retrieval strategy matches question type.

#### Acceptance Criteria

1. **R6.1** THE System SHALL use Pydantic AI framework for agent orchestration with tool calling capabilities

2. **R6.2** THE System SHALL provide TWO retrieval tools to the agent:
   - `vector_search(query: str, top_k: int = 5)` → returns similar document chunks
   - `graph_search(query: str, relationship_types: List[str])` → returns entity relationships

3. **R6.3** THE System SHALL configure agent system prompt to specify WHEN to use each tool:
   - Vector search: "When user asks about specific company information or details"
   - Graph search: "When user asks about relationships between entities or cross-company comparisons"
   - Both: "When comprehensive analysis requires both factual details and relational context"

4. **R6.4** THE System SHALL track tool usage for each query and log decisions for analysis

5. **R6.5** THE System SHALL implement streaming responses for real-time agent output with tool call visibility

6. **R6.6** THE System SHALL handle Spanish queries natively without translation (agent operates in Spanish)

7. **R6.7** THE System SHALL support multi-turn conversations with context retention across queries

### R7: Document Ingestion Workflow Automation

**User Story**: As a System Operator, I want automated document processing workflows, so that new documents are ingested without manual intervention.

#### Acceptance Criteria

1. **R7.1** THE System SHALL watch `data/documents/inbox/` directory for new files (PDF, DOCX, images)

2. **R7.2** WHEN a new file appears, THE System SHALL:
   - Move to `data/documents/processing/`
   - Extract text (with OCR if needed)
   - Chunk and embed text
   - Extract entities with LLM
   - Consolidate duplicates
   - Build knowledge graph
   - Move to `data/documents/processed/`

3. **R7.3** THE System SHALL process documents in parallel (max 4 concurrent) with shared rate limiter

4. **R7.4** WHEN processing fails, THE System SHALL move file to `data/documents/failed/` with error log

5. **R7.5** THE System SHALL update `ingestion_progress.json` with status for resume capability

6. **R7.6** THE System SHALL generate ingestion reports showing: documents processed, chunks created, entities extracted, relationships discovered

7. **R7.7** THE System SHALL complete full ingestion pipeline for a 10-page PDF in under 2 minutes

### R8: Hybrid Search Combining Vector + Graph

**User Story**: As a Data Scientist, I want hybrid search combining vector similarity and graph relationships, so that retrieval quality exceeds either method alone.

#### Acceptance Criteria

1. **R8.1** THE System SHALL implement hybrid search that executes both vector and graph queries in parallel

2. **R8.2** THE System SHALL merge results using reciprocal rank fusion: `score = 1/(rank_vector + rank_graph + 60)`

3. **R8.3** THE System SHALL deduplicate results preferring graph results when an entity appears in both

4. **R8.4** THE System SHALL expose hybrid search as agent tool: `hybrid_search(query: str, top_k: int = 5)`

5. **R8.5** THE System SHALL measure hybrid search effectiveness vs individual methods using Mean Reciprocal Rank (MRR)

6. **R8.6** THE System SHALL allow agent to override hybrid weighting (e.g., 70% vector, 30% graph) based on query type

7. **R8.7** THE System SHALL cache hybrid search results for 5 minutes to improve repeated query performance

### R9: FastAPI Agent Endpoint for Production Deployment

**User Story**: As a Backend Engineer, I want a RESTful API for agent interactions, so that multiple clients can access the RAG system.

#### Acceptance Criteria

1. **R9.1** THE System SHALL expose FastAPI endpoint at `/chat` accepting: `{ "query": str, "session_id": str, "stream": bool }`

2. **R9.2** THE System SHALL expose `/chat/stream` endpoint for server-sent events (SSE) streaming responses

3. **R9.3** THE System SHALL maintain session history in `chat_sessions` table for multi-turn conversations

4. **R9.4** THE System SHALL implement rate limiting: 60 requests/minute per client IP

5. **R9.5** THE System SHALL return responses in format: `{ "answer": str, "sources": [{"type": "vector"|"graph", "content": str, "score": float}], "tool_calls": [] }`

6. **R9.6** THE System SHALL expose `/health` endpoint checking: database connection, Neo4j connection, LLM API availability

7. **R9.7** THE System SHALL implement authentication with API keys stored in environment variables

### R10: Command Line Interface for Interactive Testing

**User Story**: As a Developer, I want a CLI for testing the agent, so that I can quickly validate retrieval quality during development.

#### Acceptance Criteria

1. **R10.1** THE System SHALL provide CLI command: `python -m agent.cli` that connects to agent API

2. **R10.2** THE System SHALL display tool calls in real-time as agent reasons about retrieval strategy

3. **R10.3** THE System SHALL show source attribution for each answer with similarity scores

4. **R10.4** THE System SHALL support CLI flags: `--verbose` (show full tool outputs), `--log-file` (save conversation)

5. **R10.5** THE System SHALL colorize output: user queries (blue), agent responses (green), tool calls (yellow)

6. **R10.6** THE System SHALL support commands: `/reset` (clear session), `/sources` (show last sources), `/stats` (show usage)

7. **R10.7** THE System SHALL save conversation history to `data/cli_sessions/` for later review

### R11: Entity Extraction from Unstructured Documents

**User Story**: As a Knowledge Engineer, I want entities automatically extracted from uploaded documents, so that knowledge graph grows with each new document.

#### Acceptance Criteria

1. **R11.1** WHEN a document chunk is created, THE System SHALL extract entities using existing IntelligenceExtractor with all 17 entity types

2. **R11.2** THE System SHALL use document metadata (company, department) to enrich entity extraction context

3. **R11.3** THE System SHALL link extracted entities to source document chunks via `entity_chunks` table

4. **R11.4** THE System SHALL run consolidation immediately after extraction to merge with existing entities

5. **R11.5** THE System SHALL discover relationships by analyzing co-occurring entities within same chunk (window size: 500 tokens)

6. **R11.6** THE System SHALL handle extraction failures gracefully, continuing with remaining chunks

7. **R11.7** THE System SHALL track extraction metrics: entities per chunk, extraction time, confidence scores

### R12: Consolidation Integration with Knowledge Graph

**User Story**: As a Data Architect, I want consolidated entities synchronized to knowledge graph, so that graph queries use deduplicated data.

#### Acceptance Criteria

1. **R12.1** WHEN entities are consolidated, THE System SHALL update Neo4j nodes to merge duplicate entities

2. **R12.2** THE System SHALL transfer relationships from merged entities to consolidated entity node

3. **R12.3** THE System SHALL update node properties with consolidated attributes: source_count, consensus_confidence, mentioned_in_documents

4. **R12.4** THE System SHALL create `MENTIONED_IN` relationships from entities to document chunks

5. **R12.5** THE System SHALL run consolidation synchronization after each batch of document ingestion

6. **R12.6** THE System SHALL maintain bidirectional sync: SQLite (source of truth) → Neo4j (graph view)

7. **R12.7** THE System SHALL provide script: `python scripts/sync_graph_consolidation.py` for manual sync if needed

### R13: Retrieval Quality Evaluation Framework

**User Story**: As a Machine Learning Engineer, I want automated evaluation of retrieval quality, so that I can measure and improve agent performance.

#### Acceptance Criteria

1. **R13.1** THE System SHALL maintain test dataset of 50 Spanish questions with ground truth answers

2. **R13.2** THE System SHALL measure retrieval metrics:
   - Precision@5: Relevant docs in top 5 / 5
   - Recall@10: Relevant docs found / Total relevant
   - Mean Reciprocal Rank (MRR)
   - NDCG (Normalized Discounted Cumulative Gain)

3. **R13.3** THE System SHALL compare vector-only, graph-only, and hybrid retrieval performance

4. **R13.4** THE System SHALL generate evaluation report: `reports/retrieval_evaluation.json` with per-query breakdown

5. **R13.5** THE System SHALL track evaluation over time to detect performance regression

6. **R13.6** THE System SHALL support A/B testing of different chunking strategies, embedding models, and prompts

7. **R13.7** THE System SHALL expose evaluation endpoint: `/evaluate` accepting test questions

### R14: Performance Optimization and Caching

**User Story**: As a Performance Engineer, I want sub-second query response times, so that users experience fast, responsive AI agents.

#### Acceptance Criteria

1. **R14.1** THE System SHALL cache embedding generation for 24 hours using Redis (optional) or in-memory cache

2. **R14.2** THE System SHALL cache vector search results for repeated queries (5-minute TTL)

3. **R14.3** THE System SHALL use connection pooling for PostgreSQL (max 20 connections) and Neo4j (max 10)

4. **R14.4** THE System SHALL implement async/await for parallel tool calls (vector + graph simultaneously)

5. **R14.5** THE System SHALL precompute embeddings for new chunks in background worker

6. **R14.6** THE System SHALL use HNSW index parameters optimized for speed: m=16, ef_construction=200

7. **R14.7** THE System SHALL achieve query response time: <1s for vector search, <2s for graph query, <2.5s for hybrid

### R15: Spanish Language Optimization

**User Story**: As a Spanish Language Specialist, I want the system optimized for Spanish text processing, so that retrieval quality matches English-language systems.

#### Acceptance Criteria

1. **R15.1** THE System SHALL use Spanish stopword removal: ["el", "la", "de", "en", "y", "a", "los", "las", "del", "al"]

2. **R15.2** THE System SHALL apply Spanish stemming using Snowball stemmer for normalization

3. **R15.3** THE System SHALL handle Spanish-specific characters in search: á, é, í, ó, ú, ñ, ü

4. **R15.4** THE System SHALL create Spanish synonyms for common business terms: "sistema" → ["sistema", "software", "herramienta", "plataforma"]

5. **R15.5** THE System SHALL use Spanish-tuned embedding model if available, otherwise fallback to multilingual model

6. **R15.6** THE System SHALL evaluate retrieval quality specifically on Spanish questions (no English fallback)

7. **R15.7** THE System SHALL provide Spanish error messages and validation feedback

## Success Criteria

### Functionality
- ✅ Processes PDF, DOCX, PNG, JPG documents with >95% success rate
- ✅ OCR accuracy >90% for printed Spanish text, >70% for handwritten
- ✅ Knowledge graph contains 500+ entity nodes with 1000+ relationships
- ✅ Vector database contains 10,000+ embedded chunks
- ✅ Agent correctly selects retrieval tool 85%+ of the time
- ✅ Can answer "¿Qué sistemas causan más puntos de dolor?" with consolidated counts

### Performance
- ✅ Document ingestion: 10-page PDF in <2 minutes
- ✅ Query response time: <2.5 seconds (hybrid search)
- ✅ Vector search: <1 second (HNSW index)
- ✅ Graph query: <2 seconds (indexed Cypher)
- ✅ Parallel document processing: 4 concurrent without bottlenecks

### Quality
- ✅ Retrieval Precision@5 ≥ 0.80
- ✅ MRR (Mean Reciprocal Rank) ≥ 0.75
- ✅ Entity extraction F1 score ≥ 0.85
- ✅ Duplicate consolidation accuracy ≥ 90%
- ✅ Spanish text processing accuracy ≥ 90%

### Integration
- ✅ Consolidation system synchronizes with knowledge graph
- ✅ Agentic RAG integrates with existing extraction pipeline
- ✅ FastAPI endpoint production-ready with auth and rate limiting
- ✅ CLI supports interactive development and testing
- ✅ Comprehensive evaluation framework validates quality

## Implementation Phases

### Phase 1: Document Ingestion Infrastructure (Week 1)
1. Multi-format document parser (PDF, DOCX, images)
2. Mistral OCR integration for scanned documents
3. Intelligent chunking with Spanish optimization
4. Document storage and metadata tracking

### Phase 2: Dual Storage Setup (Week 2)
1. PostgreSQL + pgvector database schema
2. Neo4j knowledge graph setup with Graffiti
3. Embedding generation pipeline (OpenAI)
4. Graph construction from consolidated entities

### Phase 3: Agentic RAG Implementation (Week 3)
1. Pydantic AI agent framework setup
2. Vector search and graph search tools
3. Agent system prompts for tool selection
4. FastAPI endpoint with streaming

### Phase 4: Quality & Optimization (Week 4)
1. Evaluation framework with test dataset
2. Performance optimization (caching, indexing)
3. Spanish language tuning
4. CLI for interactive testing

### Phase 5: Integration & Consolidation (Week 5)
1. Entity extraction from document chunks
2. Consolidation synchronization with graph
3. Relationship discovery from co-occurrence
4. End-to-end workflow automation

## Dependencies

### External Services
- **Neon**: PostgreSQL with pgvector (free tier available)
- **Neo4j**: Graph database (Desktop or Aura free tier)
- **OpenAI API**: Embeddings (text-embedding-3-small) + LLM (gpt-4o-mini)
- **Mistral API**: OCR (Pixtral model for Spanish documents)

### Python Libraries
```
pydantic-ai>=0.0.13        # Agentic RAG framework
graffiti>=0.1.0            # Neo4j knowledge graph library
psycopg2-binary>=2.9.9     # PostgreSQL adapter
pgvector>=0.2.4            # Vector extension
fastapi>=0.109.0           # API framework
pypdf2>=3.0.0              # PDF parsing
python-docx>=1.1.0         # Word document parsing
pillow>=10.2.0             # Image processing
pytesseract>=0.3.10        # Tesseract OCR wrapper (fallback)
openai>=1.10.0             # OpenAI API
anthropic>=0.18.0          # Optional: Claude for ensemble
neo4j>=5.16.0              # Neo4j driver
```

## Risk Mitigation

### Technical Risks
- **OCR Quality**: Mitigation: Use Mistral Pixtral + Tesseract fallback, confidence thresholds, manual review queue
- **Knowledge Graph Scale**: Mitigation: Indexed Cypher queries, connection pooling, incremental updates
- **Agent Tool Selection Accuracy**: Mitigation: Comprehensive system prompts, logging tool decisions, evaluation framework
- **Spanish Language Processing**: Mitigation: Spanish stopwords, stemming, multilingual embeddings, native evaluation

### Operational Risks
- **API Costs**: Mitigation: Rate limiting, caching, batch operations, cost monitoring
- **Database Performance**: Mitigation: HNSW indexes, query optimization, connection pooling
- **Scalability**: Mitigation: Async processing, parallel workers, queue-based ingestion

## Conclusion

This RAG 2.0 enhancement transforms the Comversa system from a JSON-only extraction pipeline into a powerful, production-ready agentic RAG system capable of processing real-world documents (PDFs, images, scans) in Spanish, leveraging both vector databases and knowledge graphs for intelligent retrieval.

**Key Innovations:**
1. **Multi-format ingestion** with Mistral OCR for Spanish documents
2. **Dual storage** combining vector search (pgvector) and graph queries (Neo4j)
3. **Agentic RAG** using Pydantic AI for intelligent tool selection
4. **Knowledge graph consolidation** for deduplicated, consensus-based intelligence
5. **Spanish-first** optimization across the entire pipeline

**Expected Impact:**
- Support real business documents (not just pre-processed JSON)
- Answer complex relational queries ("What systems cause pain?")
- Reduce duplicates by 80-95% through consolidation
- Achieve <2.5s query response times with hybrid search
- Enable production deployment via FastAPI endpoint
