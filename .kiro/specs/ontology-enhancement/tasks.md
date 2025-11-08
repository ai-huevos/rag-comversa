# Implementation Plan: Enhanced Ontology Schema

## Overview

This implementation plan converts the enhanced ontology design into discrete coding tasks. Each task builds incrementally on previous tasks and includes specific requirements references.

## Task Structure

- Top-level tasks represent major features or components
- Sub-tasks are specific implementation steps
- All tasks are required for comprehensive implementation
- All tasks reference specific requirements from requirements.md

---

## Phase 1: Foundation & Core v2.0 Entities

- [x] 1. Set up enhanced database schema with multi-level hierarchy
  - Create migration script to add v2.0 tables without breaking v1.0
  - Add organizational hierarchy fields (holding_name, company_name, business_unit, department) to all tables
  - Add metadata fields (confidence_score, needs_review, extraction_source, extraction_reasoning) to all tables
  - Create indexes for company-specific and cross-company queries
  - _Requirements: 15, 19_

- [x] 1.1 Extend database.py with v2.0 schema initialization
  - Add `init_v2_schema()` method to create new tables
  - Implement backward compatibility checks
  - Add migration utilities for backfilling v2.0 fields
  - _Requirements: 15, 19_

- [x] 1.2 Create organizational hierarchy configuration
  - Create `config/companies.json` with predefined hierarchy
  - Define business units for each company (Hotel, Comversa, Bolivian Foods)
  - Map industry contexts to business units
  - _Requirements: 15, 18_

- [x] 1.3 Write unit tests for database schema
  - Test table creation without data loss
  - Test organizational hierarchy queries
  - Test backward compatibility with v1.0 queries
  - _Requirements: 15_

- [x] 2. Implement CommunicationChannel entity extraction and storage
  - Create extraction prompt for communication channels
  - Implement confidence scoring for channel extractions
  - Add `insert_communication_channel()` method to database
  - Link communication channels to processes
  - _Requirements: 3, 8_

- [x] 2.1 Create CommunicationChannel database table
  - Define schema with channel_name, purpose, frequency, participants, response_sla_minutes
  - Add foreign key to interviews table
  - Add organizational hierarchy fields
  - _Requirements: 3_

- [x] 2.2 Implement communication channel extraction logic
  - Parse interview text for channel mentions (WhatsApp, Outlook, Teams, etc.)
  - Extract purpose and SLA information
  - Normalize response times to minutes
  - Calculate confidence score based on explicitness
  - _Requirements: 3_

- [x] 2.3 Write unit tests for CommunicationChannel extraction
  - Test extraction from sample interviews
  - Test SLA normalization ("inmediato" → 15 minutes)
  - Test confidence scoring
  - _Requirements: 3_

- [x] 3. Implement DecisionPoint entity extraction and storage
  - Create extraction prompt for decision points and escalation logic
  - Implement decision criteria parsing
  - Add `insert_decision_point()` method to database
  - Link decision points to processes
  - _Requirements: 4, 8_

- [x] 3.1 Create DecisionPoint database table
  - Define schema with decision_maker_role, decision_criteria, escalation_trigger, escalation_to_role
  - Add approval_required, approval_threshold, authority_limit_usd fields
  - Add organizational hierarchy fields
  - _Requirements: 4_

- [x] 3.2 Implement decision point extraction logic
  - Parse decision-making language ("yo decido", "requiere aprobación")
  - Extract decision criteria as structured list
  - Identify escalation triggers and targets
  - Extract authority limits and thresholds
  - _Requirements: 4_

- [x] 3.3 Write unit tests for DecisionPoint extraction
  - Test extraction of decision criteria
  - Test escalation logic parsing
  - Test authority limit extraction
  - _Requirements: 4_

- [x] 4. Implement DataFlow entity extraction and storage
  - Create extraction prompt for data movement between systems
  - Implement data quality issue detection
  - Add `insert_data_flow()` method to database
  - Link data flows to systems and processes
  - _Requirements: 5, 8_

- [x] 4.1 Create DataFlow database table
  - Define schema with source_system, target_system, data_type, transfer_method, transfer_frequency
  - Add data_quality_issues and pain_points fields
  - Add organizational hierarchy fields
  - _Requirements: 5_

