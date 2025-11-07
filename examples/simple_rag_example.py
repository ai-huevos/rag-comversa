#!/usr/bin/env python3
"""
Simple RAG Example

Shows the most common use case: generate, search, save, load
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


def example_1_generate_and_search():
    """Example 1: Generate RAG database and search"""
    print("\n" + "="*60)
    print("EXAMPLE 1: Generate and Search")
    print("="*60)
    
    # Step 1: Connect to database
    db = EnhancedIntelligenceDB("intelligence.db")
    db.connect()
    
    # Step 2: Create RAG generator
    generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
    
    # Step 3: Generate documents
    print("\n📊 Generating RAG documents...")
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    
    # Step 4: Create searchable database
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    print(f"✅ Created database with {len(documents)} documents")
    
    # Step 5: Search
    print("\n🔍 Searching...")
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    query = "What are the main problems with restaurant operations?"
    query_embedding = embedding_gen.generate_embedding(query)
    
    results = rag_db.search(query_embedding, top_k=3)
    
    # Step 6: Show results
    print(f"\nQuery: '{query}'")
    print(f"Found {len(results)} results:\n")
    
    for i, (doc, score) in enumerate(results, 1):
        print(f"{i}. {doc.entity_type.upper()} (similarity: {score:.3f})")
        print(f"   {doc.text[:150]}...\n")
    
    db.close()
    return rag_db


def example_2_save_and_load():
    """Example 2: Save and load RAG database"""
    print("\n" + "="*60)
    print("EXAMPLE 2: Save and Load")
    print("="*60)
    
    # Generate database (or use existing from example 1)
    db = EnhancedIntelligenceDB("intelligence.db")
    db.connect()
    
    generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Save to disk
    output_path = Path("examples/hotel_rag.json")
    print(f"\n💾 Saving to {output_path}...")
    rag_db.save(output_path)
    
    # Load from disk (no API calls!)
    print(f"\n📂 Loading from {output_path}...")
    loaded_db = CompanyRAGDatabase.load(output_path)
    
    print(f"✅ Loaded {len(loaded_db.documents)} documents")
    
    # Search the loaded database
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    query = "system integration issues"
    query_embedding = embedding_gen.generate_embedding(query)
    
    results = loaded_db.search(query_embedding, top_k=2)
    
    print(f"\n🔍 Search results:")
    for doc, score in results:
        print(f"   {doc.entity_type}: {score:.3f}")
    
    db.close()


def example_3_filtered_search():
    """Example 3: Search with filters"""
    print("\n" + "="*60)
    print("EXAMPLE 3: Filtered Search")
    print("="*60)
    
    # Load existing database
    db_path = Path("examples/hotel_rag.json")
    if not db_path.exists():
        print("⚠️  Run example 2 first to create the database")
        return
    
    rag_db = CompanyRAGDatabase.load(db_path)
    
    # Search with filters
    embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)
    
    query = "operational problems"
    query_embedding = embedding_gen.generate_embedding(query)
    
    # Filter 1: Only pain points
    print("\n🔍 Filter: Only pain points")
    results = rag_db.search(
        query_embedding,
        top_k=3,
        filters={'entity_type': 'pain_point'}
    )
    
    for doc, score in results:
        print(f"   {doc.entity_type}: {score:.3f}")
    
    # Filter 2: Specific business unit
    print("\n🔍 Filter: Food & Beverage only")
    results = rag_db.search(
        query_embedding,
        top_k=3,
        filters={'business_unit': 'Food & Beverage'}
    )
    
    for doc, score in results:
        print(f"   {doc.business_unit}: {score:.3f}")


def example_4_get_by_id():
    """Example 4: Get specific documents"""
    print("\n" + "="*60)
    print("EXAMPLE 4: Get Specific Documents")
    print("="*60)
    
    db_path = Path("examples/hotel_rag.json")
    if not db_path.exists():
        print("⚠️  Run example 2 first")
        return
    
    rag_db = CompanyRAGDatabase.load(db_path)
    
    # Get by ID
    doc = rag_db.get_by_id("pain_point_1")
    if doc:
        print(f"\n📄 Document: {doc.id}")
        print(f"   Type: {doc.entity_type}")
        print(f"   Company: {doc.company}")
        print(f"   Text: {doc.text[:100]}...")
    
    # Get by entity type and ID
    doc = rag_db.get_by_entity('pain_point', 1)
    if doc:
        print(f"\n📄 Pain Point 1:")
        print(f"   {doc.text[:100]}...")


def main():
    """Run all examples"""
    print("\n" + "="*60)
    print("SIMPLE RAG EXAMPLES")
    print("="*60)
    print("\nThese examples show common RAG operations:")
    print("  1. Generate and search")
    print("  2. Save and load")
    print("  3. Filtered search")
    print("  4. Get specific documents")
    
    choice = input("\nRun which example? (1-4, or 'all'): ").strip()
    
    if choice == '1':
        example_1_generate_and_search()
    elif choice == '2':
        example_2_save_and_load()
    elif choice == '3':
        example_3_filtered_search()
    elif choice == '4':
        example_4_get_by_id()
    elif choice.lower() == 'all':
        example_1_generate_and_search()
        example_2_save_and_load()
        example_3_filtered_search()
        example_4_get_by_id()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
