-- ========================================================================
-- Migration: 2025_01_02_ocr_review_queue.sql
-- Purpose: OCR review queue for low-confidence segments requiring manual QA
-- Author: storage_graph agent
-- Created: 2025-11-09
-- Dependencies: PostgreSQL 12+, UUID extension, ingestion_events (2025_01_01)
-- ========================================================================

-- Ensure UUID extension is available
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ========================================================================
-- Table: ocr_review_queue
-- Purpose: Queue low-confidence OCR segments for manual review and correction
-- ========================================================================

CREATE TABLE IF NOT EXISTS ocr_review_queue (
    -- Primary key
    id SERIAL PRIMARY KEY,

    -- Document reference
    document_id UUID NOT NULL,
    page_number INTEGER NOT NULL,
    segment_index INTEGER NOT NULL,

    -- OCR output
    ocr_text TEXT,
    confidence FLOAT NOT NULL,
    ocr_engine VARCHAR(50) NOT NULL,  -- mistral_pixtral, tesseract, fallback

    -- Spatial information for image crops
    bounding_box JSONB,  -- {x, y, width, height, page_width, page_height}
    image_crop_url TEXT,  -- Path to cropped image for reviewer

    -- Review workflow
    status VARCHAR(50) DEFAULT 'pending_review' NOT NULL,
    reviewed_by VARCHAR(100),
    corrected_text TEXT,
    review_notes TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,

    -- Priority and categorization
    priority VARCHAR(20) DEFAULT 'normal',  -- high, normal, low
    segment_type VARCHAR(50),  -- handwriting, printed_degraded, tables, mixed

    -- Flexible metadata
    metadata JSONB,  -- {original_filename, language_detected, retry_count, etc.}

    -- Constraints
    CONSTRAINT valid_confidence CHECK (confidence >= 0.0 AND confidence <= 1.0),
    CONSTRAINT positive_page_number CHECK (page_number > 0),
    CONSTRAINT non_negative_segment_index CHECK (segment_index >= 0),
    CONSTRAINT valid_status CHECK (status IN (
        'pending_review', 'in_review', 'approved', 'rejected', 'skipped'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('high', 'normal', 'low')),
    CONSTRAINT reviewed_at_check CHECK (
        (status IN ('approved', 'rejected', 'skipped') AND reviewed_at IS NOT NULL) OR
        (status IN ('pending_review', 'in_review'))
    )
);

-- ========================================================================
-- Indexes for query performance
-- ========================================================================

-- Primary query: Get pending reviews by priority and age
CREATE INDEX idx_ocr_status_priority
ON ocr_review_queue(status, priority, created_at DESC)
WHERE status = 'pending_review';

-- Fast confidence-based queries (low confidence first)
CREATE INDEX idx_ocr_confidence
ON ocr_review_queue(confidence ASC)
WHERE status = 'pending_review';

-- Document-based lookups (all segments for a document)
CREATE INDEX idx_ocr_document
ON ocr_review_queue(document_id, page_number, segment_index);

-- Reviewer activity tracking
CREATE INDEX idx_ocr_reviewed_by
ON ocr_review_queue(reviewed_by, reviewed_at DESC)
WHERE reviewed_by IS NOT NULL;

-- Segment type analytics
CREATE INDEX idx_ocr_segment_type
ON ocr_review_queue(segment_type, confidence)
WHERE segment_type IS NOT NULL;

-- OCR engine performance analysis
CREATE INDEX idx_ocr_engine_confidence
ON ocr_review_queue(ocr_engine, confidence);

-- JSONB metadata queries
CREATE INDEX idx_ocr_metadata
ON ocr_review_queue USING GIN(metadata);

-- ========================================================================
-- Comments for schema documentation
-- ========================================================================

COMMENT ON TABLE ocr_review_queue IS
'Manual review queue for OCR segments with low confidence scores. Supports Mistral Pixtral + Tesseract fallback with human QA workflow for handwriting and degraded printed text.';

COMMENT ON COLUMN ocr_review_queue.document_id IS
'Links to ingestion_events.document_id. Identifies source document for segment.';

COMMENT ON COLUMN ocr_review_queue.page_number IS
'1-based page number in original document. Used to locate segment in PDF/image.';

COMMENT ON COLUMN ocr_review_queue.segment_index IS
'0-based segment index within page. Multiple segments per page (paragraphs, tables, etc.)';

COMMENT ON COLUMN ocr_review_queue.ocr_text IS
'Raw OCR output text (may be incorrect or incomplete). Null if OCR completely failed.';

COMMENT ON COLUMN ocr_review_queue.confidence IS
'OCR confidence score 0.0-1.0. Thresholds: <0.70 handwriting, <0.90 printed. Lower = higher priority.';

COMMENT ON COLUMN ocr_review_queue.ocr_engine IS
'OCR engine used: mistral_pixtral (primary), tesseract (fallback), fallback (other).';

COMMENT ON COLUMN ocr_review_queue.bounding_box IS
'JSONB with segment coordinates: {x, y, width, height, page_width, page_height}. Used to generate image crops.';

COMMENT ON COLUMN ocr_review_queue.image_crop_url IS
'Path or URL to cropped image for reviewer: data/ocr_crops/{document_id}/page_{page}_segment_{segment}.png';

COMMENT ON COLUMN ocr_review_queue.status IS
'Review workflow status: pending_review, in_review, approved, rejected, skipped.';

COMMENT ON COLUMN ocr_review_queue.reviewed_by IS
'Username or email of reviewer (Patricia, Samuel, Armando). Null for pending reviews.';

COMMENT ON COLUMN ocr_review_queue.corrected_text IS
'Manually corrected text from reviewer. Replaces ocr_text after approval.';

COMMENT ON COLUMN ocr_review_queue.review_notes IS
'Reviewer notes in Spanish: reasons for rejection, quality issues, special handling instructions.';

COMMENT ON COLUMN ocr_review_queue.priority IS
'Review priority: high (confidence < 0.50), normal (0.50-0.70), low (0.70-0.90). Affects queue ordering.';

COMMENT ON COLUMN ocr_review_queue.segment_type IS
'Segment classification: handwriting, printed_degraded, tables, mixed. Helps route to specialized reviewers.';

COMMENT ON COLUMN ocr_review_queue.metadata IS
'Flexible JSONB: {original_filename, language_detected, retry_count, ocr_params, reviewer_flags}';

-- ========================================================================
-- Helper functions
-- ========================================================================

-- Function to auto-set priority based on confidence
CREATE OR REPLACE FUNCTION set_ocr_review_priority()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-assign priority based on confidence threshold
    IF NEW.confidence < 0.50 THEN
        NEW.priority = 'high';
    ELSIF NEW.confidence < 0.70 THEN
        NEW.priority = 'normal';
    ELSE
        NEW.priority = 'low';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate priority on insert
CREATE TRIGGER trigger_set_ocr_review_priority
    BEFORE INSERT ON ocr_review_queue
    FOR EACH ROW
    EXECUTE FUNCTION set_ocr_review_priority();

-- Function to generate image crop path
CREATE OR REPLACE FUNCTION generate_ocr_crop_path()
RETURNS TRIGGER AS $$
BEGIN
    -- Auto-generate image crop path if not provided
    IF NEW.image_crop_url IS NULL AND NEW.document_id IS NOT NULL THEN
        NEW.image_crop_url = format(
            'data/ocr_crops/%s/page_%s_segment_%s.png',
            NEW.document_id,
            NEW.page_number,
            NEW.segment_index
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-generate crop path
CREATE TRIGGER trigger_generate_ocr_crop_path
    BEFORE INSERT ON ocr_review_queue
    FOR EACH ROW
    EXECUTE FUNCTION generate_ocr_crop_path();

-- ========================================================================
-- Views for common queries
-- ========================================================================

-- View: Pending high-priority reviews (confidence < 0.50)
CREATE OR REPLACE VIEW ocr_high_priority_queue AS
SELECT
    id,
    document_id,
    page_number,
    segment_index,
    ocr_text,
    confidence,
    ocr_engine,
    image_crop_url,
    segment_type,
    created_at,
    EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - created_at)) / 3600 AS age_hours
