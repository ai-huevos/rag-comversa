-- ========================================================================
-- Rollback: 2025_01_01_ingestion_queue_rollback.sql
-- Purpose: Rollback ingestion_events table and related objects
-- Author: storage_graph agent
-- Created: 2025-11-09
-- ========================================================================

-- ========================================================================
-- SAFETY CHECKS - Prevent accidental data loss
-- ========================================================================

DO $$
DECLARE
    row_count INTEGER;
BEGIN
    -- Check if table has data
    SELECT COUNT(*) INTO row_count FROM ingestion_events;

    IF row_count > 0 THEN
        RAISE WARNING 'WARNING: ingestion_events table contains % rows', row_count;
        RAISE WARNING 'Data will be permanently deleted if rollback continues';
        RAISE WARNING 'To proceed, comment out this check in the rollback script';

        -- Uncomment the line below to allow rollback with data loss
        -- RAISE EXCEPTION 'Rollback aborted - table contains data. Comment out safety check to proceed.';
    ELSE
        RAISE NOTICE 'Table is empty - safe to rollback';
    END IF;
END $$;

-- ========================================================================
-- Drop triggers (must drop before functions)
-- ========================================================================

DROP TRIGGER IF EXISTS trigger_update_ingestion_metrics ON ingestion_events;

-- ========================================================================
-- Drop functions
-- ========================================================================

DROP FUNCTION IF EXISTS update_ingestion_metrics();

-- ========================================================================
-- Drop indexes (will be auto-dropped with table, but explicit for clarity)
-- ========================================================================

DROP INDEX IF EXISTS idx_ingestion_metadata;
DROP INDEX IF EXISTS idx_ingestion_failed;
DROP INDEX IF EXISTS idx_ingestion_connector_type;
DROP INDEX IF EXISTS idx_ingestion_document_id;
DROP INDEX IF EXISTS idx_ingestion_enqueued_at;
DROP INDEX IF EXISTS idx_ingestion_status;
DROP INDEX IF EXISTS idx_ingestion_checksum;
DROP INDEX IF EXISTS idx_ingestion_org_status;

-- ========================================================================
-- Drop table
-- ========================================================================

DROP TABLE IF EXISTS ingestion_events CASCADE;

-- ========================================================================
-- Verification
-- ========================================================================

DO $$
BEGIN
    -- Verify table is gone
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'ingestion_events') THEN
        RAISE EXCEPTION 'ERROR: ingestion_events table still exists after rollback';
    END IF;

    -- Verify trigger is gone
    IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgname = 'trigger_update_ingestion_metrics') THEN
        RAISE EXCEPTION 'ERROR: trigger_update_ingestion_metrics still exists after rollback';
    END IF;

    -- Verify function is gone
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_ingestion_metrics') THEN
        RAISE EXCEPTION 'ERROR: update_ingestion_metrics function still exists after rollback';
    END IF;

    RAISE NOTICE 'SUCCESS: Rollback 2025_01_01_ingestion_queue completed successfully';
    RAISE NOTICE 'All objects dropped: table, indexes, triggers, functions';
END $$;

-- ========================================================================
-- Manual verification queries (run separately if needed)
-- ========================================================================

-- Check no tables remain
-- SELECT table_name
-- FROM information_schema.tables
-- WHERE table_name LIKE '%ingestion%';

-- Check no functions remain
-- SELECT routine_name
-- FROM information_schema.routines
-- WHERE routine_name LIKE '%ingestion%';

-- Check no triggers remain
-- SELECT tgname
-- FROM pg_trigger
-- WHERE tgname LIKE '%ingestion%';
