# Ecosystem Exploration Queries

**Database Status:**
- ✅ PostgreSQL: Running (1,743 consolidated entities)
- ✅ Neo4j: Running (1,790 total nodes)
  - 1,743 Entity nodes (13 types)
  - 44 Employee nodes
  - 3 Organization nodes
- ✅ Relationships: 567 total (12 types)
- 🌐 Neo4j Browser: [http://localhost:7474](http://localhost:7474)
  - Username: `neo4j`
  - Password: `comversa_neo4j_2025`

**Actual Relationship Types:**
| Relationship | Count | Pattern |
|--------------|-------|---------|
| USES | 188 | process → system |
| INVOLVES | 119 | automation_candidate → system |
| FLOWS_FROM | 91 | data_flow → system |
| MENTIONED | 52 | Employee → Entity |
| WORKS_FOR | 44 | Employee → Organization |
| AFFECTS | 23 | inefficiency → process |
| FOLLOWS | 16 | temporal_pattern → process |
| GATES | 10 | decision_point → process |
| BREAKS | 10 | failure_mode → process |
| IMPROVES | 7 | automation_candidate → process |
| DEPENDS_ON | 4 | process → process |
| MOVES | 3 | automation_candidate → kpi |

---

## 1. Platform/System Ecosystem Overview

### View All Systems and Their Connections
```cypher
// Graphical view of all systems and their relationships
MATCH (s:Entity)
WHERE s.entity_type = 'system'
OPTIONAL MATCH (s)-[r]-(connected)
RETURN s, r, connected
LIMIT 100
```

### Systems with Usage Statistics
```cypher
// Systems ranked by number of connections (most critical)
MATCH (s:Entity)
WHERE s.entity_type = 'system'
OPTIONAL MATCH (s)-[r]-()
WITH s, count(r) as connection_count
RETURN
  s.name as system_name,
  coalesce(s.company, s.org_id, 'Unknown') as company,
  connection_count,
  s.source_count as mentioned_in_interviews,
  s.consensus_confidence as confidence
ORDER BY connection_count DESC
LIMIT 20
```

### Most Used Systems (Process → USES → System)
```cypher
// Systems most frequently used by processes
MATCH (process:Entity)-[r:USES]->(system:Entity)
WHERE process.entity_type = 'process' AND system.entity_type = 'system'
WITH system, count(r) as usage_count, collect(DISTINCT process.name) as used_by_processes
RETURN
  system.name as system_name,
  coalesce(system.company, system.org_id, 'Unknown') as company,
  usage_count,
  system.source_count as mentioned_in_interviews,
  size(used_by_processes) as process_count
ORDER BY usage_count DESC
LIMIT 20
```

---

## 2. Employees and Organizations

### Employee → Organization Network
```cypher
// Visualize employees and their companies
MATCH (emp:Employee)-[r:WORKS_FOR]->(org:Organization)
RETURN emp, r, org
LIMIT 50
```

### Employees by Organization
```cypher
// Employee breakdown by company
MATCH (emp:Employee)-[r:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  count(emp) as employee_count,
  collect(emp.name)[0..5] as sample_employees
ORDER BY employee_count DESC
```

### Employee Mentions (What Employees Talk About)
```cypher
// Entities mentioned by employees (from interviews)
MATCH (emp:Employee)-[r:MENTIONED]->(entity:Entity)
RETURN
  emp.name as employee,
  emp.role as role,
  entity.entity_type as mentioned_entity_type,
  entity.name as mentioned_entity,
  coalesce(entity.company, entity.org_id, 'Unknown') as entity_company
LIMIT 50
```

### Team Structures
```cypher
// Team structure entities in the knowledge graph
MATCH (team:Entity)
WHERE team.entity_type = 'team_structure'
OPTIONAL MATCH (team)-[r]-(related)
RETURN team, r, related
LIMIT 50
```

---

## 3. Processes and Their Impact

### Process → USES → System Network
```cypher
// Visualize which processes use which systems (188 relationships)
MATCH (process:Entity)-[r:USES]->(system:Entity)
WHERE process.entity_type = 'process' AND system.entity_type = 'system'
RETURN process, r, system
LIMIT 100
```

### Process Dependencies (Process → DEPENDS_ON → Process)
```cypher
// Process dependency chains (4 relationships)
MATCH path = (p1:Entity)-[:DEPENDS_ON*1..3]->(p2:Entity)
WHERE p1.entity_type = 'process' AND p2.entity_type = 'process'
RETURN path
LIMIT 20
```

### Inefficiency → AFFECTS → Process
```cypher
// Inefficiencies affecting processes (23 relationships)
MATCH (inefficiency:Entity)-[r:AFFECTS]->(process:Entity)
WHERE inefficiency.entity_type = 'inefficiency' AND process.entity_type = 'process'
RETURN
  process.organization as company,
  process.name as process_name,
  inefficiency.name as inefficiency_description,
  inefficiency.consensus_confidence as confidence
ORDER BY process.organization, confidence DESC
```

### Failure Modes Breaking Processes
```cypher
// Failure modes that break processes (10 relationships)
MATCH (failure:Entity)-[r:BREAKS]->(process:Entity)
WHERE failure.entity_type = 'failure_mode' AND process.entity_type = 'process'
RETURN
  process.organization as company,
  process.name as process_name,
  failure.name as failure_mode,
  failure.consensus_confidence as risk_level
ORDER BY risk_level DESC
```

### Decision Points Gating Processes
```cypher
// Decision points that gate processes (10 relationships)
MATCH (decision:Entity)-[r:GATES]->(process:Entity)
WHERE decision.entity_type = 'decision_point' AND process.entity_type = 'process'
RETURN
  process.organization as company,
  process.name as process_name,
  decision.name as decision_point
LIMIT 20
```

---

## 4. Company & Holdings Clustering

### Entity Breakdown by Organization
```cypher
// Count entities by type and organization
MATCH (e:Entity)
WHERE e.organization IS NOT NULL
RETURN
  e.organization as company,
  e.entity_type as type,
  count(e) as count
ORDER BY company, count DESC
```

### Visualize Company Ecosystem (Los Tajibos)
```cypher
// Complete ecosystem view for Los Tajibos
MATCH (e:Entity)
WHERE e.organization = 'Los Tajibos'
OPTIONAL MATCH (e)-[r]-(connected:Entity)
WHERE connected.organization = 'Los Tajibos'
RETURN e, r, connected
LIMIT 200
```

### Visualize Company Ecosystem (Comversa)
```cypher
// Complete ecosystem view for Comversa
MATCH (e:Entity)
WHERE e.organization = 'Comversa'
OPTIONAL MATCH (e)-[r]-(connected:Entity)
WHERE connected.organization = 'Comversa'
RETURN e, r, connected
LIMIT 200
```

### Visualize Company Ecosystem (Bolivian Foods)
```cypher
// Complete ecosystem view for Bolivian Foods
MATCH (e:Entity)
WHERE e.organization = 'Bolivian Foods'
OPTIONAL MATCH (e)-[r]-(connected:Entity)
WHERE connected.organization = 'Bolivian Foods'
RETURN e, r, connected
LIMIT 200
```

### Cross-Company Shared Systems
```cypher
// Systems used by multiple organizations (holding-level infrastructure)
MATCH (s:Entity)
WHERE s.entity_type = 'System'
WITH s, collect(DISTINCT s.organization) as orgs
WHERE size(orgs) > 1
RETURN
  s.name as system_name,
  orgs as used_by_companies,
  s.source_count as mentioned_times
ORDER BY size(orgs) DESC, s.source_count DESC
```

### Holdings Overview (All Companies)
```cypher
// Compare all three organizations side-by-side
MATCH (e:Entity)
WITH e.organization as company, e.entity_type as type, count(e) as count
RETURN company, collect({type: type, count: count}) as entity_breakdown
ORDER BY company
```

---

## 5. Advanced Exploration Queries

### Critical Path Analysis
```cypher
// Find highly connected entities (potential bottlenecks)
MATCH (e:Entity)-[r]-()
WITH e, count(r) as degree
WHERE degree > 5
RETURN
  e.entity_type as type,
  e.name as name,
  e.organization as company,
  degree as connections,
  e.consensus_confidence as confidence
ORDER BY degree DESC
LIMIT 30
```

### Automation Opportunities (Automation → IMPROVES → Process)
```cypher
// Automation candidates that improve processes (7 relationships)
MATCH (automation:Entity)-[r:IMPROVES]->(process:Entity)
WHERE automation.entity_type = 'automation_candidate' AND process.entity_type = 'process'
RETURN
  process.organization as company,
  process.name as process_name,
  automation.name as automation_opportunity,
  automation.consensus_confidence as feasibility
ORDER BY feasibility DESC
```

### Automation → INVOLVES → System Network
```cypher
// Automation candidates and systems they involve (119 relationships)
MATCH (automation:Entity)-[r:INVOLVES]->(system:Entity)
WHERE automation.entity_type = 'automation_candidate' AND system.entity_type = 'system'
RETURN automation, r, system
LIMIT 50
```

### Automation Impact on KPIs (Automation → MOVES → KPI)
```cypher
// Automation candidates that impact KPIs (3 relationships)
MATCH (automation:Entity)-[r:MOVES]->(kpi:Entity)
WHERE automation.entity_type = 'automation_candidate' AND kpi.entity_type = 'kpi'
RETURN
  automation.organization as company,
  automation.name as automation_opportunity,
  kpi.name as impacted_kpi,
  automation.consensus_confidence as confidence
ORDER BY confidence DESC
```

### Data Flow Analysis (Data → FLOWS_FROM → System)
```cypher
// Data flows originating from systems (91 relationships)
MATCH (data_flow:Entity)-[r:FLOWS_FROM]->(system:Entity)
WHERE data_flow.entity_type = 'data_flow' AND system.entity_type = 'system'
RETURN
  system.organization as company,
  system.name as source_system,
  data_flow.name as data_flow_description,
  data_flow.consensus_confidence as confidence
ORDER BY company, confidence DESC
LIMIT 30
```

### Temporal Patterns (Pattern → FOLLOWS → Process)
```cypher
// Time-based patterns following processes (16 relationships)
MATCH (pattern:Entity)-[r:FOLLOWS]->(process:Entity)
WHERE pattern.entity_type = 'temporal_pattern' AND process.entity_type = 'process'
RETURN
  process.organization as company,
  process.name as process_name,
  pattern.name as temporal_pattern,
  pattern.consensus_confidence as confidence
ORDER BY company, confidence DESC
LIMIT 30
```

### Knowledge Gaps
```cypher
// Knowledge gaps in the organization
MATCH (gap:Entity)
WHERE gap.entity_type = 'knowledge_gap'
OPTIONAL MATCH (gap)-[r]-(related)
RETURN gap, r, related
LIMIT 50
```

---

## 6. Entity Type Explorer

### All Entity Types with Counts
```cypher
// Complete breakdown of entity types
MATCH (e:Entity)
RETURN
  e.entity_type as entity_type,
  count(e) as count,
  avg(e.consensus_confidence) as avg_confidence,
  max(e.source_count) as max_mentions
ORDER BY count DESC
```

### Explore Specific Entity Types

**Communication Channels (232 nodes):**
```cypher
MATCH (c:Entity)
WHERE c.entity_type = 'communication_channel'
OPTIONAL MATCH (c)-[r]-(related)
RETURN c, r, related
LIMIT 50
```

**Success Patterns (172 nodes):**
```cypher
MATCH (s:Entity)
WHERE s.entity_type = 'success_pattern'
OPTIONAL MATCH (s)-[r]-(related)
RETURN s, r, related
LIMIT 50
```

**Pain Points (11 nodes - high value!):**
```cypher
MATCH (pain:Entity)
WHERE pain.entity_type = 'pain_point'
RETURN
  pain.organization as company,
  pain.name as pain_point,
  pain.source_count as mentioned_times,
  pain.consensus_confidence as confidence
ORDER BY pain.source_count DESC
```

**External Dependencies (8 nodes):**
```cypher
MATCH (dep:Entity)
WHERE dep.entity_type = 'external_dependency'
OPTIONAL MATCH (dep)-[r]-(related)
RETURN dep, r, related
```

### Multi-Hop Path Exploration
```cypher
// Explore indirect relationships (2-3 hops)
MATCH path = (start:Entity)-[*2..3]-(end:Entity)
WHERE start.entity_type = 'process'
  AND end.entity_type = 'kpi'
  AND start.organization = end.organization
RETURN path
LIMIT 20
```

---

## 7. PostgreSQL Complementary Queries

Run these in PostgreSQL to get detailed data:

```sql
-- Entity Type Distribution (1,743 total entities)
SELECT
  entity_type,
  organization,
  COUNT(*) as count,
  AVG(consensus_confidence) as avg_confidence,
  MAX(source_count) as max_mentions
FROM consolidated_entities
GROUP BY entity_type, organization
ORDER BY organization, count DESC;

-- High-Confidence Systems
SELECT
  name,
  organization,
  payload->>'description' as description,
  source_count,
  consensus_confidence
FROM consolidated_entities
WHERE entity_type = 'system'
  AND consensus_confidence > 0.85
ORDER BY source_count DESC
LIMIT 20;

-- Pain Points Analysis (11 total - high value entities!)
SELECT
  ce.organization,
  ce.name as pain_point,
  ce.payload->>'severity' as severity,
  ce.source_count,
  ce.consensus_confidence
FROM consolidated_entities ce
WHERE ce.entity_type = 'pain_point'
ORDER BY ce.source_count DESC, ce.consensus_confidence DESC;

-- Automation Opportunities
SELECT
  ce.organization,
  ce.name as automation_candidate,
  ce.payload->>'estimated_impact' as impact,
  ce.source_count,
  ce.consensus_confidence
FROM consolidated_entities ce
WHERE ce.entity_type = 'automation_candidate'
ORDER BY ce.consensus_confidence DESC
LIMIT 20;

-- Process Inventory by Organization
SELECT
  organization,
  COUNT(*) as process_count,
  AVG(consensus_confidence) as avg_confidence
FROM consolidated_entities
WHERE entity_type = 'process'
GROUP BY organization
ORDER BY process_count DESC;
```

---

## Best Practices for Graphical Exploration

### In Neo4j Browser:

1. **Start Small:** Begin with LIMIT 50, then expand as needed
2. **Use Filters:** Click on node types in the sidebar to show/hide
3. **Expand Nodes:** Double-click nodes to see their connections
4. **Layouts:** Try different graph layouts (force-directed, hierarchical)
5. **Colors:** Nodes are colored by entity_type automatically
6. **Save Views:** Bookmark interesting queries

### Recommended Exploration Flow:

1. **Graph Overview** → Run "All Entity Types with Counts" to understand structure
2. **Employee Network** → Run "Employee → Organization Network" to see organizational structure
3. **Company Ecosystems** → Run company-specific ecosystem queries (Los Tajibos, Comversa, Bolivian Foods)
4. **Process-System Mapping** → Run "Process → USES → System Network" to see core operations
5. **Automation Opportunities** → Run automation queries to identify improvement areas
6. **Problem Analysis** → Run "Inefficiency → AFFECTS → Process" and failure mode queries
7. **Data Flows** → Run "Data → FLOWS_FROM → System" to understand information movement
8. **Cross-Company Analysis** → Run "Cross-Company Shared Systems" to identify shared infrastructure

### Visualization Tips:

- **Large graphs:** Use `LIMIT` and filters to focus
- **Entity types as layers:** Filter by type to see patterns
- **Relationship types:** Color-code relationships for clarity
- **Company clustering:** Use organization field to group visually

---

## Quick Start Commands

### Terminal (PostgreSQL):
```bash
psql -U postgres -d comversa_rag
```

### Terminal (Neo4j):
```bash
export NEO4J_PASSWORD=comversa_neo4j_2025
cypher-shell -u neo4j -p "$NEO4J_PASSWORD"
```

### Browser (Neo4j Visual Interface):
Open: http://localhost:7474
- Username: `neo4j`
- Password: `comversa_neo4j_2025`
