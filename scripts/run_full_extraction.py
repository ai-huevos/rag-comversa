#!/usr/bin/env python3
"""
Run full extraction on all interviews
"""
import sys
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.processor import IntelligenceProcessor
from intelligence_capture.config import DB_PATH, INTERVIEWS_FILE


def main():
    """Run full extraction on all interviews"""
    print("=" * 70)
    print("🚀 FULL EXTRACTION STARTED")
    print("=" * 70)

    # Load all interviews
    print(f"\n📂 Loading interviews from: {INTERVIEWS_FILE}")
    with open(INTERVIEWS_FILE, 'r', encoding='utf-8') as f:
        interviews = json.load(f)

    print(f"✓ Loaded {len(interviews)} interviews for processing\n")

    # Initialize processor
    print(f"🔧 Initializing processor with database: {DB_PATH}")
    processor = IntelligenceProcessor(db_path=DB_PATH)
    processor.initialize()
    print("✓ Processor initialized\n")

    # Process all interviews
    print(f"🚀 Processing {len(interviews)} interviews...")
    print("=" * 70)

    try:
        for i, interview in enumerate(interviews, 1):
            meta = interview.get("meta", {})
            print(f"\n[{i}/{len(interviews)}] Processing {meta.get('company', '')} / {meta.get('respondent', 'Unknown')}")

            try:
                processor.process_interview(interview)
                print(f"  ✅ Completed")
            except Exception as e:
                print(f"  ❌ Error: {e}")
                continue

        # Show final stats
        print("\n" + "=" * 70)
        print("📊 FINAL STATISTICS")
        print("=" * 70)
        stats = processor.db.get_stats()
        for key, value in stats.items():
            if key != 'by_company':
                print(f"{key}: {value}")

        print("\n✅ Full extraction completed successfully!")

    finally:
        processor.close()


if __name__ == "__main__":
    main()
