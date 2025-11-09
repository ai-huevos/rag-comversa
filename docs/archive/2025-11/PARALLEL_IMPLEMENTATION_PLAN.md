# Parallel Processing Implementation Plan

**Goal**: Fix parallel processing, implement Knowledge Graph, run clean extraction

**Timeline**: 3-4 days for parallel + validation, then 3 weeks for Knowledge Graph (optional)

---

## Phase 1: Fix Parallel Processing (Day 1-2)

### Step 1.1: Backup Current State (30 minutes)

**What**: Save current database and code state

```bash
# Backup existing databases
mkdir -p backups/$(date +%Y%m%d)
cp data/*.db backups/$(date +%Y%m%d)/ 2>/dev/null || true

# Backup current code
git add -A
git commit -m "backup: Before parallel processing fixes"
git push origin main
```

**Files to backup**:
- `data/intelligence.db` (if exists)
- `data/full_intelligence.db` (if exists)
- All code in `intelligence_capture/`

---

### Step 1.2: Fix Database Locking (2 hours)

**Problem**: SQLite doesn't handle concurrent writes

**Solution**: Enable WAL mode + busy timeout

**File**: `intelligence_capture/database.py`

**Changes needed**:

```python
# In IntelligenceDB.__init__() or connect() method

def connect(self):
    """Connect to database with WAL mode for parallel processing"""
    self.conn = sqlite3.connect(
        self.db_path,
        timeout=30.0,  # Wait up to 30s for locks
        check_same_thread=False  # Allow multi-threading
    )
    
    # Enable WAL mode for concurrent access
    self.conn.execute("PRAGMA journal_mode=WAL")
    
    # Set busy timeout (wait 5s if database is locked)
    self.conn.execute("PRAGMA busy_timeout=5000")
    
    # Enable foreign keys
    self.conn.execute("PRAGMA foreign_keys=ON")
    
    print("✓ Database connected with WAL mode (parallel-safe)")
```

**Why this works**:
- WAL mode allows multiple readers + one writer
- Busy timeout makes workers wait instead of failing
- No more "database is locked" errors

---

### Step 1.3: Add Shared Rate Limiter (2 hours)

**Problem**: Multiple workers hit OpenAI rate limits

**Solution**: Shared rate limiter across all workers

**New File**: `intelligence_capture/rate_limiter.py`

```python
"""
Shared rate limiter for parallel processing
Ensures all workers respect OpenAI rate limits
"""
import time
import threading
from collections import deque
from datetime import datetime, timedelta


class RateLimiter:
    """
    Thread-safe rate limiter for API calls
    Tracks calls across all workers and enforces limits
    """
    
    def __init__(self, max_calls_per_minute=50):
        """
        Initialize rate limiter
        
        Args:
            max_calls_per_minute: Maximum API calls per minute (default: 50)
                                 Set below OpenAI limit (60) for safety margin
        """
        self.max_calls = max_calls_per_minute
        self.calls = deque()  # Track timestamps of recent calls
        self.lock = threading.Lock()  # Thread-safe access
        
    def wait_if_needed(self):
        """
        Wait if rate limit would be exceeded
        Call this BEFORE making an API call
        """
        with self.lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            
            # Remove calls older than 1 minute
            while self.calls and self.calls[0] < one_minute_ago:
                self.calls.popleft()
            
            # Check if we're at the limit
            if len(self.calls) >= self.max_calls:
                # Calculate how long to wait
                oldest_call = self.calls[0]
                wait_until = oldest_call + timedelta(minutes=1)
                wait_seconds = (wait_until - now).total_seconds()
                
                if wait_seconds > 0:
                    print(f"  ⏳ Rate limit: waiting {wait_seconds:.1f}s...")
                    time.sleep(wait_seconds + 0.1)  # Add small buffer
                    
                    # Clean up old calls after waiting
                    now = datetime.now()
                    one_minute_ago = now - timedelta(minutes=1)
                    while self.calls and self.calls[0] < one_minute_ago:
                        self.calls.popleft()
            
            # Record this call
            self.calls.append(now)
    
    def get_current_rate(self):
        """Get current calls per minute"""
        with self.lock:
            now = datetime.now()
            one_minute_ago = now - timedelta(minutes=1)
            
            # Count calls in last minute
            recent_calls = sum(1 for call_time in self.calls if call_time > one_minute_ago)
            return recent_calls


# Global rate limiter instance (shared across all workers)
_global_rate_limiter = None


def get_rate_limiter(max_calls_per_minute=50):
    """Get or create global rate limiter instance"""
    global _global_rate_limiter
    if _global_rate_limiter is None:
        _global_rate_limiter = RateLimiter(max_calls_per_minute)
    return _global_rate_limiter
```

