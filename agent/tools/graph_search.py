"""
Graph Search Tool for Neo4j knowledge graph queries
Queries consolidated entities and relationships with Cypher
"""
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from neo4j import AsyncDriver

from agent.tools.cache import ResultCache
from agent.tools.instrumentation import (
    InstrumentationHook,
    call_instrumentation_hook,
)

logger = logging.getLogger(__name__)


@dataclass
class GraphNode:
    """Represents a node in the knowledge graph"""
    entity_id: str
    entity_type: str
    name: str
    org_id: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphRelationship:
    """Represents a relationship in the knowledge graph"""
    start_node: GraphNode
    end_node: GraphNode
    relationship_type: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphSearchResponse:
    """Response from graph search"""
    nodes: List[GraphNode]
    relationships: List[GraphRelationship]
    query: str
    org_id: str
    relationship_types: Optional[List[str]]
    total_nodes: int
    total_relationships: int
    execution_time_ms: float
    cypher_query: str
    cache_hit: bool = False


_GRAPH_RESULT_CACHE = ResultCache()


class GraphSearchTool:
    """
    Neo4j graph search tool for relationship queries

    Queries consolidated entities and relationships with org_id namespace
    isolation. Useful for cross-entity questions like "What systems cause
    the most pain points?"
    """

    def __init__(
        self,
        neo4j_driver: AsyncDriver,
        result_cache: Optional[ResultCache] = None,
        instrumentation_hook: Optional[InstrumentationHook] = None,
    ):
        """
        Initialize graph search tool

        Args:
            neo4j_driver: Async Neo4j driver
        """
        self.driver = neo4j_driver
        self.result_cache = result_cache or ResultCache()
        self.instrumentation_hook = instrumentation_hook

    @staticmethod
    def _build_cache_key(
        query: str,
        org_id: str,
        relationship_types: Optional[List[str]],
        limit: int,
    ) -> str:
        """Construct cache key for graph search queries."""
        payload = {
            "query": query,
            "org_id": org_id,
            "relationship_types": relationship_types or [],
            "limit": limit,
        }
        return ResultCache.build_key("graph_search", payload)

    async def _emit_metrics(self, data: Dict[str, Any]) -> None:
        """Emit instrumentation metrics if hook configured."""
        await call_instrumentation_hook(
            self.instrumentation_hook,
            "graph_search",
            data,
        )

    async def search(
        self,
        query: str,
        org_id: str,
        relationship_types: Optional[List[str]] = None,
        limit: int = 20,
    ) -> GraphSearchResponse:
        """
        Execute graph relationship search

        Args:
            query: Natural language query for semantic matching on node names
            org_id: Organization namespace filter
            relationship_types: Optional list of relationship types to filter
            limit: Max nodes to return

        Returns:
            GraphSearchResponse with nodes and relationships
        """
        start_time = time.perf_counter()
        cache_key = self._build_cache_key(query, org_id, relationship_types, limit)
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
                        "relationship_types": relationship_types,
                        "limit": limit,
                        "total_nodes": cached_response.total_nodes,
                        "execution_time_ms": cached_response.execution_time_ms,
                    }
                )
                return cached_response

        logger.info(
            f"Graph search: org={org_id}, query='{query[:50]}...', "
            f"rel_types={relationship_types}, limit={limit}"
        )

        # Build Cypher query based on relationship types
        if relationship_types:
            rel_filter = " OR ".join([f"type(r) = '{rt}'" for rt in relationship_types])
            cypher_query = f"""
                MATCH (start:Entity)-[r]->(end:Entity)
                WHERE start.org_id = $org_id
                  AND end.org_id = $org_id
                  AND ({rel_filter})
                  AND (
                    toLower(start.name) CONTAINS toLower($query)
                    OR toLower(end.name) CONTAINS toLower($query)
                  )
                RETURN start, r, end
                LIMIT $limit
            """
        else:
            cypher_query = """
                MATCH (start:Entity)-[r]->(end:Entity)
                WHERE start.org_id = $org_id
                  AND end.org_id = $org_id
                  AND (
                    toLower(start.name) CONTAINS toLower($query)
                    OR toLower(end.name) CONTAINS toLower($query)
                  )
                RETURN start, r, end
                LIMIT $limit
            """

        nodes_dict: Dict[str, GraphNode] = {}
        relationships: List[GraphRelationship] = []

        async with self.driver.session() as session:
            result = await session.run(
                cypher_query,
                org_id=org_id,
                query=query,
                limit=limit,
            )

            records = await result.data()

            for record in records:
                # Extract start node
                start_data = record["start"]
                start_id = start_data.get("external_id", str(start_data.id))

                if start_id not in nodes_dict:
                    nodes_dict[start_id] = GraphNode(
                        entity_id=start_id,
                        entity_type=start_data.get("entity_type", "Unknown"),
                        name=start_data.get("name", ""),
                        org_id=start_data.get("org_id", org_id),
                        properties={
                            k: v for k, v in start_data.items()
                            if k not in ["external_id", "entity_type", "name", "org_id"]
                        },
                    )

                # Extract end node
                end_data = record["end"]
                end_id = end_data.get("external_id", str(end_data.id))

                if end_id not in nodes_dict:
                    nodes_dict[end_id] = GraphNode(
                        entity_id=end_id,
                        entity_type=end_data.get("entity_type", "Unknown"),
                        name=end_data.get("name", ""),
                        org_id=end_data.get("org_id", org_id),
                        properties={
                            k: v for k, v in end_data.items()
                            if k not in ["external_id", "entity_type", "name", "org_id"]
                        },
                    )

                # Extract relationship
                rel_data = record["r"]
                relationships.append(
                    GraphRelationship(
                        start_node=nodes_dict[start_id],
                        end_node=nodes_dict[end_id],
                        relationship_type=rel_data.type,
                        properties=dict(rel_data.items()),
                    )
                )

        execution_time_ms = (time.perf_counter() - start_time) * 1000

        logger.info(
            f"Graph search completed: {len(nodes_dict)} nodes, "
            f"{len(relationships)} relationships in {execution_time_ms:.1f}ms"
        )

        response = GraphSearchResponse(
            nodes=list(nodes_dict.values()),
            relationships=relationships,
            query=query,
            org_id=org_id,
            relationship_types=relationship_types,
            total_nodes=len(nodes_dict),
            total_relationships=len(relationships),
            execution_time_ms=execution_time_ms,
            cypher_query=cypher_query,
            cache_hit=cache_hit,
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
                "relationship_types": relationship_types,
                "limit": limit,
                "total_nodes": len(nodes_dict),
                "total_relationships": len(relationships),
                "execution_time_ms": execution_time_ms,
            }
        )

        return response


async def graph_search(
    query: str,
    org_id: str,
    relationship_types: Optional[List[str]] = None,
    limit: int = 20,
    neo4j_driver: Optional[AsyncDriver] = None,
    result_cache: Optional[ResultCache] = None,
    instrumentation_hook: Optional[InstrumentationHook] = None,
) -> GraphSearchResponse:
    """
    Standalone function interface for graph search

    This function is designed to be registered as a Pydantic AI tool.

    Args:
        query: Search query for matching node names
        org_id: Organization identifier
        relationship_types: Optional relationship type filters
        limit: Max nodes to return
        neo4j_driver: Neo4j driver (injected by agent)

    Returns:
        GraphSearchResponse
    """
    if neo4j_driver is None:
        raise ValueError("neo4j_driver must be provided")

    tool = GraphSearchTool(
        neo4j_driver=neo4j_driver,
        result_cache=result_cache or _GRAPH_RESULT_CACHE,
        instrumentation_hook=instrumentation_hook,
    )
    return await tool.search(query, org_id, relationship_types, limit)
