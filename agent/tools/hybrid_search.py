"""
Hybrid Search Tool combining vector and graph search
Uses reciprocal rank fusion to merge results from both retrieval methods
"""
import asyncio
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

import asyncpg
from neo4j import AsyncDriver
from openai import AsyncOpenAI

from agent.tools.vector_search import VectorSearchTool, VectorSearchResult
from agent.tools.graph_search import GraphSearchTool, GraphNode, GraphRelationship

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
    ):
        """
        Initialize hybrid search tool

        Args:
            db_pool: PostgreSQL connection pool
            neo4j_driver: Neo4j async driver
            openai_client: OpenAI client for embeddings
        """
        self.vector_tool = VectorSearchTool(db_pool, openai_client)
        self.graph_tool = GraphSearchTool(neo4j_driver)

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
        import time
        start_time = time.perf_counter()

        logger.info(
            f"Hybrid search: org={org_id}, query='{query[:50]}...', "
            f"weights=({weight_vector:.1f}, {weight_graph:.1f})"
        )

        # Execute both searches in parallel
        vector_task = self.vector_tool.search(query, org_id, context, top_k)
        graph_task = self.graph_tool.search(query, org_id, relationship_types, top_k * 2)

        vector_response, graph_response = await asyncio.gather(
            vector_task, graph_task, return_exceptions=False
        )

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

        return HybridSearchResponse(
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
        )


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

    tool = HybridSearchTool(db_pool, neo4j_driver, openai_client)
    return await tool.search(
        query, org_id, context, relationship_types, top_k, weight_vector, weight_graph
    )
