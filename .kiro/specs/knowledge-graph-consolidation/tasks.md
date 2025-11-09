# Implementation Plan: Knowledge Graph Consolidation System

## Overview

This implementation plan breaks down the Knowledge Graph Consolidation System into discrete, actionable coding tasks. Each task builds incrementally on previous work, with the goal of transforming fragmented entity data (25x Excel, 12x SAP) into consolidated, consensus-driven intelligence (1x Excel with 25 sources, 1x SAP with 12 sources).

**Current State Analysis:**
- ✅ Database schema exists with v1.0 and v2.0 entity tables
- ✅ Extraction pipeline fully functional
- ✅ Ensemble validation system in place
- ❌ No consolidation-specific columns (mentioned_in_interviews, source_count, etc.)
- ❌ No consolidation components (DuplicateDetector, EntityMerger, etc.)
- ❌ No consolidation configuration file
- ❌ No relationship or pattern tables

**Timeline**: 5 days
**Goal**: Reduce duplicate entities by 80-95% and enable accurate business intelligence queries

---

## Phase 1: Foundation & Schema

- [x] 0. Database Path Cleanup and SOLID Principles Enforcement
  - **Audit all database usage** - Review all scripts in `scripts/` and modules in `intelligence_capture/` to identify database path usage
  - **Standardize database paths** - Ensure all scripts use `DB_PATH` from `intelligence_capture/config.py` (currently points to `data/full_intelligence.db`)
  - **Apply Dependency Injection** - Modify all classes to accept `db_path` as constructor parameter instead of hardcoding paths
  - **Single Responsibility** - Ensure database connection logic stays in `database.py`, not scattered across scripts
  - **Update config.py** - Add clear documentation about which database is for what purpose:
    - `DB_PATH` = `data/full_intelligence.db` (production, 44 interviews)
    - `PILOT_DB_PATH` = `data/pilot_intelligence.db` (testing, 5 interviews)
    - `TEST_DB_PATH` = `data/test_intelligence.db` (unit tests, temporary)
  - **Fix scripts** - Update all scripts to:
    - Import `DB_PATH` from config instead of hardcoding
    - Accept `--db-path` CLI argument for flexibility
    - Default to `DB_PATH` if no argument provided
  - **Remove hardcoded paths** - Search for and eliminate any `sqlite3.connect("data/...")` or `IntelligenceDB("data/...")` patterns
  - **Add validation** - Create `scripts/validate_database_paths.py` to check all scripts use proper path management
  - **Document database strategy** - Update `docs/DATABASE_STRATEGY.md` with:
    - Which database to use for what purpose
    - How to properly reference databases in code
    - Migration strategy for consolidation
  - _Requirements: SOLID principles, maintainability, single source of truth_

- [ ] 1. Create Database Schema for Consolidation
  - Add consolidation migration method to `intelligence_capture/database.py`
  - Create migration script at `intelligence_capture/migrations/add_consolidation_fields.py`
  - Add columns to all entity tables: `mentioned_in_interviews` (TEXT/JSON), `source_count` (INTEGER DEFAULT 1), `consensus_confidence` (REAL DEFAULT 1.0), `is_consolidated` (BOOLEAN DEFAULT false), `has_contradictions` (BOOLEAN DEFAULT false), `contradiction_details` (TEXT/JSON), `merged_entity_ids` (TEXT/JSON), `first_mentioned_date` (TEXT), `last_mentioned_date` (TEXT), `consolidated_at` (TIMESTAMP)
  - Create `relationships` table with columns: id, source_entity_id, source_entity_type, relationship_type, target_entity_id, target_entity_type, strength, mentioned_in_interviews, created_at, updated_at
  - Create `consolidation_audit` table with columns: id, entity_type, merged_entity_ids, resulting_entity_id, similarity_score, consolidation_timestamp, rollback_timestamp, rollback_reason
  - Create `patterns` table with columns: id, pattern_type, entity_type, entity_id, pattern_frequency, source_count, high_priority, description, detected_at
  - Add indexes for performance: idx_relationships_source, idx_relationships_target, idx_audit_entity_type, idx_audit_timestamp, idx_patterns_type, idx_patterns_priority
  - Add indexes on entity name columns for fast duplicate detection
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 2. Create Consolidation Configuration
  - Create `config/consolidation_config.json` with similarity thresholds per entity type
  - Define thresholds: 0.85 default, 0.80 for pain_points/patterns, 0.90 for KPIs
  - Configure semantic vs name similarity weights (0.3 semantic, 0.7 name)
  - Set consensus confidence parameters (source_count_divisor: 10, agreement_bonus: 0.1, max_bonus: 0.3, contradiction_penalty: 0.15)
  - Configure pattern recognition thresholds (recurring_pain: 3, problematic_system: 5, high_priority_frequency: 0.30)
  - Add max_candidates limit (10) for performance
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [ ] 3. Run Database Migration
  - Execute migration script to add consolidation columns
  - Backup existing database before migration
  - Run ALTER TABLE statements for all entity tables
  - Create new tables (relationships, consolidation_audit, patterns)
  - Create indexes for performance
  - Verify migration success with schema inspection
  - Test backward compatibility (existing queries still work)
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

