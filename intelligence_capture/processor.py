"""
Main processor for Intelligence Capture System
Reads interviews, extracts entities, stores in database
Enhanced with ensemble validation for forensic-grade quality
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from database import IntelligenceDB
from extractor import IntelligenceExtractor
from validation import validate_extraction_results, print_validation_summary
from config import DB_PATH, INTERVIEWS_FILE

# Import ensemble reviewer if available
try:
    from reviewer import EnsembleReviewer
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
        ensemble_mode: str = None
    ):
        """
        Initialize processor

        Args:
            db_path: Path to SQLite database
            enable_ensemble: Enable ensemble validation (auto-detect if None)
            ensemble_mode: "full" (multi-model) or "basic" (single-model with review), reads from config if None
        """
        self.db = IntelligenceDB(db_path)
        self.extractor = IntelligenceExtractor()

        # Auto-detect ensemble availability
        if enable_ensemble is None:
            enable_ensemble = ENSEMBLE_AVAILABLE and os.getenv("ENABLE_ENSEMBLE_REVIEW", "true").lower() == "true"

        # Read ensemble mode from config if not specified
        if ensemble_mode is None:
            ensemble_mode = os.getenv("ENSEMBLE_MODE", "basic")

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
        
    def initialize(self):
        """Initialize database"""
        print("🔧 Initializing database...")
        self.db.connect()
        self.db.init_schema()
        print("✓ Database ready")
        
    def process_interview(self, interview: Dict) -> bool:
        """
        Process a single interview with optional ensemble validation

        Returns:
            True if successful, False otherwise
        """
        meta = interview.get("meta", {})
        qa_pairs = interview.get("qa_pairs", {})

        # Insert interview record
        interview_id = self.db.insert_interview(meta, qa_pairs)

        if not interview_id:
            print(f"  ⚠️  Interview already processed, skipping")
            return False

        company = meta.get("company", "Unknown")

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

        # QUALITY VALIDATION: Validate extracted entities
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

        return True
    
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
