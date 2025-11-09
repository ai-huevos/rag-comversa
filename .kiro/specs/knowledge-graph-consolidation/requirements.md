# Requirements Document: Knowledge Graph Consolidation System

## Introduction

This document defines requirements for implementing a Knowledge Graph Consolidation System that merges duplicate entities across 44 interview transcripts, builds consensus from multiple sources, and discovers relationships between entities. The system addresses a critical data quality issue: 20-30% of extracted entities are duplicates (e.g., 25 separate "Excel" entries, 12 separate "SAP" entries) that prevent meaningful business intelligence queries.

**Current State**:
- ✅ Extraction system processes all 44 interviews
- ✅ All 17 entity types extracted and stored
- ✅ Parallel processing with WAL mode (no database locking)
- ✅ Rate limiting prevents API errors
- ❌ Duplicate entities not consolidated (25x Excel, 12x SAP, etc.)
- ❌ No consensus tracking across interviews
- ❌ No relationship discovery between entities
- ❌ Cannot answer questions like "What systems cause the most pain?"

**Target State**:
- Consolidated entities with source tracking (Excel: 1 entry with 25 sources)
- Consensus confidence scores (higher confidence = more sources agree)
- Relationship discovery (System → Pain Points, Process → Systems)
- Pattern recognition (recurring issues, common workflows)
- Actionable business intelligence ready for AI agents

## Glossary

- **Knowledge Graph**: Graph database storing interconnected business intelligence with consolidated entities
- **Consolidation Agent**: AI system that identifies and merges duplicate entities across interviews
- **Entity**: Business intelligence object (System, Pain Point, Process, etc.)
- **Duplicate Entity**: Same real-world object mentioned in multiple interviews (e.g., "Excel", "Excel spreadsheet", "hojas de cálculo")
- **Consensus**: Agreement across multiple interview sources about an entity's attributes
- **Confidence Score**: Numerical measure (0.0-1.0) of how certain we are about consolidated entity data
- **Source Tracking**: Recording which interviews mentioned each entity
- **Relationship**: Connection between entities (e.g., System "Excel" causes Pain Point "manual data entry")
- **Pattern**: Recurring theme across multiple interviews (e.g., "WhatsApp communication issues")
- **Fuzzy Matching**: Algorithm for finding similar text strings despite spelling variations
- **Extraction System**: LLM-based system that processes interview transcripts
- **Database**: SQLite database storing all extracted and consolidated entities

## Requirements

### Requirement 1: Duplicate Entity Detection

**User Story:** As a Data Quality Manager, I want duplicate entities automatically detected across interviews, so that I can see consolidated intelligence instead of fragmented data.

#### Acceptance Criteria

1. WHEN the Consolidation Agent processes a newly extracted entity, THE System SHALL search for existing similar entities of the same type in the database

2. WHEN comparing entity names, THE System SHALL use fuzzy matching with a similarity threshold of 0.85 to account for spelling variations (e.g., "Excel" vs "Excel spreadsheet")

3. WHEN comparing System entities, THE System SHALL normalize names by removing common words like "sistema", "software", "herramienta" before matching

4. WHEN comparing Pain Point entities, THE System SHALL use semantic similarity (embedding-based) with threshold 0.80 to detect conceptually similar issues

5. THE System SHALL return a ranked list of similar entities with similarity scores for each candidate match

### Requirement 2: Entity Consolidation and Merging

**User Story:** As a Business Intelligence Analyst, I want duplicate entities merged into single consolidated records, so that I can query accurate entity counts and relationships.

#### Acceptance Criteria

1. WHEN duplicate entities are detected with similarity >= 0.85, THE System SHALL merge them into a single consolidated entity

2. WHEN merging entities, THE System SHALL combine descriptions by concatenating unique information from all sources

3. WHEN merging entities with conflicting attributes, THE System SHALL keep the most common value and flag the conflict for review

4. THE System SHALL preserve all original entity IDs in a merged_entity_ids field for audit trail

5. WHEN an entity is merged, THE System SHALL update all relationships to point to the consolidated entity

### Requirement 3: Source Tracking and Provenance

**User Story:** As a Research Analyst, I want to know which interviews mentioned each entity, so that I can validate findings and assess consensus strength.

#### Acceptance Criteria

1. WHEN the Consolidation Agent merges entities, THE System SHALL store mentioned_in_interviews as a JSON array of interview IDs

2. WHEN storing consolidated entities, THE System SHALL calculate source_count as the number of unique interviews mentioning the entity

3. THE System SHALL preserve the original extraction context (interview_id, question_number) for each mention

4. WHEN an entity is mentioned in multiple interviews, THE System SHALL store first_mentioned_date and last_mentioned_date

5. THE System SHALL enable querying entities by source_count (e.g., "Show systems mentioned by 10+ people")

### Requirement 4: Consensus Confidence Scoring

**User Story:** As a Digital Transformation Officer, I want confidence scores for consolidated entities, so that I can prioritize high-consensus findings over single-source claims.

#### Acceptance Criteria

