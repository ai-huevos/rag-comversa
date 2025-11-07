# Project Organization Guide

## Why We Organized It This Way

When you're learning infrastructure, a clean folder structure helps you:
1. **Find things fast** - Know where everything lives
2. **Understand what's what** - Code vs data vs docs
3. **Work safely** - Secrets stay separate from code
4. **Scale easily** - Add new features without mess

## The Structure (Explained)

```
comversa-phase1/
│
├── intelligence_capture/     ← THE SYSTEM (your production code)
│   ├── config.py            ← Settings (loads .env)
│   ├── database.py          ← Database operations
│   ├── extractor.py         ← AI extraction logic
│   ├── processor.py         ← Main pipeline
│   ├── run.py               ← Entry point (run this)
│   ├── requirements.txt     ← Python packages needed
│   └── README.md            ← Technical docs
│
├── data/                     ← ALL RAW DATA (inputs)
│   ├── interviews/          ← Interview responses
│   │   └── analysis_output/ ← Processed interviews (JSON)
│   └── company_info/        ← Company documents, CSVs
│
├── reports/                  ← GENERATED OUTPUTS
│   └── analysis/            ← Analysis reports (JSON)
│
├── docs/                     ← DOCUMENTATION (how-to guides)
│   ├── SETUP_INSTRUCTIONS.md
│   ├── INTELLIGENCE_SYSTEM_SUMMARY.md
│   ├── PROJECT_ORGANIZATION.md (this file)
│   └── [other docs]
│
├── scripts/                  ← HELPER SCRIPTS (convenience)
│   ├── run_intelligence.sh  ← Easy way to run system
│   ├── setup.sh             ← Setup helper
│   ├── check_setup.py       ← Verify everything works
│   └── process_interviews.py ← Original processing script
│
├── venv/                     ← PYTHON VIRTUAL ENVIRONMENT
│   └── [isolated packages]  ← Keeps project dependencies separate
│
├── .env                      ← SECRETS (API keys) - NEVER COMMIT
├── .env.example              ← Template for .env
├── .gitignore                ← Tells git what NOT to commit
├── README.md                 ← START HERE (main guide)
└── intelligence.db           ← OUTPUT DATABASE (created when you run)
```

## What Goes Where (Rules)

### 🤖 `intelligence_capture/` - Production Code
**What:** The system that does the work
**Contains:** Python modules, logic, algorithms
**Rule:** Only code that runs the system
**Don't put here:** Data, docs, scripts, configs

### 📊 `data/` - Raw Inputs
**What:** All data that comes IN
**Contains:** Interviews, company info, CSVs
**Rule:** Read-only inputs, never modified by code
**Don't put here:** Generated reports, databases

### 📈 `reports/` - Generated Outputs
**What:** Files created by the system
**Contains:** Analysis reports, exports
**Rule:** Can be deleted and regenerated
**Don't put here:** Raw data, code

### 📚 `docs/` - Documentation
**What:** How-to guides, explanations
**Contains:** Markdown files explaining things
**Rule:** Human-readable guides
**Don't put here:** Code, data, configs

### 🛠️ `scripts/` - Helper Scripts
**What:** Convenience tools
**Contains:** Shell scripts, utility Python scripts
**Rule:** Makes running things easier
**Don't put here:** Core system code

### 🐍 `venv/` - Virtual Environment
**What:** Isolated Python packages
**Contains:** Installed dependencies
**Rule:** Never edit manually, never commit to git
**Don't put here:** Your code

### 🔐 Root Level - Config Files
**What:** Project-wide settings
**Contains:** .env, .gitignore, README.md
**Rule:** Configuration that affects everything
**Don't put here:** Code, data

## How to Navigate

### "Where do I find...?"

**Interview data?**
→ `data/interviews/analysis_output/all_interviews.json`

**The main system?**
→ `intelligence_capture/run.py`

**How to set up?**
→ `docs/SETUP_INSTRUCTIONS.md`

**Helper scripts?**
→ `scripts/`

**Output database?**
→ `intelligence.db` (root level, created when you run)

**My API key?**
→ `.env` (root level, you create this)

### "Where do I add...?"

**New interview data?**
→ `data/interviews/`

**New company documents?**
→ `data/company_info/`

**New feature to the system?**
→ `intelligence_capture/` (new .py file)

**New helper script?**
→ `scripts/`

**New documentation?**
→ `docs/`

## Why Virtual Environment?

**Problem:** Different projects need different package versions
**Solution:** Virtual environment = isolated Python setup

**Benefits:**
- Your project's packages don't conflict with other projects
- Easy to replicate on another machine
- Standard practice in production

**How it works:**
```bash
source venv/bin/activate  # Enter the environment
# Now pip install only affects this project
deactivate                # Exit the environment
```

## Why .env for Secrets?

**Problem:** API keys are sensitive, can't commit to git
**Solution:** .env file (ignored by git)

**Benefits:**
- Secrets stay on your machine
- Easy to change without editing code
- Standard practice in production

**How it works:**
```bash
# .env file (never committed)
OPENAI_API_KEY=sk-real-key-here

# Code loads it
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
```

## Why This Structure is Production-Ready

1. **Separation of Concerns**
   - Code ≠ Data ≠ Docs ≠ Config
   - Each has its place

2. **Security**
   - Secrets in .env (not committed)
   - .gitignore protects sensitive files

3. **Maintainability**
   - Easy to find things
   - Easy to add features
   - Easy for others to understand

4. **Scalability**
   - Add new data sources → `data/`
   - Add new features → `intelligence_capture/`
   - Add new docs → `docs/`

## Common Mistakes (Avoid These)

❌ Putting code in `data/`
❌ Putting data in `intelligence_capture/`
❌ Committing `.env` to git
❌ Editing files in `venv/`
❌ Mixing scripts with core code
❌ Putting docs in root level

✅ Code in `intelligence_capture/`
✅ Data in `data/`
✅ Secrets in `.env` (gitignored)
✅ Docs in `docs/`
✅ Scripts in `scripts/`
✅ Clean root level

## Next Steps

1. **Understand the structure** (you're doing this now)
2. **Run the system** (see README.md)
3. **Query the database** (see SETUP_INSTRUCTIONS.md)
4. **Add new features** (follow the structure)

---

**Remember:** Good organization = easier debugging, faster development, safer production code.
