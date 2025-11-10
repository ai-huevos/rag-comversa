# Spanish-Aware Chunking System

Sistema de chunking consciente del español para RAG 2.0 con ventanas deslizantes y preservación de estructura Markdown.

## Características

- **Tokenización en español**: spaCy `es_core_news_md`
- **Ventanas deslizantes**: 300-500 tokens con 50 tokens de superposición
- **Ajuste a límites de oraciones**: Evita cortes en medio de oraciones
- **Preservación de Markdown**: Mantiene encabezados, tablas y estructura
- **Detección de contenido**: Tablas, listas, bloques de código
- **Características del español**: Stopwords, stemming, acentos

## Instalación

```bash
# Instalar dependencias
pip install spacy>=3.7.0 nltk>=3.8.0

# Descargar modelo spaCy español
python -m spacy download es_core_news_md
```

## Uso Básico

```python
from intelligence_capture.chunking import SpanishChunker
from intelligence_capture.models.document_payload import DocumentPayload

# Inicializar chunker
chunker = SpanishChunker()

# Crear payload de documento
payload = DocumentPayload(
    document_id="doc-123",
    org_id="los_tajibos",
    checksum="abc...",
    source_type="email",
    source_format="txt",
    mime_type="text/plain",
    original_path=Path("/ruta/documento.txt"),
    content="La reconciliación manual de facturas...",  # Contenido en español
    language="es",
    page_count=1
)

# Dividir documento en chunks
chunks = chunker.chunk_document(payload)

# Procesar chunks
for chunk in chunks:
    print(f"Chunk {chunk['metadata']['chunk_index']}")
    print(f"  Tokens: {chunk['metadata']['token_count']}")
    print(f"  Contenido: {chunk['content'][:100]}...")
```

## Preservación de Markdown

Para documentos con estructura Markdown (encabezados, tablas):

```python
# Usar método con preservación de Markdown
chunks = chunker.chunk_with_markdown_preservation(payload)

# Los chunks preservan encabezados al inicio
for chunk in chunks:
    metadata = chunk['metadata']
    if metadata['heading_level']:
        print(f"Chunk de sección nivel {metadata['heading_level']}")
    if metadata['contains_table']:
        print("Contiene tabla")
    if metadata['contains_list']:
        print("Contiene lista")
```

## Metadatos de Chunks

Cada chunk incluye metadatos completos:

```python
chunk['metadata'] = {
    'document_id': 'doc-123',
    'chunk_index': 0,

    # Tamaño
    'token_count': 400,
    'char_count': 2500,
    'span_offsets': [0, 2500],  # Posición en documento original

    # Estructura
    'section_title': 'Introducción',
    'page_number': 1,
    'heading_level': 2,

    # Características del español
    'spanish_features': {
        'total_words': 350,
        'stopword_count': 120,
        'stopword_ratio': 0.34,
        'unique_stems': 180,
        'has_accents': True,
        'avg_word_length': 6.2,
        'lexical_diversity': 0.51
    },

    # Tipos de contenido
    'contains_table': False,
    'contains_list': True,
    'contains_code': False
}
```

## Utilidades de Texto Español

```python
from intelligence_capture.chunking import SpanishTextUtils

utils = SpanishTextUtils()

# Eliminar stopwords
texto = "el sistema de gestión no funciona bien"
sin_stopwords = utils.remove_stopwords(texto)
# Resultado: "sistema gestión funciona bien"

# Stemming
stems = utils.stem_text("trabajamos trabajando trabajador trabajo")
# Resultado: ['trabaj', 'trabaj', 'trabaj', 'trabaj']

# Extraer características
features = utils.extract_features(texto)
print(features['stopword_ratio'])  # 0.375
print(features['has_accents'])     # False

# Detectar español
es_espanol = utils.is_spanish(texto)  # True
```

## Parámetros de Chunking

```python
chunker = SpanishChunker()

# Parámetros (configurables en __init__)
chunker.min_tokens = 300       # Mínimo de tokens por chunk
chunker.max_tokens = 500       # Máximo de tokens por chunk
chunker.overlap_tokens = 50    # Superposición entre chunks
chunker.target_tokens = 400    # Objetivo (punto medio del rango)
```

## Ejemplo Completo: Transcripción de Entrevista

```python
from pathlib import Path
from intelligence_capture.chunking import SpanishChunker
from intelligence_capture.models.document_payload import DocumentPayload

# Leer transcripción
with open('entrevista.txt', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Crear payload
payload = DocumentPayload(
    document_id="entrevista-001",
    org_id="los_tajibos",
    checksum="abc123",
    source_type="interview",
    source_format="txt",
    mime_type="text/plain",
    original_path=Path("entrevista.txt"),
    content=contenido,
    language="es",
    page_count=1,
    context_tags=["finanzas", "reconciliacion", "procesos"]
)

# Chunkar
chunker = SpanishChunker()
chunks = chunker.chunk_document(payload)

print(f"Generados {len(chunks)} chunks")

# Analizar chunks
for i, chunk in enumerate(chunks):
    meta = chunk['metadata']

    print(f"\nChunk {i + 1}:")
    print(f"  Tokens: {meta['token_count']}")
    print(f"  Offset: {meta['span_offsets']}")

    # Características del español
    spanish = meta['spanish_features']
    print(f"  Palabras: {spanish['total_words']}")
    print(f"  Ratio stopwords: {spanish['stopword_ratio']:.2f}")
    print(f"  Tiene acentos: {spanish['has_accents']}")

    # Vista previa
    preview = chunk['content'][:150]
    print(f"  Vista previa: {preview}...")
```

## Tests

```bash
# Tests unitarios
pytest tests/test_spanish_chunker.py -v

# Tests de integración con fixtures reales
pytest tests/test_spanish_chunker_integration.py -v

# Todos los tests con cobertura
pytest tests/test_spanish_chunker*.py --cov=intelligence_capture.chunking --cov-report=html
```

## Arquitectura

```
intelligence_capture/chunking/
├── __init__.py                  # Exportaciones del paquete
├── chunk_metadata.py            # Dataclass de metadatos
├── spanish_text_utils.py        # Utilidades NLP español
└── spanish_chunker.py           # Motor principal de chunking
```

## Limitaciones Conocidas

1. **Mapeo de secciones**: Implementación simple - producción necesita mapeo preciso de offsets
2. **Dependencia de modelo**: Requiere descarga separada de `es_core_news_md`
3. **Detección de oraciones**: Depende de spaCy (generalmente robusto para español)

## Rendimiento

- **Velocidad**: ~1000 tokens/segundo con spaCy
- **Memoria**: Procesamiento eficiente en un solo paso
- **Escalabilidad**: Lineal con tamaño de documento

## Próximos Pasos

1. **Integración con PostgreSQL** (Task 6): Tabla `document_chunks`
2. **Pipeline de embeddings** (Task 7): Vectorización de chunks
3. **Persistencia atómica** (Task 8): Transacciones documento + chunks

## Soporte

Para problemas o preguntas:
1. Revisar tests de integración para ejemplos
2. Consultar `.ai/CODING_STANDARDS.md` para patrones
3. Ver `reports/task_5_implementation_summary.md` para detalles

---

**Versión**: 1.0.0
**Fecha**: Noviembre 9, 2025
**Agente**: intake_processing (backend-architect)
