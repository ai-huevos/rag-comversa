# Design Document: Knowledge Graph Consolidation System

## Overview

The Knowledge Graph Consolidation System is a post-extraction intelligence layer that transforms fragmented entity data from 44 interviews into a unified, consensus-driven knowledge graph. The system addresses a critical data quality issue: 20-30% of extracted entities are duplicates (e.g., 25 separate "Excel" entries, 12 separate "SAP" entries), making it impossible to answer business questions like "What systems cause the most pain?"

**Key Design Principles:**
1. **Non-destructive**: Original entities preserved in audit trail
2. **Incremental**: New interviews consolidate with existing data
3. **Transparent**: All merge decisions logged with similarity scores
4. **Configurable**: Tunable thresholds per entity type
5. **Fast**: Sub-second duplicate detection, <5 min total for 44 interviews

## Architecture

### High-Level Flow

```
Interview → Extraction → Consolidation → Storage
                ↓            ↓              ↓
            Raw Entities  Duplicate    Consolidated
                         Detection      Entities
                             ↓
                         Merging +
                         Consensus
                         Scoring
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    IntelligenceProcessor                     │
│  (Orchestrates extraction + consolidation)                   │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         ↓                       ↓
┌────────────────────┐  ┌──────────────────────────┐
│ IntelligenceExtractor│  │ KnowledgeConsolidationAgent│
│ (Extracts entities)  │  │ (Merges duplicates)       │
└────────────────────┘  └──────────┬───────────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    ↓              ↓              ↓
            ┌───────────┐  ┌──────────────┐  ┌─────────────┐
            │ Duplicate  │  │   Entity     │  │ Relationship│
            │ Detector   │  │   Merger     │  │  Discovery  │
            └───────────┘  └──────────────┘  └─────────────┘
                    │              │              │
                    └──────────────┼──────────────┘
                                   ↓
                          ┌─────────────────┐
                          │  IntelligenceDB │
                          │  (SQLite + WAL) │
                          └─────────────────┘
```

## Components and Interfaces

### 1. KnowledgeConsolidationAgent

**Purpose**: Main orchestrator for consolidation logic

**Interface**:
```python
class KnowledgeConsolidationAgent:
    def __init__(self, db: IntelligenceDB, config: Dict):
        """
        Initialize consolidation agent
        
        Args:
            db: Database connection
            config: Configuration with similarity thresholds per entity type
        """
        
    def consolidate_entities(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int
    ) -> Dict[str, List[Dict]]:
        """
        Consolidate newly extracted entities with existing database
        
        Args:
            entities: Dict of entity_type -> list of entities
            interview_id: Source interview ID
            
        Returns:
            Dict of entity_type -> list of consolidated entities
        """
        
    def find_similar_entities(
        self,
        entity: Dict,
        entity_type: str
    ) -> List[Tuple[Dict, float]]:
        """
        Find existing entities similar to new entity
        
        Args:
            entity: New entity to match
            entity_type: Type of entity (systems, pain_points, etc.)
            
        Returns:
            List of (existing_entity, similarity_score) tuples, sorted by score
        """
        
    def merge_entities(
        self,
        new_entity: Dict,
        existing_entity: Dict,
        similarity_score: float
    ) -> Dict:
        """
        Merge new entity into existing entity
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            similarity_score: Similarity between entities
            
        Returns:
            Updated consolidated entity
        """
        
    def calculate_consensus_confidence(
        self,
        entity: Dict
    ) -> float:
        """
        Calculate consensus confidence score
        
        Args:
            entity: Consolidated entity with source tracking
            
        Returns:
            Confidence score (0.0-1.0)
        """
```

### 2. DuplicateDetector

**Purpose**: Identifies similar entities using fuzzy matching and semantic similarity

