# System Architecture

**Last Updated**: 2025-11-09
**Status**: ⚠️ **Implementation Complete, Bugs Present**
**See**: [DECISIONS.md](DECISIONS.md) for why decisions were made

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

### 6. Database (`intelligence_capture/database.py`)

**Purpose**: SQLite storage with WAL mode

**Schema**: 17 entity type tables + metadata

**Key Tables**:
- `interviews` - Interview metadata
- `pain_points` - Business problems
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

## References

- **Implementation Details**: See code in `intelligence_capture/`
- **Decision Rationale**: See [DECISIONS.md](DECISIONS.md)
- **Usage Instructions**: See [RUNBOOK.md](RUNBOOK.md)
- **Experiments Log**: See [EXPERIMENTS.md](EXPERIMENTS.md)
- **Current Bugs**: See [DECISIONS.md](DECISIONS.md#known-issues)

---

**Document Status**: ✅ Master Architecture Document
**Supersedes**: COMPLETE_PROJECT_SUMMARY.md, PROJECT_TRUTH_AUDIT.md, SYSTEM_ARCHITECTURE_VISUAL.md
**Last Reviewed**: 2025-11-09
