#!/usr/bin/env python3
"""
Knowledge Consolidation Agent - Main Orchestrator

Coordinates the consolidation process:
1. Duplicate detection (DuplicateDetector)
2. Entity merging (EntityMerger)
3. Consensus scoring (ConsensusScorer)
4. Database updates

Integrates with extraction pipeline to consolidate entities in real-time.
"""
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

from intelligence_capture.duplicate_detector import DuplicateDetector
from intelligence_capture.entity_merger import EntityMerger
from intelligence_capture.consensus_scorer import ConsensusScorer


class KnowledgeConsolidationAgent:
    """
    Main orchestrator for knowledge graph consolidation
    
    Features:
    - Automatic duplicate detection and merging
    - Consensus confidence scoring
    - Source tracking across interviews
    - Audit trail for all operations
    - Incremental consolidation (new interviews merge with existing data)
    """
    
    def __init__(self, db, config: Dict, openai_api_key: Optional[str] = None):
        """
        Initialize consolidation agent
        
        Args:
            db: Database instance (IntelligenceDB or EnhancedIntelligenceDB)
            config: Configuration dict with consolidation settings
            openai_api_key: Optional OpenAI API key for semantic similarity
        """
        self.db = db
        self.config = config
        
        # Initialize components
        self.duplicate_detector = DuplicateDetector(config, openai_api_key)
        self.entity_merger = EntityMerger()
        self.consensus_scorer = ConsensusScorer(config)
        
        # Statistics
        self.stats = {
            "entities_processed": 0,
            "duplicates_found": 0,
            "entities_merged": 0,
            "contradictions_detected": 0,
            "processing_time": 0.0
        }
    
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
        import time
        start_time = time.time()
        
        consolidated = {}
        
        # Process each entity type
        for entity_type, entity_list in entities.items():
            if not entity_list:
                consolidated[entity_type] = []
                continue
            
            print(f"\n  🔗 Consolidating {entity_type}...")
            consolidated[entity_type] = self._consolidate_entity_type(
                entity_list,
                entity_type,
                interview_id
            )
        
        # Update statistics
        self.stats["processing_time"] = time.time() - start_time
        
        # Print summary
        self._print_consolidation_summary()
        
        return consolidated
    
    def _consolidate_entity_type(
        self,
        entities: List[Dict],
        entity_type: str,
        interview_id: int
    ) -> List[Dict]:
        """
        Consolidate entities of a specific type
        
        Args:
            entities: List of entities to consolidate
            entity_type: Type of entity
            interview_id: Source interview ID
            
        Returns:
            List of consolidated entities
        """
        consolidated_entities = []
        
        for entity in entities:
            self.stats["entities_processed"] += 1
            
            # Find similar entities in database
            similar_entities = self.find_similar_entities(entity, entity_type)
            
            if similar_entities:
                # Merge with most similar entity
                best_match, similarity_score = similar_entities[0]
                self.stats["duplicates_found"] += 1
                
                # Merge entities
                merged_entity = self.merge_entities(
                    entity,
                    best_match,
                    interview_id,
                    similarity_score
                )
                
                self.stats["entities_merged"] += 1
                
                # Check for contradictions
                if merged_entity.get("has_contradictions", 0):
                    self.stats["contradictions_detected"] += 1
                
                consolidated_entities.append(merged_entity)
            else:
                # No duplicates found, add as new entity
                new_entity = self._prepare_new_entity(entity, interview_id)
                consolidated_entities.append(new_entity)
        
        return consolidated_entities
    
    def find_similar_entities(
        self,
        entity: Dict,
        entity_type: str
    ) -> List[Tuple[Dict, float]]:
        """
        Find existing entities similar to new entity
        
        Args:
            entity: New entity to match
            entity_type: Type of entity
            
        Returns:
            List of (existing_entity, similarity_score) tuples, sorted by score
        """
        # Get existing entities from database
        existing_entities = self._get_existing_entities(entity_type)
        
        if not existing_entities:
            return []
        
        # Use duplicate detector to find similar entities
        similar = self.duplicate_detector.find_duplicates(
            entity,
            entity_type,
            existing_entities
        )
        
        return similar
    
    def merge_entities(
        self,
        new_entity: Dict,
        existing_entity: Dict,
        interview_id: int,
        similarity_score: float
    ) -> Dict:
        """
        Merge new entity into existing entity
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            interview_id: Source interview ID
            similarity_score: Similarity between entities
            
        Returns:
            Updated consolidated entity
        """
        # Use entity merger to combine entities
        merged = self.entity_merger.merge(
            new_entity,
            existing_entity,
            interview_id,
            similarity_score
        )
        
        # Calculate consensus confidence
        confidence = self.calculate_consensus_confidence(merged)
        merged["consensus_confidence"] = confidence
        
        # Log to audit trail
        self._log_consolidation_audit(
            entity_type=new_entity.get("entity_type", "unknown"),
            merged_entity_ids=[new_entity.get("id"), existing_entity.get("id")],
            resulting_entity_id=existing_entity.get("id"),
            similarity_score=similarity_score
        )
        
        return merged
    
    def calculate_consensus_confidence(self, entity: Dict) -> float:
        """
        Calculate consensus confidence score for entity
        
        Args:
            entity: Consolidated entity with source tracking
            
        Returns:
            Confidence score (0.0-1.0)
        """
        return self.consensus_scorer.calculate_confidence(entity)
    
    def _get_existing_entities(self, entity_type: str) -> List[Dict]:
        """
        Get existing entities from database
        
        Args:
            entity_type: Type of entity
            
        Returns:
            List of existing entities
        """
        try:
            cursor = self.db.conn.cursor()
            
            # Query database for entities of this type
            cursor.execute(f"""
                SELECT * FROM {entity_type}
                WHERE is_consolidated = 1 OR is_consolidated IS NULL
            """)
            
            rows = cursor.fetchall()
            
            # Convert to list of dicts
            entities = []
            for row in rows:
                entity = dict(row)
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            print(f"  ⚠️  Error fetching existing entities: {e}")
            return []
    
    def _prepare_new_entity(self, entity: Dict, interview_id: int) -> Dict:
        """
        Prepare new entity with consolidation tracking fields
        
        Args:
            entity: New entity
            interview_id: Source interview ID
            
        Returns:
            Entity with consolidation fields initialized
        """
        # Initialize consolidation fields
        entity["mentioned_in_interviews"] = json.dumps([interview_id], ensure_ascii=False)
        entity["source_count"] = 1
        entity["consensus_confidence"] = 0.5  # Single source = lower confidence
        entity["is_consolidated"] = 0  # Not yet consolidated
        entity["has_contradictions"] = 0
        entity["contradiction_details"] = None
        entity["merged_entity_ids"] = json.dumps([], ensure_ascii=False)
        entity["first_mentioned_date"] = datetime.now().isoformat()
        entity["last_mentioned_date"] = datetime.now().isoformat()
        entity["consolidated_at"] = None
        
        return entity
    
    def _log_consolidation_audit(
        self,
        entity_type: str,
        merged_entity_ids: List[int],
        resulting_entity_id: int,
        similarity_score: float
    ):
        """
        Log consolidation operation to audit trail
        
        Args:
            entity_type: Type of entity
            merged_entity_ids: IDs of entities that were merged
            resulting_entity_id: ID of resulting consolidated entity
            similarity_score: Similarity score
        """
        try:
            cursor = self.db.conn.cursor()
            
            cursor.execute("""
                INSERT INTO consolidation_audit (
                    entity_type,
                    merged_entity_ids,
                    resulting_entity_id,
                    similarity_score,
                    consolidation_timestamp
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                entity_type,
                json.dumps(merged_entity_ids, ensure_ascii=False),
                resulting_entity_id,
                similarity_score,
                datetime.now().isoformat()
            ))
            
            self.db.conn.commit()
            
        except Exception as e:
            print(f"  ⚠️  Error logging audit trail: {e}")
    
    def _print_consolidation_summary(self):
        """Print consolidation statistics"""
        print(f"\n  📊 Consolidation Summary:")
        print(f"     Entities processed: {self.stats['entities_processed']}")
        print(f"     Duplicates found: {self.stats['duplicates_found']}")
        print(f"     Entities merged: {self.stats['entities_merged']}")
        print(f"     Contradictions detected: {self.stats['contradictions_detected']}")
        print(f"     Processing time: {self.stats['processing_time']:.2f}s")
        
        if self.stats["entities_processed"] > 0:
            reduction = (self.stats["duplicates_found"] / self.stats["entities_processed"]) * 100
            print(f"     Duplicate reduction: {reduction:.1f}%")
    
    def get_statistics(self) -> Dict:
        """
        Get consolidation statistics
        
        Returns:
            Dict with consolidation metrics
        """
        return self.stats.copy()
