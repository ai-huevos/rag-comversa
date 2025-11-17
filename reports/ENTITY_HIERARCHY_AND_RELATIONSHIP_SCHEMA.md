# Entity Hierarchy & Relationship Schema

**Date**: 2025-11-16
**Purpose**: Define clear entity hierarchy, relationships, and visualization schema for Neo4j
**Problem**: Current graph is cluttered with no clear visual hierarchy or color-coding

---

## 🎨 Visual Design Principles

### Entity Color Scheme by Layer

```
Layer 1: Organizational Structure (Blue spectrum)
  holding_name          → #1E3A8A (Dark Blue)
  company               → #2563EB (Blue)
  business_unit         → #3B82F6 (Light Blue)
  area/department       → #60A5FA (Sky Blue)
  team_structure        → #93C5FD (Pale Blue)
  role                  → #DBEAFE (Very Light Blue)

Layer 2: Strategy & Goals (Purple spectrum)
  objectives            → #6B21A8 (Dark Purple)
  kpis                  → #9333EA (Purple)

Layer 3: Operations (Green spectrum)
  process               → #15803D (Dark Green)
  temporal_pattern      → #16A34A (Green)
  data_flow             → #22C55E (Light Green)
  decision_point        → #4ADE80 (Pale Green)

Layer 4: Resources & Constraints (Orange spectrum)
  budget_constraint     → #C2410C (Dark Orange)
  system                → #EA580C (Orange)
  communication_channel → #F97316 (Light Orange)
  external_dependency   → #FB923C (Pale Orange)

Layer 5: Issues & Opportunities (Red/Yellow spectrum)
  pain_point            → #DC2626 (Red)
  failure_mode          → #EF4444 (Light Red)
  inefficiency          → #FBBF24 (Yellow)

Layer 6: Solutions & Wins (Teal spectrum)
  success_pattern       → #0D9488 (Dark Teal)
  automation_candidate  → #14B8A6 (Teal)
```

### Relationship Visual Style

```
Hierarchical (CONTAINS, BELONGS_TO):
  Style: Solid line, thickness: 2px
  Color: #64748B (Slate)

Operational (USES, EXECUTES, OWNS):
  Style: Solid line, thickness: 1.5px
  Color: #059669 (Emerald)

Measurement (MEASURED_BY, TRACKS):
  Style: Dashed line, thickness: 1px
  Color: #7C3AED (Violet)

Problem relationships (CAUSES, HAS_PAIN, EXPERIENCES):
  Style: Dotted line, thickness: 1.5px
  Color: #DC2626 (Red)

Solution relationships (SOLVES, IMPROVES):
  Style: Solid line, thickness: 2px
  Color: #14B8A6 (Teal)

Communication (COMMUNICATES_VIA, COORDINATES_WITH):
  Style: Dashed line, thickness: 1px
  Color: #F59E0B (Amber)
```

---

## 📊 Entity Hierarchy (Top to Bottom)

