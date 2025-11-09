# Knowledge Graph Consolidation - Production Runbook

**Version**: 1.0.0  
**Last Updated**: 2025-11-09  
**Status**: Production Ready  
**Owner**: System0 Intelligence Team

---

## Overview

This runbook provides operational procedures for running the Knowledge Graph Consolidation system in production. The consolidation system merges duplicate entities, discovers relationships, and identifies patterns across 44 manager interviews.

**System Capabilities:**
- Duplicate detection using fuzzy + semantic similarity
- Entity merging with contradiction detection
- Relationship discovery (System → Pain Point, Process → System)
- Pattern recognition (recurring pain points, problematic systems)
- Consensus confidence scoring
- Full audit trail and rollback capability

**Performance Metrics:**
- Processing time: <5 minutes for 44 interviews
- Duplicate reduction: 80-95% expected (when run on fresh extractions)
- Relationships discovered: 100+ expected
- Patterns identified: 10+ expected

---

## Pre-Flight Checklist

Before running consolidation in production, verify:

### 1. Environment Setup
- [ ] Python 3.8+ installed
- [ ] Virtual environment activated: `source venv/bin/activate`
- [ ] Dependencies installed: `pip install -r intelligence_capture/requirements.txt`
- [ ] OpenAI API key set: `export OPENAI_API_KEY=sk-...`

### 2. Database Backup
```bash
# Backup production database
cp data/full_intelligence.db data/full_intelligence_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh data/full_intelligence_backup_*.db
```

### 3. Configuration Validation
```bash
# Check consolidation config exists
cat config/consolidation_config.json

# Verify similarity thresholds
python -c "import json; print(json.load(open('config/consolidation_config.json'))['similarity_thresholds'])"
```

### 4. Dependency Check
```bash
# Run setup check
python scripts/check_setup.py

# Verify database accessible
sqlite3 data/full_intelligence.db "SELECT COUNT(*) FROM interviews;"
```

---

## Running Consolidation

### Option 1: Test with Sample Interviews (Recommended First)

```bash
# Test with 5 interviews
python scripts/test_consolidation_with_interviews.py --interviews 5

# Expected output:
# - Processing time: <30 seconds
# - All validation checks pass
# - Report saved to reports/consolidation_test_*.json
```

### Option 2: Full Production Run (44 Interviews)

```bash
# Run full consolidation
python scripts/test_consolidation_with_interviews.py --interviews 44

# Expected output:
# - Processing time: <5 minutes
# - Duplicate reduction: 0-95% (depends on data state)
# - Relationships discovered: 10-100+
# - Patterns identified: 4-10+
# - Report saved to reports/consolidation_test_*.json
```

### Option 3: Validate Existing Consolidation

```bash
# Run validation only (no consolidation)
python scripts/validate_consolidation.py

# Expected output:
# - All source counts valid
# - All confidence scores valid
# - No orphaned relationships
# - Report saved to reports/consolidation_report.json
```

---

## Monitoring Consolidation

### Real-Time Monitoring

Watch the consolidation log in real-time:
```bash
tail -f logs/consolidation.log
```

**Key log messages to watch for:**
- `INFO - Starting consolidation transaction` - Consolidation started
- `INFO - Consolidating {entity_type} ({count} entities)` - Processing entity type
- `INFO - Duplicates found: {count}` - Duplicates detected
- `INFO - Relationships discovered: {count}` - Relationships found
- `INFO - Consolidation transaction committed successfully` - Success
- `ERROR - Consolidation failed` - Failure (triggers rollback)

### Progress Tracking

Monitor progress via console output:
```
🔄 Processing 44 interviews...
  Processed: 5/44 (11%)
  Processed: 10/44 (23%)
  ...
  Processed: 44/44 (100%)
```

### Performance Metrics

Check processing time:
```bash
# View last consolidation time
grep "Processing time:" logs/consolidation.log | tail -1
```

---

## Common Issues & Troubleshooting

### Issue 1: API Rate Limit Exceeded

**Symptoms:**
```
ERROR - OpenAI API rate limit exceeded
ERROR - Consolidation failed: RateLimitError
```

**Resolution:**
1. Wait 60 seconds for rate limit to reset
2. Retry consolidation (automatic retry with exponential backoff)
3. If persistent, reduce batch size in config:
   ```json
   "performance": {
     "batch_size": 50  // Reduce from 100
   }
   ```

### Issue 2: Transaction Rollback

**Symptoms:**
```
ERROR - Consolidation failed: {error}
INFO - Rolling back transaction
```

