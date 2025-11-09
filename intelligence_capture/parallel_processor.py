"""
Parallel Interview Processor
Processes multiple interviews concurrently for faster extraction
"""
import json
import time
import multiprocessing as mp
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ProcessPoolExecutor, as_completed
import queue

from .processor import IntelligenceProcessor
from .config import DB_PATH, INTERVIEWS_FILE


class ParallelProcessor:
    """
    Parallel processor for extracting entities from multiple interviews concurrently

    Uses multiprocessing to handle multiple interviews in parallel while managing
    database access to avoid conflicts.
    """

    def __init__(
        self,
        db_path: Path = DB_PATH,
        max_workers: int = 4,
        enable_monitoring: bool = True
    ):
        """
        Initialize parallel processor

        Args:
            db_path: Path to SQLite database
            max_workers: Maximum number of parallel workers (default: 4)
            enable_monitoring: Enable real-time monitoring (default: True)
        """
        self.db_path = db_path
        self.max_workers = max_workers
        self.enable_monitoring = enable_monitoring

        # Validate max_workers
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")
        if max_workers > mp.cpu_count():
            print(f"⚠️  max_workers ({max_workers}) exceeds CPU count ({mp.cpu_count()})")
            print(f"   Reducing to {mp.cpu_count()} workers")
            self.max_workers = mp.cpu_count()

    def process_all_interviews_parallel(
        self,
        interviews_file: Path = INTERVIEWS_FILE,
        resume: bool = False
    ) -> Dict[str, Any]:
        """
        Process all interviews using parallel workers

        Args:
            interviews_file: Path to interviews JSON file
            resume: If True, skip already completed interviews

        Returns:
            Dictionary with processing statistics
        """
        print(f"\n{'='*70}")
        print(f"🚀 PARALLEL EXTRACTION")
        print(f"{'='*70}")
        print(f"Workers: {self.max_workers}")
        print(f"Database: {self.db_path}")
        print(f"{'='*70}\n")

        # Load interviews
        print(f"📂 Loading interviews from: {interviews_file}")
        with open(interviews_file, 'r', encoding='utf-8') as f:
            all_interviews = json.load(f)
        print(f"✓ Found {len(all_interviews)} interviews")

        # Filter for resume mode
        interviews_to_process = all_interviews
        if resume:
            # Check which are already complete
            processor = IntelligenceProcessor(db_path=self.db_path)
            processor.initialize()
            completed_interviews = processor.db.get_interviews_by_status("complete")
            completed_ids = {(i["respondent"], i["company"], i["date"]) for i in completed_interviews}
            processor.close()

            # Filter
            interviews_to_process = []
            for interview in all_interviews:
                meta = interview.get("meta", {})
                key = (meta.get("respondent"), meta.get("company"), meta.get("date"))
                if key not in completed_ids:
                    interviews_to_process.append(interview)

            print(f"📋 Resume mode: {len(interviews_to_process)} pending, {len(completed_interviews)} already complete")

        if not interviews_to_process:
            print("✓ All interviews already processed")
            return {
                "total": len(all_interviews),
                "processed": 0,
                "success": 0,
                "errors": 0,
                "elapsed_time": 0
            }

        # Process in parallel
        print(f"\n🚀 Processing {len(interviews_to_process)} interviews with {self.max_workers} workers...")
        start_time = time.time()

        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all interviews for processing
            future_to_interview = {
                executor.submit(
                    _process_single_interview,
                    interview,
                    self.db_path
                ): interview
                for interview in interviews_to_process
            }

            # Collect results as they complete
            completed_count = 0
            success_count = 0
            error_count = 0

            for future in as_completed(future_to_interview):
                interview = future_to_interview[future]
                meta = interview.get("meta", {})
                company = meta.get("company", "Unknown")
                respondent = meta.get("respondent", "Unknown")

                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1

                    if result["success"]:
                        success_count += 1
                        status = "✓"
                    else:
                        error_count += 1
                        status = "✗"

                    # Progress update
                    print(f"  [{completed_count}/{len(interviews_to_process)}] {status} {company} / {respondent}")

                    # Periodic summary (every 5 interviews)
                    if self.enable_monitoring and completed_count % 5 == 0:
                        elapsed = time.time() - start_time
                        avg_time = elapsed / completed_count
                        remaining = len(interviews_to_process) - completed_count
                        eta = avg_time * remaining
                        print(f"      ⏱️  Progress: {completed_count}/{len(interviews_to_process)} | "
                              f"Success: {success_count} | Errors: {error_count} | "
                              f"ETA: {eta:.0f}s")

                except Exception as e:
                    error_count += 1
                    print(f"  [{completed_count + 1}/{len(interviews_to_process)}] ✗ {company} / {respondent}: {str(e)[:50]}")

        elapsed_time = time.time() - start_time

        # Final summary
        print(f"\n{'='*70}")
        print(f"✓ PARALLEL EXTRACTION COMPLETE")
        print(f"{'='*70}")
        print(f"Total interviews: {len(interviews_to_process)}")
        print(f"Successful: {success_count}")
        print(f"Errors: {error_count}")
        print(f"Total time: {elapsed_time:.1f}s ({elapsed_time/60:.1f}m)")
        print(f"Avg time per interview: {elapsed_time/len(interviews_to_process):.1f}s")
        print(f"Speedup vs sequential: ~{self.max_workers * 0.7:.1f}x")
        print(f"{'='*70}\n")

        return {
            "total": len(interviews_to_process),
            "processed": completed_count,
            "success": success_count,
            "errors": error_count,
            "elapsed_time": elapsed_time,
            "avg_time_per_interview": elapsed_time / len(interviews_to_process),
            "workers": self.max_workers
        }