```
┌─────────────────────────────────────────────────────────────────┐
│                    ORGANIZATIONAL HIERARCHY                      │
└─────────────────────────────────────────────────────────────────┘

1. HOLDING (Root)
   ├─ CONTAINS → 2. COMPANY
                  ├─ CONTAINS → 3. BUSINESS_UNIT
                                ├─ CONTAINS → 4. AREA/DEPARTMENT
                                              ├─ CONTAINS → 5. TEAM_STRUCTURE
                                                            ├─ HAS_MEMBER → 6. ROLE

┌─────────────────────────────────────────────────────────────────┐
│                    STRATEGIC LAYER                               │
└─────────────────────────────────────────────────────────────────┘

7. OBJECTIVES (linked to business_unit or team)
   └─ MEASURED_BY → 8. KPI

┌─────────────────────────────────────────────────────────────────┐
│                    OPERATIONAL LAYER                             │
└─────────────────────────────────────────────────────────────────┘

9. PROCESS
   ├─ HAS_PATTERN → 10. TEMPORAL_PATTERN
   ├─ HAS_FLOW → 11. DATA_FLOW
   └─ HAS_DECISION → 12. DECISION_POINT

┌─────────────────────────────────────────────────────────────────┐
│                    RESOURCE LAYER                                │
└─────────────────────────────────────────────────────────────────┘

13. BUDGET_CONSTRAINT (linked to business_unit or process)
14. SYSTEM (used by processes)
15. COMMUNICATION_CHANNEL (used by teams)
16. EXTERNAL_DEPENDENCY (dependencies of processes/systems)

┌─────────────────────────────────────────────────────────────────┐
│                    MEASUREMENT LAYER                             │
└─────────────────────────────────────────────────────────────────┘

17. KPI (measures objectives, processes)

┌─────────────────────────────────────────────────────────────────┐
│                    ISSUE LAYER                                   │
└─────────────────────────────────────────────────────────────────┘

18. PAIN_POINT (experienced by roles, caused by systems/processes)
19. FAILURE_MODE (failure patterns in processes)
20. INEFFICIENCY (inefficiencies in processes)

┌─────────────────────────────────────────────────────────────────┐
│                    SOLUTION LAYER                                │
└─────────────────────────────────────────────────────────────────┘

21. SUCCESS_PATTERN (successful patterns in processes)
22. AUTOMATION_CANDIDATE (opportunities to automate)
```

---

## 🔗 Relationship Schema

### Level 1: Organizational Structure

```cypher
-- Holding → Company
(holding:Entity {entity_type: 'holding'})-[:CONTAINS]->(company:Entity {entity_type: 'company'})

-- Company → Business Unit
(company:Entity {entity_type: 'company'})-[:CONTAINS]->(bu:Entity {entity_type: 'business_unit'})

-- Business Unit → Area/Department
(bu:Entity {entity_type: 'business_unit'})-[:CONTAINS]->(area:Entity {entity_type: 'area'})

-- Area → Team
(area:Entity {entity_type: 'area'})-[:CONTAINS]->(team:Entity {entity_type: 'team_structure'})

-- Team → Role
(team:Entity {entity_type: 'team_structure'})-[:HAS_MEMBER]->(role:Entity {entity_type: 'role'})

-- Role → Role (coordination)
(role1:Entity {entity_type: 'role'})-[:COORDINATES_WITH]->(role2:Entity {entity_type: 'role'})

-- Team → Team (coordination)
(team1:Entity {entity_type: 'team_structure'})-[:COORDINATES_WITH]->(team2:Entity {entity_type: 'team_structure'})
```

### Level 2: Strategy & Ownership

```cypher
-- Business Unit → Objectives
(bu:Entity {entity_type: 'business_unit'})-[:HAS_OBJECTIVE]->(obj:Entity {entity_type: 'objective'})

-- Team → Objectives
(team:Entity {entity_type: 'team_structure'})-[:WORKS_TOWARD]->(obj:Entity {entity_type: 'objective'})

-- Objective → KPI
(obj:Entity {entity_type: 'objective'})-[:MEASURED_BY]->(kpi:Entity {entity_type: 'kpi'})
```

### Level 3: Operational Relationships

```cypher
-- Team → Process (ownership)
(team:Entity {entity_type: 'team_structure'})-[:OWNS]->(process:Entity {entity_type: 'process'})

-- Role → Process (executes)
(role:Entity {entity_type: 'role'})-[:EXECUTES]->(process:Entity {entity_type: 'process'})

-- Process → Temporal Pattern
(process:Entity {entity_type: 'process'})-[:HAS_PATTERN]->(pattern:Entity {entity_type: 'temporal_pattern'})

-- Process → Data Flow
(process:Entity {entity_type: 'process'})-[:HAS_FLOW]->(flow:Entity {entity_type: 'data_flow'})

-- Process → Decision Point
(process:Entity {entity_type: 'process'})-[:HAS_DECISION]->(decision:Entity {entity_type: 'decision_point'})

-- Process → Process (dependencies)
(process1:Entity {entity_type: 'process'})-[:DEPENDS_ON]->(process2:Entity {entity_type: 'process'})

-- Decision Point → Process (affects)
(decision:Entity {entity_type: 'decision_point'})-[:AFFECTS]->(process:Entity {entity_type: 'process'})
```

