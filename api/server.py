"""
FastAPI server exposing the Agentic RAG endpoints (Task 12).

Endpoints:
    - POST /chat          → Conversational answers with tool-calls + overrides
    - GET  /chat/stream   → SSE stream of reasoning/tool events
    - GET  /health        → Postgres, Neo4j, OCR, LLM readiness probe
    - POST /review/checkpoint → Reviewer approvals for checkpoints
    - POST /evaluate      → Queue retrieval evaluation runs

Features:
    * API-key auth via `X-API-Key` header
    * 60 req/min per-org rate limiting
    * Request logging to reports/api_usage/{date}.jsonl
    * Hybrid search overrides surfaced through `retrieval_overrides`
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from starlette.middleware.base import BaseHTTPMiddleware

from agent.rag_agent import RAGAgent
from agent.tools.graph_search import GraphSearchResponse, graph_search
from agent.tools.hybrid_search import HybridSearchResponse, hybrid_search
from agent.tools.vector_search import VectorSearchResponse, vector_search
from api.models import (
    ChatRequest,
    ChatResponse,
    CheckpointReviewRequest,
    CheckpointReviewResponse,
    EvaluateRequest,
    EvaluateResponse,
    HealthStatus,
    SourceAttribution,
)
from intelligence_capture.ocr.mistral_pixtral_client import MistralPixtralClient

logger = logging.getLogger("api.server")
logging.basicConfig(level=logging.INFO)

rag_agent: Optional[RAGAgent] = None


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """Simple header-based auth."""

    def __init__(self, app: FastAPI, allowed_keys: List[str]):
        super().__init__(app)
        self.allowed_keys = set([key.strip() for key in allowed_keys if key.strip()])
        if not self.allowed_keys:
            self.allowed_keys = {"dev-local"}
            logger.warning(
                "RAG API sin claves configuradas. Usando clave temporal 'dev-local'."
            )
        self.public_paths = {
            "/health",
            "/docs",
            "/openapi.json",
            "/redoc",
        }

    async def dispatch(self, request: Request, call_next):
        if request.url.path in self.public_paths:
            return await call_next(request)

        api_key = request.headers.get("x-api-key")
        if api_key not in self.allowed_keys:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida")

        return await call_next(request)


class RateLimiter:
    """In-memory sliding-window limiter per org."""

    def __init__(self, limit_per_minute: int = 60):
        self.limit = limit_per_minute
        self._lock = asyncio.Lock()
        self._windows: Dict[str, deque] = defaultdict(deque)

    async def check(self, org_id: str) -> None:
        async with self._lock:
            now = time.time()
            window_start = now - 60
            bucket = self._windows[org_id]

            while bucket and bucket[0] < window_start:
                bucket.popleft()

            if len(bucket) >= self.limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Límite de 60 solicitudes por minuto excedido para esta organización",
                )

            bucket.append(now)


class APIUsageLogger:
    """Append-only logger for API usage analytics."""

    def __init__(self, reports_dir: Optional[Path] = None):
        if reports_dir is None:
            reports_dir = Path(__file__).resolve().parents[1] / "reports" / "api_usage"
        self.reports_dir = reports_dir
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    async def log(self, payload: Dict[str, Any]) -> None:
        payload = dict(payload)
        payload["timestamp"] = datetime.utcnow().isoformat()
        path = self.reports_dir / f"{payload['timestamp'][:10]}.jsonl"

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write, path, payload)

    @staticmethod
    def _write(path: Path, record: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


class CheckpointLogger:
    """Persists checkpoint reviews for governance."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1] / "reports" / "checkpoints"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def record(self, entry: Dict[str, Any]) -> None:
        file_path = self.base_dir / "reviews.jsonl"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write, file_path, entry)

    @staticmethod
    def _write(path: Path, entry: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


class EvaluationLogger:
    """Stores evaluation requests for asynchronous execution."""

    def __init__(self, base_dir: Optional[Path] = None):
        if base_dir is None:
            base_dir = Path(__file__).resolve().parents[1] / "reports" / "evaluations"
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def enqueue(self, entry: Dict[str, Any]) -> None:
        file_path = self.base_dir / "requests.jsonl"
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._write, file_path, entry)

    @staticmethod
    def _write(path: Path, entry: Dict[str, Any]) -> None:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


