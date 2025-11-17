"""
Hybrid Search Tool combining vector and graph search
Uses reciprocal rank fusion to merge results from both retrieval methods
"""
import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import asyncpg
from neo4j import AsyncDriver
from openai import AsyncOpenAI

from agent.tools.cache import ResultCache
from agent.tools.graph_search import GraphNode, GraphRelationship, GraphSearchTool
from agent.tools.vector_search import VectorSearchResult, VectorSearchTool
from agent.tools.instrumentation import (
    InstrumentationHook,
    call_instrumentation_hook,
)

logger = logging.getLogger(__name__)


@dataclass
class HybridSearchResult:
    """Unified search result from hybrid retrieval"""
    source_type: str  # "vector" or "graph"
    content: str
    score: float
    metadata: Dict[str, Any]


@dataclass
class HybridSearchResponse:
    """Response from hybrid search with fused results"""
    results: List[HybridSearchResult]
    vector_results: List[VectorSearchResult]
    graph_nodes: List[GraphNode]
    graph_relationships: List[GraphRelationship]
    query: str
    org_id: str
    context: Optional[str]
    weight_vector: float
    weight_graph: float
    total_results: int
    execution_time_ms: float
    cache_hit: bool = False
    overrides_applied: Dict[str, Any] = field(default_factory=dict)


_HYBRID_RESULT_CACHE = ResultCache()


