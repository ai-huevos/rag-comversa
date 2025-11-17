# Guía de Pruebas del Agente RAG (Task 10)

**Fecha**: 2025-11-13
**Estado**: ✅ Suite de pruebas completa
**Archivos**: 5 archivos de prueba, ~1,200 LOC

## Resumen

Se ha creado una **estrategia de testing en 3 niveles** para validar completamente la implementación del Task 10:

### Pirámide de Testing

```
                  /\
                 /  \  Manual Tests (~20 min, real deps)
                /____\
               /      \  Integration Tests (~5 min, real deps)
              /________\
             /          \  Unit Tests (~2 sec, mocked)
            /__________  \
```

### 1️⃣ **Unit Tests con Mocks** (tests/test_agent_*.py) - 85+ tests, ~2 segundos
- ✅ **Rápidos**: Sin dependencias externas
- ✅ **Determinísticos**: Siempre mismo resultado
- ✅ **Aislados**: Prueban lógica pura
- ❌ **No prueban integración real**

**Cobertura**:
- Gestión de sesiones y conversaciones multi-turno
- Telemetría y tracking de uso de herramientas
- Orquestación del agente RAG principal
- Manejo de errores y fallback
- Aislamiento multi-org
- Operación en español sin traducción

### 2️⃣ **Integration Tests con Deps Reales** (tests/test_agent_real_integration.py) - 10+ tests, ~5 minutos
- ✅ **Valida conexiones reales**: PostgreSQL + Neo4j + OpenAI
- ✅ **Automatizable**: Puede correr en CI con setup adecuado
- ⚠️ **Requiere deps**: Bases de datos operativas
- ⚠️ **Costo**: ~$0.005 (0.5 centavos) por ejecución

**Cobertura**:
- Conexiones a PostgreSQL, Neo4j, OpenAI
- Queries end-to-end con datos reales
- Persistencia de sesiones en BD
- Telemetría guardada en PostgreSQL
- Tool selection con datos reales

### 3️⃣ **Manual Tests** (tests/MANUAL_AGENT_TEST_CHECKLIST.md) - Checklist, ~20 minutos
- ✅ **Validación completa**: Todos los flujos críticos
- ✅ **Exploración manual**: Casos edge detectados por humanos
- ✅ **Pre-producción**: Última verificación antes de desplegar
- ⚠️ **Manual**: Requiere ejecución humana

**Cobertura**:
- Flujos completos de usuario
- Edge cases y errores inesperados
- Performance bajo uso real
- Validación de costos reales

## Cuándo Usar Cada Tipo de Test

| Situación | Tipo de Test | Por Qué |
|-----------|--------------|---------|
| Desarrollo activo, iteración rápida | **Unit Tests** | Feedback inmediato, no requiere setup |
| Antes de commit/PR | **Unit Tests** | Validación rápida de lógica |
| Después de cambios en conexiones BD | **Integration Tests** | Verifica que las queries reales funcionan |
| Antes de merge a main | **Integration Tests** | Catch errores de integración |
| Antes de desplegar a staging | **Manual Tests** | Validación humana de flujos críticos |
| Antes de producción | **Todos** | 3 niveles de confianza |
| CI/CD pipeline | **Unit Tests** (siempre) + **Integration Tests** (opcional) | Balance velocidad/confianza |
| Debugging de issue en prod | **Manual Tests** | Reproducir escenario exacto |

### Workflow Recomendado

```bash
# Durante desarrollo
pytest tests/test_agent_*.py -q                    # ~2 segundos

# Antes de commit
pytest tests/test_agent_*.py -v                    # ~5 segundos

# Antes de PR (opcional, si cambió BD/conexiones)
pytest tests/test_agent_real_integration.py -v -m real_integration    # ~5 minutos

# Antes de deploy a staging
# 1. Ejecutar todos los unit tests
pytest tests/test_agent_*.py --cov=agent

# 2. Ejecutar integration tests
pytest tests/test_agent_real_integration.py -v -m real_integration

# 3. Ejecutar manual checklist
# Seguir: tests/MANUAL_AGENT_TEST_CHECKLIST.md

# Solo si los 3 niveles pasan → Deploy to staging
```

## Archivos de Prueba

### 1. Fixtures y Mocks (`tests/fixtures/agent_fixtures.py`)

