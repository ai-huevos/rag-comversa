# Current System Architecture & Data Flow

**Date**: 2025-11-16
**Status**: Pre-Phase 5 Full Extraction
**Purpose**: Understanding what's working before the full 44-interview run

---

## 🗄️ System Overview: 3 Active Databases

```
┌─────────────────────────────────────────────────────────────────┐
│                    DATA FLOW ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────┘

   JSON Transcripts (44 interviews)
   data/interviews/analysis_output/all_interviews.json
                    │
                    ▼
   ┌────────────────────────────────────────────┐
   │  EXTRACTION PIPELINE (intelligence_capture) │
   │  - 17 Entity Extractors (16 working)        │
   │  - OpenAI gpt-4o-mini (primary)             │
   │  - Safeguards + Validation                  │
   └────────────────────────────────────────────┘
                    │
                    ▼
   ╔═══════════════════════════════════════════════════════════╗
   ║  SYSTEM 1: SQLite (data/full_intelligence.db)             ║
   ║  Purpose: Raw extraction storage                          ║
   ║  Status: ✅ WORKING - 18 tables, 44 interviews            ║
   ║  Data: 276 pain_points, 208 processes, 0 team_structures ║
   ║  Size: 1.5 MB                                             ║
   ╚═══════════════════════════════════════════════════════════╝
                    │
                    │ (Consolidation Agent)
                    ▼
   ╔═══════════════════════════════════════════════════════════╗
   ║  SYSTEM 2: PostgreSQL (comversa_rag)                      ║
   ║  Purpose: Consolidated entities + RAG 2.0 storage         ║
   ║  Status: ✅ OPERATIONAL - 17+ tables                      ║
   ║  Data: 1,743 consolidated_entities, 0 embeddings          ║
   ║  Extensions: pgvector 0.8.1, pgcrypto, uuid-ossp          ║
   ╚═══════════════════════════════════════════════════════════╝
                    │
                    │ (Graph Sync)
                    ▼
   ╔═══════════════════════════════════════════════════════════╗
   ║  SYSTEM 3: Neo4j (Knowledge Graph)                        ║
   ║  Purpose: Relationship graph + pattern discovery          ║
   ║  Status: ✅ OPERATIONAL - 1,790 nodes                     ║
   ║  Data: 13 entity types, relationships mapped              ║
   ║  Version: Neo4j 2025.10.1                                 ║
   ╚═══════════════════════════════════════════════════════════╝
                    │
                    │ (RAG 2.0 - NOT YET BUILT)
                    ▼
   ┌────────────────────────────────────────────┐
   │  AGENTIC RAG SYSTEM (Planned Week 3)       │
   │  - Pydantic AI agent                        │
   │  - Vector/Graph/Hybrid search              │
   │  - FastAPI endpoint                         │
   │  Status: ⏳ PENDING                         │
   └────────────────────────────────────────────┘
```

---

## 📊 Current System Status

### ✅ SYSTEM 1: SQLite (Primary Extraction)

**Location**: `data/full_intelligence.db` (1.5 MB)
**Purpose**: Raw entity extraction storage
**Schema**: 18 tables (17 entity types + metadata)

**Current Data** (from Nov 11 backup before fixes):
```sql
Interviews:              44
Pain Points:            276
Processes:              208
Systems:                183
KPIs:                   124
Automation Candidates:  172
Inefficiencies:         123
Communication Channels: 232
Decision Points:        126
Data Flows:             137
Temporal Patterns:      210
Failure Modes:          149
Team Structures:          0  ❌ EMPTY (to be fixed)
Knowledge Gaps:           0  ❌ EMPTY (to be fixed)
Success Patterns:       172
Budget Constraints:       0  ❌ EMPTY (to be fixed)
External Dependencies:   17
----------------------------------
TOTAL:               ~2,100+ entities
```

**Status**:
- ✅ Operational
- ✅ Safeguards active
- ❌ 3 entity types empty (awaiting Phase 5 fix)

