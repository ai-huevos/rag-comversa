# Implementation Plan: Intelligent Knowledge Graph Extraction System

## Overview

This implementation plan builds a complete intelligent extraction system that gets smarter with every interview. The plan is organized into 3 phases that build upon each other in logical order.

**Goal**: Transform from isolated data extraction to an intelligent knowledge graph that consolidates entities, discovers relationships, detects patterns, and validates through consensus.

---

## Phase 1: Core Extraction & Storage ✅ COMPLETE

- [x] 1. Consolidate extraction logic to use v2.0 extractors
  - Remove duplicate v1.0 extraction methods from `extractor.py`
  - Update `IntelligenceExtractor` to be a thin orchestrator
  - Initialize all 16 extractors from `extractors.py` in `__init__()`
  - Update `extract_all()` to delegate to specialized extractors
  - Add error handling for each extractor
  - _Requirements: 1, 2_

- [x] 1.1 Update IntelligenceExtractor class structure
  - Import all extractor classes from `extractors.py`
  - Create dictionary of extractors in `__init__()`
  - Remove old `_extract_*()` methods
  - _Requirements: 1, 2_

- [x] 1.2 Implement delegating extract_all() method
  - Loop through all extractors
  - Call `extract_from_interview()` for each
  - Collect results in unified dict
  - Add progress logging for each entity type
  - _Requirements: 1, 2_

- [x] 1.3 Add error handling and fallback
  - Wrap each extractor call in try/except
  - Log errors but continue processing
  - Return empty list for failed extractions
  - Track failed extractions for reporting
  - _Requirements: 2, 8_

- [x] 2. Update processor to store all 17 entity types
  - Add storage calls for v2.0 entities in `process_interview()`
  - Extract business_unit from meta for v2.0 entities
  - Add error handling for each storage operation
  - Update progress reporting to show all entity types
  - _Requirements: 3_

- [x] 2.1 Add v2.0 entity storage calls
  - Add calls to `insert_communication_channel()`
  - Add calls to `insert_decision_point()`
  - Add calls to `insert_data_flow()`
  - Add calls to `insert_temporal_pattern()`
  - Add calls to `insert_failure_mode()`
  - Add calls to `insert_team_structure()`
  - Add calls to `insert_knowledge_gap()`
  - Add calls to `insert_success_pattern()`
  - Add calls to `insert_budget_constraint()`
  - Add calls to `insert_external_dependency()`
  - _Requirements: 3_

- [x] 2.2 Add storage error handling
  - Wrap each storage call in try/except
  - Log errors with entity type and details
  - Continue processing remaining entities
  - Track storage failures for reporting
  - _Requirements: 3, 8_

- [x] 3. Add lightweight quality validation (always on)
  - Create `validate_entity_quality()` function
  - Check required fields are populated
  - Check description length (min 20 chars)
  - Check for placeholder values ("unknown", "n/a", "tbd")
  - Check for encoding issues (escape sequences)
  - _Requirements: 5, 10_

- [x] 3.1 Create validation utility module
  - Create `intelligence_capture/validation.py`
  - Define required fields per entity type
  - Implement field validation functions
  - Implement encoding validation
  - _Requirements: 5, 10_

- [x] 3.2 Integrate validation into processor
  - Call validation after extraction
  - Log quality issues
  - Flag entities needing review
  - Optionally retry extraction on critical issues
  - _Requirements: 5, 10_

- [x] 4. Add extraction progress tracking
  - Add extraction_status column to interviews table
  - Add extraction_attempts column to interviews table
  - Add last_extraction_error column to interviews table
  - Update status during processing (pending → in_progress → complete/failed)
  - Implement resume capability
  - _Requirements: 8_

- [x] 4.1 Create database migration for progress tracking
  - Add new columns to interviews table
  - Create migration script
  - Test migration on sample database
  - _Requirements: 8_

- [x] 4.2 Implement status tracking in processor
  - Update status to "in_progress" at start
  - Update status to "complete" on success
  - Update status to "failed" on error with error message
  - Increment extraction_attempts counter
  - _Requirements: 8_

- [x] 4.3 Implement resume capability
  - Add `get_interviews_by_status()` method to database
  - Add `resume` parameter to `process_all_interviews()`
  - Filter interviews by status when resuming
  - _Requirements: 8_

