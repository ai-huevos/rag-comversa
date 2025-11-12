-- Employee Reference Table Migration
-- Part of minimal 20% approach for employee integration
-- Time to run: ~10 seconds
-- Cost: $0

BEGIN;

-- Create employees table
CREATE TABLE IF NOT EXISTS employees (
    employee_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    role TEXT,
    company TEXT,
    gc_profile TEXT,
    gc_description TEXT,
    score_game_changer INTEGER DEFAULT 0,
    score_strategist INTEGER DEFAULT 0,
    score_implementer INTEGER DEFAULT 0,
    score_polisher INTEGER DEFAULT 0,
    score_play_maker INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Simple indices for common queries
CREATE INDEX IF NOT EXISTS idx_employees_last_name
ON employees(last_name);

CREATE INDEX IF NOT EXISTS idx_employees_company
ON employees(company);

CREATE INDEX IF NOT EXISTS idx_employees_gc_profile
ON employees(gc_profile);

-- Full-text search on employee names
CREATE INDEX IF NOT EXISTS idx_employees_full_name_fts
ON employees USING gin(to_tsvector('spanish', full_name));

-- Add employee reference to consolidated_entities
ALTER TABLE consolidated_entities
ADD COLUMN IF NOT EXISTS employee_id TEXT REFERENCES employees(employee_id),
ADD COLUMN IF NOT EXISTS employee_name TEXT,
ADD COLUMN IF NOT EXISTS employee_company TEXT;

-- Index for filtering by employee
CREATE INDEX IF NOT EXISTS idx_consolidated_entities_employee
ON consolidated_entities(employee_id)
WHERE employee_id IS NOT NULL;

-- Index for combined queries (employee + entity type)
CREATE INDEX IF NOT EXISTS idx_consolidated_entities_employee_type
ON consolidated_entities(employee_id, entity_type)
WHERE employee_id IS NOT NULL;

COMMIT;

-- Verification queries
SELECT 'Tables created successfully' as status;
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_name = 'employees'
ORDER BY ordinal_position;
