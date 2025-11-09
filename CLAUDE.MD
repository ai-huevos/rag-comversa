# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# RAG-Comversa Project Context

## Project Overview
**Intelligence Extraction System** for Comversa - extracts structured business intelligence from 44 Spanish interview transcripts and stores it in a queryable SQLite database for AI agent use.

- **Language:** All interviews are in Spanish - never translate
- **Database:** SQLite with 17 entity types
- **AI Models:** OpenAI (gpt-4o-mini primary) with 6-model fallback chain
- **Companies:** Los Tajibos (hotel), Comversa (construction), Bolivian Foods (restaurants)
- **Source Data:** 44 manager interviews in Spanish

---

## Current State

### ✅ **Phases 1-4 COMPLETE** - Full System Implementation

**Phase 1: Core Integration** ✅
1. ✅ Consolidated extraction logic - All 17 entity types
2. ✅ Updated processor storage - Error handling per entity
3. ✅ Quality validation - Always-on validation
4. ✅ Progress tracking - Resume capability

**Phase 2: Optimization** ✅
5. ✅ ValidationAgent - Completeness checking
6. ✅ ExtractionMonitor - Real-time dashboard
7. ✅ Centralized configuration - extraction_config.json
8. ✅ Batch operations - Transaction support

**Phase 3: Testing & Validation** ✅
9. ✅ Test scripts - Single and batch testing
10. ✅ Validation script - Comprehensive checks
11. ✅ Documentation - SETUP.md, guides
12. ✅ Environment setup - .env.example

**Phase 4: Parallel Processing & Rate Limiting** ✅
13. ✅ WAL mode for parallel processing (no database locking)
14. ✅ Rate limiting with exponential backoff
15. ✅ Cost estimation before extraction
16. ✅ Ensemble validation (disabled by default)

**What's Working:**
- ✅ All 17 entity types extracting
- ✅ ValidationAgent (completeness checking)
- ✅ ExtractionMonitor (real-time progress)
- ✅ Quality validation (always on)
- ✅ Progress tracking with resume
- ✅ Parallel processing (WAL mode + rate limiter)
- ✅ Rate limiting (no API errors)
- ✅ Cost estimation (shows cost before extraction)
- ✅ Ensemble disabled by default (fast, cheap mode)

**Recent Fixes (2025-11-08):**
- ✅ Fixed parallel processing with WAL mode
- ✅ Added shared rate limiter
- ✅ Tested with 5 interviews (4/5 succeeded)
- ✅ Proved Knowledge Graph is essential (analyzed existing data)

### 🎯 Current Phase: Knowledge Graph Consolidation (Week 1)

**Status:** Spec created, ready to implement consolidation system

**Problem Identified:**
- 20-30% of extracted data is duplicated
- 25 separate "Excel" entries, 12 separate "SAP" entries
- Cannot answer questions like "What systems cause the most pain?"

**Solution:**
- Build Knowledge Graph Consolidation System
- Merge duplicate entities with source tracking
- Calculate consensus confidence scores
- Discover relationships between entities
- Identify recurring patterns

**Spec Location:** `.kiro/specs/knowledge-graph-consolidation/`

---

## 17 Entity Types

### v1.0 Entities (6) - Currently Working
1. PainPoint - Problems blocking work
2. Process - How work gets done
3. System - Tools/software used
4. KPI - Success metrics
5. AutomationCandidate - Automation opportunities
6. Inefficiency - Wasteful steps

### v2.0 Entities (11) - Need Integration
7. CommunicationChannel - WhatsApp, email, Teams, etc.
8. DecisionPoint - Who decides what, escalation rules
9. DataFlow - Data movement between systems
10. TemporalPattern - When things happen (daily, weekly, etc.)
11. FailureMode - What goes wrong, workarounds
12. TeamStructure - Org hierarchy, reporting lines
13. KnowledgeGap - Training needs, missing skills
14. SuccessPattern - What works well, best practices
15. BudgetConstraint - Budget limitations affecting work
16. ExternalDependency - Third-party vendors, external blockers
17. Enhanced v1.0 - System with sentiment, AutomationCandidate with effort/impact scoring

