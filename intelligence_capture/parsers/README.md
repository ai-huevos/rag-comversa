# Multi-Format Document Parsers

Document parsing adapters for RAG 2.0 multi-format ingestion pipeline.

## Overview

This package provides format-specific adapters that convert various document types into a normalized `DocumentPayload` structure for downstream processing (chunking, embedding, entity extraction).

**Design Pattern**: Strategy pattern with `BaseAdapter` abstract class
**MIME Detection**: python-magic library
**Content Preservation**: Spanish content NEVER translated

## Supported Formats

| Adapter | MIME Types | Features |
|---------|-----------|----------|
| **PDFAdapter** | `application/pdf` | Text extraction, section detection, multi-page |
| **DOCXAdapter** | `application/vnd...wordprocessingml.document` | Headings, paragraphs, tables |
| **ImageAdapter** | `image/jpeg`, `image/png`, `image/tiff`, etc. | Metadata, OCR placeholder |
| **CSVAdapter** | `text/csv`, `application/csv` | Table structure, pandas parsing |
| **XLSXAdapter** | `application/vnd...spreadsheetml.sheet` | Multi-sheet, per-sheet tables |
| **WhatsAppAdapter** | `application/json` | Messages, participants, chronology |

## Architecture

```
┌─────────────────┐
│ DocumentProcessor│  ← Orchestrator
└────────┬────────┘
         │ (MIME detection)
         ├──► PDFAdapter      ──► DocumentPayload
         ├──► DOCXAdapter     ──► DocumentPayload
         ├──► ImageAdapter    ──► DocumentPayload
         ├──► CSVAdapter      ──► DocumentPayload
         ├──► XLSXAdapter     ──► DocumentPayload
         └──► WhatsAppAdapter ──► DocumentPayload
```

## Usage

### Basic Processing

```python
from intelligence_capture.document_processor import DocumentProcessor
from pathlib import Path

# Initialize processor
processor = DocumentProcessor()

# Prepare metadata
metadata = {
    'document_id': '550e8400-e29b-41d4-a716-446655440000',
    'org_id': 'los_tajibos',
    'checksum': 'abc123...',
    'source_type': 'email',
    'context_tags': ['hotel', 'operaciones']
}

# Process document (auto-detects format)
payload = processor.process(
    Path('data/documents/inbox/manual.pdf'),
    metadata
)

# Access parsed content
print(f"Format: {payload.source_format}")
print(f"Language: {payload.language}")
print(f"Pages: {payload.page_count}")
print(f"Sections: {len(payload.sections)}")
print(f"Content: {payload.content[:100]}...")
```

### Direct Adapter Usage

```python
from intelligence_capture.parsers import PDFAdapter
from pathlib import Path

adapter = PDFAdapter()

# Parse PDF
payload = adapter.parse(
    Path('document.pdf'),
    metadata={'document_id': '...', 'org_id': '...', ...}
)

# Language detection
language = adapter.detect_language(payload.content)  # 'es', 'en', or 'es-en'

# Section extraction
sections = adapter.extract_sections(payload.content, page_number=1)
```

## DocumentPayload Schema

```python
@dataclass
class DocumentPayload:
    # Identity
    document_id: str                  # UUID
    org_id: str                      # Organization ID
    checksum: str                    # SHA-256 checksum

    # Source metadata
    source_type: str                 # email, whatsapp, api, sharepoint
    source_format: str               # pdf, docx, image, csv, xlsx, json
    mime_type: str                   # Detected MIME type
    original_path: Path              # Path to original file

    # Content (ALWAYS Spanish - never translate)
    content: str                     # Extracted text
    language: str                    # es, en, or es-en

    # Structure
    page_count: int                  # Number of pages/sections
    sections: List[Dict]             # [{title, content, level, page}]
    tables: List[Dict]               # [{headers, rows, page}]
    images: List[Dict]               # [{path, caption, page, needs_ocr}]

    # Processing metadata
    context_tags: List[str]          # Access control tags
    processed_at: datetime           # Processing timestamp
    processing_time_seconds: float   # Processing duration

    # Additional metadata
    metadata: Dict[str, Any]         # Connector-specific metadata
```

## Adapter Details

### PDFAdapter

**Library**: PyPDF2

