# Pydantic AI Agent Orchestrator - RAG 2.0

**Task 10: Implement Pydantic AI Agent Orchestrator**

This module provides intelligent retrieval tool selection combining vector search (pgvector) and graph queries (Neo4j) with Spanish-first operation and budget awareness.

## Features

✅ **Pydantic AI Framework** - Agent orchestration with tool calling capabilities (R6.1)
✅ **Multi-Tool Retrieval** - Vector, graph, hybrid search, and checkpoint lookup (R6.2)
✅ **Smart Tool Routing** - Context-aware tool selection based on query type (R6.3)
✅ **Conversation Memory** - Multi-turn context with session management (R6.7)
✅ **Tool Telemetry** - Usage logging and governance analysis (R6.4)
✅ **Spanish-First** - Native Spanish operation without translation (R6.6)
✅ **LLM Fallback Chain** - gpt-4o-mini → gpt-4o for cost efficiency (Task 10)
✅ **Budget Awareness** - Cost tracking and CostGuard integration (R14.1)
✅ **Streaming Support** - Real-time responses for API endpoints (R6.5)

## Architecture

```
RAGAgent (rag_agent.py)
├── Tools (tools/)
│   ├── vector_search.py      - Pgvector semantic search
│   ├── graph_search.py        - Neo4j relationship queries
│   ├── hybrid_search.py       - Reciprocal rank fusion
│   └── checkpoint_lookup.py   - Governance checkpoints
├── Session Management (session.py)
│   └── Multi-turn conversation context
└── Telemetry (telemetry.py)
    └── Tool usage logging & analytics
```

## Requirements

- **R6.1-R6.7**: Agentic RAG with Pydantic AI framework
- **R0.3**: Context registry lookups for org namespaces
- **R8.1-R8.7**: Hybrid search with reciprocal rank fusion
- **R9.3**: Session history for multi-turn conversations
- **R14.1**: Cost tracking and budget awareness

## Installation

Dependencies are in `requirements-rag2.txt`:

```bash
pip install pydantic-ai>=0.0.1 asyncpg>=0.29.0 neo4j>=5.14.0 openai>=1.3.0
```

## Usage

### Basic Query

```python
from agent import RAGAgent, AgentConfig

# Create agent with default configuration
agent = await RAGAgent.create()

# Execute query
response = await agent.query(
    query="¿Qué sistemas causan más puntos de dolor?",
    org_id="los_tajibos",
    context="operaciones",
)

print(response["answer"])
print(f"Tools used: {response['tool_calls']}")
```

### Custom Configuration

```python
from agent import AgentConfig

config = AgentConfig(
    primary_model="gpt-4o-mini",      # Cost-efficient primary
    fallback_model="gpt-4o",          # Fallback for complex queries
    embedding_model="text-embedding-3-small",
    max_conversation_turns=5,
    temperature=0.1,                  # Low for factual responses
)

agent = await RAGAgent.create(config=config)
```

### Multi-Turn Conversation

```python
# First turn
response1 = await agent.query(
    query="¿Cuáles son los principales sistemas en Los Tajibos?",
    org_id="los_tajibos",
    session_id="user-123",
)

# Follow-up (uses context from session_id)
response2 = await agent.query(
    query="¿Cuáles causan problemas?",
    org_id="los_tajibos",
    session_id="user-123",
)
```

### Tool Usage Statistics

```python
# Get tool usage stats for last 24 hours
stats = await agent.telemetry.get_tool_stats(
    org_id="los_tajibos",
    hours=24,
)

print(stats)
# {
#   "vector_search": {"total_calls": 45, "success_rate": 0.98, ...},
#   "graph_search": {"total_calls": 23, "success_rate": 0.95, ...},
#   ...
# }
```

## Tool Selection Guidelines

From `prompts/system_agent_prompt.md`:

- **vector_search**: Use for specific facts, quotes, or verbatim evidence from documents
- **graph_search**: Use for cross-entity questions, relationships, and system comparisons
- **hybrid_search**: Use for executive briefings or comprehensive analysis requiring both
- **checkpoint_lookup**: Use for governance reviews, approvals, and Habeas Data requests

