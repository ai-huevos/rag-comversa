"""
ExtractionMonitor - Real-time extraction monitoring and reporting
Tracks metrics, time, costs, and quality for each interview
"""
import time
from typing import Dict, List, Any, Optional
from datetime import datetime


class ExtractionMetrics:
    """Metrics for a single interview extraction"""

    def __init__(self, interview_id: int, company: str, respondent: str):
        self.interview_id = interview_id
        self.company = company
        self.respondent = respondent
        self.start_time = time.time()
        self.end_time = None
        self.duration = None
        self.success = False
        self.error = None

        # Entity counts
        self.entity_counts = {}

        # Quality metrics
        self.validation_errors = 0
        self.validation_warnings = 0
        self.missing_entity_types = []

        # Cost metrics (if available)
        self.tokens_used = 0
        self.estimated_cost = 0.0

    def finish(self, success: bool = True, error: str = None):
        """Mark extraction as finished"""
        self.end_time = time.time()
        self.duration = self.end_time - self.start_time
        self.success = success
        self.error = error

    def set_entity_counts(self, entity_counts: Dict[str, int]):
        """Set entity counts for all types"""
        self.entity_counts = entity_counts

    def set_quality_metrics(self, errors: int, warnings: int, missing_types: List[str]):
        """Set quality validation metrics"""
        self.validation_errors = errors
        self.validation_warnings = warnings
        self.missing_entity_types = missing_types

    def set_cost_metrics(self, tokens: int, cost: float):
        """Set cost metrics"""
        self.tokens_used = tokens
        self.estimated_cost = cost

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "interview_id": self.interview_id,
            "company": self.company,
            "respondent": self.respondent,
            "duration": self.duration,
            "success": self.success,
            "error": self.error,
            "entity_counts": self.entity_counts,
            "total_entities": sum(self.entity_counts.values()),
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "missing_entity_types": self.missing_entity_types,
            "tokens_used": self.tokens_used,
            "estimated_cost": self.estimated_cost
        }