### Level 4: Resource Relationships

```cypher
-- Business Unit → Budget Constraint
(bu:Entity {entity_type: 'business_unit'})-[:HAS_CONSTRAINT]->(budget:Entity {entity_type: 'budget_constraint'})

-- Process → Budget Constraint
(process:Entity {entity_type: 'process'})-[:CONSTRAINED_BY]->(budget:Entity {entity_type: 'budget_constraint'})

-- Process → System (uses)
(process:Entity {entity_type: 'process'})-[:USES]->(system:Entity {entity_type: 'system'})

-- Team → Communication Channel
(team:Entity {entity_type: 'team_structure'})-[:COMMUNICATES_VIA]->(channel:Entity {entity_type: 'communication_channel'})

-- Role → Communication Channel
(role:Entity {entity_type: 'role'})-[:COMMUNICATES_VIA]->(channel:Entity {entity_type: 'communication_channel'})

-- Process → External Dependency
(process:Entity {entity_type: 'process'})-[:DEPENDS_ON_EXTERNAL]->(dep:Entity {entity_type: 'external_dependency'})

-- System → External Dependency
(system:Entity {entity_type: 'system'})-[:DEPENDS_ON_EXTERNAL]->(dep:Entity {entity_type: 'external_dependency'})
```

### Level 5: Measurement Relationships

```cypher
-- Process → KPI (measured by)
(process:Entity {entity_type: 'process'})-[:MEASURED_BY]->(kpi:Entity {entity_type: 'kpi'})

-- System → KPI (tracks)
(system:Entity {entity_type: 'system'})-[:TRACKS]->(kpi:Entity {entity_type: 'kpi'})
```

### Level 6: Issue Relationships

```cypher
-- Process → Pain Point
(process:Entity {entity_type: 'process'})-[:HAS_PAIN]->(pain:Entity {entity_type: 'pain_point'})

-- System → Pain Point (causes)
(system:Entity {entity_type: 'system'})-[:CAUSES]->(pain:Entity {entity_type: 'pain_point'})

-- Role → Pain Point (experiences)
(role:Entity {entity_type: 'role'})-[:EXPERIENCES]->(pain:Entity {entity_type: 'pain_point'})

-- Process → Failure Mode
(process:Entity {entity_type: 'process'})-[:HAS_FAILURE]->(failure:Entity {entity_type: 'failure_mode'})

-- Process → Inefficiency
(process:Entity {entity_type: 'process'})-[:HAS_INEFFICIENCY]->(inefficiency:Entity {entity_type: 'inefficiency'})
```

### Level 7: Solution Relationships

```cypher
-- Process → Success Pattern
(process:Entity {entity_type: 'process'})-[:HAS_SUCCESS]->(success:Entity {entity_type: 'success_pattern'})

-- Automation Candidate → Pain Point (solves)
(automation:Entity {entity_type: 'automation_candidate'})-[:SOLVES]->(pain:Entity {entity_type: 'pain_point'})

-- Automation Candidate → Inefficiency (improves)
(automation:Entity {entity_type: 'automation_candidate'})-[:IMPROVES]->(inefficiency:Entity {entity_type: 'inefficiency'})

-- Automation Candidate → Process (automates)
(automation:Entity {entity_type: 'automation_candidate'})-[:AUTOMATES]->(process:Entity {entity_type: 'process'})

-- Success Pattern → Pain Point (prevents)
(success:Entity {entity_type: 'success_pattern'})-[:PREVENTS]->(pain:Entity {entity_type: 'pain_point'})
```

---

## 🏗️ Neo4j Node Labels & Properties

### Node Structure