rate_limiter = RateLimiter(limit_per_minute=60)
api_logger = APIUsageLogger()
checkpoint_logger = CheckpointLogger()
evaluation_logger = EvaluationLogger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize RAG agent on startup and close resources on shutdown."""
    global rag_agent
    logger.info("Inicializando RAGAgent para API...")
    rag_agent = await RAGAgent.create()
    yield
    if rag_agent:
        await rag_agent.close()
        logger.info("RAGAgent cerrado correctamente")


app = FastAPI(
    title="Comversa Agentic RAG API",
    description="API conversacional alimentada por RAG 2.0 con aislamiento multi-organización.",
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

origins = [
    "http://localhost:3000",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

allowed_api_keys = os.getenv("RAG_API_KEYS", os.getenv("RAG_API_KEY", "")).split(",")
app.add_middleware(APIKeyAuthMiddleware, allowed_keys=allowed_api_keys)


async def get_agent() -> RAGAgent:
    if rag_agent is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agente no inicializado",
        )
    return rag_agent


def _sse_event(event: str, data: Dict[str, Any]) -> str:
    """Format data as SSE frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def _serialize_tool_call(call: Dict[str, Any]) -> Dict[str, Any]:
    """Serialize tool call payloads into JSON-friendly dicts."""
    try:
        json.dumps(call, ensure_ascii=False)
        return call
    except TypeError:
        return json.loads(json.dumps(call, default=str))


def _extract_sources_from_calls(tool_calls: Optional[List[Dict[str, Any]]]) -> List[SourceAttribution]:
    """Best-effort extraction of sources from tool call payloads."""
    sources: List[SourceAttribution] = []
    if not tool_calls:
        return sources

    for idx, call in enumerate(tool_calls):
        tool_name = (
            call.get("tool_name")
            or call.get("name")
            or call.get("id")
            or f"tool-{idx}"
        )

        if "vector" in tool_name:
            source_type = "vector"
        elif "graph" in tool_name:
            source_type = "graph"
        elif "hybrid" in tool_name:
            source_type = "hybrid"
        else:
            source_type = "checkpoint"

        sources.append(
            SourceAttribution(
                source_type=source_type,  # type: ignore[arg-type]
                reference_id=str(call.get("id", f"{tool_name}-{idx}")),
                score=None,
                metadata={"tool_call": _serialize_tool_call(call)},
            )
        )

    return sources


def _vector_sources(response: VectorSearchResponse) -> List[SourceAttribution]:
    sources: List[SourceAttribution] = []
    for item in response.results:
        sources.append(
            SourceAttribution(
                source_type="vector",
                reference_id=str(item.chunk_id),
                score=item.similarity_score,
                metadata={
                    "document_id": str(item.document_id),
                    "document_title": item.metadata.get("document_title"),
                    "page": item.page_number,
                    "section": item.section_title,
                },
            )
        )
    return sources


def _graph_sources(response: GraphSearchResponse) -> List[SourceAttribution]:
    sources: List[SourceAttribution] = []
    for node in response.nodes:
        sources.append(
            SourceAttribution(
                source_type="graph",
                reference_id=node.entity_id,
                score=None,
                metadata={
                    "entity_type": node.entity_type,
                    "name": node.name,
                    "properties": node.properties,
                },
            )
        )
    return sources


def _hybrid_sources(response: HybridSearchResponse) -> List[SourceAttribution]:
    sources: List[SourceAttribution] = []
    for item in response.results:
        sources.append(
            SourceAttribution(
                source_type=item.source_type,  # type: ignore[arg-type]
                reference_id=item.metadata.get("chunk_id")
                or item.metadata.get("entity_id")
                or str(uuid.uuid4()),
                score=item.score,
                metadata=item.metadata,
            )
        )
    return sources


def _summarize_vector(response: VectorSearchResponse) -> str:
    if not response.results:
        return "No encontré fragmentos relevantes via búsqueda vectorial."

    lines = [
        "Resumen generado con búsqueda vectorial (pgvector):",
    ]
    for idx, chunk in enumerate(response.results[:3], start=1):
        snippet = chunk.content.strip().replace("\n", " ")
        snippet = snippet[:220] + ("…" if len(snippet) > 220 else "")
        title = chunk.metadata.get("document_title")
        lines.append(f"{idx}. {snippet} (doc: {title}, score={chunk.similarity_score:.3f})")
    return "\n".join(lines)


