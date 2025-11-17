"""
Fixtures para pruebas del agente RAG (Task 10)
Proporciona mocks y datos de prueba para testing sin dependencias externas.
"""
from __future__ import annotations

import asyncio
from datetime import datetime
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from uuid import uuid4


class MockAsyncPGPool:
    """Mock del pool de conexiones PostgreSQL"""

    def __init__(self):
        self.sessions = {}
        self.tool_logs = []
        self.closed = False

    def acquire(self):
        return MockAsyncPGConnection(self)

    async def close(self):
        self.closed = True


class MockAsyncPGConnection:
    """Mock de conexión PostgreSQL"""

    def __init__(self, pool):
        self.pool = pool

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def fetchrow(self, query: str, *args):
        """Mock fetchrow para cargar sesiones"""
        if "chat_sessions" in query and args:
            session_id = args[0]
            return self.pool.sessions.get(session_id)
        return None

    async def execute(self, query: str, *args):
        """Mock execute para guardar sesiones y logs"""
        if "chat_sessions" in query and args:
            session_id = args[0]
            self.pool.sessions[session_id] = {
                "session_id": session_id,
                "org_id": args[1],
                "context": args[2],
                "messages": args[3] if len(args) > 3 else [],
                "created_at": args[4] if len(args) > 4 else datetime.now(),
                "updated_at": args[5] if len(args) > 5 else datetime.now(),
                "metadata": args[6] if len(args) > 6 else {},
            }
        elif "tool_usage_logs" in query:
            self.pool.tool_logs.append({
                "session_id": args[0] if args else None,
                "org_id": args[1] if len(args) > 1 else None,
                "tool_name": args[2] if len(args) > 2 else None,
                "query": args[3] if len(args) > 3 else None,
                "success": args[5] if len(args) > 5 else True,
            })

    async def fetch(self, query: str, *args):
        """Mock fetch para estadísticas de herramientas"""
        if "tool_usage_logs" in query:
            # Retornar logs filtrados por org
            org_id = args[0] if args else None
            filtered = [log for log in self.pool.tool_logs if log.get("org_id") == org_id]
            return [SimpleNamespace(**log) for log in filtered]
        return []


class MockNeo4jDriver:
    """Mock del driver Neo4j"""

    def __init__(self):
        self.nodes = []
        self.relationships = []
        self.closed = False

    def session(self):
        return MockNeo4jSession(self)

    async def close(self):
        self.closed = True


class MockNeo4jSession:
    """Mock de sesión Neo4j"""

    def __init__(self, driver):
        self.driver = driver

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def run(self, query: str, **params):
        """Mock run para consultas Cypher"""
        return MockNeo4jResult(self.driver)


class MockNeo4jResult:
    """Mock de resultado Neo4j"""

    def __init__(self, driver):
        self.driver = driver

    async def data(self):
        """Retornar datos de prueba"""
        return [
            {
                "node": {
                    "entity_id": "test-entity-1",
                    "entity_type": "system",
                    "name": "Sistema Hotelero",
                    "source_count": 3,
                },
                "relationships": [],
            }
        ]


class MockOpenAIClient:
    """Mock del cliente OpenAI"""

    def __init__(self):
        self.embeddings = MockEmbeddingsAPI()
        self.chat = MockChatAPI()


class MockEmbeddingsAPI:
    """Mock de la API de embeddings"""

    def __init__(self):
        self.calls = []

    async def create(self, *, model: str, input: str | list[str]):
        """Mock create para generar embeddings"""
        inputs = [input] if isinstance(input, str) else input
        self.calls.append({"model": model, "input": inputs})

        # Generar vectores dummy de 1536 dimensiones
        return SimpleNamespace(
            data=[
                SimpleNamespace(embedding=[0.1] * 1536)
                for _ in inputs
            ]
        )


class MockChatAPI:
    """Mock de la API de chat"""

    def __init__(self):
        self.calls = []

    async def completions_create(self, **kwargs):
        """Mock completions.create"""
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        content="Respuesta de prueba en español",
                        role="assistant",
                    )
                )
            ]
        )


class MockContextRegistry:
    """Mock del registro de contexto"""

    def __init__(self):
        self.orgs = {
            "los_tajibos": {"org_id": "los_tajibos", "name": "Hotel Los Tajibos"},
            "bolivian_foods": {"org_id": "bolivian_foods", "name": "Bolivian Foods"},
            "comversa": {"org_id": "comversa", "name": "Comversa"},
        }

    async def initialize(self):
        """Mock initialize"""
        pass

    async def get_context(self, org_id: str):
        """Mock get_context"""
        return self.orgs.get(org_id)


class MockPydanticAgent:
    """Mock del agente Pydantic AI"""

    def __init__(self):
        self.tools = []
        self.calls = []

    def tool(self, func):
        """Decorator mock para registrar herramientas"""
        self.tools.append(func)
        return func

    async def run(self, query: str, **kwargs):
        """Mock run para ejecutar consultas"""
        self.calls.append({"query": query, **kwargs})

        # Simular respuesta con tool calls
        return SimpleNamespace(
            data="Respuesta de prueba en español sobre los sistemas hoteleros.",
            tool_calls=[
                {
                    "tool_name": "hybrid_search",
                    "arguments": {"query": query, "org_id": "los_tajibos"},
                }
            ],
        )


# Datos de prueba
SAMPLE_VECTOR_RESULTS = [
    {
        "chunk_id": str(uuid4()),
        "document_id": str(uuid4()),
        "content": "Los sistemas hoteleros causan varios puntos de dolor.",
        "similarity": 0.89,
        "metadata": {"section": "Operaciones", "page": 5},
    },
    {
        "chunk_id": str(uuid4()),
        "document_id": str(uuid4()),
        "content": "El check-in manual es lento y propenso a errores.",
        "similarity": 0.85,
        "metadata": {"section": "Procesos", "page": 12},
    },
]

SAMPLE_GRAPH_RESULTS = {
    "nodes": [
        {
            "entity_id": "sys-001",
            "entity_type": "system",
            "name": "Sistema de Reservas",
            "source_count": 5,
        },
        {
            "entity_id": "pp-001",
            "entity_type": "pain_point",
            "name": "Check-in Lento",
            "source_count": 3,
        },
    ],
    "relationships": [
        {
            "source": "sys-001",
            "target": "pp-001",
            "type": "CAUSES",
            "weight": 0.8,
        }
    ],
}

SAMPLE_MESSAGES = [
    {
        "role": "user",
        "content": "¿Qué sistemas causan más puntos de dolor?",
        "timestamp": "2025-11-11T10:00:00",
        "metadata": {},
    },
    {
        "role": "assistant",
        "content": "Los principales sistemas que causan dolor son el sistema de reservas y el check-in manual.",
        "timestamp": "2025-11-11T10:00:05",
        "metadata": {"tool_calls": [{"tool_name": "hybrid_search"}]},
    },
]