---

## Phase 2: Core Consolidation Components

- [ ] 4. Create DuplicateDetector Component
  - Create `intelligence_capture/duplicate_detector.py`
  - Implement `DuplicateDetector` class with `__init__(config: Dict)`
  - Implement `find_duplicates(entity, entity_type, existing_entities)` - returns list of (entity, similarity_score) tuples
  - Implement `calculate_name_similarity(name1, name2, entity_type)` - uses fuzzy matching (rapidfuzz or difflib) with entity-specific normalization
  - Implement `normalize_name(name, entity_type)` - removes common words ("sistema", "software" for systems; "problema de" for pain_points)
  - Implement `calculate_semantic_similarity(text1, text2)` - uses OpenAI embeddings + cosine similarity
  - Implement `_get_similarity_threshold(entity_type)` - reads from config
  - Cache embeddings to avoid redundant API calls
  - Return top 10 candidates sorted by similarity score
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ] 5. Create EntityMerger Component
  - Create `intelligence_capture/entity_merger.py`
  - Implement `EntityMerger` class with `merge(new_entity, existing_entity, interview_id)` method
  - Implement `combine_descriptions(desc1, desc2)` - concatenates unique sentences, removes duplicates
  - Implement `detect_contradictions(new_entity, existing_entity)` - compares attribute values (frequency, severity, etc.)
  - Implement `update_source_tracking(entity, interview_id)` - appends interview_id to mentioned_in_interviews, increments source_count
  - Implement `merge_attributes(new_attrs, existing_attrs)` - keeps most common value for conflicting attributes
  - Store merged_entity_ids for audit trail
  - Set is_consolidated = true on merged entity
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4_

- [ ] 6. Create ConsensusScorer Component
  - Create `intelligence_capture/consensus_scorer.py`
  - Implement `ConsensusScorer` class with `__init__(config: Dict)`
  - Implement `calculate_confidence(entity)` - returns float 0.0-1.0
  - Calculate base_score = min(source_count / 10, 1.0)
  - Calculate agreement_bonus = min(attribute_agreement_count * 0.1, 0.3)
  - Calculate contradiction_penalty = contradiction_count * 0.15
  - Return max(0.0, min(1.0, base_score + agreement_bonus - contradiction_penalty))
  - Implement `check_attribute_agreement(entity)` - counts attributes that agree across sources
  - Set needs_review = true if confidence < 0.6
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 7. Create KnowledgeConsolidationAgent
  - Create `intelligence_capture/consolidation_agent.py`
  - Implement `KnowledgeConsolidationAgent` class with `__init__(db: IntelligenceDB, config: Dict)`
  - Initialize DuplicateDetector, EntityMerger, ConsensusScorer components
  - Implement `consolidate_entities(entities, interview_id)` - main entry point
  - For each entity type, call `_consolidate_entity_type(entity_list, entity_type, interview_id)`
  - Implement `find_similar_entities(entity, entity_type)` - queries database for existing entities, calls DuplicateDetector
  - Implement `merge_entities(new_entity, existing_entity, similarity_score)` - calls EntityMerger, updates database
  - Implement `calculate_consensus_confidence(entity)` - calls ConsensusScorer
  - Log all merge decisions with similarity scores to consolidation_audit table
  - Return consolidated entities dict
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

