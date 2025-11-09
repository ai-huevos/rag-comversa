#!/usr/bin/env python3
"""
Generate Consolidation Dashboard Report

Creates an HTML dashboard with consolidation metrics:
- Before/after entity counts per type (bar chart)
- Top 10 most-mentioned entities (table)
- Consensus confidence distribution (histogram)
- Relationship graph (System → Pain Point connections)
- Recurring patterns (sorted by frequency)
- Entities with contradictions (table with details)

Exports as both HTML and JSON formats.
"""
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.config import DB_PATH, REPORTS_DIR


def get_entity_counts(db: EnhancedIntelligenceDB) -> Dict:
    """Get entity counts before and after consolidation"""
    cursor = db.conn.cursor()
    counts = {}
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    for entity_type in entity_types:
        try:
            # Current count
            cursor.execute(f"SELECT COUNT(*) FROM {entity_type}")
            current = cursor.fetchone()[0]
            
            # Original count (sum of source_count)
            cursor.execute(f"SELECT SUM(source_count) FROM {entity_type}")
            original = cursor.fetchone()[0] or current
            
            counts[entity_type] = {
                "before": original,
                "after": current,
                "reduction": original - current,
                "reduction_pct": ((original - current) / original * 100) if original > 0 else 0
            }
        except:
            counts[entity_type] = {"before": 0, "after": 0, "reduction": 0, "reduction_pct": 0}
    
    return counts


def get_top_entities(db: EnhancedIntelligenceDB, limit: int = 10) -> Dict:
    """Get top entities by source_count"""
    cursor = db.conn.cursor()
    top_entities = {}
    
    entity_types = [
        ("pain_points", "type"),
        ("processes", "name"),
        ("systems", "name"),
        ("kpis", "name"),
        ("automation_candidates", "process"),
        ("inefficiencies", "type")
    ]
    
    for entity_type, name_field in entity_types:
        try:
            cursor.execute(f"""
                SELECT {name_field}, source_count, consensus_confidence, mentioned_in_interviews
                FROM {entity_type}
                WHERE source_count > 1
                ORDER BY source_count DESC
                LIMIT ?
            """, (limit,))
            
            entities = []
            for row in cursor.fetchall():
                entities.append({
                    "name": row[0],
                    "source_count": row[1],
                    "consensus_confidence": round(row[2], 3) if row[2] else None,
                    "mentioned_in_interviews": json.loads(row[3]) if row[3] else []
                })
            
            if entities:
                top_entities[entity_type] = entities
        except Exception as e:
            print(f"Warning: Could not query {entity_type}: {e}")
    
    return top_entities


def get_confidence_distribution(db: EnhancedIntelligenceDB) -> Dict:
    """Get consensus confidence distribution"""
    cursor = db.conn.cursor()
    distribution = {
        "0.0-0.2": 0,
        "0.2-0.4": 0,
        "0.4-0.6": 0,
        "0.6-0.8": 0,
        "0.8-1.0": 0
    }
    
    entity_types = [
        "pain_points", "processes", "systems", "kpis",
        "automation_candidates", "inefficiencies"
    ]
    
    for entity_type in entity_types:
        try:
            cursor.execute(f"""
                SELECT consensus_confidence FROM {entity_type}
                WHERE consensus_confidence IS NOT NULL
            """)
            
            for row in cursor.fetchall():
                confidence = row[0]
                if confidence < 0.2:
                    distribution["0.0-0.2"] += 1
                elif confidence < 0.4:
                    distribution["0.2-0.4"] += 1
                elif confidence < 0.6:
                    distribution["0.4-0.6"] += 1
                elif confidence < 0.8:
                    distribution["0.6-0.8"] += 1
                else:
                    distribution["0.8-1.0"] += 1
        except:
            pass
    
    return distribution


