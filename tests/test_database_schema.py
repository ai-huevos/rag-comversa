"""
Unit tests for enhanced database schema (v2.0)
Tests backward compatibility, new tables, and organizational hierarchy
"""
import unittest
import sqlite3
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import IntelligenceDB, EnhancedIntelligenceDB


class TestDatabaseSchema(unittest.TestCase):
    """Test database schema creation and migration"""
    
    def setUp(self):
        """Create temporary database for testing"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_v1_schema_creation(self):
        """Test that v1.0 schema is created correctly"""
        self.db.init_schema()
        
        cursor = self.db.conn.cursor()
        
        # Check v1.0 tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = [
            'interviews', 'pain_points', 'processes', 'systems',
            'kpis', 'automation_candidates', 'inefficiencies'
        ]
        
        for table in expected_tables:
            self.assertIn(table, tables, f"Table {table} should exist")
    
    def test_v2_schema_creation(self):
        """Test that v2.0 schema is created correctly"""
        self.db.init_v2_schema()
        
        cursor = self.db.conn.cursor()
        
        # Check all v2.0 tables exist
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        v2_tables = [
            'communication_channels', 'decision_points', 'data_flows',
            'temporal_patterns', 'failure_modes', 'team_structures',
            'knowledge_gaps', 'success_patterns', 'budget_constraints',
            'external_dependencies'
        ]
        
        for table in v2_tables:
            self.assertIn(table, tables, f"v2.0 table {table} should exist")
    
    def test_v2_fields_added_to_interviews(self):
        """Test that v2.0 fields are added to interviews table"""
        self.db.init_v2_schema()
        
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA table_info(interviews)")
        columns = [row[1] for row in cursor.fetchall()]
        
        v2_fields = [
            'holding_name', 'business_unit', 'department',
            'interview_method', 'interview_duration_minutes',
            'discovered_org_structure', 'org_structure_validated',
            'org_structure_confidence', 'org_structure_deviations',
            'suggested_follow_up_questions'
        ]
        
        for field in v2_fields:
            self.assertIn(field, columns, f"Field {field} should be added to interviews")
    
    def test_v2_fields_added_to_pain_points(self):
        """Test that v2.0 fields are added to pain_points table"""
        self.db.init_v2_schema()
        
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA table_info(pain_points)")
        columns = [row[1] for row in cursor.fetchall()]
        
        v2_fields = [
            'holding_name', 'business_unit', 'department',
            'intensity_score', 'hair_on_fire',
            'time_wasted_per_occurrence_minutes', 'cost_impact_monthly_usd',
            'estimated_annual_cost_usd', 'jtbd_who', 'jtbd_what',
            'jtbd_where', 'jtbd_formatted', 'root_cause',
            'current_workaround', 'confidence_score', 'needs_review',
            'extraction_source', 'extraction_reasoning'
        ]
        
        for field in v2_fields:
            self.assertIn(field, columns, f"Field {field} should be added to pain_points")
    
    def test_v2_fields_added_to_automation_candidates(self):
        """Test that v2.0 fields are added to automation_candidates table"""
        self.db.init_v2_schema()
        
        cursor = self.db.conn.cursor()
        cursor.execute("PRAGMA table_info(automation_candidates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        v2_fields = [
            'holding_name', 'business_unit', 'department',
            'current_manual_process_description', 'data_sources_needed',
            'approval_required', 'approval_threshold_usd', 'monitoring_metrics',
            'effort_score', 'impact_score', 'priority_quadrant',
            'estimated_roi_months', 'estimated_annual_savings_usd',
            'ceo_priority', 'overlooked_opportunity', 'data_support_score',
            'confidence_score', 'needs_review', 'extraction_source'
        ]
        
        for field in v2_fields:
            self.assertIn(field, columns, f"Field {field} should be added to automation_candidates")
    
    def test_indexes_created(self):
        """Test that v2.0 indexes are created"""
        self.db.init_v2_schema()
        
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = [row[0] for row in cursor.fetchall()]
        
        expected_indexes = [
            'idx_interviews_company_bu',
            'idx_pain_points_company_bu',
            'idx_pain_points_needs_review',
            'idx_pain_points_hair_on_fire',
            'idx_automation_candidates_priority',
            'idx_communication_channels_company',
            'idx_decision_points_company',
            'idx_data_flows_company'
        ]
        
        for index in expected_indexes:
            self.assertIn(index, indexes, f"Index {index} should exist")
    
    def test_backward_compatibility(self):
        """Test that v1.0 data is preserved after v2.0 migration"""
        # Create v1.0 schema and insert test data
        self.db.init_schema()
        
        test_interview = {
            "company": "Hotel Los Tajibos",
            "respondent": "Test User",
            "role": "Manager",
            "date": "2024-11-07"
        }
        
        interview_id = self.db.insert_interview(test_interview, {"q1": "a1"})
        self.assertIsNotNone(interview_id)
        
        # Migrate to v2.0
        self.db.init_v2_schema()
        
        # Verify v1.0 data still exists
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM interviews WHERE id = ?", (interview_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        self.assertEqual(result[1], "Hotel Los Tajibos")  # company field
        self.assertEqual(result[2], "Test User")  # respondent field
    
    def test_no_data_loss_on_rerun(self):
        """Test that running init_v2_schema multiple times doesn't lose data"""
        # Initialize v2.0 schema
        self.db.init_v2_schema()
        
        # Insert test data
        test_interview = {
            "company": "Hotel Los Tajibos",
            "respondent": "Test User",
            "role": "Manager",
            "date": "2024-11-07"
        }
        
        interview_id = self.db.insert_interview(test_interview, {"q1": "a1"})
        
        # Run init_v2_schema again
        self.db.init_v2_schema()
        
        # Verify data still exists
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interviews")
        count = cursor.fetchone()[0]
        
        self.assertEqual(count, 1, "Data should not be lost on schema rerun")


