# Working Neo4j Queries (Without Entity Relationships)

**Status:** These queries work NOW with the current data structure
**Limitation:** No Entity↔Entity relationships exist yet

---

## 🎯 High-Value Queries That Work

### 1. Automation Opportunities (BEST DATA AVAILABLE)

```cypher
// Top automation opportunities with impact scores
MATCH (auto:Entity {entity_type: 'automation_candidate'})
WHERE auto.impact_score IS NOT NULL
OPTIONAL MATCH (emp:Employee)-[:MENTIONED]->(auto)
RETURN
  auto.name as opportunity,
  auto.company as company,
  auto.process as process_to_improve,
  auto.systems_involved as systems_needed,
  auto.impact_score as impact,
  auto.effort_estimate as effort,
  collect(DISTINCT emp.full_name) as champions
ORDER BY auto.impact_score DESC, auto.effort_estimate ASC
LIMIT 20
```

**What This Shows:**
- Automation ideas with highest ROI
- Which systems are involved
- Who's championing each idea
- Process context

---

### 2. Systems by Company (Property-Based)

```cypher
// List all systems mentioned by employees per company
MATCH (emp:Employee)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  sys.name as system,
  count(DISTINCT emp) as employee_mentions,
  collect(DISTINCT emp.full_name) as users
ORDER BY company, employee_mentions DESC
```

---

### 3. Employee Innovation Dashboard

```cypher
// Find innovation champions by company
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
OPTIONAL MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
WITH
  org.name as company,
  emp.full_name as employee,
  emp.role as role,
  emp.gc_profile as profile,
  emp.score_game_changer as innovation_score,
  count(DISTINCT auto) as automation_ideas,
  count(DISTINCT sys) as systems_mentioned
WHERE automation_ideas > 0 OR systems_mentioned > 0
RETURN
  company,
  employee,
  role,
  profile,
  innovation_score,
  automation_ideas,
  systems_mentioned
ORDER BY company, innovation_score DESC, automation_ideas DESC
```

---

### 4. KPI Tracking by Company

```cypher
// Show KPIs mentioned by employees
MATCH (emp:Employee)-[:MENTIONED]->(kpi:Entity {entity_type: 'kpi'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  kpi.name as kpi_name,
  collect(DISTINCT emp.full_name) as tracked_by,
  count(DISTINCT emp) as employee_count
ORDER BY company, employee_count DESC
```

---

### 5. Process Inefficiencies

```cypher
// Find inefficiencies with context from properties
MATCH (ineff:Entity {entity_type: 'inefficiency'})
OPTIONAL MATCH (emp:Employee)-[:MENTIONED]->(ineff)
RETURN
  ineff.name as inefficiency,
  ineff.process as affected_process,
  ineff.systems_involved as problem_systems,
  ineff.company as company,
  collect(emp.full_name) as reported_by
ORDER BY size(ineff.systems_involved) DESC
```

---

### 6. Success Patterns (What Works Well)

```cypher
// See what's working well
MATCH (success:Entity {entity_type: 'success_pattern'})
OPTIONAL MATCH (emp:Employee)-[:MENTIONED]->(success)
WHERE emp IS NOT NULL
RETURN
  success.name as success_story,
  success.company as company,
  success.process as successful_process,
  collect(emp.full_name) as mentioned_by
LIMIT 20
```

---

### 7. Communication Channels by Company

```cypher
// How teams communicate
MATCH (emp:Employee)-[:MENTIONED]->(comm:Entity {entity_type: 'communication_channel'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  comm.name as channel,
  count(DISTINCT emp) as users
ORDER BY company, users DESC
```

---

### 8. Company Comparison Dashboard

```cypher
// Compare all three companies
MATCH (org:Organization)<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
OPTIONAL MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
OPTIONAL MATCH (emp)-[:MENTIONED]->(kpi:Entity {entity_type: 'kpi'})
WITH
  org.name as company,
  count(DISTINCT emp) as employees,
  avg(emp.score_game_changer) as avg_innovation,
  avg(emp.score_strategist) as avg_strategy,
  count(DISTINCT sys) as unique_systems,
  count(DISTINCT auto) as automation_ideas,
  count(DISTINCT kpi) as kpis_tracked
RETURN
  company,
  employees,
  round(avg_innovation * 10) / 10 as innovation_score,
  round(avg_strategy * 10) / 10 as strategy_score,
  unique_systems,
  automation_ideas,
  kpis_tracked
ORDER BY company
```

---

### 9. High-Impact Game Changers

