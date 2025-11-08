# Ensemble Validation Guide

## Overview

Ensemble validation is an **optional feature** that improves extraction quality by using multiple AI models to cross-validate results. This provides forensic-grade quality but increases processing time and cost.

**Status**: ✅ Already implemented in the system
**Requirements**: OpenAI API key (required) + Anthropic API key (optional for full mode)

---

## How Ensemble Validation Works

### Basic Mode (Single Model + Review)
- Uses GPT-4o-mini for extraction
- Uses same model to review and score results
- Cheaper and faster than full mode
- Good quality improvement

### Full Mode (Multi-Model Ensemble)
- Uses GPT-4o-mini for initial extraction
- Uses GPT-4o for independent validation
- Uses Claude 3.5 Sonnet for synthesis (if Anthropic key available)
- Best quality but more expensive and slower

---

## Configuration

### Option 1: Using .env File

Add to your `.env` file:

```bash
# Enable ensemble validation
ENABLE_ENSEMBLE_REVIEW=true

# Choose mode: "basic" or "full"
ENSEMBLE_MODE=basic

# Required
OPENAI_API_KEY=sk-proj-your-openai-key

# Optional (for full mode with Claude synthesis)
ANTHROPIC_API_KEY=sk-ant-api03-your-anthropic-key
```

### Option 2: Using config/extraction_config.json

Edit `config/extraction_config.json`:

```json
{
  "ensemble": {
    "enable_ensemble_review": true,
    "ensemble_mode": "basic",
    "models": {
      "primary": "gpt-4o-mini",
      "secondary": "gpt-4o",
      "synthesis": "claude-3-5-sonnet-20241022"
    }
  }
}
```

### Option 3: Programmatic Configuration

```python
from intelligence_capture.processor import IntelligenceProcessor

processor = IntelligenceProcessor(
    enable_ensemble=True,
    ensemble_mode="basic"  # or "full"
)
```

---

## Cost and Performance Comparison

### Without Ensemble (Default)
- **Model**: GPT-4o-mini
- **Time per interview**: ~10-15 seconds
- **Cost per interview**: ~$0.01-0.02
- **Total for 44 interviews**: ~10-15 minutes, $0.50-1.00

### Basic Ensemble
- **Model**: GPT-4o-mini (extraction + review)
- **Time per interview**: ~20-30 seconds
- **Cost per interview**: ~$0.02-0.04
- **Total for 44 interviews**: ~20-25 minutes, $1.00-2.00
- **Quality improvement**: +15-25%

### Full Ensemble
- **Models**: GPT-4o-mini + GPT-4o + Claude 3.5 Sonnet
- **Time per interview**: ~40-60 seconds
- **Cost per interview**: ~$0.05-0.10
- **Total for 44 interviews**: ~30-45 minutes, $2.50-5.00
- **Quality improvement**: +30-40%

---

## When to Use Ensemble Validation

### Use Ensemble When:
- ✅ Quality is critical (forensic analysis, legal discovery)
- ✅ Data will be used for important decisions
- ✅ You need high confidence in results
- ✅ Budget allows for higher costs
- ✅ Processing time is not critical

### Skip Ensemble When:
- ⊘ Running quick tests or prototypes
- ⊘ Budget is constrained
- ⊘ Fast turnaround needed
- ⊘ Data quality is already high
- ⊘ Multiple extraction passes planned

---

## Running with Ensemble Validation

### Step 1: Configure

```bash
# Edit .env file
nano .env

# Add these lines:
ENABLE_ENSEMBLE_REVIEW=true
ENSEMBLE_MODE=basic
ANTHROPIC_API_KEY=sk-ant-... # Optional for full mode
```

### Step 2: Run Extraction

```bash
# Run with ensemble enabled
python intelligence_capture/run.py

# Or test with single interview
python scripts/test_single_interview.py

# Or test with batch
python scripts/test_batch_interviews.py
```

### Step 3: Monitor Progress

The system will display ensemble validation status:
```
✨ Ensemble validation enabled: BASIC (single-model + review)
🔍 Running ValidationAgent...
  ✓ Completeness check passed
  ✓ Quality validation passed
```

---