---

## Phase 2: Validation & Quality Infrastructure

- [ ] 5. Implement ValidationAgent for completeness checking
  - Create `intelligence_capture/validation_agent.py`
  - Implement rule-based validation (fast, no LLM calls)
  - Implement optional LLM-based validation for critical entity types
  - Add automatic re-extraction for missing entities
  - _Requirements: 5, 6, 7_

- [ ] 5.1 Create ValidationAgent class
  - Create ValidationAgent class with `validate_entities()` method
  - Define entity type keywords for heuristic checks
  - Implement `_should_have_entities()` heuristic
  - Implement `_check_entity_quality()` method
  - _Requirements: 5_

- [ ] 5.2 Implement rule-based validation
  - Check for empty entity types that should have data
  - Check entity quality (required fields, description length)
  - Check for placeholder values ("unknown", "n/a", "tbd")
  - Check for encoding issues (escape sequences)
  - _Requirements: 5, 10_

- [ ] 5.3 Implement optional LLM validation
  - Create lightweight LLM prompt for completeness check
  - Only validate critical entity types (pain_points, processes, automation_candidates)
  - Flag missing entities for re-extraction
  - _Requirements: 5_

- [ ] 5.4 Integrate validation into extraction workflow
  - Update processor to call validation after extraction
  - Re-extract missing entities with focus mode
  - Track validation metrics (missing entities, re-extractions)
  - _Requirements: 5, 6_

- [ ] 6. Add real-time monitoring dashboard
  - Create `intelligence_capture/monitor.py`
  - Track metrics per interview (entities, time, cost, quality)
  - Print real-time summary after each interview
  - Generate final report at end
  - _Requirements: 9_

- [ ] 6.1 Create ExtractionMonitor class
  - Initialize metrics dictionary
  - Implement `record_interview()` method
  - Implement `record_error()` method
  - Implement `print_summary()` method
  - _Requirements: 9_

- [ ] 6.2 Implement real-time reporting
  - Show progress (X/44 interviews)
  - Show avg time per interview
  - Show estimated total cost
  - Show entity counts per type
  - Show quality issues per type
  - _Requirements: 9_

- [ ] 6.3 Integrate monitor into processor
  - Initialize monitor in processor
  - Call `record_interview()` after each interview
  - Call `print_summary()` periodically (every 5 interviews)
  - Generate final report at end
  - _Requirements: 9_

- [ ] 7. Create centralized extraction configuration
  - Create `config/extraction_config.json`
  - Define extraction settings (model, temperature, retries)
  - Define validation settings (thresholds, re-extraction)
  - Define quality thresholds
  - Load config in processor and extractor
  - _Requirements: 4, 6, 7_

- [ ] 7.1 Design configuration schema
  - Define extraction section (model, temperature, etc.)
  - Define validation section (thresholds, re-extraction)
  - Define quality_thresholds section
  - Define entity_types section (required vs optional)
  - _Requirements: 4, 6, 7_

- [ ] 7.2 Implement configuration loader
  - Create `load_extraction_config()` function in config.py
  - Load JSON config file
  - Provide defaults for missing values
  - Validate configuration values
  - _Requirements: 4, 6, 7_

- [ ] 7.3 Update components to use configuration
  - Update extractor to use config settings
  - Update processor to use config settings
  - Update validator to use config thresholds
  - _Requirements: 4, 6, 7_

- [ ] 8. Optimize database operations with batch inserts
  - Implement `insert_entities_batch()` method
  - Use transactions for batch inserts
  - Add rollback on error
  - _Requirements: 10_

- [ ] 8.1 Implement batch insert method
  - Create generic `insert_entities_batch()` in database
  - Start transaction before inserts
  - Commit after all inserts
  - Rollback on any error
  - _Requirements: 10_

- [ ] 8.2 Update processor to use batch inserts
  - Replace individual insert calls with batch calls
  - Group entities by type for batching
  - Add error handling for batch operations
  - _Requirements: 10_

---

## Phase 3: Intelligent Knowledge Graph System

- [ ] 13. Enable ensemble validation for final pass
  - Set ENABLE_ENSEMBLE_REVIEW=true
  - Choose mode (BASIC or FULL)
  - Re-run extraction on all interviews
  - Compare quality metrics with non-ensemble
  - _Requirements: 4_

