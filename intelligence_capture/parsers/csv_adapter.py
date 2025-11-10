"""
CSV adapter using pandas

Parses CSV files and converts them to structured text representation.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base_adapter import BaseAdapter
from ..models.document_payload import DocumentPayload


class CSVAdapter(BaseAdapter):
    """
    CSV file parsing adapter

    Uses pandas to parse CSV files and convert tabular data into
    structured text representation suitable for chunking and embedding.

    Example:
        >>> adapter = CSVAdapter()
        >>> payload = adapter.parse(Path('datos.csv'), metadata)
        >>> payload.tables[0]['headers']
        ['Producto', 'Cantidad', 'Precio']
        >>> 'csv_rows' in payload.metadata
        True
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """CSV MIME types"""
        return [
            'text/csv',
            'application/csv',
            'text/plain'  # CSVs sometimes detected as plain text
        ]

    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse CSV file

        Reads CSV using pandas, converts to text representation,
        and preserves table structure.

        Args:
            file_path: Path to CSV file
            metadata: Connector metadata

        Returns:
            DocumentPayload with CSV data as text and table structure

        Raises:
            ValueError: If CSV parsing fails
        """
        # Validate inputs
        self.validate_metadata(metadata)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo CSV no encontrado: {file_path}"
            )

        start_time = datetime.now()

        try:
            # Read CSV with UTF-8 encoding (handles Spanish characters)
            df = pd.read_csv(file_path, encoding='utf-8')

            # Convert to text representation
            content_parts = [
                f"Archivo CSV: {file_path.name}",
                f"Filas: {len(df)}",
                f"Columnas: {', '.join(df.columns)}",
                "",
                "Datos:"
            ]

            # Add table in text format
            for idx, row in df.iterrows():
                row_text = " | ".join(
                    f"{col}: {row[col]}"
                    for col in df.columns
                )
                content_parts.append(f"Fila {idx + 1}: {row_text}")

            full_content = '\n'.join(content_parts)

            # Create table structure
            table = {
                'headers': list(df.columns),
                'rows': df.values.tolist(),
                'page': 1,
                'row_count': len(df),
                'column_count': len(df.columns)
            }

            # Detect language from content
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
                source_format='csv',
                mime_type='text/csv',
                original_path=file_path,

                # Content (Spanish preserved)
                content=full_content,
                language=language,

                # Structure
                page_count=1,
                sections=[],
                tables=[table],
                images=[],

                # Processing metadata
                context_tags=metadata.get('context_tags', []),
                processed_at=start_time,
                processing_time_seconds=processing_time,

                # Additional metadata
                metadata={
                    **metadata,
                    'parser': 'pandas',
                    'csv_rows': len(df),
                    'csv_columns': len(df.columns),
                    'column_names': list(df.columns)
                }
            )

        except pd.errors.ParserError as e:
            raise ValueError(
                f"Error al parsear CSV {file_path.name}: {e}"
            )
        except Exception as e:
            raise ValueError(
                f"Error procesando CSV {file_path.name}: {e}"
            )