```cypher
CREATE (n:Entity {
  -- Core identifiers
  id: "unique_id",
  entity_type: "process",  // From entity type list above

  -- Organizational context
  holding_name: "Comversa Group",
  organization: "Los Tajibos",
  business_unit: "Operations",
  area: "Maintenance",
  department: "Engineering",

  -- Entity specifics
  name: "Maintenance Planning",
  description: "Weekly maintenance planning process",

  -- Metadata
  source_count: 3,
  consensus_confidence: 0.85,

  -- Visualization
  layer: 3,  // Operational layer
  color: "#15803D",  // Dark green
  size: 1.5  // Relative size based on importance
})
```

### Additional Labels for Filtering

```cypher
-- Add layer labels for easy filtering
(:Entity:OrganizationalLayer)  // Layers 1-6 (holding → role)
(:Entity:StrategyLayer)         // Layer 7-8 (objectives, KPIs)
(:Entity:OperationalLayer)      // Layer 9-12 (processes, patterns, flows, decisions)
(:Entity:ResourceLayer)         // Layer 13-16 (budget, systems, channels, dependencies)
(:Entity:MeasurementLayer)      // Layer 17 (KPIs)
(:Entity:IssueLayer)            // Layer 18-20 (pain points, failures, inefficiencies)
(:Entity:SolutionLayer)         // Layer 21-22 (success patterns, automation)
```

---

## 📐 Property-Based Relationship Inference Rules

### Organizational Structure Inference

```cypher
-- Infer CONTAINS relationships from organization properties
MATCH (parent:Entity), (child:Entity)
WHERE parent.entity_type IN ['holding', 'company', 'business_unit', 'area']
  AND child.organization = parent.organization
  AND child.business_unit = parent.name
  AND NOT (parent)-[:CONTAINS]->(child)
CREATE (parent)-[:CONTAINS]->(child)
```

### Team → Process Ownership

```cypher
-- Infer OWNS from team_structure mentioning process
MATCH (team:Entity {entity_type: 'team_structure'}), (process:Entity {entity_type: 'process'})
WHERE process.owner_role = team.role
   OR process.responsible_team = team.name
   OR process.description CONTAINS team.name
CREATE (team)-[:OWNS]->(process)
```

### Process → System Usage

```cypher
-- Already implemented
MATCH (process:Entity {entity_type: 'process'}), (system:Entity {entity_type: 'system'})
WHERE process.systems_used CONTAINS system.name
  AND process.organization_normalized = system.organization_normalized
CREATE (process)-[:USES]->(system)
```

### System → Pain Point Causation

```cypher
-- Already implemented
MATCH (system:Entity {entity_type: 'system'}), (pain:Entity {entity_type: 'pain_point'})
WHERE pain.related_systems CONTAINS system.name
  AND system.organization_normalized = pain.organization_normalized
CREATE (system)-[:CAUSES]->(pain)
```

### Process → KPI Measurement

```cypher
-- Infer MEASURED_BY from KPI tracking processes
MATCH (process:Entity {entity_type: 'process'}), (kpi:Entity {entity_type: 'kpi'})
WHERE kpi.related_processes CONTAINS process.name
   OR kpi.measured_process = process.name
CREATE (process)-[:MEASURED_BY]->(kpi)
```

### Automation → Pain Point Solution

```cypher
-- Infer SOLVES from automation targeting pain points
MATCH (automation:Entity {entity_type: 'automation_candidate'}), (pain:Entity {entity_type: 'pain_point'})
WHERE automation.pain_point_id = pain.id
   OR automation.solves_pain_point = pain.name
CREATE (automation)-[:SOLVES]->(pain)
```

---

## 🎯 Query Examples by Use Case

### 1. Organizational Hierarchy View

```cypher
// Show org structure for a company
MATCH path = (h:Entity {entity_type: 'holding'})-[:CONTAINS*]->(n:Entity)
WHERE h.name = 'Comversa Group'
  AND n.entity_type IN ['company', 'business_unit', 'area', 'team_structure']
RETURN path
```

### 2. Team Operations View

```cypher
// Show what a team owns and uses
MATCH (team:Entity {entity_type: 'team_structure', name: 'Engineering Team'})
OPTIONAL MATCH (team)-[:OWNS]->(process:Entity)
OPTIONAL MATCH (process)-[:USES]->(system:Entity)
OPTIONAL MATCH (team)-[:COMMUNICATES_VIA]->(channel:Entity)
RETURN team, process, system, channel
```

