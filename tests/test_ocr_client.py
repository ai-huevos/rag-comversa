"""
Unit tests for OCR client components
Tests Mistral Pixtral, Tesseract, and OCR Coordinator
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import json

from intelligence_capture.ocr.mistral_pixtral_client import MistralPixtralClient
from intelligence_capture.ocr.tesseract_fallback import TesseractFallback
from intelligence_capture.ocr.ocr_coordinator import OCRCoordinator


class TestMistralPixtralClient:
    """Test Mistral Pixtral OCR client"""

    def test_init_without_api_key(self):
        """Test initialization fails without API key"""
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(ValueError, match="MISTRAL_API_KEY no configurado"):
                MistralPixtralClient()

    def test_init_with_api_key(self):
        """Test successful initialization with API key"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()
            assert client.api_key == 'test-key'
            assert client.model == 'pixtral-12b-2409'

    @patch('requests.post')
    @patch('builtins.open', create=True)
    @patch('os.path.getsize')
    def test_extract_text_success(self, mock_getsize, mock_open, mock_post):
        """Test successful text extraction"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            # Setup mocks
            mock_getsize.return_value = 1024
            mock_open.return_value.__enter__.return_value.read.return_value = b'fake-image-data'

            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                'choices': [{
                    'message': {
                        'content': 'Texto extraído en español'
                    }
                }]
            }
            mock_post.return_value = mock_response

            # Execute
            client = MistralPixtralClient()
            result = client.extract_text(
                Path('/fake/path/image.jpg'),
                language='es',
                document_type='printed'
            )

            # Verify
            assert result['text'] == 'Texto extraído en español'
            assert result['ocr_engine'] == 'mistral_pixtral'
            assert result['language_detected'] == 'es'
            assert 0.0 <= result['confidence'] <= 1.0
            assert 'metadata' in result

    @patch('requests.post')
    def test_extract_text_api_error(self, mock_post):
        """Test API error handling"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            mock_response = Mock()
            mock_response.status_code = 500
            mock_response.json.return_value = {
                'error': {'message': 'Internal server error'}
            }
            mock_post.return_value = mock_response

            client = MistralPixtralClient()

            with patch('builtins.open', create=True):
                with patch('os.path.getsize', return_value=1024):
                    with pytest.raises(ValueError, match="Error de API Mistral"):
                        client.extract_text(Path('/fake/image.jpg'))

    def test_build_spanish_prompt_handwritten(self):
        """Test Spanish prompt generation for handwritten text"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()
            prompt = client._build_spanish_prompt('es', 'handwritten')

            assert 'escrita a mano' in prompt.lower()
            assert 'español' in prompt.lower()
            assert 'ilegible' in prompt.lower()

    def test_build_spanish_prompt_printed(self):
        """Test Spanish prompt generation for printed text"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()
            prompt = client._build_spanish_prompt('es', 'printed')

            assert 'impreso' in prompt.lower()
            assert 'español' in prompt.lower()

    def test_estimate_confidence_printed(self):
        """Test confidence estimation for printed text"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()

            # High confidence for clean printed text
            conf = client._estimate_confidence('printed', 'Texto limpio y completo')
            assert conf >= 0.90

    def test_estimate_confidence_handwritten(self):
        """Test confidence estimation for handwritten text"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()

            # Medium confidence for handwritten
            conf = client._estimate_confidence('handwritten', 'Texto manuscrito')
            assert 0.70 <= conf < 0.90

    def test_estimate_confidence_illegible(self):
        """Test confidence reduction for illegible text"""
        with patch.dict('os.environ', {'MISTRAL_API_KEY': 'test-key'}):
            client = MistralPixtralClient()

            # Low confidence for illegible markers
            conf = client._estimate_confidence('handwritten', 'Texto [ILEGIBLE] parcial')
            assert conf < 0.70


