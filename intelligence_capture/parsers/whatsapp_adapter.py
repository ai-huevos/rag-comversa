"""
WhatsApp chat export adapter

Parses WhatsApp JSON exports and converts conversations to structured text.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime

from .base_adapter import BaseAdapter
from ..models.document_payload import DocumentPayload


class WhatsAppAdapter(BaseAdapter):
    """
    WhatsApp chat export parsing adapter

    Parses WhatsApp chat exports (JSON format) and converts conversations
    into structured text suitable for entity extraction and embedding.

    Expected JSON format:
    [
        {
            "timestamp": "2024-01-15T10:30:00",
            "sender": "Patricia García",
            "message": "¿Cómo va el proceso de facturación?"
        },
        ...
    ]

    Example:
        >>> adapter = WhatsAppAdapter()
        >>> payload = adapter.parse(Path('chat.json'), metadata)
        >>> payload.metadata['message_count']
        150
        >>> payload.content[:50]
        'Conversación de WhatsApp\\nParticipantes: Patricia...'
    """

    @property
    def supported_mime_types(self) -> List[str]:
        """WhatsApp export MIME types"""
        return [
            'application/json',
            'text/json'
        ]

    def parse(
        self,
        file_path: Path,
        metadata: Dict[str, Any]
    ) -> DocumentPayload:
        """
        Parse WhatsApp chat export

        Reads JSON export, identifies participants, and converts
        messages into chronological text representation.

        Args:
            file_path: Path to WhatsApp JSON export
            metadata: Connector metadata

        Returns:
            DocumentPayload with conversation as structured text

        Raises:
            ValueError: If JSON parsing or validation fails
        """
        # Validate inputs
        self.validate_metadata(metadata)

        if not file_path.exists():
            raise FileNotFoundError(
                f"Archivo WhatsApp no encontrado: {file_path}"
            )

        start_time = datetime.now()

        try:
            # Read JSON with UTF-8 encoding (handles Spanish)
            with open(file_path, 'r', encoding='utf-8') as f:
                messages = json.load(f)

            if not isinstance(messages, list):
                raise ValueError(
                    f"Formato WhatsApp inválido: se esperaba lista de mensajes"
                )

            # Extract participants
            participants = set()
            for msg in messages:
                if 'sender' in msg:
                    participants.add(msg['sender'])

            # Create header
            content_parts = [
                "Conversación de WhatsApp",
                f"Participantes: {', '.join(sorted(participants))}",
                f"Mensajes: {len(messages)}",
                "",
                "Mensajes:"
            ]

            # Format messages chronologically
            for msg in messages:
                timestamp = msg.get('timestamp', 'Sin timestamp')
                sender = msg.get('sender', 'Desconocido')
                text = msg.get('message', '')

                # Format: [Timestamp] Sender: Message
                content_parts.append(
                    f"[{timestamp}] {sender}: {text}"
                )

            full_content = '\n'.join(content_parts)

            # Detect language
            language = self.detect_language(full_content)

            # Create sections by day (if timestamps available)
            sections = self._extract_day_sections(messages)

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()

            # Create payload
            return DocumentPayload(
                # Identity
                document_id=metadata['document_id'],
                org_id=metadata['org_id'],
                checksum=metadata['checksum'],

                # Source metadata
                source_type=metadata.get('source_type', 'whatsapp'),
                source_format='whatsapp_json',
                mime_type='application/json',
                original_path=file_path,

                # Content (Spanish preserved)
                content=full_content,
                language=language,

                # Structure
                page_count=1,
                sections=sections,
                tables=[],
                images=[],

                # Processing metadata
                context_tags=metadata.get('context_tags', []),
                processed_at=start_time,
                processing_time_seconds=processing_time,

                # Additional metadata
                metadata={
                    **metadata,
                    'parser': 'WhatsAppAdapter',
                    'message_count': len(messages),
                    'participant_count': len(participants),
                    'participants': list(sorted(participants))
                }
            )

        except json.JSONDecodeError as e:
            raise ValueError(
                f"Error al parsear JSON de WhatsApp {file_path.name}: {e}"
            )
        except Exception as e:
            raise ValueError(
                f"Error procesando WhatsApp {file_path.name}: {e}"
            )

    def _extract_day_sections(
        self,
        messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Extract conversation sections by day

        Groups messages by date to create logical sections.

        Args:
            messages: List of message dictionaries

        Returns:
            List of section dictionaries with day as title
        """
        sections = []
        current_day = None

        for msg in messages:
            timestamp = msg.get('timestamp', '')
            if not timestamp:
                continue

            # Extract date (YYYY-MM-DD)
            try:
                date_part = timestamp.split('T')[0]
                if date_part != current_day:
                    current_day = date_part
                    sections.append({
                        'title': f"Fecha: {date_part}",
                        'level': 1,
                        'page': 1
                    })
            except (IndexError, ValueError):
                continue

        return sections
