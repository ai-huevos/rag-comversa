"""
Example usage of Pydantic AI RAG Agent
Task 10: Implement Pydantic AI Agent Orchestrator

This script demonstrates how to use the RAG agent for intelligent retrieval
combining vector search (pgvector) and graph queries (Neo4j).
"""
import asyncio
import logging
from agent import RAGAgent, AgentConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


async def example_single_query():
    """Example: Single query with automatic tool selection"""
    logger.info("=== Example 1: Single Query ===")

    # Create agent with default configuration
    agent = await RAGAgent.create()

    try:
        # Execute query - agent will select appropriate tool
        response = await agent.query(
            query="¿Qué sistemas causan más puntos de dolor en Los Tajibos?",
            org_id="los_tajibos",
            context="operaciones",
        )

        print(f"\nQuery: {response.get('query', 'N/A')}")
        print(f"Answer: {response['answer']}")
        print(f"Model: {response['model']}")
        print(f"Session ID: {response['session_id']}")

        if 'tool_calls' in response:
            print(f"\nTools used: {len(response['tool_calls'])} tool calls")
            for i, tool_call in enumerate(response['tool_calls'], 1):
                print(f"  {i}. {tool_call.get('tool_name', 'unknown')}")

    finally:
        await agent.close()

    logger.info("Example 1 complete\n")


async def example_multi_turn_conversation():
    """Example: Multi-turn conversation with session context"""
    logger.info("=== Example 2: Multi-Turn Conversation ===")

    agent = await RAGAgent.create()

    try:
        session_id = "demo-session-001"

        # First turn: Initial question
        response1 = await agent.query(
            query="¿Cuáles son los principales sistemas usados en Los Tajibos?",
            org_id="los_tajibos",
            session_id=session_id,
        )

        print(f"\nTurn 1:")
        print(f"Q: ¿Cuáles son los principales sistemas usados en Los Tajibos?")
        print(f"A: {response1['answer'][:200]}...")

        # Second turn: Follow-up question (uses context)
        response2 = await agent.query(
            query="¿Cuáles de esos sistemas tienen problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )

        print(f"\nTurn 2:")
        print(f"Q: ¿Cuáles de esos sistemas tienen problemas?")
        print(f"A: {response2['answer'][:200]}...")

        # Third turn: Deeper question
        response3 = await agent.query(
            query="¿Qué departamentos se ven más afectados?",
            org_id="los_tajibos",
            session_id=session_id,
        )

        print(f"\nTurn 3:")
        print(f"Q: ¿Qué departamentos se ven más afectados?")
        print(f"A: {response3['answer'][:200]}...")

    finally:
        await agent.close()

    logger.info("Example 2 complete\n")


async def example_custom_configuration():
    """Example: Custom agent configuration"""
    logger.info("=== Example 3: Custom Configuration ===")

    # Create custom configuration
    config = AgentConfig(
        primary_model="gpt-4o-mini",
        fallback_model="gpt-4o",
        embedding_model="text-embedding-3-small",
        max_conversation_turns=3,  # Keep less context
        temperature=0.0,  # Deterministic responses
    )

    agent = await RAGAgent.create(config=config)

    try:
        response = await agent.query(
            query="Dame un resumen ejecutivo de los sistemas y procesos consolidados",
            org_id="bolivian_foods",
            context="digital_transformation",
        )

        print(f"\nConfig: {config.primary_model} @ temp={config.temperature}")
        print(f"Answer: {response['answer'][:300]}...")

    finally:
        await agent.close()

    logger.info("Example 3 complete\n")


async def example_tool_statistics():
    """Example: Check tool usage statistics"""
    logger.info("=== Example 4: Tool Statistics ===")

    agent = await RAGAgent.create()

    try:
        # Execute a few queries
        for query in [
            "¿Qué dice el contrato sobre plazos?",
            "¿Qué sistemas están relacionados con el proceso de check-in?",
            "Dame un análisis completo de las operaciones hoteleras",
        ]:
            await agent.query(query, org_id="los_tajibos")

        # Get statistics
        stats = await agent.telemetry.get_tool_stats(
            org_id="los_tajibos",
            hours=1,
        )

        print("\nTool Usage Statistics (last hour):")
        for tool_name, metrics in stats.items():
            print(f"\n{tool_name}:")
            print(f"  Total calls: {metrics['total_calls']}")
            print(f"  Success rate: {metrics['success_rate']:.1%}")
            print(f"  Avg time: {metrics['avg_time_ms']:.1f}ms")
            print(f"  Total results: {metrics['total_results']}")
            if metrics['total_cost_cents']:
                print(f"  Total cost: ${metrics['total_cost_cents']/100:.4f}")

    finally:
        await agent.close()

    logger.info("Example 4 complete\n")


async def example_checkpoint_lookup():
    """Example: Lookup governance checkpoints"""
    logger.info("=== Example 5: Checkpoint Lookup ===")

    agent = await RAGAgent.create()

    try:
        # Query for checkpoint status
        response = await agent.query(
            query="¿Cuál es el estado de los checkpoints de consolidación?",
            org_id="los_tajibos",
        )

        print(f"\nCheckpoint Query Result:")
        print(response['answer'])

    finally:
        await agent.close()

    logger.info("Example 5 complete\n")


async def main():
    """Run all examples"""
    print("=" * 70)
    print("Pydantic AI RAG Agent - Examples")
    print("Task 10: Implement Pydantic AI Agent Orchestrator")
    print("=" * 70)

    # Run examples
    await example_single_query()
    await example_multi_turn_conversation()
    await example_custom_configuration()
    await example_tool_statistics()
    await example_checkpoint_lookup()

    print("=" * 70)
    print("All examples completed!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
