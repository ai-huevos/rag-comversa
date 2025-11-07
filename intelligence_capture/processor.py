"""
Main processor for Intelligence Capture System
Reads interviews, extracts entities, stores in database
"""
import json
from pathlib import Path
from typing import Dict, List
from database import IntelligenceDB
from extractor import IntelligenceExtractor
from config import DB_PATH, INTERVIEWS_FILE


class IntelligenceProcessor:
    """Processes interviews and stores extracted intelligence"""
    
    def __init__(self, db_path: Path = DB_PATH):
        self.db = IntelligenceDB(db_path)
        self.extractor = IntelligenceExtractor()
        
    def initialize(self):
        """Initialize database"""
        print("🔧 Initializing database...")
        self.db.connect()
        self.db.init_schema()
        print("✓ Database ready")
        
    def process_interview(self, interview: Dict) -> bool:
        """
        Process a single interview
        
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
        
        # Store extracted entities
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