def get_relationships(db: EnhancedIntelligenceDB, limit: int = 50) -> List[Dict]:
    """Get relationships for graph visualization"""
    cursor = db.conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                source_entity_type,
                source_entity_id,
                relationship_type,
                target_entity_type,
                target_entity_id,
                strength
            FROM relationships
            ORDER BY strength DESC
            LIMIT ?
        """, (limit,))
        
        relationships = []
        for row in cursor.fetchall():
            # Get entity names
            source_name = get_entity_name(db, row[0], row[1])
            target_name = get_entity_name(db, row[3], row[4])
            
            relationships.append({
                "source": source_name,
                "source_type": row[0],
                "relationship": row[2],
                "target": target_name,
                "target_type": row[3],
                "strength": row[5]
            })
        
        return relationships
    except:
        return []


def get_entity_name(db: EnhancedIntelligenceDB, entity_type: str, entity_id: int) -> str:
    """Get entity name by type and ID"""
    cursor = db.conn.cursor()
    
    name_fields = {
        "pain_points": "type",
        "processes": "name",
        "systems": "name",
        "kpis": "name",
        "automation_candidates": "process",
        "inefficiencies": "type"
    }
    
    name_field = name_fields.get(entity_type, "name")
    
    try:
        cursor.execute(f"SELECT {name_field} FROM {entity_type} WHERE id = ?", (entity_id,))
        result = cursor.fetchone()
        return result[0] if result else f"Unknown ({entity_type} #{entity_id})"
    except:
        return f"Unknown ({entity_type} #{entity_id})"


def get_patterns(db: EnhancedIntelligenceDB) -> List[Dict]:
    """Get recurring patterns"""
    cursor = db.conn.cursor()
    
    try:
        cursor.execute("""
            SELECT 
                pattern_type,
                entity_type,
                entity_id,
                pattern_frequency,
                source_count,
                high_priority,
                description
            FROM patterns
            ORDER BY pattern_frequency DESC, source_count DESC
        """)
        
        patterns = []
        for row in cursor.fetchall():
            patterns.append({
                "type": row[0],
                "entity_type": row[1],
                "entity_id": row[2],
                "frequency": round(row[3], 3),
                "source_count": row[4],
                "high_priority": bool(row[5]),
                "description": row[6]
            })
        
        return patterns
    except:
        return []


def get_contradictions(db: EnhancedIntelligenceDB) -> List[Dict]:
    """Get entities with contradictions"""
    cursor = db.conn.cursor()
    contradictions = []
    
    entity_types = [
        ("pain_points", "type"),
        ("processes", "name"),
        ("systems", "name"),
        ("kpis", "name"),
        ("automation_candidates", "process"),
        ("inefficiencies", "type")
    ]
    
    for entity_type, name_field in entity_types:
        try:
            cursor.execute(f"""
                SELECT {name_field}, contradiction_details
                FROM {entity_type}
                WHERE has_contradictions = 1
            """)
            
            for row in cursor.fetchall():
                details = json.loads(row[1]) if row[1] else []
                contradictions.append({
                    "entity_type": entity_type,
                    "name": row[0],
                    "details": details
                })
        except:
            pass
    
    return contradictions


def generate_html_report(
    db_path: Path,
    entity_counts: Dict,
    top_entities: Dict,
    confidence_dist: Dict,
    relationships: List[Dict],
    patterns: List[Dict],
    contradictions: List[Dict],
    output_path: Path
):
    """Generate HTML dashboard"""
    
    # Calculate totals
    total_before = sum(c["before"] for c in entity_counts.values())
    total_after = sum(c["after"] for c in entity_counts.values())
    total_reduction = total_before - total_after
    total_reduction_pct = (total_reduction / total_before * 100) if total_before > 0 else 0
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Knowledge Graph Consolidation Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #f5f7fa;
            color: #2c3e50;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            opacity: 0.9;
            font-size: 1.1em;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 10px;
        }}
        
        .stat-value {{
            font-size: 2.5em;
            font-weight: bold;
            color: #2c3e50;
        }}
        
        .stat-change {{
            margin-top: 10px;
            font-size: 0.9em;
        }}
        
        .positive {{
            color: #27ae60;
        }}
        
        .negative {{
            color: #e74c3c;
        }}
        
        .section {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #ecf0f1;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #2c3e50;
            border-bottom: 2px solid #dee2e6;
        }}
        
        td {{
            padding: 12px;
            border-bottom: 1px solid #ecf0f1;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-high {{
            background: #fee;
            color: #c00;
        }}
        
        .badge-medium {{
            background: #ffeaa7;
            color: #d63031;
        }}
        
        .badge-low {{
            background: #dfe6e9;
            color: #636e72;
        }}
        
        .chart {{
            margin: 20px 0;
        }}
        
        .bar {{
            display: flex;
            align-items: center;
            margin: 10px 0;
        }}
        
        .bar-label {{
            width: 200px;
            font-weight: 500;
        }}
        
        .bar-visual {{
            flex: 1;
            height: 30px;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 5px;
            position: relative;
        }}
        
        .bar-value {{
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            color: white;
            font-weight: bold;
        }}
        
        .relationship {{
            display: flex;
            align-items: center;
            padding: 10px;
            margin: 5px 0;
            background: #f8f9fa;
            border-radius: 5px;
        }}
        
        .rel-source {{
            flex: 1;
            font-weight: 500;
        }}
        
        .rel-arrow {{
            padding: 0 15px;
            color: #7f8c8d;
        }}
        
        .rel-target {{
            flex: 1;
            text-align: right;
        }}
        
        .no-data {{
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-style: italic;
        }}
        
        footer {{
            text-align: center;
            padding: 20px;
            color: #7f8c8d;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Knowledge Graph Consolidation Dashboard</h1>
            <div class="subtitle">
                Database: {db_path.name} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Entities Before</div>
                <div class="stat-value">{total_before:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Entities After</div>
                <div class="stat-value">{total_after:,}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Duplicates Merged</div>
                <div class="stat-value positive">{total_reduction:,}</div>
                <div class="stat-change positive">↓ {total_reduction_pct:.1f}% reduction</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Relationships</div>
                <div class="stat-value">{len(relationships):,}</div>
            </div>
        </div>
        
        <div class="section">
            <h2>Entity Counts: Before vs After</h2>
            <div class="chart">
"""
    
    # Add bar chart for entity counts
    max_count = max((c["before"] for c in entity_counts.values()), default=1)
    for entity_type, counts in entity_counts.items():
        if counts["before"] > 0:
            width_before = (counts["before"] / max_count * 100)
            width_after = (counts["after"] / max_count * 100)
            html += f"""
                <div class="bar">
                    <div class="bar-label">{entity_type.replace('_', ' ').title()}</div>
                    <div style="flex: 1;">
                        <div style="background: #dfe6e9; height: 15px; border-radius: 3px; margin: 2px 0;">
                            <div style="background: #b2bec3; width: {width_before}%; height: 100%; border-radius: 3px;"></div>
                        </div>
                        <div style="background: #dfe6e9; height: 15px; border-radius: 3px; margin: 2px 0;">
                            <div style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); width: {width_after}%; height: 100%; border-radius: 3px;"></div>
                        </div>
                    </div>
                    <div style="width: 150px; text-align: right; font-size: 0.9em;">
                        <div style="color: #7f8c8d;">{counts["before"]} → {counts["after"]}</div>
                        <div style="color: #27ae60; font-weight: 600;">-{counts["reduction_pct"]:.1f}%</div>
                    </div>
                </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Top 10 Most-Mentioned Entities</h2>
"""
    
    if top_entities:
        for entity_type, entities in top_entities.items():
            html += f"""
            <h3 style="margin-top: 20px; color: #7f8c8d;">{entity_type.replace('_', ' ').title()}</h3>
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Sources</th>
                        <th>Confidence</th>
                        <th>Interviews</th>
                    </tr>
                </thead>
                <tbody>
"""
            for entity in entities[:10]:
                interviews_str = ', '.join(str(i) for i in entity['mentioned_in_interviews'][:5])
                if len(entity['mentioned_in_interviews']) > 5:
                    interviews_str += f" +{len(entity['mentioned_in_interviews']) - 5} more"
                
                html += f"""
                    <tr>
                        <td><strong>{entity['name']}</strong></td>
                        <td>{entity['source_count']}</td>
                        <td>{entity['consensus_confidence']}</td>
                        <td style="font-size: 0.85em; color: #7f8c8d;">{interviews_str}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
"""
    else:
        html += '<div class="no-data">No multi-source entities found</div>'
    
    html += """
        </div>
        
        <div class="section">
            <h2>Consensus Confidence Distribution</h2>
            <div class="chart">
"""
    
    # Add confidence distribution bars
    max_dist = max(confidence_dist.values(), default=1)
    for range_label, count in confidence_dist.items():
        width = (count / max_dist * 100) if max_dist > 0 else 0
        html += f"""
            <div class="bar">
                <div class="bar-label">{range_label}</div>
                <div class="bar-visual" style="width: {width}%;">
                    <div class="bar-value">{count}</div>
                </div>
            </div>
"""
    
    html += """
            </div>
        </div>
        
        <div class="section">
            <h2>Relationship Graph (Top 20)</h2>
"""
    
    if relationships:
        for rel in relationships[:20]:
            html += f"""
            <div class="relationship">
                <div class="rel-source">
                    <strong>{rel['source']}</strong>
                    <div style="font-size: 0.8em; color: #7f8c8d;">{rel['source_type']}</div>
                </div>
                <div class="rel-arrow">
                    → <em>{rel['relationship']}</em> →
                </div>
                <div class="rel-target">
                    <strong>{rel['target']}</strong>
                    <div style="font-size: 0.8em; color: #7f8c8d;">{rel['target_type']}</div>
                </div>
            </div>
"""
    else:
        html += '<div class="no-data">No relationships discovered yet</div>'
    
    html += """
        </div>
        
        <div class="section">
            <h2>Recurring Patterns</h2>
"""
    
    if patterns:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Type</th>
                        <th>Description</th>
                        <th>Frequency</th>
                        <th>Sources</th>
                        <th>Priority</th>
                    </tr>
                </thead>
                <tbody>
