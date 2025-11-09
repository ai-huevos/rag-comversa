#!/usr/bin/env python3
"""
Unit Tests for Rollback Mechanism

Tests:
- Entity snapshot storage
- Entity snapshot retrieval
- Consolidation rollback
- Relationship restoration
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from intelligence_capture.database import EnhancedIntelligenceDB


class TestRollbackMechanism:
    """Test suite for rollback mechanism"""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary test database"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        
        db = EnhancedIntelligenceDB(db_path)
        db.connect()
        
        # Create schema
        cursor = db.conn.cursor()
        
        # Create systems table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS systems (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                usage_count INTEGER DEFAULT 1,
                mentioned_in_interviews TEXT,
                source_count INTEGER DEFAULT 1,
                consensus_confidence REAL DEFAULT 1.0,
                is_consolidated BOOLEAN DEFAULT 0,
                has_contradictions BOOLEAN DEFAULT 0,
                consolidated_at TIMESTAMP
            )
        """)
        
        # Create consolidation_audit table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS consolidation_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL,
                merged_entity_ids TEXT NOT NULL,
                resulting_entity_id INTEGER NOT NULL,
                similarity_score REAL NOT NULL,
                consolidation_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                rollback_timestamp TIMESTAMP,
                rollback_reason TEXT
            )
        """)
        
        # Create entity_snapshots table
        db.create_entity_snapshots_table()
        
        db.conn.commit()
        
        yield db
        
        # Cleanup
        db.conn.close()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    def test_create_entity_snapshots_table(self, temp_db):
        """Test entity_snapshots table creation"""
        cursor = temp_db.conn.cursor()
        
        # Check table exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='entity_snapshots'
        """)
        
        assert cursor.fetchone() is not None
        
        # Check columns
        cursor.execute("PRAGMA table_info(entity_snapshots)")
        columns = {row[1] for row in cursor.fetchall()}
        
        required_columns = {
            'id', 'entity_type', 'entity_id', 'snapshot_data',
            'audit_id', 'created_at'
        }
        
        assert required_columns.issubset(columns)
    
    def test_store_entity_snapshot(self, temp_db):
        """Test storing entity snapshot"""
        # Create test entity
        cursor = temp_db.conn.cursor()
        cursor.execute("""
            INSERT INTO systems (name, description, usage_count)
            VALUES (?, ?, ?)
        """, ("Excel", "Spreadsheet software", 5))
        
        entity_id = cursor.lastrowid
        temp_db.conn.commit()
        
        # Get entity data
        cursor.execute("SELECT * FROM systems WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        entity_data = dict(zip(columns, row))
        
        # Store snapshot
        success = temp_db.store_entity_snapshot(
            entity_type="systems",
            entity_id=entity_id,
            entity_data=entity_data
        )
        
        assert success
        
        # Verify snapshot stored
        cursor.execute("""
            SELECT COUNT(*) FROM entity_snapshots
            WHERE entity_type = 'systems' AND entity_id = ?
        """, (entity_id,))
        
        count = cursor.fetchone()[0]
        assert count == 1
    
    def test_get_entity_snapshot(self, temp_db):
        """Test retrieving entity snapshot"""
        # Create and store entity
        cursor = temp_db.conn.cursor()
        cursor.execute("""
            INSERT INTO systems (name, description, usage_count)
            VALUES (?, ?, ?)
        """, ("SAP", "ERP system", 3))
        
        entity_id = cursor.lastrowid
        temp_db.conn.commit()
        
        # Get entity data
        cursor.execute("SELECT * FROM systems WHERE id = ?", (entity_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        entity_data = dict(zip(columns, row))
        
        # Store snapshot
        temp_db.store_entity_snapshot(
            entity_type="systems",
            entity_id=entity_id,
            entity_data=entity_data
        )
        
        # Retrieve snapshot
        snapshot = temp_db.get_entity_snapshot(
            entity_type="systems",
            entity_id=entity_id
        )
        
        assert snapshot is not None
        assert snapshot['name'] == "SAP"
        assert snapshot['description'] == "ERP system"
        assert snapshot['usage_count'] == 3
    
    def test_rollback_consolidation(self, temp_db):
        """Test rolling back a consolidation"""
        cursor = temp_db.conn.cursor()
        
        # Create two entities that will be merged
        cursor.execute("""
            INSERT INTO systems (name, description, usage_count)
            VALUES (?, ?, ?)
        """, ("Excel", "Spreadsheet software", 1))
        entity1_id = cursor.lastrowid
        
        cursor.execute("""
            INSERT INTO systems (name, description, usage_count)
            VALUES (?, ?, ?)
        """, ("MS Excel", "Microsoft spreadsheet", 1))
        entity2_id = cursor.lastrowid
        
        temp_db.conn.commit()
        
        # Get entity data before merge
        cursor.execute("SELECT * FROM systems WHERE id = ?", (entity1_id,))
        row = cursor.fetchone()
        columns = [desc[0] for desc in cursor.description]
        entity1_data = dict(zip(columns, row))
        
        cursor.execute("SELECT * FROM systems WHERE id = ?", (entity2_id,))
        row = cursor.fetchone()
        entity2_data = dict(zip(columns, row))
        
        # Create audit record
        cursor.execute("""
            INSERT INTO consolidation_audit (
                entity_type,
                merged_entity_ids,
                resulting_entity_id,
                similarity_score
            ) VALUES (?, ?, ?, ?)
        """, (
            "systems",
            json.dumps([entity1_id, entity2_id]),
            entity1_id,
            0.92
        ))
        audit_id = cursor.lastrowid
        temp_db.conn.commit()
        
        # Store snapshots
        temp_db.store_entity_snapshot(
            entity_type="systems",
            entity_id=entity1_id,
            entity_data=entity1_data,
            audit_id=audit_id
        )
        
        temp_db.store_entity_snapshot(
            entity_type="systems",
            entity_id=entity2_id,
            entity_data=entity2_data,
            audit_id=audit_id
        )
        
        # Simulate consolidation - merge entity2 into entity1
        cursor.execute("""
            UPDATE systems
            SET name = 'Excel',
                description = 'Spreadsheet software (consolidated)',
                usage_count = 2,
                source_count = 2,
                is_consolidated = 1
            WHERE id = ?
        """, (entity1_id,))
        
        cursor.execute("DELETE FROM systems WHERE id = ?", (entity2_id,))
        temp_db.conn.commit()
        
        # Verify consolidation happened
        cursor.execute("SELECT COUNT(*) FROM systems WHERE id = ?", (entity2_id,))
        assert cursor.fetchone()[0] == 0  # Entity2 deleted
        
        cursor.execute("SELECT usage_count FROM systems WHERE id = ?", (entity1_id,))
        assert cursor.fetchone()[0] == 2  # Entity1 updated
        
        # Rollback consolidation
        success = temp_db.rollback_consolidation(
            audit_id=audit_id,
            reason="Test rollback"
        )
        
        assert success
        
        # Verify rollback
        cursor.execute("""
            SELECT rollback_timestamp, rollback_reason
            FROM consolidation_audit
            WHERE id = ?
        """, (audit_id,))
        
        rollback_ts, rollback_reason = cursor.fetchone()
        assert rollback_ts is not None
        assert rollback_reason == "Test rollback"
        
        # Verify entities restored
        cursor.execute("SELECT name, usage_count FROM systems WHERE id = ?", (entity1_id,))
        row = cursor.fetchone()
        assert row[0] == "Excel"  # Original name
        assert row[1] == 1  # Original usage_count
    
    def test_rollback_nonexistent_audit(self, temp_db):
        """Test rollback with non-existent audit ID"""
        success = temp_db.rollback_consolidation(
            audit_id=99999,
            reason="Test"
        )
        
        assert not success
    
    def test_rollback_without_snapshots(self, temp_db):
        """Test rollback without entity snapshots"""
        cursor = temp_db.conn.cursor()
        
        # Create audit record without snapshots
        cursor.execute("""
            INSERT INTO consolidation_audit (
                entity_type,
                merged_entity_ids,
                resulting_entity_id,
                similarity_score
            ) VALUES (?, ?, ?, ?)
        """, (
            "systems",
            json.dumps([1, 2]),
            1,
            0.85
        ))
        audit_id = cursor.lastrowid
        temp_db.conn.commit()
        
        # Try to rollback
        success = temp_db.rollback_consolidation(
            audit_id=audit_id,
            reason="Test"
        )
        
        assert not success


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
