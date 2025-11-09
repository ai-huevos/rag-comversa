#!/usr/bin/env python3
"""
Relationship Discoverer - Discovers relationships between entities

Identifies connections between entities based on:
1. Co-occurrence in same interview
2. Name mentions in descriptions
3. Semantic relationships

Relationship types:
- System → causes → Pain Point
- Process → uses → System
- KPI → measures → Process
- Automation → addresses → Pain Point
"""
import json
from typing import Dict, List, Optional
from intelligence_capture.logger import get_logger

# Initialize logger
logger = get_logger(__name__)


class RelationshipDiscoverer:
    """
    Discovers relationships between entities within interviews
    
    Features:
    - System-Pain Point causality detection
    - Process-System usage detection
    - Relationship strength scoring
    - Duplicate relationship prevention
    """
    
    def __init__(self, db):
        """
        Initialize relationship discoverer
        
        Args:
            db: Database instance (IntelligenceDB or EnhancedIntelligenceDB)
        """
        self.db = db
        self.stats = {
            "relationships_discovered": 0,
            "system_pain_relationships": 0,
            "process_system_relationships": 0,
            "kpi_process_relationships": 0,
            "automation_pain_relationships": 0
        }
    
    def discover_relationships(
        self,
        entities: Dict[str, List[Dict]],
        interview_id: int
    ) -> List[Dict]:
        """
        Discover relationships between entities in same interview
        
        Args:
            entities: Dict of entity_type -> list of entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        
        # System → Pain Point relationships
        system_pain_rels = self._find_system_pain_relationships(
            entities.get("systems", []),
            entities.get("pain_points", []),
            interview_id
        )
        relationships.extend(system_pain_rels)
        self.stats["system_pain_relationships"] += len(system_pain_rels)
        
        # Process → System relationships
        process_system_rels = self._find_process_system_relationships(
            entities.get("processes", []),
            entities.get("systems", []),
            interview_id
        )
        relationships.extend(process_system_rels)
        self.stats["process_system_relationships"] += len(process_system_rels)
        
        # KPI → Process relationships
        kpi_process_rels = self._find_kpi_process_relationships(
            entities.get("kpis", []),
            entities.get("processes", []),
            interview_id
        )
        relationships.extend(kpi_process_rels)
        self.stats["kpi_process_relationships"] += len(kpi_process_rels)
        
        # Automation → Pain Point relationships
        automation_pain_rels = self._find_automation_pain_relationships(
            entities.get("automation_candidates", []),
            entities.get("pain_points", []),
            interview_id
        )
        relationships.extend(automation_pain_rels)
        self.stats["automation_pain_relationships"] += len(automation_pain_rels)
        
        self.stats["relationships_discovered"] = len(relationships)
        
        if relationships:
            logger.info(f"Discovered {len(relationships)} relationships in interview {interview_id}")
        
        return relationships
    
    def _find_system_pain_relationships(
        self,
        systems: List[Dict],
        pain_points: List[Dict],
        interview_id: int
    ) -> List[Dict]:
        """
        Detect System → causes → Pain Point relationships
        
        Args:
            systems: List of system entities
            pain_points: List of pain point entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        
        for system in systems:
            system_name = system.get("name", "").lower()
            if not system_name:
                continue
            
            for pain_point in pain_points:
                # Check if pain point mentions system
                description = pain_point.get("description", "").lower()
                
                # Check for explicit mention
                if system_name in description:
                    strength = 0.8  # Explicit mention = high confidence
                    
                    relationship = self._create_relationship(
                        source_entity=system,
                        source_type="systems",
                        target_entity=pain_point,
                        target_type="pain_points",
                        relationship_type="causes",
                        strength=strength,
                        interview_id=interview_id
                    )
                    
                    relationships.append(relationship)
                    logger.debug(f"System-Pain relationship: '{system_name}' causes pain point")
        
        return relationships
    
    def _find_process_system_relationships(
        self,
        processes: List[Dict],
        systems: List[Dict],
        interview_id: int
    ) -> List[Dict]:
        """
        Detect Process → uses → System relationships
        
        Args:
            processes: List of process entities
            systems: List of system entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        
        for process in processes:
            process_name = process.get("name", "")
            process_description = process.get("description", "").lower()
            
            # Check systems field (JSON array)
            process_systems = process.get("systems", [])
            if isinstance(process_systems, str):
                try:
                    process_systems = json.loads(process_systems)
                except:
                    process_systems = []
            
            for system in systems:
                system_name = system.get("name", "").lower()
                if not system_name:
                    continue
                
                # Check if system is explicitly listed in process.systems
                if any(system_name in ps.lower() for ps in process_systems):
                    strength = 0.9  # Explicit field = very high confidence
                    
                    relationship = self._create_relationship(
                        source_entity=process,
                        source_type="processes",
                        target_entity=system,
                        target_type="systems",
                        relationship_type="uses",
                        strength=strength,
                        interview_id=interview_id
                    )
                    
                    relationships.append(relationship)
                    logger.debug(f"Process-System relationship: '{process_name}' uses '{system_name}'")
                
                # Check if system is mentioned in process description
                elif system_name in process_description:
                    strength = 0.7  # Implicit mention = medium confidence
                    
                    relationship = self._create_relationship(
                        source_entity=process,
                        source_type="processes",
                        target_entity=system,
                        target_type="systems",
                        relationship_type="uses",
                        strength=strength,
                        interview_id=interview_id
                    )
                    
                    relationships.append(relationship)
                    logger.debug(f"Process-System relationship (implicit): '{process_name}' uses '{system_name}'")
        
        return relationships
    
    def _find_kpi_process_relationships(
        self,
        kpis: List[Dict],
        processes: List[Dict],
        interview_id: int
    ) -> List[Dict]:
        """
        Detect KPI → measures → Process relationships
        
        Args:
            kpis: List of KPI entities
            processes: List of process entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        
        for kpi in kpis:
            kpi_name = kpi.get("name", "")
            
            # Check related_processes field (JSON array)
            related_processes = kpi.get("related_processes", [])
            if isinstance(related_processes, str):
                try:
                    related_processes = json.loads(related_processes)
                except:
                    related_processes = []
            
            for process in processes:
                process_name = process.get("name", "").lower()
                if not process_name:
                    continue
                
                # Check if process is explicitly listed in kpi.related_processes
                if any(process_name in rp.lower() for rp in related_processes):
                    strength = 0.9  # Explicit field = very high confidence
                    
                    relationship = self._create_relationship(
                        source_entity=kpi,
                        source_type="kpis",
                        target_entity=process,
                        target_type="processes",
                        relationship_type="measures",
                        strength=strength,
                        interview_id=interview_id
                    )
                    
                    relationships.append(relationship)
                    logger.debug(f"KPI-Process relationship: '{kpi_name}' measures '{process_name}'")
        
        return relationships
    
    def _find_automation_pain_relationships(
        self,
        automations: List[Dict],
        pain_points: List[Dict],
        interview_id: int
    ) -> List[Dict]:
        """
        Detect Automation → addresses → Pain Point relationships
        
        Args:
            automations: List of automation candidate entities
            pain_points: List of pain point entities
            interview_id: Source interview ID
            
        Returns:
            List of relationship dicts
        """
        relationships = []
        
        for automation in automations:
            automation_name = automation.get("name", "")
            automation_process = automation.get("process", "").lower()
            
            for pain_point in pain_points:
                pain_description = pain_point.get("description", "").lower()
                affected_processes = pain_point.get("affected_processes", [])
                
                if isinstance(affected_processes, str):
                    try:
                        affected_processes = json.loads(affected_processes)
                    except:
                        affected_processes = []
                
                # Check if automation process matches pain point's affected processes
                if any(automation_process in ap.lower() for ap in affected_processes):
                    strength = 0.8  # Process match = high confidence
                    
                    relationship = self._create_relationship(
                        source_entity=automation,
                        source_type="automation_candidates",
                        target_entity=pain_point,
                        target_type="pain_points",
                        relationship_type="addresses",
                        strength=strength,
                        interview_id=interview_id
                    )
                    
                    relationships.append(relationship)
                    logger.debug(f"Automation-Pain relationship: '{automation_name}' addresses pain point")
        
        return relationships
    
    def _create_relationship(
        self,
        source_entity: Dict,
        source_type: str,
        target_entity: Dict,
        target_type: str,
        relationship_type: str,
        strength: float,
        interview_id: int
    ) -> Dict:
        """
        Create relationship dict
        
        Args:
            source_entity: Source entity
            source_type: Source entity type
            target_entity: Target entity
            target_type: Target entity type
            relationship_type: Type of relationship (causes, uses, measures, addresses)
            strength: Relationship strength (0.0-1.0)
            interview_id: Source interview ID
            
        Returns:
            Relationship dict
        """
        return {
            "source_entity_id": source_entity.get("id"),
            "source_entity_type": source_type,
            "relationship_type": relationship_type,
            "target_entity_id": target_entity.get("id"),
            "target_entity_type": target_type,
            "strength": strength,
            "mentioned_in_interviews": json.dumps([interview_id], ensure_ascii=False)
        }
    
    def get_statistics(self) -> Dict:
        """
        Get relationship discovery statistics
        
        Returns:
            Dict with relationship metrics
        """
        return self.stats.copy()
