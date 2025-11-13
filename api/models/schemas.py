"""
Pydantic Models for Executive Dashboard API

All models preserve Spanish content from database.
Type-safe data structures matching the frontend TypeScript interfaces.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class CompanyData(BaseModel):
    """Company distribution data"""
    name: str = Field(..., description="Company name in Spanish")
    employees: int = Field(..., description="Number of interviewed employees")
    processes: int = Field(..., description="Number of processes")
    systems: int = Field(..., description="Number of systems")
    color: str = Field(..., description="Brand color hex code")


class Trend(BaseModel):
    """Metric trend data"""
    value: float = Field(..., description="Percentage change")
    is_positive: bool = Field(..., description="Whether trend is positive")


class MetricCard(BaseModel):
    """Dashboard metric card data"""
    title: str = Field(..., description="Metric title in Spanish")
    value: int = Field(..., description="Metric value")
    subtitle: str = Field(..., description="Metric subtitle in Spanish")
    icon: str = Field(..., description="Icon name (lucide-react)")
    trend: Optional[Trend] = Field(None, description="Optional trend data")


class PainPoint(BaseModel):
    """Pain point data with priority and impact"""
    id: str = Field(..., description="Pain point ID (UUID)")
    title: str = Field(..., description="Pain point title in Spanish")
    priority: Literal["Crítica", "Alta", "Media", "Baja"] = Field(..., description="Priority level")
    impact: str = Field(..., description="Business impact in Spanish")
    times_saved: str = Field(..., description="Time/cost savings estimate")
    company: str = Field(..., description="Company name")
    department: Optional[str] = Field(None, description="Department name")


class SystemsBreakdown(BaseModel):
    """Technology systems breakdown"""
    critical: int = Field(..., description="Number of critical systems")
    important: int = Field(..., description="Number of important systems")
    support: int = Field(..., description="Number of support systems")
    total: int = Field(..., description="Total number of systems")


class ProcessFrequency(BaseModel):
    """Process frequency distribution"""
    daily: int = Field(..., description="Number of daily processes")
    weekly: int = Field(..., description="Number of weekly processes")
    monthly: int = Field(..., description="Number of monthly processes")
    annual: int = Field(..., description="Number of annual processes")


class DashboardSummary(BaseModel):
    """Overall dashboard summary statistics"""
    total_entities: int = Field(..., description="Total consolidated entities")
    total_processes: int = Field(..., description="Total processes")
    total_systems: int = Field(..., description="Total systems")
    total_data_flows: int = Field(..., description="Total data flows")
    total_employees: int = Field(..., description="Total interviewed employees")
    interviews_completed: int = Field(..., description="Number of completed interviews")
    last_updated: str = Field(..., description="Last update timestamp ISO 8601")


class DashboardData(BaseModel):
    """Complete dashboard data payload"""
    summary: DashboardSummary
    companies: List[CompanyData]
    critical_pain_points: List[PainPoint]
    systems_breakdown: SystemsBreakdown
    process_frequency: ProcessFrequency


class EntityListItem(BaseModel):
    """Individual entity list item"""
    id: str = Field(..., description="Entity ID (UUID)")
    entity_type: str = Field(..., description="Entity type (pain_point, process, system, etc.)")
    name: str = Field(..., description="Entity name/description in Spanish")
    company: str
    department: Optional[str] = None
    severity: Optional[str] = None
    frequency: Optional[str] = None
    confidence: float = Field(..., description="Consensus confidence score 0-1")
    source_count: int = Field(..., description="Number of source interviews")
    created_at: datetime


class EntityListResponse(BaseModel):
    """Paginated entity list response"""
    entities: List[EntityListItem]
    total: int
    page: int
    page_size: int
    has_next: bool


class EntityDetailResponse(BaseModel):
    """Detailed entity information"""
    id: str = Field(..., description="Entity ID (UUID)")
    entity_type: str
    name: str
    description: str = Field(..., description="Full description in Spanish")
    company: str
    department: Optional[str] = None
    metadata: dict = Field(..., description="Additional entity-specific metadata")
    confidence: float
    source_count: int
    sources: List[str] = Field(..., description="Interview respondent names")
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """API health check response"""
    status: str = Field(..., description="API status: 'healthy' or 'unhealthy'")
    database: str = Field(..., description="Database connection status")
    neo4j: Optional[str] = Field(None, description="Neo4j connection status")
    version: str = Field(..., description="API version")
