"""
MetaOrchestrator - Multi-Agent Workflow Coordination
Orchestrates extraction, validation, re-extraction, and storage with iterative refinement
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass


@dataclass
class ProcessingResult:
    """Result of processing a single interview"""
    success: bool
    interview_id: Optional[int] = None
    entities: Dict[str, List[Dict]] = None
    entity_count: int = 0
    validation_passed: bool = False
    quality_score: float = 0.0
    iterations: int = 1
    missing_entities: List[str] = None
    consistency_issues: int = 0
    hallucination_issues: int = 0
    error: Optional[str] = None
    processing_time: float = 0.0
    api_cost: float = 0.0


class MetaOrchestrator:
    """
    Meta-orchestration layer for multi-agent workflow
    Coordinates extraction → validation → re-extraction → storage
    """

    def __init__(
        self,
        db,
        extractor,
        validation_agent=None,
        reviewer=None,
        storage_agent=None,
        monitor=None,
        config: Dict = None
    ):
        """
        Initialize meta-orchestrator with all agents

        Args:
            db: Database instance
            extractor: IntelligenceExtractor instance
            validation_agent: ValidationAgent instance (optional)
            reviewer: EnsembleReviewer instance (optional)
            storage_agent: StorageAgent instance (optional)
            monitor: ExtractionMonitor instance (optional)
            config: Configuration dictionary
        """
        self.db = db
        self.extractor = extractor
        self.validation_agent = validation_agent
        self.reviewer = reviewer
        self.storage_agent = storage_agent
        self.monitor = monitor
        self.config = config or {}

        # Get configuration
        self.max_iterations = self.config.get("validation", {}).get("max_reextraction_iterations", 2)
        self.enable_consistency_check = self.config.get("validation", {}).get("enable_consistency_check", True)
        self.enable_hallucination_check = self.config.get("validation", {}).get("enable_hallucination_detection", True)
        self.enable_focused_reextraction = self.config.get("validation", {}).get("enable_focused_reextraction", True)

        print(f"🎯 MetaOrchestrator initialized:")
        print(f"   Max iterations: {self.max_iterations}")
        print(f"   Consistency check: {'enabled' if self.enable_consistency_check else 'disabled'}")
        print(f"   Hallucination detection: {'enabled' if self.enable_hallucination_check else 'disabled'}")

    def process_interview(
        self,
        interview: Dict,
        enable_iterative_refinement: bool = True
    ) -> ProcessingResult:
        """
        Process a single interview with multi-agent workflow

        Workflow:
        1. Extract entities
        2. Validate (completeness, quality, consistency, hallucination)
        3. Re-extract if needed (focused on missing entities)
        4. Synthesize with ensemble (if enabled)
        5. Store in database

        Args:
            interview: Interview data
            enable_iterative_refinement: Enable re-extraction for missing entities

        Returns:
            ProcessingResult with detailed metrics
        """
        start_time = time.time()
        meta = interview.get("meta", {})
        qa_pairs = interview.get("qa_pairs", {})
        company = meta.get("company", "Unknown")
        respondent = meta.get("respondent", "Unknown")

        print(f"\n🎯 MetaOrchestrator: Processing {respondent} ({company})")

        # Initialize result
        result = ProcessingResult(
            success=False,
            entities={},
            missing_entities=[],
            error=None
        )

        # Stage 1: Extract interview record
        interview_id = self.db.insert_interview(meta, qa_pairs)
        if not interview_id:
            result.error = "Interview already processed"
            return result

        result.interview_id = interview_id
        self.db.update_extraction_status(interview_id, "in_progress")

        # Stage 2: Initial extraction with potential iterations
        iteration = 0
        entities = {}
        missing_entities = []
        completeness_results = {}
        quality_results = {}
        consistency_issues = []
        hallucination_issues = []

        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n  📥 Extraction iteration {iteration}/{self.max_iterations}")

            try:
                # Extract entities (focused on missing types if iteration > 1)
                if iteration == 1 or not self.enable_focused_reextraction:
                    # Full extraction
                    entities = self.extractor.extract_all(meta, qa_pairs)
                else:
                    # Focused re-extraction for missing entity types
                    print(f"     🎯 Focused re-extraction for: {', '.join(missing_entities)}")
                    new_entities = self._reextract_missing(meta, qa_pairs, missing_entities)
                    # Merge with existing entities
                    for entity_type, entity_list in new_entities.items():
                        entities[entity_type] = entities.get(entity_type, []) + entity_list

            except Exception as e:
                result.error = f"Extraction failed: {str(e)[:200]}"
                self.db.update_extraction_status(interview_id, "failed", result.error)
                result.processing_time = time.time() - start_time
                return result

            # Stage 3: Validation (if agent enabled)
            if self.validation_agent:
                print(f"  🔍 Running validation...")

                # Completeness check
                missing_entities, completeness_results = self.validation_agent.validate_entities(
                    entities, qa_pairs, meta
                )

                # Quality check
                quality_results = self.validation_agent.validate_quality(entities)

                # Consistency check
                if self.enable_consistency_check:
                    consistency_issues = self.validation_agent.validate_consistency(entities)

                # Hallucination detection
                if self.enable_hallucination_check:
                    interview_text = " ".join(qa_pairs.values())
                    hallucination_issues = self.validation_agent.detect_hallucinations(
                        entities, interview_text, threshold=0.4
                    )

                # Check if we need another iteration
                if missing_entities and enable_iterative_refinement and iteration < self.max_iterations:
                    print(f"     ⚠️  Missing entities: {', '.join(missing_entities)}")
                    print(f"     🔄 Triggering re-extraction...")
                    continue
                else:
                    # Validation complete
                    break

            else:
                # No validation agent, exit loop
                break

        result.iterations = iteration

        # Stage 4: Ensemble review (if enabled)
        if self.reviewer:
            print(f"  ✨ Running ensemble review...")
            try:
                review_results = self.reviewer.review_all_entities(entities, qa_pairs, meta)

                # Replace with synthesized results
                for entity_type, review in review_results.items():
                    entities[entity_type] = review.synthesized_result

                    # Add review metrics
                    for entity in entities[entity_type]:
                        entity["_review_metrics"] = review.metrics.to_dict()

            except Exception as e:
                print(f"     ⚠️  Ensemble review failed: {str(e)}")

        # Stage 5: Store entities
        print(f"  💾 Storing entities...")
        try:
            if self.storage_agent:
                # Use storage agent with transactions
                storage_result = self.storage_agent.store_all(entities, interview_id, company, meta)
                storage_success = storage_result.get("success", False)
                storage_errors = storage_result.get("errors", [])
            else:
                # Fallback to direct storage
                storage_errors = self._store_entities_direct(entities, interview_id, company, meta)
                storage_success = len(storage_errors) == 0

            if storage_success:
                print(f"     ✓ Storage complete")
            else:
                print(f"     ⚠️  Storage completed with {len(storage_errors)} errors")

        except Exception as e:
            result.error = f"Storage failed: {str(e)[:200]}"
            self.db.update_extraction_status(interview_id, "failed", result.error)
            result.processing_time = time.time() - start_time
            return result

        # Stage 6: Calculate final metrics
        result.entities = entities
        result.entity_count = sum(len(v) for v in entities.values())
        result.missing_entities = missing_entities
        result.consistency_issues = len(consistency_issues)
        result.hallucination_issues = len(hallucination_issues)

        # Calculate quality score
        if quality_results:
            total_entities = sum(len(results) for results in quality_results.values())
            valid_entities = sum(sum(1 for r in results if r.is_valid) for results in quality_results.values())
            result.quality_score = valid_entities / total_entities if total_entities > 0 else 0.0
        else:
            result.quality_score = 1.0  # Assume valid if no validation

        result.validation_passed = (
            len(missing_entities) == 0 and
            result.consistency_issues == 0 and
            result.quality_score > 0.7
        )

        # Update status
        self.db.update_extraction_status(interview_id, "complete")

        result.success = True
        result.processing_time = time.time() - start_time

        # Print summary
        print(f"\n  ✅ Processing complete:")
        print(f"     Entities: {result.entity_count}")
        print(f"     Quality: {result.quality_score:.2%}")
        print(f"     Iterations: {result.iterations}")
        print(f"     Time: {result.processing_time:.1f}s")

        return result

    def _reextract_missing(
        self,
        meta: Dict,
        qa_pairs: Dict,
        missing_entity_types: List[str]
    ) -> Dict[str, List[Dict]]:
        """
        Focused re-extraction for missing entity types only

        Args:
            meta: Interview metadata
            qa_pairs: Interview Q&A pairs
            missing_entity_types: List of entity types to extract

        Returns:
            Dictionary of newly extracted entities
        """
        # For now, use the extractor's extract methods directly
        # This could be optimized to call specific extractors for specific types
        entities = {}

        for entity_type in missing_entity_types:
            try:
                # Map entity type to extraction method
                method_name = f"extract_{entity_type}"
                if hasattr(self.extractor, method_name):
                    extract_method = getattr(self.extractor, method_name)
                    entities[entity_type] = extract_method(meta, qa_pairs)
                else:
                    print(f"     ⚠️  No extraction method for {entity_type}")

            except Exception as e:
                print(f"     ❌ Re-extraction failed for {entity_type}: {str(e)[:50]}")
                entities[entity_type] = []

        return entities

    def _store_entities_direct(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int,
        company: str,
        meta: Dict
    ) -> List[str]:
        """
        Direct storage without storage agent (fallback)

        Returns:
            List of error messages
        """
        storage_errors = []
        business_unit = meta.get("business_unit", meta.get("department", "Unknown"))

        # Store v1.0 entities
        for pain_point in entities.get("pain_points", []):
            try:
                self.db.insert_pain_point(interview_id, company, pain_point)
            except Exception as e:
                storage_errors.append(f"pain_point: {str(e)[:50]}")

        for process in entities.get("processes", []):
            try:
                self.db.insert_process(interview_id, company, process)
            except Exception as e:
                storage_errors.append(f"process: {str(e)[:50]}")

        for system in entities.get("systems", []):
            try:
                self.db.insert_or_update_system(system, company)
            except Exception as e:
                storage_errors.append(f"system: {str(e)[:50]}")

        for kpi in entities.get("kpis", []):
            try:
                self.db.insert_kpi(interview_id, company, kpi)
            except Exception as e:
                storage_errors.append(f"kpi: {str(e)[:50]}")

        for automation in entities.get("automation_candidates", []):
            try:
                self.db.insert_automation_candidate(interview_id, company, automation)
            except Exception as e:
                storage_errors.append(f"automation: {str(e)[:50]}")

        for inefficiency in entities.get("inefficiencies", []):
            try:
                self.db.insert_inefficiency(interview_id, company, inefficiency)
            except Exception as e:
                storage_errors.append(f"inefficiency: {str(e)[:50]}")

        # Store v2.0 entities
        for channel in entities.get("communication_channels", []):
            try:
                self.db.insert_communication_channel(interview_id, company, business_unit, channel)
            except Exception as e:
                storage_errors.append(f"communication_channel: {str(e)[:50]}")

        for decision in entities.get("decision_points", []):
            try:
                self.db.insert_decision_point(interview_id, company, business_unit, decision)
            except Exception as e:
                storage_errors.append(f"decision_point: {str(e)[:50]}")

        for flow in entities.get("data_flows", []):
            try:
                self.db.insert_data_flow(interview_id, company, business_unit, flow)
            except Exception as e:
                storage_errors.append(f"data_flow: {str(e)[:50]}")

        for pattern in entities.get("temporal_patterns", []):
            try:
                self.db.insert_temporal_pattern(interview_id, company, business_unit, pattern)
            except Exception as e:
                storage_errors.append(f"temporal_pattern: {str(e)[:50]}")

        for failure in entities.get("failure_modes", []):
            try:
                self.db.insert_failure_mode(interview_id, company, business_unit, failure)
            except Exception as e:
                storage_errors.append(f"failure_mode: {str(e)[:50]}")

        for team in entities.get("team_structures", []):
            try:
                self.db.insert_team_structure(interview_id, company, business_unit, team)
            except Exception as e:
                storage_errors.append(f"team_structure: {str(e)[:50]}")

        for gap in entities.get("knowledge_gaps", []):
            try:
                self.db.insert_knowledge_gap(interview_id, company, business_unit, gap)
            except Exception as e:
                storage_errors.append(f"knowledge_gap: {str(e)[:50]}")

        for pattern in entities.get("success_patterns", []):
            try:
                self.db.insert_success_pattern(interview_id, company, business_unit, pattern)
            except Exception as e:
                storage_errors.append(f"success_pattern: {str(e)[:50]}")

        for constraint in entities.get("budget_constraints", []):
            try:
                self.db.insert_budget_constraint(interview_id, company, business_unit, constraint)
            except Exception as e:
                storage_errors.append(f"budget_constraint: {str(e)[:50]}")

        for dependency in entities.get("external_dependencies", []):
            try:
                self.db.insert_external_dependency(interview_id, company, business_unit, dependency)
            except Exception as e:
                storage_errors.append(f"external_dependency: {str(e)[:50]}")

        return storage_errors
