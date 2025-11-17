# Graph Visualization Implementation Guide

**Date**: 2025-11-16
**Purpose**: Implement clear visual hierarchy and relationship schema for Neo4j
**Reference**: ENTITY_HIERARCHY_AND_RELATIONSHIP_SCHEMA.md

---

## 🎯 Problem

Current Neo4j graph visualization (see screenshot):
- ❌ All nodes same color (pink/purple)
- ❌ No clear hierarchy
- ❌ Relationships hard to distinguish
- ❌ Cluttered layout
- ❌ No layer-based organization

---

## ✅ Solution

Implement 6-layer hierarchical schema with:
- ✅ Color-coded entities by layer
- ✅ Clear relationship types and visual styles
- ✅ Proper node labels for filtering
- ✅ Visualization properties in graph

---

## 📋 Implementation Steps

### Step 1: Add Visualization Config

Create layer and color mapping configuration:

**File**: `intelligence_capture/visualization_config.py`

```python
"""
Visualization configuration for Neo4j knowledge graph
Defines entity layers, colors, and relationship styling
"""

ENTITY_LAYERS = {
    # Layer 1-6: Organizational Structure (Blue spectrum)
    'holding': {
        'layer': 1,
        'color': '#1E3A8A',  # Dark Blue
        'label': 'OrganizationalLayer',
        'size': 1.5
    },
    'company': {
        'layer': 2,
        'color': '#2563EB',  # Blue
        'label': 'OrganizationalLayer',
        'size': 1.4
    },
    'business_unit': {
        'layer': 3,
        'color': '#3B82F6',  # Light Blue
        'label': 'OrganizationalLayer',
        'size': 1.3
    },
    'area': {
        'layer': 4,
        'color': '#60A5FA',  # Sky Blue
        'label': 'OrganizationalLayer',
        'size': 1.2
    },
    'team_structure': {
        'layer': 5,
        'color': '#93C5FD',  # Pale Blue
        'label': 'OrganizationalLayer',
        'size': 1.2
    },
    'role': {
        'layer': 6,
        'color': '#DBEAFE',  # Very Light Blue
        'label': 'OrganizationalLayer',
        'size': 1.0
    },

    # Layer 7-8: Strategy & Goals (Purple spectrum)
    'objective': {
        'layer': 7,
        'color': '#6B21A8',  # Dark Purple
        'label': 'StrategyLayer',
        'size': 1.3
    },
    'kpi': {
        'layer': 8,
        'color': '#9333EA',  # Purple
        'label': 'MeasurementLayer',
        'size': 1.2
    },

    # Layer 9-12: Operations (Green spectrum)
    'process': {
        'layer': 9,
        'color': '#15803D',  # Dark Green
        'label': 'OperationalLayer',
        'size': 1.4
    },
    'temporal_pattern': {
        'layer': 10,
        'color': '#16A34A',  # Green
        'label': 'OperationalLayer',
        'size': 1.1
    },
    'data_flow': {
        'layer': 11,
        'color': '#22C55E',  # Light Green
        'label': 'OperationalLayer',
        'size': 1.1
    },
    'decision_point': {
        'layer': 12,
        'color': '#4ADE80',  # Pale Green
        'label': 'OperationalLayer',
        'size': 1.1
    },

    # Layer 13-16: Resources & Constraints (Orange spectrum)
    'budget_constraint': {
        'layer': 13,
        'color': '#C2410C',  # Dark Orange
        'label': 'ResourceLayer',
        'size': 1.1
    },
    'system': {
        'layer': 14,
        'color': '#EA580C',  # Orange
        'label': 'ResourceLayer',
        'size': 1.3
    },
    'communication_channel': {
        'layer': 15,
        'color': '#F97316',  # Light Orange
        'label': 'ResourceLayer',
        'size': 1.0
    },
    'external_dependency': {
        'layer': 16,
        'color': '#FB923C',  # Pale Orange
        'label': 'ResourceLayer',
        'size': 1.0
    },

    # Layer 18-20: Issues & Problems (Red/Yellow spectrum)
    'pain_point': {
        'layer': 18,
        'color': '#DC2626',  # Red
        'label': 'IssueLayer',
        'size': 1.3
    },
    'failure_mode': {
        'layer': 19,
        'color': '#EF4444',  # Light Red
        'label': 'IssueLayer',
        'size': 1.1
    },
    'inefficiency': {
        'layer': 20,
        'color': '#FBBF24',  # Yellow
        'label': 'IssueLayer',
        'size': 1.1
    },

    # Layer 21-22: Solutions & Opportunities (Teal spectrum)
    'success_pattern': {
        'layer': 21,
        'color': '#0D9488',  # Dark Teal
        'label': 'SolutionLayer',
        'size': 1.2
    },
    'automation_candidate': {
        'layer': 22,
        'color': '#14B8A6',  # Teal
        'label': 'SolutionLayer',
        'size': 1.3
    },
}

RELATIONSHIP_STYLES = {
    # Hierarchical relationships
    'CONTAINS': {'color': '#64748B', 'width': 2, 'style': 'solid'},
    'BELONGS_TO': {'color': '#64748B', 'width': 2, 'style': 'solid'},
    'HAS_MEMBER': {'color': '#64748B', 'width': 1.5, 'style': 'solid'},

    # Operational relationships
    'OWNS': {'color': '#059669', 'width': 1.5, 'style': 'solid'},
    'EXECUTES': {'color': '#059669', 'width': 1.5, 'style': 'solid'},
    'USES': {'color': '#059669', 'width': 1.5, 'style': 'solid'},
    'HAS_PATTERN': {'color': '#059669', 'width': 1, 'style': 'solid'},
    'HAS_FLOW': {'color': '#059669', 'width': 1, 'style': 'solid'},
    'HAS_DECISION': {'color': '#059669', 'width': 1, 'style': 'solid'},

    # Measurement relationships
    'MEASURED_BY': {'color': '#7C3AED', 'width': 1, 'style': 'dashed'},
    'TRACKS': {'color': '#7C3AED', 'width': 1, 'style': 'dashed'},
    'HAS_OBJECTIVE': {'color': '#7C3AED', 'width': 1.5, 'style': 'dashed'},

    # Problem relationships
    'CAUSES': {'color': '#DC2626', 'width': 1.5, 'style': 'dotted'},
    'HAS_PAIN': {'color': '#DC2626', 'width': 1.5, 'style': 'dotted'},
    'EXPERIENCES': {'color': '#DC2626', 'width': 1.5, 'style': 'dotted'},
    'HAS_FAILURE': {'color': '#DC2626', 'width': 1, 'style': 'dotted'},
    'HAS_INEFFICIENCY': {'color': '#DC2626', 'width': 1, 'style': 'dotted'},

    # Solution relationships
    'SOLVES': {'color': '#14B8A6', 'width': 2, 'style': 'solid'},
    'IMPROVES': {'color': '#14B8A6', 'width': 2, 'style': 'solid'},
    'AUTOMATES': {'color': '#14B8A6', 'width': 2, 'style': 'solid'},
    'PREVENTS': {'color': '#14B8A6', 'width': 1.5, 'style': 'solid'},
    'HAS_SUCCESS': {'color': '#14B8A6', 'width': 1.5, 'style': 'solid'},

    # Communication relationships
    'COMMUNICATES_VIA': {'color': '#F59E0B', 'width': 1, 'style': 'dashed'},
    'COORDINATES_WITH': {'color': '#F59E0B', 'width': 1, 'style': 'dashed'},

    # Dependency relationships
    'DEPENDS_ON': {'color': '#6366F1', 'width': 1, 'style': 'dashed'},
    'DEPENDS_ON_EXTERNAL': {'color': '#6366F1', 'width': 1, 'style': 'dotted'},
}


def get_visualization_properties(entity_type: str) -> dict:
    """Get visualization properties for an entity type"""
    return ENTITY_LAYERS.get(entity_type, {
        'layer': 0,
        'color': '#9CA3AF',  # Gray fallback
        'label': 'Entity',
        'size': 1.0
    })


def add_visualization_properties(entity: dict) -> dict:
    """Add visualization properties to entity"""
    entity_type = entity.get('entity_type')
    viz = get_visualization_properties(entity_type)

    entity['layer'] = viz['layer']
    entity['color'] = viz['color']
    entity['viz_label'] = viz['label']
    entity['viz_size'] = viz['size']

    return entity
```