**Capabilities**:
- Text extraction from all pages
- Basic section detection (numbered, uppercase, markers)
- Page-level content organization
- Preserves Spanish accents and special characters

**Limitations**:
- Complex table extraction deferred to OCR
- Image extraction not supported (use ImageAdapter for scanned PDFs)

**Example Output**:
```python
payload.page_count = 10
payload.sections = [
    {'title': '1. INTRODUCCIÓN', 'level': 1, 'page': 1},
    {'title': '2. PROCEDIMIENTO', 'level': 1, 'page': 2},
    {'title': '2.1. Paso Inicial', 'level': 2, 'page': 2}
]
```

### DOCXAdapter

**Library**: python-docx

**Capabilities**:
- Paragraph extraction
- Heading hierarchy detection (Heading 1, Heading 2, etc.)
- Table extraction with headers and rows
- Preserves document structure

**Limitations**:
- No page concept (DOCX is continuous)
- Image extraction requires specialized handling

**Example Output**:
```python
payload.sections = [
    {'title': 'Procedimiento de Check-In', 'level': 1, 'page': 1},
    {'title': 'Verificación de Reserva', 'level': 2, 'page': 1}
]
payload.tables = [
    {
        'headers': ['Paso', 'Responsable', 'Duración'],
        'rows': [['1', 'Recepcionista', '5 min'], ...],
        'page': 1
    }
]
```

### ImageAdapter

**Purpose**: Pre-OCR metadata extraction

**Capabilities**:
- Image file metadata
- OCR status tracking (pending/in_progress/completed)
- Placeholder content until OCR completes

**Workflow**:
1. ImageAdapter creates DocumentPayload with `needs_ocr=True`
2. OCR pipeline (Task 4) processes image
3. OCR results replace placeholder content

**Example Output**:
```python
payload.images = [
    {
        'path': Path('factura.jpg'),
        'filename': 'factura.jpg',
        'format': 'JPG',
        'file_size_bytes': 245678,
        'needs_ocr': True,
        'ocr_status': 'pending'
    }
]
payload.content = "[Imagen requiere OCR: factura.jpg]"
```

### CSVAdapter

**Library**: pandas

**Capabilities**:
- CSV parsing with UTF-8 encoding
- Table structure preservation
- Text representation for embedding

**Example Output**:
```python
payload.tables = [
    {
        'headers': ['Producto', 'Cantidad', 'Precio'],
        'rows': [
            ['Toalla', '50', '25.00'],
            ['Sábana', '30', '45.00']
        ],
        'row_count': 2,
        'column_count': 3
    }
]
payload.content = "Archivo CSV: inventario.csv\nFilas: 2\n..."
```

### XLSXAdapter

**Library**: pandas + openpyxl

**Capabilities**:
- Multi-sheet support
- Per-sheet table extraction
- Sheet metadata tracking

**Example Output**:
```python
payload.page_count = 3  # 3 sheets
payload.sections = [
    {'title': 'Hoja: Ventas', 'level': 1, 'page': 1},
    {'title': 'Hoja: Inventario', 'level': 1, 'page': 2}
]
payload.tables = [
    {'sheet_name': 'Ventas', 'headers': [...], 'rows': [...]},
    {'sheet_name': 'Inventario', 'headers': [...], 'rows': [...]}
]
```

### WhatsAppAdapter

**Format**: JSON export

**Expected JSON Structure**:
```json
[
    {
        "timestamp": "2024-01-15T10:30:00",
        "sender": "Patricia García",
        "message": "¿Cómo va el proceso de facturación?"
    },
    ...
]
```

**Capabilities**:
- Participant extraction
- Chronological message ordering
- Day-based section organization
- Conversation metadata

**Example Output**:
```python
payload.metadata = {
    'message_count': 150,
    'participant_count': 5,
    'participants': ['Patricia García', 'Samuel Rodríguez', ...]
}
payload.sections = [
    {'title': 'Fecha: 2024-01-15', 'level': 1, 'page': 1},
    {'title': 'Fecha: 2024-01-16', 'level': 1, 'page': 1}
]
```

## State Management

DocumentProcessor manages document lifecycle through state directories:

```
data/documents/
├── inbox/          ← Incoming from connectors
├── processing/     ← Currently being processed
├── processed/      ← Successfully processed
├── failed/         ← Failed with error logs
└── originals/      ← Archived originals (UUID-named)
```