class TestTesseractFallback:
    """Test Tesseract OCR fallback"""

    @patch('pytesseract.get_tesseract_version')
    def test_init_tesseract_available(self, mock_version):
        """Test initialization when Tesseract is installed"""
        mock_version.return_value = '5.0.0'
        client = TesseractFallback()
        assert client is not None

    @patch('pytesseract.get_tesseract_version')
    def test_init_tesseract_not_installed(self, mock_version):
        """Test initialization fails when Tesseract not installed"""
        mock_version.side_effect = Exception("Tesseract not found")

        with pytest.raises(ValueError, match="Tesseract no está instalado"):
            TesseractFallback()

    @patch('pytesseract.image_to_data')
    @patch('PIL.Image.open')
    @patch('pytesseract.get_tesseract_version')
    def test_extract_text_success(self, mock_version, mock_image_open, mock_image_to_data):
        """Test successful text extraction with Tesseract"""
        mock_version.return_value = '5.0.0'

        # Mock Tesseract output
        mock_image_to_data.return_value = {
            'text': ['Texto', 'español', 'extraído'],
            'conf': [95, 90, 88],
            'left': [10, 50, 100],
            'top': [10, 10, 10],
            'width': [40, 50, 60],
            'height': [20, 20, 20]
        }

        # Mock image
        mock_image = Mock()
        mock_image_open.return_value = mock_image

        # Mock Path.stat()
        mock_path = Mock(spec=Path)
        mock_path.stat.return_value.st_size = 2048

        # Execute
        client = TesseractFallback()
        result = client.extract_text(mock_path, language='spa')

        # Verify
        assert result['text'] == 'Texto español extraído'
        assert result['ocr_engine'] == 'tesseract'
        assert result['language_detected'] == 'spa'
        assert 0.80 <= result['confidence'] <= 1.0
        assert len(result['bounding_boxes']) == 3

    @patch('pytesseract.image_to_string')
    @patch('PIL.Image.open')
    @patch('pytesseract.get_tesseract_version')
    def test_extract_text_simple(self, mock_version, mock_image_open, mock_image_to_string):
        """Test simple text extraction"""
        mock_version.return_value = '5.0.0'
        mock_image_to_string.return_value = '  Texto simple  \n'

        client = TesseractFallback()
        text = client.extract_text_simple(Path('/fake/image.jpg'))

        assert text == 'Texto simple'

    @patch('pytesseract.get_languages')
    @patch('pytesseract.get_tesseract_version')
    def test_get_available_languages(self, mock_version, mock_get_languages):
        """Test getting available languages"""
        mock_version.return_value = '5.0.0'
        mock_get_languages.return_value = ['eng', 'spa', 'fra']

        client = TesseractFallback()
        langs = client.get_available_languages()

        assert 'spa' in langs
        assert 'eng' in langs