**Interface**:
```python
class DuplicateDetector:
    def __init__(self, config: Dict):
        """
        Initialize duplicate detector
        
        Args:
            config: Configuration with similarity thresholds
        """
        
    def find_duplicates(
        self,
        entity: Dict,
        entity_type: str,
        existing_entities: List[Dict]
    ) -> List[Tuple[Dict, float]]:
        """
        Find duplicate entities using fuzzy + semantic matching
        
        Args:
            entity: Entity to match
            entity_type: Type of entity
            existing_entities: List of existing entities to compare
            
        Returns:
            List of (entity, similarity_score) tuples above threshold
        """
        
    def calculate_name_similarity(
        self,
        name1: str,
        name2: str,
        entity_type: str
    ) -> float:
        """
        Calculate fuzzy string similarity with entity-specific normalization
        
        Args:
            name1: First entity name
            name2: Second entity name
            entity_type: Type of entity (for normalization rules)
            
        Returns:
            Similarity score (0.0-1.0)
        """
        
    def calculate_semantic_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        Calculate semantic similarity using embeddings
        
        Args:
            text1: First text (description)
            text2: Second text (description)
            
        Returns:
            Cosine similarity (0.0-1.0)
        """
```

### 3. EntityMerger

**Purpose**: Merges duplicate entities and tracks sources

**Interface**:
```python
class EntityMerger:
    def merge(
        self,
        new_entity: Dict,
        existing_entity: Dict,
        interview_id: int
    ) -> Dict:
        """
        Merge new entity into existing entity
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            interview_id: Source interview ID
            
        Returns:
            Updated consolidated entity
        """
        
    def combine_descriptions(
        self,
        desc1: str,
        desc2: str
    ) -> str:
        """
        Combine descriptions by concatenating unique information
        
        Args:
            desc1: First description
            desc2: Second description
            
        Returns:
            Combined description
        """
        
    def detect_contradictions(
        self,
        new_entity: Dict,
        existing_entity: Dict
    ) -> Optional[Dict]:
        """
        Detect contradictions between entity attributes
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            
        Returns:
            Contradiction details dict or None
        """
        
    def update_source_tracking(
        self,
        entity: Dict,
        interview_id: int
    ) -> Dict:
        """
        Update source tracking fields
        
        Args:
            entity: Entity to update
            interview_id: Source interview ID
            
        Returns:
            Updated entity with source tracking
        """
```

### 4. ConsensusScorer

**Purpose**: Calculates confidence scores based on source agreement

**Interface**:
```python
class ConsensusScorer:
    def calculate_confidence(
        self,
        entity: Dict
    ) -> float:
        """
        Calculate consensus confidence score
        
        Formula:
        - Base score: min(source_count / 10, 1.0)
        - Attribute agreement bonus: +0.1 per agreeing attribute (max +0.3)
        - Contradiction penalty: -0.15 per conflicting attribute
        
        Args:
            entity: Consolidated entity with source tracking
            
        Returns:
            Confidence score (0.0-1.0)
        """
        
    def check_attribute_agreement(
        self,
        entity: Dict
    ) -> int:
        """
        Count attributes that agree across sources
        
        Args:
            entity: Consolidated entity
            
        Returns:
            Number of agreeing attributes
        """
```

### 5. RelationshipDiscoverer

**Purpose**: Discovers relationships between entities

**Interface**:
```python
class RelationshipDiscoverer:
    def discover_relationships(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int
    ) -> List[Dict]:
        """
        Discover relationships between entities in same interview
        
        Args:
            entities: Dict of entity_type -> list of entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        
    def create_relationship(
        self,
        source_entity: Dict,
        source_type: str,
        target_entity: Dict,
        target_type: str,
        relationship_type: str,
        strength: float
    ) -> Dict:
        """
        Create relationship between two entities
        
        Args:
            source_entity: Source entity
            source_type: Source entity type
            target_entity: Target entity
            target_type: Target entity type
            relationship_type: Type of relationship (causes, uses, etc.)
            strength: Relationship strength (0.0-1.0)
            
        Returns:
            Relationship dict
        """
```

### 6. PatternRecognizer

**Purpose**: Identifies recurring patterns across interviews

