#!/bin/bash
# Database Activity Monitor for RAG Agent Testing
# Terminal 2 - Real-time monitoring of PostgreSQL tool usage and sessions

while true; do
  clear
  echo "════════════════════════════════════════════════════════════════════"
  echo "📊 MONITOR DEL AGENTE RAG - $(date '+%H:%M:%S')"
  echo "════════════════════════════════════════════════════════════════════"
  echo ""

  echo "🔧 ÚLTIMOS TOOL CALLS (10 segundos):"
  psql $DATABASE_URL -c "
    SELECT
      to_char(timestamp, 'HH24:MI:SS') as time,
      tool_name,
      CASE WHEN success THEN '✅' ELSE '❌' END as status,
      execution_time_ms::int as ms,
      left(query, 40) as query
    FROM tool_usage_logs
    WHERE timestamp > now() - interval '10 seconds'
    ORDER BY timestamp DESC
    LIMIT 5
  " 2>/dev/null || echo "  (sin actividad)"

  echo ""
  echo "💬 SESIONES ACTIVAS:"
  psql $DATABASE_URL -c "
    SELECT
      left(session_id, 20) as session,
      org_id,
      jsonb_array_length(messages) as msgs,
      to_char(updated_at, 'HH24:MI:SS') as updated
    FROM chat_sessions
    WHERE updated_at > now() - interval '1 minute'
    ORDER BY updated_at DESC
    LIMIT 5
  " 2>/dev/null || echo "  (sin sesiones)"

  echo ""
  echo "📈 ESTADÍSTICAS (última hora):"
  psql $DATABASE_URL -c "
    SELECT
      tool_name,
      COUNT(*) as calls,
      AVG(execution_time_ms)::int as avg_ms,
      SUM(CASE WHEN success THEN 1 ELSE 0 END)::float / COUNT(*) * 100 as success_pct
    FROM tool_usage_logs
    WHERE timestamp > now() - interval '1 hour'
    GROUP BY tool_name
    ORDER BY calls DESC
  " 2>/dev/null || echo "  (sin estadísticas)"

  echo ""
  echo "🔄 Actualizando en 3 segundos... (Ctrl+C para salir)"
  sleep 3
done