- [ ] 13.1 Configure ensemble validation
  - Update .env with ENABLE_ENSEMBLE_REVIEW=true
  - Choose ENSEMBLE_MODE (basic or full)
  - Backup non-ensemble database
  - _Requirements: 4_

- [ ] 13.2 Run ensemble extraction
  - Run full extraction with ensemble enabled
  - Monitor time and cost (will be higher)
  - Track quality improvements
  - _Requirements: 4_

- [ ] 13.3 Compare ensemble vs non-ensemble
  - Compare entity counts
  - Compare quality scores
  - Compare processing time
  - Compare costs
  - Decide if ensemble is worth the cost
  - _Requirements: 4_

- [ ] 14. Add parallel processing for speed
  - Implement parallel interview processing
  - Use multiprocessing or threading
  - Handle shared database access
  - Add configuration flag for parallel mode
  - _Requirements: 6_

- [ ] 14.1 Design parallel processing architecture
  - Choose parallelization approach (multiprocessing vs threading)
  - Design worker pool
  - Handle database locking
  - _Requirements: 6_

- [ ] 14.2 Implement parallel processor
  - Create worker function for interview processing
  - Create process pool
  - Distribute interviews across workers
  - Collect results from workers
  - _Requirements: 6_

- [ ] 14.3 Test parallel processing
  - Test with 5 interviews
  - Verify no race conditions
  - Measure speedup vs sequential
  - Test with full 44 interviews
  - _Requirements: 6_

- [ ] 15. Create extraction report generator
  - Create `scripts/generate_extraction_report.py`
  - Generate comprehensive report with all metrics
  - Include entity counts, quality scores, costs
  - Export to Excel with multiple sheets
  - Add visualizations (charts, graphs)
  - _Requirements: 9_

- [ ] 15.1 Design report structure
  - Define report sections (summary, entities, quality, costs)
  - Design Excel layout with multiple sheets
  - Plan visualizations (entity distribution, quality scores)
  - _Requirements: 9_

- [ ] 15.2 Implement report generator
  - Query database for all metrics
  - Calculate summary statistics
  - Generate Excel workbook
  - Add charts and formatting
  - _Requirements: 9_

- [ ] 15.3 Test report generation
  - Generate report from test database
  - Verify all sections present
  - Check calculations are correct
  - Review visualizations
  - _Requirements: 9_

---

- [ ] 9. Implement Knowledge Consolidation Agent
  - Create `intelligence_capture/consolidation_agent.py`
  - Implement entity similarity matching (semantic + rule-based)
  - Implement entity merging with source tracking
  - Calculate consensus confidence scores
  - Detect contradictions between sources
  - _Requirements: 11_

- [ ] 9.1 Create consolidation agent class
  - Create KnowledgeConsolidationAgent class
  - Implement `find_similar_entities()` method
  - Implement `calculate_similarity()` method
  - Implement `merge_entities()` method
  - _Requirements: 11_

- [ ] 9.2 Implement similarity matching
  - Exact name matching for systems/processes
  - Semantic similarity using embeddings
  - Attribute overlap calculation
  - Weighted combination of similarity scores
  - _Requirements: 11_

- [ ] 9.3 Implement entity merging
  - Merge descriptions with source attribution
  - Deduplicate lists (pain_points, participants)
  - Average numerical values
  - Track source interviews
  - Calculate consensus confidence
  - _Requirements: 11_

- [ ] 9.4 Add consolidation tracking to database
  - Add mentioned_in_interviews column (JSON array)
  - Add source_count column
  - Add consensus_confidence column
  - Add has_contradictions column
  - Add is_pattern column
  - Create migration script
  - _Requirements: 11_

- [ ] 10. Implement Relationship Discovery Agent
  - Create `intelligence_capture/relationship_agent.py`
  - Discover team coordination relationships
  - Discover process dependencies
  - Discover shared pain points
  - Discover system integration relationships
  - _Requirements: 11_

- [ ] 10.1 Create relationship agent class
  - Create RelationshipDiscoveryAgent class
  - Implement `discover_relationships()` method
  - Implement `discover_team_coordination()` method
  - Implement `discover_shared_pain_points()` method
  - _Requirements: 11_