- [x] 4.2 Implement data flow extraction logic
  - Parse data movement language ("paso datos de X a Y", "concilio entre")
  - Identify source and target systems
  - Classify transfer method (Manual, API, Export/Import)
  - Extract data quality issues
  - _Requirements: 5_

- [x] 4.3 Write unit tests for DataFlow extraction
  - Test system identification
  - Test transfer method classification
  - Test data quality issue extraction
  - _Requirements: 5_

- [x] 5. Implement TemporalPattern entity extraction and storage
  - Create extraction prompt for temporal patterns
  - Implement time normalization (convert "9am" to "09:00")
  - Add `insert_temporal_pattern()` method to database
  - Link temporal patterns to processes
  - _Requirements: 6, 8_

- [x] 5.1 Create TemporalPattern database table
  - Define schema with activity_name, frequency, time_of_day, duration_minutes
  - Add participants and triggers_actions fields
  - Add organizational hierarchy fields
  - _Requirements: 6_

- [x] 5.2 Implement temporal pattern extraction logic
  - Parse temporal language ("diario a las 9am", "cada lunes", "cierre mensual")
  - Normalize frequency to standard values
  - Extract and normalize time_of_day to 24-hour format
  - Extract duration if mentioned
  - _Requirements: 6_

- [x] 5.3 Write unit tests for TemporalPattern extraction
  - Test frequency normalization
  - Test time format conversion
  - Test duration extraction
  - _Requirements: 6_

- [x] 6. Implement FailureMode entity extraction and storage
  - Create extraction prompt for failure modes and recovery
  - Implement root cause analysis extraction
  - Add `insert_failure_mode()` method to database
  - Link failure modes to processes and automation candidates
  - _Requirements: 7, 8, 11_

- [x] 6.1 Create FailureMode database table
  - Define schema with failure_description, frequency, impact_description, current_workaround
  - Add root_cause, recovery_time_minutes, proposed_prevention fields
  - Add organizational hierarchy fields
  - _Requirements: 7_

- [x] 6.2 Implement failure mode extraction logic
  - Parse failure language ("se cae", "falla", "no funciona")
  - Extract workarounds and root causes
  - Identify proposed preventive solutions
  - Link to related automation candidates
  - _Requirements: 7_

- [x] 6.3 Write unit tests for FailureMode extraction
  - Test failure detection
  - Test root cause extraction
  - Test workaround identification
  - _Requirements: 7_

---

## Phase 2: Enhanced v1.0 Entities

- [x] 7. Enhance PainPoint entity with intensity, frequency, and JTBD context
  - Add new fields to pain_points table
  - Implement intensity scoring (1-10) based on language indicators
  - Implement frequency classification
  - Extract JTBD context (WHO, WHAT, WHERE)
  - Calculate hair_on_fire flag
  - _Requirements: 1, 2, 9_

- [x] 7.1 Extend pain_points table schema
  - Add intensity_score, frequency, hair_on_fire fields
  - Add time_wasted_per_occurrence_minutes, cost_impact_monthly_usd, estimated_annual_cost_usd
  - Add jtbd_who, jtbd_what, jtbd_where, jtbd_formatted fields
  - Add root_cause, current_workaround fields
  - _Requirements: 1, 2, 9_

- [x] 7.2 Implement pain point intensity scoring
  - Create language indicator mapping ("crítico" → 9, "urgente" → 8, "molesto" → 5)
  - Analyze context to determine intensity
  - Calculate confidence score for intensity assessment
  - _Requirements: 1_

- [x] 7.3 Implement JTBD context extraction
  - Extract WHO is affected (specific roles)
  - Extract WHAT job they're trying to accomplish
  - Extract WHERE in the process the pain occurs
  - Format as "When [situation], I want to [motivation], but [obstacle]"
  - _Requirements: 2_

- [x] 7.4 Implement cost quantification
  - Extract time wasted per occurrence
  - Extract cost impact if mentioned
  - Calculate estimated annual cost using formula from requirements
  - _Requirements: 9_

- [x] 7.5 Write unit tests for enhanced PainPoint extraction
  - Test intensity scoring accuracy
  - Test JTBD formatting
  - Test cost calculation
  - Test hair_on_fire flag logic
  - _Requirements: 1, 2, 9_

