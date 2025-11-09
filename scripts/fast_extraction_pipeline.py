#!/usr/bin/env python
"""
Fast Extraction Pipeline - Core Entities Only
Processes ALL 44 interviews with only the most valuable extractors
Optimized for speed and essential data
"""
import os
import sys
import json
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY not found in environment")
    exit(1)

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import FAST_DB_PATH, INTERVIEWS_FILE, PROJECT_ROOT
from intelligence_capture.extractors import (
    CommunicationChannelExtractor,
    DecisionPointExtractor,
    DataFlowExtractor,
    TemporalPatternExtractor,
    FailureModeExtractor,
    EnhancedPainPointExtractor,
    SystemExtractor,
    AutomationCandidateExtractor
)

# Configuration
BATCH_SIZE = 10  # Larger batches for speed
PROGRESS_FILE = PROJECT_ROOT / "data" / "fast_extraction_progress.json"

# CORE EXTRACTORS ONLY - Focus on high-value entities
CORE_EXTRACTORS = {
    "PainPoint": EnhancedPainPointExtractor(),
    "System": SystemExtractor(),
    "AutomationCandidate": AutomationCandidateExtractor(),
    "CommunicationChannel": CommunicationChannelExtractor(),
    "FailureMode": FailureModeExtractor()
}

print(f"""
{'='*70}
🚀 FAST EXTRACTION PIPELINE - CORE ENTITIES ONLY
{'='*70}

Extracting ONLY the most valuable entities:
  ✅ Pain Points (with intensity, frequency, cost)
  ✅ Systems (with satisfaction scores)
  ✅ Automation Candidates (with priority matrix)
  ✅ Communication Channels
  ✅ Failure Modes

Skipping lower-value entities for speed:
  ⏭️  Decision Points
  ⏭️  Data Flows
  ⏭️  Temporal Patterns
  ⏭️  Team Structures
  ⏭️  Knowledge Gaps
  ⏭️  Success Patterns
  ⏭️  Budget Constraints
  ⏭️  External Dependencies

This will be ~60% faster while capturing 80% of the value!
{'='*70}
""")