class HybridSearchTool:
    """
    Hybrid search combining vector similarity and graph relationships

    Executes vector and graph searches in parallel, then merges results using
    reciprocal rank fusion: score = 1/(rank + k) where k=60 is standard.

    Default weighting is 50/50, but can be overridden:
    - Tilt to vector for verbatim evidence questions
    - Tilt to graph for relationship/cross-entity questions
    """

    def __init__(
        self,
        db_pool: asyncpg.Pool,
        neo4j_driver: AsyncDriver,
        openai_client: AsyncOpenAI,
        result_cache: Optional[ResultCache] = None,
        vector_cache: Optional[ResultCache] = None,
        graph_cache: Optional[ResultCache] = None,
        instrumentation_hook: Optional[InstrumentationHook] = None,
    ):
        """
        Initialize hybrid search tool

        Args:
            db_pool: PostgreSQL connection pool
            neo4j_driver: Neo4j async driver
            openai_client: OpenAI client for embeddings
            result_cache: Cache for fused hybrid results
            vector_cache: Cache for vector sub-tool
            graph_cache: Cache for graph sub-tool
            instrumentation_hook: Optional metrics hook
        """
        self.result_cache = result_cache or ResultCache()
        self.vector_cache = vector_cache or ResultCache()
        self.graph_cache = graph_cache or ResultCache()
        self.instrumentation_hook = instrumentation_hook

        self.vector_tool = VectorSearchTool(
            db_pool,
            openai_client,
            result_cache=self.vector_cache,
        )
        self.graph_tool = GraphSearchTool(
            neo4j_driver,
            result_cache=self.graph_cache,
        )

    @staticmethod
    def _build_cache_key(
        query: str,
        org_id: str,
        context: Optional[str],
        relationship_types: Optional[List[str]],
        top_k: int,
        weight_vector: float,
        weight_graph: float,
    ) -> str:
        """Construct cache key for hybrid fusion results."""
        payload = {
            "query": query,
            "org_id": org_id,
            "context": context,
            "relationship_types": relationship_types or [],
            "top_k": top_k,
            "weight_vector": round(weight_vector, 3),
            "weight_graph": round(weight_graph, 3),
        }
        return ResultCache.build_key("hybrid_search", payload)

    async def _emit_metrics(self, data: Dict[str, Any]) -> None:
        """Emit metrics for hybrid search."""
        await call_instrumentation_hook(
            self.instrumentation_hook,
            "hybrid_search",
            data,
        )

    async def search(
        self,
        query: str,
        org_id: str,
        context: Optional[str] = None,
        relationship_types: Optional[List[str]] = None,
        top_k: int = 5,
        weight_vector: float = 0.5,
        weight_graph: float = 0.5,
    ) -> HybridSearchResponse:
        """
        Execute hybrid search with reciprocal rank fusion

        Args:
            query: Search query
            org_id: Organization namespace
            context: Optional business context
            relationship_types: Optional graph relationship filters
            top_k: Number of results to return
            weight_vector: Weight for vector results (0-1)
            weight_graph: Weight for graph results (0-1)

        Returns:
            HybridSearchResponse with fused results
        """
        start_time = time.perf_counter()
        cache_key = self._build_cache_key(
            query,
            org_id,
            context,
            relationship_types,
            top_k,
            weight_vector,
            weight_graph,
        )
        cache_hit = False

        if self.result_cache:
            cached_response = await self.result_cache.get(cache_key)
            if cached_response:
                cache_hit = True
                cached_response.cache_hit = True
                cached_response.execution_time_ms = (
                    time.perf_counter() - start_time
                ) * 1000
                await self._emit_metrics(
                    {
                        "org_id": org_id,
                        "cache_hit": True,
                        "query": query,
                        "context": context,
                        "relationship_types": relationship_types,
                        "top_k": top_k,
                        "weight_vector": weight_vector,
                        "weight_graph": weight_graph,
                        "result_count": cached_response.total_results,
                        "execution_time_ms": cached_response.execution_time_ms,
                    }
                )
                return cached_response

        logger.info(
            f"Hybrid search: org={org_id}, query='{query[:50]}...', "
            f"weights=({weight_vector:.1f}, {weight_graph:.1f})"
        )

        # Execute both searches in parallel
        vector_task = self.vector_tool.search(query, org_id, context, top_k)
        graph_task = self.graph_tool.search(query, org_id, relationship_types, top_k * 2)

        vector_response, graph_response = await asyncio.gather(
            vector_task,
            graph_task,
            return_exceptions=False,
        )

        vector_latency_ms = vector_response.execution_time_ms
        graph_latency_ms = graph_response.execution_time_ms

        # Apply reciprocal rank fusion
        k = 60  # Standard RRF constant

        # Score vector results
        vector_scores: Dict[str, tuple[VectorSearchResult, float]] = {}
        for rank, result in enumerate(vector_response.results, start=1):
            rrf_score = weight_vector / (rank + k)
            key = f"chunk:{result.chunk_id}"
            vector_scores[key] = (result, rrf_score)

        # Score graph nodes
        graph_scores: Dict[str, tuple[GraphNode, float]] = {}
        for rank, node in enumerate(graph_response.nodes, start=1):
            rrf_score = weight_graph / (rank + k)
            key = f"node:{node.entity_id}"
            graph_scores[key] = (node, rrf_score)

        # Merge and sort by score
        merged_results: List[HybridSearchResult] = []

        for key, (vector_result, score) in vector_scores.items():
            merged_results.append(
                HybridSearchResult(
                    source_type="vector",
                    content=vector_result.content,
                    score=score,
                    metadata={
                        "chunk_id": str(vector_result.chunk_id),
                        "document_id": str(vector_result.document_id),
                        "page_number": vector_result.page_number,
                        "section_title": vector_result.section_title,
                        "similarity_score": vector_result.similarity_score,
                        **vector_result.metadata,
                    },
                )
            )

        for key, (graph_node, score) in graph_scores.items():
            # Find related relationships for context
            related_rels = [
                rel for rel in graph_response.relationships
                if rel.start_node.entity_id == graph_node.entity_id
                or rel.end_node.entity_id == graph_node.entity_id
            ]

            content_parts = [f"{graph_node.entity_type}: {graph_node.name}"]
            if related_rels:
                content_parts.append(
                    f"Relaciones: {', '.join([rel.relationship_type for rel in related_rels[:3]])}"
                )

            merged_results.append(
                HybridSearchResult(
                    source_type="graph",
                    content=" | ".join(content_parts),
                    score=score,
                    metadata={
                        "entity_id": graph_node.entity_id,
                        "entity_type": graph_node.entity_type,
                        "name": graph_node.name,
                        "relationship_count": len(related_rels),
                        **graph_node.properties,
                    },
                )
            )

        # Sort by score descending and take top_k
        merged_results.sort(key=lambda r: r.score, reverse=True)
        merged_results = merged_results[:top_k]

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Hybrid search completed: {len(merged_results)} fused results "
            f"({len(vector_scores)} vector + {len(graph_scores)} graph) "
            f"in {execution_time_ms:.1f}ms"
        )

        overrides = {
            "context": context,
            "relationship_types": relationship_types,
            "top_k": top_k,
            "weight_vector": weight_vector,
            "weight_graph": weight_graph,
        }

        response = HybridSearchResponse(
            results=merged_results,
            vector_results=vector_response.results,
            graph_nodes=graph_response.nodes,
            graph_relationships=graph_response.relationships,
            query=query,
            org_id=org_id,
            context=context,
            weight_vector=weight_vector,
            weight_graph=weight_graph,
            total_results=len(merged_results),
            execution_time_ms=execution_time_ms,
            cache_hit=cache_hit,
            overrides_applied=overrides,
        )

        if self.result_cache:
            await self.result_cache.set(
                cache_key,
                response,
                metadata={"org_id": org_id},
            )

        await self._emit_metrics(
            {
                "org_id": org_id,
                "cache_hit": cache_hit,
                "query": query,
                "context": context,
                "relationship_types": relationship_types,
                "top_k": top_k,
                "weight_vector": weight_vector,
                "weight_graph": weight_graph,
                "result_count": len(merged_results),
                "execution_time_ms": execution_time_ms,
                "vector_latency_ms": vector_latency_ms,
                "graph_latency_ms": graph_latency_ms,
            }
        )

        return response


