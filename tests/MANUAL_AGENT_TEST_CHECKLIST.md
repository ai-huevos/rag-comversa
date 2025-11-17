# Lista de Verificación Manual del Agente RAG (Task 10)

**Propósito**: Validar que el agente funciona correctamente con dependencias reales antes de producción.

**Cuándo usar**: Después de pasar tests unitarios, antes de desplegar a staging/production.

**Duración estimada**: 15-20 minutos

**Costo estimado**: $0.02-0.05 USD (2-5 centavos)

---

## Pre-requisitos

### 1. Servicios Operativos

```bash
# Verificar PostgreSQL
psql $DATABASE_URL -c "SELECT version();"

# Verificar pgvector extension
psql $DATABASE_URL -c "SELECT extversion FROM pg_extension WHERE extname = 'vector';"

# Verificar Neo4j
cypher-shell -u neo4j -p $NEO4J_PASSWORD "RETURN 'OK' as status"

# Verificar OpenAI API
curl https://api.openai.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY" | head -20
```

### 2. Datos de Prueba

```bash
# Verificar que hay documentos ingested
psql $DATABASE_URL -c "SELECT COUNT(*) FROM documents;"

# Verificar que hay embeddings
psql $DATABASE_URL -c "SELECT COUNT(*) FROM embeddings;"

# Verificar que hay entidades consolidadas en Neo4j
cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n:Entity) RETURN count(n) as total"
```

---

## Checklist de Validación

### Fase 1: Inicialización (5 min)

#### ✅ 1.1. Crear Agente

```python
# Ejecutar desde python3 REPL o script
from agent import RAGAgent

agent = await RAGAgent.create()
print("✅ Agente creado exitosamente")
```

**Verificar**:
- [ ] No hay errores de conexión
- [ ] Todas las dependencias se inicializan
- [ ] Se cargan las credenciales correctamente

#### ✅ 1.2. Verificar Conexiones

```python
# Test PostgreSQL
async with agent.db_pool.acquire() as conn:
    result = await conn.fetchval("SELECT 1")
    print(f"PostgreSQL: {result}")  # Debe ser 1

# Test Neo4j
async with agent.neo4j_driver.session() as session:
    result = await session.run("RETURN 1 as val")
    data = await result.data()
    print(f"Neo4j: {data[0]['val']}")  # Debe ser 1

print("✅ Todas las conexiones operativas")
```

**Verificar**:
- [ ] PostgreSQL responde
- [ ] Neo4j responde
- [ ] No hay errores de autenticación

---

### Fase 2: Query Básica (5 min)

#### ✅ 2.1. Query Simple

```python
response = await agent.query(
    query="¿Qué sistemas hay en Los Tajibos?",
    org_id="los_tajibos",
)

print(f"Respuesta: {response['answer']}")
print(f"Session ID: {response['session_id']}")
print(f"Modelo: {response['model']}")
```

**Verificar**:
- [ ] Respuesta en español (no traducida)
- [ ] Mención de sistemas hoteleros
- [ ] Session ID generado
- [ ] Modelo usado: gpt-4o-mini
- [ ] Tiempo de respuesta <5 segundos

#### ✅ 2.2. Inspeccionar Tool Calls

```python
if 'tool_calls' in response:
    for tool in response['tool_calls']:
        print(f"Herramienta usada: {tool.get('tool_name', 'unknown')}")
else:
    print("⚠️ No se registraron tool calls")
```

**Verificar**:
- [ ] Al menos 1 herramienta fue usada
- [ ] Nombre de herramienta válido (vector_search, graph_search, hybrid_search)

---

### Fase 3: Conversación Multi-Turno (5 min)

#### ✅ 3.1. Turno 1: Pregunta Inicial

```python
session_id = "test-manual-001"

response1 = await agent.query(
    query="¿Cuáles son los sistemas principales en Los Tajibos?",
    org_id="los_tajibos",
    session_id=session_id,
)

print(f"Turno 1: {response1['answer'][:150]}...")
```

**Verificar**:
- [ ] Respuesta coherente
- [ ] Menciona sistemas específicos

#### ✅ 3.2. Turno 2: Pregunta de Seguimiento

```python
response2 = await agent.query(
    query="¿Cuáles de esos tienen problemas?",
    org_id="los_tajibos",
    session_id=session_id,
)

print(f"Turno 2: {response2['answer'][:150]}...")
```

