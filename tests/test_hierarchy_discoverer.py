"""
Tests for HierarchyDiscoverer
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.hierarchy_discoverer import HierarchyDiscoverer
import tempfile
import json


def create_test_database():
    """Create test database with sample interviews"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_schema()
    db.init_v2_schema()
    
    # Insert test interviews with org structure mentions
    interviews = [
        {
            "company": "Hotel Los Tajibos",
            "respondent": "Juan Pérez",
            "role": "Gerente de Restaurantes",
            "qa_pairs": {
                "¿En qué área trabajas?": "Trabajo en Alimentos y Bebidas, específicamente en el departamento de Restaurantes",
                "¿A quién reportas?": "Reporto al Gerente de A&B",
                "¿Con quién coordinas?": "Coordino con Cocina, Bares y Compras"
            }
        },
        {
            "company": "Hotel Los Tajibos",
            "respondent": "María García",
            "role": "Jefe de Cocina",
            "qa_pairs": {
                "¿Dónde trabajas?": "Soy parte de Food & Beverage, en la Cocina Central",
                "¿Quién es tu jefe?": "Reporto al Gerente de Alimentos y Bebidas"
            }
        },
        {
            "company": "Comversa",
            "respondent": "Carlos López",
            "role": "Ingeniero",
            "qa_pairs": {
                "¿En qué departamento estás?": "Estoy en Construcción, departamento de Ingeniería",
                "¿Con quién trabajas?": "Trabajo con Proyectos y Compras"
            }
        }
    ]
    
    for interview in interviews:
        interview_id = db.insert_interview(
            meta={
                "company": interview["company"],
                "respondent": interview["respondent"],
                "role": interview["role"],
                "date": "2024-11-07"
            },
            qa_pairs=interview["qa_pairs"]
        )
    
    db.conn.commit()
    return db, db_path


def test_load_predefined_hierarchy():
    """Test loading predefined hierarchy"""
    print("Testing predefined hierarchy loading...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        # Check hierarchy loaded
        assert "companies" in discoverer.predefined_hierarchy
        assert len(discoverer.predefined_hierarchy["companies"]) > 0
        
        print("✅ Predefined hierarchy loaded")
        print(f"   Companies: {len(discoverer.predefined_hierarchy['companies'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_extract_org_structure():
    """Test org structure extraction from interview"""
    print("\nTesting org structure extraction...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        qa_pairs = {
            "¿En qué área trabajas?": "Trabajo en Alimentos y Bebidas, en Restaurantes",
            "¿A quién reportas?": "Reporto al Gerente de A&B"
        }
        
        result = discoverer.extract_org_structure(qa_pairs, "Hotel Los Tajibos", "Gerente")
        
        # Check structure
        assert "self_identified_company" in result
        assert "self_identified_business_unit" in result
        assert "confidence" in result
        
        print("✅ Org structure extraction working")
        print(f"   Company: {result.get('self_identified_company')}")
        print(f"   Business Unit: {result.get('self_identified_business_unit')}")
        print(f"   Confidence: {result.get('confidence')}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_aggregate_discoveries():
    """Test aggregation of discoveries across interviews"""
    print("\nTesting discovery aggregation...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        # Create mock discoveries
        discoveries = [
            {
                "company": "Hotel Los Tajibos",
                "role": "Manager",
                "discovered": {
                    "self_identified_business_unit": "Alimentos y Bebidas",
                    "self_identified_department": "Restaurantes",
                    "coordinates_with": ["Cocina", "Bares"]
                }
            },
            {
                "company": "Hotel Los Tajibos",
                "role": "Chef",
                "discovered": {
                    "self_identified_business_unit": "Food & Beverage",
                    "self_identified_department": "Cocina",
                    "coordinates_with": ["Restaurantes"]
                }
            }
        ]
        
        aggregated = discoverer._aggregate_discoveries(discoveries)
        
        # Check aggregation
        assert "Hotel Los Tajibos" in aggregated
        assert len(aggregated["Hotel Los Tajibos"]["business_units"]) >= 1
        
        print("✅ Discovery aggregation working")
        print(f"   Companies: {list(aggregated.keys())}")
        print(f"   Business units found: {len(aggregated['Hotel Los Tajibos']['business_units'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_validate_against_predefined():
    """Test validation against predefined hierarchy"""
    print("\nTesting validation against predefined...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        # Create mock aggregated data
        aggregated = {
            "Hotel Los Tajibos": {
                "business_units": {
                    "alimentos y bebidas": {
                        "count": 2,
                        "names": ["Alimentos y Bebidas", "Food & Beverage"],
                        "most_common": "Alimentos y Bebidas",
                        "departments": {}
                    },
                    "ingeniería": {
                        "count": 1,
                        "names": ["Ingeniería"],
                        "most_common": "Ingeniería",
                        "departments": {}
                    }
                },
                "departments": {},
                "reporting_relationships": [],
                "coordination_patterns": {}
            }
        }
        
        validation = discoverer._validate_against_predefined(aggregated)
        
        # Check validation structure
        assert "confirmed_structure" in validation
        assert "naming_inconsistencies" in validation
        assert "new_discoveries" in validation
        assert "summary" in validation
        
        print("✅ Validation working")
        print(f"   Confirmed: {validation['summary']['confirmed']}")
        print(f"   Inconsistencies: {validation['summary']['inconsistencies']}")
        print(f"   New discoveries: {validation['summary']['new_discoveries']}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_discover_hierarchy():
    """Test full hierarchy discovery"""
    print("\nTesting full hierarchy discovery...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        results = discoverer.discover_hierarchy()
        
        # Check structure
        assert "discoveries" in results
        assert "aggregated" in results
        assert "validation" in results
        
        print("✅ Full hierarchy discovery working")
        print(f"   Interviews analyzed: {len(results['discoveries'])}")
        print(f"   Companies found: {len(results['aggregated'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_generate_validation_report():
    """Test validation report generation"""
    print("\nTesting validation report generation...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        # Generate report
        report_path = tempfile.mktemp(suffix='.json')
        result_path = discoverer.generate_validation_report(report_path)
        
        # Check file exists
        assert Path(result_path).exists()
        
        # Load and validate report
        with open(result_path, 'r') as f:
            report = json.load(f)
        
        assert "metadata" in report
        assert "aggregated_hierarchy" in report
        assert "validation_results" in report
        assert "recommended_actions" in report
        
        print("✅ Validation report generation working")
        print(f"   Report saved to: {result_path}")
        print(f"   Recommended actions: {len(report['recommended_actions'])}")
        
        # Cleanup
        os.unlink(result_path)
        
    finally:
        db.close()
        os.unlink(db_path)


def test_print_summary():
    """Test summary printing"""
    print("\nTesting summary printing...")
    
    db, db_path = create_test_database()
    
    try:
        discoverer = HierarchyDiscoverer(db)
        
        # This should print without errors
        discoverer.print_summary()
        
        print("✅ Summary printing working")
        
    finally:
        db.close()
        os.unlink(db_path)


if __name__ == "__main__":
    print("=" * 70)
    print("Testing HierarchyDiscoverer")
    print("=" * 70)
    print()
    
    test_load_predefined_hierarchy()
    test_extract_org_structure()
    test_aggregate_discoveries()
    test_validate_against_predefined()
    test_discover_hierarchy()
    test_generate_validation_report()
    test_print_summary()
    
    print()
    print("=" * 70)
    print("All HierarchyDiscoverer tests passed!")
    print("=" * 70)
