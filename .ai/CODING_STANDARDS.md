---
title: Coding Standards - System0 Intelligence Extraction
version: 1.0.0
last_updated: 2025-11-09
applies_to: [cursor, kiro, claude-code]
tags: [python, sqlite, openai, spanish, standards]
---

# Coding Standards

Unified coding standards for System0 Intelligence Extraction System. These standards apply to all AI coding assistants (Cursor, Kiro, Claude Code) working on this project.

---

## 🎯 Core Principles

### 1. Spanish-First Processing
**Rule**: ALL extracted content MUST remain in Spanish. NEVER translate.

```python
# ✅ CORRECT - Spanish preserved
entity = {
    "description": "Reconciliación manual de facturas causa retrasos",
    "severity": "Critical"
}

# ❌ WRONG - Translation breaks context
entity = {
    "description": "Manual invoice reconciliation causes delays",  # NEVER DO THIS
    "severity": "Critical"
}
```

**Why**: Translation loses business context and cultural nuances critical for AI agent decision-making.

### 2. UTF-8 Encoding Everywhere
**Rule**: Explicitly handle UTF-8 for Spanish characters (á, é, í, ó, ú, ñ, ¿, ¡)

```python
# ✅ CORRECT - Explicit UTF-8 handling
import json

def json_serialize(obj):
    """Serialize with Spanish characters preserved"""
    return json.dumps(obj, ensure_ascii=False)  # Critical: ensure_ascii=False

# Database connections
conn = sqlite3.connect(db_path)
conn.text_factory = str  # Ensure UTF-8 text handling

# File operations
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
```

**Why**: Prevents mojibake (corrupted Spanish text like "retraÃ±o" instead of "retraño").

### 3. Type Hints Always
**Rule**: All functions MUST have type hints for parameters and return values.

```python
# ✅ CORRECT - Type hints everywhere
from typing import Dict, List, Optional
from pathlib import Path

def process_interview(
    interview_id: int,
    config: Dict[str, Any],
    db_path: Optional[Path] = None
) -> Dict[str, List[Dict]]:
    """
    Process interview and extract entities

    Args:
        interview_id: Interview ID to process
        config: Configuration dictionary
        db_path: Optional database path override

    Returns:
        Dict mapping entity types to extracted entities
    """
    pass

# ❌ WRONG - No type hints
def process_interview(interview_id, config, db_path=None):
    pass
```

**Why**: Enables IDE autocomplete, catches type errors early, documents expected types.

### 4. Comprehensive Docstrings
**Rule**: All public functions/classes MUST have docstrings with Args/Returns/Raises sections.

```python
# ✅ CORRECT - Complete docstring
def extract_pain_points(interview: Dict[str, Any], config: Dict) -> List[Dict]:
    """
    Extract pain point entities from interview transcript

    Args:
        interview: Interview dictionary with 'raw_data' field containing Spanish transcript
        config: Extraction configuration with 'model', 'temperature', 'max_retries'

    Returns:
        List of pain point entities, each with:
            - description (Spanish): Pain point description
            - severity: "Critical" | "High" | "Medium" | "Low"
            - affected_roles: List of roles affected
            - frequency: "Daily" | "Weekly" | "Monthly" | "Occasional"

    Raises:
        ValueError: If interview missing required fields
        OpenAIError: If API call fails after max_retries

    Example:
        >>> interview = {"raw_data": "Tenemos problemas con..."}
        >>> pain_points = extract_pain_points(interview, config)
        >>> print(pain_points[0]['description'])
        "Reconciliación manual toma 3 horas diarias"
    """
    pass

# ❌ WRONG - Missing or incomplete docstring
def extract_pain_points(interview, config):
    """Extract pain points"""  # Too vague
    pass
```

**Why**: Enables AI assistants to understand function purpose without reading implementation.

---

## 🗄️ Database Patterns

### 1. WAL Mode for Parallel Processing
**Rule**: Always enable WAL mode and configure timeouts for concurrent access.

