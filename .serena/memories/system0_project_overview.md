# System0 Project Overview

## What This Project Does
Intelligence extraction system that processes 44 Spanish manager interviews and extracts structured business intelligence into a SQLite database with 17 entity types.

## Core Architecture

### Extraction Pipeline
```
Interview JSON → IntelligenceExtractor → 17 Entity Types → SQLite → Knowledge Graph → AI Agents
```

### Key Files
- `intelligence_capture/processor.py` - Main orchestrator (IntelligenceProcessor)
- `intelligence_capture/extractor.py` - Extraction coordinator (IntelligenceExtractor) 
- `intelligence_capture/extractors.py` - 13 specialized v2.0 extractors
- `intelligence_capture/database.py` - SQLite schema (IntelligenceDB, EnhancedIntelligenceDB)
- `intelligence_capture/validation_agent.py` - Quality validation
- `intelligence_capture/monitor.py` - Real-time progress tracking
- `intelligence_capture/rate_limiter.py` - Shared rate limiter for API calls

## 17 Entity Types

### v1.0 (6 types)
PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency

### v2.0 (11 types)
CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency, plus enhanced v1.0

## Important Design Patterns

### LLM Fallback Chain
6-model fallback in `_call_gpt4()`:
1. gpt-4o-mini (primary)
2. gpt-4o
3. gpt-3.5-turbo
4. o1-mini
5. o1-preview
6. claude-3-5-sonnet-20241022

### WAL Mode for Parallel Processing
- Database uses `PRAGMA journal_mode=WAL` for concurrent writes
- Shared rate limiter prevents API throttling
- Reduces processing from 15-20 min to 5-8 min

### Resume Capability
- `data/extraction_progress.json` tracks completed interviews
- `processor.py` skips completed interviews
- Use `--resume` flag

### Organizational Hierarchy
All entities: company → business_unit → department
- Defined in `config/companies.json`
- Enforced by validation_agent.py

## Critical Constraints

### Spanish-First
- All interviews in Spanish - NEVER translate
- Extraction prompts expect Spanish
- Validation works on Spanish text
- UTF-8 encoding critical

### Disabled Features
- Ensemble validation: expensive (3x cost, 3x time) - keep `ENABLE_ENSEMBLE_REVIEW=false`

### Known Issues
- 20-30% duplicate entities (addressed by knowledge graph consolidation)

## Testing Commands

```bash
# Single interview (~10 sec, ~$0.01)
python scripts/test_single_interview.py

# Batch test (~2-3 min, ~$0.10)
python scripts/test_batch_interviews.py --batch-size 5

# Full extraction (~5-8 min parallel, ~$0.50-1.00)
python intelligence_capture/run.py

# Resume interrupted
python intelligence_capture/run.py --resume
```

## Path Conventions
- Run scripts from project root
- Import from `intelligence_capture.config`
- Databases → `data/`
- Reports → `reports/`
- Specs → `.kiro/specs/`
