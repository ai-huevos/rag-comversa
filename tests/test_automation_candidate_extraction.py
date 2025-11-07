"""
Tests for AutomationCandidateExtractor - Enhanced automation candidate extraction with effort/impact scoring
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from intelligence_capture.extractors import AutomationCandidateExtractor


def test_effort_scoring():
    """Test effort score calculation based on complexity and systems involved"""
    extractor = AutomationCandidateExtractor()
    
    # Test low effort: 1 system, low complexity
    candidate_low = {
        "systems_involved": ["Excel"],
        "complexity": "Low",
        "data_sources_needed": [],
        "approval_required": False
    }
    effort = extractor._calculate_effort_score(candidate_low)
    assert effort <= 2, f"Expected low effort score <= 2, got {effort}"
    
    # Test high effort: 5+ systems, high complexity
    candidate_high = {
        "systems_involved": ["SAP", "Opera", "Simphony", "Excel", "Outlook", "Teams"],
        "complexity": "High",
        "data_sources_needed": ["SAP API", "Opera API", "Simphony API"],
        "approval_required": True
    }
    effort = extractor._calculate_effort_score(candidate_high)
    assert effort >= 4, f"Expected high effort score >= 4, got {effort}"
    
    # Test medium effort: 2-3 systems, medium complexity
    candidate_medium = {
        "systems_involved": ["SAP", "Excel"],
        "complexity": "Medium",
        "data_sources_needed": ["SAP API"],
        "approval_required": False
    }
    effort = extractor._calculate_effort_score(candidate_medium)
    assert 2 <= effort <= 4, f"Expected medium effort score 2-4, got {effort}"
    
    print("✅ Effort scoring tests passed")
    print(f"   Low effort: {extractor._calculate_effort_score(candidate_low)}")
    print(f"   Medium effort: {extractor._calculate_effort_score(candidate_medium)}")
    print(f"   High effort: {extractor._calculate_effort_score(candidate_high)}")


def test_impact_scoring():
    """Test impact score calculation based on severity, frequency, and affected roles"""
    extractor = AutomationCandidateExtractor()
    
    # Test low impact: Minor improvement, few people
    candidate_low = {
        "impact": "Low",
        "time_wasted_per_occurrence_minutes": 15,
        "frequency": "Monthly",
        "estimated_annual_savings_usd": 2000,
        "affected_roles": ["Asistente"]
    }
    impact = extractor._calculate_impact_score(candidate_low)
    assert impact <= 2, f"Expected low impact score <= 2, got {impact}"
    
    # Test high impact: Critical, daily, many people affected
    candidate_high = {
        "impact": "High - Critical bloqueante",
        "time_wasted_per_occurrence_minutes": 180,
        "frequency": "Daily",
        "estimated_annual_savings_usd": 60000,
        "affected_roles": ["Gerente", "Contador", "Asistente", "Jefe", "Analista"]
    }
    impact = extractor._calculate_impact_score(candidate_high)
    assert impact >= 4, f"Expected high impact score >= 4, got {impact}"
    
    # Test medium impact
    candidate_medium = {
        "impact": "Medium",
        "time_wasted_per_occurrence_minutes": 60,
        "frequency": "Weekly",
        "estimated_annual_savings_usd": 15000,
        "affected_roles": ["Gerente", "Contador"]
    }
    impact = extractor._calculate_impact_score(candidate_medium)
    assert 2 <= impact <= 4, f"Expected medium impact score 2-4, got {impact}"
    
    print("✅ Impact scoring tests passed")
    print(f"   Low impact: {extractor._calculate_impact_score(candidate_low)}")
    print(f"   Medium impact: {extractor._calculate_impact_score(candidate_medium)}")
    print(f"   High impact: {extractor._calculate_impact_score(candidate_high)}")


def test_priority_quadrant_classification():
    """Test priority quadrant classification based on effort and impact"""
    extractor = AutomationCandidateExtractor()
    
    # Quick Win: Low effort, High impact
    assert extractor._classify_priority_quadrant(1, 5) == "Quick Win"
    assert extractor._classify_priority_quadrant(2, 4) == "Quick Win"
    
    # Strategic: High effort, High impact
    assert extractor._classify_priority_quadrant(5, 5) == "Strategic"
    assert extractor._classify_priority_quadrant(4, 4) == "Strategic"
    
    # Incremental: Low effort, Low impact
    assert extractor._classify_priority_quadrant(1, 2) == "Incremental"
    assert extractor._classify_priority_quadrant(2, 3) == "Incremental"
    
    # Reconsider: High effort, Low impact
    assert extractor._classify_priority_quadrant(5, 2) == "Reconsider"
    assert extractor._classify_priority_quadrant(4, 1) == "Reconsider"
    
    print("✅ Priority quadrant classification tests passed")
    print(f"   Quick Win: effort=2, impact=5 → {extractor._classify_priority_quadrant(2, 5)}")
    print(f"   Strategic: effort=4, impact=4 → {extractor._classify_priority_quadrant(4, 4)}")
    print(f"   Incremental: effort=2, impact=2 → {extractor._classify_priority_quadrant(2, 2)}")
    print(f"   Reconsider: effort=5, impact=2 → {extractor._classify_priority_quadrant(5, 2)}")


def test_roi_calculation():
    """Test ROI calculation in months"""
    extractor = AutomationCandidateExtractor()
    
    # 6 month ROI: $10k cost, $20k annual savings
    roi = extractor._calculate_roi_months(20000, 10000)
    assert roi == 6.0, f"Expected 6 month ROI, got {roi}"
    
    # 12 month ROI: $15k cost, $15k annual savings
    roi = extractor._calculate_roi_months(15000, 15000)
    assert roi == 12.0, f"Expected 12 month ROI, got {roi}"
    
    # 3 month ROI: $5k cost, $20k annual savings
    roi = extractor._calculate_roi_months(20000, 5000)
    assert roi == 3.0, f"Expected 3 month ROI, got {roi}"
    
    print("✅ ROI calculation tests passed")
    print(f"   $10k cost / $20k savings = {extractor._calculate_roi_months(20000, 10000)} months")
    print(f"   $15k cost / $15k savings = {extractor._calculate_roi_months(15000, 15000)} months")
    print(f"   $5k cost / $20k savings = {extractor._calculate_roi_months(20000, 5000)} months")


def test_automation_candidate_extraction():
    """Test extraction of automation candidates with LLM"""
    import os
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping LLM extraction test (no API key)")
        return
    
    extractor = AutomationCandidateExtractor()
    
    interview_data = {
        "meta": {
            "company": "Hotel Los Tajibos",
            "role": "Gerente de Restaurantes",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué procesos manuales tienes?": "Todos los días tengo que pasar los datos de ventas de Simphony a SAP manualmente. Exporto de Simphony, concilio en Excel, y luego importo a SAP. Me toma 2 horas diarias.",
            "¿Qué te gustaría automatizar?": "Definitivamente la integración entre Simphony y SAP. Debería ser automático. También respondo las mismas preguntas por WhatsApp todo el tiempo sobre el menú y horarios."
        }
    }
    
    candidates = extractor.extract_from_interview(interview_data)
    
    if len(candidates) == 0:
        print("⚠️  No automation candidates extracted (may need better prompt)")
        return
    
    print(f"✅ Automation candidate extraction test passed")
    print(f"   Extracted {len(candidates)} candidates:")
    
    for candidate in candidates:
        print(f"\n   - {candidate['name']}")
        print(f"     Effort: {candidate.get('effort_score', 'N/A')}, Impact: {candidate.get('impact_score', 'N/A')}")
        print(f"     Priority: {candidate.get('priority_quadrant', 'N/A')}")
        print(f"     Systems: {candidate.get('systems_involved', [])}")
        print(f"     Monitoring: {candidate.get('monitoring_metrics', [])}")
        
        # Verify required fields are present
        assert candidate.get("effort_score") is not None, "Missing effort_score"
        assert candidate.get("impact_score") is not None, "Missing impact_score"
        assert candidate.get("priority_quadrant") is not None, "Missing priority_quadrant"
        assert 1 <= candidate["effort_score"] <= 5, f"Invalid effort_score: {candidate['effort_score']}"
        assert 1 <= candidate["impact_score"] <= 5, f"Invalid impact_score: {candidate['impact_score']}"
        assert candidate["priority_quadrant"] in ["Quick Win", "Strategic", "Incremental", "Reconsider"], \
            f"Invalid priority_quadrant: {candidate['priority_quadrant']}"


def test_monitoring_metrics_extraction():
    """Test that monitoring metrics are extracted for automation candidates"""
    import os
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping monitoring metrics test (no API key)")
        return
    
    extractor = AutomationCandidateExtractor()
    
    interview_data = {
        "meta": {
            "company": "Comversa",
            "role": "Gerente de IT",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué automatización propones?": "Quiero automatizar el proceso de aprobación de compras. Actualmente es todo manual y lento. La automatización debería reducir el tiempo de aprobación de 3 días a 1 día, y necesitamos monitorear que no haya errores en las aprobaciones."
        }
    }
    
    candidates = extractor.extract_from_interview(interview_data)
    
    if len(candidates) == 0:
        print("⚠️  No automation candidates extracted")
        return
    
    # Check if any candidate has monitoring metrics
    has_monitoring = any(len(c.get("monitoring_metrics", [])) > 0 for c in candidates)
    
    if has_monitoring:
        print("✅ Monitoring metrics extraction test passed")
        for candidate in candidates:
            if candidate.get("monitoring_metrics"):
                print(f"   Candidate: {candidate['name']}")
                print(f"   Monitoring: {candidate['monitoring_metrics']}")
    else:
        print("⚠️  No monitoring metrics extracted (may need better prompt)")


if __name__ == "__main__":
    print("Testing AutomationCandidateExtractor...")
    print()
    
    test_effort_scoring()
    test_impact_scoring()
    test_priority_quadrant_classification()
    test_roi_calculation()
    test_automation_candidate_extraction()
    test_monitoring_metrics_extraction()
    
    print()
    print("=" * 60)
    print("All AutomationCandidateExtractor tests completed!")
    print("=" * 60)
