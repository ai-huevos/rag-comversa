# RAG System Testing Guide

## Quick Start

### Option 1: Quick Test (Recommended First)
```bash
python scripts/quick_rag_test.py
```

This will:
- Check your intelligence.db
- Show database statistics
- Estimate cost (~$0.01-0.05)
- Generate a small RAG database
- Test semantic search
- Save the database for later use

**Time:** ~2-3 minutes  
**Cost:** ~$0.01-0.05

### Option 2: Full Interactive Demo
```bash
python scripts/demo_rag_system.py
```

This provides a menu with 7 demos:
1. Generate RAG database for Hotel Los Tajibos
2. Semantic search examples
3. Filtered search examples
4. Generate holding-level RAG database
5. Cross-company search
6. Load existing RAG database
7. Interactive search mode

## What You Can Test

### 1. Semantic Search
Ask natural language questions and get relevant results:
- "What are the biggest problems with POS systems?"
- "Which processes take the most time?"
- "What automation opportunities exist in restaurants?"

### 2. Filtered Search
Search with specific filters:
- Only pain points: `filters={'entity_type': 'pain_point'}`
- Specific business unit: `filters={'business_unit': 'Food & Beverage'}`
- High severity: `filters={'severity': 'High'}`

### 3. Cross-Company Analysis
Search across all companies to find:
- Common pain points
- Shared automation opportunities
- Best practices from one company applicable to others

### 4. Vector Similarity
Results are ranked by semantic similarity (0-1 score):
- 0.8-1.0: Very relevant
- 0.6-0.8: Relevant
- 0.4-0.6: Somewhat relevant
- <0.4: Not very relevant

## Prerequisites

1. **intelligence.db must exist**
   ```bash
   # If you don't have it, run:
   ./scripts/run_intelligence.sh
   ```

2. **OpenAI API key in .env**
   ```bash
   # Check your .env file has:
   OPENAI_API_KEY=sk-...
   ```

3. **Dependencies installed**
   ```bash
   pip install numpy  # Should already be installed
   ```

## Cost Estimates

Based on text-embedding-3-small pricing ($0.02 per 1M tokens):

| Scenario | Entities | Estimated Cost |
|----------|----------|----------------|
| Quick test (1 company, 2 entity types) | ~50-100 | $0.01-0.02 |
| Full company (all entity types) | ~200-500 | $0.02-0.05 |
| All 3 companies | ~600-1500 | $0.06-0.15 |

## Example Usage in Code

### Generate RAG Database
```python
from intelligence_capture.database import EnhancedIntelligenceDB
from intelligence_capture.rag_generator import RAGDatabaseGenerator
from intelligence_capture.config import OPENAI_API_KEY

# Connect to database
db = EnhancedIntelligenceDB("intelligence.db")
db.connect()

# Generate RAG
generator = RAGDatabaseGenerator(db, OPENAI_API_KEY)
documents = generator.generate_documents_for_company(
    "Hotel Los Tajibos",
    entity_types=['pain_point', 'automation_candidate'],
    depth=2
)

# Create searchable database
from intelligence_capture.rag_generator import CompanyRAGDatabase
rag_db = CompanyRAGDatabase("Hotel Los Tajibos", documents)

# Save for later
rag_db.save("hotel_rag.json")
```

### Search the Database
```python
from intelligence_capture.rag_generator import EmbeddingGenerator

# Create embedding generator
embedding_gen = EmbeddingGenerator(OPENAI_API_KEY)

# Search
query = "What are the biggest operational problems?"
query_embedding = embedding_gen.generate_embedding(query)
results = rag_db.search(query_embedding, top_k=5)

# Show results
for doc, score in results:
    print(f"{doc.entity_type}: {score:.3f}")
    print(doc.text[:200])
```

### Load Saved Database
```python
from intelligence_capture.rag_generator import CompanyRAGDatabase

# Load from disk (no API calls needed!)
rag_db = CompanyRAGDatabase.load("hotel_rag.json")

# Search immediately
results = rag_db.search(query_embedding, top_k=5)
```

## Troubleshooting

### "Database not found"
```bash
# Run intelligence capture first:
./scripts/run_intelligence.sh
```

### "No entities found"
Check which companies have data:
```python
db = EnhancedIntelligenceDB("intelligence.db")
db.connect()
stats = db.get_stats()
print(stats['by_company'])
```

### "API key error"
Check your .env file:
```bash
cat .env | grep OPENAI_API_KEY
```

### "Out of memory"
Reduce the number of entities:
```python
# Use fewer entity types
entity_types=['pain_point']  # Just pain points

# Or use shallow depth
depth=1  # Less relationship traversal
```

## What Gets Generated

### RAG Document Structure
Each document contains:
- **id**: Unique identifier (e.g., "pain_point_1")
- **entity_type**: Type of entity
- **company**: Company name
- **business_unit**: Business unit (if applicable)
- **text**: Full context with relationships
- **embedding**: 1536-dimensional vector
- **metadata**: Searchable attributes (severity, frequency, etc.)

### Saved Files
```
rag_databases/
├── hotel_los_tajibos_rag.json    # Company-specific
├── comversa_rag.json              # Company-specific
├── bolivian_foods_rag.json        # Company-specific
└── holding/
    ├── hotel_los_tajibos_rag.json
    ├── comversa_rag.json
    ├── bolivian_foods_rag.json
    └── holding_metadata.json       # Aggregated stats
```

## Performance Tips

1. **Start small**: Test with one company and 2 entity types first
2. **Use depth=1**: Faster generation, still good results
3. **Save databases**: Load from disk instead of regenerating
4. **Batch queries**: Generate multiple embeddings at once
5. **Filter early**: Use filters to reduce search space

## Next Steps

After testing:
1. Generate RAG databases for all companies
2. Integrate with AI agents for natural language queries
3. Build dashboards using the search API
4. Create automated reports from cross-company insights

## Support

- Check test files: `tests/test_rag_databases.py`
- Review implementation: `intelligence_capture/rag_generator.py`
- See examples: `scripts/demo_rag_system.py`
