# Knowledge Graph Enrichment System
## Incremental, Interconnected Intelligence Building

**Vision**: Every new interview makes the entire knowledge graph smarter by cross-referencing, consolidating, and building relationships with all previous knowledge.

---

## Architecture

### Enhanced Multi-Agent Workflow

```
New Interview Arrives
         │
         ▼
┌────────────────────┐
│ Extraction Agents  │ ← Extract entities from new interview
│ (17 specialized)   │
└────────┬───────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Knowledge Consolidation Agent (NEW!)          │
│ • Find duplicate entities across interviews   │
│ • Merge knowledge from multiple sources       │
│ • Calculate consensus scores                  │
│ • Identify contradictions                     │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Relationship Discovery Agent (NEW!)           │
│ • Discover connections between interviews     │
│ • Build team collaboration network            │
│ • Map process dependencies                    │
│ • Identify cross-department patterns          │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Pattern Recognition Agent (NEW!)              │
│ • Detect recurring pain points                │
│ • Identify system usage patterns              │
│ • Find consensus on priorities                │
│ • Calculate aggregate metrics                 │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Contradiction Detector (NEW!)                 │
│ • Find inconsistent information               │
│ • Flag for human review                       │
│ • Suggest reconciliation                      │
└────────┬───────────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────────────┐
│ Knowledge Graph Update                        │
│ • Merge new entities with existing ones       │
│ • Update relationships                        │
│ • Recalculate confidence scores               │
│ • Update aggregate statistics                 │
└────────────────────────────────────────────────┘
```

---

## Key Agents

### 1. Knowledge Consolidation Agent

**Purpose**: Merge duplicate entities and enrich knowledge from multiple sources

