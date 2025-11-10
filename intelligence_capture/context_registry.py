"""
Context Registry Module for Multi-Organization RAG 2.0
Provides namespace isolation, consent tracking, and access control logging
for Bolivian privacy compliance (Law 164, Constitution Art. 21, Habeas Data)

Task 0: Stand up Context Registry & Org Namespace Controls
"""
import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
import asyncpg
from functools import lru_cache
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OrganizationContext:
    """
    Organization context metadata

    Attributes:
        org_id: Unique organization identifier (e.g., 'los_tajibos')
        org_name: Full organization name
        business_unit: Business unit within organization
        department: Department within business unit (optional)
        industry_context: Industry classification
        priority_tier: Service priority level ('standard', 'premium')
        contact_owner: Contact information as dict
        consent_metadata: Consent and privacy metadata as dict
        active: Whether organization is active
    """
    org_id: str
    org_name: str
    business_unit: str
    department: Optional[str]
    industry_context: str
    priority_tier: str = "standard"
    contact_owner: Optional[Dict[str, Any]] = None
    consent_metadata: Optional[Dict[str, Any]] = None
    active: bool = True

    @property
    def namespace(self) -> str:
        """Generate unique namespace identifier"""
        parts = [self.org_id, self.business_unit]
        if self.department:
            parts.append(self.department)
        return ":".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "org_id": self.org_id,
            "org_name": self.org_name,
            "business_unit": self.business_unit,
            "department": self.department,
            "industry_context": self.industry_context,
            "priority_tier": self.priority_tier,
            "contact_owner": self.contact_owner,
            "consent_metadata": self.consent_metadata,
            "active": self.active,
            "namespace": self.namespace
        }


