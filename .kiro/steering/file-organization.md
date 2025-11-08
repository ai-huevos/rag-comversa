---
inclusion: always
---

# File Organization Rules

## CRITICAL: Never Create Files in Project Root

**RULE**: The project root directory should ONLY contain:
- `README.md` - Main project documentation
- `NEXT_STEPS.md` - Deployment/action guide
- `PROJECT_STRUCTURE.md` - Folder organization guide
- `DEPLOYMENT_COMPLETE.md` - Deployment status
- `.env` - Environment variables (never commit)
- `.gitignore` - Git ignore rules

**ALL OTHER FILES MUST GO IN SUBDIRECTORIES**

## Mandatory File Placement Rules

### 1. Documentation Files (*.md)
**Location**: `docs/`
**Examples**:
- `docs/ENSEMBLE_QUICKSTART.md`
- `docs/ENSEMBLE_VALIDATION.md`
- `docs/EXTRACTION_PIPELINE_GUIDE.md`

**Action**: When creating ANY documentation file (except the 6 allowed in root), ALWAYS use:
```python
fsWrite(path="docs/YOUR_DOCUMENT.md", text="...")
```

### 2. Database Files (*.db)
**Location**: `data/`
**Examples**:
- `data/intelligence.db`
- `data/full_intelligence.db`
- `data/pilot_intelligence.db`

**Action**: When creating or referencing databases, ALWAYS use:
```python
DB_PATH = PROJECT_ROOT / "data" / "intelligence.db"
```

### 3. Python Scripts (*.py)
**Location**: `scripts/` (for utilities) or `intelligence_capture/` (for main code)
**Examples**:
- `scripts/validate_structure.py`
- `scripts/generate_report.py`
- `intelligence_capture/processor.py`

**Action**: When creating utility scripts, ALWAYS use:
```python
fsWrite(path="scripts/your_script.py", text="...")
```

### 4. Report Files (*.json, *.xlsx, *.csv)
**Location**: `reports/`
**Examples**:
- `reports/extraction_report.json`
- `reports/quality_analysis.xlsx`

**Action**: When generating reports, ALWAYS use:
```python
output_path = PROJECT_ROOT / "reports" / "report_name.json"
output_path.parent.mkdir(parents=True, exist_ok=True)
```

### 5. Test Files (test_*.py)
**Location**: `tests/`
**Examples**:
- `tests/test_extraction.py`
- `tests/test_database.py`

**Action**: When creating tests, ALWAYS use:
```python
fsWrite(path="tests/test_feature.py", text="...")
```

### 6. Configuration Files (*.json)
**Location**: `config/`
**Examples**:
- `config/companies.json`
- `config/ceo_priorities.json`

**Action**: When creating config files, ALWAYS use:
```python
fsWrite(path="config/settings.json", text="...")
```

### 7. Data Files (*.json, *.csv)
**Location**: `data/`
**Examples**:
- `data/extraction_progress.json`
- `data/interviews/all_interviews.json`

**Action**: When creating data files, ALWAYS use:
```python
fsWrite(path="data/your_data.json", text="...")
```

## Path Configuration Reference

Always import paths from `intelligence_capture/config.py`:

```python
from config import DB_PATH, REPORTS_DIR, PROJECT_ROOT

# Database
db = IntelligenceDB(DB_PATH)  # Automatically uses data/intelligence.db

# Reports
report_path = REPORTS_DIR / "my_report.json"

# Custom paths
data_file = PROJECT_ROOT / "data" / "my_data.json"
doc_file = PROJECT_ROOT / "docs" / "MY_GUIDE.md"
```

## Validation

After creating files, you can validate structure with:
```bash
python3 scripts/validate_structure.py
```

This will check:
- ✓ No databases in root
- ✓ No scripts in root
- ✓ No documentation in root (except allowed files)
- ✓ All files in proper directories

## Examples of CORRECT File Creation

### Creating Documentation
```python
# ✅ CORRECT
fsWrite(path="docs/NEW_FEATURE_GUIDE.md", text="# Guide...")

# ❌ WRONG
fsWrite(path="NEW_FEATURE_GUIDE.md", text="# Guide...")
```

### Creating Reports
```python
# ✅ CORRECT
fsWrite(path="reports/analysis_report.json", text='{"results": [...]}')

# ❌ WRONG
fsWrite(path="analysis_report.json", text='{"results": [...]}')
```

### Creating Scripts
```python
# ✅ CORRECT
fsWrite(path="scripts/process_data.py", text="#!/usr/bin/env python3...")

# ❌ WRONG
fsWrite(path="process_data.py", text="#!/usr/bin/env python3...")
```

### Creating Databases
```python
# ✅ CORRECT
from config import DB_PATH  # Uses data/intelligence.db
db = IntelligenceDB(DB_PATH)

# ❌ WRONG
db = IntelligenceDB("intelligence.db")  # Creates in root!
```

## When User Asks to Create Files

**ALWAYS ask yourself**: "Where should this file go according to PROJECT_STRUCTURE.md?"

1. **Documentation** → `docs/`
2. **Scripts** → `scripts/`
3. **Reports** → `reports/`
4. **Data** → `data/`
5. **Tests** → `tests/`
6. **Config** → `config/`
7. **Main code** → `intelligence_capture/`

**NEVER** create files directly in root unless it's one of the 6 allowed files.

## Enforcement

If you catch yourself about to create a file in root:
1. **STOP**
2. Check `PROJECT_STRUCTURE.md`
3. Use the correct subdirectory
4. Create parent directories if needed: `path.parent.mkdir(parents=True, exist_ok=True)`

## Summary

🚫 **DON'T**: Create files in project root
✅ **DO**: Use proper subdirectories (docs/, scripts/, reports/, data/, etc.)
✅ **DO**: Import paths from config.py
✅ **DO**: Run validate_structure.py to check

**Remember**: A clean root directory = organized project = happy developers!
