"""
Pruebas para los modelos de persistencia Postgres.
"""
from uuid import UUID, uuid4

from intelligence_capture.persistence.models import (
    DocumentChunkPayload,
    DocumentPayload,
)


def test_document_payload_resolves_ingestion_uuid_first():
    ingestion_uuid = uuid4()
    payload = DocumentPayload(
        org_id="los_tajibos",
        source_type="manual_upload",
        checksum="abc123",
        storage_path="data/documents/originals/abc.pdf",
        metadata={"lang": "es"},
        ingestion_document_uuid=ingestion_uuid,
    )

    resolved_once = payload.resolve_document_id()
    resolved_twice = payload.resolve_document_id()

    assert resolved_once == ingestion_uuid
    assert resolved_twice == ingestion_uuid


def test_document_chunk_payload_as_record_serializes_optional_fields():
    document_id = uuid4()
    chunk = DocumentChunkPayload(
        content="Procesamos órdenes manuales todos los días.",
        chunk_index=0,
        token_count=12,
        page_number=1,
        section_title="Resumen",
        span_offsets={"start": 0, "end": 42},
    )

    record = chunk.as_record(document_id)

    assert UUID(record["document_id"]) == document_id
    assert record["chunk_index"] == 0
    assert record["language"] == "es"
    assert record["span_offsets"]["start"] == 0
