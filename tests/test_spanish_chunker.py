"""
Tests para Spanish-Aware Chunking

Suite de tests para:
- SpanishTextUtils (stopwords, stemming, features)
- ChunkMetadata (serialización)
- SpanishChunker (chunking, ventanas, límites de oraciones)
"""

import pytest
from pathlib import Path
from datetime import datetime
from intelligence_capture.chunking import (
    SpanishChunker,
    SpanishTextUtils,
    ChunkMetadata
)
from intelligence_capture.models.document_payload import DocumentPayload


class TestSpanishTextUtils:
    """Tests para utilidades de texto español"""

    @pytest.fixture
    def text_utils(self):
        """Crear instancia de SpanishTextUtils"""
        return SpanishTextUtils()

    def test_remove_stopwords_spanish(self, text_utils):
        """Eliminar stopwords del español"""
        text = "el sistema de gestión no funciona bien"
        result = text_utils.remove_stopwords(text)

        # Verificar que stopwords fueron eliminadas
        assert "el" not in result
        assert "de" not in result
        assert "no" not in result

        # Verificar que palabras importantes permanecen
        assert "sistema" in result
        assert "gestión" in result
        assert "funciona" in result

    def test_stem_text_spanish(self, text_utils):
        """Stemming de palabras en español"""
        text = "trabajamos trabajando trabajador trabajo"
        stems = text_utils.stem_text(text)

        # Todas las variantes deberían tener el mismo stem
        unique_stems = set(stems)
        assert len(unique_stems) == 1  # Todas relacionadas con "trabaj"

    def test_extract_features_spanish(self, text_utils):
        """Extraer características de texto español"""
        text = "La reconciliación manual de facturas toma tres horas diarias"

        features = text_utils.extract_features(text)

        # Verificar estructura de features
        assert 'total_words' in features
        assert 'stopword_count' in features
        assert 'stopword_ratio' in features
        assert 'unique_stems' in features
        assert 'has_accents' in features
        assert 'avg_word_length' in features
        assert 'lexical_diversity' in features

        # Verificar valores
        assert features['total_words'] == 9
        assert features['has_accents'] is True  # "reconciliación" tiene acento
        assert 0.0 < features['stopword_ratio'] < 1.0

    def test_is_spanish_detection(self, text_utils):
        """Detectar si texto es español"""
        spanish_text = "La gestión de procesos es muy importante para la empresa"
        english_text = "The process management is very important for the company"

        assert text_utils.is_spanish(spanish_text) is True
        assert text_utils.is_spanish(english_text) is False

    def test_empty_text_features(self, text_utils):
        """Manejar texto vacío sin errores"""
        features = text_utils.extract_features("")

        assert features['total_words'] == 0
        assert features['stopword_ratio'] == 0.0
        assert features['unique_stems'] == 0


class TestChunkMetadata:
    """Tests para metadatos de chunks"""

    def test_metadata_creation(self):
        """Crear metadatos de chunk"""
        metadata = ChunkMetadata(
            document_id="test-doc-123",
            chunk_index=0,
            token_count=400,
            char_count=2500,
            span_offsets=(0, 2500),
            section_title="Introducción",
            page_number=1,
            spanish_features={'total_words': 350}
        )

        assert metadata.document_id == "test-doc-123"
        assert metadata.chunk_index == 0
        assert metadata.token_count == 400
        assert metadata.section_title == "Introducción"

    def test_metadata_serialization(self):
        """Serializar metadatos a diccionario"""
        metadata = ChunkMetadata(
            document_id="test-doc-123",
            chunk_index=0,
            token_count=400,
            char_count=2500,
            span_offsets=(0, 2500),
            contains_table=True,
            contains_list=False
        )

        data = metadata.to_dict()

        # Verificar estructura
        assert isinstance(data, dict)
        assert data['document_id'] == "test-doc-123"
        assert data['token_count'] == 400
        assert data['contains_table'] is True
        assert data['contains_list'] is False
        assert isinstance(data['span_offsets'], list)  # Convertido a lista

    def test_metadata_deserialization(self):
        """Crear metadatos desde diccionario"""
        data = {
            'document_id': 'test-doc-123',
            'chunk_index': 0,
            'token_count': 400,
            'char_count': 2500,
            'span_offsets': [0, 2500],  # Lista en JSON
            'section_title': None,
            'page_number': None,
            'heading_level': None,
            'spanish_features': {},
            'contains_table': False,
            'contains_list': False,
            'contains_code': False
        }

        metadata = ChunkMetadata.from_dict(data)

        assert metadata.document_id == "test-doc-123"
        assert metadata.token_count == 400
        assert isinstance(metadata.span_offsets, tuple)  # Convertido a tupla