**Interface**:
```python
class PatternRecognizer:
    def __init__(self, db: IntelligenceDB):
        """Initialize pattern recognizer with database access"""
        
    def identify_patterns(self) -> List[Dict]:
        """
        Identify recurring patterns across all interviews
        
        Returns:
            List of pattern dicts with frequency and priority
        """
        
    def find_recurring_pain_points(
        self,
        threshold: int = 3
    ) -> List[Dict]:
        """
        Find pain points mentioned by threshold+ people
        
        Args:
            threshold: Minimum number of mentions
            
        Returns:
            List of recurring pain points
        """
        
    def find_problematic_systems(
        self,
        threshold: int = 5
    ) -> List[Dict]:
        """
        Find systems with negative sentiment in threshold+ interviews
        
        Args:
            threshold: Minimum number of negative mentions
            
        Returns:
            List of problematic systems
        """
```

## Data Models

### Enhanced Entity Schema

All entity tables get these additional columns:

```sql
-- Source tracking
mentioned_in_interviews TEXT,  -- JSON array of interview IDs
source_count INTEGER DEFAULT 1,
first_mentioned_date TEXT,
last_mentioned_date TEXT,

-- Consolidation metadata
is_consolidated BOOLEAN DEFAULT false,
merged_entity_ids TEXT,  -- JSON array of original entity IDs
consensus_confidence REAL DEFAULT 1.0,

-- Contradiction tracking
has_contradictions BOOLEAN DEFAULT false,
contradiction_details TEXT,  -- JSON with conflicting attributes

-- Timestamps
consolidated_at TIMESTAMP
```

### Relationships Table

```sql
CREATE TABLE relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_entity_id INTEGER NOT NULL,
    source_entity_type TEXT NOT NULL,
    relationship_type TEXT NOT NULL,
    target_entity_id INTEGER NOT NULL,
    target_entity_type TEXT NOT NULL,
    strength REAL DEFAULT 1.0,
    mentioned_in_interviews TEXT,  -- JSON array
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_relationships_source ON relationships(source_entity_id, source_entity_type);
CREATE INDEX idx_relationships_target ON relationships(target_entity_id, target_entity_type);
```

### Consolidation Audit Table

```sql
CREATE TABLE consolidation_audit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    merged_entity_ids TEXT NOT NULL,  -- JSON array
    resulting_entity_id INTEGER NOT NULL,
    similarity_score REAL NOT NULL,
    consolidation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rollback_timestamp TIMESTAMP,
    rollback_reason TEXT
);

CREATE INDEX idx_audit_entity_type ON consolidation_audit(entity_type);
CREATE INDEX idx_audit_timestamp ON consolidation_audit(consolidation_timestamp);
```

### Patterns Table

```sql
CREATE TABLE patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,  -- recurring_pain, problematic_system, etc.
    entity_type TEXT NOT NULL,
    entity_id INTEGER NOT NULL,
    pattern_frequency REAL NOT NULL,  -- 0.0-1.0 (% of interviews)
    source_count INTEGER NOT NULL,
    high_priority BOOLEAN DEFAULT false,
    description TEXT,
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patterns_type ON patterns(pattern_type);
CREATE INDEX idx_patterns_priority ON patterns(high_priority, pattern_frequency);
```

## Algorithms

### 1. Duplicate Detection Algorithm

```python
def find_duplicates(entity, entity_type, existing_entities):
    """
    Two-stage matching: fuzzy name matching + semantic similarity
    """
    candidates = []
    
    # Stage 1: Fuzzy name matching
    for existing in existing_entities:
        name_sim = calculate_fuzzy_similarity(
            normalize_name(entity['name'], entity_type),
            normalize_name(existing['name'], entity_type)
        )
        
        if name_sim >= threshold_for_type(entity_type):
            candidates.append((existing, name_sim))
    
    # Stage 2: Semantic similarity for ambiguous cases
    if len(candidates) > 1:
        for i, (existing, name_sim) in enumerate(candidates):
            semantic_sim = calculate_semantic_similarity(
                entity.get('description', ''),
                existing.get('description', '')
            )
            # Weighted average: 70% name, 30% semantic
            combined_sim = 0.7 * name_sim + 0.3 * semantic_sim
            candidates[i] = (existing, combined_sim)
    
    # Return top matches above threshold
    candidates.sort(key=lambda x: x[1], reverse=True)
    return candidates[:10]  # Limit to top 10
```