**Resolution:**
1. Check error message in logs: `grep "ERROR" logs/consolidation.log | tail -5`
2. Common causes:
   - Database locked (another process accessing DB)
   - Invalid entity data (missing required fields)
   - API failure (network issue)
3. Fix underlying issue and retry
4. Database automatically rolled back to consistent state

### Issue 3: Low Confidence Scores

**Symptoms:**
```
⚠ Average consensus_confidence < 0.75
⚠ Many entities flagged for review
```

**Resolution:**
1. Review entities with low confidence:
   ```bash
   sqlite3 data/full_intelligence.db "SELECT name, consensus_confidence FROM systems WHERE consensus_confidence < 0.6;"
   ```
2. Check for contradictions:
   ```bash
   sqlite3 data/full_intelligence.db "SELECT name, contradiction_details FROM systems WHERE has_contradictions = 1;"
   ```
3. Adjust consensus parameters in config if needed:
   ```json
   "consensus_parameters": {
     "source_count_divisor": 5,  // Lower = higher confidence
     "single_source_penalty": 0.3  // Increase to penalize single sources more
   }
   ```

### Issue 4: No Duplicates Found

**Symptoms:**
```
Duplicate reduction: 0.0%
Duplicates found: 0
```

**Possible Causes:**
1. **Data already consolidated** - Entities were already merged in previous run
2. **Thresholds too high** - Similarity thresholds preventing matches
3. **No actual duplicates** - Data is genuinely unique

**Resolution:**
1. Check if entities have `is_consolidated = true`:
   ```bash
   sqlite3 data/full_intelligence.db "SELECT COUNT(*) FROM systems WHERE is_consolidated = 1;"
   ```
2. Lower similarity thresholds in config (carefully):
   ```json
   "similarity_thresholds": {
     "systems": 0.70  // Lower from 0.75
   }
   ```
3. Review entity names manually:
   ```bash
   sqlite3 data/full_intelligence.db "SELECT name FROM systems ORDER BY name;"
   ```

### Issue 5: Orphaned Relationships

**Symptoms:**
```
✗ Found 4 orphaned relationships
```

**Resolution:**
1. Identify orphaned relationships:
   ```bash
   python scripts/validate_consolidation.py
   ```
2. Clean up orphaned relationships:
   ```bash
   sqlite3 data/full_intelligence.db "DELETE FROM relationships WHERE target_entity_id NOT IN (SELECT id FROM systems);"
   ```
3. Re-run validation to confirm fix

---

## Performance Tuning

### Optimize for Speed

If consolidation is too slow (>5 minutes for 44 interviews):

1. **Enable fuzzy-first filtering** (should already be enabled):
   ```json
   "performance": {
     "fuzzy_first_filtering": {
       "enabled": true,
       "skip_semantic_threshold": 0.95
     }
   }
   ```

2. **Increase max_candidates** (reduces API calls):
   ```json
   "performance": {
     "max_candidates": 10  // Increase to 15-20 if needed
   }
   ```

3. **Pre-compute embeddings** (one-time cost):
   ```bash
   python scripts/precompute_embeddings.py
   ```

### Optimize for Quality

If duplicate detection is missing obvious duplicates:

1. **Lower similarity thresholds**:
   ```json
   "similarity_thresholds": {
     "pain_points": 0.65,  // Lower from 0.70
     "systems": 0.70       // Lower from 0.75
   }
   ```

2. **Increase semantic weight**:
   ```json
   "similarity_weights": {
     "semantic_weight": 0.4,  // Increase from 0.3
     "name_weight": 0.6       // Decrease from 0.7
   }
   ```

3. **Disable fuzzy-first filtering** (slower but more thorough):
   ```json
   "performance": {
     "fuzzy_first_filtering": {
       "enabled": false
     }
   }
   ```

---

## Quality Validation

### Post-Consolidation Checks

After consolidation completes, run these validation checks:

```bash
# 1. Run full validation
python scripts/validate_consolidation.py

# 2. Check entity counts
sqlite3 data/full_intelligence.db "SELECT 
  'pain_points' as type, COUNT(*) as count FROM pain_points
  UNION ALL SELECT 'systems', COUNT(*) FROM systems
  UNION ALL SELECT 'processes', COUNT(*) FROM processes;"

# 3. Check multi-source entities
sqlite3 data/full_intelligence.db "SELECT name, source_count FROM systems WHERE source_count > 1 ORDER BY source_count DESC LIMIT 10;"

# 4. Check relationships
sqlite3 data/full_intelligence.db "SELECT COUNT(*) FROM relationships;"

# 5. Check patterns
sqlite3 data/full_intelligence.db "SELECT pattern_type, COUNT(*) FROM patterns GROUP BY pattern_type;"
```