class TestSpanishChunker:
    """Tests para chunker español"""

    @pytest.fixture
    def chunker(self):
        """Crear instancia de SpanishChunker"""
        try:
            return SpanishChunker()
        except ValueError as e:
            pytest.skip(f"spaCy modelo español no instalado: {e}")

    @pytest.fixture
    def sample_payload(self):
        """Crear payload de prueba con texto español"""
        # Texto largo suficiente para generar múltiples chunks
        content = """
        La reconciliación manual de facturas es un proceso crítico en el departamento de finanzas.
        Este proceso involucra múltiples pasos que toman aproximadamente tres horas diarias.

        El equipo de contabilidad debe revisar cada factura individualmente, comparándola con
        las órdenes de compra y los registros de recepción. Este trabajo manual es propenso a errores
        y causa retrasos significativos en el cierre mensual.

        Los principales problemas identificados incluyen:
        - Falta de integración entre sistemas
        - Procesos manuales repetitivos
        - Ausencia de validación automática
        - Dependencia de hojas de cálculo

        La automatización de este proceso podría reducir el tiempo de reconciliación en un 70%
        y mejorar significativamente la precisión de los datos financieros.
        """ * 10  # Repetir para generar suficiente contenido

        return DocumentPayload(
            document_id="test-doc-123",
            org_id="test_org",
            checksum="abc123",
            source_type="email",
            source_format="txt",
            mime_type="text/plain",
            original_path=Path("/tmp/test.txt"),
            content=content,
            language="es",
            page_count=1,
            sections=[
                {
                    "title": "Proceso de Reconciliación",
                    "content": content[:500],
                    "level": 2,
                    "page": 1
                }
            ]
        )

    def test_chunker_initialization(self, chunker):
        """Inicializar chunker correctamente"""
        assert chunker.min_tokens == 300
        assert chunker.max_tokens == 500
        assert chunker.overlap_tokens == 50
        assert chunker.target_tokens == 400

    def test_chunk_document_basic(self, chunker, sample_payload):
        """Dividir documento en chunks"""
        chunks = chunker.chunk_document(sample_payload)

        # Verificar que se generaron chunks
        assert len(chunks) > 0

        # Verificar estructura de chunks
        for chunk in chunks:
            assert 'content' in chunk
            assert 'metadata' in chunk
            assert isinstance(chunk['content'], str)
            assert isinstance(chunk['metadata'], dict)

    def test_chunk_size_constraints(self, chunker, sample_payload):
        """Verificar límites de tamaño de chunks"""
        chunks = chunker.chunk_document(sample_payload)

        for chunk in chunks:
            metadata = chunk['metadata']
            token_count = metadata['token_count']

            # Verificar que está en rango (excepto último chunk que puede ser menor)
            if metadata['chunk_index'] < len(chunks) - 1:
                assert chunker.min_tokens <= token_count <= chunker.max_tokens

    def test_chunk_overlap(self, chunker, sample_payload):
        """Verificar superposición entre chunks"""
        chunks = chunker.chunk_document(sample_payload)

        if len(chunks) > 1:
            # Verificar que hay contenido compartido entre chunks consecutivos
            for i in range(len(chunks) - 1):
                chunk1_content = chunks[i]['content']
                chunk2_content = chunks[i + 1]['content']

                # Los chunks deberían compartir algo de contenido
                # (superposición de 50 tokens)
                chunk1_words = chunk1_content.split()
                chunk2_words = chunk2_content.split()

                # Últimas palabras de chunk1 deberían aparecer en chunk2
                overlap_words = chunk1_words[-20:]  # Aproximadamente 20 palabras de overlap
                overlap_text = ' '.join(overlap_words)

                # Al menos algunas palabras del final de chunk1 deberían estar en chunk2
                shared_words = sum(1 for word in overlap_words if word in chunk2_words)
                assert shared_words > 0

    def test_chunk_metadata_content(self, chunker, sample_payload):
        """Verificar contenido de metadatos"""
        chunks = chunker.chunk_document(sample_payload)

        for i, chunk in enumerate(chunks):
            metadata = chunk['metadata']

            assert metadata['document_id'] == sample_payload.document_id
            assert metadata['chunk_index'] == i
            assert metadata['token_count'] > 0
            assert metadata['char_count'] > 0
            assert isinstance(metadata['span_offsets'], list)
            assert len(metadata['span_offsets']) == 2

            # Verificar características del español
            assert 'spanish_features' in metadata
            assert isinstance(metadata['spanish_features'], dict)

    def test_spanish_features_extraction(self, chunker, sample_payload):
        """Verificar extracción de características del español"""
        chunks = chunker.chunk_document(sample_payload)

        for chunk in chunks:
            spanish_features = chunk['metadata']['spanish_features']

            # Verificar que se extrajeron características
            assert 'total_words' in spanish_features
            assert 'stopword_ratio' in spanish_features
            assert 'has_accents' in spanish_features

            # Contenido en español debería tener acentos
            if spanish_features['total_words'] > 10:
                assert spanish_features['has_accents'] is True

    def test_detect_table(self, chunker):
        """Detectar tablas en texto"""
        # Texto con tabla Markdown
        table_text = """
        | Columna1 | Columna2 |
        |----------|----------|
        | Valor1   | Valor2   |
        """
        assert chunker._detect_table(table_text) is True

        # Texto sin tabla
        normal_text = "Este es un texto normal sin tablas"
        assert chunker._detect_table(normal_text) is False

    def test_detect_list(self, chunker):
        """Detectar listas en texto"""
        # Texto con lista
        list_text = """
        Los problemas incluyen:
        - Falta de integración
        - Procesos manuales
        - Ausencia de validación
        """
        assert chunker._detect_list(list_text) is True

        # Lista numerada
        numbered_list = """
        Pasos:
        1. Revisar factura
        2. Comparar con orden de compra
        3. Validar recepción
        """
        assert chunker._detect_list(numbered_list) is True

        # Texto sin lista
        normal_text = "Este es un texto normal sin listas"
        assert chunker._detect_list(normal_text) is False

    def test_detect_code(self, chunker):
        """Detectar código en texto"""
        # Texto con código
        code_text = """
        ```python
        def process_invoice():
            return True
        ```
        """
        assert chunker._detect_code(code_text) is True

        # Código indentado
        indented_code = """
        Función:
            function processInvoice() {
                return true;
            }
        """
        assert chunker._detect_code(indented_code) is True

        # Texto sin código
        normal_text = "Este es un texto normal sin código"
        assert chunker._detect_code(normal_text) is False

    def test_markdown_preservation(self, chunker):
        """Preservar estructura Markdown"""
        # Crear payload con Markdown
        markdown_content = """
## Introducción

Este es el contenido de la introducción con suficiente texto
para generar múltiples chunks y verificar la preservación de la
estructura Markdown.

## Procesos

Descripción de procesos con más contenido para generar chunks adicionales.
""" * 5

        payload = DocumentPayload(
            document_id="test-markdown",
            org_id="test_org",
            checksum="abc123",
            source_type="email",
            source_format="md",
            mime_type="text/markdown",
            original_path=Path("/tmp/test.md"),
            content=markdown_content,
            language="es",
            page_count=1
        )

        chunks = chunker.chunk_with_markdown_preservation(payload)

        # Verificar que los chunks preservan encabezados
        for chunk in chunks:
            if '##' in chunk['content']:
                # Verificar que el encabezado está al inicio
                assert chunk['content'].strip().startswith('##')

    def test_empty_content(self, chunker):
        """Manejar contenido vacío"""
        payload = DocumentPayload(
            document_id="empty-doc",
            org_id="test_org",
            checksum="abc123",
            source_type="email",
            source_format="txt",
            mime_type="text/plain",
            original_path=Path("/tmp/empty.txt"),
            content="",
            language="es",
            page_count=0
        )

        chunks = chunker.chunk_document(payload)

        # Debería manejar contenido vacío sin errores
        assert isinstance(chunks, list)

    def test_short_content(self, chunker):
        """Manejar contenido más corto que min_tokens"""
        short_content = "Este es un texto muy corto."

        payload = DocumentPayload(
            document_id="short-doc",
            org_id="test_org",
            checksum="abc123",
            source_type="email",
            source_format="txt",
            mime_type="text/plain",
            original_path=Path("/tmp/short.txt"),
            content=short_content,
            language="es",
            page_count=1
        )

        chunks = chunker.chunk_document(payload)

        # Debería generar al menos un chunk
        assert len(chunks) >= 1

        # El chunk debería contener todo el contenido
        assert chunks[0]['content'] == short_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
