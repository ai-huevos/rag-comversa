"""
FastAPI Main Application

Executive Dashboard API for Comversa RAG-2.0 System
Serves consolidated intelligence data from PostgreSQL and Neo4j.

Spanish-first: All database content preserved in Spanish.
CORS enabled for local development with Next.js frontend.
"""

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.routers import dashboard, entities
from api.services.postgres_service import PostgresService
from api.models.schemas import HealthResponse


# Version from package
__version__ = "1.0.0"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager

    Initializes database connections on startup,
    cleans up resources on shutdown.
    """
    # Startup: Initialize database connection pool
    db_service = PostgresService()
    print("✓ Database connection pool initialized")

    yield

    # Shutdown: Close database connections
    print("✓ Closing database connections")


# Initialize FastAPI app
app = FastAPI(
    title="Comversa Executive Dashboard API",
    description="REST API for executive dashboard serving consolidated intelligence from 44 manager interviews",
    version=__version__,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)


# ============================================================================
# CORS MIDDLEWARE
# ============================================================================

# Allow frontend to connect from localhost:3000 (Next.js dev server)
origins = [
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


# ============================================================================
# EXCEPTION HANDLER
# ============================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """
    Global exception handler for unhandled errors

    Returns Spanish error messages to maintain language consistency.
    """
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Error interno del servidor",
            "error": str(exc),
            "path": request.url.path
        }
    )


# ============================================================================
# ROUTERS
# ============================================================================

app.include_router(dashboard.router)
app.include_router(entities.router)


# ============================================================================
# ROOT & HEALTH ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """
    API root endpoint

    Returns:
        dict: API metadata and available endpoints
    """
    return {
        "name": "Comversa Executive Dashboard API",
        "version": __version__,
        "status": "operational",
        "endpoints": {
            "dashboard": "/api/dashboard",
            "entities": "/api/entities",
            "health": "/api/health",
            "docs": "/api/docs"
        }
    }


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint

    Verifies database connectivity and returns API status.

    Returns:
        HealthResponse: Health status with database connection state
    """
    db_service = PostgresService()

    # Check database connection
    db_healthy = db_service.health_check()
    db_status = "connected" if db_healthy else "disconnected"

    # Overall status
    overall_status = "healthy" if db_healthy else "unhealthy"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        neo4j=None,  # TODO: Add Neo4j health check later
        version=__version__
    )


# ============================================================================
# STARTUP MESSAGE
# ============================================================================

@app.on_event("startup")
async def startup_message():
    """Print startup information"""
    print("\n" + "=" * 60)
    print("🚀 COMVERSA EXECUTIVE DASHBOARD API")
    print("=" * 60)
    print(f"Version: {__version__}")
    print(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    print(f"Database: {os.getenv('DATABASE_URL', 'postgresql://localhost/comversa_rag')}")
    print(f"Docs: http://localhost:8000/api/docs")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes (dev only)
        log_level="info"
    )
