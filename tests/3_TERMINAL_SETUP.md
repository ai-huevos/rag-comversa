# Setup de 3 Terminales para Testing del Agente RAG

**Objetivo**: Ejecutar y monitorear el agente en tiempo real con 3 terminales.

**Vista general**:
- **Terminal 1 (Backend)**: Agente RAG corriendo (Python REPL o script)
- **Terminal 2 (Monitor)**: Logs de PostgreSQL/Neo4j en tiempo real
- **Terminal 3 (Testing)**: Esta sesión de Claude Code - ejecutar tests

---

## Terminal 1: 🖥️ Backend (Agente RAG)

### Opción A: Python REPL Interactivo (Recomendado)

```bash
# Terminal 1
cd /Users/tatooine/Documents/Development/Comversa/system0

# Iniciar Python con asyncio
python3 -m asyncio

# Dentro del REPL, ejecutar:
from agent import RAGAgent

# Crear agente (toma ~2-3 segundos)
agent = await RAGAgent.create()
print("✅ Agente listo! Usa 'agent.query()' para probar")

# Ahora puedes ejecutar queries:
response = await agent.query(
    query="¿Qué sistemas hay en Los Tajibos?",
    org_id="los_tajibos"
)
print(response['answer'])

# Para más queries:
r2 = await agent.query("¿Cuáles tienen problemas?", "los_tajibos")
r3 = await agent.query("Dame un resumen", "los_tajibos")

# Cuando termines:
await agent.close()
exit()
```

### Opción B: Ejecutar Script de Ejemplos

```bash
# Terminal 1
cd /Users/tatooine/Documents/Development/Comversa/system0

# Ejecutar todos los ejemplos (5 ejemplos, ~30 segundos)
python3 -m agent.example

# O crear un script personalizado
cat > test_backend.py << 'EOF'
import asyncio
from agent import RAGAgent

async def main():
    agent = await RAGAgent.create()

    print("Agente listo. Esperando queries...")

    # Bucle infinito para queries
    while True:
        try:
            query = input("\n👤 Query (o 'exit'): ")
            if query.lower() == 'exit':
                break

            response = await agent.query(query, "los_tajibos")
            print(f"\n🤖 {response['answer']}\n")

        except KeyboardInterrupt:
            break

    await agent.close()

if __name__ == "__main__":
    asyncio.run(main())
EOF

python3 test_backend.py
```

### Opción C: Jupyter Notebook (Si tienes instalado)

```bash
# Terminal 1
jupyter notebook

# Luego en el notebook:
# Cell 1:
from agent import RAGAgent
agent = await RAGAgent.create()

# Cell 2:
response = await agent.query("¿Qué sistemas hay?", "los_tajibos")
print(response['answer'])

# Cell 3:
# Más queries aquí...
```

---

## Terminal 2: 📊 Monitor (Logs de Base de Datos)

### Opción A: Monitor de Actividad Completo (Recomendado)