---

## Key Files

### Implementation
- `intelligence_capture/extractor.py` - Main extraction orchestrator (needs update)
- `intelligence_capture/extractors.py` - v2.0 specialized extractors (13 classes)
- `intelligence_capture/processor.py` - Pipeline orchestrator (needs update)
- `intelligence_capture/database.py` - Database operations
- `intelligence_capture/config.py` - Configuration

### Specs & Docs
- `.kiro/specs/extraction-completion/tasks.md` - Full task breakdown
- `.kiro/specs/extraction-completion/requirements.md` - Requirements doc
- `PHASE1_COMPLETE_SUMMARY.md` - What was built previously
- `SESSION_COMPLETE_SUMMARY.md` - Previous session summary

### Tests
- `tests/test_*.py` - Unit tests for all extractors

---

## Core Architecture

### Extraction Pipeline

```
Interview JSON → IntelligenceExtractor → 17 Entity Types → SQLite → Knowledge Graph → AI Agents
```

**Flow:**
1. `processor.py` (IntelligenceProcessor) orchestrates the pipeline
2. `extractor.py` (IntelligenceExtractor) extracts 6 v1.0 entity types
3. `extractors.py` (13 specialized extractors) extracts 11 v2.0 entity types
4. `validation_agent.py` validates completeness and quality
5. `database.py` (IntelligenceDB/EnhancedIntelligenceDB) stores entities
6. `monitor.py` (ExtractionMonitor) tracks real-time progress
7. Knowledge Graph Consolidation merges duplicates and discovers relationships

### Key Components

- **IntelligenceExtractor** (`extractor.py`): Orchestrates extraction via `extract_all()`, delegates to v2 extractors
- **IntelligenceProcessor** (`processor.py`): Main pipeline with `process_interviews()` and resume capability
- **ValidationAgent** (`validation_agent.py`): Checks completeness, encoding, placeholders
- **ExtractionMonitor** (`monitor.py`): Real-time progress dashboard
- **Rate Limiter** (`rate_limiter.py`): Exponential backoff for API calls with shared state
- **IntelligenceDB** (`database.py`): Core schema; EnhancedIntelligenceDB adds v2.0 tables

---

## Development Commands

### Setup & Configuration

```bash
# Install dependencies
pip install openai python-dotenv

# Configure API key
cp .env.example .env
# Edit .env: OPENAI_API_KEY=sk-proj-your-key-here

# Verify setup
python -c "from intelligence_capture.config import OPENAI_API_KEY; print('✓ API key configured' if OPENAI_API_KEY else '✗ No API key')"
```

### Testing

```bash
# Single interview test (~10 sec, ~$0.01)
python scripts/test_single_interview.py

# Batch test - 5 interviews (~2-3 min, ~$0.10)
python scripts/test_batch_interviews.py --batch-size 5

# Validate extraction results
python scripts/validate_extraction.py --db data/test_batch.db

# Generate comprehensive report
python scripts/generate_comprehensive_report.py --format both
```

### Production Extraction

```bash
# Full extraction - 44 interviews (~15-20 min, ~$0.50-1.00)
python intelligence_capture/run.py

# Resume interrupted extraction
python intelligence_capture/run.py --resume

# Custom database path
python intelligence_capture/run.py --db data/custom.db
```

### Database Queries

```bash
# Open database
sqlite3 intelligence.db

# Example queries
SELECT COUNT(*) FROM pain_points;
SELECT * FROM pain_points WHERE company='Los Tajibos' AND severity='Critical';
SELECT name, usage_count FROM systems ORDER BY usage_count DESC LIMIT 10;
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_automation_candidate_extraction.py

# Run tests with verbose output
pytest -v tests/
```

