"""
Configuration for Intelligence Capture System
"""
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "interviews" / "analysis_output"
DB_PATH = PROJECT_ROOT / "data" / "full_intelligence.db"  # Main production database (44 interviews)
INTERVIEWS_FILE = DATA_DIR / "all_interviews.json"

# Output directories
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)  # Ensure reports directory exists

# Load .env file if it exists
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    load_dotenv(env_file)

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable not set.\n"
        "Create a .env file (copy from .env.example) and add your API key."
    )

MODEL = "gpt-4o-mini"  # Fast and cheap for extraction
TEMPERATURE = 0.1  # Low temperature for consistent extraction

# Extraction settings
MAX_RETRIES = 3
TIMEOUT_SECONDS = 60

# Ensemble Validation Settings (Forensic-Grade Quality Review)
# Set ENABLE_ENSEMBLE_REVIEW=true in .env to enable
# Set ENSEMBLE_MODE=full for multi-model extraction (expensive but highest quality)
# Set ENSEMBLE_MODE=basic for single-model with quality scoring (cheaper, still good)
ENABLE_ENSEMBLE_REVIEW = os.getenv("ENABLE_ENSEMBLE_REVIEW", "false").lower() == "true"
ENSEMBLE_MODE = os.getenv("ENSEMBLE_MODE", "basic")  # "basic" or "full"

# Anthropic API Key (optional - for Claude synthesis agent)
# If not provided, will use GPT-4o for synthesis instead
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", None)

# Companies
COMPANIES = ["Los Tajibos", "Comversa", "Bolivian Foods"]

# Entity types from ontology
ENTITY_TYPES = [
    "pain_points",
    "processes", 
    "systems",
    "kpis",
    "automation_candidates",
    "inefficiencies"
]
