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

---

## Phase 7: Production Hardening - Critical Security Fixes

- [ ] 19. Fix SQL Injection Vulnerability
  - Add VALID_ENTITY_TYPES constant to `intelligence_capture/database.py` with all 17 entity types
  - Update `update_consolidated_entity()` method to validate entity_type against whitelist before SQL query
  - Raise ValueError with descriptive message if invalid entity_type provided
  - Add similar validation to all methods that accept entity_type parameter: `get_entities_by_type()`, `insert_entity()`, etc.
  - Add unit tests for entity type validation (test valid types pass, invalid types raise ValueError)
  - _Requirements: 16.1, 16.2, 16.3_

- [ ] 20. Implement Transaction Management
  - Update `intelligence_capture/consolidation_agent.py` - wrap `consolidate_entities()` in transaction
  - Add `self.db.conn.execute("BEGIN TRANSACTION")` at start of consolidation
  - Add `self.db.conn.commit()` after successful consolidation
  - Add try/except block with `self.db.conn.rollback()` on any exception
  - Log all transaction rollbacks with error details
  - Add transaction support to `merge_entities()` method
  - Test transaction rollback with simulated failures
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [ ] 21. Implement API Failure Resilience
  - Update `intelligence_capture/duplicate_detector.py` - add retry logic to `_get_embedding()`
  - Implement exponential backoff: sleep(2 ** attempt) for attempts 0, 1, 2
  - Add max_retries parameter (default 3) to `_get_embedding()`
  - Create custom EmbeddingError exception class
  - Raise EmbeddingError after max retries exceeded with full error details
  - Log all API failures to consolidation audit trail
  - Implement circuit breaker: disable semantic similarity after 10 consecutive failures
  - Add fallback to fuzzy-only matching when embeddings unavailable
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5_

---

## Phase 8: Production Hardening - Performance Optimization

- [ ] 22. Add Embedding Storage to Database Schema
  - Update `intelligence_capture/migrations/add_consolidation_fields.py`
  - Add `embedding_vector BLOB` column to all 17 entity tables
  - Create index on embedding_vector for faster lookups (if supported by SQLite)
  - Add `update_entity_embedding(entity_type, entity_id, embedding)` method to database.py
  - Add `get_entity_embedding(entity_type, entity_id)` method to database.py
  - Run migration to add embedding_vector columns
  - _Requirements: 19.1, 19.2_

- [ ] 23. Implement Embedding Pre-computation and Storage
  - Update `intelligence_capture/duplicate_detector.py` - store embeddings when generated
  - Modify `_get_embedding()` to check database for existing embedding before API call
  - If embedding exists in database, return it (cache hit)
  - If embedding doesn't exist, generate via API and store in database
  - Create `scripts/precompute_embeddings.py` - batch generate embeddings for existing entities
  - Script should process all entity types, generate embeddings, store in database
  - Add progress bar for batch embedding generation
  - Log cache hit rate (hits / total requests) for monitoring
  - _Requirements: 19.3, 19.4, 19.5_

- [ ] 24. Implement Fuzzy-First Candidate Filtering
  - Update `intelligence_capture/duplicate_detector.py` - modify `find_duplicates()` algorithm
  - Stage 1: Use fuzzy matching to get top 10 candidates above threshold
  - Stage 2: Only compute semantic similarity for those 10 candidates (not all entities)
  - Skip semantic similarity if fuzzy score >= 0.95 (obvious duplicate)
  - Add rapidfuzz to `intelligence_capture/requirements.txt` (10-100x faster than difflib)
  - Update `calculate_name_similarity()` to prefer rapidfuzz over difflib
  - Log candidate filtering metrics: total_entities, candidates_after_fuzzy, semantic_calls_made
  - Verify 90-95% reduction in API calls compared to naive approach
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [ ] 25. Optimize Database Queries with Indexes
  - Update `intelligence_capture/migrations/add_consolidation_fields.py`
  - Add index on name column for all entity tables: `CREATE INDEX idx_{entity_type}_name ON {entity_type}(name)`
  - Add index on source_count for pattern queries: `CREATE INDEX idx_{entity_type}_source_count ON {entity_type}(source_count)`
  - Add index on consensus_confidence for quality filtering: `CREATE INDEX idx_{entity_type}_confidence ON {entity_type}(consensus_confidence)`
  - Add index on is_consolidated for consolidation queries: `CREATE INDEX idx_{entity_type}_consolidated ON {entity_type}(is_consolidated)`
  - Run migration to create all indexes
  - Verify query performance improvement with EXPLAIN QUERY PLAN
  - _Requirements: 10.2, 10.3_

---

## Phase 9: Production Hardening - Code Quality

