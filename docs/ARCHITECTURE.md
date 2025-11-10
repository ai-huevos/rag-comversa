# System Architecture

**Last Updated**: 2025-11-09
**Status**: ⚠️ **Legacy System Complete, RAG 2.0 Phase 1 Conditional Go**
**See**: [DECISIONS.md](DECISIONS.md) for why decisions were made
**QA Status**: Phase 1 (Tasks 0-5) requires 2-3 days remediation before Week 2

---

## RAG 2.0 Phase 1 QA Status (Nov 9, 2025)

**Overall Grade**: C (62/100) - CONDITIONAL GO with mandatory fixes

**Critical Findings**:
1. 🚨 **Dependencies Not Installed**: 67 packages from requirements-rag2.txt missing (only mistralai installed)
2. 🚨 **Test Claims Invalid**: Reported "103 tests, 85% coverage" but actual execution: 0 tests, 0% coverage
3. 🚨 **UTF-8 Violations**: 3 locations in context_registry.py missing `ensure_ascii=False` (lines 352, 438, 439)
4. ⚠️  **Task 4 Incomplete**: PostgreSQL async integration acknowledged as partial
5. ⚠️  **Tasks 1-2 Untested**: No unit tests exist despite completion claim

**Prerequisites for Week 2**:
- [ ] Install dependencies: `pip install -r requirements-rag2.txt && python -m spacy download es_core_news_md`
- [ ] Fix UTF-8 violations in context_registry.py
- [ ] Complete Task 4 PostgreSQL integration
- [ ] Write missing tests for Tasks 1-2
- [ ] Execute full test suite and verify 80%+ coverage
- [ ] Update completion report with actual metrics

**Estimated Remediation**: 2-3 days

**See**: `docs/archive/2025-11/qa-reviews/` for detailed QA reports

---

## System Overview

**Intelligence Extraction System** - Extracts 17 types of structured business entities from 44 Spanish interview transcripts and stores them in SQLite for AI agent consumption.

### Key Characteristics
- **Language**: Spanish-first (no translation)
- **Database**: SQLite with WAL mode
- **AI Models**: OpenAI GPT-4o-mini (primary) with 6-model fallback chain
- **Scale**: 44 interviews → 500-800 entities → ~20 minutes processing
- **Cost**: $0.50-1.00 per full extraction

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     INTELLIGENCE CAPTURE SYSTEM                  │
└─────────────────────────────────────────────────────────────────┘

INPUT                    PROCESSING                    OUTPUT
┌────────────┐          ┌──────────────┐             ┌──────────┐
│  44 Spanish│   →      │ Processor    │      →      │ SQLite   │
│  Interviews│          │  Pipeline    │             │ Database │
│   (JSON)   │          └──────────────┘             │(17 tables)│
└────────────┘                 ↓                      └──────────┘
                       ┌──────────────┐                    ↓
                       │ Extractor    │              ┌──────────┐
                       │  (17 types)  │              │ Reports  │
                       └──────────────┘              │& Analysis│
                              ↓                      └──────────┘
                    ┌──────────────────┐
                    │ ValidationAgent  │
                    │    + Monitor     │
                    └──────────────────┘
```

---

## Core Components

### 1. Processor (`intelligence_capture/processor.py`)

**Purpose**: Orchestrate the complete extraction pipeline

**Responsibilities**:
- Load 44 interview JSON files
- Call extractor for each interview
- Store results in database
- Track progress for resume capability
- Handle errors and retries

**Key Methods**:
- `process_interviews()` - Main pipeline
- `_process_single_interview()` - Per-interview extraction
- `_store_entities()` - Database storage

**Flow**:
```python
for interview in interviews:
    entities = extractor.extract_all(interview)
    for entity_type, entity_list in entities.items():
        database.insert(entity_type, entity_list)
    progress.mark_complete(interview_id)