FROM ocr_review_queue
WHERE status = 'pending_review'
  AND priority = 'high'
ORDER BY confidence ASC, created_at ASC;

COMMENT ON VIEW ocr_high_priority_queue IS
'High-priority OCR reviews (confidence < 0.50) sorted by lowest confidence first. Includes age in hours for SLA tracking.';

-- View: Reviewer performance metrics
CREATE OR REPLACE VIEW ocr_reviewer_stats AS
SELECT
    reviewed_by,
    COUNT(*) AS total_reviews,
    COUNT(*) FILTER (WHERE status = 'approved') AS approved_count,
    COUNT(*) FILTER (WHERE status = 'rejected') AS rejected_count,
    COUNT(*) FILTER (WHERE status = 'skipped') AS skipped_count,
    AVG(confidence) AS avg_confidence_reviewed,
    AVG(EXTRACT(EPOCH FROM (reviewed_at - created_at)) / 60) AS avg_review_time_minutes
FROM ocr_review_queue
WHERE reviewed_by IS NOT NULL
GROUP BY reviewed_by
ORDER BY total_reviews DESC;

COMMENT ON VIEW ocr_reviewer_stats IS
'Reviewer performance metrics: total reviews, approval rate, average review time in minutes.';

-- ========================================================================
-- Sample usage for testing
-- ========================================================================

