"""
Pydantic AI Agent Orchestrator for RAG 2.0
Task 10: Implement Pydantic AI Agent Orchestrator

Provides intelligent retrieval tool selection combining vector search (pgvector)
and graph queries (Neo4j) with Spanish-first operation and budget awareness.

Requirements: R6.1-R6.7, R0.3
"""
import os
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from pathlib import Path

import asyncpg
from neo4j import AsyncGraphDatabase, AsyncDriver
from openai import AsyncOpenAI
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel

from agent.session import SessionManager, ConversationSession
from agent.telemetry import ToolTelemetryLogger
from agent.tools.vector_search import vector_search
from agent.tools.graph_search import graph_search
from agent.tools.hybrid_search import hybrid_search
from agent.tools.checkpoint_lookup import checkpoint_lookup
from intelligence_capture.context_registry import ContextRegistry

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """
    Configuration for RAG Agent

    Attributes:
        primary_model: Primary LLM model (gpt-4o-mini for cost efficiency)
        fallback_model: Fallback LLM model (gpt-4o for complex queries)
        embedding_model: Embedding model for vector search
        max_conversation_turns: Max turns to keep in context
        temperature: LLM temperature (0.0-1.0)
        system_prompt_path: Path to system agent prompt
    """
    primary_model: str = "gpt-4o-mini"
    fallback_model: str = "gpt-4o"
    embedding_model: str = "text-embedding-3-small"
    max_conversation_turns: int = 5
    temperature: float = 0.1  # Low temperature for factual responses
    system_prompt_path: Optional[Path] = None

    def load_system_prompt(self) -> str:
        """Load system prompt from file"""
        if self.system_prompt_path is None:
            # Default to prompts/system_agent_prompt.md
            self.system_prompt_path = (
                Path(__file__).resolve().parent.parent / "prompts" / "system_agent_prompt.md"
            )

        if not self.system_prompt_path.exists():
            logger.warning(f"System prompt not found: {self.system_prompt_path}")
            return self._default_system_prompt()

        with open(self.system_prompt_path, "r", encoding="utf-8") as f:
            return f.read()

    @staticmethod
    def _default_system_prompt() -> str:
        """Fallback system prompt if file not found"""
        return """
        Eres el Director de Inteligencia de Comversa. Operas en español.

        Usa las herramientas de búsqueda (vector_search, graph_search, hybrid_search)
        para responder preguntas con evidencia citada. Respeta el presupuesto mensual
        de $500-$1,000 USD y las obligaciones de privacidad boliviana.
        """


