"""
Pruebas unitarias para el pipeline de embeddings.
"""
from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest

from intelligence_capture.embeddings.pipeline import (
    EmbeddingPipeline,
    EmbeddingPipelineConfig,
)
from intelligence_capture.persistence.models import DocumentChunkPayload


class DummyEmbeddingsAPI:
    def __init__(self):
        self.calls = []

    async def create(self, *, model: str, input: list[str]):
        self.calls.append({"model": model, "input": input})
        # Cada vector será un valor único basado en el largo del texto
        return SimpleNamespace(
            data=[SimpleNamespace(embedding=[float(len(text))]) for text in input]
        )


class DummyOpenAIClient:
    def __init__(self):
        self.embeddings = DummyEmbeddingsAPI()


def test_embedding_pipeline_generates_and_caches_vectors():
    document_id = uuid4()
    chunks = [
        DocumentChunkPayload(content="Hola mundo", chunk_index=0, token_count=10),
        DocumentChunkPayload(content="Duplicado", chunk_index=1, token_count=9),
    ]

    client = DummyOpenAIClient()
    pipeline = EmbeddingPipeline(
        openai_client=client,
        config=EmbeddingPipelineConfig(
            batch_size=2,
            requests_per_second=1000,
            max_retries=1,
        ),
    )

    first_run = asyncio.run(pipeline.embed_document_chunks(document_id, chunks))
    second_run = asyncio.run(pipeline.embed_document_chunks(document_id, chunks))

    # Solo una llamada real gracias a la caché
    assert len(client.embeddings.calls) == 1
    assert len(first_run) == 2
    assert len(second_run) == 2
    assert second_run[0].metadata["cache_hit"] is True
    assert second_run[1].metadata["cache_hit"] is True