def _summarize_graph(response: GraphSearchResponse) -> str:
    if not response.nodes:
        return "No encontré nodos relevantes en Neo4j para esta consulta."

    lines = [
        "Resumen generado con búsqueda en el grafo (Neo4j):",
    ]
    for idx, node in enumerate(response.nodes[:3], start=1):
        lines.append(
            f"{idx}. {node.entity_type}: {node.name} (org={node.org_id})"
        )
    return "\n".join(lines)


def _summarize_hybrid(response: HybridSearchResponse) -> str:
    if not response.results:
        return "La búsqueda híbrida no devolvió resultados relevantes."

    lines = [
        "Búsqueda híbrida (vector + grafo) con pesos "
        f"{response.weight_vector:.2f}/{response.weight_graph:.2f}:",
    ]
    for idx, item in enumerate(response.results[:5], start=1):
        lines.append(f"{idx}. [{item.source_type}] {item.content} (score={item.score:.4f})")
    return "\n".join(lines)


async def _execute_direct_retrieval(
    payload: ChatRequest,
    agent: RAGAgent,
) -> Dict[str, Any]:
    overrides = payload.retrieval_overrides or {}
    session_identifier = payload.session_id or f"direct-{uuid.uuid4()}"

    if payload.retrieval_mode == "vector":
        params = overrides.get("vector_search", {})
        top_k = int(params.get("top_k", 5))
        context = params.get("context", payload.context)
        response = await vector_search(
            query=payload.query,
            org_id=payload.org_id,
            context=context,
            top_k=top_k,
            db_pool=agent.db_pool,
            openai_client=agent.openai_client,
            instrumentation_hook=agent.instrumentation.emit,
        )
        await agent.telemetry.log_tool_usage(
            session_id=session_identifier,
            org_id=payload.org_id,
            tool_name="vector_search",
            query=payload.query,
            parameters={"context": context, "top_k": top_k},
            success=True,
            execution_time_ms=response.execution_time_ms,
            result_count=response.total_found,
            cache_hit=response.cache_hit,
            retrieval_mode=payload.retrieval_mode,
        )
        answer = _summarize_vector(response)
        sources = _vector_sources(response)
        tool_calls = [
            {
                "tool_name": "vector_search",
                "parameters": {"context": context, "top_k": top_k},
                "result_count": response.total_found,
                "cache_hit": response.cache_hit,
            }
        ]
        return {
            "answer": answer,
            "session_id": session_identifier,
            "model": "direct:vector_search",
            "tool_calls": tool_calls,
            "sources": sources,
            "applied_overrides": overrides,
        }

    if payload.retrieval_mode == "graph":
        params = overrides.get("graph_search", {})
        limit = int(params.get("limit", 20))
        rel_types = params.get("relationship_types")
        response = await graph_search(
            query=payload.query,
            org_id=payload.org_id,
            relationship_types=rel_types,
            limit=limit,
            neo4j_driver=agent.neo4j_driver,
            instrumentation_hook=agent.instrumentation.emit,
        )
        await agent.telemetry.log_tool_usage(
            session_id=session_identifier,
            org_id=payload.org_id,
            tool_name="graph_search",
            query=payload.query,
            parameters={"relationship_types": rel_types, "limit": limit},
            success=True,
            execution_time_ms=response.execution_time_ms,
            result_count=response.total_nodes,
            cache_hit=response.cache_hit,
            retrieval_mode=payload.retrieval_mode,
        )
        answer = _summarize_graph(response)
        sources = _graph_sources(response)
        tool_calls = [
            {
                "tool_name": "graph_search",
                "parameters": {"relationship_types": rel_types, "limit": limit},
                "result_count": response.total_nodes,
                "cache_hit": response.cache_hit,
            }
        ]
        return {
            "answer": answer,
            "session_id": session_identifier,
            "model": "direct:graph_search",
            "tool_calls": tool_calls,
            "sources": sources,
            "applied_overrides": overrides,
        }

    # Hybrid fallback
    params = overrides.get("hybrid_search", {})
    top_k = int(params.get("top_k", 5))
    weight_vector = float(params.get("weight_vector", 0.5))
    weight_graph = float(params.get("weight_graph", 0.5))
    rel_types = params.get("relationship_types")
    context = params.get("context", payload.context)

    response = await hybrid_search(
        query=payload.query,
        org_id=payload.org_id,
        context=context,
        relationship_types=rel_types,
        top_k=top_k,
        weight_vector=weight_vector,
        weight_graph=weight_graph,
        db_pool=agent.db_pool,
        neo4j_driver=agent.neo4j_driver,
        openai_client=agent.openai_client,
        instrumentation_hook=agent.instrumentation.emit,
    )
    await agent.telemetry.log_tool_usage(
        session_id=session_identifier,
        org_id=payload.org_id,
        tool_name="hybrid_search",
        query=payload.query,
        parameters={
            "context": context,
            "relationship_types": rel_types,
            "top_k": top_k,
            "weight_vector": weight_vector,
            "weight_graph": weight_graph,
        },
        success=True,
        execution_time_ms=response.execution_time_ms,
        result_count=response.total_results,
        cache_hit=response.cache_hit,
        retrieval_mode=payload.retrieval_mode,
    )
    answer = _summarize_hybrid(response)
    sources = _hybrid_sources(response)
    tool_calls = [
        {
            "tool_name": "hybrid_search",
            "parameters": {
                "context": context,
                "relationship_types": rel_types,
                "top_k": top_k,
                "weight_vector": weight_vector,
                "weight_graph": weight_graph,
            },
            "result_count": response.total_results,
            "cache_hit": response.cache_hit,
        }
    ]
    return {
        "answer": answer,
        "session_id": session_identifier,
        "model": "direct:hybrid_search",
        "tool_calls": tool_calls,
        "sources": sources,
        "applied_overrides": overrides or response.overrides_applied,
    }