**Algorithm**:
```python
class KnowledgeConsolidationAgent:
    """
    Consolidates entities across interviews to build unified knowledge
    """

    def consolidate_entity(
        self,
        new_entity: Dict,
        entity_type: str,
        new_interview_id: int
    ) -> ConsolidationResult:
        """
        Consolidate new entity with existing knowledge

        Process:
        1. Find similar entities in knowledge graph
        2. Calculate similarity scores
        3. Decide: New entity OR merge with existing
        4. If merge: Enrich existing entity
        5. Update confidence and consensus scores
        """

        # Step 1: Find similar entities
        similar = self.find_similar_entities(
            new_entity,
            entity_type,
            threshold=0.8
        )

        if not similar:
            # Truly new entity - add to graph
            return self.add_new_entity(new_entity, new_interview_id)

        # Step 2: Find best match
        best_match = max(similar, key=lambda x: x['similarity_score'])

        if best_match['similarity_score'] > 0.9:
            # High confidence match - merge
            return self.merge_entities(
                existing=best_match['entity'],
                new=new_entity,
                interview_id=new_interview_id
            )
        else:
            # Similar but different - create new with relationship
            return self.add_related_entity(
                new_entity,
                related_to=best_match['entity'],
                interview_id=new_interview_id
            )

    def merge_entities(
        self,
        existing: Dict,
        new: Dict,
        interview_id: int
    ) -> MergeResult:
        """
        Merge new entity into existing one

        Merge Strategy:
        - Append to lists (pain_points, participants, etc.)
        - Average numerical values (scores)
        - Concatenate descriptions (with source attribution)
        - Increase confidence (more sources = higher confidence)
        - Track which interviews mentioned this entity
        """

        merged = existing.copy()

        # Track source interviews
        merged['mentioned_in_interviews'].append(interview_id)
        merged['source_count'] = len(merged['mentioned_in_interviews'])

        # Merge pain points (deduplicate)
        existing_pains = set(existing.get('pain_points', []))
        new_pains = set(new.get('pain_points', []))
        merged['pain_points'] = list(existing_pains | new_pains)

        # Merge participants (deduplicate)
        existing_participants = set(existing.get('participants', []))
        new_participants = set(new.get('participants', []))
        merged['participants'] = list(existing_participants | new_participants)

        # Update confidence based on consensus
        merged['confidence_score'] = self.calculate_consensus_confidence(
            source_count=merged['source_count'],
            agreement_score=self.calculate_agreement(existing, new)
        )

        # Validate cross-source consistency
        if self.has_contradictions(existing, new):
            merged['has_contradictions'] = True
            merged['needs_review'] = True
            merged['contradictions'] = self.identify_contradictions(existing, new)

        # Update enrichment metadata
        merged['last_enriched'] = datetime.now()
        merged['enrichment_count'] += 1

        return MergeResult(
            merged_entity=merged,
            action='merged',
            enriched_fields=self.identify_enriched_fields(existing, merged)
        )

    def find_similar_entities(
        self,
        entity: Dict,
        entity_type: str,
        threshold: float = 0.8
    ) -> List[Dict]:
        """
        Find similar entities in knowledge graph

        Similarity Strategies by Entity Type:

        - Systems: Name matching + vendor matching
        - Pain Points: Description semantic similarity
        - Processes: Name + domain matching
        - Communication Channels: Channel + participants matching
        - Decision Points: Decision maker + decision type matching
        """

        existing_entities = self.db.get_all_entities(entity_type)
        similar = []

        for existing in existing_entities:
            similarity = self.calculate_similarity(
                entity,
                existing,
                entity_type
            )

            if similarity >= threshold:
                similar.append({
                    'entity': existing,
                    'similarity_score': similarity
                })

        return similar

    def calculate_similarity(
        self,
        entity1: Dict,
        entity2: Dict,
        entity_type: str
    ) -> float:
        """
        Calculate similarity between two entities

        Multi-level similarity:
        1. Exact match (name, ID) → 1.0
        2. Semantic similarity (embeddings) → 0.7-0.95
        3. Attribute overlap → 0.5-0.8
        """

        # Level 1: Exact name match
        if entity_type in ['systems', 'processes', 'communication_channels']:
            name1 = self.normalize_name(entity1.get('name', ''))
            name2 = self.normalize_name(entity2.get('name', ''))

            if name1 == name2 and name1:
                return 1.0

        # Level 2: Semantic similarity (use embeddings)
        desc1 = entity1.get('description', '')
        desc2 = entity2.get('description', '')

        if desc1 and desc2:
            semantic_sim = self.semantic_similarity(desc1, desc2)

            # If very high semantic similarity, likely same entity
            if semantic_sim > 0.9:
                return semantic_sim

        # Level 3: Attribute overlap
        attribute_sim = self.calculate_attribute_overlap(entity1, entity2, entity_type)

        # Weighted combination
        return 0.5 * semantic_sim + 0.5 * attribute_sim

    def calculate_consensus_confidence(
        self,
        source_count: int,
        agreement_score: float
    ) -> float:
        """
        Calculate confidence based on consensus

        More sources + high agreement = higher confidence

        Formula:
        confidence = min(1.0, 0.5 + (source_count * 0.1) + (agreement_score * 0.4))

        Examples:
        - 1 source, N/A agreement: 0.5
        - 2 sources, 100% agreement: 0.9
        - 5 sources, 80% agreement: 1.0
        """

        base_confidence = 0.5
        source_bonus = min(0.4, source_count * 0.1)
        agreement_bonus = agreement_score * 0.4

        return min(1.0, base_confidence + source_bonus + agreement_bonus)
```

---

### 2. Relationship Discovery Agent

**Purpose**: Discover and build relationships between entities and interviews

