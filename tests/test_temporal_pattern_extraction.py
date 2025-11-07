"""
Unit tests for TemporalPattern extraction
Tests extraction of when activities happen, how often, and duration
"""
import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.extractors import TemporalPatternExtractor


class TestTemporalPatternExtraction(unittest.TestCase):
    """Test temporal pattern extraction logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = TemporalPatternExtractor()
    
    def test_time_normalization(self):
        """Test time normalization to 24-hour format"""
        test_cases = [
            ("9am", "09:00"),
            ("2pm", "14:00"),
            ("12pm", "12:00"),
            ("12am", "00:00"),
            ("9:30am", "09:30"),
            ("3:45pm", "15:45"),
            ("a las 9", "09:00"),
        ]
        
        for input_time, expected in test_cases:
            result = self.extractor._normalize_time(input_time)
            self.assertEqual(result, expected, f"Time '{input_time}' should normalize to {expected}")
        
        print(f"\n✅ Time normalization working correctly")
    
    def test_frequency_detection(self):
        """Test frequency detection from text"""
        test_cases = [
            ("Reunión diaria a las 9am", "Daily"),
            ("Cierre mensual el último día", "Monthly"),
            ("Revisión semanal cada viernes", "Weekly"),
            ("Reporte anual de resultados", "Annually"),
        ]
        
        for text, expected_freq in test_cases:
            # Check if frequency keyword is detected
            found = False
            for freq, keywords in self.extractor.FREQUENCY_KEYWORDS.items():
                if any(keyword in text.lower() for keyword in keywords):
                    if freq == expected_freq:
                        found = True
                        break
            
            self.assertTrue(found, f"Should detect {expected_freq} frequency in '{text}'")
        
        print(f"\n✅ Frequency detection working correctly")
    
    def test_related_process_inference(self):
        """Test inferring related process"""
        test_cases = [
            ("Gerente de Ingeniería", "reunión de mantenimiento", "Gestión de mantenimiento"),
            ("Contador", "cierre mensual", "Cierre mensual"),
            ("Gerente", "reporte semanal", "Generación de reportes"),
        ]
        
        for role, text, expected_process in test_cases:
            process = self.extractor._infer_related_process(text, role)
            self.assertIsNotNone(process, f"Should infer process for '{text}'")
            print(f"  ✅ {text} → {process}")
    
    def test_pattern_deduplication(self):
        """Test that duplicate patterns are merged"""
        rule_based = [
            {
                "activity_name": "Reunión diaria",
                "frequency": "Daily",
                "confidence_score": 0.7,
                "participants": ["Gerente"],
                "triggers_actions": []
            }
        ]
        
        llm_based = [
            {
                "activity_name": "Reunión diaria",
                "frequency": "Daily",
                "confidence_score": 0.9,
                "participants": ["Gerente", "Equipo"],
                "triggers_actions": ["Asignación de tareas"]
            }
        ]
        
        merged = self.extractor._merge_patterns(rule_based, llm_based)
        
        self.assertEqual(len(merged), 1, "Should merge duplicate patterns")
        self.assertEqual(merged[0]["confidence_score"], 0.9, "Should keep higher confidence")
        self.assertEqual(len(merged[0]["participants"]), 2, "Should merge participants")
        
        print(f"\n✅ Pattern deduplication working correctly")


class TestRealInterviewExtraction(unittest.TestCase):
    """Test extraction with real interview data"""
    
    def setUp(self):
        """Load real interview data"""
        interviews_path = Path(__file__).parent.parent / "data" / "interviews" / "analysis_output" / "all_interviews.json"
        
        if not interviews_path.exists():
            self.skipTest("Real interview data not found")
        
        with open(interviews_path, 'r', encoding='utf-8') as f:
            self.interviews = json.load(f)
        
        self.extractor = TemporalPatternExtractor()
    
    def test_extract_from_engineering_manager(self):
        """Test extraction from Gerente de Ingeniería interview"""
        interview = self.interviews[0]
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        patterns = self.extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Gerente de Ingeniería (rule-based):")
        print(f"  Total temporal patterns: {len(patterns)}")
        
        for pattern in patterns:
            print(f"  - {pattern['activity_name']}: {pattern['frequency']}")
            if pattern.get('time_of_day'):
                print(f"    Time: {pattern['time_of_day']}")
    
    def test_full_extraction_pipeline(self):
        """Test full extraction pipeline on sample data"""
        sample_interview = {
            "meta": {
                "company": "Hotel Los Tajibos",
                "respondent": "Test User",
                "role": "Gerente de Operaciones",
                "date": "2024-11-07"
            },
            "qa_pairs": {
                "¿Cuándo se reúnen?": "Tenemos reuniones diarias a las 9am con todos los jefes de área. Dura 30 minutos.",
                "¿Qué otros procesos tienen?": "El cierre mensual lo hacemos el último día del mes. También revisamos inventario cada semana los viernes."
            }
        }
        
        patterns = self.extractor.extract_from_interview(sample_interview)
        
        print(f"\n📋 Full extraction pipeline test:")
        print(f"  Total patterns extracted: {len(patterns)}")
        
        for pattern in patterns:
            print(f"\n  Pattern: {pattern['activity_name']}")
            print(f"    Frequency: {pattern['frequency']}")
            if pattern.get('time_of_day'):
                print(f"    Time: {pattern['time_of_day']}")
            if pattern.get('duration_minutes'):
                print(f"    Duration: {pattern['duration_minutes']} minutes")
            print(f"    Confidence: {pattern['confidence_score']}")
            print(f"    Source: {pattern['extraction_source']}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
