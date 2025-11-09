#!/usr/bin/env python3
"""
Consolidation Metrics Collection

Tracks and reports metrics for knowledge graph consolidation:
- Duplicates found by entity type
- Average similarity scores by entity type
- Contradictions detected by entity type
- Processing time by entity type
- API call metrics (total, cache hits/misses, failures)
- Quality metrics (duplicate reduction, confidence scores, contradiction rate)

Usage:
    from intelligence_capture.metrics import ConsolidationMetrics
    
    metrics = ConsolidationMetrics()
    metrics.track_duplicate_found("systems", 0.92)
    metrics.track_api_call(cache_hit=True)
    metrics.export_to_json("reports/metrics.json")
    metrics.display_summary()
"""
import json
import time
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime


# ANSI color codes
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


class ConsolidationMetrics:
    """
    Tracks consolidation metrics for monitoring and reporting
    
    Metrics Categories:
    - Duplicate detection: counts and similarity scores by entity type
    - Contradictions: counts by entity type
    - Processing time: time spent per entity type
    - API calls: total, cache hits/misses, failures
    - Quality: duplicate reduction, confidence scores, contradiction rate
    """
    
    def __init__(self):
        """Initialize metrics collection"""
        self.start_time = time.time()
        
        # Duplicate metrics by entity type
        self.duplicates_by_type: Dict[str, int] = {}
        self.similarity_scores_by_type: Dict[str, List[float]] = {}
        
        # Contradiction metrics by entity type
        self.contradictions_by_type: Dict[str, int] = {}
        
        # Processing time by entity type
        self.processing_time_by_type: Dict[str, float] = {}
        
        # API metrics
        self.api_metrics = {
            "total_calls": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "failed_calls": 0
        }
        
        # Quality metrics
        self.quality_metrics = {
            "entities_before": 0,
            "entities_after": 0,
            "duplicate_reduction_percentage": 0.0,
            "avg_confidence_score": 0.0,
            "contradiction_rate": 0.0
        }
        
        # Entity counts
        self.entity_counts = {
            "processed": 0,
            "merged": 0,
            "created": 0
        }
    
    def track_duplicate_found(self, entity_type: str, similarity_score: float):
        """
        Track a duplicate entity found
        
        Args:
            entity_type: Type of entity (systems, pain_points, etc.)
            similarity_score: Similarity score (0.0-1.0)
        """
        # Increment duplicate count
        if entity_type not in self.duplicates_by_type:
            self.duplicates_by_type[entity_type] = 0
        self.duplicates_by_type[entity_type] += 1
        
        # Track similarity score
        if entity_type not in self.similarity_scores_by_type:
            self.similarity_scores_by_type[entity_type] = []
        self.similarity_scores_by_type[entity_type].append(similarity_score)
    
    def track_contradiction(self, entity_type: str):
        """
        Track a contradiction detected
        
        Args:
            entity_type: Type of entity
        """
        if entity_type not in self.contradictions_by_type:
            self.contradictions_by_type[entity_type] = 0
        self.contradictions_by_type[entity_type] += 1
    
    def track_processing_time(self, entity_type: str, duration: float):
        """
        Track processing time for entity type
        
        Args:
            entity_type: Type of entity
            duration: Processing time in seconds
        """
        if entity_type not in self.processing_time_by_type:
            self.processing_time_by_type[entity_type] = 0.0
        self.processing_time_by_type[entity_type] += duration
    
    def track_api_call(
        self,
        cache_hit: bool = False,
        failed: bool = False
    ):
        """
        Track an API call
        
        Args:
            cache_hit: Whether this was a cache hit
            failed: Whether the call failed
        """
        self.api_metrics["total_calls"] += 1
        
        if cache_hit:
            self.api_metrics["cache_hits"] += 1
        else:
            self.api_metrics["cache_misses"] += 1
        
        if failed:
            self.api_metrics["failed_calls"] += 1
    
    def track_entity_processed(self):
        """Track an entity processed"""
        self.entity_counts["processed"] += 1
    
    def track_entity_merged(self):
        """Track an entity merged"""
        self.entity_counts["merged"] += 1
    
    def track_entity_created(self):
        """Track a new entity created"""
        self.entity_counts["created"] += 1
    
    def set_quality_metrics(
        self,
        entities_before: int,
        entities_after: int,
        avg_confidence: float,
        contradiction_rate: float
    ):
        """
        Set quality metrics
        
        Args:
            entities_before: Total entities before consolidation
            entities_after: Total entities after consolidation
            avg_confidence: Average consensus confidence score
            contradiction_rate: Percentage of entities with contradictions
        """
        self.quality_metrics["entities_before"] = entities_before
        self.quality_metrics["entities_after"] = entities_after
        
        if entities_before > 0:
            reduction = ((entities_before - entities_after) / entities_before) * 100
            self.quality_metrics["duplicate_reduction_percentage"] = round(reduction, 2)
        
        self.quality_metrics["avg_confidence_score"] = round(avg_confidence, 3)
        self.quality_metrics["contradiction_rate"] = round(contradiction_rate, 2)
    
    def get_avg_similarity_by_type(self) -> Dict[str, float]:
        """
        Calculate average similarity score by entity type
        
        Returns:
            Dict of entity_type -> average similarity score
        """
        avg_similarity = {}
        
        for entity_type, scores in self.similarity_scores_by_type.items():
            if scores:
                avg_similarity[entity_type] = round(sum(scores) / len(scores), 3)
            else:
                avg_similarity[entity_type] = 0.0
        
        return avg_similarity
    
    def get_cache_hit_rate(self) -> float:
        """
        Calculate cache hit rate
        
        Returns:
            Cache hit rate as percentage (0.0-100.0)
        """
        total = self.api_metrics["total_calls"]
        if total == 0:
            return 0.0
        
        hits = self.api_metrics["cache_hits"]
        return round((hits / total) * 100, 1)
    
    def get_total_processing_time(self) -> float:
        """
        Get total processing time across all entity types
        
        Returns:
            Total time in seconds
        """
        return sum(self.processing_time_by_type.values())
    
    def get_elapsed_time(self) -> float:
        """
        Get elapsed time since metrics collection started
        
        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time
    
    def to_dict(self) -> Dict:
        """
        Export metrics as dictionary
        
        Returns:
            Dict with all metrics
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "elapsed_time_seconds": round(self.get_elapsed_time(), 2),
            "duplicates_by_type": self.duplicates_by_type,
            "avg_similarity_by_type": self.get_avg_similarity_by_type(),
            "contradictions_by_type": self.contradictions_by_type,
            "processing_time_by_type": {
                k: round(v, 3) for k, v in self.processing_time_by_type.items()
            },
            "total_processing_time": round(self.get_total_processing_time(), 2),
            "api_metrics": {
                **self.api_metrics,
                "cache_hit_rate_percentage": self.get_cache_hit_rate()
            },
            "quality_metrics": self.quality_metrics,
            "entity_counts": self.entity_counts
        }
    
    def export_to_json(self, path: Path):
        """
        Export metrics to JSON file
        
        Args:
            path: Path to output file
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    def display_summary(self):
        """
        Display color-coded summary to console
        """
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}CONSOLIDATION METRICS SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")
        
        # Timing
        elapsed = self.get_elapsed_time()
        processing = self.get_total_processing_time()
        
        print(f"{Colors.BOLD}⏱️  Timing:{Colors.END}")
        print(f"  Elapsed time: {elapsed:.2f}s")
        print(f"  Processing time: {processing:.2f}s")
        
        # Entity counts
        print(f"\n{Colors.BOLD}📊 Entity Counts:{Colors.END}")
        print(f"  Processed: {self.entity_counts['processed']}")
        print(f"  Merged: {self.entity_counts['merged']}")
        print(f"  Created: {self.entity_counts['created']}")
        
        # Duplicates by type
        if self.duplicates_by_type:
            print(f"\n{Colors.BOLD}🔍 Duplicates Found:{Colors.END}")
            total_duplicates = sum(self.duplicates_by_type.values())
            print(f"  Total: {total_duplicates}")
            
            for entity_type, count in sorted(self.duplicates_by_type.items()):
                avg_sim = self.get_avg_similarity_by_type().get(entity_type, 0.0)
                print(f"  {entity_type}: {count} (avg similarity: {avg_sim:.3f})")
        
        # Contradictions
        if self.contradictions_by_type:
            print(f"\n{Colors.BOLD}⚠️  Contradictions:{Colors.END}")
            total_contradictions = sum(self.contradictions_by_type.values())
            print(f"  Total: {total_contradictions}")
            
            for entity_type, count in sorted(self.contradictions_by_type.items()):
                print(f"  {entity_type}: {count}")
        
        # API metrics
        print(f"\n{Colors.BOLD}🌐 API Metrics:{Colors.END}")
        print(f"  Total calls: {self.api_metrics['total_calls']}")
        print(f"  Cache hits: {self.api_metrics['cache_hits']}")
        print(f"  Cache misses: {self.api_metrics['cache_misses']}")
        
        cache_hit_rate = self.get_cache_hit_rate()
        if cache_hit_rate >= 95:
            color = Colors.GREEN
        elif cache_hit_rate >= 80:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        print(f"  Cache hit rate: {color}{cache_hit_rate:.1f}%{Colors.END}")
        
        if self.api_metrics['failed_calls'] > 0:
            print(f"  {Colors.RED}Failed calls: {self.api_metrics['failed_calls']}{Colors.END}")
        
        # Quality metrics
        print(f"\n{Colors.BOLD}✨ Quality Metrics:{Colors.END}")
        
        reduction = self.quality_metrics["duplicate_reduction_percentage"]
        if reduction >= 70:
            color = Colors.GREEN
        elif reduction >= 50:
            color = Colors.YELLOW
        else:
            color = Colors.RED if reduction > 0 else Colors.END
        
        print(f"  Duplicate reduction: {color}{reduction:.1f}%{Colors.END}")
        
        confidence = self.quality_metrics["avg_confidence_score"]
        if confidence >= 0.75:
            color = Colors.GREEN
        elif confidence >= 0.60:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        print(f"  Avg confidence: {color}{confidence:.3f}{Colors.END}")
        
        contradiction_rate = self.quality_metrics["contradiction_rate"]
        if contradiction_rate <= 10:
            color = Colors.GREEN
        elif contradiction_rate <= 20:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        print(f"  Contradiction rate: {color}{contradiction_rate:.1f}%{Colors.END}")
        
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 70}{Colors.END}\n")
