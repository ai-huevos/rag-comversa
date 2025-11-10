"""
OCR module for multi-format document extraction
Supports Mistral Pixtral (primary) + Tesseract (fallback)
"""

from .mistral_pixtral_client import MistralPixtralClient
from .tesseract_fallback import TesseractFallback
from .ocr_coordinator import OCRCoordinator

__all__ = [
    'MistralPixtralClient',
    'TesseractFallback',
    'OCRCoordinator'
]