class ContextRegistry:
    """
    Context Registry Manager

    Provides cached lookups, namespace validation, and audit logging
    for multi-organization RAG system with Bolivian privacy compliance.
    """

    def __init__(self, db_url: Optional[str] = None, cache_ttl: int = 3600):
        """
        Initialize Context Registry

        Args:
            db_url: PostgreSQL connection URL (default: from DATABASE_URL env)
            cache_ttl: Cache time-to-live in seconds (default: 1 hour)
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        if not self.db_url:
            raise ValueError(
                "DATABASE_URL environment variable required for Context Registry"
            )

        self.cache_ttl = cache_ttl
        self._pool: Optional[asyncpg.Pool] = None
        self._cache: Dict[str, Tuple[OrganizationContext, datetime]] = {}
        self._cache_lock = asyncio.Lock()

    async def connect(self):
        """Establish database connection pool"""
        if self._pool is None:
            self._pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10,
                timeout=30.0
            )
            logger.info("✓ Context Registry connected to PostgreSQL")

    async def close(self):
        """Close database connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Context Registry connection closed")

    async def _get_from_cache(self, key: str) -> Optional[OrganizationContext]:
        """
        Get organization context from cache

        Args:
            key: Cache key (namespace or org_id)

        Returns:
            Cached OrganizationContext if found and not expired, else None
        """
        async with self._cache_lock:
            if key in self._cache:
                context, cached_at = self._cache[key]
                if datetime.now() - cached_at < timedelta(seconds=self.cache_ttl):
                    return context
                else:
                    # Expired, remove from cache
                    del self._cache[key]
        return None

    async def _set_cache(self, key: str, context: OrganizationContext):
        """
        Store organization context in cache

        Args:
            key: Cache key (namespace or org_id)
            context: OrganizationContext to cache
        """
        async with self._cache_lock:
            self._cache[key] = (context, datetime.now())

    async def clear_cache(self):
        """Clear all cached organization contexts"""
        async with self._cache_lock:
            self._cache.clear()
            logger.info("Context Registry cache cleared")

    async def lookup_by_org_id(
        self,
        org_id: str,
        business_unit: Optional[str] = None,
        department: Optional[str] = None
    ) -> Optional[OrganizationContext]:
        """
        Lookup organization context by org_id

        Args:
            org_id: Organization identifier
            business_unit: Optional business unit filter
            department: Optional department filter

        Returns:
            OrganizationContext if found, else None
        """
        # Try cache first
        cache_key = f"{org_id}:{business_unit or '*'}:{department or '*'}"
        cached = await self._get_from_cache(cache_key)
        if cached:
            return cached

        # Query database
        await self.connect()
        async with self._pool.acquire() as conn:
            query = """
                SELECT org_id, org_name, business_unit, department, industry_context,
                       priority_tier, contact_owner, consent_metadata, active
                FROM context_registry
                WHERE org_id = $1 AND active = true
            """
            params = [org_id]

            if business_unit:
                query += " AND business_unit = $2"
                params.append(business_unit)
                if department:
                    query += " AND department = $3"
                    params.append(department)

            query += " LIMIT 1"

            row = await conn.fetchrow(query, *params)

            if row:
                context = OrganizationContext(
                    org_id=row['org_id'],
                    org_name=row['org_name'],
                    business_unit=row['business_unit'],
                    department=row['department'],
                    industry_context=row['industry_context'],
                    priority_tier=row['priority_tier'],
                    contact_owner=row['contact_owner'],
                    consent_metadata=row['consent_metadata'],
                    active=row['active']
                )

                # Cache result
                await self._set_cache(cache_key, context)

                return context

        return None

    async def lookup_by_namespace(self, namespace: str) -> Optional[OrganizationContext]:
        """
        Lookup organization context by namespace

        Args:
            namespace: Namespace string (format: 'org_id:business_unit' or 'org_id:business_unit:department')

        Returns:
            OrganizationContext if found, else None
        """
        # Try cache first
        cached = await self._get_from_cache(namespace)
        if cached:
            return cached

        # Parse namespace
        parts = namespace.split(":")
        if len(parts) < 2:
            logger.error(f"Invalid namespace format: {namespace}")
            return None

        org_id = parts[0]
        business_unit = parts[1]
        department = parts[2] if len(parts) > 2 else None

        return await self.lookup_by_org_id(org_id, business_unit, department)

    async def validate_namespace(
        self,
        org_id: str,
        business_unit: str,
        department: Optional[str] = None
    ) -> bool:
        """
        Validate that a namespace exists and is active

        Args:
            org_id: Organization identifier
            business_unit: Business unit
            department: Optional department

        Returns:
            True if namespace is valid and active, else False
        """
        context = await self.lookup_by_org_id(org_id, business_unit, department)
        return context is not None and context.active

    async def validate_consent(
        self,
        org_id: str,
        operation: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate consent metadata for an operation

        Args:
            org_id: Organization identifier
            operation: Operation type ('ingestion', 'retrieval', 'export')

        Returns:
            Tuple of (is_valid, error_message_spanish)
        """
        context = await self.lookup_by_org_id(org_id)

        if not context:
            return False, f"Organización '{org_id}' no encontrada en el registro de contexto"

        if not context.consent_metadata:
            return False, (
                f"Falta metadatos de consentimiento para '{org_id}'. "
                "Por favor, contacte al administrador del sistema."
            )

        consent = context.consent_metadata

        # Check operation-specific consent
        if operation not in consent.get("allowed_operations", []):
            return False, (
                f"Operación '{operation}' no autorizada para '{org_id}'. "
                "Referencia: Ley 164 de Telecomunicaciones y TICs, Art. 21 de la Constitución."
            )

        # Check consent expiration if applicable
        if "expiration_date" in consent:
            expiration = datetime.fromisoformat(consent["expiration_date"])
            if datetime.now() > expiration:
                return False, (
                    f"Consentimiento expirado para '{org_id}' el {consent['expiration_date']}. "
                    "Por favor, renueve el consentimiento antes de continuar."
                )

        return True, None

    async def log_access(
        self,
        org_id: str,
        access_type: str,
        business_context: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
        result_count: Optional[int] = None,
        latency_ms: Optional[int] = None
    ):
        """
        Log access event for audit trail and Bolivian privacy compliance

        Args:
            org_id: Organization identifier
            access_type: Type of access ('query', 'ingestion', 'retrieval', 'checkpoint')
            business_context: Business unit:department context
            user_id: User identifier (optional)
            session_id: Session identifier (optional)
            query_params: Query parameters as dict (optional)
            result_count: Number of results returned (optional)
            latency_ms: Query latency in milliseconds (optional)
        """
        await self.connect()
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO context_access_log
                    (org_id, business_context, access_type, user_id, session_id,
                     query_params, result_count, latency_ms)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                org_id,
                business_context,
                access_type,
                user_id,
                session_id,
                json.dumps(query_params) if query_params else None,
                result_count,
                latency_ms
            )

    async def get_all_organizations(self) -> List[OrganizationContext]:
        """
        Get all active organizations from registry

        Returns:
            List of all active OrganizationContext objects
        """
        await self.connect()
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT org_id, org_name, business_unit, department, industry_context,
                       priority_tier, contact_owner, consent_metadata, active
                FROM context_registry
                WHERE active = true
                ORDER BY org_id, business_unit, department
                """
            )

            return [
                OrganizationContext(
                    org_id=row['org_id'],
                    org_name=row['org_name'],
                    business_unit=row['business_unit'],
                    department=row['department'],
                    industry_context=row['industry_context'],
                    priority_tier=row['priority_tier'],
                    contact_owner=row['contact_owner'],
                    consent_metadata=row['consent_metadata'],
                    active=row['active']
                )
                for row in rows
            ]

    async def register_organization(
        self,
        org_id: str,
        org_name: str,
        business_unit: str,
        department: Optional[str],
        industry_context: str,
        priority_tier: str = "standard",
        contact_owner: Optional[Dict[str, Any]] = None,
        consent_metadata: Optional[Dict[str, Any]] = None
    ) -> OrganizationContext:
        """
        Register a new organization context entry

        Args:
            org_id: Unique organization identifier
            org_name: Full organization name
            business_unit: Business unit name
            department: Department name (optional)
            industry_context: Industry classification
            priority_tier: Priority level ('standard', 'premium')
            contact_owner: Contact information dict
            consent_metadata: Consent and privacy metadata dict

        Returns:
            Created OrganizationContext

        Raises:
            asyncpg.UniqueViolationError: If (org_id, business_unit, department) already exists
        """
        await self.connect()
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO context_registry
                    (org_id, org_name, business_unit, department, industry_context,
                     priority_tier, contact_owner, consent_metadata, active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING org_id, org_name, business_unit, department, industry_context,
                          priority_tier, contact_owner, consent_metadata, active
                """,
                org_id,
                org_name,
                business_unit,
                department,
                industry_context,
                priority_tier,
                json.dumps(contact_owner) if contact_owner else None,
                json.dumps(consent_metadata) if consent_metadata else None,
                True
            )

            context = OrganizationContext(
                org_id=row['org_id'],
                org_name=row['org_name'],
                business_unit=row['business_unit'],
                department=row['department'],
                industry_context=row['industry_context'],
                priority_tier=row['priority_tier'],
                contact_owner=row['contact_owner'],
                consent_metadata=row['consent_metadata'],
                active=row['active']
            )

            # Clear cache to force refresh
            await self.clear_cache()

            logger.info(
                f"✓ Registered organization: {org_id}:{business_unit}"
                + (f":{department}" if department else "")
            )

            return context


# Global registry instance (initialized lazily)
_registry: Optional[ContextRegistry] = None


def get_registry() -> ContextRegistry:
    """
    Get or create global Context Registry instance

    Returns:
        Global ContextRegistry instance
    """
    global _registry
    if _registry is None:
        _registry = ContextRegistry()
    return _registry


async def validate_and_log_access(
    org_id: str,
    access_type: str,
    operation: str = "retrieval",
    **kwargs
) -> Tuple[bool, Optional[str]]:
    """
    Helper function to validate consent and log access in one call

    Args:
        org_id: Organization identifier
        access_type: Access type for logging ('query', 'ingestion', 'retrieval')
        operation: Operation type for consent validation
        **kwargs: Additional parameters for log_access

    Returns:
        Tuple of (is_valid, error_message_spanish)
    """
    registry = get_registry()

    # Validate consent
    is_valid, error_msg = await registry.validate_consent(org_id, operation)

    # Log access regardless of validation result (for audit)
    await registry.log_access(org_id, access_type, **kwargs)

    return is_valid, error_msg