- [ ] 26. Implement Structured Logging Framework
  - Create `intelligence_capture/logger.py` - configure Python logging framework
  - Set up rotating file handler: logs/consolidation.log with 10MB max size, 5 backups
  - Set up console handler with color-coded output (colorlog library)
  - Configure log format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
  - Replace all print() statements in consolidation_agent.py with logger.info/warning/error
  - Replace all print() statements in duplicate_detector.py with logger calls
  - Replace all print() statements in entity_merger.py with logger calls
  - Replace all print() statements in consensus_scorer.py with logger calls
  - Add DEBUG level logging for detailed tracing (similarity scores, merge decisions)
  - Add INFO level logging for normal operations (entity consolidated, duplicates found)
  - Add WARNING level logging for recoverable issues (API retry, low confidence)
  - Add ERROR level logging for failures (transaction rollback, API failure)
  - _Requirements: 21.1, 21.2, 21.3, 21.4, 21.5_

- [ ] 27. Improve Contradiction Detection Logic
  - Update `intelligence_capture/entity_merger.py` - fix `detect_contradictions()` method
  - Check ALL attributes (union of both entities), not just common ones
  - Handle missing values correctly: new info vs no info vs contradiction
  - Implement `_calculate_value_similarity()` with fuzzy matching for text values
  - Use configurable similarity threshold (default 0.7) for contradiction detection
  - Store contradiction details with similarity scores and source interview IDs
  - Handle Spanish punctuation and domain-specific synonyms
  - Add unit tests for contradiction detection with various scenarios
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 28. Improve Entity Text Extraction
  - Update `intelligence_capture/duplicate_detector.py` - fix `_get_entity_text()` method
  - Combine name AND description for better semantic matching (not just name)
  - Truncate description to 200 chars to avoid overwhelming name
  - Join with space: `f"{name} {description[:200]}"`
  - Handle missing fields gracefully (empty string if both missing)
  - Add unit tests for text extraction with various entity structures
  - _Requirements: 1.4, 1.5_

- [ ] 29. Fix Consensus Scoring Formula
  - Update `intelligence_capture/consensus_scorer.py` - fix `calculate_confidence()` method
  - Adjust source_count_divisor based on total interviews: `min(config_divisor, total_interviews / 4)`
  - For 44 interviews, use divisor of 5 (20% = 1.0 confidence) instead of 10
  - Implement `_calculate_actual_agreement()` - check actual value agreement, not just non-empty fields
  - Add single_source_penalty of 0.3 for entities with source_count = 1
  - Increase contradiction_penalty to 0.25 (from 0.15)
  - Update config/consolidation_config.json with new parameters
  - Add unit tests for confidence calculation with various scenarios
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 24.1, 24.2, 24.3, 24.4_

---

## Phase 10: Production Hardening - Testing & Validation

- [ ] 30. Create Comprehensive Unit Test Suite
  - Create `tests/test_duplicate_detector.py`
    - Test fuzzy matching with various similarity levels (0.5, 0.75, 0.85, 0.95)
    - Test name normalization for each entity type (systems, pain_points, processes)
    - Test semantic similarity calculation with mock embeddings
    - Test threshold configuration per entity type
    - Test fuzzy-first candidate filtering
  - Create `tests/test_entity_merger.py`
    - Test description combination with duplicate sentences
    - Test contradiction detection with conflicting attributes
    - Test source tracking updates (mentioned_in_interviews, source_count)
    - Test attribute merging with most common value strategy
    - Test Spanish punctuation handling
  - Create `tests/test_consensus_scorer.py`
    - Test confidence calculation with source_count 1, 5, 10, 20
    - Test agreement bonus calculation
    - Test contradiction penalty
    - Test single source penalty
    - Test edge cases (0 sources, 100 sources)
  - Create `tests/test_consolidation_agent.py`
    - Test end-to-end consolidation with mock database
    - Test transaction rollback on failure
    - Test audit trail creation
  - _Requirements: 22.1, 22.2, 22.3_

- [ ] 31. Create Integration Tests with Real Data
  - Create `tests/test_consolidation_integration.py`
  - Test case 1: Duplicate detection with real duplicates
    - Create entities: "Excel", "excel", "MS Excel", "Microsoft Excel"
    - Verify all detected as duplicates with similarity scores
  - Test case 2: Contradiction detection
    - Create entities with conflicting frequency: "daily" vs "weekly"
    - Verify contradiction detected and flagged
  - Test case 3: End-to-end consolidation
    - Extract entities from 5 test interviews with known duplicates
    - Run full consolidation pipeline
    - Verify duplicate reduction (e.g., 15 entities → 8 consolidated)
    - Verify source tracking correct
    - Verify consensus scores calculated
  - Test case 4: API failure handling
    - Mock OpenAI API to return errors
    - Verify retry logic works
    - Verify fallback to fuzzy-only matching
  - Test case 5: Transaction rollback
    - Simulate failure mid-consolidation
    - Verify database rolled back to consistent state
  - _Requirements: 22.4_

