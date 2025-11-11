# Extraction Logging Guide

**Last Updated:** November 11, 2025
**Status:** ✅ Implemented and Tested

---

## Overview

Comprehensive logging infrastructure for the Intelligence Capture extraction pipeline, providing both console output and persistent file logging for debugging, monitoring, and audit trails.

## Log Files

### Primary Logs

| Log File | Purpose | Updated By |
|----------|---------|------------|
| `logs/extraction.log` | Extraction pipeline operations | `full_extraction_pipeline.py`, `test_batch_interviews.py` |
| `logs/consolidation.log` | Entity consolidation operations | `consolidation_agent.py` |

### Log Location
```bash
system0/
├── logs/
│   ├── extraction.log      # NEW - Extraction pipeline logs
│   └── consolidation.log   # Existing - Consolidation logs
```

## Features

### Dual Output
- **Console**: User-friendly formatted output with emojis
- **File**: Timestamped structured logs for analysis

### Log Levels
- `INFO`: Normal operations, progress updates, summaries
- `ERROR`: Extraction failures, API errors, database issues
- `DEBUG`: Detailed extractor calls, timing information (when enabled)

### Automatic Log Rotation
- Logs append to existing file
- UTF-8 encoding for Spanish content
- Timestamp format: `YYYY-MM-DD HH:MM:SS`

## Usage Examples

### Running Full Extraction Pipeline
```bash
# Run full extraction (44 interviews)
python scripts/full_extraction_pipeline.py

# Check logs in real-time
tail -f logs/extraction.log

# Search for errors
grep -i "error\|failed" logs/extraction.log

# Count entities extracted
grep "entities extracted" logs/extraction.log
```

### Running Batch Tests
```bash
# Test with 5 interviews
python scripts/test_batch_interviews.py

# Test with specific batch size
python scripts/test_batch_interviews.py --batch-size 10

# Monitor progress
tail -f logs/extraction.log | grep "Processing\|Completed"
```

### Testing Logging Infrastructure
```bash
# Validate logging is working
python scripts/test_logging.py

# Verify log file created
ls -lh logs/extraction.log
```

## Log Entry Examples

### Extraction Start
```
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
2025-11-11 01:21:53 - intelligence_capture - INFO - 🚀 EXTRACTION PIPELINE STARTED
2025-11-11 01:21:53 - intelligence_capture - INFO -    Timestamp: 2025-11-11 01:21:53
2025-11-11 01:21:53 - intelligence_capture - INFO -    Total interviews: 44
2025-11-11 01:21:53 - intelligence_capture - INFO -    Batch size: 5
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
```

### Batch Progress
```
2025-11-11 01:21:53 - intelligence_capture - INFO -
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
2025-11-11 01:21:53 - intelligence_capture - INFO - 📦 BATCH 1/9
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
```

### Interview Processing
```
2025-11-11 01:21:53 - intelligence_capture - INFO -
[1/44] 📝 Processing: Los Tajibos / IT Manager
2025-11-11 01:21:53 - intelligence_capture - INFO -   ✅ Completed in 45.3s | Total entities: 10
2025-11-11 01:21:53 - intelligence_capture - INFO -      - PainPoint: 5
2025-11-11 01:21:53 - intelligence_capture - INFO -      - System: 3
2025-11-11 01:21:53 - intelligence_capture - INFO -      - AutomationCandidate: 2
```

### Error Logging
```
2025-11-11 01:21:53 - intelligence_capture - ERROR -   ❌ Error processing interview test_interview: Test extraction error
2025-11-11 01:21:53 - intelligence_capture - ERROR - Test extraction error
Traceback (most recent call last):
  File "/Users/tatooine/Documents/Development/Comversa/system0/scripts/test_logging.py", line 54, in main
    raise ValueError("Test extraction error")
ValueError: Test extraction error
```

### Extraction Complete
```
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
2025-11-11 01:21:53 - intelligence_capture - INFO - ✅ EXTRACTION PIPELINE COMPLETED
2025-11-11 01:21:53 - intelligence_capture - INFO -    Duration: 1834.5s (30.6m)
2025-11-11 01:21:53 - intelligence_capture - INFO -    Processed: 42/44
2025-11-11 01:21:53 - intelligence_capture - INFO -    Failed: 2
2025-11-11 01:21:53 - intelligence_capture - INFO -    Avg time/interview: 41.7s
2025-11-11 01:21:53 - intelligence_capture - INFO -
2025-11-11 01:21:53 - intelligence_capture - INFO - 📊 ENTITIES EXTRACTED:
2025-11-11 01:21:53 - intelligence_capture - INFO -    AutomationCandidate: 67
2025-11-11 01:21:53 - intelligence_capture - INFO -    DataFlow: 45
2025-11-11 01:21:53 - intelligence_capture - INFO -    PainPoint: 120
2025-11-11 01:21:53 - intelligence_capture - INFO -    System: 89
2025-11-11 01:21:53 - intelligence_capture - INFO -    TemporalPattern: 56
2025-11-11 01:21:53 - intelligence_capture - INFO - ======================================================================
```