- [x] 8. Enhance System entity with integration pain points and satisfaction
  - Add new fields to systems table
  - Implement user satisfaction scoring based on sentiment
  - Extract integration pain points
  - Flag replacement candidates
  - _Requirements: 10_

- [x] 8.1 Extend systems table schema
  - Add integration_pain_points, data_quality_issues fields
  - Add user_satisfaction_score, replacement_candidate, adoption_rate fields
  - _Requirements: 10_

- [x] 8.2 Implement sentiment analysis for user satisfaction
  - Analyze sentiment in system mentions ("me gusta" → 8, "no sirve" → 2)
  - Calculate satisfaction score (1-10)
  - Flag replacement_candidate if score <= 3
  - _Requirements: 10_

- [x] 8.3 Write unit tests for enhanced System extraction
  - Test sentiment analysis accuracy
  - Test replacement candidate flagging
  - Test integration pain point extraction
  - _Requirements: 10_

- [x] 9. Enhance AutomationCandidate entity with monitoring and approval
  - Add new fields to automation_candidates table
  - Implement effort and impact scoring
  - Calculate priority quadrant classification
  - Extract monitoring metrics and approval requirements
  - _Requirements: 11, 14_

- [x] 9.1 Extend automation_candidates table schema
  - Add current_manual_process_description, data_sources_needed fields
  - Add approval_required, approval_threshold_usd, monitoring_metrics fields
  - Add effort_score, impact_score, priority_quadrant, estimated_roi_months fields
  - Add ceo_priority, overlooked_opportunity, data_support_score fields
  - _Requirements: 11, 14, 16_

- [x] 9.2 Implement effort scoring algorithm
  - Score based on number of systems involved (1 system → 1, 5+ systems → 5)
  - Adjust for complexity rating
  - Consider data integration requirements
  - _Requirements: 14_

- [x] 9.3 Implement impact scoring algorithm
  - Score based on pain point severity (1-10 → 1-5)
  - Weight by frequency (daily → +2, weekly → +1)
  - Consider number of affected roles
  - Factor in estimated cost savings
  - _Requirements: 14_

- [x] 9.4 Implement priority quadrant classification
  - Map (effort, impact) to quadrant: Quick Win, Strategic, Incremental, Reconsider
  - Calculate ROI if cost savings and implementation cost available
  - Rank within quadrant by ROI or impact
  - _Requirements: 14_

- [x] 9.5 Write unit tests for enhanced AutomationCandidate
  - Test effort scoring algorithm
  - Test impact scoring algorithm
  - Test quadrant classification
  - Test ROI calculation
  - _Requirements: 11, 14_

---

## Phase 3: CEO Validation & Analytics

- [x] 10. Implement CEO assumption validation framework
  - Create CEOAssumptionValidator class
  - Load CEO priorities from config/ceo_priorities.json
  - Calculate data support scores for each priority
  - Identify overlooked opportunities
  - Generate validation report
  - _Requirements: 16_

- [x] 10.1 Create CEO priorities configuration
  - Create config/ceo_priorities.json with RECALIBRACIÓN FASE 1 priorities
  - Map priorities to macroprocesos
  - Include effort and impact scores from CEO assessment
  - _Requirements: 16_

- [x] 10.2 Implement data support score calculation
  - Count interviews mentioning each CEO priority
  - Calculate score = (mentions / total interviews)
  - Flag priorities with low data support (< 0.3)
  - _Requirements: 16_

- [x] 10.3 Implement overlooked opportunity detection
  - Identify pain points mentioned in >= 30% of interviews
  - Check if pain point maps to any CEO priority
  - Flag as overlooked_opportunity if not in CEO list
  - Calculate potential ROI for overlooked opportunities
  - _Requirements: 16_

- [x] 10.4 Generate CEO validation report
  - Create report with confirmed priorities, weak priorities, overlooked opportunities
  - Include data support scores and evidence
  - Export to Excel for executive review
  - _Requirements: 16_

- [x] 10.5 Write unit tests for CEO validation
  - Test data support calculation
  - Test overlooked opportunity detection
  - Test report generation
  - _Requirements: 16_