- [ ] 10.2 Create relationships database table
  - Create entity_relationships table
  - Add relationship_type, entity1, entity2 columns
  - Add mentioned_in_interviews, validated columns
  - Add confidence, metadata columns
  - _Requirements: 11_

- [ ] 10.3 Implement team coordination discovery
  - Parse communication channels for participants
  - Find cross-interview coordination mentions
  - Create validated relationships (both sides confirm)
  - Create unvalidated relationships (single source)
  - _Requirements: 11_

- [ ] 10.4 Implement shared pain point discovery
  - Find similar pain points across interviews
  - Group by semantic similarity
  - Track frequency and departments
  - Calculate priority scores
  - _Requirements: 11_

- [ ] 11. Implement Pattern Recognition Agent
  - Create `intelligence_capture/pattern_agent.py`
  - Detect recurring pain points (3+ mentions)
  - Detect system usage patterns
  - Detect communication patterns
  - Detect success patterns
  - _Requirements: 12_

- [ ] 11.1 Create pattern agent class
  - Create PatternRecognitionAgent class
  - Implement `recognize_patterns()` method
  - Implement `detect_pain_point_patterns()` method
  - Implement `detect_system_usage_patterns()` method
  - _Requirements: 12_

- [ ] 11.2 Create patterns database table
  - Create detected_patterns table
  - Add pattern_type, pattern_name columns
  - Add frequency, mentioned_in_interviews columns
  - Add priority_score, recommended_action columns
  - _Requirements: 12_

- [ ] 11.3 Implement pain point pattern detection
  - Cluster pain points by semantic similarity
  - Identify patterns with 3+ mentions
  - Calculate severity and priority scores
  - Generate recommended actions
  - _Requirements: 12_

- [ ] 11.4 Implement system usage pattern detection
  - Aggregate system mentions across interviews
  - Calculate average satisfaction scores
  - Identify common complaints
  - Flag low satisfaction + high usage systems
  - _Requirements: 12_

- [ ] 12. Implement Contradiction Detector
  - Create `intelligence_capture/contradiction_detector.py`
  - Detect conflicting information about same entity
  - Detect numerical contradictions (significant differences)
  - Detect categorical contradictions (different values)
  - Detect semantic contradictions (using LLM)
  - _Requirements: 11_

- [ ] 12.1 Create contradiction detector class
  - Create ContradictionDetector class
  - Implement `detect_contradictions()` method
  - Implement `identify_conflicts()` method
  - Implement `check_semantic_contradiction()` method
  - _Requirements: 11_

- [ ] 12.2 Create contradictions database table
  - Create contradictions table
  - Add entity_type, field, value1, value2 columns
  - Add interview1_id, interview2_id columns
  - Add severity, status, resolution columns
  - _Requirements: 11_

- [ ] 12.3 Implement conflict detection
  - Check numerical contradictions (>50% difference)
  - Check categorical contradictions (different values)
  - Check semantic contradictions (LLM-based)
  - Assign severity levels
  - Suggest resolution strategies
  - _Requirements: 11_

- [ ] 13. Integrate knowledge graph agents into orchestrator
  - Update MetaOrchestrator to call consolidation agent
  - Update MetaOrchestrator to call relationship agent
  - Update MetaOrchestrator to call pattern agent (every 5 interviews)
  - Update MetaOrchestrator to call contradiction detector
  - Update storage to handle relationships, patterns, contradictions
  - _Requirements: 11, 12_

- [ ] 13.1 Update orchestrator workflow
  - Add consolidation stage after validation
  - Add relationship discovery stage
  - Add pattern recognition stage (every 5 interviews)
  - Add contradiction detection stage
  - Update progress reporting
  - _Requirements: 11, 12_

- [ ] 13.2 Update storage agent
  - Add methods to store relationships
  - Add methods to store patterns
  - Add methods to store contradictions
  - Update transaction handling
  - _Requirements: 11, 12_

- [ ] 14. Test knowledge graph enrichment with 5 interviews
  - Test with 5 interviews
  - Verify entity consolidation working
  - Verify relationships discovered
  - Verify patterns detected
  - Verify contradictions flagged
  - _Requirements: 11, 12_

