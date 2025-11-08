#!/usr/bin/env python3
"""
Pre-Flight Check for Full Extraction Run

Verifies all systems are ready before processing 44 interviews:
1. Configuration is correct
2. Database is accessible
3. Interview files exist
4. API keys are set
5. Ensemble validation is configured
6. UTF-8 handling is correct
7. Disk space is available
"""
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "intelligence_capture"))

# Load .env file
from dotenv import load_dotenv
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)


def check_environment():
    """Check environment variables"""
    print("\n1️⃣ ENVIRONMENT VARIABLES")
    print("=" * 60)
    
    issues = []
    
    # Check OpenAI API key
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print(f"  ✅ OPENAI_API_KEY: Set ({openai_key[:10]}...)")
    else:
        issues.append("OPENAI_API_KEY not set")
        print("  ❌ OPENAI_API_KEY: Not set")
    
    # Check Anthropic API key (optional)
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        print(f"  ✅ ANTHROPIC_API_KEY: Set ({anthropic_key[:10]}...)")
    else:
        print("  ⚠️  ANTHROPIC_API_KEY: Not set (optional, will use GPT-4o for synthesis)")
    
    # Check ensemble settings
    ensemble_enabled = os.getenv("ENABLE_ENSEMBLE_REVIEW", "false").lower()
    ensemble_mode = os.getenv("ENSEMBLE_MODE", "basic")
    
    print(f"  ℹ️  ENABLE_ENSEMBLE_REVIEW: {ensemble_enabled}")
    print(f"  ℹ️  ENSEMBLE_MODE: {ensemble_mode}")
    
    if ensemble_enabled == "true":
        print("  ✅ Ensemble validation enabled")
    else:
        print("  ⚠️  Ensemble validation disabled")
    
    return issues


def check_files():
    """Check required files exist"""
    print("\n2️⃣ REQUIRED FILES")
    print("=" * 60)
    
    issues = []
    
    # Check interview file
    interview_file = PROJECT_ROOT / "data" / "interviews" / "analysis_output" / "all_interviews.json"
    if interview_file.exists():
        import json
        with open(interview_file, 'r', encoding='utf-8') as f:
            interviews = json.load(f)
        print(f"  ✅ Interview file: {interview_file.name} ({len(interviews)} interviews)")
    else:
        issues.append(f"Interview file not found: {interview_file}")
        print(f"  ❌ Interview file: Not found")
    
    # Check database
    db_file = PROJECT_ROOT / "data" / "full_intelligence.db"
    if db_file.exists():
        size_mb = db_file.stat().st_size / (1024 * 1024)
        print(f"  ✅ Database: {db_file.name} ({size_mb:.1f} MB)")
    else:
        print(f"  ⚠️  Database: Will be created")
    
    # Check config files
    config_files = [
        PROJECT_ROOT / "config" / "companies.json",
        PROJECT_ROOT / "config" / "ceo_priorities.json"
    ]
    
    for config_file in config_files:
        if config_file.exists():
            print(f"  ✅ Config: {config_file.name}")
        else:
            print(f"  ⚠️  Config: {config_file.name} (optional)")
    
    return issues


def check_modules():
    """Check required Python modules"""
    print("\n3️⃣ PYTHON MODULES")
    print("=" * 60)
    
    issues = []
    
    required_modules = [
        ("openai", "OpenAI API client"),
        ("anthropic", "Anthropic API client (optional)"),
        ("sqlite3", "SQLite database"),
        ("json", "JSON handling"),
        ("pathlib", "Path handling")
    ]
    
    for module_name, description in required_modules:
        try:
            __import__(module_name)
            print(f"  ✅ {module_name}: {description}")
        except ImportError:
            if module_name == "anthropic":
                print(f"  ⚠️  {module_name}: {description} - Not installed (optional)")
            else:
                issues.append(f"{module_name} not installed")
                print(f"  ❌ {module_name}: {description} - Not installed")
    
    return issues


def check_code_integrity():
    """Check code files are present"""
    print("\n4️⃣ CODE INTEGRITY")
    print("=" * 60)
    
    issues = []
    
    required_files = [
        "intelligence_capture/config.py",
        "intelligence_capture/database.py",
        "intelligence_capture/extractor.py",
        "intelligence_capture/processor.py",
        "intelligence_capture/reviewer.py",
        "intelligence_capture/run.py"
    ]
    
    for file_path in required_files:
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"  ✅ {file_path}")
        else:
            issues.append(f"Missing file: {file_path}")
            print(f"  ❌ {file_path}")
    
    return issues


