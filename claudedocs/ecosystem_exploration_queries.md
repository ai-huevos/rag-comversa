# Ecosystem Exploration Queries

**Database Status:**
- ✅ PostgreSQL: Running (1,743 consolidated entities)
- ✅ Neo4j: Running (1,743 nodes)
- 🌐 Neo4j Browser: [http://localhost:7474](http://localhost:7474)
  - Username: `neo4j`
  - Password: `comversa_neo4j_2025`

---

## 1. Platform/System Ecosystem Overview

### View All Systems and Their Connections
```cypher
// Graphical view of all systems and their relationships
MATCH (s:Entity)
WHERE s.entity_type = 'System'
OPTIONAL MATCH (s)-[r]-(connected)
RETURN s, r, connected
LIMIT 100
```

### Systems with Usage Statistics
```cypher
// Systems ranked by number of connections (most critical)
MATCH (s:Entity)
WHERE s.entity_type = 'System'
OPTIONAL MATCH (s)-[r]-()
WITH s, count(r) as connection_count
RETURN
  s.name as system_name,
  s.organization as company,
  connection_count,
  s.source_count as mentioned_in_interviews,
  s.consensus_confidence as confidence
ORDER BY connection_count DESC
LIMIT 20
```

### System Dependencies Network
```cypher
// Visualize how systems depend on each other
MATCH path = (s1:Entity)-[:DEPENDS_ON|INTEGRATES_WITH*1..2]-(s2:Entity)
WHERE s1.entity_type = 'System' AND s2.entity_type = 'System'
RETURN path
LIMIT 50
```

---

## 2. Actors Who Use Systems

### People and Their Systems
```cypher
// Show which people use which systems
MATCH (person:Entity)-[r:USES|MANAGES|ADMINISTERS]-(system:Entity)
WHERE person.entity_type IN ['Person', 'TeamStructure']
  AND system.entity_type = 'System'
RETURN person, r, system
LIMIT 50
```

### Most Active Users/Teams
```cypher
// Teams or people with most system interactions
MATCH (actor:Entity)-[r]-(system:Entity)
WHERE actor.entity_type IN ['Person', 'TeamStructure']
  AND system.entity_type = 'System'
WITH actor, count(DISTINCT system) as systems_used
RETURN
  actor.name as actor_name,
  actor.entity_type as actor_type,
  actor.organization as company,
  systems_used
ORDER BY systems_used DESC
LIMIT 20
```

---

## 3. Processes Being Impacted

### Processes Connected to Systems
```cypher
// Visualize which processes use which systems
MATCH (process:Entity)-[r]-(system:Entity)
WHERE process.entity_type = 'Process'
  AND system.entity_type = 'System'
RETURN process, r, system
LIMIT 100
```

### Process-System-Pain Point Triangle
```cypher
// Show relationships between processes, systems, and problems
MATCH path = (process:Entity)-[:USES]-(system:Entity)-[:CAUSES]-(pain:Entity)
WHERE process.entity_type = 'Process'
  AND system.entity_type = 'System'
  AND pain.entity_type = 'PainPoint'
RETURN path
LIMIT 50
```

### Process Inefficiencies by Organization
```cypher
// Inefficient processes grouped by company
MATCH (process:Entity)-[r:HAS_INEFFICIENCY]-(inefficiency:Entity)
WHERE process.entity_type = 'Process'
  AND inefficiency.entity_type = 'Inefficiency'
RETURN
  process.organization as company,
  process.name as process_name,
  inefficiency.name as inefficiency,
  inefficiency.consensus_confidence as confidence
ORDER BY process.organization, confidence DESC
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

### Automation Opportunities
```cypher
// Systems with automation candidates
MATCH (system:Entity)-[r:CAN_AUTOMATE]-(automation:Entity)
WHERE system.entity_type = 'System'
  AND automation.entity_type = 'AutomationCandidate'
RETURN system, r, automation
LIMIT 50
```

### Knowledge Gaps in Systems
```cypher
// Areas where documentation/training is needed
MATCH (system:Entity)-[r:HAS_GAP]-(gap:Entity)
WHERE system.entity_type = 'System'
  AND gap.entity_type = 'KnowledgeGap'
RETURN
  system.organization as company,
  system.name as system,
  gap.name as knowledge_gap,
  gap.consensus_confidence as urgency
ORDER BY company, urgency DESC
```

### Temporal Patterns (When Things Happen)
```cypher
// Time-based patterns in processes/systems
MATCH (e:Entity)
WHERE e.entity_type = 'TemporalPattern'
OPTIONAL MATCH (e)-[r]-(related)
RETURN e, r, related
LIMIT 50
```

---

## 6. PostgreSQL Complementary Queries

Run these in PostgreSQL to get detailed data:

```sql
-- Entity Type Distribution
SELECT
  entity_type,
  organization,
  COUNT(*) as count,
  AVG(consensus_confidence) as avg_confidence
FROM consolidated_entities
GROUP BY entity_type, organization
ORDER BY organization, count DESC;

-- High-Confidence Systems
SELECT
  name,
  organization,
  metadata->>'description' as description,
  source_count,
  consensus_confidence
FROM consolidated_entities
WHERE entity_type = 'System'
  AND consensus_confidence > 0.85
ORDER BY source_count DESC
LIMIT 20;

-- Pain Points with Solutions
SELECT
  ce.organization,
  ce.name as pain_point,
  ce.metadata->>'severity' as severity,
  ce.source_count
FROM consolidated_entities ce
WHERE ce.entity_type = 'PainPoint'
ORDER BY ce.organization, ce.source_count DESC;
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

1. **Company Overview** → Run holdings overview query
2. **System Mapping** → Run system ecosystem query for each company
3. **Process Analysis** → Run process-system connections
4. **Actor Identification** → Run people/teams using systems
5. **Pain Points** → Run process inefficiencies by organization
6. **Cross-Company** → Run shared systems query

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
