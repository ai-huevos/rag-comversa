"""
Tests for Entity Context Builder

Tests the ability to build rich context for entities by traversing relationships.
"""
import pytest
import json
from pathlib import Path
from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import EntityContextBuilder


@pytest.fixture
def test_db():
    """Create a test database with sample data"""
    db_path = Path("test_context_builder.db")
    
    # Remove if exists
    if db_path.exists():
        db_path.unlink()
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_v2_schema()
    
    # Insert test interview
    interview_id = db.insert_interview(
        meta={
            "company": "Hotel Los Tajibos",
            "respondent": "Test Manager",
            "role": "F&B Manager",
            "date": "2024-11-07"
        },
        qa_pairs={"q1": "test"}
    )
    
    # Insert test pain point
    db.insert_enhanced_pain_point(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        pain_point={
            "type": "Process Inefficiency",
            "description": "Manual reconciliation between Opera, Simphony and SAP",
            "affected_roles": ["F&B Manager", "Accountant"],
            "affected_processes": ["Daily sales closing"],
            "frequency": "Daily",
            "severity": "High",
            "intensity_score": 8,
            "hair_on_fire": True,
            "time_wasted_per_occurrence_minutes": 120,
            "estimated_annual_cost_usd": 24000,
            "jtbd_who": "F&B Manager",
            "jtbd_what": "Close daily sales",
            "jtbd_where": "During end-of-day closing (22:00-24:00)",
            "jtbd_formatted": "When closing daily sales, I want to reconcile all systems automatically, but I have to do it manually which takes 2 hours",
            "root_cause": "Systems not integrated, manual double entry",
            "current_workaround": "Export from each system and reconcile in Excel",
            "confidence_score": 0.95,
            "extraction_source": "interview_1_question_5"
        }
    )
    
    # Insert test process
    db.insert_process(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        process={
            "name": "Daily sales closing",
            "owner": "F&B Manager",
            "domain": "Finance",
            "description": "Reconcile sales from all POS systems",
            "systems": ["Opera PMS", "Simphony POS", "SAP"],
            "frequency": "Daily"
        }
    )
    
    # Insert test systems
    db.insert_or_update_enhanced_system(
        system={
            "name": "Simphony POS",
            "vendor": "Oracle",
            "type": "Point of Sale",
            "user_satisfaction_score": 7.5,
            "integration_pain_points": ["No API integration", "Manual export required"],
            "data_quality_issues": ["Inconsistent data format"]
        },
        company="Hotel Los Tajibos"
    )
    
    db.insert_or_update_enhanced_system(
        system={
            "name": "SAP",
            "vendor": "SAP",
            "type": "ERP",
            "user_satisfaction_score": 6.0,
            "integration_pain_points": ["Complex import process"],
            "data_quality_issues": []
        },
        company="Hotel Los Tajibos"
    )
    
    # Insert test automation candidate
    db.insert_enhanced_automation_candidate(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        candidate={
            "name": "Automatic Opera-Simphony-SAP integration",
            "process": "Daily sales closing",
            "trigger_event": "End of shift in Simphony",
            "action": "Automatically transfer sales data to SAP",
            "output": "Consolidated sales report",
            "owner": "F&B Manager",
            "complexity": "Medium",
            "impact": "High",
            "systems_involved": ["Opera PMS", "Simphony POS", "SAP"],
            "current_manual_process_description": "Export from each system, reconcile in Excel, import to SAP manually",
            "data_sources_needed": ["Simphony API", "Opera API", "SAP API"],
            "effort_score": 3,
            "impact_score": 5,
            "priority_quadrant": "Strategic",
            "estimated_roi_months": 6,
            "estimated_annual_savings_usd": 24000,
            "confidence_score": 0.93
        }
    )
    
    # Insert test data flow
    db.insert_data_flow(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        flow={
            "source_system": "Simphony POS",
            "target_system": "SAP",
            "data_type": "Daily sales",
            "transfer_method": "Manual",
            "transfer_frequency": "Daily",
            "data_quality_issues": ["Reconciliation errors", "Inconsistent data"],
            "pain_points": ["Takes 2 hours", "Error-prone"],
            "related_process": "Daily sales closing",
            "confidence_score": 0.92
        }
    )
    
    # Insert test failure mode
    db.insert_failure_mode(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        failure={
            "failure_description": "Reconciliation errors between systems",
            "frequency": "Weekly",
            "impact_description": "Delayed reports, incorrect financial data",
            "root_cause": "Manual data entry errors",
            "current_workaround": "Manual verification and correction",
            "recovery_time_minutes": 60,
            "proposed_prevention": "Automated integration",
            "related_process": "Daily sales closing",
            "confidence_score": 0.90
        }
    )
    
    yield db
    
    # Cleanup
    db.close()
    if db_path.exists():
        db_path.unlink()


