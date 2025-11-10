-- ========================================================================
-- Rollback: 2025_01_02_ocr_review_queue_rollback.sql
-- Purpose: Rollback ocr_review_queue table, views, and related objects
-- Author: storage_graph agent
-- Created: 2025-11-09
-- ========================================================================

-- ========================================================================
-- SAFETY CHECKS - Prevent accidental data loss
-- ========================================================================

DO $$
DECLARE
    row_count INTEGER;
    pending_count INTEGER;
BEGIN
    -- Check if table has data
    SELECT COUNT(*) INTO row_count FROM ocr_review_queue;
    SELECT COUNT(*) INTO pending_count FROM ocr_review_queue WHERE status = 'pending_review';

    IF row_count > 0 THEN
        RAISE WARNING 'WARNING: ocr_review_queue table contains % rows', row_count;
        RAISE WARNING 'Including % pending reviews that will be lost', pending_count;
        RAISE WARNING 'Data will be permanently deleted if rollback continues';

        -- Uncomment the line below to allow rollback with data loss
        -- RAISE EXCEPTION 'Rollback aborted - table contains data. Comment out safety check to proceed.';
    ELSE
        RAISE NOTICE 'Table is empty - safe to rollback';
    END IF;
END $$;

-- ========================================================================
-- Drop views (must drop before table)
-- ========================================================================

DROP VIEW IF EXISTS ocr_reviewer_stats CASCADE;
DROP VIEW IF EXISTS ocr_high_priority_queue CASCADE;

-- ========================================================================
-- Drop triggers (must drop before functions)
-- ========================================================================

DROP TRIGGER IF EXISTS trigger_generate_ocr_crop_path ON ocr_review_queue;
DROP TRIGGER IF EXISTS trigger_set_ocr_review_priority ON ocr_review_queue;

-- ========================================================================
-- Drop functions
-- ========================================================================

DROP FUNCTION IF EXISTS generate_ocr_crop_path();
DROP FUNCTION IF EXISTS set_ocr_review_priority();

-- ========================================================================
-- Drop indexes (will be auto-dropped with table, but explicit for clarity)
-- ========================================================================

DROP INDEX IF EXISTS idx_ocr_metadata;
DROP INDEX IF EXISTS idx_ocr_engine_confidence;
DROP INDEX IF EXISTS idx_ocr_segment_type;
DROP INDEX IF EXISTS idx_ocr_reviewed_by;
DROP INDEX IF EXISTS idx_ocr_document;
DROP INDEX IF EXISTS idx_ocr_confidence;
DROP INDEX IF EXISTS idx_ocr_status_priority;

-- ========================================================================
-- Drop table
-- ========================================================================

DROP TABLE IF EXISTS ocr_review_queue CASCADE;

-- ========================================================================
-- Verification
-- ========================================================================

DO $$
BEGIN
    -- Verify table is gone
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ocr_review_queue') THEN
        RAISE EXCEPTION 'ERROR: ocr_review_queue table still exists after rollback';
    END IF;

    -- Verify views are gone
    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'ocr_high_priority_queue') THEN
        RAISE EXCEPTION 'ERROR: ocr_high_priority_queue view still exists after rollback';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'ocr_reviewer_stats') THEN
        RAISE EXCEPTION 'ERROR: ocr_reviewer_stats view still exists after rollback';
    END IF;

    -- Verify triggers are gone
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname IN ('trigger_set_ocr_review_priority', 'trigger_generate_ocr_crop_path')) THEN
        RAISE EXCEPTION 'ERROR: OCR triggers still exist after rollback';
    END IF;

    -- Verify functions are gone
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname IN ('set_ocr_review_priority', 'generate_ocr_crop_path')) THEN
        RAISE EXCEPTION 'ERROR: OCR functions still exist after rollback';
    END IF;

    RAISE NOTICE 'SUCCESS: Rollback 2025_01_02_ocr_review_queue completed successfully';
    RAISE NOTICE 'All objects dropped: table, views, indexes, triggers, functions';
END $$;

-- ========================================================================
-- Manual verification queries (run separately if needed)
-- ========================================================================

-- Check no tables remain
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_name LIKE '%ocr%';

-- Check no views remain
-- SELECT table_name
-- FROM information_schema.views
-- WHERE table_name LIKE '%ocr%';

-- Check no functions remain
-- SELECT routine_name
-- FROM information_schema.routines
-- WHERE routine_name LIKE '%ocr%';

-- Check no triggers remain
-- SELECT tgname
-- FROM pg_trigger
-- WHERE tgname LIKE '%ocr%';