### 2. Name Normalization Algorithm

```python
def normalize_name(name, entity_type):
    """
    Entity-specific normalization rules
    """
    name = name.lower().strip()
    
    # Remove common prefixes/suffixes
    if entity_type == 'systems':
        # Remove: "sistema", "software", "herramienta", "plataforma"
        remove_words = ['sistema', 'software', 'herramienta', 'plataforma']
        for word in remove_words:
            name = name.replace(word, '').strip()
    
    elif entity_type == 'pain_points':
        # Remove: "problema de", "dificultad con", "issue with"
        remove_phrases = ['problema de', 'dificultad con', 'issue with']
        for phrase in remove_phrases:
            name = name.replace(phrase, '').strip()
    
    # Remove extra whitespace
    name = ' '.join(name.split())
    
    return name
```

### 3. Consensus Confidence Algorithm

```python
def calculate_consensus_confidence(entity):
    """
    Multi-factor confidence scoring
    """
    # Base score from source count (more sources = higher confidence)
    base_score = min(entity['source_count'] / 10.0, 1.0)
    
    # Attribute agreement bonus
    agreement_bonus = 0.0
    if entity.get('attribute_agreement_count', 0) > 0:
        agreement_bonus = min(
            entity['attribute_agreement_count'] * 0.1,
            0.3  # Max +0.3
        )
    
    # Contradiction penalty
    contradiction_penalty = 0.0
    if entity.get('has_contradictions'):
        contradiction_count = len(entity.get('contradiction_details', []))
        contradiction_penalty = contradiction_count * 0.15
    
    # Final score
    confidence = base_score + agreement_bonus - contradiction_penalty
    
    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, confidence))
```

### 4. Relationship Discovery Algorithm

```python
def discover_relationships(entities, interview_id):
    """
    Discover relationships based on co-occurrence in same interview
    """
    relationships = []
    
    # System → Pain Point relationships
    for system in entities.get('systems', []):
        for pain_point in entities.get('pain_points', []):
            # Check if pain point mentions system
            if system['name'].lower() in pain_point['description'].lower():
                relationships.append({
                    'source_entity_id': system['id'],
                    'source_entity_type': 'systems',
                    'relationship_type': 'causes',
                    'target_entity_id': pain_point['id'],
                    'target_entity_type': 'pain_points',
                    'strength': 0.8,
                    'mentioned_in_interviews': [interview_id]
                })
    
    # Process → System relationships
    for process in entities.get('processes', []):
        for system in entities.get('systems', []):
            # Check if process mentions system
            if system['name'].lower() in process['description'].lower():
                relationships.append({
                    'source_entity_id': process['id'],
                    'source_entity_type': 'processes',
                    'relationship_type': 'uses',
                    'target_entity_id': system['id'],
                    'target_entity_type': 'systems',
                    'strength': 0.7,
                    'mentioned_in_interviews': [interview_id]
                })
    
    return relationships
```

## Error Handling

### Consolidation Errors

1. **Similarity Calculation Failure**
   - Fallback: Skip semantic similarity, use name matching only
   - Log: Warning with entity details
   - Continue: Process remaining entities

2. **Database Lock During Merge**
   - Retry: Up to 3 times with exponential backoff
   - Fallback: Queue entity for later consolidation
   - Alert: If retry limit exceeded

3. **Contradiction Detection Failure**
   - Fallback: Merge without contradiction tracking
   - Log: Warning with entity details
   - Flag: needs_review = true

4. **Relationship Discovery Failure**
   - Fallback: Skip relationship creation
   - Log: Warning with entity details
   - Continue: Process remaining relationships

### Rollback Scenarios

1. **Incorrect Merge Detected**
   - Action: Restore original entities from audit table
   - Update: All relationships to point to original entities
   - Log: Rollback operation with reason

2. **Data Corruption**
   - Action: Restore from last known good state
   - Verify: Database integrity checks
   - Alert: System administrator

## Testing Strategy

### Unit Tests

1. **DuplicateDetector Tests**
   - Test fuzzy matching with various similarity levels
   - Test name normalization for each entity type
   - Test semantic similarity calculation
   - Test threshold configuration