---

### Step 1.4: Update Extractor to Use Rate Limiter (1 hour)

**File**: `intelligence_capture/extractor.py`

**Changes**:

```python
# At top of file
from .rate_limiter import get_rate_limiter

class IntelligenceExtractor:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.rate_limiter = get_rate_limiter(max_calls_per_minute=50)
        # ... rest of init
    
    def _call_gpt4(self, system_prompt: str, user_prompt: str) -> Dict:
        """Call GPT-4 with rate limiting and retry logic"""
        import time
        from openai import RateLimitError
        
        for attempt in range(MAX_RETRIES):
            try:
                # WAIT for rate limiter BEFORE making call
                self.rate_limiter.wait_if_needed()
                
                response = self.client.chat.completions.create(
                    model=MODEL,
                    temperature=TEMPERATURE,
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                )
                
                result = json.loads(response.choices[0].message.content)
                return result
                
            except RateLimitError as e:
                # Should rarely happen now with rate limiter
                wait_time = min(2 ** attempt, 60)
                print(f"  ⚠️  Rate limit hit (unexpected), waiting {wait_time}s...")
                time.sleep(wait_time)
                if attempt == MAX_RETRIES - 1:
                    print(f"  ❌ Rate limit exceeded after {MAX_RETRIES} attempts")
                    return {}
            except Exception as e:
                print(f"  ⚠️  Attempt {attempt + 1} failed: {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    print(f"  ❌ Failed after {MAX_RETRIES} attempts")
                    return {}
                time.sleep(1)
        
        return {}
```

---

### Step 1.5: Update Parallel Processor (1 hour)

**File**: `intelligence_capture/parallel_processor.py`

**Changes**: Ensure it uses the fixed database and rate limiter

```python
# Worker function already creates its own processor
# Processor will automatically use WAL mode and rate limiter
# No changes needed if database.py and extractor.py are fixed

# But add better error handling:

def _process_single_interview(interview: Dict, db_path: Path) -> Dict[str, Any]:
    """
    Worker function with improved error handling
    """
    import time
    
    start_time = time.time()
    meta = interview.get("meta", {})
    company = meta.get("company", "Unknown")
    respondent = meta.get("respondent", "Unknown")
    
    try:
        # Create processor (will use WAL mode automatically)
        processor = IntelligenceProcessor(db_path=db_path)
        processor.initialize()
        
        # Process interview
        success = processor.process_interview(interview)
        
        # Close processor
        processor.close()
        
        elapsed = time.time() - start_time
        
        return {
            "success": success,
            "company": company,
            "respondent": respondent,
            "elapsed_time": elapsed,
            "error": None
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        error_msg = str(e)[:200]  # Truncate long errors
        print(f"  ❌ Worker error for {company}/{respondent}: {error_msg}")
        
        return {
            "success": False,
            "company": company,
            "respondent": respondent,
            "elapsed_time": elapsed,
            "error": error_msg
        }
```

---

### Step 1.6: Test Parallel Processing (1 hour)

**Test Script**: `scripts/test_parallel.py` (new)

