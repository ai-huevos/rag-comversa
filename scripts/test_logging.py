#!/usr/bin/env python3
"""
Test extraction logging infrastructure
Quick validation that logging is working correctly
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.logging_config import (
    setup_extraction_logging,
    log_extraction_start,
    log_extraction_complete,
    log_interview_start,
    log_interview_complete,
    log_interview_error,
    log_batch_progress
)


def main():
    """Test logging functionality"""
    print("\n🧪 Testing Extraction Logging Infrastructure\n")
    print("=" * 70)

    # Setup logger
    logger = setup_extraction_logging()
    print("✅ Logger initialized")

    # Test extraction start log
    log_extraction_start(logger, 44, 5)
    print("✅ Extraction start logged")

    # Test batch progress log
    log_batch_progress(logger, 1, 9)
    print("✅ Batch progress logged")

    # Test interview start log
    log_interview_start(logger, 1, 44, "Los Tajibos", "IT Manager")
    print("✅ Interview start logged")

    # Test interview complete log
    log_interview_complete(logger, "interview_1", 45.3, {
        "PainPoint": 5,
        "System": 3,
        "AutomationCandidate": 2
    })
    print("✅ Interview complete logged")

    # Test interview error log
    try:
        raise ValueError("Test extraction error")
    except Exception as e:
        log_interview_error(logger, "test_interview", e)
        print("✅ Interview error logged")

    # Test extraction complete log
    log_extraction_complete(
        logger,
        total_interviews=44,
        processed=42,
        failed=2,
        duration_seconds=1834.5,
        entities_extracted={
            "PainPoint": 120,
            "System": 89,
            "AutomationCandidate": 67,
            "DataFlow": 45,
            "TemporalPattern": 56
        }
    )
    print("✅ Extraction complete logged")

    print("\n" + "=" * 70)
    print("✅ All logging tests passed!")
    print(f"\n📄 Check log file: logs/extraction.log")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