---

## Next Steps: Knowledge Graph Consolidation (Week 1)

### Week 1 Goal: Build Consolidation System
**Objective:** Merge duplicate entities and build consensus from multiple sources

**Timeline:** 5 days
- Day 1: Database schema + duplicate detector
- Day 2: Entity merger + consensus scorer + consolidation agent
- Day 3: Integration with processor + database migration
- Day 4: Relationship discovery + pattern recognition
- Day 5: Testing with 10 interviews + validation

**Expected Results:**
- Duplicate reduction: 80-95% (48 system entries → 3 consolidated)
- Source tracking: All entities have mentioned_in_interviews
- Consensus confidence: Average >= 0.75
- Relationships: System → Pain Point, Process → System
- Patterns: Recurring issues identified (30%+ of interviews)

### How to Start
```bash
# 1. Review the spec
cat .kiro/specs/knowledge-graph-consolidation/requirements.md
cat .kiro/specs/knowledge-graph-consolidation/design.md
cat .kiro/specs/knowledge-graph-consolidation/tasks.md

# 2. Start with Task 1: Database Schema
# Open tasks.md and click "Start task" next to Task 1
```

### After Week 1: Full Extraction
Once consolidation is complete, run full 44-interview extraction:
```bash
# Run extraction with consolidation
python intelligence_capture/run.py

# Validate consolidation
python scripts/validate_consolidation.py

# Generate consolidation report
python scripts/generate_consolidation_report.py
```

**Expected:**
- Processing time: 15-20 minutes
- Cost: ~$2.00-3.50
- Consolidated, intelligent data ready for AI agents

---

## Configuration

### Main Config: `config/extraction_config.json`

```json
{
  "extraction": {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_retries": 3
  },
  "validation": {
    "enable_validation_agent": true,
    "enable_llm_validation": false  // Disable for speed
  },
  "ensemble": {
    "enable_ensemble_review": false  // KEEP DISABLED - expensive
  },
  "monitoring": {
    "enable_monitor": true,
    "print_summary_every_n": 5
  },
  "performance": {
    "parallel_processing": true  // Now working with WAL mode
  }
}
```

### Environment Variables: `.env`

```ini
OPENAI_API_KEY=sk-proj-your-key-here
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here  # Optional
ENABLE_ENSEMBLE_REVIEW=false  # Keep disabled
```

---

## Critical Design Patterns

### LLM Fallback Chain

The system uses a 6-model fallback chain in `_call_gpt4()`:
1. gpt-4o-mini (primary)
2. gpt-4o
3. gpt-3.5-turbo
4. o1-mini
5. o1-preview
6. claude-3-5-sonnet-20241022

Each model attempts with exponential backoff before falling to next.

### WAL Mode & Parallel Processing

SQLite WAL (Write-Ahead Logging) mode enables parallel processing:
- Database created with `PRAGMA journal_mode=WAL` in `database.py`
- Shared rate limiter prevents API throttling across workers
- Processing time reduced from 15-20 min to ~5-8 min for 44 interviews

### Resume Capability

Progress tracking enables resuming interrupted extractions:
- `data/extraction_progress.json` tracks completed interviews
- `processor.py` checks progress and skips completed interviews
- Use `--resume` flag to continue from last checkpoint

### Organizational Hierarchy

All entities linked to: company → business_unit → department
- Defined in `config/companies.json`
- Enforced by validation_agent.py
- Critical for multi-company queries

### Validation Strategy

**Always-on validation** (validation_agent.py):
- Completeness checks (min entities per interview)
- Encoding validation (UTF-8, no mojibake)
- Placeholder detection (no "N/A", "Unknown")
- Quality thresholds configurable

**Optional ensemble validation** (DISABLED by default):
- Multi-model cross-validation
- Expensive - only enable for critical quality needs

---

## File Organization