```python
#!/usr/bin/env python3
"""
Test parallel processing with fixes
"""
import sys
from pathlib import Path
import time

sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.parallel_processor import ParallelProcessor

print("🧪 Testing Parallel Processing Fixes\n")
print("="*60)

# Test 1: Small batch (5 interviews, 2 workers)
print("\nTest 1: 5 interviews with 2 workers")
print("-"*60)

db_test = Path("data/test_parallel_5.db")
if db_test.exists():
    db_test.unlink()

processor = ParallelProcessor(db_path=db_test, max_workers=2)

start = time.time()
results = processor.process_all_interviews_parallel(
    interviews_file=Path("data/interviews/analysis_output/all_interviews.json"),
    resume=False
)
elapsed = time.time() - start

print(f"\n✓ Test 1 Complete:")
print(f"  Time: {elapsed:.1f}s")
print(f"  Success: {results['success']}/{results['total']}")
print(f"  Errors: {results['errors']}")

if results['errors'] == 0:
    print("  ✅ No errors - parallel processing working!")
else:
    print("  ⚠️  Some errors occurred")

# Test 2: Larger batch (10 interviews, 4 workers)
print("\n" + "="*60)
print("\nTest 2: 10 interviews with 4 workers")
print("-"*60)

db_test2 = Path("data/test_parallel_10.db")
if db_test2.exists():
    db_test2.unlink()

processor2 = ParallelProcessor(db_path=db_test2, max_workers=4)

start = time.time()
results2 = processor2.process_all_interviews_parallel(
    interviews_file=Path("data/interviews/analysis_output/all_interviews.json"),
    resume=False
)
elapsed2 = time.time() - start

print(f"\n✓ Test 2 Complete:")
print(f"  Time: {elapsed2:.1f}s")
print(f"  Success: {results2['success']}/{results2['total']}")
print(f"  Errors: {results2['errors']}")

if results2['errors'] == 0:
    print("  ✅ No errors - parallel processing working!")
else:
    print("  ⚠️  Some errors occurred")

# Summary
print("\n" + "="*60)
print("📊 PARALLEL PROCESSING TEST SUMMARY")
print("="*60)

if results['errors'] == 0 and results2['errors'] == 0:
    print("✅ All tests passed!")
    print("✅ Parallel processing is working correctly")
    print("\nNext: Run full 44-interview extraction with parallel mode")
else:
    print("⚠️  Some tests had errors")
    print("Review error messages above")
    print("May need additional fixes")
```

**Run test**:
```bash
python3 scripts/test_parallel.py
```

**Expected output**:
```
Test 1: 5 interviews with 2 workers
✓ Test 1 Complete:
  Time: 90.0s
  Success: 5/5
  Errors: 0
  ✅ No errors - parallel processing working!

Test 2: 10 interviews with 4 workers
✓ Test 2 Complete:
  Time: 80.0s
  Success: 10/10
  Errors: 0
  ✅ No errors - parallel processing working!

✅ All tests passed!
✅ Parallel processing is working correctly
```

---

## Phase 2: Clean State Extraction (Day 3)

### Step 2.1: Backup v1.0 Data (15 minutes)

```bash
# Create backup directory
mkdir -p backups/v1.0_extraction

# Backup all existing databases
cp data/*.db backups/v1.0_extraction/ 2>/dev/null || true

# Backup any reports
cp -r reports/ backups/v1.0_extraction/reports/ 2>/dev/null || true

# Document what was backed up
echo "Backup created: $(date)" > backups/v1.0_extraction/README.txt
echo "Contains: v1.0 extraction databases and reports" >> backups/v1.0_extraction/README.txt
ls -lh backups/v1.0_extraction/ >> backups/v1.0_extraction/README.txt
```

---

### Step 2.2: Clean State (5 minutes)

```bash
# Remove old databases (keep backups!)
rm data/intelligence.db 2>/dev/null || true
rm data/full_intelligence.db 2>/dev/null || true
rm data/test_*.db 2>/dev/null || true

# Clear old reports
rm -rf reports/*.json reports/*.xlsx 2>/dev/null || true

# Verify clean state
ls -la data/*.db 2>/dev/null || echo "✓ No databases (clean state)"
```

---

### Step 2.3: Run Full Extraction with Parallel Mode (20 minutes)

```bash
# Run with parallel processing (4 workers)
python3 intelligence_capture/parallel_processor.py --workers 4

# Or use main script (will use sequential by default)
python3 intelligence_capture/run.py
```

**Expected**:
- Time: 5-8 minutes (parallel) or 15-20 minutes (sequential)
- Cost: $0.50-1.00
- All 44 interviews processed
- Database: `data/intelligence.db`

---

### Step 2.4: Validate Extraction (5 minutes)

