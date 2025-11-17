# Ecosystem Analysis: Platforms, Actors, Processes & Companies

**Updated:** November 14, 2025
**Status:** ✅ Employee data synced to Neo4j (44 employees, 3 organizations)

---

## 🎯 Your Questions Answered

### 1. The Platform/System Ecosystem

**What systems exist and how they connect**

```cypher
// Complete system ecosystem with connections
MATCH (s:Entity {entity_type: 'system'})
OPTIONAL MATCH (s)-[r]-(connected)
RETURN s, r, connected
LIMIT 200
```

**Systems clustered by organization**

```cypher
// Systems grouped by company (using Employee connections)
MATCH (emp:Employee)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN org, sys, emp
LIMIT 100
```

**Critical systems (most connected)**

```cypher
// Find highly-connected systems (potential bottlenecks)
MATCH (s:Entity {entity_type: 'system'})
OPTIONAL MATCH (s)-[r]-()
WITH s, count(r) as connection_count
WHERE connection_count > 0
RETURN
  s.name as system_name,
  s.source_count as mentions,
  connection_count as total_connections
ORDER BY connection_count DESC, s.source_count DESC
LIMIT 20
```

---

### 2. What Actors Use Them

**Employees and their systems**

```cypher
// Visualize employees and systems they mention
MATCH (emp:Employee)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
RETURN emp, sys
LIMIT 50
```

**Employees by company with their tech stack**

```cypher
// See what systems each company's employees use
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
RETURN
  org.name as company,
  emp.full_name as employee,
  emp.role as role,
  emp.gc_profile as profile,
  collect(DISTINCT sys.name)[0..5] as systems_mentioned
ORDER BY company, employee
```

**High-impact employees (Game Changers & Strategists)**

```cypher
// Find innovation leaders and strategic thinkers
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
WHERE emp.score_game_changer >= 5 OR emp.score_strategist >= 10
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN
  org.name as company,
  emp.full_name as employee,
  emp.role as role,
  emp.gc_profile as profile,
  emp.score_game_changer as innovation_score,
  emp.score_strategist as strategy_score,
  count(DISTINCT entity) as total_mentions
ORDER BY company, innovation_score DESC, strategy_score DESC
```

**Team composition by GC profiles**

```cypher
// Understand team dynamics by GC Index profiles
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
WITH org.name as company,
     collect({
       name: emp.full_name,
       role: emp.role,
       profile: emp.gc_profile,
       game_changer: emp.score_game_changer,
       strategist: emp.score_strategist,
       implementer: emp.score_implementer
     }) as team_members
RETURN
  company,
  size(team_members) as team_size,
  team_members
ORDER BY company
```

---

### 3. What Processes Are Being Impacted

**Processes and the systems they use**

```cypher
// Map process-system dependencies
MATCH (proc:Entity {entity_type: 'process'})-[r]-(sys:Entity {entity_type: 'system'})
RETURN proc, r, sys
LIMIT 100
```

**Processes with pain points and failures**

```cypher
// See which processes have problems
MATCH (proc:Entity {entity_type: 'process'})
OPTIONAL MATCH (proc)-[r1]-(pain:Entity {entity_type: 'pain_point'})
OPTIONAL MATCH (proc)-[r2]-(failure:Entity {entity_type: 'failure_mode'})
OPTIONAL MATCH (proc)-[r3]-(inefficiency:Entity {entity_type: 'inefficiency'})
RETURN proc, r1, pain, r2, failure, r3, inefficiency
LIMIT 50
```

**Processes with automation potential**

```cypher
// Find processes that could be automated
MATCH (proc:Entity {entity_type: 'process'})-[r]-(auto:Entity {entity_type: 'automation_candidate'})
RETURN proc, r, auto
LIMIT 50
```

**Process owners (who mentioned which processes)**

```cypher
// Link employees to the processes they mentioned
MATCH (emp:Employee)-[:MENTIONED]->(proc:Entity {entity_type: 'process'})
MATCH (emp)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  emp.full_name as employee,
  emp.role as role,
  proc.name as process,
  proc.source_count as process_mentions
ORDER BY company, employee
```

---

### 4. Cluster Them by Companies and Holdings

**Complete company ecosystem view**

```cypher
// Everything related to one company
MATCH (org:Organization {name: 'COMVERSA'})
MATCH (emp:Employee)-[:WORKS_FOR]->(org)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN org, emp, entity
LIMIT 200
```