"""
        for pattern in patterns:
            priority_badge = 'badge-high' if pattern['high_priority'] else 'badge-low'
            priority_text = 'HIGH' if pattern['high_priority'] else 'Normal'
            html += f"""
                <tr>
                    <td>{pattern['type'].replace('_', ' ').title()}</td>
                    <td>{pattern['description']}</td>
                    <td>{pattern['frequency'] * 100:.1f}%</td>
                    <td>{pattern['source_count']}</td>
                    <td><span class="badge {priority_badge}">{priority_text}</span></td>
                </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<div class="no-data">No patterns identified yet</div>'
    
    html += """
        </div>
        
        <div class="section">
            <h2>Entities with Contradictions</h2>
"""
    
    if contradictions:
        html += """
            <table>
                <thead>
                    <tr>
                        <th>Entity Type</th>
                        <th>Name</th>
                        <th>Contradictions</th>
                    </tr>
                </thead>
                <tbody>
"""
        for contradiction in contradictions:
            details_str = '<br>'.join(str(d) for d in contradiction['details'][:3])
            html += f"""
                <tr>
                    <td>{contradiction['entity_type'].replace('_', ' ').title()}</td>
                    <td><strong>{contradiction['name']}</strong></td>
                    <td style="font-size: 0.85em;">{details_str}</td>
                </tr>
"""
        html += """
                </tbody>
            </table>
"""
    else:
        html += '<div class="no-data">✓ No contradictions found</div>'
    
    html += """
        </div>
        
        <footer>
            Generated by Knowledge Graph Consolidation System
        </footer>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✓ HTML dashboard saved to: {output_path}")


def generate_json_report(
    db_path: Path,
    entity_counts: Dict,
    top_entities: Dict,
    confidence_dist: Dict,
    relationships: List[Dict],
    patterns: List[Dict],
    contradictions: List[Dict],
    output_path: Path
):
    """Generate JSON report"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "database": str(db_path),
        "entity_counts": entity_counts,
        "top_entities": top_entities,
        "confidence_distribution": confidence_dist,
        "relationships": relationships,
        "patterns": patterns,
        "contradictions": contradictions,
        "summary": {
            "total_before": sum(c["before"] for c in entity_counts.values()),
            "total_after": sum(c["after"] for c in entity_counts.values()),
            "total_reduction": sum(c["reduction"] for c in entity_counts.values()),
            "total_relationships": len(relationships),
            "total_patterns": len(patterns),
            "high_priority_patterns": sum(1 for p in patterns if p['high_priority']),
            "total_contradictions": len(contradictions)
        }
    }
    
    # Write JSON file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"✓ JSON report saved to: {output_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Generate Knowledge Graph consolidation dashboard"
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help=f"Path to database file (default: {DB_PATH})"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPORTS_DIR,
        help=f"Output directory (default: {REPORTS_DIR})"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("KNOWLEDGE GRAPH CONSOLIDATION DASHBOARD")
    print("=" * 70)
    print(f"Database: {args.db_path}")
    print(f"Output: {args.output_dir}")
    print()
    
    # Check if database exists
    if not args.db_path.exists():
        print(f"✗ Database not found: {args.db_path}")
        sys.exit(1)
    
    # Connect to database
    print("📂 Connecting to database...")
    db = EnhancedIntelligenceDB(args.db_path)
    db.connect()
    print("✓ Connected")
    
    # Collect data
    print("\n📊 Collecting consolidation metrics...")
    entity_counts = get_entity_counts(db)
    top_entities = get_top_entities(db)
    confidence_dist = get_confidence_distribution(db)
    relationships = get_relationships(db)
    patterns = get_patterns(db)
    contradictions = get_contradictions(db)
    print("✓ Data collected")
    
    # Generate reports
    print("\n📝 Generating reports...")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = args.output_dir / f"consolidation_dashboard_{timestamp}.html"
    json_path = args.output_dir / f"consolidation_dashboard_{timestamp}.json"
    
    generate_html_report(
        args.db_path,
        entity_counts,
        top_entities,
        confidence_dist,
        relationships,
        patterns,
        contradictions,
        html_path
    )
    
    generate_json_report(
        args.db_path,
        entity_counts,
        top_entities,
        confidence_dist,
        relationships,
        patterns,
        contradictions,
        json_path
    )
    
    # Close database
    db.close()
    
    print("\n" + "=" * 70)
    print("✓ Dashboard generation complete!")
    print("=" * 70)
    print(f"\nOpen the HTML dashboard in your browser:")
    print(f"  file://{html_path.absolute()}")
    print()


if __name__ == "__main__":
    main()