**Verificar**:
- [ ] Usa contexto del turno anterior (menciona sistemas sin que se repita la pregunta)
- [ ] Responde específicamente sobre problemas
- [ ] Session ID es el mismo

#### ✅ 3.3. Turno 3: Profundización

```python
response3 = await agent.query(
    query="¿En qué departamentos impactan más?",
    org_id="los_tajibos",
    session_id=session_id,
)

print(f"Turno 3: {response3['answer'][:150]}...")
```

**Verificar**:
- [ ] Usa contexto acumulado
- [ ] Menciona departamentos específicos
- [ ] Coherencia con respuestas anteriores

---

### Fase 4: Selección de Herramientas (3 min)

#### ✅ 4.1. Forzar Vector Search

```python
# Query que debe usar búsqueda vectorial (texto específico)
response_vector = await agent.query(
    query='¿Qué dice exactamente el documento sobre "check-in manual"?',
    org_id="los_tajibos",
)

print(f"Vector search: {response_vector['answer'][:100]}...")
```

**Verificar**:
- [ ] Cita texto específico del documento
- [ ] Usa comillas o evidencia directa

#### ✅ 4.2. Forzar Graph Search

```python
# Query que debe usar búsqueda en grafo (relaciones)
response_graph = await agent.query(
    query="¿Qué sistemas causan puntos de dolor y por qué?",
    org_id="los_tajibos",
)

print(f"Graph search: {response_graph['answer'][:100]}...")
```

**Verificar**:
- [ ] Menciona relaciones entre entidades
- [ ] Identifica causas y efectos

#### ✅ 4.3. Forzar Hybrid Search

```python
# Query que debe usar búsqueda híbrida (análisis completo)
response_hybrid = await agent.query(
    query="Dame un resumen ejecutivo completo de las operaciones",
    org_id="los_tajibos",
)

print(f"Hybrid search: {response_hybrid['answer'][:100]}...")
```

**Verificar**:
- [ ] Respuesta comprehensiva
- [ ] Combina datos de múltiples fuentes

---

### Fase 5: Aislamiento Multi-Org (2 min)

#### ✅ 5.1. Query para Diferentes Orgs

```python
# Los Tajibos
response_lt = await agent.query(
    query="¿Qué sistemas hay?",
    org_id="los_tajibos",
    session_id="lt-test",
)

# Bolivian Foods
response_bf = await agent.query(
    query="¿Qué sistemas hay?",
    org_id="bolivian_foods",
    session_id="bf-test",
)

print(f"Los Tajibos: {response_lt['answer'][:80]}")
print(f"Bolivian Foods: {response_bf['answer'][:80]}")
```

**Verificar**:
- [ ] Respuestas diferentes (contexto específico de cada org)
- [ ] No hay "leak" de datos entre organizaciones
- [ ] Sessions IDs diferentes

---

### Fase 6: Telemetría y Costos (2 min)

#### ✅ 6.1. Verificar Logging de Telemetría

```sql
-- Ejecutar en PostgreSQL
SELECT
    tool_name,
    COUNT(*) as calls,
    AVG(execution_time_ms) as avg_time,
    SUM(CASE WHEN success THEN 1 ELSE 0 END) as successes
FROM tool_usage_logs
WHERE timestamp > now() - interval '10 minutes'
GROUP BY tool_name;
```

**Verificar**:
- [ ] Hay logs recientes
- [ ] Success rate >90%
- [ ] Avg time <2000ms (2 segundos)

#### ✅ 6.2. Verificar Persistencia de Sesiones

```sql
-- Ejecutar en PostgreSQL
SELECT
    session_id,
    org_id,
    array_length(messages::json, 1) as message_count,
    updated_at
FROM chat_sessions
WHERE updated_at > now() - interval '10 minutes'
ORDER BY updated_at DESC
LIMIT 5;
```

**Verificar**:
- [ ] Sesiones guardadas en base de datos
- [ ] Mensajes persistidos correctamente
- [ ] Timestamps actualizándose

---

### Fase 7: Manejo de Errores (2 min)

#### ✅ 7.1. Query Ambigua

```python
response = await agent.query(
    query="?",
    org_id="los_tajibos",
)

print(f"Query ambigua: {response['answer']}")
```

**Verificar**:
- [ ] No crashea
- [ ] Responde en español
- [ ] Pide clarificación

#### ✅ 7.2. Org ID Inválido

```python
response = await agent.query(
    query="Test",
    org_id="org_inexistente_12345",
)

print(f"Org inválido: {response['answer']}")
```