```

---

### 2. Extractor (`intelligence_capture/extractor.py`)

**Purpose**: Orchestrate extraction of 17 entity types

**Responsibilities**:
- Coordinate all specialized extractors
- Call OpenAI API with structured prompts
- Handle LLM fallback chain (6 models)
- Parse JSON responses
- Calculate confidence scores

**Key Methods**:
- `extract_all()` - Orchestrates all extractions
- `_call_gpt4()` - LLM API with fallback
- Individual extraction methods (17 types)

**Extraction Pattern** (per entity type):
```python
def _extract_<entity_type>(self, meta, qa_pairs):
    # 1. Build system prompt (what to extract)
    system_prompt = """Extract {entity_type} from Spanish interview
    Output JSON: [{schema}]"""

    # 2. Build user prompt (interview content)
    user_prompt = f"Interview: {meta}\nQ&A: {qa_pairs}"

    # 3. Call LLM with fallback chain
    response = self._call_gpt4(system_prompt, user_prompt)

    # 4. Parse and validate JSON
    entities = json.loads(response)

    # 5. Add metadata (company, BU, confidence)
    for entity in entities:
        entity['company'] = meta['company']
        entity['confidence'] = 0.85

    return entities
```

**LLM Fallback Chain**:
1. gpt-4o-mini (fast, cheap) → try 3x with exponential backoff
2. gpt-4o (better quality) → try 3x
3. gpt-3.5-turbo → try 3x
4. o1-mini → try 3x
5. o1-preview → try 3x
6. claude-3-5-sonnet-20241022 → try 3x

---

### 3. Specialized Extractors (`intelligence_capture/extractors.py`)

**Purpose**: 11 v2.0 specialized extraction classes

**Extractors**:
1. `CommunicationChannelExtractor` - WhatsApp, email, Teams
2. `DecisionPointExtractor` - Who decides what, escalation
3. `DataFlowExtractor` - Data movement between systems
4. `TemporalPatternExtractor` - When things happen
5. `FailureModeExtractor` - What goes wrong, workarounds
6. `TeamStructureExtractor` - Org hierarchy
7. `KnowledgeGapExtractor` - Training needs
8. `SuccessPatternExtractor` - What works well
9. `BudgetConstraintExtractor` - Budget limitations
10. `ExternalDependencyExtractor` - Third-party blockers
11. Enhanced v1.0 extractors (sentiment, scoring)

**Pattern**: Each extractor has:
- `extract()` method
- Specialized system prompt
- JSON schema definition
- Confidence scoring logic

---

### 4. ValidationAgent (`intelligence_capture/validation_agent.py`)

**Purpose**: Automated quality checking

**Validation Types**:

1. **Completeness Check**:
   - Minimum entities per interview
   - All required fields present
   - No placeholder values ("N/A", "Unknown")

2. **Quality Check**:
   - UTF-8 encoding correct
   - No escaped characters (`\u00f3`)
   - Descriptions not empty
   - Confidence scores reasonable

3. **Consistency Check**:
   - Companies match known list
   - Business units valid
   - Departments exist

**Usage**:
```python
validator = ValidationAgent(config)
is_valid = validator.validate(entities, interview_id)
if not is_valid:
    logger.warning(f"Validation failed for {interview_id}")
```

---

### 5. Monitor (`intelligence_capture/monitor.py`)

**Purpose**: Real-time progress tracking

**Metrics Tracked**:
- Entities extracted per type
- Processing time per interview
- API cost per interview
- Quality scores
- Success/failure rates

**Output**:
```
Processing interview 5/44...
  ✓ Pain points: 12
  ✓ Processes: 18
  ✓ Systems: 15
  ✓ Time: 28s
  ✓ Cost: $0.03

Overall Progress:
  Total entities: 245
  Average time: 26s/interview
  Total cost: $0.15
```

---

### 6. Knowledge Graph Consolidation (Phases 1-11 Complete)

**Purpose**: Merge duplicate entities, discover relationships, identify patterns

**Status**: ✅ **Production-ready** (69% complete - 36/52 tasks)

**Components**:
- `consolidation_agent.py` - Main orchestrator with metrics integration
- `duplicate_detector.py` - Fuzzy + semantic matching (96x speedup achieved)
- `entity_merger.py` - Merge logic with source tracking
- `consensus_scorer.py` - Confidence calculation
- `relationship_discoverer.py` - System→Pain, Process→System, KPI→Process, Automation→Pain
- `pattern_recognizer.py` - Recurring patterns, problematic systems
- `metrics.py` - Comprehensive metrics collection (NEW)
- `rollback_consolidation.py` - Rollback mechanism with entity snapshots (NEW)

**Flow**:
```python
# After extraction
entities = extractor.extract_all(interview)

