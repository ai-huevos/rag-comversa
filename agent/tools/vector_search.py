"""
Vector Search Tool for pgvector semantic retrieval
Queries PostgreSQL with pgvector for similar document chunks
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from uuid import UUID

import asyncpg
from openai import AsyncOpenAI

logger = logging.getLogger(__name__)


@dataclass
class VectorSearchResult:
    """Single vector search result with chunk content and metadata"""
    chunk_id: UUID
    document_id: UUID
    content: str
    similarity_score: float
    metadata: Dict[str, Any]
    page_number: Optional[int] = None
    section_title: Optional[str] = None


@dataclass
class VectorSearchResponse:
    """Response from vector search with results and metadata"""
    results: List[VectorSearchResult]
    query: str
    org_id: str
    context: Optional[str]
    top_k: int
    total_found: int
    execution_time_ms: float


class VectorSearchTool:
    """
    Pgvector search tool for semantic retrieval from document chunks

    Uses OpenAI embeddings + PostgreSQL HNSW index for fast similarity search
    with org_id namespace isolation and optional context filtering.
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        openai_client: AsyncOpenAI,
        embedding_model: str = "text-embedding-3-small",
    ):
        """
        Initialize vector search tool

        Args:
            db_pool: AsyncPG connection pool
            openai_client: OpenAI async client for embeddings
            embedding_model: Model name for embeddings
        """
        self.db_pool = db_pool
        self.openai_client = openai_client
        self.embedding_model = embedding_model

    async def search(
        self,
        query: str,
        org_id: str,
        context: Optional[str] = None,
        top_k: int = 5,
    ) -> VectorSearchResponse:
        """
        Execute vector similarity search

        Args:
            query: Search query in Spanish or English
            org_id: Organization namespace filter
            context: Optional business context filter
            top_k: Number of results to return (default 5)

        Returns:
            VectorSearchResponse with matching chunks
        """
        import time
        start_time = time.perf_counter()

        # Generate query embedding
        logger.info(f"Vector search: org={org_id}, query='{query[:50]}...', top_k={top_k}")

        try:
            embedding_response = await self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=query,
            )
            query_embedding = embedding_response.data[0].embedding

        except Exception as exc:
            logger.error(f"Failed to generate query embedding: {exc}")
            raise RuntimeError(f"Embedding generation failed: {exc}") from exc

        # Query pgvector with org_id filter
        vector_literal = f"[{','.join(str(v) for v in query_embedding)}]"

        sql = """
            SELECT
                dc.id as chunk_id,
                dc.document_id,
                dc.content,
                dc.page_number,
                dc.section_title,
                dc.language,
                dc.spanish_features,
                d.title as document_title,
                d.source_type,
                d.original_filename,
                d.metadata as document_metadata,
                1 - (e.embedding <=> $1::vector) as similarity_score
            FROM document_chunks dc
            JOIN embeddings e ON e.chunk_id = dc.id
            JOIN documents d ON d.id = dc.document_id
            WHERE d.org_id = $2
              AND ($3::text IS NULL OR d.metadata->>'business_context' = $3)
            ORDER BY e.embedding <=> $1::vector
            LIMIT $4
        """

        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch(sql, vector_literal, org_id, context, top_k)

        # Convert rows to VectorSearchResult objects
        results = []
        for row in rows:
            metadata = {
                "document_title": row["document_title"],
                "source_type": row["source_type"],
                "original_filename": row["original_filename"],
                "language": row["language"],
                "spanish_features": row["spanish_features"],
                "document_metadata": row["document_metadata"],
            }

            results.append(
                VectorSearchResult(
                    chunk_id=row["chunk_id"],
                    document_id=row["document_id"],
                    content=row["content"],
                    similarity_score=float(row["similarity_score"]),
                    metadata=metadata,
                    page_number=row["page_number"],
                    section_title=row["section_title"],
                )
            )

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Vector search completed: {len(results)} results in {execution_time_ms:.1f}ms"
        )

        return VectorSearchResponse(
            results=results,
            query=query,
            org_id=org_id,
            context=context,
            top_k=top_k,
            total_found=len(results),
            execution_time_ms=execution_time_ms,
        )


async def vector_search(
    query: str,
    org_id: str,
    context: Optional[str] = None,
    top_k: int = 5,
    db_pool: Optional[asyncpg.Pool] = None,
    openai_client: Optional[AsyncOpenAI] = None,
) -> VectorSearchResponse:
    """
    Standalone function interface for vector search

    This function is designed to be registered as a Pydantic AI tool.

    Args:
        query: Search query
        org_id: Organization identifier
        context: Optional business context
        top_k: Number of results
        db_pool: Database pool (injected by agent)
        openai_client: OpenAI client (injected by agent)

    Returns:
        VectorSearchResponse
    """
    if db_pool is None or openai_client is None:
        raise ValueError("db_pool and openai_client must be provided")

    tool = VectorSearchTool(db_pool, openai_client)
    return await tool.search(query, org_id, context, top_k)
