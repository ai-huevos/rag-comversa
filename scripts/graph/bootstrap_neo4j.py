#!/usr/bin/env python3
"""
Inicializa Neo4j con los constraints necesarios para RAG 2.0.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from graph.knowledge_graph_builder import KnowledgeGraphBuilder, load_neo4j_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bootstrap de Neo4j para Knowledge Graph Consolidation."
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Ruta alternativa a config/database.toml",
    )
    parser.add_argument(
        "--print-health",
        action="store_true",
        help="Ejecuta un healthcheck después de crear constraints.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path: Optional[Path] = Path(args.config) if args.config else None
    config = load_neo4j_config(config_path)

    builder = KnowledgeGraphBuilder(config)
    try:
        builder.ensure_constraints()
        if args.print_health:
            health = builder.healthcheck()
            print(json.dumps(health, indent=2, ensure_ascii=False))
        else:
            print("✓ Constraints verificados correctamente.")
    finally:
        builder.close()


if __name__ == "__main__":
    main()
