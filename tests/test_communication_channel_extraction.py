"""
Unit tests for CommunicationChannel extraction
Tests extraction logic with real interview data
"""
import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.extractors import CommunicationChannelExtractor, normalize_sla_to_minutes


class TestCommunicationChannelExtraction(unittest.TestCase):
    """Test communication channel extraction logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Skip LLM tests if no API key
        self.skip_llm = not Path(__file__).parent.parent.joinpath(".env").exists()
        
        # Sample interview data
        self.sample_interview = {
            "meta": {
                "company": "Hotel Los Tajibos",
                "respondent": "Test User",
                "role": "Gerente de Ingeniería",
                "date": "2024-11-07"
            },
            "qa_pairs": {
                "¿Qué herramientas utilizas?": "Uso WhatsApp para coordinación diaria con el equipo y Outlook para solicitudes formales. También tenemos reuniones semanales.",
                "¿Cómo te comunicas?": "WhatsApp es para todo lo urgente, respondo inmediato. Outlook para cosas que pueden esperar hasta el mismo día."
            }
        }
    
    def test_rule_based_extraction(self):
        """Test rule-based channel extraction"""
        extractor = CommunicationChannelExtractor()
        
        text = "Uso WhatsApp para coordinación diaria y Outlook para solicitudes formales"
        meta = {"role": "Gerente"}
        
        channels = extractor._rule_based_extraction(text, meta)
        
        # Should find WhatsApp and Outlook
        channel_names = [c["channel_name"] for c in channels]
        self.assertIn("WhatsApp", channel_names)
        self.assertIn("Outlook", channel_names)
        
        print(f"\n✅ Rule-based extraction found {len(channels)} channels:")
        for channel in channels:
            print(f"  - {channel['channel_name']}: {channel['purpose']}")
    
    def test_sla_extraction(self):
        """Test SLA extraction from text"""
        extractor = CommunicationChannelExtractor()
        
        test_cases = [
            ("respondo inmediato", 15),
            ("mismo día", 480),
            ("24 horas", 1440),
            ("urgente", 30),
        ]
        
        for text, expected_minutes in test_cases:
            sla = extractor._extract_sla(text, "WhatsApp")
            self.assertEqual(sla, expected_minutes, f"SLA for '{text}' should be {expected_minutes} minutes")
        
        print(f"\n✅ SLA extraction working correctly")
    
    def test_frequency_inference(self):
        """Test frequency inference"""
        extractor = CommunicationChannelExtractor()
        
        test_cases = [
            ("uso diario", "Daily"),
            ("reuniones semanales", "Weekly"),
            ("todo el tiempo", "Continuous"),
            ("cuando es necesario", "As needed"),
        ]
        
        for text, expected_freq in test_cases:
            freq = extractor._infer_frequency(text, "WhatsApp")
            self.assertEqual(freq, expected_freq, f"Frequency for '{text}' should be {expected_freq}")
        
        print(f"\n✅ Frequency inference working correctly")
    
    def test_pain_point_extraction(self):
        """Test pain point extraction"""
        extractor = CommunicationChannelExtractor()
        
        text = "WhatsApp tiene pérdida de trazabilidad y la información dispersa es un problema"
        pain_points = extractor._extract_pain_points(text, "WhatsApp")
        
        self.assertGreater(len(pain_points), 0, "Should find pain points")
        self.assertTrue(any("trazabilidad" in pp.lower() for pp in pain_points))
        
        print(f"\n✅ Pain point extraction found: {pain_points}")
    
    def test_normalize_sla_to_minutes(self):
        """Test SLA normalization function"""
        test_cases = [
            ("15 minutos", 15),
            ("2 horas", 120),
            ("1 día", 1440),
            ("mismo día", 480),
            ("inmediato", 15),
            ("24 horas", 1440),
        ]
        
        for text, expected in test_cases:
            result = normalize_sla_to_minutes(text)
            self.assertEqual(result, expected, f"'{text}' should normalize to {expected} minutes")
        
        print(f"\n✅ SLA normalization working for all test cases")
    
    def test_channel_deduplication(self):
        """Test that duplicate channels are merged"""
        extractor = CommunicationChannelExtractor()
        
        rule_based = [
            {"channel_name": "WhatsApp", "confidence_score": 0.7, "pain_points": ["Pérdida de trazabilidad"]}
        ]
        
        llm_based = [
            {"channel_name": "WhatsApp", "confidence_score": 0.9, "pain_points": ["Información dispersa"]}
        ]
        
        merged = extractor._merge_channels(rule_based, llm_based)
        
        self.assertEqual(len(merged), 1, "Should merge duplicate channels")
        self.assertEqual(merged[0]["confidence_score"], 0.9, "Should keep higher confidence")
        self.assertEqual(len(merged[0]["pain_points"]), 2, "Should merge pain points")
        
        print(f"\n✅ Channel deduplication working correctly")


class TestRealInterviewExtraction(unittest.TestCase):
    """Test extraction with real interview data"""
    
    def setUp(self):
        """Load real interview data"""
        interviews_path = Path(__file__).parent.parent / "data" / "interviews" / "analysis_output" / "all_interviews.json"
        
        if not interviews_path.exists():
            self.skipTest("Real interview data not found")
        
        with open(interviews_path, 'r', encoding='utf-8') as f:
            self.interviews = json.load(f)
        
        # Skip LLM tests if no API key
        self.skip_llm = not Path(__file__).parent.parent.joinpath(".env").exists()
    
    def test_extract_from_engineering_manager_interview(self):
        """Test extraction from Gerente de Ingeniería interview"""
        # First interview is from Gerente de Ingeniería
        interview = self.interviews[0]
        
        extractor = CommunicationChannelExtractor()
        
        # Test rule-based extraction only (no API key needed)
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        channels = extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Gerente de Ingeniería interview:")
        print(f"  Total channels found: {len(channels)}")
        
        # Should find WhatsApp, Outlook (communication channels)
        # Note: Excel, AutoCAD, MaintainX are tools/systems, not communication channels
        channel_names = [c["channel_name"] for c in channels]
        
        self.assertIn("WhatsApp", channel_names, "Should find WhatsApp")
        self.assertIn("Outlook", channel_names, "Should find Outlook")
        
        for channel in channels:
            print(f"\n  Channel: {channel['channel_name']}")
            print(f"    Purpose: {channel['purpose']}")
            print(f"    Frequency: {channel['frequency']}")
            if channel['pain_points']:
                print(f"    Pain points: {', '.join(channel['pain_points'])}")
    
    def test_extract_from_accounting_manager_interview(self):
        """Test extraction from Gerente de Contabilidad interview"""
        # Second interview is from Gerente de Contabilidad
        interview = self.interviews[1]
        
        extractor = CommunicationChannelExtractor()
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        channels = extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Gerente de Contabilidad interview:")
        print(f"  Total channels found: {len(channels)}")
        
        # Should find systems mentioned (Simphony, Micros, Opera, SAP, Satcom)
        # Note: These are systems, not communication channels, but extractor might pick them up
        
        for channel in channels:
            print(f"  - {channel['channel_name']}: {channel['purpose']}")
    
    def test_extract_from_it_analyst_interview(self):
        """Test extraction from Analista TI interview"""
        # Third interview is from Analista TI
        interview = self.interviews[2]
        
        extractor = CommunicationChannelExtractor()
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        channels = extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Analista TI interview:")
        print(f"  Total channels found: {len(channels)}")
        
        # Should find Jira, SharePoint, Power Automate, etc.
        channel_names = [c["channel_name"] for c in channels]
        
        self.assertIn("Jira", channel_names, "Should find Jira")
        self.assertIn("SharePoint", channel_names, "Should find SharePoint")
        
        for channel in channels:
            print(f"  - {channel['channel_name']}: {channel['purpose']}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
