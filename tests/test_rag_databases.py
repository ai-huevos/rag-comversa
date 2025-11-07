"""
Tests for Company and Holding RAG Databases

Tests vector search, filtering, and cross-company capabilities.
"""
import pytest
import numpy as np
from pathlib import Path
from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import (
    RAGDatabaseGenerator,
    CompanyRAGDatabase,
    HoldingRAGDatabase,
    RAGDocument,
    EmbeddingGenerator
)
from intelligence_capture.config import OPENAI_API_KEY


@pytest.fixture
def test_db_with_multiple_entities():
    """Create test database with multiple entities for search testing"""
    db_path = Path("test_rag_db.db")
    
    if db_path.exists():
        db_path.unlink()
    
    db = EnhancedIntelligenceDB(db_path)
    db.connect()
    db.init_v2_schema()
    
    # Insert interview
    interview_id = db.insert_interview(
        meta={
            "company": "Hotel Los Tajibos",
            "respondent": "Test Manager",
            "role": "F&B Manager",
            "date": "2024-11-07"
        },
        qa_pairs={"q1": "test"}
    )
    
    # Insert multiple pain points with different characteristics
    db.insert_enhanced_pain_point(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        pain_point={
            "description": "Manual reconciliation between POS systems",
            "severity": "High",
            "intensity_score": 8,
            "hair_on_fire": True,
            "frequency": "Daily",
            "confidence_score": 0.95
        }
    )
    
    db.insert_enhanced_pain_point(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Hospitality",
        pain_point={
            "description": "Slow check-in process during peak hours",
            "severity": "Medium",
            "intensity_score": 6,
            "hair_on_fire": False,
            "frequency": "Weekly",
            "confidence_score": 0.85
        }
    )
    
    db.insert_enhanced_pain_point(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        pain_point={
            "description": "Inventory tracking errors in restaurant supplies",
            "severity": "Medium",
            "intensity_score": 5,
            "hair_on_fire": False,
            "frequency": "Monthly",
            "confidence_score": 0.80
        }
    )
    
    # Insert automation candidate
    db.insert_enhanced_automation_candidate(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        candidate={
            "name": "Automated POS reconciliation",
            "process": "Daily sales closing",
            "priority_quadrant": "Strategic",
            "effort_score": 3,
            "impact_score": 5,
            "confidence_score": 0.90
        }
    )
    
    yield db
    
    db.close()
    if db_path.exists():
        db_path.unlink()


def test_company_rag_database_creation(test_db_with_multiple_entities):
    """Test creating a company-specific RAG database"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Generate documents
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    
    # Create RAG database
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Verify database properties
    assert rag_db.company_name == "Hotel Los Tajibos"
    assert len(rag_db.documents) == len(documents)
    assert rag_db.embeddings_matrix is not None
    assert rag_db.embeddings_matrix.shape[0] == len(documents)
    assert rag_db.embeddings_matrix.shape[1] == 1536
    
    print(f"\n✅ Created RAG database with {len(documents)} documents")


def test_vector_search(test_db_with_multiple_entities):
    """Test semantic search using vector similarity"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Generate RAG database
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Generate query embedding
    query = "Problems with point of sale systems and reconciliation"
    query_embedding = generator.embedding_generator.generate_embedding(query)
    
    # Search
    results = rag_db.search(query_embedding, top_k=3)
    
    # Verify results
    assert len(results) > 0
    assert len(results) <= 3
    
    # Verify result structure
    for doc, score in results:
        assert isinstance(doc, RAGDocument)
        assert isinstance(score, float)
        assert 0 <= score <= 1  # Cosine similarity range
        assert doc.company == "Hotel Los Tajibos"
    
    # Verify results are sorted by similarity
    scores = [score for _, score in results]
    assert scores == sorted(scores, reverse=True)
    
    print(f"\n✅ Search returned {len(results)} results")
    print(f"   Top result: {results[0][0].entity_type} (score: {results[0][1]:.3f})")
    print(f"   Description: {results[0][0].text[:100]}...")


def test_filtered_search(test_db_with_multiple_entities):
    """Test search with entity type filters"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Generate RAG database with multiple entity types
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Search with filter for pain_points only
    query = "operational problems"
    query_embedding = generator.embedding_generator.generate_embedding(query)
    
    results = rag_db.search(
        query_embedding,
        top_k=5,
        filters={'entity_type': 'pain_point'}
    )
    
    # Verify all results are pain points
    assert all(doc.entity_type == 'pain_point' for doc, _ in results)
    
    print(f"\n✅ Filtered search returned {len(results)} pain_point results")


def test_business_unit_filter(test_db_with_multiple_entities):
    """Test filtering by business unit"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Search with business unit filter
    query = "operational issues"
    query_embedding = generator.embedding_generator.generate_embedding(query)
    
    results = rag_db.search(
        query_embedding,
        top_k=5,
        filters={'business_unit': 'Food & Beverage'}
    )
    
    # Verify all results are from Food & Beverage
    assert all(doc.business_unit == 'Food & Beverage' for doc, _ in results)
    
    print(f"\n✅ Business unit filter returned {len(results)} F&B results")


