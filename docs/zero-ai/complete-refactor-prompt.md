# Complete System0 Refactor Prompt

**Use this prompt to kickstart a greenfield refactor with any AI tool**

---

## Context

I'm refactoring **system0**, an AI-powered business intelligence extraction 
system, from scratch. The current codebase has technical debt and missing 
features. I want to rebuild it properly using EARS requirements and modern 
best practices.

---

## Current System (What Works)

**Extraction:**
- 17 entity types from Spanish interviews
- Multi-model fallback (6 models)
- ValidationAgent (completeness, quality, consistency)
- ~30s processing time, ~$0.02 cost per interview

**Storage:**
- SQLite with WAL mode
- Knowledge graph consolidation (77% complete)
- Duplicate detection, entity merging, relationship discovery

**Monitoring:**
- Real-time progress tracking
- Cost estimation
- Quality metrics

---

## Problems with Current System

1. **Prompts hardcoded** - Can't version or A/B test
2. **No evaluation pipeline** - Can't measure quality improvements
3. **No PII detection** - Security risk
4. **No caching** - Performance bottleneck
5. **No user feedback** - Can't improve from usage
6. **Parallel processing broken** - SQLite WAL issues
7. **No frontend** - CLI only, not user-friendly

---

## New System Requirements

### Functional Requirements

**Core Extraction:**
- Extract 17 entity types from Spanish interviews
- Support multi-format (PDF, DOCX, images, CSV, XLSX, WhatsApp)
- Process 100+ interviews/hour
- Achieve ≥85% extraction accuracy
- Preserve Spanish (no translation)
- UTF-8 encoding throughout

**Prompt Engineering:**
- Version control (v1, v2, v3)
- Load from YAML files
- A/B testing support
- Evaluation pipeline with 30-sample test set

**Quality Assurance:**
- Completeness checking (rule-based + LLM)
- Quality validation (UTF-8, required fields)
- Consistency checking (entity references)
- Hallucination detection (keyword overlap)
- Confidence scores per entity

**Cost Control:**
- Estimate cost before processing
- Hard limit ($1000/month)
- Alert at 90% threshold
- Track cumulative costs

**Knowledge Graph:**
- Entity consolidation (fuzzy + semantic)
- Relationship discovery (4 types)
- Pattern recognition (recurring issues)
- Neo4j storage

**RAG Enhancement:**
- Vector search (similar interviews)
- Hybrid search (vector + keyword)
- Context-aware extraction
- PostgreSQL + pgvector

**User Feedback:**
- 5-star rating system
- Correction mechanism
- Feedback storage
- Continuous improvement

### Non-Functional Requirements

**Performance:**
- <30s extraction time per interview
- <200ms API response time
- <2s frontend page load
- 50 API calls/minute rate limit

**Reliability:**
- 99.9% uptime
- Multi-model fallback (6 models)
- Retry logic (3 attempts, exponential backoff)
- Resume capability for failed extractions

**Security:**
- PII detection and redaction
- JWT authentication
- SQL injection prevention
- HTTPS only
- Audit logging

**Scalability:**
- Horizontal scaling (stateless services)
- Queue-based architecture
- Connection pooling
- Caching layer (Redis)

**Observability:**
- Real-time monitoring
- Structured logging
- Metrics collection (Prometheus)
- Distributed tracing
- Alerting (PagerDuty)

### Frontend Requirements

**Dashboard:**
- Recent extractions overview
- Aggregate metrics (success rate, cost, time)
- Real-time updates (WebSocket)
- Quick actions (upload, review)

**Upload Interface:**
- Drag-drop upload
- Batch upload support
- File format validation
- Progress indicators

**Review Interface:**
- Entity grid view
- Detail view with validation results
- Inline editing
- Bulk actions (approve, reject, flag)

**Knowledge Graph Explorer:**
- Visual graph (React Flow)
- Entity filtering
- Relationship exploration
- Pattern highlighting

**Feedback Interface:**
- 5-star rating
- Correction mechanism
- Comment system
- History tracking

**Reports:**
- Template-based reports
- Export (PDF, Excel, CSV)
- Sharing (email, link)
- Scheduling

---

## Technology Stack

### Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI (async)
- **Database:** PostgreSQL + pgvector, Neo4j
- **Cache:** Redis
- **Queue:** Celery + RabbitMQ
- **Testing:** Pytest
- **Type Checking:** Mypy
- **Formatting:** Black + isort

### Frontend
- **Framework:** React 18 + TypeScript
- **UI Library:** Shadcn/ui + Tailwind CSS
- **State:** TanStack Query + Zustand
- **Routing:** React Router v6
- **Real-time:** Socket.io
- **Visualization:** D3.js + React Flow
- **Testing:** Jest + React Testing Library

### Infrastructure
- **Containerization:** Docker + Docker Compose
- **Orchestration:** Kubernetes
- **CI/CD:** GitHub Actions
- **Monitoring:** Prometheus + Grafana
- **Logging:** ELK Stack
- **Secrets:** Vault

---

## Architecture

