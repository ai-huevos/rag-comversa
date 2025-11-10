"""
Repositorio asincrónico para persistir documentos, chunks y embeddings en Postgres.
"""
from __future__ import annotations

import json
from typing import List, Optional, Sequence
from uuid import UUID, uuid4

import asyncpg

from intelligence_capture.persistence.models import (
    ChunkEmbeddingPayload,
    DocumentChunkPayload,
    DocumentPayload,
    DocumentPersistenceResult,
)


class DocumentRepositoryError(RuntimeError):
    """Excepción base para errores del repositorio."""


class DocumentRepository:
    """
    Administra inserciones atomicas para documentos y chunks en Postgres.
    """

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    @classmethod
    async def create(
        cls,
        dsn: str,
        *,
        min_size: int = 1,
        max_size: int = 10,
        timeout: int = 60,
    ) -> "DocumentRepository":
        """
        Crea un repositorio con su propio pool de conexiones.
        """
        try:
            pool = await asyncpg.create_pool(
                dsn,
                min_size=min_size,
                max_size=max_size,
                timeout=timeout,
                command_timeout=timeout,
            )
            return cls(pool)
        except Exception as exc:  # pragma: no cover - depende del entorno
            raise DocumentRepositoryError(
                f"No se pudo crear el pool de Postgres: {exc}"
            ) from exc

    async def close(self) -> None:
        """Cierra el pool."""
        if self._pool:
            await self._pool.close()

    async def persist_document_bundle(
        self,
        payload: DocumentPayload,
        *,
        chunk_embeddings: Optional[List[ChunkEmbeddingPayload]] = None,
    ) -> DocumentPersistenceResult:
        """
        Inserta documento, chunks y embeddings dentro de una única transacción.
        """
        document_id = payload.resolve_document_id()
        chunk_ids = [chunk.chunk_id for chunk in payload.chunks]

        try:
            async with self._pool.acquire() as conn:
                async with conn.transaction():
                    await self._upsert_document(conn, document_id, payload)

                    if payload.chunks:
                        await self._insert_chunks(conn, document_id, payload.chunks)

                    embedding_count = 0
                    if chunk_embeddings:
                        embedding_count = await self._insert_embeddings(
                            conn,
                            chunk_embeddings,
                        )

                    if payload.ingestion_event_id:
                        await conn.execute(
                            """
                            UPDATE ingestion_events
                               SET document_row_id = $1
                             WHERE id = $2
                            """,
                            str(document_id),
                            payload.ingestion_event_id,
                        )

                    return DocumentPersistenceResult(
                        document_id=document_id,
                        chunk_ids=chunk_ids,
                        embedding_count=embedding_count,
                    )
        except Exception as exc:
            raise DocumentRepositoryError(
                f"Error al persistir documento {document_id}: {exc}"
            ) from exc

    async def mark_document_status(
        self,
        document_id: UUID,
        *,
        status: str,
        metadata: Optional[dict] = None,
    ) -> None:
        """
        Actualiza el estado del documento y, opcionalmente, fusiona metadatos.
        """
        metadata_json = (
            json.dumps(metadata, ensure_ascii=False) if metadata is not None else None
        )
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE documents
                   SET document_status = $2,
                       metadata = CASE
                           WHEN $3::jsonb IS NULL THEN metadata
                           ELSE COALESCE(metadata, '{}'::jsonb) || $3::jsonb
                       END
                 WHERE id = $1
                """,
                str(document_id),
                status,
                metadata_json,
            )

    async def _upsert_document(
        self,
        conn: asyncpg.Connection,
        document_id: UUID,
        payload: DocumentPayload,
    ) -> None:
        metadata_json = json.dumps(payload.metadata or {}, ensure_ascii=False)
        await conn.execute(
            """
            INSERT INTO documents (
                id,
                org_id,
                ingestion_event_id,
                source_type,
                source_format,
                title,
                language,
                page_count,
                checksum,
                storage_path,
                original_filename,
                document_status,
                metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8,
                $9, $10, $11, $12, $13::jsonb
            )
            ON CONFLICT (id)
            DO UPDATE SET
                ingestion_event_id = COALESCE(EXCLUDED.ingestion_event_id, documents.ingestion_event_id),
                source_type = EXCLUDED.source_type,
                source_format = EXCLUDED.source_format,
                title = COALESCE(EXCLUDED.title, documents.title),
                language = EXCLUDED.language,
                page_count = EXCLUDED.page_count,
                checksum = EXCLUDED.checksum,
                storage_path = EXCLUDED.storage_path,
                original_filename = COALESCE(EXCLUDED.original_filename, documents.original_filename),
                document_status = EXCLUDED.document_status,
                metadata = EXCLUDED.metadata
            """,
            str(document_id),
            payload.org_id,
            payload.ingestion_event_id,
            payload.source_type,
            payload.source_format,
            payload.title,
            payload.language,
            payload.page_count,
            payload.checksum,
            payload.storage_path,
            payload.original_filename,
            payload.document_status,
            metadata_json,
        )

    async def _insert_chunks(
        self,
        conn: asyncpg.Connection,
        document_id: UUID,
        chunks: Sequence[DocumentChunkPayload],
    ) -> None:
        chunk_sql = """
            INSERT INTO document_chunks (
                id,
                document_id,
                chunk_index,
                content,
                token_count,
                page_number,
                section_title,
                language,
                span_offsets,
                spanish_features
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9::jsonb, $10::jsonb
            )
            ON CONFLICT (id)
            DO UPDATE SET
                chunk_index = EXCLUDED.chunk_index,
                content = EXCLUDED.content,
                token_count = EXCLUDED.token_count,
                page_number = EXCLUDED.page_number,
                section_title = EXCLUDED.section_title,
                language = EXCLUDED.language,
                span_offsets = EXCLUDED.span_offsets,
                spanish_features = EXCLUDED.spanish_features
        """
        params = [
            (
                str(chunk.chunk_id),
                str(document_id),
                chunk.chunk_index,
                chunk.content,
                chunk.token_count,
                chunk.page_number,
                chunk.section_title,
                chunk.language,
                json.dumps(chunk.span_offsets or {}, ensure_ascii=False),
                json.dumps(chunk.spanish_features or {}, ensure_ascii=False),
            )
            for chunk in chunks
        ]

        await conn.executemany(chunk_sql, params)

    async def _insert_embeddings(
        self,
        conn: asyncpg.Connection,
        embeddings: Sequence[ChunkEmbeddingPayload],
    ) -> int:
        embedding_sql = """
            INSERT INTO embeddings (
                id,
                chunk_id,
                document_id,
                provider,
                model,
                dimensions,
                embedding,
                cost_cents,
                metadata
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7::vector, $8, $9::jsonb
            )
            ON CONFLICT (chunk_id)
            DO UPDATE SET
                provider = EXCLUDED.provider,
                model = EXCLUDED.model,
                dimensions = EXCLUDED.dimensions,
                embedding = EXCLUDED.embedding,
                cost_cents = EXCLUDED.cost_cents,
                metadata = EXCLUDED.metadata
        """

        params = [
            (
                str(uuid4()),
                str(embedding.chunk_id),
                str(embedding.document_id),
                embedding.provider,
                embedding.model,
                embedding.resolved_dimensions(),
                self._vector_literal(embedding.vector),
                float(embedding.cost_cents),
                json.dumps(embedding.metadata or {}, ensure_ascii=False),
            )
            for embedding in embeddings
        ]

        if not params:
            return 0

        await conn.executemany(embedding_sql, params)
        return len(params)

    @staticmethod
    def _vector_literal(values: Sequence[float]) -> str:
        """
        Convierte una secuencia numérica en el literal esperado por pgvector.
        """
        formatted = ",".join(f"{value:.8f}" for value in values)
        return f"[{formatted}]"
