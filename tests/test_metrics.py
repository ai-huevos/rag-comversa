#!/usr/bin/env python3
"""
Unit Tests for ConsolidationMetrics

Tests:
- Duplicate tracking
- Contradiction tracking
- API call tracking
- Quality metrics calculation
- JSON export
- Console display
"""
import pytest
import json
import tempfile
from pathlib import Path
from intelligence_capture.metrics import ConsolidationMetrics


class TestConsolidationMetrics:
    """Test suite for ConsolidationMetrics"""
    
    @pytest.fixture
    def metrics(self):
        """Create metrics instance"""
        return ConsolidationMetrics()
    
    def test_track_duplicate_found(self, metrics):
        """Test tracking duplicate entities"""
        metrics.track_duplicate_found("systems", 0.92)
        metrics.track_duplicate_found("systems", 0.88)
        metrics.track_duplicate_found("pain_points", 0.85)
        
        assert metrics.duplicates_by_type["systems"] == 2
        assert metrics.duplicates_by_type["pain_points"] == 1
        
        # Check similarity scores
        assert len(metrics.similarity_scores_by_type["systems"]) == 2
        assert 0.92 in metrics.similarity_scores_by_type["systems"]
        assert 0.88 in metrics.similarity_scores_by_type["systems"]
    
    def test_get_avg_similarity_by_type(self, metrics):
        """Test average similarity calculation"""
        metrics.track_duplicate_found("systems", 0.90)
        metrics.track_duplicate_found("systems", 0.80)
        metrics.track_duplicate_found("systems", 0.85)
        
        avg_similarity = metrics.get_avg_similarity_by_type()
        
        assert "systems" in avg_similarity
        # Average of 0.90, 0.80, 0.85 = 0.85
        assert avg_similarity["systems"] == 0.85
    
    def test_track_contradiction(self, metrics):
        """Test tracking contradictions"""
        metrics.track_contradiction("pain_points")
        metrics.track_contradiction("pain_points")
        metrics.track_contradiction("systems")
        
        assert metrics.contradictions_by_type["pain_points"] == 2
        assert metrics.contradictions_by_type["systems"] == 1
    
    def test_track_processing_time(self, metrics):
        """Test tracking processing time"""
        metrics.track_processing_time("systems", 1.5)
        metrics.track_processing_time("systems", 0.5)
        metrics.track_processing_time("pain_points", 2.0)
        
        assert metrics.processing_time_by_type["systems"] == 2.0
        assert metrics.processing_time_by_type["pain_points"] == 2.0
        assert metrics.get_total_processing_time() == 4.0
    
    def test_track_api_call(self, metrics):
        """Test tracking API calls"""
        # Track cache hits
        metrics.track_api_call(cache_hit=True)
        metrics.track_api_call(cache_hit=True)
        
        # Track cache misses
        metrics.track_api_call(cache_hit=False)
        
        # Track failed call
        metrics.track_api_call(cache_hit=False, failed=True)
        
        assert metrics.api_metrics["total_calls"] == 4
        assert metrics.api_metrics["cache_hits"] == 2
        assert metrics.api_metrics["cache_misses"] == 2
        assert metrics.api_metrics["failed_calls"] == 1
    
    def test_get_cache_hit_rate(self, metrics):
        """Test cache hit rate calculation"""
        # 3 hits out of 4 calls = 75%
        metrics.track_api_call(cache_hit=True)
        metrics.track_api_call(cache_hit=True)
        metrics.track_api_call(cache_hit=True)
        metrics.track_api_call(cache_hit=False)
        
        cache_hit_rate = metrics.get_cache_hit_rate()
        assert cache_hit_rate == 75.0
    
    def test_track_entity_counts(self, metrics):
        """Test tracking entity counts"""
        metrics.track_entity_processed()
        metrics.track_entity_processed()
        metrics.track_entity_merged()
        metrics.track_entity_created()
        
        assert metrics.entity_counts["processed"] == 2
        assert metrics.entity_counts["merged"] == 1
        assert metrics.entity_counts["created"] == 1
    
    def test_set_quality_metrics(self, metrics):
        """Test setting quality metrics"""
        metrics.set_quality_metrics(
            entities_before=100,
            entities_after=80,
            avg_confidence=0.85,
            contradiction_rate=5.5
        )
        
        assert metrics.quality_metrics["entities_before"] == 100
        assert metrics.quality_metrics["entities_after"] == 80
        assert metrics.quality_metrics["duplicate_reduction_percentage"] == 20.0
        assert metrics.quality_metrics["avg_confidence_score"] == 0.85
        assert metrics.quality_metrics["contradiction_rate"] == 5.5
    
    def test_to_dict(self, metrics):
        """Test exporting metrics as dictionary"""
        metrics.track_duplicate_found("systems", 0.90)
        metrics.track_api_call(cache_hit=True)
        metrics.set_quality_metrics(100, 80, 0.85, 5.0)
        
        data = metrics.to_dict()
        
        assert "timestamp" in data
        assert "elapsed_time_seconds" in data
        assert "duplicates_by_type" in data
        assert "avg_similarity_by_type" in data
        assert "api_metrics" in data
        assert "quality_metrics" in data
        assert "entity_counts" in data
        
        assert data["duplicates_by_type"]["systems"] == 1
        assert data["api_metrics"]["cache_hit_rate_percentage"] == 100.0
    
    def test_export_to_json(self, metrics):
        """Test exporting metrics to JSON file"""
        metrics.track_duplicate_found("systems", 0.90)
        metrics.set_quality_metrics(100, 80, 0.85, 5.0)
        
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            metrics.export_to_json(temp_path)
            
            # Verify file exists and contains valid JSON
            assert temp_path.exists()
            
            with open(temp_path, 'r') as f:
                data = json.load(f)
            
            assert "timestamp" in data
            assert data["duplicates_by_type"]["systems"] == 1
        
        finally:
            if temp_path.exists():
                temp_path.unlink()
    
    def test_display_summary(self, metrics, capsys):
        """Test console display (just verify it doesn't crash)"""
        metrics.track_duplicate_found("systems", 0.90)
        metrics.track_api_call(cache_hit=True)
        metrics.set_quality_metrics(100, 80, 0.85, 5.0)
        
        # Should not raise any exceptions
        metrics.display_summary()
        
        # Verify some output was produced
        captured = capsys.readouterr()
        assert "CONSOLIDATION METRICS SUMMARY" in captured.out
        assert "Timing" in captured.out
        assert "Entity Counts" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
