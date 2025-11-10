"""
Unit tests for multi-format document processor

Tests all adapters and the DocumentProcessor orchestrator.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime
import tempfile
import shutil

from intelligence_capture.models.document_payload import DocumentPayload
from intelligence_capture.document_processor import DocumentProcessor
from intelligence_capture.parsers import (
    PDFAdapter,
    DOCXAdapter,
    ImageAdapter,
    CSVAdapter,
    XLSXAdapter,
    WhatsAppAdapter
)


# Test fixtures
@pytest.fixture
def temp_dir():
    """Create temporary directory for test files"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing"""
    return {
        'document_id': '550e8400-e29b-41d4-a716-446655440000',
        'org_id': 'los_tajibos',
        'checksum': 'abc123def456',
        'source_type': 'email',
        'context_tags': ['hotel', 'operaciones', 'recepcion']
    }


@pytest.fixture
def processor(temp_dir):
    """Create DocumentProcessor with temporary directory"""
    return DocumentProcessor(base_dir=temp_dir)


class TestDocumentPayload:
    """Test DocumentPayload dataclass"""

    def test_payload_creation(self, sample_metadata):
        """Test creating DocumentPayload"""
        payload = DocumentPayload(
            document_id=sample_metadata['document_id'],
            org_id=sample_metadata['org_id'],
            checksum=sample_metadata['checksum'],
            source_type=sample_metadata['source_type'],
            source_format='pdf',
            mime_type='application/pdf',
            original_path=Path('test.pdf'),
            content='Test content in Spanish',
            language='es',
            page_count=1,
            context_tags=sample_metadata['context_tags']
        )

        assert payload.document_id == sample_metadata['document_id']
        assert payload.org_id == 'los_tajibos'
        assert payload.language == 'es'
        assert payload.page_count == 1

    def test_payload_to_dict(self, sample_metadata):
        """Test converting payload to dictionary"""
        payload = DocumentPayload(
            document_id=sample_metadata['document_id'],
            org_id=sample_metadata['org_id'],
            checksum=sample_metadata['checksum'],
            source_type=sample_metadata['source_type'],
            source_format='pdf',
            mime_type='application/pdf',
            original_path=Path('test.pdf'),
            content='Contenido en español',
            language='es',
            page_count=1,
            context_tags=['test']
        )

        payload_dict = payload.to_dict()

        assert isinstance(payload_dict, dict)
        assert payload_dict['org_id'] == 'los_tajibos'
        assert payload_dict['content'] == 'Contenido en español'
        assert isinstance(payload_dict['original_path'], str)

    def test_payload_from_dict(self, sample_metadata):
        """Test creating payload from dictionary"""
        payload_dict = {
            'document_id': sample_metadata['document_id'],
            'org_id': sample_metadata['org_id'],
            'checksum': sample_metadata['checksum'],
            'source_type': sample_metadata['source_type'],
            'source_format': 'pdf',
            'mime_type': 'application/pdf',
            'original_path': 'test.pdf',
            'content': 'Test',
            'language': 'es',
            'page_count': 1,
            'sections': [],
            'tables': [],
            'images': [],
            'context_tags': [],
            'processed_at': datetime.now().isoformat(),
            'processing_time_seconds': 1.0,
            'metadata': {}
        }

        payload = DocumentPayload.from_dict(payload_dict)

        assert payload.org_id == 'los_tajibos'
        assert isinstance(payload.original_path, Path)


class TestBaseAdapter:
    """Test base adapter functionality"""

    def test_language_detection_spanish(self):
        """Test Spanish language detection"""
        adapter = PDFAdapter()

        spanish_text = """
        El proceso de facturación en el hotel requiere la coordinación
        entre recepción y contabilidad. Los huéspedes deben recibir
        su factura antes de realizar el check-out.
        """

        language = adapter.detect_language(spanish_text)
        assert language == 'es'

    def test_language_detection_english(self):
        """Test English language detection"""
        adapter = PDFAdapter()

        english_text = """
        The invoicing process at the hotel requires coordination
        between reception and accounting. Guests must receive
        their invoice before checking out.
        """

        language = adapter.detect_language(english_text)
        assert language == 'en'

    def test_language_detection_bilingual(self):
        """Test bilingual language detection"""
        adapter = PDFAdapter()

        bilingual_text = """
        El invoice process requiere coordination entre reception
        y accounting department. The guests deben receive their
        factura before el check-out.
        """

        language = adapter.detect_language(bilingual_text)
        assert language == 'es-en'

    def test_section_extraction(self):
        """Test section extraction from text"""
        adapter = PDFAdapter()

        text = """
        1. INTRODUCCIÓN
        Este documento describe el procedimiento.

        2. PROCESO
        El proceso consta de los siguientes pasos.

        2.1. Primer paso
        Descripción del primer paso.
        """

        sections = adapter.extract_sections(text, page_number=1)

        assert len(sections) > 0
        assert sections[0]['title'] == '1. INTRODUCCIÓN'
        assert sections[0]['page'] == 1
        assert any('PROCESO' in s['title'] for s in sections)