**Verificar**:
- [ ] No crashea
- [ ] Maneja el error gracefully
- [ ] Respuesta en español

---

### Fase 8: Limpieza (1 min)

#### ✅ 8.1. Cerrar Conexiones

```python
await agent.close()
print("✅ Conexiones cerradas correctamente")
```

**Verificar**:
- [ ] No hay errores al cerrar
- [ ] Recursos liberados

---

## Resumen de Validación

### ✅ Criterios de Éxito

- [ ] **Inicialización**: Agente se crea sin errores
- [ ] **Conectividad**: PostgreSQL + Neo4j + OpenAI operativos
- [ ] **Query Básica**: Respuesta coherente en español <5s
- [ ] **Multi-Turno**: Mantiene contexto entre turnos
- [ ] **Tool Selection**: Usa herramientas apropiadas
- [ ] **Multi-Org**: Aislamiento correcto de datos
- [ ] **Telemetría**: Logs guardados en PostgreSQL
- [ ] **Persistencia**: Sesiones guardadas correctamente
- [ ] **Error Handling**: Maneja errores sin crash
- [ ] **Cleanup**: Cierra conexiones sin errores

### 🚨 Red Flags (Fallos Críticos)

- ❌ **Error de conexión**: No puede conectar a PostgreSQL/Neo4j
- ❌ **Query timeout**: Toma >10 segundos responder
- ❌ **Respuesta en inglés**: Traduce automáticamente
- ❌ **Data leak**: Muestra datos de otra organización
- ❌ **No persistence**: Sesiones no se guardan
- ❌ **High cost**: >$0.01 por query simple
- ❌ **Crash**: El agente se cae con query válida

### ⚠️ Warnings (Requieren Investigación)

- ⚠️ Respuesta lenta (>3 segundos para query simple)
- ⚠️ Tool selection incorrecta (>20% de las veces)
- ⚠️ Contexto perdido en multi-turno
- ⚠️ Telemetría incompleta

---

## Registro de Resultados

**Fecha**: _______________
**Ejecutado por**: _______________
**Versión**: Task 10 - RAG Agent Orchestrator

### Resultados

| Fase | Estado | Notas |
|------|--------|-------|
| 1. Inicialización | ☐ Pass ☐ Fail | |
| 2. Query Básica | ☐ Pass ☐ Fail | |
| 3. Multi-Turno | ☐ Pass ☐ Fail | |
| 4. Tool Selection | ☐ Pass ☐ Fail | |
| 5. Multi-Org | ☐ Pass ☐ Fail | |
| 6. Telemetría | ☐ Pass ☐ Fail | |
| 7. Error Handling | ☐ Pass ☐ Fail | |
| 8. Limpieza | ☐ Pass ☐ Fail | |

**Costo Total**: $_________ USD

**Decision**: ☐ Aprobado para producción ☐ Requiere correcciones

---

## Script de Ejecución Rápida

Guardar como `manual_test_agent.py` y ejecutar:

```python
#!/usr/bin/env python3
"""Script de validación manual del agente RAG"""
import asyncio
from agent import RAGAgent

async def main():
    print("🚀 Iniciando validación manual del agente RAG...")

    # Crear agente
    agent = await RAGAgent.create()

    try:
        # Test 1: Query simple
        print("\n📝 Test 1: Query simple")
        r1 = await agent.query("¿Qué sistemas hay?", "los_tajibos")
        print(f"✅ Respuesta: {r1['answer'][:100]}...")

        # Test 2: Multi-turno
        print("\n💬 Test 2: Multi-turno")
        r2 = await agent.query("¿Cuáles son los sistemas?", "los_tajibos", session_id="test-001")
        r3 = await agent.query("¿Cuáles tienen problemas?", "los_tajibos", session_id="test-001")
        print(f"✅ Turno 1: {r2['answer'][:50]}...")
        print(f"✅ Turno 2: {r3['answer'][:50]}...")

        # Test 3: Multi-org
        print("\n🏢 Test 3: Multi-org")
        r4 = await agent.query("Test", "los_tajibos")
        r5 = await agent.query("Test", "bolivian_foods")
        print(f"✅ Session LT: {r4['session_id'][:20]}...")
        print(f"✅ Session BF: {r5['session_id'][:20]}...")

        print("\n✅ Todas las pruebas pasaron")

    finally:
        await agent.close()
        print("🧹 Conexiones cerradas")

if __name__ == "__main__":
    asyncio.run(main())
```

Ejecutar:
```bash
python3 manual_test_agent.py
```