async def _execute_chat(payload: ChatRequest, agent: RAGAgent) -> Dict[str, Any]:
    if payload.retrieval_mode != "auto":
        return await _execute_direct_retrieval(payload, agent)

    agent_result = await agent.query(
        query=payload.query,
        org_id=payload.org_id,
        context=payload.context,
        session_id=payload.session_id,
        retrieval_overrides=payload.retrieval_overrides,
    )

    sources = _extract_sources_from_calls(agent_result.get("tool_calls"))

    return {
        "answer": agent_result["answer"],
        "session_id": agent_result["session_id"],
        "model": agent_result.get("model", agent.config.primary_model),
        "tool_calls": agent_result.get("tool_calls", []),
        "sources": sources,
        "applied_overrides": agent_result.get(
            "applied_overrides",
            payload.retrieval_overrides or {},
        ),
    }


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest, agent: RAGAgent = Depends(get_agent)):
    await rate_limiter.check(payload.org_id)
    start = time.perf_counter()

    try:
        result = await _execute_chat(payload, agent)
        latency = (time.perf_counter() - start) * 1000
        response = ChatResponse(
            **result,
            latency_ms=latency,
            retrieval_mode=payload.retrieval_mode,
        )
        await api_logger.log(
            {
                "endpoint": "/chat",
                "org_id": payload.org_id,
                "session_id": response.session_id,
                "latency_ms": latency,
                "retrieval_mode": payload.retrieval_mode,
                "success": True,
            }
        )
        return response

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Fallo en /chat: %s", exc)
        await api_logger.log(
            {
                "endpoint": "/chat",
                "org_id": payload.org_id,
                "session_id": payload.session_id,
                "success": False,
                "error": str(exc),
            }
        )
        raise HTTPException(status_code=500, detail="Error interno procesando la consulta")