```cypher
// Los Tajibos ecosystem
MATCH (org:Organization {name: 'LOS TAJIBOS'})
MATCH (emp:Employee)-[:WORKS_FOR]->(org)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN org, emp, entity
LIMIT 200
```

```cypher
// Bolivian Foods ecosystem
MATCH (org:Organization {name: 'BOLIVIAN FOODS'})
MATCH (emp:Employee)-[:WORKS_FOR]->(org)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN org, emp, entity
LIMIT 200
```

**Holdings overview (all three companies)**

```cypher
// See all organizations, their employees, and key entities
MATCH (org:Organization)
OPTIONAL MATCH (org)<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
WHERE entity.entity_type IN ['system', 'process', 'pain_point', 'automation_candidate']
RETURN org, emp, entity
LIMIT 300
```

**Company comparison dashboard**

```cypher
// Compare companies side-by-side
MATCH (org:Organization)
OPTIONAL MATCH (org)<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
OPTIONAL MATCH (emp)-[:MENTIONED]->(pain:Entity {entity_type: 'pain_point'})
OPTIONAL MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
WITH
  org.name as company,
  count(DISTINCT emp) as employee_count,
  avg(emp.score_game_changer) as avg_innovation,
  avg(emp.score_strategist) as avg_strategy,
  count(DISTINCT sys) as systems_count,
  count(DISTINCT pain) as pain_points,
  count(DISTINCT auto) as automation_ideas
RETURN
  company,
  employee_count,
  round(avg_innovation * 10) / 10 as avg_innovation_score,
  round(avg_strategy * 10) / 10 as avg_strategy_score,
  systems_count,
  pain_points,
  automation_ideas
ORDER BY company
```

**Cross-company shared entities**

```cypher
// Find systems/processes used across multiple companies
MATCH (emp1:Employee)-[:WORKS_FOR]->(org1:Organization)
MATCH (emp2:Employee)-[:WORKS_FOR]->(org2:Organization)
MATCH (emp1)-[:MENTIONED]->(entity:Entity)<-[:MENTIONED]-(emp2)
WHERE org1.name < org2.name  // Avoid duplicates
  AND entity.entity_type IN ['system', 'process']
RETURN
  org1.name as company1,
  org2.name as company2,
  entity.entity_type as type,
  entity.name as shared_entity,
  count(*) as shared_mentions
ORDER BY shared_mentions DESC
LIMIT 30
```

---

## 🎨 Best Visualization Approaches

### For Neo4j Browser (Graphical)

1. **Org Chart with Tech Stack**
```cypher
// Beautiful org visualization
MATCH (org:Organization)<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
RETURN org, emp, sys
LIMIT 100
```

**Customize in Neo4j Browser:**
- Node size: By `score_game_changer` (innovation potential)
- Node color: Already colored by label (Employee, Organization, Entity)
- Caption: `full_name` for employees, `name` for entities

2. **Problem-Process-Owner Triangle**
```cypher
// See who owns which processes and their problems
MATCH (emp:Employee)-[:MENTIONED]->(proc:Entity {entity_type: 'process'})
OPTIONAL MATCH (proc)-[r]-(pain:Entity {entity_type: 'pain_point'})
RETURN emp, proc, r, pain
LIMIT 50
```

3. **Innovation Network**
```cypher
// Employees with automation ideas and their companies
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
RETURN org, emp, auto
LIMIT 50
```

---

### For PostgreSQL (Detailed Analysis)

**Company workforce analysis:**
```sql
SELECT
  company,
  COUNT(*) as employees,
  AVG(score_game_changer) as avg_innovation,
  AVG(score_strategist) as avg_strategy,
  AVG(score_implementer) as avg_execution,
  COUNT(*) FILTER (WHERE role ILIKE '%director%') as directors,
  COUNT(*) FILTER (WHERE role ILIKE '%gerente%') as managers
FROM employees
GROUP BY company
ORDER BY company;
```

**Systems by company (via employee mentions):**
```sql
SELECT
  e.company,
  ce.name as system,
  COUNT(DISTINCT e.employee_id) as mentioned_by_employees,
  ce.source_count as total_mentions
FROM consolidated_entities ce
JOIN employees e ON ce.employee_id = e.employee_id
WHERE ce.entity_type = 'system'
GROUP BY e.company, ce.name, ce.source_count
ORDER BY e.company, mentioned_by_employees DESC;
```

**Process ownership map:**
```sql
SELECT
  e.company,
  e.full_name,
  e.role,
  ce.name as process,
  ce.entity_type
FROM consolidated_entities ce
JOIN employees e ON ce.employee_id = e.employee_id
WHERE ce.entity_type = 'process'
ORDER BY e.company, e.full_name;
```

