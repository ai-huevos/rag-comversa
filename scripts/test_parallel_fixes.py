#!/usr/bin/env python3
"""
Test parallel processing fixes (WAL mode + rate limiter)
Tests with 5 interviews using 2 workers
"""
import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    from intelligence_capture.parallel_processor import ParallelProcessor
    from intelligence_capture.config import PROJECT_ROOT
    
    print("🧪 Testing Parallel Processing Fixes")
    print("="*70)
    print("Testing: WAL mode + Rate limiter")
    print("Test: 5 interviews with 2 workers")
    print("="*70)

    # Create test database
    db_test = PROJECT_ROOT / "data" / "test_parallel_5.db"
    if db_test.exists():
        db_test.unlink()
        print(f"✓ Cleaned up old test database")

    # Load first 5 interviews
    interviews_file = Path("data/interviews/analysis_output/all_interviews.json")
    print(f"\n📂 Loading interviews from: {interviews_file}")

    with open(interviews_file, 'r', encoding='utf-8') as f:
        all_interviews = json.load(f)

    # Take first 5
    test_interviews = all_interviews[:5]
    print(f"✓ Loaded {len(test_interviews)} interviews for testing")

    # Write to temp file
    temp_file = Path("data/temp_test_5.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(test_interviews, f, ensure_ascii=False, indent=2)

    print(f"\n🚀 Starting parallel processing test...")
    print(f"   Workers: 2")
    print(f"   Interviews: 5")
    print(f"   Database: {db_test}")
    print("-"*70)

    # Run parallel processing
    processor = ParallelProcessor(db_path=db_test, max_workers=2, enable_monitoring=True)

    start = time.time()
    try:
        results = processor.process_all_interviews_parallel(
            interviews_file=temp_file,
            resume=False
        )
        elapsed = time.time() - start
        
        print("\n" + "="*70)
        print("📊 TEST RESULTS")
        print("="*70)
        print(f"Total interviews: {results['total']}")
        print(f"Processed: {results['processed']}")
        print(f"Success: {results['success']}")
        print(f"Errors: {results['errors']}")
        print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
        print(f"Avg per interview: {elapsed/results['total']:.1f}s")
        
        if results['errors'] == 0:
            print("\n✅ TEST PASSED!")
            print("   - No database locking errors")
            print("   - No rate limit errors")
            print("   - All interviews processed successfully")
            print("\n🎉 Parallel processing is working!")
            exit_code = 0
        else:
            print("\n⚠️  TEST HAD ERRORS")
            print(f"   - {results['errors']} interviews failed")
            print("   - Check error messages above")
            exit_code = 1
            
    except Exception as e:
        print("\n" + "="*70)
        print("❌ TEST FAILED")
        print("="*70)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        exit_code = 1
    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()
        print(f"\n💾 Test database saved at: {db_test}")
        print(f"   Inspect with: sqlite3 {db_test}")

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
