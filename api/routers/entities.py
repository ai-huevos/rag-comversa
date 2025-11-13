"""
Entities Router

CRUD endpoints for browsing and searching consolidated entities.
Supports filtering, pagination, and search.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from api.models.schemas import EntityListResponse, EntityDetailResponse
from api.services.postgres_service import PostgresService

router = APIRouter(prefix="/api/entities", tags=["Entities"])
db_service = PostgresService()


@router.get("/", response_model=EntityListResponse)
async def list_entities(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (pain_point, process, system, etc.)"),
    company: Optional[str] = Query(None, description="Filter by company name"),
    search: Optional[str] = Query(None, description="Search in entity name (case-insensitive)"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page (max 200)")
):
    """
    List entities with optional filters

    Query parameters:
    - entity_type: Filter by entity type (e.g., 'pain_point', 'process', 'system')
    - company: Filter by company name (e.g., 'Los Tajibos', 'Comversa', 'Bolivian Foods')
    - search: Search term for entity names (case-insensitive partial match)
    - page: Page number starting from 1
    - page_size: Number of items per page (1-200)

    Returns:
        EntityListResponse: Paginated entity list with metadata

    Example:
        GET /api/entities?entity_type=pain_point&company=Los Tajibos&page=1&page_size=20
    """
    try:
        entities, total = db_service.get_entities(
            entity_type=entity_type,
            company=company,
            search=search,
            page=page,
            page_size=page_size
        )

        has_next = (page * page_size) < total

        return EntityListResponse(
            entities=entities,
            total=total,
            page=page,
            page_size=page_size,
            has_next=has_next
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving entities: {str(e)}"
        )


@router.get("/{entity_id}", response_model=EntityDetailResponse)
async def get_entity(entity_id: int):
    """
    Get detailed entity information by ID

    Args:
        entity_id: Entity ID from consolidated_entities table

    Returns:
        EntityDetailResponse: Full entity details including metadata and sources

    Raises:
        HTTPException: 404 if entity not found, 500 on database error

    Example:
        GET /api/entities/42
    """
    try:
        entity = db_service.get_entity_detail(entity_id)

        if not entity:
            raise HTTPException(
                status_code=404,
                detail=f"Entity with ID {entity_id} not found"
            )

        return entity

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving entity: {str(e)}"
        )


@router.get("/types/available")
async def get_available_entity_types():
    """
    Get list of available entity types in the database

    Returns:
        dict: Dictionary with entity types and their counts

    Example response:
        {
            "pain_point": 250,
            "process": 170,
            "system": 183,
            "kpi": 90,
            ...
        }
    """
    try:
        query = """
        SELECT entity_type, COUNT(*) as count
        FROM consolidated_entities
        GROUP BY entity_type
        ORDER BY count DESC
        """
        results = db_service.execute_query(query)

        return {row["entity_type"]: row["count"] for row in results}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving entity types: {str(e)}"
        )


@router.get("/companies/available")
async def get_available_companies():
    """
    Get list of companies in the database

    Returns:
        List[str]: List of unique company names

    Example response:
        ["Los Tajibos", "Comversa", "Bolivian Foods"]
    """
    try:
        query = """
        SELECT DISTINCT metadata->>'company' as company
        FROM consolidated_entities
        WHERE metadata->>'company' IS NOT NULL
        ORDER BY company
        """
        results = db_service.execute_query(query)

        return [row["company"] for row in results]

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving companies: {str(e)}"
        )