**Implementation**:
```python
class RelationshipDiscoveryAgent:
    """
    Discovers relationships between entities across interviews
    """

    def discover_relationships(
        self,
        new_interview_id: int,
        entities: Dict[str, List[Dict]]
    ) -> List[Relationship]:
        """
        Discover relationships with existing knowledge

        Relationships to discover:
        1. Team Coordination: Who works with whom
        2. Process Dependencies: Which processes depend on others
        3. System Integration: Which systems connect
        4. Shared Pain Points: Which teams have same issues
        5. Communication Patterns: Who communicates how
        """

        relationships = []

        # 1. Team Coordination Relationships
        team_rels = self.discover_team_coordination(
            new_interview_id,
            entities.get('communication_channels', []),
            entities.get('team_structures', [])
        )
        relationships.extend(team_rels)

        # 2. Process Dependencies
        process_rels = self.discover_process_dependencies(
            entities.get('processes', []),
            entities.get('data_flows', [])
        )
        relationships.extend(process_rels)

        # 3. Shared Pain Points
        pain_rels = self.discover_shared_pain_points(
            new_interview_id,
            entities.get('pain_points', [])
        )
        relationships.extend(pain_rels)

        # 4. System Integration
        system_rels = self.discover_system_integration(
            entities.get('data_flows', []),
            entities.get('systems', [])
        )
        relationships.extend(system_rels)

        return relationships

    def discover_team_coordination(
        self,
        new_interview_id: int,
        comm_channels: List[Dict],
        team_structures: List[Dict]
    ) -> List[Relationship]:
        """
        Discover which teams coordinate with each other

        Example:
        Interview 14: "Coordino con Housekeeping por WhatsApp"
        Interview 21: "Recibo solicitudes de Recepción por WhatsApp"

        → Create relationship: Recepción ↔ Housekeeping (via WhatsApp)
        → Mark as validated (both sides confirm)
        """

        relationships = []
        new_interview = self.db.get_interview(new_interview_id)
        new_role = new_interview['role']
        new_dept = new_interview['department']

        # Find coordination mentions in communication channels
        for channel in comm_channels:
            participants = channel.get('participants', [])

            # Find if any existing interviews mention coordinating with new interview's role
            for participant in participants:
                if participant != new_role:
                    # Search existing interviews for this coordination
                    existing_coordination = self.find_coordination_mentions(
                        role1=new_role,
                        role2=participant,
                        channel=channel['channel_name']
                    )

                    if existing_coordination:
                        # Create validated relationship
                        relationships.append(Relationship(
                            type='coordinates_with',
                            entity1=new_role,
                            entity2=participant,
                            channel=channel['channel_name'],
                            mentioned_in_interviews=[new_interview_id] + existing_coordination['interview_ids'],
                            validated=True,  # Both sides confirm
                            validation_type='cross_validated',
                            confidence=0.95
                        ))
                    else:
                        # Create unvalidated relationship (only one side mentioned)
                        relationships.append(Relationship(
                            type='coordinates_with',
                            entity1=new_role,
                            entity2=participant,
                            channel=channel['channel_name'],
                            mentioned_in_interviews=[new_interview_id],
                            validated=False,
                            validation_type='single_source',
                            confidence=0.7
                        ))

        return relationships

    def discover_shared_pain_points(
        self,
        new_interview_id: int,
        pain_points: List[Dict]
    ) -> List[Relationship]:
        """
        Find pain points mentioned by multiple people

        This reveals critical patterns:
        - Same issue in multiple departments → Systemic problem
        - Same issue mentioned 5+ times → High priority
        - Issue mentioned by manager + staff → Validated
        """

        relationships = []

        for pain_point in pain_points:
            # Find similar pain points in other interviews
            similar_pains = self.find_similar_pain_points(
                pain_point,
                threshold=0.85
            )

            if similar_pains:
                # Create pattern relationship
                relationships.append(Relationship(
                    type='shared_pain_point',
                    pattern_name=pain_point['description'],
                    mentioned_in_interviews=[new_interview_id] + [p['interview_id'] for p in similar_pains],
                    frequency=len(similar_pains) + 1,
                    departments=self.get_departments_for_interviews([new_interview_id] + [p['interview_id'] for p in similar_pains]),
                    priority_score=self.calculate_pattern_priority(len(similar_pains) + 1),
                    is_pattern=True,
                    confidence=0.9
                ))

        return relationships
```

---

### 3. Pattern Recognition Agent

**Purpose**: Identify recurring patterns and aggregate insights