### Manual Sampling

Manually review a sample of consolidated entities:

```bash
# Top 10 most-mentioned entities
sqlite3 data/full_intelligence.db "SELECT name, source_count, consensus_confidence FROM systems ORDER BY source_count DESC LIMIT 10;"

# Entities with contradictions
sqlite3 data/full_intelligence.db "SELECT name, contradiction_details FROM systems WHERE has_contradictions = 1;"

# Recent consolidations
sqlite3 data/full_intelligence.db "SELECT name, consolidated_at FROM systems WHERE is_consolidated = 1 ORDER BY consolidated_at DESC LIMIT 10;"
```

---

## Rollback Consolidation

If consolidation produces incorrect results, rollback to previous state:

### Option 1: Restore from Backup

```bash
# Stop any running processes
pkill -f consolidation

# Restore backup
cp data/full_intelligence_backup_YYYYMMDD_HHMMSS.db data/full_intelligence.db

# Verify restoration
python scripts/validate_consolidation.py
```

### Option 2: Use Rollback Script

```bash
# Find consolidation audit ID
sqlite3 data/full_intelligence.db "SELECT id, entity_type, consolidated_at FROM consolidation_audit ORDER BY consolidated_at DESC LIMIT 10;"

# Rollback specific consolidation
python scripts/rollback_consolidation.py --audit-id 123 --reason "Incorrect merge"

# Verify rollback
python scripts/validate_consolidation.py
```

---

## Reporting

### Generate Consolidation Dashboard

```bash
# Generate HTML dashboard
python scripts/generate_consolidation_report.py

# Output: reports/consolidation_dashboard_YYYYMMDD_HHMMSS.html
# Open in browser to view metrics, charts, and entity lists
```

### Export Metrics

```bash
# Export metrics to JSON
python scripts/generate_consolidation_report.py --format json

# Output: reports/consolidation_dashboard_YYYYMMDD_HHMMSS.json
```

---

## Production Deployment Checklist

Before promoting consolidation to production:

- [ ] All tests pass (pilot + full)
- [ ] Performance meets targets (<5 minutes)
- [ ] Duplicate reduction achieved (70-95%)
- [ ] Relationships discovered (10+)
- [ ] Patterns identified (4+)
- [ ] No orphaned relationships
- [ ] Average confidence >= 0.75
- [ ] Contradiction rate < 10%
- [ ] Backup strategy in place
- [ ] Rollback procedure tested
- [ ] Monitoring configured
- [ ] Team trained on runbook

---

## Support & Escalation

### Log Files

- **Consolidation logs**: `logs/consolidation.log`
- **Extraction logs**: `logs/extraction.log`
- **Error logs**: `logs/error.log`

### Diagnostic Commands

```bash
# Check system status
python scripts/check_setup.py

# Validate database
python scripts/validate_consolidation.py

# Check recent errors
grep "ERROR" logs/consolidation.log | tail -20

# Check API usage
grep "API call" logs/consolidation.log | wc -l
```

### Escalation Path

1. **Level 1**: Check this runbook for common issues
2. **Level 2**: Review logs and run diagnostic commands
3. **Level 3**: Contact System0 Intelligence Team
4. **Level 4**: Rollback to backup and schedule maintenance window

---

## Appendix: Configuration Reference

### Similarity Thresholds

| Entity Type | Threshold | Rationale |
|-------------|-----------|-----------|
| pain_points | 0.70 | Lower threshold to catch more duplicates |
| processes | 0.75 | Moderate threshold for process names |
| systems | 0.75 | Moderate threshold for system names |
| kpis | 0.85 | Higher threshold for precise KPI names |
| team_structures | 0.90 | Highest threshold for org structure |

### Consensus Parameters

| Parameter | Value | Description |
|-----------|-------|-------------|
| source_count_divisor | 5 | 20% of interviews (9/44) = 1.0 confidence |
| agreement_bonus | 0.05 | Bonus per agreeing attribute |
| max_agreement_bonus | 0.30 | Maximum bonus from agreement |
| contradiction_penalty | 0.25 | Penalty per contradiction |
| single_source_penalty | 0.30 | Penalty for single-source entities |

### Performance Settings

| Setting | Value | Description |
|---------|-------|-------------|
| max_candidates | 10 | Max entities to compare per duplicate check |
| batch_size | 100 | Entities processed per batch |
| fuzzy_first_filtering | true | Use fuzzy matching before semantic similarity |
| skip_semantic_threshold | 0.95 | Skip semantic check if fuzzy score >= 0.95 |

---

**End of Runbook**

For questions or issues not covered here, contact the System0 Intelligence Team.
