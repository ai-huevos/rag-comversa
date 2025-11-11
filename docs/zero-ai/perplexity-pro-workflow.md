# Perplexity Pro Workflow: Research & Architecture

**Role:** Research assistant + Architecture advisor  
**Timeline:** Week 1-2  
**Output:** Architecture decisions, technology choices, best practices

---

## Phase 1: Research Best Practices (Week 1)

### Prompt 1: LLM Extraction Patterns
```
I'm building a production system that extracts 17 entity types from Spanish 
business interviews using LLMs. Research the latest best practices for:

1. Prompt engineering patterns (2024-2025)
2. Multi-model fallback strategies
3. Cost optimization techniques
4. Quality validation approaches
5. Spanish NLP considerations

Focus on production systems, not research papers. Include:
- Real-world examples from companies
- Performance benchmarks
- Cost comparisons
- Common pitfalls

Cite sources with URLs.
```

### Prompt 2: RAG Architecture Patterns
```
Research modern RAG (Retrieval-Augmented Generation) architectures for:

1. Document processing pipelines (PDF, DOCX, images, CSV)
2. Vector database selection (pgvector vs Pinecone vs Weaviate)
3. Chunking strategies for Spanish text
4. Embedding models for Spanish (multilingual vs Spanish-specific)
5. Hybrid search (vector + keyword)

Include:
- Architecture diagrams
- Performance comparisons
- Cost analysis
- Production case studies

Focus on systems processing 1000+ documents.
```

### Prompt 3: Knowledge Graph Patterns
```
Research knowledge graph patterns for business intelligence:

1. Entity deduplication algorithms (fuzzy + semantic)
2. Relationship discovery techniques
3. Pattern recognition approaches
4. Neo4j vs other graph databases
5. Integration with vector databases

Include:
- Algorithm comparisons
- Performance benchmarks
- Real-world implementations
- Common challenges

Focus on systems with 10,000+ entities.
```

---

## Phase 2: Architecture Design (Week 1-2)

### Prompt 4: System Architecture
```
Design a production architecture for system0 with these requirements:

**Functional:**
- Extract 17 entity types from Spanish interviews
- Process 100+ interviews/hour
- Support multi-format documents (PDF, DOCX, images, CSV)
- RAG-based context enhancement
- Knowledge graph for relationships

**Non-Functional:**
- 99.9% uptime
- <30s processing time per interview
- <$1000/month API costs
- Horizontal scalability
- Real-time monitoring

**Constraints:**
- Spanish-first (no translation)
- GDPR/privacy compliant
- Cloud-agnostic (AWS/GCP/Azure)

Provide:
1. High-level architecture diagram
2. Component breakdown
3. Technology stack recommendations
4. Deployment strategy
5. Cost estimates

Compare at least 3 architecture options.
```

---

## Output: Architecture Decision Records

Save research to `docs/architecture/`:
- `adr-001-llm-extraction-patterns.md`
- `adr-002-rag-architecture.md`
- `adr-003-knowledge-graph-design.md`
- `adr-004-system-architecture.md`
