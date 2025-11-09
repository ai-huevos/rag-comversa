# Knowledge Graph Implementation Roadmap

**Date:** November 8, 2025  
**Project:** Intelligence Capture System - Knowledge Graph Consolidation  
**Designer:** Daniel (Manifestor, Quick Start 9, Strategic + Activator)  
**Status:** Design Review Complete - Ready for Implementation

---

## Executive Summary

This document provides a complete, phase-by-phase implementation roadmap for adding knowledge graph consolidation to the existing extraction pipeline. The system will merge duplicate entities (e.g., 25 "Excel" entries → 1 consolidated entry), track consensus across interviews, and discover relationships between entities.

**Key Decision:** Build consolidation DURING extraction (not after) to avoid duplicate work.

**Timeline:** 2-3 weeks (12-15 days)  
**Estimated Cost:** $1.20 for 44 interviews (vs $2.00 if done separately)  
**Complexity:** Medium - builds on proven extraction system

---

## 1. SYSTEM INTEGRATION MAP

### Current Flow (Without Knowledge Graph)
```
Interview JSON → Extractor (17 types) → SQLite → AI Agents
                                          ↓
                                    Duplicate data
                                    (25x Excel, 12x SAP)
```

### Enhanced Flow (With Knowledge Graph)
```
Interview JSON → Extractor (17 types) → Consolidation Agent → SQLite → AI Agents
                                              ↓
                                        Find duplicates
                                        Merge entities
                                        Track sources
                                        Build relationships
                                              ↓
                                        Consolidated data
                                        (1x Excel with 25 sources)
```

### Integration Points

**Files to Modify:**
- `intelligence_capture/processor.py` - Add consolidation step after extraction
- `intelligence_capture/database.py` - Add consolidation columns and tables
- `intelligence_capture/config.py` - Add consolidation configuration

**Files to Create:**
- `intelligence_capture/consolidation_agent.py` - Main consolidation logic
- `intelligence_capture/duplicate_detector.py` - Fuzzy matching
- `intelligence_capture/entity_merger.py` - Merge logic
- `tests/test_consolidation.py` - Unit tests


### Data Flow

**Question:** Do entities go to both SQLite AND graph? Or graph reads from SQLite?

**Answer:** Entities go to SQLite with consolidation metadata embedded:

```python
# During extraction (for each interview):
entities = extractor.extract_all(meta, qa_pairs)  # Extract 17 types

# NEW: Consolidation step
for entity_type, entity_list in entities.items():
    for entity in entity_list:
        # Check if similar entity exists
        similar = consolidation_agent.find_similar(entity, entity_type)
        
        if similar:
            # Merge with existing entity
            merged = consolidation_agent.merge(entity, similar)
            db.update_entity(merged)  # Update existing record
        else:
            # New entity, store it
            db.insert_entity(entity)  # Insert new record

# Entities stored in SQLite with consolidation metadata:
# - mentioned_in_interviews: [1, 3, 5, 7, ...]
# - source_count: 25
# - is_consolidated: true
# - consensus_confidence: 0.85
```

**No separate graph database** - consolidation metadata lives in SQLite alongside entities.

### Query Path

**Question:** Do AI agents query graph directly or through existing system?

**Answer:** AI agents query SQLite as before, but now get consolidated data:

```python
# Before consolidation:
systems = db.query("SELECT * FROM systems WHERE name LIKE '%Excel%'")
# Returns: 25 separate rows

# After consolidation:
systems = db.query("SELECT * FROM systems WHERE name = 'Excel'")
# Returns: 1 row with source_count=25, mentioned_in_interviews=[...]
```

### Migration Strategy

**Question:** Can we add graph without breaking extraction?

**Answer:** YES - consolidation is additive:

1. Add new columns to existing tables (ALTER TABLE)
2. Existing data remains unchanged
3. New extractions get consolidation
4. Can run consolidation on existing data later (optional)

**Backward Compatibility:**
- Existing queries still work (new columns have defaults)
- Extraction pipeline unchanged (consolidation is optional step)
- Can disable consolidation via config flag

---

## 2. PHASE-BY-PHASE IMPLEMENTATION PLAN

### Phase 1: Foundation (4-6 hours)

**Goal:** Basic consolidation working for one entity type (systems)

#### Task 1.1: Database Schema Enhancement
**File:** `intelligence_capture/database.py`  
**Code:**
```python
def add_consolidation_columns(self):
    """Add consolidation tracking columns to all entity tables"""
    cursor = self.conn.cursor()
    
    # Add to systems table first (test with one table)
    self._add_column_if_not_exists('systems', 'mentioned_in_interviews', 'TEXT')
    self._add_column_if_not_exists('systems', 'source_count', 'INTEGER DEFAULT 1')
    self._add_column_if_not_exists('systems', 'is_consolidated', 'INTEGER DEFAULT 0')
    self._add_column_if_not_exists('systems', 'consensus_confidence', 'REAL DEFAULT 1.0')
    
    self.conn.commit()
```

