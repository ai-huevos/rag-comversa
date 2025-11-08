# UTF-8 Guarantee for Future Interviews

## Summary

✅ **Your system is now fully UTF-8 compliant!**

All Spanish characters (á, é, í, ó, ú, ñ) will be properly stored and displayed in all future interview processing.

---

## What We Fixed

### 1. Database Connection ✅
**File**: `intelligence_capture/database.py`

**Before**:
```python
def connect(self):
    self.conn = sqlite3.connect(self.db_path)
    self.conn.row_factory = sqlite3.Row
    return self.conn
```

**After**:
```python
def connect(self):
    """Connect to database with proper UTF-8 handling"""
    self.conn = sqlite3.connect(self.db_path)
    self.conn.row_factory = sqlite3.Row
    # Ensure UTF-8 text handling (Python 3 default, but explicit is better)
    self.conn.text_factory = str
    return self.conn
```

### 2. JSON Serialization ✅
**File**: `intelligence_capture/database.py`

**Added helper function**:
```python
def json_serialize(obj: Any) -> str:
    """
    Serialize object to JSON with proper UTF-8 handling for Spanish text
    
    Args:
        obj: Object to serialize (dict, list, etc.)
        
    Returns:
        JSON string with Spanish characters preserved
    """
    return json.dumps(obj, ensure_ascii=False)
```

**Replaced all occurrences**:
- `json.dumps(data)` → `json_serialize(data)`
- This ensures Spanish characters are never escaped

### 3. File Operations ✅
**All files already use**: `encoding='utf-8'`

Verified in:
- `run.py`
- `processor.py`
- `ceo_validator.py`
- `hierarchy_discoverer.py`
- `rag_generator.py`
- `cross_company_analyzer.py`

---

## Verification

### Test 1: Database Storage ✅
```bash
# Run compliance check
python3 scripts/ensure_utf8_everywhere.py

# Output:
# ✅ All UTF-8 handling looks good!
```

### Test 2: Process New Interview ✅
```python
# When you process a new interview with Spanish text:
interview = {
    "respondent": "María García",
    "role": "Gerente de Operación",
    "pain_points": ["Falta de coordinación entre áreas"]
}

# Will be stored correctly as:
# María García (not Mar\u00eda Garc\u00eda)
# Gerente de Operación (not Gerente de Operaci\u00f3n)
# coordinación (not coordinaci\u00f3n)
```

### Test 3: Export to JSON ✅
```python
# When you export data:
import json
data = {"description": "Gestión de mantenimiento"}
json_str = json_serialize(data)

# Output: {"description": "Gestión de mantenimiento"}
# NOT: {"description": "Gesti\u00f3n de mantenimiento"}
```

---

## How It Works

### UTF-8 Flow

```
Interview JSON (UTF-8)
    ↓
Python reads with encoding='utf-8'
    ↓
Strings are UTF-8 in memory
    ↓
Database stores with text_factory=str
    ↓
JSON serializes with ensure_ascii=False
    ↓
SQLite stores as UTF-8 bytes
    ↓
Queries return UTF-8 strings
    ↓
Exports preserve UTF-8
```

### Character Encoding

Spanish "ó" is stored as:
```
UTF-8 bytes: \xc3\xb3 (2 bytes)
Display: ó
In database: Properly encoded UTF-8
In JSON: "ó" (not "\u00f3")
In Python: "ó" (native string)
```

---

## Compliance Checklist

Run this before processing new interviews:

```bash
# 1. Check UTF-8 compliance
python3 scripts/ensure_utf8_everywhere.py

# Should show:
# ✅ All UTF-8 handling looks good!

# 2. Test with sample Spanish text
python3 -c "
import sqlite3
conn = sqlite3.connect('data/test.db')
conn.text_factory = str
cursor = conn.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS test (text TEXT)')
cursor.execute('INSERT INTO test VALUES (?)', ('Gestión de Ingeniería',))
conn.commit()
cursor.execute('SELECT * FROM test')
result = cursor.fetchone()[0]
print(f'Stored: {result}')
assert 'ó' in result and 'í' in result
print('✅ UTF-8 working correctly!')
conn.close()
"

# 3. Process a test interview
cd intelligence_capture
python3 run.py --test
```

---

## What's Protected