def check_utf8_compliance():
    """Check UTF-8 handling"""
    print("\n5️⃣ UTF-8 COMPLIANCE")
    print("=" * 60)
    
    try:
        from database import IntelligenceDB, json_serialize
        print("  ✅ json_serialize() helper available")
        
        # Test UTF-8 handling
        test_data = {"text": "Gestión de Ingeniería"}
        json_str = json_serialize(test_data)
        
        if "\\u" not in json_str and "ó" in json_str and "í" in json_str:
            print("  ✅ UTF-8 serialization working correctly")
            print(f"     Sample: {json_str[:50]}...")
        else:
            print("  ❌ UTF-8 serialization may have issues")
            return ["UTF-8 serialization not working correctly"]
        
        return []
    except Exception as e:
        print(f"  ❌ Error checking UTF-8: {e}")
        return [f"UTF-8 check failed: {e}"]


def check_disk_space():
    """Check available disk space"""
    print("\n6️⃣ DISK SPACE")
    print("=" * 60)
    
    import shutil
    
    data_dir = PROJECT_ROOT / "data"
    stat = shutil.disk_usage(data_dir)
    
    free_gb = stat.free / (1024 ** 3)
    total_gb = stat.total / (1024 ** 3)
    used_gb = stat.used / (1024 ** 3)
    
    print(f"  Total: {total_gb:.1f} GB")
    print(f"  Used: {used_gb:.1f} GB")
    print(f"  Free: {free_gb:.1f} GB")
    
    if free_gb < 1:
        print("  ⚠️  Low disk space (< 1 GB free)")
        return ["Low disk space"]
    else:
        print("  ✅ Sufficient disk space")
        return []


def estimate_cost():
    """Estimate processing cost"""
    print("\n7️⃣ COST ESTIMATE")
    print("=" * 60)
    
    ensemble_enabled = os.getenv("ENABLE_ENSEMBLE_REVIEW", "false").lower() == "true"
    ensemble_mode = os.getenv("ENSEMBLE_MODE", "basic")
    
    num_interviews = 44
    
    if not ensemble_enabled:
        cost_per_interview = 0.03
        mode = "Standard extraction"
    elif ensemble_mode == "basic":
        cost_per_interview = 0.03
        mode = "BASIC ensemble (single-model + review)"
    else:  # full
        cost_per_interview = 0.15
        mode = "FULL ensemble (multi-model + synthesis)"
    
    total_cost = num_interviews * cost_per_interview
    
    print(f"  Mode: {mode}")
    print(f"  Interviews: {num_interviews}")
    print(f"  Cost per interview: ${cost_per_interview:.2f}")
    print(f"  Total estimated cost: ${total_cost:.2f}")
    
    if ensemble_mode == "full":
        print(f"  ⚠️  FULL mode is expensive (~${total_cost:.2f})")
        print(f"  💡 Consider BASIC mode (~$1.32) for testing")
    else:
        print(f"  ✅ Cost is reasonable")
    
    return []


def estimate_time():
    """Estimate processing time"""
    print("\n8️⃣ TIME ESTIMATE")
    print("=" * 60)
    
    ensemble_enabled = os.getenv("ENABLE_ENSEMBLE_REVIEW", "false").lower() == "true"
    ensemble_mode = os.getenv("ENSEMBLE_MODE", "basic")
    
    num_interviews = 44
    
    if not ensemble_enabled:
        time_per_interview = 30  # seconds
        mode = "Standard extraction"
    elif ensemble_mode == "basic":
        time_per_interview = 30  # seconds
        mode = "BASIC ensemble"
    else:  # full
        time_per_interview = 90  # seconds
        mode = "FULL ensemble"
    
    total_seconds = num_interviews * time_per_interview
    total_minutes = total_seconds / 60
    
    print(f"  Mode: {mode}")
    print(f"  Time per interview: ~{time_per_interview}s")
    print(f"  Total estimated time: ~{total_minutes:.0f} minutes")
    
    if total_minutes > 60:
        print(f"  ⚠️  Processing will take over 1 hour")
    else:
        print(f"  ✅ Processing time is reasonable")
    
    return []


def main():
    """Run all pre-flight checks"""
    print("=" * 60)
    print("PRE-FLIGHT CHECK FOR FULL EXTRACTION")
    print("=" * 60)
    print("\nVerifying system readiness before processing 44 interviews...")
    
    all_issues = []
    
    # Run all checks
    all_issues.extend(check_environment())
    all_issues.extend(check_files())
    all_issues.extend(check_modules())
    all_issues.extend(check_code_integrity())
    all_issues.extend(check_utf8_compliance())
    all_issues.extend(check_disk_space())
    all_issues.extend(estimate_cost())
    all_issues.extend(estimate_time())
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    if not all_issues:
        print("\n✅ ALL CHECKS PASSED!")
        print("\nSystem is ready for full extraction.")
        print("\nTo proceed:")
        print("  cd intelligence_capture")
        print("  python3 run.py")
        print("\nOr to test first:")
        print("  python3 run.py --test")
        return 0
    else:
        print(f"\n❌ {len(all_issues)} ISSUES FOUND:")
        for issue in all_issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before proceeding.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