**Implementation**:
```python
class PatternRecognitionAgent:
    """
    Recognizes patterns across interviews to surface insights
    """

    def recognize_patterns(
        self,
        current_interview_count: int
    ) -> List[Pattern]:
        """
        Recognize patterns after processing new interview

        Patterns to detect:
        1. Recurring pain points (mentioned by N+ people)
        2. System usage patterns (popularity, issues)
        3. Communication patterns (preferred channels)
        4. Process patterns (common workflows)
        5. Success patterns (what works well)
        """

        patterns = []

        # Only run pattern detection after minimum interview count
        if current_interview_count < 5:
            return patterns

        # 1. Pain Point Patterns
        pain_patterns = self.detect_pain_point_patterns()
        patterns.extend(pain_patterns)

        # 2. System Usage Patterns
        system_patterns = self.detect_system_usage_patterns()
        patterns.extend(system_patterns)

        # 3. Communication Patterns
        comm_patterns = self.detect_communication_patterns()
        patterns.extend(comm_patterns)

        # 4. Success Patterns
        success_patterns = self.detect_success_patterns()
        patterns.extend(success_patterns)

        return patterns

    def detect_pain_point_patterns(self) -> List[Pattern]:
        """
        Detect recurring pain points

        Example Output:
        {
          "pattern_type": "recurring_pain_point",
          "description": "Pérdida de trazabilidad en WhatsApp",
          "frequency": 7,  # 7 people mentioned this
          "interviews": [2, 5, 14, 18, 21, 33, 40],
          "departments": ["Recepción", "Housekeeping", "Ingeniería"],
          "companies": ["Hotel Los Tajibos"],
          "priority_score": 9.5,  # HIGH - affects multiple departments
          "recommended_action": "Implement WhatsApp alternative with tracking"
        }
        """

        patterns = []

        # Group pain points by semantic similarity
        pain_clusters = self.cluster_pain_points_by_similarity(
            threshold=0.8
        )

        for cluster in pain_clusters:
            if len(cluster['pain_points']) >= 3:  # Mentioned by 3+ people
                pattern = Pattern(
                    pattern_type='recurring_pain_point',
                    description=cluster['representative_description'],
                    frequency=len(cluster['pain_points']),
                    interviews=cluster['interview_ids'],
                    departments=cluster['departments'],
                    companies=cluster['companies'],
                    severity=self.calculate_cluster_severity(cluster),
                    priority_score=self.calculate_pattern_priority(
                        frequency=len(cluster['pain_points']),
                        departments=len(cluster['departments']),
                        severity=cluster['avg_severity']
                    ),
                    recommended_action=self.generate_recommendation(cluster),
                    confidence=0.85 + (len(cluster['pain_points']) * 0.03)  # More mentions = higher confidence
                )

                patterns.append(pattern)

        return patterns

    def detect_system_usage_patterns(self) -> List[Pattern]:
        """
        Detect system usage and satisfaction patterns

        Example Output:
        {
          "pattern_type": "system_dissatisfaction",
          "system_name": "Opera PMS",
          "mentioned_in_interviews": 12,
          "avg_satisfaction": 3.2,  # Out of 10
          "common_complaints": ["Lento", "Complicado", "Fallas frecuentes"],
          "priority_score": 9.8,  # CRITICAL - widely used, widely disliked
          "recommended_action": "Evaluar alternativas a Opera PMS"
        }
        """

        patterns = []

        # Get all systems mentioned across interviews
        systems = self.db.query("""
            SELECT
                name,
                COUNT(DISTINCT interview_id) as mention_count,
                AVG(satisfaction_score) as avg_satisfaction,
                GROUP_CONCAT(DISTINCT pain_points) as all_pain_points
            FROM systems
            WHERE company = ?
            GROUP BY name
            HAVING mention_count >= 3
            ORDER BY mention_count DESC
        """, (company,))

        for system in systems:
            # Low satisfaction + high usage = critical issue
            if system['avg_satisfaction'] < 5.0 and system['mention_count'] >= 5:
                pattern = Pattern(
                    pattern_type='system_dissatisfaction',
                    system_name=system['name'],
                    mentioned_in_interviews=system['mention_count'],
                    avg_satisfaction=system['avg_satisfaction'],
                    common_complaints=self.extract_common_complaints(system['all_pain_points']),
                    priority_score=self.calculate_system_priority(
                        usage=system['mention_count'],
                        satisfaction=system['avg_satisfaction']
                    ),
                    recommended_action=f"Evaluar alternativas a {system['name']}",
                    confidence=0.9
                )

                patterns.append(pattern)

        return patterns
```

---

### 4. Contradiction Detector

**Purpose**: Identify inconsistent information for review

