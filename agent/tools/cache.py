"""
In-memory TTL cache for retrieval tool results.
Provides 5-minute caching for vector, graph, and hybrid search responses.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheEntry:
    """Single cache entry with value, expiration timestamp, and metadata."""

    value: Any
    expires_at: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResultCache:
    """
    Simple async-safe TTL cache for retrieval results (default 5 minutes).

    Uses SHA-256 of normalized keys to support complex query payloads without
    leaking PII. Designed for short-lived application instances; swap with
    Redis-backed implementation when Task 17 introduces centralized caching.
    """

    def __init__(self, ttl_seconds: int = 300, max_entries: int = 512):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time-to-live for entries (default 5 minutes).
            max_entries: Max number of entries before evicting LRU.
        """
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()
        self._lru_order: Dict[str, float] = {}

    @staticmethod
    def build_key(tool_name: str, payload: Dict[str, Any]) -> str:
        """
        Build deterministic cache key from tool name + payload.

        Args:
            tool_name: Name of the retrieval tool.
            payload: Dict with query parameters.

        Returns:
            Hex digest representing cache key.
        """
        normalized = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        raw = f"{tool_name}:{normalized}".encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    async def get(self, key: str) -> Optional[Any]:
        """
        Retrieve cached value if still valid.

        Args:
            key: Cache key produced by `build_key`.

        Returns:
            Cached value copy or None if missing/expired.
        """
        async with self._lock:
            entry = self._cache.get(key)
            if not entry:
                return None

            now = time.time()
            if entry.expires_at <= now:
                # Expired entry cleanup
                self._cache.pop(key, None)
                self._lru_order.pop(key, None)
                return None

            self._lru_order[key] = now
            return copy.deepcopy(entry.value)

    async def set(
        self,
        key: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Store value in cache with TTL.

        Args:
            key: Cache key.
            value: Value to store.
            metadata: Optional metadata for debugging.
        """
        async with self._lock:
            if len(self._cache) >= self.max_entries:
                await self._evict_lru()

            expires_at = time.time() + self.ttl_seconds
            self._cache[key] = CacheEntry(
                value=copy.deepcopy(value),
                expires_at=expires_at,
                metadata=metadata or {},
            )
            self._lru_order[key] = time.time()

    async def invalidate(self, key: str) -> None:
        """Remove specific key from cache."""
        async with self._lock:
            self._cache.pop(key, None)
            self._lru_order.pop(key, None)

    async def clear(self) -> None:
        """Clear entire cache (mainly for testing)."""
        async with self._lock:
            self._cache.clear()
            self._lru_order.clear()

    async def _evict_lru(self) -> None:
        """Evict least recently used entry when capacity reached."""
        if not self._lru_order:
            return
        lru_key = min(self._lru_order, key=self._lru_order.get)
        self._cache.pop(lru_key, None)
        self._lru_order.pop(lru_key, None)