**Processing Flow**:
1. File arrives in `inbox/`
2. Moved to `processing/` during parse
3. Original copied to `originals/{uuid}`
4. Checksum verified
5. Moved to `processed/` on success OR `failed/` on error

**Error Handling**:
- Failed documents moved to `failed/` with `.error.txt` log
- Error logs include: error message, file name, MIME type, timestamp, metadata
- All error messages in Spanish

## Language Detection

**Heuristic**: Stopword frequency analysis

```python
spanish_stopwords = {'de', 'la', 'que', 'el', 'en', ...}
english_stopwords = {'the', 'of', 'and', 'to', 'a', ...}

spanish_count = len(words & spanish_stopwords)
english_count = len(words & english_stopwords)

if spanish_count > english_count * 2:
    return 'es'
elif english_count > spanish_count * 2:
    return 'en'
else:
    return 'es-en'  # Bilingual
```

## Section Extraction

**Heuristics** for identifying sections:

1. **Number-prefixed**: `1. Introducción`, `2.1. Paso inicial`
2. **Uppercase titles**: `PROCEDIMIENTO`, `CONCLUSIONES`
3. **Common markers**: `Capítulo`, `Sección`, `Parte`, `Anexo`

**Example**:
```python
sections = [
    {'title': '1. INTRODUCCIÓN', 'level': 1, 'page': 1},
    {'title': '2. PROCESO', 'level': 1, 'page': 2},
    {'title': '2.1. Verificación', 'level': 2, 'page': 2}
]
```

## Testing

### Unit Tests

```bash
pytest tests/test_document_processor.py -v
```

Tests cover:
- DocumentPayload creation and serialization
- Language detection (Spanish/English/bilingual)
- Section extraction
- All 6 adapters
- Spanish content preservation
- UTF-8 encoding

### Integration Tests

```bash
python scripts/test_document_processing.py
python scripts/test_document_processing.py --format csv
python scripts/test_document_processing.py --verbose
```

Tests end-to-end processing with:
- CSV files
- WhatsApp JSON exports
- Text/Markdown files
- Spanish preservation validation
- Processor statistics

## Best Practices

### ✅ DO

- **Preserve Spanish**: Never translate content
- **Use UTF-8**: Explicit encoding in all file operations
- **Validate metadata**: Check required fields before processing
- **Log errors**: Write detailed Spanish error logs to `failed/`
- **Verify checksums**: Confirm data integrity after processing

### ❌ DON'T

- **Never translate**: Spanish content must remain in Spanish
- **No ensure_ascii=True**: Always use `ensure_ascii=False` in JSON
- **No silent failures**: Always log errors with context
- **No hardcoded paths**: Use configurable base directories
- **No missing type hints**: All functions need type annotations

## Integration with RAG 2.0 Pipeline

```
Connectors (Task 1-2) → Queue (Task 2) → DocumentProcessor (Task 3)
                                                    ↓
                                          DocumentPayload
                                                    ↓
                                              OCR (Task 4)
                                                    ↓
                                           Chunking (Task 5)
                                                    ↓
                                           Embeddings (Task 7)
                                                    ↓
                                    PostgreSQL + Neo4j (Tasks 6-9)
```

## Dependencies

```
PyPDF2>=3.0.0              # PDF parsing
python-docx>=0.8.11        # DOCX parsing
python-magic>=0.4.27       # MIME type detection
pandas>=2.0.0              # CSV/XLSX parsing
openpyxl>=3.1.2            # Excel file support
```

Install:
```bash
pip install -r requirements-rag2.txt
```

## Next Steps

- **Task 4**: Wire OCR engine (Mistral Pixtral + Tesseract fallback)
- **Task 5**: Implement Spanish-aware chunking (300-500 tokens, spacy)
- **Task 8**: Connect to PostgreSQL document persistence
- **Integration**: Link with connectors and ingestion queue

## References

- **Design**: `.kiro/specs/rag-2.0-enhancement/design.md`
- **Tasks**: `.kiro/specs/rag-2.0-enhancement/tasks.md` (Task 3)
- **Coding Standards**: `.ai/CODING_STANDARDS.md`
- **Main Docs**: `CLAUDE.md` section 2.5
