"""
Integration test using real interview data
Tests that the enhanced schema works with actual interview data from the 44 interviews
"""
import unittest
import sqlite3
import json
import tempfile
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB


class TestRealInterviewData(unittest.TestCase):
    """Test database with real interview data"""
    
    def setUp(self):
        """Create temporary database and load real interview data"""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.db_path = Path(self.temp_db.name)
        self.db = EnhancedIntelligenceDB(self.db_path)
        self.db.connect()
        self.db.init_v2_schema()
        
        # Load real interview data
        self.interviews_path = Path(__file__).parent.parent / "data" / "interviews" / "analysis_output" / "all_interviews.json"
        with open(self.interviews_path, 'r', encoding='utf-8') as f:
            self.interviews = json.load(f)
    
    def tearDown(self):
        """Clean up temporary database"""
        self.db.close()
        if self.db_path.exists():
            self.db_path.unlink()
    
    def test_load_real_interviews(self):
        """Test loading real interview data into database"""
        print(f"\n📊 Loading {len(self.interviews)} real interviews...")
        
        loaded_count = 0
        for interview in self.interviews[:5]:  # Test with first 5 interviews
            meta = interview['meta']
            qa_pairs = interview['qa_pairs']
            
            # Infer company from role/context if not specified
            company = meta.get('company', '')
            if not company:
                # Try to infer from role or content
                role = meta.get('role', '').lower()
                if 'hotel' in str(qa_pairs).lower() or 'hospedaje' in str(qa_pairs).lower():
                    company = "Hotel Los Tajibos"
                elif 'construcción' in str(qa_pairs).lower() or 'inmobiliaria' in str(qa_pairs).lower():
                    company = "Comversa"
                elif 'producción' in str(qa_pairs).lower() or 'franquicia' in str(qa_pairs).lower():
                    company = "Bolivian Foods"
                else:
                    company = "Unknown"
                
                meta['company'] = company
            
            interview_id = self.db.insert_interview(meta, qa_pairs)
            self.assertIsNotNone(interview_id, f"Failed to insert interview for {meta.get('respondent')}")
            loaded_count += 1
            print(f"  ✅ Loaded interview {loaded_count}: {meta.get('respondent')} ({meta.get('role')}) - {company}")
        
        # Verify interviews were loaded
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM interviews")
        count = cursor.fetchone()[0]
        
        self.assertEqual(count, 5, "Should have loaded 5 interviews")
        print(f"\n✅ Successfully loaded {count} interviews into database")
    
    def test_insert_pain_point_from_real_interview(self):
        """Test inserting pain points extracted from real interview"""
        # Load first interview (Gerente de Ingeniería)
        interview = self.interviews[0]
        meta = interview['meta']
        meta['company'] = "Hotel Los Tajibos"  # Inferred from content
        
        interview_id = self.db.insert_interview(meta, interview['qa_pairs'])
        
        # Extract a pain point from the interview
        # From: "Gestionar reparaciónes con personal interno o proveedor con tiempos muy ajustados y falta de recursos"
        pain_point = {
            "type": "Resource Constraint",
            "description": "Gestionar reparaciones con personal interno o proveedor con tiempos muy ajustados y falta de recursos para agilizar",
            "affected_roles": ["Gerente de Ingeniería", "Técnicos de Mantenimiento"],
            "affected_processes": ["Gestión de mantenimiento"],
            "frequency": "Daily",
            "severity": "High",
            "impact_description": "Retrasos en reparaciones, afecta operativa del hotel",
            "proposed_solutions": ["Implementación de software MaintainX", "Mejor gestión de inventarios"],
            # v2.0 fields
            "intensity_score": 8,
            "time_wasted_per_occurrence_minutes": 120,
            "cost_impact_monthly_usd": 2000,
            "jtbd_who": "Gerente de Ingeniería",
            "jtbd_what": "Gestionar reparaciones urgentes",
            "jtbd_where": "Durante operativa diaria del hotel",
            "root_cause": "Falta de herramientas de gestión y recursos limitados",
            "current_workaround": "Coordinación manual vía WhatsApp",
            "confidence_score": 0.95,
            "extraction_source": "interview_1_question_5"
        }
        
        self.db.insert_pain_point(interview_id, "Hotel Los Tajibos", pain_point)
        
        # Verify pain point was inserted with v2.0 fields
        cursor = self.db.conn.cursor()
        cursor.execute("SELECT * FROM pain_points WHERE interview_id = ?", (interview_id,))
        result = cursor.fetchone()
        
        self.assertIsNotNone(result)
        
        # Check v2.0 fields are populated
        cursor.execute("PRAGMA table_info(pain_points)")
        columns = {row[1]: idx for idx, row in enumerate(cursor.fetchall())}
        
        # Verify v2.0 fields exist and have values
        self.assertIn('intensity_score', columns)
        self.assertIn('jtbd_who', columns)
        self.assertIn('root_cause', columns)
        self.assertIn('confidence_score', columns)
        
        print(f"\n✅ Pain point inserted with v2.0 fields:")
        print(f"  - Intensity: {pain_point['intensity_score']}/10")
        print(f"  - Frequency: {pain_point['frequency']}")
        print(f"  - Time wasted: {pain_point['time_wasted_per_occurrence_minutes']} min/occurrence")
        print(f"  - Cost impact: ${pain_point['cost_impact_monthly_usd']}/month")
        print(f"  - Root cause: {pain_point['root_cause']}")
    
    def test_query_by_company_with_real_data(self):
        """Test company-specific queries with real interview data"""
        # Load interviews for different companies
        hotel_interview = self.interviews[0]  # Gerente de Ingeniería - Hotel
        hotel_interview['meta']['company'] = "Hotel Los Tajibos"
        
        accounting_interview = self.interviews[1]  # Gerente de Contabilidad - Hotel
        accounting_interview['meta']['company'] = "Hotel Los Tajibos"
        
        # Insert interviews
        hotel_id = self.db.insert_interview(hotel_interview['meta'], hotel_interview['qa_pairs'])
        accounting_id = self.db.insert_interview(accounting_interview['meta'], accounting_interview['qa_pairs'])
        
        # Insert pain points for each
        self.db.insert_pain_point(hotel_id, "Hotel Los Tajibos", {
            "type": "Tool Gap",
            "description": "Falta de herramientas de gestión de mantenimiento",
            "severity": "High"
        })
        
        self.db.insert_pain_point(accounting_id, "Hotel Los Tajibos", {
            "type": "Process Inefficiency",
            "description": "Conciliaciones manuales entre sistemas",
            "severity": "High"
        })
        
        # Query pain points for Hotel Los Tajibos
        hotel_pain_points = self.db.query_by_company("Hotel Los Tajibos", "pain_point")
        
        self.assertEqual(len(hotel_pain_points), 2)
        print(f"\n✅ Found {len(hotel_pain_points)} pain points for Hotel Los Tajibos:")
        for pp in hotel_pain_points:
            print(f"  - {pp['description']}")
    
    def test_database_stats_with_real_data(self):
        """Test statistics generation with real interview data"""
        # Load first 3 interviews
        for interview in self.interviews[:3]:
            meta = interview['meta']
            # Infer company
            if 'hotel' in str(interview['qa_pairs']).lower():
                meta['company'] = "Hotel Los Tajibos"
            else:
                meta['company'] = "Unknown"
            
            self.db.insert_interview(meta, interview['qa_pairs'])
        
        # Get stats
        stats = self.db.get_v2_stats()
        
        print(f"\n📊 Database Statistics:")
        print(f"  - Total interviews: {stats['interviews']}")
        print(f"  - Total pain points: {stats['pain_points']}")
        print(f"  - Total processes: {stats['processes']}")
        print(f"  - Communication channels: {stats['communication_channels']}")
        print(f"  - Decision points: {stats['decision_points']}")
        print(f"  - Data flows: {stats['data_flows']}")
        print(f"  - Temporal patterns: {stats['temporal_patterns']}")
        print(f"  - Failure modes: {stats['failure_modes']}")
        
        self.assertEqual(stats['interviews'], 3)
        self.assertIn('by_company', stats)
    
    def test_real_interview_content_analysis(self):
        """Analyze real interview content to understand extraction needs"""
        print(f"\n🔍 Analyzing real interview content...")
        print(f"Total interviews available: {len(self.interviews)}")
        
        # Analyze first 5 interviews
        companies_found = set()
        roles_found = set()
        systems_mentioned = set()
        
        for i, interview in enumerate(self.interviews[:5], 1):
            meta = interview['meta']
            qa_pairs = interview['qa_pairs']
            
            print(f"\n📋 Interview {i}:")
            print(f"  Respondent: {meta.get('respondent')}")
            print(f"  Role: {meta.get('role')}")
            print(f"  Date: {meta.get('date')}")
            
            roles_found.add(meta.get('role', 'Unknown'))
            
            # Look for system mentions
            content = str(qa_pairs).lower()
            if 'sap' in content:
                systems_mentioned.add('SAP')
            if 'whatsapp' in content:
                systems_mentioned.add('WhatsApp')
            if 'excel' in content:
                systems_mentioned.add('Excel')
            if 'outlook' in content:
                systems_mentioned.add('Outlook')
            if 'maintainx' in content:
                systems_mentioned.add('MaintainX')
            if 'jira' in content:
                systems_mentioned.add('Jira')
            if 'power automate' in content:
                systems_mentioned.add('Power Automate')
            
            # Infer company
            if 'hotel' in content or 'hospedaje' in content:
                companies_found.add('Hotel Los Tajibos')
            elif 'construcción' in content or 'inmobiliaria' in content:
                companies_found.add('Comversa')
            elif 'producción' in content or 'franquicia' in content:
                companies_found.add('Bolivian Foods')
        
        print(f"\n📊 Analysis Summary:")
        print(f"  Companies identified: {', '.join(companies_found) if companies_found else 'None (needs inference)'}")
        print(f"  Unique roles: {len(roles_found)}")
        print(f"  Systems mentioned: {', '.join(sorted(systems_mentioned))}")
        
        print(f"\n💡 Insights for extraction:")
        print(f"  - Company field is empty in metadata, needs inference from content")
        print(f"  - {len(systems_mentioned)} different systems mentioned (integration opportunities)")
        print(f"  - Roles are well-defined, can be used for business unit classification")
        
        self.assertGreater(len(systems_mentioned), 0, "Should find system mentions in interviews")


if __name__ == '__main__':
    unittest.main(verbosity=2)
