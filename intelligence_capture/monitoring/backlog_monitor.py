"""
Monitoreo de backlog para entidades no consolidadas en SQLite.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

from intelligence_capture.logger import get_logger

logger = get_logger(__name__)


@dataclass
class BacklogThresholds:
    """
    Límites operativos para disparar alertas del backlog.
    """

    max_entities: int = 100
    max_age_days: int = 7
    processing_rate_per_minute: float = 20.0


@dataclass
class BacklogMetrics:
    """
    Métricas calculadas por el monitor de backlog.
    """

    total_unconsolidated: int
    oldest_entity_timestamp: Optional[str]
    estimated_minutes: float
    per_entity_counts: Dict[str, int] = field(default_factory=dict)


class ConsolidationBacklogMonitor:
    """
    Calcula el backlog de consolidación revisando tablas SQLite con is_consolidated=0.
    """

    def __init__(
        self,
        db_path: Path,
        thresholds: Optional[BacklogThresholds] = None,
        report_path: Optional[Path] = None,
    ) -> None:
        self.db_path = Path(db_path)
        self.thresholds = thresholds or BacklogThresholds()
        self.report_path = report_path or Path("reports/consolidation_backlog.json")
        self._entity_tables = [
            "pain_points",
            "processes",
            "systems",
            "kpis",
            "automation_candidates",
            "inefficiencies",
            "communication_channels",
            "decision_points",
            "data_flows",
            "temporal_patterns",
            "failure_modes",
            "team_structures",
            "knowledge_gaps",
            "success_patterns",
            "budget_constraints",
            "external_dependencies",
        ]
        self._column_cache: Dict[str, bool] = {}

    def collect_metrics(self) -> BacklogMetrics:
        """
        Recorre las tablas soportadas y agrega métricas globales.
        """
        if not self.db_path.exists():
            logger.warning("La base SQLite no existe: %s", self.db_path)
            return BacklogMetrics(0, None, 0.0, {})

        per_entity: Dict[str, int] = {}
        total = 0
        oldest: Optional[str] = None

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            for table in self._entity_tables:
                if not self._table_has_column(conn, table, "is_consolidated"):
                    continue
                counts = conn.execute(
                    f"""
                    SELECT COUNT(*) AS total,
                           MIN(created_at) AS oldest_row
                      FROM {table}
                     WHERE COALESCE(is_consolidated, 0) = 0
                    """
                ).fetchone()

                table_total = int(counts["total"] or 0)
                per_entity[table] = table_total
                total += table_total

                table_oldest = counts["oldest_row"]
                if table_oldest and (oldest is None or table_oldest < oldest):
                    oldest = table_oldest
        finally:
            conn.close()

        estimated_minutes = 0.0
        if self.thresholds.processing_rate_per_minute > 0:
            estimated_minutes = round(
                total / self.thresholds.processing_rate_per_minute, 2
            )

        normalized_oldest = self._normalize_sqlite_timestamp(oldest) if oldest else None
        return BacklogMetrics(
            total_unconsolidated=total,
            oldest_entity_timestamp=normalized_oldest,
            estimated_minutes=estimated_minutes,
            per_entity_counts=per_entity,
        )

    def should_alert(self, metrics: BacklogMetrics) -> bool:
        """
        Determina si se deben disparar alertas basadas en los thresholds.
        """
        if metrics.total_unconsolidated >= self.thresholds.max_entities:
            return True
        if metrics.oldest_entity_timestamp:
            oldest_dt = self._parse_timestamp(metrics.oldest_entity_timestamp)
            if oldest_dt and datetime.utcnow() - oldest_dt > timedelta(days=self.thresholds.max_age_days):
                return True
        return False

    def persist_report(self, metrics: BacklogMetrics) -> None:
        """
        Escribe el último snapshot de backlog.
        """
        self.report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.report_path, "w", encoding="utf-8") as handler:
            json.dump(asdict(metrics), handler, indent=2, ensure_ascii=False)

    def _table_has_column(
        self,
        conn: sqlite3.Connection,
        table: str,
        column: str,
    ) -> bool:
        cache_key = f"{table}:{column}"
        if cache_key in self._column_cache:
            return self._column_cache[cache_key]

        cursor = conn.execute(f"PRAGMA table_info({table})")
        columns = {row["name"] for row in cursor.fetchall()}
        has_column = column in columns
        self._column_cache[cache_key] = has_column
        if not has_column:
            logger.debug("La tabla %s no expone la columna %s; se omitirá del backlog.", table, column)
        return has_column

    @staticmethod
    def _normalize_sqlite_timestamp(value: str) -> str:
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.isoformat()
        except ValueError:
            return value

    @staticmethod
    def _parse_timestamp(value: str) -> Optional[datetime]:
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None