---

## Phase 3: Database Integration

- [ ] 8. Update Database Storage Methods
  - Modify `intelligence_capture/database.py`
  - Update all `insert_*` methods to check if entity already exists
  - If entity exists and is_consolidated = true, call `update_consolidated_entity()` instead of insert
  - Implement `update_consolidated_entity(entity_type, entity_id, new_data, interview_id)` - updates source tracking, recalculates confidence
  - Implement `insert_relationship(relationship)` - inserts into relationships table
  - Implement `insert_consolidation_audit(audit_record)` - inserts into consolidation_audit table
  - Add transaction support for atomic consolidation operations
  - Add `get_entities_by_type(entity_type, limit=None)` for duplicate detection queries
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 9. Integrate Consolidation into Processor
  - Modify `intelligence_capture/processor.py`
  - Import KnowledgeConsolidationAgent
  - Initialize consolidation_agent in `__init__` if config.consolidation.enabled = true
  - In `process_interview()`, after extraction, call `consolidation_agent.consolidate_entities(entities, interview_id)`
  - Store consolidated entities instead of raw entities
  - Add consolidation timing metrics to processing report
  - Handle consolidation errors gracefully (log and continue with raw entities if consolidation fails)
  - Add consolidation status to extraction progress tracking
  - _Requirements: 9.1, 9.2, 9.3, 9.4_

---

## Phase 4: Relationship Discovery & Pattern Recognition

- [ ] 10. Create RelationshipDiscoverer Component
  - Create `intelligence_capture/relationship_discoverer.py`
  - Implement `RelationshipDiscoverer` class with `__init__(db: IntelligenceDB)`
  - Implement `discover_relationships(entities, interview_id)` - returns list of relationship dicts
  - Implement `_find_system_pain_relationships(systems, pain_points, interview_id)` - detects System → causes → Pain Point
  - Implement `_find_process_system_relationships(processes, systems, interview_id)` - detects Process → uses → System
  - Check for entity name mentions in descriptions (case-insensitive)
  - Set relationship strength based on mention clarity (0.8 for explicit, 0.6 for implicit)
  - Store relationships with mentioned_in_interviews tracking
  - Prevent duplicate relationships
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 11. Integrate Relationship Discovery
  - Modify `intelligence_capture/consolidation_agent.py`
  - Import RelationshipDiscoverer
  - Initialize relationship_discoverer in `__init__`
  - In `consolidate_entities()`, after entity consolidation, call `relationship_discoverer.discover_relationships()`
  - Store discovered relationships in database via `db.insert_relationship()`
  - Update existing relationships if same relationship found in multiple interviews
  - Log relationship discovery metrics
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 12. Create PatternRecognizer Component
  - Create `intelligence_capture/pattern_recognizer.py`
  - Implement `PatternRecognizer` class with `__init__(db: IntelligenceDB, config: Dict)`
  - Implement `identify_patterns()` - main entry point, returns list of pattern dicts
  - Implement `find_recurring_pain_points(threshold=3)` - queries pain_points with source_count >= threshold
  - Implement `find_problematic_systems(threshold=5)` - queries systems with negative sentiment in threshold+ interviews
  - Calculate pattern_frequency = source_count / total_interviews
  - Set high_priority = true if pattern_frequency >= 0.30
  - Store patterns in patterns table
  - Return patterns sorted by frequency and priority
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

---

## Phase 5: Testing & Validation

- [ ] 13. Create Consolidation Test Suite
  - Create `tests/test_duplicate_detector.py` - test fuzzy matching, name normalization, semantic similarity
  - Create `tests/test_entity_merger.py` - test description combination, contradiction detection, source tracking
  - Create `tests/test_consensus_scorer.py` - test confidence calculation with various source counts
  - Create `tests/test_consolidation_agent.py` - test end-to-end consolidation
  - Create `tests/test_relationship_discoverer.py` - test relationship discovery
  - Create `tests/test_pattern_recognizer.py` - test pattern detection
  - Use pytest fixtures for test data
  - Mock database calls where appropriate
  - _Requirements: All requirements (validation)_

