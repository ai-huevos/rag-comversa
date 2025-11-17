#!/usr/bin/env python3
"""
Infer Neo4j entity-to-entity relationships from consolidated entity metadata.

This reads PostgreSQL `consolidated_entities` rows, inspects well-known
properties (e.g., process, systems_involved), and creates Neo4j relationships
using the existing KnowledgeGraphBuilder.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set

sys.path.insert(0, str((os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))))

import psycopg2
from psycopg2.extras import RealDictCursor

from graph import GraphRelationship, KnowledgeGraphBuilder

# Map source entity_type → list of property-based inference rules
RELATIONSHIP_RULES: Dict[str, Sequence[Dict[str, Any]]] = {
    "automation_candidate": [
        {
            "properties": (
                "process",
                "process_name",
                "processes",
                "related_process",
                "target_process",
                "affected_process",
                "affected_processes",
            ),
            "relationship_type": "IMPROVES",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems_involved", "systems", "related_systems", "systems_needed"),
            "relationship_type": "INVOLVES",
            "target_entity_type": "system",
        },
        {
            "properties": ("monitoring_metrics", "kpis_impacted", "kpi", "kpis"),
            "relationship_type": "MOVES",
            "target_entity_type": "kpi",
        },
        {
            "properties": ("pain_point", "pain_points", "pain_point_reference"),
            "relationship_type": "RESOLVES",
            "target_entity_type": "pain_point",
        },
    ],
    "pain_point": [
        {
            "properties": (
                "process",
                "processes",
                "affected_process",
                "affected_processes",
                "related_process",
            ),
            "relationship_type": "AFFECTS",
            "target_entity_type": "process",
        },
        {
            "properties": (
                "systems_involved",
                "systems",
                "related_systems",
                "root_cause",
                "root_cause_system",
            ),
            "relationship_type": "CAUSED_BY",
            "target_entity_type": "system",
        },
        {
            "properties": ("automation_candidates", "solutions", "proposed_solutions"),
            "relationship_type": "ADDRESSED_BY",
            "target_entity_type": "automation_candidate",
        },
    ],
    "inefficiency": [
        {
            "properties": ("process", "processes", "related_process", "impacted_process"),
            "relationship_type": "AFFECTS",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems", "systems_involved", "related_systems"),
            "relationship_type": "CAUSED_BY",
            "target_entity_type": "system",
        },
    ],
    "process": [
        {
            "properties": ("systems", "systems_involved", "related_systems"),
            "relationship_type": "USES",
            "target_entity_type": "system",
        },
        {
            "properties": ("dependencies", "inputs"),
            "relationship_type": "DEPENDS_ON",
            "target_entity_type": "process",
        },
    ],
    "system": [
        {
            "properties": ("integrations", "integrates_with", "related_systems"),
            "relationship_type": "INTEGRATES_WITH",
            "target_entity_type": "system",
        }
    ],
    "data_flow": [
        {
            "properties": (
                "source_system",
                "source_systems",
                "upstream_system",
                "origin_systems",
            ),
            "relationship_type": "FLOWS_FROM",
            "target_entity_type": "system",
        },
        {
            "properties": (
                "destination_system",
                "destination_systems",
                "downstream_system",
                "target_systems",
            ),
            "relationship_type": "FLOWS_TO",
            "target_entity_type": "system",
        },
    ],
    "temporal_pattern": [
        {
            "properties": (
                "process",
                "processes",
                "related_process",
                "applies_to_process",
            ),
            "relationship_type": "FOLLOWS",
            "target_entity_type": "process",
        }
    ],
    "decision_point": [
        {
            "properties": ("process", "processes", "related_process", "gate_process"),
            "relationship_type": "GATES",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems_involved", "systems", "tools"),
            "relationship_type": "EVALUATES_WITH",
            "target_entity_type": "system",
        },
    ],
    "communication_channel": [
        {
            "properties": ("processes", "used_in_processes", "supports_process"),
            "relationship_type": "SUPPORTS",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems_involved", "systems", "platform", "tools"),
            "relationship_type": "ENABLES",
            "target_entity_type": "system",
        },
    ],
    "kpi": [
        {
            "properties": ("process", "processes", "related_process", "monitored_process"),
            "relationship_type": "MEASURES",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems", "systems_involved", "data_sources_needed"),
            "relationship_type": "TRACKED_IN",
            "target_entity_type": "system",
        },
    ],
    "failure_mode": [
        {
            "properties": ("process", "processes", "related_process"),
            "relationship_type": "BREAKS",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems", "systems_involved", "failure_points"),
            "relationship_type": "OCCURS_IN",
            "target_entity_type": "system",
        },
    ],
    "success_pattern": [
        {
            "properties": ("process", "processes", "related_process"),
            "relationship_type": "ENHANCES",
            "target_entity_type": "process",
        },
        {
            "properties": ("systems", "systems_involved", "tools"),
            "relationship_type": "LEVERAGES",
            "target_entity_type": "system",
        },
    ],
}


@dataclass
class EntityRecord:
    sqlite_id: int
    entity_type: str
    name: str
    org_id: str
    payload: Dict[str, Any]

    @property
    def external_id(self) -> str:
        return f"sqlite_{self.entity_type}_{self.sqlite_id}"


def normalize_text(value: str) -> str:
    """Normalize labels for reliable lookups."""
    if value is None:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return text


def extract_terms(raw: Any) -> List[str]:
    """Convert property values into a list of candidate names."""
    if raw is None:
        return []
    if isinstance(raw, (list, tuple, set)):
        terms: List[str] = []
        for item in raw:
            terms.extend(extract_terms(item))
        return terms
    if isinstance(raw, dict):
        for key in ("name", "label", "value", "title"):
            if key in raw and raw[key]:
                return [str(raw[key])]
        return []
    if isinstance(raw, (int, float)):
        return [str(raw)]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        if text.startswith("[") or text.startswith("{"):
            try:
                loaded = json.loads(text)
            except json.JSONDecodeError:
                pass
            else:
                return extract_terms(loaded)
        if any(sep in text for sep in (",", ";", "|")):
            parts = re.split(r"[;,|]", text)
            return [part.strip() for part in parts if part.strip()]
        return [text]
    return []


def load_entities(pg_url: str) -> List[EntityRecord]:
    """Fetch consolidated entity rows from PostgreSQL."""
    conn = psycopg2.connect(pg_url)
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(
            """
            SELECT
                sqlite_entity_id,
                entity_type,
                name,
                COALESCE(org_id, 'unknown') AS org_id,
                payload
            FROM consolidated_entities
            """
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    records: List[EntityRecord] = []
    for row in rows:
        payload = row["payload"]
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        payload = payload or {}
        records.append(
            EntityRecord(
                sqlite_id=row["sqlite_entity_id"],
                entity_type=row["entity_type"],
                name=row["name"] or "",
                org_id=row["org_id"],
                payload=payload,
            )
        )
    return records


def build_lookup(records: Iterable[EntityRecord]) -> Dict[Tuple[str, str], Dict[str, List[EntityRecord]]]:
    """Index entities by (org_id, entity_type) → normalized name → records."""
    lookup: Dict[Tuple[str, str], Dict[str, List[EntityRecord]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        key = (record.org_id or "unknown", record.entity_type)
        normalized = normalize_text(record.name)
        if normalized:
            lookup[key][normalized].append(record)
    return lookup


def pick_property(payload: Dict[str, Any], candidate_names: Sequence[str]) -> Tuple[Optional[str], Optional[Any]]:
    """Return (property_name, value) for the first matching candidate."""
    for name in candidate_names:
        if name in payload and payload[name] not in (None, "", []):
            return name, payload[name]
    return None, None


def find_matching_entity(
    lookup: Dict[Tuple[str, str], Dict[str, List[EntityRecord]]],
    org_id: str,
    entity_type: str,
    term: str,
) -> Optional[EntityRecord]:
    normalized = normalize_text(term)
    if not normalized:
        return None
    org_key = org_id or "unknown"
    candidates = lookup.get((org_key, entity_type), {}).get(normalized)
    if candidates:
        return candidates[0]
    return None


def infer_relationships(
    records: Sequence[EntityRecord],
    lookup: Dict[Tuple[str, str], Dict[str, List[EntityRecord]]],
    limit: Optional[int] = None,
) -> Tuple[List[GraphRelationship], Dict[str, Counter]]:
    """Infer GraphRelationship objects and aggregate stats."""
    relationships: List[GraphRelationship] = []
    seen: Set[Tuple[str, str, str]] = set()
    stats = {
        "relationships_by_type": Counter(),
        "missing_targets": Counter(),
    }

    for record in records:
        rules = RELATIONSHIP_RULES.get(record.entity_type)
        if not rules:
            continue

        for rule in rules:
            property_name, value = pick_property(record.payload, rule["properties"])
            if value is None:
                continue
            terms = extract_terms(value)
            for term in terms:
                target = find_matching_entity(
                    lookup, record.org_id, rule["target_entity_type"], term
                )
                if not target:
                    stats["missing_targets"][(record.entity_type, rule["target_entity_type"], rule["relationship_type"])] += 1
                    continue
                rel_key = (record.external_id, target.external_id, rule["relationship_type"])
                if rel_key in seen or record.external_id == target.external_id:
                    continue
                seen.add(rel_key)
                relationships.append(
                    GraphRelationship(
                        start_external_id=record.external_id,
                        end_external_id=target.external_id,
                        relationship_type=rule["relationship_type"],
                        org_id=record.org_id,
                        properties={
                            "source_property": property_name or rule["properties"][0],
                            "source_value": term,
                        },
                    )
                )
                stats["relationships_by_type"][rule["relationship_type"]] += 1
                if limit and len(relationships) >= limit:
                    return relationships, stats
    return relationships, stats


def print_summary(records: Sequence[EntityRecord], relationships: Sequence[GraphRelationship], stats: Dict[str, Counter]) -> None:
    print("=" * 72)
    print("ENTITY RELATIONSHIP INFERENCE")
    print("=" * 72)
    print(f"Entities scanned : {len(records):>5}")
    print(f"Relationships    : {len(relationships):>5}")
    if relationships:
        print("\nBreakdown by relationship type:")
        for rel_type, count in stats["relationships_by_type"].most_common():
            print(f"  {rel_type:<16} {count}")

    missing = stats["missing_targets"]
    if missing:
        print("\nMissing target matches (top 5 combos):")
        for combo, count in missing.most_common(5):
            src_type, tgt_type, rel_type = combo
            print(f"  {src_type} → {rel_type} → {tgt_type}: {count} unmatched values")

    if relationships:
        sample = relationships[:5]
        print("\nSample relationships:")
        for rel in sample:
            print(
                f"  {rel.start_external_id} -[{rel.relationship_type}]-> {rel.end_external_id} "
                f"(org={rel.org_id})"
            )
    print()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Infer entity relationships from consolidated metadata.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute relationships but skip writing to Neo4j.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of relationships to infer (for smoke tests).",
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="Override DATABASE_URL when fetching consolidated_entities.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress console output (useful when imported by other scripts).",
    )
    return parser.parse_args()


def run_inference(
    *,
    pg_url: Optional[str] = None,
    dry_run: bool = False,
    limit: Optional[int] = None,
    builder: Optional[KnowledgeGraphBuilder] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Public entry point so other scripts can reuse the inference logic."""
    resolved_pg_url = pg_url or os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/comversa_rag",
    )
    records = load_entities(resolved_pg_url)
    if not records:
        if verbose:
            print("⊘ No consolidated entities found in PostgreSQL. Run the backfill first.")
        return {"records": 0, "relationships": 0, "merged": 0, "stats": {}}

    lookup = build_lookup(records)
    relationships, stats = infer_relationships(records, lookup, limit=limit)
    if verbose:
        print_summary(records, relationships, stats)

    summary: Dict[str, Any] = {
        "records": len(records),
        "relationships": len(relationships),
        "merged": 0,
        "stats": stats,
    }

    if not relationships:
        if verbose:
            print("No relationships inferred. Review the missing targets summary above.")
        return summary

    if dry_run:
        if verbose:
            print("Dry run enabled; skipping Neo4j merge.")
        return summary

    internal_builder = builder or KnowledgeGraphBuilder.from_config()
    try:
        merged = internal_builder.merge_relationships(relationships)
    finally:
        if builder is None:
            internal_builder.close()

    summary["merged"] = merged
    if verbose:
        print(f"✅ Neo4j merge complete → {merged} relationships created/updated.")
    return summary


def main() -> None:
    args = parse_args()
    run_inference(
        pg_url=args.database_url,
        dry_run=args.dry_run,
        limit=args.limit,
        builder=None,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
