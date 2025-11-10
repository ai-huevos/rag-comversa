"""
Sistema de chunking consciente del español para RAG 2.0

Módulo de chunking que maneja:
- Tokenización en español con spaCy
- Ventanas deslizantes (300-500 tokens, 50 tokens de superposición)
- Preservación de estructura Markdown
- Características específicas del español (stopwords, stemming)
"""

from .spanish_chunker import SpanishChunker
from .spanish_text_utils import SpanishTextUtils
from .chunk_metadata import ChunkMetadata

__all__ = [
    'SpanishChunker',
    'SpanishTextUtils',
    'ChunkMetadata'
]
