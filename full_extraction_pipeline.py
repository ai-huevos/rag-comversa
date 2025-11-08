#!/usr/bin/env python
"""
Full Extraction Pipeline
Processes ALL 44 interviews with all extractors (v1.0 + v2.0 entities)
"""
import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict, List, Optional

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.extractors import (
    CommunicationChannelExtractor,
    DecisionPointExtractor,
    DataFlowExtractor,
    TemporalPatternExtractor,
    FailureModeExtractor,
    EnhancedPainPointExtractor,
    SystemExtractor,
    AutomationCandidateExtractor,
    TeamStructureExtractor,
    KnowledgeGapExtractor,
    SuccessPatternExtractor,
    BudgetConstraintExtractor,
    ExternalDependencyExtractor
)

# Configuration
DB_PATH = Path("data/full_intelligence.db")
INTERVIEWS_PATH = Path("data/interviews/analysis_output/all_interviews.json")
BATCH_SIZE = 5  # Process 5 interviews at a time
RETRY_ATTEMPTS = 3
RETRY_DELAY = 5  # seconds

# Progress tracking
PROGRESS_FILE = Path("data/extraction_progress.json")


class ExtractionPipeline:
    """Manages the full extraction pipeline with batch processing and retry logic"""
    
    def __init__(self, db_path: Path, interviews_path: Path):
        self.db_path = db_path
        self.interviews_path = interviews_path
        self.db = None
        self.extractors = {}
        self.stats = {
            "total_interviews": 0,
            "processed_interviews": 0,
            "failed_interviews": [],
            "entities_extracted": {},
            "start_time": None,
            "end_time": None,
            "total_duration_seconds": 0
        }
    
    def initialize(self):
        """Initialize database and extractors"""
        print("🔧 Initializing pipeline...")
        
        # Create database
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
        self.db.init_v2_schema()
        print(f"  ✅ Database initialized: {self.db_path}")
        
        # Initialize all extractors
        print("  🤖 Initializing extractors...")
        self.extractors = {
            "CommunicationChannel": CommunicationChannelExtractor(),
            "DecisionPoint": DecisionPointExtractor(),
            "DataFlow": DataFlowExtractor(),
            "TemporalPattern": TemporalPatternExtractor(),
            "FailureMode": FailureModeExtractor(),
            "PainPoint": EnhancedPainPointExtractor(),
            "System": SystemExtractor(),
            "AutomationCandidate": AutomationCandidateExtractor(),
            "TeamStructure": TeamStructureExtractor(),
            "KnowledgeGap": KnowledgeGapExtractor(),
            "SuccessPattern": SuccessPatternExtractor(),
            "BudgetConstraint": BudgetConstraintExtractor(),
            "ExternalDependency": ExternalDependencyExtractor()
        }
        
        # Initialize stats
        for entity_name in self.extractors.keys():
            self.stats["entities_extracted"][entity_name] = 0
        
        print(f"  ✅ {len(self.extractors)} extractors ready")
    
    def load_interviews(self) -> List[Dict]:
        """Load all interviews from JSON file"""
        if not self.interviews_path.exists():
            raise FileNotFoundError(f"Interviews not found at {self.interviews_path}")
        
        with open(self.interviews_path, 'r', encoding='utf-8') as f:
            interviews = json.load(f)
        
        self.stats["total_interviews"] = len(interviews)
        return interviews
    
    def load_progress(self) -> Dict:
        """Load progress from previous run if exists"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {"processed_ids": [], "last_index": 0}
    
    def save_progress(self, processed_ids: List[int], last_index: int):
        """Save progress to resume from failures"""
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                "processed_ids": processed_ids,
                "last_index": last_index,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
    
    def process_interview(self, interview: Dict, interview_idx: int) -> Dict:
        """
        Process a single interview with all extractors
        
        Returns:
            Dict with extraction results and stats
        """
        meta = interview.get("meta", {})
        role = meta.get('role', 'Unknown')
        company = meta.get('company', 'Unknown')
        
        print(f"\n[{interview_idx + 1}/{self.stats['total_interviews']}] Processing: {role}")
        print("-" * 70)
        
        result = {
            "interview_id": None,
            "entities": {},
            "errors": []
        }
        
        try:
            # Insert interview record
            interview_id = self.db.insert_interview(meta, interview['qa_pairs'])
            result["interview_id"] = interview_id
            print(f"  ✅ Interview record created (ID: {interview_id})")
            
            # Extract entities with each extractor
            business_unit = meta.get('business_unit', 'Unknown')
            
            for entity_name, extractor in self.extractors.items():
                try:
                    entities = extractor.extract_from_interview(interview)
                    result["entities"][entity_name] = entities
                    self.stats["entities_extracted"][entity_name] += len(entities)
                    
                    # Store in database
                    self._store_entities(interview_id, company, business_unit, entity_name, entities)
                    
                    print(f"  ✅ {entity_name}: {len(entities)} entities")
                    
                except Exception as e:
                    error_msg = f"{entity_name} extraction failed: {str(e)}"
                    result["errors"].append(error_msg)
                    print(f"  ❌ {entity_name}: {str(e)[:100]}")
            
            self.stats["processed_interviews"] += 1
            
        except Exception as e:
            error_msg = f"Interview processing failed: {str(e)}"
            result["errors"].append(error_msg)
            print(f"  ❌ Interview failed: {str(e)}")
            self.stats["failed_interviews"].append({
                "index": interview_idx,
                "role": role,
                "company": company,
                "error": str(e)
            })
        
        return result
    
    def _store_entities(self, interview_id: int, company: str, business_unit: str, 
                       entity_name: str, entities: List[Dict]):
        """Store extracted entities in database"""
        for entity in entities:
            try:
                if entity_name == "CommunicationChannel":
                    self.db.insert_communication_channel(interview_id, company, business_unit, entity)
                elif entity_name == "DecisionPoint":
                    self.db.insert_decision_point(interview_id, company, business_unit, entity)
                elif entity_name == "DataFlow":
                    self.db.insert_data_flow(interview_id, company, business_unit, entity)
                elif entity_name == "TemporalPattern":
                    self.db.insert_temporal_pattern(interview_id, company, business_unit, entity)
                elif entity_name == "FailureMode":
                    self.db.insert_failure_mode(interview_id, company, business_unit, entity)
                elif entity_name == "PainPoint":
                    self.db.insert_enhanced_pain_point(interview_id, company, business_unit, entity)
                elif entity_name == "System":
                    self.db.insert_enhanced_system(interview_id, company, business_unit, entity)
                elif entity_name == "AutomationCandidate":
                    self.db.insert_enhanced_automation_candidate(interview_id, company, business_unit, entity)
                elif entity_name == "TeamStructure":
                    self.db.insert_team_structure(interview_id, company, business_unit, entity)
                elif entity_name == "KnowledgeGap":
                    self.db.insert_knowledge_gap(interview_id, company, business_unit, entity)
                elif entity_name == "SuccessPattern":
                    self.db.insert_success_pattern(interview_id, company, business_unit, entity)
                elif entity_name == "BudgetConstraint":
                    self.db.insert_budget_constraint(interview_id, company, business_unit, entity)
                elif entity_name == "ExternalDependency":
                    self.db.insert_external_dependency(interview_id, company, business_unit, entity)
            except Exception as e:
                print(f"    ⚠️  Failed to store {entity_name}: {str(e)[:100]}")
    
    def process_batch(self, interviews: List[Dict], start_idx: int, batch_size: int) -> List[Dict]:
        """Process a batch of interviews"""
        end_idx = min(start_idx + batch_size, len(interviews))
        batch = interviews[start_idx:end_idx]
        
        results = []
        for i, interview in enumerate(batch):
            result = self.process_interview(interview, start_idx + i)
            results.append(result)
            
            # Save progress after each interview
            self.save_progress(
                [r["interview_id"] for r in results if r["interview_id"]],
                start_idx + i + 1
            )
        
        return results
    
    def run(self):
        """Run the full extraction pipeline"""
        print("=" * 70)
        print("🚀 FULL EXTRACTION PIPELINE - ALL 44 INTERVIEWS")
        print("=" * 70)
        print(f"\nDatabase: {self.db_path}")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        self.stats["start_time"] = datetime.now().isoformat()
        start_time = time.time()
        
        # Initialize
        self.initialize()
        
        # Load interviews
        print(f"\n📂 Loading interviews...")
        interviews = self.load_interviews()
        print(f"  ✅ Loaded {len(interviews)} interviews")
        
        # Check for previous progress
        progress = self.load_progress()
        start_idx = progress.get("last_index", 0)
        
        if start_idx > 0:
            print(f"\n🔄 Resuming from interview {start_idx + 1}")
        
        # Process in batches
        print(f"\n{'='*70}")
        print(f"📊 EXTRACTION IN PROGRESS")
        print(f"{'='*70}")
        
        while start_idx < len(interviews):
            print(f"\n📦 Processing batch starting at interview {start_idx + 1}...")
            
            try:
                self.process_batch(interviews, start_idx, BATCH_SIZE)
                start_idx += BATCH_SIZE
                
                # Brief pause between batches to avoid rate limits
                if start_idx < len(interviews):
                    print(f"\n⏸️  Pausing 2 seconds before next batch...")
                    time.sleep(2)
                    
            except Exception as e:
                print(f"\n❌ Batch processing error: {str(e)}")
                print(f"   Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
        
        # Finalize
        end_time = time.time()
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["total_duration_seconds"] = int(end_time - start_time)
        
        self.print_summary()
        self.save_report()
        
        # Cleanup
        if self.db:
            self.db.close()
        
        # Remove progress file on successful completion
        if PROGRESS_FILE.exists() and not self.stats["failed_interviews"]:
            PROGRESS_FILE.unlink()
    
    def print_summary(self):
        """Print extraction summary"""
        print(f"\n{'='*70}")
        print("📈 EXTRACTION SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Total Interviews: {self.stats['total_interviews']}")
        print(f"Successfully Processed: {self.stats['processed_interviews']}")
        print(f"Failed: {len(self.stats['failed_interviews'])}")
        
        print(f"\n📊 Entities Extracted:")
        total_entities = 0
        for entity_name, count in sorted(self.stats["entities_extracted"].items()):
            avg = count / self.stats['processed_interviews'] if self.stats['processed_interviews'] > 0 else 0
            print(f"  • {entity_name:25s}: {count:4d} total ({avg:4.1f} per interview)")
            total_entities += count
        
        avg_total = total_entities / self.stats['processed_interviews'] if self.stats['processed_interviews'] > 0 else 0
        print(f"\n  {'TOTAL':25s}: {total_entities:4d} entities ({avg_total:4.1f} per interview)")
        
        # Duration
        duration_min = self.stats["total_duration_seconds"] / 60
        print(f"\n⏱️  Duration: {duration_min:.1f} minutes ({self.stats['total_duration_seconds']} seconds)")
        
        if self.stats["failed_interviews"]:
            print(f"\n⚠️  Failed Interviews:")
            for failed in self.stats["failed_interviews"]:
                print(f"  • [{failed['index']}] {failed['role']} - {failed['company']}")
                print(f"    Error: {failed['error'][:100]}")
    
    def save_report(self):
        """Save detailed extraction report"""
        report_path = Path("reports/full_extraction_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Detailed report saved to: {report_path}")


def main():
    """Main entry point"""
    pipeline = ExtractionPipeline(DB_PATH, INTERVIEWS_PATH)
    
    try:
        pipeline.run()
        print(f"\n✅ Full extraction pipeline complete!")
        print(f"📁 Database: {DB_PATH}")
        print(f"\nNext steps:")
        print(f"  1. Review extraction report in reports/full_extraction_report.json")
        print(f"  2. Run quality validation (Task 15)")
        print(f"  3. Generate comprehensive analytics")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Pipeline interrupted by user")
        print(f"   Progress saved. Run again to resume from last checkpoint.")
    except Exception as e:
        print(f"\n\n❌ Pipeline failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
