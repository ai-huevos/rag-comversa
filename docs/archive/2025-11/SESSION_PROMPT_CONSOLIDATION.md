# Knowledge Graph Consolidation - Next Session Prompt

## Context

You are continuing development of the **Knowledge Graph Consolidation System** for an Intelligence Capture platform. This system transforms fragmented entity data (e.g., 25 duplicate "Excel" entries) into consolidated, consensus-driven intelligence (1 "Excel" entity with 25 sources).

**Current Status**: Task 0 (Database Path Cleanup) is complete and merged into main. All database paths now follow SOLID principles with a single source of truth.

**Current Branch**: `feature/kg-consolidation-schema`

## Project Overview

**Goal**: Reduce duplicate entities by 80-95% while maintaining source tracking and consensus confidence scoring.

**Example**: 
- Before: 48 separate "Excel" entities (one per interview)
- After: 1 consolidated "Excel" entity with `source_count=48`, `mentioned_in_interviews=[1,2,3...]`, `consensus_confidence=0.95`

## Architecture Principles (CRITICAL)

### SOLID Principles - MUST FOLLOW

1. **Single Responsibility Principle (SRP)**
   - Each class has ONE reason to change
   - Database operations ONLY in `database.py`
   - Configuration ONLY in `config.py`
   - Business logic separated from infrastructure

2. **Open/Closed Principle (OCP)**
   - Classes open for extension, closed for modification
   - Use dependency injection for flexibility
   - Accept parameters instead of hardcoding values

3. **Liskov Substitution Principle (LSP)**
   - All database instances follow same interface
   - Subclasses can replace parent classes without breaking code

4. **Interface Segregation Principle (ISP)**
   - Clean separation between database operations and business logic
   - Classes don't depend on methods they don't use

5. **Dependency Inversion Principle (DIP)**
   - Depend on abstractions (config constants), not concrete implementations
   - High-level modules don't depend on low-level modules

### Code Quality Standards

- ✅ **Import from config**: Always use `from intelligence_capture.config import DB_PATH`
- ✅ **Dependency injection**: Classes accept `db_path` parameter
- ✅ **CLI arguments**: Scripts accept `--db-path` for flexibility
- ✅ **No hardcoding**: Never use `Path("data/...")` outside config.py
- ✅ **Validation**: Run `python3 scripts/validate_database_paths.py` before committing
- ✅ **Minimal code**: Write ONLY what's needed, avoid over-engineering
- ✅ **Test as you go**: Verify each component works before moving to next

## Next Tasks (Phase 1: Foundation & Schema)

### Task 1: Create Database Schema for Consolidation
**Status**: Not started
**Priority**: HIGH

**Objective**: Add consolidation tracking columns to all 17 entity tables and create 3 new tables (relationships, consolidation_audit, patterns).

**Implementation Requirements**:

1. **Modify `intelligence_capture/database.py`**:
   - Add method `add_consolidation_schema()` to `EnhancedIntelligenceDB` class
   - Use `_add_column_if_not_exists()` pattern (already exists in codebase)
   - Follow existing schema patterns (see `init_v2_schema()` for reference)

2. **Add columns to ALL entity tables** (17 tables):
   ```python
   # Consolidation tracking columns
   mentioned_in_interviews  # TEXT/JSON - list of interview IDs
   source_count            # INTEGER DEFAULT 1 - how many interviews mention this
   consensus_confidence    # REAL DEFAULT 1.0 - confidence score 0.0-1.0
   is_consolidated         # BOOLEAN DEFAULT false - has been merged
   has_contradictions      # BOOLEAN DEFAULT false - conflicting data found
   contradiction_details   # TEXT/JSON - details of contradictions
   merged_entity_ids       # TEXT/JSON - IDs of entities merged into this one
   first_mentioned_date    # TEXT - first interview date
   last_mentioned_date     # TEXT - most recent interview date
   consolidated_at         # TIMESTAMP - when consolidation happened
   ```

3. **Create 3 new tables**:

   **relationships table**:
   ```sql
   CREATE TABLE IF NOT EXISTS relationships (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       source_entity_id INTEGER NOT NULL,
       source_entity_type TEXT NOT NULL,
       relationship_type TEXT NOT NULL,
       target_entity_id INTEGER NOT NULL,
       target_entity_type TEXT NOT NULL,
       strength REAL DEFAULT 0.8,
       mentioned_in_interviews TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   ```

   **consolidation_audit table**:
   ```sql
   CREATE TABLE IF NOT EXISTS consolidation_audit (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       entity_type TEXT NOT NULL,
       merged_entity_ids TEXT NOT NULL,
       resulting_entity_id INTEGER NOT NULL,
       similarity_score REAL NOT NULL,
       consolidation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       rollback_timestamp TIMESTAMP,
       rollback_reason TEXT
   )
   ```

   **patterns table**:
   ```sql
   CREATE TABLE IF NOT EXISTS patterns (
       id INTEGER PRIMARY KEY AUTOINCREMENT,
       pattern_type TEXT NOT NULL,
       entity_type TEXT NOT NULL,
       entity_id INTEGER NOT NULL,
       pattern_frequency REAL NOT NULL,
       source_count INTEGER NOT NULL,
       high_priority BOOLEAN DEFAULT false,
       description TEXT,
       detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
   ```

