"""
Tests for Embedding Generation

Tests the ability to generate vector embeddings for entity contexts.
"""
import pytest
import os
from pathlib import Path
from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import (
    EntityContextBuilder, 
    EmbeddingGenerator,
    RAGDatabaseGenerator
)
from intelligence_capture.config import OPENAI_API_KEY


@pytest.fixture
def test_db():
    """Create a test database with sample data"""
    db_path = Path("test_embedding_gen.db")
    
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
            "jtbd_formatted": "When closing daily sales, I want to reconcile all systems automatically, but I have to do it manually which takes 2 hours",
            "root_cause": "Systems not integrated",
            "confidence_score": 0.95
        }
    )
    
    # Insert test automation candidate
    db.insert_enhanced_automation_candidate(
        interview_id=interview_id,
        company="Hotel Los Tajibos",
        business_unit="Food & Beverage",
        candidate={
            "name": "Automatic Opera-Simphony-SAP integration",
            "process": "Daily sales closing",
            "action": "Automatically transfer sales data to SAP",
            "systems_involved": ["Opera PMS", "Simphony POS", "SAP"],
            "effort_score": 3,
            "impact_score": 5,
            "priority_quadrant": "Strategic",
            "estimated_roi_months": 6,
            "estimated_annual_savings_usd": 24000,
            "confidence_score": 0.93
        }
    )
    
    yield db
    
    # Cleanup
    db.close()
    if db_path.exists():
        db_path.unlink()


def test_embedding_generator_initialization():
    """Test that EmbeddingGenerator initializes correctly"""
    generator = EmbeddingGenerator(OPENAI_API_KEY)
    
    assert generator.api_key == OPENAI_API_KEY
    assert generator.model == "text-embedding-3-small"
    assert generator.embedding_dimensions == 1536
    
    print("\n✅ EmbeddingGenerator initialized correctly")


def test_generate_single_embedding():
    """Test generating embedding for a single text"""
    generator = EmbeddingGenerator(OPENAI_API_KEY)
    
    text = "This is a test text for embedding generation."
    
    embedding = generator.generate_embedding(text)
    
    # Verify embedding properties
    assert isinstance(embedding, list)
    assert len(embedding) == 1536  # text-embedding-3-small dimension
    assert all(isinstance(x, float) for x in embedding)
    
    # Verify embedding values are normalized (roughly between -1 and 1)
    assert all(-2 < x < 2 for x in embedding)
    
    print(f"\n✅ Generated embedding with {len(embedding)} dimensions")
    print(f"   Sample values: {embedding[:5]}")


def test_generate_embeddings_batch():
    """Test generating embeddings for multiple texts"""
    generator = EmbeddingGenerator(OPENAI_API_KEY)
    
    texts = [
        "First test text about hotel operations",
        "Second test text about restaurant management",
        "Third test text about system integration"
    ]
    
    embeddings = generator.generate_embeddings_batch(texts, batch_size=10)
    
    # Verify we got embeddings for all texts
    assert len(embeddings) == len(texts)
    
    # Verify each embedding has correct dimensions
    for embedding in embeddings:
        assert len(embedding) == 1536
        assert all(isinstance(x, float) for x in embedding)
    
    # Verify embeddings are different (semantic similarity)
    assert embeddings[0] != embeddings[1]
    assert embeddings[1] != embeddings[2]
    
    print(f"\n✅ Generated {len(embeddings)} embeddings in batch")


def test_generate_context_embedding(test_db):
    """Test generating embedding for an EntityContext"""
    builder = EntityContextBuilder(test_db)
    generator = EmbeddingGenerator(OPENAI_API_KEY)
    
    # Build context for pain point
    context = builder.build_context('pain_point', 1, depth=2)
    
    # Generate embedding
    embedding, metadata = generator.generate_context_embedding(context)
    
    # Verify embedding
    assert isinstance(embedding, list)
    assert len(embedding) == 1536
    
    # Verify metadata
    assert metadata['entity_id'] == 1
    assert metadata['entity_type'] == 'pain_point'
    assert metadata['company'] == "Hotel Los Tajibos"
    assert metadata['business_unit'] == "Food & Beverage"
    assert 'text_length' in metadata
    assert metadata['severity'] == 'High'
    
    print(f"\n✅ Generated context embedding with metadata")
    print(f"   Text length: {metadata['text_length']} chars")
    print(f"   Metadata keys: {list(metadata.keys())}")


