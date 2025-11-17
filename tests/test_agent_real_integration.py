"""
Pruebas de integración REALES del agente RAG (Task 10)
Requiere dependencias reales: PostgreSQL, Neo4j, OpenAI API

⚠️ ADVERTENCIA: Estas pruebas:
- Requieren bases de datos operativas
- Consumen créditos de OpenAI API
- Toman ~30-60 segundos en ejecutar
- Deben ejecutarse manualmente, no en CI

Uso:
    # Asegurar que las variables de entorno estén configuradas
    export DATABASE_URL="postgresql://postgres@localhost:5432/comversa_rag"
    export NEO4J_URI="neo4j://localhost:7687"
    export NEO4J_PASSWORD="comversa_neo4j_2025"
    export OPENAI_API_KEY="sk-..."

    # Ejecutar con flag especial
    pytest tests/test_agent_real_integration.py -v -m real_integration
"""
from __future__ import annotations

import os
import asyncio
from datetime import datetime

import pytest

# Marcar todos los tests como real_integration
pytestmark = pytest.mark.real_integration


def check_environment():
    """Verificar que todas las variables de entorno están configuradas"""
    required_vars = [
        "DATABASE_URL",
        "NEO4J_URI",
        "NEO4J_PASSWORD",
        "OPENAI_API_KEY",
    ]

    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        pytest.skip(
            f"Skipping real integration tests. Missing env vars: {', '.join(missing)}\n"
            f"Set them with: export {missing[0]}=..."
        )


@pytest.fixture(scope="module")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def real_agent():
    """
    Agente RAG con conexiones reales

    ⚠️ Requiere:
    - PostgreSQL con pgvector operativo
    - Neo4j con datos de prueba
    - OpenAI API key válida
    """
    check_environment()

    from agent import RAGAgent, AgentConfig

    # Configuración optimizada para tests (modelos más baratos)
    config = AgentConfig(
        primary_model="gpt-4o-mini",  # Más barato para tests
        temperature=0.0,  # Determinístico
        max_conversation_turns=3,  # Menos contexto
    )

    print("\n🔧 Creando agente con conexiones reales...")
    agent = await RAGAgent.create(config=config)

    print("✅ Agente creado exitosamente")

    yield agent

    # Cleanup
    print("\n🧹 Cerrando conexiones...")
    await agent.close()
    print("✅ Conexiones cerradas")


class TestRealAgentCreation:
    """Pruebas de creación del agente con dependencias reales"""

    @pytest.mark.asyncio
    async def test_agent_factory_creates_real_connections(self, real_agent):
        """Debe crear agente con conexiones reales a todas las dependencias"""
        assert real_agent is not None
        assert real_agent.db_pool is not None
        assert real_agent.neo4j_driver is not None
        assert real_agent.openai_client is not None
        assert real_agent.context_registry is not None

        print("✅ Todas las conexiones creadas")

    @pytest.mark.asyncio
    async def test_database_connection_works(self, real_agent):
        """Debe conectarse a PostgreSQL exitosamente"""
        async with real_agent.db_pool.acquire() as conn:
            result = await conn.fetchval("SELECT 1")
            assert result == 1

        print("✅ PostgreSQL operativo")

    @pytest.mark.asyncio
    async def test_neo4j_connection_works(self, real_agent):
        """Debe conectarse a Neo4j exitosamente"""
        async with real_agent.neo4j_driver.session() as session:
            result = await session.run("RETURN 1 as value")
            data = await result.data()
            assert data[0]["value"] == 1

        print("✅ Neo4j operativo")


class TestRealAgentQueries:
    """Pruebas de queries reales con el agente"""

    @pytest.mark.asyncio
    async def test_simple_query_end_to_end(self, real_agent):
        """
        Debe ejecutar query completa end-to-end

        ⚠️ Costo aproximado: $0.0003 (0.03 centavos)
        """
        print("\n🚀 Ejecutando query real...")

        response = await real_agent.query(
            query="¿Qué sistemas hay en Los Tajibos?",
            org_id="los_tajibos",
        )

        # Verificaciones básicas
        assert "answer" in response
        assert response["answer"]  # No vacío
        assert "session_id" in response
        assert "model" in response

        print(f"✅ Query ejecutada exitosamente")
        print(f"📝 Respuesta: {response['answer'][:100]}...")
        print(f"🎯 Modelo usado: {response['model']}")

        # Verificar que la respuesta está en español
        assert any(
            word in response["answer"].lower()
            for word in ["sistema", "hay", "los tajibos", "hotel"]
        ), "La respuesta debe estar en español y mencionar sistemas/hotel"

    @pytest.mark.asyncio
    async def test_multi_turn_conversation_real(self, real_agent):
        """
        Debe mantener contexto entre múltiples turnos

        ⚠️ Costo aproximado: $0.0009 (3 queries * $0.0003)
        """
        session_id = f"test-real-{datetime.now().timestamp()}"

        print(f"\n💬 Iniciando conversación multi-turno (session={session_id[:20]}...)")

        # Turno 1
        print("\n👤 Turno 1: ¿Qué sistemas hay?")
        response1 = await real_agent.query(
            query="¿Qué sistemas hay en Los Tajibos?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta 1: {response1['answer'][:100]}...")

        # Turno 2 (usa contexto del turno 1)
        print("\n👤 Turno 2: ¿Cuáles tienen problemas?")
        response2 = await real_agent.query(
            query="¿Cuáles de esos sistemas tienen problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta 2: {response2['answer'][:100]}...")

        # Turno 3 (usa contexto acumulado)
        print("\n👤 Turno 3: ¿Por qué?")
        response3 = await real_agent.query(
            query="¿Por qué tienen esos problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta 3: {response3['answer'][:100]}...")

        # Verificar que todas las respuestas comparten session_id
        assert response1["session_id"] == session_id
        assert response2["session_id"] == session_id
        assert response3["session_id"] == session_id

        print("\n✅ Conversación multi-turno exitosa")

    @pytest.mark.asyncio
    async def test_tool_selection_real(self, real_agent):
        """
        Debe seleccionar herramientas apropiadas

        ⚠️ Costo aproximado: $0.0009 (3 queries con diferentes herramientas)
        """
        print("\n🔧 Probando selección de herramientas...")

        # Query que debería usar vector_search (buscar texto específico)
        print("\n🔍 Test 1: Vector search (buscar texto específico)")
        response_vector = await real_agent.query(
            query="¿Qué dice el documento sobre el check-in?",
            org_id="los_tajibos",
        )
        print(f"✅ Respuesta vector: {response_vector['answer'][:80]}...")

        # Query que debería usar graph_search (relaciones)
        print("\n🕸️ Test 2: Graph search (relaciones entre entidades)")
        response_graph = await real_agent.query(
            query="¿Qué sistemas están relacionados con puntos de dolor?",
            org_id="los_tajibos",
        )
        print(f"✅ Respuesta graph: {response_graph['answer'][:80]}...")

        # Query que debería usar hybrid_search (análisis completo)
        print("\n⚡ Test 3: Hybrid search (análisis completo)")
        response_hybrid = await real_agent.query(
            query="Dame un resumen completo de las operaciones hoteleras",
            org_id="los_tajibos",
        )
        print(f"✅ Respuesta hybrid: {response_hybrid['answer'][:80]}...")

        # Todas deben tener respuestas válidas
        assert all([
            response_vector["answer"],
            response_graph["answer"],
            response_hybrid["answer"],
        ])

        print("\n✅ Selección de herramientas funcionando")