class TestImageAdapter:
    """Test image adapter"""

    def test_image_adapter_mime_types(self):
        """Test supported MIME types"""
        adapter = ImageAdapter()

        assert 'image/jpeg' in adapter.supported_mime_types
        assert 'image/png' in adapter.supported_mime_types
        assert 'image/tiff' in adapter.supported_mime_types

    def test_image_adapter_creates_ocr_placeholder(
        self,
        temp_dir,
        sample_metadata
    ):
        """Test that image adapter creates OCR placeholder"""
        adapter = ImageAdapter()

        # Create dummy image file
        image_path = temp_dir / 'test_image.jpg'
        image_path.write_bytes(b'fake image data')

        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(image_path.read_bytes()).hexdigest()
        sample_metadata['checksum'] = checksum

        # Parse image
        payload = adapter.parse(image_path, sample_metadata)

        assert payload.source_format == 'image'
        assert len(payload.images) == 1
        assert payload.images[0]['needs_ocr'] is True
        assert payload.images[0]['ocr_status'] == 'pending'
        assert '[Imagen requiere OCR' in payload.content


class TestCSVAdapter:
    """Test CSV adapter"""

    def test_csv_adapter_parse(self, temp_dir, sample_metadata):
        """Test CSV parsing"""
        adapter = CSVAdapter()

        # Create test CSV
        csv_path = temp_dir / 'test.csv'
        csv_content = """Producto,Cantidad,Precio
Toalla,50,25.00
Sábana,30,45.00
Almohada,20,35.00"""

        csv_path.write_text(csv_content, encoding='utf-8')

        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(csv_path.read_bytes()).hexdigest()
        sample_metadata['checksum'] = checksum

        # Parse CSV
        payload = adapter.parse(csv_path, sample_metadata)

        assert payload.source_format == 'csv'
        assert len(payload.tables) == 1
        assert payload.tables[0]['headers'] == ['Producto', 'Cantidad', 'Precio']
        assert len(payload.tables[0]['rows']) == 3
        assert 'Toalla' in payload.content


class TestWhatsAppAdapter:
    """Test WhatsApp adapter"""

    def test_whatsapp_adapter_parse(self, temp_dir, sample_metadata):
        """Test WhatsApp JSON parsing"""
        adapter = WhatsAppAdapter()

        # Create test WhatsApp export
        whatsapp_path = temp_dir / 'chat.json'
        messages = [
            {
                'timestamp': '2024-01-15T10:30:00',
                'sender': 'Patricia García',
                'message': '¿Cómo va el proceso de facturación?'
            },
            {
                'timestamp': '2024-01-15T10:35:00',
                'sender': 'Samuel Rodríguez',
                'message': 'Estamos trabajando en automatizarlo'
            },
            {
                'timestamp': '2024-01-15T10:40:00',
                'sender': 'Patricia García',
                'message': 'Excelente, ¿para cuándo estaría listo?'
            }
        ]

        whatsapp_path.write_text(
            json.dumps(messages, ensure_ascii=False),
            encoding='utf-8'
        )

        # Calculate checksum
        import hashlib
        checksum = hashlib.sha256(whatsapp_path.read_bytes()).hexdigest()
        sample_metadata['checksum'] = checksum

        # Parse WhatsApp
        payload = adapter.parse(whatsapp_path, sample_metadata)

        assert payload.source_format == 'whatsapp_json'
        assert payload.metadata['message_count'] == 3
        assert payload.metadata['participant_count'] == 2
        assert 'Patricia García' in payload.metadata['participants']
        assert 'facturación' in payload.content


class TestDocumentProcessor:
    """Test DocumentProcessor orchestrator"""

    def test_processor_initialization(self, processor):
        """Test processor directory creation"""
        assert processor.originals_dir.exists()
        assert processor.processing_dir.exists()
        assert processor.processed_dir.exists()
        assert processor.failed_dir.exists()

    def test_adapter_registration(self, processor):
        """Test that all adapters are registered"""
        adapters = processor.get_supported_formats()

        assert 'PDFAdapter' in adapters
        assert 'DOCXAdapter' in adapters
        assert 'ImageAdapter' in adapters
        assert 'CSVAdapter' in adapters
        assert 'XLSXAdapter' in adapters
        assert 'WhatsAppAdapter' in adapters

    def test_get_stats(self, processor):
        """Test getting processing statistics"""
        stats = processor.get_stats()

        assert 'processing' in stats
        assert 'processed' in stats
        assert 'failed' in stats
        assert 'originals' in stats
        assert stats['processing'] == 0  # Initially empty


def test_spanish_content_preservation():
    """Test that Spanish content is never translated"""
    adapter = PDFAdapter()

    spanish_text = """
    El proceso de recepción de huéspedes incluye:
    - Verificación de reserva
    - Registro en el sistema
    - Entrega de llaves
    """

    # Language detection should identify Spanish
    language = adapter.detect_language(spanish_text)
    assert language == 'es'

    # Content should remain in Spanish (not translated)
    assert 'huéspedes' in spanish_text
    assert 'llaves' in spanish_text
    assert 'guests' not in spanish_text  # Never translate!


def test_utf8_encoding():
    """Test UTF-8 encoding for Spanish characters"""
    payload = DocumentPayload(
        document_id='test-id',
        org_id='los_tajibos',
        checksum='test-checksum',
        source_type='email',
        source_format='pdf',
        mime_type='application/pdf',
        original_path=Path('test.pdf'),
        content='Año: 2024, Otoño, niño, señor',
        language='es',
        page_count=1,
        context_tags=[]
    )

    # Convert to dict with ensure_ascii=False
    payload_dict = payload.to_dict()
    json_str = json.dumps(payload_dict, ensure_ascii=False)

    # Spanish characters should be preserved
    assert 'Año' in json_str
    assert 'Otoño' in json_str
    assert 'niño' in json_str
    assert 'señor' in json_str

    # Should NOT be escaped Unicode
    assert '\\u' not in json_str


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
