-- ========================================================================
-- Migration: 2025_01_01_ingestion_queue.sql
-- Purpose: Ingestion event tracking queue for RAG 2.0 multi-format pipeline
-- Author: storage_graph agent
-- Created: 2025-11-09
-- Dependencies: PostgreSQL 12+, context_registry (2025_01_00)
-- ========================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================================================
-- Table: ingestion_events
-- Purpose: Track document ingestion lifecycle from queue to completion
-- ========================================================================

CREATE TABLE IF NOT EXISTS ingestion_events (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Organization and document identity
    org_id VARCHAR(100) NOT NULL,
    document_id UUID NOT NULL DEFAULT uuid_generate_v4(),

    -- Source tracking
    connector_type VARCHAR(50) NOT NULL,
    source_path TEXT NOT NULL,
    source_format VARCHAR(50),  -- pdf, docx, image, csv, xlsx, whatsapp, json

    -- File integrity
    checksum VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT,

    -- Processing status
    status VARCHAR(50) DEFAULT 'queued' NOT NULL,
    stage VARCHAR(50),  -- enqueued, parsing, ocr, chunking, embedding, extraction, completed, failed

    -- Timestamps
    enqueued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,

    -- Error handling
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,

    -- Flexible metadata (connector-specific details, page counts, etc.)
    metadata JSONB,

    -- Processing metrics
    processing_time_seconds FLOAT,

    -- Constraints
    CONSTRAINT unique_checksum UNIQUE(checksum),
    CONSTRAINT valid_status CHECK (status IN (
        'queued', 'processing', 'completed', 'failed', 'retrying', 'cancelled'
    )),
    CONSTRAINT valid_stage CHECK (stage IN (
        'enqueued', 'parsing', 'ocr', 'chunking', 'embedding', 'extraction',
        'consolidation', 'graph_write', 'completed', 'failed'
    )),
    CONSTRAINT positive_file_size CHECK (file_size_bytes >= 0),
    CONSTRAINT positive_retry_count CHECK (retry_count >= 0),
    CONSTRAINT started_after_enqueued CHECK (started_at IS NULL OR started_at >= enqueued_at),
    CONSTRAINT completed_after_started CHECK (completed_at IS NULL OR completed_at >= started_at)
);

-- ========================================================================
-- Indexes for query performance
-- ========================================================================

-- Primary query patterns: org-based status filtering
CREATE INDEX idx_ingestion_org_status
ON ingestion_events(org_id, status);

-- Fast checksum lookups for deduplication
CREATE INDEX idx_ingestion_checksum
ON ingestion_events(checksum);

-- Status-based queries for worker polling
CREATE INDEX idx_ingestion_status
ON ingestion_events(status)
WHERE status IN ('queued', 'retrying');

-- Time-based queries for SLA monitoring
CREATE INDEX idx_ingestion_enqueued_at
ON ingestion_events(enqueued_at DESC);

-- Document ID lookups
CREATE INDEX idx_ingestion_document_id
ON ingestion_events(document_id);

-- Connector analytics
CREATE INDEX idx_ingestion_connector_type
ON ingestion_events(connector_type);

-- Failed job investigation
CREATE INDEX idx_ingestion_failed
ON ingestion_events(status, error_message)
WHERE status = 'failed';

-- JSONB metadata queries (GIN index for flexible queries)
CREATE INDEX idx_ingestion_metadata
ON ingestion_events USING GIN(metadata);

-- ========================================================================
-- Comments for schema documentation
-- ========================================================================

COMMENT ON TABLE ingestion_events IS
'Document ingestion lifecycle tracking for RAG 2.0 pipeline. Records every document from queue entry to completion, supporting multi-format ingestion, error recovery, and SLA monitoring.';

COMMENT ON COLUMN ingestion_events.org_id IS
'Organization namespace from context_registry. Enforces data isolation per company (Los Tajibos, Comversa, Bolivian Foods).';

COMMENT ON COLUMN ingestion_events.document_id IS
'Unique document identifier (UUID). Links to documents table after successful ingestion.';

COMMENT ON COLUMN ingestion_events.connector_type IS
'Source connector: email, whatsapp, api, sharepoint, drive, manual_upload.';

