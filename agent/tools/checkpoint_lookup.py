"""
Checkpoint Lookup Tool for governance and compliance
Retrieves approved checkpoints from reports/checkpoints/ for model review
"""
import logging
import json
import time
from pathlib import Path
from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

CheckpointStage = Literal["ingestion", "ocr", "consolidation", "retrieval", "agent"]


@dataclass
class CheckpointMetadata:
    """Metadata for a checkpoint bundle"""
    checkpoint_id: str
    stage: CheckpointStage
    org_id: str
    timestamp: datetime
    status: str  # "approved", "pending", "rejected"
    reviewer: Optional[str]
    metrics: Dict[str, Any]
    artifacts: List[str]
    notes: Optional[str] = None


@dataclass
class CheckpointLookupResponse:
    """Response from checkpoint lookup"""
    checkpoints: List[CheckpointMetadata]
    stage: CheckpointStage
    org_id: str
    latest_checkpoint: Optional[CheckpointMetadata]
    total_found: int
    execution_time_ms: float


class CheckpointLookupTool:
    """
    Checkpoint lookup tool for governance queries

    Searches reports/checkpoints/{org_id}/{stage}/ for approved model outputs
    to support compliance reviews and Habeas Data requests.

    Per R16: Blocks promotion of new models/prompts/orgs until checkpoints
    receive approval from designated reviewers (Patricia, Samuel, Armando).
    """

    def __init__(self, checkpoints_root: Optional[Path] = None):
        """
        Initialize checkpoint lookup tool

        Args:
            checkpoints_root: Root directory for checkpoints
                             (default: reports/checkpoints)
        """
        if checkpoints_root is None:
            # Assume we're running from project root
            checkpoints_root = Path(__file__).resolve().parent.parent.parent / "reports" / "checkpoints"

        self.checkpoints_root = checkpoints_root
        logger.info(f"Checkpoint lookup initialized: {self.checkpoints_root}")

    async def lookup(
        self,
        stage: CheckpointStage,
        org_id: str,
        limit: int = 10,
    ) -> CheckpointLookupResponse:
        """
        Lookup checkpoints for a specific stage and organization

        Args:
            stage: Checkpoint stage (ingestion, ocr, consolidation, retrieval, agent)
            org_id: Organization identifier
            limit: Max number of checkpoints to return

        Returns:
            CheckpointLookupResponse with checkpoint metadata
        """
        start_time = time.perf_counter()

        logger.info(f"Checkpoint lookup: org={org_id}, stage={stage}, limit={limit}")

        checkpoints: List[CheckpointMetadata] = []

        # Look for checkpoints in reports/checkpoints/{org_id}/{stage}/
        stage_dir = self.checkpoints_root / org_id / stage

        if not stage_dir.exists():
            logger.warning(f"Checkpoint directory not found: {stage_dir}")
            return CheckpointLookupResponse(
                checkpoints=[],
                stage=stage,
                org_id=org_id,
                latest_checkpoint=None,
                total_found=0,
                execution_time_ms=(time.perf_counter() - start_time) * 1000,
            )

        # Find all checkpoint metadata files
        metadata_files = sorted(
            stage_dir.glob("**/metadata.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )[:limit]

        for metadata_file in metadata_files:
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Parse checkpoint metadata
                checkpoint_id = data.get("checkpoint_id", metadata_file.parent.name)
                timestamp_str = data.get("timestamp")
                timestamp = (
                    datetime.fromisoformat(timestamp_str)
                    if timestamp_str
                    else datetime.fromtimestamp(metadata_file.stat().st_mtime)
                )

                # Find associated artifact files
                artifacts = [
                    str(p.relative_to(stage_dir))
                    for p in metadata_file.parent.glob("*")
                    if p.name != "metadata.json"
                ]

                checkpoint = CheckpointMetadata(
                    checkpoint_id=checkpoint_id,
                    stage=stage,
                    org_id=org_id,
                    timestamp=timestamp,
                    status=data.get("status", "pending"),
                    reviewer=data.get("reviewer"),
                    metrics=data.get("metrics", {}),
                    artifacts=artifacts,
                    notes=data.get("notes"),
                )

                checkpoints.append(checkpoint)

            except Exception as exc:
                logger.warning(f"Failed to parse checkpoint {metadata_file}: {exc}")
                continue

        latest_checkpoint = checkpoints[0] if checkpoints else None

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Checkpoint lookup completed: {len(checkpoints)} checkpoints found "
            f"in {execution_time_ms:.1f}ms"
        )

        return CheckpointLookupResponse(
            checkpoints=checkpoints,
            stage=stage,
            org_id=org_id,
            latest_checkpoint=latest_checkpoint,
            total_found=len(checkpoints),
            execution_time_ms=execution_time_ms,
        )


async def checkpoint_lookup(
    stage: CheckpointStage,
    org_id: str,
    limit: int = 10,
    checkpoints_root: Optional[Path] = None,
) -> CheckpointLookupResponse:
    """
    Standalone function interface for checkpoint lookup

    This function is designed to be registered as a Pydantic AI tool.

    Args:
        stage: Checkpoint stage
        org_id: Organization identifier
        limit: Max checkpoints to return
        checkpoints_root: Checkpoints directory (optional)

    Returns:
        CheckpointLookupResponse
    """
    tool = CheckpointLookupTool(checkpoints_root)
    return await tool.lookup(stage, org_id, limit)
