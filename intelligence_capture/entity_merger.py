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

from intelligence_capture.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


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
        existing_entity: Dict,
        similarity_threshold: float = 0.7
    ) -> List[Dict]:
        """
        Detect contradictions between entity attributes
        
        Improved logic:
        - Checks ALL attributes (union of both entities), not just common ones
        - Handles missing values correctly: new info vs no info vs contradiction
        - Uses fuzzy matching for text values with configurable threshold
        - Stores contradiction details with similarity scores
        
        Args:
            new_entity: Newly extracted entity
            existing_entity: Existing consolidated entity
            similarity_threshold: Threshold for considering values similar (default 0.7)
            
        Returns:
            List of contradiction dicts with format:
            {
                "attribute": "frequency",
                "values": ["daily", "weekly"],
                "similarity_score": 0.3,
                "sources": [1, 2]
            }
        """
        contradictions = []
        
        # Metadata fields to skip
        metadata_fields = {
            "id", "interview_id", "created_at", "mentioned_in_interviews",
            "source_count", "consensus_confidence", "is_consolidated",
            "has_contradictions", "contradiction_details", "merged_entity_ids",
            "first_mentioned_date", "last_mentioned_date", "consolidated_at",
            "name", "description"  # Name and description are merged, not compared
        }
        
        # Get ALL attributes from both entities (union)
        all_attributes = set(new_entity.keys()) | set(existing_entity.keys())
        
        # Filter out metadata fields
        comparable_attributes = all_attributes - metadata_fields
        
        for attr in comparable_attributes:
            new_value = new_entity.get(attr)
            existing_value = existing_entity.get(attr)
            
            # Handle missing values correctly
            # Case 1: Both missing - no contradiction
            if new_value is None and existing_value is None:
                continue
            
            # Case 2: One missing - this is NEW INFO, not a contradiction
            if new_value is None or existing_value is None:
                logger.debug(f"New info for attribute '{attr}': {new_value or existing_value}")
                continue
            
            # Convert to strings for comparison
            new_value_str = str(new_value).strip()
            existing_value_str = str(existing_value).strip()
            
            # Skip if either is empty string
            if not new_value_str or not existing_value_str:
                continue
            
            # Case 3: Both have values - check if they contradict
            # Calculate similarity between values
            similarity_score = self._calculate_value_similarity(
                new_value_str,
                existing_value_str
            )
            
            # If similarity is below threshold, it's a contradiction
            if similarity_score < similarity_threshold:
                # Get source interviews
                mentioned_in = self._parse_json_field(
                    existing_entity.get("mentioned_in_interviews", "[]")
                )
                
                logger.warning(f"Contradiction detected for '{attr}': '{existing_value_str}' vs '{new_value_str}' (similarity={similarity_score:.2f})")
                
                contradictions.append({
                    "attribute": attr,
                    "values": [existing_value_str, new_value_str],
                    "similarity_score": similarity_score,
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
    
    def _calculate_value_similarity(self, value1: str, value2: str) -> float:
        """
        Calculate similarity between two attribute values using fuzzy matching
        
        Handles:
        - Exact matches (1.0)
        - Spanish/English synonyms (1.0)
        - Fuzzy string matching for text values (0.0-1.0)
        - Spanish punctuation and accents
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            Similarity score (0.0-1.0), where 1.0 = identical, 0.0 = completely different
        """
        # Normalize for comparison (lowercase, strip)
        v1 = value1.lower().strip()
        v2 = value2.lower().strip()
        
        # Exact match
        if v1 == v2:
            return 1.0
        
        # Check for domain-specific synonyms (Spanish/English)
        synonyms = {
            # Severity/Priority
            "high": ["alta", "alto", "elevado", "elevada", "crítico", "crítica"],
            "medium": ["media", "medio", "moderado", "moderada"],
            "low": ["baja", "bajo", "menor"],
            
            # Frequency
            "daily": ["diario", "diaria", "todos los días", "cada día", "cotidiano"],
            "weekly": ["semanal", "cada semana", "por semana"],
            "monthly": ["mensual", "cada mes", "por mes"],
            "yearly": ["anual", "cada año", "por año"],
            
            # Status
            "active": ["activo", "activa", "en curso"],
            "inactive": ["inactivo", "inactiva", "pausado", "pausada"],
            "completed": ["completado", "completada", "terminado", "terminada"],
            
            # Impact
            "critical": ["crítico", "crítica", "grave"],
            "major": ["mayor", "importante"],
            "minor": ["menor", "pequeño", "pequeña"],
        }
        
        # Check if both values are synonyms
        for key, values in synonyms.items():
            # Both in same synonym group
            if v1 in values and v2 in values:
                return 1.0
            # One is key, other is synonym
            if (v1 == key and v2 in values) or (v2 == key and v1 in values):
                return 1.0
        
        # Use fuzzy string matching for text values
        # Try rapidfuzz if available, otherwise use difflib
        try:
            from rapidfuzz import fuzz
            # Token sort ratio handles word order differences
            similarity = fuzz.token_sort_ratio(v1, v2) / 100.0
        except ImportError:
            # Fallback to difflib
            from difflib import SequenceMatcher
            similarity = SequenceMatcher(None, v1, v2).ratio()
        
        return similarity
    
    def _are_values_similar(self, value1: str, value2: str) -> bool:
        """
        Check if two values are similar enough to not be a contradiction
        
        DEPRECATED: Use _calculate_value_similarity() instead
        
        Args:
            value1: First value
            value2: Second value
            
        Returns:
            True if values are similar, False if contradictory
        """
        # Use new similarity calculation with 0.7 threshold
        similarity = self._calculate_value_similarity(value1, value2)
        return similarity >= 0.7
    
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
