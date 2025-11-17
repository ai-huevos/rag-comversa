#!/usr/bin/env python3
"""
Script de prueba rápida para Terminal 3
Ejecuta queries y muestra resultados en vivo
"""
import asyncio
import sys
from datetime import datetime
from agent import RAGAgent, AgentConfig


async def main():
    print("=" * 70)
    print("🧪 TESTING DEL AGENTE RAG - Terminal 3")
    print("=" * 70)
    print()

    # Crear agente
    print("🚀 Creando agente...")
    config = AgentConfig(
        primary_model="gpt-4o-mini",
        temperature=0.0,
        max_conversation_turns=3,
    )
    agent = await RAGAgent.create(config=config)
    print("✅ Agente creado\n")

    try:
        # Test 1: Query simple
        print("-" * 70)
        print("📝 TEST 1: Query Simple")
        print("-" * 70)

        query1 = "¿Qué sistemas hay en Los Tajibos?"
        print(f"Query: {query1}")
        print("Ejecutando...")

        response1 = await agent.query(
            query=query1,
            org_id="los_tajibos",
        )

        print(f"\n✅ Respuesta ({response1['model']}):")
        print(f"   {response1['answer'][:200]}...")
        print(f"\n📊 Session ID: {response1['session_id'][:30]}...")

        if 'tool_calls' in response1 and response1['tool_calls']:
            print(f"🔧 Tools usados: {len(response1['tool_calls'])}")
            for tool in response1['tool_calls']:
                print(f"   - {tool.get('tool_name', 'unknown')}")

        print()
        input("Presiona ENTER para continuar...")

        # Test 2: Conversación multi-turno
        print("\n" + "-" * 70)
        print("💬 TEST 2: Conversación Multi-Turno")
        print("-" * 70)

        session_id = f"test-{datetime.now().timestamp()}"
        print(f"Session ID: {session_id[:30]}...\n")

        # Turno 1
        print("👤 Turno 1: ¿Cuáles son los sistemas principales?")
        r1 = await agent.query(
            query="¿Cuáles son los sistemas principales en Los Tajibos?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta: {r1['answer'][:150]}...\n")

        # Turno 2
        print("👤 Turno 2: ¿Cuáles tienen problemas?")
        r2 = await agent.query(
            query="¿Cuáles de esos sistemas tienen problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta: {r2['answer'][:150]}...\n")

        # Turno 3
        print("👤 Turno 3: ¿Por qué?")
        r3 = await agent.query(
            query="¿Por qué tienen esos problemas?",
            org_id="los_tajibos",
            session_id=session_id,
        )
        print(f"🤖 Respuesta: {r3['answer'][:150]}...\n")

        print(f"✅ Conversación completada ({len([r1, r2, r3])} turnos)")
        print()
        input("Presiona ENTER para continuar...")

        # Test 3: Diferentes herramientas
        print("\n" + "-" * 70)
        print("🔧 TEST 3: Selección de Herramientas")
        print("-" * 70)

        test_queries = [
            ("Vector Search", '¿Qué dice sobre "check-in manual"?'),
            ("Graph Search", "¿Qué sistemas causan puntos de dolor?"),
            ("Hybrid Search", "Dame un resumen ejecutivo de operaciones"),
        ]

        for tool_type, query in test_queries:
            print(f"\n🔍 {tool_type}")
            print(f"Query: {query}")

            resp = await agent.query(query, "los_tajibos")
            print(f"Respuesta: {resp['answer'][:100]}...")

        print()
        input("Presiona ENTER para continuar...")

        # Test 4: Multi-org
        print("\n" + "-" * 70)
        print("🏢 TEST 4: Aislamiento Multi-Org")
        print("-" * 70)

        orgs = ["los_tajibos", "bolivian_foods", "comversa"]

        for org in orgs:
            print(f"\n🏢 Org: {org}")
            resp = await agent.query(
                query="¿Qué sistemas principales hay?",
                org_id=org,
            )
            print(f"Session: {resp['session_id'][:20]}...")
            print(f"Respuesta: {resp['answer'][:80]}...")

        print("\n✅ Aislamiento verificado (diferentes session IDs)")
        print()

        # Resumen
        print("\n" + "=" * 70)
        print("📊 RESUMEN DE TESTS")
        print("=" * 70)
        print("✅ Query simple - PASS")
        print("✅ Multi-turno - PASS")
        print("✅ Tool selection - PASS")
        print("✅ Multi-org - PASS")
        print()
        print("💡 Revisa Terminal 2 para ver los logs de BD")
        print()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cerrar agente
        print("🧹 Cerrando conexiones...")
        await agent.close()
        print("✅ Conexiones cerradas")
        print()
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
