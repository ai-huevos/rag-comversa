-- ========================================================================
-- Rollback Script: 2025_01_01_pgvector_rollback.sql
-- Purpose        : Drop pgvector core schema objects created by
--                  2025_01_01_pgvector.sql
-- Author         : consolidation_automation agent
-- Created        : 2025-11-10
-- ========================================================================

DO $$
BEGIN
    RAISE NOTICE 'Starting rollback for 2025_01_01_pgvector...';
END $$;

-- Views
DROP VIEW IF EXISTS vw_documents_pending_embeddings;

-- Foreign keys on ingestion_events
ALTER TABLE ingestion_events
    DROP CONSTRAINT IF EXISTS ingestion_events_document_row_fk;

ALTER TABLE ingestion_events
    DROP COLUMN IF EXISTS document_row_id;

-- Consolidation events table
DROP TABLE IF EXISTS consolidation_events;

-- Embeddings table + indexes
DROP INDEX IF EXISTS idx_embeddings_hnsw;
DROP INDEX IF EXISTS idx_embeddings_model;
DROP INDEX IF EXISTS idx_embeddings_document_id;
DROP INDEX IF EXISTS idx_embeddings_chunk_id;
DROP TABLE IF EXISTS embeddings;

-- Consolidated data tables
DROP TRIGGER IF EXISTS trigger_consolidated_patterns_updated_at ON consolidated_patterns;
DROP FUNCTION IF EXISTS touch_consolidated_patterns_updated_at;
DROP INDEX IF EXISTS idx_consolidated_patterns_org;
DROP TABLE IF EXISTS consolidated_patterns;

DROP TRIGGER IF EXISTS trigger_consolidated_relationships_updated_at ON consolidated_relationships;
DROP FUNCTION IF EXISTS touch_consolidated_relationships_updated_at;
DROP INDEX IF EXISTS idx_consolidated_relationships_strength;
DROP INDEX IF EXISTS idx_consolidated_relationships_org;
DROP TABLE IF EXISTS consolidated_relationships;

DROP TRIGGER IF EXISTS trigger_consolidated_entities_updated_at ON consolidated_entities;
DROP FUNCTION IF EXISTS touch_consolidated_entities_updated_at;
DROP INDEX IF EXISTS idx_consolidated_entities_confidence;
DROP INDEX IF EXISTS idx_consolidated_entities_org;
DROP TABLE IF EXISTS consolidated_entities;

-- Document chunks
DROP TRIGGER IF EXISTS trigger_document_chunks_updated_at ON document_chunks;
DROP FUNCTION IF EXISTS touch_document_chunks_updated_at;
DROP INDEX IF EXISTS idx_chunks_spanish_features;
DROP INDEX IF EXISTS idx_chunks_span_offsets;
DROP INDEX IF EXISTS idx_chunks_language;
DROP INDEX IF EXISTS idx_chunks_document_index;
DROP TABLE IF EXISTS document_chunks;

-- Documents
DROP TRIGGER IF EXISTS trigger_documents_updated_at ON documents;
DROP FUNCTION IF EXISTS touch_documents_updated_at;
DROP INDEX IF EXISTS idx_documents_updated_at;
DROP INDEX IF EXISTS idx_documents_checksum;
DROP INDEX IF EXISTS idx_documents_org_status;
ALTER TABLE documents
    DROP CONSTRAINT IF EXISTS fk_documents_ingestion_event;
DROP TABLE IF EXISTS documents;

DO $$
BEGIN
    RAISE NOTICE 'Rollback 2025_01_01_pgvector completed successfully.';
END $$;