### High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                         FRONTEND                             │
│  React + TypeScript + Shadcn/ui + TanStack Query           │
└─────────────────────────────────────────────────────────────┘
                            ↓ HTTPS
┌─────────────────────────────────────────────────────────────┐
│                      API GATEWAY                             │
│  FastAPI + JWT Auth + Rate Limiting + CORS                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
        ┌──────────────────┴──────────────────┐
        ↓                                      ↓
┌──────────────────┐                  ┌──────────────────┐
│  EXTRACTION      │                  │  QUERY           │
│  SERVICE         │                  │  SERVICE         │
│  (Async Workers) │                  │  (Read-only)     │
└──────────────────┘                  └──────────────────┘
        ↓                                      ↓
┌──────────────────┐                  ┌──────────────────┐
│  VALIDATION      │                  │  CONSOLIDATION   │
│  SERVICE         │                  │  SERVICE         │
└──────────────────┘                  └──────────────────┘
        ↓                                      ↓
┌─────────────────────────────────────────────────────────────┐
│                      MESSAGE QUEUE                           │
│  RabbitMQ + Celery (Task Distribution)                      │
└─────────────────────────────────────────────────────────────┘
        ↓                                      ↓
┌──────────────────┐                  ┌──────────────────┐
│  STORAGE         │                  │  CACHE           │
│  PostgreSQL      │                  │  Redis           │
│  + pgvector      │                  │  (Sessions,      │
│  Neo4j (Graph)   │                  │   Results)       │
└──────────────────┘                  └──────────────────┘
```

### Service Breakdown

**Extraction Service:**
- Load prompts from YAML
- Call LLM APIs (multi-model fallback)
- Parse JSON responses
- Calculate confidence scores
- Emit progress events (WebSocket)

**Validation Service:**
- Completeness checking
- Quality validation
- Consistency checking
- Hallucination detection
- Flag entities for review

**Consolidation Service:**
- Duplicate detection (fuzzy + semantic)
- Entity merging
- Relationship discovery
- Pattern recognition
- Update knowledge graph

**Query Service:**
- Vector search (pgvector)
- Graph queries (Neo4j)
- Hybrid search
- Aggregations
- Export generation

---

## Your Task

Generate a complete implementation plan with:

### 1. Project Structure
```
system0-v2/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, logging, monitoring
│   │   ├── extractors/   # Entity extractors
│   │   ├── validation/   # Validation pipeline
│   │   ├── storage/      # Repository pattern
│   │   ├── consolidation/# Knowledge graph
│   │   └── workers/      # Celery tasks
│   ├── tests/
│   ├── migrations/
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── pages/        # Page components
│   │   ├── api/          # API client
│   │   ├── hooks/        # Custom hooks
│   │   └── utils/        # Utilities
│   ├── public/
│   └── package.json
├── prompts/              # Prompt templates
├── config/               # Configuration files
├── deploy/               # Kubernetes manifests
└── docs/                 # Documentation
```

### 2. Implementation Phases

Break down into 8 weekly phases:
- Week 1: Requirements & Architecture
- Week 2: Core Infrastructure
- Week 3: Extraction Pipeline
- Week 4: Validation & Quality
- Week 5: Storage & Consolidation
- Week 6: API & Integration
- Week 7: Testing & Refinement
- Week 8: Deployment & Launch

For each phase, provide:
- Specific tasks
- Files to create
- Code examples
- Test requirements
- Success criteria

### 3. Code Examples

Provide production-ready code for:
- Configuration system (Pydantic)
- Extractor factory pattern
- Repository pattern (async)
- FastAPI endpoints
- React components (TypeScript)
- WebSocket integration
- Test examples (pytest, jest)

### 4. Migration Strategy

How to migrate from current system:
- Data migration scripts
- Parallel running strategy
- Rollback plan
- Testing approach

---

## Constraints

1. **Spanish-first** - Never translate content
2. **UTF-8 everywhere** - ensure_ascii=False
3. **Type hints** - All functions typed
4. **Async/await** - For I/O operations
5. **EARS requirements** - Traceable to code
6. **80%+ coverage** - All code tested
7. **Production-ready** - No shortcuts

---

## Success Criteria

### Code Quality
- 80%+ test coverage
- 0 critical security issues
- A+ code quality score
- Full type coverage

### Performance
- <30s extraction time
- <200ms API response
- <2s page load
- 99.9% uptime

### User Experience
- ≥4.5/5 rating
- <5% error rate
- ≥90% task completion
- <10s time to first value

---

## Output Format

Provide:
1. **Complete project structure** (directory tree)
2. **Implementation plan** (8 weeks, detailed tasks)
3. **Code examples** (10+ files with full implementation)
4. **Testing strategy** (unit, integration, e2e)
5. **Deployment guide** (Docker, Kubernetes)
6. **Migration plan** (from current system)

---

## Begin

Start with Week 1: Requirements & Architecture. Provide:
- Refined EARS requirements (if needed)
- System architecture diagram
- Technology stack justification
- Risk assessment
- Timeline with milestones
