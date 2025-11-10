"""
Image adapter for pre-OCR processing

Stores image metadata and marks images for OCR processing.
Actual OCR happens in a separate pipeline stage.
"""

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import hashlib

from .base_adapter import BaseAdapter
from ..models.document_payload import DocumentPayload


class ImageAdapter(BaseAdapter):
    """
    Image file parsing adapter (pre-OCR)

    Handles image files by storing metadata and marking them for OCR
    processing. Does not perform actual OCR - that happens in the
    OCR pipeline stage (Task 4).

    Supported formats: JPEG, PNG, TIFF, BMP

    Example:
        >>> adapter = ImageAdapter()
        >>> payload = adapter.parse(Path('factura.jpg'), metadata)
        >>> payload.images[0]['needs_ocr']
        True
        >>> payload.content
        '[Imagen requiere OCR: factura.jpg]'
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """Image MIME types"""
        return [
            'image/jpeg',
            'image/png',
            'image/tiff',
            'image/bmp',
            'image/gif',
            'image/webp'
        ]

    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse image file metadata

        Creates placeholder payload with image metadata.
        Actual text extraction happens in OCR pipeline.

        Args:
            file_path: Path to image file
            metadata: Connector metadata

        Returns:
            DocumentPayload with image metadata and OCR flag

        Raises:
            ValueError: If image parsing fails
        """
        # Validate inputs
        self.validate_metadata(metadata)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo de imagen no encontrado: {file_path}"
            )

        start_time = datetime.now()

        try:
            # Get image file size
            file_size = file_path.stat().st_size

            # Create image metadata
            image_metadata = {
                'path': file_path,
                'filename': file_path.name,
                'format': file_path.suffix[1:].upper(),  # e.g., 'JPG'
                'file_size_bytes': file_size,
                'needs_ocr': True,
                'ocr_status': 'pending',
                'page': 1  # Images are single page
            }

            # Placeholder content (will be replaced by OCR)
            placeholder_content = (
                f"[Imagen requiere OCR: {file_path.name}]\n"
                f"Formato: {image_metadata['format']}\n"
                f"Tamaño: {file_size / 1024:.1f} KB"
            )

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
                source_format='image',
                mime_type=metadata.get('mime_type', 'image/jpeg'),
                original_path=file_path,

                # Content (placeholder until OCR)
                content=placeholder_content,
                language='unknown',  # Will be detected after OCR

                # Structure
                page_count=1,
                sections=[],
                tables=[],
                images=[image_metadata],

                # Processing metadata
                context_tags=metadata.get('context_tags', []),
                processed_at=start_time,
                processing_time_seconds=processing_time,

                # Additional metadata
                metadata={
                    **metadata,
                    'parser': 'ImageAdapter',
                    'requires_ocr': True,
                    'ocr_priority': metadata.get('ocr_priority', 'normal')
                }
            )

        except Exception as e:
            raise ValueError(
                f"Error procesando imagen {file_path.name}: {e}"
            )