---

### Step 2: Update Consolidation Agent

Add visualization properties during entity consolidation:

**File**: `intelligence_capture/consolidation_agent.py`

```python
# Add import
from .visualization_config import add_visualization_properties

# In EntityMerger.merge_entities() method
def merge_entities(self, entity_group: List[Dict]) -> Dict:
    """Merge duplicate entities into single consolidated entity"""
    # ... existing merge logic ...

    merged = {
        'sqlite_entity_id': primary['id'],
        'entity_type': entity_type,
        'name': primary['name'],
        'org_id': self._extract_org_id(primary),
        'source_count': len(entity_group),
        'consensus_confidence': self._calculate_consensus(entity_group),
        'payload': payload
    }

    # Add visualization properties
    merged = add_visualization_properties(merged)

    return merged
```

---

### Step 3: Update Graph Sync Script

Modify sync script to use visualization properties:

**File**: `scripts/sync_consolidated_to_neo4j.py`

```python
# Add import
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence_capture.visualization_config import ENTITY_LAYERS

def normalize_entity_properties(properties: dict) -> dict:
    """Ensure common aliases exist + add visualization properties"""
    # Existing normalization
    org_alias = properties.get("organization") or properties.get("company") or properties.get("holding_name")
    if org_alias:
        properties["organization"] = org_alias
        properties["organization_normalized"] = str(org_alias).strip().lower()

    # Add visualization properties if not present
    entity_type = properties.get('entity_type')
    if entity_type and entity_type in ENTITY_LAYERS:
        viz = ENTITY_LAYERS[entity_type]
        if 'layer' not in properties:
            properties['layer'] = viz['layer']
        if 'color' not in properties:
            properties['color'] = viz['color']
        if 'viz_label' not in properties:
            properties['viz_label'] = viz['label']
        if 'viz_size' not in properties:
            properties['viz_size'] = viz['size']

    return properties

# In sync_entities() function
def sync_entities(builder, entities):
    """Sync entities to Neo4j with layer labels"""
    for entity in entities:
        # Add layer-specific label
        labels = ['Entity']
        if 'viz_label' in entity.properties:
            labels.append(entity.properties['viz_label'])

        builder.create_or_update_entity(
            external_id=entity.external_id,
            labels=labels,  # Include layer label
            entity_type=entity.entity_type,
            name=entity.name,
            org_id=entity.org_id,
            properties=entity.properties
        )
```