```bash
# Terminal 2
cd /Users/tatooine/Documents/Development/Comversa/system0

# Script de monitoreo en tiempo real
cat > monitor_activity.sh << 'EOF'
#!/bin/bash
while true; do
  clear
  echo "════════════════════════════════════════════════════════════════════"
  echo "📊 MONITOR DEL AGENTE RAG - $(date '+%H:%M:%S')"
  echo "════════════════════════════════════════════════════════════════════"
  echo ""

  echo "🔧 ÚLTIMOS TOOL CALLS (10 segundos):"
  psql $DATABASE_URL -c "
    SELECT
      to_char(timestamp, 'HH24:MI:SS') as time,
      tool_name,
      CASE WHEN success THEN '✅' ELSE '❌' END as status,
      execution_time_ms::int as ms,
      left(query, 40) as query
    FROM tool_usage_logs
    WHERE timestamp > now() - interval '10 seconds'
    ORDER BY timestamp DESC
    LIMIT 5
  " 2>/dev/null || echo "  (sin actividad)"

  echo ""
  echo "💬 SESIONES ACTIVAS:"
  psql $DATABASE_URL -c "
    SELECT
      left(session_id, 20) as session,
      org_id,
      jsonb_array_length(messages) as msgs,
      to_char(updated_at, 'HH24:MI:SS') as updated
    FROM chat_sessions
    WHERE updated_at > now() - interval '1 minute'
    ORDER BY updated_at DESC
    LIMIT 5
  " 2>/dev/null || echo "  (sin sesiones)"

  echo ""
  echo "📈 ESTADÍSTICAS (última hora):"
  psql $DATABASE_URL -c "
    SELECT
      tool_name,
      COUNT(*) as calls,
      AVG(execution_time_ms)::int as avg_ms,
      SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_pct
    FROM tool_usage_logs
    WHERE timestamp > now() - interval '1 hour'
    GROUP BY tool_name
    ORDER BY calls DESC
  " 2>/dev/null || echo "  (sin estadísticas)"

  echo ""
  echo "🔄 Actualizando en 3 segundos... (Ctrl+C para salir)"
  sleep 3
done
EOF

chmod +x monitor_activity.sh
./monitor_activity.sh
```

### Opción B: Monitor Simple de Tool Usage

```bash
# Terminal 2
watch -n 2 "psql \$DATABASE_URL -t -c \"
SELECT
  to_char(timestamp, 'HH24:MI:SS') as time,
  tool_name,
  CASE WHEN success THEN '✅' ELSE '❌' END,
  execution_time_ms::int || 'ms' as time,
  left(query, 50) as query
FROM tool_usage_logs
ORDER BY timestamp DESC
LIMIT 10
\""
```

### Opción C: Monitor de Neo4j + PostgreSQL

```bash
# Terminal 2
cat > monitor_dual.sh << 'EOF'
#!/bin/bash
while true; do
  clear
  echo "=== PostgreSQL Activity ==="
  psql $DATABASE_URL -c "SELECT COUNT(*) as tool_calls_last_minute FROM tool_usage_logs WHERE timestamp > now() - interval '1 minute'"

  echo ""
  echo "=== Neo4j Entities ==="
  cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n:Entity) RETURN n.entity_type, count(n) ORDER BY count(n) DESC LIMIT 5" 2>/dev/null

  echo ""
  sleep 3
done
EOF

chmod +x monitor_dual.sh
./monitor_dual.sh
```

### Opción D: Logs de PostgreSQL Nativo (Avanzado)

```bash
# Terminal 2
# Ver logs de PostgreSQL en tiempo real
tail -f /opt/homebrew/var/log/postgresql@15.log | grep -i "select\|insert\|update"
```

---

## Terminal 3: 💻 Testing (Esta Sesión de Claude Code)

### Opción A: Script de Test Interactivo (Recomendado)

```bash
# Terminal 3 (esta sesión)
cd /Users/tatooine/Documents/Development/Comversa/system0

# Ejecutar script de testing
python3 tests/manual_quick_test.py
```

**Output esperado**:
```
======================================================================
🧪 TESTING DEL AGENTE RAG - Terminal 3
======================================================================

🚀 Creando agente...
✅ Agente creado

----------------------------------------------------------------------
📝 TEST 1: Query Simple
----------------------------------------------------------------------
Query: ¿Qué sistemas hay en Los Tajibos?
Ejecutando...

✅ Respuesta (gpt-4o-mini):
   Los principales sistemas son...

📊 Session ID: abc123...
🔧 Tools usados: 1
   - hybrid_search

Presiona ENTER para continuar...
```

### Opción B: Tests Automatizados

```bash
# Terminal 3

# Unit tests (rápido, 2 segundos)
pytest tests/test_agent_session.py -v

# Integration tests (5 minutos, requiere BD reales)
pytest tests/test_agent_real_integration.py -v -m real_integration

# Test específico
pytest tests/test_agent_real_integration.py::TestRealAgentQueries::test_simple_query_end_to_end -v
```

### Opción C: Python REPL para Queries Ad-Hoc