class ExtractionMonitor:
    """
    Monitors extraction progress and generates real-time reports
    Tracks metrics for all interviews and provides summaries
    """

    def __init__(self, total_interviews: int = 0):
        """
        Initialize monitor

        Args:
            total_interviews: Total number of interviews to process (for progress tracking)
        """
        self.total_interviews = total_interviews
        self.metrics = []  # List of ExtractionMetrics
        self.start_time = time.time()
        self.current_metric = None

    def start_interview(self, interview_id: int, company: str, respondent: str) -> ExtractionMetrics:
        """
        Start tracking a new interview

        Args:
            interview_id: Interview ID
            company: Company name
            respondent: Respondent name

        Returns:
            ExtractionMetrics for this interview
        """
        metric = ExtractionMetrics(interview_id, company, respondent)
        self.current_metric = metric
        return metric

    def finish_interview(self, metric: ExtractionMetrics, success: bool = True, error: str = None):
        """
        Finish tracking an interview

        Args:
            metric: ExtractionMetrics for the interview
            success: Whether extraction succeeded
            error: Error message if failed
        """
        metric.finish(success, error)
        self.metrics.append(metric)
        self.current_metric = None

    def record_interview(
        self,
        interview_id: int,
        company: str,
        respondent: str,
        entity_counts: Dict[str, int],
        duration: float = None,
        success: bool = True,
        error: str = None,
        validation_errors: int = 0,
        validation_warnings: int = 0,
        missing_entity_types: List[str] = None,
        tokens: int = 0,
        cost: float = 0.0
    ):
        """
        Record metrics for a completed interview

        Args:
            interview_id: Interview ID
            company: Company name
            respondent: Respondent name
            entity_counts: Dictionary of entity type -> count
            duration: Processing duration in seconds
            success: Whether extraction succeeded
            error: Error message if failed
            validation_errors: Number of validation errors
            validation_warnings: Number of validation warnings
            missing_entity_types: List of missing entity types
            tokens: Number of tokens used
            cost: Estimated cost in dollars
        """
        metric = ExtractionMetrics(interview_id, company, respondent)

        if duration:
            metric.end_time = metric.start_time + duration
            metric.duration = duration
        else:
            metric.finish(success, error)

        metric.set_entity_counts(entity_counts)
        metric.set_quality_metrics(validation_errors, validation_warnings, missing_entity_types or [])
        metric.set_cost_metrics(tokens, cost)

        self.metrics.append(metric)

    def record_error(self, interview_id: int, company: str, respondent: str, error: str):
        """
        Record a failed interview

        Args:
            interview_id: Interview ID
            company: Company name
            respondent: Respondent name
            error: Error message
        """
        metric = ExtractionMetrics(interview_id, company, respondent)
        metric.finish(success=False, error=error)
        self.metrics.append(metric)

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all processed interviews

        Returns:
            Dictionary with summary metrics
        """
        if not self.metrics:
            return {
                "total_processed": 0,
                "total_expected": self.total_interviews,
                "progress_pct": 0,
                "success_count": 0,
                "error_count": 0,
                "avg_duration": 0,
                "total_duration": 0,
                "avg_entities": 0,
                "total_entities": 0,
                "entity_counts": {},
                "avg_cost": 0,
                "total_cost": 0,
                "quality_issues": 0
            }

        successful_metrics = [m for m in self.metrics if m.success]
        failed_metrics = [m for m in self.metrics if not m.success]

        total_processed = len(self.metrics)
        success_count = len(successful_metrics)
        error_count = len(failed_metrics)

        # Duration metrics
        durations = [m.duration for m in successful_metrics if m.duration]
        avg_duration = sum(durations) / len(durations) if durations else 0
        total_duration = sum(durations) if durations else 0

        # Entity metrics
        entity_totals = {}
        for metric in successful_metrics:
            for entity_type, count in metric.entity_counts.items():
                entity_totals[entity_type] = entity_totals.get(entity_type, 0) + count

        total_entities = sum(entity_totals.values())
        avg_entities = total_entities / success_count if success_count > 0 else 0

        # Cost metrics
        total_cost = sum(m.estimated_cost for m in successful_metrics)
        avg_cost = total_cost / success_count if success_count > 0 else 0

        # Quality metrics
        quality_issues = sum(m.validation_errors for m in successful_metrics)

        # Progress
        progress_pct = (total_processed / self.total_interviews * 100) if self.total_interviews > 0 else 0

        # Estimated time remaining
        if avg_duration > 0 and self.total_interviews > 0:
            remaining_interviews = self.total_interviews - total_processed
            estimated_time_remaining = avg_duration * remaining_interviews
        else:
            estimated_time_remaining = 0

        return {
            "total_processed": total_processed,
            "total_expected": self.total_interviews,
            "progress_pct": progress_pct,
            "success_count": success_count,
            "error_count": error_count,
            "avg_duration": avg_duration,
            "total_duration": total_duration,
            "estimated_time_remaining": estimated_time_remaining,
            "avg_entities": avg_entities,
            "total_entities": total_entities,
            "entity_counts": entity_totals,
            "avg_cost": avg_cost,
            "total_cost": total_cost,
            "quality_issues": quality_issues
        }

    def print_summary(self, detailed: bool = False):
        """
        Print real-time summary of extraction progress

        Args:
            detailed: If True, print detailed entity counts
        """
        summary = self.get_summary()

        print(f"\n{'='*70}")
        print(f"📊 EXTRACTION PROGRESS SUMMARY")
        print(f"{'='*70}")

        # Progress
        print(f"\n📈 Progress:")
        print(f"  Processed: {summary['total_processed']}/{summary['total_expected']} ({summary['progress_pct']:.1f}%)")
        print(f"  Success: {summary['success_count']}")
        print(f"  Errors: {summary['error_count']}")

        # Time metrics
        if summary['avg_duration'] > 0:
            print(f"\n⏱️  Time:")
            print(f"  Avg per interview: {summary['avg_duration']:.1f}s")
            print(f"  Total elapsed: {summary['total_duration']:.1f}s ({summary['total_duration']/60:.1f}m)")
            if summary['estimated_time_remaining'] > 0:
                print(f"  Estimated remaining: {summary['estimated_time_remaining']:.1f}s ({summary['estimated_time_remaining']/60:.1f}m)")

        # Entity metrics
        if summary['total_entities'] > 0:
            print(f"\n📋 Entities:")
            print(f"  Total extracted: {summary['total_entities']}")
            print(f"  Avg per interview: {summary['avg_entities']:.1f}")

            if detailed and summary['entity_counts']:
                print(f"\n  By type:")
                for entity_type, count in sorted(summary['entity_counts'].items(), key=lambda x: x[1], reverse=True):
                    print(f"    {entity_type}: {count}")

        # Cost metrics
        if summary['total_cost'] > 0:
            print(f"\n💰 Cost:")
            print(f"  Total: ${summary['total_cost']:.4f}")
            print(f"  Avg per interview: ${summary['avg_cost']:.4f}")

        # Quality metrics
        if summary['quality_issues'] > 0:
            print(f"\n⚠️  Quality:")
            print(f"  Validation errors: {summary['quality_issues']}")

        print(f"\n{'='*70}")

    def print_final_report(self):
        """Print comprehensive final report"""
        print(f"\n{'='*70}")
        print(f"📊 FINAL EXTRACTION REPORT")
        print(f"{'='*70}")

        summary = self.get_summary()

        print(f"\n✅ Completion:")
        print(f"  Total interviews: {summary['total_expected']}")
        print(f"  Successfully processed: {summary['success_count']}")
        print(f"  Failed: {summary['error_count']}")
        print(f"  Success rate: {summary['success_count']/summary['total_processed']*100:.1f}%" if summary['total_processed'] > 0 else "  Success rate: 0%")

        print(f"\n⏱️  Performance:")
        print(f"  Total time: {summary['total_duration']:.1f}s ({summary['total_duration']/60:.1f}m)")
        print(f"  Avg time per interview: {summary['avg_duration']:.1f}s")

        print(f"\n📋 Entities Extracted:")
        print(f"  Total: {summary['total_entities']}")
        print(f"  Avg per interview: {summary['avg_entities']:.1f}")

        if summary['entity_counts']:
            print(f"\n  Breakdown by type:")
            for entity_type, count in sorted(summary['entity_counts'].items(), key=lambda x: x[1], reverse=True):
                avg_per_interview = count / summary['success_count'] if summary['success_count'] > 0 else 0
                print(f"    {entity_type:30s}: {count:4d} (avg {avg_per_interview:.1f}/interview)")

        if summary['total_cost'] > 0:
            print(f"\n💰 Costs:")
            print(f"  Total estimated cost: ${summary['total_cost']:.4f}")
            print(f"  Avg cost per interview: ${summary['avg_cost']:.4f}")

        if summary['quality_issues'] > 0:
            print(f"\n⚠️  Quality Issues:")
            print(f"  Total validation errors: {summary['quality_issues']}")

        # Show failed interviews if any
        failed_metrics = [m for m in self.metrics if not m.success]
        if failed_metrics:
            print(f"\n❌ Failed Interviews:")
            for metric in failed_metrics:
                print(f"  - {metric.company} / {metric.respondent}: {metric.error[:100]}")

        print(f"\n{'='*70}")
        print(f"✓ Extraction complete!")
        print(f"{'='*70}")

    def export_metrics(self, filepath: str):
        """
        Export metrics to JSON file

        Args:
            filepath: Path to output JSON file
        """
        import json

        data = {
            "summary": self.get_summary(),
            "interviews": [m.to_dict() for m in self.metrics],
            "timestamp": datetime.now().isoformat()
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"✓ Metrics exported to: {filepath}")