### 3. Pain Point Root Cause View

```cypher
// Trace pain points to root causes
MATCH path = (role:Entity {entity_type: 'role'})
             -[:EXPERIENCES]->(pain:Entity {entity_type: 'pain_point'})
             <-[:CAUSES]-(system:Entity {entity_type: 'system'})
             <-[:USES]-(process:Entity {entity_type: 'process'})
WHERE role.organization = 'Los Tajibos'
RETURN path
LIMIT 20
```

### 4. Process Efficiency View

```cypher
// Show process with pain points, inefficiencies, and automation candidates
MATCH (process:Entity {entity_type: 'process'})
OPTIONAL MATCH (process)-[:HAS_PAIN]->(pain:Entity)
OPTIONAL MATCH (process)-[:HAS_INEFFICIENCY]->(inefficiency:Entity)
OPTIONAL MATCH (automation:Entity)-[:AUTOMATES]->(process)
WHERE process.organization = 'Los Tajibos'
RETURN process, pain, inefficiency, automation
LIMIT 10
```

### 5. Strategic Alignment View

```cypher
// Show how processes align to objectives via KPIs
MATCH path = (bu:Entity {entity_type: 'business_unit'})
             -[:HAS_OBJECTIVE]->(obj:Entity)
             -[:MEASURED_BY]->(kpi:Entity)
             <-[:MEASURED_BY]-(process:Entity)
WHERE bu.name = 'Operations'
RETURN path
```

---

## 🔧 Implementation Plan

### Phase 1: Update Entity Properties ✅ (During extraction/consolidation)

Add layer and visualization properties during consolidation:

```python
# intelligence_capture/consolidation_agent.py

ENTITY_LAYERS = {
    'holding': {'layer': 1, 'color': '#1E3A8A', 'label': 'OrganizationalLayer'},
    'company': {'layer': 2, 'color': '#2563EB', 'label': 'OrganizationalLayer'},
    'business_unit': {'layer': 3, 'color': '#3B82F6', 'label': 'OrganizationalLayer'},
    'area': {'layer': 4, 'color': '#60A5FA', 'label': 'OrganizationalLayer'},
    'team_structure': {'layer': 5, 'color': '#93C5FD', 'label': 'OrganizationalLayer'},
    'role': {'layer': 6, 'color': '#DBEAFE', 'label': 'OrganizationalLayer'},
    'objective': {'layer': 7, 'color': '#6B21A8', 'label': 'StrategyLayer'},
    'kpi': {'layer': 8, 'color': '#9333EA', 'label': 'MeasurementLayer'},
    'process': {'layer': 9, 'color': '#15803D', 'label': 'OperationalLayer'},
    'temporal_pattern': {'layer': 10, 'color': '#16A34A', 'label': 'OperationalLayer'},
    'data_flow': {'layer': 11, 'color': '#22C55E', 'label': 'OperationalLayer'},
    'decision_point': {'layer': 12, 'color': '#4ADE80', 'label': 'OperationalLayer'},
    'budget_constraint': {'layer': 13, 'color': '#C2410C', 'label': 'ResourceLayer'},
    'system': {'layer': 14, 'color': '#EA580C', 'label': 'ResourceLayer'},
    'communication_channel': {'layer': 15, 'color': '#F97316', 'label': 'ResourceLayer'},
    'external_dependency': {'layer': 16, 'color': '#FB923C', 'label': 'ResourceLayer'},
    'pain_point': {'layer': 18, 'color': '#DC2626', 'label': 'IssueLayer'},
    'failure_mode': {'layer': 19, 'color': '#EF4444', 'label': 'IssueLayer'},
    'inefficiency': {'layer': 20, 'color': '#FBBF24', 'label': 'IssueLayer'},
    'success_pattern': {'layer': 21, 'color': '#0D9488', 'label': 'SolutionLayer'},
    'automation_candidate': {'layer': 22, 'color': '#14B8A6', 'label': 'SolutionLayer'},
}

def add_visualization_properties(entity: dict) -> dict:
    """Add layer, color, and label for Neo4j visualization"""
    entity_type = entity.get('entity_type')
    if entity_type in ENTITY_LAYERS:
        viz = ENTITY_LAYERS[entity_type]
        entity['layer'] = viz['layer']
        entity['color'] = viz['color']
        entity['viz_label'] = viz['label']
    return entity
```

