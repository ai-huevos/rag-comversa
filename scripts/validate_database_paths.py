#!/usr/bin/env python3
"""
Database Path Validation Script
Ensures all scripts follow SOLID principles for database path management
"""
import sys
import re
from pathlib import Path
from typing import List, Tuple, Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.config import DB_PATH, PILOT_DB_PATH, FAST_DB_PATH, TEST_DB_PATH


class DatabasePathValidator:
    """Validates database path usage across the codebase"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.issues = []
        self.warnings = []
        self.passed = []
        
    def validate_all(self) -> bool:
        """Run all validation checks"""
        print("=" * 70)
        print("🔍 DATABASE PATH VALIDATION")
        print("=" * 70)
        print(f"Project Root: {self.project_root}\n")
        
        # Check 1: No hardcoded database paths
        print("📋 Check 1: No hardcoded database paths...")
        self.check_hardcoded_paths()
        
        # Check 2: All scripts import from config
        print("\n📋 Check 2: Scripts import from config...")
        self.check_config_imports()
        
        # Check 3: Classes use dependency injection
        print("\n📋 Check 3: Classes use dependency injection...")
        self.check_dependency_injection()
        
        # Check 4: Config has all required paths
        print("\n📋 Check 4: Config has all required paths...")
        self.check_config_completeness()
        
        # Print summary
        self.print_summary()
        
        return len(self.issues) == 0
    
    def check_hardcoded_paths(self):
        """Check for hardcoded database paths"""
        patterns = [
            r'Path\(["\']data/.*\.db["\']',  # Path("data/something.db")
            r'["\']data/.*\.db["\']',  # "data/something.db"
            r'sqlite3\.connect\(["\']',  # sqlite3.connect("...")
        ]
        
        python_files = list(self.project_root.glob("**/*.py"))
        python_files = [f for f in python_files if 'venv' not in str(f) and '.git' not in str(f)]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                for line_num, line in enumerate(lines, 1):
                    # Skip comments and docstrings
                    if line.strip().startswith('#') or '"""' in line or "'''" in line:
                        continue
                    
                    for pattern in patterns:
                        if re.search(pattern, line):
                            # Check if it's in config.py (allowed)
                            if 'config.py' in str(file_path):
                                continue
                            
                            # Check if it's in validate_database_paths.py (allowed - these are regex patterns)
                            if 'validate_database_paths.py' in str(file_path):
                                continue
                            
                            # Check if it's importing from config
                            if 'from intelligence_capture.config import' in line:
                                continue
                            
                            self.issues.append(
                                f"❌ {file_path.relative_to(self.project_root)}:{line_num}\n"
                                f"   Hardcoded path: {line.strip()}"
                            )
            except Exception as e:
                self.warnings.append(f"⚠️  Could not read {file_path}: {e}")
        
        if not self.issues:
            self.passed.append("✅ No hardcoded database paths found")
    
    def check_config_imports(self):
        """Check that scripts import database paths from config"""
        script_dir = self.project_root / "scripts"
        if not script_dir.exists():
            self.warnings.append("⚠️  scripts/ directory not found")
            return
        
        # Skip utility/documentation scripts that don't need database path management
        skip_scripts = [
            '__init__.py',
            'validate_database_paths.py',
            'ensure_utf8_everywhere.py',  # Documentation script
            'fix_spanish_encoding.py',  # One-off utility script
        ]
        
        scripts = list(script_dir.glob("*.py"))
        scripts = [s for s in scripts if s.name not in skip_scripts]
        
        for script in scripts:
            try:
                with open(script, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if script uses database
                uses_db = any(pattern in content for pattern in [
                    'IntelligenceDB(',
                    'EnhancedIntelligenceDB(',
                    'sqlite3.connect'
                ])
                
                if uses_db:
                    # Check if it imports from config
                    imports_config = 'from intelligence_capture.config import' in content
                    
                    if not imports_config:
                        self.issues.append(
                            f"❌ {script.relative_to(self.project_root)}\n"
                            f"   Uses database but doesn't import from config"
                        )
                    else:
                        self.passed.append(f"✅ {script.name} imports from config")
            except Exception as e:
                self.warnings.append(f"⚠️  Could not read {script}: {e}")
    
    def check_dependency_injection(self):
        """Check that classes accept db_path as parameter"""
        module_dir = self.project_root / "intelligence_capture"
        if not module_dir.exists():
            self.warnings.append("⚠️  intelligence_capture/ directory not found")
            return
        
        modules = list(module_dir.glob("*.py"))
        modules = [m for m in modules if m.name not in ['__init__.py', 'config.py']]
        
        for module in modules:
            try:
                with open(module, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Find class definitions
                class_pattern = r'class\s+(\w+).*?def\s+__init__\s*\([^)]*\)'
                matches = re.finditer(class_pattern, content, re.DOTALL)
                
                for match in matches:
                    class_name = match.group(1)
                    init_signature = match.group(0)
                    
                    # Check if class uses database
                    if 'IntelligenceDB' in content or 'db_path' in content.lower():
                        # Check if __init__ accepts db_path parameter
                        if 'db_path' not in init_signature:
                            self.warnings.append(
                                f"⚠️  {module.name}::{class_name}\n"
                                f"   Consider accepting db_path parameter for flexibility"
                            )
                        else:
                            self.passed.append(f"✅ {class_name} uses dependency injection")
            except Exception as e:
                self.warnings.append(f"⚠️  Could not analyze {module}: {e}")
    
    def check_config_completeness(self):
        """Check that config.py has all required database paths"""
        required_paths = {
            'DB_PATH': DB_PATH,
            'PILOT_DB_PATH': PILOT_DB_PATH,
            'FAST_DB_PATH': FAST_DB_PATH,
            'TEST_DB_PATH': TEST_DB_PATH
        }
        
        for name, path in required_paths.items():
            if path is None:
                self.issues.append(f"❌ config.py missing: {name}")
            else:
                self.passed.append(f"✅ config.py defines: {name} = {path}")
    
    def print_summary(self):
        """Print validation summary"""
        print("\n" + "=" * 70)
        print("📊 VALIDATION SUMMARY")
        print("=" * 70)
        
        if self.passed:
            print(f"\n✅ PASSED ({len(self.passed)}):")
            for item in self.passed[:10]:  # Show first 10
                print(f"  {item}")
            if len(self.passed) > 10:
                print(f"  ... and {len(self.passed) - 10} more")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for item in self.warnings:
                print(f"  {item}")
        
        if self.issues:
            print(f"\n❌ ISSUES ({len(self.issues)}):")
            for item in self.issues:
                print(f"  {item}")
        
        print("\n" + "=" * 70)
        if self.issues:
            print("❌ VALIDATION FAILED")
            print(f"   {len(self.issues)} issue(s) must be fixed")
        else:
            print("✅ VALIDATION PASSED")
            print("   All database paths follow SOLID principles")
        print("=" * 70)


def main():
    """Main entry point"""
    project_root = Path(__file__).parent.parent
    validator = DatabasePathValidator(project_root)
    
    success = validator.validate_all()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
