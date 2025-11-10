"""
Document parsers for multi-format support

This package provides adapters for parsing various document formats
into the normalized DocumentPayload structure.
"""

from .base_adapter import BaseAdapter
from .pdf_adapter import PDFAdapter
from .docx_adapter import DOCXAdapter
from .image_adapter import ImageAdapter
from .csv_adapter import CSVAdapter
from .xlsx_adapter import XLSXAdapter
from .whatsapp_adapter import WhatsAppAdapter

__all__ = [
    'BaseAdapter',
    'PDFAdapter',
    'DOCXAdapter',
    'ImageAdapter',
    'CSVAdapter',
    'XLSXAdapter',
    'WhatsAppAdapter'
]
