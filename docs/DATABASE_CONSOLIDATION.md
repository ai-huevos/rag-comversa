# Database Consolidation Guide

## Current Situation

You have **3 databases** that were created at different stages:

### 1. `data/full_intelligence.db` (1.0 MB) ⭐ **MAIN DATABASE**
- **Created**: During full extraction pipeline
- **Contains**: All 44 interviews fully processed
- **Entities**: 115 pain points + all other entity types
- **Status**: ✅ Review fields added, ✅ Encoding fixed (705 rows)
- **Use**: This is your production database

### 2. `data/intelligence.db` (100 KB)
- **Created**: By `run.py` during testing
- **Contains**: 1 interview (test data)
- **Status**: ✅ Review fields added, ✅ Encoding fixed (52 rows)
- **Use**: Test/development database

### 3. `data/pilot_intelligence.db` (252 KB)
- **Created**: During pilot extraction (5 interviews)
- **Contains**: 5 interviews
- **Status**: ✅ Encoding fixed (50 rows), ⚠️ No review fields
- **Use**: Historical/pilot data

## Why Multiple Databases?

This happened because:
1. **Pilot phase**: Created `pilot_intelligence.db` to test with 5 interviews
2. **Full extraction**: Created `full_intelligence.db` with all 44 interviews
3. **Testing**: `run.py` creates `intelligence.db` by default

## Recommendation: Use ONE Database

**Use `data/full_intelligence.db` as your single source of truth**

### Why?
- ✅ Contains all 44 interviews
- ✅ Has all entity types extracted
- ✅ Review fields already added
- ✅ Spanish encoding fixed
- ✅ Most complete dataset

## Configuration Update

Update `intelligence_capture/config.py` to always use the full database:

```python
# Before
DB_PATH = PROJECT_ROOT / "data" / "intelligence.db"

# After
DB_PATH = PROJECT_ROOT / "data" / "full_intelligence.db"
```

## What to Do with Other Databases

### Option A: Keep for Reference (Recommended)
- Keep `pilot_intelligence.db` as historical record
- Keep `intelligence.db` for quick tests
- Always use `full_intelligence.db` for production

### Option B: Delete Extras
```bash
# Backup first
cp data/intelligence.db data/backups/intelligence_test.db
cp data/pilot_intelligence.db data/backups/pilot_historical.db

# Then delete
rm data/intelligence.db
rm data/pilot_intelligence.db
```

## Spanish Encoding Fix

All three databases have been fixed! ✅

**Fixed**: 807 total rows across all databases
- `full_intelligence.db`: 705 rows
- `intelligence.db`: 52 rows  
- `pilot_intelligence.db`: 50 rows

**What was fixed**:
- "Ingeniería" (was "Ingenier\u00eda")
- "gestión" (was "gesti\u00f3n")
- "planificación" (was "planificaci\u00f3n")
- "coordinación" (was "coordinaci\u00f3n")
- And all other Spanish accents (á, é, í, ó, ú, ñ)

## Verification

Check that Spanish characters display correctly:

```bash
# Check full database
sqlite3 data/full_intelligence.db "SELECT respondent, role FROM interviews LIMIT 5;"

# Should show:
# Ferrufino Hurtado Javier|Gerente de Ingeniería
# (not: Gerente de Ingenier\u00eda)
```

## Going Forward

### For Production Use
```bash
# Always use full database
cd intelligence_capture
python3 run.py  # Will use full_intelligence.db after config update
```

### For Testing
```bash
# Use test database
cd intelligence_capture
python3 run.py --test  # Quick test with 1 interview
```

### For New Extractions
All new extractions will go to `full_intelligence.db` and will:
- ✅ Have proper Spanish encoding (UTF-8)
- ✅ Have review fields for quality tracking
- ✅ Be stored in the main production database

## Summary

| Database | Size | Interviews | Status | Use |
|----------|------|------------|--------|-----|
| `full_intelligence.db` | 1.0 MB | 44 | ✅ Production | **Main database** |
| `intelligence.db` | 100 KB | 1 | ✅ Test | Testing only |
| `pilot_intelligence.db` | 252 KB | 5 | ✅ Historical | Reference only |

**Action**: Update config to use `full_intelligence.db` as default.