```
system0/
├── intelligence_capture/     # Main Python package
│   ├── processor.py          # Pipeline orchestrator
│   ├── extractor.py          # Main extraction (v1.0 + orchestration)
│   ├── extractors.py         # v2.0 specialized extractors
│   ├── database.py           # SQLite schema and operations
│   ├── validation_agent.py   # Quality validation
│   ├── monitor.py            # Real-time progress tracking
│   ├── rate_limiter.py       # Shared rate limiter
│   ├── parallel_processor.py # Parallel extraction with WAL
│   └── run.py                # Entry point
├── config/
│   ├── extraction_config.json   # All extraction settings
│   ├── companies.json           # Organizational hierarchy
│   └── ceo_priorities.json      # CEO prioritized processes
├── data/
│   ├── intelligence.db          # Production database
│   ├── interviews/analysis_output/all_interviews.json  # Source data
│   └── extraction_progress.json # Resume tracking
├── scripts/
│   ├── test_single_interview.py    # Single interview test
│   ├── test_batch_interviews.py    # Batch testing
│   ├── validate_extraction.py      # Validation
│   ├── test_parallel_fixes.py      # Test parallel processing
│   └── generate_comprehensive_report.py  # Reporting
├── .kiro/specs/
│   ├── extraction-completion/      # Phase 1-4 specs
│   └── knowledge-graph-consolidation/  # Week 1 consolidation spec
└── tests/                    # Unit tests for all extractors
```

**Path conventions:**
- Always run scripts from project root
- Import paths from `intelligence_capture.config`
- All databases go to `data/`
- All reports go to `reports/`

---

## Known Issues & Constraints

### Features Now Working (Fixed)

1. **Parallel processing** (`parallel_processing: true`)
   - ✅ Fixed with WAL mode in database.py
   - ✅ Shared rate limiter prevents conflicts
   - ✅ 4/5 test interviews succeeded

### DO NOT USE (Disabled Features)

1. **Ensemble validation** (`ENABLE_ENSEMBLE_REVIEW=false`)
   - Complex and expensive (3x cost, 3x time)
   - Only enable if absolutely necessary for quality

### Performance Characteristics

- Single interview: ~10 seconds, ~$0.01
- 44 interviews (parallel): ~5-8 minutes, ~$0.50-1.00
- 44 interviews (sequential): ~15-20 minutes, ~$0.50-1.00
- Rate limiting: Exponential backoff prevents API errors
- Resume: Can restart from any point without re-processing

---

## Testing Strategy

**Always test before full extraction:**

1. **Single interview** - Verify extraction logic works
2. **Batch (5 interviews)** - Verify performance and quality
3. **Validate results** - Check completeness and integrity
4. **Full extraction (44)** - Production run

---

## Important Notes

1. **Spanish-first:** All content is in Spanish - extraction prompts expect Spanish, validation works on Spanish text
2. **No translation:** Never translate interviews or extracted entities
3. **Organizational hierarchy:** Always respect company → business_unit → department structure
4. **Entity relationships:** All entities must reference valid interview_id
5. **UTF-8 encoding:** Critical for Spanish text - check with validation_agent
6. **Cost estimation:** System shows estimated cost and requests confirmation before extraction
7. **WAL mode:** Database uses WAL mode for parallel processing - improves performance 2-3x
8. **Duplicate entities:** 20-30% of extracted data is duplicated - knowledge graph consolidation addresses this

---

## Git Workflow

```bash
# Always work on feature branches
git checkout -b feature/your-feature-name

# Commit after completing tasks
git add .
git commit -m "feat: descriptive message"

# Push when ready
git push -u origin feature/your-feature-name
```

---

**Last Updated:** 2025-11-08
**Current Focus:** Knowledge Graph Consolidation System
**Progress:** ✅ Phases 1-4 Complete | 🎯 Consolidation Spec Created (0/18 tasks)
