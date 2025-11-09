#!/usr/bin/env python
"""
Pilot Extraction Script
Processes 5-10 interviews to validate extractors before full run
"""
import os
import sys
import json
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
from intelligence_capture.config import PILOT_DB_PATH, INTERVIEWS_FILE
from intelligence_capture.extractors import (
    CommunicationChannelExtractor,
    DecisionPointExtractor,
    DataFlowExtractor,
    TemporalPatternExtractor,
    FailureModeExtractor
)

# Configuration
PILOT_SIZE = 5  # Number of interviews to process

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Pilot extraction with 5-10 interviews')
    parser.add_argument('--db-path', type=Path, default=PILOT_DB_PATH,
                       help=f'Database path (default: {PILOT_DB_PATH})')
    parser.add_argument('--interviews', type=Path, default=INTERVIEWS_FILE,
                       help=f'Interviews JSON file (default: {INTERVIEWS_FILE})')
    parser.add_argument('--size', type=int, default=PILOT_SIZE,
                       help=f'Number of interviews to process (default: {PILOT_SIZE})')
    args = parser.parse_args()
    
    db_path = args.db_path
    interviews_path = args.interviews
    pilot_size = args.size
    
    print("=" * 70)
    print("🚀 PILOT EXTRACTION - Phase 1 Entities")
    print("=" * 70)
    print(f"\nProcessing: {pilot_size} interviews")
    print(f"Database: {db_path}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load interviews
    if not interviews_path.exists():
        print(f"❌ Interviews not found at {interviews_path}")
        return
    
    with open(interviews_path, 'r', encoding='utf-8') as f:
        all_interviews = json.load(f)
    
    print(f"✅ Loaded {len(all_interviews)} total interviews")
    
    # Select pilot interviews (first N)
    pilot_interviews = all_interviews[:pilot_size]
    print(f"📋 Selected {len(pilot_interviews)} for pilot:\n")
    for i, interview in enumerate(pilot_interviews, 1):
        print(f"  {i}. {interview['meta'].get('role', 'Unknown')} - {interview['meta'].get('company', 'Unknown')}")
    
    # Initialize database
    print(f"\n🗄️  Initializing database...")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_v2_schema()
    
    # Initialize extractors
    print("🤖 Initializing extractors...")
    extractors = {
        "CommunicationChannel": CommunicationChannelExtractor(),
        "DecisionPoint": DecisionPointExtractor(),
        "DataFlow": DataFlowExtractor(),
        "TemporalPattern": TemporalPatternExtractor(),
        "FailureMode": FailureModeExtractor()
    }
    
    # Process each interview
    print(f"\n{'='*70}")
    print("📊 EXTRACTION RESULTS")
    print(f"{'='*70}\n")
    
    total_entities = {name: 0 for name in extractors.keys()}
    
    for idx, interview in enumerate(pilot_interviews, 1):
        meta = interview['meta']
        role = meta.get('role', 'Unknown')
        company = meta.get('company', 'Unknown')
        
        print(f"\n[{idx}/{len(pilot_interviews)}] Processing: {role}")
        print("-" * 70)
        
        # Insert interview
        interview_id = db.insert_interview(meta, interview['qa_pairs'])
        
        # Extract entities
        results = {}
        for entity_name, extractor in extractors.items():
            try:
                entities = extractor.extract_from_interview(interview)
                results[entity_name] = entities
                total_entities[entity_name] += len(entities)
                
                # Store in database
                business_unit = meta.get('business_unit', 'Unknown')
                
                if entity_name == "CommunicationChannel":
                    for entity in entities:
                        db.insert_communication_channel(interview_id, company, business_unit, entity)
                elif entity_name == "DecisionPoint":
                    for entity in entities:
                        db.insert_decision_point(interview_id, company, business_unit, entity)
                elif entity_name == "DataFlow":
                    for entity in entities:
                        db.insert_data_flow(interview_id, company, business_unit, entity)
                elif entity_name == "TemporalPattern":
                    for entity in entities:
                        db.insert_temporal_pattern(interview_id, company, business_unit, entity)
                elif entity_name == "FailureMode":
                    for entity in entities:
                        db.insert_failure_mode(interview_id, company, business_unit, entity)
                
                print(f"  ✅ {entity_name}: {len(entities)} entities")
                
            except Exception as e:
                print(f"  ❌ {entity_name}: Error - {str(e)}")
                results[entity_name] = []
    
    # Summary
    print(f"\n{'='*70}")
    print("📈 PILOT EXTRACTION SUMMARY")
    print(f"{'='*70}\n")
    
    print(f"Interviews Processed: {len(pilot_interviews)}")
    print(f"\nEntities Extracted:")
    for entity_name, count in total_entities.items():
        avg = count / len(pilot_interviews) if pilot_interviews else 0
        print(f"  • {entity_name}: {count} total ({avg:.1f} per interview)")
    
    total = sum(total_entities.values())
    print(f"\n  TOTAL: {total} entities ({total/len(pilot_interviews):.1f} per interview)")
    
    # Database stats
    print(f"\n📊 Database Statistics:")
    stats = db.get_v2_stats()
    for key, value in stats.items():
        if isinstance(value, (int, float)):
            print(f"  • {key}: {value}")
    
    print(f"\n✅ Pilot extraction complete!")
    print(f"📁 Database saved to: {db_path}")
    print(f"\nNext steps:")
    print(f"  1. Review extracted entities in database")
    print(f"  2. Check extraction quality and confidence scores")
    print(f"  3. Identify any issues before full extraction")
    
    db.close()

if __name__ == "__main__":
    main()
