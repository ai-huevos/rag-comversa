# Cursor + Claude Workflow: Implementation

**Role:** Primary development environment  
**Timeline:** Weeks 2-6  
**Output:** Production-ready codebase

---

## Setup (Day 1)

### 1. Create New Project Structure
```bash
mkdir system0-v2
cd system0-v2
git init
```

### 2. Configure Cursor
Create `.cursorrules`:
```
# System0 V2 Coding Standards

## Core Principles
1. Spanish-first processing (NEVER translate)
2. UTF-8 with ensure_ascii=False
3. Type hints on all functions
4. Comprehensive docstrings (Args/Returns/Raises)
5. EARS-compliant requirements traceability

## Architecture
- Async/await for I/O operations
- Dependency injection for testability
- Repository pattern for data access
- Factory pattern for extractors
- Observer pattern for monitoring

## Testing
- Pytest for unit tests
- 80%+ code coverage
- Integration tests for pipelines
- Evaluation tests with 30-sample set

## Documentation
- README.md for setup
- API docs with examples
- Runbook for operations
- ADRs for decisions
```

### 3. Initialize Project
```bash
# Create structure
mkdir -p src/{core,extractors,validation,storage,monitoring,api}
mkdir -p tests/{unit,integration,evaluation}
mkdir -p config prompts docs

# Initialize Python
python -m venv venv
source venv/bin/activate
pip install poetry
poetry init
```

---

## Week 2: Core Infrastructure

### Prompt 1: Project Setup
```
Create a production-ready Python project structure for system0 v2:

Requirements:
- Poetry for dependency management
- Pytest for testing
- Black + isort for formatting
- Mypy for type checking
- Pre-commit hooks
- GitHub Actions CI/CD

Generate:
1. pyproject.toml with all dependencies
2. .pre-commit-config.yaml
3. .github/workflows/ci.yml
4. Makefile with common commands
5. README.md with setup instructions

Follow best practices for 2025.
```

### Prompt 2: Configuration System
```
Implement a configuration system with:

1. Environment variables (highest priority)
2. YAML config files (config/*.yaml)
3. Defaults (lowest priority)

Requirements:
- Type-safe (Pydantic models)
- Validation on load
- Hot-reload support
- Secrets management (env vars only)

Files:
- src/core/config.py
- config/extraction.yaml
- config/validation.yaml
- config/monitoring.yaml

Include tests.
```

---

## Week 3: Extraction Pipeline

### Prompt 3: Extractor Factory
```
Implement an extractor factory pattern:

Requirements:
- Support 17 entity types
- Load prompts from prompts/ directory
- Version control (v1, v2, v3)
- Multi-model fallback (6 models)
- Rate limiting (50 calls/min)
- Cost tracking

Files:
- src/extractors/factory.py
- src/extractors/base.py
- src/extractors/pain_point.py (example)
- prompts/pain_point/v1.yaml
- tests/unit/test_extractor_factory.py

Use async/await for API calls.
```

---

## Week 4: Validation & Quality

### Prompt 4: Validation Pipeline
```
Implement validation pipeline:

Requirements:
- Completeness checking (rule-based)
- Quality validation (UTF-8, required fields)
- Consistency checking (entity references)
- Hallucination detection (keyword overlap)
- Configurable thresholds

Files:
- src/validation/pipeline.py
- src/validation/completeness.py
- src/validation/quality.py
- src/validation/consistency.py
- tests/unit/test_validation.py

Return structured validation results.
```

---

## Week 5: Storage & Consolidation

### Prompt 5: Repository Pattern
```
Implement repository pattern for data access:

Requirements:
- Abstract interface (Protocol)
- SQLite implementation (with WAL)
- PostgreSQL implementation (async)
- Neo4j implementation (for graph)
- Transaction support
- Migration system

Files:
- src/storage/repository.py (interface)
- src/storage/sqlite_repo.py
- src/storage/postgres_repo.py
- src/storage/neo4j_repo.py
- migrations/001_initial_schema.sql

Include connection pooling.
```

---

## Week 6: API & Frontend Integration

### Prompt 6: FastAPI Backend
```
Implement FastAPI backend:

Endpoints:
- POST /api/v1/extract (extract from interview)
- GET /api/v1/interviews (list interviews)
- GET /api/v1/interviews/{id} (get interview)
- POST /api/v1/feedback (submit rating)
- GET /api/v1/metrics (monitoring)

Requirements:
- OpenAPI docs
- Authentication (JWT)
- Rate limiting
- CORS for frontend
- WebSocket for progress

Files:
- src/api/main.py
- src/api/routes/extraction.py
- src/api/routes/interviews.py
- src/api/auth.py
- tests/integration/test_api.py
```

---

## Tips for Cursor

1. **Use Cmd+K for inline edits** - Select code, Cmd+K, describe change
2. **Use Cmd+L for chat** - Ask questions about codebase
3. **Use @-mentions** - Reference files (@config.py) or docs (@README.md)
4. **Use Composer** - Multi-file edits (Cmd+I)
5. **Use Terminal** - Run tests, format code, commit

---

## Quality Gates

Before merging each week:
- [ ] All tests pass (pytest)
- [ ] 80%+ coverage (pytest-cov)
- [ ] Type checks pass (mypy)
- [ ] Formatting correct (black, isort)
- [ ] No linting errors (ruff)
- [ ] Documentation updated
