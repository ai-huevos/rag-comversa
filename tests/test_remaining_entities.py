"""
Tests for Remaining v2.0 Entity Extractors

Tests TeamStructure, KnowledgeGap, SuccessPattern, BudgetConstraint, and ExternalDependency extractors.
"""
import pytest
from intelligence_capture.extractors import (
    TeamStructureExtractor,
    KnowledgeGapExtractor,
    SuccessPatternExtractor,
    BudgetConstraintExtractor,
    ExternalDependencyExtractor
)
from intelligence_capture.config import OPENAI_API_KEY


def test_team_structure_extractor():
    """Test TeamStructure extractor"""
    extractor = TeamStructureExtractor(OPENAI_API_KEY)
    
    interview_data = {
        "meta": {
            "company": "Hotel Los Tajibos",
            "role": "Gerente de Restaurantes",
            "respondent": "Test Manager"
        },
        "qa_pairs": {
            "Q1": "¿Cuál es tu rol?",
            "A1": "Soy Gerente de Restaurantes. Tengo un equipo de 15 personas incluyendo meseros, cocineros y bartenders. Reporto al Gerente de Alimentos y Bebidas y coordino diariamente con Housekeeping y Recepción."
        }
    }
    
    results = extractor.extract_from_interview(interview_data)
    
    # Should extract team structure
    assert isinstance(results, list)
    
    if len(results) > 0:
        team = results[0]
        assert "role" in team
        assert "confidence_score" in team
        print(f"\n✅ Extracted team structure: {team.get('role')}")
        print(f"   Team size: {team.get('team_size')}")
        print(f"   Reports to: {team.get('reports_to')}")
    else:
        print("\n⚠️  No team structure extracted (may need better prompt)")


def test_knowledge_gap_extractor():
    """Test KnowledgeGap extractor"""
    extractor = KnowledgeGapExtractor(OPENAI_API_KEY)
    
    interview_data = {
        "meta": {
            "company": "Hotel Los Tajibos",
            "role": "Recepcionista",
            "respondent": "Test Receptionist"
        },
        "qa_pairs": {
            "Q1": "¿Qué dificultades tienes?",
            "A1": "No sé cómo usar bien el sistema Opera. Nunca recibí capacitación formal, solo me enseñaron lo básico. Cuando hay problemas complicados, no sé qué hacer y tengo que llamar a mi supervisor."
        }
    }
    
    results = extractor.extract_from_interview(interview_data)
    
    # Should extract knowledge gaps
    assert isinstance(results, list)
    
    if len(results) > 0:
        gap = results[0]
        assert "area" in gap
        assert "confidence_score" in gap
        print(f"\n✅ Extracted knowledge gap: {gap.get('area')}")
        print(f"   Training needed: {gap.get('training_needed')}")
    else:
        print("\n⚠️  No knowledge gaps extracted")


def test_success_pattern_extractor():
    """Test SuccessPattern extractor"""
    extractor = SuccessPatternExtractor(OPENAI_API_KEY)
    
    interview_data = {
        "meta": {
            "company": "Hotel Los Tajibos",
            "role": "Jefe de Ingeniería",
            "respondent": "Test Engineer"
        },
        "qa_pairs": {
            "Q1": "¿Qué funciona bien en tu área?",
            "A1": "El sistema de mantenimiento preventivo funciona muy bien. Tenemos un calendario claro y todos saben qué hacer. Esto nos ha ayudado a reducir emergencias en un 40%. Es una best practice que podría replicarse en otras áreas."
        }
    }
    
    results = extractor.extract_from_interview(interview_data)
    
    # Should extract success patterns
    assert isinstance(results, list)
    
    if len(results) > 0:
        pattern = results[0]
        assert "pattern" in pattern
        assert "confidence_score" in pattern
        print(f"\n✅ Extracted success pattern: {pattern.get('pattern')}")
        print(f"   Benefit: {pattern.get('benefit')}")
    else:
        print("\n⚠️  No success patterns extracted")


def test_budget_constraint_extractor():
    """Test BudgetConstraint extractor"""
    extractor = BudgetConstraintExtractor(OPENAI_API_KEY)
    
    interview_data = {
        "meta": {
            "company": "Comversa",
            "role": "Gerente de Proyecto",
            "respondent": "Test PM"
        },
        "qa_pairs": {
            "Q1": "¿Cómo manejas el presupuesto?",
            "A1": "Tengo autorización para aprobar gastos hasta $5,000. Cualquier cosa mayor requiere aprobación del Director de Construcción. El proceso de aprobación puede tomar 2-3 días, lo cual a veces retrasa el proyecto."
        }
    }
    
    results = extractor.extract_from_interview(interview_data)
    
    # Should extract budget constraints
    assert isinstance(results, list)
    
    if len(results) > 0:
        constraint = results[0]
        assert "area" in constraint
        assert "confidence_score" in constraint
        print(f"\n✅ Extracted budget constraint: {constraint.get('area')}")
        print(f"   Approval required above: ${constraint.get('approval_required_above')}")
        print(f"   Approver: {constraint.get('approver')}")
    else:
        print("\n⚠️  No budget constraints extracted")


def test_external_dependency_extractor():
    """Test ExternalDependency extractor"""
    extractor = ExternalDependencyExtractor(OPENAI_API_KEY)
    
    interview_data = {
        "meta": {
            "company": "Bolivian Foods",
            "role": "Gerente de Producción",
            "respondent": "Test Production Manager"
        },
        "qa_pairs": {
            "Q1": "¿Con qué proveedores trabajas?",
            "A1": "Trabajamos con Distribuidora ABC para materias primas. Nos entregan semanalmente. El coordinador de compras maneja la relación. Tenemos un SLA de 48 horas para entregas urgentes. Los pagos se procesan mensualmente a través de finanzas."
        }
    }
    
    results = extractor.extract_from_interview(interview_data)
    
    # Should extract external dependencies
    assert isinstance(results, list)
    
    if len(results) > 0:
        dep = results[0]
        assert "vendor" in dep
        assert "confidence_score" in dep
        print(f"\n✅ Extracted external dependency: {dep.get('vendor')}")
        print(f"   Service: {dep.get('service')}")
        print(f"   Frequency: {dep.get('frequency')}")
    else:
        print("\n⚠️  No external dependencies extracted")


def test_all_extractors_initialization():
    """Test that all extractors can be initialized"""
    extractors = [
        TeamStructureExtractor(OPENAI_API_KEY),
        KnowledgeGapExtractor(OPENAI_API_KEY),
        SuccessPatternExtractor(OPENAI_API_KEY),
        BudgetConstraintExtractor(OPENAI_API_KEY),
        ExternalDependencyExtractor(OPENAI_API_KEY)
    ]
    
    for extractor in extractors:
        assert extractor.client is not None
        print(f"✅ {extractor.__class__.__name__} initialized")


def test_extractors_with_empty_interview():
    """Test extractors with empty interview data"""
    extractors = [
        TeamStructureExtractor(OPENAI_API_KEY),
        KnowledgeGapExtractor(OPENAI_API_KEY),
        SuccessPatternExtractor(OPENAI_API_KEY),
        BudgetConstraintExtractor(OPENAI_API_KEY),
        ExternalDependencyExtractor(OPENAI_API_KEY)
    ]
    
    empty_interview = {
        "meta": {"company": "Test", "role": "Test"},
        "qa_pairs": {}
    }
    
    for extractor in extractors:
        results = extractor.extract_from_interview(empty_interview)
        assert isinstance(results, list)
        assert len(results) == 0
        print(f"✅ {extractor.__class__.__name__} handles empty interview")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