# Consolidate with metrics tracking
consolidated = consolidation_agent.consolidate_entities(entities, interview_id)
# - Finds duplicates (fuzzy 70% + semantic 30%)
# - Merges entities (tracks sources, detects contradictions)
# - Calculates confidence (based on source agreement)
# - Discovers relationships (co-occurrence in interviews)
# - Identifies patterns (recurring issues, problematic systems)
# - Tracks metrics (duplicates, API calls, quality)

# Store consolidated entities
database.insert(consolidated)

# Export metrics
metrics = consolidation_agent.get_metrics()
metrics.export_to_json("reports/metrics.json")
metrics.display_summary()
```

**Key Features**:
- **Duplicate detection**: 0.70-0.90 similarity thresholds (tuned per entity type)
- **Source tracking**: `mentioned_in_interviews`, `source_count`
- **Consensus scoring**: Tuned for 44 interviews (source_count_divisor=5)
- **Relationships**: 4 types (causes, uses, measures, addresses)
- **Patterns**: Recurring pains (3+ mentions), problematic systems (5+ mentions)
- **Performance**: 96x speedup, 95% cost reduction via fuzzy-first filtering
- **Rollback**: Entity snapshots with full rollback capability
- **Metrics**: Comprehensive tracking (duplicates, API calls, quality, performance)

**Production Configuration** (`config/consolidation_config.json`):
- Lower thresholds for pain_points (0.70) and processes (0.75) to catch more duplicates
- Higher thresholds for KPIs (0.85) and team_structures (0.90) for precision
- Fuzzy-first filtering enabled (skip semantic if fuzzy >0.95)
- Retry logic with exponential backoff and circuit breaker
- Structured logging to `logs/consolidation.log`

**Completed Phases**:
- ✅ Phase 1-3: Foundation, core components, database integration
- ✅ Phase 4-6: Relationships, patterns, testing, reporting
- ✅ Phase 7-9: Security hardening, performance optimization, code quality
- ✅ Phase 10-11: Testing, rollback, metrics, production configuration

**Pending**: 
- Phase 12: Final validation (Tasks 37-40)
- Phase 13-14: RAG 2.0 integration, PostgreSQL/Neo4j sync (Week 5)

**See**: `.kiro/specs/knowledge-graph-consolidation/` for full specs

---

### 7. Database (`intelligence_capture/database.py`)

**Purpose**: SQLite storage with WAL mode

**Schema**: 17 entity type tables + metadata + consolidation fields + rollback support

**Key Tables**:
- `interviews` - Interview metadata
- `pain_points` - Business problems
- `relationships` - Entity connections (4 types: causes, uses, measures, addresses)
- `patterns` - Recurring issues (recurring_pain, problematic_system)
- `consolidation_audit` - Merge audit trail with rollback tracking
- `entity_snapshots` - Entity state before consolidation (for rollback)
- `processes` - Workflows
- `systems` - Tools/software
- `kpis` - Success metrics
- `automation_candidates` - Automation opportunities
- `inefficiencies` - Wasteful steps
- `communication_channels` - WhatsApp, email, etc.
- `decision_points` - Decision rules
- `data_flows` - Data movement
- `temporal_patterns` - Timing patterns
- `failure_modes` - Failure scenarios
- (+ 6 more entity types)

**Key Features**:
- Foreign keys link entities to interviews
- Indexes for fast queries
- WAL mode for parallel access
- Progress tracking columns
- Review status fields

**Common Fields** (all entities):
```sql
id INTEGER PRIMARY KEY
interview_id INTEGER REFERENCES interviews(id)
company TEXT
business_unit TEXT
department TEXT
confidence REAL
needs_review BOOLEAN
review_notes TEXT
reviewed_at TIMESTAMP
```

---

## Data Flow

### End-to-End Extraction Flow

```
1. Load Interviews
   ├─ Read: data/interviews/analysis_output/all_interviews.json
   ├─ Parse: 44 interview objects
   └─ Metadata: company, role, department

