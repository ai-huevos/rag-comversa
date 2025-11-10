"""
Ingestion Queue Manager
Provides queue-based job management with visibility timeouts and progress tracking

Task 2: Implement Queue-Based Ingestion Backbone
"""
import asyncio
import asyncpg
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"


@dataclass
class IngestionJob:
    """
    Ingestion job metadata

    Attributes:
        job_id: Unique job identifier (UUID)
        org_id: Organization identifier
        document_id: Document identifier (UUID)
        checksum: SHA-256 checksum of source file
        storage_path: Path to document in inbox
        connector_type: Source connector type
        source_format: MIME type/format
        metadata: Additional metadata dict
        status: Job status
        created_at: Job creation timestamp
        started_at: Processing start timestamp
        completed_at: Processing completion timestamp
        error_message: Error message if failed
        retry_count: Number of retry attempts
        visibility_timeout: Visibility timeout (for in-progress jobs)
        worker_id: Worker ID processing the job
    """
    org_id: str
    checksum: str
    storage_path: str
    connector_type: str
    source_format: str
    metadata: Dict[str, Any]
    job_id: Optional[str] = None
    document_id: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    visibility_timeout: Optional[datetime] = None
    worker_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "job_id": self.job_id,
            "org_id": self.org_id,
            "document_id": self.document_id,
            "checksum": self.checksum,
            "storage_path": str(self.storage_path),
            "connector_type": self.connector_type,
            "source_format": self.source_format,
            "metadata": self.metadata,
            "status": self.status.value if isinstance(self.status, JobStatus) else self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "visibility_timeout": self.visibility_timeout.isoformat() if self.visibility_timeout else None,
            "worker_id": self.worker_id
        }


