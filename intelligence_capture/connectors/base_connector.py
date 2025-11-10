"""
Base Connector Abstract Class
Provides common infrastructure for all source connectors

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import hashlib
import json
import logging
from intelligence_capture.context_registry import get_registry

logger = logging.getLogger(__name__)


@dataclass
class ConnectorMetadata:
    """
    Metadata envelope for connector-sourced documents

    Attributes:
        source_path: Path to downloaded/extracted file
        source_type: Connector type ('email', 'whatsapp', 'api', 'sharepoint')
        source_format: File format/MIME type
        org_id: Organization identifier
        business_unit: Business unit (optional)
        department: Department (optional)
        connector_metadata: Additional connector-specific metadata
        checksum: SHA-256 checksum of file
        collected_at: Timestamp of collection
        consent_validated: Whether consent was validated
    """
    source_path: Path
    source_type: str
    source_format: str
    org_id: str
    business_unit: Optional[str] = None
    department: Optional[str] = None
    connector_metadata: Dict[str, Any] = field(default_factory=dict)
    checksum: Optional[str] = None
    collected_at: datetime = field(default_factory=datetime.now)
    consent_validated: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "source_path": str(self.source_path),
            "source_type": self.source_type,
            "source_format": self.source_format,
            "org_id": self.org_id,
            "business_unit": self.business_unit,
            "department": self.department,
            "connector_metadata": self.connector_metadata,
            "checksum": self.checksum,
            "collected_at": self.collected_at.isoformat(),
            "consent_validated": self.consent_validated
        }


class BaseConnector(ABC):
    """
    Abstract base class for source connectors

    All connectors must:
    1. Validate consent via ContextRegistry
    2. Enforce file size limits (50 MB)
    3. Enforce batch limits (≤100 docs)
    4. Generate metadata envelopes
    5. Drop files to inbox taxonomy
    6. Log activity
    """

    # Class constants
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
    MAX_BATCH_SIZE = 100  # Maximum documents per batch

    def __init__(
        self,
        org_id: str,
        business_unit: Optional[str] = None,
        department: Optional[str] = None,
        inbox_root: Path = Path("data/documents/inbox")
    ):
        """
        Initialize base connector

        Args:
            org_id: Organization identifier
            business_unit: Business unit (optional)
            department: Department (optional)
            inbox_root: Root directory for inbox taxonomy
        """
        self.org_id = org_id
        self.business_unit = business_unit
        self.department = department
        self.inbox_root = inbox_root
        self.registry = get_registry()
        self.activity_log: List[Dict[str, Any]] = []

        # Derived properties
        self.connector_type = self._get_connector_type()
        self.inbox_path = self._get_inbox_path()

    @abstractmethod
    def _get_connector_type(self) -> str:
        """
        Get connector type identifier

        Returns:
            Connector type string ('email', 'whatsapp', 'api', 'sharepoint')
        """
        pass

    def _get_inbox_path(self) -> Path:
        """
        Get inbox path following taxonomy: inbox/{connector}/{org}/

        Returns:
            Path to connector's inbox directory
        """
        path = self.inbox_root / self.connector_type / self.org_id

        # Create directory if it doesn't exist
        path.mkdir(parents=True, exist_ok=True)

        return path

    async def validate_consent(self, operation: str = "ingestion") -> bool:
        """
        Validate consent metadata via ContextRegistry

        Args:
            operation: Operation type (default: 'ingestion')

        Returns:
            True if consent is valid, False otherwise

        Raises:
            ValueError: If consent validation fails (Spanish error message)
        """
        is_valid, error_msg = await self.registry.validate_consent(self.org_id, operation)

        if not is_valid:
            raise ValueError(error_msg)  # Spanish error message from registry

        return True

    def validate_file_size(self, file_path: Path) -> bool:
        """
        Validate file size against MAX_FILE_SIZE limit

        Args:
            file_path: Path to file to validate

        Returns:
            True if file size is valid

        Raises:
            ValueError: If file exceeds size limit (Spanish error message)
        """
        size = file_path.stat().st_size

        if size > self.MAX_FILE_SIZE:
            size_mb = size / 1024 / 1024
            limit_mb = self.MAX_FILE_SIZE / 1024 / 1024
            raise ValueError(
                f"Archivo '{file_path.name}' excede el límite de {limit_mb:.0f} MB: "
                f"{size_mb:.1f} MB. Por favor, divida el archivo o contacte al administrador."
            )

        return True

    def validate_batch_size(self, batch_count: int) -> bool:
        """
        Validate batch size against MAX_BATCH_SIZE limit

        Args:
            batch_count: Number of documents in batch

        Returns:
            True if batch size is valid

        Raises:
            ValueError: If batch exceeds limit (Spanish error message)
        """
        if batch_count > self.MAX_BATCH_SIZE:
            raise ValueError(
                f"Lote excede el límite de {self.MAX_BATCH_SIZE} documentos: {batch_count}. "
                "Por favor, reduzca el tamaño del lote."
            )

        return True

    def calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum for file

        Args:
            file_path: Path to file

        Returns:
            Hex-encoded SHA-256 checksum
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def create_metadata_envelope(
        self,
        source_path: Path,
        source_format: str,
        connector_metadata: Dict[str, Any] = None
    ) -> ConnectorMetadata:
        """
        Create metadata envelope for document

        Args:
            source_path: Path to source file
            source_format: File format/MIME type
            connector_metadata: Additional connector-specific metadata

        Returns:
            ConnectorMetadata envelope
        """
        checksum = self.calculate_checksum(source_path)

        metadata = ConnectorMetadata(
            source_path=source_path,
            source_type=self.connector_type,
            source_format=source_format,
            org_id=self.org_id,
            business_unit=self.business_unit,
            department=self.department,
            connector_metadata=connector_metadata or {},
            checksum=checksum,
            consent_validated=True  # Set after validation
        )

        return metadata

    def save_to_inbox(
        self,
        source_file: Path,
        metadata: ConnectorMetadata
    ) -> Path:
        """
        Save file and metadata to inbox taxonomy

        Args:
            source_file: Source file to copy
            metadata: Metadata envelope

        Returns:
            Path to saved file in inbox
        """
        # Generate unique filename using checksum
        filename = f"{metadata.checksum[:16]}_{source_file.name}"
        inbox_file = self.inbox_path / filename

        # Copy file to inbox
        inbox_file.write_bytes(source_file.read_bytes())

        # Save metadata JSON
        metadata_file = inbox_file.with_suffix(inbox_file.suffix + '.meta.json')
        metadata_file.write_text(
            json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        logger.info(f"✓ Saved to inbox: {inbox_file.relative_to(self.inbox_root)}")

        return inbox_file

    def log_activity(
        self,
        action: str,
        status: str,
        details: Dict[str, Any] = None
    ):
        """
        Log connector activity

        Args:
            action: Action performed ('fetch', 'validate', 'save')
            status: Status ('success', 'error', 'warning')
            details: Additional details
        """
        entry = {
            "timestamp": datetime.now().isoformat(),
            "connector_type": self.connector_type,
            "org_id": self.org_id,
            "action": action,
            "status": status,
            "details": details or {}
        }

        self.activity_log.append(entry)

        # Log to file
        activity_dir = Path("reports/connector_activity")
        activity_dir.mkdir(parents=True, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")
        activity_file = activity_dir / f"{date_str}.jsonl"

        with open(activity_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    @abstractmethod
    async def fetch_documents(self) -> List[ConnectorMetadata]:
        """
        Fetch documents from source

        Must be implemented by subclass to:
        1. Authenticate to source
        2. Fetch/download documents
        3. Validate consent
        4. Validate file sizes and batch size
        5. Create metadata envelopes
        6. Save to inbox
        7. Log activity

        Returns:
            List of ConnectorMetadata for successfully fetched documents

        Raises:
            ValueError: If consent validation fails (Spanish error)
            Exception: For other errors (should include Spanish messages)
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        Run connector fetch cycle

        Returns:
            Summary dictionary with counts and errors
        """
        logger.info(f"🔌 Starting {self.connector_type} connector for {self.org_id}")

        try:
            # Validate consent before fetching
            await self.validate_consent()

            # Fetch documents
            metadata_list = await self.fetch_documents()

            # Log summary
            self.log_activity(
                action="fetch_complete",
                status="success",
                details={
                    "documents_fetched": len(metadata_list),
                    "total_size_bytes": sum(
                        m.source_path.stat().st_size for m in metadata_list
                    )
                }
            )

            return {
                "status": "success",
                "connector_type": self.connector_type,
                "org_id": self.org_id,
                "documents_fetched": len(metadata_list),
                "activity_log": self.activity_log
            }

        except Exception as e:
            logger.error(f"✗ {self.connector_type} connector failed: {e}")

            self.log_activity(
                action="fetch_complete",
                status="error",
                details={"error": str(e)}
            )

            return {
                "status": "error",
                "connector_type": self.connector_type,
                "org_id": self.org_id,
                "error": str(e),
                "activity_log": self.activity_log
            }
