# Phase 5: Full System Execution Plan

**Date**: 2025-11-16
**Objective**: Complete end-to-end extraction → consolidation → graph sync with relationship discovery
**Branch**: `feat/phase5-full-extraction-with-relationships`

---

## 📋 System Architecture Updates

### How Relationship Inference Fits Into the Flow

```
┌──────────────────────────────────────────────────────────────┐
│              UPDATED DATA FLOW ARCHITECTURE                   │
└──────────────────────────────────────────────────────────────┘

1. EXTRACTION PIPELINE
   intelligence_capture/run.py
   ↓
   SQLite (raw entities)
   - 44 interviews
   - ~3,000 entities (after Phase 5)

2. CONSOLIDATION AGENT                    ← EXISTING
   scripts/run_consolidation.py
   ↓
   Components:
   a) DuplicateDetector
   b) EntityMerger
   c) ConsensusScorer
   d) RelationshipDiscoverer              ← Finds co-occurrence patterns
   e) PatternRecognizer
   ↓
   PostgreSQL (consolidated_entities)
   - ~2,000-2,500 entities
   - consolidated_relationships table     ← From RelationshipDiscoverer

3. GRAPH SYNC                              ← ENHANCED
   scripts/sync_consolidated_to_neo4j.py
   ↓
   Process:
   a) Sync consolidated entities → Neo4j nodes
   b) Sync consolidated_relationships → Neo4j edges (EXISTING)
   c) AUTOMATICALLY calls inference module (NEW!)
   ↓
   Inference Module:
   scripts/infer_entity_relationships.py  ← RUNS AUTOMATICALLY
   - Reads entity properties (process, systems_involved, etc.)
   - Creates additional relationships from metadata
   - Normalizes labels, fuzzy matching
   - Creates: AFFECTS, IMPROVES, USES, INVOLVES, etc.
   ↓
   Neo4j (Knowledge Graph)
   - Nodes: ~2,500-3,000
   - Relationships: ~500-1,000 (inferred) + consolidated_relationships
```

### Two Sources of Relationships

**Source 1: ConsolidationAgent.RelationshipDiscoverer**
- **Location**: `intelligence_capture/consolidation_agent.py`
- **Method**: Co-occurrence analysis during consolidation
- **Output**: `consolidated_relationships` table in PostgreSQL
- **When**: During `python scripts/run_consolidation.py`
- **Relationships Created**: Based on entities appearing together

**Source 2: Inference Script (Property-Based)**
- **Location**: `scripts/infer_entity_relationships.py`
- **Method**: Parses entity properties (process, systems_involved, etc.)
- **Output**: Direct to Neo4j graph
- **When**: Automatically after sync (or manually)
- **Relationships Created**: AFFECTS, IMPROVES, USES, INVOLVES, FLOWS_TO/FROM

**They Work Together**:
```
RelationshipDiscoverer → PostgreSQL consolidated_relationships
                        ↓
                  Graph Sync copies these
                        ↓
                    Neo4j edges
                        +
                Inference Script adds MORE edges
                        ↓
            Complete Knowledge Graph
```

---

## ✅ Model Fallback Verification

### Round-Robin Chain (Load Distribution)
```python
# config/extraction_config.json
"round_robin": [
    "gpt-4o-mini",  # Primary (80% of calls)
    "gpt-4o-mini",  # Load distribution
    "gpt-4o"        # Occasionally use stronger model
]
```

### Fallback Chain (Error Recovery)
```python
"fallback": [
    "gpt-4o-mini",  # Try primary first
    "gpt-4o",       # Fallback to stronger model
    "o1-mini"       # Final fallback (reasoning model)
]
```

### How It Works
```python
# intelligence_capture/extractors.py

def call_llm_with_fallback(client, messages, temperature=0.1, max_retries=3):
    """
    1. MODEL_ROUTER.next_model() → picks from round_robin (gpt-4o-mini mostly)
    2. Try up to 3 times with that model
    3. If rate limit error → switch to next model in fallback chain
    4. Continue until success or all models exhausted
    """
    model_sequence = MODEL_ROUTER.build_sequence()
    # Returns: ["gpt-4o-mini", "gpt-4o", "o1-mini"]

    for model in model_sequence:
        for attempt in range(max_retries):
            try:
                # Rate limiter prevents hitting quota
                limiter = get_rate_limiter(max_calls_per_minute=50, key=f"openai:{model}")
                limiter.wait_if_needed()

                response = client.chat.completions.create(model=model, ...)
                return response
            except RateLimitError:
                print(f"  → Rate limit hit, switching to next model")
                break  # Try next model
```

**Result**: ✅ **Model fallback IS working correctly**

---

## 🎯 Full Execution Plan

