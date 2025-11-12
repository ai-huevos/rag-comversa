"""
Configuration for Intelligence Capture System
"""
import logging
import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
logger = logging.getLogger(__name__)
DATA_DIR = PROJECT_ROOT / "data" / "interviews" / "analysis_output"
INTERVIEWS_FILE = DATA_DIR / "all_interviews.json"

# Database Paths - Single Source of Truth
# Use these constants instead of hardcoding paths in scripts
DB_PATH = PROJECT_ROOT / "data" / "full_intelligence.db"  # Main production database (44 interviews)
PILOT_DB_PATH = PROJECT_ROOT / "data" / "pilot_intelligence.db"  # Testing database (5-10 interviews)
FAST_DB_PATH = PROJECT_ROOT / "data" / "fast_intelligence.db"  # Fast extraction (core entities only)
TEST_DB_PATH = PROJECT_ROOT / "data" / "test_intelligence.db"  # Unit tests (temporary, auto-cleaned)

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
        "model_routing": {
            "round_robin": [
                "gpt-4o-mini",
                "gpt-4o-mini",
                "gpt-4o"
            ],
            "fallback": [
                "gpt-4o-mini",
                "gpt-4o",
                "o1-mini"
            ],
            "providers": {
                "gpt-4o-mini": {"provider": "openai"},
                "gpt-4o": {"provider": "openai"},
                "o1-mini": {"provider": "openai"},
                "gemini-1.5-pro": {"provider": "gemini"},
                "deepseek-chat": {"provider": "deepseek"},
                "k2-large": {"provider": "k2"}
            }
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
    logger.error("Config validation failed", exc_info=True)
    print(f"⚠️  Error validando configuración: {e}")
    print("   Continuando con valores predeterminados")
    EXTRACTION_CONFIG = None

MODEL_ROUTING_CONFIG = (EXTRACTION_CONFIG or {}).get("model_routing", {})
ROUND_ROBIN_CHAIN = MODEL_ROUTING_CONFIG.get("round_robin", ["gpt-4o-mini"])
FALLBACK_CHAIN = MODEL_ROUTING_CONFIG.get("fallback", ROUND_ROBIN_CHAIN)
MODEL_PROVIDER_MAP = MODEL_ROUTING_CONFIG.get("providers", {})

# Consolidation Configuration Loader
def load_consolidation_config(config_path: Path = None) -> dict:
    """
    Load consolidation configuration from JSON file

    Args:
        config_path: Path to config file (default: PROJECT_ROOT/config/consolidation_config.json)

    Returns:
        Dictionary with consolidation configuration settings
    """
    import json

    # Default config path
    if config_path is None:
        config_path = PROJECT_ROOT / "config" / "consolidation_config.json"

    # Default configuration (fallback)
    default_config = {
        "similarity_thresholds": {
            "pain_points": 0.80,
            "processes": 0.85,
            "systems": 0.85,
            "kpis": 0.90,
            "automation_candidates": 0.85,
            "inefficiencies": 0.80,
            "communication_channels": 0.85,
            "decision_points": 0.85,
            "data_flows": 0.85,
            "temporal_patterns": 0.80,
            "failure_modes": 0.80,
            "team_structures": 0.85,
            "knowledge_gaps": 0.80,
            "success_patterns": 0.80,
            "budget_constraints": 0.85,
            "external_dependencies": 0.85,
            "default": 0.85
        },
        "similarity_weights": {
            "semantic_weight": 0.3,
            "name_weight": 0.7
        },
        "consensus_parameters": {
            "source_count_divisor": 10,
            "agreement_bonus": 0.1,
            "max_bonus": 0.3,
            "contradiction_penalty": 0.15
        },
        "pattern_thresholds": {
            "recurring_pain_threshold": 3,
            "problematic_system_threshold": 5,
            "high_priority_frequency": 0.30
        },
        "performance": {
            "max_candidates": 10,
            "batch_size": 100,
            "enable_caching": True
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
            print(f"✓ Loaded consolidation config from: {config_path}")
            return config

        except Exception as e:
            print(f"⚠️  Failed to load consolidation config from {config_path}: {e}")
            print(f"   Using default configuration")
            return default_config
    else:
        print(f"ℹ️  Consolidation config file not found: {config_path}")
        print(f"   Using default configuration")
        return default_config


def validate_consolidation_config(config: dict) -> bool:
    """
    Validate consolidation configuration

    Args:
        config: Configuration dictionary

    Returns:
        True if valid, raises ValueError if invalid
    """
    required_sections = [
        "similarity_thresholds",
        "similarity_weights",
        "consensus_parameters",
        "pattern_thresholds",
        "performance"
    ]

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required config section: {section}")

    # Validate similarity thresholds (0.0-1.0)
    for entity_type, threshold in config["similarity_thresholds"].items():
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"Similarity threshold for {entity_type} must be between 0.0 and 1.0")

    # Validate weights sum to 1.0
    weights = config["similarity_weights"]
    weight_sum = weights.get("semantic_weight", 0) + weights.get("name_weight", 0)
    if not 0.99 <= weight_sum <= 1.01:  # Allow small floating point errors
        raise ValueError(f"Similarity weights must sum to 1.0 (got {weight_sum})")

    # Validate consensus parameters
    consensus = config["consensus_parameters"]
    if consensus.get("source_count_divisor", 10) <= 0:
        raise ValueError("source_count_divisor must be positive")

    return True
