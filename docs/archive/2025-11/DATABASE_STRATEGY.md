# Database Strategy

## Overview

This document defines the database management strategy for the Intelligence Capture System, ensuring SOLID principles and maintainability.

## Database Files

### Production Databases

#### 1. Full Intelligence Database
- **Path**: `data/full_intelligence.db`
- **Config Constant**: `DB_PATH`
- **Purpose**: Main production database with all 44 interviews
- **Entities**: All v1.0 and v2.0 entities (17 types)
- **Use Cases**:
  - Production analytics
  - Cross-company analysis
  - CEO validation
  - RAG system queries
  - Consolidation system (future)

#### 2. Pilot Intelligence Database
- **Path**: `data/pilot_intelligence.db`
- **Config Constant**: `PILOT_DB_PATH`
- **Purpose**: Testing database with 5-10 interviews
- **Use Cases**:
  - Extractor validation
  - Quick testing
  - Development iterations
  - Quality checks before full extraction

#### 3. Fast Intelligence Database
- **Path**: `data/fast_intelligence.db`
- **Config Constant**: `FAST_DB_PATH`
- **Purpose**: Fast extraction with core entities only
- **Entities**: Pain Points, Systems, Automation Candidates, Communication Channels, Failure Modes
- **Use Cases**:
  - Quick insights (60% faster)
  - MVP demonstrations
  - Core entity analysis

### Test Databases

#### 4. Test Intelligence Database
- **Path**: `data/test_intelligence.db`
- **Config Constant**: `TEST_DB_PATH`
- **Purpose**: Unit and integration tests
- **Lifecycle**: Created and destroyed automatically by tests
- **Use Cases**:
  - pytest fixtures
  - Integration tests
  - CI/CD pipelines

## SOLID Principles Applied

### 1. Single Responsibility Principle (SRP)
- **Database connection logic** lives ONLY in `intelligence_capture/database.py`
- **Path configuration** lives ONLY in `intelligence_capture/config.py`
- **Scripts** focus on orchestration, not database management

### 2. Open/Closed Principle (OCP)
- Scripts can work with ANY database via dependency injection
- No need to modify scripts to use different databases
- Extensible for future database types (PostgreSQL, etc.)

### 3. Liskov Substitution Principle (LSP)
- All database instances follow the same interface
- `IntelligenceDB` and `EnhancedIntelligenceDB` are interchangeable
- Scripts work with any database that implements the interface

### 4. Interface Segregation Principle (ISP)
- Clean separation between database operations and business logic
- Scripts don't depend on database internals
- Database classes expose only necessary methods

### 5. Dependency Inversion Principle (DIP)
- Scripts depend on abstractions (config constants), not concrete paths
- High-level modules (scripts) don't depend on low-level modules (file paths)
- Both depend on abstractions (config interface)

## Usage Guidelines

### For Script Authors

#### ✅ DO: Import from config
```python
from intelligence_capture.config import DB_PATH, PILOT_DB_PATH

db = EnhancedIntelligenceDB(DB_PATH)
```

#### ✅ DO: Accept CLI arguments
```python
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--db-path', type=Path, default=DB_PATH)
args = parser.parse_args()

db = EnhancedIntelligenceDB(args.db_path)
```

#### ✅ DO: Use dependency injection
```python
class MyProcessor:
    def __init__(self, db_path: Path = DB_PATH):
        self.db = EnhancedIntelligenceDB(db_path)
```

#### ❌ DON'T: Hardcode paths
```python
# BAD - hardcoded path
db = EnhancedIntelligenceDB(Path("data/intelligence.db"))

# BAD - hardcoded string
db_path = "data/full_intelligence.db"
```

#### ❌ DON'T: Use sqlite3.connect directly
```python
# BAD - bypasses database abstraction
import sqlite3
conn = sqlite3.connect("data/intelligence.db")

# GOOD - use database class
from intelligence_capture.database import EnhancedIntelligenceDB
db = EnhancedIntelligenceDB(DB_PATH)
db.connect()
```

