# Setup Guide - Intelligence Extraction System

## Quick Start

### 1. Install Dependencies

```bash
pip install openai python-dotenv
```

### 2. Configure API Key

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-proj-your-key-here
```

### 3. Run Tests

```bash
# Test with single interview
python scripts/test_single_interview.py

# Test with batch of 5 interviews
python scripts/test_batch_interviews.py

# Validate extraction results
python scripts/validate_extraction.py
```

---

## Detailed Setup

### Prerequisites

- Python 3.8+
- OpenAI API key (required)
- Anthropic API key (optional, for ensemble validation)

### Installation Steps

#### 1. Install Required Python Packages

```bash
# Core dependencies
pip install openai python-dotenv

# Optional: For full functionality
pip install anthropic  # If using ensemble validation
```

#### 2. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and configure your API keys:

```ini
# Required
OPENAI_API_KEY=sk-proj-your-openai-key-here

# Optional (for ensemble validation)
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key-here
ENABLE_ENSEMBLE_REVIEW=false
ENSEMBLE_MODE=basic
```

#### 3. Verify Setup

Check that the configuration is correct:

```bash
python -c "from intelligence_capture.config import OPENAI_API_KEY; print('✓ API key configured' if OPENAI_API_KEY else '✗ No API key')"
```

---

## Running Tests

### Test Scripts Overview

1. **test_single_interview.py** - Test extraction on one interview
2. **test_batch_interviews.py** - Test with multiple interviews
3. **validate_extraction.py** - Validate database contents

### Single Interview Test

```bash
# Test first interview (index 0)
python scripts/test_single_interview.py

# Test specific interview
python scripts/test_single_interview.py --index 5

# Use custom database
python scripts/test_single_interview.py --db data/my_test.db
```

**Expected output:**
- Creates `data/test_single.db`
- Shows entity counts for all 17 types
- Displays sample extracted entities
- Reports quality metrics

### Batch Interview Test

```bash
# Test 5 interviews (default)
python scripts/test_batch_interviews.py

# Test with custom batch size
python scripts/test_batch_interviews.py --batch-size 10

# Test resume capability
python scripts/test_batch_interviews.py --test-resume
```

**Expected output:**
- Creates `data/test_batch.db`
- Shows performance metrics (time, entities/sec)
- Per-interview breakdown
- Estimates time for full extraction

### Validation Script

```bash
# Validate database
python scripts/validate_extraction.py

# Validate specific database
python scripts/validate_extraction.py --db data/test_batch.db

# Export validation report
python scripts/validate_extraction.py --export reports/validation.json
```

**Expected output:**
- Completeness checks (all entity types)
- Quality checks (empty fields, encoding)
- Integrity checks (orphaned records)
- Pass/fail summary

---

## Production Extraction

### Full Extraction (All 44 Interviews)

```bash
# Run full extraction
python intelligence_capture/run.py

# With custom database
python intelligence_capture/run.py --db data/production.db

# Resume interrupted extraction
python intelligence_capture/run.py --resume
```

### Monitor Progress

The extraction system includes real-time monitoring:
- Progress updates every 5 interviews (configurable)
- Entity counts per interview
- Estimated time remaining
- Quality validation results

---

## Configuration

### Extraction Configuration

Edit `config/extraction_config.json` to customize:

```json
{
  "extraction": {
    "model": "gpt-4o-mini",
    "temperature": 0.1,
    "max_retries": 3
  },
  "validation": {
    "enable_validation_agent": true,
    "enable_llm_validation": false
  },
  "monitoring": {
    "enable_monitor": true,
    "print_summary_every_n": 5
  }
}
```

### Performance Tuning

**For faster extraction:**
- Use `gpt-4o-mini` model (default)
- Disable LLM validation: `enable_llm_validation: false`
- Disable ensemble review: `ENABLE_ENSEMBLE_REVIEW=false`

**For higher quality:**
- Enable LLM validation: `enable_llm_validation: true`
- Enable ensemble review: `ENABLE_ENSEMBLE_REVIEW=true`
- Use `ENSEMBLE_MODE=full` for multi-model validation

---

## Troubleshooting

### Common Issues

**ImportError: No module named 'openai'**
```bash
pip install openai python-dotenv
```

**ValueError: OPENAI_API_KEY environment variable not set**
```bash
# Create .env file and add your API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your-key-here
```

**FileNotFoundError: all_interviews.json not found**
```bash
# Verify interviews file exists
ls -la data/interviews/analysis_output/all_interviews.json
```

**Database locked error**
```bash
# Close any open connections to the database
# Delete test database and try again
rm data/test_*.db
```

---

## Next Steps

After successful setup:

1. ✅ Run single interview test
2. ✅ Run batch test (5 interviews)
3. ✅ Review test results
4. 🚀 Run full extraction (44 interviews)
5. ✅ Validate results
6. 📊 Generate reports

---

## Support

For issues or questions:
- Check `scripts/README.md` for detailed script documentation
- Review `.kiro/specs/extraction-completion/tasks.md` for implementation details
- Check configuration in `config/extraction_config.json`

---

## File Structure

```
rag-comversa/
├── .env                          # API keys (create from .env.example)
├── .env.example                  # Environment template
├── config/
│   └── extraction_config.json   # Extraction settings
├── intelligence_capture/
│   ├── processor.py             # Main processor
│   ├── extractor.py             # Entity extraction
│   ├── validation_agent.py      # Validation logic
│   └── monitor.py               # Real-time monitoring
├── scripts/
│   ├── test_single_interview.py # Single interview test
│   ├── test_batch_interviews.py # Batch test
│   ├── validate_extraction.py   # Validation script
│   └── README.md                # Script documentation
└── data/
    ├── test_single.db           # Single test database
    ├── test_batch.db            # Batch test database
    └── full_intelligence.db     # Production database
```