2. Extract Entities (per interview)
   ├─ Call: extractor.extract_all(interview)
   ├─ LLM: 17 API calls per interview (one per entity type)
   ├─ Parse: JSON responses
   ├─ Validate: completeness, quality
   └─ Output: Dict[entity_type, List[entity]]

3. Store in Database
   ├─ For each entity type:
   │   ├─ Insert into appropriate table
   │   ├─ Link to interview via interview_id
   │   └─ Store confidence, metadata
   └─ Update progress tracking

4. Monitor & Report
   ├─ Track: time, cost, quality
   ├─ Print: periodic summaries
   └─ Generate: final report

5. Validation
   ├─ Run: scripts/validate_extraction.py
   ├─ Check: completeness, quality, consistency
   └─ Report: issues found
```

---

## Configuration

### Centralized Config (`config/extraction_config.json`)

```json
{
  "extraction": {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_retries": 3
  },
  "validation": {
    "enable_validation_agent": true,
    "enable_llm_validation": false
  },
  "ensemble": {
    "enable_ensemble_review": false
  },
  "monitoring": {
    "enable_monitor": true,
    "print_summary_every_n": 5
  },
  "performance": {
    "parallel_processing": true
  }
}
```

### Environment Variables (`.env`)

```bash
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...  # Optional for Claude fallback
ENABLE_ENSEMBLE_REVIEW=false  # Keep disabled
```

---

## Performance Characteristics

### Standard Sequential Extraction
- **Time**: 10-15 minutes for 44 interviews
- **Cost**: $0.50-1.00
- **Throughput**: 30s per interview
- **Quality**: Good with ValidationAgent

### With Parallel Processing (CURRENTLY BROKEN)
- **Time**: 5-8 minutes for 44 interviews (est.)
- **Issue**: Database locking prevents parallel writes
- **Status**: ❌ Not working (see [DECISIONS.md](DECISIONS.md#parallel-processing))

### With Ensemble Validation (DISABLED)
- **Time**: 30-45 minutes for 44 interviews
- **Cost**: $2.50-5.00 (5x more expensive)
- **Quality**: 30-40% improvement
- **Status**: Implemented but disabled by default (too complex)

---

## Error Handling

### Retry Strategy

**LLM API Calls**:
```python
for attempt in range(max_retries):
    try:
        response = openai.call(...)
        return response
    except RateLimitError:
        wait_time = 2 ** attempt  # Exponential backoff
        time.sleep(wait_time)
    except APIError:
        # Fallback to next model in chain
        model = next_model()
```

**Database Operations**:
```python
try:
    db.insert_entities(entities)
except sqlite3.IntegrityError:
    logger.error("Duplicate entity")
    # Skip and continue
except sqlite3.OperationalError:
    logger.error("Database locked")
    # Retry with exponential backoff
