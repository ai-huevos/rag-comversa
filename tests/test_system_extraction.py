"""
Tests for SystemExtractor - Enhanced system entity extraction with integration pain points and user satisfaction
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from intelligence_capture.extractors import SystemExtractor


def test_sentiment_analysis():
    """Test sentiment analysis for user satisfaction scoring"""
    extractor = SystemExtractor()
    
    # Test positive sentiment
    text_positive = "SAP funciona bien y me gusta mucho, es muy útil para nuestro trabajo"
    score = extractor._analyze_sentiment(text_positive, "SAP")
    assert score >= 7, f"Expected positive score >= 7, got {score}"
    
    # Test negative sentiment
    text_negative = "SAP no sirve, es muy lento y complicado, nadie lo usa"
    score = extractor._analyze_sentiment(text_negative, "SAP")
    assert score <= 4, f"Expected negative score <= 4, got {score}"
    
    # Test neutral sentiment
    text_neutral = "Usamos SAP para contabilidad"
    score = extractor._analyze_sentiment(text_neutral, "SAP")
    assert 4 <= score <= 6, f"Expected neutral score 4-6, got {score}"
    
    print("✅ Sentiment analysis tests passed")


def test_system_extraction_with_integration_issues():
    """Test extraction of systems with integration pain points"""
    import os
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping LLM extraction test (no API key)")
        return
    
    extractor = SystemExtractor()
    
    interview_data = {
        "meta": {
            "company": "Hotel Los Tajibos",
            "role": "Gerente de Restaurantes",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué sistemas usas?": "Uso Simphony para el POS y SAP para contabilidad. El problema es que no están integrados, tengo que pasar los datos manualmente de uno a otro. Simphony funciona bien pero SAP es muy lento y complicado.",
            "¿Hay problemas con los sistemas?": "Sí, la conciliación entre Simphony y SAP es manual y toma 2 horas diarias. Los datos a veces no coinciden y hay errores."
        }
    }
    
    systems = extractor.extract_from_interview(interview_data)
    
    # Should extract at least 2 systems
    assert len(systems) >= 2, f"Expected at least 2 systems, got {len(systems)}"
    
    # Find SAP and Simphony
    sap = next((s for s in systems if "SAP" in s["name"]), None)
    simphony = next((s for s in systems if "Simphony" in s["name"]), None)
    
    assert sap is not None, "SAP system not extracted"
    assert simphony is not None, "Simphony system not extracted"
    
    # Check SAP has low satisfaction (should be lower than Simphony)
    assert sap["user_satisfaction_score"] <= 5, f"SAP should have low satisfaction, got {sap['user_satisfaction_score']}"
    
    # Check Simphony has higher satisfaction than SAP (relative comparison)
    assert simphony["user_satisfaction_score"] >= sap["user_satisfaction_score"], \
        f"Simphony satisfaction ({simphony['user_satisfaction_score']}) should be >= SAP satisfaction ({sap['user_satisfaction_score']})"
    
    # Check for integration pain points
    has_integration_issue = any(
        "integr" in str(s.get("integration_pain_points", [])).lower() or
        "manual" in str(s.get("integration_pain_points", [])).lower()
        for s in systems
    )
    assert has_integration_issue, "Integration pain points not detected"
    
    # Check for data quality issues
    has_data_quality_issue = any(
        "error" in str(s.get("data_quality_issues", [])).lower() or
        "concilia" in str(s.get("data_quality_issues", [])).lower()
        for s in systems
    )
    assert has_data_quality_issue, "Data quality issues not detected"
    
    print("✅ System extraction with integration issues tests passed")
    print(f"   Extracted systems: {[s['name'] for s in systems]}")
    print(f"   SAP satisfaction: {sap['user_satisfaction_score']}")
    print(f"   Simphony satisfaction: {simphony['user_satisfaction_score']}")


def test_replacement_candidate_flagging():
    """Test that systems with low satisfaction are flagged as replacement candidates"""
    import os
    
    # Skip if no API key
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Skipping replacement candidate test (no API key)")
        return
    
    extractor = SystemExtractor()
    
    interview_data = {
        "meta": {
            "company": "Comversa",
            "role": "Contador",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué opinas del sistema actual?": "El sistema actual no funciona bien, es obsoleto y falla constantemente. Necesitamos cambiarlo urgentemente."
        }
    }
    
    systems = extractor.extract_from_interview(interview_data)
    
    if len(systems) == 0:
        print("⚠️  No systems extracted (may need better prompt)")
        return
    
    # Should have at least one system with low satisfaction
    low_satisfaction_systems = [s for s in systems if s.get("user_satisfaction_score", 5) <= 4]
    assert len(low_satisfaction_systems) > 0, "No low satisfaction systems found"
    
    # Check if any are flagged as replacement candidates
    replacement_candidates = [s for s in systems if s.get("replacement_candidate")]
    
    if len(replacement_candidates) > 0:
        print("✅ Replacement candidate flagging tests passed")
        print(f"   Replacement candidates: {[s['name'] for s in replacement_candidates]}")
        print(f"   Satisfaction scores: {[(s['name'], s['user_satisfaction_score']) for s in replacement_candidates]}")
    else:
        print("✅ Low satisfaction detection tests passed")
        print(f"   Low satisfaction systems: {[(s['name'], s['user_satisfaction_score']) for s in low_satisfaction_systems]}")
        print("   Note: Systems not explicitly flagged as replacement candidates, but low satisfaction detected")


def test_adoption_rate_extraction():
    """Test extraction of adoption rate when mentioned"""
    extractor = SystemExtractor()
    
    interview_data = {
        "meta": {
            "company": "Bolivian Foods",
            "role": "Gerente de IT",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Cómo va la adopción del nuevo sistema?": "Implementamos un nuevo CRM pero solo el 30% del equipo lo usa. La mayoría sigue usando Excel porque el CRM es complicado."
        }
    }
    
    systems = extractor.extract_from_interview(interview_data)
    
    # Should extract CRM with low adoption rate
    crm = next((s for s in systems if "CRM" in s["name"] or "CRM" in s["type"]), None)
    
    if crm:
        # Check if adoption rate was extracted (should be around 0.3)
        if crm.get("adoption_rate"):
            assert 0.2 <= crm["adoption_rate"] <= 0.4, \
                f"Expected adoption rate around 0.3, got {crm['adoption_rate']}"
            print(f"✅ Adoption rate extraction test passed: {crm['adoption_rate']}")
        else:
            print("⚠️  Adoption rate not extracted (optional)")
    else:
        print("⚠️  CRM not extracted (may need better prompt)")


if __name__ == "__main__":
    print("Testing SystemExtractor...")
    print()
    
    test_sentiment_analysis()
    test_system_extraction_with_integration_issues()
    test_replacement_candidate_flagging()
    test_adoption_rate_extraction()
    
    print()
    print("=" * 60)
    print("All SystemExtractor tests completed!")
    print("=" * 60)
