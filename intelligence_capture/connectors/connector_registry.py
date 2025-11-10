"""
Connector Registry and Factory
Provides factory pattern for connector creation from configuration

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from pathlib import Path
from typing import Dict, Any, Optional, Type
import logging
from .base_connector import BaseConnector
from .email_connector import EmailConnector
from .whatsapp_connector import WhatsAppConnector
from .api_connector import APIConnector
from .sharepoint_connector import SharePointConnector

logger = logging.getLogger(__name__)


class ConnectorRegistry:
    """
    Connector factory and registry

    Provides:
    - Factory pattern for creating connectors from config
    - Connector type validation
    - Configuration validation
    """

    # Map connector types to classes
    CONNECTOR_TYPES: Dict[str, Type[BaseConnector]] = {
        "email": EmailConnector,
        "whatsapp": WhatsAppConnector,
        "api": APIConnector,
        "sharepoint": SharePointConnector
    }

    @classmethod
    def create_connector(
        cls,
        connector_type: str,
        org_id: str,
        config: Dict[str, Any]
    ) -> BaseConnector:
        """
        Create connector instance from configuration

        Args:
            connector_type: Connector type ('email', 'whatsapp', 'api', 'sharepoint')
            org_id: Organization identifier
            config: Connector-specific configuration

        Returns:
            Configured connector instance

        Raises:
            ValueError: If connector type invalid or config missing required fields
        """
        if connector_type not in cls.CONNECTOR_TYPES:
            valid_types = ', '.join(cls.CONNECTOR_TYPES.keys())
            raise ValueError(
                f"Tipo de conector inválido: '{connector_type}'. "
                f"Tipos válidos: {valid_types}"
            )

        connector_class = cls.CONNECTOR_TYPES[connector_type]

        try:
            if connector_type == "email":
                return cls._create_email_connector(org_id, config)
            elif connector_type == "whatsapp":
                return cls._create_whatsapp_connector(org_id, config)
            elif connector_type == "api":
                return cls._create_api_connector(org_id, config)
            elif connector_type == "sharepoint":
                return cls._create_sharepoint_connector(org_id, config)
            else:
                raise ValueError(f"Conector no implementado: {connector_type}")

        except KeyError as e:
            raise ValueError(
                f"Configuración incompleta para conector '{connector_type}': "
                f"falta campo requerido '{e.args[0]}'"
            )

    @classmethod
    def _create_email_connector(
        cls,
        org_id: str,
        config: Dict[str, Any]
    ) -> EmailConnector:
        """Create email connector from config"""
        import os

        # Resolve OAuth token from env if needed
        oauth_token = config['oauth_token']
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

    @classmethod
    def _create_whatsapp_connector(
        cls,
        org_id: str,
        config: Dict[str, Any]
    ) -> WhatsAppConnector:
        """Create WhatsApp connector from config"""
        return WhatsAppConnector(
            org_id=org_id,
            export_directory=Path(config['export_directory']),
            business_unit=config.get('business_unit'),
            department=config.get('department'),
            include_media=config.get('include_media', True)
        )

    @classmethod
    def _create_api_connector(
        cls,
        org_id: str,
        config: Dict[str, Any]
    ) -> APIConnector:
        """Create API connector from config"""
        return APIConnector(
            org_id=org_id,
            api_url=config['api_url'],
            auth_config=config['auth_config'],
            business_unit=config.get('business_unit'),
            department=config.get('department'),
            pagination_config=config.get('pagination_config'),
            rate_limit_delay=config.get('rate_limit_delay', 1.0)
        )

    @classmethod
    def _create_sharepoint_connector(
        cls,
        org_id: str,
        config: Dict[str, Any]
    ) -> SharePointConnector:
        """Create SharePoint connector from config"""
        import os

        # Resolve client secret from env if needed
        client_secret = config['client_secret']
        if client_secret.startswith('env:'):
            env_var = client_secret[4:]
            client_secret = os.getenv(env_var, '')
            if not client_secret:
                raise ValueError(
                    f"Variable de entorno '{env_var}' no encontrada para client_secret"
                )

        return SharePointConnector(
            org_id=org_id,
            site_url=config['site_url'],
            folder_path=config['folder_path'],
            client_id=config['client_id'],
            client_secret=client_secret,
            business_unit=config.get('business_unit'),
            department=config.get('department'),
            recursive=config.get('recursive', True),
            file_extensions=config.get('file_extensions')
        )

    @classmethod
    def create_from_config_file(
        cls,
        config_file: Path
    ) -> Dict[str, BaseConnector]:
        """
        Create multiple connectors from YAML config file

        Config format:
        ```yaml
        connectors:
          - org_id: los_tajibos
            type: email
            config:
              imap_host: imap.gmail.com
              imap_user: hotel@lostajibos.com
              oauth_token: env:TAJIBOS_GMAIL_TOKEN
              business_unit: Hotel

          - org_id: comversa
            type: whatsapp
            config:
              export_directory: data/whatsapp_exports/comversa
              business_unit: Construcción
        ```

        Args:
            config_file: Path to YAML configuration file

        Returns:
            Dict mapping connector keys to connector instances
        """
        import yaml

        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        connectors = {}

        for connector_def in config.get('connectors', []):
            org_id = connector_def['org_id']
            connector_type = connector_def['type']
            connector_config = connector_def['config']

            # Create connector
            connector = cls.create_connector(
                connector_type=connector_type,
                org_id=org_id,
                config=connector_config
            )

            # Store with unique key
            key = f"{org_id}:{connector_type}"
            connectors[key] = connector

            logger.info(
                f"✓ Registered {connector_type} connector for {org_id}"
            )

        return connectors

    @classmethod
    def get_supported_types(cls) -> List[str]:
        """
        Get list of supported connector types

        Returns:
            List of connector type strings
        """
        return list(cls.CONNECTOR_TYPES.keys())

    @classmethod
    def validate_config(
        cls,
        connector_type: str,
        config: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate connector configuration

        Args:
            connector_type: Connector type
            config: Configuration dict

        Returns:
            Tuple of (is_valid, error_message_spanish)
        """
        if connector_type not in cls.CONNECTOR_TYPES:
            return False, f"Tipo de conector inválido: '{connector_type}'"

        # Required fields by connector type
        required_fields = {
            "email": ['imap_host', 'imap_user', 'oauth_token'],
            "whatsapp": ['export_directory'],
            "api": ['api_url', 'auth_config'],
            "sharepoint": ['site_url', 'folder_path', 'client_id', 'client_secret']
        }

        missing_fields = [
            field for field in required_fields[connector_type]
            if field not in config
        ]

        if missing_fields:
            return False, (
                f"Configuración incompleta para conector '{connector_type}': "
                f"faltan campos {', '.join(missing_fields)}"
            )

        return True, None
