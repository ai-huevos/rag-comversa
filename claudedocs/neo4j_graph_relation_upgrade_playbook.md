# Neo4j Graph Relation Upgrade Playbook

**Audience:** Data/graph engineers working on `system0`  
**Sources:** Project scripts & docs (`scripts/sync_consolidated_to_neo4j.py`, `scripts/infer_entity_relationships.py`, `intelligence_capture/consolidation_sync.py`, `claudedocs/neo4j_data_structure_analysis.md`) + Neo4j product documentation.

---

## 1. Where We Are Today

| Stage | Current Implementation | Observations |
| --- | --- | --- |
| Extraction | `intelligence_capture/run.py` writes raw entities into SQLite per interview | 44 interviews → ~3k raw entities with metadata-rich payloads |
| Consolidation | `scripts/run_consolidation.py` → PostgreSQL `consolidated_entities` & (still sparse) `consolidated_relationships` | Dedupes, scores consensus, preserves payload JSON but only seeds a handful of explicit relationships |
| Graph Sync | `scripts/sync_consolidated_to_neo4j.py` uses `KnowledgeGraphBuilder` (`graph/knowledge_graph_builder.py`) | Nodes: 1,743 `Entity`, 44 `Employee`, 3 `Organization`; relationships limited to `MENTIONED`, `WORKS_FOR`, plus edges inferred post-sync |
| Post-sync inference | `scripts/infer_entity_relationships.py` + visualization inference helpers | Adds ~500–1,000 edges (AFFECTS, IMPROVES, USES…), but coverage depends on payload cleanliness and label normalization |

**Pain:** Entity-to-entity relations are mostly inferred, not codified in Postgres, leaving gaps for automated reasoning, Cypher traversals, and Bloom visualizations (see `claudedocs/neo4j_data_structure_analysis.md`).

---

## 2. Storage & Modeling: Cross-Reference With Neo4j Guidance

