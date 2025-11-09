#!/usr/bin/env python3
"""
Unit Tests for EntityMerger Component

Tests:
- Description combination with duplicate sentences
- Contradiction detection with conflicting attributes
- Source tracking updates
- Attribute merging strategies
- Spanish punctuation handling
"""
import pytest
import json
from intelligence_capture.entity_merger import EntityMerger


class TestEntityMerger:
    """Test suite for EntityMerger"""
    
    @pytest.fixture
    def merger(self):
        """Create merger instance"""
        return EntityMerger()
    
    # Test 1: Description Combination
    
    def test_combine_descriptions_removes_duplicates(self, merger):
        """Test description combination removes duplicate sentences"""
        desc1 = "Excel is a spreadsheet. It's used for data analysis."
        desc2 = "Excel is a spreadsheet. It has many features."
        
        combined = merger.combine_descriptions(desc1, desc2)
        
        # Should contain unique sentences only
        assert "Excel is a spreadsheet" in combined
        assert "It's used for data analysis" in combined
        assert "It has many features" in combined
        # Should not duplicate "Excel is a spreadsheet"
        assert combined.count("Excel is a spreadsheet") == 1
    
    def test_combine_descriptions_handles_empty(self, merger):
        """Test description combination handles empty strings"""
        assert merger.combine_descriptions("", "") == ""
        assert merger.combine_descriptions("Text", "") == "Text"
        assert merger.combine_descriptions("", "Text") == "Text"
    
    def test_combine_descriptions_case_insensitive_dedup(self, merger):
        """Test description combination is case-insensitive for deduplication"""
        desc1 = "Excel is great."
        desc2 = "EXCEL IS GREAT."
        
        combined = merger.combine_descriptions(desc1, desc2)
        
        # Should only include one version
        sentences = combined.split(". ")
        assert len(sentences) <= 2  # One sentence + possible empty
    
    # Test 2: Contradiction Detection
    
    def test_detect_contradictions_finds_conflicting_frequency(self, merger):
        """Test contradiction detection finds conflicting frequency values"""
        new_entity = {
            "name": "Excel",
            "frequency": "daily",
            "interview_id": 2
        }
        
        existing_entity = {
            "name": "Excel",
            "frequency": "weekly",
            "mentioned_in_interviews": "[1]"
        }
        
        contradictions = merger.detect_contradictions(new_entity, existing_entity)
        
        assert len(contradictions) > 0
        assert any(c["attribute"] == "frequency" for c in contradictions)
    
    def test_detect_contradictions_ignores_similar_values(self, merger):
        """Test contradiction detection ignores similar/synonym values"""
        new_entity = {
            "name": "Excel",
            "severity": "high",
            "interview_id": 2
        }
        
        existing_entity = {
            "name": "Excel",
            "severity": "alta",  # Spanish synonym for "high"
            "mentioned_in_interviews": "[1]"
        }
        
        contradictions = merger.detect_contradictions(new_entity, existing_entity)
        
        # Should not detect contradiction (synonyms)
        severity_contradictions = [c for c in contradictions if c["attribute"] == "severity"]
        assert len(severity_contradictions) == 0
    
    def test_detect_contradictions_handles_missing_values(self, merger):
        """Test contradiction detection handles missing values correctly"""
        new_entity = {
            "name": "Excel",
            "frequency": "daily",
            "interview_id": 2
        }
        
        existing_entity = {
            "name": "Excel",
            # frequency missing
            "mentioned_in_interviews": "[1]"
        }
        
        contradictions = merger.detect_contradictions(new_entity, existing_entity)
        
        # Should not detect contradiction (new info, not conflict)
        frequency_contradictions = [c for c in contradictions if c["attribute"] == "frequency"]
        assert len(frequency_contradictions) == 0
    
    def test_detect_contradictions_includes_similarity_score(self, merger):
        """Test contradiction detection includes similarity scores"""
        new_entity = {
            "name": "Excel",
            "status": "active",
            "interview_id": 2
        }
        
        existing_entity = {
            "name": "Excel",
            "status": "inactive",
            "mentioned_in_interviews": "[1]"
        }
        
        contradictions = merger.detect_contradictions(new_entity, existing_entity)
        
        if len(contradictions) > 0:
            assert "similarity_score" in contradictions[0]
            assert 0.0 <= contradictions[0]["similarity_score"] <= 1.0
    
    def test_detect_contradictions_checks_all_attributes(self, merger):
        """Test contradiction detection checks ALL attributes, not just predefined"""
        new_entity = {
            "name": "Excel",
            "custom_field": "value1",
            "interview_id": 2
        }
        
        existing_entity = {
            "name": "Excel",
            "custom_field": "value2",
            "mentioned_in_interviews": "[1]"
        }
        
        contradictions = merger.detect_contradictions(new_entity, existing_entity)
        
        # Should detect contradiction in custom field
        custom_contradictions = [c for c in contradictions if c["attribute"] == "custom_field"]
        assert len(custom_contradictions) > 0
    
    # Test 3: Source Tracking Updates
    
    def test_update_source_tracking_adds_interview_id(self, merger):
        """Test source tracking adds new interview ID"""
        entity = {
            "name": "Excel",
            "mentioned_in_interviews": "[1, 2]",
            "source_count": 2
        }
        
        updated = merger.update_source_tracking(entity, 3)
        
        mentioned_in = json.loads(updated["mentioned_in_interviews"])
        assert 3 in mentioned_in
        assert updated["source_count"] == 3
    
    def test_update_source_tracking_avoids_duplicates(self, merger):
        """Test source tracking doesn't add duplicate interview IDs"""
        entity = {
            "name": "Excel",
            "mentioned_in_interviews": "[1, 2]",
            "source_count": 2
        }
        
        updated = merger.update_source_tracking(entity, 2)  # Already exists
        
        mentioned_in = json.loads(updated["mentioned_in_interviews"])
        assert mentioned_in.count(2) == 1
        assert updated["source_count"] == 2
    
    def test_update_source_tracking_initializes_empty(self, merger):
        """Test source tracking initializes for new entity"""
        entity = {
            "name": "Excel"
        }
        
        updated = merger.update_source_tracking(entity, 1)
        
        mentioned_in = json.loads(updated["mentioned_in_interviews"])
        assert mentioned_in == [1]
        assert updated["source_count"] == 1
    
    def test_update_source_tracking_updates_dates(self, merger):
        """Test source tracking updates date fields"""
        entity = {
            "name": "Excel",
            "mentioned_in_interviews": "[1]",
            "source_count": 1
        }
        
        updated = merger.update_source_tracking(entity, 2)
        
        assert "first_mentioned_date" in updated
        assert "last_mentioned_date" in updated
    
    # Test 4: Attribute Merging
    
    def test_merge_attributes_keeps_existing_non_empty(self, merger):
        """Test attribute merging keeps existing non-empty values"""
        new_entity = {
            "name": "Excel",
            "description": "New description"
        }
        
        existing_entity = {
            "name": "Excel",
            "description": "Existing description",
            "priority": "high"
        }
        
        merged = merger.merge_attributes(new_entity, existing_entity, [])
        
        # Should keep existing description (not empty)
        assert merged["description"] == "Existing description"
        # Should keep existing priority
        assert merged["priority"] == "high"
    
    def test_merge_attributes_fills_empty_values(self, merger):
        """Test attribute merging fills empty values from new entity"""
        new_entity = {
            "name": "Excel",
            "priority": "high"
        }
        
        existing_entity = {
            "name": "Excel",
            "priority": None  # Empty
        }
        
        merged = merger.merge_attributes(new_entity, existing_entity, [])
        
        # Should use new value for empty field
        assert merged["priority"] == "high"
    
    def test_merge_attributes_skips_contradicting_attributes(self, merger):
        """Test attribute merging skips contradicting attributes"""
        new_entity = {
            "name": "Excel",
            "frequency": "daily"
        }
        
        existing_entity = {
            "name": "Excel",
            "frequency": "weekly"
        }
        
        contradictions = [{"attribute": "frequency"}]
        
        merged = merger.merge_attributes(new_entity, existing_entity, contradictions)
        
        # Should keep existing value for contradicting attribute
        assert merged["frequency"] == "weekly"
    
    def test_merge_attributes_combines_lists(self, merger):
        """Test attribute merging combines list values"""
        new_entity = {
            "name": "Excel",
            "tags": ["spreadsheet", "microsoft"]
        }
        
        existing_entity = {
            "name": "Excel",
            "tags": ["office", "spreadsheet"]
        }
        
        merged = merger.merge_attributes(new_entity, existing_entity, [])
        
        # Should combine and deduplicate lists
        assert "spreadsheet" in merged["tags"]
        assert "microsoft" in merged["tags"]
        assert "office" in merged["tags"]
        assert merged["tags"].count("spreadsheet") == 1
    
    # Test 5: Full Merge Operation
    
    def test_merge_combines_all_operations(self, merger):
        """Test merge performs all operations correctly"""
        new_entity = {
            "name": "Excel",
            "description": "Spreadsheet tool",
            "frequency": "daily",
            "interview_id": 2
        }
        
        existing_entity = {
            "id": 1,
            "name": "Excel",
            "description": "Microsoft Excel",
            "mentioned_in_interviews": "[1]",
            "source_count": 1,
            "merged_entity_ids": "[]"
        }
        
        merged = merger.merge(new_entity, existing_entity, 2, 0.95)
        
        # Check source tracking updated
        assert merged["source_count"] == 2
        mentioned_in = json.loads(merged["mentioned_in_interviews"])
        assert 2 in mentioned_in
        
        # Check description combined
        assert "Microsoft Excel" in merged["description"] or "Spreadsheet tool" in merged["description"]
        
        # Check consolidation flags set
        assert merged["is_consolidated"] == 1
        assert "consolidated_at" in merged
    
    def test_merge_detects_and_flags_contradictions(self, merger):
        """Test merge detects contradictions and sets flags"""
        new_entity = {
            "name": "Excel",
            "frequency": "daily",
            "interview_id": 2
        }
        
        existing_entity = {
            "id": 1,
            "name": "Excel",
            "frequency": "weekly",
            "mentioned_in_interviews": "[1]",
            "source_count": 1,
            "merged_entity_ids": "[]"
        }
        
        merged = merger.merge(new_entity, existing_entity, 2, 0.90)
        
        # Should flag contradictions
        assert merged.get("has_contradictions") == 1
        assert "contradiction_details" in merged
    
    # Test 6: Value Similarity Calculation
    
    def test_calculate_value_similarity_exact_match(self, merger):
        """Test value similarity for exact matches"""
        similarity = merger._calculate_value_similarity("daily", "daily")
        assert similarity == 1.0
    
    def test_calculate_value_similarity_synonyms(self, merger):
        """Test value similarity recognizes synonyms"""
        similarity = merger._calculate_value_similarity("high", "alta")
        assert similarity == 1.0
        
        similarity = merger._calculate_value_similarity("daily", "diario")
        assert similarity == 1.0
    
    def test_calculate_value_similarity_fuzzy_match(self, merger):
        """Test value similarity uses fuzzy matching"""
        similarity = merger._calculate_value_similarity("Excel", "Excel spreadsheet")
        assert 0.5 <= similarity <= 1.0
    
    def test_calculate_value_similarity_different_values(self, merger):
        """Test value similarity for completely different values"""
        similarity = merger._calculate_value_similarity("daily", "monthly")
        assert similarity < 0.7


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
