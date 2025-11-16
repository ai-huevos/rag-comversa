"""
Test Extraction Safeguards

Validates that Phase 3 prevention measures work correctly:
1. Extractor initialization verification
2. Zero-entity detection
3. Extraction status logic
4. Batch validation

See: reports/phase3_prevention_implementation.md
"""
import pytest
from intelligence_capture.extraction_safeguards import (
    ExtractionSafeguards,
    ExtractionFailureError,
    ExtractorConfigurationError,
    EntityCountMetrics
)


class TestExtractorInitializationVerification:
    """Test extractor initialization checks"""

    def test_complete_v2_extractors(self):
        """Should pass with all 13 v2.0 extractors"""
        v2_extractors = {
            "communication_channels": "mock",
            "systems_v2": "mock",
            "decision_points": "mock",
            "data_flows": "mock",
            "temporal_patterns": "mock",
            "failure_modes": "mock",
            "pain_points_v2": "mock",
            "automation_candidates_v2": "mock",
            "team_structures": "mock",
            "knowledge_gaps": "mock",
            "success_patterns": "mock",
            "budget_constraints": "mock",
            "external_dependencies": "mock"
        }

        is_valid, missing = ExtractionSafeguards.verify_extractor_initialization(
            v2_extractors,
            has_legacy_extractors=True
        )

        assert is_valid == True
        assert len(missing) == 0

    def test_missing_v2_extractors(self):
        """Should raise error with missing v2.0 extractors"""
        v2_extractors = {
            "communication_channels": "mock",
            "systems_v2": "mock"
            # Missing 11 extractors
        }

        with pytest.raises(ExtractorConfigurationError) as exc_info:
            ExtractionSafeguards.verify_extractor_initialization(
                v2_extractors,
                has_legacy_extractors=True
            )

        assert "Incomplete extractor initialization" in str(exc_info.value)
        assert "5/16" in str(exc_info.value)  # 2 v2 extractors + 3 legacy = 5 total

    def test_missing_legacy_extractors(self):
        """Should flag missing legacy extractors"""
        v2_extractors = {
            name: "mock"
            for name in ExtractionSafeguards.EXPECTED_V2_EXTRACTORS
        }

        with pytest.raises(ExtractorConfigurationError):
            ExtractionSafeguards.verify_extractor_initialization(
                v2_extractors,
                has_legacy_extractors=False  # Legacy missing
            )


class TestZeroEntityDetection:
    """Test zero-entity failure detection"""

    def test_zero_entities_raises_error(self):
        """Should raise ExtractionFailureError for zero entities"""
        entities = {
            "pain_points": [],
            "processes": [],
            "systems": []
        }

        meta = {"respondent": "Test User", "company": "Test Co"}

        with pytest.raises(ExtractionFailureError) as exc_info:
            ExtractionSafeguards.validate_extraction_results(
                entities,
                interview_id=1,
                meta=meta
            )

        assert "ZERO ENTITIES EXTRACTED" in str(exc_info.value)
        assert "Test User" in str(exc_info.value)

    def test_single_entity_passes(self):
        """Should pass with at least one entity"""
        entities = {
            "pain_points": [{"description": "Test pain point"}],
            "processes": [],
            "systems": []
        }

        meta = {"respondent": "Test User", "company": "Test Co"}

        metrics = ExtractionSafeguards.validate_extraction_results(
            entities,
            interview_id=1,
            meta=meta
        )

        assert metrics.total_entities == 1
        assert metrics.has_zero_entities == False

    def test_low_entity_count_warning(self, caplog):
        """Should warn on low entity counts"""
        import logging
        caplog.set_level(logging.WARNING)

        entities = {
            "pain_points": [{"description": "Test"}],
            "processes": [{"name": "Test"}]
            # Total: 2 entities (below threshold of 5)
        }

        meta = {"respondent": "Test User", "company": "Test Co"}

        metrics = ExtractionSafeguards.validate_extraction_results(
            entities,
            interview_id=1,
            meta=meta
        )

        assert metrics.total_entities == 2
        assert "Low entity count" in caplog.text


