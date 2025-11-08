"""
Integration tests for full extraction pipeline
Tests end-to-end extraction from interviews to database
"""
import pytest
import json
import sqlite3
import os
from pathlib import Path
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.extractors import (
    CommunicationChannelExtractor,
    DecisionPointExtractor,
    DataFlowExtractor,
    TemporalPatternExtractor,
    FailureModeExtractor,
    EnhancedPainPointExtractor,
    SystemExtractor,
    AutomationCandidateExtractor
)


@pytest.fixture
def temp_db():
    """Create temporary database for testing"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_intelligence.db"
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_v2_schema()
    
    yield db
    
    # Cleanup
    db.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_interview():
    """Sample interview data for testing"""
    return {
        "meta": {
            "company": "Hotel Los Tajibos",
            "respondent": "Test Manager",
            "role": "Gerente de Operaciones",
            "date": "2024-11-07",
            "business_unit": "Hospitality"
        },
        "qa_pairs": {
            "¿Qué herramientas utilizas?": "Uso WhatsApp para comunicación urgente, Opera para reservas, y SAP para contabilidad. Tengo problemas con la conciliación manual entre sistemas.",
            "¿Cuáles son tus principales desafíos?": "El mayor problema es la falta de integración entre sistemas. Paso 2 horas diarias haciendo conciliación manual. Es crítico y urgente resolver esto.",
            "¿Cómo tomas decisiones?": "Yo decido sobre mantenimiento hasta $5000. Si es más, escalo al Gerente General. Las decisiones urgentes las tomo inmediatamente.",
            "¿Cuándo realizas tus tareas?": "Hago la conciliación diaria a las 9am. Toma aproximadamente 2 horas. También tenemos reuniones semanales los lunes.",
            "¿Qué falla frecuentemente?": "El sistema Opera se cae semanalmente. Cuando falla, perdemos reservas y tenemos que llamar a soporte. Tarda 2 horas en resolverse."
        }
    }


def test_full_pipeline_with_sample_interview(temp_db, sample_interview):
    """Test complete extraction pipeline with sample interview"""
    import os
    
    # Skip if no API key (LLM extraction requires it)
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set, skipping LLM extraction test")
    
    # Insert interview
    interview_id = temp_db.insert_interview(
        sample_interview["meta"],
        sample_interview["qa_pairs"]
    )
    
    assert interview_id is not None
    assert interview_id > 0
    
    # Extract with all extractors
    extractors = {
        "CommunicationChannel": CommunicationChannelExtractor(),
        "DecisionPoint": DecisionPointExtractor(),
        "DataFlow": DataFlowExtractor(),
        "TemporalPattern": TemporalPatternExtractor(),
        "FailureMode": FailureModeExtractor(),
        "PainPoint": EnhancedPainPointExtractor(),
        "System": SystemExtractor(),
        "AutomationCandidate": AutomationCandidateExtractor()
    }
    
    company = sample_interview["meta"]["company"]
    business_unit = sample_interview["meta"]["business_unit"]
    
    extraction_results = {}
    
    for entity_name, extractor in extractors.items():
        entities = extractor.extract_from_interview(sample_interview)
        extraction_results[entity_name] = entities
        
        # Store in database
        for entity in entities:
            if entity_name == "CommunicationChannel":
                temp_db.insert_communication_channel(interview_id, company, business_unit, entity)
            elif entity_name == "DecisionPoint":
                temp_db.insert_decision_point(interview_id, company, business_unit, entity)
            elif entity_name == "DataFlow":
                temp_db.insert_data_flow(interview_id, company, business_unit, entity)
            elif entity_name == "TemporalPattern":
                temp_db.insert_temporal_pattern(interview_id, company, business_unit, entity)
            elif entity_name == "FailureMode":
                temp_db.insert_failure_mode(interview_id, company, business_unit, entity)
            elif entity_name == "PainPoint":
                temp_db.insert_enhanced_pain_point(interview_id, company, business_unit, entity)
            elif entity_name == "System":
                temp_db.insert_enhanced_system(interview_id, company, business_unit, entity)
            elif entity_name == "AutomationCandidate":
                temp_db.insert_enhanced_automation_candidate(interview_id, company, business_unit, entity)
    
    # Verify extraction results (at least some entities should be extracted)
    total_entities = sum(len(entities) for entities in extraction_results.values())
    assert total_entities > 0, "Should extract at least some entities"
    
    # Verify database storage
    cursor = temp_db.conn.cursor()
    
    # Check interviews table
    cursor.execute("SELECT COUNT(*) FROM interviews")
    assert cursor.fetchone()[0] == 1


def test_batch_processing_simulation(temp_db):
    """Test batch processing with multiple interviews"""
    
    # Create 3 sample interviews
    interviews = []
    for i in range(3):
        interviews.append({
            "meta": {
                "company": f"Company {i+1}",
                "respondent": f"Manager {i+1}",
                "role": f"Role {i+1}",
                "date": "2024-11-07",
                "business_unit": "Operations"
            },
            "qa_pairs": {
                "Question 1": f"Answer from interview {i+1}",
                "Question 2": "We use WhatsApp for communication"
            }
        })
    
    # Process each interview
    interview_ids = []
    for interview in interviews:
        interview_id = temp_db.insert_interview(
            interview["meta"],
            interview["qa_pairs"]
        )
        interview_ids.append(interview_id)
        
        # Extract communication channels
        extractor = CommunicationChannelExtractor()
        channels = extractor.extract_from_interview(interview)
        
        for channel in channels:
            temp_db.insert_communication_channel(
                interview_id,
                interview["meta"]["company"],
                interview["meta"]["business_unit"],
                channel
            )
    
    # Verify all interviews stored
    cursor = temp_db.conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM interviews")
    assert cursor.fetchone()[0] == 3
    
    # Verify interview IDs are unique
    assert len(set(interview_ids)) == 3
    assert all(id > 0 for id in interview_ids)


def test_error_handling_and_recovery(temp_db, sample_interview):
    """Test pipeline handles errors gracefully"""
    
    # Insert interview
    interview_id = temp_db.insert_interview(
        sample_interview["meta"],
        sample_interview["qa_pairs"]
    )
    
    # Try to insert invalid entity (missing required fields)
    invalid_channel = {
        "channel_name": "WhatsApp"
        # Missing other required fields
    }
    
    # Should not crash, should handle gracefully
    try:
        temp_db.insert_communication_channel(
            interview_id,
            sample_interview["meta"]["company"],
            sample_interview["meta"]["business_unit"],
            invalid_channel
        )
        # If it succeeds, that's fine (defaults are used)
    except Exception as e:
        # If it fails, that's also acceptable
        assert "required" in str(e).lower() or "constraint" in str(e).lower()


def test_confidence_scoring_stored(temp_db, sample_interview):
    """Test that confidence scores are properly stored"""
    import os
    
    # Skip if no API key (LLM extraction requires it)
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set, skipping LLM extraction test")
    
    interview_id = temp_db.insert_interview(
        sample_interview["meta"],
        sample_interview["qa_pairs"]
    )
    
    # Extract pain points (has confidence scoring)
    extractor = EnhancedPainPointExtractor()
    pain_points = extractor.extract_from_interview(sample_interview)
    
    # If no pain points extracted, that's okay for this test
    if len(pain_points) == 0:
        pytest.skip("No pain points extracted from sample interview")
    
    for pain_point in pain_points:
        temp_db.insert_enhanced_pain_point(
            interview_id,
            sample_interview["meta"]["company"],
            sample_interview["meta"]["business_unit"],
            pain_point
        )
    
    # Verify confidence scores stored
    cursor = temp_db.conn.cursor()
    cursor.execute("""
        SELECT confidence_score, needs_review 
        FROM pain_points
        WHERE confidence_score IS NOT NULL
    """)
    
    results = cursor.fetchall()
    assert len(results) > 0, "Should have pain points with confidence scores"
    
    for confidence, needs_review in results:
        assert 0.0 <= confidence <= 1.0, "Confidence should be between 0 and 1"
        assert needs_review in (0, 1), "needs_review should be boolean"


def test_company_filtering(temp_db):
    """Test that company-specific queries work"""
    
    # Insert interviews for different companies
    companies = ["Hotel Los Tajibos", "Comversa", "Bolivian Foods"]
    
    for company in companies:
        interview = {
            "meta": {
                "company": company,
                "respondent": f"Manager at {company}",
                "role": "Manager",
                "date": "2024-11-07",
                "business_unit": "Operations"
            },
            "qa_pairs": {
                "Question": "We use WhatsApp"
            }
        }
        
        interview_id = temp_db.insert_interview(interview["meta"], interview["qa_pairs"])
        
        # Extract and store a channel
        extractor = CommunicationChannelExtractor()
        channels = extractor.extract_from_interview(interview)
        
        for channel in channels:
            temp_db.insert_communication_channel(
                interview_id,
                company,
                interview["meta"]["business_unit"],
                channel
            )
    
    # Query by company
    cursor = temp_db.conn.cursor()
    
    for company in companies:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM communication_channels 
            WHERE company_name = ?
        """, (company,))
        
        count = cursor.fetchone()[0]
        assert count > 0, f"Should have channels for {company}"


def test_extraction_with_real_interview_structure():
    """Test extraction with actual interview JSON structure"""
    
    # Load a real interview if available
    interviews_path = Path("data/interviews/analysis_output/all_interviews.json")
    
    if not interviews_path.exists():
        pytest.skip("Real interview data not available")
    
    with open(interviews_path, 'r', encoding='utf-8') as f:
        interviews = json.load(f)
    
    if len(interviews) == 0:
        pytest.skip("No interviews in file")
    
    # Test with first interview
    interview = interviews[0]
    
    # Verify structure
    assert "meta" in interview
    assert "qa_pairs" in interview
    assert "role" in interview["meta"]
    
    # Test extraction
    extractor = CommunicationChannelExtractor()
    channels = extractor.extract_from_interview(interview)
    
    # Should extract something (or empty list is valid)
    assert isinstance(channels, list)
    
    if len(channels) > 0:
        # Verify channel structure
        channel = channels[0]
        assert "channel_name" in channel
        assert "confidence_score" in channel
        assert 0.0 <= channel["confidence_score"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
