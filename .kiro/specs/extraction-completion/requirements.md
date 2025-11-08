# Requirements Document: Complete Intelligence Extraction System

## Introduction

This document defines requirements for completing and fixing the Intelligence Capture System to extract all 17 entity types from 44 interviews and produce a high-quality, validated database ready for AI agent use.

**Current State**:
- ✅ Database schema complete (17 entity types defined)
- ✅ Ensemble validation system implemented (forensic-grade quality review)
- ✅ v2.0 extractors exist in `extractors.py` (11 new entity types)
- ❌ Main `extractor.py` only extracts 6 v1.0 entity types
- ❌ `processor.py` only stores 6 v1.0 entity types
- ❌ No integration between v2.0 extractors and main pipeline
- ❌ Ensemble system enabled but adds complexity without solving core problem

**Target State**:
- One complete database with all 17 entity types
- All 44 interviews processed
- Quality validation via ensemble system (optional)
- Simple, maintainable extraction pipeline
- Fast processing (~30-45 min for 44 interviews)
- Cost-effective (~$1.50-$6.60 depending on ensemble mode)

## Glossary

- **Extraction System**: LLM-based system that processes interview transcripts to populate knowledge graph
- **Entity Type**: Category of business intelligence (e.g., PainPoint, Process, CommunicationChannel)
- **v1.0 Entities**: Original 6 entity types (PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency)
- **v2.0 Entities**: Enhanced 11 entity types (CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency, plus enhanced v1.0)
- **Ensemble Validation**: Multi-model extraction and synthesis for forensic-grade quality (optional)
- **Extractor**: Module responsible for extracting entities from interview text
- **Processor**: Module responsible for orchestrating extraction and storage
- **Database**: SQLite database storing all extracted entities

## Requirements

### Requirement 1: Complete Entity Extraction

**User Story:** As a Digital Transformation Officer, I want all 17 entity types extracted from interviews, so that I have complete operational intelligence for AI agents.

#### Acceptance Criteria

1. WHEN the Extraction System processes an interview, THE System SHALL extract all 17 entity types: PainPoint, Process, System, KPI, AutomationCandidate, Inefficiency, CommunicationChannel, DecisionPoint, DataFlow, TemporalPattern, FailureMode, TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency

2. WHEN extraction completes, THE System SHALL store all extracted entities in the database

3. THE System SHALL use existing v2.0 extractors from `extractors.py` for new entity types

4. THE System SHALL maintain backward compatibility with v1.0 extraction logic

5. WHEN all 44 interviews are processed, THE System SHALL have data for all 17 entity types in the database

### Requirement 2: Simplified Extraction Pipeline

**User Story:** As a System Maintainer, I want a simple, maintainable extraction pipeline, so that I can easily debug and extend the system.

#### Acceptance Criteria

1. THE Extraction System SHALL have a single entry point in `extractor.py` that orchestrates all entity extraction

2. WHEN extracting entities, THE System SHALL call specialized extractors from `extractors.py` for v2.0 entities

3. THE System SHALL handle extraction failures gracefully without stopping the entire pipeline

4. WHEN an extractor fails, THE System SHALL log the error and continue with remaining entity types

5. THE System SHALL provide clear progress indicators showing which entity types are being extracted

### Requirement 3: Integrated Storage Pipeline

**User Story:** As a Data Engineer, I want all extracted entities automatically stored in the database, so that no data is lost.

#### Acceptance Criteria

1. WHEN the Processor receives extracted entities, THE System SHALL store all 17 entity types in their respective database tables

2. THE System SHALL use existing database insert methods from `database.py` for all entity types

3. WHEN storing entities, THE System SHALL include organizational hierarchy (company, business_unit, department)

4. THE System SHALL link entities to their source interview via interview_id

5. WHEN storage fails for an entity, THE System SHALL log the error and continue with remaining entities

### Requirement 4: Optional Ensemble Validation

**User Story:** As a Quality Manager, I want optional ensemble validation, so that I can choose between speed and quality based on my needs.

#### Acceptance Criteria

1. THE System SHALL support ensemble validation as an optional feature controlled by environment variable ENABLE_ENSEMBLE_REVIEW

2. WHEN ENABLE_ENSEMBLE_REVIEW=false, THE System SHALL use single-model extraction (fast, cheap)

3. WHEN ENABLE_ENSEMBLE_REVIEW=true, THE System SHALL use ensemble validation (slower, higher quality)

4. THE System SHALL default to ENABLE_ENSEMBLE_REVIEW=false for production use

5. WHEN ensemble validation is disabled, THE System SHALL complete 44 interviews in approximately 30-45 minutes

### Requirement 5: Extraction Completeness Validation

**User Story:** As a Data Quality Manager, I want validation queries to verify extraction completeness, so that I can confirm all entity types have data.

#### Acceptance Criteria

1. THE System SHALL provide a validation script that checks entity counts for all 17 types

2. WHEN validation runs, THE System SHALL report count of entities per type

3. THE System SHALL flag entity types with zero count as missing

4. THE System SHALL check that all 44 interviews are represented in the database

5. THE System SHALL verify that all entities link to valid interviews (referential integrity)

### Requirement 6: Performance Optimization

**User Story:** As a System Administrator, I want fast extraction processing, so that I can iterate quickly during development.

#### Acceptance Criteria

1. WHEN processing 44 interviews with ensemble disabled, THE System SHALL complete in 30-45 minutes

2. WHEN processing 44 interviews with ensemble enabled (BASIC mode), THE System SHALL complete in 45-60 minutes

3. WHEN processing 44 interviews with ensemble enabled (FULL mode), THE System SHALL complete in 60-90 minutes

4. THE System SHALL use gpt-4o-mini as the primary model for cost-effectiveness

