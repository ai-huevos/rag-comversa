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

### Requirement 16: Production Security Hardening

**User Story:** As a Security Engineer, I want all SQL injection vulnerabilities eliminated and input validation enforced, so that the system is secure against malicious inputs.

#### Acceptance Criteria

1. THE System SHALL validate all entity_type parameters against a whitelist of valid entity types before using in SQL queries

2. WHEN an invalid entity_type is provided, THE System SHALL raise a ValueError with a descriptive message

3. THE System SHALL sanitize all user-provided entity data before database insertion to prevent SQL injection

4. THE System SHALL store API keys only in environment variables and never log them in plain text

5. THE System SHALL implement rate limiting for OpenAI API calls to prevent quota exhaustion

### Requirement 17: Transaction Management and Data Integrity

**User Story:** As a Database Administrator, I want all consolidation operations wrapped in transactions, so that database remains consistent even if operations fail mid-process.

#### Acceptance Criteria

1. WHEN the Consolidation Agent begins consolidation, THE System SHALL start a database transaction before any entity updates

2. WHEN all consolidation operations complete successfully, THE System SHALL commit the transaction

3. WHEN any consolidation operation fails, THE System SHALL rollback the transaction and restore database to previous state

4. THE System SHALL log all transaction rollbacks with error details for debugging

5. THE System SHALL verify database integrity after each consolidation batch (no orphaned records, valid foreign keys)

### Requirement 18: API Failure Resilience

**User Story:** As a System Operator, I want the system to handle OpenAI API failures gracefully with retries, so that temporary API issues don't cause consolidation failures.

#### Acceptance Criteria

1. WHEN an OpenAI API call fails, THE System SHALL retry up to 3 times with exponential backoff (2^attempt seconds)

2. WHEN all retry attempts fail, THE System SHALL raise an EmbeddingError with details about the failure

3. THE System SHALL log all API failures to the consolidation audit trail with timestamp and error message

4. WHEN embedding generation fails for an entity, THE System SHALL fall back to fuzzy matching only (no semantic similarity)

5. THE System SHALL implement a circuit breaker that disables semantic similarity after 10 consecutive API failures

### Requirement 19: Performance Optimization - Embedding Storage

**User Story:** As a Performance Engineer, I want embeddings pre-computed and stored in the database, so that consolidation completes in minutes instead of hours.

#### Acceptance Criteria

1. THE System SHALL add an embedding_vector column (BLOB) to all entity tables for storing pre-computed embeddings

2. WHEN an entity is first inserted, THE System SHALL generate and store its embedding vector

3. WHEN searching for duplicates, THE System SHALL use stored embeddings instead of generating new ones

4. THE System SHALL implement a batch embedding generation script for existing entities without embeddings

5. WHEN embeddings are stored, THE System SHALL reduce consolidation time from 8+ hours to under 5 minutes for 44 interviews

### Requirement 20: Fuzzy-First Candidate Filtering

**User Story:** As a Performance Engineer, I want fuzzy matching to filter candidates before semantic similarity, so that we reduce expensive API calls from 1000+ to 10 per entity.

#### Acceptance Criteria

1. WHEN searching for duplicates, THE System SHALL first use fuzzy matching to identify top 10 candidates

2. WHEN fuzzy matching returns fewer than 10 candidates above threshold, THE System SHALL only compute semantic similarity for those candidates

3. THE System SHALL skip semantic similarity calculation if fuzzy matching score >= 0.95 (obvious duplicate)

4. THE System SHALL add rapidfuzz library to requirements.txt for 10-100x faster fuzzy matching

5. WHEN fuzzy-first filtering is enabled, THE System SHALL reduce API calls by 90-95% compared to comparing against all entities

### Requirement 21: Structured Logging Framework

**User Story:** As a DevOps Engineer, I want structured logging with log levels and log files, so that I can debug issues and monitor system health in production.

#### Acceptance Criteria

1. THE System SHALL use Python's logging framework instead of print() statements for all output

2. THE System SHALL configure log levels: DEBUG for detailed tracing, INFO for normal operations, WARNING for recoverable issues, ERROR for failures

3. THE System SHALL write logs to both console and rotating log files in logs/ directory

4. THE System SHALL include timestamp, log level, module name, and message in all log entries

5. THE System SHALL log all consolidation decisions (merge, skip, contradiction) at INFO level with entity details

### Requirement 22: Comprehensive Testing Suite

**User Story:** As a QA Engineer, I want comprehensive unit and integration tests, so that I can verify system correctness and catch regressions.

