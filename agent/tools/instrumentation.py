"""
Retrieval instrumentation helpers for evaluation metrics (Task 11).
Provides reusable hooks that tools can call to emit latency/result stats.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, Optional

logger = logging.getLogger(__name__)

InstrumentationHook = Callable[[str, Dict[str, Any]], Awaitable[None]]


class RetrievalInstrumentation:
    """
    Lightweight instrumentation writer that records retrieval metrics
    to JSONL files under `reports/retrieval_metrics/{date}.jsonl`.
    """

    def __init__(self, reports_dir: Optional[Path] = None):
        """
        Initialize instrumentation writer.

        Args:
            reports_dir: Optional base directory for metrics.
        """
        if reports_dir is None:
            reports_dir = (
                Path(__file__).resolve().parents[2] / "reports" / "retrieval_metrics"
            )

        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def emit(self, tool_name: str, payload: Dict[str, Any]) -> None:
        """
        Persist instrumentation payload to JSONL file asynchronously.

        Args:
            tool_name: Name of retrieval tool.
            payload: Metrics payload (latency, cache hit, etc.).
        """
        timestamp = datetime.utcnow().isoformat()
        record = {
            "tool": tool_name,
            "timestamp": timestamp,
            **payload,
        }

        file_path = self.reports_dir / f"{timestamp[:10]}.jsonl"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            self._write_jsonl,
            file_path,
            record,
        )

    @staticmethod
    def _write_jsonl(file_path: Path, record: Dict[str, Any]) -> None:
        """Write record to JSONL file (sync helper executed in executor)."""
        try:
            with open(file_path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except Exception as exc:
            logger.warning(f"No se pudo escribir métrica de retrieval: {exc}")


async def call_instrumentation_hook(
    hook: Optional[InstrumentationHook],
    tool_name: str,
    payload: Dict[str, Any],
) -> None:
    """
    Utility to invoke instrumentation hook if provided.

    Args:
        hook: Callable compatible with InstrumentationHook.
        tool_name: Tool being instrumented.
        payload: Metrics payload.
    """
    if hook is None:
        return

    try:
        await hook(tool_name, payload)
    except Exception as exc:
        logger.warning(f"Error emitiendo métricas de {tool_name}: {exc}")
