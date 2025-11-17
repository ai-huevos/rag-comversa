#!/bin/bash
# Quick Stats - One-time snapshot of agent activity

echo "📊 RAG AGENT QUICK STATS"
echo "========================"
echo ""

echo "🔧 Tool Calls (last hour):"
psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM tool_usage_logs WHERE timestamp > now() - interval '1 hour'" 2>/dev/null || echo "Error: Cannot connect to database"

echo ""
echo "💬 Active Sessions:"
psql $DATABASE_URL -t -c "SELECT COUNT(*) FROM chat_sessions WHERE updated_at > now() - interval '1 hour'" 2>/dev/null || echo "Error: Cannot connect to database"

echo ""
echo "🌐 Neo4j Entities:"
cypher-shell -u neo4j -p $NEO4J_PASSWORD "MATCH (n:Entity) RETURN count(n)" 2>/dev/null | tail -1 || echo "Error: Cannot connect to Neo4j"

echo ""
echo "✅ Stats complete"
