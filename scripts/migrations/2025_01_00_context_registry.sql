-- Context Registry Migration
-- Task 0: Stand up Context Registry & Org Namespace Controls
-- Date: 2025-01-09
-- Purpose: Multi-organization context tracking for RAG 2.0 enhancement

-- Enable pgvector extension if not already enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Context Registry Table
-- Stores organization metadata, business units, departments, and consent information
-- Ensures unique (org_id, business_unit, department) namespace for multi-tenant data isolation
CREATE TABLE IF NOT EXISTS context_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id TEXT NOT NULL,
    org_name TEXT NOT NULL,
    business_unit TEXT NOT NULL,
    department TEXT,
    industry_context TEXT,
    priority_tier TEXT DEFAULT 'standard',
    contact_owner JSONB,
    consent_metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    active BOOLEAN DEFAULT true,
    UNIQUE (org_id, business_unit, department)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_context_registry_org_id ON context_registry(org_id);
CREATE INDEX IF NOT EXISTS idx_context_registry_active ON context_registry(active);
CREATE INDEX IF NOT EXISTS idx_context_registry_priority ON context_registry(priority_tier);

-- Audit table for context registry changes
CREATE TABLE IF NOT EXISTS context_registry_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registry_id UUID NOT NULL REFERENCES context_registry(id),
    action TEXT NOT NULL, -- 'created', 'updated', 'deactivated'
    changed_by TEXT,
    changed_at TIMESTAMPTZ DEFAULT now(),
    old_values JSONB,
    new_values JSONB
);

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_context_registry_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update timestamp on changes
CREATE TRIGGER context_registry_update_timestamp
    BEFORE UPDATE ON context_registry
    FOR EACH ROW
    EXECUTE FUNCTION update_context_registry_timestamp();

-- Function to log audit trail
CREATE OR REPLACE FUNCTION log_context_registry_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO context_registry_audit (registry_id, action, new_values)
        VALUES (NEW.id, 'created', row_to_json(NEW)::jsonb);
    ELSIF TG_OP = 'UPDATE' THEN
        INSERT INTO context_registry_audit (registry_id, action, old_values, new_values)
        VALUES (NEW.id, 'updated', row_to_json(OLD)::jsonb, row_to_json(NEW)::jsonb);
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO context_registry_audit (registry_id, action, old_values)
        VALUES (OLD.id, 'deleted', row_to_json(OLD)::jsonb);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log changes
CREATE TRIGGER context_registry_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON context_registry
    FOR EACH ROW
    EXECUTE FUNCTION log_context_registry_changes();

-- Access control logging table
-- Tracks every query execution to ensure Bolivian privacy compliance
CREATE TABLE IF NOT EXISTS context_access_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id TEXT NOT NULL,
    business_context TEXT,
    access_type TEXT NOT NULL, -- 'query', 'ingestion', 'retrieval', 'checkpoint'
    user_id TEXT,
    session_id TEXT,
    accessed_at TIMESTAMPTZ DEFAULT now(),
    query_params JSONB,
    result_count INTEGER,
    latency_ms INTEGER
);

-- Index for access log queries
CREATE INDEX IF NOT EXISTS idx_access_log_org_id ON context_access_log(org_id);
CREATE INDEX IF NOT EXISTS idx_access_log_accessed_at ON context_access_log(accessed_at);
CREATE INDEX IF NOT EXISTS idx_access_log_access_type ON context_access_log(access_type);

-- Seed initial organizations from companies.json
-- This will be executed by the sync script after migration
COMMENT ON TABLE context_registry IS 'Multi-organization context registry for RAG 2.0 namespace isolation';
COMMENT ON TABLE context_registry_audit IS 'Audit trail for context registry changes';
COMMENT ON TABLE context_access_log IS 'Access control logging for Bolivian privacy compliance (Law 164, Habeas Data)';