def test_get_by_id(test_db_with_multiple_entities):
    """Test retrieving documents by ID"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Get first document
    first_doc = documents[0]
    retrieved_doc = rag_db.get_by_id(first_doc.id)
    
    assert retrieved_doc is not None
    assert retrieved_doc.id == first_doc.id
    assert retrieved_doc.entity_type == first_doc.entity_type
    
    print(f"\n✅ Retrieved document by ID: {retrieved_doc.id}")


def test_get_by_entity(test_db_with_multiple_entities):
    """Test retrieving documents by entity type and ID"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    # Get pain point with ID 1
    doc = rag_db.get_by_entity('pain_point', 1)
    
    assert doc is not None
    assert doc.entity_type == 'pain_point'
    assert doc.entity_id == 1
    
    print(f"\n✅ Retrieved pain_point 1")


def test_rag_statistics(test_db_with_multiple_entities):
    """Test RAG database statistics"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    stats = rag_db.get_statistics()
    
    # Verify statistics structure
    assert 'company' in stats
    assert 'total_documents' in stats
    assert 'entity_types' in stats
    assert 'business_units' in stats
    
    assert stats['company'] == "Hotel Los Tajibos"
    assert stats['total_documents'] == len(documents)
    assert 'pain_point' in stats['entity_types']
    
    print(f"\n✅ Statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Entity types: {stats['entity_types']}")
    print(f"   Business units: {stats['business_units']}")


def test_save_and_load_company_rag(test_db_with_multiple_entities, tmp_path):
    """Test saving and loading company RAG database"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Generate and save
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)
    
    output_path = tmp_path / "hotel_rag.json"
    rag_db.save(output_path)
    
    # Load
    loaded_db = CompanyRAGDatabase.load(output_path)
    
    # Verify
    assert loaded_db.company_name == rag_db.company_name
    assert len(loaded_db.documents) == len(rag_db.documents)
    assert loaded_db.embeddings_matrix.shape == rag_db.embeddings_matrix.shape
    
    print(f"\n✅ Saved and loaded company RAG database")


def test_holding_rag_database_creation(test_db_with_multiple_entities):
    """Test creating holding-level RAG database"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Create company databases
    hotel_docs = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    hotel_db = CompanyRAGDatabase("Hotel Los Tajibos", hotel_docs)
    
    company_databases = {
        "Hotel Los Tajibos": hotel_db
    }
    
    # Create holding database
    holding_db = HoldingRAGDatabase(company_databases)
    
    # Verify
    assert len(holding_db.company_databases) == 1
    assert "Hotel Los Tajibos" in holding_db.company_databases
    assert len(holding_db.all_documents) == len(hotel_docs)
    assert holding_db.embeddings_matrix is not None
    
    print(f"\n✅ Created holding RAG database with {len(holding_db.all_documents)} documents")


def test_holding_cross_company_search(test_db_with_multiple_entities):
    """Test searching across companies in holding database"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    # Create holding database
    hotel_docs = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    hotel_db = CompanyRAGDatabase("Hotel Los Tajibos", hotel_docs)
    
    holding_db = HoldingRAGDatabase({"Hotel Los Tajibos": hotel_db})
    
    # Search across all companies
    query = "system integration problems"
    query_embedding = generator.embedding_generator.generate_embedding(query)
    
    results = holding_db.search(query_embedding, top_k=3)
    
    # Verify results
    assert len(results) > 0
    for doc, score in results:
        assert isinstance(doc, RAGDocument)
        assert isinstance(score, float)
    
    print(f"\n✅ Cross-company search returned {len(results)} results")


def test_holding_company_filter(test_db_with_multiple_entities):
    """Test filtering by company in holding database"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    hotel_docs = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    hotel_db = CompanyRAGDatabase("Hotel Los Tajibos", hotel_docs)
    
    holding_db = HoldingRAGDatabase({"Hotel Los Tajibos": hotel_db})
    
    # Search with company filter
    query = "operational issues"
    query_embedding = generator.embedding_generator.generate_embedding(query)
    
    results = holding_db.search(
        query_embedding,
        top_k=3,
        company_filter="Hotel Los Tajibos"
    )
    
    # Verify all results are from Hotel Los Tajibos
    assert all(doc.company == "Hotel Los Tajibos" for doc, _ in results)
    
    print(f"\n✅ Company-filtered search returned {len(results)} results")


def test_holding_statistics(test_db_with_multiple_entities):
    """Test holding-level statistics"""
    generator = RAGDatabaseGenerator(test_db_with_multiple_entities, OPENAI_API_KEY)
    
    hotel_docs = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    hotel_db = CompanyRAGDatabase("Hotel Los Tajibos", hotel_docs)
    
    holding_db = HoldingRAGDatabase({"Hotel Los Tajibos": hotel_db})
    
    stats = holding_db.get_statistics()
    
    # Verify structure
    assert 'total_documents' in stats
    assert 'companies' in stats
    assert 'entity_types' in stats
    assert 'Hotel Los Tajibos' in stats['companies']
    
    print(f"\n✅ Holding statistics:")
    print(f"   Total documents: {stats['total_documents']}")
    print(f"   Companies: {list(stats['companies'].keys())}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
