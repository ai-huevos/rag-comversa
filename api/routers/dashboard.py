"""
Dashboard Router

Main dashboard data endpoint that aggregates all dashboard components.
Returns data in Spanish as stored in the database.
"""

from fastapi import APIRouter, HTTPException
from api.models.schemas import DashboardData
from api.services.postgres_service import PostgresService

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])
db_service = PostgresService()


@router.get("/", response_model=DashboardData)
async def get_dashboard_data():
    """
    Get complete dashboard data

    Returns consolidated dashboard data including:
    - Summary statistics (total entities, processes, systems, etc.)
    - Company distribution
    - Critical pain points
    - Systems breakdown
    - Process frequency distribution

    All content returned in Spanish as stored in database.

    Returns:
        DashboardData: Complete dashboard payload

    Raises:
        HTTPException: 500 if database query fails
    """
    try:
        # Aggregate all dashboard components
        summary = db_service.get_dashboard_summary()
        companies = db_service.get_company_distribution()
        pain_points = db_service.get_critical_pain_points(limit=10)
        systems = db_service.get_systems_breakdown()
        frequency = db_service.get_process_frequency()

        return DashboardData(
            summary=summary,
            companies=companies,
            critical_pain_points=pain_points,
            systems_breakdown=systems,
            process_frequency=frequency
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving dashboard data: {str(e)}"
        )


@router.get("/summary")
async def get_summary_only():
    """
    Get dashboard summary statistics only

    Lightweight endpoint for just the top-level metrics.

    Returns:
        DashboardSummary: Summary statistics
    """
    try:
        return db_service.get_dashboard_summary()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving summary: {str(e)}"
        )


@router.get("/companies")
async def get_companies_only():
    """
    Get company distribution data only

    Returns:
        List[CompanyData]: Company distribution
    """
    try:
        return db_service.get_company_distribution()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving company data: {str(e)}"
        )


@router.get("/pain-points")
async def get_pain_points_only(limit: int = 10):
    """
    Get critical pain points only

    Args:
        limit: Maximum number of pain points to return (default 10)

    Returns:
        List[PainPoint]: Critical pain points
    """
    try:
        return db_service.get_critical_pain_points(limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving pain points: {str(e)}"
        )