### Step 0: Create New Branch & Cleanup

```bash
# 1. Create new feature branch
git checkout development
git pull origin development
git checkout -b feat/phase5-full-extraction-with-relationships

# 2. Backup current state (CRITICAL!)
DATE=$(date +%Y%m%d_%H%M%S)
cp data/full_intelligence.db data/backups/full_intelligence_pre_phase5_${DATE}.db

# 3. Clean ALL databases for fresh run
rm -f data/full_intelligence.db
rm -f data/test_single.db
rm -f data/pilot_intelligence.db

# 4. Clean PostgreSQL (optional - or keep old data for comparison)
psql -U postgres -d comversa_rag -c "TRUNCATE TABLE consolidated_entities CASCADE"
psql -U postgres -d comversa_rag -c "TRUNCATE TABLE consolidated_relationships CASCADE"
psql -U postgres -d comversa_rag -c "TRUNCATE TABLE consolidation_events CASCADE"

# 5. Clean Neo4j graph
export NEO4J_PASSWORD=comversa_neo4j_2025
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH (n) DETACH DELETE n"

# Verify clean state
echo "=== SQLite: Should be empty ==="
ls -la data/full_intelligence.db 2>/dev/null || echo "✓ Removed"

echo "=== PostgreSQL: Should be 0 ==="
psql -U postgres -d comversa_rag -c "SELECT COUNT(*) FROM consolidated_entities"

echo "=== Neo4j: Should be 0 ==="
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" "MATCH (n) RETURN count(n)"
```

---

### Step 1: Full Extraction (44 Interviews)

**Command**:
```bash
python3 intelligence_capture/run.py
```

**What Happens**:
1. Loads 44 interviews from JSON
2. Initializes 16 extractors (with safeguards)
3. For each interview:
   - Extracts with round-robin model selection
   - Fallback on rate limits
   - Validates results (safeguards)
   - Stores in SQLite
4. Batch validation at end

**Expected Duration**: 40-60 minutes
**Expected Cost**: $2-5 USD
**Expected Output**: ~3,000 entities in SQLite

**Monitor**:
```bash
# In separate terminal
watch -n 10 'sqlite3 data/full_intelligence.db "
SELECT
    (SELECT COUNT(*) FROM interviews) as interviews,
    (SELECT COUNT(*) FROM pain_points) as pain_points,
    (SELECT COUNT(*) FROM team_structures) as team_structures,
    (SELECT COUNT(*) FROM knowledge_gaps) as knowledge_gaps,
    (SELECT COUNT(*) FROM budget_constraints) as budget_constraints
"'
```

**Success Criteria**:
- ✅ 44/44 interviews processed
- ✅ team_structures ≥ 40
- ✅ knowledge_gaps ≥ 5
- ✅ budget_constraints ≥ 20
- ✅ Total entities ≥ 3,000

---

### Step 2: Consolidation (Deduplication + Relationships)

**Command**:
```bash
python3 scripts/run_consolidation.py
```

**What Happens**:
1. **DuplicateDetector**: Finds similar entities
   - Exact matches
   - Fuzzy matches (Levenshtein)
   - Semantic similarity

2. **EntityMerger**: Merges duplicates
   - Combines metadata
   - Preserves sources
   - Calculates consensus

3. **RelationshipDiscoverer**: Finds co-occurrence patterns
   - Entities mentioned together
   - Creates relationship candidates
   - Stores in `consolidated_relationships`

4. **PatternRecognizer**: Identifies patterns
   - Recurring themes
   - Process chains
   - Failure modes

**Expected Duration**: 5-10 minutes
**Expected Output**:
- ~2,000-2,500 consolidated_entities
- ~200-500 consolidated_relationships (from co-occurrence)

**Verify**:
```bash
psql -U postgres -d comversa_rag -c "
SELECT
    (SELECT COUNT(*) FROM consolidated_entities) as entities,
    (SELECT COUNT(*) FROM consolidated_relationships) as relationships,
    (SELECT COUNT(*) FROM consolidation_events) as events
"
```

---

### Step 3: Graph Sync + Relationship Inference

**Command**:
```bash
python3 scripts/sync_consolidated_to_neo4j.py
```

**What Happens**:

**Phase A: Entity Sync**
1. Read from PostgreSQL `consolidated_entities`
2. Transform to Cypher format
3. Create/update Neo4j nodes

**Phase B: Relationship Sync**
1. Read from PostgreSQL `consolidated_relationships`
2. Create Neo4j edges
3. Handle relationship types

**Phase C: Automatic Relationship Inference** (NEW!)
1. Script automatically calls `infer_entity_relationships.py`
2. Parses entity properties:
   - `process` field → IMPROVES relationships
   - `systems_involved` → INVOLVES/USES relationships
   - `related_process` → AFFECTS relationships
