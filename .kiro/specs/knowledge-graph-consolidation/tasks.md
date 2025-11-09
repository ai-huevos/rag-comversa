# Implementation Plan: Knowledge Graph Consolidation System

## Overview

This implementation plan breaks down the Knowledge Graph Consolidation System into discrete, actionable coding tasks. Each task builds incrementally on previous work, with the goal of transforming fragmented entity data (25x Excel, 12x SAP) into consolidated, consensus-driven intelligence (1x Excel with 25 sources, 1x SAP with 12 sources).

**Timeline**: 5 days (Week 1)
**Goal**: Reduce duplicate entities by 80-95% and enable accurate business intelligence queries

---

## Phase 1: Foundation (Day 1)

### Task 1: Create Database Schema for Consolidation

Create database migration script to add consolidation tracking columns to all entity tables.

**Files to modify:**
- `intelligence_capture/database.py` - Add schema migration method
- Create `intelligence_capture/migrations/add_consolidation_fields.py`

**Implementation details:**
- Add columns to all 17 entity tables: `mentioned_in_interviews` (TEXT/JSON), `source_count` (INTEGER DEFAULT 1), `consensus_confidence` (REAL DEFAULT 1.0), `is_consolidated` (BOOLEAN DEFAULT false), `has_contradictions` (BOOLEAN DEFAULT false), `contradiction_details` (TEXT/JSON), `merged_entity_ids` (TEXT/JSON), `first_mentioned_date` (TEXT), `last_mentioned_date` (TEXT), `consolidated_at` (TIMESTAMP)
- Create `relationships` table with columns: `id`, `source_entity_id`, `source_entity_type`, `relationship_type`, `target_entity_id`, `target_entity_type`, `strength`, `mentioned_in_interviews`, `created_at`, `updated_at`
- Create `consolidation_audit` table with columns: `id`, `entity_type`, `merged_entity_ids`, `resulting_entity_id`, `similarity_score`, `consolidation_timestamp`, `rollback_timestamp`, `rollback_reason`
- Create `patterns` table with columns: `id`, `pattern_type`, `entity_type`, `entity_id`, `pattern_frequency`, `source_count`, `high_priority`, `description`, `detected_at`
- Add indexes: `idx_relationships_source`, `idx_relationships_target`, `idx_audit_entity_type`, `idx_audit_timestamp`, `idx_patterns_type`, `idx_patterns_priority`
- Add indexes on entity name columns for fast duplicate detection

_Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

### Task 2: Create Consolidation Configuration

Create configuration file for consolidation settings with similarity thresholds per entity type.

**Files to create:**
- `config/consolidation_config.json`

**Implementation details:**
- Define similarity thresholds for all 17 entity types (default 0.85 for most, 0.80 for pain_points/patterns, 0.90 for precise entities like KPIs)
- Configure semantic vs name similarity weights (0.3 semantic, 0.7 name)
- Set consensus confidence parameters (source_count_divisor: 10, agreement_bonus: 0.1, max_bonus: 0.3, contradiction_penalty: 0.15)
- Configure pattern recognition thresholds (recurring_pain: 3, problematic_system: 5, high_priority_frequency: 0.30)
- Add max_candidates limit (10) for performance

_Requirements: 14.1, 14.2, 14.3, 14.4_

### Task 3: Create DuplicateDetector Component

Implement duplicate detection using fuzzy string matching and semantic similarity.

**Files to create:**
- `intelligence_capture/duplicate_detector.py`

**Implementation details:**
- Create `DuplicateDetector` class with `__init__(config: Dict)`
- Implement `find_duplicates(entity, entity_type, existing_entities)` - returns list of (entity, similarity_score) tuples
- Implement `calculate_name_similarity(name1, name2, entity_type)` - uses fuzzy matching (rapidfuzz or difflib) with entity-specific normalization
- Implement `normalize_name(name, entity_type)` - removes common words ("sistema", "software" for systems; "problema de" for pain_points)
- Implement `calculate_semantic_similarity(text1, text2)` - uses OpenAI embeddings + cosine similarity
- Implement `_get_similarity_threshold(entity_type)` - reads from config
- Cache embeddings to avoid redundant API calls
- Return top 10 candidates sorted by similarity score

_Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

---

## Phase 2: Core Consolidation Logic (Day 2)

### Task 4: Create EntityMerger Component

Implement entity merging logic with source tracking and contradiction detection.

**Files to create:**
- `intelligence_capture/entity_merger.py`

**Implementation details:**
- Create `EntityMerger` class with `merge(new_entity, existing_entity, interview_id)` method
- Implement `combine_descriptions(desc1, desc2)` - concatenates unique sentences, removes duplicates
- Implement `detect_contradictions(new_entity, existing_entity)` - compares attribute values (frequency, severity, etc.), returns contradiction dict or None
- Implement `update_source_tracking(entity, interview_id)` - appends interview_id to mentioned_in_interviews, increments source_count, updates first/last_mentioned_date
- Implement `merge_attributes(new_attrs, existing_attrs)` - keeps most common value for conflicting attributes
- Store merged_entity_ids for audit trail
- Set is_consolidated = true on merged entity

_Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 3.1, 3.2, 3.3, 3.4, 3.5, 5.1, 5.2, 5.3, 5.4_

### Task 5: Create ConsensusScorer Component

Implement consensus confidence scoring based on source count and attribute agreement.

**Files to create:**
- `intelligence_capture/consensus_scorer.py`

**Implementation details:**
- Create `ConsensusScorer` class with `__init__(config: Dict)`
- Implement `calculate_confidence(entity)` - returns float 0.0-1.0
- Calculate base_score = min(source_count / 10, 1.0)
- Calculate agreement_bonus = min(attribute_agreement_count * 0.1, 0.3)
- Calculate contradiction_penalty = contradiction_count * 0.15
- Return max(0.0, min(1.0, base_score + agreement_bonus - contradiction_penalty))
- Implement `check_attribute_agreement(entity)` - counts attributes that agree across sources
- Set needs_review = true if confidence < 0.6

_Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

### Task 6: Create KnowledgeConsolidationAgent

Implement main consolidation orchestrator that uses DuplicateDetector, EntityMerger, and ConsensusScorer.

**Files to create:**
- `intelligence_capture/consolidation_agent.py`

**Implementation details:**
- Create `KnowledgeConsolidationAgent` class with `__init__(db: IntelligenceDB, config: Dict)`
- Initialize DuplicateDetector, EntityMerger, ConsensusScorer components
- Implement `consolidate_entities(entities, interview_id)` - main entry point
- For each entity type, call `_consolidate_entity_type(entity_list, entity_type, interview_id)`
- Implement `find_similar_entities(entity, entity_type)` - queries database for existing entities, calls DuplicateDetector
- Implement `merge_entities(new_entity, existing_entity, similarity_score)` - calls EntityMerger, updates database
- Implement `calculate_consensus_confidence(entity)` - calls ConsensusScorer
- Log all merge decisions with similarity scores to consolidation_audit table
- Return consolidated entities dict

_Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

---

## Phase 3: Integration (Day 3)

### Task 7: Integrate Consolidation into Processor

Modify IntelligenceProcessor to call KnowledgeConsolidationAgent after extraction.

**Files to modify:**
- `intelligence_capture/processor.py`

**Implementation details:**
- Import KnowledgeConsolidationAgent
- Initialize consolidation_agent in `__init__` if config.consolidation.enabled = true
- In `process_interview()`, after `extractor.extract_all()`, call `consolidation_agent.consolidate_entities(entities, interview_id)`
- Store consolidated entities instead of raw entities
- Add consolidation timing metrics to processing report
- Handle consolidation errors gracefully (log and continue with raw entities if consolidation fails)
- Add consolidation status to extraction progress tracking

_Requirements: 9.1, 9.2, 9.3, 9.4_

### Task 8: Update Database Storage Methods

Modify database insert/update methods to handle consolidated entities with source tracking.

**Files to modify:**
- `intelligence_capture/database.py`

