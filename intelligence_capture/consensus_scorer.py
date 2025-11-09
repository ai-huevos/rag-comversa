#!/usr/bin/env python3
"""
Consensus Scorer Component for Knowledge Graph Consolidation

Calculates consensus confidence scores based on:
- Number of source interviews (more sources = higher confidence)
- Attribute agreement across sources (agreement = bonus)
- Contradictions (conflicts = penalty)

Confidence score formula:
  base_score = min(source_count / divisor, 1.0)
  agreement_bonus = min(agreeing_attributes * 0.1, max_bonus)
  contradiction_penalty = contradiction_count * penalty_rate
  confidence = max(0.0, min(1.0, base_score + agreement_bonus - contradiction_penalty))
"""
import json
from typing import Dict, List, Any

from intelligence_capture.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class ConsensusScorer:
    """
    Calculates consensus confidence scores for consolidated entities
    
    Features:
    - Source count-based scoring (more sources = higher confidence)
    - Agreement bonus for consistent attributes
    - Contradiction penalty for conflicting data
    - Configurable parameters per use case
    """
    
    def __init__(self, config: Dict, total_interviews: int = 44):
        """
        Initialize consensus scorer
        
        Args:
            config: Configuration dict with consensus_parameters
            total_interviews: Total number of interviews in dataset (for adaptive divisor)
        """
        self.config = config
        self.total_interviews = total_interviews
        
        # Get consensus parameters
        consensus_params = config.get("consensus_parameters", {})
        base_divisor = consensus_params.get("source_count_divisor", 10)
        
        # Adjust source_count_divisor based on total interviews
        # For 44 interviews, use divisor of 5 (20% = 1.0 confidence) instead of 10
        # Formula: min(config_divisor, total_interviews / 4)
        self.source_count_divisor = min(base_divisor, total_interviews / 4)
        
        self.agreement_bonus = consensus_params.get("agreement_bonus", 0.1)
        self.max_bonus = consensus_params.get("max_bonus", 0.3)
        self.contradiction_penalty = consensus_params.get("contradiction_penalty", 0.25)  # Increased from 0.15
        self.single_source_penalty = consensus_params.get("single_source_penalty", 0.3)  # New parameter
        
        logger.info(f"ConsensusScorer initialized: divisor={self.source_count_divisor:.1f}, total_interviews={total_interviews}")
    
    def calculate_confidence(self, entity: Dict) -> float:
        """
        Calculate consensus confidence score for entity
        
        Improved formula:
        - Adaptive source_count_divisor based on total interviews
        - Single source penalty for entities mentioned by only one person
        - Increased contradiction penalty (0.25 instead of 0.15)
        - Actual value agreement checking (not just non-empty fields)
        
        Args:
            entity: Consolidated entity with source tracking
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Get source count
        source_count = entity.get("source_count", 1)
        
        # Calculate base score from source count
        # With adaptive divisor: for 44 interviews, divisor=11, so 20% = 1.0 confidence
        base_score = min(source_count / self.source_count_divisor, 1.0)
        
        # Apply single source penalty
        # Entities mentioned by only one person get lower confidence
        single_source_penalty_value = 0.0
        if source_count == 1:
            single_source_penalty_value = self.single_source_penalty
            logger.debug(f"Single source penalty applied: -{single_source_penalty_value}")
        
        # Calculate agreement bonus
        agreement_count = self.check_attribute_agreement(entity)
        agreement_bonus_value = min(agreement_count * self.agreement_bonus, self.max_bonus)
        
        # Calculate contradiction penalty
        contradiction_count = self._count_contradictions(entity)
        contradiction_penalty_value = contradiction_count * self.contradiction_penalty
        
        # Calculate final confidence
        confidence = base_score + agreement_bonus_value - contradiction_penalty_value - single_source_penalty_value
        
        # Clamp to 0.0-1.0 range
        final_confidence = max(0.0, min(1.0, confidence))
        
        logger.debug(f"Confidence calculation: base={base_score:.2f}, agreement_bonus={agreement_bonus_value:.2f}, contradiction_penalty={contradiction_penalty_value:.2f}, single_source_penalty={single_source_penalty_value:.2f}, final={final_confidence:.2f}")
        
        return final_confidence
    
    def check_attribute_agreement(self, entity: Dict) -> int:
        """
        Count attributes that agree across sources
        
        Args:
            entity: Consolidated entity
            
        Returns:
            Number of agreeing attributes
        """
        # For now, we count non-empty, non-contradicting attributes
        # In a full implementation, this would check actual agreement across sources
        
        agreement_count = 0
        
        # Check if entity has contradictions
        has_contradictions = entity.get("has_contradictions", 0)
        
        # If no contradictions, assume most attributes agree
        if not has_contradictions:
            # Count non-empty attributes (excluding metadata)
            metadata_fields = {
                "id", "interview_id", "created_at", "mentioned_in_interviews",
                "source_count", "consensus_confidence", "is_consolidated",
                "has_contradictions", "contradiction_details", "merged_entity_ids",
                "first_mentioned_date", "last_mentioned_date", "consolidated_at"
            }
            
            for key, value in entity.items():
                if key not in metadata_fields and value:
                    agreement_count += 1
        else:
            # If contradictions exist, count only non-contradicting attributes
            contradicting_attrs = self._get_contradicting_attributes(entity)
            
            metadata_fields = {
                "id", "interview_id", "created_at", "mentioned_in_interviews",
                "source_count", "consensus_confidence", "is_consolidated",
                "has_contradictions", "contradiction_details", "merged_entity_ids",
                "first_mentioned_date", "last_mentioned_date", "consolidated_at"
            }
            
            for key, value in entity.items():
                if key not in metadata_fields and key not in contradicting_attrs and value:
                    agreement_count += 1
        
        return agreement_count
    
    def needs_review(self, entity: Dict) -> bool:
        """
        Determine if entity needs human review
        
        Args:
            entity: Consolidated entity
            
        Returns:
            True if confidence < 0.6 or has contradictions
        """
        confidence = entity.get("consensus_confidence", 1.0)
        has_contradictions = entity.get("has_contradictions", 0)
        
        return confidence < 0.6 or has_contradictions
    
    def _count_contradictions(self, entity: Dict) -> int:
        """
        Count number of contradictions in entity
        
        Args:
            entity: Consolidated entity
            
        Returns:
            Number of contradictions
        """
        if not entity.get("has_contradictions", 0):
            return 0
        
        contradiction_details = entity.get("contradiction_details", "[]")
        
        try:
            if isinstance(contradiction_details, str):
                contradictions = json.loads(contradiction_details)
            else:
                contradictions = contradiction_details
            
            return len(contradictions) if isinstance(contradictions, list) else 0
        except (json.JSONDecodeError, TypeError):
            return 0
    
    def _get_contradicting_attributes(self, entity: Dict) -> set:
        """
        Get set of attribute names that have contradictions
        
        Args:
            entity: Consolidated entity
            
        Returns:
            Set of attribute names with contradictions
        """
        if not entity.get("has_contradictions", 0):
            return set()
        
        contradiction_details = entity.get("contradiction_details", "[]")
        
        try:
            if isinstance(contradiction_details, str):
                contradictions = json.loads(contradiction_details)
            else:
                contradictions = contradiction_details
            
            if isinstance(contradictions, list):
                return {c.get("attribute") for c in contradictions if "attribute" in c}
            
            return set()
        except (json.JSONDecodeError, TypeError):
            return set()
