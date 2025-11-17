"""Visualization defaults for the Neo4j knowledge graph.

This module centralizes the color palette, layering, and stylistic
information required by the consolidation and sync pipelines so every
entity carries the right metadata for downstream visualization.
"""

from __future__ import annotations

from typing import Any, Dict


# Layer + color configuration -------------------------------------------------
ENTITY_LAYERS: Dict[str, Dict[str, Any]] = {
    # Layer 1-6: Organizational structure (blue spectrum)
    "holding": {"layer": 1, "color": "#1E3A8A", "label": "OrganizationalLayer", "size": 1.5},
    "company": {"layer": 2, "color": "#2563EB", "label": "OrganizationalLayer", "size": 1.4},
    "business_unit": {"layer": 3, "color": "#3B82F6", "label": "OrganizationalLayer", "size": 1.3},
    "area": {"layer": 4, "color": "#60A5FA", "label": "OrganizationalLayer", "size": 1.2},
    "team_structure": {"layer": 5, "color": "#93C5FD", "label": "OrganizationalLayer", "size": 1.2},
    "role": {"layer": 6, "color": "#DBEAFE", "label": "OrganizationalLayer", "size": 1.0},

    # Layer 7-8: Strategy & goals (purple spectrum)
    "objective": {"layer": 7, "color": "#6B21A8", "label": "StrategyLayer", "size": 1.3},
    "kpi": {"layer": 8, "color": "#9333EA", "label": "MeasurementLayer", "size": 1.2},

    # Layer 9-12: Operations (green spectrum)
    "process": {"layer": 9, "color": "#15803D", "label": "OperationalLayer", "size": 1.4},
    "temporal_pattern": {"layer": 10, "color": "#16A34A", "label": "OperationalLayer", "size": 1.1},
    "data_flow": {"layer": 11, "color": "#22C55E", "label": "OperationalLayer", "size": 1.1},
    "decision_point": {"layer": 12, "color": "#4ADE80", "label": "OperationalLayer", "size": 1.1},

    # Layer 13-16: Resources & constraints (orange spectrum)
    "budget_constraint": {"layer": 13, "color": "#C2410C", "label": "ResourceLayer", "size": 1.1},
    "system": {"layer": 14, "color": "#EA580C", "label": "ResourceLayer", "size": 1.3},
    "communication_channel": {"layer": 15, "color": "#F97316", "label": "ResourceLayer", "size": 1.0},
    "external_dependency": {"layer": 16, "color": "#FB923C", "label": "ResourceLayer", "size": 1.0},

    # Layer 18-20: Issues & problems (red/yellow spectrum)
    "pain_point": {"layer": 18, "color": "#DC2626", "label": "IssueLayer", "size": 1.3},
    "failure_mode": {"layer": 19, "color": "#EF4444", "label": "IssueLayer", "size": 1.1},
    "inefficiency": {"layer": 20, "color": "#FBBF24", "label": "IssueLayer", "size": 1.1},

    # Layer 21-22: Solutions & automation (teal spectrum)
    "success_pattern": {"layer": 21, "color": "#0D9488", "label": "SolutionLayer", "size": 1.2},
    "automation_candidate": {"layer": 22, "color": "#14B8A6", "label": "SolutionLayer", "size": 1.3},
}


RELATIONSHIP_STYLES: Dict[str, Dict[str, Any]] = {
    # Hierarchy
    "CONTAINS": {"color": "#64748B", "width": 2, "style": "solid"},
    "BELONGS_TO": {"color": "#64748B", "width": 2, "style": "solid"},
    "HAS_MEMBER": {"color": "#64748B", "width": 1.5, "style": "solid"},

    # Operational
    "OWNS": {"color": "#059669", "width": 1.5, "style": "solid"},
    "EXECUTES": {"color": "#059669", "width": 1.5, "style": "solid"},
    "USES": {"color": "#059669", "width": 1.5, "style": "solid"},
    "HAS_PATTERN": {"color": "#059669", "width": 1, "style": "solid"},
    "HAS_FLOW": {"color": "#059669", "width": 1, "style": "solid"},
    "HAS_DECISION": {"color": "#059669", "width": 1, "style": "solid"},

    # Measurement
    "MEASURED_BY": {"color": "#7C3AED", "width": 1, "style": "dashed"},
    "TRACKS": {"color": "#7C3AED", "width": 1, "style": "dashed"},
    "HAS_OBJECTIVE": {"color": "#7C3AED", "width": 1.5, "style": "dashed"},

    # Issues
    "CAUSES": {"color": "#DC2626", "width": 1.5, "style": "dotted"},
    "HAS_PAIN": {"color": "#DC2626", "width": 1.5, "style": "dotted"},
    "EXPERIENCES": {"color": "#DC2626", "width": 1.5, "style": "dotted"},
    "HAS_FAILURE": {"color": "#DC2626", "width": 1, "style": "dotted"},
    "HAS_INEFFICIENCY": {"color": "#DC2626", "width": 1, "style": "dotted"},

    # Solutions
    "SOLVES": {"color": "#14B8A6", "width": 2, "style": "solid"},
    "IMPROVES": {"color": "#14B8A6", "width": 2, "style": "solid"},
    "AUTOMATES": {"color": "#14B8A6", "width": 2, "style": "solid"},
    "PREVENTS": {"color": "#14B8A6", "width": 1.5, "style": "solid"},
    "HAS_SUCCESS": {"color": "#14B8A6", "width": 1.5, "style": "solid"},

    # Communication / dependencies
    "COMMUNICATES_VIA": {"color": "#F59E0B", "width": 1, "style": "dashed"},
    "COORDINATES_WITH": {"color": "#F59E0B", "width": 1, "style": "dashed"},
    "DEPENDS_ON": {"color": "#6366F1", "width": 1, "style": "dashed"},
    "DEPENDS_ON_EXTERNAL": {"color": "#6366F1", "width": 1, "style": "dotted"},
}


def get_visualization_properties(entity_type: str) -> Dict[str, Any]:
    """Return the visualization defaults for a given entity type."""

    return ENTITY_LAYERS.get(
        entity_type,
        {"layer": 0, "color": "#9CA3AF", "label": "Entity", "size": 1.0},
    )


def add_visualization_properties(entity: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure an entity dict carries layer/color metadata used by Neo4j."""

    if entity is None:
        return entity

    entity_type = entity.get("entity_type")
    viz = get_visualization_properties(entity_type)

    entity.setdefault("layer", viz["layer"])
    entity.setdefault("color", viz["color"])
    entity.setdefault("viz_label", viz["label"])
    entity.setdefault("viz_size", viz["size"])

    return entity


def get_relationship_style(relationship_type: str) -> Dict[str, Any]:
    """Look up styling defaults for the requested relationship type."""

    return RELATIONSHIP_STYLES.get(
        relationship_type.upper(),
        {"color": "#94A3B8", "width": 1, "style": "solid"},
    )


__all__ = [
    "ENTITY_LAYERS",
    "RELATIONSHIP_STYLES",
    "add_visualization_properties",
    "get_visualization_properties",
    "get_relationship_style",
]
