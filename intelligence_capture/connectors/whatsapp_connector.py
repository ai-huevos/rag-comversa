"""
WhatsApp Connector
Parses WhatsApp export files (text and JSON formats)

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import json
import re
from datetime import datetime
from .base_connector import BaseConnector, ConnectorMetadata

logger = logging.getLogger(__name__)


class WhatsAppConnector(BaseConnector):
    """
    WhatsApp connector for processing export files

    Supports:
    - WhatsApp export text format (_chat.txt)
    - WhatsApp JSON export format
    """

    def __init__(
        self,
        org_id: str,
        export_directory: Path,
        business_unit: Optional[str] = None,
        department: Optional[str] = None,
        inbox_root: Path = Path("data/documents/inbox"),
        include_media: bool = True
    ):
        """
        Initialize WhatsApp connector

        Args:
            org_id: Organization identifier
            export_directory: Directory containing WhatsApp exports
            business_unit: Business unit (optional)
            department: Department (optional)
            inbox_root: Root directory for inbox taxonomy
            include_media: Include media attachments (images, videos, docs)
        """
        super().__init__(org_id, business_unit, department, inbox_root)

        self.export_directory = Path(export_directory)
        self.include_media = include_media

        if not self.export_directory.exists():
            raise ValueError(
                f"Directorio de exportación WhatsApp no existe: {export_directory}"
            )

    def _get_connector_type(self) -> str:
        """Get connector type identifier"""
        return "whatsapp"

    def parse_text_export(self, export_file: Path) -> Dict[str, Any]:
        """
        Parse WhatsApp text export format

        Format: [DD/MM/YYYY, HH:MM:SS] Contact Name: Message text

        Args:
            export_file: Path to _chat.txt file

        Returns:
            Parsed conversation data
        """
        messages = []
        message_pattern = r'\[(\d{1,2}/\d{1,2}/\d{4}), (\d{1,2}:\d{2}:\d{2})\] ([^:]+): (.+)'

        with open(export_file, 'r', encoding='utf-8') as f:
            content = f.read()

            for match in re.finditer(message_pattern, content, re.MULTILINE):
                date, time, sender, text = match.groups()

                messages.append({
                    "date": date,
                    "time": time,
                    "sender": sender.strip(),
                    "text": text.strip()
                })

        return {
            "format": "whatsapp_text_export",
            "message_count": len(messages),
            "messages": messages,
            "export_file": str(export_file)
        }

    def parse_json_export(self, export_file: Path) -> Dict[str, Any]:
        """
        Parse WhatsApp JSON export format

        Args:
            export_file: Path to JSON export file

        Returns:
            Parsed conversation data
        """
        with open(export_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return {
            "format": "whatsapp_json_export",
            "message_count": len(data.get("messages", [])),
            **data
        }

    def convert_to_structured_document(
        self,
        conversation_data: Dict[str, Any],
        output_path: Path
    ):
        """
        Convert conversation to structured JSON document

        Args:
            conversation_data: Parsed conversation data
            output_path: Path to save structured document
        """
        # Create structured format for ingestion
        structured = {
            "document_type": "whatsapp_conversation",
            "metadata": {
                "source_format": conversation_data["format"],
                "message_count": conversation_data["message_count"],
                "export_date": datetime.now().isoformat()
            },
            "content": conversation_data
        }

        output_path.write_text(
            json.dumps(structured, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

    async def fetch_documents(self) -> List[ConnectorMetadata]:
        """
        Fetch WhatsApp export files

        Returns:
            List of ConnectorMetadata for processed exports

        Raises:
            ValueError: If consent validation fails
        """
        metadata_list = []

        # Find all WhatsApp export files
        text_exports = list(self.export_directory.glob("**/*_chat.txt"))
        json_exports = list(self.export_directory.glob("**/*.json"))

        all_exports = text_exports + json_exports

        # Validate batch size
        self.validate_batch_size(len(all_exports))

        logger.info(
            f"📱 Encontrados {len(text_exports)} exports de texto y "
            f"{len(json_exports)} exports JSON"
        )

        # Process each export
        for export_file in all_exports:
            try:
                # Validate file size
                self.validate_file_size(export_file)

                # Parse based on format
                if export_file.name.endswith('_chat.txt'):
                    conversation_data = self.parse_text_export(export_file)
                else:
                    conversation_data = self.parse_json_export(export_file)

                # Convert to structured JSON
                temp_dir = Path("data/documents/temp")
                temp_dir.mkdir(parents=True, exist_ok=True)

                structured_file = temp_dir / f"{export_file.stem}_structured.json"
                self.convert_to_structured_document(conversation_data, structured_file)

                # Create metadata envelope
                connector_metadata = {
                    "original_file": str(export_file),
                    "message_count": conversation_data["message_count"],
                    "format": conversation_data["format"]
                }

                metadata = self.create_metadata_envelope(
                    source_path=structured_file,
                    source_format="application/json",
                    connector_metadata=connector_metadata
                )

                # Save to inbox
                self.save_to_inbox(structured_file, metadata)

                # Clean up temp file
                structured_file.unlink()

                metadata_list.append(metadata)

                self.log_activity(
                    action="whatsapp_export_processed",
                    status="success",
                    details={
                        "file": str(export_file),
                        "messages": conversation_data["message_count"]
                    }
                )

            except Exception as e:
                logger.error(f"✗ Error procesando {export_file}: {e}")
                self.log_activity(
                    action="process_export",
                    status="error",
                    details={
                        "file": str(export_file),
                        "error": str(e)
                    }
                )

        # Process media attachments if enabled
        if self.include_media:
            media_files = []
            for ext in ['.jpg', '.jpeg', '.png', '.pdf', '.docx', '.mp4']:
                media_files.extend(self.export_directory.glob(f"**/*{ext}"))

            for media_file in media_files:
                try:
                    self.validate_file_size(media_file)

                    import mimetypes
                    mime_type, _ = mimetypes.guess_type(str(media_file))
                    mime_type = mime_type or 'application/octet-stream'

                    connector_metadata = {
                        "media_type": "attachment",
                        "original_filename": media_file.name
                    }

                    metadata = self.create_metadata_envelope(
                        source_path=media_file,
                        source_format=mime_type,
                        connector_metadata=connector_metadata
                    )

                    self.save_to_inbox(media_file, metadata)
                    metadata_list.append(metadata)

                except ValueError as e:
                    logger.warning(f"⚠️  {e}")
                except Exception as e:
                    logger.error(f"✗ Error procesando media {media_file}: {e}")

        return metadata_list