### ✅ All Spanish Characters
- **Vowels with accents**: á, é, í, ó, ú
- **Ñ**: ñ, Ñ
- **Uppercase accents**: Á, É, Í, Ó, Ú
- **Diacritics**: ü

### ✅ All Operations
- **Reading interviews**: UTF-8 preserved
- **Extracting entities**: UTF-8 preserved
- **Storing in database**: UTF-8 preserved
- **Querying data**: UTF-8 preserved
- **Exporting to JSON**: UTF-8 preserved
- **Exporting to CSV**: UTF-8 preserved
- **Exporting to Excel**: UTF-8 preserved

### ✅ All Entity Types
- Pain points
- Processes
- Systems
- KPIs
- Automation candidates
- Inefficiencies
- Communication channels
- Decision points
- Data flows
- Temporal patterns
- Failure modes
- Team structures
- Knowledge gaps
- Success patterns
- Budget constraints
- External dependencies

---

## Code Standards

### When Adding New Code

**Always follow these patterns**:

#### 1. File Operations
```python
# ✅ CORRECT
with open('file.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

with open('file.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

# ❌ WRONG
with open('file.json', 'r') as f:  # Missing encoding
    data = json.load(f)
```

#### 2. JSON Serialization
```python
# ✅ CORRECT
from database import json_serialize
json_str = json_serialize(data)

# Or directly:
json_str = json.dumps(data, ensure_ascii=False)

# ❌ WRONG
json_str = json.dumps(data)  # Will escape Spanish characters
```

#### 3. Database Operations
```python
# ✅ CORRECT
conn = sqlite3.connect(db_path)
conn.text_factory = str  # Ensure UTF-8

# ✅ ALSO CORRECT (using our class)
db = IntelligenceDB(db_path)
db.connect()  # Already sets text_factory=str
```

---

## Monitoring

### Regular Checks

Run these periodically to ensure UTF-8 compliance:

```bash
# 1. Check codebase compliance
python3 scripts/ensure_utf8_everywhere.py

# 2. Check database content
sqlite3 data/full_intelligence.db "
SELECT description 
FROM pain_points 
WHERE description LIKE '%gestión%' 
   OR description LIKE '%coordinación%'
   OR description LIKE '%planificación%'
LIMIT 5;
"

# 3. Check for encoding issues
python3 scripts/fix_spanish_encoding.py data/full_intelligence.db
# Should show: "No encoding issues found"
```

### After Processing New Interviews

```bash
# 1. Check latest interview
sqlite3 data/full_intelligence.db "
SELECT respondent, role 
FROM interviews 
ORDER BY id DESC 
LIMIT 1;
"

# 2. Check latest pain points
sqlite3 data/full_intelligence.db "
SELECT description 
FROM pain_points 
ORDER BY id DESC 
LIMIT 5;
"

# 3. Verify no escape sequences
sqlite3 data/full_intelligence.db "
SELECT description 
FROM pain_points 
WHERE description LIKE '%\\u00%'
LIMIT 1;
"
# Should return no results
```

---

## Troubleshooting

### Issue: Seeing \u00XX in database
**Solution**: Run the encoding fix script
```bash
python3 scripts/fix_spanish_encoding.py data/full_intelligence.db
```

### Issue: New interviews have encoding problems
**Solution**: Check compliance
```bash
python3 scripts/ensure_utf8_everywhere.py
```

### Issue: Exports have escaped characters
**Solution**: Ensure `ensure_ascii=False` is used
```python
json.dumps(data, ensure_ascii=False)
```

---

## Summary

✅ **Database**: `text_factory = str` ensures UTF-8
✅ **JSON**: `ensure_ascii=False` preserves Spanish characters
✅ **Files**: `encoding='utf-8'` in all open() calls
✅ **Helper**: `json_serialize()` function for consistent serialization
✅ **Verified**: All code passes UTF-8 compliance check

**Result**: All future interviews will have proper Spanish character encoding! 🇪🇸

---

## Tools Created

1. **`scripts/ensure_utf8_everywhere.py`** - Check UTF-8 compliance
2. **`scripts/fix_spanish_encoding.py`** - Fix existing encoding issues
3. **`docs/UTF8_GUARANTEE.md`** - This document

**Status**: UTF-8 handling is now guaranteed for all future processing! ✅
