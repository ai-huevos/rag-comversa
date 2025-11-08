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


# Extraction Configuration Loader
def load_extraction_config(config_path: Path = None) -> dict:
    """
    Load extraction configuration from JSON file

    Args:
        config_path: Path to config file (default: PROJECT_ROOT/config/extraction_config.json)

    Returns:
        Dictionary with configuration settings
    """
    import json

    # Default config path
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "extraction_config.json"

    # Default configuration (fallback)
    default_config = {
        "extraction": {
            "model": MODEL,
            "temperature": TEMPERATURE,
            "max_retries": MAX_RETRIES,
            "timeout_seconds": TIMEOUT_SECONDS,
            "max_tokens": 4000
        },
        "validation": {
            "enable_validation_agent": True,
            "enable_llm_validation": False,
            "min_description_length": 20,
            "check_encoding": True,
            "check_placeholders": True
        },
        "ensemble": {
            "enable_ensemble_review": ENABLE_ENSEMBLE_REVIEW,
            "ensemble_mode": ENSEMBLE_MODE,
            "models": {
                "primary": "gpt-4o-mini",
                "secondary": "gpt-4o",
                "synthesis": "claude-3-5-sonnet-20241022"
            }
        },
        "monitoring": {
            "enable_monitor": True,
            "print_summary_every_n": 5,
            "export_metrics": True,
            "metrics_output_dir": "reports/metrics"
        },
        "quality_thresholds": {
            "min_entities_per_interview": 5,
            "max_validation_errors_per_interview": 10,
            "min_completeness_score": 0.7,
            "critical_entity_types": ["pain_points", "processes", "systems"]
        },
        "entity_types": {
            "v1.0": {
                "required": ["pain_points", "processes", "systems"],
                "optional": ["kpis", "automation_candidates", "inefficiencies"]
            },
            "v2.0": {
                "required": ["communication_channels", "decision_points"],
                "optional": [
                    "data_flows", "temporal_patterns", "failure_modes",
                    "team_structures", "knowledge_gaps", "success_patterns",
                    "budget_constraints", "external_dependencies"
                ]
            }
        },
        "database": {
            "batch_size": 100,
            "use_transactions": True,
            "connection_timeout": 30
        },
        "performance": {
            "parallel_processing": False,
            "max_workers": 4,
            "enable_caching": False
        }
    }

    # Try to load from file
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = json.load(f)

            # Merge with defaults (file config takes precedence)
            def deep_merge(base, override):
                """Deep merge two dictionaries"""
                result = base.copy()
                for key, value in override.items():
                    if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                        result[key] = deep_merge(result[key], value)
                    else:
                        result[key] = value
                return result

            config = deep_merge(default_config, file_config)
            print(f"✓ Loaded extraction config from: {config_path}")
            return config

        except Exception as e:
            print(f"⚠️  Failed to load config from {config_path}: {e}")
            print(f"   Using default configuration")
            return default_config
    else:
        print(f"ℹ️  Config file not found: {config_path}")
        print(f"   Using default configuration")
        return default_config


def validate_extraction_config(config: dict) -> bool:
    """
    Validate extraction configuration

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises ValueError if invalid
    """
    required_sections = ["extraction", "validation", "ensemble", "monitoring"]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")

    # Validate extraction settings
    if config["extraction"]["temperature"] < 0 or config["extraction"]["temperature"] > 2:
        raise ValueError("Temperature must be between 0 and 2")

    if config["extraction"]["max_retries"] < 1:
        raise ValueError("max_retries must be at least 1")

    # Validate ensemble mode
    valid_modes = ["basic", "full"]
    if config["ensemble"]["ensemble_mode"] not in valid_modes:
        raise ValueError(f"ensemble_mode must be one of: {valid_modes}")

    return True


# Load default extraction configuration
try:
    EXTRACTION_CONFIG = load_extraction_config()
    validate_extraction_config(EXTRACTION_CONFIG)
except Exception as e:
    print(f"⚠️  Config validation failed: {e}")
    print(f"   Continuing with defaults")
    EXTRACTION_CONFIG = None
