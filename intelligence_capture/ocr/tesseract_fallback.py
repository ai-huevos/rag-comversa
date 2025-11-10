"""
Tesseract OCR fallback for low-cost extraction
Used when Mistral Pixtral fails or for batch processing with cost constraints
"""

import pytesseract
from PIL import Image
from pathlib import Path
from typing import Dict, Any, List


class TesseractFallback:
    """Tesseract OCR fallback para extracción de bajo costo"""

    def __init__(self):
        """
        Inicializar Tesseract OCR fallback

        Raises:
            ValueError: Si Tesseract no está instalado en el sistema
        """
        # Verificar que Tesseract está instalado
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise ValueError(
                "Tesseract no está instalado. "
                "Instalar: brew install tesseract (macOS) | "
                "apt-get install tesseract-ocr (Ubuntu) | "
                f"Error: {e}"
            )

    def extract_text(
        self,
        image_path: Path,
        language: str = "spa"  # Tesseract usa "spa" para español
    ) -> Dict[str, Any]:
        """
        Extraer texto usando Tesseract OCR

        Args:
            image_path: Ruta al archivo de imagen
            language: Código de idioma de Tesseract (spa=español, eng=inglés)

        Returns:
            Dict con mismo formato que MistralPixtralClient:
            - text: Texto extraído
            - confidence: Confianza promedio
            - bounding_boxes: Lista de cajas delimitadoras con confianza
            - language_detected: Idioma usado
            - ocr_engine: "tesseract"
            - metadata: Versión de Tesseract y metadatos

        Raises:
            ValueError: Si extracción falla con mensaje en español
        """
        try:
            # Abrir imagen
            image = Image.open(image_path)

            # Extraer texto con datos de confianza
            data = pytesseract.image_to_data(
                image,
                lang=language,
                output_type=pytesseract.Output.DICT,
                config='--psm 1'  # Automatic page segmentation with OSD
            )

            # Combinar texto y calcular métricas
            text_parts = []
            bounding_boxes = []
            confidences = []

            for i, text in enumerate(data['text']):
                if text.strip():  # Solo texto no vacío
                    text_parts.append(text)

                    # Confianza de Tesseract (0-100) convertida a 0.0-1.0
                    conf = float(data['conf'][i]) / 100.0 if data['conf'][i] != -1 else 0.0
                    confidences.append(conf)

                    # Caja delimitadora
                    bounding_boxes.append({
                        'text': text,
                        'bbox': [
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ],
                        'confidence': conf
                    })

            # Texto completo
            full_text = ' '.join(text_parts)

            # Confianza promedio (solo palabras con conf > 0)
            valid_confidences = [c for c in confidences if c > 0]
            avg_confidence = (
                sum(valid_confidences) / len(valid_confidences)
                if valid_confidences
                else 0.0
            )

            # Detectar texto vacío o muy corto (posible falla)
            if len(full_text.strip()) < 10:
                avg_confidence *= 0.5  # Reducir confianza para texto muy corto

            return {
                'text': full_text,
                'confidence': avg_confidence,
                'bounding_boxes': bounding_boxes,
                'language_detected': language,
                'ocr_engine': 'tesseract',
                'metadata': {
                    'tesseract_version': str(pytesseract.get_tesseract_version()),
                    'total_words': len(text_parts),
                    'image_size_bytes': image_path.stat().st_size,
                    'image_path': str(image_path),
                    'psm_mode': '1'  # Page segmentation mode
                }
            }

        except FileNotFoundError:
            raise ValueError(f"Error: archivo de imagen no encontrado: {image_path}")
        except Image.UnidentifiedImageError:
            raise ValueError(f"Error: formato de imagen no soportado: {image_path}")
        except pytesseract.TesseractError as e:
            raise ValueError(f"Error de Tesseract OCR: {e}")
        except Exception as e:
            raise ValueError(f"Error extrayendo texto con Tesseract: {e}")

    def extract_text_simple(
        self,
        image_path: Path,
        language: str = "spa"
    ) -> str:
        """
        Extraer solo texto sin metadatos (más rápido)

        Args:
            image_path: Ruta al archivo de imagen
            language: Código de idioma de Tesseract

        Returns:
            Texto extraído como string

        Raises:
            ValueError: Si extracción falla
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=language, config='--psm 1')
            return text.strip()

        except Exception as e:
            raise ValueError(f"Error extrayendo texto simple con Tesseract: {e}")

    def get_available_languages(self) -> List[str]:
        """
        Obtener lista de idiomas disponibles en Tesseract

        Returns:
            Lista de códigos de idioma disponibles

        Raises:
            ValueError: Si no se puede obtener la lista de idiomas
        """
        try:
            langs = pytesseract.get_languages()
            return sorted(langs)

        except Exception as e:
            raise ValueError(f"Error obteniendo idiomas de Tesseract: {e}")
