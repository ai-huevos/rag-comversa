"""
Builder de Neo4j para sincronizar entidades consolidadas.
"""
from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from neo4j import GraphDatabase, basic_auth

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class Neo4jConfig:
    """Configuración para conectarse a Neo4j."""

    uri: str
    user: str
    password: str
    database: str = "neo4j"


def load_neo4j_config(config_path: Optional[Path] = None) -> Neo4jConfig:
    """
    Carga la configuración de Neo4j desde config/database.toml.
    """
    config_path = config_path or Path(__file__).resolve().parent.parent / "config" / "database.toml"
    with open(config_path, "rb") as fh:
        data = tomllib.load(fh)

    neo4j_section = data.get("neo4j")
    if not neo4j_section:
        raise ValueError("La sección [neo4j] no existe en config/database.toml")

    password = os.getenv("NEO4J_PASSWORD")
    if not password:
        raise ValueError(
            "NEO4J_PASSWORD no está definido. Exporta la variable antes de ejecutar el builder."
        )

    return Neo4jConfig(
        uri=neo4j_section["uri"],
        user=neo4j_section["user"],
        password=password,
        database=neo4j_section.get("database", "neo4j"),
    )


@dataclass
class GraphEntity:
    """
    Representa una entidad consolidada que será escrita en Neo4j.
    """

    external_id: str
    entity_type: str
    name: str
    org_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> Dict[str, Any]:
        return {
            "external_id": self.external_id,
            "entity_type": self.entity_type,
            "name": self.name,
            "org_id": self.org_id,
            "properties": self.properties,
        }


@dataclass
class GraphRelationship:
    """
    Relación entre entidades consolidadas.
    """

    start_external_id: str
    end_external_id: str
    relationship_type: str
    org_id: str
    properties: Dict[str, Any] = field(default_factory=dict)

    def normalized_type(self) -> str:
        rel_type = self.relationship_type.upper().replace(" ", "_")
        if not re.fullmatch(r"[A-Z_][A-Z0-9_]*", rel_type):
            raise ValueError(f"Tipo de relación no permitido: {self.relationship_type}")
        return rel_type

    def to_payload(self) -> Dict[str, Any]:
        payload = {
            "start_external_id": self.start_external_id,
            "end_external_id": self.end_external_id,
            "relationship_type": self.normalized_type(),
            "org_id": self.org_id,
            "properties": self.properties,
        }
        return payload


class KnowledgeGraphBuilder:
    """
    Encapsula las operaciones de MERGE contra Neo4j.
    """

    def __init__(self, config: Neo4jConfig):
        self._config = config
        self._driver = GraphDatabase.driver(
            config.uri,
            auth=basic_auth(config.user, config.password),
            max_connection_lifetime=3600,
        )

    @classmethod
    def from_config(cls, config_path: Optional[Path] = None) -> "KnowledgeGraphBuilder":
        """Convenience constructor usando database.toml."""
        return cls(load_neo4j_config(config_path))

    def close(self) -> None:
        """Cierra el driver de Neo4j."""
        if self._driver:
            self._driver.close()

    def ensure_constraints(self) -> None:
        """
        Crea constraints básicos para evitar duplicados por org_id/external_id.
        """
        cypher_statements = [
            """
            CREATE CONSTRAINT entity_org_unique IF NOT EXISTS
            FOR (e:Entity)
            REQUIRE (e.org_id, e.external_id) IS UNIQUE
            """,
            """
            CREATE INDEX entity_type_idx IF NOT EXISTS
            FOR (e:Entity)
            ON (e.entity_type, e.org_id)
            """,
        ]

        with self._driver.session(database=self._config.database) as session:
            for statement in cypher_statements:
                session.execute_write(lambda tx, stmt: tx.run(stmt), statement)
                logger.info("Constraint verificado: %s", statement.strip().splitlines()[0])

    def merge_entities(self, entities: Sequence[GraphEntity]) -> int:
        """
        Inserta o actualiza nodos para la organización provista en cada entidad.
        """
        if not entities:
            return 0

        payload = [entity.to_payload() for entity in entities]

        def _merge(tx, nodes: List[Dict[str, Any]]):
            return tx.run(
                """
                UNWIND $nodes AS node
                MERGE (e:Entity {
                    org_id: node.org_id,
                    entity_type: node.entity_type,
                    external_id: node.external_id
                })
                SET e.name = node.name,
                    e.name_normalized = toLower(node.name),
                    e += node.properties,
                    e.updated_at = datetime()
                RETURN COUNT(e) AS merged
                """,
                nodes=nodes,
            ).single()[0]

        with self._driver.session(database=self._config.database) as session:
            merged = session.execute_write(_merge, payload)
            logger.info("Entidades consolidadas en Neo4j: %s", merged)
            return merged

    def merge_relationships(self, relationships: Sequence[GraphRelationship]) -> int:
        """
        Inserta relaciones consolidadas, transfiriendo métricas clave.
        """
        if not relationships:
            return 0

        payload = [rel.to_payload() for rel in relationships]
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for rel in payload:
            grouped.setdefault(rel["relationship_type"], []).append(rel)

        with self._driver.session(database=self._config.database) as session:
            merged = 0
            for rel_type, rel_payload in grouped.items():
                merged += session.execute_write(
                    self._merge_relationships_tx,
                    rel_type,
                    rel_payload,
                )
            logger.info("Relaciones consolidadas en Neo4j: %s", merged)
            return merged

    @staticmethod
    def _merge_relationships_tx(
        tx,
        relationship_type: str,
        relationships: List[Dict[str, Any]],
    ) -> int:
        query = f"""
            UNWIND $relationships AS rel
            MATCH (start:Entity {{
                org_id: rel.org_id,
                external_id: rel.start_external_id
            }})
            MATCH (end:Entity {{
                org_id: rel.org_id,
                external_id: rel.end_external_id
            }})
            MERGE (start)-[r:{relationship_type} {{org_id: rel.org_id}}]->(end)
            SET r += rel.properties,
                r.updated_at = datetime()
            RETURN COUNT(r) AS merged
        """
        return tx.run(query, relationships=relationships).single()[0]

    def healthcheck(self) -> Dict[str, Any]:
        """
        Ejecuta consultas básicas para validar la conectividad.
        """
        with self._driver.session(database=self._config.database) as session:
            summary = session.execute_read(
                lambda tx: tx.run("RETURN 1 AS ok").single()
            )
        return {"neo4j_ok": bool(summary["ok"])}


__all__ = [
    "KnowledgeGraphBuilder",
    "GraphEntity",
    "GraphRelationship",
    "Neo4jConfig",
    "load_neo4j_config",
]