**Implementation details:**
- Update all `insert_*` methods (insert_pain_point, insert_system, etc.) to check if entity already exists
- If entity exists and is_consolidated = true, call `update_consolidated_entity()` instead of insert
- Implement `update_consolidated_entity(entity_type, entity_id, new_data, interview_id)` - updates source tracking, recalculates confidence
- Implement `insert_relationship(relationship)` - inserts into relationships table
- Implement `insert_consolidation_audit(audit_record)` - inserts into consolidation_audit table
- Add transaction support for atomic consolidation operations
- Add `get_entities_by_type(entity_type, limit=None)` for duplicate detection queries

_Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

### Task 9: Run Database Migration

Execute migration script to add consolidation columns to existing database.

**Files to run:**
- `intelligence_capture/migrations/add_consolidation_fields.py`

**Implementation details:**
- Backup existing database before migration
- Run ALTER TABLE statements for all 17 entity tables
- Create new tables (relationships, consolidation_audit, patterns)
- Create indexes for performance
- Verify migration success with schema inspection
- Test backward compatibility (existing queries still work)

_Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

---

## Phase 4: Relationship Discovery (Day 4)

### Task 10: Create RelationshipDiscoverer Component

Implement relationship discovery between entities based on co-occurrence.

**Files to create:**
- `intelligence_capture/relationship_discoverer.py`

**Implementation details:**
- Create `RelationshipDiscoverer` class with `__init__(db: IntelligenceDB)`
- Implement `discover_relationships(entities, interview_id)` - returns list of relationship dicts
- Implement `_find_system_pain_relationships(systems, pain_points, interview_id)` - detects System → causes → Pain Point
- Implement `_find_process_system_relationships(processes, systems, interview_id)` - detects Process → uses → System
- Check for entity name mentions in descriptions (case-insensitive)
- Set relationship strength based on mention clarity (0.8 for explicit, 0.6 for implicit)
- Store relationships with mentioned_in_interviews tracking
- Prevent duplicate relationships (check if relationship already exists)

_Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

### Task 11: Integrate Relationship Discovery

Add relationship discovery to consolidation workflow.

**Files to modify:**
- `intelligence_capture/consolidation_agent.py`

**Implementation details:**
- Import RelationshipDiscoverer
- Initialize relationship_discoverer in `__init__`
- In `consolidate_entities()`, after entity consolidation, call `relationship_discoverer.discover_relationships(consolidated_entities, interview_id)`
- Store discovered relationships in database via `db.insert_relationship()`
- Update existing relationships if same relationship found in multiple interviews (increment strength, add interview_id)
- Log relationship discovery metrics (count of new relationships, updated relationships)

_Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

### Task 12: Create PatternRecognizer Component

Implement pattern recognition for recurring issues and problematic systems.

**Files to create:**
- `intelligence_capture/pattern_recognizer.py`

**Implementation details:**
- Create `PatternRecognizer` class with `__init__(db: IntelligenceDB, config: Dict)`
- Implement `identify_patterns()` - main entry point, returns list of pattern dicts
- Implement `find_recurring_pain_points(threshold=3)` - queries pain_points with source_count >= threshold
- Implement `find_problematic_systems(threshold=5)` - queries systems with negative sentiment in threshold+ interviews
- Calculate pattern_frequency = source_count / total_interviews
- Set high_priority = true if pattern_frequency >= 0.30
- Store patterns in patterns table
- Return patterns sorted by frequency and priority

_Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

---

## Phase 5: Testing and Validation (Day 5)

### Task 13: Create Consolidation Test Suite

Write unit tests for all consolidation components.

**Files to create:**
- `tests/test_duplicate_detector.py`
- `tests/test_entity_merger.py`
- `tests/test_consensus_scorer.py`
- `tests/test_consolidation_agent.py`
- `tests/test_relationship_discoverer.py`
- `tests/test_pattern_recognizer.py`

**Implementation details:**
- Test DuplicateDetector: fuzzy matching with various similarity levels, name normalization, semantic similarity
- Test EntityMerger: description combination, contradiction detection, source tracking
- Test ConsensusScorer: confidence calculation with various source counts, agreement bonus, contradiction penalty
- Test ConsolidationAgent: end-to-end consolidation, duplicate detection, merging
- Test RelationshipDiscoverer: System → Pain Point discovery, Process → System discovery
- Test PatternRecognizer: recurring pain detection, problematic system detection
- Use pytest fixtures for test data
- Mock database calls where appropriate