```

---

## Security Considerations

### SQL Injection Prevention
- ✅ **Parameterized queries**: All database operations use `?` placeholders
- ❌ **Never string interpolation**: `f"SELECT * FROM {table}"` forbidden

### API Key Management
- ✅ **Environment variables**: Keys in `.env`, not hardcoded
- ✅ **Git ignored**: `.env` in `.gitignore`
- ❌ **No validation**: Keys not validated before use (could fail mid-extraction)

### Cost Controls
- ⚠️ **No hard limits**: System doesn't enforce max cost
- ⚠️ **No estimation**: Doesn't show estimated cost before running
- ⚠️ **Manual monitoring**: User must watch cost manually

---

## Known Architectural Issues

### 🚨 Critical Issues (Block Production)

See [DECISIONS.md](DECISIONS.md) for detailed analysis.

1. **No Rate Limiting**
   - LLM API calls don't respect OpenAI limits
   - Will fail after ~50-100 requests
   - **Impact**: Cannot run 44-interview extraction reliably

2. **Database Locking (Parallel Mode)**
   - SQLite WAL mode not sufficient
   - Parallel workers deadlock
   - **Impact**: Parallel processing completely broken

3. **No Cost Controls**
   - System doesn't stop at cost threshold
   - Could accidentally spend $50+
   - **Impact**: Financial risk

### ⚠️ Important Issues (Degrade Experience)

4. **Weak Resume Logic**
   - Progress tracking basic
   - Doesn't detect stuck interviews
   - **Impact**: Manual intervention required on failure

5. **Validation Doesn't Block**
   - Validation warnings logged but not enforced
   - Bad data stored in database
   - **Impact**: Quality issues not prevented

---

## Testing Strategy

See [RUNBOOK.md](RUNBOOK.md) for detailed testing procedures.

### Test Scripts

1. **Single Interview Test** (`scripts/test_single_interview.py`)
   - Tests 1 interview (~30s, $0.03)
   - Verifies all 17 entity types extract
   - Quick sanity check

2. **Batch Test** (`scripts/test_batch_interviews.py`)
   - Tests 5 interviews (~3 min, $0.15)
   - Tests resume capability
   - Performance benchmarking

3. **Validation Script** (`scripts/validate_extraction.py`)
   - Checks completeness (all 17 types have data)
   - Checks quality (no empty fields, UTF-8 correct)
   - Checks consistency (valid companies, no orphans)

---

## Future Architecture Considerations

### Knowledge Graph (Documented but NOT Implemented)

**Concept**: Consolidate duplicate entities and discover relationships

**Proposed Components**:
- `KnowledgeConsolidationAgent` - Merge duplicates
- `RelationshipDiscoveryAgent` - Find connections
- `PatternRecognitionAgent` - Identify recurring themes
- `ContradictionDetector` - Flag inconsistencies

**Status**: ❌ Only documented, 0% implemented

**Decision**: See [DECISIONS.md](DECISIONS.md#knowledge-graph) for why not implemented yet

---

## Technology Stack

### Languages
- **Python 3.9+**: Primary language
- **SQL**: SQLite for storage

### Dependencies
- **openai**: GPT API client
- **anthropic**: Claude API client (fallback)
- **python-dotenv**: Environment variable management
- **pandas**: Report generation (optional)
- **openpyxl**: Excel export (optional)

### Development Tools
- **pytest**: Unit testing (planned)
- **black**: Code formatting (not configured)
- **mypy**: Type checking (not configured)

---

## Deployment Architecture

### Current: Local Development
- ✅ Runs on developer machine
- ✅ Suitable for 44 interviews
- ❌ No production deployment
- ❌ No cloud infrastructure

### Future: Cloud Deployment (Planned but NOT Documented)
- ⏳ AWS/GCP/Azure (undecided)
- ⏳ Containerization (Docker)
- ⏳ Scalable storage
- ⏳ API endpoints

**Status**: ❌ No `cloud.md`, no deployment docs, 0% implemented

---

## RAG 2.0 PostgreSQL Schemas (Tasks 2 & 4)

### Migration Files Created: 2025-11-09

#### Ingestion Queue Schema (`2025_01_01_ingestion_queue.sql`)

**Purpose**: Track document ingestion lifecycle from queue to completion for RAG 2.0 multi-format pipeline.

**Table: ingestion_events**
```sql
CREATE TABLE ingestion_events (
    id SERIAL PRIMARY KEY,
    org_id VARCHAR(100) NOT NULL,              -- Los Tajibos, Comversa, Bolivian Foods
    document_id UUID NOT NULL,                  -- Links to documents table
    connector_type VARCHAR(50) NOT NULL,        -- email, whatsapp, api, sharepoint, drive
    source_path TEXT NOT NULL,                  -- data/documents/inbox/{connector}/{org}/...
    source_format VARCHAR(50),                  -- pdf, docx, image, csv, xlsx, whatsapp
    checksum VARCHAR(64) NOT NULL UNIQUE,       -- SHA-256 for deduplication
    file_size_bytes BIGINT,
    status VARCHAR(50) DEFAULT 'queued',        -- queued, processing, completed, failed
    stage VARCHAR(50),                          -- enqueued, parsing, ocr, chunking, embedding...
    enqueued_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,                         -- Spanish error messages
    retry_count INTEGER DEFAULT 0,
    processing_time_seconds FLOAT,
    metadata JSONB                              -- Flexible connector-specific details
);
```

**Key Indexes**:
- `idx_ingestion_org_status` - Org-based status filtering
- `idx_ingestion_checksum` - Fast deduplication lookups
- `idx_ingestion_status` - Worker polling for queued jobs
- `idx_ingestion_metadata` - GIN index for JSONB queries

**Auto-calculated Fields**:
- `processing_time_seconds` - Calculated by trigger on completion

**Rollback**: `scripts/migrations/rollback/2025_01_01_ingestion_queue_rollback.sql`

---

#### OCR Review Queue Schema (`2025_01_02_ocr_review_queue.sql`)

**Purpose**: Queue low-confidence OCR segments for manual review and correction.

**Table: ocr_review_queue**
```sql
CREATE TABLE ocr_review_queue (
    id SERIAL PRIMARY KEY,
    document_id UUID NOT NULL,                  -- Links to ingestion_events
    page_number INTEGER NOT NULL,               -- 1-based page number
    segment_index INTEGER NOT NULL,             -- 0-based segment within page
    ocr_text TEXT,                              -- Raw OCR output (may be incorrect)
    confidence FLOAT NOT NULL,                  -- 0.0-1.0 confidence score
    ocr_engine VARCHAR(50) NOT NULL,            -- mistral_pixtral, tesseract
    bounding_box JSONB,                         -- {x, y, width, height, ...}
    image_crop_url TEXT,                        -- Path to cropped image
    status VARCHAR(50) DEFAULT 'pending_review', -- pending_review, in_review, approved, rejected
    reviewed_by VARCHAR(100),                   -- Reviewer username/email
    corrected_text TEXT,                        -- Manually corrected text
    review_notes TEXT,                          -- Spanish reviewer notes
    created_at TIMESTAMP DEFAULT NOW(),
    reviewed_at TIMESTAMP,
    priority VARCHAR(20) DEFAULT 'normal',      -- high, normal, low
    segment_type VARCHAR(50),                   -- handwriting, printed_degraded, tables
    metadata JSONB
);
```

**Key Indexes**:
- `idx_ocr_status_priority` - Pending reviews by priority
- `idx_ocr_confidence` - Low confidence segments first
- `idx_ocr_document` - All segments for a document
- `idx_ocr_reviewed_by` - Reviewer activity tracking

**Views Created**:
- `ocr_high_priority_queue` - Pending reviews with confidence < 0.50
- `ocr_reviewer_stats` - Reviewer performance metrics

**Auto-calculated Fields**:
- `priority` - Auto-set by trigger based on confidence thresholds:
  - High: confidence < 0.50
  - Normal: 0.50-0.70
  - Low: 0.70-0.90
- `image_crop_url` - Auto-generated path: `data/ocr_crops/{document_id}/page_{page}_segment_{segment}.png`

**Rollback**: `scripts/migrations/rollback/2025_01_02_ocr_review_queue_rollback.sql`

---

### Migration Runner

**Script**: `scripts/run_pg_migrations.py`

**Usage**:
```bash
# Run all pending migrations
python scripts/run_pg_migrations.py

