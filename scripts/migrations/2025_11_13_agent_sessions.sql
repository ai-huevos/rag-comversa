-- Task 14: Session storage + telemetry tables for Agentic RAG API

BEGIN;

CREATE TABLE IF NOT EXISTS chat_sessions (
    session_id UUID PRIMARY KEY,
    org_id TEXT NOT NULL,
    context TEXT,
    messages JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_chat_sessions_org ON chat_sessions(org_id);

CREATE TABLE IF NOT EXISTS tool_usage_logs (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    org_id TEXT NOT NULL,
    tool_name TEXT NOT NULL,
    query TEXT NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    success BOOLEAN NOT NULL,
    execution_time_ms DOUBLE PRECISION NOT NULL,
    result_count INTEGER NOT NULL DEFAULT 0,
    error_message TEXT,
    cost_cents DOUBLE PRECISION,
    cache_hit BOOLEAN NOT NULL DEFAULT FALSE,
    retrieval_mode TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tool_usage_org_time
    ON tool_usage_logs(org_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_tool_usage_tool
    ON tool_usage_logs(tool_name);

COMMIT;