- [ ] 14.1 Test consolidation
  - Process 5 interviews with consolidation
  - Verify duplicate entities merged
  - Verify source tracking working
  - Verify consensus confidence calculated
  - _Requirements: 11_

- [ ] 14.2 Test relationship discovery
  - Verify team coordination relationships
  - Verify shared pain point relationships
  - Verify validated vs unvalidated relationships
  - Check relationship confidence scores
  - _Requirements: 11_

- [ ] 14.3 Test pattern recognition
  - Verify recurring pain points detected
  - Verify system usage patterns detected
  - Verify priority scores calculated
  - Check recommended actions generated
  - _Requirements: 12_

- [ ] 15. Run full extraction with intelligent knowledge graph
  - Process all 44 interviews with enrichment
  - Monitor consolidation metrics
  - Monitor relationship discovery
  - Monitor pattern detection
  - Generate knowledge graph summary report
  - _Requirements: 11, 12_

- [ ] 15.1 Backup existing database
  - Backup current database
  - Clear extraction status if needed
  - Configure for full knowledge graph extraction
  - _Requirements: 11, 12_

- [ ] 15.2 Execute full intelligent extraction
  - Run extraction with all knowledge graph agents
  - Track consolidation statistics (merged vs new entities)
  - Track relationship statistics (validated vs unvalidated)
  - Track pattern statistics (frequency, priority)
  - Monitor time and cost
  - _Requirements: 11, 12_

- [ ] 15.3 Generate knowledge graph intelligence report
  - Report total entities (consolidated vs raw extractions)
  - Report relationships discovered (by type)
  - Report patterns detected (with priorities and recommendations)
  - Report contradictions found (flagged for review)
  - Report high-confidence entities (3+ sources)
  - Calculate average consensus confidence
  - Generate actionable insights summary
  - _Requirements: 11, 12_

---

## Phase 4: Optional Performance Enhancements

**Note**: This phase is optional. Only implement if you need 3-5x speedup or forensic-grade ensemble validation.

- [ ] 16. Add parallel processing for speed
  - Implement parallel interview processing
  - Use multiprocessing with worker pool
  - Handle shared database access
  - Add configuration flag for parallel mode
  - _Requirements: 6_

- [ ] 16.1 Design parallel processing architecture
  - Choose parallelization approach (multiprocessing)
  - Design worker pool (4 workers recommended)
  - Handle database locking
  - _Requirements: 6_

- [ ] 16.2 Implement parallel processor
  - Create worker function for interview processing
  - Create process pool
  - Distribute interviews across workers
  - Collect results from workers
  - _Requirements: 6_

- [ ] 16.3 Test parallel processing
  - Test with 5 interviews
  - Verify no race conditions
  - Measure speedup vs sequential
  - Test with full 44 interviews
  - _Requirements: 6_

- [ ] 17. Enable ensemble validation for maximum quality
  - Set ENABLE_ENSEMBLE_REVIEW=true
  - Choose mode (BASIC or FULL)
  - Re-run extraction on all interviews
  - Compare quality metrics with standard extraction
  - _Requirements: 4_

- [ ] 17.1 Configure ensemble validation
  - Update .env with ENABLE_ENSEMBLE_REVIEW=true
  - Choose ENSEMBLE_MODE (basic or full)
  - Backup standard extraction database
  - _Requirements: 4_

- [ ] 17.2 Run ensemble extraction
  - Run full extraction with ensemble enabled
  - Monitor time and cost (will be higher)
  - Track quality improvements
  - _Requirements: 4_

- [ ] 17.3 Compare ensemble vs standard
  - Compare entity counts
  - Compare quality scores
  - Compare processing time
  - Compare costs
  - Decide if ensemble is worth the cost
  - _Requirements: 4_

- [ ] 18. Create comprehensive extraction report generator
  - Create `scripts/generate_extraction_report.py`
  - Generate comprehensive report with all metrics
  - Include entity counts, quality scores, costs
  - Export to Excel with multiple sheets
  - Add visualizations (charts, graphs)
  - _Requirements: 9_

- [ ] 18.1 Design report structure
  - Define report sections (summary, entities, quality, costs, knowledge graph)
  - Design Excel layout with multiple sheets
  - Plan visualizations (entity distribution, quality scores, patterns)
  - _Requirements: 9_

