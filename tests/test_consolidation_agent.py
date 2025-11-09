#!/usr/bin/env python3
"""
Unit Tests for KnowledgeConsolidationAgent

Tests:
- End-to-end consolidation with mock database
- Transaction rollback on failure
- Audit trail creation
"""
import pytest
import json
from unittest.mock import Mock, MagicMock, patch
from intelligence_capture.consolidation_agent import KnowledgeConsolidationAgent


class TestKnowledgeConsolidationAgent:
    """Test suite for KnowledgeConsolidationAgent"""
    
    @pytest.fixture
    def config(self):
        """Standard configuration for tests"""
        return {
            "similarity_thresholds": {
                "systems": 0.85,
                "pain_points": 0.80,
                "default": 0.85
            },
            "similarity_weights": {
                "semantic_weight": 0.3,
                "name_weight": 0.7
            },
            "consensus_parameters": {
                "source_count_divisor": 10,
                "agreement_bonus": 0.1,
                "max_bonus": 0.3,
                "contradiction_penalty": 0.25,
                "single_source_penalty": 0.3
            },
            "performance": {
                "max_candidates": 10,
                "enable_caching": True,
                "use_db_storage": False
            },
            "retry": {
                "max_retries": 3,
                "circuit_breaker_threshold": 10
            }
        }
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.conn = Mock()
        db.conn.cursor = Mock(return_value=Mock())
        db.conn.execute = Mock()
        db.conn.commit = Mock()
        db.conn.rollback = Mock()
        return db
    
    @pytest.fixture
    def agent(self, mock_db, config):
        """Create agent instance with mock database"""
        return KnowledgeConsolidationAgent(mock_db, config, openai_api_key=None)
    
    # Test 1: End-to-End Consolidation
    
    def test_consolidate_entities_processes_all_types(self, agent, mock_db):
        """Test consolidation processes all entity types"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"}
            ],
            "pain_points": [
                {"name": "Manual data entry", "description": "Time consuming"}
            ]
        }
        
        # Mock database to return no existing entities
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_db.conn.cursor.return_value = mock_cursor
        
        result = agent.consolidate_entities(entities, interview_id=1)
        
        # Should process both entity types
        assert "systems" in result
        assert "pain_points" in result
        assert len(result["systems"]) == 1
        assert len(result["pain_points"]) == 1
    
    def test_consolidate_entities_merges_duplicates(self, agent, mock_db):
        """Test consolidation merges duplicate entities"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"}
            ]
        }
        
        # Mock database to return existing similar entity
        existing_entity = {
            "id": 1,
            "name": "Excel spreadsheet",
            "description": "Microsoft Excel",
            "mentioned_in_interviews": "[1]",
            "source_count": 1,
            "is_consolidated": 0,
            "merged_entity_ids": "[]"
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[existing_entity])
        mock_db.conn.cursor.return_value = mock_cursor
        
        result = agent.consolidate_entities(entities, interview_id=2)
        
        # Should merge with existing entity
        assert len(result["systems"]) == 1
        # Source count should be updated
        assert result["systems"][0]["source_count"] == 2
    
    def test_consolidate_entities_updates_statistics(self, agent, mock_db):
        """Test consolidation updates statistics"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"},
                {"name": "SAP", "description": "ERP system"}
            ]
        }
        
        # Mock database to return no existing entities
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_db.conn.cursor.return_value = mock_cursor
        
        agent.consolidate_entities(entities, interview_id=1)
        
        stats = agent.get_statistics()
        
        # Should track entities processed
        assert stats["entities_processed"] == 2
    
    # Test 2: Transaction Management
    
    def test_consolidate_entities_commits_on_success(self, agent, mock_db):
        """Test consolidation commits transaction on success"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"}
            ]
        }
        
        # Mock database to return no existing entities
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_db.conn.cursor.return_value = mock_cursor
        
        agent.consolidate_entities(entities, interview_id=1)
        
        # Should begin and commit transaction
        mock_db.conn.execute.assert_any_call("BEGIN TRANSACTION")
        mock_db.conn.commit.assert_called_once()
    
    def test_consolidate_entities_rolls_back_on_failure(self, agent, mock_db):
        """Test consolidation rolls back transaction on failure"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"}
            ]
        }
        
        # Mock database to raise exception
        mock_db.conn.cursor.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            agent.consolidate_entities(entities, interview_id=1)
        
        # Should rollback transaction
        mock_db.conn.rollback.assert_called_once()
    
    def test_consolidate_entities_logs_error_on_failure(self, agent, mock_db):
        """Test consolidation logs error on failure"""
        entities = {
            "systems": [
                {"name": "Excel", "description": "Spreadsheet"}
            ]
        }
        
        # Mock database to raise exception
        mock_db.conn.cursor.side_effect = Exception("Database error")
        
        with pytest.raises(Exception):
            agent.consolidate_entities(entities, interview_id=1)
        
        # Should attempt to log error (even if it fails)
        # We can't easily verify logging, but we can verify rollback was called
        mock_db.conn.rollback.assert_called_once()
    
    # Test 3: Audit Trail Creation
    
    def test_merge_entities_logs_to_audit_trail(self, agent, mock_db):
        """Test merge operation logs to audit trail"""
        new_entity = {
            "id": 2,
            "name": "Excel",
            "entity_type": "systems"
        }
        
        existing_entity = {
            "id": 1,
            "name": "Excel spreadsheet",
            "mentioned_in_interviews": "[1]",
            "source_count": 1,
            "merged_entity_ids": "[]"
        }
        
        # Mock cursor for audit logging
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value = mock_cursor
        
        agent.merge_entities(new_entity, existing_entity, interview_id=2, similarity_score=0.95)
        
        # Should insert into consolidation_audit table
        mock_cursor.execute.assert_called()
        call_args = mock_cursor.execute.call_args
        assert "consolidation_audit" in call_args[0][0]
    
    def test_audit_trail_includes_similarity_score(self, agent, mock_db):
        """Test audit trail includes similarity score"""
        new_entity = {
            "id": 2,
            "name": "Excel",
            "entity_type": "systems"
        }
        
        existing_entity = {
            "id": 1,
            "name": "Excel spreadsheet",
            "mentioned_in_interviews": "[1]",
            "source_count": 1,
            "merged_entity_ids": "[]"
        }
        
        # Mock cursor for audit logging
        mock_cursor = Mock()
        mock_db.conn.cursor.return_value = mock_cursor
        
        agent.merge_entities(new_entity, existing_entity, interview_id=2, similarity_score=0.92)
        
        # Should include similarity score in audit
        call_args = mock_cursor.execute.call_args
        assert 0.92 in call_args[0][1]
    
    # Test 4: Entity Preparation
    
    def test_prepare_new_entity_initializes_fields(self, agent):
        """Test new entity preparation initializes all consolidation fields"""
        entity = {
            "name": "Excel",
            "description": "Spreadsheet"
        }
        
        prepared = agent._prepare_new_entity(entity, interview_id=1)
        
        # Should initialize consolidation fields
        assert "mentioned_in_interviews" in prepared
        assert "source_count" in prepared
        assert prepared["source_count"] == 1
        assert "consensus_confidence" in prepared
        assert prepared["consensus_confidence"] == 0.5  # Single source
        assert "is_consolidated" in prepared
        assert prepared["is_consolidated"] == 0
        assert "has_contradictions" in prepared
        assert prepared["has_contradictions"] == 0
    
    def test_prepare_new_entity_sets_dates(self, agent):
        """Test new entity preparation sets date fields"""
        entity = {
            "name": "Excel"
        }
        
        prepared = agent._prepare_new_entity(entity, interview_id=1)
        
        # Should set date fields
        assert "first_mentioned_date" in prepared
        assert "last_mentioned_date" in prepared
        assert prepared["first_mentioned_date"] is not None
        assert prepared["last_mentioned_date"] is not None
    
    # Test 5: Duplicate Detection Integration
    
    def test_find_similar_entities_queries_database(self, agent, mock_db):
        """Test find_similar_entities queries database correctly"""
        entity = {"name": "Excel"}
        
        # Mock database to return existing entities
        existing_entity = {
            "id": 1,
            "name": "Excel spreadsheet",
            "description": "Microsoft Excel"
        }
        
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[existing_entity])
        mock_db.conn.cursor.return_value = mock_cursor
        
        similar = agent.find_similar_entities(entity, "systems")
        
        # Should query database
        mock_cursor.execute.assert_called()
        # Query should filter by is_consolidated
        call_args = mock_cursor.execute.call_args
        assert "is_consolidated" in call_args[0][0]
    
    def test_find_similar_entities_returns_empty_for_no_matches(self, agent, mock_db):
        """Test find_similar_entities returns empty list when no matches"""
        entity = {"name": "Unique System XYZ"}
        
        # Mock database to return no entities
        mock_cursor = Mock()
        mock_cursor.fetchall = Mock(return_value=[])
        mock_db.conn.cursor.return_value = mock_cursor
        
        similar = agent.find_similar_entities(entity, "systems")
        
        # Should return empty list
        assert similar == []
    
    # Test 6: Consensus Confidence Calculation
    
    def test_calculate_consensus_confidence_uses_scorer(self, agent):
        """Test consensus confidence calculation uses ConsensusScorer"""
        entity = {
            "name": "Excel",
            "source_count": 5,
            "mentioned_in_interviews": "[1, 2, 3, 4, 5]"
        }
        
        confidence = agent.calculate_consensus_confidence(entity)
        
        # Should return a value between 0 and 1
        assert 0.0 <= confidence <= 1.0
    
    def test_calculate_consensus_confidence_higher_for_more_sources(self, agent):
        """Test confidence is higher for entities with more sources"""
        entity_few_sources = {
            "name": "Excel",
            "source_count": 2,
            "mentioned_in_interviews": "[1, 2]"
        }
        
        entity_many_sources = {
            "name": "Excel",
            "source_count": 10,
            "mentioned_in_interviews": json.dumps(list(range(1, 11)))
        }
        
        conf_few = agent.calculate_consensus_confidence(entity_few_sources)
        conf_many = agent.calculate_consensus_confidence(entity_many_sources)
        
        # More sources should have higher confidence
        assert conf_many > conf_few


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
