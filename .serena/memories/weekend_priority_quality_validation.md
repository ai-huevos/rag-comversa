# Weekend Priority: Comprehensive Quality Validation (Nov 15-17, 2025)

## Rationale
Can't build platform or sell with confidence until we validate the "gold" is being extracted optimally. This is the foundation everything else depends on.

## Test Plan

### 1. Entity Extraction Validation
**Run full test suite across all 17 entity extractors:**
```bash
# v1.0 entity tests (6 types)
pytest tests/test_extractor.py -v

# v2.0 entity tests (11 types) 
pytest tests/test_extractors.py -v
```

**Expected Coverage**: 85%+ test coverage across all entity types

### 2. Consolidation Quality Tests
**Validate 1,743 consolidated entities:**
```bash
pytest tests/test_consolidation_agent.py -v
pytest tests/test_duplicate_detector.py -v
pytest tests/test_entity_merger.py -v
pytest tests/test_consensus_scorer.py -v
```

**Target Metrics**:
- 85% confidence score validated
- 12% consolidation rate confirmed
- 8% contradiction rate acceptable

### 3. Knowledge Graph Integrity
**Verify Neo4j knowledge graph:**
```bash
# Check entity counts
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) RETURN n.entity_type as type, count(n) as count ORDER BY count DESC"

# Verify high-confidence entities
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" \
  "MATCH (n:Entity) WHERE n.consensus_confidence > 0.85 RETURN n.entity_type, n.name, n.source_count LIMIT 20"
```

**Expected**: 1,743 entities across 13 types with proper constraints and indexes

### 4. RAG Retrieval Quality
**Test retrieval precision:**
```bash
python scripts/evaluate_retrieval.py
```

**Target Metrics** (from docs/RUNBOOK.md):
- Precision@5 ≥ 0.80
- MRR (Mean Reciprocal Rank) ≥ 0.75

### 5. Dashboard Metrics Validation
**Confirm reported metrics are accurate:**
- $157K annual savings calculation methodology
- 98 automations identification process
- 276 pain points extraction completeness
- 423% ROI calculation verification

### 6. PostgreSQL + pgvector Status
**Verify database migrations:**
```bash
psql -U postgres -d comversa_rag -c "\dt"
psql -U postgres -d comversa_rag -c "\d embeddings"
```

**Check**: 12 tables operational, HNSW vector indexing ready

## Success Criteria
✅ All 17 entity extractors tested and validated
✅ Knowledge graph consolidation verified (1,743 entities)
✅ RAG retrieval quality measured (Precision@5, MRR)
✅ Dashboard metrics confirmed accurate
✅ Confidence scores validated (85% average)
✅ Contradiction rate acceptable (8%)
✅ Comprehensive test report generated

## Deliverable
**Generate comprehensive quality report** documenting:
- Test coverage percentages
- Metric validation results
- Areas of concern requiring attention
- GO/NO-GO decision for platform launch

## Timeline
Weekend (Nov 15-17, 2025) - Friday evening + Saturday + Sunday morning

## Resources Needed
- pytest test suite
- SQLite/PostgreSQL/Neo4j query access
- scripts/evaluate_retrieval.py
- Weekend time allocation