- [ ] 18.2 Implement report generator
  - Query database for all metrics
  - Calculate summary statistics
  - Generate Excel workbook
  - Add charts and formatting
  - Include knowledge graph insights
  - _Requirements: 9_

- [ ] 18.3 Test report generation
  - Generate report from test database
  - Verify all sections present
  - Check calculations are correct
  - Review visualizations
  - _Requirements: 9_

---

## Summary

**Total Tasks**: 18 top-level tasks, 60+ sub-tasks

**Reorganized Implementation Timeline**:

### Phase 1: Core Extraction & Storage ✅ COMPLETE
**Time**: 2-3 hours
**Status**: ✅ Complete
- All 17 entity types extracting and storing
- Progress tracking and resume capability

### Phase 2: Validation & Quality Infrastructure
**Time**: 2-3 hours
**Status**: 🔄 Ready to Start
- ValidationAgent for completeness
- Real-time monitoring dashboard
- Centralized configuration
- Batch database operations

### Phase 3: Intelligent Knowledge Graph System
**Time**: 3-4 hours
**Status**: ⏳ Depends on Phase 2
- Knowledge consolidation (merge duplicates)
- Relationship discovery (team coordination, dependencies)
- Pattern recognition (recurring issues, trends)
- Contradiction detection
- Full intelligent extraction

### Phase 4: Optional Performance Enhancements
**Time**: 1-2 hours
**Status**: ⏳ Optional
- Parallel processing (3-5x speedup)
- Ensemble validation (forensic quality)
- Comprehensive reporting

**Total Development Time**: 7-10 hours (Phases 2-3) or 8-12 hours (Phases 2-4)

---

## Success Criteria

### After Phase 2 (Validation Infrastructure)
- ✅ ValidationAgent operational
- ✅ Zero missing entities guaranteed
- ✅ Real-time monitoring functional
- ✅ Configuration-driven workflow

### After Phase 3 (Knowledge Graph)
- ✅ Entities consolidated across interviews
- ✅ Relationships discovered and validated
- ✅ Patterns detected (3+ mentions)
- ✅ Contradictions flagged for review
- ✅ Consensus confidence >0.85
- ✅ Actionable insights generated

### After Phase 4 (Optional Performance)
- ✅ 3-5x speedup with parallel processing
- ✅ Forensic-grade quality with ensemble
- ✅ Comprehensive Excel reports

---

## Expected Output

After completing Phases 2-3, you'll have:

```
📊 INTELLIGENT KNOWLEDGE GRAPH SUMMARY

Total Entities: 1,234 (consolidated from 2,156 raw extractions)
├─ Pain Points: 89 unique (mentioned 347 times total)
├─ Systems: 23 unique (mentioned 412 times total)
├─ Processes: 67 unique (mentioned 289 times total)
└─ ... (14 more types)

Relationships Discovered: 456
├─ Team Coordination: 127 (89 validated)
├─ Process Dependencies: 98
├─ Shared Pain Points: 156
└─ System Integration: 75

Patterns Detected: 23
🔥 TOP PATTERNS:
1. WhatsApp Tracking Issues (12 interviews, 4 depts) → Priority: 9.8
2. Opera PMS Slowness (18 interviews, avg satisfaction: 3.1/10) → Priority: 9.5
3. Manual Data Entry (15 interviews, 8h/week wasted) → Priority: 9.3

Contradictions Found: 7
⚠️  NEEDS REVIEW:
1. SAP usage (5 say essential, 3 say not used)
2. Maintenance SLA (reports vary: 15min to 24h)

High-Confidence Entities: 789 (mentioned by 3+ sources)
Consensus Confidence: 0.87 average

✨ Knowledge Graph is PRODUCTION-READY for AI Agents!
```

---

## Next Steps

**Immediate**: Start Phase 2, Task 5 (ValidationAgent)
**Then**: Complete Phase 2 (tasks 5-8)
**Then**: Complete Phase 3 (tasks 9-15) - Knowledge Graph
**Optional**: Phase 4 if you need speed/ensemble/reporting

**Ready to begin?** Open tasks.md and start with Task 5!
