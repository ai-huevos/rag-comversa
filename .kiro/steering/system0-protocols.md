---
inclusion: always
---

# System0 Intelligence Extraction Protocols

## Project Context

**System0** extracts structured business intelligence from 44 Spanish manager interviews into SQLite (17 entity types), with migration path to PostgreSQL+pgvector and Neo4j for RAG 2.0.

**Companies**: Los Tajibos, Comversa, Bolivian Foods
**Language**: Spanish only - NEVER translate
**Current Status**: Extraction working, RAG 2.0 in progress (Week 1/5)

---

## 🚨 Critical Rules - NEVER Violate

### 1. Spanish-First Processing (ADR-001)
**NEVER translate Spanish content to any other language**

```python
# ✅ CORRECT
entity = {
    "description": "Reconciliación manual de facturas causa retrasos",
    "severity": "Critical"
}

# ❌ WRONG - Translation breaks context
entity = {
    "description": "Manual invoice reconciliation causes delays"
}
```

**Why**: Translation loses business context and cultural nuances critical for AI agents.

### 2. UTF-8 Encoding Everywhere
**Always use UTF-8 with `ensure_ascii=False`**

```python
# ✅ CORRECT
json.dumps(data, ensure_ascii=False)
open(file, 'r', encoding='utf-8')
conn.text_factory = str  # SQLite UTF-8

# ❌ WRONG
json.dumps(data)  # Escapes Spanish characters
```

**Why**: Prevents mojibake (corrupted text like "retraÃ±o" instead of "retraño").

### 3. Cost Controls
**Always estimate cost before expensive operations**

- Estimate cost for >5 interviews
- Require confirmation if cost >$1.00
- Track cumulative costs during runs
- Monthly budget: $500-$1,000 USD

### 4. No Destructive Actions Without Approval
**Never execute without explicit user confirmation:**
- `git reset --hard`
- Database migrations without rollback plan
- Deleting production data
- Processing documents without consent metadata

### 5. Test Before Full Runs
**Always follow test hierarchy:**

```bash
# 1. Single interview (~30s, $0.03)
python scripts/test_single_interview.py

# 2. Batch test (~3 min, $0.15)
python scripts/test_batch_interviews.py --batch-size 5

# 3. Full extraction (~20 min, $0.50-1.00)
python intelligence_capture/run.py
```

---

## 📋 Required Patterns

### Database Operations

**Always use WAL mode:**
```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA busy_timeout=5000")
conn.execute("PRAGMA foreign_keys=ON")
```

**Always use transactions:**
```python
try:
    # Multiple operations
    conn.commit()
except Exception:
    conn.rollback()
    raise
```

**Always prevent SQL injection:**
```python
# ✅ Whitelist validation
if entity_type not in VALID_ENTITY_TYPES:
    raise ValueError(f"Invalid entity type: {entity_type}")

# ✅ Parameterized queries for values
cursor.execute("SELECT * FROM pain_points WHERE id=?", (id,))
```

### API Calls

**Always use rate limiter:**
```python
from .rate_limiter import get_rate_limiter

rate_limiter = get_rate_limiter(max_calls_per_minute=50)
rate_limiter.wait_if_needed()  # Before API call
```

**Always use fallback chain:**
```python
models = ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo', 
          'o1-mini', 'o1-preview', 'claude-3-5-sonnet']
```

**Always parse JSON robustly:**
```python
# Remove markdown code blocks
if "```json" in response:
    response = response.split("```json")[1].split("```")[0]

# Validate structure
data = json.loads(response.strip())
if not isinstance(data, list):
    raise ValueError(f"Expected list, got {type(data)}")
```

### Code Quality

**Always include:**
- Type hints on all functions
- Comprehensive docstrings (Args/Returns/Raises)
- Contextual error messages (include interview_id, entity_type)
- Progress indicators for long operations

```python
def extract_entities(
    interview_id: int,
    config: Dict[str, Any]
) -> List[Dict]:
    """
    Extract entities from interview
    
    Args:
        interview_id: Interview ID to process
        config: Extraction configuration
        
    Returns:
        List of extracted entities
        
    Raises:
        ValueError: If interview not found
    """
    pass