2. **EntityMerger Tests**
   - Test description combination
   - Test contradiction detection
   - Test source tracking updates
   - Test attribute merging

3. **ConsensusScorer Tests**
   - Test confidence calculation with various source counts
   - Test agreement bonus calculation
   - Test contradiction penalty
   - Test edge cases (0 sources, 100 sources)

4. **RelationshipDiscoverer Tests**
   - Test System → Pain Point discovery
   - Test Process → System discovery
   - Test relationship strength calculation
   - Test duplicate relationship prevention

### Integration Tests

1. **End-to-End Consolidation**
   - Extract entities from 5 test interviews
   - Run consolidation
   - Verify duplicate reduction
   - Verify source tracking
   - Verify consensus scores

2. **Incremental Consolidation**
   - Consolidate initial batch
   - Add new interview
   - Verify incremental merge
   - Verify confidence score updates

3. **Relationship Discovery**
   - Extract entities with known relationships
   - Run relationship discovery
   - Verify relationships created
   - Verify relationship strength

4. **Pattern Recognition**
   - Create test data with recurring patterns
   - Run pattern recognition
   - Verify patterns detected
   - Verify priority flagging

### Performance Tests

1. **Duplicate Detection Performance**
   - Measure time to find duplicates in 1000 entities
   - Target: <1 second per entity
   - Verify: Database index usage

2. **Full Consolidation Performance**
   - Measure time to consolidate 44 interviews
   - Target: <5 minutes total
   - Verify: No memory leaks

3. **Incremental Update Performance**
   - Measure time to add new interview to consolidated data
   - Target: <10 seconds per interview
   - Verify: No performance degradation over time

## Configuration

### consolidation_config.json

```json
{
  "consolidation": {
    "enabled": true,
    "similarity_thresholds": {
      "systems": 0.85,
      "pain_points": 0.80,
      "processes": 0.85,
      "kpis": 0.90,
      "automation_candidates": 0.80,
      "inefficiencies": 0.80,
      "communication_channels": 0.85,
      "decision_points": 0.80,
      "data_flows": 0.85,
      "temporal_patterns": 0.85,
      "failure_modes": 0.80,
      "team_structures": 0.90,
      "knowledge_gaps": 0.80,
      "success_patterns": 0.80,
      "budget_constraints": 0.85,
      "external_dependencies": 0.85
    },
    "semantic_similarity_weight": 0.3,
    "name_similarity_weight": 0.7,
    "max_candidates": 10,
    "consensus_confidence": {
      "source_count_divisor": 10,
      "agreement_bonus_per_attribute": 0.1,
      "max_agreement_bonus": 0.3,
      "contradiction_penalty_per_attribute": 0.15
    },
    "pattern_recognition": {
      "recurring_pain_threshold": 3,
      "problematic_system_threshold": 5,
      "high_priority_frequency": 0.30
    }
  }
}
```

## Deployment Considerations

### Database Migration

1. **Add Consolidation Columns**
   - Run migration script to add columns to all entity tables
   - Create relationships table
   - Create consolidation_audit table
   - Create patterns table
   - Create indexes for performance

2. **Backward Compatibility**
   - Existing queries continue to work
   - New columns have default values
   - No data loss during migration

### Performance Optimization

1. **Database Indexes**
   - Index on entity names for fast duplicate detection
   - Index on source_count for pattern queries
   - Index on consensus_confidence for quality filtering

2. **Caching**
   - Cache fuzzy matching results for common names
   - Cache semantic embeddings for descriptions
   - Clear cache after each interview batch

3. **Batch Processing**
   - Process entities in batches of 100
   - Commit transactions after each batch
   - Use WAL mode for concurrent access

### Monitoring

1. **Consolidation Metrics**
   - Duplicate reduction percentage
   - Average consensus confidence
   - Contradiction rate
   - Processing time per interview

2. **Quality Metrics**
   - Entities with confidence < 0.6
   - Entities with contradictions
   - Relationships discovered
   - Patterns identified

3. **Performance Metrics**
   - Duplicate detection time
   - Merge operation time
   - Database query time
   - Total consolidation time