**Tables**:
1. `interviews` - Interview metadata (44 records)
2. `pain_points` - Pain point entities (276)
3. `processes` - Process entities (208)
4. `systems` - System entities (183)
5. `kpis` - KPI entities (124)
6. `automation_candidates` - Automation opportunities (172)
7. `inefficiencies` - Inefficiency entities (123)
8. `communication_channels` - Communication methods (232)
9. `decision_points` - Decision points (126)
10. `data_flows` - Data flow entities (137)
11. `temporal_patterns` - Time-based patterns (210)
12. `failure_modes` - Failure scenarios (149)
13. `team_structures` - Team org (0 - **BROKEN**)
14. `knowledge_gaps` - Knowledge gaps (0 - **BROKEN**)
15. `success_patterns` - Success patterns (172)
16. `budget_constraints` - Budget limits (0 - **BROKEN**)
17. `external_dependencies` - External deps (17)
18. `sqlite_sequence` - Auto-increment tracking

---

### ✅ SYSTEM 2: PostgreSQL + pgvector (RAG 2.0 Storage)

**Connection**: `postgresql://postgres@localhost:5432/comversa_rag`
**Purpose**: Consolidated entities + vector embeddings for RAG
**Status**: ✅ Operational (setup complete Nov 11)

**Current Data**:
```sql
consolidated_entities:       1,743  ✅ (from old consolidation)
consolidated_relationships:      0
consolidated_patterns:           0
embeddings:                      0  ⏳ (awaiting Task 7)
documents:                       0  ⏳ (awaiting ingestion)
document_chunks:                 0  ⏳ (awaiting chunking)
context_registry:                0  ⏳ (awaiting intake)
employees:                   1,088  ✅ (synced)
```

**Key Tables** (17 total):
1. **RAG 2.0 Core**:
   - `documents` - Source documents
   - `document_chunks` - Text chunks for retrieval
   - `embeddings` - Vector embeddings (HNSW indexed)

2. **Consolidation Data**:
   - `consolidated_entities` - Deduplicated entities (1,743)
   - `consolidated_relationships` - Entity relationships
   - `consolidated_patterns` - Discovered patterns
   - `consolidation_events` - Consolidation audit trail
   - `consolidation_audit` - Quality metrics

3. **Context & Governance**:
   - `context_registry` - Document metadata/permissions
   - `context_registry_audit` - Access logging
   - `context_access_log` - Usage tracking

4. **Entity Tables** (mirrored from SQLite):
   - `automation_candidates`
   - `budget_constraints`
   - `communication_channels`
   - `data_flows`
   - `decision_points`
   - (+ 12 more entity types)

**Extensions**:
- ✅ `pgvector 0.8.1` - Vector similarity search
- ✅ `pgcrypto` - Encryption functions
- ✅ `uuid-ossp` - UUID generation

**Indexes**:
- ✅ HNSW index on `embeddings.embedding` (for vector search)
- ✅ B-tree indexes on foreign keys
- ✅ Composite indexes on common queries

---

### ✅ SYSTEM 3: Neo4j (Knowledge Graph)

**Connection**: `neo4j://localhost:7687`
**Credentials**: `neo4j / comversa_neo4j_2025`
**Purpose**: Relationship graph for pattern discovery
**Status**: ✅ Operational (1,790 nodes)

**Current Data**:
```cypher
Total Nodes:                1,790

Entity Breakdown (Top 10):
communication_channel:        232
temporal_pattern:             210
system:                       183
success_pattern:              172
process:                      170
failure_mode:                 149
data_flow:                    137
decision_point:               126
kpi:                          124
inefficiency:                 123
```

**Graph Schema**:
```cypher
Nodes:
  - Entity (base type)
    - Properties: id, entity_type, name, description,
                  source_count, consensus_confidence

Relationships:
  - USES (Process → System)
  - CAUSES (System → PainPoint)
  - DEPENDS_ON (Process → Process)
  - COMMUNICATES_VIA (Team → Channel)
  - MEASURED_BY (Process → KPI)
  - (+ more to be discovered)
```

**Constraints & Indexes**:
- ✅ Unique constraint on `Entity.id`
- ✅ Index on `Entity.entity_type`
- ✅ Index on `Entity.consensus_confidence`

---

## 🔄 Data Flow Pipeline (Step-by-Step)

### Phase 1: Extraction (CURRENT SYSTEM)