---

### Step 4: Update Relationship Inference

Enhance relationship inference with proper relationship types:

**File**: `scripts/infer_entity_relationships.py`

Add these inference rules:

```python
def infer_organizational_structure(graph_builder):
    """Infer CONTAINS relationships in organizational hierarchy"""
    query = """
    MATCH (parent:Entity), (child:Entity)
    WHERE parent.entity_type IN ['holding', 'company', 'business_unit', 'area']
      AND child.organization = parent.organization
      AND (
        (parent.entity_type = 'holding' AND child.entity_type = 'company')
        OR (parent.entity_type = 'company' AND child.business_unit = parent.name)
        OR (parent.entity_type = 'business_unit' AND child.area = parent.name)
        OR (parent.entity_type = 'area' AND child.entity_type = 'team_structure')
      )
      AND NOT EXISTS((parent)-[:CONTAINS]->(child))
    CREATE (parent)-[:CONTAINS {inferred: true, confidence: 0.9}]->(child)
    RETURN count(*) as created
    """
    result = graph_builder.execute_query(query)
    return result[0]['created'] if result else 0


def infer_team_ownership(graph_builder):
    """Infer OWNS relationships: Team → Process"""
    query = """
    MATCH (team:Entity {entity_type: 'team_structure'}), (process:Entity {entity_type: 'process'})
    WHERE process.owner_role = team.role
       OR process.responsible_team = team.name
       OR process.description CONTAINS team.name
       AND team.organization_normalized = process.organization_normalized
       AND NOT EXISTS((team)-[:OWNS]->(process))
    CREATE (team)-[:OWNS {inferred: true, confidence: 0.8}]->(process)
    RETURN count(*) as created
    """
    result = graph_builder.execute_query(query)
    return result[0]['created'] if result else 0


def infer_process_measurements(graph_builder):
    """Infer MEASURED_BY relationships: Process → KPI"""
    query = """
    MATCH (process:Entity {entity_type: 'process'}), (kpi:Entity {entity_type: 'kpi'})
    WHERE kpi.related_processes CONTAINS process.name
       OR kpi.measured_process = process.name
       AND process.organization_normalized = kpi.organization_normalized
       AND NOT EXISTS((process)-[:MEASURED_BY]->(kpi))
    CREATE (process)-[:MEASURED_BY {inferred: true, confidence: 0.85}]->(kpi)
    RETURN count(*) as created
    """
    result = graph_builder.execute_query(query)
    return result[0]['created'] if result else 0


def infer_automation_solutions(graph_builder):
    """Infer SOLVES relationships: Automation → Pain Point"""
    query = """
    MATCH (automation:Entity {entity_type: 'automation_candidate'}), (pain:Entity {entity_type: 'pain_point'})
    WHERE automation.pain_point_id = pain.id
       OR automation.solves_pain_point = pain.name
       OR automation.description CONTAINS pain.description
       AND automation.organization_normalized = pain.organization_normalized
       AND NOT EXISTS((automation)-[:SOLVES]->(pain))
    CREATE (automation)-[:SOLVES {inferred: true, confidence: 0.75}]->(pain)
    RETURN count(*) as created
    """
    result = graph_builder.execute_query(query)
    return result[0]['created'] if result else 0


# Add to run_inference() function
def run_inference(pg_url, dry_run=False, limit=None, builder=None, verbose=True):
    """Run all relationship inference rules"""
    total_created = 0

    # Existing inferences
    total_created += infer_process_uses_system(builder)
    total_created += infer_system_causes_pain(builder)

    # New inferences
    total_created += infer_organizational_structure(builder)
    total_created += infer_team_ownership(builder)
    total_created += infer_process_measurements(builder)
    total_created += infer_automation_solutions(builder)

    if verbose:
        print(f"✓ Total relationships inferred: {total_created}")

    return total_created
```