4. **Create indexes for performance**:
   ```python
   # Relationship indexes
   CREATE INDEX IF NOT EXISTS idx_relationships_source ON relationships(source_entity_id, source_entity_type)
   CREATE INDEX IF NOT EXISTS idx_relationships_target ON relationships(target_entity_id, target_entity_type)
   
   # Audit indexes
   CREATE INDEX IF NOT EXISTS idx_audit_entity_type ON consolidation_audit(entity_type)
   CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON consolidation_audit(consolidation_timestamp)
   
   # Pattern indexes
   CREATE INDEX IF NOT EXISTS idx_patterns_type ON patterns(pattern_type)
   CREATE INDEX IF NOT EXISTS idx_patterns_priority ON patterns(high_priority)
   
   # Entity name indexes for duplicate detection
   CREATE INDEX IF NOT EXISTS idx_pain_points_description ON pain_points(description)
   CREATE INDEX IF NOT EXISTS idx_systems_name ON systems(name)
   CREATE INDEX IF NOT EXISTS idx_processes_name ON processes(name)
   ```

5. **Create migration script** at `intelligence_capture/migrations/add_consolidation_fields.py`:
   - Standalone script that can be run independently
   - Backs up database before migration
   - Uses transactions for safety
   - Validates migration success
   - Follows this pattern:
   ```python
   #!/usr/bin/env python3
   """
   Migration: Add Consolidation Fields
   Adds consolidation tracking columns to all entity tables
   """
   import sys
   from pathlib import Path
   sys.path.insert(0, str(Path(__file__).parent.parent.parent))
   
   from intelligence_capture.database import EnhancedIntelligenceDB
   from intelligence_capture.config import DB_PATH
   
   def main():
       # Implementation here
       pass
   
   if __name__ == "__main__":
       main()
   ```

**Testing Requirements**:
- Run migration on test database first
- Verify all columns added successfully
- Verify indexes created
- Verify backward compatibility (existing queries still work)
- Run `python3 scripts/validate_database_paths.py` to ensure compliance

**Requirements Reference**: 8.1, 8.2, 8.3, 8.4, 8.5

---

### Task 2: Create Consolidation Configuration
**Status**: Not started
**Priority**: HIGH

**Objective**: Create `config/consolidation_config.json` with similarity thresholds and consolidation parameters.

**Implementation Requirements**:

1. **Create `config/consolidation_config.json`**:
   ```json
   {
     "similarity_thresholds": {
       "pain_points": 0.80,
       "processes": 0.85,
       "systems": 0.85,
       "kpis": 0.90,
       "automation_candidates": 0.85,
       "inefficiencies": 0.80,
       "communication_channels": 0.85,
       "decision_points": 0.85,
       "data_flows": 0.85,
       "temporal_patterns": 0.80,
       "failure_modes": 0.80,
       "team_structures": 0.85,
       "knowledge_gaps": 0.80,
       "success_patterns": 0.80,
       "budget_constraints": 0.85,
       "external_dependencies": 0.85,
       "default": 0.85
     },
     "similarity_weights": {
       "semantic_weight": 0.3,
       "name_weight": 0.7
     },
     "consensus_parameters": {
       "source_count_divisor": 10,
       "agreement_bonus": 0.1,
       "max_bonus": 0.3,
       "contradiction_penalty": 0.15
     },
     "pattern_thresholds": {
       "recurring_pain_threshold": 3,
       "problematic_system_threshold": 5,
       "high_priority_frequency": 0.30
     },
     "performance": {
       "max_candidates": 10,
       "batch_size": 100,
       "enable_caching": true
     }
   }
   ```

2. **Add config loader to `intelligence_capture/config.py`**:
   ```python
   def load_consolidation_config(config_path: Path = None) -> dict:
       """Load consolidation configuration from JSON file"""
       if config_path is None:
           config_path = PROJECT_ROOT / "config" / "consolidation_config.json"
       
       # Load and return config
       # Include validation
       pass
   ```

**Testing Requirements**:
- Verify JSON is valid
- Verify all required keys present
- Test config loader function
- Verify thresholds are reasonable (0.0-1.0)

**Requirements Reference**: 14.1, 14.2, 14.3, 14.4

---

### Task 3: Run Database Migration
**Status**: Not started (depends on Task 1)
**Priority**: HIGH

**Objective**: Execute migration script to add consolidation columns to production database.

**Implementation Requirements**:

