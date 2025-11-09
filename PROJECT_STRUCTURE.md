# Project Structure Guide

## Current Folder Organization

```
system0/
├── .env                          # Environment variables (API keys, config)
├── .gitignore                    # Git ignore rules
├── README.md                     # Main project documentation
├── NEXT_STEPS.md                 # Deployment guide
├── PROJECT_STRUCTURE.md          # This file
│
├── .kiro/                        # Kiro IDE configuration
│   └── specs/                    # Project specifications
│       ├── extraction-completion/
│       │   ├── requirements.md   # Extraction system requirements
│       │   ├── design.md         # Extraction system design
│       │   └── tasks.md          # Extraction tasks
│       ├── ontology-enhancement/
│       │   ├── requirements.md   # Ontology enhancement requirements
│       │   ├── design.md         # Ontology design
│       │   └── tasks.md          # Ontology tasks
│       └── knowledge-graph-consolidation/
│           ├── requirements.md   # Consolidation requirements (NEW)
│           ├── design.md         # Consolidation design (NEW)
│           └── tasks.md          # Consolidation tasks (18 tasks) (NEW)
│
├── config/                       # Configuration files
│   ├── companies.json            # Company hierarchy definitions
│   ├── ceo_priorities.json       # CEO prioritized macroprocesos
│   ├── extraction_config.json    # Extraction configuration
│   └── consolidation_config.json # Consolidation configuration (NEW)
│
├── data/                         # All data files (databases, interviews)
│   ├── intelligence.db           # Main database (created by run.py)
│   ├── full_intelligence.db      # Full extraction database
│   ├── pilot_intelligence.db     # Pilot extraction database
│   ├── fast_intelligence.db      # Fast extraction database
│   ├── extraction_progress.json  # Progress tracking
│   ├── company_info/             # Company information
│   └── interviews/               # Interview data
│       └── analysis_output/
│           └── all_interviews.json  # 44 processed interviews
│
├── docs/                         # All documentation
│   ├── ENSEMBLE_QUICKSTART.md    # Quick start for ensemble validation
│   ├── ENSEMBLE_VALIDATION.md    # Full ensemble validation docs
│   ├── EXTRACTION_PIPELINE_GUIDE.md
│   ├── RAG_TESTING_GUIDE.md
│   ├── QUICK_REFERENCE.md
│   ├── AI_AGENTS_EXPLAINED.md
│   ├── COMPLETE_SYSTEM_OVERVIEW.md
│   ├── FINDINGS_ANALYSIS.md
│   ├── INTELLIGENCE_SYSTEM_SUMMARY.md
│   ├── LANGUAGE_STRATEGY.md
│   ├── LLM_FALLBACK_SYSTEM.md
│   ├── ONTOLOGY_BRAINSTORM.md
│   ├── ONTOLOGY_COMPARISON.md
│   ├── PHASE1_EXECUTIVE_SUMMARY.md
│   ├── PHASE1_SOP_PACK.md
│   ├── PROJECT_ORGANIZATION.md
│   ├── QUICK_START_GUIDE.md
│   ├── SETUP_INSTRUCTIONS.md
│   ├── SYSTEM_ARCHITECTURE_VISUAL.md
│   ├── WHAT_WE_BUILT.md
│   └── [other documentation files]
│
├── examples/                     # Example code
│   └── simple_rag_example.py
│
├── intelligence_capture/         # Main Python package
│   ├── __init__.py
│   ├── config.py                 # Configuration (paths, API keys)
│   ├── database.py               # Database operations
│   ├── extractor.py              # Entity extraction logic
│   ├── extractors.py             # Additional extractors
│   ├── processor.py              # Main processing orchestrator
│   ├── reviewer.py               # Ensemble validation system
│   ├── consolidation_agent.py    # Knowledge Graph consolidation (NEW)
│   ├── duplicate_detector.py     # Duplicate entity detection (NEW)
│   ├── entity_merger.py          # Entity merging logic (NEW)
│   ├── consensus_scorer.py       # Consensus confidence scoring (NEW)
│   ├── relationship_discoverer.py # Relationship discovery (NEW)
│   ├── pattern_recognizer.py     # Pattern recognition (NEW)
│   ├── rate_limiter.py           # Shared rate limiter
│   ├── rag_generator.py          # RAG database generation
│   ├── ceo_validator.py          # CEO assumption validation
│   ├── cross_company_analyzer.py # Cross-company analysis
│   ├── hierarchy_discoverer.py   # Org hierarchy discovery
│   ├── migrate_add_review_fields.py  # Database migration
│   ├── migrations/               # Database migrations (NEW)
│   │   └── add_consolidation_fields.py
│   ├── run.py                    # Main entry point
│   ├── requirements.txt          # Python dependencies
│   └── README.md
│
├── reports/                      # Generated reports (JSON, Excel)
│   ├── comprehensive_extraction_report.json
│   ├── full_extraction_report.json
│   └── analysis/                 # Analysis reports
│
├── scripts/                      # Utility scripts
│   ├── check_setup.py            # Verify setup
│   ├── demo_rag_system.py        # RAG system demo
│   ├── process_interviews.py     # Interview processing
│   ├── quick_rag_test.py         # Quick RAG test
│   ├── run_intelligence.sh       # Shell script runner
│   ├── setup.sh                  # Setup script
│   ├── show_structure.sh         # Show project structure
│   ├── pilot_extraction.py       # Pilot extraction (5 interviews)
│   ├── fast_extraction_pipeline.py   # Fast extraction
│   ├── full_extraction_pipeline.py   # Full extraction
│   ├── generate_extraction_report.py # Report generation
│   ├── monitor_extraction.py     # Monitor extraction progress
│   ├── test_consolidation.py     # Test consolidation (NEW)
│   ├── validate_consolidation.py # Validate consolidation (NEW)
│   └── generate_consolidation_report.py # Consolidation report (NEW)
│
├── tests/                        # Unit and integration tests
│   ├── test_automation_candidate_extraction.py
│   ├── test_ceo_validator.py
│   ├── test_communication_channel_extraction.py
│   ├── test_cross_company_analyzer.py
│   ├── test_data_flow_extraction.py
│   ├── test_database_schema.py
│   ├── test_decision_point_extraction.py
│   ├── test_embedding_generation.py
│   ├── test_entity_context_builder.py
│   ├── test_full_extraction_pipeline.py
│   ├── test_hierarchy_discoverer.py
│   ├── test_llm_fallback.py
│   ├── test_rag_databases.py
│   ├── test_real_interview_data.py
│   ├── test_remaining_entities.py
│   ├── test_system_extraction.py
│   ├── test_temporal_pattern_extraction.py
│   ├── test_duplicate_detector.py        # Consolidation tests (NEW)
│   ├── test_entity_merger.py             # Consolidation tests (NEW)
│   ├── test_consensus_scorer.py          # Consolidation tests (NEW)
│   ├── test_consolidation_agent.py       # Consolidation tests (NEW)
│   ├── test_relationship_discoverer.py   # Consolidation tests (NEW)
│   ├── test_pattern_recognizer.py        # Consolidation tests (NEW)
│   └── test_consolidation_integration.py # Consolidation tests (NEW)
│
└── venv/                         # Python virtual environment
```

