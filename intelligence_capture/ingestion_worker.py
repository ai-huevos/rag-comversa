#!/usr/bin/env python3
"""
Worker de ingesta con modo de consolidación y alertas de backlog.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault("OPENAI_API_KEY", "local-worker-placeholder")

from intelligence_capture.config import DB_PATH, load_consolidation_config  # noqa: E402
from intelligence_capture.consolidation_sync import ConsolidationSync  # noqa: E402
from intelligence_capture.logger import get_logger  # noqa: E402
from intelligence_capture.monitoring import (  # noqa: E402
    BacklogThresholds,
    ConsolidationBacklogMonitor,
)

logger = get_logger("ingestion_worker")


@dataclass
class WorkerConfig:
    mode: str
    consolidation_mode: str
    poll_interval_seconds: int
    batch_size: int
    status_file: Path


@dataclass
class WorkerCycleResult:
    cycle_started_at: str
    processed_events: int
    backlog_entities: int
    backlog_oldest: Optional[str]
    alerts_triggered: bool
    mode: str


class IngestionWorker:
    """
    Orquesta las operaciones de consolidación y reporta métricas operativas.
    """

    def __init__(
        self,
        *,
        backlog_monitor: ConsolidationBacklogMonitor,
        consolidation_sync: ConsolidationSync,
        config: WorkerConfig,
    ) -> None:
        self.backlog_monitor = backlog_monitor
        self.consolidation_sync = consolidation_sync
        self.config = config
        self._full_replay_done = False

    async def run(self) -> None:
        logger.info(
            "Worker iniciado en modo %s (consolidation=%s)",
            self.config.mode,
            self.config.consolidation_mode,
        )
        try:
            while True:
                result = self.run_once()
                self._write_status(result)
                sleep_seconds = self.config.poll_interval_seconds
                if result.processed_events > 0:
                    sleep_seconds = max(1, sleep_seconds // 2)
                await asyncio.sleep(sleep_seconds)
        finally:
            self.consolidation_sync.close()

    def run_once(self) -> WorkerCycleResult:
        metrics = self.backlog_monitor.collect_metrics()
        self.backlog_monitor.persist_report(metrics)

        alert = self.backlog_monitor.should_alert(metrics)
        if alert:
            logger.warning(
                "Backlog elevado: %s entidades sin consolidar (más antiguo: %s)",
                metrics.total_unconsolidated,
                metrics.oldest_entity_timestamp,
            )

        processed = 0
        if self.config.mode == "consolidation":
            processed = self._execute_consolidation_cycle(alert)

        return WorkerCycleResult(
            cycle_started_at=datetime.utcnow().isoformat(),
            processed_events=processed,
            backlog_entities=metrics.total_unconsolidated,
            backlog_oldest=metrics.oldest_entity_timestamp,
            alerts_triggered=alert,
            mode=self.config.consolidation_mode,
        )

    def _execute_consolidation_cycle(self, alert_active: bool) -> int:
        if self.config.consolidation_mode == "dry-run":
            logger.info("Modo dry-run: se omite sync, solo se reportan métricas.")
            return 0

        if self.config.consolidation_mode == "full" and not self._full_replay_done:
            logger.info("Iniciando replay completo de eventos de consolidación.")
            self.consolidation_sync.truncate_shadow_tables()
            self.consolidation_sync.reset_events()
            self._full_replay_done = True

        processed = self.consolidation_sync.sync_pending_events(limit=self.config.batch_size)
        if processed == 0 and alert_active:
            logger.warning("Backlog en alerta pero no se procesaron eventos en este ciclo.")
        else:
            logger.info("Eventos procesados en este ciclo: %s", processed)
        return processed

    def _write_status(self, status: WorkerCycleResult) -> None:
        self.config.status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config.status_file, "w", encoding="utf-8") as handler:
            json.dump(asdict(status), handler, indent=2, ensure_ascii=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Worker de ingesta con soporte de consolidación.")
    parser.add_argument(
        "--mode",
        choices=["consolidation"],
        default="consolidation",
        help="Modo principal del worker (default: consolidation).",
    )
    parser.add_argument(
        "--consolidation-mode",
        choices=["incremental", "full", "dry-run"],
        default="incremental",
        help="Estrategia de sincronización hacia Postgres/Neo4j.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=250,
        help="Eventos por lote al aplicar ConsolidationSync.",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=60,
        help="Segundos de espera entre ciclos.",
    )
    parser.add_argument(
        "--status-file",
        type=str,
        default="reports/ingestion_status.json",
        help="Archivo donde se escribe el estado del último ciclo.",
    )
    parser.add_argument(
        "--max-backlog",
        type=int,
        default=100,
        help="Límite de entidades sin consolidar antes de alertar.",
    )
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=7,
        help="Edad máxima (días) del backlog antes de alertar.",
    )
    parser.add_argument(
        "--graph-batch-size",
        type=int,
        help="Tamaño de lote para merges en Neo4j (opcional).",
    )
    return parser.parse_args()


def build_worker(args: argparse.Namespace) -> IngestionWorker:
    consolidation_conf = load_consolidation_config()
    sync_config = dict(consolidation_conf.get("consolidation_sync", {}))
    sync_config.setdefault("enabled", True)
    if args.graph_batch_size:
        sync_config["graph_batch_size"] = args.graph_batch_size

    backlog_thresholds = BacklogThresholds(
        max_entities=args.max_backlog,
        max_age_days=args.max_age_days,
    )
    backlog_monitor = ConsolidationBacklogMonitor(
        db_path=DB_PATH,
        thresholds=backlog_thresholds,
    )

    status_file = Path(args.status_file)
    worker_config = WorkerConfig(
        mode=args.mode,
        consolidation_mode=args.consolidation_mode,
        poll_interval_seconds=args.poll_interval,
        batch_size=args.batch_size,
        status_file=status_file,
    )

    consolidation_sync = ConsolidationSync(sqlite_db=None, config=sync_config)

    return IngestionWorker(
        backlog_monitor=backlog_monitor,
        consolidation_sync=consolidation_sync,
        config=worker_config,
    )


def main() -> None:
    args = parse_args()
    worker = build_worker(args)
    asyncio.run(worker.run())


if __name__ == "__main__":
    main()