**Test:**
```python
def test_schema_migration():
    db = IntelligenceDB(":memory:")
    db.connect()
    db.init_schema()
    db.add_consolidation_columns()
    
    # Verify columns exist
    cursor = db.conn.cursor()
    cursor.execute("PRAGMA table_info(systems)")
    columns = [row[1] for row in cursor.fetchall()]
    
    assert 'mentioned_in_interviews' in columns
    assert 'source_count' in columns
    assert 'is_consolidated' in columns
```

**Time:** 1 hour  
**Success Criteria:** Schema migration runs without errors, columns added

---

#### Task 1.2: Duplicate Detector
**File:** `intelligence_capture/duplicate_detector.py`  
**Code:**
```python
from fuzzywuzzy import fuzz

class DuplicateDetector:
    def __init__(self, threshold=0.85):
        self.threshold = threshold
    
    def find_similar(self, entity_name, existing_entities):
        """Find similar entities using fuzzy matching"""
        matches = []
        
        for existing in existing_entities:
            similarity = fuzz.ratio(
                self._normalize(entity_name),
                self._normalize(existing['name'])
            ) / 100.0
            
            if similarity >= self.threshold:
                matches.append((existing, similarity))
        
        # Return top match
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[0] if matches else None
    
    def _normalize(self, name):
        """Normalize entity name for comparison"""
        return name.lower().strip()
```

**Test:**
```python
def test_duplicate_detection():
    detector = DuplicateDetector(threshold=0.85)
    
    existing = [
        {'id': 1, 'name': 'Excel'},
        {'id': 2, 'name': 'SAP'}
    ]
    
    # Should match Excel
    match = detector.find_similar('Excel spreadsheet', existing)
    assert match is not None
    assert match[0]['name'] == 'Excel'
    
    # Should not match
    match = detector.find_similar('WhatsApp', existing)
    assert match is None
```

**Time:** 2 hours  
**Success Criteria:** Fuzzy matching works, returns correct matches

---

#### Task 1.3: Entity Merger
**File:** `intelligence_capture/entity_merger.py`  
**Code:**
```python
import json

class EntityMerger:
    def merge(self, new_entity, existing_entity, interview_id):
        """Merge new entity into existing entity"""
        # Parse existing interviews list
        interviews = json.loads(existing_entity.get('mentioned_in_interviews', '[]'))
        
        # Add new interview
        if interview_id not in interviews:
            interviews.append(interview_id)
        
        # Update entity
        merged = existing_entity.copy()
        merged['mentioned_in_interviews'] = json.dumps(interviews)
        merged['source_count'] = len(interviews)
        merged['is_consolidated'] = True
        merged['consensus_confidence'] = min(len(interviews) / 10.0, 1.0)
        
        return merged
```

**Test:**
```python
def test_entity_merge():
    merger = EntityMerger()
    
    existing = {
        'id': 1,
        'name': 'Excel',
        'mentioned_in_interviews': '[1, 3]',
        'source_count': 2
    }
    
    new = {'name': 'Excel spreadsheet'}
    
    merged = merger.merge(new, existing, interview_id=5)
    
    assert merged['source_count'] == 3
    assert 5 in json.loads(merged['mentioned_in_interviews'])
    assert merged['is_consolidated'] == True
```

**Time:** 1 hour  
**Success Criteria:** Merge logic works, updates source tracking

---

#### Task 1.4: Consolidation Agent
**File:** `intelligence_capture/consolidation_agent.py`  
**Code:**
```python
from .duplicate_detector import DuplicateDetector
from .entity_merger import EntityMerger

class ConsolidationAgent:
    def __init__(self, db, threshold=0.85):
        self.db = db
        self.detector = DuplicateDetector(threshold)
        self.merger = EntityMerger()
    
    def consolidate_entity(self, entity, entity_type, interview_id):
        """Consolidate single entity"""
        # Get existing entities of same type
        existing = self.db.get_all_entities(entity_type)
        
        # Find similar entity
        match = self.detector.find_similar(entity['name'], existing)
        
        if match:
            # Merge with existing
            existing_entity, similarity = match
            merged = self.merger.merge(entity, existing_entity, interview_id)
            self.db.update_entity(entity_type, merged['id'], merged)
            return merged
        else:
            # Insert new entity
            entity['mentioned_in_interviews'] = json.dumps([interview_id])
            entity['source_count'] = 1
            entity['is_consolidated'] = False
            entity['consensus_confidence'] = 0.5  # Single source
            return self.db.insert_entity(entity_type, entity)
```

**Test:**
```python
def test_consolidation():
    db = IntelligenceDB(":memory:")
    db.connect()
    db.init_schema()
    db.add_consolidation_columns()
    
    agent = ConsolidationAgent(db)
    
    # First entity
    entity1 = {'name': 'Excel', 'domain': 'Office'}
    result1 = agent.consolidate_entity(entity1, 'systems', interview_id=1)
    assert result1['source_count'] == 1
    
    # Duplicate entity
    entity2 = {'name': 'Excel spreadsheet', 'domain': 'Office'}
    result2 = agent.consolidate_entity(entity2, 'systems', interview_id=2)
    assert result2['source_count'] == 2
    assert result2['is_consolidated'] == True
```

**Time:** 2 hours  
**Success Criteria:** End-to-end consolidation works for systems table

---

**Phase 1 Total:** 6 hours  
**Phase 1 Success:** Can consolidate systems table, Excel goes from 25 → 1

---

