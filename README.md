# Comversa Phase 1 - AI Agent Infrastructure

Production-ready intelligence capture system for Los Tajibos, Comversa, and Bolivian Foods.

## 📁 Project Structure

```
comversa-phase1/
│
├── intelligence_capture/       # 🤖 AI Intelligence System (THE MAIN SYSTEM)
│   ├── config.py              # Configuration
│   ├── database.py            # SQLite schema
│   ├── extractor.py           # GPT-4 extraction
│   ├── processor.py           # Main pipeline
│   └── run.py                 # Entry point
│
├── data/                       # 📊 All raw data
│   ├── interviews/            # Interview responses
│   │   └── analysis_output/   # Processed interviews
│   └── company_info/          # Company documents
│
├── reports/                    # 📈 Generated reports
│   └── analysis/              # Analysis outputs
│
├── docs/                       # 📚 Documentation
│   ├── SETUP_INSTRUCTIONS.md  # How to set up
│   ├── INTELLIGENCE_SYSTEM_SUMMARY.md
│   └── [other docs]
│
├── scripts/                    # 🛠️ Helper scripts
│   ├── run_intelligence.sh    # Run the system
│   ├── setup.sh               # Setup helper
│   └── check_setup.py         # Verify setup
│
├── venv/                       # 🐍 Python virtual environment
├── .env                        # 🔐 Secrets (YOUR API KEYS)
├── .gitignore                  # Git ignore rules
└── intelligence.db             # 💾 Output database
```

## 🚀 Quick Start

### 1. Setup (First Time Only)

```bash
# Add your OpenAI API key
# Edit .env and replace placeholder with your key
nano .env

# Verify setup
python scripts/check_setup.py
```

### 2. Test with One Interview

```bash
./scripts/run_intelligence.sh --test
```

This processes ONE interview and shows you what gets extracted.

### 3. Process All Interviews

```bash
./scripts/run_intelligence.sh
```

This processes all 44 interviews (~5-10 minutes, ~$0.50-$1.00).

### 4. Query the Database

```bash
sqlite3 intelligence.db

# Example queries:
SELECT * FROM pain_points WHERE company='Los Tajibos' AND severity='Critical';
SELECT name, usage_count FROM systems ORDER BY usage_count DESC LIMIT 10;
```

## 📖 Documentation

- **Setup Guide:** `docs/SETUP_INSTRUCTIONS.md`
- **System Overview:** `docs/INTELLIGENCE_SYSTEM_SUMMARY.md`
- **Technical Details:** `intelligence_capture/README.md`

## 🎯 What This Does

**Input:** 44 manager interviews (Spanish text)

**Processing:** GPT-4 extracts structured data:
- Pain points (problems blocking work)
- Processes (how work gets done)
- Systems (tools used)
- KPIs (success metrics)
- Automation opportunities
- Inefficiencies

**Output:** SQLite database with queryable insights, separated by company

## 🏢 Companies Covered

- **Los Tajibos** - Hotel operations
- **Comversa** - Construction & real estate
- **Bolivian Foods** - Restaurant franchises

## 💡 Why This Matters

**Before:** Unstructured interview text
**After:** Queryable database ready for AI agents

You can now:
- Query specific insights by company
- Count automation opportunities
- Identify critical pain points
- Feed structured data to AI agents
- Generate reports

## 🔧 Troubleshooting

Run the setup checker:
```bash
python scripts/check_setup.py
```

Common issues:
- **API key not set:** Edit `.env` with your real OpenAI key
- **Packages not installed:** Run `source venv/bin/activate && pip install -r intelligence_capture/requirements.txt`
- **Permission denied:** Run `chmod +x scripts/*.sh`

## 📊 Database Schema

7 tables with full relationships:
- `interviews` - Raw interview data
- `pain_points` - Problems identified
- `processes` - Business processes
- `systems` - Tools/software
- `kpis` - Success metrics
- `automation_candidates` - Automation opportunities
- `inefficiencies` - Redundant steps

## 🔐 Security

- API keys stored in `.env` (never committed to git)
- `.gitignore` protects secrets
- Virtual environment isolates dependencies

## 📈 Cost & Performance

- **Test (1 interview):** ~10 seconds, ~$0.01
- **Full (44 interviews):** ~5-10 minutes, ~$0.50-$1.00
- **Model:** gpt-4o-mini (fast, cheap, accurate)

## 🎓 Learning Notes

This is production code that:
- ✓ Handles errors with retries
- ✓ Validates inputs
- ✓ Logs progress
- ✓ Prevents duplicates
- ✓ Manages secrets safely
- ✓ Uses virtual environments
- ✓ Follows Python best practices

## 🚦 Status

**Current:** Ready to run
**Next:** Add your API key and test

## 📞 Support

1. Check `docs/SETUP_INSTRUCTIONS.md`
2. Run `python scripts/check_setup.py`
3. Review error messages (they tell you what's wrong)

---

**Built for:** Comversa Phase 1
**Purpose:** Transform interviews into actionable intelligence
**Status:** Production-ready
# rag-comversa