## Log Analysis Commands

### Quick Stats
```bash
# Count total interviews processed
grep "Processing:" logs/extraction.log | wc -l

# Count successful completions
grep "✅ Completed" logs/extraction.log | wc -l

# Count errors
grep -c "ERROR" logs/extraction.log

# Find slowest interviews
grep "Completed in" logs/extraction.log | sort -t: -k2 -n | tail -5

# Entity extraction summary
grep "ENTITIES EXTRACTED" -A 20 logs/extraction.log | tail -1
```

### Performance Analysis
```bash
# Average time per interview
grep "Avg time/interview" logs/extraction.log | tail -1

# Total duration of last run
grep "Duration:" logs/extraction.log | tail -1

# Entities per interview
grep "Total entities:" logs/extraction.log
```

### Error Investigation
```bash
# List all errors
grep "ERROR" logs/extraction.log

# Errors with context (3 lines before/after)
grep -B3 -A3 "ERROR" logs/extraction.log

# Failed interviews
grep "Error processing interview" logs/extraction.log

# Specific extractor failures
grep "extraction failed" logs/extraction.log
```

## Programmatic Access

### Using Logging in Scripts
```python
from intelligence_capture.logging_config import (
    setup_extraction_logging,
    log_extraction_start,
    log_extraction_complete,
    log_interview_start,
    log_interview_complete,
    log_interview_error,
    log_batch_progress
)

# Initialize logger
logger = setup_extraction_logging()

# Log extraction start
log_extraction_start(logger, total_interviews=44, batch_size=5)

# Log interview processing
log_interview_start(logger, 1, 44, "Los Tajibos", "IT Manager")
# ... process interview ...
log_interview_complete(logger, "interview_1", duration=45.3, entities={"PainPoint": 5})

# Log completion
log_extraction_complete(logger, 44, 42, 2, 1834.5, entity_counts)
```

### Custom Logging
```python
# Direct logger access
logger = setup_extraction_logging()
logger.info("Custom information message")
logger.warning("Custom warning message")
logger.error("Custom error message")
logger.debug("Custom debug message")  # Only if log_level=logging.DEBUG
```

## Files Modified

### New Files
- `intelligence_capture/logging_config.py` - Logging infrastructure
- `scripts/test_logging.py` - Logging validation script
- `docs/EXTRACTION_LOGGING.md` - This documentation

### Updated Files
- `scripts/full_extraction_pipeline.py` - Added comprehensive logging
- `scripts/test_batch_interviews.py` - Added logging integration

## Integration with Zero-AI Framework

This logging infrastructure supports the **Production Readiness Checklist** from `.kiro/specs/zero-ai/requirements.md`:

- ✅ **Monitoring dashboard**: Logs provide data for monitoring extraction accuracy over time
- ✅ **Failure handling**: Comprehensive error logging with stack traces
- ✅ **Documentation**: This guide + inline code documentation

### Next Steps for Production (Jan 15, 2026)

1. **Add log aggregation** (Week 3-4):
   - Ship logs to centralized logging service (e.g., CloudWatch, Datadog)
   - Set up alerts for error patterns

2. **Add performance metrics** (Week 4):
   - Track extraction latency percentiles
   - Monitor API costs per interview
   - Alert on degraded performance

3. **Add audit trail** (Week 4):
   - Log all entity modifications
   - Track consolidation decisions
   - Enable compliance reporting

## Troubleshooting

### Log File Not Created
```bash
# Check logs directory exists
ls -la logs/

# Create if missing
mkdir -p logs

# Check permissions
ls -la logs/
```

### Logs Not Appearing
```bash
# Check if logger is initialized
python scripts/test_logging.py

# Verify imports
python -c "from intelligence_capture.logging_config import setup_extraction_logging; print('OK')"
```

### Disk Space Issues
```bash
# Check log file size
ls -lh logs/extraction.log

# Archive old logs
tar -czf logs/archive/extraction_$(date +%Y%m%d).tar.gz logs/extraction.log
> logs/extraction.log  # Clear current log
```

## References

- **Implementation**: `intelligence_capture/logging_config.py`
- **Usage**: `scripts/full_extraction_pipeline.py`, `scripts/test_batch_interviews.py`
- **Testing**: `scripts/test_logging.py`
- **Related**: `logs/consolidation.log` (existing consolidation logging)

---

**Status**: ✅ Production Ready
**Test Coverage**: Validated with `scripts/test_logging.py`
**Next Review**: Week 3 (RAG 2.0 Phase 3)
