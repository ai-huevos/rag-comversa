"""
Modelos de datos utilizados por el repositorio de PostgreSQL.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence
from uuid import UUID, uuid4


@dataclass
class DocumentChunkPayload:
    """
    Representa un fragmento normalizado que será persistido en Postgres.
    """

    content: str
    chunk_index: int
    token_count: int
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    language: str = "es"
    span_offsets: Optional[Dict[str, Any]] = None
    spanish_features: Optional[Dict[str, Any]] = None
    chunk_id: UUID = field(default_factory=uuid4)

    def as_record(self, document_id: UUID) -> Dict[str, Any]:
        """
        Serializa el chunk para inserciones parametrizadas.
        """
        return {
            "id": str(self.chunk_id),
            "document_id": str(document_id),
            "chunk_index": self.chunk_index,
            "content": self.content,
            "token_count": self.token_count,
            "page_number": self.page_number,
            "section_title": self.section_title,
            "language": self.language,
            "span_offsets": self.span_offsets or {},
            "spanish_features": self.spanish_features or {},
        }


@dataclass
class DocumentPayload:
    """
    Metadatos del documento y sus chunks asociados.
    """

    org_id: str
    source_type: str
    checksum: str
    storage_path: str
    metadata: Dict[str, Any]
    source_format: Optional[str] = None
    title: Optional[str] = None
    language: str = "es"
    page_count: Optional[int] = None
    original_filename: Optional[str] = None
    ingestion_event_id: Optional[int] = None
    ingestion_document_uuid: Optional[UUID] = None
    document_id: Optional[UUID] = None
    document_status: str = "pending"
    chunks: List[DocumentChunkPayload] = field(default_factory=list)

    def resolve_document_id(self) -> UUID:
        """
        Determina el UUID del documento, reutilizando el generado por ingestion_events.
        """
        if self.document_id:
            return self.document_id
        if self.ingestion_document_uuid:
            self.document_id = self.ingestion_document_uuid
            return self.document_id
        self.document_id = uuid4()
        return self.document_id


@dataclass
class ChunkEmbeddingPayload:
    """
    Embedding generado para un chunk concreto.
    """

    chunk_id: UUID
    document_id: UUID
    vector: Sequence[float]
    provider: str = "openai"
    model: str = "text-embedding-3-small"
    dimensions: Optional[int] = None
    cost_cents: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def resolved_dimensions(self) -> int:
        """
        Devuelve la dimensión del vector para almacenamiento consistente.
        """
        if self.dimensions is not None:
            return self.dimensions
        self.dimensions = len(self.vector)
        return self.dimensions


@dataclass
class DocumentPersistenceResult:
    """
    Resultado de una operación de persistencia en Postgres.
    """

    document_id: UUID
    chunk_ids: List[UUID]
    embedding_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el resultado para logs o métricas."""
        return {
            "document_id": str(self.document_id),
            "chunk_ids": [str(chunk_id) for chunk_id in self.chunk_ids],
            "embedding_count": self.embedding_count,
        }