---

### Step 5: Neo4j Browser Styling

Apply this configuration in Neo4j Browser:

**Settings → Graph Stylesheet**

```css
/* Node styling by layer */
node.OrganizationalLayer {
  color: #2563EB;
  border-color: #1E3A8A;
  text-color-internal: white;
  diameter: 50px;
  caption: "{name}";
}

node.StrategyLayer {
  color: #9333EA;
  border-color: #6B21A8;
  text-color-internal: white;
  diameter: 45px;
  caption: "{name}";
}

node.OperationalLayer {
  color: #16A34A;
  border-color: #15803D;
  text-color-internal: white;
  diameter: 55px;
  caption: "{name}";
}

node.ResourceLayer {
  color: #EA580C;
  border-color: #C2410C;
  text-color-internal: white;
  diameter: 40px;
  caption: "{name}";
}

node.IssueLayer {
  color: #DC2626;
  border-color: #991B1B;
  text-color-internal: white;
  diameter: 50px;
  caption: "{name}";
}

node.SolutionLayer {
  color: #14B8A6;
  border-color: #0D9488;
  text-color-internal: white;
  diameter: 50px;
  caption: "{name}";
}

/* Relationship styling */
relationship {
  shaft-width: 2px;
  color: #94A3B8;
}

relationship.CONTAINS {
  color: #64748B;
  shaft-width: 2px;
}

relationship.OWNS {
  color: #059669;
  shaft-width: 1.5px;
}

relationship.USES {
  color: #059669;
  shaft-width: 1.5px;
}

relationship.MEASURED_BY {
  color: #7C3AED;
  shaft-width: 1px;
  line-style: dashed;
}

relationship.CAUSES {
  color: #DC2626;
  shaft-width: 1.5px;
  line-style: dotted;
}

relationship.SOLVES {
  color: #14B8A6;
  shaft-width: 2px;
}

relationship.COMMUNICATES_VIA {
  color: #F59E0B;
  shaft-width: 1px;
  line-style: dashed;
}
```