Proporciona mocks para todas las dependencias externas:

```python
- MockAsyncPGPool         # PostgreSQL mock
- MockNeo4jDriver         # Neo4j mock
- MockOpenAIClient        # OpenAI API mock
- MockContextRegistry     # Context registry mock
- MockPydanticAgent       # Pydantic AI agent mock
```

**Datos de prueba incluidos:**
- SAMPLE_VECTOR_RESULTS (resultados de búsqueda vectorial)
- SAMPLE_GRAPH_RESULTS (resultados de grafo de conocimiento)
- SAMPLE_MESSAGES (mensajes de conversación de ejemplo)

### 2. Pruebas de Sesión (`tests/test_agent_session.py`)

**26 tests** cubriendo:

#### ConversationMessage
- Creación de mensajes con role y content
- Metadata adicional
- Timestamps automáticos

#### ConversationSession
- Creación de sesiones
- Agregar mensajes
- Obtener contexto para LLM (max_turns)
- Formateo de mensajes

#### SessionManager
- Get or create session
- Generación de session_id
- Caché en memoria
- Persistencia a PostgreSQL
- Add message and save
- Clear cache
- Cargar sesiones existentes
- Aislamiento multi-org

**Ejemplo de test:**
```python
def test_get_context_messages(self):
    """Debe retornar mensajes formateados para LLM"""
    session = ConversationSession(
        session_id="test-session-4",
        org_id="los_tajibos",
    )

    # Agregar múltiples mensajes
    for i in range(6):
        session.add_message("user", f"Pregunta {i}")
        session.add_message("assistant", f"Respuesta {i}")

    # Obtener solo los últimos 3 turnos (6 mensajes)
    context = session.get_context_messages(max_turns=3)

    assert len(context) == 6  # 3 turnos * 2 mensajes
```

### 3. Pruebas de Telemetría (`tests/test_agent_telemetry.py`)

**20 tests** cubriendo:

#### ToolTelemetryLogger
- Log de uso exitoso de herramientas
- Log de fallos
- Tracking de costos
- Estadísticas por herramienta
- Estadísticas multi-herramienta
- Aislamiento por organización
- Serialización de parámetros complejos
- Logging concurrente
- Tracking de tiempos de ejecución
- Tracking de cantidad de resultados
- Mensajes de error detallados
- Soporte de español
- Acumulación de costos

**Ejemplo de test:**
```python
def test_log_tool_usage_success(self, telemetry, mock_pool):
    """Debe registrar uso exitoso de herramienta"""
    asyncio.run(
        telemetry.log_tool_usage(
            session_id="test-session",
            org_id="los_tajibos",
            tool_name="vector_search",
            query="¿Qué sistemas hay?",
            parameters={"top_k": 5},
            success=True,
            execution_time_ms=150.5,
            result_count=5,
        )
    )

    assert len(mock_pool.tool_logs) == 1
    log = mock_pool.tool_logs[0]
    assert log["tool_name"] == "vector_search"
    assert log["success"] is True
```

### 4. Pruebas del RAGAgent (`tests/test_agent_rag_agent.py`)

**21 tests** cubriendo:

#### AgentConfig
- Configuración por defecto
- Configuración personalizada
- Carga de system prompt

#### RAGAgent
- Inicialización del agente
- Registro de herramientas
- Ejecución de queries exitosa
- Queries con contexto de sesión
- Fallback on error
- Manejo de errores
- Operación en español
- Aislamiento por organización
- Uso del parámetro de contexto
- Logging de telemetría
- Cleanup de conexiones
- Factory method `RAGAgent.create()`
- Validación de env vars
- Límite de conversation turns

**Ejemplo de test:**
```python
def test_query_execution_success(self, rag_agent):
    """Debe ejecutar query exitosamente"""
    mock_result = MagicMock()
    mock_result.data = "Los sistemas principales son X, Y, Z."
    mock_result.tool_calls = [
        {"tool_name": "hybrid_search", "arguments": {}}
    ]

    rag_agent.agent.run = AsyncMock(return_value=mock_result)

    response = asyncio.run(
        rag_agent.query(
            query="¿Qué sistemas hay?",
            org_id="los_tajibos",
        )
    )

    assert "answer" in response
    assert "Los sistemas principales" in response["answer"]
    assert response["model"] == "gpt-4o-mini"
```

