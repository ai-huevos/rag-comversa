"""
Email Connector (IMAP OAuth)
Fetches emails with attachments via IMAP with OAuth authentication

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
import imaplib
import email
from email.header import decode_header
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import mimetypes
from datetime import datetime
import os
from .base_connector import BaseConnector, ConnectorMetadata

logger = logging.getLogger(__name__)


class EmailConnector(BaseConnector):
    """
    Email connector using IMAP with OAuth authentication

    Fetches emails with attachments from specified folder/label.
    Supports Gmail, Outlook, and other IMAP providers.
    """

    def __init__(
        self,
        org_id: str,
        imap_host: str,
        imap_user: str,
        oauth_token: str,
        folder: str = "INBOX",
        business_unit: Optional[str] = None,
        department: Optional[str] = None,
        inbox_root: Path = Path("data/documents/inbox"),
        max_emails: int = 100,
        unread_only: bool = True
    ):
        """
        Initialize email connector

        Args:
            org_id: Organization identifier
            imap_host: IMAP server hostname
            imap_user: IMAP username/email
            oauth_token: OAuth access token
            folder: IMAP folder to monitor (default: 'INBOX')
            business_unit: Business unit (optional)
            department: Department (optional)
            inbox_root: Root directory for inbox taxonomy
            max_emails: Maximum emails to fetch per run
            unread_only: Only fetch unread emails
        """
        super().__init__(org_id, business_unit, department, inbox_root)

        self.imap_host = imap_host
        self.imap_user = imap_user
        self.oauth_token = oauth_token
        self.folder = folder
        self.max_emails = max_emails
        self.unread_only = unread_only
        self.connection: Optional[imaplib.IMAP4_SSL] = None

    def _get_connector_type(self) -> str:
        """Get connector type identifier"""
        return "email"

    def connect(self):
        """
        Connect to IMAP server with OAuth

        Raises:
            Exception: If connection fails (Spanish error)
        """
        try:
            # Connect to IMAP server
            self.connection = imaplib.IMAP4_SSL(self.imap_host)

            # Authenticate with OAuth
            auth_string = f"user={self.imap_user}\x01auth=Bearer {self.oauth_token}\x01\x01"
            self.connection.authenticate('XOAUTH2', lambda x: auth_string)

            # Select folder
            result, data = self.connection.select(self.folder, readonly=False)

            if result != 'OK':
                raise Exception(
                    f"Error al seleccionar carpeta '{self.folder}': {data}"
                )

            logger.info(f"✓ Conectado a IMAP: {self.imap_host}/{self.folder}")

        except Exception as e:
            raise Exception(
                f"Error de conexión IMAP para '{self.org_id}': {e}. "
                "Verifique las credenciales OAuth."
            )

    def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except:
                pass
            self.connection = None

    def get_attachment_mime_type(self, filename: str, content_type: str) -> str:
        """
        Determine MIME type for attachment

        Args:
            filename: Attachment filename
            content_type: Content-Type from email header

        Returns:
            MIME type string
        """
        # Try content_type first
        if content_type and '/' in content_type:
            mime_type = content_type.split(';')[0].strip()
            if mime_type != 'application/octet-stream':
                return mime_type

        # Fall back to guessing from filename
        guessed, _ = mimetypes.guess_type(filename)
        return guessed or 'application/octet-stream'

    async def fetch_documents(self) -> List[ConnectorMetadata]:
        """
        Fetch emails with attachments from IMAP

        Returns:
            List of ConnectorMetadata for extracted attachments

        Raises:
            ValueError: If consent validation fails
            Exception: For IMAP/processing errors
        """
        # Connect to IMAP
        self.connect()

        metadata_list = []

        try:
            # Build search criteria
            search_criteria = 'UNSEEN' if self.unread_only else 'ALL'

            # Search for emails
            result, data = self.connection.search(None, search_criteria)

            if result != 'OK':
                raise Exception(f"Error de búsqueda IMAP: {data}")

            email_ids = data[0].split()

            # Limit to max_emails
            if len(email_ids) > self.max_emails:
                logger.warning(
                    f"⚠️  Encontrados {len(email_ids)} emails, "
                    f"limitando a {self.max_emails}"
                )
                email_ids = email_ids[:self.max_emails]

            # Validate batch size
            self.validate_batch_size(len(email_ids))

            logger.info(f"📧 Procesando {len(email_ids)} emails...")

            # Process each email
            for email_id in email_ids:
                try:
                    # Fetch email
                    result, data = self.connection.fetch(email_id, '(RFC822)')

                    if result != 'OK':
                        continue

                    # Parse email
                    msg = email.message_from_bytes(data[0][1])

                    # Extract metadata
                    subject = str(decode_header(msg['Subject'])[0][0])
                    sender = msg['From']
                    date_str = msg['Date']

                    # Process attachments
                    for part in msg.walk():
                        if part.get_content_maintype() == 'multipart':
                            continue
                        if part.get('Content-Disposition') is None:
                            continue

                        filename = part.get_filename()
                        if not filename:
                            continue

                        # Decode filename
                        decoded = decode_header(filename)[0]
                        filename = decoded[0] if isinstance(decoded[0], str) else decoded[0].decode(decoded[1] or 'utf-8')

                        # Save attachment to temp directory
                        temp_dir = Path("data/documents/temp")
                        temp_dir.mkdir(parents=True, exist_ok=True)

                        temp_file = temp_dir / filename
                        temp_file.write_bytes(part.get_payload(decode=True))

                        # Validate file size
                        try:
                            self.validate_file_size(temp_file)
                        except ValueError as e:
                            logger.warning(f"⚠️  {e}")
                            temp_file.unlink()  # Delete oversized file
                            continue

                        # Determine MIME type
                        mime_type = self.get_attachment_mime_type(
                            filename,
                            part.get_content_type()
                        )

                        # Create metadata envelope
                        connector_metadata = {
                            "email_id": email_id.decode(),
                            "subject": subject,
                            "sender": sender,
                            "received_date": date_str,
                            "attachment_name": filename,
                            "imap_folder": self.folder
                        }

                        metadata = self.create_metadata_envelope(
                            source_path=temp_file,
                            source_format=mime_type,
                            connector_metadata=connector_metadata
                        )

                        # Save to inbox
                        inbox_file = self.save_to_inbox(temp_file, metadata)

                        # Clean up temp file
                        temp_file.unlink()

                        metadata_list.append(metadata)

                        self.log_activity(
                            action="attachment_saved",
                            status="success",
                            details={
                                "filename": filename,
                                "mime_type": mime_type,
                                "email_subject": subject
                            }
                        )

                    # Mark email as read (if processing succeeded)
                    if not self.unread_only:
                        self.connection.store(email_id, '+FLAGS', '\\Seen')

                except Exception as e:
                    logger.error(f"✗ Error procesando email {email_id}: {e}")
                    self.log_activity(
                        action="process_email",
                        status="error",
                        details={
                            "email_id": email_id.decode(),
                            "error": str(e)
                        }
                    )

        finally:
            # Always disconnect
            self.disconnect()

        return metadata_list


# Factory function for easy instantiation
def create_email_connector(
    org_id: str,
    config: Dict[str, Any]
) -> EmailConnector:
    """
    Create email connector from configuration

    Args:
        org_id: Organization identifier
        config: Configuration dict with:
            - imap_host: IMAP server hostname
            - imap_user: IMAP username/email
            - oauth_token: OAuth access token (or env var name)
            - folder: IMAP folder (optional, default: 'INBOX')
            - max_emails: Max emails per run (optional, default: 100)
            - unread_only: Only fetch unread (optional, default: True)

    Returns:
        Configured EmailConnector instance
    """
    # Resolve OAuth token from env if needed
    oauth_token = config.get('oauth_token', '')
    if oauth_token.startswith('env:'):
        env_var = oauth_token[4:]
        oauth_token = os.getenv(env_var, '')
        if not oauth_token:
            raise ValueError(
                f"Variable de entorno '{env_var}' no encontrada para OAuth token"
            )

    return EmailConnector(
        org_id=org_id,
        imap_host=config['imap_host'],
        imap_user=config['imap_user'],
        oauth_token=oauth_token,
        folder=config.get('folder', 'INBOX'),
        business_unit=config.get('business_unit'),
        department=config.get('department'),
        max_emails=config.get('max_emails', 100),
        unread_only=config.get('unread_only', True)
    )