---

## 🧪 Testing the Visualization

After implementation, test with these queries:

### Test 1: Layer-Based Filtering

```cypher
// Show only operational layer
MATCH (n:OperationalLayer)
RETURN n
LIMIT 50
```

### Test 2: Organizational Hierarchy (Blue)

```cypher
// Show org structure in blue tones
MATCH path = (h:OrganizationalLayer)-[:CONTAINS*]->(child:OrganizationalLayer)
WHERE h.entity_type = 'holding'
RETURN path
LIMIT 20
```

### Test 3: Pain Point Analysis (Red + Orange)

```cypher
// Show issues (red) caused by resources (orange)
MATCH path = (system:ResourceLayer)-[:CAUSES]->(pain:IssueLayer)
RETURN path
LIMIT 30
```

### Test 4: Solution Mapping (Teal solving Red)

```cypher
// Show automations (teal) solving pain points (red)
MATCH path = (automation:SolutionLayer)-[:SOLVES]->(pain:IssueLayer)
RETURN path
LIMIT 20
```

### Test 5: Multi-Layer Pattern

```cypher
// Show team (blue) → process (green) → system (orange) → pain (red)
MATCH path = (team:OrganizationalLayer {entity_type: 'team_structure'})
             -[:OWNS]->(process:OperationalLayer)
             -[:USES]->(system:ResourceLayer)
             -[:CAUSES]->(pain:IssueLayer)
RETURN path
LIMIT 10
```

---

## 📋 Execution Checklist

Before running full pipeline:

- [ ] Create `intelligence_capture/visualization_config.py`
- [ ] Update `intelligence_capture/consolidation_agent.py`
- [ ] Update `scripts/sync_consolidated_to_neo4j.py`
- [ ] Enhance `scripts/infer_entity_relationships.py`
- [ ] Apply Neo4j Browser styling
- [ ] Test with sample data

After full pipeline:

- [ ] Verify color-coded nodes in Neo4j Browser
- [ ] Confirm layer labels working
- [ ] Test relationship type styling
- [ ] Validate inference rules creating proper relationships
- [ ] Generate visualization screenshots for documentation

---

## 🎯 Expected Results

**Before** (current):
- All nodes pink/purple
- No hierarchy visible
- Relationships indistinguishable
- Cluttered layout

**After** (with implementation):
- Blue: Organizational structure (holding → team)
- Purple: Strategy (objectives, KPIs)
- Green: Operations (processes, patterns, flows)
- Orange: Resources (systems, channels, budget)
- Red/Yellow: Issues (pain points, failures, inefficiencies)
- Teal: Solutions (success patterns, automation)

**Clear visual hierarchy** enabling intuitive graph exploration! 🎨

---

**Next**: Implement Steps 1-5, then run full pipeline with visualization