```
1. SOURCE DATA
   Location: data/interviews/analysis_output/all_interviews.json
   Format: JSON with 44 interview transcripts
   Size: ~2-3 MB
   Language: Spanish

   ↓

2. EXTRACTION PIPELINE (intelligence_capture/processor.py)
   Entry: IntelligenceProcessor.process_interviews()

   a) Load interviews from JSON
   b) Initialize extractors (16 types)
   c) Verify extractors (safeguard #1)
   d) For each interview:
      - Extract with 17 different extractors
      - Validate results (safeguard #2)
      - Store in SQLite
      - Update status
   e) Batch validation (safeguard #4)

   ↓

3. SQLite STORAGE (data/full_intelligence.db)
   - Raw entities stored (2,100+ currently)
   - Interview metadata tracked
   - Extraction status logged
   - Ready for consolidation
```

### Phase 2: Consolidation (WORKING)

```
4. CONSOLIDATION AGENT (intelligence_capture/consolidation_agent.py)
   Entry: scripts/run_consolidation.py

   Components:
   a) DuplicateDetector - Find similar entities
      - Exact match (name/description)
      - Fuzzy match (Levenshtein distance)
      - Semantic similarity (embeddings)

   b) EntityMerger - Merge duplicates
      - Combine metadata
      - Preserve source references
      - Calculate consensus confidence

   c) ConsensusScorer - Quality scoring
      - Source agreement
      - Attribute consistency
      - Confidence weighting

   d) RelationshipDiscoverer - Find connections
      - Co-occurrence patterns
      - Explicit references
      - Implicit relationships

   e) PatternRecognizer - Identify patterns
      - Recurring themes
      - Process chains
      - Failure modes

   ↓

5. POSTGRESQL STORAGE (comversa_rag)
   Write to:
   - consolidated_entities (1,743 currently)
   - consolidated_relationships
   - consolidated_patterns
   - consolidation_events (audit trail)
```

### Phase 3: Graph Sync (WORKING)

```
6. GRAPH SYNC (scripts/sync_consolidated_to_neo4j.py)
   Entry: ConsolidationSync.sync_to_graph()

   Process:
   a) Read from PostgreSQL consolidated_entities
   b) Transform to Cypher format
   c) Create/update nodes in Neo4j
   d) Create relationships
   e) Update indexes

   ↓

7. NEO4J STORAGE (Knowledge Graph)
   - 1,790 nodes (Entity type)
   - Relationships mapped
   - Queryable via Cypher
   - Ready for pattern queries
```

### Phase 4: RAG Pipeline (NOT YET BUILT - Week 3)

```
8. DOCUMENT PROCESSING (Planned)
   - Ingest source documents
   - OCR PDFs/images
   - Chunk text (Spanish-aware)
   - Store in PostgreSQL documents/chunks

   ↓

9. EMBEDDING GENERATION (Planned - Task 7)
   - Generate embeddings for chunks
   - Use OpenAI text-embedding-3-small
   - Store in PostgreSQL embeddings table
   - Cost guard active

   ↓

10. AGENTIC RAG (Planned - Week 3)
    - Pydantic AI agent
    - Vector search (pgvector)
    - Graph search (Neo4j)
    - Hybrid retrieval
    - FastAPI endpoint /chat
    - CLI interface
```

---

## ❌ What's Missing Before Full Run

### 1. Empty Entity Tables (WILL BE FIXED IN PHASE 5)

**Problem**: 3 entity types extracting 0 entities
```
team_structures:      0  ❌
knowledge_gaps:       0  ❌
budget_constraints:   0  ❌
```

**Root Cause**: JSON format mismatch (prompts vs response_format)

**Fix Applied** (awaiting validation):
- JSON format alignment in extractors.py
- Database serialization in database.py
- Broader keywords in knowledge_gaps

**Will be validated when**: Phase 5 full extraction runs

---

### 2. Consolidation Pipeline (PARTIAL)

**What's Working**:
- ✅ SQLite → consolidation_agent → PostgreSQL
- ✅ PostgreSQL → graph_sync → Neo4j
- ✅ 1,743 entities consolidated (OLD data)

**What's Missing**:
- ⏳ Re-run consolidation on NEW extraction data
- ⏳ Sync fresh consolidated entities to Neo4j
- ⏳ Pattern discovery on new relationships

**When to run**: After Phase 5 extraction completes