1. WHEN calculating consensus confidence, THE System SHALL use the formula: base_score = min(source_count / 10, 1.0) to reward multiple sources

2. WHEN entity attributes agree across sources, THE System SHALL increase confidence by 0.1 per agreeing attribute (max +0.3)

3. WHEN entity attributes conflict across sources, THE System SHALL decrease confidence by 0.15 per conflicting attribute

4. THE System SHALL store consensus_confidence as a REAL value between 0.0 and 1.0

5. WHEN consensus_confidence < 0.6, THE System SHALL flag needs_review = true for human validation

### Requirement 5: Contradiction Detection and Flagging

**User Story:** As a Quality Manager, I want contradictions between interview sources automatically detected, so that I can investigate discrepancies and resolve conflicts.

#### Acceptance Criteria

1. WHEN merging entities with different attribute values, THE System SHALL detect contradictions (e.g., one interview says "daily" frequency, another says "weekly")

2. WHEN contradictions are detected, THE System SHALL store has_contradictions = true and list conflicting_attributes

3. THE System SHALL store contradiction_details as JSON with format: {"attribute": "frequency", "values": ["daily", "weekly"], "sources": [interview_id_1, interview_id_2]}

4. WHEN contradictions exist, THE System SHALL reduce consensus_confidence by 0.15 per contradiction

5. THE System SHALL generate a contradiction_report listing all entities with conflicts for human review

### Requirement 6: Relationship Discovery Between Entities

**User Story:** As an AI Agent Developer, I want relationships between entities automatically discovered, so that agents can answer questions like "What systems cause the most pain points?"

#### Acceptance Criteria

1. WHEN the Consolidation Agent processes interviews, THE System SHALL detect relationships where entities are mentioned together in the same context

2. WHEN a System and Pain Point are mentioned in the same answer, THE System SHALL create a relationship: System → causes → Pain Point

3. WHEN a Process and System are mentioned together, THE System SHALL create a relationship: Process → uses → System

4. THE System SHALL store relationships in a relationships table with fields: source_entity_id, source_entity_type, relationship_type, target_entity_id, target_entity_type, strength (0.0-1.0)

5. WHEN a relationship is mentioned in multiple interviews, THE System SHALL increase relationship strength by 0.2 per additional source (max 1.0)

### Requirement 7: Pattern Recognition Across Interviews

**User Story:** As a Digital Transformation Officer, I want recurring patterns automatically identified, so that I can prioritize systemic issues affecting multiple teams.

#### Acceptance Criteria

1. WHEN the Consolidation Agent processes all interviews, THE System SHALL identify Pain Points mentioned by 3 or more people as recurring_pattern = true

2. WHEN a System is mentioned with negative sentiment in 5+ interviews, THE System SHALL flag it as problematic_system = true

3. THE System SHALL calculate pattern_frequency = (count of interviews mentioning pattern / total interviews) for each pattern

4. WHEN pattern_frequency >= 0.30 (30% of interviews), THE System SHALL classify the pattern as high_priority = true

5. THE System SHALL generate a patterns_report listing all recurring patterns ranked by frequency and impact

### Requirement 8: Database Schema Enhancement for Consolidation

**User Story:** As a Database Engineer, I want database schema updated to support consolidation tracking, so that all consolidation metadata is persisted.

#### Acceptance Criteria

1. THE System SHALL add mentioned_in_interviews column (TEXT/JSON) to all entity tables (systems, pain_points, processes, etc.)

2. THE System SHALL add source_count column (INTEGER DEFAULT 1) to all entity tables

3. THE System SHALL add consensus_confidence column (REAL DEFAULT 1.0) to all entity tables

4. THE System SHALL add is_consolidated column (BOOLEAN DEFAULT false) to all entity tables

5. THE System SHALL add has_contradictions column (BOOLEAN DEFAULT false) and contradiction_details column (TEXT/JSON) to all entity tables

### Requirement 9: Consolidation Agent Integration with Extraction Pipeline

**User Story:** As a System Architect, I want consolidation to run automatically after extraction, so that the database always contains consolidated data.

#### Acceptance Criteria

1. WHEN the Extraction System completes processing an interview, THE System SHALL invoke the Consolidation Agent before storing entities

2. WHEN the Consolidation Agent receives new entities, THE System SHALL check for duplicates and merge if similarity >= 0.85

3. WHEN no duplicates are found, THE System SHALL insert the new entity with source_count = 1 and consensus_confidence = 0.5 (single source)

4. WHEN duplicates are found and merged, THE System SHALL update the existing entity with incremented source_count and recalculated consensus_confidence

5. THE System SHALL complete consolidation within 2 seconds per entity to maintain extraction performance

### Requirement 10: Consolidation Performance and Scalability

**User Story:** As a System Administrator, I want consolidation to process 44 interviews efficiently, so that total extraction time remains under 20 minutes.

#### Acceptance Criteria

1. WHEN processing 44 interviews sequentially, THE System SHALL complete consolidation in under 5 minutes total (average 7 seconds per interview)

2. WHEN searching for duplicate entities, THE System SHALL use database indexes on entity names for sub-second query performance