class TestBatchValidation:
    """Test batch-level validation"""

    def test_complete_batch_failure(self):
        """Should raise error if all interviews have zero entities"""
        metrics_list = [
            EntityCountMetrics(
                total_entities=0,
                entities_by_type={},
                interviews_processed=1,
                avg_entities_per_interview=0.0,
                zero_entity_interviews=1,
                low_entity_interviews=1
            )
            for _ in range(10)
        ]

        with pytest.raises(ExtractionFailureError) as exc_info:
            ExtractionSafeguards.validate_batch_results(metrics_list)

        assert "COMPLETE BATCH FAILURE" in str(exc_info.value)
        assert "Nov 11" in str(exc_info.value)

    def test_anomalous_extraction_rates(self, caplog):
        """Should warn on anomalously low extraction rates"""
        import logging
        caplog.set_level(logging.WARNING)

        metrics_list = [
            EntityCountMetrics(
                total_entities=3,  # Below expected average of 20
                entities_by_type={"pain_points": 3},
                interviews_processed=1,
                avg_entities_per_interview=3.0,
                zero_entity_interviews=0,
                low_entity_interviews=1
            )
            for _ in range(10)
        ]

        batch_metrics = ExtractionSafeguards.validate_batch_results(metrics_list)

        assert batch_metrics.total_entities == 30
        assert batch_metrics.interviews_processed == 10
        assert "Anomalous extraction rates" in caplog.text

    def test_high_zero_entity_rate(self, caplog):
        """Should warn if >10% of interviews have zero entities"""
        import logging
        caplog.set_level(logging.WARNING)

        metrics_list = []

        # 15% with zero entities (3 out of 20)
        for i in range(20):
            if i < 3:
                metrics = EntityCountMetrics(
                    total_entities=0,
                    entities_by_type={},
                    interviews_processed=1,
                    avg_entities_per_interview=0.0,
                    zero_entity_interviews=1,
                    low_entity_interviews=1
                )
            else:
                metrics = EntityCountMetrics(
                    total_entities=20,
                    entities_by_type={"pain_points": 10, "processes": 10},
                    interviews_processed=1,
                    avg_entities_per_interview=20.0,
                    zero_entity_interviews=0,
                    low_entity_interviews=0
                )
            metrics_list.append(metrics)

        batch_metrics = ExtractionSafeguards.validate_batch_results(metrics_list)

        assert batch_metrics.zero_entity_rate == 15.0
        assert "High zero-entity rate" in caplog.text

    def test_healthy_batch(self):
        """Should pass validation for healthy extraction batch"""
        metrics_list = [
            EntityCountMetrics(
                total_entities=25,
                entities_by_type={"pain_points": 10, "processes": 8, "systems": 7},
                interviews_processed=1,
                avg_entities_per_interview=25.0,
                zero_entity_interviews=0,
                low_entity_interviews=0
            )
            for _ in range(44)  # Full batch
        ]

        batch_metrics = ExtractionSafeguards.validate_batch_results(metrics_list)

        assert batch_metrics.total_entities == 25 * 44
        assert batch_metrics.avg_entities_per_interview == 25.0
        assert batch_metrics.zero_entity_interviews == 0
        assert batch_metrics.has_zero_entities == False
        assert batch_metrics.has_anomalous_counts == False


class TestEntityCountMetrics:
    """Test EntityCountMetrics dataclass"""

    def test_has_zero_entities(self):
        """Test zero entity detection"""
        metrics = EntityCountMetrics(
            total_entities=0,
            entities_by_type={},
            interviews_processed=1,
            avg_entities_per_interview=0.0,
            zero_entity_interviews=1,
            low_entity_interviews=1
        )

        assert metrics.has_zero_entities == True
        assert metrics.has_anomalous_counts == True
        assert metrics.zero_entity_rate == 100.0

    def test_has_anomalous_counts(self):
        """Test anomalous count detection"""
        metrics = EntityCountMetrics(
            total_entities=4,
            entities_by_type={"pain_points": 4},
            interviews_processed=1,
            avg_entities_per_interview=4.0,
            zero_entity_interviews=0,
            low_entity_interviews=1
        )

        assert metrics.has_zero_entities == False
        assert metrics.has_anomalous_counts == True  # avg < 5

    def test_healthy_metrics(self):
        """Test healthy extraction metrics"""
        metrics = EntityCountMetrics(
            total_entities=30,
            entities_by_type={"pain_points": 15, "processes": 10, "systems": 5},
            interviews_processed=1,
            avg_entities_per_interview=30.0,
            zero_entity_interviews=0,
            low_entity_interviews=0
        )

        assert metrics.has_zero_entities == False
        assert metrics.has_anomalous_counts == False
        assert metrics.zero_entity_rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