```python
# ✅ CORRECT - WAL mode with proper configuration
def connect(self):
    """Connect to database with WAL mode for parallel processing"""
    self.conn = sqlite3.connect(
        self.db_path,
        timeout=30.0,  # Wait up to 30s for locks
        check_same_thread=False  # Allow multi-threading
    )
    self.conn.row_factory = sqlite3.Row  # Return rows as dicts
    self.conn.text_factory = str  # UTF-8 text handling

    # Enable WAL mode for concurrent access
    self.conn.execute("PRAGMA journal_mode=WAL")

    # Set busy timeout (wait 5s if database is locked)
    self.conn.execute("PRAGMA busy_timeout=5000")

    # Enable foreign keys
    self.conn.execute("PRAGMA foreign_keys=ON")

    print("✓ Database connected with WAL mode (parallel-safe)")

    return self.conn

# ❌ WRONG - No WAL mode, will cause locking issues
def connect(self):
    self.conn = sqlite3.connect(self.db_path)
    return self.conn
```

**Why**: WAL mode prevents database locking during parallel processing (ADR-007).

### 2. SQL Injection Prevention
**Rule**: Always use whitelists for dynamic table/column names, parameterized queries for values.

```python
# ✅ CORRECT - Whitelist validation
VALID_ENTITY_TYPES = {
    "pain_points", "processes", "systems", "kpis",
    "automation_candidates", "inefficiencies"
}

def get_entities(entity_type: str) -> List[Dict]:
    """
    Get entities of specified type

    Args:
        entity_type: Entity type (must be in VALID_ENTITY_TYPES)

    Raises:
        ValueError: If entity_type not in whitelist
    """
    # Validate against whitelist (prevents SQL injection)
    if entity_type not in VALID_ENTITY_TYPES:
        raise ValueError(f"Invalid entity type: {entity_type}")

    # Now safe to use in SQL (whitelisted)
    cursor.execute(f"SELECT * FROM {entity_type}")

    return cursor.fetchall()

# ❌ WRONG - SQL injection vulnerability
def get_entities(entity_type):
    # Direct string interpolation - DANGEROUS
    cursor.execute(f"SELECT * FROM {entity_type}")  # Allows: "; DROP TABLE users;--"
```

**Why**: Prevents SQL injection attacks from user-supplied entity types.

### 3. Transaction Management
**Rule**: Use transactions for multi-statement operations, commit explicitly.

```python
# ✅ CORRECT - Explicit transaction management
def store_extraction_results(interview_id: int, entities: Dict[str, List[Dict]]):
    """Store extraction results in transaction"""
    try:
        # Start transaction (implicit after first execute)
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                self.store_entity(entity_type, entity, interview_id)

        # Mark interview as processed
        self.update_extraction_status(interview_id, "completed")

        # Commit all changes together
        self.conn.commit()

    except Exception as e:
        # Rollback on any error
        self.conn.rollback()
        raise

# ❌ WRONG - No transaction, partial data on failure
def store_extraction_results(interview_id, entities):
    for entity_type, entity_list in entities.items():
        for entity in entity_list:
            self.store_entity(entity_type, entity, interview_id)
            # Implicit commit after each insert - not atomic!
```

**Why**: Ensures all-or-nothing semantics - no partial data in database on failure.

---

## 🤖 OpenAI API Patterns

### 1. Multi-Model Fallback Chain
**Rule**: Always implement fallback chain with exponential backoff.

```python
# ✅ CORRECT - Fallback chain with exponential backoff
def _call_gpt4(
    self,
    system_prompt: str,
    user_prompt: str,
    max_retries: int = 3
) -> Dict:
    """
    Call OpenAI API with fallback chain

    Models tried in order:
    1. gpt-4o-mini (primary - fastest, cheapest)
    2. gpt-4o (fallback 1)
    3. gpt-3.5-turbo (fallback 2)
    4. o1-mini (fallback 3)
    5. o1-preview (fallback 4)
    6. claude-3-5-sonnet (fallback 5 - Anthropic)

    Args:
        system_prompt: System instructions
        user_prompt: User query with interview transcript
        max_retries: Retries per model with exponential backoff

    Returns:
        Parsed JSON response from successful model

    Raises:
        Exception: If all models fail after all retries
    """
    models = [
        'gpt-4o-mini',
        'gpt-4o',
        'gpt-3.5-turbo',
        'o1-mini',
        'o1-preview',
        'claude-3-5-sonnet-20241022'
    ]

    for model in models:
        for attempt in range(max_retries):
            try:
                response = self._api_call(model, system_prompt, user_prompt)
                print(f"✓ {model} succeeded on attempt {attempt + 1}")
                return response

            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                print(f"⚠️  {model} failed (attempt {attempt + 1}): {e}")
                print(f"   Retrying in {wait_time}s...")
                time.sleep(wait_time)

        print(f"✗ {model} exhausted all {max_retries} retries")

    raise Exception("All models failed after all retries")

# ❌ WRONG - Single model, no retries
def _call_gpt4(self, system_prompt, user_prompt):
    return openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[...]
    )
```