3. THE System SHALL cache fuzzy matching results to avoid redundant similarity calculations

4. WHEN parallel processing is enabled, THE System SHALL handle concurrent consolidation requests safely using database transactions

5. THE System SHALL limit similarity search to the top 10 most similar candidates to prevent performance degradation

### Requirement 11: Consolidation Validation and Quality Checks

**User Story:** As a Quality Manager, I want validation checks after consolidation, so that I can verify data integrity and consolidation accuracy.

#### Acceptance Criteria

1. WHEN consolidation completes, THE System SHALL verify that total entity count decreased (duplicates were merged)

2. THE System SHALL check that all entities have source_count >= 1 and consensus_confidence between 0.0 and 1.0

3. THE System SHALL validate that mentioned_in_interviews contains valid interview IDs that exist in the interviews table

4. THE System SHALL verify that no orphaned relationships exist (all relationship targets point to existing entities)

5. THE System SHALL generate a consolidation_report with metrics: entities_before, entities_after, duplicates_merged, average_consensus_confidence

### Requirement 12: Incremental Consolidation for New Interviews

**User Story:** As a System Operator, I want new interviews to consolidate with existing data, so that I can add interviews over time without reprocessing everything.

#### Acceptance Criteria

1. WHEN processing a new interview after initial consolidation, THE System SHALL compare new entities against existing consolidated entities

2. WHEN a new entity matches an existing consolidated entity, THE System SHALL update the existing entity by adding the new interview to mentioned_in_interviews

3. THE System SHALL recalculate consensus_confidence after each incremental update

4. WHEN a new entity introduces contradictions, THE System SHALL update has_contradictions and contradiction_details

5. THE System SHALL maintain consolidation performance for incremental updates (under 10 seconds per interview)

### Requirement 13: Consolidation Reporting and Analytics

**User Story:** As a Business Intelligence Analyst, I want consolidation reports showing before/after metrics, so that I can demonstrate data quality improvements.

#### Acceptance Criteria

1. WHEN consolidation completes, THE System SHALL generate a report showing entity counts before and after consolidation for each entity type

2. THE System SHALL calculate and report duplicate_reduction_percentage = ((entities_before - entities_after) / entities_before) * 100

3. THE System SHALL list top 10 most-mentioned entities by source_count for each entity type

4. THE System SHALL report average consensus_confidence by entity type

5. THE System SHALL list all entities with has_contradictions = true for human review

### Requirement 14: Fuzzy Matching Configuration and Tuning

**User Story:** As a Data Scientist, I want configurable fuzzy matching thresholds, so that I can tune consolidation accuracy vs recall.

#### Acceptance Criteria

1. THE System SHALL support configurable similarity thresholds per entity type via configuration file

2. WHEN similarity_threshold is set to 0.90, THE System SHALL only merge highly similar entities (conservative, fewer false positives)

3. WHEN similarity_threshold is set to 0.80, THE System SHALL merge more aggressively (liberal, more false positives but fewer missed duplicates)

4. THE System SHALL default to similarity_threshold = 0.85 as a balanced setting

5. THE System SHALL log all merge decisions with similarity scores for post-hoc analysis and threshold tuning

### Requirement 15: Consolidation Rollback and Audit Trail

**User Story:** As a System Administrator, I want to rollback incorrect consolidations, so that I can fix mistakes without losing data.

#### Acceptance Criteria

1. WHEN entities are merged, THE System SHALL preserve original entities in a consolidation_audit table

2. THE System SHALL store consolidation_timestamp, merged_entity_ids, resulting_entity_id, and similarity_score for each merge

3. WHEN a consolidation needs to be rolled back, THE System SHALL provide a rollback function that restores original entities

4. THE System SHALL maintain referential integrity during rollback by updating relationships to point back to original entities

5. THE System SHALL log all rollback operations with reason and timestamp for audit purposes

## Success Criteria

### Data Quality
- ✅ Duplicate entities reduced by 80-95% (e.g., 25 Excel entries → 1 consolidated entry)
- ✅ All consolidated entities have source_count >= 1
- ✅ Average consensus_confidence >= 0.75 across all entity types
- ✅ <10% of entities flagged with has_contradictions = true
- ✅ All relationships point to valid consolidated entities

### Performance
- ✅ Consolidation completes in under 5 minutes for 44 interviews
- ✅ Duplicate detection query time < 1 second per entity
- ✅ Incremental consolidation < 10 seconds per new interview
- ✅ Total extraction + consolidation time < 20 minutes

### Intelligence
- ✅ Relationships discovered between entities (System → Pain Point, Process → System)
- ✅ Recurring patterns identified (mentioned in 30%+ of interviews)
- ✅ Contradictions detected and flagged for review
- ✅ Consensus confidence scores enable prioritization
- ✅ Can answer questions like "What systems cause the most pain?" with accurate counts

### Maintainability
- ✅ Configurable similarity thresholds per entity type
- ✅ Audit trail for all consolidation operations
- ✅ Rollback capability for incorrect merges
- ✅ Comprehensive consolidation reports
- ✅ Clear logging of merge decisions with similarity scores
