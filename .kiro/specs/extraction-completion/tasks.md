# Implementation Plan: Complete & Optimize Intelligence Extraction System

## Overview

This implementation plan provides discrete, actionable tasks to complete and optimize the Intelligence Capture System. The plan is organized into 4 phases with clear dependencies and success criteria.

---

## Phase 1: Core Fixes & Integration

- [ ] 1. Consolidate extraction logic to use v2.0 extractors
  - Remove duplicate v1.0 extraction methods from `extractor.py`
  - Update `IntelligenceExtractor` to be a thin orchestrator
  - Initialize all 16 extractors from `extractors.py` in `__init__()`
  - Update `extract_all()` to delegate to specialized extractors
  - Add error handling for each extractor
  - _Requirements: 1, 2_

- [ ] 1.1 Update IntelligenceExtractor class structure
  - Import all extractor classes from `extractors.py`
  - Create dictionary of extractors in `__init__()`
  - Remove old `_extract_*()` methods
  - _Requirements: 1, 2_

- [ ] 1.2 Implement delegating extract_all() method
  - Loop through all extractors
  - Call `extract_from_interview()` for each
  - Collect results in unified dict
  - Add progress logging for each entity type
  - _Requirements: 1, 2_

- [ ] 1.3 Add error handling and fallback
  - Wrap each extractor call in try/except
  - Log errors but continue processing
  - Return empty list for failed extractions
  - Track failed extractions for reporting
  - _Requirements: 2, 8_

- [ ] 2. Update processor to store all 17 entity types
  - Add storage calls for v2.0 entities in `process_interview()`
  - Extract business_unit from meta for v2.0 entities
  - Add error handling for each storage operation
  - Update progress reporting to show all entity types
  - _Requirements: 3_

- [ ] 2.1 Add v2.0 entity storage calls
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

- [ ] 2.2 Add storage error handling
  - Wrap each storage call in try/except
  - Log errors with entity type and details
  - Continue processing remaining entities
  - Track storage failures for reporting
  - _Requirements: 3, 8_

- [ ] 3. Add lightweight quality validation (always on)
  - Create `validate_entity_quality()` function
  - Check required fields are populated
  - Check description length (min 20 chars)
  - Check for placeholder values ("unknown", "n/a", "tbd")
  - Check for encoding issues (escape sequences)
  - _Requirements: 5, 10_

- [ ] 3.1 Create validation utility module
  - Create `intelligence_capture/validation.py`
  - Define required fields per entity type
  - Implement field validation functions
  - Implement encoding validation
  - _Requirements: 5, 10_

- [ ] 3.2 Integrate validation into processor
  - Call validation after extraction
  - Log quality issues
  - Flag entities needing review
  - Optionally retry extraction on critical issues
  - _Requirements: 5, 10_

- [ ] 4. Add extraction progress tracking
  - Add extraction_status column to interviews table
  - Add extraction_attempts column to interviews table
  - Add last_extraction_error column to interviews table
  - Update status during processing (pending → in_progress → complete/failed)
  - Implement resume capability
  - _Requirements: 8_

- [ ] 4.1 Create database migration for progress tracking
  - Add new columns to interviews table
  - Create migration script
  - Test migration on sample database
  - _Requirements: 8_

- [ ] 4.2 Implement status tracking in processor
  - Update status to "in_progress" at start
  - Update status to "complete" on success
  - Update status to "failed" on error with error message
  - Increment extraction_attempts counter
  - _Requirements: 8_

- [ ] 4.3 Implement resume capability
  - Add `get_interviews_by_status()` method to database
  - Add `resume` parameter to `process_all_interviews()`
  - Filter interviews by status when resuming
  - _Requirements: 8_

---

## Phase 2: Optimization

- [ ] 5. Implement multi-agent validation workflow
  - Create `ValidationAgent` class for completeness checking
  - Implement rule-based validation (fast, no LLM calls)
  - Implement optional LLM-based validation for critical entity types
  - Add automatic re-extraction for missing entities
  - _Requirements: 5, 6, 7_

- [ ] 5.1 Create ValidationAgent class
  - Create `intelligence_capture/validation_agent.py`
  - Implement `validate_entities()` method
  - Define entity type keywords for heuristic checks
  - Implement `_should_have_entities()` heuristic
  - _Requirements: 5_

- [ ] 5.2 Implement rule-based validation
  - Check for empty entity types that should have data
  - Check entity quality (required fields, description length)
  - Check for placeholder values
  - Check for encoding issues
  - _Requirements: 5, 10_

- [ ] 5.3 Implement optional LLM validation
  - Create lightweight LLM prompt for completeness check
  - Only validate critical entity types (pain_points, processes, automation_candidates)
  - Flag missing entities for re-extraction
  - _Requirements: 5_

- [ ] 5.4 Integrate validation into extraction workflow
  - Call validation after initial extraction
  - Re-extract missing entities with focus mode
  - Track validation metrics (missing entities, re-extractions)
  - _Requirements: 5, 6_

- [ ] 6. Add real-time validation dashboard
  - Create `ExtractionMonitor` class
  - Track metrics per interview (entities, time, cost, quality)
  - Print real-time summary after each interview
  - Generate final report at end
  - _Requirements: 9_

- [ ] 6.1 Create ExtractionMonitor class
  - Create `intelligence_capture/monitor.py`
  - Initialize metrics dictionary
  - Implement `record_interview()` method
  - Implement `record_error()` method
  - _Requirements: 9_

- [ ] 6.2 Implement real-time reporting
  - Implement `print_summary()` method
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

- [ ] 7. Optimize database operations with batch inserts
  - Implement `insert_entities_batch()` method
  - Use transactions for batch inserts
  - Add rollback on error
  - _Requirements: 10_