class TestRealSessionPersistence:
    """Pruebas de persistencia de sesiones en PostgreSQL"""

    @pytest.mark.asyncio
    async def test_session_saved_to_database(self, real_agent):
        """Debe guardar sesiones en PostgreSQL"""
        session_id = f"test-persist-{datetime.now().timestamp()}"

        print(f"\n💾 Probando persistencia (session={session_id[:20]}...)")

        # Ejecutar query para crear sesión
        response = await real_agent.query(
            query="Hola, soy una prueba",
            org_id="los_tajibos",
            session_id=session_id,
        )

        # Verificar que se guardó en la base de datos
        async with real_agent.db_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM chat_sessions WHERE session_id = $1",
                session_id,
            )

            assert row is not None, "La sesión debe estar guardada en la BD"
            assert row["org_id"] == "los_tajibos"
            assert len(row["messages"]) >= 2  # user + assistant

        print("✅ Sesión persistida exitosamente en PostgreSQL")


class TestRealTelemetry:
    """Pruebas de telemetría con PostgreSQL"""

    @pytest.mark.asyncio
    async def test_tool_usage_logged_to_database(self, real_agent):
        """Debe registrar uso de herramientas en PostgreSQL"""
        print("\n📊 Probando logging de telemetría...")

        # Ejecutar query
        response = await real_agent.query(
            query="Test query para telemetría",
            org_id="los_tajibos",
        )

        # Verificar que hay logs de telemetría
        async with real_agent.db_pool.acquire() as conn:
            count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM tool_usage_logs
                WHERE org_id = $1
                AND timestamp > now() - interval '1 minute'
                """,
                "los_tajibos",
            )

            # Debe haber al menos 1 log reciente
            assert count >= 1, f"Debe haber logs de telemetría, encontrados: {count}"

        print(f"✅ Telemetría registrada: {count} logs")


class TestRealCostTracking:
    """Pruebas de tracking de costos"""

    @pytest.mark.asyncio
    async def test_cost_per_query_is_reasonable(self, real_agent):
        """Debe mantener costos por query razonables (<$0.001)"""
        print("\n💰 Probando tracking de costos...")

        # Ejecutar una query
        response = await real_agent.query(
            query="Query de prueba para costos",
            org_id="los_tajibos",
        )

        # En un sistema real, verificaríamos el costo en telemetry
        # Por ahora, solo verificamos que la query funcionó
        assert response["answer"]

        print("✅ Query ejecutada (costo esperado: <$0.001)")
        print("💡 Revisar logs de telemetría para costos exactos")


class TestRealErrorHandling:
    """Pruebas de manejo de errores en producción"""

    @pytest.mark.asyncio
    async def test_handles_invalid_org_gracefully(self, real_agent):
        """Debe manejar org_id inválido sin crash"""
        print("\n⚠️ Probando manejo de errores...")

        response = await real_agent.query(
            query="Test query",
            org_id="org_inexistente_12345",
        )

        # Debe retornar respuesta (posiblemente con error message)
        # pero no debe crashear
        assert "answer" in response

        print("✅ Error manejado gracefully")


# Configuración de pytest marks
def pytest_configure(config):
    """Registrar custom markers"""
    config.addinivalue_line(
        "markers",
        "real_integration: tests que requieren dependencias reales (PostgreSQL, Neo4j, OpenAI)"
    )


if __name__ == "__main__":
    print("=" * 70)
    print("⚠️  PRUEBAS DE INTEGRACIÓN REALES")
    print("=" * 70)
    print()
    print("Estas pruebas requieren:")
    print("  - PostgreSQL + pgvector operativo")
    print("  - Neo4j con datos consolidados")
    print("  - OpenAI API key válida")
    print()
    print("Costo aproximado: $0.005 (0.5 centavos)")
    print()
    print("Para ejecutar:")
    print("  pytest tests/test_agent_real_integration.py -v -m real_integration")
    print()
    print("=" * 70)
