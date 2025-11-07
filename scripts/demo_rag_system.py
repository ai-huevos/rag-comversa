#!/usr/bin/env python3
"""
Demo script for RAG Database System

Shows how to:
1. Generate RAG databases from existing intelligence.db
2. Perform semantic searches
3. Query with filters
4. Save and load databases
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import (
    RAGDatabaseGenerator,
    CompanyRAGDatabase,
    HoldingRAGDatabase
)
from intelligence_capture.config import OPENAI_API_KEY


def demo_basic_rag_generation():
    """Demo 1: Generate RAG database for one company"""
    print("\n" + "="*60)
    print("DEMO 1: Generate RAG Database for Hotel Los Tajibos")
    print("="*60)
    
    # Connect to existing database
    db_path = Path("intelligence.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("   Run the intelligence capture system first!")
        return None
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    
    # Check if v2.0 schema exists, if not initialize it
    try:
        cursor = db.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='communication_channels'")
        if not cursor.fetchone():
            print("\n📊 Initializing v2.0 schema...")
            db.init_v2_schema()
    except:
        pass
    
    # Create RAG generator
    generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
    
    # Estimate cost first
    print("\n💰 Estimating cost...")
    estimate = generator.estimate_generation_cost("Hotel Los Tajibos")
    print(f"   Entities to process: {estimate['total_entities']}")
    print(f"   Estimated tokens: {estimate['estimated_tokens']:,}")
    print(f"   Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    
    # Ask for confirmation
    response = input("\n   Continue? (y/n): ")
    if response.lower() != 'y':
        print("   Cancelled.")
        return None
    
    # Generate RAG database
    print("\n🔨 Generating RAG database...")
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate', 'process'],
        depth=2
    )
    
    # Create searchable database
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Show statistics
    stats = rag_db.get_statistics()
    print(f"\n📊 Database Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Entity types: {stats['entity_types']}")
    print(f"   Business units: {stats['business_units']}")
    
    # Save database
    output_path = Path("rag_databases/hotel_los_tajibos_rag.json")
    rag_db.save(output_path)
    
    db.close()
    return rag_db


def demo_semantic_search(rag_db: CompanyRAGDatabase):
    """Demo 2: Perform semantic searches"""
    print("\n" + "="*60)
    print("DEMO 2: Semantic Search")
    print("="*60)
    
    if rag_db is None:
        print("❌ No RAG database available. Run Demo 1 first.")
        return
    
    # Create embedding generator for queries
    from intelligence_capture.rag_generator import EmbeddingGenerator
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    # Example queries
    queries = [
        "What are the biggest problems with POS systems and reconciliation?",
        "Which processes take the most time and could be automated?",
        "What are the pain points in the restaurant operations?"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n🔍 Query {i}: {query}")
        
        # Generate query embedding
        query_embedding = embedding_gen.generate_embedding(query)
        
        # Search
        results = rag_db.search(query_embedding, top_k=3)
        
        print(f"\n   Found {len(results)} results:")
        for j, (doc, score) in enumerate(results, 1):
            print(f"\n   {j}. {doc.entity_type.upper()} (similarity: {score:.3f})")
            print(f"      Business Unit: {doc.business_unit}")
            # Show first 150 chars of text
            text_preview = doc.text.replace('\n', ' ')[:150]
            print(f"      Preview: {text_preview}...")


def demo_filtered_search(rag_db: CompanyRAGDatabase):
    """Demo 3: Search with filters"""
    print("\n" + "="*60)
    print("DEMO 3: Filtered Search")
    print("="*60)
    
    if rag_db is None:
        print("❌ No RAG database available. Run Demo 1 first.")
        return
    
    from intelligence_capture.rag_generator import EmbeddingGenerator
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    # Search only for pain points
    query = "What are the operational problems?"
    print(f"\n🔍 Query: {query}")
    print(f"   Filter: entity_type = 'pain_point'")
    
    query_embedding = embedding_gen.generate_embedding(query)
    
    results = rag_db.search(
        query_embedding,
        top_k=5,
        filters={'entity_type': 'pain_point'}
    )
    
    print(f"\n   Found {len(results)} pain points:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n   {i}. Similarity: {score:.3f}")
        print(f"      Business Unit: {doc.business_unit}")
        # Extract description from metadata if available
        if 'severity' in doc.metadata:
            print(f"      Severity: {doc.metadata['severity']}")
        if 'frequency' in doc.metadata:
            print(f"      Frequency: {doc.metadata['frequency']}")


def demo_holding_level_rag():
    """Demo 4: Generate holding-level RAG database"""
    print("\n" + "="*60)
    print("DEMO 4: Holding-Level RAG Database")
    print("="*60)
    
    db_path = Path("intelligence.db")
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        return None
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    
    # Create RAG generator
    generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
    
    # Estimate cost for all companies
    print("\n💰 Estimating cost for all companies...")
    estimate = generator.estimate_generation_cost()
    print(f"   Total entities: {estimate['total_entities']}")
    print(f"   Companies: {', '.join(estimate['companies'])}")
    print(f"   Estimated cost: ${estimate['estimated_cost_usd']:.4f}")
    
    response = input("\n   Continue? (y/n): ")
    if response.lower() != 'y':
        print("   Cancelled.")
        db.close()
        return None
    
    # Generate holding-level RAG
    print("\n🔨 Generating holding-level RAG database...")
    holding_db = generator.generate_holding_rag(
        output_dir=Path("rag_databases/holding")
    )
    
    # Show statistics
    stats = holding_db.get_statistics()
    print(f"\n📊 Holding Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Companies: {list(stats['companies'].keys())}")
    print(f"   Entity types: {stats['entity_types']}")
    
    db.close()
    return holding_db


def demo_cross_company_search(holding_db: HoldingRAGDatabase):
    """Demo 5: Search across all companies"""
    print("\n" + "="*60)
    print("DEMO 5: Cross-Company Search")
    print("="*60)
    
    if holding_db is None:
        print("❌ No holding database available. Run Demo 4 first.")
        return
    
    from intelligence_capture.rag_generator import EmbeddingGenerator
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    # Search across all companies
    query = "What are common automation opportunities across all companies?"
    print(f"\n🔍 Query: {query}")
    
    query_embedding = embedding_gen.generate_embedding(query)
    
    results = holding_db.search(
        query_embedding,
        top_k=5,
        filters={'entity_type': 'automation_candidate'}
    )
    
    print(f"\n   Found {len(results)} automation opportunities:")
    for i, (doc, score) in enumerate(results, 1):
        print(f"\n   {i}. {doc.company} - Similarity: {score:.3f}")
        print(f"      Business Unit: {doc.business_unit}")
        if 'priority_quadrant' in doc.metadata:
            print(f"      Priority: {doc.metadata['priority_quadrant']}")


def demo_load_existing_rag():
    """Demo 6: Load previously saved RAG database"""
    print("\n" + "="*60)
    print("DEMO 6: Load Existing RAG Database")
    print("="*60)
    
    rag_path = Path("rag_databases/hotel_los_tajibos_rag.json")
    
    if not rag_path.exists():
        print(f"❌ No saved RAG database found at {rag_path}")
        print("   Run Demo 1 first to generate and save a database.")
        return None
    
    print(f"\n📂 Loading RAG database from {rag_path}...")
    rag_db = CompanyRAGDatabase.load(rag_path)
    
    # Show statistics
    stats = rag_db.get_statistics()
    print(f"\n📊 Loaded Database Statistics:")
    print(f"   Company: {stats['company']}")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Entity types: {stats['entity_types']}")
    
    return rag_db


def interactive_search(rag_db: CompanyRAGDatabase):
    """Demo 7: Interactive search mode"""
    print("\n" + "="*60)
    print("DEMO 7: Interactive Search")
    print("="*60)
    
    if rag_db is None:
        print("❌ No RAG database available.")
        return
    
    from intelligence_capture.rag_generator import EmbeddingGenerator
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    print(f"\n🔍 Interactive search for {rag_db.company_name}")
    print("   Type your questions (or 'quit' to exit)")
    
    while True:
        query = input("\n   Query: ").strip()
        
        if query.lower() in ['quit', 'exit', 'q']:
            break
        
        if not query:
            continue
        
        # Generate embedding and search
        query_embedding = embedding_gen.generate_embedding(query)
        results = rag_db.search(query_embedding, top_k=3)
        
        print(f"\n   Found {len(results)} results:")
        for i, (doc, score) in enumerate(results, 1):
            print(f"\n   {i}. {doc.entity_type.upper()} (similarity: {score:.3f})")
            print(f"      Business Unit: {doc.business_unit}")
            text_preview = doc.text.replace('\n', ' ')[:200]
            print(f"      {text_preview}...")


def main():
    """Main demo menu"""
    print("\n" + "="*60)
    print("RAG DATABASE SYSTEM DEMO")
    print("="*60)
    print("\nAvailable demos:")
    print("  1. Generate RAG database for Hotel Los Tajibos")
    print("  2. Semantic search examples")
    print("  3. Filtered search examples")
    print("  4. Generate holding-level RAG database")
    print("  5. Cross-company search")
    print("  6. Load existing RAG database")
    print("  7. Interactive search mode")
    print("  8. Run all demos")
    print("  0. Exit")
    
    rag_db = None
    holding_db = None
    
    while True:
        choice = input("\nSelect demo (0-8): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
        
        elif choice == '1':
            rag_db = demo_basic_rag_generation()
        
        elif choice == '2':
            if rag_db is None:
                rag_db = demo_load_existing_rag()
            demo_semantic_search(rag_db)
        
        elif choice == '3':
            if rag_db is None:
                rag_db = demo_load_existing_rag()
            demo_filtered_search(rag_db)
        
        elif choice == '4':
            holding_db = demo_holding_level_rag()
        
        elif choice == '5':
            if holding_db is None:
                print("\n⚠️  Need to generate holding database first (Demo 4)")
            else:
                demo_cross_company_search(holding_db)
        
        elif choice == '6':
            rag_db = demo_load_existing_rag()
        
        elif choice == '7':
            if rag_db is None:
                rag_db = demo_load_existing_rag()
            interactive_search(rag_db)
        
        elif choice == '8':
            print("\n🚀 Running all demos...")
            rag_db = demo_basic_rag_generation()
            if rag_db:
                demo_semantic_search(rag_db)
                demo_filtered_search(rag_db)
            holding_db = demo_holding_level_rag()
            if holding_db:
                demo_cross_company_search(holding_db)
        
        else:
            print("❌ Invalid choice. Please select 0-8.")


if __name__ == "__main__":
    main()