**Why**: Achieves 99.9% success rate (EXP-003), handles rate limiting gracefully.

### 2. Structured Output Parsing
**Rule**: Always validate and parse JSON responses with error handling.

```python
# ✅ CORRECT - Robust JSON parsing
def parse_extraction_response(response_text: str) -> List[Dict]:
    """
    Parse JSON response from LLM

    Args:
        response_text: Raw text response from API

    Returns:
        Parsed list of entity dictionaries

    Raises:
        ValueError: If JSON parsing fails
    """
    try:
        # Remove markdown code blocks if present
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        # Parse JSON
        data = json.loads(response_text.strip())

        # Validate structure
        if not isinstance(data, list):
            raise ValueError(f"Expected list, got {type(data)}")

        return data

    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON response: {e}\nResponse: {response_text[:500]}")

# ❌ WRONG - No error handling
def parse_extraction_response(response_text):
    return json.loads(response_text)  # Crashes on invalid JSON
```

**Why**: LLMs sometimes return markdown-wrapped JSON or invalid JSON; robust parsing prevents crashes.

---

## ⚙️ Configuration Management

### 1. Configuration Hierarchy
**Rule**: Support environment variables > config file > defaults, in that order.

```python
# ✅ CORRECT - Configuration hierarchy
import os
from pathlib import Path
from typing import Dict, Any

def load_extraction_config() -> Dict[str, Any]:
    """
    Load extraction configuration with hierarchy:
    1. Environment variables (highest priority)
    2. config/extraction_config.json
    3. Hardcoded defaults (lowest priority)

    Returns:
        Configuration dictionary
    """
    # Defaults
    config = {
        "extraction": {
            "model": "gpt-4o-mini",
            "temperature": 0.1,
            "max_retries": 3
        },
        "validation": {
            "enable_validation_agent": True,
            "enable_llm_validation": False
        },
        "ensemble": {
            "enable_ensemble_review": False
        }
    }

    # Load from file if exists
    config_path = Path("config/extraction_config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            file_config = json.load(f)
            # Merge file config (overrides defaults)
            config = {**config, **file_config}

    # Environment variables override all
    if os.getenv("ENABLE_ENSEMBLE_REVIEW"):
        config["ensemble"]["enable_ensemble_review"] = (
            os.getenv("ENABLE_ENSEMBLE_REVIEW").lower() == "true"
        )

    return config

# ❌ WRONG - Hardcoded values
def load_config():
    return {
        "model": "gpt-4o-mini",  # Can't override
        "temperature": 0.1
    }
```

**Why**: Allows deployment-specific overrides without changing code.

### 2. Feature Flags
**Rule**: Use feature flags for experimental features, read from config.

```python
# ✅ CORRECT - Feature flags with config
class IntelligenceProcessor:
    def __init__(
        self,
        db_path: Path = DB_PATH,
        enable_ensemble: bool = None,  # None = read from config
        config: dict = None
    ):
        # Load configuration
        if config is None:
            config = load_extraction_config()

        self.config = config

        # Read ensemble flag from config if not specified
        if enable_ensemble is None:
            enable_ensemble = config.get("ensemble", {}).get("enable_ensemble_review", False)

        self.enable_ensemble = enable_ensemble

        # Initialize ensemble only if enabled
        if self.enable_ensemble:
            self.reviewer = EnsembleReviewer()
            print("✨ Ensemble validation enabled")
        else:
            self.reviewer = None
            print("ℹ️  Ensemble validation disabled")

# ❌ WRONG - Hardcoded feature flag
class IntelligenceProcessor:
    def __init__(self):
        self.enable_ensemble = True  # Always on, can't disable
```

**Why**: Allows enabling/disabling features without code changes (e.g., disable ensemble to reduce cost).

---

## 📊 Error Handling & Logging

### 1. Contextual Error Messages
**Rule**: Error messages MUST include context (entity_type, interview_id, operation).