_Requirements: All requirements (validation)_

### Task 14: Create Integration Test with Sample Data

Test end-to-end consolidation with 5 sample interviews.

**Files to create:**
- `tests/test_consolidation_integration.py`
- `scripts/test_consolidation.py`

**Implementation details:**
- Create test database with 5 sample interviews containing known duplicates (3x Excel, 2x SAP)
- Run full extraction + consolidation pipeline
- Verify duplicate reduction (5 entities → 2 consolidated entities)
- Verify source tracking (Excel has 3 sources, SAP has 2 sources)
- Verify consensus confidence scores calculated correctly
- Verify relationships discovered (at least 2 relationships)
- Verify patterns identified (at least 1 recurring pattern)
- Generate consolidation report with before/after metrics
- Assert: duplicate_reduction_percentage >= 50%

_Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5_

### Task 15: Create Consolidation Validation Script

Create validation script to verify consolidation quality and generate reports.

**Files to create:**
- `scripts/validate_consolidation.py`

**Implementation details:**
- Implement `validate_consolidation(db_path)` - runs all validation checks
- Check: all entities have source_count >= 1
- Check: all entities have consensus_confidence between 0.0 and 1.0
- Check: mentioned_in_interviews contains valid interview IDs
- Check: no orphaned relationships (all targets exist)
- Check: duplicate reduction achieved (entities_after < entities_before)
- Generate consolidation_report.json with metrics: entities_before, entities_after, duplicates_merged, average_consensus_confidence, contradiction_count, relationship_count, pattern_count
- List top 10 most-mentioned entities by source_count
- List all entities with has_contradictions = true
- Print summary to console with color-coded status (✓ green, ✗ red)

_Requirements: 11.1, 11.2, 11.3, 11.4, 11.5, 13.1, 13.2, 13.3, 13.4, 13.5_

### Task 16: Test with 10 Interviews

Run consolidation on 10 interviews and validate results.

**Files to run:**
- `scripts/test_consolidation.py --interviews 10`

**Implementation details:**
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

_Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 12.1, 12.2, 12.3, 12.4, 12.5_

---

## Phase 6: Reporting and Documentation (Bonus)

### Task 17: Create Consolidation Dashboard

Create reporting script to visualize consolidation results.

**Files to create:**
- `scripts/generate_consolidation_report.py`

**Implementation details:**
- Generate HTML report with consolidation metrics
- Show before/after entity counts per type (bar chart)
- Show top 10 most-mentioned entities (table)
- Show consensus confidence distribution (histogram)
- Show relationship graph (System → Pain Point connections)
- Show recurring patterns (sorted by frequency)
- Show entities with contradictions (table with details)
- Export report as HTML and JSON
- Include timestamp and database path in report

_Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

### Task 18: Update Documentation

Update project documentation to reflect consolidation system.

**Files to modify:**
- `CLAUDE.MD` - Update current state, add consolidation status
- `PROJECT_STRUCTURE.md` - Add consolidation_agent.py and related files
- `docs/KNOWLEDGE_GRAPH_CONSOLIDATION.md` - Create comprehensive guide

**Implementation details:**
- Document consolidation workflow in CLAUDE.MD
- Add consolidation configuration to PROJECT_STRUCTURE.MD
- Create KNOWLEDGE_GRAPH_CONSOLIDATION.md with: overview, architecture, usage guide, configuration options, troubleshooting
- Include example queries for consolidated data
- Document relationship types and pattern types
- Add consolidation metrics to success criteria

_Requirements: All requirements (documentation)_

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

**Day 1**: Tasks 1-3 (Foundation)
**Day 2**: Tasks 4-6 (Core Logic)
**Day 3**: Tasks 7-9 (Integration)
**Day 4**: Tasks 10-12 (Relationships & Patterns)
**Day 5**: Tasks 13-16 (Testing & Validation)
**Bonus**: Tasks 17-18 (Reporting & Docs)

**Total**: 18 tasks over 5 days
