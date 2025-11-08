#!/usr/bin/env python3
"""
Ensure UTF-8 Handling Everywhere

This script verifies and documents UTF-8 handling across the codebase.
It checks:
1. Database connections use proper text handling
2. File operations use encoding='utf-8'
3. JSON operations use ensure_ascii=False
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_utf8_compliance():
    """Check UTF-8 compliance across codebase"""
    
    print("=" * 60)
    print("UTF-8 COMPLIANCE CHECK")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # Check 1: Database connection
    print("\n1️⃣ Checking database.py...")
    db_file = PROJECT_ROOT / "intelligence_capture" / "database.py"
    
    with open(db_file, 'r', encoding='utf-8') as f:
        db_content = f.read()
    
    if 'text_factory = str' in db_content or 'text_factory = lambda x: str(x, "utf-8")' in db_content:
        print("  ✅ Database text_factory configured for UTF-8")
    else:
        warnings.append("database.py: text_factory not explicitly set (Python 3 default is OK)")
        print("  ⚠️  text_factory not explicitly set (using Python 3 default)")
    
    # Check 2: File operations
    print("\n2️⃣ Checking file operations...")
    py_files = list((PROJECT_ROOT / "intelligence_capture").glob("*.py"))
    
    files_with_open = []
    for py_file in py_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'open(' in content:
                files_with_open.append(py_file.name)
                # Check if encoding is specified
                if "encoding='utf-8'" in content or 'encoding="utf-8"' in content:
                    print(f"  ✅ {py_file.name}: Uses encoding='utf-8'")
                else:
                    warnings.append(f"{py_file.name}: Some open() calls may not specify encoding")
                    print(f"  ⚠️  {py_file.name}: Check if all open() calls specify encoding")
    
    # Check 3: JSON operations
    print("\n3️⃣ Checking JSON operations...")
    for py_file in py_files:
        with open(py_file, 'r', encoding='utf-8') as f:
            content = f.read()
            if 'json.dumps(' in content:
                if 'ensure_ascii=False' in content:
                    print(f"  ✅ {py_file.name}: Uses ensure_ascii=False")
                else:
                    warnings.append(f"{py_file.name}: json.dumps() without ensure_ascii=False")
                    print(f"  ⚠️  {py_file.name}: json.dumps() should use ensure_ascii=False")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not issues and not warnings:
        print("✅ All UTF-8 handling looks good!")
        print("\nPython 3 defaults:")
        print("  • Strings are UTF-8 by default")
        print("  • SQLite handles UTF-8 automatically")
        print("  • File operations should specify encoding='utf-8'")
        print("  • JSON should use ensure_ascii=False for Spanish")
        return 0
    
    if warnings:
        print(f"\n⚠️  {len(warnings)} warnings:")
        for warning in warnings:
            print(f"  - {warning}")
    
    if issues:
        print(f"\n❌ {len(issues)} issues:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    
    print("\n💡 Recommendations:")
    print("  1. Always use encoding='utf-8' in open() calls")
    print("  2. Always use ensure_ascii=False in json.dumps()")
    print("  3. Python 3 handles UTF-8 by default, but be explicit")
    
    return 0


def show_best_practices():
    """Show UTF-8 best practices"""
    print("\n" + "=" * 60)
    print("UTF-8 BEST PRACTICES")
    print("=" * 60)
    
    print("""
1. FILE OPERATIONS
   ✅ Good:
      with open('file.json', 'r', encoding='utf-8') as f:
          data = json.load(f)
   
   ❌ Bad:
      with open('file.json', 'r') as f:  # No encoding specified
          data = json.load(f)

2. JSON OPERATIONS
   ✅ Good:
      json.dumps(data, ensure_ascii=False, indent=2)
   
   ❌ Bad:
      json.dumps(data)  # Will escape Spanish characters

3. DATABASE OPERATIONS
   ✅ Good (Python 3):
      conn = sqlite3.connect(db_path)
      # Python 3 handles UTF-8 automatically
   
   ✅ Better (explicit):
      conn = sqlite3.connect(db_path)
      conn.text_factory = str  # Ensure UTF-8 strings

4. STRING LITERALS
   ✅ Good (Python 3):
      text = "Gestión de mantenimiento"
      # Python 3 strings are UTF-8 by default
   
   ✅ Also good:
      text = "Gestión de mantenimiento"
      assert "ó" in text  # Works perfectly

5. API RESPONSES
   ✅ Good:
      return jsonify({"text": "Gestión"})
      # Flask/FastAPI handle UTF-8 automatically
   
   ✅ Also good:
      response = Response(
          json.dumps(data, ensure_ascii=False),
          mimetype='application/json; charset=utf-8'
      )
""")


if __name__ == "__main__":
    result = check_utf8_compliance()
    show_best_practices()
    sys.exit(result)