```python
# ✅ CORRECT - Contextual error messages
def store_entity(
    entity_type: str,
    entity: Dict,
    interview_id: int
):
    """Store entity with contextual error handling"""
    try:
        # Validate entity type
        if entity_type not in VALID_ENTITY_TYPES:
            raise ValueError(
                f"Invalid entity_type '{entity_type}' for interview {interview_id}. "
                f"Valid types: {', '.join(VALID_ENTITY_TYPES)}"
            )

        # Validate required fields
        required_fields = ["description", "company", "department"]
        missing = [f for f in required_fields if f not in entity]
        if missing:
            raise ValueError(
                f"Missing required fields for {entity_type} in interview {interview_id}: "
                f"{', '.join(missing)}"
            )

        # Store entity
        cursor.execute(f"INSERT INTO {entity_type} (...) VALUES (...)", entity)

    except sqlite3.IntegrityError as e:
        raise ValueError(
            f"Database constraint violation storing {entity_type} for interview {interview_id}: {e}"
        )
    except Exception as e:
        raise Exception(
            f"Failed to store {entity_type} for interview {interview_id}: {e}"
        )

# ❌ WRONG - Vague error messages
def store_entity(entity_type, entity, interview_id):
    cursor.execute(f"INSERT INTO {entity_type} (...) VALUES (...)", entity)
    # Error: "UNIQUE constraint failed" - which entity? which interview?
```

**Why**: Makes debugging possible - you know exactly which interview/entity failed and why.

### 2. Progress Indicators
**Rule**: Print progress indicators for long-running operations.

```python
# ✅ CORRECT - Progress indicators
def process_interviews(
    interviews: List[Dict],
    enable_monitor: bool = True
):
    """Process interviews with progress tracking"""
    total = len(interviews)

    # Initialize monitor if enabled
    if enable_monitor:
        monitor = ExtractionMonitor(total_interviews=total)

    for i, interview in enumerate(interviews, 1):
        print(f"\n{'='*60}")
        print(f"Processing interview {i}/{total}: {interview['respondent']}")
        print(f"{'='*60}")

        try:
            # Extract entities
            entities = self.extractor.extract_all(interview)

            # Store entities
            self.db.store_extraction_results(interview['id'], entities)

            # Update monitor
            if enable_monitor:
                monitor.record_success(interview['id'], len(entities))

            print(f"✓ Interview {i}/{total} complete: {len(entities)} entities extracted")

        except Exception as e:
            print(f"✗ Interview {i}/{total} failed: {e}")

            # Update monitor with error
            if enable_monitor:
                monitor.record_error(interview['id'], str(e))

    # Final summary
    print(f"\n{'='*60}")
    print(f"EXTRACTION COMPLETE")
    print(f"{'='*60}")
    print(f"✓ Successful: {success_count}/{total}")
    print(f"✗ Failed: {fail_count}/{total}")

# ❌ WRONG - Silent processing
def process_interviews(interviews):
    for interview in interviews:
        entities = self.extractor.extract_all(interview)
        self.db.store_extraction_results(interview['id'], entities)
    # No idea what's happening or if it's working
```

**Why**: User knows progress, can estimate time remaining, can stop if errors detected.

---

## 🧪 Testing Patterns

### 1. Test Hierarchy
**Rule**: Always test in this order: single → batch → full.

```bash
# ✅ CORRECT - Test hierarchy
# 1. Single interview test (~30s, $0.03)
python scripts/test_single_interview.py

# 2. Batch test - 5 interviews (~3 min, $0.15)
python scripts/test_batch_interviews.py --batch-size 5

# 3. Full extraction - 44 interviews (~20 min, $0.50-1.00)
# ONLY run if single and batch tests pass
python intelligence_capture/run.py

# ❌ WRONG - Jump directly to full extraction
python intelligence_capture/run.py  # May fail, waste $1.00
```

**Why**: Fails fast, cheaper, easier to debug.

### 2. Cost Estimation Before Execution
**Rule**: Always estimate cost before expensive operations, require confirmation.