class TestOrganizationalHierarchy(unittest.TestCase):
    """Test organizational hierarchy queries"""
    
    def setUp(self):
        """Create temporary database with test data"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
        self.db.init_v2_schema()
        
        # Insert test interviews for different companies
        self._insert_test_data()
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()
    
    def _insert_test_data(self):
        """Insert test data for multiple companies"""
        # Hotel Los Tajibos interview
        hotel_interview = {
            "company": "Hotel Los Tajibos",
            "respondent": "Juan Pérez",
            "role": "Gerente de Restaurantes",
            "date": "2024-11-01"
        }
        hotel_id = self.db.insert_interview(hotel_interview, {"q1": "a1"})
        
        # Comversa interview
        comversa_interview = {
            "company": "Comversa",
            "respondent": "María García",
            "role": "Gerente de Construcción",
            "date": "2024-11-02"
        }
        comversa_id = self.db.insert_interview(comversa_interview, {"q1": "a1"})
        
        # Bolivian Foods interview
        bolivian_interview = {
            "company": "Bolivian Foods",
            "respondent": "Carlos López",
            "role": "Gerente de Producción",
            "date": "2024-11-03"
        }
        bolivian_id = self.db.insert_interview(bolivian_interview, {"q1": "a1"})
        
        # Insert pain points for each company
        self.db.insert_pain_point(hotel_id, "Hotel Los Tajibos", {
            "type": "Process Inefficiency",
            "description": "Manual reconciliation",
            "severity": "High"
        })
        
        self.db.insert_pain_point(comversa_id, "Comversa", {
            "type": "Communication Gap",
            "description": "Delayed approvals",
            "severity": "Medium"
        })
        
        self.db.insert_pain_point(bolivian_id, "Bolivian Foods", {
            "type": "System Issue",
            "description": "Inventory tracking",
            "severity": "High"
        })
    
    def test_query_by_company(self):
        """Test querying entities for specific company"""
        hotel_pain_points = self.db.query_by_company("Hotel Los Tajibos", "pain_point")
        
        self.assertEqual(len(hotel_pain_points), 1)
        self.assertEqual(hotel_pain_points[0]['company'], "Hotel Los Tajibos")
        self.assertIn("Manual reconciliation", hotel_pain_points[0]['description'])
    
    def test_query_cross_company_count(self):
        """Test cross-company aggregation with count"""
        result = self.db.query_cross_company("pain_point", aggregation="count")
        
        self.assertEqual(len(result), 3)
        self.assertEqual(result["Hotel Los Tajibos"], 1)
        self.assertEqual(result["Comversa"], 1)
        self.assertEqual(result["Bolivian Foods"], 1)
    
    def test_query_cross_company_list(self):
        """Test cross-company aggregation with list"""
        result = self.db.query_cross_company("pain_point", aggregation="list")
        
        self.assertEqual(len(result), 3)
        self.assertIn("Hotel Los Tajibos", result)
        self.assertIn("Comversa", result)
        self.assertIn("Bolivian Foods", result)
        
        # Check that each company has its pain points
        self.assertEqual(len(result["Hotel Los Tajibos"]), 1)
        self.assertEqual(len(result["Comversa"]), 1)
        self.assertEqual(len(result["Bolivian Foods"]), 1)
    
    def test_get_v2_stats(self):
        """Test v2.0 statistics generation"""
        stats = self.db.get_v2_stats()
        
        # Check v1.0 stats
        self.assertEqual(stats['interviews'], 3)
        self.assertEqual(stats['pain_points'], 3)
        
        # Check v2.0 stats
        self.assertIn('communication_channels', stats)
        self.assertIn('decision_points', stats)
        self.assertIn('hair_on_fire_problems', stats)
        
        # Check company breakdown
        self.assertIn('by_company', stats)
        self.assertEqual(len(stats['by_company']), 3)


if __name__ == '__main__':
    unittest.main()
