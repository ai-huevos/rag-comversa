#!/usr/bin/env python3
"""
Intelligence Capture System - Main Entry Point

Usage:
    python run.py                    # Process all interviews
    python run.py --test             # Process only first interview (for testing)
    python run.py --stats            # Show database stats only
"""
import sys
import json
from pathlib import Path
from processor import IntelligenceProcessor
from config import INTERVIEWS_FILE, DB_PATH


def test_single_interview():
    """Test with a single interview"""
    print("🧪 TEST MODE - Processing first interview only\n")
    
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)
    
    if not interviews:
        print("❌ No interviews found")
        return
    
    processor = IntelligenceProcessor()
    processor.initialize()
    
    try:
        processor.process_interview(interviews[0])
        
        # Show stats
        stats = processor.db.get_stats()
        print(f"\n📊 TEST RESULTS")
        print(f"{'='*60}")
        for key, value in stats.items():
            if key != 'by_company':
                print(f"{key}: {value}")
    finally:
        processor.close()


def show_stats():
    """Show database statistics"""
    if not DB_PATH.exists():
        print("❌ Database not found. Run processing first.")
        return
    
    processor = IntelligenceProcessor()
    processor.initialize()
    
    try:
        stats = processor.db.get_stats()
        
        print(f"\n📊 DATABASE STATISTICS")
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
    finally:
        processor.close()


def process_all():
    """Process all interviews"""
    print("🚀 INTELLIGENCE CAPTURE SYSTEM")
    print("="*60)
    print(f"Database: {DB_PATH}")
    print(f"Interviews: {INTERVIEWS_FILE}")
    print("="*60)
    
    processor = IntelligenceProcessor()
    processor.initialize()
    
    try:
        processor.process_all_interviews()
    finally:
        processor.close()
    
    print(f"\n✅ DONE! Database saved to: {DB_PATH}")


def main():
    """Main entry point"""
    
    # Check if OpenAI API key is set
    import os
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY environment variable not set")
        print("\nSet it with:")
        print("  export OPENAI_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Parse arguments
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "--test":
            test_single_interview()
        elif arg == "--stats":
            show_stats()
        elif arg == "--help":
            print(__doc__)
        else:
            print(f"Unknown argument: {arg}")
            print(__doc__)
    else:
        # Default: process all
        process_all()


if __name__ == "__main__":
    main()