class TestOCRCoordinator:
    """Test OCR Coordinator"""

    @patch('intelligence_capture.ocr.ocr_coordinator.TesseractFallback')
    @patch('intelligence_capture.ocr.ocr_coordinator.MistralPixtralClient')
    def test_init_with_mistral_and_tesseract(self, mock_mistral, mock_tesseract):
        """Test initialization with both OCR engines"""
        mock_conn = Mock()
        coordinator = OCRCoordinator(mock_conn)

        assert coordinator.mistral_client is not None
        assert coordinator.tesseract_fallback is not None
        assert coordinator.conn == mock_conn

    @patch('intelligence_capture.ocr.ocr_coordinator.TesseractFallback')
    @patch('intelligence_capture.ocr.ocr_coordinator.MistralPixtralClient')
    def test_init_mistral_unavailable(self, mock_mistral, mock_tesseract):
        """Test initialization when Mistral unavailable"""
        mock_mistral.side_effect = ValueError("No API key")

        mock_conn = Mock()
        coordinator = OCRCoordinator(mock_conn)

        assert coordinator.mistral_client is None
        assert coordinator.tesseract_fallback is not None

    @patch('intelligence_capture.ocr.ocr_coordinator.get_rate_limiter')
    @patch('intelligence_capture.ocr.ocr_coordinator.TesseractFallback')
    @patch('intelligence_capture.ocr.ocr_coordinator.MistralPixtralClient')
    def test_process_image_mistral_success(self, mock_mistral_cls, mock_tesseract_cls, mock_rate_limiter):
        """Test successful image processing with Mistral"""
        # Setup mocks
        mock_mistral = Mock()
        mock_mistral.extract_text.return_value = {
            'text': 'Texto extraído',
            'confidence': 0.95,
            'ocr_engine': 'mistral_pixtral',
            'language_detected': 'es',
            'bounding_boxes': [],
            'metadata': {}
        }
        mock_mistral_cls.return_value = mock_mistral

        mock_rate_limiter.return_value.wait_if_needed = Mock()

        mock_conn = Mock()
        coordinator = OCRCoordinator(mock_conn)

        # Execute
        result = coordinator.process_image(
            Path('/fake/image.jpg'),
            document_id='test-123',
            page_number=1,
            document_type='printed'
        )

        # Verify
        assert result['text'] == 'Texto extraído'
        assert result['confidence'] == 0.95
        assert coordinator.stats['mistral_success'] == 1
        assert coordinator.stats['tesseract_fallback'] == 0

    @patch('intelligence_capture.ocr.ocr_coordinator.get_rate_limiter')
    @patch('intelligence_capture.ocr.ocr_coordinator.TesseractFallback')
    @patch('intelligence_capture.ocr.ocr_coordinator.MistralPixtralClient')
    def test_process_image_fallback_to_tesseract(self, mock_mistral_cls, mock_tesseract_cls, mock_rate_limiter):
        """Test fallback to Tesseract when Mistral fails"""
        # Setup Mistral to fail
        mock_mistral = Mock()
        mock_mistral.extract_text.side_effect = Exception("API error")
        mock_mistral_cls.return_value = mock_mistral

        # Setup Tesseract to succeed
        mock_tesseract = Mock()
        mock_tesseract.extract_text.return_value = {
            'text': 'Texto Tesseract',
            'confidence': 0.85,
            'ocr_engine': 'tesseract',
            'language_detected': 'spa',
            'bounding_boxes': [],
            'metadata': {}
        }
        mock_tesseract_cls.return_value = mock_tesseract

        mock_rate_limiter.return_value.wait_if_needed = Mock()

        mock_conn = Mock()
        coordinator = OCRCoordinator(mock_conn)

        # Execute
        result = coordinator.process_image(
            Path('/fake/image.jpg'),
            document_id='test-123',
            page_number=1,
            document_type='general'
        )

        # Verify
        assert result['ocr_engine'] == 'tesseract'
        assert coordinator.stats['tesseract_fallback'] == 1

    @patch('intelligence_capture.ocr.ocr_coordinator.get_rate_limiter')
    @patch('intelligence_capture.ocr.ocr_coordinator.TesseractFallback')
    @patch('intelligence_capture.ocr.ocr_coordinator.MistralPixtralClient')
    def test_get_stats(self, mock_mistral_cls, mock_tesseract_cls, mock_rate_limiter):
        """Test statistics calculation"""
        mock_rate_limiter.return_value.wait_if_needed = Mock()

        mock_conn = Mock()
        coordinator = OCRCoordinator(mock_conn)

        coordinator.stats = {
            'total_processed': 10,
            'mistral_success': 7,
            'tesseract_fallback': 2,
            'review_queue_added': 3,
            'errors': 1
        }

        stats = coordinator.get_stats()

        assert stats['total_processed'] == 10
        assert stats['success_rate'] == 0.9  # (7 + 2) / 10
        assert stats['review_rate'] == 0.3  # 3 / 10


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