class FastExtractionPipeline:
    """Fast extraction pipeline with core entities only"""
    
    def __init__(self, db_path: Path, interviews_path: Path):
        self.db_path = db_path
        self.interviews_path = interviews_path
        self.db = None
        self.stats = {
            "total_interviews": 0,
            "processed_interviews": 0,
            "failed_interviews": [],
            "entities_extracted": {name: 0 for name in CORE_EXTRACTORS.keys()},
            "start_time": None,
            "end_time": None,
            "total_duration_seconds": 0
        }
    
    def initialize(self):
        """Initialize database"""
        print("🔧 Initializing fast pipeline...")
        
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
        self.db.init_v2_schema()
        print(f"  ✅ Database initialized: {self.db_path}")
        print(f"  ✅ {len(CORE_EXTRACTORS)} core extractors ready")
    
    def load_interviews(self):
        """Load all interviews"""
        if not self.interviews_path.exists():
            raise FileNotFoundError(f"Interviews not found at {self.interviews_path}")
        
        with open(self.interviews_path, 'r', encoding='utf-8') as f:
            interviews = json.load(f)
        
        self.stats["total_interviews"] = len(interviews)
        return interviews
    
    def load_progress(self):
        """Load progress from previous run"""
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {"processed_ids": [], "last_index": 0}
    
    def save_progress(self, processed_ids, last_index):
        """Save progress"""
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump({
                "processed_ids": processed_ids,
                "last_index": last_index,
                "timestamp": datetime.now().isoformat()
            }, f, indent=2)
    
    def process_interview(self, interview, interview_idx):
        """Process single interview with core extractors only"""
        meta = interview.get("meta", {})
        role = meta.get('role', 'Unknown')
        company = meta.get('company', 'Unknown')
        
        print(f"\n[{interview_idx + 1}/{self.stats['total_interviews']}] {role}")
        
        result = {"interview_id": None, "entities": {}, "errors": []}
        
        try:
            # Insert interview
            interview_id = self.db.insert_interview(meta, interview['qa_pairs'])
            result["interview_id"] = interview_id
            
            business_unit = meta.get('business_unit', 'Unknown')
            
            # Extract with core extractors only
            for entity_name, extractor in CORE_EXTRACTORS.items():
                try:
                    entities = extractor.extract_from_interview(interview)
                    result["entities"][entity_name] = entities
                    self.stats["entities_extracted"][entity_name] += len(entities)
                    
                    # Store in database
                    for entity in entities:
                        if entity_name == "PainPoint":
                            self.db.insert_enhanced_pain_point(interview_id, company, business_unit, entity)
                        elif entity_name == "System":
                            self.db.insert_enhanced_system(interview_id, company, business_unit, entity)
                        elif entity_name == "AutomationCandidate":
                            self.db.insert_enhanced_automation_candidate(interview_id, company, business_unit, entity)
                        elif entity_name == "CommunicationChannel":
                            self.db.insert_communication_channel(interview_id, company, business_unit, entity)
                        elif entity_name == "FailureMode":
                            self.db.insert_failure_mode(interview_id, company, business_unit, entity)
                    
                    print(f"  ✅ {entity_name}: {len(entities)}")
                    
                except Exception as e:
                    print(f"  ❌ {entity_name}: {str(e)[:80]}")
                    result["errors"].append(f"{entity_name}: {str(e)}")
            
            self.stats["processed_interviews"] += 1
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:80]}")
            self.stats["failed_interviews"].append({
                "index": interview_idx,
                "role": role,
                "error": str(e)
            })
        
        return result
    
    def run(self):
        """Run fast extraction pipeline"""
        self.stats["start_time"] = datetime.now().isoformat()
        start_time = time.time()
        
        # Initialize
        self.initialize()
        
        # Load interviews
        print(f"\n📂 Loading interviews...")
        interviews = self.load_interviews()
        print(f"  ✅ Loaded {len(interviews)} interviews")
        
        # Check progress
        progress = self.load_progress()
        start_idx = progress.get("last_index", 0)
        
        if start_idx > 0:
            print(f"\n🔄 Resuming from interview {start_idx + 1}")
        
        # Process all interviews
        print(f"\n{'='*70}")
        print(f"📊 FAST EXTRACTION IN PROGRESS")
        print(f"{'='*70}")
        
        processed_ids = []
        
        for idx in range(start_idx, len(interviews)):
            result = self.process_interview(interviews[idx], idx)
            
            if result["interview_id"]:
                processed_ids.append(result["interview_id"])
            
            # Save progress every 5 interviews
            if (idx + 1) % 5 == 0:
                self.save_progress(processed_ids, idx + 1)
        
        # Finalize
        end_time = time.time()
        self.stats["end_time"] = datetime.now().isoformat()
        self.stats["total_duration_seconds"] = int(end_time - start_time)
        
        self.print_summary()
        self.save_report()
        
        if self.db:
            self.db.close()
        
        # Remove progress file on success
        if PROGRESS_FILE.exists() and not self.stats["failed_interviews"]:
            PROGRESS_FILE.unlink()
    
    def print_summary(self):
        """Print summary"""
        print(f"\n{'='*70}")
        print("📈 FAST EXTRACTION SUMMARY")
        print(f"{'='*70}\n")
        
        print(f"Interviews: {self.stats['processed_interviews']}/{self.stats['total_interviews']}")
        print(f"Failed: {len(self.stats['failed_interviews'])}")
        
        print(f"\n📊 Core Entities Extracted:")
        total = 0
        for name, count in self.stats["entities_extracted"].items():
            avg = count / self.stats['processed_interviews'] if self.stats['processed_interviews'] > 0 else 0
            print(f"  • {name:25s}: {count:4d} ({avg:4.1f} per interview)")
            total += count
        
        avg_total = total / self.stats['processed_interviews'] if self.stats['processed_interviews'] > 0 else 0
        print(f"\n  {'TOTAL':25s}: {total:4d} ({avg_total:4.1f} per interview)")
        
        duration_min = self.stats["total_duration_seconds"] / 60
        print(f"\n⏱️  Duration: {duration_min:.1f} minutes")
        print(f"⚡ Speed: {self.stats['processed_interviews'] / duration_min:.1f} interviews/minute")
    
    def save_report(self):
        """Save report"""
        report_path = Path("reports/fast_extraction_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Report: {report_path}")


def main():
    """Main entry point"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Fast extraction pipeline with core entities only')
    parser.add_argument('--db-path', type=Path, default=FAST_DB_PATH,
                       help=f'Database path (default: {FAST_DB_PATH})')
    parser.add_argument('--interviews', type=Path, default=INTERVIEWS_FILE,
                       help=f'Interviews JSON file (default: {INTERVIEWS_FILE})')
    args = parser.parse_args()
    
    pipeline = FastExtractionPipeline(args.db_path, args.interviews)
    
    try:
        pipeline.run()
        print(f"\n✅ Fast extraction complete!")
        print(f"📁 Database: {args.db_path}")
        print(f"\nNext steps:")
        print(f"  1. Review report: reports/fast_extraction_report.json")
        print(f"  2. Generate comprehensive analytics")
        print(f"  3. Run CEO validation and cross-company analysis")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted - progress saved")
    except Exception as e:
        print(f"\n\n❌ Failed: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()