```cypher
// Innovation leaders with their ideas
MATCH (emp:Employee)
WHERE emp.score_game_changer >= 5
OPTIONAL MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
OPTIONAL MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  emp.full_name as innovator,
  emp.role as role,
  emp.score_game_changer as innovation_score,
  emp.gc_profile as profile,
  collect(auto.name)[0..3] as automation_ideas
ORDER BY innovation_score DESC
```

---

### 10. Systems Involved in Automation

```cypher
// Which systems are part of automation plans
MATCH (auto:Entity {entity_type: 'automation_candidate'})
WHERE auto.systems_involved IS NOT NULL
UNWIND auto.systems_involved as system_name
RETURN
  system_name,
  count(auto) as automation_mentions,
  collect(DISTINCT auto.name)[0..3] as example_automations
ORDER BY automation_mentions DESC
LIMIT 20
```

---

## 📊 Visualization-Friendly Queries

### Company Ecosystem View

```cypher
// Visual org chart with entities
MATCH (org:Organization {name: 'COMVERSA'})<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
WHERE entity.entity_type IN ['system', 'automation_candidate', 'kpi']
RETURN org, emp, entity
LIMIT 100
```

### Innovation Network

```cypher
// Employees connected through automation ideas
MATCH (emp:Employee)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
WHERE auto.impact_score >= 4
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN emp, auto, org
LIMIT 50
```

### System Users

```cypher
// See who uses which systems
MATCH (emp:Employee)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN emp, sys, org
LIMIT 100
```

---

## 🎨 PostgreSQL Queries for Detailed Analysis

When Neo4j graph visualization isn't enough, use PostgreSQL for detailed data:

```sql
-- Automation opportunities ranked by impact
SELECT
  ce.name as opportunity,
  ce.payload->>'company' as company,
  ce.payload->>'process' as process,
  ce.payload->>'systems_involved' as systems,
  (ce.payload->>'impact_score')::int as impact,
  (ce.payload->>'effort_estimate')::text as effort,
  e.full_name as champion
FROM consolidated_entities ce
LEFT JOIN employees e ON ce.employee_id = e.employee_id
WHERE ce.entity_type = 'automation_candidate'
  AND ce.payload->>'impact_score' IS NOT NULL
ORDER BY (ce.payload->>'impact_score')::int DESC
LIMIT 20;
```

```sql
-- Systems by company with user counts
SELECT
  e.company,
  ce.name as system,
  COUNT(DISTINCT e.employee_id) as users,
  string_agg(DISTINCT e.full_name, ', ') as user_list
FROM consolidated_entities ce
JOIN employees e ON ce.employee_id = e.employee_id
WHERE ce.entity_type = 'system'
GROUP BY e.company, ce.name
ORDER BY e.company, users DESC;
```

```sql
-- Innovation champions
SELECT
  e.company,
  e.full_name,
  e.role,
  e.gc_profile,
  e.score_game_changer,
  COUNT(DISTINCT ce.id) FILTER (WHERE ce.entity_type = 'automation_candidate') as automation_ideas,
  COUNT(DISTINCT ce.id) FILTER (WHERE ce.entity_type = 'system') as systems_mentioned
FROM employees e
LEFT JOIN consolidated_entities ce ON e.employee_id = ce.employee_id
GROUP BY e.employee_id, e.company, e.full_name, e.role, e.gc_profile, e.score_game_changer
HAVING COUNT(DISTINCT ce.id) > 0
ORDER BY e.company, e.score_game_changer DESC;
```

---

## ⚠️ What Still Won't Work

These queries require Entity↔Entity relationships (not yet available):

```cypher
// ❌ Won't work - no CAUSED_BY relationships
MATCH (pain:Entity {entity_type: 'pain_point'})-[:CAUSED_BY]->(sys:Entity)
RETURN pain, sys

// ❌ Won't work - no USES relationships
MATCH (proc:Entity {entity_type: 'process'})-[:USES]->(sys:Entity)
RETURN proc, sys

// ❌ Won't work - no IMPROVES relationships
MATCH (auto:Entity)-[:IMPROVES]->(proc:Entity)
RETURN auto, proc
```

**Workaround:** Use property-based queries (examples above) until relationships are created.

---

## 🚀 Next Step: Create Relationships

To make the graph fully connected, we need to:
1. **Infer relationships from properties** (quick fix - 1-2 hours)
2. **Add relationship extraction to pipeline** (long-term - next sprint)

See [neo4j_data_structure_analysis.md](neo4j_data_structure_analysis.md) for implementation details.