-- Example: Insert low-confidence handwriting segment
-- INSERT INTO ocr_review_queue (
--     document_id, page_number, segment_index, ocr_text, confidence,
--     ocr_engine, segment_type, bounding_box, metadata
-- ) VALUES (
--     '550e8400-e29b-41d4-a716-446655440000',
--     3,
--     2,
--     'Rconclición mnual d factura',  -- Garbled OCR text
--     0.45,
--     'mistral_pixtral',
--     'handwriting',
--     '{"x": 120, "y": 450, "width": 600, "height": 80, "page_width": 1200, "page_height": 1600}'::jsonb,
--     '{"language_detected": "es", "original_filename": "notas_reunión.pdf"}'::jsonb
-- );

-- Example: Query pending reviews by priority
-- SELECT id, page_number, segment_index, ocr_text, confidence, priority, image_crop_url
-- FROM ocr_review_queue
-- WHERE status = 'pending_review'
-- ORDER BY priority DESC, confidence ASC
-- LIMIT 10;

-- Example: Reviewer approves corrected text
-- UPDATE ocr_review_queue
-- SET status = 'approved',
--     corrected_text = 'Reconciliación manual de factura',
--     reviewed_by = 'patricia@comversa.com',
--     reviewed_at = CURRENT_TIMESTAMP,
--     review_notes = 'Texto corregido manualmente. Escritura a mano legible.'
-- WHERE id = 1;

-- Example: Reviewer rejects (illegible)
-- UPDATE ocr_review_queue
-- SET status = 'rejected',
--     reviewed_by = 'samuel@comversa.com',
--     reviewed_at = CURRENT_TIMESTAMP,
--     review_notes = 'Texto ilegible incluso para revisión manual. Solicitar documento digital original.'
-- WHERE id = 2;

-- ========================================================================
-- Migration validation query
-- ========================================================================

DO $$
BEGIN
    -- Check table exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ocr_review_queue') THEN
        RAISE EXCEPTION 'ERROR: ocr_review_queue table not created';
    END IF;

    -- Check indexes exist
    IF NOT EXISTS (SELECT 1 FROM pg_indexes WHERE tablename = 'ocr_review_queue' AND indexname = 'idx_ocr_status_priority') THEN
        RAISE EXCEPTION 'ERROR: idx_ocr_status_priority index not created';
    END IF;

    -- Check views exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'ocr_high_priority_queue') THEN
        RAISE EXCEPTION 'ERROR: ocr_high_priority_queue view not created';
    END IF;

    RAISE NOTICE 'SUCCESS: Migration 2025_01_02_ocr_review_queue completed successfully';
END $$;
