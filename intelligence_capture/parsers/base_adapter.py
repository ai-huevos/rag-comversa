"""
Base adapter interface for document parsing

This module defines the abstract base class that all document parsers
must implement to ensure consistent behavior across formats.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any

from ..models.document_payload import DocumentPayload


class BaseAdapter(ABC):
    """
    Abstract base class for document adapters

    All document format adapters must inherit from this class and implement
    the required methods. This ensures consistent parsing behavior and error
    handling across all supported formats.

    Example:
        >>> class MyAdapter(BaseAdapter):
        ...     @property
        ...     def supported_mime_types(self) -> List[str]:
        ...         return ['application/custom']
        ...
        ...     def parse(self, file_path, metadata):
        ...         # Parse logic here
        ...         return DocumentPayload(...)
    """

    @property
    @abstractmethod
    def supported_mime_types(self) -> List[str]:
        """
        MIME types this adapter handles

        Returns:
            List of MIME type strings (e.g., ['application/pdf'])

        Example:
            >>> adapter = PDFAdapter()
            >>> adapter.supported_mime_types
            ['application/pdf']
        """
        pass

    @abstractmethod
    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse document and return normalized payload

        This is the main entry point for document parsing. Implementations
        should extract text, structure, and metadata from the document
        and return a DocumentPayload with Spanish content preserved.

        Args:
            file_path: Path to document file to parse
            metadata: Metadata from connector containing:
                - document_id: UUID for this document
                - org_id: Organization identifier
                - checksum: SHA-256 checksum
                - source_type: Connector type (email, whatsapp, etc.)
                - context_tags: Access control tags from registry

        Returns:
            DocumentPayload with extracted content and structure

        Raises:
            ValueError: If parsing fails (with Spanish error message)
            FileNotFoundError: If file_path does not exist

        Example:
            >>> adapter = PDFAdapter()
            >>> metadata = {
            ...     'document_id': '550e8400-e29b-41d4-a716-446655440000',
            ...     'org_id': 'los_tajibos',
            ...     'checksum': 'abc123...',
            ...     'source_type': 'email',
            ...     'context_tags': ['hotel', 'operaciones']
            ... }
            >>> payload = adapter.parse(Path('document.pdf'), metadata)
            >>> print(payload.content[:100])  # Spanish content
        """
        pass

    def detect_language(self, text: str) -> str:
        """
        Detect document language using heuristics

        Uses stopword frequency analysis to determine if document is
        Spanish, English, or bilingual (es-en).

        Args:
            text: Text content to analyze (typically first 500 words)

        Returns:
            Language code: 'es', 'en', or 'es-en'

        Example:
            >>> adapter = PDFAdapter()
            >>> adapter.detect_language("El proceso de facturación...")
            'es'
            >>> adapter.detect_language("The invoicing process...")
            'en'
            >>> adapter.detect_language("El invoice process combina...")
            'es-en'
        """
        # Spanish stopwords (most common)
        spanish_stopwords = {
            'de', 'la', 'que', 'el', 'en', 'y', 'a', 'los', 'del', 'se',
            'las', 'por', 'un', 'para', 'con', 'no', 'una', 'su', 'al',
            'lo', 'como', 'más', 'pero', 'sus', 'le', 'ya', 'o', 'este'
        }

        # English stopwords (most common)
        english_stopwords = {
            'the', 'of', 'and', 'to', 'a', 'in', 'is', 'that', 'it', 'was',
            'for', 'on', 'are', 'with', 'as', 'be', 'at', 'by', 'this',
            'from', 'or', 'an', 'were', 'which', 'have', 'has', 'had'
        }

        # Analyze first 500 words (or less)
        words = text.lower().split()[:500]
        word_set = set(words)

        # Count stopword matches
        spanish_count = len(word_set & spanish_stopwords)
        english_count = len(word_set & english_stopwords)

        # Determine language based on ratio
        if spanish_count > english_count * 2:
            return 'es'  # Predominantly Spanish
        elif english_count > spanish_count * 2:
            return 'en'  # Predominantly English
        else:
            return 'es-en'  # Bilingual (mixed Spanish/English)

    def extract_sections(
        self,
        text: str,
        page_number: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Extract sections from text using simple heuristics

        Identifies potential section titles (lines starting with numbers,
        uppercase text, or common markers) and creates section metadata.

        Args:
            text: Text content to analyze
            page_number: Page number where text appears

        Returns:
            List of section dictionaries with title, content, level, page

        Example:
            >>> adapter = PDFAdapter()
            >>> sections = adapter.extract_sections("1. INTRODUCCIÓN\\n...")
            >>> sections[0]
            {'title': '1. INTRODUCCIÓN', 'level': 1, 'page': 1}
        """
        sections = []
        lines = text.split('\n')

        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Section indicators:
            # - Starts with number (e.g., "1. Introducción")
            # - All uppercase (e.g., "PROCEDIMIENTO")
            # - Starts with common markers (e.g., "Capítulo", "Sección")

            is_section = False
            level = 1

            # Number-prefixed sections
            if stripped and stripped[0].isdigit():
                is_section = True
                # Count dots to determine level (e.g., "1.2.3" = level 3)
                level = stripped.split()[0].count('.') + 1

            # Uppercase titles (min 3 chars, max 100 chars)
            elif (stripped.isupper() and
                  3 <= len(stripped) <= 100 and
                  not stripped.endswith(':')):
                is_section = True
                level = 1

            # Common section markers
            elif any(stripped.startswith(marker) for marker in [
                'Capítulo', 'Sección', 'Parte', 'Anexo', 'Apéndice'
            ]):
                is_section = True
                level = 1

            if is_section:
                sections.append({
                    'title': stripped,
                    'level': level,
                    'page': page_number
                })

        return sections

    def validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate required metadata fields

        Args:
            metadata: Metadata dictionary to validate

        Raises:
            ValueError: If required fields missing (Spanish error message)

        Example:
            >>> adapter.validate_metadata({'document_id': '...'})
            ValueError: "Campos requeridos faltantes: org_id, checksum..."
        """
        required_fields = [
            'document_id',
            'org_id',
            'checksum',
            'source_type'
        ]

        missing = [f for f in required_fields if f not in metadata]
        if missing:
            raise ValueError(
                f"Campos requeridos faltantes en metadata: {', '.join(missing)}"
            )
