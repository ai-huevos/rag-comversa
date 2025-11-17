# Estrategia Completa de Testing - Agente RAG (Task 10)

**Pregunta**: "Si el agente corre con mocks, ¿cómo sabemos que funciona?"

**Respuesta**: Usamos una estrategia de testing en 3 niveles que combina velocidad, confianza y validación real.

---

## La Pirámide de Testing

```
                        Confianza
                           ↑
                  /\       |
                 /  \      |    Manual Tests
                /____\     |    (~20 min, $0.02-0.05)
               /      \    |    ✅ 100% confianza real
              /________\   |    ❌ Lento, manual
             /          \  |
            /   Unit     \ |    Integration Tests
           /    Tests     \|    (~5 min, $0.005)
          /______________  \    ✅ Valida conexiones reales
         /                  \   ⚠️ Requiere setup
        /____________________\
                               Unit Tests
                               (~2 sec, gratis)
                               ✅ Rápido, automatizable
                               ⚠️ No valida integración

                               ← Velocidad
```

---

## Nivel 1: Unit Tests con Mocks (85+ tests)

### ¿Qué Prueban?

- ✅ **Lógica del agente**: Decisiones, flujos, algoritmos
- ✅ **Manejo de errores**: Fallback, recovery, edge cases
- ✅ **Gestión de estado**: Sesiones, contexto, caché
- ✅ **Interfaces**: Contratos entre componentes

### ¿Qué NO Prueban?

- ❌ Que PostgreSQL esté corriendo
- ❌ Que Neo4j tenga datos correctos
- ❌ Que OpenAI API responda
- ❌ Que las queries SQL sean válidas
- ❌ Que los índices estén optimizados

### Cuándo Usar

```bash
# Durante desarrollo (cada 5 minutos)
pytest tests/test_agent_session.py -q

# Antes de commit
pytest tests/test_agent_*.py -v

# En CI/CD (siempre)
pytest tests/test_agent_*.py --cov=agent
```

### Ejemplo

```python
def test_query_execution_success(self, rag_agent):
    """Debe ejecutar query exitosamente"""
    # Mock del resultado
    mock_result = MagicMock()
    mock_result.data = "Los sistemas principales son X, Y, Z."

    rag_agent.agent.run = AsyncMock(return_value=mock_result)

    # Ejecutar query
    response = asyncio.run(
        rag_agent.query(
            query="¿Qué sistemas hay?",
            org_id="los_tajibos",
        )
    )

    # ✅ Prueba que la LÓGICA funciona
    # ❌ NO prueba que PostgreSQL funciona
    assert "answer" in response
    assert response["model"] == "gpt-4o-mini"
```

**Valor**: Feedback instantáneo sobre lógica del código.

---

## Nivel 2: Integration Tests con Deps Reales (10+ tests)

### ¿Qué Prueban?

- ✅ **Conexiones reales**: PostgreSQL + Neo4j + OpenAI conectan
- ✅ **Queries funcionan**: SQL y Cypher se ejecutan correctamente
- ✅ **Datos persisten**: Sesiones y telemetría se guardan
- ✅ **Costos reales**: Validación de gasto por query
- ✅ **Latencia real**: Performance con datos reales

### ¿Qué NO Prueban?

- ❌ Exploración manual de edge cases
- ❌ UX de conversaciones largas
- ❌ Calidad de respuestas (subjetivo)
- ❌ Comportamiento bajo carga extrema

### Cuándo Usar

```bash
# Después de cambios en BD
pytest tests/test_agent_real_integration.py -v -m real_integration

# Antes de PR (si cambió conexiones)
pytest tests/test_agent_real_integration.py -v -m real_integration

# Antes de deploy a staging
pytest tests/test_agent_real_integration.py -v -m real_integration
```

### Ejemplo

```python
@pytest.mark.asyncio
async def test_database_connection_works(self, real_agent):
    """Debe conectarse a PostgreSQL exitosamente"""
    # ✅ Conexión REAL a PostgreSQL
    async with real_agent.db_pool.acquire() as conn:
        result = await conn.fetchval("SELECT 1")
        assert result == 1

    # ✅ Prueba que PostgreSQL está corriendo
    # ✅ Prueba que las credenciales son correctas
    # ✅ Prueba que pgvector está instalado
```

