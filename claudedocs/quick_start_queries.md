# Quick Start: Visual Ecosystem Exploration

## 🚀 Getting Started

**Neo4j Browser is now open:** http://localhost:7474
- Username: `neo4j`
- Password: `comversa_neo4j_2025`

---

## 📊 Current Data Overview

**Total Entities:** 1,743 across 13 types

| Entity Type | Count | Description |
|-------------|-------|-------------|
| Communication Channels | 232 | Email, WhatsApp, Slack, etc. |
| Temporal Patterns | 210 | When things happen (daily, weekly, month-end) |
| Systems | 183 | Software platforms (Micros, Opera, SAP, etc.) |
| Success Patterns | 172 | What works well |
| Processes | 170 | Business workflows |
| Failure Modes | 149 | Common breakdowns |
| Data Flows | 137 | How information moves |
| Decision Points | 126 | Where choices are made |
| KPIs | 124 | Metrics being tracked |
| Inefficiencies | 123 | Process bottlenecks |
| Automation Candidates | 98 | Tasks that could be automated |
| Pain Points | 11 | Major problems (high confidence) |
| External Dependencies | 8 | Outside systems/vendors |

**Note:** Organization tagging is incomplete (most tagged as "default"). You'll need to infer company from entity names and context.

---

## 🎯 Start Here: Copy-Paste These Queries into Neo4j Browser

### 1. Overview: See All Entity Types
```cypher
// Get a sample of each entity type
MATCH (e:Entity)
WITH e.entity_type as type, collect(e)[0..5] as samples
RETURN type, samples
ORDER BY type
```

### 2. System Ecosystem Map
```cypher
// Visualize all systems and their immediate connections
MATCH (s:Entity {entity_type: 'system'})
OPTIONAL MATCH (s)-[r]-(connected)
RETURN s, r, connected
LIMIT 100
```

### 3. Process-System Dependencies
```cypher
// How processes use systems
MATCH (p:Entity {entity_type: 'process'})-[r]-(s:Entity {entity_type: 'system'})
RETURN p, r, s
LIMIT 50
```

### 4. Pain Points Network
```cypher
// What causes pain points and what they affect
MATCH (pain:Entity {entity_type: 'pain_point'})
OPTIONAL MATCH (pain)-[r]-(related)
RETURN pain, r, related
LIMIT 100
```

### 5. Automation Opportunities
```cypher
// Processes that could be automated
MATCH (auto:Entity {entity_type: 'automation_candidate'})
OPTIONAL MATCH (auto)-[r]-(related)
RETURN auto, r, related
LIMIT 50
```

### 6. Communication Breakdown
```cypher
// How teams communicate
MATCH (comm:Entity {entity_type: 'communication_channel'})
OPTIONAL MATCH (comm)-[r]-(related)
RETURN comm, r, related
LIMIT 100
```

### 7. Temporal Patterns (When Things Happen)
```cypher
// Time-based patterns in operations
MATCH (temp:Entity {entity_type: 'temporal_pattern'})
OPTIONAL MATCH (temp)-[r]-(related)
RETURN temp, r, related
LIMIT 50
```

### 8. Success Patterns (What Works)
```cypher
// Proven successful approaches
MATCH (success:Entity {entity_type: 'success_pattern'})
OPTIONAL MATCH (success)-[r]-(related)
RETURN success, r, related
LIMIT 50
```

### 9. Failure Modes (What Breaks)
```cypher
// Common failure patterns
MATCH (failure:Entity {entity_type: 'failure_mode'})
OPTIONAL MATCH (failure)-[r]-(related)
RETURN failure, r, related
LIMIT 50
```

### 10. Data Flow Visualization
```cypher
// How data moves through the organization
MATCH (flow:Entity {entity_type: 'data_flow'})
OPTIONAL MATCH (flow)-[r]-(related)
RETURN flow, r, related
LIMIT 50
```

---

## 🏢 Company-Specific Analysis

Since organization tagging is incomplete, use name patterns to filter:

### Los Tajibos Systems
```cypher
// Look for Los Tajibos-related entities
MATCH (e:Entity)
WHERE e.name =~ '.*Tajibos.*'
   OR e.name =~ '.*Opera.*'
   OR e.name =~ '.*Marriott.*'
   OR e.name =~ '.*MGS.*'
OPTIONAL MATCH (e)-[r]-(related)
RETURN e, r, related
LIMIT 100
```

### Comversa/Bolivian Foods Systems
```cypher
// Look for food/production-related entities
MATCH (e:Entity)
WHERE e.name =~ '.*SAP.*'
   OR e.name =~ '.*producción.*'
   OR e.name =~ '.*inventario.*'
   OR e.employee_company IN ['COMVERSA', 'BOLIVIAN FOODS']
OPTIONAL MATCH (e)-[r]-(related)
RETURN e, r, related
LIMIT 100
```

---

## 🔍 Exploration Workflow