#### Acceptance Criteria

1. THE System SHALL have unit tests for DuplicateDetector covering fuzzy matching, semantic similarity, and name normalization

2. THE System SHALL have unit tests for EntityMerger covering description combination, contradiction detection, and source tracking

3. THE System SHALL have unit tests for ConsensusScorer covering confidence calculation with various source counts and contradictions

4. THE System SHALL have integration tests for end-to-end consolidation with real duplicate entities

5. THE System SHALL have performance tests measuring consolidation time and memory usage with 1000+ entities

### Requirement 23: Rollback Mechanism Implementation

**User Story:** As a Data Quality Manager, I want to rollback incorrect consolidations, so that I can fix mistakes without losing data or manual intervention.

#### Acceptance Criteria

1. WHEN entities are merged, THE System SHALL store entity snapshots in consolidation_audit table before modification

2. THE System SHALL provide a rollback_consolidation(audit_id, reason) function that restores original entities

3. WHEN rollback is executed, THE System SHALL restore original entity data from snapshots

4. WHEN rollback is executed, THE System SHALL update all relationships to point back to original entities

5. THE System SHALL mark audit records with rollback_timestamp and rollback_reason after successful rollback

### Requirement 24: Configuration Tuning for Production

**User Story:** As a Data Scientist, I want similarity thresholds and consensus parameters tuned for 44 interviews, so that consolidation accuracy is optimized for our dataset size.

#### Acceptance Criteria

1. THE System SHALL lower similarity thresholds to 0.70-0.75 for pain_points and processes to catch more duplicates

2. THE System SHALL adjust source_count_divisor to 5 (20% of 44 interviews = 1.0 confidence) instead of 10

3. THE System SHALL add single_source_penalty of 0.3 to reduce confidence for entities mentioned by only one person

4. THE System SHALL increase contradiction_penalty to 0.25 to more heavily penalize conflicting information

5. THE System SHALL document all configuration parameters with rationale and tuning guidance

### Requirement 25: Monitoring and Metrics Collection

**User Story:** As a System Administrator, I want consolidation metrics collected and exported, so that I can monitor system health and identify issues.

#### Acceptance Criteria

1. THE System SHALL collect metrics: duplicates_by_type, avg_similarity_by_type, contradictions_by_type, processing_time_by_type

2. THE System SHALL track API call metrics: total_calls, cache_hits, cache_misses, failed_calls

3. THE System SHALL calculate quality metrics: duplicate_reduction_percentage, avg_confidence_score, contradiction_rate

4. THE System SHALL export metrics to JSON file after each consolidation run

5. THE System SHALL display summary metrics in console with color-coded status (green for good, yellow for warnings, red for errors)

## Success Criteria

### Data Quality
- ✅ Duplicate entities reduced by 80-95% (e.g., 25 Excel entries → 1 consolidated entry)
- ✅ All consolidated entities have source_count >= 1
- ✅ Average consensus_confidence >= 0.75 across all entity types
- ✅ <10% of entities flagged with has_contradictions = true
- ✅ All relationships point to valid consolidated entities

### Performance
- ✅ Consolidation completes in under 5 minutes for 44 interviews (with optimizations)
- ✅ Duplicate detection query time < 1 second per entity
- ✅ Incremental consolidation < 10 seconds per new interview
- ✅ Total extraction + consolidation time < 20 minutes
- ✅ API calls reduced by 90-95% through fuzzy-first filtering and embedding caching

### Security & Reliability
- ✅ No SQL injection vulnerabilities (entity type whitelist enforced)
- ✅ All consolidation operations wrapped in transactions
- ✅ API failures handled with retry logic and circuit breaker
- ✅ All sensitive data (API keys) stored in environment variables only

### Intelligence
- ✅ Relationships discovered between entities (System → Pain Point, Process → System)
- ✅ Recurring patterns identified (mentioned in 30%+ of interviews)
- ✅ Contradictions detected and flagged for review
- ✅ Consensus confidence scores enable prioritization
- ✅ Can answer questions like "What systems cause the most pain?" with accurate counts

### Maintainability
- ✅ Configurable similarity thresholds per entity type (tuned for 44 interviews)
- ✅ Audit trail for all consolidation operations
- ✅ Rollback capability for incorrect merges (with entity snapshots)
- ✅ Comprehensive consolidation reports with metrics
- ✅ Structured logging with log levels and log files
- ✅ Comprehensive test suite (unit, integration, performance tests)
- ✅ Monitoring metrics exported to JSON for analysis
