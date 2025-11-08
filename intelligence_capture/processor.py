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

        # Extract entities using AI
        try:
            entities = self.extractor.extract_all(meta, qa_pairs)
        except Exception as e:
            print(f"  ❌ Extraction failed: {str(e)}")
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

        # Store extracted entities (with review metrics if available)
        try:
            # Pain points
            for pain_point in entities.get("pain_points", []):
                self.db.insert_pain_point(interview_id, company, pain_point)

            # Processes
            for process in entities.get("processes", []):
                self.db.insert_process(interview_id, company, process)

            # Systems
            for system in entities.get("systems", []):
                self.db.insert_or_update_system(system, company)

            # KPIs
            for kpi in entities.get("kpis", []):
                self.db.insert_kpi(interview_id, company, kpi)

            # Automation candidates
            for automation in entities.get("automation_candidates", []):
                self.db.insert_automation_candidate(interview_id, company, automation)

            # Inefficiencies
            for inefficiency in entities.get("inefficiencies", []):
                self.db.insert_inefficiency(interview_id, company, inefficiency)

            print(f"  ✓ Stored all entities")
            return True

        except Exception as e:
            print(f"  ❌ Storage failed: {str(e)}")
            return False
    
    def process_all_interviews(self, interviews_file: Path = INTERVIEWS_FILE):
        """Process all interviews from JSON file"""
        
        print(f"\n📂 Loading interviews from: {interviews_file}")
        
        with open(interviews_file, 'r', encoding='utf-8') as f:
            interviews = json.load(f)
        
        print(f"✓ Found {len(interviews)} interviews")
        
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