**Implementation**:
```python
class ContradictionDetector:
    """
    Detects contradictions and inconsistencies across interviews
    """

    def detect_contradictions(
        self,
        new_interview_id: int,
        entities: Dict[str, List[Dict]]
    ) -> List[Contradiction]:
        """
        Detect contradictions between new interview and existing knowledge

        Types of contradictions:
        1. Conflicting information about same entity
        2. Different descriptions of same process
        3. Disagreement on priorities
        4. Inconsistent data (numbers don't match)
        """

        contradictions = []

        # Check each entity type for contradictions
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                # Find similar entities in existing knowledge
                similar = self.find_similar_entities(entity, entity_type)

                for existing in similar:
                    # Check for contradictions
                    conflicts = self.identify_conflicts(entity, existing)

                    if conflicts:
                        contradictions.append(Contradiction(
                            entity_type=entity_type,
                            field=conflicts['field'],
                            value1=conflicts['value1'],
                            value2=conflicts['value2'],
                            interview1=existing['interview_id'],
                            interview2=new_interview_id,
                            severity=conflicts['severity'],
                            recommended_resolution=conflicts['resolution']
                        ))

        return contradictions

    def identify_conflicts(
        self,
        entity1: Dict,
        entity2: Dict
    ) -> Optional[Dict]:
        """
        Identify specific fields that conflict

        Example:
        Interview 14: "Opera es lento"
        Interview 28: "Opera funciona bien, es rápido"

        → Contradiction detected
        """

        conflicts = []

        # Check numerical contradictions
        for field in ['frequency', 'cost', 'time', 'satisfaction_score']:
            if field in entity1 and field in entity2:
                diff = abs(entity1[field] - entity2[field])

                # If difference is significant, flag as contradiction
                if diff > entity1[field] * 0.5:  # 50% difference
                    conflicts.append({
                        'field': field,
                        'value1': entity1[field],
                        'value2': entity2[field],
                        'severity': 'medium',
                        'resolution': 'average_values'
                    })

        # Check categorical contradictions
        for field in ['severity', 'priority', 'status']:
            if field in entity1 and field in entity2:
                if entity1[field] != entity2[field]:
                    conflicts.append({
                        'field': field,
                        'value1': entity1[field],
                        'value2': entity2[field],
                        'severity': 'high',
                        'resolution': 'human_review'
                    })

        # Check semantic contradictions (using LLM)
        desc1 = entity1.get('description', '')
        desc2 = entity2.get('description', '')

        if desc1 and desc2:
            semantic_conflict = self.check_semantic_contradiction(desc1, desc2)
            if semantic_conflict:
                conflicts.append(semantic_conflict)

        return conflicts[0] if conflicts else None
```

---

## Database Schema Changes

### Add Consolidation Tracking

