"""
Tests for CEOAssumptionValidator
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.ceo_validator import CEOAssumptionValidator
import tempfile
import json


def create_test_database():
    """Create a test database with sample data"""
    # Create temporary database
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_schema()
    db.init_v2_schema()
    
    # Insert test interviews
    for i in range(10):
        interview_id = db.insert_interview(
            meta={
                "company": f"Company{i % 3}",
                "respondent": f"User{i}",
                "role": f"Role{i}",
                "date": "2024-11-07"
            },
            qa_pairs={"Q1": "A1"}
        )
        
        # Insert pain points with keywords matching CEO priorities
        if i < 5:  # 50% mention "reportes"
            db.insert_pain_point(
                interview_id=interview_id,
                company=f"Company{i % 3}",
                pain_point={
                    "type": "Process Inefficiency",
                    "description": "Necesitamos mejores reportes y KPIs para tomar decisiones",
                    "affected_roles": ["Manager"],
                    "affected_processes": ["Reporting"],
                    "frequency": "Daily",
                    "severity": "High",
                    "impact_description": "No tenemos visibilidad",
                    "proposed_solutions": ["Dashboard automático"]
                }
            )
        
        if i < 3:  # 30% mention "inventario"
            db.insert_pain_point(
                interview_id=interview_id,
                company=f"Company{i % 3}",
                pain_point={
                    "type": "System Issue",
                    "description": "Gestión de inventarios es manual y propenso a errores",
                    "affected_roles": ["Warehouse Manager"],
                    "affected_processes": ["Inventory Management"],
                    "frequency": "Daily",
                    "severity": "High",
                    "impact_description": "Stock outs frecuentes",
                    "proposed_solutions": ["Sistema automatizado"]
                }
            )
        
        if i < 7:  # 70% mention something not in CEO priorities
            db.insert_pain_point(
                interview_id=interview_id,
                company=f"Company{i % 3}",
                pain_point={
                    "type": "Communication Issue",
                    "description": "Comunicación entre departamentos es caótica y desorganizada",
                    "affected_roles": ["All Staff"],
                    "affected_processes": ["Internal Communication"],
                    "frequency": "Daily",
                    "severity": "Medium",
                    "impact_description": "Pérdida de información",
                    "proposed_solutions": ["Sistema de comunicación centralizado"]
                }
            )
        
        # Insert automation candidates
        if i < 2:
            db.insert_automation_candidate(
                interview_id=interview_id,
                company=f"Company{i % 3}",
                automation={
                    "name": "Bot de WhatsApp para consultas",
                    "process": "Customer Service",
                    "trigger": "Message received",
                    "action": "Auto-respond",
                    "output": "Response",
                    "owner": "IT",
                    "complexity": "Low",
                    "impact": "High",
                    "effort_estimate": "2 weeks",
                    "systems_involved": ["WhatsApp API"]
                }
            )
        
        if i == 5:
            # Automation not in CEO priorities
            db.insert_automation_candidate(
                interview_id=interview_id,
                company=f"Company{i % 3}",
                automation={
                    "name": "Sistema de gestión de reuniones",
                    "process": "Meeting Management",
                    "trigger": "Meeting scheduled",
                    "action": "Auto-coordinate",
                    "output": "Calendar invite",
                    "owner": "Admin",
                    "complexity": "Medium",
                    "impact": "Medium",
                    "effort_estimate": "1 month",
                    "systems_involved": ["Calendar", "Email"]
                }
            )
    
    db.conn.commit()
    return db, db_path


def test_load_ceo_priorities():
    """Test loading CEO priorities from JSON"""
    print("Testing CEO priorities loading...")
    
    db, db_path = create_test_database()
    
    try:
        validator = CEOAssumptionValidator(db)
        
        # Check priorities loaded
        assert "quick_wins" in validator.ceo_priorities
        assert "strategic" in validator.ceo_priorities
        assert len(validator.ceo_priorities["quick_wins"]) > 0
        assert len(validator.ceo_priorities["strategic"]) > 0
        
        # Check keywords mapping
        assert len(validator.keywords_mapping) > 0
        assert "Reportes y KPIs Inteligentes" in validator.keywords_mapping
        
        print("✅ CEO priorities loaded successfully")
        print(f"   Quick Wins: {len(validator.ceo_priorities['quick_wins'])}")
        print(f"   Strategic: {len(validator.ceo_priorities['strategic'])}")
        print(f"   Keywords: {len(validator.keywords_mapping)}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_calculate_data_support():
    """Test data support calculation for CEO priorities"""
    print("\nTesting data support calculation...")
    
    db, db_path = create_test_database()
    
    try:
        validator = CEOAssumptionValidator(db)
        
        # Test priority with high support (reportes - 50% of interviews)
        priority_reportes = {
            "name": "Reportes y KPIs Inteligentes",
            "description": "Dashboard automático"
        }
        
        support = validator.calculate_data_support(priority_reportes)
        
        assert support["total_interviews"] == 10
        assert support["mention_count"] == 5  # 50% of interviews
        assert support["support_percentage"] == 50.0
        assert len(support["matching_entities"]) > 0
        
        print("✅ Data support calculation working")
        print(f"   Total interviews: {support['total_interviews']}")
        print(f"   Mentions: {support['mention_count']}")
        print(f"   Support: {support['support_percentage']}%")
        
        # Test priority with medium support (inventario - 30%)
        priority_inventario = {
            "name": "Gestión de Inventarios y Compras",
            "description": "Sistema de inventarios"
        }
        
        support2 = validator.calculate_data_support(priority_inventario)
        assert support2["support_percentage"] == 30.0
        
        print(f"   Inventory support: {support2['support_percentage']}%")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_validate_priorities():
    """Test full priority validation"""
    print("\nTesting priority validation...")
    
    db, db_path = create_test_database()
    
    try:
        validator = CEOAssumptionValidator(db)
        
        results = validator.validate_priorities()
        
        # Check structure
        assert "confirmed_priorities" in results
        assert "weak_priorities" in results
        assert "overlooked_opportunities" in results
        assert "emergent_opportunities" in results
        assert "summary" in results
        
        # Check summary
        summary = results["summary"]
        assert summary["total_priorities"] > 0
        assert summary["confirmed"] >= 0
        assert summary["weak"] >= 0
        assert summary["overlooked"] >= 0
        assert summary["emergent"] >= 0
        
        print("✅ Priority validation working")
        print(f"   Total priorities: {summary['total_priorities']}")
        print(f"   Confirmed: {summary['confirmed']}")
        print(f"   Weak: {summary['weak']}")
        print(f"   Overlooked: {summary['overlooked']}")
        print(f"   Emergent: {summary['emergent']}")
        
        # Check confirmed priorities have high support
        for priority in results["confirmed_priorities"]:
            assert priority["support_percentage"] >= 30
            print(f"   ✓ {priority['name']}: {priority['support_percentage']}%")
        
        # Check overlooked opportunities
        if results["overlooked_opportunities"]:
            print(f"\n   Overlooked opportunities found:")
            for opp in results["overlooked_opportunities"][:2]:
                print(f"   - {opp['description'][:50]}... ({opp['support_percentage']}%)")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_generate_report():
    """Test report generation"""
    print("\nTesting report generation...")
    
    db, db_path = create_test_database()
    
    try:
        validator = CEOAssumptionValidator(db)
        
        # Generate report
        report_path = tempfile.mktemp(suffix='.json')
        result_path = validator.generate_validation_report(report_path)
        
        # Check file exists
        assert Path(result_path).exists()
        
        # Load and validate report
        with open(result_path, 'r') as f:
            report = json.load(f)
        
        assert "metadata" in report
        assert "validation_results" in report
        assert "summary" in report["validation_results"]
        
        print("✅ Report generation working")
        print(f"   Report saved to: {result_path}")
        
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
        validator = CEOAssumptionValidator(db)
        
        # This should print without errors
        validator.print_summary()
        
        print("✅ Summary printing working")
        
    finally:
        db.close()
        os.unlink(db_path)


if __name__ == "__main__":
    print("=" * 70)
    print("Testing CEOAssumptionValidator")
    print("=" * 70)
    print()
    
    test_load_ceo_priorities()
    test_calculate_data_support()
    test_validate_priorities()
    test_generate_report()
    test_print_summary()
    
    print()
    print("=" * 70)
    print("All CEOAssumptionValidator tests passed!")
    print("=" * 70)
