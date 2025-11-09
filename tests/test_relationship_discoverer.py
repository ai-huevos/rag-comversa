#!/usr/bin/env python3
"""
Unit Tests for RelationshipDiscoverer Component

Tests:
- System → Pain Point relationship discovery
- Process → System relationship discovery
- KPI → Process relationship discovery
- Automation → Pain Point relationship discovery
- Relationship strength calculation
- Duplicate relationship prevention
"""
import pytest
from unittest.mock import Mock, MagicMock
from intelligence_capture.relationship_discoverer import RelationshipDiscoverer


class TestRelationshipDiscoverer:
    """Test suite for RelationshipDiscoverer"""
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.conn = Mock()
        return db
    
    @pytest.fixture
    def discoverer(self, mock_db):
        """Create discoverer instance"""
        return RelationshipDiscoverer(mock_db)
    
    # Test 1: System → Pain Point Relationships
    
    def test_system_pain_explicit_mention(self, discoverer):
        """Test System → Pain Point with explicit mention"""
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        pain_points = [
            {
                "id": 10,
                "description": "Excel crashes frequently causing data loss"
            }
        ]
        
        relationships = discoverer._find_system_pain_relationships(
            systems, pain_points, interview_id=1
        )
        
        assert len(relationships) == 1
        assert relationships[0]["source_entity_id"] == 1
        assert relationships[0]["target_entity_id"] == 10
        assert relationships[0]["relationship_type"] == "causes"
        assert relationships[0]["strength"] == 0.8  # Explicit mention
    
    def test_system_pain_no_mention(self, discoverer):
        """Test System → Pain Point with no mention"""
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        pain_points = [
            {
                "id": 10,
                "description": "Communication delays between teams"
            }
        ]
        
        relationships = discoverer._find_system_pain_relationships(
            systems, pain_points, interview_id=1
        )
        
        assert len(relationships) == 0
    
    def test_system_pain_case_insensitive(self, discoverer):
        """Test System → Pain Point is case-insensitive"""
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        pain_points = [
            {
                "id": 10,
                "description": "EXCEL crashes frequently"
            }
        ]
        
        relationships = discoverer._find_system_pain_relationships(
            systems, pain_points, interview_id=1
        )
        
        assert len(relationships) == 1
    
    # Test 2: Process → System Relationships
    
    def test_process_system_explicit_field(self, discoverer):
        """Test Process → System with explicit systems field"""
        processes = [
            {
                "id": 5,
                "name": "Monthly Reporting",
                "description": "Generate monthly reports",
                "systems": ["Excel", "SAP"]
            }
        ]
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        
        relationships = discoverer._find_process_system_relationships(
            processes, systems, interview_id=1
        )
        
        assert len(relationships) == 1
        assert relationships[0]["source_entity_id"] == 5
        assert relationships[0]["target_entity_id"] == 1
        assert relationships[0]["relationship_type"] == "uses"
        assert relationships[0]["strength"] == 0.9  # Explicit field
    
    def test_process_system_implicit_mention(self, discoverer):
        """Test Process → System with implicit mention in description"""
        processes = [
            {
                "id": 5,
                "name": "Monthly Reporting",
                "description": "Generate monthly reports using Excel",
                "systems": []
            }
        ]
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        
        relationships = discoverer._find_process_system_relationships(
            processes, systems, interview_id=1
        )
        
        assert len(relationships) == 1
        assert relationships[0]["strength"] == 0.7  # Implicit mention
    
    def test_process_system_json_string_systems(self, discoverer):
        """Test Process → System with systems as JSON string"""
        import json
        
        processes = [
            {
                "id": 5,
                "name": "Monthly Reporting",
                "description": "Generate reports",
                "systems": json.dumps(["Excel", "SAP"])
            }
        ]
        systems = [
            {"id": 1, "name": "Excel"}
        ]
        
        relationships = discoverer._find_process_system_relationships(
            processes, systems, interview_id=1
        )
        
        assert len(relationships) == 1
    
    # Test 3: KPI → Process Relationships
    
    def test_kpi_process_explicit_field(self, discoverer):
        """Test KPI → Process with explicit related_processes field"""
        kpis = [
            {
                "id": 20,
                "name": "Report Completion Rate",
                "related_processes": ["Monthly Reporting", "Quarterly Review"]
            }
        ]
        processes = [
            {"id": 5, "name": "Monthly Reporting"}
        ]
        
        relationships = discoverer._find_kpi_process_relationships(
            kpis, processes, interview_id=1
        )
        
        assert len(relationships) == 1
        assert relationships[0]["source_entity_id"] == 20
        assert relationships[0]["target_entity_id"] == 5
        assert relationships[0]["relationship_type"] == "measures"
        assert relationships[0]["strength"] == 0.9
    
    def test_kpi_process_json_string(self, discoverer):
        """Test KPI → Process with related_processes as JSON string"""
        import json
        
        kpis = [
            {
                "id": 20,
                "name": "Report Completion Rate",
                "related_processes": json.dumps(["Monthly Reporting"])
            }
        ]
        processes = [
            {"id": 5, "name": "Monthly Reporting"}
        ]
        
        relationships = discoverer._find_kpi_process_relationships(
            kpis, processes, interview_id=1
        )
        
        assert len(relationships) == 1
    
    # Test 4: Automation → Pain Point Relationships
    
    def test_automation_pain_process_match(self, discoverer):
        """Test Automation → Pain Point with matching process"""
        import json
        
        automations = [
            {
                "id": 30,
                "name": "Auto-generate reports",
                "process": "Monthly Reporting"
            }
        ]
        pain_points = [
            {
                "id": 10,
                "description": "Manual reporting takes too long",
                "affected_processes": json.dumps(["Monthly Reporting"])
            }
        ]
        
        relationships = discoverer._find_automation_pain_relationships(
            automations, pain_points, interview_id=1
        )
        
        assert len(relationships) == 1
        assert relationships[0]["source_entity_id"] == 30
        assert relationships[0]["target_entity_id"] == 10
        assert relationships[0]["relationship_type"] == "addresses"
        assert relationships[0]["strength"] == 0.8
    
    # Test 5: Full Discovery Integration
    
    def test_discover_relationships_all_types(self, discoverer):
        """Test full relationship discovery with all entity types"""
        import json
        
        entities = {
            "systems": [
                {"id": 1, "name": "Excel"}
            ],
            "pain_points": [
                {
                    "id": 10,
                    "description": "Excel crashes frequently",
                    "affected_processes": json.dumps(["Monthly Reporting"])
                }
            ],
            "processes": [
                {
                    "id": 5,
                    "name": "Monthly Reporting",
                    "description": "Generate reports",
                    "systems": ["Excel"]
                }
            ],
            "kpis": [
                {
                    "id": 20,
                    "name": "Report Completion Rate",
                    "related_processes": ["Monthly Reporting"]
                }
            ],
            "automation_candidates": [
                {
                    "id": 30,
                    "name": "Auto-generate reports",
                    "process": "Monthly Reporting"
                }
            ]
        }
        
        relationships = discoverer.discover_relationships(entities, interview_id=1)
        
        # Should find:
        # 1. System → Pain Point (Excel causes crash)
        # 2. Process → System (Monthly Reporting uses Excel)
        # 3. KPI → Process (Report Completion Rate measures Monthly Reporting)
        # 4. Automation → Pain Point (Auto-generate addresses manual reporting pain)
        assert len(relationships) >= 4
        
        # Check statistics
        stats = discoverer.get_statistics()
        assert stats["relationships_discovered"] >= 4
        assert stats["system_pain_relationships"] >= 1
        assert stats["process_system_relationships"] >= 1
        assert stats["kpi_process_relationships"] >= 1
        assert stats["automation_pain_relationships"] >= 1
    
    def test_discover_relationships_empty_entities(self, discoverer):
        """Test relationship discovery with empty entities"""
        entities = {
            "systems": [],
            "pain_points": [],
            "processes": []
        }
        
        relationships = discoverer.discover_relationships(entities, interview_id=1)
        
        assert len(relationships) == 0
    
    # Test 6: Relationship Creation
    
    def test_create_relationship_structure(self, discoverer):
        """Test relationship dict structure"""
        relationship = discoverer._create_relationship(
            source_entity={"id": 1, "name": "Excel"},
            source_type="systems",
            target_entity={"id": 10, "description": "Crash"},
            target_type="pain_points",
            relationship_type="causes",
            strength=0.8,
            interview_id=1
        )
        
        assert relationship["source_entity_id"] == 1
        assert relationship["source_entity_type"] == "systems"
        assert relationship["target_entity_id"] == 10
        assert relationship["target_entity_type"] == "pain_points"
        assert relationship["relationship_type"] == "causes"
        assert relationship["strength"] == 0.8
        assert "mentioned_in_interviews" in relationship
