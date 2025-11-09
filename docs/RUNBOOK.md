# System0 Runbook

**Purpose**: Operational guide for running and maintaining the Intelligence Extraction System
**Last Updated**: 2025-11-09
**Status**: ⚠️ **System has critical bugs, use with caution**

---

## Quick Reference

| Task | Command | Time | Cost |
|------|---------|------|------|
| Setup environment | `cp .env.example .env` + edit | 5 min | Free |
| Test single interview | `python scripts/test_single_interview.py` | 30s | $0.03 |
| Test batch (5 interviews) | `python scripts/test_batch_interviews.py` | 3 min | $0.15 |
| Full extraction (44) | `python intelligence_capture/run.py` | 20 min | $0.50-1.00 |
| Validate results | `python scripts/validate_extraction.py` | 1 min | Free |
| Generate report | `python scripts/generate_comprehensive_report.py` | 1 min | Free |

---

## Prerequisites

### System Requirements
- **Python**: 3.9 or higher
- **OS**: macOS, Linux, or Windows
- **RAM**: 2GB minimum
- **Disk**: 500MB for data and reports

### Dependencies
```bash
pip install openai python-dotenv pandas openpyxl anthropic
```

### API Keys Required
- **OpenAI API key** (required): From [platform.openai.com](https://platform.openai.com/)
- **Anthropic API key** (optional): For Claude fallback

---

## Setup (5 Minutes)

### Step 1: Clone and Navigate
```bash
cd /Users/tatooine/Documents/Development/Comversa/system0
```

### Step 2: Install Dependencies
```bash
pip install openai python-dotenv pandas openpyxl
```

### Step 3: Configure API Keys
```bash
# Copy template
cp .env.example .env

# Edit .env and add your API key
# OPENAI_API_KEY=sk-proj-your-key-here
# ANTHROPIC_API_KEY=sk-ant-your-key-here  # Optional
# ENABLE_ENSEMBLE_REVIEW=false  # Keep disabled
```

### Step 4: Verify Setup
```bash
python -c "from intelligence_capture.config import OPENAI_API_KEY; print('✓ API key configured' if OPENAI_API_KEY else '✗ No API key')"
```

Expected output: `✓ API key configured`

---

## Development Workflow

### Standard Development Cycle
```
1. Make changes to code
2. Run single interview test (30s)
3. Run batch test if changes significant (3 min)
4. Run validation script
5. Update this runbook if process changes
```

### Testing Hierarchy

**Level 1: Single Interview** (always run)
```bash
python scripts/test_single_interview.py
```
- Tests 1 interview
- Verifies all 17 entity types extract
- Quick sanity check
- ~30 seconds, ~$0.03

**Level 2: Batch Test** (run before commits)
```bash
python scripts/test_batch_interviews.py --batch-size 5
```
- Tests 5 interviews
- Tests resume capability
- Performance benchmark
- ~3 minutes, ~$0.15

**Level 3: Full Extraction** (run before release)
```bash
python intelligence_capture/run.py
```
- Tests all 44 interviews
- Production simulation
- Comprehensive validation
- ~20 minutes, ~$0.50-1.00

---

## Common Operations

### 1. Test Single Interview

**Purpose**: Quick sanity check after code changes

**Command**:
```bash
python scripts/test_single_interview.py
```

**Expected Output**:
```
🔍 Testing single interview extraction...

Interview: [Name], [Role]
Company: [Company]

Extracting entities...
  ✓ Pain points: 12
  ✓ Processes: 18
  ✓ Systems: 15
  ✓ KPIs: 3
  ✓ Automation candidates: 8
  ✓ Inefficiencies: 5
  ✓ Communication channels: 9
  ✓ Decision points: 6
  ✓ Data flows: 7
  ✓ Temporal patterns: 11
  ✓ Failure modes: 4
  ✓ Team structures: 2
  ✓ Knowledge gaps: 1
  ✓ Success patterns: 1
  ✓ Budget constraints: 1
  ✓ External dependencies: 2

✅ All 17 entity types extracted successfully

Sample entities:
  Pain point: "Conciliación manual de pagos toma 3 horas diarias"
  System: "Opera PMS - lento, crashes frecuentes"
  Automation: "Automatizar envío de facturas por WhatsApp"

Time: 28s
Cost: $0.03
```

**Troubleshooting**:
- If fails: Check API key in `.env`
- If "No entities": Check interview JSON format
- If timeout: Check internet connection

---

### 2. Test Batch (5 Interviews)

**Purpose**: Test performance and resume capability

**Command**:
```bash
python scripts/test_batch_interviews.py --batch-size 5
```

**Options**:
- `--batch-size N`: Number of interviews to test (default: 5)
- `--db PATH`: Custom database path

**Expected Output**:
```
🔍 Testing batch extraction (5 interviews)...

Processing interview 1/5... ✓ (26s, $0.03)
Processing interview 2/5... ✓ (28s, $0.03)
Processing interview 3/5... ✓ (30s, $0.03)
Processing interview 4/5... ✓ (27s, $0.03)
Processing interview 5/5... ✓ (29s, $0.03)

Results:
  Total time: 140s (2.3 minutes)
  Average time: 28s per interview
  Total cost: $0.15
  Success rate: 100% (5/5)

Entities extracted:
  Pain points: 58
  Processes: 92
  Systems: 74
  (... all 17 types ...)

✅ Batch test successful
```

---

### 3. Full Extraction (44 Interviews)

**Purpose**: Production run to extract all entities

**⚠️ WARNING**: System has critical bugs that may cause failures. See [Known Issues](#known-issues).

**Command**:
```bash
python intelligence_capture/run.py
```

**What happens**:
1. Loads 44 interview JSON files
2. Extracts 17 entity types per interview
3. Stores in `data/intelligence.db`
4. Tracks progress in `data/extraction_progress.json`
5. Prints periodic summaries every 5 interviews

**Expected Output**:
```
🚀 Starting extraction (44 interviews)...

[1/44] Processing interview: [Name]...
  ✓ Extracted 105 entities (28s, $0.03)

[2/44] Processing interview: [Name]...
  ✓ Extracted 98 entities (27s, $0.03)

...

[5/44] Summary:
  Interviews: 5/44 (11%)
  Total entities: 523
  Average time: 27s/interview
  Total cost: $0.15
  ETA: 18 minutes

...

[44/44] Processing interview: [Name]...
  ✓ Extracted 102 entities (29s, $0.03)

✅ Extraction complete!

Final statistics:
  Interviews processed: 44
  Total entities: 4,582
  Total time: 22 minutes
  Total cost: $0.88

Database: data/intelligence.db
Next step: Run validation script
```

**Known Issues**:
- ⚠️ May hit rate limits after 20-30 interviews (no rate limiting implemented)
- ⚠️ Can't use `--parallel` flag (database locking broken)
- ⚠️ No cost limit (could exceed expected cost if interviews longer than average)

---

### 4. Validate Extraction Results

**Purpose**: Verify extraction completeness and quality

**Command**:
```bash
python scripts/validate_extraction.py --db data/intelligence.db
```

**Options**:
- `--db PATH`: Database to validate
- `--export PATH`: Export results to JSON

**Expected Output**:
```
🔍 Validating extraction...

Completeness Check:
  ✓ All 17 entity types have data
  ✓ All 44 interviews processed

Quality Check:
  ✓ No empty descriptions (0 found)
  ✓ No placeholder values (0 found)
  ✓ UTF-8 encoding correct (0 issues)

Consistency Check:
  ✓ All entities link to valid interviews
  ✓ All companies valid (Los Tajibos, Comversa, Bolivian Foods)
  ✓ No orphaned entities

Entity Counts:
  pain_points: 125
  processes: 218
  systems: 186
  kpis: 58
  automation_candidates: 142
  inefficiencies: 98
  communication_channels: 234
  decision_points: 124
  data_flows: 145
  temporal_patterns: 189
  failure_modes: 52
  team_structures: 24
  knowledge_gaps: 8
  success_patterns: 14
  budget_constraints: 9
  external_dependencies: 28

✅ Validation passed: 1,654 entities extracted
```

**Warning Signs**:
- ❌ Entity type with 0 count (extraction failed)
- ⚠️ Entity type with very low count (< 5)
- ❌ UTF-8 encoding issues (Spanish characters broken)
- ❌ Orphaned entities (interview_id not found)

---

### 5. Generate Reports

**Purpose**: Create Excel/JSON reports for analysis

**Command**:
```bash
python scripts/generate_comprehensive_report.py --format both
```

**Options**:
- `--format {json,excel,both}`: Output format (default: both)
- `--db PATH`: Database path
- `--output DIR`: Output directory (default: reports/)

**Output Files**:
```
reports/
├── intelligence_report.json         # JSON export
└── intelligence_report.xlsx         # Excel workbook
    ├── Summary                      # Overall statistics
    ├── Entity Counts                # Counts by type
    ├── Company Breakdown            # Per-company analysis
    ├── Quality Metrics              # Confidence and quality
    ├── Top Pain Points              # Critical issues
    └── Automation Opportunities     # Top automation candidates
```

---

## Resume Interrupted Extraction

**Scenario**: Extraction crashes or is interrupted mid-run.

**How it works**:
- Progress tracked in `data/extraction_progress.json`
- Re-running continues from last completed interview
- Already processed interviews skipped

**Command**:
```bash
python intelligence_capture/run.py --resume
```

**What happens**:
```
🔄 Resuming extraction...

Progress found: 23/44 interviews complete
Skipping 23 completed interviews...

[24/44] Processing interview: [Name]...
  ✓ Extracted 98 entities (27s, $0.03)

...
```

**Manual Resume**:
If `--resume` doesn't work:
```bash
# 1. Check progress file
cat data/extraction_progress.json

# 2. Delete progress file to restart from scratch
rm data/extraction_progress.json

# 3. Re-run extraction
python intelligence_capture/run.py
```

---

## Database Operations

### View Database Contents
```bash
# Open database
sqlite3 data/intelligence.db

# List tables
.tables

# Count entities per type
SELECT 'pain_points' as type, COUNT(*) FROM pain_points
UNION ALL SELECT 'processes', COUNT(*) FROM processes
UNION ALL SELECT 'systems', COUNT(*) FROM systems;

# View specific entities
SELECT * FROM pain_points WHERE severity='Critical' LIMIT 10;

# View company distribution
SELECT company, COUNT(*) FROM pain_points GROUP BY company;

# Exit
.quit
```

### Export Database to CSV
```bash
# Export pain points
sqlite3 data/intelligence.db <<EOF
.headers on
.mode csv
.output pain_points.csv
SELECT * FROM pain_points;
.quit
EOF
```

### Backup Database
```bash
# Create timestamped backup
cp data/intelligence.db data/intelligence_backup_$(date +%Y%m%d_%H%M%S).db

# Verify backup
ls -lh data/intelligence_backup_*.db
```

---

## Configuration

### Main Config: `config/extraction_config.json`

**Current Settings**:
```json
{
  "extraction": {
    "model": "gpt-4o-mini",           # Primary LLM
    "temperature": 0.1,               # Low = deterministic
    "max_retries": 3                  # Retries per model
  },
  "validation": {
    "enable_validation_agent": true,  # Rule-based validation
    "enable_llm_validation": false    # Expensive, keep disabled
  },
  "ensemble": {
    "enable_ensemble_review": false   # KEEP DISABLED
  },
  "monitoring": {
    "enable_monitor": true,           # Real-time progress
    "print_summary_every_n": 5        # Summary frequency
  },
  "performance": {
    "parallel_processing": false      # BROKEN, keep disabled
  }
}
```

**Safe to Change**:
- `model`: Switch to "gpt-4o" for better quality (slower, more expensive)
- `temperature`: Increase to 0.2 for more creative responses
- `print_summary_every_n`: Change summary frequency

**DO NOT Change**:
- `enable_ensemble_review`: false (too complex, too expensive)
- `parallel_processing`: false (broken due to database locking)
- `enable_llm_validation`: false (2x cost for marginal benefit)

---

## Known Issues

### 🚨 Critical Issues (Block Production)

#### 1. No Rate Limiting
**Problem**: System doesn't respect OpenAI rate limits
**Impact**: Will fail after 20-30 interviews
**Workaround**: None - must fix code
**Status**: ❌ Not fixed
**See**: [DECISIONS.md#ADR-009](DECISIONS.md#adr-009-production-bugs-unfixed)

#### 2. Database Locking (Parallel Mode)
**Problem**: Parallel processing broken
**Impact**: Can't use `--parallel` flag
**Workaround**: Use sequential mode (default)
**Status**: ❌ Not fixed

#### 3. No Cost Controls
**Problem**: No maximum cost limit
**Impact**: Could accidentally spend $50+
**Workaround**: Monitor costs manually during extraction
**Status**: ❌ Not fixed

### ⚠️ Important Issues (Degrade Experience)

#### 4. Weak Resume Logic
**Problem**: Can't detect stuck interviews
**Impact**: Manual intervention required
**Workaround**: Check progress file, delete if stuck
**Status**: ❌ Not fixed

#### 5. Validation Doesn't Block
**Problem**: Bad data stored despite warnings
**Impact**: Quality issues not prevented
**Workaround**: Run validation script after extraction
**Status**: ❌ Not fixed

---

## Troubleshooting

### "OpenAI API error: Rate limit exceeded"
**Cause**: Hitting OpenAI rate limits (critical bug #1)
**Solution**:
```bash
# Wait 1 hour for rate limit to reset
# Then resume:
python intelligence_capture/run.py --resume
```

### "Database is locked"
**Cause**: Another process using database, or parallel mode enabled
**Solution**:
```bash
# Check if other process running
ps aux | grep intelligence_capture

# Kill other processes
killall -9 python

# Disable parallel mode in config
# Set parallel_processing: false
```

### "No module named 'openai'"
**Cause**: Dependencies not installed
**Solution**:
```bash
pip install openai python-dotenv pandas openpyxl
```

### "Authentication error: Invalid API key"
**Cause**: API key not configured or invalid
**Solution**:
```bash
# Check .env file exists
ls -la .env

# Verify API key format
cat .env | grep OPENAI_API_KEY

# Should look like: OPENAI_API_KEY=sk-proj-...
```

### "No entities extracted"
**Cause**: Interview JSON format incorrect, or API error
**Solution**:
```bash
# Check interview JSON structure
head -20 data/interviews/analysis_output/all_interviews.json

# Check API key works
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

---

## Maintenance Tasks

### Daily
- ❌ Not applicable (system runs on-demand)

### Weekly
- ❌ Not applicable (no recurring tasks)

### Monthly
- [ ] Review API costs in OpenAI dashboard
- [ ] Check for new interview files
- [ ] Backup database: `cp data/intelligence.db backups/`

### As Needed
- [ ] Update dependencies: `pip install --upgrade openai`
- [ ] Review and update this runbook when process changes
- [ ] Archive old databases: Move to `data/archive/`

---

## Documentation Maintenance Rules

### Before Creating New Documentation
1. **Ask**: "Can this update an existing master doc?"
2. **Ask**: "Is this an experiment or a decision?"
3. **Ask**: "Where will I look for this in 2 weeks?"

### After Each Work Session
1. Update master docs with new learnings
2. Move superseded docs to `docs/archive/YYYY-MM/`
3. Update experiment status in [EXPERIMENTS.md](EXPERIMENTS.md)

### Weekly Documentation Review
1. Consolidate similar documents
2. Archive superseded content
3. Ensure one clear path to each topic
4. Update cross-references

---

## Emergency Procedures

### System Hangs Mid-Extraction
```bash
# 1. Check if process still running
ps aux | grep intelligence_capture

# 2. Kill process
kill -9 <PID>

# 3. Check progress file
cat data/extraction_progress.json

# 4. Resume extraction
python intelligence_capture/run.py --resume
```

### Database Corrupted
```bash
# 1. Check integrity
sqlite3 data/intelligence.db "PRAGMA integrity_check;"

# 2. If corrupted, restore from backup
cp data/intelligence_backup_latest.db data/intelligence.db

# 3. Re-run extraction from progress
python intelligence_capture/run.py --resume
```

### API Key Compromised
```bash
# 1. Revoke old key in OpenAI dashboard
# 2. Generate new API key
# 3. Update .env file
# 4. Verify new key works
python -c "from openai import OpenAI; client = OpenAI(); print('✓ Key works')"
```

---

## Performance Optimization

### Current Performance
- **Sequential**: 20 minutes, $0.50-1.00 for 44 interviews
- **Parallel**: ❌ Broken (database locking)

### Future Optimizations (Not Implemented)
- **Batch API calls**: Reduce latency
- **Caching**: Reuse embeddings
- **Parallel processing fix**: Write queue or database per worker
- **GPT-4o-mini-2024**: Newer, faster model

---

## References

- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Decisions**: [DECISIONS.md](DECISIONS.md)
- **Experiments**: [EXPERIMENTS.md](EXPERIMENTS.md)
- **Bugs**: [DECISIONS.md#ADR-009](DECISIONS.md#adr-009-production-bugs-unfixed)

---

**Document Status**: ✅ Master Operational Runbook
**Supersedes**: SETUP.md, scripts/README.md, operational content scattered across docs
**Last Reviewed**: 2025-11-09
**Next Review**: After critical bugs fixed