```sql
-- Add to all entity tables
ALTER TABLE pain_points ADD COLUMN mentioned_in_interviews TEXT; -- JSON array of interview IDs
ALTER TABLE pain_points ADD COLUMN source_count INTEGER DEFAULT 1;
ALTER TABLE pain_points ADD COLUMN last_enriched TIMESTAMP;
ALTER TABLE pain_points ADD COLUMN enrichment_count INTEGER DEFAULT 0;
ALTER TABLE pain_points ADD COLUMN consensus_confidence REAL DEFAULT 0.0;
ALTER TABLE pain_points ADD COLUMN has_contradictions INTEGER DEFAULT 0;
ALTER TABLE pain_points ADD COLUMN is_pattern INTEGER DEFAULT 0;

-- New table: Entity Relationships
CREATE TABLE entity_relationships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relationship_type TEXT NOT NULL, -- 'coordinates_with', 'depends_on', 'shared_pain', etc.
    entity1_type TEXT NOT NULL,
    entity1_id INTEGER NOT NULL,
    entity2_type TEXT NOT NULL,
    entity2_id INTEGER NOT NULL,
    mentioned_in_interviews TEXT, -- JSON array
    validated INTEGER DEFAULT 0,
    validation_type TEXT, -- 'cross_validated', 'single_source'
    confidence REAL DEFAULT 0.0,
    metadata TEXT, -- JSON with additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- New table: Detected Patterns
CREATE TABLE detected_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_type TEXT NOT NULL,
    pattern_name TEXT NOT NULL,
    description TEXT,
    frequency INTEGER, -- How many times mentioned
    mentioned_in_interviews TEXT, -- JSON array
    departments TEXT, -- JSON array
    companies TEXT, -- JSON array
    priority_score REAL,
    confidence REAL,
    recommended_action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- New table: Contradictions
CREATE TABLE contradictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL,
    field TEXT NOT NULL,
    value1 TEXT,
    value2 TEXT,
    interview1_id INTEGER,
    interview2_id INTEGER,
    severity TEXT, -- 'low', 'medium', 'high'
    status TEXT DEFAULT 'pending', -- 'pending', 'resolved', 'ignored'
    resolution TEXT,
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Processing Flow

### Updated Interview Processing

```python
class EnhancedMetaOrchestrator:
    """
    Orchestrates knowledge graph building with consolidation
    """

    def process_interview_with_consolidation(
        self,
        interview: Dict,
        interview_number: int,
        total_interviews: int
    ) -> ProcessingResult:
        """
        Process interview and integrate with existing knowledge graph

        Flow:
        1. Extract entities (as before)
        2. Validate extraction (as before)
        3. ✨ NEW: Consolidate with existing knowledge
        4. ✨ NEW: Discover relationships
        5. ✨ NEW: Detect patterns
        6. ✨ NEW: Identify contradictions
        7. Store consolidated knowledge
        8. ✨ NEW: Update knowledge graph statistics
        """

        print(f"\n{'='*60}")
        print(f"📊 PROCESSING INTERVIEW {interview_number}/{total_interviews}")
        print(f"{'='*60}")

        # Stage 1: Extract entities
        print("\n🔍 Stage 1: Extracting entities...")
        entities = self.extractor.extract_all(interview)

        # Stage 2: Validate extraction
        print("\n✅ Stage 2: Validating extraction...")
        validation = self.validator.validate_entities(entities, interview)

        if validation.needs_reextraction:
            entities = self.reextract_missing(interview, validation)

        # ✨ Stage 3: Consolidate with existing knowledge
        print("\n🔗 Stage 3: Consolidating with knowledge graph...")
        consolidated = self.consolidator.consolidate_all_entities(
            entities,
            interview['meta']['interview_id']
        )

        print(f"   • Merged: {consolidated['merged_count']} entities")
        print(f"   • New: {consolidated['new_count']} entities")
        print(f"   • Enriched: {consolidated['enriched_count']} existing entities")

        # ✨ Stage 4: Discover relationships
        print("\n🕸️  Stage 4: Discovering relationships...")
        relationships = self.relationship_agent.discover_relationships(
            interview['meta']['interview_id'],
            consolidated['entities']
        )

        print(f"   • New relationships: {len(relationships)}")
        print(f"   • Validated relationships: {sum(1 for r in relationships if r.validated)}")

        # ✨ Stage 5: Detect patterns (every 5 interviews)
        if interview_number % 5 == 0:
            print("\n📊 Stage 5: Detecting patterns...")
            patterns = self.pattern_agent.recognize_patterns(interview_number)

            print(f"   • Patterns detected: {len(patterns)}")
            for pattern in patterns[:3]:  # Show top 3
                print(f"     - {pattern.description} (freq: {pattern.frequency})")

        # ✨ Stage 6: Detect contradictions
        print("\n⚠️  Stage 6: Checking for contradictions...")
        contradictions = self.contradiction_detector.detect_contradictions(
            interview['meta']['interview_id'],
            consolidated['entities']
        )

        if contradictions:
            print(f"   • Contradictions found: {len(contradictions)}")
            for contradiction in contradictions[:2]:  # Show first 2
                print(f"     - {contradiction.field}: '{contradiction.value1}' vs '{contradiction.value2}'")
        else:
            print("   • No contradictions detected ✓")

        # Stage 7: Store consolidated knowledge
        print("\n💾 Stage 7: Storing consolidated knowledge...")
        self.storage.store_all(
            entities=consolidated['entities'],
            relationships=relationships,
            patterns=patterns if interview_number % 5 == 0 else [],
            contradictions=contradictions,
            interview_meta=interview['meta']
        )

        # ✨ Stage 8: Update knowledge graph statistics
        print("\n📈 Stage 8: Updating knowledge graph statistics...")
        stats = self.knowledge_graph.update_statistics()

        print(f"\n{'='*60}")
        print(f"📊 KNOWLEDGE GRAPH STATUS")
        print(f"{'='*60}")
        print(f"Total entities: {stats['total_entities']}")
        print(f"Total relationships: {stats['total_relationships']}")
        print(f"Patterns detected: {stats['total_patterns']}")
        print(f"Avg consensus confidence: {stats['avg_consensus']:.2f}")
        print(f"Entities with 3+ sources: {stats['high_confidence_entities']}")

        return ProcessingResult(
            success=True,
            consolidated=consolidated,
            relationships=relationships,
            patterns=patterns if interview_number % 5 == 0 else [],
            contradictions=contradictions,
            stats=stats
        )