### Phase 1: High-Level Understanding (Start Here)
1. Run **Query #1** (Overview) to see all entity types
2. Run **Query #2** (System Ecosystem) to map platforms
3. Click on interesting nodes to explore their connections

### Phase 2: Process Analysis
1. Run **Query #3** (Process-System) to understand workflows
2. Run **Query #10** (Data Flows) to see information movement
3. Run **Query #6** (Communication) to map collaboration

### Phase 3: Problems & Solutions
1. Run **Query #4** (Pain Points) to identify major issues
2. Run **Query #9** (Failure Modes) to see what breaks
3. Run **Query #5** (Automation) to find improvement opportunities

### Phase 4: Patterns & Learning
1. Run **Query #8** (Success Patterns) to see what works
2. Run **Query #7** (Temporal Patterns) to understand timing
3. Cross-reference with company-specific queries

---

## 🎨 Neo4j Browser Tips

### Visual Customization
- **Node Size:** Right sidebar → Node size by property (use `source_count`)
- **Node Color:** Already colored by `entity_type`
- **Node Labels:** Click node type in sidebar → Caption: `name`
- **Layout:** Try "Force-directed" and "Hierarchical" layouts

### Navigation
- **Pan:** Click and drag background
- **Zoom:** Scroll wheel or pinch
- **Expand:** Double-click a node to see its neighbors
- **Select:** Click node → See properties in right panel
- **Deselect:** Click background

### Filtering
- **By Type:** Click entity type in left sidebar to show/hide
- **By Property:** Use WHERE clauses in queries
- **By Relationship:** Click relationship type to hide/show

### Saving Work
- **Star Queries:** Click ⭐ to bookmark useful queries
- **Export:** Right-click graph → Export as PNG/SVG
- **History:** Use `:history` command to see past queries

---

## 📋 Sample Questions You Can Answer

### Platform Questions
- **Q:** "What systems are most connected?"
  - Run Query #2, look for nodes with many edges

- **Q:** "Which systems have automation potential?"
  - Run Query #5, see systems linked to automation_candidate nodes

### Process Questions
- **Q:** "What processes depend on which systems?"
  - Run Query #3, follow the edges

- **Q:** "Where do processes fail?"
  - Run Query #9, look for failure_mode connections

### Strategic Questions
- **Q:** "What are our biggest pain points?"
  - Run Query #4, focus on high `source_count` nodes

- **Q:** "What practices should we replicate?"
  - Run Query #8, identify success_pattern nodes

---

## 🔧 Next Steps for Better Organization View

The data currently lacks strong organization tagging. To improve clustering by company:

### Option 1: Manual Tagging (Quick)
Use Neo4j Browser to manually tag key systems:
```cypher
// Example: Tag Marriott systems as Los Tajibos
MATCH (s:Entity {entity_type: 'system'})
WHERE s.name =~ '.*Marriott.*' OR s.name =~ '.*Opera.*'
SET s.organization = 'Los Tajibos'
```

### Option 2: Re-run Consolidation (Complete)
Improve the consolidation agent to extract organization from interview metadata, then re-sync to Neo4j.

---

## 💡 Pro Tips

1. **Start Small:** Use `LIMIT 50` first, expand to 100+ once you understand patterns
2. **Layer Analysis:** Hide/show entity types to see different "layers" of the ecosystem
3. **Path Finding:** Use `MATCH path = (a)-[*1..3]-(b)` to find connections between specific nodes
4. **Text Search:** Use `WHERE e.name CONTAINS 'keyword'` to find specific entities
5. **Export Insights:** Take screenshots of interesting patterns for reports

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Too many nodes | Reduce LIMIT or add more WHERE filters |
| No relationships shown | Some nodes might be isolated (no connections) |
| Can't find specific system | Try partial name match: `WHERE e.name CONTAINS 'partial'` |
| Graph is messy | Try different layout algorithms or hide less relevant node types |
| Query too slow | Add more specific WHERE clauses, reduce LIMIT |

---

## 📞 Quick Reference

**Databases:**
- PostgreSQL: `psql -U postgres -d comversa_rag`
- Neo4j CLI: `cypher-shell -u neo4j -p comversa_neo4j_2025`
- Neo4j Browser: http://localhost:7474

**Key Fields:**
- `entity_type`: Type of entity (system, process, etc.)
- `name`: Entity name/description
- `source_count`: How many times mentioned (higher = more important)
- `employee_company`: Tagged organization (sparse data)
- `consensus_confidence`: Quality score (most are 1.0)

**Useful Cypher Patterns:**
```cypher
// Find by name
MATCH (e:Entity) WHERE e.name CONTAINS 'search_term' RETURN e

// Find by type
MATCH (e:Entity {entity_type: 'type_name'}) RETURN e

// Find relationships
MATCH (a)-[r]-(b) WHERE ... RETURN a, r, b

// Count by type
MATCH (e:Entity) RETURN e.entity_type, count(e) ORDER BY count(e) DESC
```
