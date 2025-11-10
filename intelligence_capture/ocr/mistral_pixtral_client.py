"""
Mistral Pixtral OCR client with Spanish support
Primary OCR engine for multi-format document processing
"""

import os
import requests
import base64
from typing import Dict, Any, List
from pathlib import Path


class MistralPixtralClient:
    """Mistral Pixtral OCR client with Spanish support"""

    def __init__(self):
        """
        Initialize Mistral Pixtral client

        Raises:
            ValueError: Si MISTRAL_API_KEY no está configurado en environment
        """
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY no configurado en environment")

        self.api_base = "https://api.mistral.ai/v1"
        self.model = "pixtral-12b-2409"
        self.min_confidence_handwriting = 0.70
        self.min_confidence_printed = 0.90

    def extract_text(
        self,
        image_path: Path,
        language: str = "es",
        document_type: str = "general"
    ) -> Dict[str, Any]:
        """
        Extraer texto de imagen usando Mistral Pixtral

        Args:
            image_path: Ruta al archivo de imagen
            language: Código de idioma (default: "es" para español)
            document_type: Tipo de documento ("printed", "handwritten", "general")

        Returns:
            Dict con:
            - text: Texto extraído
            - confidence: Puntuación de confianza general
            - bounding_boxes: Lista de {text, bbox: [x, y, w, h], confidence}
            - language_detected: Idioma detectado
            - ocr_engine: "mistral_pixtral"
            - metadata: Metadatos adicionales de OCR

        Raises:
            ValueError: Si la llamada de API falla con mensaje de error en español
        """
        try:
            # Codificar imagen a base64
            with open(image_path, 'rb', encoding=None) as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')

            # Preparar solicitud con prompt en español
            prompt_text = self._build_spanish_prompt(language, document_type)

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.0  # Determinístico para OCR
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # Llamar API
            response = requests.post(
                f"{self.api_base}/chat/completions",
                json=payload,
                headers=headers,
                timeout=30
            )

            if response.status_code != 200:
                error_detail = response.json().get('error', {}).get('message', 'Error desconocido')
                raise ValueError(
                    f"Error de API Mistral (código {response.status_code}): {error_detail}"
                )

            result = response.json()

            # Parsear respuesta
            extracted_text = result['choices'][0]['message']['content']

            # Calcular confianza promedio
            # Nota: Pixtral no retorna confianza directa, estimamos basado en tipo de documento
            confidence = self._estimate_confidence(document_type, extracted_text)

            return {
                'text': extracted_text,
                'confidence': confidence,
                'bounding_boxes': [],  # Requeriría respuesta estructurada de Pixtral
                'language_detected': language,
                'ocr_engine': 'mistral_pixtral',
                'metadata': {
                    'model': self.model,
                    'document_type': document_type,
                    'image_size_bytes': os.path.getsize(image_path),
                    'image_path': str(image_path)
                }
            }

        except FileNotFoundError:
            raise ValueError(f"Error: archivo de imagen no encontrado: {image_path}")
        except requests.exceptions.Timeout:
            raise ValueError("Error: tiempo de espera agotado en llamada de API Mistral (30s)")
        except requests.exceptions.RequestException as e:
            raise ValueError(f"Error de conexión a API Mistral: {e}")
        except Exception as e:
            raise ValueError(f"Error extrayendo texto de imagen: {e}")

    def _build_spanish_prompt(self, language: str, document_type: str) -> str:
        """
        Construir prompt en español para extracción de OCR

        Args:
            language: Código de idioma
            document_type: Tipo de documento

        Returns:
            Texto de prompt en español
        """
        if document_type == "handwritten":
            return (
                "Extrae TODO el texto de esta imagen escrita a mano. "
                "Idioma: español. "
                "Proporciona el texto completo, preservando saltos de línea y estructura. "
                "Si hay texto ilegible, indica [ILEGIBLE]."
            )
        elif document_type == "printed":
            return (
                "Extrae TODO el texto de este documento impreso. "
                "Idioma: español. "
                "Preserva la estructura exacta del documento, incluyendo párrafos, "
                "listas y formato. Mantén los números, fechas y nombres exactos."
            )
        else:  # general
            return (
                "Extrae TODO el texto de esta imagen. "
                "Idioma: español. "
                "El documento puede contener texto impreso, escrito a mano o ambos. "
                "Preserva la estructura y formato original. "
                "Indica [IMPRESO] o [MANUSCRITO] al inicio de cada sección si hay mezcla."
            )

    def _estimate_confidence(self, document_type: str, extracted_text: str) -> float:
        """
        Estimar confianza basada en tipo de documento y texto extraído

        Args:
            document_type: Tipo de documento
            extracted_text: Texto extraído

        Returns:
            Puntuación de confianza (0.0 - 1.0)
        """
        # Heurística básica: documento impreso = alta confianza, manuscrito = media
        base_confidence = 0.95 if document_type == "printed" else 0.75

        # Reducir confianza si hay marcadores de texto ilegible
        if "[ILEGIBLE]" in extracted_text:
            base_confidence *= 0.6

        # Reducir confianza si texto muy corto (posible falla)
        if len(extracted_text.strip()) < 20:
            base_confidence *= 0.7

        return min(base_confidence, 1.0)