**Costo**: ~$0.005 (0.5 centavos) por ejecución completa.

**Valor**: Confianza de que las conexiones reales funcionan.

---

## Nivel 3: Manual Tests (Checklist de 20 min)

### ¿Qué Prueban?

- ✅ **Flujos completos de usuario**: Conversaciones naturales
- ✅ **Edge cases**: Casos que los tests automáticos no cubren
- ✅ **UX real**: Calidad de respuestas, coherencia
- ✅ **Performance**: Latencia percibida por usuario
- ✅ **Costos reales**: Validación de budget

### ¿Qué NO Prueban?

- ❌ Regresiones automáticas (muy lento)
- ❌ Edge cases exhaustivos (tomaría días)

### Cuándo Usar

```bash
# Antes de deploy a staging
# Seguir: tests/MANUAL_AGENT_TEST_CHECKLIST.md

# Antes de deploy a production
# Seguir: tests/MANUAL_AGENT_TEST_CHECKLIST.md

# Después de bug crítico en prod
# Reproducir escenario exacto manualmente
```

### Ejemplo

```markdown
### ✅ 3.2. Turno 2: Pregunta de Seguimiento

Ejecutar:
```python
response2 = await agent.query(
    query="¿Cuáles de esos tienen problemas?",
    org_id="los_tajibos",
    session_id=session_id,
)
```

**Verificar**:
- [ ] Usa contexto del turno anterior
- [ ] No pide que se repita información
- [ ] Responde específicamente sobre problemas
- [ ] Session ID es el mismo
```

**Costo**: ~$0.02-0.05 USD (2-5 centavos) por checklist completo.

**Valor**: Última validación antes de producción.

---

## Comparación de Estrategias

| Aspecto | Unit Tests | Integration Tests | Manual Tests |
|---------|------------|-------------------|--------------|
| **Tiempo** | ~2 segundos | ~5 minutos | ~20 minutos |
| **Costo** | Gratis | ~$0.005 | ~$0.02-0.05 |
| **Setup** | Ninguno | PostgreSQL + Neo4j + OpenAI | PostgreSQL + Neo4j + OpenAI |
| **Automatización** | 100% | 95% | 0% |
| **Confianza** | 60% | 85% | 100% |
| **Cobertura** | Lógica | Integración | End-to-end |
| **Feedback** | Instantáneo | 5 min | 20 min |
| **CI/CD** | Siempre | Opcional | No |
| **Regresiones** | Detecta | Detecta | No práctico |

---

## Workflow Recomendado

### Durante Desarrollo (Iteración Rápida)

```bash
# Cada 5-10 minutos mientras codificas
pytest tests/test_agent_session.py -q  # Solo el archivo que estás editando
```

**Beneficio**: Feedback inmediato sin esperar.

### Antes de Commit

```bash
# Antes de git commit
pytest tests/test_agent_*.py -v
```

**Beneficio**: Asegura que no rompiste nada.

### Antes de Pull Request

```bash
# Si cambiaste lógica de conexiones o queries
pytest tests/test_agent_real_integration.py -v -m real_integration
```

**Beneficio**: Valida que tus cambios funcionan con BD reales.

### Antes de Deploy a Staging

```bash
# 1. Unit tests con cobertura
pytest tests/test_agent_*.py --cov=agent --cov-report=html

# 2. Integration tests
pytest tests/test_agent_real_integration.py -v -m real_integration

# 3. Manual checklist
# Ejecutar: tests/MANUAL_AGENT_TEST_CHECKLIST.md

# Solo si los 3 niveles pasan ✅ → Deploy
```

**Beneficio**: Máxima confianza antes de staging.

### Antes de Deploy a Production

```bash
# Mismos 3 niveles + validación de stakeholders
# + Load testing (si es primera vez en prod)
```

---

## ¿Por Qué Necesitamos los 3 Niveles?

### Solo Unit Tests (❌ No Suficiente)