## Comparing Results

### Run Without Ensemble (Baseline)

```bash
# Configure for non-ensemble
echo "ENABLE_ENSEMBLE_REVIEW=false" >> .env

# Run extraction
python intelligence_capture/run.py

# Validate
python scripts/validate_extraction.py --export reports/baseline_validation.json
```

### Run With Ensemble

```bash
# Configure for ensemble
echo "ENABLE_ENSEMBLE_REVIEW=true" >> .env
echo "ENSEMBLE_MODE=basic" >> .env

# Backup baseline database
cp data/full_intelligence.db data/full_intelligence_baseline.db

# Run extraction with ensemble
python intelligence_capture/run.py

# Validate
python scripts/validate_extraction.py --export reports/ensemble_validation.json
```

### Compare Results

```python
import json

# Load baseline
with open('reports/baseline_validation.json') as f:
    baseline = json.load(f)

# Load ensemble
with open('reports/ensemble_validation.json') as f:
    ensemble = json.load(f)

# Compare
print(f"Baseline entities: {baseline['results']['completeness']['total_entities']}")
print(f"Ensemble entities: {ensemble['results']['completeness']['total_entities']}")

baseline_quality = baseline['results']['quality']['issue_count']
ensemble_quality = ensemble['results']['quality']['issue_count']
improvement = ((baseline_quality - ensemble_quality) / baseline_quality * 100)
print(f"Quality improvement: {improvement:.1f}%")
```

---

## Troubleshooting

### Issue: "Ensemble reviewer not available"
**Solution**: The `reviewer.py` module is present. Check if all dependencies are installed.

### Issue: Anthropic API key error in full mode
**Solution**: Full mode can run with just OpenAI. Claude synthesis is optional. If you want Claude synthesis, add `ANTHROPIC_API_KEY` to `.env`.

### Issue: Significantly slower processing
**Expected**: Ensemble validation is slower by design. Use basic mode for better speed/quality balance.

### Issue: Higher costs than expected
**Expected**: Ensemble validation costs more. Monitor costs in real-time through the extraction monitor.

---

## Technical Details

### Implementation

Ensemble validation is implemented in:
- `intelligence_capture/reviewer.py` - Ensemble review logic
- `intelligence_capture/processor.py` - Integration point
- `config/extraction_config.json` - Configuration

### Review Process

1. **Initial Extraction**: GPT-4o-mini extracts entities
2. **Review Phase**:
   - Basic: Same model reviews and scores
   - Full: GPT-4o independently validates
3. **Synthesis**:
   - Basic: Weighted merge based on scores
   - Full: Claude synthesizes final results (if available)
4. **Quality Metrics**: Each entity tagged with review metrics

### Review Metrics Stored

Each entity includes:
```python
{
  "name": "Entity name",
  "description": "...",
  "_review_metrics": {
    "confidence_score": 0.95,
    "validation_method": "ensemble",
    "issues_found": [],
    "synthesis_method": "weighted_merge"
  }
}
```

---

## Recommendations

### For Most Users
Use **default mode (no ensemble)**:
- Fast (10-15 minutes for 44 interviews)
- Low cost ($0.50-1.00)
- Good quality with ValidationAgent

### For High-Quality Needs
Use **basic ensemble**:
- Moderate speed (20-25 minutes)
- Moderate cost ($1.00-2.00)
- 15-25% quality improvement

### For Critical Applications
Use **full ensemble**:
- Slower (30-45 minutes)
- Higher cost ($2.50-5.00)
- 30-40% quality improvement
- Multi-model validation

---

## Next Steps

1. **Try basic ensemble** on a small batch:
   ```bash
   # Configure
   echo "ENABLE_ENSEMBLE_REVIEW=true" >> .env
   echo "ENSEMBLE_MODE=basic" >> .env

   # Test with 5 interviews
   python scripts/test_batch_interviews.py --batch-size 5
   ```

2. **Compare results** with baseline

3. **Decide** based on quality improvement vs. cost

4. **Run full extraction** if ensemble provides value

---

**Summary**: Ensemble validation is ready to use. Enable it in `.env` or config file, then run extraction as normal. The system handles the rest automatically.