@app.get("/chat/stream")
async def chat_stream_endpoint(
    request: Request,
    org_id: str = Query(..., description="Organización solicitante"),
    query: str = Query(..., description="Pregunta del usuario"),
    session_id: Optional[str] = Query(None),
    context: Optional[str] = Query(None),
    retrieval_mode: str = Query("auto"),
    overrides: Optional[str] = Query(
        None,
        description="Overrides en JSON para herramientas (opcional)",
    ),
    agent: RAGAgent = Depends(get_agent),
):
    await rate_limiter.check(org_id)

    retrieval_overrides = None
    if overrides:
        try:
            retrieval_overrides = json.loads(overrides)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Overrides inválidos: {exc}") from exc

    try:
        payload = ChatRequest(
            org_id=org_id,
            query=query,
            context=context,
            session_id=session_id,
            retrieval_mode=retrieval_mode,  # type: ignore[arg-type]
            retrieval_overrides=retrieval_overrides,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors()) from exc

    async def event_stream() -> AsyncIterator[str]:
        start = time.perf_counter()
        yield _sse_event("status", {"state": "received"})

        try:
            result = await _execute_chat(payload, agent)
            for idx, call in enumerate(result.get("tool_calls", [])):
                yield _sse_event(
                    "tool_call",
                    {"index": idx, "tool_call": call},
                )

            latency = (time.perf_counter() - start) * 1000
            final_payload = ChatResponse(
                **result,
                latency_ms=latency,
                retrieval_mode=retrieval_mode,  # type: ignore[arg-type]
            )
            yield _sse_event("answer", final_payload.dict())
            await api_logger.log(
                {
                    "endpoint": "/chat/stream",
                    "org_id": org_id,
                    "session_id": final_payload.session_id,
                    "latency_ms": latency,
                    "retrieval_mode": retrieval_mode,
                    "success": True,
                }
            )

        except asyncio.CancelledError:
            logger.info("Cliente canceló stream para org=%s", org_id)
            raise

        except Exception as exc:
            logger.exception("Fallo en /chat/stream: %s", exc)
            await api_logger.log(
                {
                    "endpoint": "/chat/stream",
                    "org_id": org_id,
                    "session_id": session_id,
                    "success": False,
                    "error": str(exc),
                }
            )
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
async def health_endpoint(agent: RAGAgent = Depends(get_agent)):
    postgres_ok = False
    neo4j_ok = False
    ocr_ok = False
    llm_ok = bool(os.getenv("OPENAI_API_KEY"))

    try:
        async with agent.db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        postgres_ok = True
    except Exception as exc:
        logger.warning("Postgres no disponible: %s", exc)

    try:
        async with agent.neo4j_driver.session() as session:
            await session.run("RETURN 1")
        neo4j_ok = True
    except Exception as exc:
        logger.warning("Neo4j no disponible: %s", exc)

    try:
        MistralPixtralClient()
        ocr_ok = True
    except Exception as exc:
        logger.warning("OCR (Mistral Pixtral) no disponible: %s", exc)

    status_label = (
        "healthy" if postgres_ok and neo4j_ok and llm_ok else "degraded"
    )

    health = HealthStatus(
        postgres=postgres_ok,
        neo4j=neo4j_ok,
        ocr=ocr_ok,
        llm=llm_ok,
        timestamp=datetime.utcnow(),
    )

    return {"status": status_label, "details": health}


@app.post("/review/checkpoint", response_model=CheckpointReviewResponse)
async def review_checkpoint(payload: CheckpointReviewRequest):
    review_id = str(uuid.uuid4())
    record = {
        "review_id": review_id,
        "recorded_at": datetime.utcnow().isoformat(),
        **payload.dict(),
    }
    await checkpoint_logger.record(record)
    return CheckpointReviewResponse(
        review_id=review_id,
        recorded_at=datetime.utcnow(),
        status=payload.status,
    )


@app.post("/evaluate", response_model=EvaluateResponse)
async def enqueue_evaluation(payload: EvaluateRequest):
    request_id = str(uuid.uuid4())
    record = {
        "request_id": request_id,
        "org_id": payload.org_id,
        "dataset": payload.dataset,
        "mode": payload.mode,
        "threshold_mrr": payload.threshold_mrr,
        "status": "queued",
        "requested_at": datetime.utcnow().isoformat(),
    }
    await evaluation_logger.enqueue(record)
    return EvaluateResponse(
        request_id=request_id,
        status="queued",
        message="Evaluación registrada; ejecutar scripts/evaluate_retrieval.py para procesar.",
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "message": "Payload inválido"},
    )
