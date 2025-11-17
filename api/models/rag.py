"""
Pydantic models for the Agentic RAG API endpoints (Task 12).
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class SourceAttribution(BaseModel):
    """Single cited source returned to clients."""

    source_type: Literal["vector", "graph", "hybrid", "checkpoint"]
    reference_id: str = Field(..., description="Chunk ID, entity ID o referencia externa")
    score: Optional[float] = Field(None, description="Puntaje de similitud/confianza")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Chat/completions request payload for RAG API."""

    org_id: str = Field(..., description="Identificador de organización (namespace)")
    query: str = Field(..., description="Pregunta del usuario en español")
    context: Optional[str] = Field(None, description="Contexto de negocio opcional")
    session_id: Optional[str] = Field(
        None,
        description="ID de sesión para conversaciones multi-turno",
    )
    retrieval_mode: Literal["auto", "vector", "graph", "hybrid"] = Field(
        "auto",
        description="Modo preferido de búsqueda; 'auto' delega en el agente",
    )
    retrieval_overrides: Optional[Dict[str, Dict[str, Any]]] = Field(
        None,
        description="Overrides para herramientas (p. ej. pesos de hybrid_search)",
    )


class ChatResponse(BaseModel):
    """Structured agent response payload."""

    answer: str
    session_id: str
    model: str
    latency_ms: float
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    sources: List[SourceAttribution] = Field(default_factory=list)
    applied_overrides: Dict[str, Any] = Field(default_factory=dict)
    retrieval_mode: Literal["auto", "vector", "graph", "hybrid"] = "auto"


class HealthStatus(BaseModel):
    """Detailed subsystem health metrics."""

    postgres: bool
    neo4j: bool
    ocr: bool
    llm: bool
    timestamp: datetime


class CheckpointReviewRequest(BaseModel):
    """Payload for /review/checkpoint submissions."""

    org_id: str
    stage: str = Field(..., description="Etapa del checkpoint (ingestion, ocr, evaluation, etc.)")
    reviewer: str = Field(..., description="Nombre de la persona que revisa")
    status: Literal["approved", "rejected", "needs_changes"]
    notes: Optional[str] = Field(None, description="Notas en español")
    reference_path: Optional[str] = Field(
        None, description="Ruta relativa al bundle de evidencia revisado"
    )


class CheckpointReviewResponse(BaseModel):
    """Response confirming checkpoint review capture."""

    review_id: str
    recorded_at: datetime
    status: str


class EvaluateRequest(BaseModel):
    """Payload to trigger /evaluate runs."""

    org_id: str
    dataset: Optional[str] = Field(
        None, description="Nombre del dataset (default: tests/data/rag_eval/es_queries.json)"
    )
    mode: Literal["vector", "graph", "hybrid", "all"] = "all"
    threshold_mrr: Optional[float] = Field(
        None, description="MRR mínimo aceptable para bloquear despliegues"
    )


class EvaluateResponse(BaseModel):
    """Response returned after enqueueing evaluation."""

    request_id: str
    status: Literal["queued", "running", "completed"]
    message: str