- [ ] 7.1 Implement batch insert method
  - Create generic `insert_entities_batch()` in database
  - Start transaction before inserts
  - Commit after all inserts
  - Rollback on any error
  - _Requirements: 10_

- [ ] 7.2 Update processor to use batch inserts
  - Replace individual insert calls with batch calls
  - Group entities by type for batching
  - Add error handling for batch operations
  - _Requirements: 10_

- [ ] 8. Create centralized extraction configuration
  - Create `config/extraction_config.json`
  - Define extraction settings (model, temperature, retries)
  - Define validation settings (thresholds, ensemble mode)
  - Define entity type priorities (required vs optional)
  - Load config in processor and extractor
  - _Requirements: 4, 6, 7_

- [ ] 8.1 Design configuration schema
  - Define extraction section (model, temperature, etc.)
  - Define validation section (thresholds, ensemble mode)
  - Define quality_thresholds section
  - Define entity_types section (required vs optional)
  - _Requirements: 4, 6, 7_

- [ ] 8.2 Implement configuration loader
  - Create `load_extraction_config()` function in config.py
  - Load JSON config file
  - Provide defaults for missing values
  - Validate configuration values
  - _Requirements: 4, 6, 7_

- [ ] 8.3 Update components to use configuration
  - Update extractor to use config settings
  - Update processor to use config settings
  - Update validator to use config thresholds
  - _Requirements: 4, 6, 7_

---

## Phase 3: Testing & Validation

- [ ] 9. Create comprehensive validation script
  - Create `scripts/validate_extraction.py`
  - Check entity counts for all 17 types
  - Check interview coverage (all 44 processed)
  - Check referential integrity (no orphaned entities)
  - Check data quality (no empty fields, encoding issues)
  - Generate validation report
  - _Requirements: 5, 10_

- [ ] 9.1 Implement completeness checks
  - Query entity counts for all 17 types
  - Flag types with zero count
  - Check all 44 interviews are in database
  - Check all companies represented
  - _Requirements: 5_

- [ ] 9.2 Implement quality checks
  - Check for empty descriptions
  - Check for encoding issues (escape sequences)
  - Check for orphaned entities (invalid interview_id)
  - Check for duplicate entities
  - _Requirements: 5, 10_

- [ ] 9.3 Generate validation report
  - Create summary with pass/fail for each check
  - List specific issues found
  - Provide recommendations for fixes
  - Export to JSON and/or Excel
  - _Requirements: 5, 10_

- [ ] 10. Test with single interview
  - Run extraction on single interview
  - Verify all 17 entity types extracted
  - Verify all entities stored in database
  - Verify quality validation works
  - Verify progress tracking works
  - _Requirements: All_

- [ ] 10.1 Create test script
  - Create `scripts/test_single_interview.py`
  - Load first interview from dataset
  - Run extraction and storage
  - Run validation checks
  - Print detailed results
  - _Requirements: All_

- [ ] 10.2 Verify extraction results
  - Check entity counts per type
  - Inspect sample entities for quality
  - Verify database storage
  - Check for errors or warnings
  - _Requirements: All_

- [ ] 11. Test with 5 interviews
  - Run extraction on 5 interviews
  - Verify consistent results across interviews
  - Check performance metrics (time, cost)
  - Verify resume capability works
  - _Requirements: All_

- [ ] 11.1 Create test script for batch
  - Create `scripts/test_batch_interviews.py`
  - Load first 5 interviews
  - Run extraction with monitoring
  - Test resume by interrupting and restarting
  - _Requirements: All_

- [ ] 11.2 Analyze batch results
  - Check entity counts per interview
  - Calculate avg time per interview
  - Calculate avg cost per interview
  - Identify any quality issues
  - _Requirements: All_

- [ ] 12. Run full extraction (44 interviews)
  - Backup existing database
  - Run extraction on all 44 interviews
  - Monitor progress in real-time
  - Handle any errors gracefully
  - Generate final report
  - _Requirements: All_

- [ ] 12.1 Prepare for full extraction
  - Backup existing database
  - Clear extraction status (if re-running)
  - Configure extraction settings (batch mode, ensemble off)
  - _Requirements: All_

- [ ] 12.2 Execute full extraction
  - Run `python intelligence_capture/run.py`
  - Monitor real-time dashboard
  - Track time and cost
  - Handle any errors
  - _Requirements: All_

- [ ] 12.3 Validate full extraction results
  - Run validation script
  - Check all 17 entity types have data
  - Check all 44 interviews processed
  - Review quality metrics
  - Generate final report
  - _Requirements: All_

---

## Phase 4: Optional Enhancements

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

## Summary

**Total Tasks**: 15 top-level tasks, 45+ sub-tasks

**Implementation Timeline**:
- Phase 1 (Core Fixes): 2-3 hours
- Phase 2 (Optimization): 2-3 hours
- Phase 3 (Testing): 1-2 hours
- Phase 4 (Optional): 1-2 hours
- **Total**: 6-10 hours

**Key Milestones**:
- After Phase 1: All 17 entity types extracting and storing
- After Phase 2: Optimized for speed and cost
- After Phase 3: Validated and production-ready
- After Phase 4: Enhanced with optional features

**Success Criteria**:
- ✅ All 17 entity types extracted
- ✅ All 44 interviews processed
- ✅ Processing time: 15-20 min
- ✅ Cost: $0.50-$1.00
- ✅ Quality validation passing
- ✅ Resume capability working
- ✅ Real-time monitoring functional

**Next Steps**:
1. Review and approve this implementation plan
2. Start with Phase 1, Task 1 (consolidate extraction logic)
3. Test after each phase before proceeding
4. Generate final extraction report after Phase 3
