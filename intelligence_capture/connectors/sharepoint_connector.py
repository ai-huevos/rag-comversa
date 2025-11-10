"""
SharePoint Connector
Fetches documents from SharePoint/OneDrive folders

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import mimetypes
from datetime import datetime
import os
from .base_connector import BaseConnector, ConnectorMetadata

logger = logging.getLogger(__name__)


class SharePointConnector(BaseConnector):
    """
    SharePoint/OneDrive connector

    Supports:
    - SharePoint Online document libraries
    - OneDrive for Business shared folders
    - Office 365 Groups document libraries

    Note: Requires Office365-REST-Python-Client library
    """

    def __init__(
        self,
        org_id: str,
        site_url: str,
        folder_path: str,
        client_id: str,
        client_secret: str,
        business_unit: Optional[str] = None,
        department: Optional[str] = None,
        inbox_root: Path = Path("data/documents/inbox"),
        recursive: bool = True,
        file_extensions: Optional[List[str]] = None
    ):
        """
        Initialize SharePoint connector

        Args:
            org_id: Organization identifier
            site_url: SharePoint site URL
            folder_path: Document library folder path
            client_id: Azure AD app client ID
            client_secret: Azure AD app client secret
            business_unit: Business unit (optional)
            department: Department (optional)
            inbox_root: Root directory for inbox taxonomy
            recursive: Recursively fetch subfolders
            file_extensions: Allowed file extensions (default: common docs)
        """
        super().__init__(org_id, business_unit, department, inbox_root)

        self.site_url = site_url
        self.folder_path = folder_path
        self.client_id = client_id
        self.client_secret = client_secret
        self.recursive = recursive
        self.file_extensions = file_extensions or [
            '.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv',
            '.jpg', '.jpeg', '.png', '.json'
        ]

        self.context = None

    def _get_connector_type(self) -> str:
        """Get connector type identifier"""
        return "sharepoint"

    def connect(self):
        """
        Connect to SharePoint site

        Raises:
            Exception: If connection fails (Spanish error)
        """
        try:
            from office365.runtime.auth.client_credential import ClientCredential
            from office365.sharepoint.client_context import ClientContext

            # Authenticate with client credentials
            credentials = ClientCredential(self.client_id, self.client_secret)
            self.context = ClientContext(self.site_url).with_credentials(credentials)

            # Test connection
            web = self.context.web
            self.context.load(web)
            self.context.execute_query()

            logger.info(f"✓ Conectado a SharePoint: {web.properties['Title']}")

        except Exception as e:
            raise Exception(
                f"Error de conexión SharePoint para '{self.org_id}': {e}. "
                "Verifique las credenciales de Azure AD."
            )

    def download_file(self, file_item: Any, temp_dir: Path) -> Path:
        """
        Download file from SharePoint

        Args:
            file_item: SharePoint file item
            temp_dir: Temporary download directory

        Returns:
            Path to downloaded file
        """
        filename = file_item.properties["Name"]
        temp_file = temp_dir / filename

        with open(temp_file, 'wb') as local_file:
            file_item.download(local_file).execute_query()

        return temp_file

    def list_files(self, folder_url: str, recursive: bool = True) -> List[Any]:
        """
        List files in SharePoint folder

        Args:
            folder_url: Folder URL path
            recursive: Recursively list subfolders

        Returns:
            List of SharePoint file items
        """
        files = []

        # Get folder
        folder = self.context.web.get_folder_by_server_relative_url(folder_url)
        self.context.load(folder)
        self.context.execute_query()

        # Get files in folder
        folder_files = folder.files
        self.context.load(folder_files)
        self.context.execute_query()

        for file_item in folder_files:
            filename = file_item.properties["Name"]
            ext = Path(filename).suffix.lower()

            # Filter by extension
            if ext in self.file_extensions:
                files.append(file_item)

        # Recursively process subfolders
        if recursive:
            subfolders = folder.folders
            self.context.load(subfolders)
            self.context.execute_query()

            for subfolder in subfolders:
                subfolder_url = subfolder.properties["ServerRelativeUrl"]
                files.extend(self.list_files(subfolder_url, recursive=True))

        return files

    async def fetch_documents(self) -> List[ConnectorMetadata]:
        """
        Fetch documents from SharePoint folder

        Returns:
            List of ConnectorMetadata for fetched documents

        Raises:
            ValueError: If consent validation fails
        """
        # Connect to SharePoint
        self.connect()

        metadata_list = []

        try:
            # List files
            logger.info(f"📂 Listando archivos en {self.folder_path}...")
            files = self.list_files(self.folder_path, recursive=self.recursive)

            # Validate batch size
            self.validate_batch_size(len(files))

            logger.info(f"Encontrados {len(files)} archivos")

            # Create temp directory
            temp_dir = Path("data/documents/temp")
            temp_dir.mkdir(parents=True, exist_ok=True)

            # Download and process each file
            for file_item in files:
                try:
                    filename = file_item.properties["Name"]
                    file_size = file_item.properties["Length"]

                    # Check file size before downloading
                    if file_size > self.MAX_FILE_SIZE:
                        size_mb = file_size / 1024 / 1024
                        limit_mb = self.MAX_FILE_SIZE / 1024 / 1024
                        logger.warning(
                            f"⚠️  Archivo '{filename}' excede límite "
                            f"({size_mb:.1f} MB > {limit_mb:.0f} MB)"
                        )
                        continue

                    # Download file
                    logger.info(f"⬇️  Descargando {filename}...")
                    temp_file = self.download_file(file_item, temp_dir)

                    # Validate file size (double-check)
                    self.validate_file_size(temp_file)

                    # Determine MIME type
                    mime_type, _ = mimetypes.guess_type(str(temp_file))
                    mime_type = mime_type or 'application/octet-stream'

                    # Create metadata envelope
                    connector_metadata = {
                        "sharepoint_url": file_item.properties["ServerRelativeUrl"],
                        "created": file_item.properties.get("TimeCreated", ""),
                        "modified": file_item.properties.get("TimeLastModified", ""),
                        "author": file_item.properties.get("Author", ""),
                        "file_size": file_size
                    }

                    metadata = self.create_metadata_envelope(
                        source_path=temp_file,
                        source_format=mime_type,
                        connector_metadata=connector_metadata
                    )

                    # Save to inbox
                    self.save_to_inbox(temp_file, metadata)

                    # Clean up temp file
                    temp_file.unlink()

                    metadata_list.append(metadata)

                    self.log_activity(
                        action="file_downloaded",
                        status="success",
                        details={
                            "filename": filename,
                            "mime_type": mime_type,
                            "size_bytes": file_size
                        }
                    )

                except ValueError as e:
                    logger.warning(f"⚠️  {e}")
                except Exception as e:
                    logger.error(f"✗ Error procesando {filename}: {e}")
                    self.log_activity(
                        action="process_file",
                        status="error",
                        details={
                            "filename": filename if 'filename' in locals() else 'unknown',
                            "error": str(e)
                        }
                    )

        finally:
            # Cleanup handled per-file
            pass

        return metadata_list