### For Class Authors

#### ✅ DO: Accept db_path parameter
```python
class MyExtractor:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.db = None
    
    def connect(self):
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
```

#### ✅ DO: Use context managers
```python
class MyAnalyzer:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
    
    def analyze(self):
        db = EnhancedIntelligenceDB(self.db_path)
        db.connect()
        try:
            # Do work
            results = db.query_something()
            return results
        finally:
            db.close()
```

## Configuration Management

### Adding New Database Types

1. Add constant to `intelligence_capture/config.py`:
```python
NEW_DB_PATH = PROJECT_ROOT / "data" / "new_intelligence.db"
```

2. Document purpose in this file

3. Update validation script if needed

### Changing Database Locations

1. Update ONLY `intelligence_capture/config.py`
2. All scripts automatically use new location
3. No need to modify individual scripts

## Validation

### Automated Checks

Run the validation script to ensure compliance:

```bash
python3 scripts/validate_database_paths.py
```

This checks:
- ✅ No hardcoded database paths
- ✅ All scripts import from config
- ✅ Classes use dependency injection
- ✅ Config has all required paths

### Manual Review Checklist

Before committing code that touches databases:

- [ ] Imported paths from `intelligence_capture.config`
- [ ] No hardcoded `Path("data/...")` strings
- [ ] Classes accept `db_path` parameter
- [ ] CLI arguments support `--db-path` flag
- [ ] No direct `sqlite3.connect()` calls
- [ ] Validation script passes

## Migration Strategy

### For Consolidation System

When implementing the consolidation system:

1. **Use existing databases** - Don't create new ones
2. **Add consolidation columns** to existing tables
3. **Use DB_PATH** for production consolidation
4. **Use PILOT_DB_PATH** for testing consolidation
5. **Accept db_path parameter** in all consolidation classes

Example:
```python
class KnowledgeConsolidationAgent:
    def __init__(self, db_path: Path = DB_PATH, config: Dict = None):
        self.db = EnhancedIntelligenceDB(db_path)
        self.config = config or load_consolidation_config()
```

### For Future Enhancements

When adding new features:

1. **Reuse existing databases** when possible
2. **Add new constants** to config.py if needed
3. **Follow dependency injection** pattern
4. **Update this document** with new database purposes
5. **Run validation script** before committing

## Troubleshooting

### Issue: Script can't find database

**Solution**: Check that you're importing from config:
```python
from intelligence_capture.config import DB_PATH
```

### Issue: Database locked error

**Solution**: Ensure WAL mode is enabled (already done in `database.py`):
```python
self.conn.execute("PRAGMA journal_mode=WAL")
```

### Issue: Wrong database being used

**Solution**: Check CLI arguments or default values:
```bash
python3 scripts/my_script.py --db-path data/pilot_intelligence.db
```

### Issue: Validation script fails

**Solution**: Fix reported issues:
1. Remove hardcoded paths
2. Import from config
3. Add dependency injection
4. Re-run validation

## Best Practices Summary

1. **Single Source of Truth**: All paths in `config.py`
2. **Dependency Injection**: Classes accept `db_path` parameter
3. **CLI Flexibility**: Scripts accept `--db-path` argument
4. **No Hardcoding**: Never use `Path("data/...")` outside config
5. **Use Abstractions**: Always use `IntelligenceDB` classes, not `sqlite3` directly
6. **Validate Often**: Run `validate_database_paths.py` before commits
7. **Document Changes**: Update this file when adding new databases

## References

- **Config File**: `intelligence_capture/config.py`
- **Database Classes**: `intelligence_capture/database.py`
- **Validation Script**: `scripts/validate_database_paths.py`
- **Project Structure**: `PROJECT_STRUCTURE.md`

---

**Last Updated**: 2024-11-09
**Maintained By**: Development Team
**Related Specs**: Knowledge Graph Consolidation (`.kiro/specs/knowledge-graph-consolidation/`)