```python
# Test pasa ✅
mock_pool.execute.return_value = "OK"
response = agent.query("test")
assert response["answer"]

# Pero en producción:
# ❌ PostgreSQL no está corriendo
# ❌ Tabla chat_sessions no existe
# ❌ SQL query tiene un typo
# → El agente crashea
```

**Problema**: Mocks ocultan errores de integración.

### Solo Integration Tests (❌ No Práctico)

```python
# Test requiere:
# - PostgreSQL corriendo ⏰
# - Neo4j corriendo ⏰
# - OpenAI API key válida 💰
# - Datos de prueba cargados ⏰
# → Toma 5 minutos cada vez

# Durante desarrollo:
# - Editas código
# - Esperas 5 minutos
# - Test falla
# - Editas código
# - Esperas 5 minutos...
# → Muy lento para iterar
```

**Problema**: Demasiado lento para desarrollo iterativo.

### Solo Manual Tests (❌ No Escalable)

```
# Cada vez que cambias una línea:
# 1. Iniciar agente ⏰
# 2. Ejecutar 8 fases del checklist ⏰
# 3. Registrar resultados manualmente ⏰
# → 20 minutos cada vez

# Después de 10 cambios pequeños:
# → 3+ horas de testing manual
# → Errores por fatiga humana
# → No detecta regresiones automáticamente
```

**Problema**: No escala para desarrollo continuo.

### Los 3 Niveles Juntos (✅ Balance Óptimo)

```
Desarrollo:
├─ Unit tests (2 sec) → Feedback instantáneo
├─ Integration tests (5 min) → Valida antes de PR
└─ Manual tests (20 min) → Valida antes de deploy

Resultado:
✅ Desarrollo rápido
✅ Confianza en integraciones
✅ Validación final humana
✅ Costo razonable (~$0.10/día desarrollo)
```

---

## Resumen Ejecutivo

### ¿Cómo Sabemos que el Agente Funciona?

**3 niveles de validación:**

1. **Unit Tests** → Prueban que la **lógica** es correcta
2. **Integration Tests** → Prueban que las **conexiones** funcionan
3. **Manual Tests** → Prueban que la **experiencia** es buena

### ¿Cuál Usar?

- **Siempre**: Unit tests (rápido, automatizable)
- **Cambios en BD**: Integration tests (valida queries reales)
- **Antes de producción**: Manual tests (validación final)

### Quick Start

1. **Validar que funciona ahora** (5 min):
   ```bash
   python3 -m agent.example
   ```

2. **Ejecutar unit tests** (2 sec):
   ```bash
   pytest tests/test_agent_*.py -q
   ```

3. **Ejecutar integration tests** (5 min, ~$0.005):
   ```bash
   pytest tests/test_agent_real_integration.py -v -m real_integration
   ```

4. **Manual checklist** (20 min, ~$0.03):
   ```bash
   # Seguir: tests/MANUAL_AGENT_TEST_CHECKLIST.md
   ```

---

## Archivos de Referencia

| Archivo | Descripción | Cuándo Usar |
|---------|-------------|-------------|
| [agent/QUICK_START.md](../agent/QUICK_START.md) | Ejecutar agente con conexiones reales | Primera vez |
| [tests/TEST_AGENT_GUIDE.md](TEST_AGENT_GUIDE.md) | Guía completa de testing | Desarrollo |
| [tests/test_agent_*.py](.) | Unit tests con mocks | Siempre |
| [tests/test_agent_real_integration.py](test_agent_real_integration.py) | Integration tests reales | Antes de PR |
| [tests/MANUAL_AGENT_TEST_CHECKLIST.md](MANUAL_AGENT_TEST_CHECKLIST.md) | Checklist de validación manual | Antes de deploy |
| [TASK_10_COMPLETE.md](../TASK_10_COMPLETE.md) | Documentación de implementación | Referencia |

---

**Conclusión**: Los mocks son rápidos y confiables para **lógica**, pero necesitamos integration tests y manual testing para **validar conexiones reales** y **experiencia de usuario**. Los 3 niveles juntos nos dan **máxima confianza a mínimo costo**.