class RAGAgent:
    """
    Pydantic AI Agent Orchestrator for RAG 2.0

    Integrates:
    - Pydantic AI agent framework with tool calling
    - Vector search (pgvector) for document chunks
    - Graph search (Neo4j) for entity relationships
    - Hybrid search with reciprocal rank fusion
    - Multi-turn conversation memory
    - Tool telemetry and cost tracking
    - Spanish-first operation with LLM fallback chain

    Requirements: R6.1-R6.7, R0.3
    """

    def __init__(
        self,
        config: AgentConfig,
        db_pool: asyncpg.Pool,
        neo4j_driver: AsyncDriver,
        openai_client: AsyncOpenAI,
        context_registry: ContextRegistry,
    ):
        """
        Initialize RAG Agent

        Args:
            config: Agent configuration
            db_pool: PostgreSQL connection pool
            neo4j_driver: Neo4j async driver
            openai_client: OpenAI client
            context_registry: Context registry for org lookup
        """
        self.config = config
        self.db_pool = db_pool
        self.neo4j_driver = neo4j_driver
        self.openai_client = openai_client
        self.context_registry = context_registry

        # Initialize session manager and telemetry
        self.session_manager = SessionManager(db_pool)
        self.telemetry = ToolTelemetryLogger(db_pool)

        # Load system prompt
        system_prompt = config.load_system_prompt()

        # Create Pydantic AI agent with primary model
        self.agent = Agent(
            model=OpenAIModel(config.primary_model),
            system_prompt=system_prompt,
        )

        # Register tools with the agent
        self._register_tools()

        logger.info(
            f"RAG Agent initialized: model={config.primary_model}, "
            f"fallback={config.fallback_model}"
        )

    def _register_tools(self):
        """Register retrieval tools with Pydantic AI agent"""
        # Note: Tool registration depends on pydantic-ai version
        # This is a simplified example - adjust based on actual API

        @self.agent.tool
        async def vector_search_tool(query: str, org_id: str, context: str = None, top_k: int = 5):
            """
            Search document chunks using vector similarity.
            Use for specific facts, quotes, or verbatim evidence.
            """
            import time
            start_time = time.perf_counter()

            try:
                response = await vector_search(
                    query=query,
                    org_id=org_id,
                    context=context,
                    top_k=top_k,
                    db_pool=self.db_pool,
                    openai_client=self.openai_client,
                )

                await self.telemetry.log_tool_usage(
                    session_id="current",  # TODO: inject session_id
                    org_id=org_id,
                    tool_name="vector_search",
                    query=query,
                    parameters={"context": context, "top_k": top_k},
                    success=True,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=response.total_found,
                )

                return response

            except Exception as exc:
                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="vector_search",
                    query=query,
                    parameters={"context": context, "top_k": top_k},
                    success=False,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=0,
                    error_message=str(exc),
                )
                raise

        @self.agent.tool
        async def graph_search_tool(
            query: str,
            org_id: str,
            relationship_types: List[str] = None,
            limit: int = 20,
        ):
            """
            Search knowledge graph for entity relationships.
            Use for cross-entity questions like "What systems cause pain points?"
            """
            import time
            start_time = time.perf_counter()

            try:
                response = await graph_search(
                    query=query,
                    org_id=org_id,
                    relationship_types=relationship_types,
                    limit=limit,
                    neo4j_driver=self.neo4j_driver,
                )

                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="graph_search",
                    query=query,
                    parameters={"relationship_types": relationship_types, "limit": limit},
                    success=True,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=response.total_nodes,
                )

                return response

            except Exception as exc:
                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="graph_search",
                    query=query,
                    parameters={"relationship_types": relationship_types, "limit": limit},
                    success=False,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=0,
                    error_message=str(exc),
                )
                raise

        @self.agent.tool
        async def hybrid_search_tool(
            query: str,
            org_id: str,
            context: str = None,
            relationship_types: List[str] = None,
            top_k: int = 5,
            weight_vector: float = 0.5,
            weight_graph: float = 0.5,
        ):
            """
            Combined vector + graph search with reciprocal rank fusion.
            Use for executive briefings or comprehensive analysis.
            Default weighting: 50/50, adjust based on question type.
            """
            import time
            start_time = time.perf_counter()

            try:
                response = await hybrid_search(
                    query=query,
                    org_id=org_id,
                    context=context,
                    relationship_types=relationship_types,
                    top_k=top_k,
                    weight_vector=weight_vector,
                    weight_graph=weight_graph,
                    db_pool=self.db_pool,
                    neo4j_driver=self.neo4j_driver,
                    openai_client=self.openai_client,
                )

                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="hybrid_search",
                    query=query,
                    parameters={
                        "context": context,
                        "relationship_types": relationship_types,
                        "top_k": top_k,
                        "weight_vector": weight_vector,
                        "weight_graph": weight_graph,
                    },
                    success=True,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=response.total_results,
                )

                return response

            except Exception as exc:
                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="hybrid_search",
                    query=query,
                    parameters={
                        "context": context,
                        "relationship_types": relationship_types,
                        "top_k": top_k,
                        "weight_vector": weight_vector,
                        "weight_graph": weight_graph,
                    },
                    success=False,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=0,
                    error_message=str(exc),
                )
                raise

        @self.agent.tool
        async def checkpoint_lookup_tool(stage: str, org_id: str, limit: int = 10):
            """
            Lookup governance checkpoints for compliance review.
            Use when asked about approved models, recent evaluations, or Habeas Data.
            """
            import time
            start_time = time.perf_counter()

            try:
                response = await checkpoint_lookup(
                    stage=stage,
                    org_id=org_id,
                    limit=limit,
                )

                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="checkpoint_lookup",
                    query=f"stage={stage}",
                    parameters={"stage": stage, "limit": limit},
                    success=True,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=response.total_found,
                )

                return response

            except Exception as exc:
                await self.telemetry.log_tool_usage(
                    session_id="current",
                    org_id=org_id,
                    tool_name="checkpoint_lookup",
                    query=f"stage={stage}",
                    parameters={"stage": stage, "limit": limit},
                    success=False,
                    execution_time_ms=(time.perf_counter() - start_time) * 1000,
                    result_count=0,
                    error_message=str(exc),
                )
                raise

        logger.info("Tools registered with Pydantic AI agent")

    async def query(
        self,
        query: str,
        org_id: str,
        context: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a query with the RAG agent

        Args:
            query: User query in Spanish
            org_id: Organization namespace
            context: Optional business context
            session_id: Optional session ID for conversation context

        Returns:
            Dict with answer, sources, tool_calls, and metadata
        """
        # Get or create session
        session = await self.session_manager.get_or_create_session(
            session_id, org_id, context
        )

        # Add user message
        await self.session_manager.add_message_and_save(
            session, "user", query
        )

        # Get conversation context
        context_messages = session.get_context_messages(
            max_turns=self.config.max_conversation_turns
        )

        try:
            # Run agent with conversation context
            # Note: Exact API depends on pydantic-ai version
            result = await self.agent.run(
                query,
                message_history=context_messages,
            )

            # Extract answer and tool calls
            answer = result.data if hasattr(result, 'data') else str(result)
            tool_calls = getattr(result, 'tool_calls', [])

            # Add assistant message
            await self.session_manager.add_message_and_save(
                session, "assistant", answer, {"tool_calls": tool_calls}
            )

            return {
                "answer": answer,
                "session_id": session.session_id,
                "tool_calls": tool_calls,
                "model": self.config.primary_model,
            }

        except Exception as exc:
            logger.error(f"Agent query failed: {exc}")

            # Try fallback to gpt-4o if primary model fails
            if self.config.fallback_model != self.config.primary_model:
                logger.info(f"Attempting fallback to {self.config.fallback_model}")

                try:
                    fallback_agent = Agent(
                        model=OpenAIModel(self.config.fallback_model),
                        system_prompt=self.config.load_system_prompt(),
                    )

                    result = await fallback_agent.run(
                        query,
                        message_history=context_messages,
                    )

                    answer = result.data if hasattr(result, 'data') else str(result)

                    await self.session_manager.add_message_and_save(
                        session, "assistant", answer, {"fallback": True}
                    )

                    return {
                        "answer": answer,
                        "session_id": session.session_id,
                        "model": self.config.fallback_model,
                        "fallback": True,
                    }

                except Exception as fallback_exc:
                    logger.error(f"Fallback also failed: {fallback_exc}")

            # Return error response
            error_msg = (
                f"Lo siento, no pude procesar tu consulta. "
                f"Error: {str(exc)}"
            )

            await self.session_manager.add_message_and_save(
                session, "assistant", error_msg, {"error": str(exc)}
            )

            return {
                "answer": error_msg,
                "session_id": session.session_id,
                "error": str(exc),
            }

    async def close(self):
        """Close connections"""
        if self.db_pool:
            await self.db_pool.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()

    @classmethod
    async def create(
        cls,
        config: Optional[AgentConfig] = None,
        db_url: Optional[str] = None,
        neo4j_uri: Optional[str] = None,
        neo4j_user: Optional[str] = None,
        neo4j_password: Optional[str] = None,
        openai_api_key: Optional[str] = None,
    ) -> "RAGAgent":
        """
        Factory method to create RAG Agent with connections

        Args:
            config: Agent configuration
            db_url: PostgreSQL connection URL
            neo4j_uri: Neo4j connection URI
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
            openai_api_key: OpenAI API key

        Returns:
            Initialized RAGAgent
        """
        if config is None:
            config = AgentConfig()

        # Get connection details from environment if not provided
        db_url = db_url or os.getenv("DATABASE_URL")
        neo4j_uri = neo4j_uri or os.getenv("NEO4J_URI")
        neo4j_user = neo4j_user or os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = neo4j_password or os.getenv("NEO4J_PASSWORD")
        openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")

        if not all([db_url, neo4j_uri, neo4j_password, openai_api_key]):
            raise ValueError(
                "Missing required environment variables: "
                "DATABASE_URL, NEO4J_URI, NEO4J_PASSWORD, OPENAI_API_KEY"
            )

        # Create connections
        db_pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10)
        neo4j_driver = AsyncGraphDatabase.driver(
            neo4j_uri,
            auth=(neo4j_user, neo4j_password),
        )
        openai_client = AsyncOpenAI(api_key=openai_api_key)

        # Create context registry
        context_registry = ContextRegistry(db_url)
        await context_registry.initialize()

        return cls(config, db_pool, neo4j_driver, openai_client, context_registry)