1. **Backup database first**:
   ```bash
   cp data/full_intelligence.db data/full_intelligence_backup_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Run migration**:
   ```bash
   python3 intelligence_capture/migrations/add_consolidation_fields.py
   ```

3. **Verify migration**:
   - Check all columns added
   - Check all tables created
   - Check all indexes created
   - Run existing queries to verify backward compatibility

4. **Test with pilot database**:
   ```bash
   python3 intelligence_capture/migrations/add_consolidation_fields.py --db-path data/pilot_intelligence.db
   ```

**Testing Requirements**:
- Test on pilot database first
- Verify schema with `PRAGMA table_info(table_name)`
- Run validation queries
- Ensure no data loss
- Verify performance (indexes working)

**Requirements Reference**: 8.1, 8.2, 8.3, 8.4, 8.5

---

## File Organization (CRITICAL)

Follow the project structure strictly:

```
intelligence_capture/
├── database.py              # Add consolidation schema methods here
├── config.py                # Add consolidation config loader here
└── migrations/              # Create this directory
    └── add_consolidation_fields.py

config/
└── consolidation_config.json  # Create this file

scripts/
└── validate_database_paths.py  # Run this before committing
```

**Rules**:
- ✅ All Python modules in `intelligence_capture/`
- ✅ All configuration in `config/`
- ✅ All scripts in `scripts/`
- ✅ All documentation in `docs/`
- ✅ Never create files in project root (except allowed files)

## Git Workflow

### Before Starting
```bash
git status                    # Verify on feature/kg-consolidation-schema
git pull origin main          # Get latest changes
```

### During Development
```bash
# After completing each task
git add -A
git commit -m "feat(task-N): Brief description

- Bullet point of what was done
- Another change
- Reference to requirements

Task N complete"

git push origin feature/kg-consolidation-schema
```

### After Completing Phase 1
```bash
# Merge into main
git checkout main
git pull origin main
git merge feature/kg-consolidation-schema
git push origin main

# Clean up
git branch -D feature/kg-consolidation-schema
git push origin --delete feature/kg-consolidation-schema
```

## Validation Checklist

Before committing ANY code:

- [ ] Run `python3 scripts/validate_database_paths.py` - must pass
- [ ] No hardcoded database paths (use config imports)
- [ ] All classes accept `db_path` parameter (dependency injection)
- [ ] All scripts accept `--db-path` CLI argument
- [ ] Code follows SOLID principles
- [ ] Minimal implementation (no over-engineering)
- [ ] Tests pass (if applicable)
- [ ] Documentation updated (if needed)

## Common Pitfalls to Avoid

❌ **DON'T**:
- Hardcode database paths: `Path("data/intelligence.db")`
- Use `sqlite3.connect()` directly (use `IntelligenceDB` classes)
- Create files in project root
- Over-engineer solutions
- Skip validation checks
- Commit without testing

✅ **DO**:
- Import from config: `from intelligence_capture.config import DB_PATH`
- Use dependency injection: `def __init__(self, db_path: Path = DB_PATH)`
- Follow existing patterns in codebase
- Write minimal, focused code
- Test incrementally
- Run validation before committing

## Success Criteria

Phase 1 is complete when:

1. ✅ All 17 entity tables have consolidation columns
2. ✅ 3 new tables created (relationships, consolidation_audit, patterns)
3. ✅ All indexes created for performance
4. ✅ Migration script works on test database
5. ✅ Migration script works on production database
6. ✅ Consolidation config file created and validated
7. ✅ Config loader function implemented
8. ✅ All validation checks pass
9. ✅ Backward compatibility maintained
10. ✅ Documentation updated

## Reference Documents

- **Requirements**: `.kiro/specs/knowledge-graph-consolidation/requirements.md`
- **Design**: `.kiro/specs/knowledge-graph-consolidation/design.md`
- **Tasks**: `.kiro/specs/knowledge-graph-consolidation/tasks.md`
- **Database Strategy**: `docs/DATABASE_STRATEGY.md`
- **Project Structure**: `PROJECT_STRUCTURE.md`

## Quick Start Command

```bash
# Verify you're on the right branch
git branch --show-current  # Should show: feature/kg-consolidation-schema

# Start with Task 1
# Read the requirements and design documents first
# Then implement the database schema changes
```

## Questions to Ask Yourself

Before writing code:
1. Does this follow SOLID principles?
2. Am I importing from config instead of hardcoding?
3. Does this class accept db_path as a parameter?
4. Is this the minimal implementation needed?
5. Have I looked at existing patterns in the codebase?
6. Will this pass the validation script?

## Final Notes

- **Focus on one task at a time** - Complete Task 1 fully before moving to Task 2
- **Test incrementally** - Don't wait until the end to test
- **Follow existing patterns** - Look at how `init_v2_schema()` works
- **Keep it simple** - Minimal code that solves the problem
- **Validate often** - Run validation script frequently
- **Commit frequently** - Small, focused commits with clear messages

**Remember**: The goal is to build a solid foundation for the consolidation system. Quality over speed. SOLID principles are non-negotiable.

Good luck! 🚀
