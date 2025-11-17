# Quick Start: Ejecutar el Agente RAG con Conexiones Reales

**Objetivo**: Validar que el agente funciona con PostgreSQL, Neo4j y OpenAI API reales.

**Tiempo**: 5 minutos

**Costo**: ~$0.001 (0.1 centavos)

---

## Prerequisitos

### 1. Servicios Operativos

```bash
# Verificar PostgreSQL + pgvector
psql postgresql://postgres@localhost:5432/comversa_rag -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"

# Verificar Neo4j
cypher-shell -u neo4j -p comversa_neo4j_2025 "MATCH (n:Entity) RETURN count(n) LIMIT 1"

# Verificar OpenAI API key
echo $OPENAI_API_KEY  # Debe empezar con sk-
```

### 2. Variables de Entorno

```bash
# En ~/.zshrc o ~/.bashrc
export DATABASE_URL="postgresql://postgres@localhost:5432/comversa_rag"
export NEO4J_URI="neo4j://localhost:7687"
export NEO4J_USER="neo4j"
export NEO4J_PASSWORD="comversa_neo4j_2025"
export OPENAI_API_KEY="sk-..."  # Tu API key

# Aplicar cambios
source ~/.zshrc  # o ~/.bashrc
```

### 3. Dependencias Python

```bash
pip install -r requirements-rag2.txt
```

---

## Opción 1: Script de Ejemplo (agent/example.py)

El agente incluye un script de demostración con 5 ejemplos.

### Ejecutar Todo

```bash
cd /Users/tatooine/Documents/Development/Comversa/system0
python3 -m agent.example
```

**Output esperado**:
```
======================================================================
Pydantic AI RAG Agent - Examples
Task 10: Implement Pydantic AI Agent Orchestrator
======================================================================

=== Example 1: Single Query ===
INFO:agent.rag_agent:RAG Agent initialized: model=gpt-4o-mini, fallback=gpt-4o

Query: ¿Qué sistemas causan más puntos de dolor en Los Tajibos?
Answer: Los principales sistemas que causan puntos de dolor son...
Model: gpt-4o-mini
Session ID: abc123...

Tools used: 1 tool calls
  1. hybrid_search

...

=== Example 5: Checkpoint Lookup ===
...

======================================================================
All examples completed!
======================================================================
```

### Ejecutar Solo un Ejemplo

```python
# Editar agent/example.py, comentar todos menos uno
async def main():
    await example_single_query()  # Solo este
    # await example_multi_turn_conversation()
    # ...
```

---

## Opción 2: Python REPL Interactivo

### Session Básica

```python
import asyncio
from agent import RAGAgent

# Crear agente (toma ~2 segundos)
agent = await RAGAgent.create()

# Hacer una query
response = await agent.query(
    query="¿Qué sistemas hay en Los Tajibos?",
    org_id="los_tajibos",
)

# Ver respuesta
print(response['answer'])
print(f"Session: {response['session_id']}")
print(f"Model: {response['model']}")

# Cerrar conexiones
await agent.close()
```

### Conversación Multi-Turno

```python
import asyncio
from agent import RAGAgent

agent = await RAGAgent.create()
session_id = "my-session-001"

# Turno 1
r1 = await agent.query(
    "¿Cuáles son los sistemas principales?",
    "los_tajibos",
    session_id=session_id
)
print(f"Turno 1: {r1['answer'][:100]}...")

# Turno 2 (usa contexto del turno 1)
r2 = await agent.query(
    "¿Cuáles tienen problemas?",
    "los_tajibos",
    session_id=session_id
)
print(f"Turno 2: {r2['answer'][:100]}...")

# Turno 3 (usa contexto acumulado)
r3 = await agent.query(
    "¿Por qué?",
    "los_tajibos",
    session_id=session_id
)
print(f"Turno 3: {r3['answer'][:100]}...")

await agent.close()
```

### Ver Estadísticas de Herramientas

```python
import asyncio
from agent import RAGAgent

agent = await RAGAgent.create()

# Hacer algunas queries
for query in [
    "¿Qué dice sobre check-in?",
    "¿Qué sistemas causan dolor?",
    "Dame un resumen completo"
]:
    await agent.query(query, "los_tajibos")

# Ver estadísticas
stats = await agent.telemetry.get_tool_stats(
    org_id="los_tajibos",
    hours=1
)

for tool_name, metrics in stats.items():
    print(f"\n{tool_name}:")
    print(f"  Calls: {metrics.get('total_calls', 0)}")
    print(f"  Success rate: {metrics.get('success_rate', 0):.1%}")

await agent.close()
```

---

## Opción 3: Script Personalizado

Crear `test_agent.py`:

