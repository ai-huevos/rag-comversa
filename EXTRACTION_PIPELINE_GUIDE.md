# Extraction Pipeline Guide

## Two Pipeline Options

We have two extraction pipelines to choose from based on your needs:

### 🚀 Fast Pipeline (RECOMMENDED)
**File:** `fast_extraction_pipeline.py`

**What it extracts:**
- ✅ Pain Points (with intensity, frequency, cost)
- ✅ Systems (with satisfaction scores)
- ✅ Automation Candidates (with priority matrix)
- ✅ Communication Channels
- ✅ Failure Modes

**Advantages:**
- ~60% faster (15-20 minutes for 44 interviews)
- Captures 80% of the business value
- Focuses on actionable insights
- Lower API costs (~$0.50-0.75)

**Best for:**
- Initial extraction and analysis
- Quick insights and decision-making
- CEO validation and prioritization
- Most business use cases

**Run it:**
```bash
./venv/bin/python fast_extraction_pipeline.py
```

---

### 🔬 Full Pipeline (COMPREHENSIVE)
**File:** `full_extraction_pipeline.py`

**What it extracts:**
- All 5 core entities from Fast Pipeline
- Plus 8 additional entities:
  - Decision Points
  - Data Flows
  - Temporal Patterns
  - Team Structures
  - Knowledge Gaps
  - Success Patterns
  - Budget Constraints
  - External Dependencies

**Advantages:**
- Complete data capture
- Detailed operational intelligence
- Full organizational context
- Maximum research depth

**Disadvantages:**
- ~2.5x slower (40-50 minutes for 44 interviews)
- Higher API costs (~$1.50-2.00)
- More data to review and validate

**Best for:**
- Research and deep analysis
- Complete organizational mapping
- Academic or consulting projects
- When you need every detail

**Run it:**
```bash
./venv/bin/python full_extraction_pipeline.py
```

---

## Recommendation

**Start with the Fast Pipeline!**

1. Run `fast_extraction_pipeline.py` first
2. Generate reports and validate findings
3. Make business decisions based on core insights
4. Only run full pipeline if you need the additional detail

The Fast Pipeline gives you everything you need for:
- Identifying hair-on-fire problems
- Prioritizing automation candidates
- Understanding system pain points
- CEO assumption validation
- Cross-company pattern analysis

---

## After Extraction

Once extraction is complete, generate the comprehensive report:

```bash
./venv/bin/python generate_extraction_report.py
```

This will create:
- Entity statistics
- Quality metrics
- CEO validation results
- Cross-company insights
- Top findings (hair-on-fire problems, quick wins, etc.)

---

## Database Outputs

**Fast Pipeline:** `data/fast_intelligence.db`
**Full Pipeline:** `data/full_intelligence.db`

Both databases have the same schema, just different amounts of data.

---

## Troubleshooting

### Pipeline is slow
- Use Fast Pipeline instead of Full Pipeline
- Check your internet connection (LLM API calls)
- Reduce BATCH_SIZE in the script

### Schema errors
- Delete the database file and re-run
- The schema is auto-created on first run

### API rate limits
- The pipeline has automatic retry logic
- It will wait and retry with fallback models
- Progress is saved every 5 interviews

### Resume from failure
- Just run the script again
- It will resume from the last checkpoint
- Progress is saved in `data/*_extraction_progress.json`

---

## Cost Estimates

**Fast Pipeline (5 extractors):**
- Per interview: ~$0.01-0.02
- 44 interviews: ~$0.50-0.75
- Time: 15-20 minutes

**Full Pipeline (13 extractors):**
- Per interview: ~$0.03-0.05
- 44 interviews: ~$1.50-2.00
- Time: 40-50 minutes

Both are very affordable for the value provided!
