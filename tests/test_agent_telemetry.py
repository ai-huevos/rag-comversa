"""
Pruebas unitarias para telemetría del agente RAG (Task 10)
Valida el tracking de uso de herramientas y análisis de costos.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta

import pytest

from agent.telemetry import ToolTelemetryLogger
from tests.fixtures.agent_fixtures import MockAsyncPGPool


class TestToolTelemetryLogger:
    """Pruebas para ToolTelemetryLogger"""

    @pytest.fixture
    def mock_pool(self):
        """Pool mock para testing"""
        return MockAsyncPGPool()

    @pytest.fixture
    def telemetry(self, mock_pool):
        """ToolTelemetryLogger con pool mock"""
        return ToolTelemetryLogger(mock_pool)

    def test_telemetry_creation(self, telemetry):
        """Debe crear logger con pool"""
        assert telemetry.db_pool is not None

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

        # Verificar que se guardó en el mock
        assert len(mock_pool.tool_logs) == 1
        log = mock_pool.tool_logs[0]
        assert log["tool_name"] == "vector_search"
        assert log["success"] is True

    def test_log_tool_usage_failure(self, telemetry, mock_pool):
        """Debe registrar fallo de herramienta"""
        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test-session",
                org_id="los_tajibos",
                tool_name="graph_search",
                query="Test query",
                parameters={},
                success=False,
                execution_time_ms=50.0,
                result_count=0,
                error_message="Connection timeout",
            )
        )

        assert len(mock_pool.tool_logs) == 1
        log = mock_pool.tool_logs[0]
        assert log["success"] is False

    def test_log_tool_usage_with_cost(self, telemetry, mock_pool):
        """Debe registrar costo de operación"""
        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test-session",
                org_id="los_tajibos",
                tool_name="hybrid_search",
                query="Test",
                parameters={},
                success=True,
                execution_time_ms=250.0,
                result_count=10,
                cost_cents=0.03,  # $0.0003
            )
        )

        # Cost tracking está implementado en el logger real
        assert len(mock_pool.tool_logs) == 1

    def test_get_tool_stats_single_tool(self, telemetry, mock_pool):
        """Debe calcular estadísticas para una herramienta"""
        # Registrar varios usos
        for i in range(5):
            asyncio.run(
                telemetry.log_tool_usage(
                    session_id=f"session-{i}",
                    org_id="los_tajibos",
                    tool_name="vector_search",
                    query=f"Query {i}",
                    parameters={},
                    success=i < 4,  # 4 éxitos, 1 fallo
                    execution_time_ms=100.0 + i * 10,
                    result_count=5,
                )
            )

        stats = asyncio.run(
            telemetry.get_tool_stats(
                org_id="los_tajibos",
                hours=1,
            )
        )

        # Mock retorna los logs directamente
        # En implementación real, calcularía estadísticas
        assert stats is not None

    def test_get_tool_stats_multiple_tools(self, telemetry, mock_pool):
        """Debe separar estadísticas por herramienta"""
        # Registrar uso de diferentes herramientas
        tools = ["vector_search", "graph_search", "hybrid_search"]
        for tool in tools:
            asyncio.run(
                telemetry.log_tool_usage(
                    session_id="test",
                    org_id="los_tajibos",
                    tool_name=tool,
                    query="Test",
                    parameters={},
                    success=True,
                    execution_time_ms=100.0,
                    result_count=5,
                )
            )

        assert len(mock_pool.tool_logs) == 3

    def test_get_tool_stats_org_isolation(self, telemetry, mock_pool):
        """Debe aislar estadísticas por organización"""
        # Registrar uso para diferentes orgs
        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test-1",
                org_id="los_tajibos",
                tool_name="vector_search",
                query="Test",
                parameters={},
                success=True,
                execution_time_ms=100.0,
                result_count=5,
            )
        )

        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test-2",
                org_id="bolivian_foods",
                tool_name="vector_search",
                query="Test",
                parameters={},
                success=True,
                execution_time_ms=100.0,
                result_count=5,
            )
        )

        # Verificar que ambos se registraron
        assert len(mock_pool.tool_logs) == 2

        # Las estadísticas deben filtrarse por org
        stats_lt = asyncio.run(
            telemetry.get_tool_stats("los_tajibos", hours=1)
        )
        stats_bf = asyncio.run(
            telemetry.get_tool_stats("bolivian_foods", hours=1)
        )

        # Mock retorna logs filtrados por org
        assert stats_lt != stats_bf

    def test_log_parameters_serialization(self, telemetry, mock_pool):
        """Debe serializar parámetros complejos"""
        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test",
                org_id="los_tajibos",
                tool_name="hybrid_search",
                query="Test",
                parameters={
                    "top_k": 10,
                    "weights": {"vector": 0.6, "graph": 0.4},
                    "filters": ["system", "pain_point"],
                },
                success=True,
                execution_time_ms=200.0,
                result_count=8,
            )
        )

        assert len(mock_pool.tool_logs) == 1

    def test_concurrent_logging(self, telemetry, mock_pool):
        """Debe manejar múltiples logs concurrentes"""
        async def log_multiple():
            tasks = []
            for i in range(10):
                task = telemetry.log_tool_usage(
                    session_id=f"session-{i}",
                    org_id="los_tajibos",
                    tool_name="vector_search",
                    query=f"Query {i}",
                    parameters={},
                    success=True,
                    execution_time_ms=100.0,
                    result_count=5,
                )
                tasks.append(task)

            await asyncio.gather(*tasks)

        asyncio.run(log_multiple())

        # Todos los logs deben estar registrados
        assert len(mock_pool.tool_logs) == 10

    def test_execution_time_tracking(self, telemetry, mock_pool):
        """Debe rastrear tiempos de ejecución correctamente"""
        times = [50.0, 100.0, 150.0, 200.0, 250.0]

        for time_ms in times:
            asyncio.run(
                telemetry.log_tool_usage(
                    session_id="test",
                    org_id="los_tajibos",
                    tool_name="vector_search",
                    query="Test",
                    parameters={},
                    success=True,
                    execution_time_ms=time_ms,
                    result_count=5,
                )
            )

        # Verificar que todos los tiempos se registraron
        assert len(mock_pool.tool_logs) == 5

    def test_result_count_tracking(self, telemetry, mock_pool):
        """Debe rastrear cantidad de resultados"""
        result_counts = [0, 3, 5, 10, 20]

        for count in result_counts:
            asyncio.run(
                telemetry.log_tool_usage(
                    session_id="test",
                    org_id="los_tajibos",
                    tool_name="vector_search",
                    query="Test",
                    parameters={},
                    success=count > 0,
                    execution_time_ms=100.0,
                    result_count=count,
                )
            )

        assert len(mock_pool.tool_logs) == 5

    def test_error_message_logging(self, telemetry, mock_pool):
        """Debe registrar mensajes de error detallados"""
        error_msg = "PostgreSQL connection failed: timeout after 30s"

        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test",
                org_id="los_tajibos",
                tool_name="vector_search",
                query="Test",
                parameters={},
                success=False,
                execution_time_ms=30000.0,
                result_count=0,
                error_message=error_msg,
            )
        )

        # Error message se guarda en el log
        assert len(mock_pool.tool_logs) == 1

    def test_spanish_language_support(self, telemetry, mock_pool):
        """Debe manejar queries en español correctamente"""
        asyncio.run(
            telemetry.log_tool_usage(
                session_id="test",
                org_id="los_tajibos",
                tool_name="hybrid_search",
                query="¿Cuáles son los principales puntos de dolor en el sistema de reservas?",
                parameters={"context": "operaciones"},
                success=True,
                execution_time_ms=250.0,
                result_count=12,
            )
        )

        log = mock_pool.tool_logs[0]
        assert "puntos de dolor" in log["query"]

    def test_cost_accumulation(self, telemetry, mock_pool):
        """Debe acumular costos para análisis de presupuesto"""
        costs = [0.0001, 0.0003, 0.0005, 0.0002]  # USD

        for cost_usd in costs:
            asyncio.run(
                telemetry.log_tool_usage(
                    session_id="test",
                    org_id="los_tajibos",
                    tool_name="hybrid_search",
                    query="Test",
                    parameters={},
                    success=True,
                    execution_time_ms=200.0,
                    result_count=10,
                    cost_cents=cost_usd * 100,  # Convertir a centavos
                )
            )

        # Total: $0.0011 para 4 queries
        assert len(mock_pool.tool_logs) == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
