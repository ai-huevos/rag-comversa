"""
Pruebas unitarias para la gestión de sesiones del agente RAG (Task 10)
Valida el manejo de conversaciones multi-turno y persistencia.
"""
from __future__ import annotations

import asyncio
from datetime import datetime

import pytest

from agent.session import (
    ConversationMessage,
    ConversationSession,
    SessionManager,
)
from tests.fixtures.agent_fixtures import MockAsyncPGPool


class TestConversationMessage:
    """Pruebas para ConversationMessage"""

    def test_message_creation(self):
        """Debe crear un mensaje con role y content"""
        msg = ConversationMessage(
            role="user",
            content="¿Qué sistemas hay?",
        )

        assert msg.role == "user"
        assert msg.content == "¿Qué sistemas hay?"
        assert isinstance(msg.timestamp, datetime)
        assert msg.metadata == {}

    def test_message_with_metadata(self):
        """Debe almacenar metadata adicional"""
        msg = ConversationMessage(
            role="assistant",
            content="Respuesta",
            metadata={"tool_calls": ["hybrid_search"]},
        )

        assert msg.metadata["tool_calls"] == ["hybrid_search"]


class TestConversationSession:
    """Pruebas para ConversationSession"""

    def test_session_creation(self):
        """Debe crear una sesión nueva"""
        session = ConversationSession(
            session_id="test-session-1",
            org_id="los_tajibos",
            context="operaciones",
        )

        assert session.session_id == "test-session-1"
        assert session.org_id == "los_tajibos"
        assert session.context == "operaciones"
        assert len(session.messages) == 0

    def test_add_message(self):
        """Debe agregar mensajes a la sesión"""
        session = ConversationSession(
            session_id="test-session-2",
            org_id="los_tajibos",
        )

        session.add_message("user", "Pregunta 1")
        session.add_message("assistant", "Respuesta 1")

        assert len(session.messages) == 2
        assert session.messages[0].role == "user"
        assert session.messages[0].content == "Pregunta 1"
        assert session.messages[1].role == "assistant"

    def test_add_message_updates_timestamp(self):
        """Debe actualizar updated_at al agregar mensajes"""
        session = ConversationSession(
            session_id="test-session-3",
            org_id="los_tajibos",
        )

        created = session.created_at
        session.add_message("user", "Test")

        assert session.updated_at > created

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
        assert context[0]["role"] == "user"
        assert context[0]["content"] == "Pregunta 3"  # Últimos 3 turnos
        assert "timestamp" not in context[0]  # Solo role y content

    def test_get_context_messages_empty_session(self):
        """Debe retornar lista vacía si no hay mensajes"""
        session = ConversationSession(
            session_id="test-session-5",
            org_id="los_tajibos",
        )

        context = session.get_context_messages()
        assert context == []


class TestSessionManager:
    """Pruebas para SessionManager"""

    @pytest.fixture
    def mock_pool(self):
        """Pool mock para testing"""
        return MockAsyncPGPool()

    @pytest.fixture
    def session_manager(self, mock_pool, event_loop):
        """SessionManager con pool mock"""
        # Create SessionManager within event loop context
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        manager = SessionManager(mock_pool)
        return manager

    def test_session_manager_creation(self, session_manager):
        """Debe crear SessionManager con pool"""
        assert session_manager.db_pool is not None
        assert session_manager._memory_cache == {}

    def test_get_or_create_new_session(self, session_manager):
        """Debe crear nueva sesión si no existe"""
        session = asyncio.run(
            session_manager.get_or_create_session(
                session_id="new-session",
                org_id="los_tajibos",
                context="operaciones",
            )
        )

        assert session.session_id == "new-session"
        assert session.org_id == "los_tajibos"
        assert session.context == "operaciones"
        assert len(session.messages) == 0

    def test_get_or_create_generates_session_id(self, session_manager):
        """Debe generar session_id si no se proporciona"""
        session = asyncio.run(
            session_manager.get_or_create_session(
                session_id=None,
                org_id="los_tajibos",
            )
        )

        assert session.session_id is not None
        assert len(session.session_id) > 10  # UUID

    def test_session_caching(self, session_manager):
        """Debe cachear sesiones en memoria"""
        # Primera llamada - crea nueva sesión
        session1 = asyncio.run(
            session_manager.get_or_create_session(
                session_id="cached-session",
                org_id="los_tajibos",
            )
        )

        # Segunda llamada - debe retornar la misma instancia
        session2 = asyncio.run(
            session_manager.get_or_create_session(
                session_id="cached-session",
                org_id="los_tajibos",
            )
        )

        assert session1 is session2
        assert "cached-session" in session_manager._memory_cache

    def test_save_session(self, session_manager, mock_pool):
        """Debe guardar sesión en base de datos"""
        session = ConversationSession(
            session_id="save-test",
            org_id="los_tajibos",
            context="test",
        )
        session.add_message("user", "Test message")

        asyncio.run(session_manager.save_session(session))

        # Verificar que se guardó en el mock
        assert "save-test" in mock_pool.sessions
        assert mock_pool.sessions["save-test"]["org_id"] == "los_tajibos"

    def test_add_message_and_save(self, session_manager, mock_pool):
        """Debe agregar mensaje y guardar automáticamente"""
        session = ConversationSession(
            session_id="add-save-test",
            org_id="los_tajibos",
        )

        asyncio.run(
            session_manager.add_message_and_save(
                session=session,
                role="user",
                content="Test question",
                metadata={"test": True},
            )
        )

        assert len(session.messages) == 1
        assert session.messages[0].content == "Test question"
        assert "add-save-test" in mock_pool.sessions

    def test_clear_cache(self, session_manager):
        """Debe limpiar el caché de memoria"""
        # Crear una sesión (se cachea automáticamente)
        asyncio.run(
            session_manager.get_or_create_session(
                session_id="clear-test",
                org_id="los_tajibos",
            )
        )

        assert "clear-test" in session_manager._memory_cache

        # Limpiar caché
        asyncio.run(session_manager.clear_cache())

        assert session_manager._memory_cache == {}

    def test_load_session_from_database(self, session_manager, mock_pool):
        """Debe cargar sesión existente desde base de datos"""
        # Simular sesión en DB
        mock_pool.sessions["existing-session"] = {
            "session_id": "existing-session",
            "org_id": "los_tajibos",
            "context": "test",
            "messages": [
                {
                    "role": "user",
                    "content": "Old message",
                    "timestamp": datetime.now().isoformat(),
                    "metadata": {},
                }
            ],
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "metadata": {},
        }

        # Cargar sesión
        session = asyncio.run(
            session_manager.get_or_create_session(
                session_id="existing-session",
                org_id="los_tajibos",
            )
        )

        assert session.session_id == "existing-session"
        assert len(session.messages) == 1
        assert session.messages[0].content == "Old message"

    def test_multi_org_isolation(self, session_manager):
        """Debe aislar sesiones por organización"""
        session_lt = asyncio.run(
            session_manager.get_or_create_session(
                session_id="org-test-1",
                org_id="los_tajibos",
            )
        )

        session_bf = asyncio.run(
            session_manager.get_or_create_session(
                session_id="org-test-2",
                org_id="bolivian_foods",
            )
        )

        assert session_lt.org_id == "los_tajibos"
        assert session_bf.org_id == "bolivian_foods"
        assert session_lt.session_id != session_bf.session_id


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
