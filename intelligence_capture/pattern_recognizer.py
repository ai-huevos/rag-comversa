#!/usr/bin/env python3
"""
Pattern Recognizer - Identifies recurring patterns across interviews

Detects:
1. Recurring pain points (mentioned by 3+ people)
2. Problematic systems (negative sentiment in 5+ interviews)
3. High-priority patterns (mentioned in 30%+ of interviews)

Patterns are stored in the patterns table for analysis and reporting.
"""
import json
from typing import Dict, List, Optional
from intelligence_capture.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class PatternRecognizer:
    """
    Identifies recurring patterns across all interviews
    
    Features:
    - Recurring pain point detection
    - Problematic system identification
    - Pattern frequency calculation
    - High-priority pattern flagging
    """
    
    def __init__(self, db, config: Dict):
        """
        Initialize pattern recognizer
        
        Args:
            db: Database instance (IntelligenceDB or EnhancedIntelligenceDB)
            config: Configuration dict with pattern recognition settings
        """
        self.db = db
        self.config = config
        
        # Get thresholds from config
        pattern_config = config.get("consolidation", {}).get("pattern_recognition", {})
        self.recurring_pain_threshold = pattern_config.get("recurring_pain_threshold", 3)
        self.problematic_system_threshold = pattern_config.get("problematic_system_threshold", 5)
        self.high_priority_frequency = pattern_config.get("high_priority_frequency", 0.30)
        
        self.stats = {
            "patterns_identified": 0,
            "recurring_pain_points": 0,
            "problematic_systems": 0,
            "high_priority_patterns": 0
        }
    
    def identify_patterns(self) -> List[Dict]:
        """
        Identify recurring patterns across all interviews
        
        Returns:
            List of pattern dicts with frequency and priority
        """
        patterns = []
        
        # Get total interview count for frequency calculation
        total_interviews = self._get_total_interviews()
        
        if total_interviews == 0:
            logger.warning("No interviews found, cannot identify patterns")
            return patterns
        
        # Find recurring pain points
        recurring_pains = self.find_recurring_pain_points(self.recurring_pain_threshold)
        for pain in recurring_pains:
            pattern = self._create_pattern(
                pattern_type="recurring_pain",
                entity_type="pain_points",
                entity_id=pain["id"],
                source_count=pain["source_count"],
                total_interviews=total_interviews,
                description=f"Recurring pain point: {pain['description'][:100]}"
            )
            patterns.append(pattern)
        
        self.stats["recurring_pain_points"] = len(recurring_pains)
        
        # Find problematic systems
        problematic_systems = self.find_problematic_systems(self.problematic_system_threshold)
        for system in problematic_systems:
            pattern = self._create_pattern(
                pattern_type="problematic_system",
                entity_type="systems",
                entity_id=system["id"],
                source_count=system["source_count"],
                total_interviews=total_interviews,
                description=f"Problematic system: {system['name']}"
            )
            patterns.append(pattern)
        
        self.stats["problematic_systems"] = len(problematic_systems)
        
        # Count high-priority patterns
        high_priority = sum(1 for p in patterns if p["high_priority"])
        self.stats["high_priority_patterns"] = high_priority
        self.stats["patterns_identified"] = len(patterns)
        
        # Store patterns in database
        for pattern in patterns:
            self._store_pattern(pattern)
        
        if patterns:
            logger.info(f"Identified {len(patterns)} patterns ({high_priority} high-priority)")
        
        return patterns
    
    def find_recurring_pain_points(self, threshold: int = 3) -> List[Dict]:
        """
        Find pain points mentioned by threshold+ people
        
        Args:
            threshold: Minimum number of mentions
            
        Returns:
            List of recurring pain points
        """
        cursor = self.db.conn.cursor()
        
        try:
            cursor.execute("""
                SELECT id, description, source_count, consensus_confidence
                FROM pain_points
                WHERE source_count >= ?
                  AND is_consolidated = 1
                ORDER BY source_count DESC
            """, (threshold,))
            
            rows = cursor.fetchall()
            
            pain_points = []
            for row in rows:
                pain_points.append({
                    "id": row[0],
                    "description": row[1],
                    "source_count": row[2],
                    "consensus_confidence": row[3]
                })
            
            return pain_points
            
        except Exception as e:
            logger.warning(f"Error finding recurring pain points: {e}")
            return []
    
    def find_problematic_systems(self, threshold: int = 5) -> List[Dict]:
        """
        Find systems with negative sentiment in threshold+ interviews
        
        This is a simplified version that looks for systems mentioned frequently
        in pain points. A more sophisticated version would analyze sentiment.
        
        Args:
            threshold: Minimum number of negative mentions
            
        Returns:
            List of problematic systems
        """
        cursor = self.db.conn.cursor()
        
        try:
            # Find systems that are mentioned in many pain points
            # This is a proxy for "problematic" systems
            cursor.execute("""
                SELECT s.id, s.name, s.usage_count as source_count
                FROM systems s
                WHERE s.usage_count >= ?
                  AND EXISTS (
                    SELECT 1 FROM pain_points pp
                    WHERE pp.description LIKE '%' || s.name || '%'
                  )
                ORDER BY s.usage_count DESC
            """, (threshold,))
            
            rows = cursor.fetchall()
            
            systems = []
            for row in rows:
                systems.append({
                    "id": row[0],
                    "name": row[1],
                    "source_count": row[2]
                })
            
            return systems
            
        except Exception as e:
            logger.warning(f"Error finding problematic systems: {e}")
            return []
    
    def _get_total_interviews(self) -> int:
        """
        Get total number of interviews in database
        
        Returns:
            Total interview count
        """
        cursor = self.db.conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*) FROM interviews")
            result = cursor.fetchone()
            return result[0] if result else 0
            
        except Exception as e:
            logger.warning(f"Error getting total interviews: {e}")
            return 0
    
    def _create_pattern(
        self,
        pattern_type: str,
        entity_type: str,
        entity_id: int,
        source_count: int,
        total_interviews: int,
        description: str
    ) -> Dict:
        """
        Create pattern dict
        
        Args:
            pattern_type: Type of pattern (recurring_pain, problematic_system)
            entity_type: Type of entity
            entity_id: Entity ID
            source_count: Number of sources mentioning this pattern
            total_interviews: Total number of interviews
            description: Pattern description
            
        Returns:
            Pattern dict
        """
        # Calculate pattern frequency
        pattern_frequency = source_count / total_interviews if total_interviews > 0 else 0.0
        
        # Determine if high priority
        high_priority = pattern_frequency >= self.high_priority_frequency
        
        return {
            "pattern_type": pattern_type,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "pattern_frequency": pattern_frequency,
            "source_count": source_count,
            "high_priority": high_priority,
            "description": description
        }
    
    def _store_pattern(self, pattern: Dict) -> bool:
        """
        Store pattern in database
        
        Args:
            pattern: Pattern dict
            
        Returns:
            True if successful, False otherwise
        """
        cursor = self.db.conn.cursor()
        
        try:
            # Check if pattern already exists
            cursor.execute("""
                SELECT id FROM patterns
                WHERE pattern_type = ?
                  AND entity_type = ?
                  AND entity_id = ?
            """, (
                pattern["pattern_type"],
                pattern["entity_type"],
                pattern["entity_id"]
            ))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update existing pattern
                cursor.execute("""
                    UPDATE patterns
                    SET pattern_frequency = ?,
                        source_count = ?,
                        high_priority = ?,
                        description = ?,
                        detected_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (
                    pattern["pattern_frequency"],
                    pattern["source_count"],
                    1 if pattern["high_priority"] else 0,
                    pattern["description"],
                    existing[0]
                ))
            else:
                # Insert new pattern
                cursor.execute("""
                    INSERT INTO patterns (
                        pattern_type,
                        entity_type,
                        entity_id,
                        pattern_frequency,
                        source_count,
                        high_priority,
                        description
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    pattern["pattern_type"],
                    pattern["entity_type"],
                    pattern["entity_id"],
                    pattern["pattern_frequency"],
                    pattern["source_count"],
                    1 if pattern["high_priority"] else 0,
                    pattern["description"]
                ))
            
            self.db.conn.commit()
            return True
            
        except Exception as e:
            logger.warning(f"Error storing pattern: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """
        Get pattern recognition statistics
        
        Returns:
            Dict with pattern metrics
        """
        return self.stats.copy()
