#!/usr/bin/env python3
"""
Test Consolidation System

Tests the Knowledge Graph consolidation system with sample data.
Creates test entities with known duplicates and verifies consolidation works.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.consolidation_agent import KnowledgeConsolidationAgent
from intelligence_capture.config import load_consolidation_config, PILOT_DB_PATH
import os


def create_test_entities():
    """Create test entities with known duplicates"""
    return {
        "systems": [
            {"name": "Excel", "description": "Microsoft Excel spreadsheet tool"},
            {"name": "Excel spreadsheet", "description": "Excel for data management"},
            {"name": "Microsoft Excel", "description": "Spreadsheet software"},
            {"name": "SAP", "description": "SAP ERP system"},
            {"name": "SAP ERP", "description": "Enterprise resource planning"},
        ],
        "pain_points": [
            {
                "type": "Manual data entry",
                "description": "Employees spend hours entering data manually",
                "severity": "High",
                "frequency": "Daily"
            },
            {
                "type": "Manual data entry",
                "description": "Manual data input takes too much time",
                "severity": "High",
                "frequency": "Daily"
            },
            {
                "type": "Communication delays",
                "description": "Messages take too long to reach team members",
                "severity": "Medium",
                "frequency": "Weekly"
            }
        ]
    }


def test_consolidation():
    """Test consolidation system"""
    print("=" * 70)
    print("KNOWLEDGE GRAPH CONSOLIDATION TEST")
    print("=" * 70)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    config = load_consolidation_config()
    print(f"   Similarity threshold for systems: {config['similarity_thresholds']['systems']}")
    print(f"   Similarity threshold for pain_points: {config['similarity_thresholds']['pain_points']}")
    
    # Connect to database
    print(f"\n📂 Connecting to test database: {PILOT_DB_PATH}")
    db = EnhancedIntelligenceDB(PILOT_DB_PATH)
    db.connect()
    
    # Initialize consolidation agent
    print("\n🔗 Initializing consolidation agent...")
    agent = KnowledgeConsolidationAgent(
        db=db,
        config=config,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create test entities
    print("\n📝 Creating test entities...")
    test_entities = create_test_entities()
    print(f"   Systems: {len(test_entities['systems'])} entities")
    print(f"   Pain Points: {len(test_entities['pain_points'])} entities")
    
    # Test duplicate detection
    print("\n🔍 Testing duplicate detection...")
    
    # Test systems
    print("\n   Testing systems:")
    excel_entity = test_entities["systems"][0]
    similar_systems = agent.find_similar_entities(excel_entity, "systems")
    
    if similar_systems:
        print(f"   ✓ Found {len(similar_systems)} similar entities to 'Excel':")
        for entity, score in similar_systems[:3]:
            print(f"     - {entity.get('name', 'N/A')} (similarity: {score:.2f})")
    else:
        print(f"   ℹ️  No similar entities found (database may be empty)")
    
    # Test pain points
    print("\n   Testing pain points:")
    pain_entity = test_entities["pain_points"][0]
    similar_pains = agent.find_similar_entities(pain_entity, "pain_points")
    
    if similar_pains:
        print(f"   ✓ Found {len(similar_pains)} similar entities to 'Manual data entry':")
        for entity, score in similar_pains[:3]:
            print(f"     - {entity.get('type', 'N/A')} (similarity: {score:.2f})")
    else:
        print(f"   ℹ️  No similar entities found (database may be empty)")
    
    # Test consolidation
    print("\n🔗 Testing consolidation...")
    interview_id = 999  # Test interview ID
    
    consolidated = agent.consolidate_entities(test_entities, interview_id)
    
    # Print results
    print("\n📊 Consolidation Results:")
    for entity_type, entities in consolidated.items():
        print(f"\n   {entity_type}:")
        print(f"     Original: {len(test_entities[entity_type])} entities")
        print(f"     Consolidated: {len(entities)} entities")
        
        if len(test_entities[entity_type]) > len(entities):
            reduction = ((len(test_entities[entity_type]) - len(entities)) / len(test_entities[entity_type])) * 100
            print(f"     Reduction: {reduction:.1f}%")
    
    # Print statistics
    stats = agent.get_statistics()
    print("\n📈 Statistics:")
    print(f"   Entities processed: {stats['entities_processed']}")
    print(f"   Duplicates found: {stats['duplicates_found']}")
    print(f"   Entities merged: {stats['entities_merged']}")
    print(f"   Contradictions detected: {stats['contradictions_detected']}")
    print(f"   Processing time: {stats['processing_time']:.2f}s")
    
    # Close database
    db.close()
    
    print("\n✅ Test complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_consolidation()