## File Naming Conventions

### Databases (in `data/`)
- `intelligence.db` - Main production database
- `full_intelligence.db` - Full extraction with all entities
- `pilot_intelligence.db` - Pilot/test database
- `*_intelligence.db` - Other database variants

### Reports (in `reports/`)
- `*_report.json` - JSON format reports
- `*_report.xlsx` - Excel format reports
- `analysis/*.json` - Analysis outputs

### Documentation (in `docs/`)
- `*.md` - All markdown documentation
- Use UPPERCASE for major guides (e.g., `ENSEMBLE_QUICKSTART.md`)
- Use Title Case for specific docs (e.g., `Quick_Start_Guide.md`)

### Scripts (in `scripts/`)
- `*.py` - Python scripts
- `*.sh` - Shell scripts
- Use snake_case for filenames

## Path Configuration

All paths are configured in `intelligence_capture/config.py`:

```python
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "interviews" / "analysis_output"
DB_PATH = PROJECT_ROOT / "data" / "intelligence.db"
REPORTS_DIR = PROJECT_ROOT / "reports"
```

## Best Practices

### When Creating New Files

1. **Databases** → Always save to `data/`
2. **Reports** → Always save to `reports/`
3. **Documentation** → Always save to `docs/`
4. **Scripts** → Always save to `scripts/`
5. **Tests** → Always save to `tests/`

### When Writing Scripts

1. Import paths from `config.py`:
   ```python
   from config import DB_PATH, REPORTS_DIR
   ```

2. Or use relative paths from PROJECT_ROOT:
   ```python
   from pathlib import Path
   PROJECT_ROOT = Path(__file__).parent.parent
   DB_PATH = PROJECT_ROOT / "data" / "intelligence.db"
   ```

3. Always create parent directories:
   ```python
   output_path.parent.mkdir(parents=True, exist_ok=True)
   ```

### When Running Scripts

Always run from the project root:
```bash
# Good
python3 intelligence_capture/run.py
python3 scripts/generate_extraction_report.py

# Bad (don't cd into directories)
cd intelligence_capture && python3 run.py
```

## Migration Checklist

When adding new features that create files:

- [ ] Update `config.py` with new path constants
- [ ] Ensure files go to correct directories
- [ ] Update `.gitignore` if needed
- [ ] Document in this file
- [ ] Update `NEXT_STEPS.md` if user-facing

## Current Status

✅ All documentation moved to `docs/`
✅ All scripts moved to `scripts/`
✅ Database path updated to `data/intelligence.db`
✅ Reports directory configured in `config.py`
✅ Migration script updated
✅ Ensemble validation system integrated
✅ Parallel processing with WAL mode
✅ Rate limiting with exponential backoff
🎯 Knowledge Graph Consolidation spec created (ready to implement)

## Quick Reference

| What | Where | Example |
|------|-------|---------|
| Main database | `data/intelligence.db` | Production data |
| Interview data | `data/interviews/analysis_output/` | 44 interviews |
| Reports | `reports/` | JSON/Excel outputs |
| Documentation | `docs/` | All .md files |
| Scripts | `scripts/` | Utility scripts |
| Tests | `tests/` | Unit/integration tests |
| Config | `config/` | JSON configuration |
| Main code | `intelligence_capture/` | Python package |
