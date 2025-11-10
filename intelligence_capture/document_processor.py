"""
Multi-format document processor with MIME-based routing

This module orchestrates document parsing by detecting MIME types and
routing to appropriate adapters for format-specific processing.
"""

import magic
import shutil
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from .models.document_payload import DocumentPayload
from .parsers import (
    BaseAdapter,
    PDFAdapter,
    DOCXAdapter,
    ImageAdapter,
    CSVAdapter,
    XLSXAdapter,
    WhatsAppAdapter
)


class DocumentProcessor:
    """
    Multi-format document processor with state management

    Orchestrates document parsing by:
    1. Detecting MIME type using python-magic
    2. Routing to appropriate adapter based on MIME type
    3. Managing document state directories (processing/processed/failed)
    4. Verifying checksums and storing originals
    5. Providing error handling and recovery

    State Directories:
        data/documents/inbox/        - Incoming documents from connectors
        data/documents/processing/   - Currently being processed
        data/documents/processed/    - Successfully processed
        data/documents/failed/       - Failed processing with error logs
        data/documents/originals/    - Archived originals with UUID names

    Example:
        >>> processor = DocumentProcessor()
        >>> metadata = {
        ...     'document_id': '550e8400-e29b-41d4-a716-446655440000',
        ...     'org_id': 'los_tajibos',
        ...     'checksum': 'abc123...',
        ...     'source_type': 'email',
        ...     'context_tags': ['hotel', 'operaciones']
        ... }
        >>> payload = processor.process(
        ...     Path('data/documents/inbox/email/manual.pdf'),
        ...     metadata
        ... )
        >>> payload.page_count
        10
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None
    ):
        """
        Initialize document processor

        Args:
            base_dir: Base directory for document storage
                     (default: data/documents)
        """
        # Set up directory structure
        if base_dir is None:
            base_dir = Path("data/documents")

        self.base_dir = base_dir
        self.originals_dir = base_dir / "originals"
        self.processing_dir = base_dir / "processing"
        self.processed_dir = base_dir / "processed"
        self.failed_dir = base_dir / "failed"

        # Create all directories
        for dir_path in [
            self.originals_dir,
            self.processing_dir,
            self.processed_dir,
            self.failed_dir
        ]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Register adapters by MIME type
        self.adapters = self._register_adapters()

    def _register_adapters(self) -> Dict[str, BaseAdapter]:
        """
        Register all adapters by MIME type

        Creates instances of all adapters and maps their supported
        MIME types to adapter instances.

        Returns:
            Dictionary mapping MIME types to adapter instances

        Example:
            >>> adapters = processor._register_adapters()
            >>> 'application/pdf' in adapters
            True
            >>> type(adapters['application/pdf'])
            <class 'PDFAdapter'>
        """
        adapter_instances = [
            PDFAdapter(),
            DOCXAdapter(),
            ImageAdapter(),
            CSVAdapter(),
            XLSXAdapter(),
            WhatsAppAdapter()
        ]

        mime_map = {}
        for adapter in adapter_instances:
            for mime_type in adapter.supported_mime_types:
                mime_map[mime_type] = adapter

        return mime_map

    def process(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Process document through appropriate adapter

        Workflow:
        1. Move file to processing directory
        2. Detect MIME type
        3. Route to adapter
        4. Parse document
        5. Store original with checksum verification
        6. Move to processed directory
        7. Return DocumentPayload

        Args:
            file_path: Path to document in inbox
            metadata: Metadata from connector containing:
                - document_id: UUID
                - org_id: Organization ID
                - checksum: SHA-256 checksum
                - source_type: Connector type
                - context_tags: Access control tags

        Returns:
            DocumentPayload with extracted content

        Raises:
            ValueError: If format unsupported or processing fails
            FileNotFoundError: If file does not exist

        Example:
            >>> payload = processor.process(
            ...     Path('inbox/email/manual.pdf'),
            ...     metadata
            ... )
            >>> payload.source_format
            'pdf'
        """
        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {file_path}"
            )

        start_time = datetime.now()
        checksum = metadata['checksum']
        doc_id = metadata['document_id']

        try:
            # Move to processing directory
            processing_path = self.processing_dir / f"{checksum}_{file_path.name}"
            shutil.copy2(file_path, processing_path)

            # Detect MIME type
            mime_type = magic.from_file(str(processing_path), mime=True)

            # Find appropriate adapter
            if mime_type not in self.adapters:
                raise ValueError(
                    f"Formato no soportado: {mime_type} ({file_path.name})"
                )

            adapter = self.adapters[mime_type]

            # Add MIME type to metadata
            metadata['mime_type'] = mime_type

            # Parse document
            payload = adapter.parse(processing_path, metadata)

            # Store original with UUID filename
            original_path = self.originals_dir / f"{doc_id}{file_path.suffix}"
            shutil.copy2(file_path, original_path)

            # Verify checksum
            calculated_checksum = self._calculate_checksum(original_path)
            if calculated_checksum != checksum:
                raise ValueError(
                    f"Error de verificación de checksum para {file_path.name}. "
                    f"Esperado: {checksum}, calculado: {calculated_checksum}"
                )

            # Move to processed directory
            processed_path = self.processed_dir / f"{checksum}_{file_path.name}"
            shutil.move(str(processing_path), str(processed_path))

            # Update processing time
            total_time = (datetime.now() - start_time).total_seconds()
            payload.processing_time_seconds = total_time

            return payload

        except Exception as e:
            # Move to failed directory with error log
            failed_path = self.failed_dir / f"{checksum}_{file_path.name}"

            if processing_path.exists():
                shutil.move(str(processing_path), str(failed_path))

            # Write error log
            error_log_path = failed_path.with_suffix(
                failed_path.suffix + '.error.txt'
            )
            error_log_path.write_text(
                f"Error: {str(e)}\n"
                f"Archivo: {file_path.name}\n"
                f"MIME Type: {metadata.get('mime_type', 'unknown')}\n"
                f"Timestamp: {datetime.now().isoformat()}\n"
                f"Metadata: {metadata}\n",
                encoding='utf-8'
            )

            raise ValueError(
                f"Error procesando {file_path.name}: {e}"
            )

    def _calculate_checksum(self, file_path: Path) -> str:
        """
        Calculate SHA-256 checksum of file

        Args:
            file_path: Path to file

        Returns:
            Hexadecimal checksum string

        Example:
            >>> checksum = processor._calculate_checksum(Path('file.pdf'))
            >>> len(checksum)
            64  # SHA-256 is 64 hex characters
        """
        sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            # Read in 8KB chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)

        return sha256.hexdigest()

    def get_stats(self) -> Dict[str, int]:
        """
        Get processing statistics

        Returns:
            Dictionary with counts for each state directory

        Example:
            >>> stats = processor.get_stats()
            >>> stats
            {
                'processing': 0,
                'processed': 42,
                'failed': 3,
                'originals': 42
            }
        """
        return {
            'processing': len(list(self.processing_dir.iterdir())),
            'processed': len(list(self.processed_dir.iterdir())),
            'failed': len([
                f for f in self.failed_dir.iterdir()
                if not f.name.endswith('.error.txt')
            ]),
            'originals': len(list(self.originals_dir.iterdir()))
        }

    def get_supported_formats(self) -> Dict[str, List[str]]:
        """
        Get supported MIME types grouped by adapter

        Returns:
            Dictionary mapping adapter names to MIME type lists

        Example:
            >>> formats = processor.get_supported_formats()
            >>> formats['PDFAdapter']
            ['application/pdf']
        """
        formats = {}

        for mime_type, adapter in self.adapters.items():
            adapter_name = adapter.__class__.__name__
            if adapter_name not in formats:
                formats[adapter_name] = []
            formats[adapter_name].append(mime_type)

        return formats

    def cleanup_failed(self, days_old: int = 7) -> int:
        """
        Clean up old failed documents

        Removes failed documents older than specified days.

        Args:
            days_old: Remove files older than this many days

        Returns:
            Number of files removed

        Example:
            >>> removed = processor.cleanup_failed(days_old=30)
            >>> print(f"Removed {removed} old failed documents")
        """
        import time

        removed_count = 0
        cutoff_time = time.time() - (days_old * 24 * 60 * 60)

        for file_path in self.failed_dir.iterdir():
            if file_path.stat().st_mtime < cutoff_time:
                file_path.unlink()
                removed_count += 1

        return removed_count
