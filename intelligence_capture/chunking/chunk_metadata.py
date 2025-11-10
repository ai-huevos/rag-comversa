"""
Metadatos de chunk para rastreo y recuperación

Metadata builder para chunks de documentos que rastrea:
- Posición en documento original
- Características del texto en español
- Información estructural (secciones, páginas)
- Tipos de contenido (tablas, listas, código)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Tuple


@dataclass
class ChunkMetadata:
    """
    Metadatos para chunk de documento

    Attributes:
        document_id: ID del documento fuente
        chunk_index: Índice del chunk en secuencia
        token_count: Número de tokens en el chunk
        char_count: Número de caracteres en el chunk
        span_offsets: (inicio, fin) posiciones de caracteres en documento original
        section_title: Título de sección si está disponible
        page_number: Número de página si está disponible
        heading_level: Nivel de encabezado (1-6) si aplica
        spanish_features: Características de texto en español
        contains_table: Si el chunk contiene datos tabulares
        contains_list: Si el chunk contiene listas
        contains_code: Si el chunk contiene código
    """
    document_id: str
    chunk_index: int
    token_count: int
    char_count: int
    span_offsets: Tuple[int, int]  # (start, end) character positions

    # Información estructural
    section_title: Optional[str] = None
    page_number: Optional[int] = None
    heading_level: Optional[int] = None

    # Características del español
    spanish_features: Dict[str, Any] = field(default_factory=dict)

    # Tipos de contenido
    contains_table: bool = False
    contains_list: bool = False
    contains_code: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """
        Convertir a diccionario para serialización JSON

        Returns:
            Diccionario con todos los metadatos (ensure_ascii=False para español)
        """
        return {
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'token_count': self.token_count,
            'char_count': self.char_count,
            'span_offsets': list(self.span_offsets),  # Convert tuple to list for JSON
            'section_title': self.section_title,
            'page_number': self.page_number,
            'heading_level': self.heading_level,
            'spanish_features': self.spanish_features,
            'contains_table': self.contains_table,
            'contains_list': self.contains_list,
            'contains_code': self.contains_code
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChunkMetadata':
        """
        Crear desde diccionario

        Args:
            data: Diccionario de metadatos

        Returns:
            Instancia de ChunkMetadata
        """
        # Convert list back to tuple for span_offsets
        if 'span_offsets' in data and isinstance(data['span_offsets'], list):
            data['span_offsets'] = tuple(data['span_offsets'])

        return cls(**data)