3. Normalizes labels (case, diacritics)
4. Fuzzy matching for entity names
5. Creates additional relationships

**Expected Duration**: 2-5 minutes
**Expected Output**:
- Nodes: ~2,500-3,000
- Relationships: ~500-1,000 (inferred) + consolidated relationships

**Verify**:
```bash
export NEO4J_PASSWORD=comversa_neo4j_2025

# Total nodes
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n) RETURN count(n) as total_nodes"

# Entity breakdown
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) RETURN n.entity_type, count(n) ORDER BY count(n) DESC LIMIT 15"

# Relationship counts by type
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH ()-[r]->() RETURN type(r) as rel_type, count(r) as total ORDER BY total DESC"

# Entity-to-Entity relationships (should be >0 now!)
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (e1:Entity)-[r]-(e2:Entity) RETURN count(r) as entity_relationships"
```

---

### Step 4: Pattern Discovery & Validation

**Command**:
```bash
# Review pattern discoveries in Neo4j Browser
open http://localhost:7474

# Or via command line
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" << 'EOF'
// 1. Pain points with their causes
MATCH (pain:Entity {entity_type: 'pain_point'})-[r:CAUSED_BY|AFFECTS]-(cause)
RETURN pain.name, type(r), cause.entity_type, cause.name
LIMIT 20;

// 2. Automation opportunities with processes
MATCH (auto:Entity {entity_type: 'automation_candidate'})-[r:IMPROVES]-(proc:Entity {entity_type: 'process'})
RETURN auto.name, proc.name, auto.impact_score
ORDER BY auto.impact_score DESC
LIMIT 10;

// 3. System dependencies
MATCH (proc:Entity {entity_type: 'process'})-[r:USES]-(sys:Entity {entity_type: 'system'})
RETURN proc.name, sys.name
LIMIT 20;

// 4. Connected components (how interconnected is the graph?)
CALL gds.alpha.scc.stream({
  nodeProjection: 'Entity',
  relationshipProjection: '*'
})
YIELD nodeId, componentId
RETURN componentId, count(nodeId) as component_size
ORDER BY component_size DESC
LIMIT 10;
EOF
```

---

## 📊 Expected Results

### SQLite (After Step 1)
```
Interviews:              44
Pain Points:            300-400
Processes:              200-300
Systems:                180-250
Team Structures:        40-100   ✅ FIXED
Knowledge Gaps:         5-20     ✅ FIXED
Budget Constraints:     20-40    ✅ FIXED
Other types:            ~2,000
-----------------------------------
TOTAL:                  ~3,000+ entities
```

### PostgreSQL (After Step 2)
```
consolidated_entities:       2,000-2,500  (after deduplication)
consolidated_relationships:  200-500      (co-occurrence patterns)
consolidation_events:        500-1,000    (merge operations)
```

### Neo4j (After Step 3)
```
Nodes:
  Entity:               2,000-2,500
  Employee:             44 (if synced)
  Organization:         3 (if synced)

Relationships:
  AFFECTS:              100-200  (inferred from properties)
  IMPROVES:             80-150   (automation → process)
  USES:                 150-300  (process → system)
  INVOLVES:             100-200  (multi-system operations)
  CAUSED_BY:            50-100   (pain → system/process)
  [From consolidation]: 200-500  (co-occurrence)
  -----------------------------------
  TOTAL:                ~700-1,500 relationships
```

---

## 🔍 Validation Queries

### 1. Data Quality Check
```bash
# SQLite
sqlite3 data/full_intelligence.db << 'EOF'
SELECT
    'Interviews' as entity_type, COUNT(*) FROM interviews
UNION ALL SELECT 'Pain Points', COUNT(*) FROM pain_points
UNION ALL SELECT 'Team Structures', COUNT(*) FROM team_structures
UNION ALL SELECT 'Knowledge Gaps', COUNT(*) FROM knowledge_gaps
UNION ALL SELECT 'Budget Constraints', COUNT(*) FROM budget_constraints;

-- Check for empty required fields
SELECT 'Empty descriptions' as issue, COUNT(*)
FROM pain_points WHERE description IS NULL OR description = '';
EOF
```

### 2. Consolidation Quality
```bash
# PostgreSQL
psql -U postgres -d comversa_rag << 'EOF'
-- Entity type breakdown
SELECT
    entity_type,
    COUNT(*) as total,
    AVG(source_count) as avg_sources,
    AVG(consensus_confidence) as avg_confidence
FROM consolidated_entities
GROUP BY entity_type
ORDER BY total DESC;

-- High-confidence entities
SELECT entity_type, name, source_count, consensus_confidence
FROM consolidated_entities
WHERE consensus_confidence > 0.85
ORDER BY source_count DESC
LIMIT 20;

-- Relationship quality
SELECT
    relationship_type,
    COUNT(*) as total,
    AVG(confidence) as avg_confidence
FROM consolidated_relationships
GROUP BY relationship_type
ORDER BY total DESC;
EOF
```

