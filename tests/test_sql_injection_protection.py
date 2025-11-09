"""
Unit tests for SQL injection protection in database.py
"""
import pytest
import tempfile
from pathlib import Path
from intelligence_capture.database import IntelligenceDB, VALID_ENTITY_TYPES


def test_valid_entity_types_constant():
    """Test that VALID_ENTITY_TYPES contains all expected entity types"""
    expected_types = {
        "pain_points",
        "processes",
        "systems",
        "kpis",
        "automation_candidates",
        "inefficiencies",
        "communication_channels",
        "decision_points",
        "data_flows",
        "temporal_patterns",
        "failure_modes",
        "team_structures",
        "knowledge_gaps",
        "success_patterns",
        "budget_constraints",
        "external_dependencies"
    }
    
    assert VALID_ENTITY_TYPES == expected_types, "VALID_ENTITY_TYPES should contain all 17 entity types"


def test_update_consolidated_entity_validates_entity_type():
    """Test that update_consolidated_entity rejects invalid entity types"""
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = IntelligenceDB(db_path)
        db.connect()
        db.init_schema()
        
        # Test with invalid entity type (SQL injection attempt)
        with pytest.raises(ValueError) as exc_info:
            db.update_consolidated_entity(
                entity_type="systems; DROP TABLE systems; --",
                entity_id=1,
                updated_data={"name": "test"},
                interview_id=1
            )
        
        assert "Invalid entity type" in str(exc_info.value)
        assert "Must be one of" in str(exc_info.value)
        
        # Test with valid entity type (should not raise)
        # Note: This will fail because entity doesn't exist, but that's OK
        # We're just testing that validation passes
        try:
            db.update_consolidated_entity(
                entity_type="systems",
                entity_id=999,  # Non-existent ID
                updated_data={"name": "test"},
                interview_id=1
            )
        except ValueError:
            pytest.fail("Valid entity type should not raise ValueError")
        
        db.close()
    finally:
        db_path.unlink()


def test_get_entities_by_type_validates_entity_type():
    """Test that get_entities_by_type rejects invalid entity types"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = IntelligenceDB(db_path)
        db.connect()
        db.init_schema()
        
        # Test with invalid entity type
        with pytest.raises(ValueError) as exc_info:
            db.get_entities_by_type(
                entity_type="systems UNION SELECT * FROM interviews"
            )
        
        assert "Invalid entity type" in str(exc_info.value)
        
        # Test with valid entity type (should not raise)
        result = db.get_entities_by_type(entity_type="systems")
        assert isinstance(result, list)
        
        db.close()
    finally:
        db_path.unlink()


def test_check_entity_exists_validates_entity_type():
    """Test that check_entity_exists rejects invalid entity types"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = IntelligenceDB(db_path)
        db.connect()
        db.init_schema()
        
        # Test with invalid entity type
        with pytest.raises(ValueError) as exc_info:
            db.check_entity_exists(
                entity_type="systems' OR '1'='1",
                entity_id=1
            )
        
        assert "Invalid entity type" in str(exc_info.value)
        
        # Test with valid entity type (should not raise)
        result = db.check_entity_exists(entity_type="systems", entity_id=1)
        assert isinstance(result, bool)
        
        db.close()
    finally:
        db_path.unlink()


def test_insert_or_update_entity_validates_entity_type():
    """Test that insert_or_update_entity rejects invalid entity types"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = IntelligenceDB(db_path)
        db.connect()
        db.init_schema()
        
        # Test with invalid entity type
        with pytest.raises(ValueError) as exc_info:
            db.insert_or_update_entity(
                entity_type="systems; DELETE FROM interviews; --",
                entity={"name": "test"},
                interview_id=1
            )
        
        assert "Invalid entity type" in str(exc_info.value)
        
        db.close()
    finally:
        db_path.unlink()


def test_all_valid_entity_types_accepted():
    """Test that all valid entity types are accepted"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = Path(tmp.name)
    
    try:
        db = IntelligenceDB(db_path)
        db.connect()
        db.init_schema()
        
        # Test each valid entity type
        for entity_type in VALID_ENTITY_TYPES:
            # Should not raise ValueError
            result = db.get_entities_by_type(entity_type=entity_type)
            assert isinstance(result, list), f"Failed for entity_type: {entity_type}"
        
        db.close()
    finally:
        db_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