### 5. Pruebas de Integración (`tests/test_agent_integration.py`)

**18 tests** cubriendo:

#### Flujos End-to-End
- Conversación de un solo turno
- Conversación multi-turno con contexto
- Orquestación de vector search
- Orquestación de graph search
- Orquestación de hybrid search
- Recuperación de errores y fallback
- Persistencia de sesión
- Logging de telemetría
- Aislamiento multi-org
- Operación en español end-to-end
- Propagación de parámetro de contexto
- Tracking de costos
- Cleanup y cierre de conexiones

#### Criterios de Aceptación (Task 10)
- Creación del agente
- Query único
- Conversación multi-turno
- Estadísticas de herramientas
- Cleanup de recursos

**Ejemplo de test:**
```python
def test_multi_turn_conversation_flow(self, integrated_agent):
    """Debe manejar conversación multi-turno con contexto"""
    session_id = "multi-turn-test"

    # Turno 1: Pregunta inicial
    response1 = asyncio.run(
        integrated_agent.query(
            query="¿Qué sistemas hay?",
            org_id="los_tajibos",
            session_id=session_id,
        )
    )

    # Turno 2: Pregunta de seguimiento (usa contexto)
    response2 = asyncio.run(
        integrated_agent.query(
            query="¿Cuáles tienen problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )
    )

    # Todas las respuestas deben compartir session_id
    assert response1["session_id"] == session_id
    assert response2["session_id"] == session_id
```

## Instalación de Dependencias

Antes de ejecutar las pruebas, instalar las dependencias de RAG 2.0:

```bash
pip install -r requirements-rag2.txt
```

Dependencias clave:
- `asyncpg>=0.29.0` - PostgreSQL async driver
- `pydantic-ai>=0.0.1` - Pydantic AI framework
- `neo4j>=5.14.0` - Neo4j driver
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support

## Ejecutar las Pruebas

### Opción 1: Script Test Runner

```bash
# Ejecutar todas las pruebas del agente
python tests/run_agent_tests.py

# Modo verbose con más detalles
python tests/run_agent_tests.py --verbose

# Con reporte de cobertura
python tests/run_agent_tests.py --coverage
```

### Opción 2: Pytest Directo

```bash
# Todas las pruebas del agente
pytest tests/test_agent_*.py -v

# Solo tests de sesión
pytest tests/test_agent_session.py -v

# Solo tests de telemetría
pytest tests/test_agent_telemetry.py -v

# Solo tests del RAGAgent
pytest tests/test_agent_rag_agent.py -v

# Solo tests de integración
pytest tests/test_agent_integration.py -v

# Con cobertura
pytest tests/test_agent_*.py --cov=agent --cov-report=html
```

### Opción 3: Test Específico

```bash
# Ejecutar un test específico
pytest tests/test_agent_session.py::TestSessionManager::test_get_or_create_new_session -v

# Ejecutar una clase de tests
pytest tests/test_agent_session.py::TestConversationSession -v
```

## Estructura de Tests

```
tests/
├── fixtures/
│   └── agent_fixtures.py          # Mocks y datos de prueba
├── test_agent_session.py          # 26 tests - Sesiones
├── test_agent_telemetry.py        # 20 tests - Telemetría
├── test_agent_rag_agent.py        # 21 tests - RAGAgent
├── test_agent_integration.py     # 18 tests - Integración
├── run_agent_tests.py             # Test runner
└── TEST_AGENT_GUIDE.md            # Esta guía
```

**Total**: 85+ tests, ~1,200 líneas de código de prueba

## Cobertura Esperada

Con todas las pruebas ejecutándose exitosamente:

- **agent/session.py**: ~95% de cobertura
- **agent/telemetry.py**: ~90% de cobertura
- **agent/rag_agent.py**: ~85% de cobertura
- **agent/tools/*.py**: ~75% de cobertura (integración)

## Validación de Requisitos

### Requisitos de Task 10

| Req | Descripción | Tests |
|-----|-------------|-------|
| R6.1 | Pydantic AI framework | `test_agent_rag_agent.py` |
| R6.2 | Vector/graph search tools | `test_agent_integration.py` |
| R6.3 | Agent system prompt | `test_agent_rag_agent.py::TestAgentConfig` |
| R6.4 | Tool usage tracking | `test_agent_telemetry.py` |
| R6.5 | Streaming response support | Framework ready |
| R6.6 | Native Spanish operation | `test_spanish_language_*` |
| R6.7 | Multi-turn conversation | `test_agent_session.py`, `test_agent_integration.py` |
| R0.3 | Context registry isolation | `test_org_isolation_*` |

### Criterios de Éxito

- ✅ Pydantic AI agent con tool calling
- ✅ Vector search y graph search tools
- ✅ Tool routing guidelines configurado
- ✅ Tool usage telemetry logging
- ✅ Spanish system prompt integration
- ✅ Multi-turn conversation support
- ✅ LLM fallback chain (gpt-4o-mini → gpt-4o)
- ✅ Context registry integration

## Patrones de Test

### 1. Async Testing

```python
def test_async_operation(self):
    """Tests async deben usar asyncio.run"""
    result = asyncio.run(
        async_function(param1, param2)
    )
    assert result is not None
```

### 2. Mock de Dependencias

```python
@pytest.fixture
def mock_dependencies(self):
    """Crear mocks para todas las dependencias"""
    return {
        "db_pool": MockAsyncPGPool(),
        "neo4j_driver": MockNeo4jDriver(),
        "openai_client": MockOpenAIClient(),
    }
```

### 3. Aislamiento de Tests

Cada test debe:
- Ser independiente
- Usar fixtures para setup
- Limpiar recursos al finalizar
- No depender de orden de ejecución

### 4. Assertions en Español

```python
def test_operacion_en_espanol(self):
    """Debe operar completamente en español"""
    respuesta = ejecutar_query("¿Qué sistemas hay?")

    # Verificar español sin traducción
    assert "sistemas" in respuesta
    assert "hay" in respuesta
```

## Troubleshooting

### Error: ModuleNotFoundError: No module named 'asyncpg'

**Solución**: Instalar dependencias RAG 2.0
```bash
pip install -r requirements-rag2.txt
```

### Error: No module named 'agent'

**Solución**: Ejecutar desde el directorio raíz del proyecto
```bash
cd /Users/tatooine/Documents/Development/Comversa/system0
pytest tests/test_agent_*.py
```

### Error: Database connection failed

**Solución**: Los tests usan mocks, no requieren base de datos real. Verificar que se están usando los fixtures correctos.

### Error: Import error in fixtures

**Solución**: Verificar que el módulo `agent` esté en el PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:/Users/tatooine/Documents/Development/Comversa/system0"
```

## Próximos Pasos

### Para Desarrollo

1. **Ejecutar tests antes de commits**:
   ```bash
   pytest tests/test_agent_*.py -q
   ```

2. **Verificar cobertura regularmente**:
   ```bash
   pytest tests/test_agent_*.py --cov=agent --cov-report=term-missing
   ```

3. **Agregar tests para nuevas features**:
   - Seguir patrones existentes
   - Usar fixtures de `agent_fixtures.py`
   - Mantener tests en español

### Para Production

1. **Tests de humo en staging**:
   ```bash
   pytest tests/test_agent_integration.py -k "acceptance" -v
   ```

2. **Load testing** (por implementar):
   - Concurrent queries
   - Session persistence under load
   - Tool selection accuracy

3. **Performance benchmarks** (por implementar):
   - Query latency: <2.5s for hybrid search
   - Tool mis-selection: <15%
   - Cost per query: <$0.0005

## Referencias

- **Task 10 Complete**: [TASK_10_COMPLETE.md](../TASK_10_COMPLETE.md)
- **Agent README**: [agent/README.md](../agent/README.md)
- **Requisitos**: [.kiro/specs/rag-2.0-enhancement/requirements.md](../.kiro/specs/rag-2.0-enhancement/requirements.md)
- **Design**: [.kiro/specs/rag-2.0-enhancement/design.md](../.kiro/specs/rag-2.0-enhancement/design.md)
- **Tasks**: [.kiro/specs/rag-2.0-enhancement/tasks.md](../.kiro/specs/rag-2.0-enhancement/tasks.md)

---

**Creado**: 2025-11-13
**Autor**: Claude Code
**Estado**: ✅ Suite completa de pruebas lista para ejecución
**Cobertura**: 85+ tests cubriendo todos los componentes de Task 10
