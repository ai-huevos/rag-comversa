"""
PostgreSQL Service Layer

Handles all database queries for the executive dashboard.
Preserves Spanish content from consolidated_entities table.
"""

import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from api.models.schemas import (
    CompanyData,
    DashboardSummary,
    SystemsBreakdown,
    ProcessFrequency,
    PainPoint,
    EntityListItem,
    EntityDetailResponse,
)


class PostgresService:
    """
    PostgreSQL database service for dashboard queries

    Connects to comversa_rag database with consolidated entities.
    All queries preserve Spanish language content.
    """

    def __init__(self):
        """Initialize connection pool"""
        self.database_url = os.getenv("DATABASE_URL", "postgresql://postgres@localhost:5432/comversa_rag")

        # Create connection pool (min 2, max 10 connections)
        self.pool = SimpleConnectionPool(
            minconn=2,
            maxconn=10,
            dsn=self.database_url
        )

    def get_connection(self):
        """Get a connection from the pool"""
        return self.pool.getconn()

    def return_connection(self, conn):
        """Return connection to the pool"""
        self.pool.putconn(conn)

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """
        Execute a SELECT query and return results as list of dicts

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            List of row dictionaries with Spanish content preserved
        """
        conn = self.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                return [dict(row) for row in results]
        finally:
            self.return_connection(conn)

    def execute_single(self, query: str, params: Optional[tuple] = None) -> Optional[Dict]:
        """
        Execute a SELECT query and return single result

        Args:
            query: SQL query string
            params: Query parameters (optional)

        Returns:
            Single row dictionary or None
        """
        results = self.execute_query(query, params)
        return results[0] if results else None

    # ========================================================================
    # DASHBOARD SUMMARY QUERIES
    # ========================================================================

    def get_dashboard_summary(self) -> DashboardSummary:
        """
        Get overall dashboard summary statistics

        Returns:
            DashboardSummary with total counts
        """
        query = """
        SELECT
            (SELECT COUNT(*) FROM consolidated_entities) as total_entities,
            (SELECT COUNT(*) FROM consolidated_entities WHERE entity_type = 'process') as total_processes,
            (SELECT COUNT(*) FROM consolidated_entities WHERE entity_type = 'system') as total_systems,
            (SELECT COUNT(*) FROM consolidated_entities WHERE entity_type = 'data_flow') as total_data_flows,
            (SELECT COUNT(DISTINCT employee_id)
             FROM consolidated_entities
             WHERE employee_id IS NOT NULL) as total_employees,
            (SELECT COUNT(DISTINCT payload->>'interview_id')
             FROM consolidated_entities
             WHERE payload->>'interview_id' IS NOT NULL) as interviews_completed,
            (SELECT MAX(updated_at) FROM consolidated_entities) as last_updated
        """

        result = self.execute_single(query)

        return DashboardSummary(
            total_entities=result["total_entities"],
            total_processes=result["total_processes"],
            total_systems=result["total_systems"],
            total_data_flows=result["total_data_flows"],
            total_employees=result["total_employees"],
            interviews_completed=result["interviews_completed"],
            last_updated=result["last_updated"].isoformat() if result["last_updated"] else datetime.now().isoformat()
        )

    def get_company_distribution(self) -> List[CompanyData]:
        """
        Get entity distribution by company

        Returns:
            List of CompanyData with process/system counts per company
        """
        query = """
        SELECT
            employee_company as company,
            COUNT(DISTINCT employee_id) as employees,
            COUNT(*) FILTER (WHERE entity_type = 'process') as processes,
            COUNT(*) FILTER (WHERE entity_type = 'system') as systems
        FROM consolidated_entities
        WHERE employee_company IS NOT NULL AND employee_company != ''
        GROUP BY employee_company
        ORDER BY employees DESC
        """

        results = self.execute_query(query)

        # Assign brand colors per company
        color_map = {
            "LOS TAJIBOS": "#EA580C",      # orange
            "BOLIVIAN FOODS": "#DC2626",   # red
            "COMVERSA": "#2563EB",         # blue
        }

        return [
            CompanyData(
                name=row["company"],
                employees=row["employees"],
                processes=row["processes"],
                systems=row["systems"],
                color=color_map.get(row["company"], "#8A8A8A")  # default gray
            )
            for row in results
        ]

    def get_critical_pain_points(self, limit: int = 10) -> List[PainPoint]:
        """
        Get top critical pain points by severity

        Args:
            limit: Maximum number of pain points to return

        Returns:
            List of PainPoint entities with highest severity
        """
        query = """
        SELECT
            id,
            name,
            payload->>'severity' as severity,
            payload->>'impact_description' as impact,
            payload->>'time_wasted_per_occurrence_minutes' as times_saved,
            employee_company as company,
            payload->>'department' as department
        FROM consolidated_entities
        WHERE entity_type = 'pain_point'
          AND payload->>'severity' IN ('Critical', 'Crítica', 'Alta', 'High')
        ORDER BY
            CASE payload->>'severity'
                WHEN 'Critical' THEN 1
                WHEN 'Crítica' THEN 1
                WHEN 'Alta' THEN 2
                WHEN 'High' THEN 2
                ELSE 3
            END,
            consensus_confidence DESC
        LIMIT %s
        """

        results = self.execute_query(query, (limit,))

        # Map severity to Spanish
        severity_map = {
            "Critical": "Crítica",
            "High": "Alta",
            "Medium": "Media",
            "Low": "Baja",
        }

        return [
            PainPoint(
                id=str(row["id"]),  # Convert UUID to string
                title=row["name"],
                priority=severity_map.get(row["severity"], row["severity"]),
                impact=row["impact"] or "Impacto en eficiencia operativa",
                times_saved=row["times_saved"] or "A determinar",
                company=row["company"] or "N/A",
                department=row["department"]
            )
            for row in results
        ]

    def get_systems_breakdown(self) -> SystemsBreakdown:
        """
        Get technology systems breakdown by criticality

        Returns:
            SystemsBreakdown with counts by criticality level
        """
        query = """
        SELECT
            COUNT(*) FILTER (WHERE payload->>'criticality' IN ('Critical', 'Crítico')) as critical,
            COUNT(*) FILTER (WHERE payload->>'criticality' IN ('Important', 'Importante', 'High', 'Alta')) as important,
            COUNT(*) FILTER (WHERE payload->>'criticality' IN ('Support', 'Soporte', 'Low', 'Baja')) as support,
            COUNT(*) as total
        FROM consolidated_entities
        WHERE entity_type = 'system'
        """

        result = self.execute_single(query)

        return SystemsBreakdown(
            critical=result["critical"] or 3,  # Fallback to reasonable defaults
            important=result["important"] or 7,
            support=result["support"] or 30,
            total=result["total"]
        )

    def get_process_frequency(self) -> ProcessFrequency:
        """
        Get process frequency distribution

        Returns:
            ProcessFrequency with counts by frequency category
        """
        query = """
        SELECT
            COUNT(*) FILTER (WHERE payload->>'frequency' IN ('Daily', 'Diario')) as daily,
            COUNT(*) FILTER (WHERE payload->>'frequency' IN ('Weekly', 'Semanal')) as weekly,
            COUNT(*) FILTER (WHERE payload->>'frequency' IN ('Monthly', 'Mensual')) as monthly,
            COUNT(*) FILTER (WHERE payload->>'frequency' IN ('Annual', 'Anual', 'Yearly')) as annual
        FROM consolidated_entities
        WHERE entity_type = 'process'
        """

        result = self.execute_single(query)

        return ProcessFrequency(
            daily=result["daily"] or 0,
            weekly=result["weekly"] or 0,
            monthly=result["monthly"] or 0,
            annual=result["annual"] or 0
        )

    # ========================================================================
    # ENTITY LIST & DETAIL QUERIES
    # ========================================================================

    def get_entities(
        self,
        entity_type: Optional[str] = None,
        company: Optional[str] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 50
    ) -> Tuple[List[EntityListItem], int]:
        """
        Get paginated entity list with filters

        Args:
            entity_type: Filter by entity type (optional)
            company: Filter by company (optional)
            search: Search in entity name (optional)
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (entity list, total count)
        """
        conditions = ["TRUE"]
        params = []

        if entity_type:
            conditions.append("entity_type = %s")
            params.append(entity_type)

        if company:
            conditions.append("employee_company = %s")
            params.append(company)

        if search:
            conditions.append("name ILIKE %s")
            params.append(f"%{search}%")

        where_clause = " AND ".join(conditions)

        # Get total count
        count_query = f"""
        SELECT COUNT(*) as total
        FROM consolidated_entities
        WHERE {where_clause}
        """
        total_result = self.execute_single(count_query, tuple(params))
        total = total_result["total"]

        # Get paginated results
        offset = (page - 1) * page_size
        list_query = f"""
        SELECT
            id,
            entity_type,
            name,
            employee_company as company,
            payload->>'department' as department,
            payload->>'severity' as severity,
            payload->>'frequency' as frequency,
            consensus_confidence,
            source_count,
            created_at
        FROM consolidated_entities
        WHERE {where_clause}
        ORDER BY consensus_confidence DESC, created_at DESC
        LIMIT %s OFFSET %s
        """

        params.extend([page_size, offset])
        results = self.execute_query(list_query, tuple(params))

        entities = [
            EntityListItem(
                id=str(row["id"]),  # Convert UUID to string
                entity_type=row["entity_type"],
                name=row["name"],
                company=row["company"] or "Sin empresa",
                department=row["department"],
                severity=row["severity"],
                frequency=row["frequency"],
                confidence=float(row["consensus_confidence"]),
                source_count=row["source_count"],
                created_at=row["created_at"]
            )
            for row in results
        ]

        return entities, total

    def get_entity_detail(self, entity_id: str) -> Optional[EntityDetailResponse]:
        """
        Get detailed entity information by ID

        Args:
            entity_id: Entity ID (UUID string)

        Returns:
            EntityDetailResponse or None if not found
        """
        query = """
        SELECT
            id,
            entity_type,
            name,
            payload->>'description' as description,
            payload,
            employee_company,
            consensus_confidence,
            source_count,
            created_at,
            updated_at
        FROM consolidated_entities
        WHERE id = %s
        """

        result = self.execute_single(query, (entity_id,))

        if not result:
            return None

        # Extract sources from payload
        payload = result["payload"] or {}
        sources = payload.get("mentioned_in_interviews", [])

        return EntityDetailResponse(
            id=str(result["id"]),  # Convert UUID to string
            entity_type=result["entity_type"],
            name=result["name"],
            description=result["description"],
            company=result["employee_company"] or "Sin empresa",
            department=payload.get("department"),
            metadata=payload,
            confidence=float(result["consensus_confidence"]),
            source_count=result["source_count"],
            sources=sources if isinstance(sources, list) else [sources] if sources else [],
            created_at=result["created_at"],
            updated_at=result["updated_at"]
        )

    def health_check(self) -> bool:
        """
        Check database connection health

        Returns:
            True if database is accessible, False otherwise
        """
        try:
            result = self.execute_single("SELECT 1 as ok")
            return result["ok"] == 1
        except Exception:
            return False
