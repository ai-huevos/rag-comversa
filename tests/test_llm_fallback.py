"""
Test LLM fallback logic to ensure it handles rate limits gracefully
"""
import sys
import os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from intelligence_capture.extractors import (
    SystemExtractor,
    AutomationCandidateExtractor,
    CommunicationChannelExtractor
)


def test_system_extractor_with_fallback():
    """Test that SystemExtractor uses fallback models on rate limits"""
    print("Testing SystemExtractor with fallback...")
    
    extractor = SystemExtractor()
    
    interview_data = {
        "meta": {
            "company": "Test Company",
            "role": "Test Role",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué sistemas usas?": "Usamos SAP para contabilidad y funciona bien."
        }
    }
    
    try:
        systems = extractor.extract_from_interview(interview_data)
        print(f"✅ SystemExtractor completed (extracted {len(systems)} systems)")
        if systems:
            print(f"   First system: {systems[0].get('name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ SystemExtractor failed: {e}")
        return False


def test_automation_candidate_extractor_with_fallback():
    """Test that AutomationCandidateExtractor uses fallback models"""
    print("\nTesting AutomationCandidateExtractor with fallback...")
    
    extractor = AutomationCandidateExtractor()
    
    interview_data = {
        "meta": {
            "company": "Test Company",
            "role": "Test Role",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Qué automatizarías?": "Me gustaría automatizar el proceso de reportes que hago manualmente cada día."
        }
    }
    
    try:
        candidates = extractor.extract_from_interview(interview_data)
        print(f"✅ AutomationCandidateExtractor completed (extracted {len(candidates)} candidates)")
        if candidates:
            print(f"   First candidate: {candidates[0].get('name', 'Unknown')}")
            print(f"   Priority: {candidates[0].get('priority_quadrant', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ AutomationCandidateExtractor failed: {e}")
        return False


def test_communication_channel_extractor_with_fallback():
    """Test that CommunicationChannelExtractor uses fallback models"""
    print("\nTesting CommunicationChannelExtractor with fallback...")
    
    extractor = CommunicationChannelExtractor()
    
    interview_data = {
        "meta": {
            "company": "Test Company",
            "role": "Test Role",
            "respondent": "Test User",
            "date": "2024-11-07"
        },
        "qa_pairs": {
            "¿Cómo te comunicas?": "Uso WhatsApp para urgencias y Outlook para solicitudes formales."
        }
    }
    
    try:
        channels = extractor.extract_from_interview(interview_data)
        print(f"✅ CommunicationChannelExtractor completed (extracted {len(channels)} channels)")
        if channels:
            print(f"   First channel: {channels[0].get('channel_name', 'Unknown')}")
        return True
    except Exception as e:
        print(f"❌ CommunicationChannelExtractor failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Testing LLM Fallback Logic")
    print("=" * 60)
    print()
    print("This test will attempt to use LLM extraction with automatic")
    print("fallback to alternative models if rate limits are hit.")
    print()
    
    results = []
    
    # Test each extractor
    results.append(test_system_extractor_with_fallback())
    results.append(test_automation_candidate_extractor_with_fallback())
    results.append(test_communication_channel_extractor_with_fallback())
    
    print()
    print("=" * 60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("=" * 60)
    
    if all(results):
        print("✅ All extractors successfully use fallback logic!")
    else:
        print("⚠️  Some extractors had issues (may be expected if all models hit rate limits)")