def test_cost_estimation():
    """Test cost estimation for embedding generation"""
    generator = EmbeddingGenerator(OPENAI_API_KEY)
    
    # Estimate cost for 100 texts with 500 tokens each
    cost = generator.estimate_cost(num_texts=100, avg_tokens_per_text=500)
    
    # Verify cost is reasonable
    assert cost > 0
    assert cost < 1.0  # Should be less than $1 for 100 texts
    
    # text-embedding-3-small is $0.02 per 1M tokens
    # 100 texts * 500 tokens = 50,000 tokens = $0.001
    expected_cost = (100 * 500 / 1_000_000) * 0.02
    assert abs(cost - expected_cost) < 0.0001
    
    print(f"\n✅ Cost estimation working correctly")
    print(f"   100 texts (500 tokens each): ${cost:.4f}")


def test_rag_database_generator_initialization(test_db):
    """Test that RAGDatabaseGenerator initializes correctly"""
    generator = RAGDatabaseGenerator(test_db, OPENAI_API_KEY)
    
    assert generator.db == test_db
    assert isinstance(generator.context_builder, EntityContextBuilder)
    assert isinstance(generator.embedding_generator, EmbeddingGenerator)
    assert generator.documents == []
    
    print("\n✅ RAGDatabaseGenerator initialized correctly")


def test_generate_documents_for_company(test_db):
    """Test generating RAG documents for a company"""
    generator = RAGDatabaseGenerator(test_db, OPENAI_API_KEY)
    
    # Generate documents for Hotel Los Tajibos
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point', 'automation_candidate'],
        depth=1
    )
    
    # Verify documents were generated
    assert len(documents) > 0
    
    # Verify document structure
    for doc in documents:
        assert doc.company == "Hotel Los Tajibos"
        assert doc.entity_type in ['pain_point', 'automation_candidate']
        assert len(doc.embedding) == 1536
        assert len(doc.text) > 0
        assert 'entity_id' in doc.metadata
    
    print(f"\n✅ Generated {len(documents)} documents for Hotel Los Tajibos")
    print(f"   Entity types: {set(d.entity_type for d in documents)}")


def test_save_and_load_documents(test_db, tmp_path):
    """Test saving and loading RAG documents"""
    generator = RAGDatabaseGenerator(test_db, OPENAI_API_KEY)
    
    # Generate documents
    documents = generator.generate_documents_for_company(
        "Hotel Los Tajibos",
        entity_types=['pain_point'],
        depth=1
    )
    
    # Save documents
    output_path = tmp_path / "test_rag.json"
    generator.save_documents(documents, output_path)
    
    # Verify file was created
    assert output_path.exists()
    assert output_path.stat().st_size > 0
    
    # Load documents
    loaded_documents = generator.load_documents(output_path)
    
    # Verify loaded documents match original
    assert len(loaded_documents) == len(documents)
    
    for orig, loaded in zip(documents, loaded_documents):
        assert orig.id == loaded.id
        assert orig.entity_type == loaded.entity_type
        assert orig.company == loaded.company
        assert orig.embedding == loaded.embedding
        assert orig.text == loaded.text
    
    print(f"\n✅ Saved and loaded {len(documents)} documents successfully")


def test_estimate_generation_cost(test_db):
    """Test cost estimation for RAG database generation"""
    generator = RAGDatabaseGenerator(test_db, OPENAI_API_KEY)
    
    # Estimate cost for Hotel Los Tajibos
    estimate = generator.estimate_generation_cost("Hotel Los Tajibos")
    
    # Verify estimate structure
    assert 'total_entities' in estimate
    assert 'estimated_tokens' in estimate
    assert 'estimated_cost_usd' in estimate
    assert 'companies' in estimate
    
    # Verify values are reasonable
    assert estimate['total_entities'] > 0
    assert estimate['estimated_cost_usd'] > 0
    assert estimate['estimated_cost_usd'] < 1.0  # Should be very cheap for test data
    
    print(f"\n✅ Cost estimation:")
    print(f"   Total entities: {estimate['total_entities']}")
    print(f"   Estimated tokens: {estimate['estimated_tokens']:,}")
    print(f"   Estimated cost: ${estimate['estimated_cost_usd']:.4f}")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "-s"])
