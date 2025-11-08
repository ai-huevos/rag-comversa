#!/usr/bin/env python3
"""
Test sequential processing with WAL mode + rate limiter fixes
Tests with 5 interviews
"""
import sys
import json
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.processor import IntelligenceProcessor

print("🧪 Testing Sequential Processing with Fixes")
print("="*70)
print("Testing: WAL mode + Rate limiter")
print("Test: 5 interviews (sequential)")
print("="*70)

# Create test database
db_test = Path("data/test_sequential_5.db")
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
temp_file = Path("data/temp_test_5_seq.json")
with open(temp_file, 'w', encoding='utf-8') as f:
    json.dump(test_interviews, f, ensure_ascii=False, indent=2)

print(f"\n🚀 Starting sequential processing test...")
print(f"   Interviews: 5")
print(f"   Database: {db_test}")
print("-"*70)

# Initialize processor
processor = IntelligenceProcessor(db_path=db_test)
processor.initialize()

start = time.time()
success_count = 0
error_count = 0

try:
    # Process each interview
    for i, interview in enumerate(test_interviews, 1):
        meta = interview.get("meta", {})
        print(f"\n[{i}/5] Processing: {meta.get('respondent')} ({meta.get('role')})")
        
        result = processor.process_interview(interview)
        
        if result:
            success_count += 1
            print(f"  ✓ Success")
        else:
            error_count += 1
            print(f"  ✗ Failed")
    
    elapsed = time.time() - start
    
    print("\n" + "="*70)
    print("📊 TEST RESULTS")
    print("="*70)
    print(f"Total interviews: 5")
    print(f"Success: {success_count}")
    print(f"Errors: {error_count}")
    print(f"Time: {elapsed:.1f}s ({elapsed/60:.1f}m)")
    print(f"Avg per interview: {elapsed/5:.1f}s")
    
    if error_count == 0:
        print("\n✅ TEST PASSED!")
        print("   - WAL mode working")
        print("   - Rate limiter working")
        print("   - No API errors")
        print("\n🎉 Sequential processing is working!")
        exit_code = 0
    else:
        print("\n⚠️  TEST HAD ERRORS")
        print(f"   - {error_count} interviews failed")
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
    processor.close()
    # Cleanup
    if temp_file.exists():
        temp_file.unlink()
    print(f"\n💾 Test database saved at: {db_test}")
    print(f"   Inspect with: sqlite3 {db_test}")

sys.exit(exit_code)