```

---

## Benefits of This Approach

### 1. **Compound Intelligence**
- Interview 1 provides base knowledge
- Interview 2 validates + enriches
- Interview 21 confirms patterns + adds depth
- Knowledge quality increases exponentially

### 2. **Pattern Recognition**
```
After 5 interviews: "WhatsApp mentioned 3 times"
After 10 interviews: "WhatsApp is the primary channel (8/10 interviews)"
After 20 interviews: "WhatsApp communication issues is a cross-department pattern affecting 12 teams"
```

### 3. **Consensus Validation**
```
1 person says: "Opera is slow" → Confidence: 0.7
3 people say: "Opera is slow" → Confidence: 0.9
8 people say: "Opera is slow" → Confidence: 0.98 + Pattern detected
```

### 4. **Relationship Mapping**
```
Interview 14: "I coordinate with Housekeeping"
Interview 21: "I receive requests from Reception"
→ Validated relationship: Reception ↔ Housekeeping
→ Channel: WhatsApp
→ Pain points: Both mention lack of tracking
```

### 5. **Contradiction Detection**
```
Interview 5: "SAP is essential, we use it daily"
Interview 23: "We don't use SAP, only Opera"
→ Contradiction flagged for human review
→ Possible causes: Different departments, outdated info, miscommunication
```

---

## Cost & Performance

### Additional Costs
- **Consolidation Agent**: ~$0.01 per interview (minimal - mostly rule-based)
- **Relationship Discovery**: ~$0.02 per interview (embeddings + matching)
- **Pattern Recognition**: ~$0.05 per 5 interviews (LLM analysis)
- **Total Additional**: ~$0.03-0.04 per interview

### New Total Cost
- **Base extraction**: $1.50 (current)
- **Knowledge consolidation**: ~$1.50 (new)
- **Total**: ~$3.00 for 44 interviews

### ROI
- **2x cost** → **10x value** (interconnected knowledge vs isolated data)
- Patterns emerge that would be impossible to see otherwise
- Validation across sources increases confidence
- Relationships reveal organizational insights

---

## Implementation Priority

### Phase 1: Foundation (This week)
1. ✅ Implement KnowledgeConsolidationAgent
2. ✅ Add consolidation tracking to database
3. ✅ Update orchestrator to run consolidation
4. Test with 5 interviews

### Phase 2: Relationships (Next week)
5. ✅ Implement RelationshipDiscoveryAgent
6. ✅ Add relationships table
7. ✅ Build relationship queries
8. Test relationship validation

### Phase 3: Intelligence (Week 3)
9. ✅ Implement PatternRecognitionAgent
10. ✅ Implement ContradictionDetector
11. ✅ Add patterns and contradictions tables
12. Build intelligence dashboard

---

## Example Output

After processing all 44 interviews:

```
📊 FINAL KNOWLEDGE GRAPH SUMMARY
{'='*60}

Total Entities: 1,234 (consolidated from 2,156 raw extractions)
├─ Pain Points: 89 unique (mentioned 347 times total)
├─ Systems: 23 unique (mentioned 412 times total)
├─ Processes: 67 unique (mentioned 289 times total)
└─ ... (14 more types)

Relationships Discovered: 456
├─ Team Coordination: 127 (89 validated)
├─ Process Dependencies: 98
├─ Shared Pain Points: 156
└─ System Integration: 75

Patterns Detected: 23
🔥 TOP PATTERNS:
1. WhatsApp Tracking Issues (12 interviews, 4 departments) → Priority: 9.8
2. Opera PMS Slowness (18 interviews, avg satisfaction: 3.1/10) → Priority: 9.5
3. Manual Data Entry (15 interviews, 8h/week wasted) → Priority: 9.3

Contradictions Found: 7
⚠️  NEEDS REVIEW:
1. SAP usage (5 say essential, 3 say not used) → Different departments?
2. Maintenance SLA (reports vary: 15min to 24h) → Need clarification

High-Confidence Entities: 789 (mentioned by 3+ sources)
Consensus Confidence: 0.87 average

Knowledge Graph is PRODUCTION-READY for AI Agents! ✨
```

---

This transforms your system from a **data extraction tool** into an **intelligence building machine**! 🚀
