# Testing & Validation Scripts

This directory contains scripts for testing and validating the Intelligence Extraction System.

## Scripts Overview

### 1. validate_extraction.py
Comprehensive validation script that checks extraction completeness, quality, and integrity.

**Usage:**
```bash
# Validate default database
python scripts/validate_extraction.py

# Validate specific database
python scripts/validate_extraction.py --db path/to/database.db

# Export validation report to JSON
python scripts/validate_extraction.py --export reports/validation_report.json
```

**What it checks:**
- Entity counts for all 17 entity types
- Interview coverage (all interviews processed)
- Referential integrity (no orphaned entities)
- Data quality (empty fields, encoding issues)
- Duplicate detection

**Exit codes:**
- 0: All validation checks passed
- 1: Validation issues detected

---

### 2. test_single_interview.py
Test extraction on a single interview to verify the system works correctly.

**Usage:**
```bash
# Test with first interview (index 0)
python scripts/test_single_interview.py

# Test with specific interview
python scripts/test_single_interview.py --index 5

# Test with custom database path
python scripts/test_single_interview.py --db data/my_test.db
```

**What it does:**
- Extracts entities from one interview
- Verifies all entity types are extracted
- Shows sample extracted entities
- Checks data quality
- Saves to test database

**Output:**
- Creates `data/test_single.db` by default
- Prints detailed extraction results
- Shows entity counts and samples

---

### 3. test_batch_interviews.py
Test extraction on a batch of interviews (default: 5) to verify consistency and performance.

**Usage:**
```bash
# Test with 5 interviews (default)
python scripts/test_batch_interviews.py

# Test with custom batch size
python scripts/test_batch_interviews.py --batch-size 10

# Test resume capability
python scripts/test_batch_interviews.py --test-resume

# Test with custom database
python scripts/test_batch_interviews.py --db data/my_batch_test.db
```

**What it does:**
- Processes multiple interviews
- Tracks performance metrics (time, entities/sec)
- Checks consistency across interviews
- Estimates time for full 44-interview run
- Tests resume capability (optional)

**Output:**
- Creates `data/test_batch.db` by default
- Shows per-interview breakdown
- Displays performance metrics
- Estimates full extraction time

---

## Testing Workflow

### Quick Verification
Test that extraction is working:
```bash
python scripts/test_single_interview.py
```

### Performance Testing
Test with a batch to check speed and consistency:
```bash
python scripts/test_batch_interviews.py --batch-size 5
```

### Full Validation
After running extraction on the full database:
```bash
python scripts/validate_extraction.py --export reports/validation_report.json
```

### Resume Testing
Verify resume capability works:
```bash
python scripts/test_batch_interviews.py --test-resume
```

---

## Interpreting Results

### Validation Script
- **✓ Green checkmarks**: Everything is working correctly
- **⚠ Yellow warnings**: Some issues detected but not critical
- **✗ Red errors**: Critical issues that need fixing

### Test Scripts
- **Success**: All interviews processed without errors
- **Total entities**: Should be > 0 for successful extraction
- **Avg entities/interview**: Typically 10-50 depending on interview
- **Quality issues**: Should be 0 or minimal

---

## Common Issues & Solutions

### Issue: "Table not found" errors
**Solution**: The database schema hasn't been initialized properly. Run the initialization first.

### Issue: Zero entities extracted
**Solution**: Check OpenAI API key is set correctly in `.env` file.

### Issue: Encoding issues detected
**Solution**: Verify UTF-8 encoding is being used consistently. Check validation.py settings.

### Issue: Resume not working
**Solution**: Check extraction_status column exists in interviews table.

---

## Next Steps

After all tests pass:
1. Run full extraction: `python intelligence_capture/run.py`
2. Validate results: `python scripts/validate_extraction.py`
3. Review metrics in the monitoring dashboard output
4. Check validation report for any quality issues

---

## Dependencies

All scripts require:
- Python 3.8+
- SQLite3
- OpenAI API key (in `.env`)
- Intelligence Capture System installed

See main project README for installation instructions.
