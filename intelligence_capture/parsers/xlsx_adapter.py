"""
Excel XLSX adapter using openpyxl/pandas

Parses Excel files and extracts sheets, tables, and structured data.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base_adapter import BaseAdapter
from ..models.document_payload import DocumentPayload


class XLSXAdapter(BaseAdapter):
    """
    Excel XLSX file parsing adapter

    Uses pandas with openpyxl engine to parse Excel files, extracting
    data from multiple sheets and converting to text representation.

    Example:
        >>> adapter = XLSXAdapter()
        >>> payload = adapter.parse(Path('reporte.xlsx'), metadata)
        >>> len(payload.tables)
        3  # One per sheet
        >>> payload.sections[0]['title']
        'Hoja: Ventas'
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """Excel MIME types"""
        return [
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.ms-excel'
        ]

    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse Excel XLSX file

        Reads all sheets from Excel file, converts each to text
        representation, and preserves table structures.

        Args:
            file_path: Path to XLSX file
            metadata: Connector metadata

        Returns:
            DocumentPayload with Excel data as text and table structures

        Raises:
            ValueError: If Excel parsing fails
        """
        # Validate inputs
        self.validate_metadata(metadata)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo Excel no encontrado: {file_path}"
            )

        start_time = datetime.now()

        try:
            # Read Excel file with all sheets
            excel_file = pd.ExcelFile(file_path, engine='openpyxl')

            content_parts = [
                f"Archivo Excel: {file_path.name}",
                f"Hojas: {len(excel_file.sheet_names)}",
                ""
            ]

            sections = []
            tables = []

            # Process each sheet
            for sheet_idx, sheet_name in enumerate(excel_file.sheet_names, 1):
                df = excel_file.parse(sheet_name)

                # Add section for this sheet
                sections.append({
                    'title': f"Hoja: {sheet_name}",
                    'level': 1,
                    'page': sheet_idx
                })

                # Sheet summary
                content_parts.append(f"## {sheet_name}")
                content_parts.append(f"Filas: {len(df)}")
                content_parts.append(f"Columnas: {', '.join(df.columns)}")
                content_parts.append("")

                # Add table data (limited to avoid huge payloads)
                max_rows = 100  # Limit rows in content
                for idx, row in df.head(max_rows).iterrows():
                    row_text = " | ".join(
                        f"{col}: {row[col]}"
                        for col in df.columns
                    )
                    content_parts.append(f"  Fila {idx + 1}: {row_text}")

                if len(df) > max_rows:
                    content_parts.append(
                        f"  ... ({len(df) - max_rows} filas adicionales)"
                    )

                content_parts.append("")

                # Add table structure
                tables.append({
                    'sheet_name': sheet_name,
                    'headers': list(df.columns),
                    'rows': df.values.tolist(),
                    'page': sheet_idx,
                    'row_count': len(df),
                    'column_count': len(df.columns)
                })

            full_content = '\n'.join(content_parts)

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
                source_format='xlsx',
                mime_type=self.supported_mime_types[0],
                original_path=file_path,

                # Content (Spanish preserved)
                content=full_content,
                language=language,

                # Structure
                page_count=len(excel_file.sheet_names),
                sections=sections,
                tables=tables,
                images=[],

                # Processing metadata
                context_tags=metadata.get('context_tags', []),
                processed_at=start_time,
                processing_time_seconds=processing_time,

                # Additional metadata
                metadata={
                    **metadata,
                    'parser': 'pandas+openpyxl',
                    'sheet_count': len(excel_file.sheet_names),
                    'sheet_names': excel_file.sheet_names,
                    'total_rows': sum(len(t['rows']) for t in tables),
                    'total_columns': sum(t['column_count'] for t in tables)
                }
            )

        except Exception as e:
            raise ValueError(
                f"Error procesando Excel {file_path.name}: {e}"
            )