5. THE System SHALL implement rate limit handling with automatic retries

### Requirement 7: Cost Management

**User Story:** As a Budget Manager, I want predictable extraction costs, so that I can plan expenses.

#### Acceptance Criteria

1. WHEN processing 44 interviews with ensemble disabled, THE System SHALL cost approximately $1.50

2. WHEN processing 44 interviews with ensemble BASIC mode, THE System SHALL cost approximately $2.00

3. WHEN processing 44 interviews with ensemble FULL mode, THE System SHALL cost approximately $6.60

4. THE System SHALL log estimated costs after each interview

5. THE System SHALL provide a cost summary report after full extraction

### Requirement 8: Error Handling and Recovery

**User Story:** As a System Operator, I want robust error handling, so that extraction can recover from failures.

#### Acceptance Criteria

1. WHEN an API call fails, THE System SHALL retry up to 3 times with exponential backoff

2. WHEN rate limits are hit, THE System SHALL wait and retry automatically

3. WHEN an interview fails to process, THE System SHALL log the error and continue with remaining interviews

4. THE System SHALL track which interviews were successfully processed to enable resume

5. WHEN extraction is interrupted, THE System SHALL allow resuming from the last successful interview

### Requirement 9: Progress Reporting

**User Story:** As a System Operator, I want clear progress reporting, so that I can monitor extraction status.

#### Acceptance Criteria

1. WHEN processing interviews, THE System SHALL display progress as "[X/44] Processing..."

2. WHEN extracting entities, THE System SHALL show which entity types are being extracted

3. WHEN extraction completes, THE System SHALL display summary statistics (entities extracted per type)

4. THE System SHALL show processing time and estimated cost

5. THE System SHALL display any errors or warnings encountered during extraction

### Requirement 10: Database Integrity

**User Story:** As a Data Engineer, I want database integrity checks, so that I can trust the data quality.

#### Acceptance Criteria

1. THE System SHALL enforce foreign key constraints between entities and interviews

2. THE System SHALL prevent duplicate interviews using UNIQUE constraints

3. THE System SHALL validate that all required fields are populated before insertion

4. THE System SHALL check for orphaned entities (entities without valid interview_id)

5. THE System SHALL provide a database integrity check script

### Requirement 11: Knowledge Graph Consolidation

**User Story:** As a Business Intelligence Analyst, I want entities consolidated across interviews, so that I can see patterns and consensus from multiple sources.

#### Acceptance Criteria

1. WHEN processing an interview, THE System SHALL identify duplicate entities across interviews

2. WHEN duplicate entities are found, THE System SHALL merge them and track all source interviews

3. THE System SHALL calculate consensus confidence scores based on number of sources

4. THE System SHALL detect contradictions between different interview sources

5. THE System SHALL discover relationships between entities across interviews (team coordination, shared pain points)

### Requirement 12: Pattern Recognition

**User Story:** As a Digital Transformation Officer, I want recurring patterns identified automatically, so that I can prioritize systemic issues.

#### Acceptance Criteria

1. WHEN processing interviews, THE System SHALL detect recurring pain points mentioned by 3+ people

2. THE System SHALL identify system usage patterns (popularity, satisfaction trends)

3. THE System SHALL detect communication patterns across teams

4. THE System SHALL calculate priority scores for detected patterns

5. THE System SHALL generate recommended actions for high-priority patterns

### Requirement 13: Parallel Processing

**User Story:** As a System Administrator, I want parallel interview processing, so that I can process large batches quickly.

#### Acceptance Criteria

1. THE System SHALL support parallel processing of multiple interviews simultaneously

2. WHEN parallel processing is enabled, THE System SHALL use a configurable number of worker processes

3. THE System SHALL handle database locking and concurrent access safely

4. THE System SHALL provide 3-5x speedup compared to sequential processing

5. THE System SHALL maintain data integrity during parallel operations

### Requirement 14: Ensemble Validation

**User Story:** As a Quality Manager, I want forensic-grade ensemble validation, so that I can ensure maximum extraction quality for critical decisions.

#### Acceptance Criteria

1. THE System SHALL support ensemble validation using multiple LLM models

2. WHEN ensemble validation is enabled, THE System SHALL extract entities using multiple models

3. THE System SHALL synthesize results from multiple models into consensus entities

4. THE System SHALL calculate quality scores across multiple dimensions

5. THE System SHALL provide configurable ensemble modes (BASIC, FULL)

## Success Criteria

### Completeness
- ✅ All 17 entity types extracted
- ✅ All 44 interviews processed
- ✅ No missing entity types (count > 0 for all types)
- ✅ All entities linked to valid interviews

### Quality
- ✅ ValidationAgent operational
- ✅ Zero missing entities guaranteed
- ✅ 90%+ entities with quality score > 0.8
- ✅ <5% entities needing human review
- ✅ No empty descriptions or required fields
- ✅ Spanish characters correctly encoded (UTF-8)
- ✅ Confidence scores calculated for all entities

### Intelligence
- ✅ Entities consolidated across interviews
- ✅ Relationships discovered and validated
- ✅ Patterns detected (recurring issues)
- ✅ Contradictions flagged for review
- ✅ Consensus confidence >0.85
- ✅ Actionable insights generated

### Performance
- ✅ Processing time: 15-20 min (sequential) or 5-7 min (parallel)
- ✅ Cost: $2.00-$3.50 depending on features
- ✅ No rate limit failures
- ✅ Graceful error handling
- ✅ Resume capability

### Maintainability
- ✅ Simple, clear code structure
- ✅ Modular extractors for each entity type
- ✅ Comprehensive error logging
- ✅ Easy to add new entity types
- ✅ Configuration-driven workflow
- ✅ Real-time monitoring dashboard
- ✅ Comprehensive test coverage (>80%)
