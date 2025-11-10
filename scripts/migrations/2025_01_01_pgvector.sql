-- ========================================================================
-- Migration: 2025_01_01_pgvector.sql
-- Purpose: Core PostgreSQL schema for documents, chunks, embeddings, and
--          ingestion/ocr telemetry required for RAG 2.0 Phase 2.
-- Author : consolidation_automation agent
-- Created: 2025-11-10
-- Notes  : Must be executed after context registry (2025_01_00) so org_id
--          namespaces already exist.
-- ========================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS vector;

-- ========================================================================
-- Table: documents
-- ========================================================================
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id VARCHAR(100) NOT NULL,
    ingestion_event_id INTEGER,
    source_type VARCHAR(50) NOT NULL,
    source_format VARCHAR(50),
    title TEXT,
    language VARCHAR(10) DEFAULT 'es',
    page_count INTEGER DEFAULT 0,
    checksum VARCHAR(64) NOT NULL,
    storage_path TEXT,
    original_filename TEXT,
    document_status VARCHAR(50) DEFAULT 'pending',
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT documents_unique_checksum UNIQUE (checksum),
    CONSTRAINT documents_valid_status CHECK (
        document_status IN (
            'pending',
            'processing',
            'completed',
            'failed',
            'archived'
        )
    )
);

ALTER TABLE documents
    ADD CONSTRAINT fk_documents_ingestion_event
    FOREIGN KEY (ingestion_event_id)
    REFERENCES ingestion_events (id)
    ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_documents_org_status
    ON documents (org_id, document_status);

CREATE INDEX IF NOT EXISTS idx_documents_checksum
    ON documents (checksum);

CREATE INDEX IF NOT EXISTS idx_documents_updated_at
    ON documents (updated_at DESC);

COMMENT ON TABLE documents IS
'Repositorio principal de documentos normalizados utilizados por el pipeline RAG 2.0.';

COMMENT ON COLUMN documents.metadata IS
'JSONB flexible con metadatos de conectores, consentimiento y etiquetas contextuales.';

-- ========================================================================
-- Helper trigger: keep updated_at in sync
-- ========================================================================
CREATE OR REPLACE FUNCTION touch_documents_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_documents_updated_at
    BEFORE UPDATE ON documents
    FOR EACH ROW
    EXECUTE FUNCTION touch_documents_updated_at();

-- ========================================================================
-- Table: document_chunks
-- ========================================================================
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    token_count INTEGER NOT NULL,
    page_number INTEGER,
    section_title TEXT,
    language VARCHAR(10) DEFAULT 'es',
    span_offsets JSONB,
    spanish_features JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    CONSTRAINT chunk_index_positive CHECK (chunk_index >= 0),
    CONSTRAINT chunk_token_positive CHECK (token_count >= 0)
);

ALTER TABLE document_chunks
    ADD CONSTRAINT fk_chunks_document
    FOREIGN KEY (document_id)
    REFERENCES documents (id)
    ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_chunks_document_index
    ON document_chunks (document_id, chunk_index);

CREATE INDEX IF NOT EXISTS idx_chunks_language
    ON document_chunks (language);

CREATE INDEX IF NOT EXISTS idx_chunks_span_offsets
    ON document_chunks
    USING GIN (span_offsets);

CREATE INDEX IF NOT EXISTS idx_chunks_spanish_features
    ON document_chunks
    USING GIN (spanish_features);

CREATE OR REPLACE FUNCTION touch_document_chunks_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_document_chunks_updated_at
    BEFORE UPDATE ON document_chunks
    FOR EACH ROW
    EXECUTE FUNCTION touch_document_chunks_updated_at();

COMMENT ON TABLE document_chunks IS
'Fragmentos normalizados listos para embeddings/vector search. Mantienen idioma y secciones.';

-- ========================================================================
-- Table: embeddings
-- ========================================================================
CREATE TABLE IF NOT EXISTS embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    chunk_id UUID NOT NULL,
    document_id UUID NOT NULL,
    provider VARCHAR(50) NOT NULL DEFAULT 'openai',
    model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    dimensions INTEGER NOT NULL DEFAULT 1536,
    embedding VECTOR(1536) NOT NULL,
    cost_cents NUMERIC(10, 4) DEFAULT 0.0,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    metadata JSONB,
    CONSTRAINT fk_embeddings_chunk
        FOREIGN KEY (chunk_id)
        REFERENCES document_chunks (id)
        ON DELETE CASCADE,
    CONSTRAINT fk_embeddings_document
        FOREIGN KEY (document_id)
        REFERENCES documents (id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_embeddings_chunk_id
    ON embeddings (chunk_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_document_id
    ON embeddings (document_id);

CREATE INDEX IF NOT EXISTS idx_embeddings_model
    ON embeddings (model);

-- HNSW index for pgvector (cosine distance)
CREATE INDEX IF NOT EXISTS idx_embeddings_hnsw
    ON embeddings
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 200);

COMMENT ON TABLE embeddings IS
'Vectores pgvector generados por el pipeline de embeddings con metadatos de costo.';

-- ========================================================================
-- Table: consolidation_events
-- Purpose: Event log for ConsolidationSync → Postgres/Neo4j reconciliation
-- ========================================================================
CREATE TABLE IF NOT EXISTS consolidation_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER NOT NULL,
    sqlite_entity_uuid TEXT,
    sqlite_table TEXT,
    event_type VARCHAR(50) NOT NULL,
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processed_at TIMESTAMPTZ,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_consolidation_events_processed
    ON consolidation_events (processed, created_at);

CREATE INDEX IF NOT EXISTS idx_consolidation_events_entity
    ON consolidation_events (entity_type, entity_id);

COMMENT ON TABLE consolidation_events IS
'Bitácora de eventos de ConsolidationSync utilizada para propagar merges a Postgres y Neo4j.';

-- ========================================================================
-- Table: consolidated_entities
-- Purpose: Shadow table for consolidated entity snapshots (Postgres)
-- ========================================================================
CREATE TABLE IF NOT EXISTS consolidated_entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sqlite_entity_id INTEGER NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    name TEXT NOT NULL,
    org_id VARCHAR(100),
    source_count INTEGER DEFAULT 0,
    consensus_confidence FLOAT,
    payload JSONB NOT NULL,
    related_chunk_ids UUID[],
    last_synced_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(sqlite_entity_id, entity_type)
);