```python
# ✅ CORRECT - Cost estimation with confirmation
def run_extraction(interviews: List[Dict], confirm: bool = True):
    """
    Run extraction with cost estimation

    Args:
        interviews: List of interviews to process
        confirm: If True, require user confirmation before proceeding
    """
    # Estimate cost
    estimated_cost = estimate_extraction_cost(
        num_interviews=len(interviews),
        avg_entities_per_interview=50,
        model="gpt-4o-mini"
    )

    print(f"\n📊 EXTRACTION ESTIMATE")
    print(f"   Interviews: {len(interviews)}")
    print(f"   Estimated time: {len(interviews) * 30} seconds")
    print(f"   Estimated cost: ${estimated_cost:.2f}")

    if confirm:
        response = input("\nProceed with extraction? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Extraction cancelled by user")
            return

    # Proceed with extraction
    print("\n🚀 Starting extraction...")
    process_interviews(interviews)

# ❌ WRONG - No cost estimate
def run_extraction(interviews):
    process_interviews(interviews)  # Surprise $5 bill
```

**Why**: Prevents accidental expensive operations (critical for ADR-003 cost controls bug).

---

## 📁 File Organization

### 1. Project Structure
**Rule**: Follow this directory structure consistently.

```
system0/
├── intelligence_capture/      # Main Python package
│   ├── __init__.py
│   ├── processor.py           # Pipeline orchestrator
│   ├── extractor.py           # Main extraction (v1.0)
│   ├── extractors.py          # v2.0 specialized extractors
│   ├── database.py            # SQLite schema and operations
│   ├── validation_agent.py    # Quality validation
│   ├── monitor.py             # Real-time progress tracking
│   ├── rate_limiter.py        # Shared rate limiter
│   └── config.py              # Configuration management
├── config/
│   ├── extraction_config.json # All extraction settings
│   └── companies.json         # Organizational hierarchy
├── data/
│   ├── intelligence.db        # Production database
│   └── interviews/            # Source data
├── scripts/
│   ├── test_single_interview.py    # Single interview test
│   ├── test_batch_interviews.py    # Batch testing
│   └── validate_extraction.py      # Validation
├── tests/                     # Unit tests
│   └── test_*.py
├── docs/                      # Documentation
│   ├── README.md              # Master index
│   ├── ARCHITECTURE.md        # System architecture
│   ├── DECISIONS.md           # Architecture Decision Records
│   ├── RUNBOOK.md             # Operations guide
│   └── EXPERIMENTS.md         # Experiment log
└── .ai/                       # AI assistant configuration
    └── CODING_STANDARDS.md    # This file
```

### 2. Import Conventions
**Rule**: Use relative imports within package, absolute for external.

```python
# ✅ CORRECT - Relative imports within package
# In intelligence_capture/processor.py
from .database import IntelligenceDB
from .extractor import IntelligenceExtractor
from .validation_agent import ValidationAgent
from .config import DB_PATH, INTERVIEWS_FILE

# Absolute imports for external packages
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

# ❌ WRONG - Absolute imports for package modules
from intelligence_capture.database import IntelligenceDB  # Breaks if package renamed
```

**Why**: Relative imports are refactor-safe, absolute imports are clear for external dependencies.

---

## 🌐 Spanish Language Patterns

### 1. Entity Field Naming
**Rule**: Use English for field names, Spanish for field values.

```python
# ✅ CORRECT - English field names, Spanish values
entity = {
    "description": "La reconciliación manual de facturas toma 3 horas diarias",
    "severity": "Critical",
    "affected_roles": ["Contador", "Jefe de Finanzas"],
    "company": "Los Tajibos",
    "department": "Finanzas"
}

# ❌ WRONG - Spanish field names (breaks code)
entity = {
    "descripción": "La reconciliación...",  # ❌ Invalid Python key
    "severidad": "Critical"
}

# ❌ WRONG - Translated values (loses context)
entity = {
    "description": "Manual invoice reconciliation takes 3 hours daily",  # ❌ Translated
    "severity": "Critical"
}
```

**Why**: English field names work in Python; Spanish values preserve business context.

### 2. Organizational Hierarchy Terms
**Rule**: Use official Spanish names for companies, business units, departments.

```python
# ✅ CORRECT - Official Spanish names
COMPANIES = {
    "Los Tajibos": {
        "business_units": {
            "Hotel": {
                "departments": ["Recepción", "Housekeeping", "Cocina", "Mantenimiento"]
            }
        }
    },
    "Comversa": {
        "business_units": {
            "Construcción": {
                "departments": ["Obras", "Compras", "Logística"]
            }
        }
    }
}

# ❌ WRONG - Translated names (breaks validation)
COMPANIES = {
    "The Tajibos": {  # ❌ Wrong
        "business_units": {
            "Hotel": {
                "departments": ["Reception", "Housekeeping"]  # ❌ Wrong
            }
        }
    }
}
```

