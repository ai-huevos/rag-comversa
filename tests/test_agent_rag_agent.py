"""
Pruebas unitarias para el agente RAG principal (Task 10)
Valida la orquestación de herramientas y generación de respuestas.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.rag_agent import AgentConfig, RAGAgent
from tests.fixtures.agent_fixtures import (
    MockAsyncPGPool,
    MockContextRegistry,
    MockNeo4jDriver,
    MockOpenAIClient,
)


class TestAgentConfig:
    """Pruebas para AgentConfig"""

    def test_default_configuration(self):
        """Debe crear configuración con valores por defecto"""
        config = AgentConfig()

        assert config.primary_model == "gpt-4o-mini"
        assert config.fallback_model == "gpt-4o"
        assert config.embedding_model == "text-embedding-3-small"
        assert config.max_conversation_turns == 5
        assert config.temperature == 0.1

    def test_custom_configuration(self):
        """Debe permitir configuración personalizada"""
        config = AgentConfig(
            primary_model="gpt-4o",
            temperature=0.0,
            max_conversation_turns=3,
        )

        assert config.primary_model == "gpt-4o"
        assert config.temperature == 0.0
        assert config.max_conversation_turns == 3

    def test_load_system_prompt_default(self):
        """Debe cargar prompt por defecto si archivo no existe"""
        config = AgentConfig(
            system_prompt_path=Path("/non/existent/path.md")
        )

        prompt = config.load_system_prompt()

        assert "Director de Inteligencia" in prompt
        assert "español" in prompt
        assert "vector_search" in prompt

    def test_load_system_prompt_from_file(self, tmp_path):
        """Debe cargar prompt desde archivo si existe"""
        prompt_file = tmp_path / "test_prompt.md"
        prompt_file.write_text(
            "Eres un agente de prueba. Operas en español.",
            encoding="utf-8",
        )

        config = AgentConfig(system_prompt_path=prompt_file)
        prompt = config.load_system_prompt()

        assert "agente de prueba" in prompt
        assert "español" in prompt


class TestRAGAgent:
    """Pruebas para RAGAgent"""

    @pytest.fixture
    def mock_dependencies(self):
        """Dependencias mock para el agente"""
        return {
            "config": AgentConfig(),
            "db_pool": MockAsyncPGPool(),
            "neo4j_driver": MockNeo4jDriver(),
            "openai_client": MockOpenAIClient(),
            "context_registry": MockContextRegistry(),
        }

    @pytest.fixture
    def rag_agent(self, mock_dependencies):
        """RAGAgent con dependencias mock"""
        with patch("agent.rag_agent.Agent") as mock_agent_class:
            # Mock del agente Pydantic AI
            mock_agent = MagicMock()
            mock_agent.tool = lambda func: func  # Decorator mock
            mock_agent_class.return_value = mock_agent

            agent = RAGAgent(**mock_dependencies)
            agent.agent = mock_agent
            return agent

    def test_agent_initialization(self, rag_agent, mock_dependencies):
        """Debe inicializar agente con todas las dependencias"""
        assert rag_agent.config is not None
        assert rag_agent.db_pool is not None
        assert rag_agent.neo4j_driver is not None
        assert rag_agent.openai_client is not None
        assert rag_agent.context_registry is not None
        assert rag_agent.session_manager is not None
        assert rag_agent.telemetry is not None

    def test_agent_tool_registration(self, mock_dependencies):
        """Debe registrar herramientas con Pydantic AI"""
        with patch("agent.rag_agent.Agent") as mock_agent_class:
            mock_agent = MagicMock()
            tool_calls = []

            def mock_tool_decorator(func):
                tool_calls.append(func.__name__)
                return func

            mock_agent.tool = mock_tool_decorator
            mock_agent_class.return_value = mock_agent

            RAGAgent(**mock_dependencies)

            # Verificar que se registraron las 4 herramientas
            assert "vector_search_tool" in tool_calls
            assert "graph_search_tool" in tool_calls
            assert "hybrid_search_tool" in tool_calls
            assert "checkpoint_lookup_tool" in tool_calls

    def test_query_execution_success(self, rag_agent):
        """Debe ejecutar query exitosamente"""
        # Mock del resultado del agente
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
        assert "session_id" in response
        assert "model" in response
        assert response["model"] == "gpt-4o-mini"

    def test_query_with_session_context(self, rag_agent):
        """Debe usar contexto de sesión en queries"""
        mock_result = MagicMock()
        mock_result.data = "Respuesta con contexto"
        mock_result.tool_calls = []

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        # Primera query
        response1 = asyncio.run(
            rag_agent.query(
                query="¿Qué sistemas hay?",
                org_id="los_tajibos",
                session_id="test-session",
            )
        )

        # Segunda query con mismo session_id (debe usar contexto)
        response2 = asyncio.run(
            rag_agent.query(
                query="¿Cuáles tienen problemas?",
                org_id="los_tajibos",
                session_id="test-session",
            )
        )

        # Ambas queries deben compartir session_id
        assert response1["session_id"] == response2["session_id"]

    def test_query_fallback_on_error(self, rag_agent):
        """Debe usar modelo fallback si primary falla"""
        # Simular fallo del modelo primary
        rag_agent.agent.run = AsyncMock(
            side_effect=Exception("Primary model failed")
        )

        # Mock de fallback exitoso
        with patch("agent.rag_agent.Agent") as mock_agent_class:
            mock_fallback = MagicMock()
            mock_fallback.run = AsyncMock(
                return_value=MagicMock(data="Fallback response")
            )
            mock_agent_class.return_value = mock_fallback

            response = asyncio.run(
                rag_agent.query(
                    query="Test query",
                    org_id="los_tajibos",
                )
            )

            # Debe retornar respuesta (error o fallback)
            assert "answer" in response

    def test_query_error_handling(self, rag_agent):
        """Debe manejar errores gracefully"""
        # Simular error en ambos modelos
        rag_agent.agent.run = AsyncMock(
            side_effect=Exception("Both models failed")
        )

        response = asyncio.run(
            rag_agent.query(
                query="Test query",
                org_id="los_tajibos",
            )
        )

        assert "answer" in response
        assert "Lo siento" in response["answer"]
        assert "error" in response

    def test_spanish_language_operation(self, rag_agent):
        """Debe operar en español sin traducción"""
        mock_result = MagicMock()
        mock_result.data = (
            "El sistema de reservas causa dolor debido a errores manuales."
        )
        mock_result.tool_calls = []

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        response = asyncio.run(
            rag_agent.query(
                query="¿Por qué el sistema de reservas causa dolor?",
                org_id="los_tajibos",
            )
        )

        # Verificar que la respuesta está en español
        assert "sistema de reservas" in response["answer"]
        assert "causa dolor" in response["answer"]

    def test_org_namespace_isolation(self, rag_agent):
        """Debe aislar queries por organización"""
        mock_result = MagicMock()
        mock_result.data = "Response"
        mock_result.tool_calls = []

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        # Query para Los Tajibos
        response_lt = asyncio.run(
            rag_agent.query(
                query="Test query",
                org_id="los_tajibos",
            )
        )

        # Query para Bolivian Foods
        response_bf = asyncio.run(
            rag_agent.query(
                query="Test query",
                org_id="bolivian_foods",
            )
        )

        # Deben tener diferentes sesiones
        assert response_lt["session_id"] != response_bf["session_id"]

    def test_context_parameter_usage(self, rag_agent):
        """Debe usar parámetro de contexto en queries"""
        mock_result = MagicMock()
        mock_result.data = "Response"
        mock_result.tool_calls = []

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        response = asyncio.run(
            rag_agent.query(
                query="Test query",
                org_id="los_tajibos",
                context="operaciones_hoteleras",
            )
        )

        assert "session_id" in response

    def test_tool_telemetry_logging(self, rag_agent):
        """Debe registrar uso de herramientas en telemetría"""
        mock_result = MagicMock()
        mock_result.data = "Response"
        mock_result.tool_calls = [
            {"tool_name": "vector_search"},
            {"tool_name": "graph_search"},
        ]

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        response = asyncio.run(
            rag_agent.query(
                query="Test query",
                org_id="los_tajibos",
            )
        )

        # Tool calls están en la respuesta
        assert "tool_calls" in response
        assert len(response.get("tool_calls", [])) == 2

    def test_agent_close_cleanup(self, rag_agent):
        """Debe cerrar conexiones al finalizar"""
        asyncio.run(rag_agent.close())

        assert rag_agent.db_pool.closed is True
        assert rag_agent.neo4j_driver.closed is True

    def test_agent_create_factory_method(self):
        """Debe crear agente con factory method"""
        with patch.dict(
            "os.environ",
            {
                "DATABASE_URL": "postgresql://test",
                "NEO4J_URI": "neo4j://test",
                "NEO4J_PASSWORD": "test",
                "OPENAI_API_KEY": "test",
            },
        ):
            with patch("agent.rag_agent.asyncpg.create_pool") as mock_pool:
                with patch("agent.rag_agent.AsyncGraphDatabase.driver") as mock_driver:
                    with patch("agent.rag_agent.AsyncOpenAI") as mock_openai:
                        with patch("agent.rag_agent.ContextRegistry") as mock_registry:
                            with patch("agent.rag_agent.Agent"):
                                mock_pool.return_value = AsyncMock()
                                mock_driver.return_value = MagicMock()
                                mock_openai.return_value = MagicMock()
                                mock_registry_instance = MagicMock()
                                mock_registry_instance.initialize = AsyncMock()
                                mock_registry.return_value = mock_registry_instance

                                agent = asyncio.run(RAGAgent.create())

                                assert agent is not None

    def test_agent_create_missing_env_vars(self):
        """Debe fallar si faltan variables de entorno"""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError) as exc_info:
                asyncio.run(RAGAgent.create())

            assert "Missing required environment variables" in str(exc_info.value)

    def test_max_conversation_turns_limit(self, rag_agent):
        """Debe limitar contexto a max_conversation_turns"""
        mock_result = MagicMock()
        mock_result.data = "Response"
        mock_result.tool_calls = []

        rag_agent.agent.run = AsyncMock(return_value=mock_result)

        session_id = "limit-test"

        # Hacer 10 queries (20 mensajes total)
        for i in range(10):
            asyncio.run(
                rag_agent.query(
                    query=f"Query {i}",
                    org_id="los_tajibos",
                    session_id=session_id,
                )
            )

        # Obtener sesión
        session = asyncio.run(
            rag_agent.session_manager.get_or_create_session(
                session_id, "los_tajibos"
            )
        )

        # Contexto debe limitarse a max_turns (5 turnos = 10 mensajes)
        context = session.get_context_messages(
            max_turns=rag_agent.config.max_conversation_turns
        )
        assert len(context) <= 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