```

---

## 📁 File Organization

**NEVER create files in project root except:**
- README.md, CLAUDE.MD, PROJECT_STRUCTURE.md
- .env, .gitignore

**Always use proper directories:**
- Documentation → `docs/`
- Scripts → `scripts/`
- Reports → `reports/`
- Data/Databases → `data/`
- Tests → `tests/`
- Config → `config/`
- Main code → `intelligence_capture/`

**Always import paths from config:**
```python
from intelligence_capture.config import DB_PATH, REPORTS_DIR, PROJECT_ROOT
```

---

## 🎯 Current Development Status

### What's Working ✅
- All 17 entity types extracting successfully
- Rate limiter preventing API failures
- Cost estimation and confirmation
- WAL mode for database concurrency
- Resume capability for interrupted runs
- ValidationAgent catching quality issues
- ExtractionMonitor tracking progress

### What's In Progress 🟡
- RAG 2.0 enhancement (Week 1/5)
  - Context Registry + connectors
  - Multi-format DocumentProcessor
  - Mistral Pixtral OCR
  - Spanish chunking
- Knowledge Graph consolidation (specs ready)

### Known Issues ⚠️
- Pilot database empty (needs repopulation)
- Entity consolidation not synced to Neo4j yet
- Ingestion automation incomplete

---

## 🔄 Active Initiatives

### RAG 2.0 Enhancement
**Specs**: `.kiro/specs/rag-2.0-enhancement/`
**Timeline**: 5 weeks
**Current**: Week 1 - Intake & OCR

**Key Tasks**:
- Tasks 0-2: Context Registry, connectors, ingestion queue
- Tasks 3-5: DocumentProcessor, OCR, Spanish chunking
- Tasks 6-9: PostgreSQL+pgvector, embeddings, Neo4j
- Tasks 10-14: Pydantic AI agent, FastAPI, CLI
- Tasks 15-18: Evaluation, optimization, CostGuard
- Tasks 19-21: ConsolidationSync, workers, runbooks

### Knowledge Graph Consolidation
**Specs**: `.kiro/specs/knowledge-graph-consolidation/`
**Status**: Specs ready, implementation pending

**Purpose**: Merge duplicate entities (25 "Excel" → 1 consolidated)

---

## 🤖 Agent Roles (from .codex/agent_roles.yaml)

### Orchestrator
- Maintains `.kiro/specs/*/tasks.md`
- Validates dependencies
- **Cannot**: Modify code or run migrations

### Intake & Processing
- Implements connectors, DocumentProcessor, OCR, chunking
- **Paths**: `intelligence_capture/{connectors,document_processor,ocr,chunking}`
- **Cannot**: Modify database schemas or API

### Storage & Graph
- PostgreSQL migrations, embeddings, Neo4j builder
- **Paths**: `scripts/migrations/`, `intelligence_capture/{database,embeddings}`, `graph/`
- **Requires**: Rollback plan for all migrations

### Agent & API
- Pydantic AI agent, retrieval tools, FastAPI, CLI
- **Paths**: `agent/`, `api/`, `prompts/`, `tests/test_agent*`
- **Cannot**: Touch migrations or consolidation

### Quality & Governance
- Evaluation, optimization, CostGuard, checkpoints
- **Paths**: `reports/`, `scripts/evaluate_retrieval.py`, `governance/`
- **Approves**: All production promotions

### Consolidation & Automation
- ConsolidationSync, ingestion workers, runbooks
- **Paths**: `intelligence_capture/{consolidation_agent,ingestion_worker}.py`
- **Cannot**: Alter Orchestrator tasks or agent prompts

---

## 📊 Database Status

### Production Databases
- **full_intelligence.db** (1.2 MB, 44 interviews)
  - 126 pain points, 162 systems, 236 comm channels
  - Status: ✅ PRIMARY - Single source of truth
  
- **pilot_intelligence.db** (320 KB, 5 interviews)
  - Status: ⚠️ Empty - needs repopulation

### Schema
- **v1.0 (7 tables)**: interviews, pain_points, processes, systems, kpis, automation_candidates, inefficiencies
- **v2.0 (+11 tables)**: communication_channels, decision_points, data_flows, temporal_patterns, failure_modes, team_structures, knowledge_gaps, success_patterns, budget_constraints, external_dependencies

---

## 🔍 Before Starting Work

### Always Check:
1. **Bootstrap files loaded?**
   - CLAUDE.MD
   - .codex/manifest.yaml
   - .codex/agent_roles.yaml
   - Relevant spec tasks.md

2. **Git status clean?**
   ```bash
   git status
   git fetch origin
   ```

3. **Database status?**
   ```bash
   sqlite3 data/full_intelligence.db "SELECT COUNT(*) FROM interviews;"
   ```

4. **Cost estimate?**
   - For any operation >5 interviews
   - Confirm if >$1.00

5. **Test hierarchy followed?**
   - Single → Batch → Full

---

## 🚫 Anti-Patterns - Never Do This

### 1. Never Disable Tests
```python
# ❌ WRONG
# def test_parallel_processing():
#     pass  # Disabled because failing

# ✅ CORRECT - Fix the issue
def test_parallel_processing():
    db.execute("PRAGMA journal_mode=WAL")
    assert parallel_process(interviews) == expected
```

### 2. Never Build Features Before Fixing Bugs
```python
# ❌ WRONG: Phase 1 → Bugs → Skip fixes → Phase 2
# ✅ CORRECT: Phase 1 → Bugs → FIX BUGS → Phase 2
```

### 3. Never Skip Cost Controls
```python
# ❌ WRONG
for interview in load_interviews():
    extract(interview)  # Could cost $50

# ✅ CORRECT
cost = estimate_cost(load_interviews())
if cost > 1.00 and not confirm():
    return
```

### 4. Never Create Root Files
```python
# ❌ WRONG
fsWrite("analysis_report.md", content)

# ✅ CORRECT
fsWrite("docs/analysis_report.md", content)
```

---

## 📚 Key References

- **CLAUDE.MD** - Primary operating manual
- **docs/ARCHITECTURE.md** - System architecture
- **docs/DECISIONS.md** - Architecture Decision Records (ADRs)
- **docs/RUNBOOK.md** - Operations guide
- **docs/DATABASE_AUDIT_2025_11_09.md** - Database forensic audit
- **.ai/CODING_STANDARDS.md** - Detailed coding standards
- **.codex/manifest.yaml** - Initiative timeline and guardrails
- **.codex/agent_roles.yaml** - Agent responsibilities

---

## ✅ Quick Checklist

Before committing code:
- [ ] Spanish content not translated
- [ ] UTF-8 with `ensure_ascii=False`
- [ ] Type hints on all functions
- [ ] Docstrings with Args/Returns/Raises
- [ ] Error messages include context
- [ ] WAL mode enabled for database
- [ ] Rate limiter used for API calls
- [ ] Cost estimated for expensive ops
- [ ] Tests pass (single → batch)
- [ ] Files in correct directories
- [ ] No root-level files created

---

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Status**: Active - RAG 2.0 Week 1/5
**Next Review**: After RAG 2.0 Week 1 completion