| Topic | Current Pattern | Recommended Practice (Neo4j docs) | Improvements |
| --- | --- | --- | --- |
| Node labels | Single `Entity` label + visualization layer labels set via `viz_label` (`graph/knowledge_graph_builder.py:80-118`) | [Graph Data Modeling → Labeling](https://neo4j.com/docs/developer-manual/current/modeling/modeling-structure/) recommends semantic labels per type plus optional hierarchy labels | Keep visualization layers, but also add type-specific labels (e.g., `:Entity:Process`) to honor label-based pattern matching and index selectivity |
| Relationship vocabulary | Inference script emits AFFECTS/USES/etc. but naming is inconsistent with domain | [Modeling Relationships](https://neo4j.com/docs/getting-started/current/data-modeling/relationships/) emphasizes verb-based, directed, domain-friendly names | Create canonical dictionary (Pain→Process = `CAUSES` or `AFFECTS`?). Align inference rules + consolidation agent outputs so Postgres + Neo4j share the same relationship type strings |
| Properties | JSON payload flattened into node props; relationships only store `source_property` + `source_value` | [Property Graph Model](https://neo4j.com/docs/getting-started/current/data-modeling/graph-modeling/) encourages storing provenance + metrics on both nodes and relationships | Extend `GraphRelationship.properties` to persist strength/confidence/time-scope from PostgreSQL (`consolidated_relationships`) and inference stats (`source_count`, `consensus_confidence`) |
| Constraints & indexes | `KnowledgeGraphBuilder.ensure_constraints()` adds uniqueness + basic index, but not invoked from sync script | [Cypher Manual → Constraints & Indexes](https://neo4j.com/docs/cypher-manual/current/indexes-for-search-performance/) stresses running `CREATE CONSTRAINT IF NOT EXISTS…` before bulk merges | Call `builder.ensure_constraints()` during bootstrap, add composite indexes on `(entity_type, name_normalized)` and relationship properties used in lookups |
| Org boundaries | `org_id` stored as property; inference ensures same `org_id` before linking | [Multi-tenant modeling](https://neo4j.com/docs/operations-manual/current/manage-multi-tenancy/) suggests either separate DBs or mandatory tenant property + security predicate | Continue storing `org_id` but also add `:Organization` nodes owning their subgraphs via `CONTAINS`/`BELONGS_TO` edges (already partially inferred) and enforce `WHERE entity.org_id = $org_id` in all writes/reads |

---

## 3. Data Loading & Synchronization Best Practices

1. **Batching & Periodic Writes**
   - Current: Python driver writes all nodes/edges in-memory.
   - Reference: [Neo4j Bulk Import & `apoc.periodic.iterate`](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/#import-tool-overview) + [APOC Periodic Iterate](https://neo4j.com/docs/apoc/current/graph-updates/periodic/) for streaming merges.
   - Action: When reloading 2–3k nodes, wrap merges via `apoc.periodic.iterate` or chunked `UNWIND` statements to keep memory low and benefit from transactional checkpoints. For nightly rebuilds, consider exporting CSV from Postgres and using `neo4j-admin database import` in a staging DB, then swap DB aliases.

2. **Idempotent MERGE semantics**
   - Already using `MERGE` on `(org_id, entity_type, external_id)`.
   - Reference: [Cypher Best Practices → MERGE vs CREATE](https://neo4j.com/docs/cypher-manual/current/clauses/merge/).
   - Action: Expand MERGE key for relationships to include `source_property` when duplicates are acceptable; otherwise maintain `relationship_id` from Postgres.

3. **Streaming payload improvements**
   - Reference: [Drivers Manual → Transaction functions](https://neo4j.com/docs/python-manual/current/transactions/) show best patterns for `execute_write`.
   - Action: In `scripts/sync_consolidated_to_neo4j.py`, call `builder.ensure_constraints()` once, then reuse sessions via transaction functions for both nodes and edges.

4. **Observability**
   - Reference: [Operations Manual → Query Log & Metrics](https://neo4j.com/docs/operations-manual/current/monitoring/metrics/).
   - Action: Enable query logging during sync to profile slow merges; store counts from inference summary back into `consolidation_events` for trending.

---

## 4. Querying & Analytics Patterns

| Need | Current Approach | Doc Guidance | Upgrade |
| --- | --- | --- | --- |
| Entity context queries | Property-based lookups (`MATCH (pain:Entity {entity_type: 'pain_point'})`) | [Cypher Manual → Pattern Matching](https://neo4j.com/docs/cypher-manual/current/patterns/simple-patterns/) | After we add specific labels, queries become `MATCH (pain:PainPoint)` which is faster and aligns with docs |
| Traversals | Limited due to missing relationships | [Cypher Manual → Variable-Length Paths](https://neo4j.com/docs/cypher-manual/current/patterns/path-patterns/) | Build compound queries: e.g., `MATCH (pain:PainPoint)-[:AFFECTS]->(proc:Process)-[:USES]->(sys:System)` for root-cause chains |
| Diagnostics | Manual scripts in docs | [Cypher → EXPLAIN/PROFILE](https://neo4j.com/docs/cypher-manual/current/query-tuning/basic-query-tuning/) | Document a runbook: `PROFILE MATCH ...` and ensure indexes cover `entity_type + org_id + name_normalized` |
| Analytics | Not yet using GDS | [Graph Data Science Manual](https://neo4j.com/docs/graph-data-science/current/) | After relationships mature, run `gds.pageRank.stream` on process/system subgraph to rank high-impact systems; use `gds.shortestPath` to trace multi-hop dependencies |

**Query Templates to Publish**
```cypher
// Pain points, processes, systems
MATCH (pain:PainPoint)-[:AFFECTS]->(proc:Process)
OPTIONAL MATCH (proc)-[:USES]->(sys:System)
RETURN pain.name, proc.name, collect(DISTINCT sys.name) AS systems;

// Automation ROI path
MATCH (auto:AutomationCandidate)-[:IMPROVES]->(proc:Process)
MATCH (proc)-[:MEASURED_BY]->(kpi:KPI)
RETURN auto.name, proc.name, kpi.name, kpi.target_value;
```
- Template references ↔ `RELATIONSHIP_RULES` in `scripts/infer_entity_relationships.py`.

---

## 5. Relationship Improvement Blueprint

### 5.1 Immediate (This week)
1. **Normalize labels before sync**  
   - Extend `normalize_entity_properties()` (`scripts/sync_consolidated_to_neo4j.py`) to add type-specific boolean flags used by `KnowledgeGraphBuilder` to append labels.
2. **Tighten inference dictionary**  
   - Review `RELATIONSHIP_RULES` (pain_point, inefficiency, etc.) and align property names with actual payload keys from PostgreSQL; log unmatched values back into `consolidation_events`.
3. **Persist inference output**  
   - Store each inferred relationship into `consolidated_relationships` with `relationship_origin = 'property_inference'` so Postgres is the system of record (aligns with [Operations Manual → Data governance](https://neo4j.com/docs/operations-manual/current/clustering/data-governance/)).

### 5.2 Short Term (Next sprint)
1. **Enhance ConsolidationAgent**  
   - Implement `RelationshipDiscoverer` described in `claudedocs/neo4j_data_structure_analysis.md` to fill `consolidated_relationships`. Reference [GenAI & Graph modeling article](https://neo4j.com/docs/genai-ecosystem/current/design/graph-construction/) for prompt patterns.
2. **Use APOC text utilities**  
   - Deploy [APOC text & NLP functions](https://neo4j.com/docs/apoc/current/functions/text/) to match process/system names (e.g., `apoc.text.levenshteinSimilarity`) instead of manual normalization.
3. **Build unit tests around inference**  
   - Add fixtures under `tests/graph/` verifying `infer_entity_relationships` creates expected edges for sample payloads; emulate doc guidance on [Testing Cypher](https://neo4j.com/docs/cypher-manual/current/testing/) with in-memory test harness (e.g., `neo4j` testcontainer).

### 5.3 Medium Term
1. **LLM-Assisted relationship extraction**  
   - Add `RelationshipExtractor` to `intelligence_capture` referencing doc on [GraphRAG patterns](https://neo4j.com/docs/genai-ecosystem/current/design/knowledge-graphs/#graphrag) to capture cause/effect statements at extraction time.
2. **Adopt Graph Data Science (GDS)**  
   - Once relationships rich, load subgraphs (`gds.graph.project`) and run community detection to cluster related pain points/processes; use scores to prioritize automations.
3. **Model for support insights**  
   - Build `SUPPORTS` relationships between `Employee`/`Process` nodes using mention metadata, enabling queries like “which team handles system outages?”.

---

## 6. Support, Observability, and Ops Alignment

| Area | Doc Reference | Action |
| --- | --- | --- |
| Backups | [Operations Manual → Backup & Restore](https://neo4j.com/docs/operations-manual/current/backup-restore/) | Snapshots before/after full reload; store in `/backups/neo4j` with timestamp naming |
| Health checks | [Driver Manual → Connectivity verification](https://neo4j.com/docs/python-manual/current/client-applications/#python-driver-connectivity) | Expose `/health/neo4j` endpoint in API using `KnowledgeGraphBuilder.healthcheck()` |
| Monitoring | [Neo4j Ops Manager (NOM)](https://neo4j.com/docs/ops-manager/current/) | Adopt NOM or Prometheus metrics to alert if relationship counts drop below thresholds |
| Access control | [Operations Manual → Role-based access](https://neo4j.com/docs/operations-manual/current/authentication-authorization/) | When sharing Bloom dashboards, enforce roles (e.g., analysts can read but not write) |

---

## 7. Suggested Next Steps Checklist

1. Run `python3 scripts/run_consolidation.py` → `python3 scripts/sync_consolidated_to_neo4j.py --inference-dry-run` and persist inference stats to `reports/`.
2. Update `KnowledgeGraphBuilder` to append entity-type labels and call `ensure_constraints()` before merges.
3. Define canonical relationship dictionary + property schema in `config/graph_relationships.yml` (new file), reuse it in consolidation + inference.
4. Publish Cypher runbook (queries above + `EXPLAIN/PROFILE` instructions) under `docs/graph_queries.md`.
5. Pilot GDS analysis once entity relationships surpass 500 stable edges; capture learnings for stakeholder-facing reports.

This playbook aligns the current pipeline with the official Neo4j guidance so we can confidently scale relationships, query depth, and support insights without reworking the foundation later.

---

## 8. Alignment With Phase 5 Execution Plan

| Execution Plan Item (`claudedocs/phase5_full_system_execution_plan.md`) | Playbook Tie-in |
| --- | --- |
| Relationship inference wired into `scripts/sync_consolidated_to_neo4j.py` (Section “Updated Data Flow Architecture”) | Sections 2 & 5 specify label normalization, canonical relationship vocab, and persisting inferred edges back into Postgres so Phase 5 can demonstrate durable relationships rather than ephemeral property joins. |
| Clean-room rebuild (Step 0) before running extraction/consolidation | Section 3’s batching/import guidance + Section 6’s backup strategy ensure we can repeatedly rebuild Neo4j after each full extraction run without data loss. |
| Neo4j visualization readiness (Phase 5 objective) | Section 4 query templates + Section 5 measurement relationships (MEASURED_BY) give dashboards immediate value once Phase 5 completes. |

---

## 9. Neo4j Documentation Reference Map

| Topic | Official Doc Section | How We Apply It |
| --- | --- | --- |
| Data modeling & labels | [Developer Manual → Modeling concepts](https://neo4j.com/docs/developer-manual/current/modeling/modeling-structure/) | Add per-type labels to nodes and document them in `config/graph_relationships.yml`, enabling `MATCH (:Process)` patterns. |
| Relationship semantics | [Getting Started → Modeling relationships](https://neo4j.com/docs/getting-started/current/data-modeling/relationships/) | Normalize naming (CAUSES, IMPROVES, USES) so inference + consolidation generate identical edge types. |
| Bulk import / streaming | [Operations Manual → `neo4j-admin import`](https://neo4j.com/docs/operations-manual/current/tools/neo4j-admin/neo4j-admin-import/) & [APOC `periodic.iterate`](https://neo4j.com/docs/apoc/current/graph-updates/periodic/) | For large rebuilds export CSV from Postgres, import into staging DB, then move alias; for daily deltas keep Python driver but chunk writes. |
| Cypher tuning | [Cypher Manual → Query tuning](https://neo4j.com/docs/cypher-manual/current/query-tuning/basic-query-tuning/) | Encourage `EXPLAIN/PROFILE` on dashboards, add indexes on `(entity_type, org_id, name_normalized)` before shipping dashboards. |
| Graph Data Science | [GDS Manual](https://neo4j.com/docs/graph-data-science/current/) | Once relationships stabilized, run PageRank or community detection on process/system graph for prioritization insights. |
| APOC utilities | [APOC Reference](https://neo4j.com/docs/apoc/current/) | Replace manual normalization with `apoc.text.clean`, use `apoc.periodic.iterate` for property-based inference Cypher, and run `apoc.meta.stats` after sync to confirm counts. |
| Security & RBAC | [Operations Manual → Authentication & authorization](https://neo4j.com/docs/operations-manual/current/authentication-authorization/) | Map `Organization` to Neo4j roles when exposing Bloom; create read-only roles for analysts. |
| Monitoring & backups | [Operations Manual → Monitoring](https://neo4j.com/docs/operations-manual/current/monitoring/) and [Backup & Restore](https://neo4j.com/docs/operations-manual/current/backup-restore/) | Hook query logs + Prometheus metrics; schedule nightly `neo4j-admin database backup` tied to the consolidation schedule. |

Use this matrix as a quick index when updating the pipeline—each improvement references a canonical doc page for deeper detail.

---

## 10. Support Intelligence Use Cases (Powered by the Graph)

| Use Case | Cypher Pattern | Notes |
| --- | --- | --- |
| Triage a pain point | `MATCH (pain:PainPoint {org_id: $org})-[:AFFECTS]->(proc:Process)-[:USES]->(sys:System)` | Surfaces the process/system dependency path for support teams; complements `claudedocs/cleanup and data restoration.md` by pinpointing which systems need restore steps. |
| Identify automation ROI | `MATCH (auto:AutomationCandidate)-[:IMPROVES]->(proc:Process)-[:MEASURED_BY]->(kpi:KPI)` | Links automation ideas to measurable KPIs for exec reviews. |
| Map employee mentions to support scope | `MATCH (emp:Employee)-[:MENTIONED]->(entity)<-[:AFFECTS]-(pain:PainPoint)` | Connects interview insights to actionable support tickets. |
| Dependency change impact | `MATCH p = (sys:System)-[:INTEGRATES_WITH*1..3]->(other:System)` | Uses variable-length traversals to assess ripple effects before system upgrades. |
| Alert routing | `MATCH (team:Entity {entity_type:'team_structure'})-[:OWNS]->(proc:Process)-[:USES]->(sys:System {name:$system})` | Guides support escalation to the right team when a system outage occurs. |

Publish these queries (and their indexed variants) alongside the runbooks so the support organization can pull precise insights instead of relying on spreadsheets.

---

**Appendix: Environment Hooks**

- `.env` / `config/database.toml` hold the `NEO4J_URI`, `NEO4J_USER`, and `NEO4J_PASSWORD` variables referenced by every script—keep them synchronized with deployment secrets.
- `claudedocs/cleanup and data restoration.md` should link back to this playbook so post-incident restores automatically include Neo4j constraint checks and inference reruns.
- For disaster recovery, pair the Postgres + Neo4j backups mentioned in Section 6 with the SQLite snapshots created before running `scripts/run_consolidation.py`.
