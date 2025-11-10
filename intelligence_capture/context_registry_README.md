# Context Registry Module

Multi-organization namespace isolation and Bolivian privacy compliance for RAG 2.0 system.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements-rag2.txt

# Set database URL
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"

# Run migration
psql $DATABASE_URL < scripts/migrations/2025_01_00_context_registry.sql

# Sync organizations from companies.json
python scripts/context_registry_sync.py

# Verify
python scripts/context_registry_sync.py --list
```

## Usage Examples

### Basic Lookup

```python
from intelligence_capture.context_registry import get_registry

# Get registry instance
registry = get_registry()
await registry.connect()

# Lookup by org_id
context = await registry.lookup_by_org_id(
    org_id="los_tajibos",
    business_unit="Hospitality",
    department="Recepción"
)

print(f"Namespace: {context.namespace}")
# Output: los_tajibos:Hospitality:Recepción
```

### Validate Consent

```python
# Check if operation is allowed
is_valid, error_msg = await registry.validate_consent(
    org_id="los_tajibos",
    operation="ingestion"
)

if not is_valid:
    # Error message is in Spanish for Bolivian users
    print(error_msg)
```

### Log Access (Required for Compliance)

```python
# Log every access for audit trail
await registry.log_access(
    org_id="comversa",
    access_type="retrieval",
    business_context="Construction:Proyectos",
    query_params={"query": "¿Qué sistemas causan dolor?"},
    result_count=5,
    latency_ms=250
)
```

### Helper Function (Recommended)

```python
from intelligence_capture.context_registry import validate_and_log_access

# Combined consent validation + access logging
is_valid, error_msg = await validate_and_log_access(
    org_id="bolivian_foods",
    access_type="query",
    operation="retrieval",
    business_context="Manufacturing:Producción",
    query_params={"query": "optimización de producción"}
)

if not is_valid:
    raise PermissionError(error_msg)
```

## Integration Patterns

### DocumentProcessor Integration

```python
from intelligence_capture.context_registry import validate_and_log_access

async def process_document(doc_path: str, org_id: str, business_unit: str):
    # 1. Validate consent before processing
    is_valid, error = await validate_and_log_access(
        org_id=org_id,
        access_type="ingestion",
        operation="ingestion",
        business_context=f"{business_unit}"
    )

    if not is_valid:
        return {"error": error, "status": "forbidden"}

    # 2. Process document
    result = await process_doc(doc_path)

    # 3. Attach org_id to database record
    await db.insert_document(
        org_id=org_id,
        business_unit=business_unit,
        **result
    )

    return result
```

### FastAPI Middleware Integration

```python
from fastapi import Request, HTTPException
from intelligence_capture.context_registry import get_registry

@app.middleware("http")
async def validate_org_namespace(request: Request, call_next):
    # Extract org_id from request
    org_id = request.headers.get("X-Org-ID")

    if not org_id:
        raise HTTPException(400, "X-Org-ID header required")

    # Validate namespace exists
    registry = get_registry()
    is_valid = await registry.validate_namespace(
        org_id=org_id,
        business_unit=request.query_params.get("business_unit", "*")
    )

    if not is_valid:
        raise HTTPException(
            403,
            f"Organización '{org_id}' no autorizada"
        )

    # Log access
    await registry.log_access(
        org_id=org_id,
        access_type="query",
        user_id=request.headers.get("X-User-ID")
    )

    return await call_next(request)
```

### Pydantic AI Agent Integration

```python
from intelligence_capture.context_registry import get_registry

async def agent_query(query: str, org_id: str, session_id: str):
    registry = get_registry()

    # 1. Get organization context
    context = await registry.lookup_by_org_id(org_id)

    if not context:
        return {"error": f"Organización '{org_id}' no encontrada"}

    # 2. Inject context into agent prompt
    agent_context = {
        "org_id": context.org_id,
        "org_name": context.org_name,
        "industry": context.industry_context,
        "namespace": context.namespace
    }

    # 3. Execute agent query
    result = await agent.run(query, context=agent_context)

    # 4. Log access
    await registry.log_access(
        org_id=org_id,
        access_type="retrieval",
        session_id=session_id,
        query_params={"query": query},
        result_count=len(result.get("sources", [])),
        latency_ms=result.get("latency_ms")
    )

    return result
