#!/usr/bin/env python3
"""
Entity Merger Component for Knowledge Graph Consolidation

Merges duplicate entities by:
- Combining descriptions (removing duplicates)
- Detecting contradictions in attributes
- Tracking source interviews
- Maintaining audit trail

Preserves all original data for rollback capability.
"""
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter


class EntityMerger:
    """
    Merges duplicate entities while preserving source tracking and detecting contradictions
    
    Features:
    - Non-destructive merging (original data preserved)
    - Contradiction detection for conflicting attributes
    - Source tracking across interviews
    - Audit trail for all merge operations
    """
    
    def __init__(self):
        """Initialize entity merger"""
        pass
    
    def merge(
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
            interview_id: Source interview ID for new entity
            similarity_score: Similarity score between entities
            
        Returns:
            Updated consolidated entity with merged data
        """
        # Create a copy to avoid modifying original
        merged = existing_entity.copy()
        
        # Update source tracking
        merged = self.update_source_tracking(merged, interview_id)
        
        # Merge descriptions
        if "description" in new_entity or "description" in existing_entity:
            merged["description"] = self.combine_descriptions(
                existing_entity.get("description", ""),
                new_entity.get("description", "")
            )
        
        # Merge attributes and detect contradictions
        contradictions = self.detect_contradictions(new_entity, existing_entity)
        merged = self.merge_attributes(new_entity, merged, contradictions)
        
        # Update contradiction tracking
        if contradictions:
            merged["has_contradictions"] = 1  # SQLite boolean
            merged["contradiction_details"] = json.dumps(contradictions, ensure_ascii=False)
        
        # Track merged entity IDs
        merged_ids = self._parse_json_field(merged.get("merged_entity_ids", "[]"))
        if "id" in new_entity and new_entity["id"] not in merged_ids:
            merged_ids.append(new_entity["id"])
        merged["merged_entity_ids"] = json.dumps(merged_ids, ensure_ascii=False)
        
        # Mark as consolidated
        merged["is_consolidated"] = 1  # SQLite boolean
        merged["consolidated_at"] = datetime.now().isoformat()
        
        return merged
    
    def combine_descriptions(self, desc1: str, desc2: str) -> str:
        """
        Combine descriptions by concatenating unique sentences
        
        Args:
            desc1: First description
            desc2: Second description
            
        Returns:
            Combined description with duplicates removed
        """
        if not desc1 and not desc2:
            return ""
        if not desc1:
            return desc2
        if not desc2:
            return desc1
        
        # Split into sentences
        sentences1 = self._split_sentences(desc1)
        sentences2 = self._split_sentences(desc2)
        
        # Combine and remove duplicates (case-insensitive)
        seen = set()
        unique_sentences = []
        
        for sentence in sentences1 + sentences2:
            sentence_lower = sentence.lower().strip()
            if sentence_lower and sentence_lower not in seen:
                seen.add(sentence_lower)
                unique_sentences.append(sentence)
        
        return " ".join(unique_sentences)
    
    def detect_contradictions(
        self,
        new_entity: Dict,
        existing_entity: Dict
    ) -> List[Dict]:
        """
        Detect contradictions between entity attributes
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            
        Returns:
            List of contradiction dicts with format:
            {"attribute": "frequency", "values": ["daily", "weekly"], "sources": [1, 2]}
        """
        contradictions = []
        
        # Attributes to check for contradictions
        comparable_attributes = [
            "frequency", "severity", "priority", "status",
            "type", "category", "impact", "urgency"
        ]
        
        for attr in comparable_attributes:
            if attr not in new_entity or attr not in existing_entity:
                continue
            
            new_value = str(new_entity[attr]).lower().strip()
            existing_value = str(existing_entity[attr]).lower().strip()
            
            # Skip if values are the same or empty
            if not new_value or not existing_value:
                continue
            if new_value == existing_value:
                continue
            
            # Check if values are significantly different
            if not self._are_values_similar(new_value, existing_value):
                # Get source interviews
                mentioned_in = self._parse_json_field(
                    existing_entity.get("mentioned_in_interviews", "[]")
                )
                
                contradictions.append({
                    "attribute": attr,
                    "values": [existing_value, new_value],
                    "sources": mentioned_in + [new_entity.get("interview_id", 0)]
                })
        
        return contradictions
    
    def update_source_tracking(
        self,
        entity: Dict,
        interview_id: int
    ) -> Dict:
        """
        Update source tracking fields for entity
        
        Args:
            entity: Entity to update
            interview_id: Interview ID to add
            
        Returns:
            Updated entity with source tracking
        """
        # Parse mentioned_in_interviews
        mentioned_in = self._parse_json_field(
            entity.get("mentioned_in_interviews", "[]")
        )
        
        # Add interview_id if not already present
        if interview_id not in mentioned_in:
            mentioned_in.append(interview_id)
        
        # Update fields
        entity["mentioned_in_interviews"] = json.dumps(mentioned_in, ensure_ascii=False)
        entity["source_count"] = len(mentioned_in)
        
        # Update date tracking
        # Note: Assumes interview dates are stored in interviews table
        # For now, just track consolidation timestamp
        if "first_mentioned_date" not in entity or not entity["first_mentioned_date"]:
            entity["first_mentioned_date"] = datetime.now().isoformat()
        
        entity["last_mentioned_date"] = datetime.now().isoformat()
        
        return entity
    
    def merge_attributes(
        self,
        new_entity: Dict,
        existing_entity: Dict,
        contradictions: List[Dict]
    ) -> Dict:
        """
        Merge attributes, keeping most common value for conflicts
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            contradictions: List of detected contradictions
            
        Returns:
            Entity with merged attributes
        """
        merged = existing_entity.copy()
        
        # Get contradicting attributes
        contradicting_attrs = {c["attribute"] for c in contradictions}
        
        # For non-contradicting attributes, prefer new value if existing is empty
        for key, value in new_entity.items():
            # Skip special fields
            if key in ["id", "interview_id", "created_at"]:
                continue
            
            # Skip consolidation tracking fields
            if key in ["mentioned_in_interviews", "source_count", "consensus_confidence",
                      "is_consolidated", "has_contradictions", "contradiction_details",
                      "merged_entity_ids", "first_mentioned_date", "last_mentioned_date",
                      "consolidated_at"]:
                continue
            
            # If attribute has contradiction, keep existing value (most common)
            if key in contradicting_attrs:
                continue
            
            # If existing value is empty/null, use new value
            if key not in merged or not merged[key]:
                merged[key] = value
            
            # For list/array fields, combine them
            elif isinstance(value, list) and isinstance(merged.get(key), list):
                # Combine and deduplicate
                combined = list(set(merged[key] + value))
                merged[key] = combined
        
        return merged
    
    def _split_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences
        
        Args:
            text: Text to split
            
        Returns:
            List of sentences
        """
        if not text:
            return []
        
        # Simple sentence splitting (handles . ! ?)
        import re
        sentences = re.split(r'[.!?]+', text)
        
        # Clean up and filter empty
        return [s.strip() for s in sentences if s.strip()]
    
    def _are_values_similar(self, value1: str, value2: str) -> bool:
        """
        Check if two values are similar enough to not be a contradiction
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            True if values are similar, False if contradictory
        """
        # Exact match
        if value1 == value2:
            return True
        
        # Check for common synonyms
        synonyms = {
            "high": ["alta", "alto", "elevado", "elevada"],
            "medium": ["media", "medio", "moderado", "moderada"],
            "low": ["baja", "bajo"],
            "daily": ["diario", "diaria", "todos los días", "cada día"],
            "weekly": ["semanal", "cada semana"],
            "monthly": ["mensual", "cada mes"],
        }
        
        for key, values in synonyms.items():
            if value1 in values and value2 in values:
                return True
            if value1 == key and value2 in values:
                return True
            if value2 == key and value1 in values:
                return True
        
        return False
    
    def _parse_json_field(self, field: Any) -> List:
        """
        Parse JSON field safely
        
        Args:
            field: Field value (string, list, or None)
            
        Returns:
            Parsed list or empty list
        """
        if not field:
            return []
        
        if isinstance(field, list):
            return field
        
        if isinstance(field, str):
            try:
                parsed = json.loads(field)
                return parsed if isinstance(parsed, list) else []
            except (json.JSONDecodeError, TypeError):
                return []
        
        return []
