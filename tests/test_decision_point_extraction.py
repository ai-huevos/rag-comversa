"""
Unit tests for DecisionPoint extraction
Tests extraction of decision-making logic and escalation flows
"""
import unittest
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.extractors import DecisionPointExtractor


class TestDecisionPointExtraction(unittest.TestCase):
    """Test decision point extraction logic"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.extractor = DecisionPointExtractor()
    
    def test_decision_type_inference_from_role(self):
        """Test inferring decision type from role"""
        test_cases = [
            ("Gerente de Ingeniería", "priorizo las tareas", "Priorización de mantenimiento"),
            ("Gerente de Contabilidad", "apruebo los pagos", "Aprobación de pagos"),
            ("Jefe de Compras", "autorizo compras", "Aprobación de compras"),
            ("Chef Ejecutivo", "decido el menú", "Gestión de menú y producción"),
        ]
        
        for role, text, expected_type in test_cases:
            decision_type = self.extractor._infer_decision_type(text, role)
            self.assertIsNotNone(decision_type, f"Should infer decision type for {role}")
            print(f"  ✅ {role} → {decision_type}")
    
    def test_criteria_extraction(self):
        """Test extracting decision criteria"""
        text = "Evalúo basado en la criticidad, el impacto en el huésped, y la seguridad"
        criteria = self.extractor._extract_criteria(text)
        
        self.assertGreater(len(criteria), 0, "Should extract criteria")
        self.assertIn("Criticidad", criteria)
        self.assertIn("Impacto", criteria)
        self.assertIn("Seguridad", criteria)
        
        print(f"\n✅ Extracted criteria: {criteria}")
    
    def test_approval_required_detection(self):
        """Test detecting if approval is required"""
        test_cases = [
            ("Requiere aprobación del gerente", True),
            ("Necesita aprobación de finanzas", True),
            ("Yo decido directamente", False),
            ("Debe ser aprobado por el director", True),
        ]
        
        for text, expected in test_cases:
            result = self.extractor._check_approval_required(text)
            self.assertEqual(result, expected, f"Approval detection failed for: {text}")
        
        print(f"\n✅ Approval detection working correctly")
    
    def test_authority_limit_extraction(self):
        """Test extracting monetary authority limits"""
        test_cases = [
            ("Puedo aprobar hasta $5000", 5000.0),
            ("Mi límite de autorización es $10,000", 10000.0),
            ("Tengo autoridad de $2,500", 2500.0),
        ]
        
        for text, expected in test_cases:
            result = self.extractor._extract_authority_limit(text)
            self.assertEqual(result, expected, f"Authority limit extraction failed for: {text}")
        
        print(f"\n✅ Authority limit extraction working correctly")
    
    def test_escalation_trigger_extraction(self):
        """Test extracting escalation triggers"""
        test_cases = [
            "Escalo cuando afecta seguridad",
            "Elevo si supera el presupuesto",
            "Consulto en caso de alto impacto"
        ]
        
        for text in test_cases:
            trigger = self.extractor._extract_escalation_trigger(text)
            self.assertIsNotNone(trigger, f"Should extract escalation trigger from: {text}")
            print(f"  ✅ Trigger: {trigger}")
    
    def test_escalation_target_extraction(self):
        """Test extracting escalation targets"""
        test_cases = [
            ("Escalo al Gerente General", "Gerente General"),
            ("Consulto con el Director", "Director"),
            ("Reporto a mi jefe inmediato", "Jefe Inmediato"),
        ]
        
        for text, expected_role in test_cases:
            target = self.extractor._extract_escalation_target(text)
            self.assertIsNotNone(target, f"Should extract escalation target from: {text}")
            print(f"  ✅ {text} → {target}")
    
    def test_related_process_inference(self):
        """Test inferring related process"""
        test_cases = [
            ("Gerente de Ingeniería", "gestiono el mantenimiento", "Gestión de mantenimiento"),
            ("Gerente de Contabilidad", "proceso los pagos", "Gestión de pagos"),  # Text has "pagos" so should return "Gestión de pagos"
            ("Gerente de Contabilidad", "gestiono la contabilidad", "Gestión contable"),  # No "pagos" in text, returns role-based
            ("Jefe de Compras", "autorizo las compras", "Gestión de compras"),
        ]
        
        for role, text, expected_process in test_cases:
            process = self.extractor._infer_related_process(text, role)
            self.assertEqual(process, expected_process, f"Process inference failed for {role} with text '{text}'")
        
        print(f"\n✅ Process inference working correctly")


class TestRealInterviewDecisionExtraction(unittest.TestCase):
    """Test extraction with real interview data"""
    
    def setUp(self):
        """Load real interview data"""
        interviews_path = Path(__file__).parent.parent / "data" / "interviews" / "analysis_output" / "all_interviews.json"
        
        if not interviews_path.exists():
            self.skipTest("Real interview data not found")
        
        with open(interviews_path, 'r', encoding='utf-8') as f:
            self.interviews = json.load(f)
        
        self.extractor = DecisionPointExtractor()
    
    def test_extract_from_engineering_manager(self):
        """Test extraction from Gerente de Ingeniería interview"""
        interview = self.interviews[0]
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        decisions = self.extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Gerente de Ingeniería:")
        print(f"  Total decision points: {len(decisions)}")
        
        if decisions:
            for decision in decisions:
                print(f"\n  Decision Type: {decision['decision_type']}")
                print(f"    Decision Maker: {decision['decision_maker_role']}")
                if decision['decision_criteria']:
                    print(f"    Criteria: {', '.join(decision['decision_criteria'])}")
                if decision['escalation_trigger']:
                    print(f"    Escalation Trigger: {decision['escalation_trigger']}")
                if decision['escalation_to_role']:
                    print(f"    Escalates To: {decision['escalation_to_role']}")
        
        self.assertGreater(len(decisions), 0, "Should extract at least one decision point")
    
    def test_extract_from_accounting_manager(self):
        """Test extraction from Gerente de Contabilidad interview"""
        interview = self.interviews[1]
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in interview['qa_pairs'].items()])
        decisions = self.extractor._rule_based_extraction(text, interview['meta'])
        
        print(f"\n📋 Extracted from Gerente de Contabilidad:")
        print(f"  Total decision points: {len(decisions)}")
        
        for decision in decisions:
            print(f"  - {decision['decision_type']}")
            if decision['decision_criteria']:
                print(f"    Criteria: {', '.join(decision['decision_criteria'])}")
    
    def test_extract_from_chef(self):
        """Test extraction from Chef Ejecutivo interview"""
        # Find chef interview
        chef_interview = None
        for interview in self.interviews:
            if "chef" in interview['meta'].get('role', '').lower():
                chef_interview = interview
                break
        
        if not chef_interview:
            self.skipTest("Chef interview not found")
        
        text = "\n\n".join([f"Q: {q}\nA: {a}" for q, a in chef_interview['qa_pairs'].items()])
        decisions = self.extractor._rule_based_extraction(text, chef_interview['meta'])
        
        print(f"\n📋 Extracted from Chef Ejecutivo:")
        print(f"  Total decision points: {len(decisions)}")
        
        for decision in decisions:
            print(f"  - {decision['decision_type']}")
            print(f"    Related Process: {decision['related_process']}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