```

## Configuration

Edit [`config/context_registry.yaml`](../config/context_registry.yaml) to customize:

- **Cache TTL**: Default 1 hour (3600s)
- **Priority Tiers**: Standard vs Premium settings
- **Consent Template**: Default operations and retention
- **Rate Limiting**: Requests per minute per org
- **Monitoring**: Health checks and alerting

## CLI Tools

### Sync Organizations

```bash
# Dry run (preview changes)
python scripts/context_registry_sync.py --dry-run

# Sync to database
python scripts/context_registry_sync.py

# Custom config file
python scripts/context_registry_sync.py --config path/to/companies.json
```

### List Organizations

```bash
# Show all organizations and namespaces
python scripts/context_registry_sync.py --list
```

### Run Tests

```bash
# Verify implementation
python scripts/test_context_registry.py

# With pytest
pytest tests/test_context_registry.py -v
```

## Database Schema

### context_registry
Stores organization metadata with unique `(org_id, business_unit, department)` constraint.

### context_access_log
Audit trail for all access events (required for Bolivian privacy compliance).

### context_registry_audit
Tracks all changes to registry entries.

See [`scripts/migrations/2025_01_00_context_registry.sql`](../scripts/migrations/2025_01_00_context_registry.sql) for full schema.

## Compliance

### Bolivian Privacy Framework
- **Law 164**: Telecommunications and ICTs
- **Constitution Art. 21**: Right to Privacy
- **Habeas Data**: 12-month retention requirement

### Features
✅ Access logging for all operations
✅ Spanish-language error messages
✅ Consent validation before operations
✅ Per-org namespace isolation
✅ Full audit trail

## Caching

- **Default TTL**: 1 hour (configurable)
- **Backend**: In-memory (Redis support available)
- **Invalidation**: Automatic on org updates
- **Manual Clear**: `await registry.clear_cache()`

## Performance

- **Connection Pool**: 2-10 connections
- **Async Operations**: Non-blocking I/O
- **Cache Hit Rate**: ~90% after warmup
- **Lookup Latency**: <10ms (cached), <50ms (uncached)

## Error Handling

All errors return Spanish-language messages referencing Bolivian legal framework:

```python
# Example error message
"Organización 'invalid_org' no encontrada en el registro de contexto"

"Operación 'export' no autorizada para 'los_tajibos'.
Referencia: Ley 164 de Telecomunicaciones y TICs, Art. 21 de la Constitución."
```

## Development

### Add New Organization

1. Edit [`config/companies.json`](../config/companies.json)
2. Run sync: `python scripts/context_registry_sync.py`
3. Verify: `python scripts/context_registry_sync.py --list`

### Custom Consent Metadata

```python
custom_consent = {
    "consent_obtained": True,
    "consent_date": "2025-01-09",
    "allowed_operations": ["ingestion", "retrieval"],
    "data_retention_days": 180,
    "privacy_framework": "Bolivian Law 164",
    "notes": "Limited to ingestion and retrieval only"
}

await registry.register_organization(
    org_id="new_org",
    consent_metadata=custom_consent,
    ...
)
```

## Troubleshooting

### "DATABASE_URL not set"
```bash
export DATABASE_URL="postgresql://user:pass@localhost:5432/dbname"
```

### "No module named 'asyncpg'"
```bash
pip install -r requirements-rag2.txt
```

### "Organization not found"
```bash
# Check if org is synced
python scripts/context_registry_sync.py --list

# Re-sync from companies.json
python scripts/context_registry_sync.py
```

### Clear Cache
```python
registry = get_registry()
await registry.connect()
await registry.clear_cache()
```

## References

- **Full Implementation Summary**: [`reports/task_0_implementation_summary.md`](../reports/task_0_implementation_summary.md)
- **Requirements**: [`.kiro/specs/rag-2.0-enhancement/requirements.md`](../.kiro/specs/rag-2.0-enhancement/requirements.md)
- **Design**: [`.kiro/specs/rag-2.0-enhancement/design.md`](../.kiro/specs/rag-2.0-enhancement/design.md)
- **Tasks**: [`.kiro/specs/rag-2.0-enhancement/tasks.md`](../.kiro/specs/rag-2.0-enhancement/tasks.md)