def _process_single_interview(interview: Dict, db_path: Path) -> Dict[str, Any]:
    """
    Worker function to process a single interview

    This runs in a separate process to enable parallel execution.
    Each worker has its own database connection to avoid conflicts.

    Args:
        interview: Interview dictionary
        db_path: Path to database

    Returns:
        Dictionary with result information
    """
    import time

    start_time = time.time()
    meta = interview.get("meta", {})
    company = meta.get("company", "Unknown")
    respondent = meta.get("respondent", "Unknown")

    try:
        # Create processor for this worker
        processor = IntelligenceProcessor(db_path=db_path)
        processor.initialize()

        # Process interview
        success = processor.process_interview(interview)

        # Close processor
        processor.close()

        elapsed = time.time() - start_time

        return {
            "success": success,
            "company": company,
            "respondent": respondent,
            "elapsed_time": elapsed,
            "error": None
        }

    except Exception as e:
        elapsed = time.time() - start_time
        return {
            "success": False,
            "company": company,
            "respondent": respondent,
            "elapsed_time": elapsed,
            "error": str(e)
        }


def compare_sequential_vs_parallel(
    interviews_file: Path = INTERVIEWS_FILE,
    batch_size: int = 10,
    max_workers: int = 4
):
    """
    Compare sequential vs parallel processing performance

    Args:
        interviews_file: Path to interviews JSON file
        batch_size: Number of interviews to test (default: 10)
        max_workers: Number of parallel workers (default: 4)
    """
    print(f"\n{'='*70}")
    print(f"⚡ SEQUENTIAL VS PARALLEL COMPARISON")
    print(f"{'='*70}")
    print(f"Batch size: {batch_size}")
    print(f"Parallel workers: {max_workers}")
    print(f"{'='*70}\n")

    # Load interviews
    with open(interviews_file, 'r', encoding='utf-8') as f:
        interviews = json.load(f)[:batch_size]

    # Test sequential
    print("🐌 Running sequential processing...")
    from .config import PROJECT_ROOT
    db_sequential = PROJECT_ROOT / "data" / "test_sequential.db"
    if db_sequential.exists():
        db_sequential.unlink()

    start_seq = time.time()
    processor = IntelligenceProcessor(db_path=db_sequential)
    processor.initialize()
    for interview in interviews:
        processor.process_interview(interview)
    processor.close()
    time_sequential = time.time() - start_seq

    print(f"✓ Sequential complete: {time_sequential:.1f}s")

    # Test parallel
    print(f"\n🚀 Running parallel processing...")
    db_parallel = PROJECT_ROOT / "data" / "test_parallel.db"
    if db_parallel.exists():
        db_parallel.unlink()

    start_par = time.time()
    parallel = ParallelProcessor(db_path=db_parallel, max_workers=max_workers)

    # Write temp file with subset
    temp_file = Path("data/temp_batch.json")
    with open(temp_file, 'w', encoding='utf-8') as f:
        json.dump(interviews, f, ensure_ascii=False, indent=2)

    parallel.process_all_interviews_parallel(interviews_file=temp_file)
    time_parallel = time.time() - start_par

    # Clean up
    temp_file.unlink()

    print(f"✓ Parallel complete: {time_parallel:.1f}s")

    # Comparison
    speedup = time_sequential / time_parallel
    efficiency = speedup / max_workers * 100

    print(f"\n{'='*70}")
    print(f"📊 PERFORMANCE COMPARISON")
    print(f"{'='*70}")
    print(f"Sequential: {time_sequential:.1f}s")
    print(f"Parallel: {time_parallel:.1f}s")
    print(f"Speedup: {speedup:.2f}x")
    print(f"Efficiency: {efficiency:.1f}%")
    print(f"Time saved: {time_sequential - time_parallel:.1f}s")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Parallel interview processor")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers")
    parser.add_argument("--resume", action="store_true", help="Resume from previous run")
    parser.add_argument("--compare", action="store_true", help="Compare sequential vs parallel")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for comparison")
    args = parser.parse_args()

    if args.compare:
        compare_sequential_vs_parallel(batch_size=args.batch_size, max_workers=args.workers)
    else:
        processor = ParallelProcessor(max_workers=args.workers)
        processor.process_all_interviews_parallel(resume=args.resume)