## Tool Routing Logic

The agent automatically selects tools based on query patterns:

| Query Pattern | Tool Selection | Example |
|---------------|----------------|---------|
| Specific facts, documents | `vector_search` | "¿Qué dice el contrato sobre...?" |
| Relationships, comparisons | `graph_search` | "¿Qué sistemas causan dolor?" |
| Executive briefings | `hybrid_search` | "Resumen completo de Los Tajibos" |
| Compliance, reviews | `checkpoint_lookup` | "Estado de aprobaciones" |

## Telemetry & Governance

All tool calls are logged to:

1. **PostgreSQL** (`tool_usage_logs` table) - Real-time queries
2. **JSON Reports** (`reports/agent_usage/{org}/{date}.jsonl`) - Offline analysis
3. **Checkpoint Bundles** (`reports/checkpoints/{org}/{stage}/`) - Governance review

Metrics tracked:
- Tool selection rate (target: 85%+ correct selection)
- Execution time (vector <1s, graph <2s, hybrid <2.5s)
- Success/failure rates
- Cost per query (embeddings + LLM tokens)

## LLM Fallback Chain

1. **Primary**: `gpt-4o-mini` - Cost-efficient for most queries ($0.00015/1K tokens)
2. **Fallback**: `gpt-4o` - Complex synthesis when primary fails ($0.005/1K tokens)

No translation occurs - agent operates natively in Spanish per R6.6.

## Spanish Language Features

- Native Spanish system prompt from `prompts/system_agent_prompt.md`
- Spanish error messages and validation
- Bolivian privacy compliance references (Constitution Art. 21, Law 164)
- Synonym dictionaries for business terms (R15.4)

## Integration with RAG 2.0 Pipeline

```
Document Sources
    ↓
Ingestion Queue (Task 2)
    ↓
Document Processor (Task 3)
    ↓
OCR Engine (Task 4) + Chunking (Task 5)
    ↓
Dual Storage (Tasks 6-9)
    ├── PostgreSQL + pgvector
    └── Neo4j + Graffiti
         ↓
    RAG Agent (Task 10) ← You are here
         ↓
    FastAPI Endpoints (Task 12)
```

## Performance Targets

- Vector search: **<1 second** (HNSW index)
- Graph query: **<2 seconds** (indexed Cypher)
- Hybrid search: **<2.5 seconds** (parallel execution)
- Tool mis-selection: **<15%** (governance alert threshold)

## Testing

```bash
# Unit tests
pytest agent/tests/test_rag_agent.py -v

# Integration tests with fixtures
pytest agent/tests/test_integration.py -v

# Load test
python agent/tests/load_test.py --queries=100 --concurrent=10
```

## Environment Variables

```bash
# Required
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_PASSWORD="password"
export OPENAI_API_KEY="sk-..."

# Optional
export NEO4J_USER="neo4j"  # default
```

## Next Steps (Week 3)

- [ ] **Task 11**: Ship retrieval tool adapters & hybrid search refinements
- [ ] **Task 12**: Expose FastAPI endpoints with `/chat`, `/chat/stream`, `/health`
- [ ] **Task 13**: Deliver developer CLI for interactive testing
- [ ] **Task 14**: Add session storage, telemetry dashboards, cost alerts

## References

- **Requirements**: `.kiro/specs/rag-2.0-enhancement/requirements.md` (R6.1-R6.7)
- **Design**: `.kiro/specs/rag-2.0-enhancement/design.md` (Section 3, Component Designs)
- **Tasks**: `.kiro/specs/rag-2.0-enhancement/tasks.md` (Task 10)
- **System Prompt**: `prompts/system_agent_prompt.md`

## Support

For issues or questions:
- Check `CLAUDE.MD` for system overview
- Review `reports/agent_usage/{org}/{date}.jsonl` for telemetry
- Run `/health` endpoint to verify database/Neo4j connectivity

---

**Status**: ✅ Task 10 Complete - Pydantic AI Agent Orchestrator Implemented

**Timestamp**: 2025-11-11