- [ ] 32. Create Performance Tests
  - Create `tests/test_consolidation_performance.py`
  - Test case 1: Consolidation time with 1000 entities
    - Generate 1000 test entities with 10% duplicates
    - Measure consolidation time (target: <2 minutes)
    - Verify memory usage stays under 500MB
  - Test case 2: Embedding cache hit rate
    - Run consolidation twice on same data
    - Measure cache hit rate (target: >95% on second run)
  - Test case 3: Database query performance
    - Measure time for duplicate search query (target: <100ms)
    - Verify indexes are being used (EXPLAIN QUERY PLAN)
  - Test case 4: API call reduction
    - Count API calls with and without fuzzy-first filtering
    - Verify 90-95% reduction in API calls
  - _Requirements: 22.5_

- [ ] 33. Update Test Consolidation Script
  - Update `scripts/test_consolidation.py` - add comprehensive testing
  - Add test with real duplicate entities (not empty database)
  - Add test for contradiction detection
  - Add test for rollback mechanism
  - Add performance measurement (time and memory)
  - Add validation of all consolidation metrics
  - Generate detailed test report with pass/fail for each check
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

---

## Phase 11: Production Hardening - Rollback & Monitoring

- [ ] 34. Implement Rollback Mechanism
  - Update `intelligence_capture/database.py` - add entity snapshot storage
  - Create `entity_snapshots` table: id, entity_type, entity_id, snapshot_data (JSON), created_at
  - Implement `store_entity_snapshot(entity_type, entity_id, entity_data)` method
  - Update `intelligence_capture/consolidation_agent.py` - store snapshots before merge
  - Implement `rollback_consolidation(audit_id, reason)` method
  - Retrieve audit record and entity snapshots
  - Restore original entity data from snapshots
  - Update relationships to point back to original entities
  - Mark audit record with rollback_timestamp and rollback_reason
  - Create `scripts/rollback_consolidation.py` - CLI tool for rollback
  - Add unit tests for rollback functionality
  - _Requirements: 23.1, 23.2, 23.3, 23.4, 23.5_

- [ ] 35. Implement Metrics Collection
  - Create `intelligence_capture/metrics.py` - ConsolidationMetrics class
  - Track duplicates_by_type: count of duplicates found per entity type
  - Track avg_similarity_by_type: average similarity score per entity type
  - Track contradictions_by_type: count of contradictions per entity type
  - Track processing_time_by_type: time spent per entity type
  - Track API metrics: total_calls, cache_hits, cache_misses, failed_calls
  - Track quality metrics: duplicate_reduction_percentage, avg_confidence_score, contradiction_rate
  - Implement `export_to_json(path)` - export metrics to JSON file
  - Implement `display_summary()` - print color-coded summary to console
  - Integrate metrics collection into consolidation_agent.py
  - _Requirements: 25.1, 25.2, 25.3, 25.4, 25.5_

- [ ] 36. Update Configuration for Production
  - Update `config/consolidation_config.json` - tune all parameters
  - Lower similarity thresholds: pain_points=0.70, processes=0.75, systems=0.75
  - Keep high thresholds for precise entities: kpis=0.85, team_structures=0.90
  - Update consensus parameters: source_count_divisor=5, single_source_penalty=0.3
  - Update consensus parameters: contradiction_penalty=0.25, agreement_bonus=0.05
  - Add fuzzy_first_filtering: enabled=true, max_candidates=10, skip_semantic_threshold=0.95
  - Add retry_config: max_retries=3, exponential_backoff=true, circuit_breaker_threshold=10
  - Add logging_config: level="INFO", file="logs/consolidation.log", max_size_mb=10
  - Document all parameters with comments explaining rationale
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_

---

## Phase 12: Production Hardening - Final Validation

- [ ] 37. Run Pilot Test with 5 Interviews
  - Select 5 diverse interviews (different companies, roles)
  - Run `scripts/test_consolidation.py --interviews 5`
  - Verify all critical fixes working: no SQL injection, transactions work, API retries work
  - Verify performance optimizations: embeddings cached, fuzzy-first filtering active
  - Measure consolidation time (target: <30 seconds for 5 interviews)
  - Verify duplicate reduction (expect 70-90%)
  - Verify average consensus_confidence >= 0.70
  - Review entities with contradictions (expect <10%)
  - Validate all database integrity checks pass
  - Generate pilot test report with metrics
  - _Requirements: All requirements (validation)_