### Phase 2: Update Graph Sync Script

**File**: `scripts/sync_consolidated_to_neo4j.py`

```python
# Add layer labels when creating nodes
def create_entity_node(builder, entity):
    labels = ['Entity']

    # Add layer label
    if 'viz_label' in entity.properties:
        labels.append(entity.properties['viz_label'])

    builder.create_node(
        external_id=entity.external_id,
        labels=labels,
        properties={
            **entity.properties,
            'layer': entity.properties.get('layer', 0),
            'color': entity.properties.get('color', '#9CA3AF'),
        }
    )
```

### Phase 3: Enhanced Relationship Inference

**File**: `scripts/infer_entity_relationships.py`

Add all the relationship inference rules from above:
- Organizational structure (CONTAINS, BELONGS_TO)
- Team ownership (OWNS, EXECUTES)
- Resource usage (USES, COMMUNICATES_VIA)
- Measurement (MEASURED_BY, TRACKS)
- Issues (CAUSES, HAS_PAIN, EXPERIENCES)
- Solutions (SOLVES, IMPROVES, AUTOMATES)

### Phase 4: Neo4j Styling Configuration

**File**: `config/neo4j_visualization.json`

```json
{
  "node_styling": {
    "Entity": {
      "color": "{color}",
      "size": "{source_count * 10}",
      "label": "{name}"
    }
  },
  "relationship_styling": {
    "CONTAINS": {"color": "#64748B", "width": 2, "style": "solid"},
    "OWNS": {"color": "#059669", "width": 1.5, "style": "solid"},
    "USES": {"color": "#059669", "width": 1.5, "style": "solid"},
    "MEASURED_BY": {"color": "#7C3AED", "width": 1, "style": "dashed"},
    "CAUSES": {"color": "#DC2626", "width": 1.5, "style": "dotted"},
    "SOLVES": {"color": "#14B8A6", "width": 2, "style": "solid"},
    "COMMUNICATES_VIA": {"color": "#F59E0B", "width": 1, "style": "dashed"}
  }
}
```

---

## 🎨 Neo4j Browser Styling

Apply this in Neo4j Browser Settings:

```css
/* Node styling by layer */
node.OrganizationalLayer {
  color: #2563EB;
  border-color: #1E3A8A;
  diameter: 50px;
}

node.StrategyLayer {
  color: #9333EA;
  border-color: #6B21A8;
  diameter: 45px;
}

node.OperationalLayer {
  color: #16A34A;
  border-color: #15803D;
  diameter: 55px;
}

node.ResourceLayer {
  color: #EA580C;
  border-color: #C2410C;
  diameter: 40px;
}

node.IssueLayer {
  color: #DC2626;
  border-color: #991B1B;
  diameter: 50px;
}

node.SolutionLayer {
  color: #14B8A6;
  border-color: #0D9488;
  diameter: 50px;
}

/* Relationship styling */
relationship {
  shaft-width: 2px;
}

relationship.CONTAINS {
  color: #64748B;
  shaft-width: 2px;
}

relationship.USES {
  color: #059669;
  shaft-width: 1.5px;
}

relationship.CAUSES {
  color: #DC2626;
  shaft-width: 1.5px;
  line-style: dotted;
}
```

---

## 📊 Expected Results

After implementation, queries will show:

**Organizational View**: Blue hierarchy from holding → company → team
**Operational View**: Green processes with their patterns/flows/decisions
**Issue Analysis**: Red pain points connected to orange systems/resources
**Solution Mapping**: Teal automation candidates solving red pain points

**Clear visual hierarchy** with color-coded layers makes graph exploration intuitive.

---

**Next**: Implement Phase 1-4 before running full pipeline