### 3. Graph Connectivity
```cypher
// Neo4j - Most connected entities
MATCH (e:Entity)
WITH e, size((e)-[]-()) as connections
ORDER BY connections DESC
LIMIT 20
RETURN e.entity_type, e.name, connections;

// Isolated nodes (should be minimal)
MATCH (e:Entity)
WHERE NOT (e)-[]-()
RETURN e.entity_type, count(e) as isolated_count;

// Relationship diversity
MATCH (e:Entity)-[r]-()
WITH e, collect(DISTINCT type(r)) as rel_types
RETURN e.name, e.entity_type, rel_types
ORDER BY size(rel_types) DESC
LIMIT 10;
```

---

## 📝 Post-Execution Documentation

After completing all steps, create summary report:

```bash
# Generate comparison report
python3 << 'EOF'
import sqlite3
from datetime import datetime

print("=" * 70)
print(f"PHASE 5 EXECUTION REPORT - {datetime.now()}")
print("=" * 70)

# SQLite stats
db = sqlite3.connect('data/full_intelligence.db')
cursor = db.cursor()

tables = [
    'pain_points', 'processes', 'systems', 'kpis',
    'automation_candidates', 'inefficiencies',
    'communication_channels', 'decision_points', 'data_flows',
    'temporal_patterns', 'failure_modes',
    'team_structures', 'knowledge_gaps', 'success_patterns',
    'budget_constraints', 'external_dependencies'
]

print("\nSQLite Extraction Results:")
print("-" * 70)
total = 0
for table in tables:
    count = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    total += count
    status = "✅" if count > 0 else "❌"
    print(f"{status} {table:30s}: {count:5d}")

print(f"\nTotal entities: {total}")
db.close()
EOF
```

---

## 🎯 Success Criteria Summary

| Metric | Target | Critical |
|--------|--------|----------|
| Interviews processed | 44/44 | ✅ Yes |
| team_structures | ≥40 | ✅ Yes |
| knowledge_gaps | ≥5 | ⚠️ Nice to have |
| budget_constraints | ≥20 | ✅ Yes |
| Total SQLite entities | ≥3,000 | ✅ Yes |
| Consolidated entities | 2,000-2,500 | ✅ Yes |
| Neo4j nodes | 2,000-2,500 | ✅ Yes |
| Entity-Entity relationships | ≥500 | ✅ Yes |
| No extraction errors | 0 errors | ✅ Yes |
| Safeguards triggered | 0 failures | ✅ Yes |

---

## 🔧 Troubleshooting

### Issue: Extraction Fails Early
```bash
# Check safeguard logs
grep -i "extraction failure\|critical" /tmp/extraction.log

# Verify extractors loaded
python3 -c "from intelligence_capture.processor import IntelligenceProcessor; p = IntelligenceProcessor(); print(len(p.extractor.v2_extractors))"
# Should print: 13
```

### Issue: Consolidation Slow
```bash
# Check progress
psql -U postgres -d comversa_rag -c "SELECT COUNT(*) FROM consolidation_events"

# Monitor in real-time
tail -f reports/consolidation_*.log
```

### Issue: Neo4j Relationships Not Created
```bash
# Check if inference ran
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (e1:Entity)-[r]-(e2:Entity) RETURN count(r)"

# If 0, manually run inference
python3 scripts/infer_entity_relationships.py --dry-run
python3 scripts/infer_entity_relationships.py
```

---

## 📋 Commit Strategy

```bash
# After successful execution
git add -A
git commit -m "feat: Complete Phase 5 full extraction with relationship discovery

- Extracted 44 interviews (~3,000 entities)
- Fixed team_structures, knowledge_gaps, budget_constraints
- Consolidated to ~2,500 entities
- Generated ~500-1,000 Neo4j relationships
- Validated model fallback mechanism
- Verified end-to-end pipeline

Metrics:
- Interviews: 44/44 (100%)
- SQLite entities: 3,XXX
- Consolidated: 2,XXX
- Neo4j relationships: XXX
- Duration: XX minutes
- Cost: $X.XX"

# Push to remote
git push origin feat/phase5-full-extraction-with-relationships

# Create PR
gh pr create --title "Phase 5: Full extraction with relationship discovery" \
  --body "Complete end-to-end extraction pipeline with Neo4j relationship inference"
```

---

**Ready to execute!** 🚀

Start with Step 0 (branch creation + cleanup) when ready.