COMMENT ON COLUMN ingestion_events.source_path IS
'Original file path: data/documents/inbox/{connector}/{org}/{filename}';

COMMENT ON COLUMN ingestion_events.source_format IS
'Detected MIME type/format: pdf, docx, image, csv, xlsx, whatsapp, json.';

COMMENT ON COLUMN ingestion_events.checksum IS
'SHA-256 checksum for file integrity and deduplication. Prevents re-processing same document.';

COMMENT ON COLUMN ingestion_events.status IS
'High-level processing status: queued, processing, completed, failed, retrying, cancelled.';

COMMENT ON COLUMN ingestion_events.stage IS
'Current pipeline stage: enqueued, parsing, ocr, chunking, embedding, extraction, consolidation, graph_write, completed, failed.';

COMMENT ON COLUMN ingestion_events.error_message IS
'Spanish error message for failed ingestions. Used for debugging and user notifications.';

COMMENT ON COLUMN ingestion_events.metadata IS
'Flexible JSONB field for connector-specific metadata: {page_count, language, consent_status, original_filename, etc.}';

COMMENT ON COLUMN ingestion_events.processing_time_seconds IS
'Total processing time from started_at to completed_at. Used for performance monitoring and SLA tracking.';

-- ========================================================================
-- Helper functions
-- ========================================================================

-- Function to update processing metrics on completion
CREATE OR REPLACE FUNCTION update_ingestion_metrics()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate processing time when status changes to completed or failed
    IF NEW.status IN ('completed', 'failed') AND NEW.started_at IS NOT NULL THEN
        NEW.processing_time_seconds = EXTRACT(EPOCH FROM (NEW.completed_at - NEW.started_at));
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate processing metrics
CREATE TRIGGER trigger_update_ingestion_metrics
    BEFORE UPDATE ON ingestion_events
    FOR EACH ROW
    WHEN (NEW.status IN ('completed', 'failed') AND NEW.completed_at IS NOT NULL)
    EXECUTE FUNCTION update_ingestion_metrics();

-- ========================================================================
-- Sample usage for testing
-- ========================================================================

-- Example: Queue a PDF document for ingestion
-- INSERT INTO ingestion_events (
--     org_id, connector_type, source_path, source_format, checksum, file_size_bytes, metadata
-- ) VALUES (
--     'los_tajibos',
--     'manual_upload',
--     'data/documents/inbox/manual_upload/los_tajibos/2025-11-09_financial_report.pdf',
--     'pdf',
--     'abc123def456...',
--     2048576,
--     '{"page_count": 12, "language": "es", "consent_status": "approved"}'::jsonb
-- );

-- Example: Query queued documents for processing
-- SELECT id, org_id, source_path, source_format, enqueued_at
-- FROM ingestion_events
-- WHERE status = 'queued'
-- ORDER BY enqueued_at ASC
-- LIMIT 10;

-- Example: Update status to processing
-- UPDATE ingestion_events
-- SET status = 'processing',
--     stage = 'parsing',
--     started_at = CURRENT_TIMESTAMP
-- WHERE id = 1;

-- Example: Mark as completed
-- UPDATE ingestion_events
-- SET status = 'completed',
--     stage = 'completed',
--     completed_at = CURRENT_TIMESTAMP
-- WHERE id = 1;

-- Example: Record failure
-- UPDATE ingestion_events
-- SET status = 'failed',
--     stage = 'ocr',
--     completed_at = CURRENT_TIMESTAMP,
--     error_message = 'Error OCR: Imagen demasiado borrosa para procesamiento automático. Requiere revisión manual.',
--     retry_count = retry_count + 1
-- WHERE id = 1;

-- ========================================================================
-- Migration validation query
-- ========================================================================

-- Verify table structure
DO $$
BEGIN
    -- Check table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ingestion_events') THEN
        RAISE EXCEPTION 'ERROR: ingestion_events table not created';
    END IF;

    -- Check indexes exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'ingestion_events' AND indexname = 'idx_ingestion_org_status') THEN
        RAISE EXCEPTION 'ERROR: idx_ingestion_org_status index not created';
    END IF;

    RAISE NOTICE 'SUCCESS: Migration 2025_01_01_ingestion_queue completed successfully';
END $$;
