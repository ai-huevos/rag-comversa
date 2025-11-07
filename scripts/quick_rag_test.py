#!/usr/bin/env python3
"""
Quick RAG System Test

Tests the RAG system with your existing intelligence.db
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import (
    RAGDatabaseGenerator,
    CompanyRAGDatabase,
    EmbeddingGenerator
)
from intelligence_capture.config import OPENAI_API_KEY


def main():
    print("\n" + "="*60)
    print("QUICK RAG SYSTEM TEST")
    print("="*60)
    
    # Check if database exists
    db_path = Path("intelligence.db")
    if not db_path.exists():
        print(f"\n❌ Database not found at {db_path}")
        print("   Please run the intelligence capture system first:")
        print("   ./scripts/run_intelligence.sh")
        return
    
    print(f"\n✅ Found database: {db_path}")
    
    # Connect to database
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    
    # Initialize v2.0 schema if needed
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='communication_channels'")
        if not cursor.fetchone():
            print("\n📊 Initializing v2.0 schema...")
            db.init_v2_schema()
    except Exception as e:
        print(f"⚠️  Schema check: {e}")
    
    # Get database stats
    stats = db.get_stats()
    print(f"\n📊 Database Statistics:")
    print(f"   Interviews: {stats.get('interviews', 0)}")
    print(f"   Pain Points: {stats.get('pain_points', 0)}")
    print(f"   Processes: {stats.get('processes', 0)}")
    print(f"   Systems: {stats.get('systems', 0)}")
    print(f"   Automation Candidates: {stats.get('automation_candidates', 0)}")
    
    if stats.get('pain_points', 0) == 0:
        print("\n⚠️  No data in database. Run intelligence capture first.")
        db.close()
        return
    
    # Create RAG generator
    print("\n🔨 Creating RAG generator...")
    generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
    
    # Estimate cost
    print("\n💰 Estimating cost...")
    estimate = generator.estimate_generation_cost("Hotel Los Tajibos")
    print(f"   Entities: {estimate['total_entities']}")
    print(f"   Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    
    if estimate['total_entities'] == 0:
        print("\n⚠️  No entities found for Hotel Los Tajibos")
        print("   Available companies:", stats.get('by_company', {}))
        db.close()
        return
    
    # Ask for confirmation
    response = input("\n   Generate RAG database? (y/n): ")
    if response.lower() != 'y':
        print("   Cancelled.")
        db.close()
        return
    
    # Generate RAG database (just pain points and automation candidates for speed)
    print("\n🔨 Generating RAG database...")
    print("   (Processing pain_points and automation_candidates only)")
    
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1  # Shallow depth for speed
    )
    
    if not documents:
        print("\n⚠️  No documents generated")
        db.close()
        return
    
    # Create searchable database
    print(f"\n📊 Creating searchable database...")
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Show statistics
    rag_stats = rag_db.get_statistics()
    print(f"\n✅ RAG Database Created!")
    print(f"   Total documents: {rag_stats['total_documents']}")
    print(f"   Entity types: {rag_stats['entity_types']}")
    
    # Test search
    print("\n🔍 Testing semantic search...")
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    test_query = "What are the biggest operational problems?"
    print(f"   Query: '{test_query}'")
    
    query_embedding = embedding_gen.generate_embedding(test_query)
    results = rag_db.search(query_embedding, top_k=3)
    
    print(f"\n   Found {len(results)} results:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n   {i}. {doc.entity_type.upper()} (similarity: {score:.3f})")
        print(f"      Business Unit: {doc.business_unit}")
        text_preview = doc.text.replace('\n', ' ')[:150]
        print(f"      Preview: {text_preview}...")
    
    # Save database
    output_path = Path("rag_databases/hotel_test_rag.json")
    rag_db.save(output_path)
    
    print(f"\n✅ Test complete!")
    print(f"\n💡 Next steps:")
    print(f"   1. Run full demo: python scripts/demo_rag_system.py")
    print(f"   2. Load saved database: CompanyRAGDatabase.load('{output_path}')")
    print(f"   3. Try interactive search in demo (option 7)")
    
    db.close()


if __name__ == "__main__":
    main()