- [ ] 14. Create Integration Test with Sample Data
  - Create `tests/test_consolidation_integration.py`
  - Create `scripts/test_consolidation.py`
  - Create test database with 5 sample interviews containing known duplicates (3x Excel, 2x SAP)
  - Run full extraction + consolidation pipeline
  - Verify duplicate reduction (5 entities → 2 consolidated entities)
  - Verify source tracking (Excel has 3 sources, SAP has 2 sources)
  - Verify consensus confidence scores calculated correctly
  - Verify relationships discovered (at least 2 relationships)
  - Verify patterns identified (at least 1 recurring pattern)
  - Generate consolidation report with before/after metrics
  - Assert: duplicate_reduction_percentage >= 50%
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 15. Create Consolidation Validation Script
  - Create `scripts/validate_consolidation.py`
  - Implement `validate_consolidation(db_path)` - runs all validation checks
  - Check: all entities have source_count >= 1
  - Check: all entities have consensus_confidence between 0.0 and 1.0
  - Check: mentioned_in_interviews contains valid interview IDs
  - Check: no orphaned relationships (all targets exist)
  - Check: duplicate reduction achieved (entities_after < entities_before)
  - Generate consolidation_report.json with metrics
  - List top 10 most-mentioned entities by source_count
  - List all entities with has_contradictions = true
  - Print summary to console with color-coded status
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 16. Test with 10 Interviews
  - Run `scripts/test_consolidation.py --interviews 10`
  - Select 10 diverse interviews (different companies, roles)
  - Run extraction + consolidation pipeline
  - Measure processing time (target: <2 minutes)
  - Verify duplicate reduction (expect 70-90% reduction)
  - Verify average consensus_confidence >= 0.70
  - Verify relationships discovered (expect 20+ relationships)
  - Verify patterns identified (expect 3+ recurring patterns)
  - Generate detailed consolidation report
  - Review entities with contradictions (expect <10%)
  - Validate all database integrity checks pass
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 12.1, 12.2, 12.3, 12.4, 12.5_

---

## Phase 6: Reporting & Documentation

- [ ] 17. Create Consolidation Dashboard
  - Create `scripts/generate_consolidation_report.py`
  - Generate HTML report with consolidation metrics
  - Show before/after entity counts per type (bar chart)
  - Show top 10 most-mentioned entities (table)
  - Show consensus confidence distribution (histogram)
  - Show relationship graph (System → Pain Point connections)
  - Show recurring patterns (sorted by frequency)
  - Show entities with contradictions (table with details)
  - Export report as HTML and JSON
  - Include timestamp and database path in report
  - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

- [ ] 18. Update Documentation
  - Update `CLAUDE.MD` - add consolidation status
  - Update `PROJECT_STRUCTURE.md` - add consolidation components
  - Create `docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md` - comprehensive guide with overview, architecture, usage guide, configuration options, troubleshooting
  - Include example queries for consolidated data
  - Document relationship types and pattern types
  - Add consolidation metrics to success criteria
  - _Requirements: All requirements (documentation)_

---

## Success Metrics

After completing all tasks, the system should achieve:

- ✅ **Duplicate Reduction**: 80-95% reduction in duplicate entities (48 → 3 for systems)
- ✅ **Source Tracking**: All consolidated entities have mentioned_in_interviews and source_count
- ✅ **Consensus Confidence**: Average confidence >= 0.75 across all entity types
- ✅ **Contradictions**: <10% of entities flagged with has_contradictions
- ✅ **Relationships**: System → Pain Point and Process → System relationships discovered
- ✅ **Patterns**: Recurring patterns identified (mentioned in 30%+ of interviews)
- ✅ **Performance**: Consolidation completes in <5 minutes for 44 interviews
- ✅ **Quality**: All validation checks pass (no orphaned relationships, valid interview IDs)

---

## Task Execution Order

**Phase 1**: Tasks 1-3 (Foundation & Schema)
**Phase 2**: Tasks 4-7 (Core Components)
**Phase 3**: Tasks 8-9 (Database Integration)
**Phase 4**: Tasks 10-12 (Relationships & Patterns)
**Phase 5**: Tasks 13-16 (Testing & Validation)
**Phase 6**: Tasks 17-18 (Reporting & Documentation)

**Total**: 19 tasks (includes database cleanup task 0)