- [x] 11. Implement cross-company pattern recognition
  - Create CrossCompanyAnalyzer class
  - Identify common pain points across companies
  - Calculate pain point prevalence
  - Detect standardization opportunities
  - Generate cross-company insights report
  - _Requirements: 13_

- [x] 11.1 Implement common pain point detection
  - Group similar pain points across companies using semantic similarity
  - Calculate prevalence = (companies affected / total companies)
  - Rank by prevalence and impact
  - _Requirements: 13_

- [x] 11.2 Implement standardization opportunity detection
  - Identify processes that exist in multiple companies
  - Compare implementations across companies
  - Flag standardization_opportunity if implementations differ significantly
  - _Requirements: 13_

- [x] 11.3 Generate cross-company insights report
  - Highlight shared challenges (pain points in all 3 companies)
  - Identify divergent approaches (same process, different implementations)
  - Suggest shared solutions and economies of scale
  - _Requirements: 13_

- [x] 11.4 Write unit tests for cross-company analysis
  - Test pain point similarity detection
  - Test prevalence calculation
  - Test standardization opportunity flagging
  - _Requirements: 13_

---

## Phase 4: Hierarchy Discovery & Validation

- [x] 12. Implement dynamic hierarchy discovery system
  - Create HierarchyDiscoverer class
  - Extract organizational mentions from interviews
  - Aggregate discoveries across all interviews
  - Validate against predefined hierarchy
  - Generate hierarchy validation report
  - _Requirements: 15, 19_

- [x] 12.1 Implement organizational structure extraction
  - Create extraction prompt for org structure mentions
  - Parse self-identified company, business unit, department
  - Extract reporting relationships
  - Identify coordinating departments
  - _Requirements: 15, 19_

- [x] 12.2 Store discovered org structure in interviews table
  - Add discovered_org_structure JSON field to interviews table
  - Add org_structure_validated, org_structure_confidence, org_structure_deviations fields
  - Store both predefined classification AND discovered structure
  - _Requirements: 15, 19_

- [x] 12.3 Implement hierarchy aggregation and validation
  - Aggregate org mentions across all interviews
  - Compare discovered vs predefined hierarchy
  - Identify naming inconsistencies
  - Detect new organizational units not in predefined hierarchy
  - _Requirements: 15_

- [x] 12.4 Generate hierarchy validation report
  - Create report with confirmed structure, naming inconsistencies, new discoveries
  - Include evidence (interview count, confidence scores)
  - Suggest hierarchy updates with priority levels
  - Export to Excel for human review
  - _Requirements: 15_

- [x] 12.5 Implement hierarchy update and reprocessing
  - Apply approved hierarchy updates to configuration
  - Reprocess affected interviews with corrected hierarchy
  - Update all related entities with corrected org structure
  - _Requirements: 15_

- [x] 12.6 Write unit tests for hierarchy discovery
  - Test org structure extraction
  - Test aggregation logic
  - Test validation against predefined
  - Test report generation
  - _Requirements: 15_

---

## Phase 5: RAG Database Generation

- [x] 13. Implement company-specific RAG database generator
  - Create RAGDatabaseGenerator class
  - Generate vector embeddings for all entities
  - Partition data by company
  - Build rich context by traversing entity relationships
  - Create queryable RAG database per company
  - _Requirements: 17_

- [x] 13.1 Implement entity context builder
  - Traverse relationships to build rich context (e.g., PainPoint → Process → Systems → FailureModes)
  - Format context as natural language text
  - Include all relevant metadata
  - _Requirements: 17_

- [x] 13.2 Implement embedding generation
  - Use OpenAI text-embedding-3-small model
  - Generate embeddings for each entity's context
  - Store embeddings with entity metadata
  - _Requirements: 17_

- [x] 13.3 Implement company-specific RAG database creation
  - Filter entities by company_name
  - Generate embeddings for company-specific entities
  - Create vector database (FAISS or similar)
  - Store metadata for retrieval
  - _Requirements: 17_

- [x] 13.4 Implement holding-level RAG database creation
  - Aggregate entities from all companies
  - Generate embeddings for cross-company insights
  - Create holding-level vector database
  - Enable cross-company queries
  - _Requirements: 17_

