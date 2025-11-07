"""
Tests for CrossCompanyAnalyzer
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.cross_company_analyzer import CrossCompanyAnalyzer
import tempfile
import json


def create_test_database():
    """Create a test database with multi-company data"""
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    db_path = db_file.name
    db_file.close()
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_schema()
    db.init_v2_schema()
    
    companies = ["Hotel Los Tajibos", "Comversa", "Bolivian Foods"]
    
    # Insert interviews for each company
    for company_idx, company in enumerate(companies):
        for i in range(3):
            interview_id = db.insert_interview(
                meta={
                    "company": company,
                    "respondent": f"User{company_idx}_{i}",
                    "role": f"Manager",
                    "date": "2024-11-07"
                },
                qa_pairs={"Q1": "A1"}
            )
            
            # Common pain point across all companies
            db.insert_pain_point(
                interview_id=interview_id,
                company=company,
                pain_point={
                    "type": "Process Inefficiency",
                    "description": "Reportes manuales toman mucho tiempo y son propensos a errores",
                    "affected_roles": ["Manager"],
                    "affected_processes": ["Reporting"],
                    "frequency": "Daily",
                    "severity": "High",
                    "impact_description": "Pérdida de tiempo",
                    "proposed_solutions": ["Automatización"]
                }
            )
            
            # Pain point in 2 companies
            if company_idx < 2:
                db.insert_pain_point(
                    interview_id=interview_id,
                    company=company,
                    pain_point={
                        "type": "System Issue",
                        "description": "Sistema de inventarios no está integrado con contabilidad",
                        "affected_roles": ["Warehouse Manager"],
                        "affected_processes": ["Inventory"],
                        "frequency": "Daily",
                        "severity": "Medium",
                        "impact_description": "Doble entrada",
                        "proposed_solutions": ["Integración"]
                    }
                )
            
            # Company-specific pain point
            db.insert_pain_point(
                interview_id=interview_id,
                company=company,
                pain_point={
                    "type": "Communication",
                    "description": f"Problema específico de {company}",
                    "affected_roles": ["Staff"],
                    "affected_processes": ["Communication"],
                    "frequency": "Weekly",
                    "severity": "Low",
                    "impact_description": "Minor issue",
                    "proposed_solutions": []
                }
            )
            
            # Process that exists in multiple companies
            db.insert_process(
                interview_id=interview_id,
                company=company,
                process={
                    "name": "Cierre mensual contable",
                    "owner": "Contador",
                    "domain": "Finance",
                    "description": f"Proceso de cierre en {company}",
                    "inputs": ["Transacciones"],
                    "outputs": ["Reportes"],
                    "systems": [f"System_{company_idx}"],  # Different systems
                    "frequency": "Monthly",
                    "dependencies": []
                }
            )
            
            # Automation candidate
            if i == 0:
                db.insert_automation_candidate(
                    interview_id=interview_id,
                    company=company,
                    automation={
                        "name": f"Automatización de reportes - {company}",
                        "process": "Generación de reportes",
                        "trigger": "Fin de mes",
                        "action": "Generar automáticamente",
                        "output": "Reportes",
                        "owner": "IT",
                        "complexity": "Medium",
                        "impact": "High",
                        "effort_estimate": "2 months",
                        "systems_involved": [f"System_{company_idx}"]
                    }
                )
    
    # Insert shared systems
    for company in companies:
        db.insert_or_update_system(
            system={
                "name": "SAP",
                "domain": "ERP",
                "vendor": "SAP",
                "type": "ERP",
                "pain_points": [f"Lento en {company}", "Complejo"]
            },
            company=company
        )
    
    db.conn.commit()
    return db, db_path


def test_get_companies():
    """Test getting list of companies"""
    print("Testing company list retrieval...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        assert len(analyzer.companies) == 3
        assert "Hotel Los Tajibos" in analyzer.companies
        assert "Comversa" in analyzer.companies
        assert "Bolivian Foods" in analyzer.companies
        
        print("✅ Company list retrieved successfully")
        print(f"   Companies: {', '.join(analyzer.companies)}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_detect_common_pain_points():
    """Test detection of common pain points across companies"""
    print("\nTesting common pain point detection...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        common_pain_points = analyzer._detect_common_pain_points()
        
        # Should find at least 2 common pain points
        assert len(common_pain_points) >= 2
        
        # Find the pain point in all 3 companies
        all_companies_pain = [p for p in common_pain_points if p["prevalence"] == 1.0]
        assert len(all_companies_pain) >= 1
        
        # Find the pain point in 2 companies
        two_companies_pain = [p for p in common_pain_points if p["prevalence"] == 0.67]
        assert len(two_companies_pain) >= 1
        
        print("✅ Common pain point detection working")
        print(f"   Total common pain points: {len(common_pain_points)}")
        
        for pain in common_pain_points[:2]:
            print(f"   - {pain['description'][:50]}...")
            print(f"     Companies: {', '.join(pain['companies_affected'])}")
            print(f"     Prevalence: {int(pain['prevalence'] * 100)}%")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_detect_standardization_opportunities():
    """Test detection of standardization opportunities"""
    print("\nTesting standardization opportunity detection...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        standardization_opps = analyzer._detect_standardization_opportunities()
        
        # Should find at least 1 standardization opportunity
        # (Cierre mensual contable exists in all companies with different systems)
        assert len(standardization_opps) >= 1
        
        print("✅ Standardization opportunity detection working")
        print(f"   Total opportunities: {len(standardization_opps)}")
        
        for opp in standardization_opps[:2]:
            print(f"   - {opp['process_name']}")
            print(f"     Companies: {', '.join(opp['companies_affected'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_analyze_shared_systems():
    """Test analysis of shared systems"""
    print("\nTesting shared system analysis...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        shared_systems = analyzer._analyze_shared_systems()
        
        # Should find SAP as shared system
        assert len(shared_systems) >= 1
        
        sap_system = next((s for s in shared_systems if s["system_name"] == "SAP"), None)
        assert sap_system is not None
        assert sap_system["usage_count"] == 3  # Used by all 3 companies
        
        print("✅ Shared system analysis working")
        print(f"   Total shared systems: {len(shared_systems)}")
        
        for system in shared_systems:
            print(f"   - {system['system_name']}")
            print(f"     Used by: {', '.join(system['companies_using'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_detect_divergent_approaches():
    """Test detection of divergent approaches"""
    print("\nTesting divergent approach detection...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        divergent = analyzer._detect_divergent_approaches()
        
        # Should find divergent approaches for report generation
        # (each company has different automation approach)
        assert len(divergent) >= 1
        
        print("✅ Divergent approach detection working")
        print(f"   Total divergent approaches: {len(divergent)}")
        
        for div in divergent[:2]:
            print(f"   - {div['process']}")
            print(f"     Companies: {', '.join(div['companies'])}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_analyze_patterns():
    """Test full pattern analysis"""
    print("\nTesting full pattern analysis...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        results = analyzer.analyze_patterns()
        
        # Check structure
        assert "common_pain_points" in results
        assert "standardization_opportunities" in results
        assert "shared_systems" in results
        assert "divergent_approaches" in results
        assert "summary" in results
        
        # Check summary
        summary = results["summary"]
        assert summary["total_companies"] == 3
        assert summary["common_pain_points"] >= 2
        assert summary["standardization_opportunities"] >= 1
        assert summary["shared_systems"] >= 1
        
        print("✅ Full pattern analysis working")
        print(f"   Companies: {summary['total_companies']}")
        print(f"   Common pain points: {summary['common_pain_points']}")
        print(f"   Standardization opportunities: {summary['standardization_opportunities']}")
        print(f"   Shared systems: {summary['shared_systems']}")
        print(f"   Divergent approaches: {summary['divergent_approaches']}")
        
    finally:
        db.close()
        os.unlink(db_path)


def test_generate_insights_report():
    """Test insights report generation"""
    print("\nTesting insights report generation...")
    
    db, db_path = create_test_database()
    
    try:
        analyzer = CrossCompanyAnalyzer(db)
        
        # Generate report
        report_path = tempfile.mktemp(suffix='.json')
        result_path = analyzer.generate_insights_report(report_path)
        
        # Check file exists
        assert Path(result_path).exists()
        
        # Load and validate report
        with open(result_path, 'r') as f:
            report = json.load(f)
        
        assert "metadata" in report
        assert "analysis_results" in report
        assert "recommendations" in report
        
        print("✅ Insights report generation working")
        print(f"   Report saved to: {result_path}")
        print(f"   Recommendations: {len(report['recommendations'])}")
        
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
        analyzer = CrossCompanyAnalyzer(db)
        
        # This should print without errors
        analyzer.print_summary()
        
        print("✅ Summary printing working")
        
    finally:
        db.close()
        os.unlink(db_path)


if __name__ == "__main__":
    print("=" * 70)
    print("Testing CrossCompanyAnalyzer")
    print("=" * 70)
    print()
    
    test_get_companies()
    test_detect_common_pain_points()
    test_detect_standardization_opportunities()
    test_analyze_shared_systems()
    test_detect_divergent_approaches()
    test_analyze_patterns()
    test_generate_insights_report()
    test_print_summary()
    
    print()
    print("=" * 70)
    print("All CrossCompanyAnalyzer tests passed!")
    print("=" * 70)
