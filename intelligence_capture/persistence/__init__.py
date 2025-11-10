"""
Persistencia de documentos y chunks para PostgreSQL.
"""
from intelligence_capture.persistence.models import (  # noqa: F401
    DocumentChunkPayload,
    DocumentPayload,
    ChunkEmbeddingPayload,
    DocumentPersistenceResult,
)
try:  # pragma: no cover - evita fallar cuando asyncpg no está instalado en pruebas rápidas
    from intelligence_capture.persistence.document_repository import (  # type: ignore F401
        DocumentRepository,
        DocumentRepositoryError,
    )
except Exception:  # pragma: no cover
    DocumentRepository = None  # type: ignore[assignment]
    DocumentRepositoryError = RuntimeError

__all__ = [
    "DocumentChunkPayload",
    "DocumentPayload",
    "ChunkEmbeddingPayload",
    "DocumentPersistenceResult",
]

if DocumentRepository is not None:
    __all__.extend(["DocumentRepository", "DocumentRepositoryError"])