```bash
# Terminal 3
python3 -m asyncio

# Ejecutar queries de prueba
from agent import RAGAgent
agent = await RAGAgent.create()

# Test 1: Query simple
r1 = await agent.query("¿Qué sistemas hay?", "los_tajibos")
print(r1['answer'])

# Test 2: Multi-turno
sid = "test-001"
r2 = await agent.query("¿Cuáles son los sistemas?", "los_tajibos", session_id=sid)
r3 = await agent.query("¿Cuáles tienen problemas?", "los_tajibos", session_id=sid)

# Test 3: Ver estadísticas
stats = await agent.telemetry.get_tool_stats("los_tajibos", hours=1)
print(stats)

await agent.close()
```

### Opción D: Monitorear PostgreSQL/Neo4j Directamente

```bash
# Terminal 3

# Ver sesiones en tiempo real
watch -n 3 "psql \$DATABASE_URL -c 'SELECT session_id, org_id, jsonb_array_length(messages) FROM chat_sessions ORDER BY updated_at DESC LIMIT 5'"

# Ver tool usage
watch -n 3 "psql \$DATABASE_URL -c 'SELECT tool_name, COUNT(*) FROM tool_usage_logs GROUP BY tool_name'"

# Ver entidades en Neo4j
watch -n 5 "cypher-shell -u neo4j -p \$NEO4J_PASSWORD 'MATCH (n:Entity) RETURN n.entity_type, count(n) LIMIT 10'"
```

---

## Workflow Completo Paso a Paso

### Setup Inicial (Una vez)

1. **Verificar dependencias**:
```bash
# En cualquier terminal
psql $DATABASE_URL -c "SELECT 1"  # PostgreSQL
cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 1"  # Neo4j
echo $OPENAI_API_KEY  # OpenAI
```

2. **Instalar dependencias Python**:
```bash
pip install -r requirements-rag2.txt
```

### Flujo de Testing

**Paso 1: Iniciar Backend (Terminal 1)**
```bash
# Terminal 1
python3 -m asyncio
from agent import RAGAgent
agent = await RAGAgent.create()
print("✅ Ready")
```

**Paso 2: Iniciar Monitor (Terminal 2)**
```bash
# Terminal 2
cd /Users/tatooine/Documents/Development/Comversa/system0
./monitor_activity.sh
```

**Paso 3: Ejecutar Tests (Terminal 3)**
```bash
# Terminal 3
python3 tests/manual_quick_test.py
```

**Paso 4: Observar**
- Terminal 1: Ver queries ejecutándose
- Terminal 2: Ver logs de BD en tiempo real
- Terminal 3: Ver resultados de tests

**Paso 5: Interactuar**
```bash
# En Terminal 1 (Python REPL):
response = await agent.query(
    "¿Qué sistemas causan dolor?",
    "los_tajibos"
)
print(response['answer'])

# Inmediatamente ver en Terminal 2:
# - Tool call registrado
# - Session guardada
# - Telemetría actualizada
```

---

## Casos de Uso Comunes

### Caso 1: Desarrollo Iterativo

```bash
# Terminal 1: Agente en REPL (mantener abierto)
# Terminal 2: Monitor (mantener abierto)
# Terminal 3: Editar código → re-importar → test

# En Terminal 3:
# 1. Editar agent/rag_agent.py
# 2. En Terminal 1, re-importar:
import importlib
import agent.rag_agent
importlib.reload(agent.rag_agent)

# 3. Re-crear agente con cambios
agent = await RAGAgent.create()

# 4. Test query
response = await agent.query("test", "los_tajibos")
```

### Caso 2: Debugging de Issue

```bash
# Terminal 1: Reproducir issue con query específica
response = await agent.query("query problemática", "los_tajibos")

# Terminal 2: Ver exactamente qué pasó en BD
# - ¿Qué tool se usó?
# - ¿Cuánto tiempo tomó?
# - ¿Hubo error?

# Terminal 3: Ejecutar test que reproduce el issue
pytest tests/test_specific_issue.py -v
```