**Command**:
```bash
# After full extraction
python scripts/run_consolidation.py
python scripts/sync_consolidated_to_neo4j.py
```

---

### 3. RAG 2.0 Pipeline (NOT STARTED)

**What's Missing**:
- ⏳ Document ingestion (Task 0-2, Week 1)
- ⏳ OCR pipeline (Task 3, Week 1)
- ⏳ Spanish chunking (Task 5, Week 1)
- ⏳ Embedding generation (Task 7, Week 2)
- ⏳ Vector search (Task 7, Week 2)
- ⏳ Agentic RAG (Tasks 10-14, Week 3)
- ⏳ FastAPI endpoint (Task 12, Week 3)

**Status**: Week 1/5 in progress (per CLAUDE.md)

**Next Steps**:
1. Task 0-5: Intake & OCR (Week 1)
2. Task 7: Embedding pipeline (Week 2)
3. Tasks 10-14: Agentic RAG (Week 3)

---

## 🚦 Pre-Flight Checklist for Phase 5

### ✅ Systems Operational
- [x] SQLite database ready
- [x] PostgreSQL+pgvector ready
- [x] Neo4j graph ready
- [x] Extraction safeguards active (13/13 tests passing)
- [x] Backup created (20251116_200218)

### ✅ Code Fixes Applied
- [x] JSON format alignment (extractors.py)
- [x] Database serialization (database.py)
- [x] Broader keywords (knowledge_gaps)
- [x] Defensive parsing (all 3 extractors)

### ✅ Validation Complete
- [x] Phase 4 test extraction: 71 entities (15/16 types)
- [x] team_structures: 1 (was 0)
- [x] knowledge_gaps: 4 (was 0)
- [x] budget_constraints: 2 (was 0)

### ⏳ Post-Phase 5 Actions
- [ ] Run consolidation on new data
- [ ] Sync to Neo4j
- [ ] Update documentation
- [ ] Begin RAG 2.0 Week 2 tasks

---

## 📋 Expected Data Flow After Phase 5

```
POST-PHASE 5 STATE (Expected)

SQLite (full_intelligence.db):
  Interviews:              44
  Total entities:      ~3,000+
  team_structures:       40-100  ✅ FIXED
  knowledge_gaps:         5-20   ✅ FIXED
  budget_constraints:    20-40   ✅ FIXED
  All other types:    ~2,800+

         ↓ (consolidation)

PostgreSQL (comversa_rag):
  consolidated_entities: ~2,000-2,500  (after deduplication)
  consolidation_events:  ~500-1,000    (merge operations)

         ↓ (graph sync)

Neo4j (Knowledge Graph):
  Total nodes:          ~2,500-3,000
  Relationships:        ~5,000-10,000
  Entity types:         16 (all complete)

         ↓ (RAG 2.0 - Week 2-3)

Embeddings:
  document_chunks:      ~500-1,000
  embeddings:           ~500-1,000
  Vector index:         HNSW ready
```

---

## 🎯 Summary: What Works Now

**Extraction Pipeline**: ✅ Working
- 16/17 extractors operational
- Safeguards active and tested
- Validates immediately on failure
- Protects database from corruption

**Storage Layer**: ✅ 3 databases operational
- SQLite: Raw extraction (1.5 MB)
- PostgreSQL: Consolidated data (1,743 entities)
- Neo4j: Knowledge graph (1,790 nodes)

**Consolidation**: ✅ Working (on old data)
- DuplicateDetector operational
- EntityMerger tested
- GraphSync working
- Needs re-run on new data

**RAG 2.0**: ⏳ Week 1/5 in progress
- Databases ready
- Pipeline not yet built
- Embeddings pending
- Agent pending

---

## 🚨 Critical Gap Before Full Run

**NONE** - System is ready!

The only missing piece is the NEW extraction data itself, which Phase 5 will provide.

After Phase 5:
1. ✅ SQLite will have 3,000+ entities (including 3 fixed types)
2. ⏳ Run consolidation to populate PostgreSQL
3. ⏳ Sync to Neo4j for updated graph
4. ⏳ Continue RAG 2.0 development (Week 2+)

---

**Ready to proceed with Phase 5 full extraction!** 🚀

All systems operational. No blockers detected.
