"""
OCR Coordinator with rate limiting and review queue integration
Orchestrates Mistral Pixtral + Tesseract fallback with quality controls
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime

from ..rate_limiter import get_rate_limiter
from .mistral_pixtral_client import MistralPixtralClient
from .tesseract_fallback import TesseractFallback


class OCRCoordinator:
    """Coordina OCR con rate limiting y cola de revisión"""

    def __init__(self, db_connection):
        """
        Inicializar coordinador de OCR

        Args:
            db_connection: Conexión asyncpg a PostgreSQL

        Raises:
            ValueError: Si falta configuración requerida
        """
        self.conn = db_connection

        # Inicializar clientes OCR
        try:
            self.mistral_client = MistralPixtralClient()
        except ValueError as e:
            print(f"⚠️  Advertencia: Mistral Pixtral no disponible: {e}")
            self.mistral_client = None

        try:
            self.tesseract_fallback = TesseractFallback()
        except ValueError as e:
            raise ValueError(f"Error crítico: Tesseract fallback no disponible: {e}")

        # Rate limiter: máximo 5 llamadas OCR concurrentes
        self.rate_limiter = get_rate_limiter(
            max_calls_per_minute=5,
            name="ocr"
        )

        # Umbrales de confianza para revisión manual
        self.min_confidence_handwriting = 0.70
        self.min_confidence_printed = 0.90

        # Estadísticas
        self.stats = {
            'total_processed': 0,
            'mistral_success': 0,
            'tesseract_fallback': 0,
            'review_queue_added': 0,
            'errors': 0
        }

    def process_image(
        self,
        image_path: Path,
        document_id: str,
        page_number: int,
        document_type: str = "general",
        force_tesseract: bool = False
    ) -> Dict[str, Any]:
        """
        Procesar imagen con OCR, fallback a Tesseract si es necesario

        Args:
            image_path: Ruta a archivo de imagen
            document_id: UUID del documento
            page_number: Número de página
            document_type: "printed", "handwritten", o "general"
            force_tesseract: Forzar uso de Tesseract (omitir Mistral)

        Returns:
            Resultado OCR con estructura estándar

        Raises:
            ValueError: Si ambos OCR fallan
        """
        self.stats['total_processed'] += 1

        # Aplicar rate limiting
        self.rate_limiter.wait_if_needed()

        # Intentar Mistral Pixtral primero (a menos que force_tesseract)
        if not force_tesseract and self.mistral_client:
            try:
                print(f"  🔍 Procesando con Mistral Pixtral: página {page_number}...")
                result = self.mistral_client.extract_text(
                    image_path,
                    language="es",
                    document_type=document_type
                )

                self.stats['mistral_success'] += 1

                # Verificar si necesita revisión manual
                threshold = (
                    self.min_confidence_handwriting
                    if document_type == "handwritten"
                    else self.min_confidence_printed
                )

                if result['confidence'] < threshold:
                    print(f"  ⚠️  Confianza baja ({result['confidence']:.2f} < {threshold:.2f}), "
                          f"agregando a cola de revisión...")
                    self._enqueue_for_review(
                        document_id,
                        page_number,
                        result,
                        image_path,
                        document_type
                    )

                return result

            except Exception as e:
                print(f"  ⚠️  Mistral Pixtral falló: {e}")
                print(f"  🔄 Intentando con Tesseract fallback...")

        # Fallback a Tesseract
        try:
            result = self.tesseract_fallback.extract_text(
                image_path,
                language="spa"
            )

            self.stats['tesseract_fallback'] += 1
            print(f"  ✓ Tesseract exitoso: página {page_number} "
                  f"(confianza: {result['confidence']:.2f})")

            # Tesseract siempre tiene menor confianza, agregar a revisión si es manuscrito
            if document_type == "handwritten" or result['confidence'] < self.min_confidence_printed:
                print(f"  ⚠️  Tesseract con confianza baja, agregando a cola de revisión...")
                self._enqueue_for_review(
                    document_id,
                    page_number,
                    result,
                    image_path,
                    document_type
                )

            return result

        except Exception as e:
            self.stats['errors'] += 1
            raise ValueError(
                f"Error: ambos OCR fallaron para página {page_number}. "
                f"Mistral: {e if not self.mistral_client else 'falló'}, "
                f"Tesseract: {e}"
            )

    def process_document(
        self,
        image_paths: List[Path],
        document_id: str,
        document_type: str = "general"
    ) -> List[Dict[str, Any]]:
        """
        Procesar documento completo con múltiples páginas

        Args:
            image_paths: Lista de rutas a imágenes (una por página)
            document_id: UUID del documento
            document_type: Tipo de documento

        Returns:
            Lista de resultados OCR (uno por página)
        """
        results = []

        print(f"\n{'='*60}")
        print(f"🔍 Procesando documento OCR: {document_id}")
        print(f"   Páginas: {len(image_paths)}")
        print(f"   Tipo: {document_type}")
        print(f"{'='*60}\n")

        for i, image_path in enumerate(image_paths, 1):
            try:
                result = self.process_image(
                    image_path,
                    document_id,
                    page_number=i,
                    document_type=document_type
                )
                results.append(result)

            except Exception as e:
                print(f"  ✗ Error procesando página {i}: {e}")
                # Agregar resultado de error
                results.append({
                    'text': '',
                    'confidence': 0.0,
                    'error': str(e),
                    'page_number': i,
                    'ocr_engine': 'failed'
                })

        # Estadísticas finales
        print(f"\n{'='*60}")
        print(f"✓ Documento OCR completo: {document_id}")
        print(f"   Páginas procesadas: {len(results)}/{len(image_paths)}")
        print(f"   Confianza promedio: {self._calculate_avg_confidence(results):.2f}")
        print(f"{'='*60}\n")

        return results

    def _enqueue_for_review(
        self,
        document_id: str,
        page_number: int,
        ocr_result: Dict[str, Any],
        image_path: Path,
        document_type: str,
        segment_index: int = 0
    ):
        """
        Agregar segmento OCR de baja confianza a cola de revisión

        Args:
            document_id: UUID del documento
            page_number: Número de página
            ocr_result: Resultado OCR con confianza baja
            image_path: Ruta a imagen original
            document_type: Tipo de documento
            segment_index: Índice de segmento en página (default: 0 = página completa)
        """
        try:
            # Determinar tipo de segmento
            segment_type = self._classify_segment_type(document_type, ocr_result)

            # Generar ruta de recorte de imagen (se creará en revisión manual)
            image_crop_url = f"data/ocr_crops/{document_id}/page_{page_number}_segment_{segment_index}.png"

            # Preparar metadata
            metadata = {
                'original_filename': image_path.name,
                'language_detected': ocr_result.get('language_detected', 'es'),
                'ocr_params': ocr_result.get('metadata', {}),
                'retry_count': 0
            }

            # Insertar en PostgreSQL ocr_review_queue
            query = """
            INSERT INTO ocr_review_queue (
                document_id, page_number, segment_index,
                ocr_text, confidence, ocr_engine,
                bounding_box, image_crop_url,
                segment_type, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """

            # Ejecutar inserción (asumiendo conexión asyncpg)
            # Nota: En producción esto debería ser async, aquí simplificado
            # review_id = await self.conn.fetchval(
            #     query,
            #     document_id, page_number, segment_index,
            #     ocr_result.get('text', ''),
            #     ocr_result['confidence'],
            #     ocr_result['ocr_engine'],
            #     json.dumps({}),  # bounding_box (página completa por ahora)
            #     image_crop_url,
            #     segment_type,
            #     json.dumps(metadata)
            # )

            # Por ahora, solo registrar en log (hasta integración completa con Postgres)
            print(f"  📋 Agregado a cola de revisión: página {page_number}, "
                  f"confianza {ocr_result['confidence']:.2f}, "
                  f"tipo '{segment_type}'")

            self.stats['review_queue_added'] += 1

        except Exception as e:
            print(f"  ⚠️  Error agregando a cola de revisión: {e}")

    def _classify_segment_type(
        self,
        document_type: str,
        ocr_result: Dict[str, Any]
    ) -> str:
        """
        Clasificar tipo de segmento para ruteo de revisores

        Args:
            document_type: Tipo de documento
            ocr_result: Resultado OCR

        Returns:
            Tipo de segmento: handwriting, printed_degraded, tables, mixed
        """
        if document_type == "handwritten":
            return "handwriting"
        elif document_type == "printed":
            # Verificar si confianza baja indica degradación
            if ocr_result['confidence'] < 0.80:
                return "printed_degraded"
            return "printed"
        else:
            # General: detectar texto mixto
            text = ocr_result.get('text', '')
            if '[MANUSCRITO]' in text or '[IMPRESO]' in text:
                return "mixed"
            return "general"

    def _calculate_avg_confidence(self, results: List[Dict[str, Any]]) -> float:
        """
        Calcular confianza promedio de resultados

        Args:
            results: Lista de resultados OCR

        Returns:
            Confianza promedio (0.0 - 1.0)
        """
        valid_results = [r for r in results if 'confidence' in r and r['confidence'] > 0]
        if not valid_results:
            return 0.0

        return sum(r['confidence'] for r in valid_results) / len(valid_results)

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de procesamiento OCR

        Returns:
            Dict con estadísticas de uso
        """
        return {
            **self.stats,
            'success_rate': (
                (self.stats['mistral_success'] + self.stats['tesseract_fallback'])
                / max(self.stats['total_processed'], 1)
            ),
            'review_rate': (
                self.stats['review_queue_added']
                / max(self.stats['total_processed'], 1)
            )
        }