### Caso 3: Performance Testing

```bash
# Terminal 1: Ejecutar múltiples queries
for i in range(10):
    await agent.query(f"Query {i}", "los_tajibos")

# Terminal 2: Ver estadísticas de performance
# - Avg execution time
# - Success rate
# - Tool distribution

# Terminal 3: Analizar resultados
psql $DATABASE_URL -c "
SELECT
  AVG(execution_time_ms) as avg_ms,
  MAX(execution_time_ms) as max_ms,
  MIN(execution_time_ms) as min_ms
FROM tool_usage_logs
WHERE timestamp > now() - interval '1 minute'
"
```

---

## Troubleshooting

### Terminal 1 (Backend) - Error al crear agente

**Síntoma**: `ModuleNotFoundError: No module named 'asyncpg'`

**Solución**:
```bash
pip install -r requirements-rag2.txt
```

### Terminal 2 (Monitor) - `psql: command not found`

**Solución**:
```bash
# Agregar psql al PATH
export PATH="/opt/homebrew/opt/postgresql@15/bin:$PATH"

# O usar ruta completa
/opt/homebrew/opt/postgresql@15/bin/psql $DATABASE_URL
```

### Terminal 3 (Testing) - Tests fallan

**Síntoma**: `Connection refused` en tests

**Solución**:
```bash
# Verificar que PostgreSQL y Neo4j están corriendo
brew services list | grep -E "postgresql|neo4j"

# Iniciar si están stopped
brew services start postgresql@15
brew services start neo4j
```

### Monitor muestra "(sin actividad)"

**Causa**: El agente no está ejecutando queries

**Solución**: Ejecutar una query en Terminal 1 o Terminal 3

---

## Scripts Útiles

### Quick Reset (Limpiar datos de testing)

```bash
# Limpiar logs de testing (últimos 5 minutos)
psql $DATABASE_URL -c "DELETE FROM tool_usage_logs WHERE timestamp > now() - interval '5 minutes'"

# Limpiar sesiones de testing
psql $DATABASE_URL -c "DELETE FROM chat_sessions WHERE session_id LIKE 'test-%'"
```

### Quick Stats (Ver resumen rápido)

```bash
# Ver resumen de actividad
cat > quick_stats.sh << 'EOF'
echo "Tool Calls (last hour):"
psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM tool_usage_logs WHERE timestamp > now() - interval '1 hour'"

echo ""
echo "Active Sessions:"
psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM chat_sessions WHERE updated_at > now() - interval '1 hour'"

echo ""
echo "Neo4j Entities:"
cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n:Entity) RETURN count(n)" 2>/dev/null | tail -1
EOF

chmod +x quick_stats.sh
./quick_stats.sh
```

---

## Próximos Pasos

Una vez que domines el setup de 3 terminales:

1. **Automatizar con tmux** (opcional):
```bash
tmux new-session -d -s agent
tmux split-window -h
tmux split-window -v
# Terminal 1: Backend
# Terminal 2: Monitor
# Terminal 3: Testing
```

2. **Implementar FastAPI** (Task 12):
   - Terminal 1: `uvicorn api.server:app --reload`
   - Terminal 2: Monitor logs
   - Terminal 3: `curl` requests

3. **Implementar CLI** (Task 13):
   - Terminal 1: Backend agent
   - Terminal 2: Monitor
   - Terminal 3: `python -m agent.cli`

---

**Resumen**:
- **Terminal 1** = Agente corriendo (backend)
- **Terminal 2** = Logs en vivo (monitor)
- **Terminal 3** = Ejecutar tests (esta sesión)

**Empezar ahora**:
```bash
# Terminal 1
python3 -m asyncio
from agent import RAGAgent
agent = await RAGAgent.create()

# Terminal 2
cd /Users/tatooine/Documents/Development/Comversa/system0
./tests/monitor_activity.sh  # (crear primero copiando de arriba)

# Terminal 3
python3 tests/manual_quick_test.py
```
