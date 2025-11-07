#!/usr/bin/env python3
"""
Check if Intelligence Capture System is properly set up
"""
import sys
from pathlib import Path

def check_setup():
    """Check all setup requirements"""
    
    print("🔍 Checking Intelligence Capture System setup...\n")
    
    all_good = True
    
    # Check 1: .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print("✓ .env file exists")
        
        # Check if it has a real key
        with open(env_file) as f:
            content = f.read()
            if "sk-your-actual-key-here" in content or "your-openai-api-key-here" in content:
                print("  ⚠️  WARNING: .env file still has placeholder key")
                print("  → Edit .env and add your real OpenAI API key")
                all_good = False
            else:
                print("  ✓ API key appears to be set")
    else:
        print("✗ .env file NOT found")
        print("  → Copy .env.example to .env and add your API key")
        all_good = False
    
    # Check 2: Virtual environment
    venv_dir = Path("venv")
    if venv_dir.exists():
        print("✓ Virtual environment exists")
    else:
        print("✗ Virtual environment NOT found")
        print("  → Run: python3 -m venv venv")
        all_good = False
    
    # Check 3: Packages installed
    try:
        import openai
        print("✓ OpenAI package installed")
    except ImportError:
        print("✗ OpenAI package NOT installed")
        print("  → Run: source venv/bin/activate && pip install -r intelligence_capture/requirements.txt")
        all_good = False
    
    try:
        from dotenv import load_dotenv
        print("✓ python-dotenv package installed")
    except ImportError:
        print("✗ python-dotenv package NOT installed")
        print("  → Run: source venv/bin/activate && pip install -r intelligence_capture/requirements.txt")
        all_good = False
    
    # Check 4: Interview data exists
    interviews_file = Path("data/interviews/analysis_output/all_interviews.json")
    if interviews_file.exists():
        import json
        with open(interviews_file) as f:
            interviews = json.load(f)
        print(f"✓ Interview data found ({len(interviews)} interviews)")
    else:
        print("✗ Interview data NOT found")
        print("  → Expected: data/interviews/analysis_output/all_interviews.json")
        all_good = False
    
    # Check 5: Intelligence capture code exists
    required_files = [
        "intelligence_capture/config.py",
        "intelligence_capture/database.py",
        "intelligence_capture/extractor.py",
        "intelligence_capture/processor.py",
        "intelligence_capture/run.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print("✗ Missing code files:")
        for file in missing_files:
            print(f"  - {file}")
        all_good = False
    else:
        print("✓ All code files present")
    
    # Summary
    print("\n" + "="*60)
    if all_good:
        print("✅ SETUP COMPLETE - Ready to run!")
        print("\nNext steps:")
        print("  1. Make sure your OpenAI API key is in .env")
        print("  2. Run test: ./run_intelligence.sh --test")
        print("  3. If test works, run full: ./run_intelligence.sh")
        return 0
    else:
        print("❌ SETUP INCOMPLETE - Fix issues above")
        print("\nSee SETUP_INSTRUCTIONS.md for help")
        return 1

if __name__ == "__main__":
    sys.exit(check_setup())