- [ ] 38. Run Full Test with 44 Interviews
  - Backup production database before test
  - Run `scripts/fast_extraction_pipeline.py` with consolidation enabled
  - Monitor consolidation in real-time (logs, metrics)
  - Measure total consolidation time (target: <5 minutes)
  - Verify duplicate reduction (expect 80-95%)
  - Verify average consensus_confidence >= 0.75
  - Verify relationships discovered (expect 100+ relationships)
  - Verify patterns identified (expect 10+ recurring patterns)
  - Review all entities with contradictions
  - Validate all database integrity checks pass
  - Generate comprehensive consolidation report
  - _Requirements: All requirements (production validation)_

- [ ] 39. Create Production Runbook
  - Create `docs/CONSOLIDATION_RUNBOOK.md`
  - Document pre-flight checklist: database backup, config validation, dependency check
  - Document how to run consolidation: commands, parameters, expected output
  - Document how to monitor consolidation: logs, metrics, progress tracking
  - Document common issues and troubleshooting: API failures, transaction rollbacks, low confidence
  - Document how to rollback consolidation: identify audit_id, run rollback script, verify restoration
  - Document performance tuning: adjust thresholds, enable/disable features, optimize queries
  - Document quality validation: run validation script, review contradictions, manual sampling
  - Include example commands and expected outputs
  - _Requirements: All requirements (documentation)_

- [ ] 40. Update Project Documentation
  - Update `docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md` - add production hardening section
  - Document all security fixes (SQL injection, transaction management, API resilience)
  - Document all performance optimizations (embedding storage, fuzzy-first filtering)
  - Document all code quality improvements (logging, testing, metrics)
  - Update `PROJECT_STRUCTURE.md` - add new files (logger.py, metrics.py, rollback script)
  - Update `CLAUDE.MD` - mark consolidation as production-ready
  - Create `docs/CONSOLIDATION_PRODUCTION_READY.md` - comprehensive summary
  - Include before/after metrics from QA review
  - Include timeline and effort breakdown
  - _Requirements: All requirements (documentation)_

---

## Success Metrics

After completing all tasks, the system should achieve:

### Data Quality
- ✅ **Duplicate Reduction**: 80-95% reduction in duplicate entities (48 → 3 for systems)
- ✅ **Source Tracking**: All consolidated entities have mentioned_in_interviews and source_count
- ✅ **Consensus Confidence**: Average confidence >= 0.75 across all entity types
- ✅ **Contradictions**: <10% of entities flagged with has_contradictions
- ✅ **Relationships**: System → Pain Point and Process → System relationships discovered
- ✅ **Patterns**: Recurring patterns identified (mentioned in 30%+ of interviews)

### Performance
- ✅ **Consolidation Time**: <5 minutes for 44 interviews (down from 8+ hours)
- ✅ **API Call Reduction**: 90-95% fewer API calls through fuzzy-first filtering
- ✅ **Cache Hit Rate**: >95% embedding cache hit rate on subsequent runs
- ✅ **Query Performance**: <100ms for duplicate detection queries

### Security & Reliability
- ✅ **No SQL Injection**: Entity type whitelist enforced, all inputs validated
- ✅ **Transaction Safety**: All consolidation operations wrapped in transactions
- ✅ **API Resilience**: Retry logic with exponential backoff, circuit breaker implemented
- ✅ **Data Integrity**: No orphaned records, all foreign keys valid

### Code Quality
- ✅ **Structured Logging**: Python logging framework with rotating files
- ✅ **Test Coverage**: Comprehensive unit, integration, and performance tests
- ✅ **Metrics Collection**: All consolidation metrics tracked and exported
- ✅ **Rollback Capability**: Full rollback mechanism with entity snapshots

### Production Readiness
- ✅ **QA Review Score**: Improved from 7.5/10 to 9.5/10
- ✅ **All Critical Issues**: Fixed (SQL injection, transactions, API failures)
- ✅ **All High Priority**: Fixed (performance, contradiction detection, rollback)
- ✅ **Documentation**: Complete runbook and production guide

---

## Task Execution Order

**Phase 1**: Tasks 0-3 (Foundation & Schema) - COMPLETED
**Phase 2**: Tasks 4-7 (Core Components) - COMPLETED
**Phase 3**: Tasks 8-9 (Database Integration) - COMPLETED
**Phase 4**: Tasks 10-12 (Relationships & Patterns) - COMPLETED
**Phase 5**: Tasks 13-16 (Testing & Validation) - COMPLETED
**Phase 6**: Tasks 17-18 (Reporting & Documentation) - COMPLETED
**Phase 7**: Tasks 19-21 (Critical Security Fixes) - NEW
**Phase 8**: Tasks 22-25 (Performance Optimization) - NEW
**Phase 9**: Tasks 26-29 (Code Quality) - NEW
**Phase 10**: Tasks 30-33 (Testing & Validation) - NEW
**Phase 11**: Tasks 34-36 (Rollback & Monitoring) - NEW
**Phase 12**: Tasks 37-40 (Final Validation) - NEW

**Total**: 41 tasks (19 original + 22 production hardening)