---

## 🎯 Recommended Exploration Path

### Phase 1: High-Level View (Start Here)
```cypher
// 1. See all three organizations
MATCH (org:Organization)
RETURN org

// 2. See organization structure
MATCH (org:Organization)<-[:WORKS_FOR]-(emp:Employee)
RETURN org, emp
LIMIT 100

// 3. Add key systems to the view
MATCH (org:Organization)<-[:WORKS_FOR]-(emp:Employee)
OPTIONAL MATCH (emp)-[:MENTIONED]->(sys:Entity {entity_type: 'system'})
RETURN org, emp, sys
LIMIT 150
```

### Phase 2: Deep Dive by Company
```cypher
// Pick one company and explore deeply
MATCH (org:Organization {name: 'COMVERSA'})
MATCH (emp:Employee)-[:WORKS_FOR]->(org)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN org, emp, entity
LIMIT 200

// Then explore by entity type
MATCH (org:Organization {name: 'COMVERSA'})
MATCH (emp:Employee)-[:WORKS_FOR]->(org)
OPTIONAL MATCH (emp)-[:MENTIONED]->(entity:Entity)
WHERE entity.entity_type IN ['system', 'process', 'pain_point']
RETURN org, emp, entity
```

### Phase 3: Problem & Opportunity Analysis
```cypher
// Pain points across companies
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
MATCH (emp)-[:MENTIONED]->(pain:Entity {entity_type: 'pain_point'})
RETURN org, emp, pain

// Automation opportunities
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
MATCH (emp)-[:MENTIONED]->(auto:Entity {entity_type: 'automation_candidate'})
RETURN org, emp, auto
```

### Phase 4: Strategic Insights
```cypher
// Innovation leaders by company
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
WHERE emp.score_game_changer >= 5
OPTIONAL MATCH (emp)-[:MENTIONED]->(idea:Entity {entity_type: 'automation_candidate'})
RETURN org, emp, idea

// Cross-company shared challenges
MATCH (emp1:Employee)-[:WORKS_FOR]->(org1:Organization)
MATCH (emp2:Employee)-[:WORKS_FOR]->(org2:Organization)
MATCH (emp1)-[:MENTIONED]->(entity:Entity)<-[:MENTIONED]-(emp2)
WHERE org1 <> org2 AND entity.entity_type = 'pain_point'
RETURN org1, org2, entity, emp1, emp2
```

---

## 📊 Quick Stats Available Now

Run these in Neo4j Browser to get instant insights:

```cypher
// Total counts
MATCH (org:Organization) RETURN count(org) as organizations;
MATCH (emp:Employee) RETURN count(emp) as employees;
MATCH (e:Entity) RETURN count(e) as entities;

// Employees per company
MATCH (org:Organization)<-[:WORKS_FOR]-(emp:Employee)
RETURN org.name as company, count(emp) as employees
ORDER BY employees DESC;

// Entity types per company
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
MATCH (emp)-[:MENTIONED]->(entity:Entity)
RETURN
  org.name as company,
  entity.entity_type as type,
  count(entity) as count
ORDER BY company, count DESC;

// Innovation potential by company
MATCH (emp:Employee)-[:WORKS_FOR]->(org:Organization)
RETURN
  org.name as company,
  avg(emp.score_game_changer) as avg_innovation,
  avg(emp.score_strategist) as avg_strategy
ORDER BY avg_innovation DESC;
```

---

## 🎨 Neo4j Browser Styling Tips

1. **Size nodes by importance:**
   - Right sidebar → Size → Select property: `source_count` or `score_game_changer`

2. **Color customization:**
   - Employees: Blue
   - Organizations: Green
   - Entities: By entity_type (auto-colored)

3. **Caption control:**
   - Employee nodes: Show `full_name`
   - Entity nodes: Show `name`
   - Organization nodes: Show `name`

4. **Layout optimization:**
   - Try "Hierarchical" for org charts
   - Try "Force-directed" for networks
   - Use "Circular" for company comparisons

---

## 🚀 Next Steps

1. **Open Neo4j Browser:** http://localhost:7474
2. **Start with:** Phase 1 queries (org overview)
3. **Deep dive:** Pick a company and explore
4. **Export insights:** Take screenshots of interesting patterns
5. **Share findings:** Export as PNG/SVG for presentations

**Pro Tip:** Double-click on Organization nodes to expand and see all connected employees and entities!
