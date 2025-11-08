#!/usr/bin/env python3
"""
Validate Project Structure

Checks that files are in the correct directories according to PROJECT_STRUCTURE.md
"""
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

def check_structure():
    """Validate project structure"""
    print("🔍 VALIDATING PROJECT STRUCTURE")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # Check required directories exist
    required_dirs = [
        "data",
        "docs",
        "reports",
        "scripts",
        "tests",
        "intelligence_capture",
        "config",
        ".kiro/specs/ontology-enhancement"
    ]
    
    print("\n📁 Checking required directories...")
    for dir_path in required_dirs:
        full_path = PROJECT_ROOT / dir_path
        if full_path.exists():
            print(f"  ✓ {dir_path}")
        else:
            issues.append(f"Missing directory: {dir_path}")
            print(f"  ✗ {dir_path} - MISSING")
    
    # Check for files in wrong locations (root directory)
    print("\n📄 Checking for misplaced files in root...")
    root_files = list(PROJECT_ROOT.glob("*.py"))
    root_files += list(PROJECT_ROOT.glob("*.db"))
    root_files += [f for f in PROJECT_ROOT.glob("*.json") if f.name not in [".gitignore"]]
    
    # Allowed files in root
    allowed_root_files = {
        "README.md",
        "NEXT_STEPS.md",
        "PROJECT_STRUCTURE.md",
        ".gitignore",
        ".env"
    }
    
    for file in root_files:
        if file.name not in allowed_root_files:
            warnings.append(f"File in root should be moved: {file.name}")
            print(f"  ⚠️  {file.name} - Should be in scripts/ or data/")
    
    # Check database locations
    print("\n💾 Checking database locations...")
    db_files = list(PROJECT_ROOT.glob("*.db"))
    for db_file in db_files:
        issues.append(f"Database in root: {db_file.name} - Should be in data/")
        print(f"  ✗ {db_file.name} - Should be in data/")
    
    data_dbs = list((PROJECT_ROOT / "data").glob("*.db"))
    for db_file in data_dbs:
        print(f"  ✓ data/{db_file.name}")
    
    # Check documentation locations
    print("\n📚 Checking documentation locations...")
    root_docs = [f for f in PROJECT_ROOT.glob("*.md") if f.name not in allowed_root_files]
    for doc in root_docs:
        warnings.append(f"Documentation in root: {doc.name} - Should be in docs/")
        print(f"  ⚠️  {doc.name} - Should be in docs/")
    
    docs_count = len(list((PROJECT_ROOT / "docs").glob("*.md")))
    print(f"  ✓ {docs_count} files in docs/")
    
    # Check scripts locations
    print("\n🔧 Checking scripts locations...")
    root_scripts = list(PROJECT_ROOT.glob("*.py"))
    for script in root_scripts:
        if script.name not in ["setup.py"]:  # setup.py is allowed in root
            warnings.append(f"Script in root: {script.name} - Should be in scripts/")
            print(f"  ⚠️  {script.name} - Should be in scripts/")
    
    scripts_count = len(list((PROJECT_ROOT / "scripts").glob("*.py")))
    print(f"  ✓ {scripts_count} files in scripts/")
    
    # Check reports directory
    print("\n📊 Checking reports directory...")
    reports_dir = PROJECT_ROOT / "reports"
    if reports_dir.exists():
        reports_count = len(list(reports_dir.glob("*.json")))
        print(f"  ✓ {reports_count} report files in reports/")
    else:
        print(f"  ℹ️  reports/ directory will be created when needed")
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    if not issues and not warnings:
        print("✅ Project structure is perfect!")
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
    
    print("\n💡 Run the following to fix warnings:")
    print("   See PROJECT_STRUCTURE.md for proper organization")
    
    return 0


if __name__ == "__main__":
    sys.exit(check_structure())
