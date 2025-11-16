"""
Extraction Safeguards - Prevention measures for silent extraction failures

Implements validation checks identified in Phase 2 forensic analysis:
- Zero-entity failure detection
- Extractor initialization verification
- Entity count monitoring and alerts
- Pre-flight validation checks

See: reports/phase2_forensic_analysis.md
"""
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class ExtractionFailureError(Exception):
    """Raised when extraction fails with zero entities extracted"""
    pass


class ExtractorConfigurationError(Exception):
    """Raised when extractor initialization is incomplete"""
    pass


@dataclass
class EntityCountMetrics:
    """Metrics for entity extraction counts"""
    total_entities: int
    entities_by_type: Dict[str, int]
    interviews_processed: int
    avg_entities_per_interview: float
    zero_entity_interviews: int
    low_entity_interviews: int  # < 5 entities

    @property
    def has_zero_entities(self) -> bool:
        """Check if no entities were extracted"""
        return self.total_entities == 0

    @property
    def has_anomalous_counts(self) -> bool:
        """Check for anomalously low extraction rates"""
        if self.interviews_processed == 0:
            return False

        # Flag if avg < 5 entities per interview (expected: 15-50)
        return self.avg_entities_per_interview < 5.0

    @property
    def zero_entity_rate(self) -> float:
        """Percentage of interviews with zero entities"""
        if self.interviews_processed == 0:
            return 0.0
        return (self.zero_entity_interviews / self.interviews_processed) * 100


