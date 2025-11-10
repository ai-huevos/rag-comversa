"""
DocumentPayload dataclass for normalized document representation

This module defines the canonical document payload structure used throughout
the RAG 2.0 pipeline for multi-format document processing.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


@dataclass
class DocumentPayload:
    """
    Normalized document payload for downstream processing

    This dataclass represents a parsed document in a format-agnostic way,
    preserving metadata, content, structure, and processing information
    for ingestion into PostgreSQL and Neo4j storage layers.

    Attributes:
        document_id: Unique document identifier (UUID)
        org_id: Organization identifier from context registry
        checksum: SHA-256 checksum of original file
        source_type: Source connector type (email, whatsapp, api, sharepoint)
        source_format: File format (pdf, docx, image, csv, xlsx, json)
        mime_type: MIME type of original file
        original_path: Path to original file in storage
        content: Extracted text content (Spanish, never translated)
        language: Detected language code (es, en, es-en for bilingual)
        page_count: Number of pages/sections in document
        sections: Structured sections with titles and content
        tables: Extracted tables with headers and rows
        images: Image metadata for OCR processing
        context_tags: Tags from ContextRegistry for access control
        processed_at: Timestamp when document was processed
        processing_time_seconds: Time taken to process document
        metadata: Additional connector-specific metadata

    Example:
        >>> payload = DocumentPayload(
        ...     document_id="550e8400-e29b-41d4-a716-446655440000",
        ...     org_id="los_tajibos",
        ...     checksum="abc123...",
        ...     source_type="email",
        ...     source_format="pdf",
        ...     mime_type="application/pdf",
        ...     original_path=Path("data/documents/originals/550e8400.pdf"),
        ...     content="Procedimiento de recepción de huéspedes...",
        ...     language="es",
        ...     page_count=10,
        ...     sections=[{"title": "Introducción", "content": "...", "page": 1}],
        ...     tables=[],
        ...     images=[],
        ...     context_tags=["hotel", "operaciones", "recepcion"],
        ...     metadata={"sender": "patricia@lostajibos.com"}
        ... )
    """

    # Identity
    document_id: str
    org_id: str
    checksum: str

    # Source metadata
    source_type: str  # email, whatsapp, api, sharepoint
    source_format: str  # pdf, docx, image, csv, xlsx, json
    mime_type: str
    original_path: Path

    # Content (ALWAYS in Spanish - never translate)
    content: str
    language: str  # es, en, es-en (bilingual)

    # Structure
    page_count: int
    sections: List[Dict[str, Any]] = field(default_factory=list)
    # Section structure: {"title": str, "content": str, "level": int, "page": int}

    tables: List[Dict[str, Any]] = field(default_factory=list)
    # Table structure: {"headers": List[str], "rows": List[List[str]], "page": int}

    images: List[Dict[str, Any]] = field(default_factory=list)
    # Image structure: {"path": Path, "caption": str, "page": int, "needs_ocr": bool}

    # Processing metadata
    context_tags: List[str] = field(default_factory=list)
    processed_at: datetime = field(default_factory=datetime.now)
    processing_time_seconds: float = 0.0

    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert payload to dictionary for JSON serialization

        Returns:
            Dictionary representation with Path objects converted to strings

        Example:
            >>> payload_dict = payload.to_dict()
            >>> import json
            >>> json.dumps(payload_dict, ensure_ascii=False)  # Preserves Spanish
        """
        return {
            'document_id': self.document_id,
            'org_id': self.org_id,
            'checksum': self.checksum,
            'source_type': self.source_type,
            'source_format': self.source_format,
            'mime_type': self.mime_type,
            'original_path': str(self.original_path),
            'content': self.content,
            'language': self.language,
            'page_count': self.page_count,
            'sections': self.sections,
            'tables': self.tables,
            'images': [
                {**img, 'path': str(img['path'])}
                for img in self.images
            ],
            'context_tags': self.context_tags,
            'processed_at': self.processed_at.isoformat(),
            'processing_time_seconds': self.processing_time_seconds,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DocumentPayload':
        """
        Create DocumentPayload from dictionary

        Args:
            data: Dictionary representation of payload

        Returns:
            DocumentPayload instance

        Raises:
            ValueError: If required fields missing
        """
        # Convert string paths back to Path objects
        data['original_path'] = Path(data['original_path'])

        for img in data.get('images', []):
            if 'path' in img:
                img['path'] = Path(img['path'])

        # Convert ISO timestamp back to datetime
        if isinstance(data['processed_at'], str):
            data['processed_at'] = datetime.fromisoformat(data['processed_at'])

        return cls(**data)

    def get_summary(self) -> str:
        """
        Get human-readable summary of document payload

        Returns:
            Multi-line summary string
        """
        return f"""
DocumentPayload Summary:
  ID: {self.document_id}
  Org: {self.org_id}
  Format: {self.source_format} ({self.mime_type})
  Language: {self.language}
  Pages: {self.page_count}
  Sections: {len(self.sections)}
  Tables: {len(self.tables)}
  Images: {len(self.images)}
  Content Length: {len(self.content)} chars
  Processing Time: {self.processing_time_seconds:.2f}s
  Tags: {', '.join(self.context_tags)}
        """.strip()
