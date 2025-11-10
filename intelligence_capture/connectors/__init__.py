"""
Source Connectors for RAG 2.0 Multi-Format Ingestion
Provides connectors for email, WhatsApp, API, and SharePoint sources

Task 1: Normalize Source Connectors into Inbox Taxonomy
"""
from .base_connector import BaseConnector, ConnectorMetadata
from .connector_registry import ConnectorRegistry
from .email_connector import EmailConnector
from .whatsapp_connector import WhatsAppConnector
from .api_connector import APIConnector
from .sharepoint_connector import SharePointConnector

__all__ = [
    "BaseConnector",
    "ConnectorMetadata",
    "ConnectorRegistry",
    "EmailConnector",
    "WhatsAppConnector",
    "APIConnector",
    "SharePointConnector",
]