class ExtractionSafeguards:
    """Validates extraction pipeline to prevent silent failures"""

    # Expected entity types (based on forensic analysis)
    EXPECTED_V1_EXTRACTORS = {"processes", "kpis", "inefficiencies"}
    EXPECTED_V2_EXTRACTORS = {
        "communication_channels", "systems_v2", "decision_points",
        "data_flows", "temporal_patterns", "failure_modes",
        "pain_points_v2", "automation_candidates_v2", "team_structures",
        "knowledge_gaps", "success_patterns", "budget_constraints",
        "external_dependencies"
    }
    EXPECTED_TOTAL_EXTRACTORS = 16  # 13 v2.0 + 3 legacy

    # Entity count thresholds
    MIN_ENTITIES_PER_INTERVIEW = 1  # Absolute minimum
    EXPECTED_MIN_ENTITIES_PER_INTERVIEW = 5  # Warning threshold
    EXPECTED_AVG_ENTITIES_PER_INTERVIEW = 20  # Normal range: 15-50

    @classmethod
    def verify_extractor_initialization(
        cls,
        v2_extractors: Dict,
        has_legacy_extractors: bool = True
    ) -> Tuple[bool, List[str]]:
        """
        Verify all expected extractors are initialized

        Args:
            v2_extractors: Dictionary of initialized v2.0 extractors
            has_legacy_extractors: Whether legacy extractors are available

        Returns:
            (is_valid, missing_extractors)

        Raises:
            ExtractorConfigurationError: If critical extractors are missing
        """
        missing = []

        # Check v2.0 extractors
        initialized_v2 = set(v2_extractors.keys())
        missing_v2 = cls.EXPECTED_V2_EXTRACTORS - initialized_v2
        if missing_v2:
            missing.extend([f"v2.0:{name}" for name in missing_v2])

        # Check legacy extractors (processes, kpis, inefficiencies)
        if has_legacy_extractors:
            total_count = len(v2_extractors) + len(cls.EXPECTED_V1_EXTRACTORS)
        else:
            total_count = len(v2_extractors)
            missing.extend([f"v1.0:{name}" for name in cls.EXPECTED_V1_EXTRACTORS])

        # Validate total count
        if total_count < cls.EXPECTED_TOTAL_EXTRACTORS:
            error_msg = (
                f"Incomplete extractor initialization: {total_count}/{cls.EXPECTED_TOTAL_EXTRACTORS} loaded. "
                f"Missing: {', '.join(missing)}"
            )
            logger.error(error_msg)
            raise ExtractorConfigurationError(error_msg)

        is_valid = len(missing) == 0
        return is_valid, missing

    @classmethod
    def validate_extraction_results(
        cls,
        entities: Dict[str, List],
        interview_id: int,
        meta: Dict
    ) -> EntityCountMetrics:
        """
        Validate extraction results for a single interview

        Args:
            entities: Extracted entities dictionary
            interview_id: Interview ID for logging
            meta: Interview metadata

        Returns:
            EntityCountMetrics with extraction statistics

        Raises:
            ExtractionFailureError: If zero entities extracted
        """
        # Count entities by type
        entities_by_type = {}
        total_entities = 0

        for entity_type, entity_list in entities.items():
            count = len(entity_list) if entity_list else 0
            entities_by_type[entity_type] = count
            total_entities += count

        # Calculate metrics
        metrics = EntityCountMetrics(
            total_entities=total_entities,
            entities_by_type=entities_by_type,
            interviews_processed=1,
            avg_entities_per_interview=float(total_entities),
            zero_entity_interviews=1 if total_entities == 0 else 0,
            low_entity_interviews=1 if total_entities < cls.EXPECTED_MIN_ENTITIES_PER_INTERVIEW else 0
        )

        # Check for zero entities (CRITICAL)
        if metrics.has_zero_entities:
            respondent = meta.get('respondent', 'Unknown')
            company = meta.get('company', 'Unknown')
            error_msg = (
                f"ZERO ENTITIES EXTRACTED from interview {interview_id} "
                f"({company} / {respondent}). "
                f"This indicates extraction pipeline failure. "
                f"See reports/phase2_forensic_analysis.md"
            )
            logger.error(error_msg)
            raise ExtractionFailureError(error_msg)

        # Warn on low entity counts
        if total_entities < cls.EXPECTED_MIN_ENTITIES_PER_INTERVIEW:
            respondent = meta.get('respondent', 'Unknown')
            logger.warning(
                f"Low entity count for interview {interview_id} ({respondent}): "
                f"{total_entities} entities (expected >{cls.EXPECTED_MIN_ENTITIES_PER_INTERVIEW})"
            )

        return metrics

    @classmethod
    def validate_batch_results(
        cls,
        metrics_list: List[EntityCountMetrics]
    ) -> EntityCountMetrics:
        """
        Validate extraction results across a batch of interviews

        Args:
            metrics_list: List of metrics from individual interviews

        Returns:
            Aggregated EntityCountMetrics

        Raises:
            ExtractionFailureError: If anomalous extraction rates detected
        """
        if not metrics_list:
            raise ExtractionFailureError("No extraction metrics provided")

        # Aggregate metrics
        total_entities = sum(m.total_entities for m in metrics_list)
        interviews_processed = len(metrics_list)
        zero_entity_count = sum(m.zero_entity_interviews for m in metrics_list)
        low_entity_count = sum(m.low_entity_interviews for m in metrics_list)

        # Aggregate entity counts by type
        all_types = set()
        for m in metrics_list:
            all_types.update(m.entities_by_type.keys())

        entities_by_type = {}
        for entity_type in all_types:
            entities_by_type[entity_type] = sum(
                m.entities_by_type.get(entity_type, 0)
                for m in metrics_list
            )

        # Calculate batch metrics
        avg_entities = total_entities / interviews_processed if interviews_processed > 0 else 0.0

        batch_metrics = EntityCountMetrics(
            total_entities=total_entities,
            entities_by_type=entities_by_type,
            interviews_processed=interviews_processed,
            avg_entities_per_interview=avg_entities,
            zero_entity_interviews=zero_entity_count,
            low_entity_interviews=low_entity_count
        )

        # Check for complete batch failure
        if batch_metrics.has_zero_entities:
            error_msg = (
                f"COMPLETE BATCH FAILURE: Zero entities extracted from {interviews_processed} interviews. "
                f"This is identical to the Nov 11 incident. "
                f"Extraction pipeline is misconfigured or LLM API is failing. "
                f"ABORTING to prevent data loss."
            )
            logger.error(error_msg)
            raise ExtractionFailureError(error_msg)

        # Check for anomalous rates
        if batch_metrics.has_anomalous_counts:
            logger.warning(
                f"Anomalous extraction rates detected: "
                f"avg={batch_metrics.avg_entities_per_interview:.1f} entities/interview "
                f"(expected >{cls.EXPECTED_AVG_ENTITIES_PER_INTERVIEW})"
            )

        # Check for high zero-entity rate
        zero_rate = batch_metrics.zero_entity_rate
        if zero_rate > 10.0:  # More than 10% with zero entities
            logger.warning(
                f"High zero-entity rate: {zero_rate:.1f}% of interviews ({zero_entity_count}/{interviews_processed}) "
                f"extracted zero entities. Review extraction configuration."
            )

        # Log summary
        logger.info(
            f"Batch extraction summary: {total_entities} total entities, "
            f"avg={batch_metrics.avg_entities_per_interview:.1f}/interview, "
            f"zero-entity={zero_entity_count}, low-entity={low_entity_count}"
        )

        return batch_metrics

    @classmethod
    def pre_flight_check(
        cls,
        extractor,
        db,
        test_interview_id: Optional[int] = None
    ) -> bool:
        """
        Run pre-flight validation before batch extraction

        Args:
            extractor: IntelligenceExtractor instance
            db: Database instance
            test_interview_id: Optional interview ID to test (uses first if None)

        Returns:
            True if pre-flight checks pass

        Raises:
            ExtractorConfigurationError: If extractor validation fails
            ExtractionFailureError: If test extraction fails
        """
        logger.info("Running pre-flight checks...")

        # 1. Verify extractor initialization
        logger.info("  Checking extractor initialization...")
        has_v2 = hasattr(extractor, 'v2_extractors')
        has_legacy = hasattr(extractor, '_extract_processes')

        if has_v2:
            is_valid, missing = cls.verify_extractor_initialization(
                extractor.v2_extractors,
                has_legacy_extractors=has_legacy
            )
            logger.info(f"  ✓ All {cls.EXPECTED_TOTAL_EXTRACTORS} extractors initialized")
        else:
            logger.error("  ✗ No v2 extractors found")
            raise ExtractorConfigurationError("v2 extractors not initialized")

        # 2. Test single interview extraction (if database has interviews)
        if test_interview_id or db:
            logger.info("  Testing single interview extraction...")
            # TODO: Implement test extraction
            # For now, skip if no test interview specified
            if test_interview_id:
                logger.warning("  ⚠️  Test interview extraction not yet implemented")
            else:
                logger.info("  ⓘ  No test interview specified, skipping extraction test")

        logger.info("✓ Pre-flight checks passed")
        return True
