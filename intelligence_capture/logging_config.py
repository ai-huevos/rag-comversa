"""
Centralized logging configuration for Intelligence Capture System
Provides consistent file and console logging across all components
"""
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


def setup_extraction_logging(
    log_file: Optional[Path] = None,
    log_level: int = logging.INFO,
    logger_name: str = "intelligence_capture"
) -> logging.Logger:
    """
    Configure logging for extraction pipeline

    Args:
        log_file: Path to log file (default: logs/extraction.log)
        log_level: Logging level (default: INFO)
        logger_name: Name of logger (default: intelligence_capture)

    Returns:
        Configured logger instance
    """
    # Default log file
    if log_file is None:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / "extraction.log"

    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create logger
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler with detailed formatting
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)

    # Console handler with simpler formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter('%(message)s')
    console_handler.setFormatter(console_formatter)

    # Add handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Prevent propagation to avoid duplicate logs
    logger.propagate = False

    return logger


def log_extraction_start(logger: logging.Logger, interview_count: int, batch_size: Optional[int] = None):
    """Log extraction start with metadata"""
    separator = "=" * 70
    logger.info(separator)
    logger.info("🚀 EXTRACTION PIPELINE STARTED")
    logger.info(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   Total interviews: {interview_count}")
    if batch_size:
        logger.info(f"   Batch size: {batch_size}")
    logger.info(separator)


def log_extraction_complete(
    logger: logging.Logger,
    total_interviews: int,
    processed: int,
    failed: int,
    duration_seconds: float,
    entities_extracted: dict
):
    """Log extraction completion with summary statistics"""
    separator = "=" * 70
    logger.info(separator)
    logger.info("✅ EXTRACTION PIPELINE COMPLETED")
    logger.info(f"   Duration: {duration_seconds:.1f}s ({duration_seconds/60:.1f}m)")
    logger.info(f"   Processed: {processed}/{total_interviews}")
    logger.info(f"   Failed: {failed}")
    logger.info(f"   Avg time/interview: {duration_seconds/total_interviews:.1f}s")
    logger.info("")
    logger.info("📊 ENTITIES EXTRACTED:")
    for entity_type, count in sorted(entities_extracted.items()):
        logger.info(f"   {entity_type}: {count}")
    logger.info(separator)


def log_interview_start(logger: logging.Logger, interview_num: int, total: int, company: str, respondent: str):
    """Log individual interview processing start"""
    logger.info(f"\n[{interview_num}/{total}] 📝 Processing: {company} / {respondent}")


def log_interview_complete(logger: logging.Logger, interview_id: str, duration: float, entities: dict):
    """Log individual interview processing completion"""
    total_entities = sum(entities.values())
    logger.info(f"  ✅ Completed in {duration:.1f}s | Total entities: {total_entities}")
    for entity_type, count in entities.items():
        if count > 0:
            logger.info(f"     - {entity_type}: {count}")


def log_interview_error(logger: logging.Logger, interview_id: str, error: Exception):
    """Log interview processing error"""
    logger.error(f"  ❌ Error processing interview {interview_id}: {str(error)}")
    logger.exception(error)


def log_extractor_call(logger: logging.Logger, extractor_name: str, attempt: int = 1):
    """Log extractor API call"""
    logger.debug(f"  🤖 Calling {extractor_name} (attempt {attempt})")


def log_extractor_success(logger: logging.Logger, extractor_name: str, count: int, duration: float):
    """Log successful extraction"""
    logger.debug(f"  ✓ {extractor_name}: {count} entities in {duration:.2f}s")


def log_extractor_error(logger: logging.Logger, extractor_name: str, error: str):
    """Log extraction error"""
    logger.warning(f"  ⚠️  {extractor_name} failed: {error}")


def log_batch_progress(logger: logging.Logger, batch_num: int, total_batches: int):
    """Log batch processing progress"""
    logger.info(f"\n{'='*70}")
    logger.info(f"📦 BATCH {batch_num}/{total_batches}")
    logger.info(f"{'='*70}")


def log_validation_results(logger: logging.Logger, validation_errors: list):
    """Log validation results"""
    if validation_errors:
        logger.warning(f"  ⚠️  Validation issues found: {len(validation_errors)} errors")
        for error in validation_errors[:5]:  # Log first 5 errors
            logger.warning(f"     - {error}")
        if len(validation_errors) > 5:
            logger.warning(f"     ... and {len(validation_errors) - 5} more")
    else:
        logger.info(f"  ✅ Validation passed")


def create_extraction_report(
    logger: logging.Logger,
    report_data: dict,
    report_file: Optional[Path] = None
) -> Path:
    """
    Create and save extraction report

    Args:
        logger: Logger instance
        report_data: Dictionary containing report data
        report_file: Path to save report (default: reports/extraction_report_{timestamp}.json)

    Returns:
        Path to saved report file
    """
    import json

    if report_file is None:
        reports_dir = Path(__file__).parent.parent / "reports"
        reports_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = reports_dir / f"extraction_report_{timestamp}.json"

    # Ensure directory exists
    report_file.parent.mkdir(parents=True, exist_ok=True)

    # Save report
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    logger.info(f"\n📄 Report saved: {report_file}")
    return report_file
