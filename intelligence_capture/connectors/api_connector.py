"""
API Connector
Fetches documents from API endpoints (generic dumps)

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
import logging
import json
import requests
from datetime import datetime
import time
from .base_connector import BaseConnector, ConnectorMetadata

logger = logging.getLogger(__name__)


class APIConnector(BaseConnector):
    """
    Generic API connector for document dumps

    Supports REST APIs with:
    - JSON responses
    - Pagination
    - Authentication (API key, Bearer token, Basic auth)
    - Rate limiting
    """

    def __init__(
        self,
        org_id: str,
        api_url: str,
        auth_config: Dict[str, Any],
        business_unit: Optional[str] = None,
        department: Optional[str] = None,
        inbox_root: Path = Path("data/documents/inbox"),
        pagination_config: Optional[Dict[str, Any]] = None,
        rate_limit_delay: float = 1.0,
        response_parser: Optional[Callable] = None
    ):
        """
        Initialize API connector

        Args:
            org_id: Organization identifier
            api_url: API endpoint URL
            auth_config: Authentication configuration:
                - type: 'api_key' | 'bearer' | 'basic' | 'none'
                - api_key: API key value (for api_key type)
                - token: Bearer token (for bearer type)
                - username/password: For basic auth
                - header_name: Custom header name (optional)
            business_unit: Business unit (optional)
            department: Department (optional)
            inbox_root: Root directory for inbox taxonomy
            pagination_config: Pagination configuration (optional):
                - type: 'offset' | 'page' | 'cursor' | 'none'
                - page_size: Items per page
                - max_pages: Maximum pages to fetch
            rate_limit_delay: Delay between requests in seconds
            response_parser: Custom response parser function (optional)
        """
        super().__init__(org_id, business_unit, department, inbox_root)

        self.api_url = api_url
        self.auth_config = auth_config
        self.pagination_config = pagination_config or {"type": "none"}
        self.rate_limit_delay = rate_limit_delay
        self.response_parser = response_parser or self._default_parser

        self.session = requests.Session()
        self._setup_authentication()

    def _get_connector_type(self) -> str:
        """Get connector type identifier"""
        return "api"

    def _setup_authentication(self):
        """Setup authentication headers"""
        auth_type = self.auth_config.get("type", "none")

        if auth_type == "api_key":
            header_name = self.auth_config.get("header_name", "X-API-Key")
            self.session.headers[header_name] = self.auth_config["api_key"]

        elif auth_type == "bearer":
            self.session.headers["Authorization"] = f"Bearer {self.auth_config['token']}"

        elif auth_type == "basic":
            from requests.auth import HTTPBasicAuth
            self.session.auth = HTTPBasicAuth(
                self.auth_config["username"],
                self.auth_config["password"]
            )

    def _default_parser(self, response_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Default response parser

        Expects response format:
        {
            "data": [
                {"id": "...", "content": "...", ...},
                ...
            ]
        }

        Args:
            response_data: API response JSON

        Returns:
            List of document records
        """
        if isinstance(response_data, list):
            return response_data
        elif "data" in response_data:
            return response_data["data"]
        elif "results" in response_data:
            return response_data["results"]
        else:
            return [response_data]

    def fetch_page(self, page: int = 1, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch single page from API

        Args:
            page: Page number (for page/offset pagination)
            cursor: Cursor value (for cursor pagination)

        Returns:
            API response JSON

        Raises:
            Exception: If API request fails (Spanish error)
        """
        pagination_type = self.pagination_config.get("type", "none")
        params = {}

        if pagination_type == "page":
            params["page"] = page
            params["page_size"] = self.pagination_config.get("page_size", 100)

        elif pagination_type == "offset":
            page_size = self.pagination_config.get("page_size", 100)
            params["offset"] = (page - 1) * page_size
            params["limit"] = page_size

        elif pagination_type == "cursor" and cursor:
            params["cursor"] = cursor
            params["page_size"] = self.pagination_config.get("page_size", 100)

        try:
            response = self.session.get(self.api_url, params=params, timeout=30)
            response.raise_for_status()

            # Rate limiting
            time.sleep(self.rate_limit_delay)

            return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(
                f"Error de solicitud API para '{self.org_id}': {e}. "
                "Verifique la URL y las credenciales de autenticación."
            )

    async def fetch_documents(self) -> List[ConnectorMetadata]:
        """
        Fetch documents from API

        Returns:
            List of ConnectorMetadata for fetched documents

        Raises:
            ValueError: If consent validation fails
        """
        metadata_list = []
        all_records = []

        pagination_type = self.pagination_config.get("type", "none")
        max_pages = self.pagination_config.get("max_pages", 10)

        if pagination_type == "none":
            # Single request, no pagination
            response_data = self.fetch_page()
            all_records = self.response_parser(response_data)

        elif pagination_type in ["page", "offset"]:
            # Page/offset pagination
            for page in range(1, max_pages + 1):
                logger.info(f"Fetching page {page}...")

                response_data = self.fetch_page(page=page)
                records = self.response_parser(response_data)

                if not records:
                    break

                all_records.extend(records)

                # Check for end of data
                if len(records) < self.pagination_config.get("page_size", 100):
                    break

        elif pagination_type == "cursor":
            # Cursor pagination
            cursor = None
            page = 1

            while page <= max_pages:
                logger.info(f"Fetching page {page} (cursor: {cursor})...")

                response_data = self.fetch_page(cursor=cursor)
                records = self.response_parser(response_data)

                if not records:
                    break

                all_records.extend(records)

                # Get next cursor
                cursor = response_data.get("next_cursor") or response_data.get("cursor")
                if not cursor:
                    break

                page += 1

        # Validate batch size
        self.validate_batch_size(len(all_records))

        logger.info(f"📡 Fetched {len(all_records)} records from API")

        # Save each record as JSON document
        temp_dir = Path("data/documents/temp")
        temp_dir.mkdir(parents=True, exist_ok=True)

        for idx, record in enumerate(all_records):
            try:
                # Generate filename
                record_id = record.get("id", f"record_{idx}")
                filename = f"api_dump_{record_id}.json"
                temp_file = temp_dir / filename

                # Save record as JSON
                temp_file.write_text(
                    json.dumps(record, ensure_ascii=False, indent=2),
                    encoding='utf-8'
                )

                # Validate file size
                self.validate_file_size(temp_file)

                # Create metadata envelope
                connector_metadata = {
                    "record_id": record_id,
                    "api_url": self.api_url,
                    "fetched_at": datetime.now().isoformat()
                }

                metadata = self.create_metadata_envelope(
                    source_path=temp_file,
                    source_format="application/json",
                    connector_metadata=connector_metadata
                )

                # Save to inbox
                self.save_to_inbox(temp_file, metadata)

                # Clean up temp file
                temp_file.unlink()

                metadata_list.append(metadata)

            except ValueError as e:
                logger.warning(f"⚠️  {e}")
            except Exception as e:
                logger.error(f"✗ Error procesando record {idx}: {e}")

        return metadata_list