```bash
# Run validation
python3 scripts/validate_extraction.py

# Generate report
python3 scripts/generate_comprehensive_report.py --format both
```

**Check**:
- All 17 entity types have data
- All 44 interviews processed
- No critical errors
- Quality metrics acceptable

---

## Phase 3: Knowledge Graph (Optional, 3 weeks)

### Decision Point

**After Phase 2 extraction, analyze results**:

1. **Check for duplicates**:
   ```sql
   sqlite3 data/intelligence.db
   
   -- How many times is each system mentioned?
   SELECT name, COUNT(*) as mentions
   FROM systems
   GROUP BY name
   HAVING mentions > 1
   ORDER BY mentions DESC
   LIMIT 20;
   ```

2. **Check for patterns**:
   ```sql
   -- Most common pain points
   SELECT description, COUNT(*) as frequency
   FROM pain_points
   GROUP BY description
   HAVING frequency > 2
   ORDER BY frequency DESC
   LIMIT 10;
   ```

3. **Decide**:
   - **Many duplicates + patterns** → Implement Knowledge Graph
   - **Few duplicates, obvious patterns** → Skip Knowledge Graph
   - **Unsure** → Implement just consolidation (Week 1 only)

---

### If Implementing Knowledge Graph

**Week 1: Consolidation** (5 days)
- Day 1: Create `consolidation_agent.py`
- Day 2: Add database tables for consolidation
- Day 3: Implement entity merging logic
- Day 4: Test with 5 interviews
- Day 5: Run on full 44 interviews

**Week 2: Relationships** (5 days)
- Day 1: Create `relationship_agent.py`
- Day 2: Add relationships table
- Day 3: Implement relationship discovery
- Day 4: Test relationship queries
- Day 5: Generate relationship reports

**Week 3: Intelligence** (5 days)
- Day 1-2: Create `pattern_agent.py`
- Day 3-4: Create `contradiction_detector.py`
- Day 5: Build simple dashboard/reports

---

## Timeline Summary

### Fast Track (No Knowledge Graph)
- **Day 1-2**: Fix parallel processing
- **Day 3**: Clean extraction with parallel mode
- **Total**: 3 days

### Full Track (With Knowledge Graph)
- **Day 1-2**: Fix parallel processing
- **Day 3**: Clean extraction
- **Week 2-4**: Implement Knowledge Graph
- **Total**: 3-4 weeks

---

## Success Criteria

### Phase 1 Success (Parallel Processing)
- ✅ Test with 5 interviews: 0 errors
- ✅ Test with 10 interviews: 0 errors
- ✅ No "database is locked" errors
- ✅ No rate limit errors
- ✅ Speedup: 2-3x faster than sequential

### Phase 2 Success (Clean Extraction)
- ✅ All 44 interviews processed
- ✅ All 17 entity types have data
- ✅ Validation passes
- ✅ Cost: $0.50-1.00
- ✅ Time: 5-8 minutes (parallel) or 15-20 minutes (sequential)

### Phase 3 Success (Knowledge Graph - Optional)
- ✅ Duplicates consolidated
- ✅ Relationships discovered
- ✅ Patterns detected
- ✅ Contradictions flagged
- ✅ Reports generated

---

## Risk Mitigation

### Backup Strategy
- ✅ Backup before each phase
- ✅ Keep v1.0 data separate
- ✅ Git commits at each step
- ✅ Can rollback if needed

### Testing Strategy
- ✅ Test with 5 interviews first
- ✅ Then 10 interviews
- ✅ Then full 44 interviews
- ✅ Validate at each step

### Fallback Plan
- If parallel fails → Use sequential mode
- If Knowledge Graph too complex → Skip it
- If extraction fails → Restore from backup

---

## Next Steps

**Immediate** (Start now):
1. Read this plan
2. Confirm approach
3. Start Phase 1, Step 1.1 (backup)

**After confirmation**:
4. Implement database WAL mode
5. Implement rate limiter
6. Test parallel processing
7. Run clean extraction

---

**Plan Created**: 2025-11-08  
**Estimated Time**: 3 days (fast track) or 3-4 weeks (with Knowledge Graph)  
**Status**: Ready to start
