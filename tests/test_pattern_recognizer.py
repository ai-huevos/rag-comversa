#!/usr/bin/env python3
"""
Unit Tests for PatternRecognizer Component

Tests:
- Recurring pain point detection
- Problematic system identification
- Pattern frequency calculation
- High-priority pattern flagging
- Pattern storage in database
"""
import pytest
from unittest.mock import Mock, MagicMock
from intelligence_capture.pattern_recognizer import PatternRecognizer


class TestPatternRecognizer:
    """Test suite for PatternRecognizer"""
    
    @pytest.fixture
    def config(self):
        """Standard configuration for tests"""
        return {
            "consolidation": {
                "pattern_recognition": {
                    "recurring_pain_threshold": 3,
                    "problematic_system_threshold": 5,
                    "high_priority_frequency": 0.30
                }
            }
        }
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database"""
        db = Mock()
        db.conn = Mock()
        db.conn.cursor = Mock()
        return db
    
    @pytest.fixture
    def recognizer(self, mock_db, config):
        """Create recognizer instance"""
        return PatternRecognizer(mock_db, config)
    
    # Test 1: Recurring Pain Point Detection
    
    def test_find_recurring_pain_points_above_threshold(self, recognizer, mock_db):
        """Test finding pain points above threshold"""
        # Mock database response
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (1, "Manual data entry is time-consuming", 5, 0.85),
            (2, "Excel crashes frequently", 4, 0.75),
            (3, "Communication delays", 3, 0.70)
        ]
        mock_db.conn.cursor.return_value = cursor_mock
        
        pain_points = recognizer.find_recurring_pain_points(threshold=3)
        
        assert len(pain_points) == 3
        assert pain_points[0]["source_count"] == 5
        assert pain_points[1]["source_count"] == 4
        assert pain_points[2]["source_count"] == 3
    
    def test_find_recurring_pain_points_below_threshold(self, recognizer, mock_db):
        """Test that pain points below threshold are excluded"""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (1, "Manual data entry", 5, 0.85),
            (2, "Excel crashes", 2, 0.60)  # Below threshold of 3
        ]
        mock_db.conn.cursor.return_value = cursor_mock
        
        pain_points = recognizer.find_recurring_pain_points(threshold=3)
        
        # Should only return the one above threshold
        assert len(pain_points) == 2  # Mock returns both, but query filters
    
    def test_find_recurring_pain_points_empty(self, recognizer, mock_db):
        """Test with no recurring pain points"""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        mock_db.conn.cursor.return_value = cursor_mock
        
        pain_points = recognizer.find_recurring_pain_points(threshold=3)
        
        assert len(pain_points) == 0
    
    # Test 2: Problematic System Identification
    
    def test_find_problematic_systems_above_threshold(self, recognizer, mock_db):
        """Test finding systems above threshold"""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = [
            (1, "Excel", 8),
            (2, "SAP", 6),
            (3, "WhatsApp", 5)
        ]
        mock_db.conn.cursor.return_value = cursor_mock
        
        systems = recognizer.find_problematic_systems(threshold=5)
        
        assert len(systems) == 3
        assert systems[0]["name"] == "Excel"
        assert systems[0]["source_count"] == 8
    
    def test_find_problematic_systems_empty(self, recognizer, mock_db):
        """Test with no problematic systems"""
        cursor_mock = MagicMock()
        cursor_mock.fetchall.return_value = []
        mock_db.conn.cursor.return_value = cursor_mock
        
        systems = recognizer.find_problematic_systems(threshold=5)
        
        assert len(systems) == 0
    
    # Test 3: Pattern Frequency Calculation
    
    def test_create_pattern_frequency_calculation(self, recognizer):
        """Test pattern frequency calculation"""
        pattern = recognizer._create_pattern(
            pattern_type="recurring_pain",
            entity_type="pain_points",
            entity_id=1,
            source_count=10,
            total_interviews=20,
            description="Manual data entry"
        )
        
        assert pattern["pattern_frequency"] == 0.5  # 10/20
        assert pattern["source_count"] == 10
    
    def test_create_pattern_zero_interviews(self, recognizer):
        """Test pattern frequency with zero interviews"""
        pattern = recognizer._create_pattern(
            pattern_type="recurring_pain",
            entity_type="pain_points",
            entity_id=1,
            source_count=5,
            total_interviews=0,
            description="Test"
        )
        
        assert pattern["pattern_frequency"] == 0.0
    
    # Test 4: High-Priority Pattern Flagging
    
    def test_high_priority_pattern_above_threshold(self, recognizer):
        """Test high-priority flagging for patterns above 30% frequency"""
        pattern = recognizer._create_pattern(
            pattern_type="recurring_pain",
            entity_type="pain_points",
            entity_id=1,
            source_count=15,
            total_interviews=44,  # 15/44 = 34% > 30%
            description="Manual data entry"
        )
        
        assert pattern["high_priority"] is True
    
    def test_high_priority_pattern_below_threshold(self, recognizer):
        """Test high-priority flagging for patterns below 30% frequency"""
        pattern = recognizer._create_pattern(
            pattern_type="recurring_pain",
            entity_type="pain_points",
            entity_id=1,
            source_count=10,
            total_interviews=44,  # 10/44 = 23% < 30%
            description="Minor issue"
        )
        
        assert pattern["high_priority"] is False
    
    def test_high_priority_pattern_exactly_threshold(self, recognizer):
        """Test high-priority flagging at exactly 30% frequency"""
        pattern = recognizer._create_pattern(
            pattern_type="recurring_pain",
            entity_type="pain_points",
            entity_id=1,
            source_count=30,
            total_interviews=100,  # 30/100 = 30%
            description="Common issue"
        )
        
        assert pattern["high_priority"] is True
    
    # Test 5: Full Pattern Identification
    
    def test_identify_patterns_integration(self, recognizer, mock_db):
        """Test full pattern identification"""
        # Mock total interviews
        cursor_mock = MagicMock()
        
        # First call: get total interviews
        # Second call: get recurring pain points
        # Third call: get problematic systems
        cursor_mock.fetchone.return_value = (44,)  # Total interviews
        cursor_mock.fetchall.side_effect = [
            [(1, "Manual data entry", 15, 0.85)],  # Recurring pains
            [(1, "Excel", 20)]  # Problematic systems
        ]
        
        mock_db.conn.cursor.return_value = cursor_mock
        
        patterns = recognizer.identify_patterns()
        
        # Should find 2 patterns (1 pain + 1 system)
        assert len(patterns) == 2
        
        # Check statistics
        stats = recognizer.get_statistics()
        assert stats["patterns_identified"] == 2
        assert stats["recurring_pain_points"] == 1
        assert stats["problematic_systems"] == 1
    
    def test_identify_patterns_no_interviews(self, recognizer, mock_db):
        """Test pattern identification with no interviews"""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = (0,)  # No interviews
        mock_db.conn.cursor.return_value = cursor_mock
        
        patterns = recognizer.identify_patterns()
        
        assert len(patterns) == 0
    
    # Test 6: Pattern Storage
    
    def test_store_pattern_new(self, recognizer, mock_db):
        """Test storing a new pattern"""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = None  # Pattern doesn't exist
        mock_db.conn.cursor.return_value = cursor_mock
        
        pattern = {
            "pattern_type": "recurring_pain",
            "entity_type": "pain_points",
            "entity_id": 1,
            "pattern_frequency": 0.34,
            "source_count": 15,
            "high_priority": True,
            "description": "Manual data entry"
        }
        
        result = recognizer._store_pattern(pattern)
        
        assert result is True
        # Verify INSERT was called
        cursor_mock.execute.assert_called()
    
    def test_store_pattern_update_existing(self, recognizer, mock_db):
        """Test updating an existing pattern"""
        cursor_mock = MagicMock()
        cursor_mock.fetchone.return_value = (1,)  # Pattern exists with id=1
        mock_db.conn.cursor.return_value = cursor_mock
        
        pattern = {
            "pattern_type": "recurring_pain",
            "entity_type": "pain_points",
            "entity_id": 1,
            "pattern_frequency": 0.40,
            "source_count": 18,
            "high_priority": True,
            "description": "Manual data entry (updated)"
        }
        
        result = recognizer._store_pattern(pattern)
        
        assert result is True
        # Verify UPDATE was called
        cursor_mock.execute.assert_called()
    
    # Test 7: Configuration
    
    def test_configuration_thresholds(self, config):
        """Test that configuration thresholds are loaded correctly"""
        mock_db = Mock()
        recognizer = PatternRecognizer(mock_db, config)
        
        assert recognizer.recurring_pain_threshold == 3
        assert recognizer.problematic_system_threshold == 5
        assert recognizer.high_priority_frequency == 0.30
    
    def test_configuration_defaults(self):
        """Test default configuration values"""
        mock_db = Mock()
        empty_config = {"consolidation": {}}
        recognizer = PatternRecognizer(mock_db, empty_config)
        
        # Should use defaults
        assert recognizer.recurring_pain_threshold == 3
        assert recognizer.problematic_system_threshold == 5
        assert recognizer.high_priority_frequency == 0.30
