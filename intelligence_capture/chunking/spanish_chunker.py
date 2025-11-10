"""
Chunker consciente del español con ventanas deslizantes

Implementa chunking optimizado para español:
- Tokenización con spaCy (es_core_news_md)
- Ventanas de 300-500 tokens con 50 tokens de superposición
- Preservación de estructura Markdown
- Ajuste a límites de oraciones
- Extracción de metadatos de chunks
"""

import re
from typing import List, Dict, Any, Optional
from intelligence_capture.models.document_payload import DocumentPayload
from .chunk_metadata import ChunkMetadata
from .spanish_text_utils import SpanishTextUtils


class SpanishChunker:
    """
    Chunker consciente del español con ventanas deslizantes

    Características:
    - Tokenización con spaCy para español
    - Ventanas de 300-500 tokens con 50 tokens de superposición
    - Ajuste a límites de oraciones
    - Preservación de estructura Markdown
    - Detección de tablas y listas
    - Extracción de características del español

    Attributes:
        nlp: Modelo spaCy español (es_core_news_md)
        text_utils: Utilidades de texto español
        min_tokens: Mínimo de tokens por chunk (300)
        max_tokens: Máximo de tokens por chunk (500)
        overlap_tokens: Tokens de superposición entre chunks (50)
        target_tokens: Objetivo de tokens por chunk (400)
    """

    def __init__(self):
        """
        Inicializar chunker con modelo spaCy español

        Raises:
            ValueError: Si modelo spaCy español no está instalado
        """
        # Intentar cargar modelo spaCy español
        try:
            import spacy
            self.nlp = spacy.load("es_core_news_md")
        except OSError:
            raise ValueError(
                "Modelo spaCy español no encontrado. "
                "Instalar con: python -m spacy download es_core_news_md"
            )

        self.text_utils = SpanishTextUtils()

        # Parámetros de chunking (de requisitos R3.1-R3.7)
        self.min_tokens = 300
        self.max_tokens = 500
        self.overlap_tokens = 50
        self.target_tokens = 400  # Punto medio del rango

    def chunk_document(
        self,
        payload: DocumentPayload
    ) -> List[Dict[str, Any]]:
        """
        Dividir documento en chunks de 300-500 tokens con superposición

        Algoritmo:
        1. Tokenizar con spaCy
        2. Crear ventanas deslizantes de target_tokens
        3. Ajustar a límites de oraciones
        4. Extraer metadatos (sección, página, características español)
        5. Aplicar superposición de overlap_tokens

        Args:
            payload: DocumentPayload con contenido a dividir

        Returns:
            Lista de diccionarios de chunks, cada uno con:
            - content: Texto del chunk (español)
            - metadata: ChunkMetadata con información de posición y características

        Example:
            >>> chunker = SpanishChunker()
            >>> payload = DocumentPayload(content="Texto largo...", ...)
            >>> chunks = chunker.chunk_document(payload)
            >>> print(f"Generados {len(chunks)} chunks")
            >>> print(chunks[0]['metadata']['token_count'])
        """
        # Procesar contenido con spaCy
        doc = self.nlp(payload.content)

        chunks = []
        chunk_index = 0

        # Convertir a lista de tokens para indexación
        tokens = [token for token in doc]
        total_tokens = len(tokens)

        # Ventana deslizante con superposición
        start_idx = 0
        while start_idx < total_tokens:
            # Calcular límites del chunk
            end_idx = min(start_idx + self.target_tokens, total_tokens)

            # Ajustar a límite de oración si no es el último chunk
            if end_idx < total_tokens:
                end_idx = self._adjust_to_sentence_boundary(tokens, start_idx, end_idx)

            # Validar que no sea chunk vacío
            if end_idx <= start_idx:
                break

            # Extraer chunk
            chunk_tokens = tokens[start_idx:end_idx]
            chunk_text = ' '.join([t.text for t in chunk_tokens])

            # Encontrar información de sección
            section_info = self._find_section(payload.sections, chunk_tokens[0].idx)

            # Extraer características del español
            spanish_features = self.text_utils.extract_features(chunk_text)

            # Construir metadatos
            metadata = ChunkMetadata(
                document_id=payload.document_id,
                chunk_index=chunk_index,
                token_count=len(chunk_tokens),
                char_count=len(chunk_text),
                span_offsets=(
                    chunk_tokens[0].idx,
                    chunk_tokens[-1].idx + len(chunk_tokens[-1].text)
                ),
                section_title=section_info.get('title'),
                page_number=section_info.get('page'),
                heading_level=section_info.get('level'),
                spanish_features=spanish_features,
                contains_table=self._detect_table(chunk_text),
                contains_list=self._detect_list(chunk_text),
                contains_code=self._detect_code(chunk_text)
            )

            # Agregar chunk
            chunks.append({
                'content': chunk_text,
                'metadata': metadata.to_dict()
            })

            chunk_index += 1

            # Mover ventana con superposición
            start_idx = end_idx - self.overlap_tokens

            # Evitar bucles infinitos si la superposición es mayor que el avance
            if start_idx <= tokens[chunk_index - 1].i if chunk_index > 0 else 0:
                start_idx = end_idx

        return chunks

    def _adjust_to_sentence_boundary(
        self,
        tokens: List,
        start_idx: int,
        end_idx: int
    ) -> int:
        """
        Ajustar límite de chunk al final de oración más cercano

        Busca hacia atrás hasta 50 tokens para encontrar final de oración

        Args:
            tokens: Lista de tokens spaCy
            start_idx: Índice de inicio del chunk
            end_idx: Índice de fin propuesto

        Returns:
            Índice ajustado al final de oración
        """
        # Buscar final de oración en últimos 50 tokens
        search_start = max(start_idx, end_idx - 50)

        for i in range(end_idx - 1, search_start, -1):
            if tokens[i].is_sent_end:
                return i + 1

        # Si no se encuentra, retornar índice original
        return end_idx

    def _find_section(
        self,
        sections: List[Dict[str, Any]],
        char_offset: int
    ) -> Dict[str, Any]:
        """
        Encontrar información de sección para posición de carácter

        Args:
            sections: Lista de secciones del documento
            char_offset: Posición de carácter en documento

        Returns:
            Diccionario con información de sección (title, page, level)
        """
        # Implementación simple: retornar primera sección si existe
        # En producción, esto debería mapear offsets a secciones
        if sections:
            # TODO: Implementar búsqueda binaria por char_offset
            return sections[0]

        return {}

    def _detect_table(self, text: str) -> bool:
        """
        Detectar si chunk contiene datos tabulares

        Heurísticas:
        - Presencia de caracteres pipe (|) para tablas Markdown
        - Múltiples tabs consecutivos
        - Patrones de encabezados tabulares

        Args:
            text: Texto del chunk

        Returns:
            True si detecta contenido tabular
        """
        # Detectar tablas Markdown
        if '|' in text and '-|-' in text:
            return True

        # Detectar múltiples tabs (datos tabulares)
        if text.count('\t') > 3:
            return True

        # Detectar patrones de tabla CSV/TSV
        lines = text.split('\n')
        if len(lines) > 2:
            # Contar delimitadores consistentes
            first_line_tabs = lines[0].count('\t')
            first_line_commas = lines[0].count(',')

            if first_line_tabs > 2 or first_line_commas > 2:
                # Verificar consistencia en próximas líneas
                consistent = sum(
                    1 for line in lines[1:3]
                    if line.count('\t') == first_line_tabs or
                    line.count(',') == first_line_commas
                )
                if consistent >= 2:
                    return True

        return False

    def _detect_list(self, text: str) -> bool:
        """
        Detectar si chunk contiene listas

        Heurísticas:
        - Viñetas (•, ·, -, *)
        - Listas numeradas (1., 2., a), b))
        - Múltiples líneas con mismo marcador

        Args:
            text: Texto del chunk

        Returns:
            True si detecta listas
        """
        # Marcadores de lista
        list_markers = ['•', '·', '-', '*', '○', '◦', '▪', '▫']

        lines = text.split('\n')

        # Contar líneas con marcadores
        list_lines = sum(
            1 for line in lines
            if any(line.strip().startswith(marker) for marker in list_markers)
        )

        # Detectar listas numeradas
        numbered_lines = sum(
            1 for line in lines
            if re.match(r'^\s*\d+[\.)]\s+', line) or
            re.match(r'^\s*[a-z][\.)]\s+', line)
        )

        # Considerar lista si hay 3+ líneas con marcadores
        return list_lines >= 3 or numbered_lines >= 3

    def _detect_code(self, text: str) -> bool:
        """
        Detectar si chunk contiene código

        Heurísticas:
        - Bloques de código Markdown (```)
        - Líneas con indentación significativa
        - Palabras clave de programación

        Args:
            text: Texto del chunk

        Returns:
            True si detecta código
        """
        # Detectar bloques de código Markdown
        if '```' in text:
            return True

        # Detectar bloques con indentación (4+ espacios)
        lines = text.split('\n')
        indented_lines = sum(
            1 for line in lines
            if line.startswith('    ') or line.startswith('\t')
        )

        if indented_lines >= 3:
            return True

        # Palabras clave de programación comunes
        code_keywords = [
            'function', 'def ', 'class ', 'import ', 'return ',
            'if ', 'else', 'for ', 'while ', 'var ', 'const ',
            'let ', 'async ', 'await ', 'try', 'catch'
        ]

        return any(keyword in text for keyword in code_keywords)

    def chunk_with_markdown_preservation(
        self,
        payload: DocumentPayload
    ) -> List[Dict[str, Any]]:
        """
        Dividir documento preservando estructura Markdown

        Para documentos con estructura (encabezados, tablas),
        preserva formato Markdown en chunks

        Args:
            payload: DocumentPayload con contenido Markdown

        Returns:
            Lista de chunks con estructura Markdown preservada
        """
        # Verificar si contenido tiene Markdown
        has_markdown = any([
            '##' in payload.content,
            '|' in payload.content and '-|-' in payload.content,
            '```' in payload.content
        ])

        if not has_markdown:
            # Si no hay Markdown, usar chunking estándar
            return self.chunk_document(payload)

        # Dividir en secciones por encabezados principales
        sections = self._split_on_headings(payload.content)

        all_chunks = []
        for section in sections:
            # Crear payload temporal para sección
            section_payload = DocumentPayload(
                document_id=payload.document_id,
                org_id=payload.org_id,
                checksum=payload.checksum,
                source_type=payload.source_type,
                source_format=payload.source_format,
                mime_type=payload.mime_type,
                original_path=payload.original_path,
                content=section['content'],
                language=payload.language,
                page_count=payload.page_count,
                sections=payload.sections,
                tables=payload.tables,
                images=payload.images,
                context_tags=payload.context_tags
            )

            # Chunkar sección
            chunks = self.chunk_document(section_payload)

            # Agregar encabezado a cada chunk si existe
            if section.get('heading'):
                for chunk in chunks:
                    chunk['content'] = f"{section['heading']}\n\n{chunk['content']}"
                    chunk['metadata']['heading_level'] = section.get('level', 2)

            all_chunks.extend(chunks)

        return all_chunks

    def _split_on_headings(self, content: str) -> List[Dict[str, Any]]:
        """
        Dividir contenido en secciones por encabezados Markdown

        Args:
            content: Contenido con encabezados Markdown

        Returns:
            Lista de secciones con heading y content
        """
        sections = []
        lines = content.split('\n')

        current_heading = None
        current_level = None
        current_content = []

        for line in lines:
            # Detectar encabezados Markdown (## o más)
            heading_match = re.match(r'^(#{2,6})\s+(.+)$', line)

            if heading_match:
                # Guardar sección anterior
                if current_content:
                    sections.append({
                        'heading': current_heading,
                        'level': current_level,
                        'content': '\n'.join(current_content)
                    })

                # Iniciar nueva sección
                current_level = len(heading_match.group(1))
                current_heading = line
                current_content = []
            else:
                current_content.append(line)

        # Guardar última sección
        if current_content:
            sections.append({
                'heading': current_heading,
                'level': current_level,
                'content': '\n'.join(current_content)
            })

        return sections