```python
#!/usr/bin/env python3
"""
Script de prueba rápida del agente RAG
"""
import asyncio
from agent import RAGAgent, AgentConfig

async def main():
    print("🚀 Iniciando agente RAG...")

    # Configuración personalizada
    config = AgentConfig(
        primary_model="gpt-4o-mini",
        temperature=0.0,  # Determinístico
        max_conversation_turns=3,
    )

    # Crear agente
    agent = await RAGAgent.create(config=config)
    print("✅ Agente creado\n")

    try:
        # Test 1: Query simple
        print("📝 Test 1: Query simple")
        r1 = await agent.query(
            query="¿Qué sistemas hay en Los Tajibos?",
            org_id="los_tajibos",
        )
        print(f"Respuesta: {r1['answer'][:150]}...\n")

        # Test 2: Multi-turno
        print("💬 Test 2: Conversación multi-turno")
        session_id = "test-001"

        r2 = await agent.query(
            "¿Cuáles son los principales procesos?",
            "los_tajibos",
            session_id=session_id
        )
        print(f"Turno 1: {r2['answer'][:100]}...")

        r3 = await agent.query(
            "¿Cuáles son ineficientes?",
            "los_tajibos",
            session_id=session_id
        )
        print(f"Turno 2: {r3['answer'][:100]}...\n")

        # Test 3: Different tools
        print("🔧 Test 3: Diferentes herramientas")

        # Vector search (texto específico)
        r4 = await agent.query(
            '¿Qué dice sobre "check-in manual"?',
            "los_tajibos"
        )
        print(f"Vector: {r4['answer'][:80]}...")

        # Graph search (relaciones)
        r5 = await agent.query(
            "¿Qué sistemas causan puntos de dolor?",
            "los_tajibos"
        )
        print(f"Graph: {r5['answer'][:80]}...")

        # Hybrid search (completo)
        r6 = await agent.query(
            "Dame un resumen ejecutivo",
            "los_tajibos"
        )
        print(f"Hybrid: {r6['answer'][:80]}...\n")

        print("✅ Todos los tests pasaron exitosamente")

    except Exception as e:
        print(f"❌ Error: {e}")
        raise

    finally:
        # Siempre cerrar conexiones
        await agent.close()
        print("🧹 Conexiones cerradas")

if __name__ == "__main__":
    asyncio.run(main())
```

Ejecutar:
```bash
python3 test_agent.py
```

---

## Verificar que Funcionó

### 1. Check Logs de Telemetría

```sql
-- Conectar a PostgreSQL
psql $DATABASE_URL

-- Ver últimas queries
SELECT
    tool_name,
    query,
    success,
    execution_time_ms,
    timestamp
FROM tool_usage_logs
WHERE timestamp > now() - interval '10 minutes'
ORDER BY timestamp DESC
LIMIT 10;
```

### 2. Check Sesiones Guardadas

```sql
-- Ver sesiones recientes
SELECT
    session_id,
    org_id,
    jsonb_array_length(messages) as message_count,
    updated_at
FROM chat_sessions
WHERE updated_at > now() - interval '10 minutes'
ORDER BY updated_at DESC
LIMIT 5;

-- Ver mensajes de una sesión específica
SELECT
    session_id,
    jsonb_pretty(messages) as conversation
FROM chat_sessions
WHERE session_id = 'tu-session-id';
```

### 3. Check Neo4j

```bash
# Ver entidades consultadas recientemente
cypher-shell -u neo4j -p $NEO4J_PASSWORD "
MATCH (n:Entity)
WHERE n.entity_type IN ['system', 'pain_point', 'process']
RETURN n.entity_type, n.name, n.source_count
ORDER BY n.source_count DESC
LIMIT 10
"
```

---

## Troubleshooting

### Error: "No module named 'agent'"

**Solución**: Ejecutar desde el directorio raíz del proyecto
```bash
cd /Users/tatooine/Documents/Development/Comversa/system0
python3 -m agent.example  # Usar -m para module import
```

### Error: "Missing required environment variables"

**Solución**: Verificar que todas las variables estén configuradas
```bash
echo "DATABASE_URL: $DATABASE_URL"
echo "NEO4J_URI: $NEO4J_URI"
echo "NEO4J_PASSWORD: $NEO4J_PASSWORD"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:0:7}..."  # Solo primeros 7 chars
```

### Error: "Connection to database failed"

**Solución**: Verificar que PostgreSQL esté corriendo
```bash
# Ver status
pg_ctl status -D /opt/homebrew/var/postgresql@15

# Iniciar si está stopped
brew services start postgresql@15
```

### Error: "Neo4j connection failed"

**Solución**: Verificar que Neo4j esté corriendo
```bash
# Ver status
brew services list | grep neo4j

# Iniciar si está stopped
brew services start neo4j
```

### Error: "OpenAI API error"

**Solución**: Verificar API key y balance
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | jq '.data[0].id'

# Si retorna un modelo, la key es válida
```

### Respuesta lenta (>10 segundos)

**Posibles causas**:
1. Primera query (carga inicial de conexiones)
2. Neo4j sin índices (ejecutar `scripts/graph/bootstrap_neo4j.py`)
3. PostgreSQL sin índices HNSW (revisar migration 2025_01_01_pgvector.sql)

**Solución**: Queries subsiguientes deben ser <3 segundos

---

## Próximos Pasos

Una vez que el quick start funciona:

1. **Tests unitarios** (para desarrollo rápido):
   ```bash
   pytest tests/test_agent_*.py -q
   ```

2. **Tests de integración** (antes de PR):
   ```bash
   pytest tests/test_agent_real_integration.py -v -m real_integration
   ```

3. **Manual testing** (antes de producción):
   ```bash
   # Seguir checklist en:
   tests/MANUAL_AGENT_TEST_CHECKLIST.md
   ```

4. **Explorar API** (Task 12 - próximo):
   ```bash
   # Cuando esté implementado:
   uvicorn api.server:app --reload
   curl http://localhost:8000/chat -X POST -d '{"query": "..."}'
   ```

---

## Referencias

- **Agent README**: [agent/README.md](README.md)
- **Test Guide**: [tests/TEST_AGENT_GUIDE.md](../tests/TEST_AGENT_GUIDE.md)
- **Task 10 Complete**: [TASK_10_COMPLETE.md](../TASK_10_COMPLETE.md)
- **Requirements**: [.kiro/specs/rag-2.0-enhancement/requirements.md](../.kiro/specs/rag-2.0-enhancement/requirements.md)
