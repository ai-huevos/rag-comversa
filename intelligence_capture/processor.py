"""
Main processor for Intelligence Capture System
Reads interviews, extracts entities, stores in database
Enhanced with ensemble validation for forensic-grade quality
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from .database import IntelligenceDB, EnhancedIntelligenceDB
from .extractor import IntelligenceExtractor
from .validation import validate_extraction_results, print_validation_summary
from .validation_agent import ValidationAgent
from .monitor import ExtractionMonitor
from .config import DB_PATH, INTERVIEWS_FILE, EXTRACTION_CONFIG, load_extraction_config

# Import ensemble reviewer if available
try:
    from .reviewer import EnsembleReviewer
    ENSEMBLE_AVAILABLE = True
except ImportError:
    ENSEMBLE_AVAILABLE = False
    print("⚠️  Ensemble reviewer not available")


class IntelligenceProcessor:
    """
    Processes interviews and stores extracted intelligence
    Enhanced with ensemble validation system
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        enable_ensemble: bool = None,
        ensemble_mode: str = None,
        enable_validation_agent: bool = None,
        enable_llm_validation: bool = None,
        config: dict = None
    ):
        """
        Initialize processor with optional configuration

        Args:
            db_path: Path to SQLite database
            enable_ensemble: Enable ensemble validation (auto-detect if None)
            ensemble_mode: "full" (multi-model) or "basic" (single-model with review), reads from config if None
            enable_validation_agent: Enable ValidationAgent for completeness checking (reads from config if None)
            enable_llm_validation: Enable LLM-based validation in ValidationAgent (reads from config if None)
            config: Configuration dictionary (loads from file if None)
        """
        # Load configuration
        if config is None:
            config = EXTRACTION_CONFIG or load_extraction_config()

        self.config = config

        self.db = EnhancedIntelligenceDB(db_path)
        self.extractor = IntelligenceExtractor()

        # Read ensemble settings from config if not specified
        if enable_ensemble is None:
            enable_ensemble = (
                ENSEMBLE_AVAILABLE and
                config.get("ensemble", {}).get("enable_ensemble_review", False)
            )

        if ensemble_mode is None:
            ensemble_mode = config.get("ensemble", {}).get("ensemble_mode", "basic")

        self.enable_ensemble = enable_ensemble
        self.ensemble_mode = ensemble_mode

        # Initialize ensemble reviewer if enabled
        if self.enable_ensemble and ENSEMBLE_AVAILABLE:
            full_ensemble = (ensemble_mode == "full")
            self.reviewer = EnsembleReviewer(
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
                enable_ensemble=full_ensemble
            )
            mode_str = "FULL (multi-model)" if full_ensemble else "BASIC (single-model + review)"
            print(f"✨ Ensemble validation enabled: {mode_str}")
        else:
            self.reviewer = None
            print("ℹ️  Ensemble validation disabled")

        # Initialize ValidationAgent for completeness checking
        if enable_validation_agent is None:
            enable_validation_agent = config.get("validation", {}).get("enable_validation_agent", True)

        if enable_llm_validation is None:
            enable_llm_validation = config.get("validation", {}).get("enable_llm_validation", False)

        if enable_validation_agent:
            self.validation_agent = ValidationAgent(
                enable_llm_validation=enable_llm_validation,
                openai_api_key=os.getenv("OPENAI_API_KEY")
            )
            validation_mode = "with LLM validation" if enable_llm_validation else "rule-based only"
        else:
            self.validation_agent = None
        
        # Initialize consolidation agent if enabled
        enable_consolidation = config.get("consolidation", {}).get("enabled", False)
        if enable_consolidation:
            try:
                from .consolidation_agent import KnowledgeConsolidationAgent
                from .config import load_consolidation_config
                
                consolidation_config = load_consolidation_config()
                self.consolidation_agent = KnowledgeConsolidationAgent(
                    db=self.db,
                    config=consolidation_config,
                    openai_api_key=os.getenv("OPENAI_API_KEY")
                )
                print("🔗 Knowledge Graph consolidation enabled")
            except Exception as e:
                print(f"⚠️  Failed to initialize consolidation: {e}")
                self.consolidation_agent = None
        else:
            self.consolidation_agent = None
            print("ℹ️  Knowledge Graph consolidation disabled")
            print(f"🔍 ValidationAgent enabled: {validation_mode}")
        else:
            self.validation_agent = None
            print("ℹ️  ValidationAgent disabled")

        # Monitor will be initialized when processing starts
        self.monitor = None
        
    def initialize(self):
        """Initialize database"""
        print("🔧 Initializing database...")
        self.db.connect()
        self.db.init_v2_schema()
        print("✓ Database ready")
        
    def process_interview(self, interview: Dict) -> bool:
        """
        Process a single interview with optional ensemble validation

        Returns:
            True if successful, False otherwise
        """
        import time

        meta = interview.get("meta", {})
        qa_pairs = interview.get("qa_pairs", {})
        company = meta.get("company", "Unknown")
        respondent = meta.get("respondent", "Unknown")

        # Start timing if monitor is active
        start_time = time.time()

        # Insert interview record
        interview_id = self.db.insert_interview(meta, qa_pairs)

        if not interview_id:
            print(f"  ⚠️  Interview already processed, skipping")
            return False

        # Start monitoring if enabled
        if self.monitor:
            current_metric = self.monitor.start_interview(interview_id, company, respondent)

        # Update status to in_progress
        self.db.update_extraction_status(interview_id, "in_progress")

        # Extract entities using AI
        try:
            entities = self.extractor.extract_all(meta, qa_pairs)
        except Exception as e:
            error_msg = str(e)[:200]  # Truncate error message
            print(f"  ❌ Extraction failed: {error_msg}")
            self.db.update_extraction_status(interview_id, "failed", error_msg)
            return False

        # ENSEMBLE VALIDATION: Review extractions if enabled
        review_results = {}
        if self.reviewer:
            try:
                review_results = self.reviewer.review_all_entities(
                    entities,
                    qa_pairs,
                    meta
                )

                # Replace entities with synthesized results
                for entity_type, review in review_results.items():
                    entities[entity_type] = review.synthesized_result

                    # Add review metrics to each entity
                    for entity in entities[entity_type]:
                        entity["_review_metrics"] = review.metrics.to_dict()

            except Exception as e:
                print(f"  ⚠️  Ensemble review failed: {str(e)}")
                print(f"     Continuing with original extractions...")

        # VALIDATION AGENT: Check completeness and quality
        if self.validation_agent:
            print("  🔍 Running ValidationAgent...")
            try:
                # Check completeness
                missing_entities, completeness_results = self.validation_agent.validate_entities(
                    entities, qa_pairs, meta
                )

                if missing_entities:
                    print(f"  ⚠️  Missing entities detected: {', '.join(missing_entities)}")
                    # TODO: Implement focused re-extraction for missing entities
                else:
                    print(f"  ✓ Completeness check passed")

                # Check quality
                quality_results = self.validation_agent.validate_quality(entities)

                # Get summary
                summary = self.validation_agent.get_validation_summary(
                    completeness_results, quality_results
                )

                total_errors = summary['quality']['total_errors']
                total_warnings = summary['quality']['total_warnings']

                if total_errors > 0:
                    print(f"  ⚠️  Quality validation found {total_errors} errors, {total_warnings} warnings")
                else:
                    print(f"  ✓ Quality validation passed ({total_warnings} warnings)")

            except Exception as e:
                print(f"  ⚠️  ValidationAgent failed: {str(e)}")
                print(f"     Continuing with storage...")
        else:
            # QUALITY VALIDATION: Validate extracted entities (fallback)
            print("  🔍 Running quality validation...")
            try:
                validation_results = validate_extraction_results(entities)

                # Count validation issues
                total_errors = sum(sum(len(r.errors) for r in results) for results in validation_results.values())
                total_warnings = sum(sum(len(r.warnings) for r in results) for results in validation_results.values())

                if total_errors > 0:
                    print(f"  ⚠️  Quality validation found {total_errors} errors, {total_warnings} warnings")
                    # Entities are marked with _validation_failed flag but still stored
                else:
                    print(f"  ✓ Quality validation passed ({total_warnings} warnings)")

            except Exception as e:
                print(f"  ⚠️  Quality validation failed: {str(e)}")
                print(f"     Continuing with storage...")

        # CONSOLIDATION: Merge duplicates if enabled
        if self.consolidation_agent:
            print("  🔗 Running consolidation...")
            try:
                entities = self.consolidation_agent.consolidate_entities(
                    entities,
                    interview_id
                )
                
                # Get consolidation stats
                stats = self.consolidation_agent.get_statistics()
                if stats["duplicates_found"] > 0:
                    print(f"  ✓ Consolidated {stats['duplicates_found']} duplicates")
                
            except Exception as e:
                print(f"  ⚠️  Consolidation failed: {str(e)}")
                print(f"     Continuing with original entities...")
        
        # Extract business_unit for v2.0 entities (with fallback)
        business_unit = meta.get("business_unit", meta.get("department", "Unknown"))

        # Store extracted entities (with review metrics if available)
        storage_errors = []

        # v1.0 entities
        try:
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
                    storage_errors.append(f"automation_candidate: {str(e)[:50]}")

            for inefficiency in entities.get("inefficiencies", []):
                try:
                    self.db.insert_inefficiency(interview_id, company, inefficiency)
                except Exception as e:
                    storage_errors.append(f"inefficiency: {str(e)[:50]}")

            print(f"  ✓ Stored v1.0 entities")

        except Exception as e:
            print(f"  ⚠️  v1.0 storage error: {str(e)}")

        # v2.0 entities
        try:
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

            # Enhanced v1.0 entities (if present)
            for pain_point in entities.get("pain_points_v2", []):
                try:
                    self.db.insert_enhanced_pain_point(interview_id, company, business_unit, pain_point)
                except Exception as e:
                    storage_errors.append(f"enhanced_pain_point: {str(e)[:50]}")

            for system in entities.get("systems_v2", []):
                try:
                    self.db.insert_or_update_enhanced_system(system, company)
                except Exception as e:
                    storage_errors.append(f"enhanced_system: {str(e)[:50]}")

            for automation in entities.get("automation_candidates_v2", []):
                try:
                    self.db.insert_enhanced_automation_candidate(interview_id, company, business_unit, automation)
                except Exception as e:
                    storage_errors.append(f"enhanced_automation_candidate: {str(e)[:50]}")

            print(f"  ✓ Stored v2.0 entities")

        except Exception as e:
            print(f"  ⚠️  v2.0 storage error: {str(e)}")

        # Report any storage errors
        if storage_errors:
            print(f"  ⚠️  {len(storage_errors)} storage errors:")
            for error in storage_errors[:5]:  # Show first 5
                print(f"     - {error}")
            if len(storage_errors) > 5:
                print(f"     ... and {len(storage_errors) - 5} more")

        print(f"  ✓ Storage complete (errors: {len(storage_errors)})")

        # Update status to complete
        self.db.update_extraction_status(interview_id, "complete")

        # Record monitoring metrics if enabled
        if self.monitor:
            # Count entities
            entity_counts = {k: len(v) for k, v in entities.items()}

            # Get validation metrics (if validation agent was used)
            if self.validation_agent and 'missing_entities' in locals():
                validation_errors = summary.get('quality', {}).get('total_errors', 0)
                validation_warnings = summary.get('quality', {}).get('total_warnings', 0)
                missing_types = missing_entities
            else:
                validation_errors = 0
                validation_warnings = 0
                missing_types = []

            # Finish tracking
            current_metric.finish(success=True)
            current_metric.set_entity_counts(entity_counts)
            current_metric.set_quality_metrics(validation_errors, validation_warnings, missing_types)

            self.monitor.finish_interview(current_metric, success=True)

        return True
    
    def _estimate_extraction_cost(self, num_interviews: int) -> float:
        """
        Estimate API cost for extraction
        
        Args:
            num_interviews: Number of interviews to process
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimates:
        # - 17 entity types per interview
        # - ~$0.001-0.002 per API call with gpt-4o-mini
        # - Ensemble multiplies by 3x
        
        base_cost_per_interview = 0.02  # $0.02 per interview
        
        if self.enable_ensemble:
            multiplier = 3  # Ensemble uses 3x API calls
        else:
            multiplier = 1
            
        total_cost = num_interviews * base_cost_per_interview * multiplier
        return total_cost
    
    def process_all_interviews(self, interviews_file: Path = INTERVIEWS_FILE, resume: bool = False):
        """
        Process all interviews from JSON file

        Args:
            interviews_file: Path to interviews JSON file
            resume: If True, only process pending/failed interviews (skips completed)
        """

        print(f"\n📂 Loading interviews from: {interviews_file}")

        with open(interviews_file, 'r', encoding='utf-8') as f:
            interviews = json.load(f)

        print(f"✓ Found {len(interviews)} interviews")
        
        # Estimate cost and get confirmation
        estimated_cost = self._estimate_extraction_cost(len(interviews))
        print(f"\n💰 Estimated cost: ${estimated_cost:.2f}")
        print(f"   (Based on ~17 API calls per interview at $0.001-0.002 per call)")
        
        if estimated_cost > 1.0:
            try:
                confirm = input(f"\n⚠️  Estimated cost is ${estimated_cost:.2f}. Continue? (y/n): ")
                if confirm.lower() != 'y':
                    print("❌ Extraction cancelled by user")
                    return
            except (EOFError, KeyboardInterrupt):
                print("\n❌ Extraction cancelled")
                return
        
        print(f"✓ Starting extraction...")

        # If resuming, check which interviews are already complete
        if resume:
            completed_interviews = self.db.get_interviews_by_status("complete")
            completed_ids = {(i["respondent"], i["company"], i["date"]) for i in completed_interviews}

            # Filter out completed interviews
            interviews_to_process = []
            for interview in interviews:
                meta = interview.get("meta", {})
                key = (meta.get("respondent"), meta.get("company"), meta.get("date"))
                if key not in completed_ids:
                    interviews_to_process.append(interview)

            print(f"📋 Resume mode: {len(interviews_to_process)} pending/failed, {len(completed_interviews)} already complete")
            interviews = interviews_to_process

        # Initialize monitor for real-time tracking
        enable_monitor = self.config.get("monitoring", {}).get("enable_monitor", True)
        if enable_monitor:
            self.monitor = ExtractionMonitor(total_interviews=len(interviews))
            print(f"📊 Monitoring enabled for {len(interviews)} interviews")
        else:
            self.monitor = None

        # Get summary frequency from config
        summary_frequency = self.config.get("monitoring", {}).get("print_summary_every_n", 5)

        success_count = 0
        skip_count = 0
        error_count = 0

        for i, interview in enumerate(interviews, 1):
            print(f"\n[{i}/{len(interviews)}] Processing...")

            result = self.process_interview(interview)

            if result is True:
                success_count += 1
            elif result is False:
                skip_count += 1
            else:
                error_count += 1

            # Print periodic summary based on config
            if self.monitor and (i % summary_frequency == 0 or i == len(interviews)):
                self.monitor.print_summary(detailed=False)
        
        # Print final report
        if self.monitor:
            self.monitor.print_final_report()
        else:
            print(f"\n{'='*60}")
            print(f"📊 PROCESSING COMPLETE")
            print(f"{'='*60}")
            print(f"✓ Processed: {success_count}")
            print(f"⊘ Skipped: {skip_count}")
            print(f"✗ Errors: {error_count}")

        # Show database stats
        stats = self.db.get_stats()
        print(f"\n📈 DATABASE STATS")
        print(f"{'='*60}")
        print(f"Interviews: {stats['interviews']}")
        print(f"Pain Points: {stats['pain_points']}")
        print(f"Processes: {stats['processes']}")
        print(f"Systems: {stats['systems']}")
        print(f"KPIs: {stats['kpis']}")
        print(f"Automation Candidates: {stats['automation_candidates']}")
        print(f"Inefficiencies: {stats['inefficiencies']}")

        print(f"\n📊 BY COMPANY")
        print(f"{'='*60}")
        for company, count in stats.get('by_company', {}).items():
            print(f"{company}: {count} interviews")
    
    def close(self):
        """Close database connection"""
        self.db.close()