class IngestionQueue:
    """
    Queue manager for document ingestion

    Provides:
    - Enqueue/dequeue with visibility timeouts
    - Job status tracking
    - Resume support via progress file
    - Backlog monitoring
    """

    # Configuration
    DEFAULT_VISIBILITY_TIMEOUT = 600  # 10 minutes
    MAX_RETRIES = 3
    BACKLOG_THRESHOLD_HOURS = 24

    def __init__(
        self,
        db_url: str,
        progress_file: Path = Path("data/ingestion_progress.json")
    ):
        """
        Initialize ingestion queue

        Args:
            db_url: PostgreSQL connection URL
            progress_file: Path to progress tracking file
        """
        self.db_url = db_url
        self.progress_file = progress_file
        self._pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Establish database connection pool"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10,
                timeout=30.0
            )
            logger.info("✓ Ingestion queue connected to PostgreSQL")

    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum for file"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    async def enqueue(
        self,
        org_id: str,
        file_path: Path,
        connector_type: str,
        source_format: str,
        metadata: Dict[str, Any]
    ) -> str:
        """
        Add document to ingestion queue

        Args:
            org_id: Organization identifier
            file_path: Path to document file
            connector_type: Source connector type
            source_format: MIME type/format
            metadata: Additional metadata

        Returns:
            Job ID (UUID)
        """
        await self.connect()

        # Calculate checksum
        checksum = self._calculate_checksum(file_path)

        # Check for duplicate (same checksum)
        async with self._pool.acquire() as conn:
            existing = await conn.fetchrow(
                """
                SELECT job_id, status FROM ingestion_events
                WHERE checksum = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                checksum
            )

            if existing and existing['status'] in ['completed', 'in_progress']:
                logger.warning(
                    f"⚠️  Documento duplicado (checksum: {checksum[:16]}...), "
                    f"status: {existing['status']}"
                )
                return existing['job_id']

            # Insert new job
            job_id = await conn.fetchval(
                """
                INSERT INTO ingestion_events
                    (org_id, checksum, storage_path, connector_type, source_format,
                     metadata, status, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING job_id
                """,
                org_id,
                checksum,
                str(file_path),
                connector_type,
                source_format,
                json.dumps(metadata, ensure_ascii=False),
                JobStatus.PENDING.value,
                datetime.now()
            )

            logger.info(f"✓ Enqueued job {job_id} for {file_path.name}")

            # Update progress file
            await self._update_progress_file({
                "action": "enqueued",
                "job_id": str(job_id),
                "org_id": org_id,
                "file": str(file_path),
                "timestamp": datetime.now().isoformat()
            })

            return str(job_id)

    async def dequeue(
        self,
        worker_id: str,
        visibility_timeout: int = None
    ) -> Optional[IngestionJob]:
        """
        Get next job from queue with visibility timeout

        Args:
            worker_id: Worker identifier
            visibility_timeout: Visibility timeout in seconds (default: 10 min)

        Returns:
            IngestionJob if available, None if queue empty
        """
        await self.connect()

        if visibility_timeout is None:
            visibility_timeout = self.DEFAULT_VISIBILITY_TIMEOUT

        async with self._pool.acquire() as conn:
            # Find next pending job or timed-out job
            now = datetime.now()
            timeout_cutoff = now + timedelta(seconds=visibility_timeout)

            row = await conn.fetchrow(
                """
                UPDATE ingestion_events
                SET
                    status = $1,
                    started_at = $2,
                    visibility_timeout = $3,
                    worker_id = $4
                WHERE job_id = (
                    SELECT job_id FROM ingestion_events
                    WHERE (status = $5 OR
                           (status = $1 AND visibility_timeout < $2))
                      AND retry_count < $6
                    ORDER BY created_at ASC
                    LIMIT 1
                    FOR UPDATE SKIP LOCKED
                )
                RETURNING *
                """,
                JobStatus.IN_PROGRESS.value,
                now,
                timeout_cutoff,
                worker_id,
                JobStatus.PENDING.value,
                self.MAX_RETRIES
            )

            if not row:
                return None

            # Convert to IngestionJob
            job = IngestionJob(
                job_id=str(row['job_id']),
                org_id=row['org_id'],
                document_id=str(row['document_id']) if row['document_id'] else None,
                checksum=row['checksum'],
                storage_path=row['storage_path'],
                connector_type=row['connector_type'],
                source_format=row['source_format'],
                metadata=json.loads(row['metadata']) if row['metadata'] else {},
                status=JobStatus(row['status']),
                created_at=row['created_at'],
                started_at=row['started_at'],
                completed_at=row['completed_at'],
                error_message=row['error_message'],
                retry_count=row['retry_count'],
                visibility_timeout=row['visibility_timeout'],
                worker_id=row['worker_id']
            )

            logger.info(
                f"🔄 Dequeued job {job.job_id} for worker {worker_id}"
            )

            return job

    async def complete_job(
        self,
        job_id: str,
        document_id: str,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Mark job as completed or failed

        Args:
            job_id: Job ID
            document_id: Document ID (if successful)
            success: Whether job succeeded
            error_message: Error message if failed
        """
        await self.connect()

        async with self._pool.acquire() as conn:
            if success:
                await conn.execute(
                    """
                    UPDATE ingestion_events
                    SET status = $1,
                        completed_at = $2,
                        document_id = $3
                    WHERE job_id = $4
                    """,
                    JobStatus.COMPLETED.value,
                    datetime.now(),
                    document_id,
                    job_id
                )

                logger.info(f"✓ Completed job {job_id}")

            else:
                # Check retry count
                retry_count = await conn.fetchval(
                    "SELECT retry_count FROM ingestion_events WHERE job_id = $1",
                    job_id
                )

                if retry_count >= self.MAX_RETRIES - 1:
                    # Max retries reached, mark as failed
                    await conn.execute(
                        """
                        UPDATE ingestion_events
                        SET status = $1,
                            completed_at = $2,
                            error_message = $3,
                            retry_count = retry_count + 1
                        WHERE job_id = $4
                        """,
                        JobStatus.FAILED.value,
                        datetime.now(),
                        error_message,
                        job_id
                    )

                    logger.error(
                        f"✗ Failed job {job_id} after {self.MAX_RETRIES} retries: "
                        f"{error_message}"
                    )

                else:
                    # Schedule for retry
                    await conn.execute(
                        """
                        UPDATE ingestion_events
                        SET status = $1,
                            error_message = $2,
                            retry_count = retry_count + 1,
                            visibility_timeout = NULL
                        WHERE job_id = $3
                        """,
                        JobStatus.RETRY.value,
                        error_message,
                        job_id
                    )

                    logger.warning(
                        f"⚠️  Retrying job {job_id} (attempt {retry_count + 1}/{self.MAX_RETRIES})"
                    )

    async def get_queue_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics

        Returns:
            Dict with queue statistics
        """
        await self.connect()

        async with self._pool.acquire() as conn:
            stats = await conn.fetchrow(
                """
                SELECT
                    COUNT(*) FILTER (WHERE status = 'pending') as pending,
                    COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                    COUNT(*) FILTER (WHERE status = 'completed') as completed,
                    COUNT(*) FILTER (WHERE status = 'failed') as failed,
                    COUNT(*) FILTER (WHERE status = 'retry') as retry,
                    COUNT(*) as total
                FROM ingestion_events
                WHERE created_at > NOW() - INTERVAL '7 days'
                """
            )

            # Check backlog
            oldest_pending = await conn.fetchval(
                """
                SELECT MIN(created_at)
                FROM ingestion_events
                WHERE status = 'pending'
                """
            )

            backlog_hours = None
            backlog_alert = False

            if oldest_pending:
                backlog_delta = datetime.now() - oldest_pending
                backlog_hours = backlog_delta.total_seconds() / 3600

                if backlog_hours > self.BACKLOG_THRESHOLD_HOURS:
                    backlog_alert = True
                    logger.warning(
                        f"⚠️  Backlog alert: {stats['pending']} pending jobs, "
                        f"oldest is {backlog_hours:.1f} hours old"
                    )

            return {
                "pending": stats['pending'],
                "in_progress": stats['in_progress'],
                "completed": stats['completed'],
                "failed": stats['failed'],
                "retry": stats['retry'],
                "total": stats['total'],
                "backlog_hours": backlog_hours,
                "backlog_alert": backlog_alert,
                "timestamp": datetime.now().isoformat()
            }

    async def _update_progress_file(self, entry: Dict[str, Any]):
        """
        Update progress file for resume support

        Args:
            entry: Progress entry to append
        """
        # Create parent directory if needed
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)

        # Append to progress file (JSONL format)
        with open(self.progress_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
