"""
PDF document adapter using PyPDF2

Parses PDF files and extracts text, sections, and basic structure.
"""

import PyPDF2
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base_adapter import BaseAdapter
from ..models.document_payload import DocumentPayload


class PDFAdapter(BaseAdapter):
    """
    PDF document parsing adapter

    Uses PyPDF2 to extract text content, identify sections, and preserve
    page structure from PDF documents. Handles multi-page documents and
    preserves Spanish content without translation.

    Example:
        >>> adapter = PDFAdapter()
        >>> metadata = {
        ...     'document_id': '550e8400-...',
        ...     'org_id': 'los_tajibos',
        ...     'checksum': 'abc123...',
        ...     'source_type': 'email',
        ...     'context_tags': ['hotel']
        ... }
        >>> payload = adapter.parse(Path('manual.pdf'), metadata)
        >>> payload.page_count
        10
        >>> payload.language
        'es'
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """PDF MIME types"""
        return ['application/pdf']

    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse PDF document

        Extracts text from all pages, identifies sections using heuristics,
        and creates normalized DocumentPayload.

        Args:
            file_path: Path to PDF file
            metadata: Connector metadata

        Returns:
            DocumentPayload with extracted content

        Raises:
            ValueError: If PDF parsing fails (Spanish error message)
            FileNotFoundError: If file does not exist
        """
        # Validate inputs
        self.validate_metadata(metadata)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo PDF no encontrado: {file_path}"
            )

        start_time = datetime.now()

        try:
            with open(file_path, 'rb') as f:
                pdf = PyPDF2.PdfReader(f)

                # Extract text from all pages
                content_parts = []
                all_sections = []

                for page_num, page in enumerate(pdf.pages, 1):
                    # Extract text from page
                    page_text = page.extract_text()
                    content_parts.append(page_text)

                    # Extract sections from this page
                    page_sections = self.extract_sections(page_text, page_num)
                    all_sections.extend(page_sections)

                # Combine all page content
                full_content = '\n\n'.join(content_parts)

                # Detect language
                language = self.detect_language(full_content)

                # Calculate processing time
                processing_time = (datetime.now() - start_time).total_seconds()

                # Create payload
                return DocumentPayload(
                    # Identity
                    document_id=metadata['document_id'],
                    org_id=metadata['org_id'],
                    checksum=metadata['checksum'],

                    # Source metadata
                    source_type=metadata['source_type'],
                    source_format='pdf',
                    mime_type='application/pdf',
                    original_path=file_path,

                    # Content (Spanish preserved)
                    content=full_content,
                    language=language,

                    # Structure
                    page_count=len(pdf.pages),
                    sections=all_sections,
                    tables=[],  # Table extraction is complex, defer to OCR
                    images=[],  # Image extraction requires specialized tools

                    # Processing metadata
                    context_tags=metadata.get('context_tags', []),
                    processed_at=start_time,
                    processing_time_seconds=processing_time,

                    # Additional metadata
                    metadata={
                        **metadata,
                        'parser': 'PyPDF2',
                        'pdf_version': getattr(pdf, 'pdf_version', None),
                        'encrypted': pdf.is_encrypted
                    }
                )

        except PyPDF2.errors.PdfReadError as e:
            raise ValueError(
                f"Error al leer PDF {file_path.name}: {e}"
            )
        except Exception as e:
            raise ValueError(
                f"Error procesando PDF {file_path.name}: {e}"
            )
