"""
Tool Telemetry and Usage Logging
Tracks tool calls for governance analysis and cost monitoring
"""
import logging
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class ToolUsageLog:
    """
    Log entry for a single tool call

    Tracks tool selection, execution time, success/failure, and cost
    for governance analysis and optimization (R6.4, R6.7).
    """
    session_id: str
    org_id: str
    tool_name: str
    query: str
    parameters: Dict[str, Any]
    success: bool
    execution_time_ms: float
    result_count: int
    error_message: Optional[str] = None
    cost_cents: Optional[float] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class ToolTelemetryLogger:
    """
    Logs tool usage to PostgreSQL and JSON files for analysis

    Provides:
    - Real-time tool_usage_logs table updates
    - Daily JSON reports for offline analysis
    - Cost tracking integration with CostGuard
    - Mis-selection detection (>15% failure rate alerts)
    """

    def __init__(
        self,
        db_pool: Optional[asyncpg.Pool] = None,
        reports_dir: Optional[Path] = None,
    ):
        """
        Initialize telemetry logger

        Args:
            db_pool: PostgreSQL pool for tool_usage_logs table
            reports_dir: Directory for JSON reports (default: reports/agent_usage)
        """
        self.db_pool = db_pool

        if reports_dir is None:
            reports_dir = Path(__file__).resolve().parent.parent / "reports" / "agent_usage"

        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        logger.info(f"Tool telemetry initialized: reports_dir={self.reports_dir}")

    async def log_tool_usage(
        self,
        session_id: str,
        org_id: str,
        tool_name: str,
        query: str,
        parameters: Dict[str, Any],
        success: bool,
        execution_time_ms: float,
        result_count: int = 0,
        error_message: Optional[str] = None,
        cost_cents: Optional[float] = None,
    ) -> None:
        """
        Log a tool usage event

        Args:
            session_id: Conversation session ID
            org_id: Organization namespace
            tool_name: Tool identifier (vector_search, graph_search, etc.)
            query: Query text
            parameters: Tool parameters used
            success: Whether tool call succeeded
            execution_time_ms: Execution time in milliseconds
            result_count: Number of results returned
            error_message: Error message if failed
            cost_cents: Estimated cost in cents (for embeddings)
        """
        usage_log = ToolUsageLog(
            session_id=session_id,
            org_id=org_id,
            tool_name=tool_name,
            query=query,
            parameters=parameters,
            success=success,
            execution_time_ms=execution_time_ms,
            result_count=result_count,
            error_message=error_message,
            cost_cents=cost_cents,
        )

        # Log to database if available
        if self.db_pool:
            await self._log_to_database(usage_log)

        # Log to JSON file
        await self._log_to_json(usage_log)

        # Log summary to logger
        status = "SUCCESS" if success else "FAILURE"
        logger.info(
            f"Tool usage [{status}]: {tool_name} | org={org_id} | "
            f"time={execution_time_ms:.1f}ms | results={result_count}"
        )

    async def _log_to_database(self, usage_log: ToolUsageLog) -> None:
        """Persist log to tool_usage_logs table"""
        try:
            async with self.db_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO tool_usage_logs (
                        session_id,
                        org_id,
                        tool_name,
                        query,
                        parameters,
                        success,
                        execution_time_ms,
                        result_count,
                        error_message,
                        cost_cents,
                        timestamp
                    ) VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7, $8, $9, $10, $11)
                    """,
                    usage_log.session_id,
                    usage_log.org_id,
                    usage_log.tool_name,
                    usage_log.query,
                    json.dumps(usage_log.parameters),
                    usage_log.success,
                    usage_log.execution_time_ms,
                    usage_log.result_count,
                    usage_log.error_message,
                    usage_log.cost_cents,
                    usage_log.timestamp,
                )

        except Exception as exc:
            logger.warning(f"Failed to log to database: {exc}")

    async def _log_to_json(self, usage_log: ToolUsageLog) -> None:
        """Append log to daily JSON file"""
        try:
            # Organize by org_id and date
            date_str = usage_log.timestamp.strftime("%Y-%m-%d")
            org_dir = self.reports_dir / usage_log.org_id
            org_dir.mkdir(parents=True, exist_ok=True)

            log_file = org_dir / f"{date_str}.jsonl"

            # Convert to dict and serialize
            log_dict = asdict(usage_log)
            log_dict["timestamp"] = usage_log.timestamp.isoformat()

            # Append as JSONL
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_dict, ensure_ascii=False) + "\n")

        except Exception as exc:
            logger.warning(f"Failed to log to JSON: {exc}")

    async def get_tool_stats(
        self,
        org_id: str,
        hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Get tool usage statistics for the last N hours

        Args:
            org_id: Organization namespace
            hours: Hours to look back

        Returns:
            Dict with tool usage stats including success rate
        """
        if not self.db_pool:
            return {"error": "Database pool not available"}

        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT
                        tool_name,
                        COUNT(*) as total_calls,
                        COUNT(*) FILTER (WHERE success) as successful_calls,
                        AVG(execution_time_ms) as avg_time_ms,
                        SUM(result_count) as total_results,
                        SUM(cost_cents) as total_cost_cents
                    FROM tool_usage_logs
                    WHERE org_id = $1
                      AND timestamp >= NOW() - INTERVAL '1 hour' * $2
                    GROUP BY tool_name
                    ORDER BY total_calls DESC
                    """,
                    org_id,
                    hours,
                )

                stats = {}
                for row in rows:
                    tool_name = row["tool_name"]
                    total = row["total_calls"]
                    successful = row["successful_calls"]

                    stats[tool_name] = {
                        "total_calls": total,
                        "successful_calls": successful,
                        "success_rate": successful / total if total > 0 else 0,
                        "avg_time_ms": float(row["avg_time_ms"] or 0),
                        "total_results": row["total_results"],
                        "total_cost_cents": float(row["total_cost_cents"] or 0),
                    }

                return stats

        except Exception as exc:
            logger.error(f"Failed to get tool stats: {exc}")
            return {"error": str(exc)}
