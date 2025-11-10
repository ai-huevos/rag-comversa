"""
Pipeline de embeddings con caché y control de tasa.
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
import math
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol, Sequence, Tuple
from uuid import UUID

try:  # pragma: no cover - dependencia opcional
    from openai import AsyncOpenAI
except ImportError:  # pragma: no cover
    AsyncOpenAI = Any  # type: ignore[assignment]

try:  # pragma: no cover - dependerá de si redis está disponible
    import redis.asyncio as aioredis
except ImportError:  # pragma: no cover
    aioredis = None

from intelligence_capture.persistence.models import (
    ChunkEmbeddingPayload,
    DocumentChunkPayload,
)

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingPipelineConfig:
    """
    Configuración del pipeline de embeddings.
    """

    model: str = "text-embedding-3-small"
    batch_size: int = 100
    max_retries: int = 3
    request_timeout_seconds: float = 30.0
    cost_per_1k_tokens_cents: float = 0.002  # $0.00002 -> 0.002 centavos
    default_dimensions: int = 1536
    cache_ttl_seconds: int = 86_400
    requests_per_second: int = 4


class EmbeddingCacheProtocol(Protocol):
    """Contrato mínimo para cachés de embeddings."""

    async def get(self, key: str) -> Optional[List[float]]:
        """Obtiene un vector almacenado."""

    async def set(self, key: str, vector: Sequence[float], ttl: int) -> None:
        """Guarda un vector con TTL."""


class InMemoryEmbeddingCache(EmbeddingCacheProtocol):
    """Caché simple en memoria para entornos locales."""

    def __init__(self):
        self._store: Dict[str, Tuple[List[float], float]] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[List[float]]:
        async with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            vector, expires_at = entry
            if expires_at < time.time():
                self._store.pop(key, None)
                return None
            return list(vector)

    async def set(self, key: str, vector: Sequence[float], ttl: int) -> None:
        async with self._lock:
            self._store[key] = (list(vector), time.time() + ttl)


class RedisEmbeddingCache(EmbeddingCacheProtocol):
    """Caché basado en Redis Streams/keys."""

    def __init__(self, redis_url: str):
        if aioredis is None:  # pragma: no cover
            raise RuntimeError(
                "redis package not installed. Run `pip install -r requirements-rag2.txt`."
            )
        self._redis = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=False)

    async def get(self, key: str) -> Optional[List[float]]:
        payload = await self._redis.get(key)
        if payload is None:
            return None
        return self._deserialize_vector(payload)

    async def set(self, key: str, vector: Sequence[float], ttl: int) -> None:
        serialized = self._serialize_vector(vector)
        await self._redis.setex(key, ttl, serialized)

    @staticmethod
    def _serialize_vector(vector: Sequence[float]) -> bytes:
        return ",".join(f"{value:.8f}" for value in vector).encode("utf-8")

    @staticmethod
    def _deserialize_vector(payload: bytes) -> List[float]:
        return [float(value) for value in payload.decode("utf-8").split(",") if value]


class AsyncRateLimiter:
    """Limitador de tasa simple basado en bucket."""

    def __init__(self, requests_per_second: int):
        self._interval = 1.0 / max(requests_per_second, 1)
        self._lock = asyncio.Lock()
        self._last_call: float = 0.0

    async def acquire(self) -> None:
        async with self._lock:
            elapsed = time.perf_counter() - self._last_call
            wait_time = self._interval - elapsed
            if wait_time > 0:
                await asyncio.sleep(wait_time)
            self._last_call = time.perf_counter()


class EmbeddingPipeline:
    """
    Orquesta la generación de embeddings con caché y métricas básicas.
    """

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        config: Optional[EmbeddingPipelineConfig] = None,
        cache: Optional[EmbeddingCacheProtocol] = None,
    ):
        if openai_client is None:
            raise ValueError("Se requiere un cliente AsyncOpenAI válido.")
        self._client = openai_client
        self._config = config or EmbeddingPipelineConfig()
        self._cache = cache or InMemoryEmbeddingCache()
        self._limiter = AsyncRateLimiter(self._config.requests_per_second)

    async def embed_document_chunks(
        self,
        document_id: UUID,
        chunks: Sequence[DocumentChunkPayload],
    ) -> List[ChunkEmbeddingPayload]:
        """
        Genera embeddings para los chunks solicitados.
        """
        cache_hits: List[ChunkEmbeddingPayload] = []
        missing_chunks: List[Tuple[DocumentChunkPayload, str]] = []
        order_map = {chunk.chunk_id: idx for idx, chunk in enumerate(chunks)}

        for chunk in chunks:
            cache_key = self._cache_key(document_id, chunk)
            cached_vector = await self._cache.get(cache_key)
            if cached_vector:
                cache_hits.append(
                    ChunkEmbeddingPayload(
                        chunk_id=chunk.chunk_id,
                        document_id=document_id,
                        vector=cached_vector,
                        metadata={
                            "cache_hit": True,
                            "token_estimate": self._estimate_tokens(chunk.content),
                        },
                    )
                )
            else:
                missing_chunks.append((chunk, cache_key))

        new_embeddings: List[ChunkEmbeddingPayload] = []
        if missing_chunks:
            batches = [
                missing_chunks[i : i + self._config.batch_size]
                for i in range(0, len(missing_chunks), self._config.batch_size)
            ]
            for batch in batches:
                batch_embeddings = await self._embed_batch(document_id, batch)
                new_embeddings.extend(batch_embeddings)

        combined = cache_hits + new_embeddings
        combined.sort(key=lambda payload: order_map.get(payload.chunk_id, 0))
        return combined

    async def _embed_batch(
        self,
        document_id: UUID,
        batch: Sequence[Tuple[DocumentChunkPayload, str]],
    ) -> List[ChunkEmbeddingPayload]:
        payload_chunks = [item[0] for item in batch]

        async def _execute_request():
            await self._limiter.acquire()
            return await asyncio.wait_for(
                self._client.embeddings.create(
                    model=self._config.model,
                    input=[chunk.content for chunk in payload_chunks],
                ),
                timeout=self._config.request_timeout_seconds,
            )

        response = await self._execute_with_retries(_execute_request)
        if response is None:  # pragma: no cover - solo si agotamos reintentos
            raise RuntimeError("No se pudo generar embeddings tras múltiples intentos.")

        embeddings: List[ChunkEmbeddingPayload] = []
        for idx, data in enumerate(response.data):
            chunk = payload_chunks[idx]
            vector = data.embedding
            token_estimate = self._estimate_tokens(chunk.content)
            cost_cents = (token_estimate / 1000.0) * self._config.cost_per_1k_tokens_cents

            payload = ChunkEmbeddingPayload(
                chunk_id=chunk.chunk_id,
                document_id=document_id,
                vector=vector,
                model=self._config.model,
                provider="openai",
                dimensions=len(vector) or self._config.default_dimensions,
                cost_cents=cost_cents,
                metadata={
                    "cache_hit": False,
                    "token_estimate": token_estimate,
                    "batch_size": len(payload_chunks),
                },
            )
            embeddings.append(payload)

        # Persistir en caché
        for payload, (_, cache_key) in zip(embeddings, batch):
            await self._cache.set(cache_key, payload.vector, self._config.cache_ttl_seconds)

        return embeddings

    async def _execute_with_retries(self, func):
        last_error = None
        for attempt in range(1, self._config.max_retries + 1):
            try:
                return await func()
            except Exception as exc:  # pragma: no cover - dependiente de API
                last_error = exc
                backoff = min(2 ** attempt, 10)
                logger.warning(
                    "Fallo al solicitar embeddings (intento %s/%s): %s. Reintentando en %.1fs",
                    attempt,
                    self._config.max_retries,
                    exc,
                    backoff,
                )
                await asyncio.sleep(backoff)
        logger.error("Todas las solicitudes de embeddings fallaron: %s", last_error)
        return None

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """
        Heurística simple: 4 caracteres ~ 1 token.
        """
        if not text:
            return 0
        return max(1, math.ceil(len(text) / 4))

    @staticmethod
    def _cache_key(document_id: UUID, chunk: DocumentChunkPayload) -> str:
        checksum = hashlib.sha256(chunk.content.encode("utf-8")).hexdigest()
        return f"{document_id}:{chunk.chunk_id}:{checksum}"