# Show migration status
python scripts/run_pg_migrations.py --status

# Preview migrations (dry run)
python scripts/run_pg_migrations.py --dry-run

# Rollback specific migration
python scripts/run_pg_migrations.py --rollback 2025_01_01_ingestion_queue
```

**Features**:
- Transaction-safe execution
- Migration history tracking in `migration_history` table
- Automatic rollback on failure
- Dry-run mode for preview
- Safety checks before rollback (warns if data exists)

**Environment**:
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

---

### RAG 2.0 Architecture Diagram (Phase 1 - Weeks 1-2)

```
┌──────────────────────────────────────────────────────────────────┐
│                    RAG 2.0 INGESTION PIPELINE                     │
└──────────────────────────────────────────────────────────────────┘

SOURCES                QUEUE                   PROCESSING
┌──────────┐          ┌─────────────┐         ┌──────────────┐
│ Email    │   →      │ Ingestion   │    →    │ Document     │
│ WhatsApp │   →      │ Events      │    →    │ Processor    │
│ SharePt  │   →      │ (Postgres)  │    →    │ Multi-format │
│ API      │   →      └─────────────┘         └──────────────┘
└──────────┘                 ↓                       ↓
                     ┌─────────────┐         ┌──────────────┐
                     │ Worker Pool │    →    │ OCR Engine   │
                     │ (4 concurrent)         │ Pixtral/Tess │
                     └─────────────┘         └──────────────┘
                                                     ↓
                                             ┌──────────────┐
                                             │ OCR Review   │
                                             │ Queue (low   │
                                             │ confidence)  │
                                             └──────────────┘
                                                     ↓