CREATE INDEX IF NOT EXISTS idx_consolidated_entities_org
    ON consolidated_entities (org_id, entity_type);

CREATE INDEX IF NOT EXISTS idx_consolidated_entities_confidence
    ON consolidated_entities (consensus_confidence DESC);

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION touch_consolidated_entities_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consolidated_entities_updated_at
    BEFORE UPDATE ON consolidated_entities
    FOR EACH ROW
    EXECUTE FUNCTION touch_consolidated_entities_updated_at();

COMMENT ON TABLE consolidated_entities IS
'Instantáneas consolidadas utilizadas por ConsolidationSync para exponer datos consolidados en PostgreSQL.';

-- ========================================================================
-- Table: consolidated_relationships
-- ========================================================================
CREATE TABLE IF NOT EXISTS consolidated_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sqlite_relationship_id INTEGER,
    relationship_type VARCHAR(100) NOT NULL,
    from_sqlite_entity_id INTEGER NOT NULL,
    to_sqlite_entity_id INTEGER NOT NULL,
    org_id VARCHAR(100),
    relationship_strength FLOAT,
    consensus_confidence FLOAT,
    payload JSONB NOT NULL,
    last_synced_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(relationship_type, from_sqlite_entity_id, to_sqlite_entity_id)
);

CREATE INDEX IF NOT EXISTS idx_consolidated_relationships_org
    ON consolidated_relationships (org_id, relationship_type);

CREATE INDEX IF NOT EXISTS idx_consolidated_relationships_strength
    ON consolidated_relationships (relationship_strength DESC NULLS LAST);

CREATE OR REPLACE FUNCTION touch_consolidated_relationships_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consolidated_relationships_updated_at
    BEFORE UPDATE ON consolidated_relationships
    FOR EACH ROW
    EXECUTE FUNCTION touch_consolidated_relationships_updated_at();

COMMENT ON TABLE consolidated_relationships IS
'Relaciones consolidadas sincronizadas desde SQLite para análisis en Postgres/Neo4j.';

-- ========================================================================
-- Table: consolidated_patterns
-- ========================================================================
CREATE TABLE IF NOT EXISTS consolidated_patterns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sqlite_pattern_id INTEGER,
    pattern_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    org_id VARCHAR(100),
    support_count INTEGER DEFAULT 0,
    payload JSONB NOT NULL,
    last_synced_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    UNIQUE(pattern_type, description)
);

CREATE INDEX IF NOT EXISTS idx_consolidated_patterns_org
    ON consolidated_patterns (org_id, pattern_type);

CREATE OR REPLACE FUNCTION touch_consolidated_patterns_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_consolidated_patterns_updated_at
    BEFORE UPDATE ON consolidated_patterns
    FOR EACH ROW
    EXECUTE FUNCTION touch_consolidated_patterns_updated_at();

COMMENT ON TABLE consolidated_patterns IS
'Patrones consolidados sincronizados para informes y dashboards en Postgres.';

-- ========================================================================
-- Views for operational monitoring
-- ========================================================================
CREATE OR REPLACE VIEW vw_documents_pending_embeddings AS
SELECT
    d.id AS document_id,
    d.org_id,
    COUNT(c.id) FILTER (WHERE e.id IS NULL) AS chunks_without_embedding,
    COUNT(c.id) AS total_chunks,
    MIN(c.created_at) AS first_chunk_created_at
FROM documents d
JOIN document_chunks c ON c.document_id = d.id
LEFT JOIN embeddings e ON e.chunk_id = c.id
GROUP BY d.id, d.org_id
HAVING COUNT(c.id) FILTER (WHERE e.id IS NULL) > 0;

COMMENT ON VIEW vw_documents_pending_embeddings IS
'Ayuda a monitorear chunks pendientes de embeddings para alertar backlog.';

-- ========================================================================
-- Sample policies for ingestion_events to document linkage
-- ========================================================================
ALTER TABLE ingestion_events
    ADD COLUMN IF NOT EXISTS document_row_id UUID;

ALTER TABLE ingestion_events
    ADD CONSTRAINT ingestion_events_document_row_fk
    FOREIGN KEY (document_row_id)
    REFERENCES documents (id)
    ON DELETE SET NULL;

COMMENT ON COLUMN ingestion_events.document_row_id IS
'Referencia directa a documents.id una vez que el archivo fue normalizado.';