async def hybrid_search(
    query: str,
    org_id: str,
    context: Optional[str] = None,
    relationship_types: Optional[List[str]] = None,
    top_k: int = 5,
    weight_vector: float = 0.5,
    weight_graph: float = 0.5,
    db_pool: Optional[asyncpg.Pool] = None,
    neo4j_driver: Optional[AsyncDriver] = None,
    openai_client: Optional[AsyncOpenAI] = None,
    result_cache: Optional[ResultCache] = None,
    vector_cache: Optional[ResultCache] = None,
    graph_cache: Optional[ResultCache] = None,
    instrumentation_hook: Optional[InstrumentationHook] = None,
) -> HybridSearchResponse:
    """
    Standalone function interface for hybrid search

    This function is designed to be registered as a Pydantic AI tool.

    Args:
        query: Search query
        org_id: Organization identifier
        context: Optional business context
        relationship_types: Optional graph relationship filters
        top_k: Number of results
        weight_vector: Vector search weight
        weight_graph: Graph search weight
        db_pool: Database pool (injected by agent)
        neo4j_driver: Neo4j driver (injected by agent)
        openai_client: OpenAI client (injected by agent)

    Returns:
        HybridSearchResponse
    """
    if db_pool is None or neo4j_driver is None or openai_client is None:
        raise ValueError("db_pool, neo4j_driver, and openai_client must be provided")

    tool = HybridSearchTool(
        db_pool=db_pool,
        neo4j_driver=neo4j_driver,
        openai_client=openai_client,
        result_cache=result_cache or _HYBRID_RESULT_CACHE,
        vector_cache=vector_cache,
        graph_cache=graph_cache,
        instrumentation_hook=instrumentation_hook,
    )
    return await tool.search(
        query,
        org_id,
        context,
        relationship_types,
        top_k,
        weight_vector,
        weight_graph,
    )