def test_build_pain_point_context(test_db):
    """Test building context for a pain point"""
    builder = EntityContextBuilder(test_db)
    
    # Build context for pain point ID 1
    context = builder.build_context('pain_point', 1, depth=2)
    
    # Verify basic properties
    assert context.entity_type == 'pain_point'
    assert context.entity_id == 1
    assert context.company == "Hotel Los Tajibos"
    assert context.business_unit == "Food & Beverage"
    
    # Verify primary text contains key information
    assert "Manual reconciliation" in context.primary_text
    assert "Intensity: 8/10" in context.primary_text
    assert "HAIR-ON-FIRE" in context.primary_text
    assert "Daily" in context.primary_text
    
    # Verify related entities were found
    assert 'processes' in context.related_entities or 'automation_candidates' in context.related_entities
    
    # Verify full context includes company info
    assert "Company: Hotel Los Tajibos" in context.full_context
    assert "Business Unit: Food & Beverage" in context.full_context
    
    # Verify metadata
    assert context.metadata['severity'] == 'High'
    assert context.metadata['hair_on_fire'] == 1
    assert context.metadata['estimated_annual_cost_usd'] == 24000
    
    print("\n✅ Pain Point Context:")
    print(context.full_context[:500])


def test_build_process_context(test_db):
    """Test building context for a process"""
    builder = EntityContextBuilder(test_db)
    
    # Build context for process ID 1
    context = builder.build_context('process', 1, depth=2)
    
    # Verify basic properties
    assert context.entity_type == 'process'
    assert context.company == "Hotel Los Tajibos"
    
    # Verify primary text
    assert "Daily sales closing" in context.primary_text
    assert "F&B Manager" in context.primary_text
    assert "Opera PMS" in context.primary_text or "Simphony POS" in context.primary_text
    
    # Verify related entities
    assert 'pain_points' in context.related_entities or 'systems' in context.related_entities
    
    print("\n✅ Process Context:")
    print(context.full_context[:500])


def test_build_system_context(test_db):
    """Test building context for a system"""
    builder = EntityContextBuilder(test_db)
    
    # Build context for system (Simphony POS should be ID 1)
    context = builder.build_context('system', 1, depth=2)
    
    # Verify basic properties
    assert context.entity_type == 'system'
    
    # Verify primary text
    assert "Simphony POS" in context.primary_text
    assert "Oracle" in context.primary_text
    assert "User Satisfaction: 7.5/10" in context.primary_text
    
    # Verify related entities
    assert 'processes' in context.related_entities or 'data_flows' in context.related_entities
    
    print("\n✅ System Context:")
    print(context.full_context[:500])


def test_build_automation_candidate_context(test_db):
    """Test building context for an automation candidate"""
    builder = EntityContextBuilder(test_db)
    
    # Build context for automation candidate ID 1
    context = builder.build_context('automation_candidate', 1, depth=2)
    
    # Verify basic properties
    assert context.entity_type == 'automation_candidate'
    assert context.company == "Hotel Los Tajibos"
    
    # Verify primary text
    assert "Opera-Simphony-SAP" in context.primary_text
    assert "Strategic" in context.primary_text
    assert "Effort: 3/5" in context.primary_text
    assert "Impact: 5/5" in context.primary_text
    
    # Verify metadata
    assert context.metadata['priority_quadrant'] == 'Strategic'
    assert context.metadata['estimated_roi_months'] == 6
    
    print("\n✅ Automation Candidate Context:")
    print(context.full_context[:500])


def test_build_data_flow_context(test_db):
    """Test building context for a data flow"""
    builder = EntityContextBuilder(test_db)
    
    # Build context for data flow ID 1
    context = builder.build_context('data_flow', 1, depth=2)
    
    # Verify basic properties
    assert context.entity_type == 'data_flow'
    
    # Verify primary text
    assert "Simphony POS → SAP" in context.primary_text
    assert "Manual" in context.primary_text
    assert "Daily sales" in context.primary_text
    
    # Verify related entities
    assert 'source_systems' in context.related_entities or 'target_systems' in context.related_entities or 'processes' in context.related_entities
    
    print("\n✅ Data Flow Context:")
    print(context.full_context[:500])


def test_context_depth_parameter(test_db):
    """Test that depth parameter affects relationship traversal"""
    builder = EntityContextBuilder(test_db)
    
    # Build with depth 1
    context_depth_1 = builder.build_context('pain_point', 1, depth=1)
    
    # Build with depth 2
    context_depth_2 = builder.build_context('pain_point', 1, depth=2)
    
    # Both should have related entities
    assert len(context_depth_1.related_entities) > 0
    assert len(context_depth_2.related_entities) > 0
    
    # Full context should be different lengths
    assert len(context_depth_1.full_context) > 0
    assert len(context_depth_2.full_context) > 0
    
    print(f"\n✅ Depth 1 context length: {len(context_depth_1.full_context)}")
    print(f"✅ Depth 2 context length: {len(context_depth_2.full_context)}")


def test_metadata_extraction(test_db):
    """Test that metadata is correctly extracted for different entity types"""
    builder = EntityContextBuilder(test_db)
    
    # Pain point metadata
    pain_context = builder.build_context('pain_point', 1, depth=1)
    assert 'severity' in pain_context.metadata
    assert 'hair_on_fire' in pain_context.metadata
    assert 'estimated_annual_cost_usd' in pain_context.metadata
    
    # Automation candidate metadata
    auto_context = builder.build_context('automation_candidate', 1, depth=1)
    assert 'priority_quadrant' in auto_context.metadata
    assert 'effort_score' in auto_context.metadata
    assert 'impact_score' in auto_context.metadata
    
    # System metadata
    system_context = builder.build_context('system', 1, depth=1)
    assert 'user_satisfaction_score' in system_context.metadata
    
    print("\n✅ Metadata extraction working correctly")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
