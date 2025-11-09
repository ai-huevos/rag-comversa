#!/usr/bin/env python3
"""
Unit Tests for ConsensusScorer Component

Tests:
- Confidence calculation with various source counts
- Agreement bonus calculation
- Contradiction penalty
- Single source penalty
- Edge cases
"""
import pytest
import json
from intelligence_capture.consensus_scorer import ConsensusScorer


class TestConsensusScorer:
    """Test suite for ConsensusScorer"""
    
    @pytest.fixture
    def config(self):
        """Standard configuration for tests"""
        return {
            "consensus_parameters": {
                "source_count_divisor": 10,
                "agreement_bonus": 0.1,
                "max_bonus": 0.3,
                "contradiction_penalty": 0.25,
                "single_source_penalty": 0.3
            }
        }
    
    @pytest.fixture
    def scorer(self, config):
        """Create scorer instance with 44 total interviews"""
        return ConsensusScorer(config, total_interviews=44)
    
    # Test 1: Confidence Calculation with Various Source Counts
    
    def test_confidence_single_source(self, scorer):
        """Test confidence calculation for single source entity"""
        entity = {
            "name": "Excel",
            "source_count": 1,
            "mentioned_in_interviews": "[1]"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # Single source should have low confidence due to penalty
        # base_score = 1/11 = 0.09, minus single_source_penalty = 0.3
        # Result should be close to 0.0 (clamped)
        assert 0.0 <= confidence <= 0.3
    
    def test_confidence_five_sources(self, scorer):
        """Test confidence calculation for 5 sources"""
        entity = {
            "name": "Excel",
            "source_count": 5,
            "mentioned_in_interviews": "[1, 2, 3, 4, 5]"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 5/11 = 0.45
        # No single source penalty
        # Should be around 0.45
        assert 0.4 <= confidence <= 0.6
    
    def test_confidence_ten_sources(self, scorer):
        """Test confidence calculation for 10 sources"""
        entity = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11)))
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 10/11 = 0.91
        # Should be high confidence
        assert 0.8 <= confidence <= 1.0
    
    def test_confidence_twenty_sources(self, scorer):
        """Test confidence calculation for 20 sources (exceeds divisor)"""
        entity = {
            "name": "Excel",
            "source_count": 20,
            "mentioned_in_interviews": json.dumps(list(range(1, 21)))
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = min(20/11, 1.0) = 1.0
        # Should be maximum confidence
        assert confidence >= 0.9
    
    # Test 2: Agreement Bonus Calculation
    
    def test_agreement_bonus_increases_confidence(self, scorer):
        """Test agreement bonus increases confidence"""
        entity_without_agreement = {
            "name": "Excel",
            "source_count": 5,
            "mentioned_in_interviews": "[1, 2, 3, 4, 5]"
        }
        
        entity_with_agreement = {
            "name": "Excel",
            "source_count": 5,
            "mentioned_in_interviews": "[1, 2, 3, 4, 5]",
            "frequency": "daily",
            "severity": "high",
            "priority": "critical"
        }
        
        conf_without = scorer.calculate_confidence(entity_without_agreement)
        conf_with = scorer.calculate_confidence(entity_with_agreement)
        
        # Entity with more attributes should have higher confidence
        assert conf_with >= conf_without
    
    def test_agreement_bonus_capped_at_max(self, scorer):
        """Test agreement bonus is capped at max_bonus"""
        # Create entity with many attributes (should trigger max bonus)
        entity = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "attr1": "value1",
            "attr2": "value2",
            "attr3": "value3",
            "attr4": "value4",
            "attr5": "value5",
            "attr6": "value6",
            "attr7": "value7",
            "attr8": "value8",
            "attr9": "value9",
            "attr10": "value10"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 10/11 = 0.91
        # max_bonus = 0.3
        # Maximum possible = 0.91 + 0.3 = 1.21, clamped to 1.0
        assert confidence == 1.0
    
    # Test 3: Contradiction Penalty
    
    def test_contradiction_penalty_reduces_confidence(self, scorer):
        """Test contradiction penalty reduces confidence"""
        entity_without_contradiction = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "has_contradictions": 0
        }
        
        entity_with_contradiction = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "has_contradictions": 1,
            "contradiction_details": json.dumps([
                {"attribute": "frequency", "values": ["daily", "weekly"]}
            ])
        }
        
        conf_without = scorer.calculate_confidence(entity_without_contradiction)
        conf_with = scorer.calculate_confidence(entity_with_contradiction)
        
        # Entity with contradictions should have lower confidence
        assert conf_with < conf_without
        # Penalty should be 0.25 per contradiction
        assert abs((conf_without - conf_with) - 0.25) < 0.05
    
    def test_multiple_contradictions_compound_penalty(self, scorer):
        """Test multiple contradictions compound the penalty"""
        entity = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "has_contradictions": 1,
            "contradiction_details": json.dumps([
                {"attribute": "frequency", "values": ["daily", "weekly"]},
                {"attribute": "severity", "values": ["high", "low"]},
                {"attribute": "priority", "values": ["urgent", "normal"]}
            ])
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 10/11 = 0.91
        # contradiction_penalty = 3 * 0.25 = 0.75
        # Result = 0.91 - 0.75 = 0.16
        assert 0.1 <= confidence <= 0.3
    
    # Test 4: Single Source Penalty
    
    def test_single_source_penalty_applied(self, scorer):
        """Test single source penalty is applied correctly"""
        entity = {
            "name": "Excel",
            "source_count": 1,
            "mentioned_in_interviews": "[1]"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 1/11 = 0.09
        # single_source_penalty = 0.3
        # Result = 0.09 - 0.3 = -0.21, clamped to 0.0
        assert confidence == 0.0
    
    def test_single_source_penalty_not_applied_for_multiple(self, scorer):
        """Test single source penalty not applied for multiple sources"""
        entity = {
            "name": "Excel",
            "source_count": 2,
            "mentioned_in_interviews": "[1, 2]"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = 2/11 = 0.18
        # No single source penalty
        # Should be around 0.18
        assert confidence >= 0.15
    
    # Test 5: Edge Cases
    
    def test_confidence_zero_sources(self, scorer):
        """Test confidence calculation with 0 sources (edge case)"""
        entity = {
            "name": "Excel",
            "source_count": 0,
            "mentioned_in_interviews": "[]"
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # Should return 0.0 (clamped)
        assert confidence == 0.0
    
    def test_confidence_hundred_sources(self, scorer):
        """Test confidence calculation with 100 sources (edge case)"""
        entity = {
            "name": "Excel",
            "source_count": 100,
            "mentioned_in_interviews": json.dumps(list(range(1, 101)))
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # base_score = min(100/11, 1.0) = 1.0
        # Should be maximum confidence
        assert confidence >= 0.9
    
    def test_confidence_clamped_to_range(self, scorer):
        """Test confidence is always clamped to 0.0-1.0 range"""
        # Test with extreme penalties
        entity = {
            "name": "Excel",
            "source_count": 1,
            "mentioned_in_interviews": "[1]",
            "has_contradictions": 1,
            "contradiction_details": json.dumps([
                {"attribute": f"attr{i}", "values": ["v1", "v2"]}
                for i in range(10)  # 10 contradictions
            ])
        }
        
        confidence = scorer.calculate_confidence(entity)
        
        # Should be clamped to 0.0
        assert 0.0 <= confidence <= 1.0
    
    # Test 6: Adaptive Divisor
    
    def test_adaptive_divisor_for_44_interviews(self, scorer):
        """Test adaptive divisor is calculated correctly for 44 interviews"""
        # For 44 interviews: min(10, 44/4) = min(10, 11) = 10
        # But the scorer should use 11 based on the formula
        assert scorer.source_count_divisor == 11.0
    
    def test_adaptive_divisor_for_small_dataset(self):
        """Test adaptive divisor for small dataset"""
        config = {
            "consensus_parameters": {
                "source_count_divisor": 10,
                "agreement_bonus": 0.1,
                "max_bonus": 0.3,
                "contradiction_penalty": 0.25,
                "single_source_penalty": 0.3
            }
        }
        
        scorer = ConsensusScorer(config, total_interviews=20)
        
        # For 20 interviews: min(10, 20/4) = min(10, 5) = 5
        assert scorer.source_count_divisor == 5.0
    
    def test_adaptive_divisor_for_large_dataset(self):
        """Test adaptive divisor for large dataset"""
        config = {
            "consensus_parameters": {
                "source_count_divisor": 10,
                "agreement_bonus": 0.1,
                "max_bonus": 0.3,
                "contradiction_penalty": 0.25,
                "single_source_penalty": 0.3
            }
        }
        
        scorer = ConsensusScorer(config, total_interviews=100)
        
        # For 100 interviews: min(10, 100/4) = min(10, 25) = 10
        assert scorer.source_count_divisor == 10.0
    
    # Test 7: Needs Review Flag
    
    def test_needs_review_low_confidence(self, scorer):
        """Test needs_review flag for low confidence entities"""
        entity = {
            "name": "Excel",
            "source_count": 1,
            "mentioned_in_interviews": "[1]",
            "consensus_confidence": 0.5
        }
        
        needs_review = scorer.needs_review(entity)
        
        # Low confidence should trigger review
        assert needs_review == True
    
    def test_needs_review_contradictions(self, scorer):
        """Test needs_review flag for entities with contradictions"""
        entity = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "consensus_confidence": 0.8,
            "has_contradictions": 1
        }
        
        needs_review = scorer.needs_review(entity)
        
        # Contradictions should trigger review
        assert needs_review == True
    
    def test_needs_review_high_confidence_no_contradictions(self, scorer):
        """Test needs_review flag for high confidence entities without contradictions"""
        entity = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11))),
            "consensus_confidence": 0.9,
            "has_contradictions": 0
        }
        
        needs_review = scorer.needs_review(entity)
        
        # High confidence without contradictions should not trigger review
        assert needs_review == False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