- [x] 13.5 Implement RAG query interface
  - Create query method with company filter
  - Implement semantic search using embeddings
  - Return relevant entities with context
  - Support natural language queries
  - _Requirements: 17_

- [x] 13.6 Write unit tests for RAG generation
  - Test context building
  - Test embedding generation
  - Test company-specific filtering
  - Test query interface
  - _Requirements: 17_

---

## Phase 6: Remaining v2.0 Entities

- [x] 14. Implement remaining v2.0 entities (TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, ExternalDependency)
  - Create database tables for 5 remaining entities
  - Implement extraction prompts for each entity type
  - Add insert methods to database class
  - Link entities to related processes and pain points
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.1 Implement TeamStructure entity
  - Create team_structures table
  - Extract team size, reporting relationships, coordination patterns
  - Identify external dependencies
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.2 Implement KnowledgeGap entity
  - Create knowledge_gaps table
  - Extract training needs and skill gaps
  - Identify affected roles and impact
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.3 Implement SuccessPattern entity
  - Create success_patterns table
  - Extract what works well and why
  - Identify replication opportunities
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.4 Implement BudgetConstraint entity
  - Create budget_constraints table
  - Extract budget limits and approval thresholds
  - Identify budget-related pain points
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.5 Implement ExternalDependency entity
  - Create external_dependencies table
  - Extract vendor relationships and SLAs
  - Identify coordination requirements
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

- [x] 14.6 Write unit tests for remaining entities
  - Test extraction for each entity type
  - Test database storage and retrieval
  - Test relationship linking
  - _Requirements: (from ONTOLOGY_BRAINSTORM.md)_

---

## Phase 7: Integration & Quality Assurance

- [ ] 15. Implement extraction quality validation
  - Add confidence scoring to all extraction methods
  - Implement needs_review flagging for low confidence
  - Add conflict detection across interviews
  - Generate extraction quality report
  - _Requirements: 12_

- [ ] 15.1 Implement confidence scoring algorithm
  - Score based on language clarity and explicitness
  - Adjust for context availability
  - Flag needs_review if confidence < 0.7
  - _Requirements: 12_

- [ ] 15.2 Implement conflict detection
  - Compare same entity extracted from different interviews
  - Flag conflicts when information contradicts
  - Store conflicting sources for human review
  - _Requirements: 12_

- [ ] 15.3 Generate extraction quality report
  - Report entities by confidence score
  - List entities needing review
  - Highlight conflicts requiring resolution
  - _Requirements: 12_

- [ ] 15.4 Write unit tests for quality validation
  - Test confidence scoring
  - Test conflict detection
  - Test report generation
  - _Requirements: 12_

- [ ] 16. Create end-to-end extraction pipeline
  - Implement main extraction script that processes all 44 interviews
  - Orchestrate all extraction steps in correct order
  - Generate comprehensive extraction report
  - Handle errors gracefully with logging
  - _Requirements: All_

- [x] 16.1 Implement batch processing
  - Process interviews in batches to manage API rate limits
  - Implement retry logic for API failures
  - Track progress and resume from failures
  - _Requirements: All_

- [x] 16.2 Generate comprehensive extraction report
  - Summary statistics (entities extracted, confidence scores, etc.)
  - CEO validation results
  - Hierarchy validation results
  - Cross-company insights
  - Quality metrics
  - _Requirements: All_

- [x] 16.3 Write integration tests
  - Test full pipeline on sample interviews
  - Test error handling and recovery
  - Test report generation
  - _Requirements: All_

- [ ] 17. Create documentation and examples
  - Write README with setup instructions
  - Document database schema
  - Provide example queries
  - Create usage examples for RAG databases
  - Document configuration options
  - _Requirements: All_

---

## Summary

**Total Tasks**: 17 top-level tasks, 60+ sub-tasks
**All Tasks Required**: Comprehensive implementation with full testing and documentation
**Estimated Timeline**: 6 weeks
**Implementation Tasks**: 43 sub-tasks
**Testing & Documentation**: 17 sub-tasks

**Key Milestones**:
- Week 2: Core v2.0 entities functional
- Week 3: Enhanced v1.0 entities complete
- Week 4: CEO validation and analytics working
- Week 5: RAG databases generated
- Week 6: Full system integrated and tested