**Why**: Validation checks against official names; translation causes mismatches.

---

## 🚨 Critical Anti-Patterns

### Things to NEVER Do

#### 1. ❌ Never Disable Tests to Make Things Work
```python
# ❌ WRONG - Commenting out failing test
# def test_parallel_processing():
#     # FIXME: Test fails, disabled for now
#     pass

# ✅ CORRECT - Fix the underlying issue
def test_parallel_processing():
    # Enable WAL mode to fix parallel processing
    db.execute("PRAGMA journal_mode=WAL")
    # Now test passes
    assert parallel_process(interviews) == expected_results
```

**Why**: Disabled tests hide bugs; fix the bug instead (from RULES.md).

#### 2. ❌ Never Build Features Before Fixing Bugs
```python
# ❌ WRONG - ADR-009 antipattern
# Phase 1: Build extraction system
# Phase 2: Discover bugs (rate limiting, database locking)
# Phase 3: Skip bug fixes, build ensemble validation instead
# Phase 4: Discover system unusable for production

# ✅ CORRECT - Fix bugs before new features
# Phase 1: Build extraction system
# Phase 2: Discover bugs
# Phase 3: FIX THE BUGS (rate limiting, database locking)
# Phase 4: Then build new features (ensemble, knowledge graph)
```

**Why**: Technical debt compounds; foundation must be solid (from ADR-009).

#### 3. ❌ Never Skip Cost Controls
```python
# ❌ WRONG - No cost protection
def extract_all_interviews():
    for interview in load_interviews():
        extract(interview)  # Could cost $50 by accident

# ✅ CORRECT - Cost estimation with confirmation
def extract_all_interviews(confirm=True):
    cost = estimate_cost(load_interviews())
    print(f"Estimated cost: ${cost:.2f}")

    if confirm and cost > 1.00:
        if input("Proceed? [y/N]: ").lower() != 'y':
            return

    for interview in load_interviews():
        extract(interview)
```

**Why**: Prevents accidental expensive operations (from RUNBOOK.md Critical Bugs).

---

## ✅ Code Review Checklist

Before committing code, verify:

### Type Safety
- [ ] All functions have type hints
- [ ] All parameters have types specified
- [ ] Return types are documented

### Documentation
- [ ] All public functions have docstrings
- [ ] Docstrings include Args/Returns/Raises
- [ ] Complex logic has inline comments

### Error Handling
- [ ] All exceptions are caught and logged
- [ ] Error messages include context (interview_id, entity_type, operation)
- [ ] Database operations use transactions

### Spanish Processing
- [ ] No translation of Spanish content
- [ ] UTF-8 encoding explicitly specified
- [ ] `ensure_ascii=False` in JSON serialization

### Database Operations
- [ ] WAL mode enabled for connections
- [ ] SQL injection prevention (whitelists for dynamic names)
- [ ] Parameterized queries for values
- [ ] Foreign keys enabled

### API Calls
- [ ] Multi-model fallback chain implemented
- [ ] Exponential backoff for retries
- [ ] Cost estimation before expensive operations
- [ ] JSON response parsing with error handling

### Testing
- [ ] Single interview test passes
- [ ] Batch test passes (if applicable)
- [ ] Cost estimate shown before full extraction

---

## 🔧 Tool-Specific Configuration

### Cursor IDE (.cursorrules or .cursor/rules/)
Copy this file to `.cursorrules` or `.cursor/rules/coding-standards.mdc` for Cursor IDE support.

### Kiro Specs (.kiro/)
This file integrates with Kiro's spec-driven development. Reference in spec files:
```yaml
coding_standards: .ai/CODING_STANDARDS.md
```

### Claude Code (CLAUDE.md)
This file is automatically read by Claude Code via `.ai/` directory scanning.

---

## 📚 References

- **ARCHITECTURE.md**: System architecture and component details
- **DECISIONS.md**: Architecture Decision Records explaining WHY
- **RUNBOOK.md**: Operations guide with troubleshooting
- **EXPERIMENTS.md**: Experiment results and patterns
- **RULES.md**: Claude Code behavioral rules

---

**Version**: 1.0.0
**Last Updated**: November 9, 2025
**Applies To**: All AI coding assistants (Cursor, Kiro, Claude Code)
**Next Review**: After fixing 5 critical bugs