STORAGE                                      ┌──────────────┐
┌──────────┐                                 │ Document     │
│Postgres  │   ←──────────────────────────   │ Chunks       │
│+ pgvector│                                 │ Spanish      │
│          │                                 └──────────────┘
│Neo4j     │   ←──────────────────────────   Knowledge Graph
│Graph     │                                 (Phase 2)
└──────────┘
```

**Data Flow**:
1. **Connectors** → Drop files in `data/documents/inbox/{connector}/{org}/`
2. **Ingestion Watcher** → Queue jobs in `ingestion_events` (status: queued)
3. **Worker Pool** → Poll queue, process documents (status: processing)
4. **DocumentProcessor** → Parse multi-format (PDF, DOCX, images, CSV, XLSX)
5. **OCR Engine** → Process images/scanned PDFs with Mistral Pixtral
6. **Low Confidence** → Queue in `ocr_review_queue` for manual review
7. **Spanish Chunker** → Split into 300-500 token chunks
8. **Embeddings Pipeline** → Generate vectors with `text-embedding-3-small`
9. **Postgres Storage** → Store chunks + embeddings in pgvector
10. **Completion** → Update `ingestion_events` (status: completed)

**Concurrency**:
- Max 4 concurrent workers (configurable)
- Max 5 concurrent OCR calls (shared rate limiter)
- Shared rate limiter across all workers

**Error Handling**:
- Retry up to 3 times per document
- Failed documents → `status: failed`, Spanish error messages
- Processing directories: `processing/`, `processed/`, `failed/`

---

### Database Configuration

**File**: `config/database.toml`

```toml
# PostgreSQL connection for RAG 2.0
[postgresql]
read_uri = "postgresql://user:pass@host:5432/dbname"
write_uri = "postgresql://user:pass@host:5432/dbname"
pool_size = 10
max_overflow = 20
pool_timeout = 30

# SQLite (legacy - consolidation only)
[sqlite]
path = "data/full_intelligence.db"
wal_mode = true
busy_timeout = 5000

# Neo4j (Phase 2)
[neo4j]
uri = "neo4j://localhost:7687"
user = "neo4j"
# password from environment: NEO4J_PASSWORD
```

**Environment Variables**:
```bash
DATABASE_URL="postgresql://user:pass@host:5432/dbname"  # Required for migrations
NEO4J_PASSWORD="..."                                     # Required for graph
OPENAI_API_KEY="..."                                     # Required for embeddings
MISTRAL_API_KEY="..."                                    # Required for OCR
```

---

## References

- **Implementation Details**: See code in `intelligence_capture/`
- **Decision Rationale**: See [DECISIONS.md](DECISIONS.md)
- **Usage Instructions**: See [RUNBOOK.md](RUNBOOK.md)
- **Experiments Log**: See [EXPERIMENTS.md](EXPERIMENTS.md)
- **Current Bugs**: See [DECISIONS.md](DECISIONS.md#known-issues)
- **RAG 2.0 Tasks**: See [.kiro/specs/rag-2.0-enhancement/tasks.md](.kiro/specs/rag-2.0-enhancement/tasks.md)

---

**Document Status**: ✅ Master Architecture Document
**Supersedes**: COMPLETE_PROJECT_SUMMARY.md, PROJECT_TRUTH_AUDIT.md, SYSTEM_ARCHITECTURE_VISUAL.md
**Last Reviewed**: 2025-11-09
**RAG 2.0 Schemas**: Tasks 2 & 4 Complete (2025-11-09)
