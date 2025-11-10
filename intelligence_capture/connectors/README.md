# Source Connectors - RAG 2.0

Multi-format document ingestion connectors for RAG 2.0 enhancement.

## Overview

The connector system provides **4 specialized connectors** for fetching documents from various sources:

1. **EmailConnector** - IMAP OAuth for email attachments
2. **WhatsAppConnector** - WhatsApp export parser (text/JSON)
3. **APIConnector** - Generic REST API dumps
4. **SharePointConnector** - SharePoint/OneDrive folders

All connectors:
- ✅ Validate consent via ContextRegistry
- ✅ Enforce file size limits (50 MB)
- ✅ Enforce batch limits (≤100 docs)
- ✅ Calculate SHA-256 checksums
- ✅ Generate metadata envelopes
- ✅ Organize files in inbox taxonomy
- ✅ Log activity in Spanish
- ✅ Return Spanish error messages

## Quick Start

### 1. Create Configuration File

Create `config/connectors.yaml`:

```yaml
connectors:
  # Email connector for Los Tajibos hotel
  - org_id: los_tajibos
    type: email
    config:
      imap_host: imap.gmail.com
      imap_user: hotel@lostajibos.com
      oauth_token: env:TAJIBOS_GMAIL_TOKEN  # From environment variable
      folder: INBOX
      business_unit: Hotel
      max_emails: 100
      unread_only: true

  # WhatsApp connector for Comversa
  - org_id: comversa
    type: whatsapp
    config:
      export_directory: data/whatsapp_exports/comversa
      business_unit: Construcción
      include_media: true

  # API connector for Bolivian Foods
  - org_id: bolivian_foods
    type: api
    config:
      api_url: https://api.bolivianfoods.com/documents
      auth_config:
        type: bearer
        token: env:BOLIVIAN_FOODS_API_TOKEN
      business_unit: Producción
      pagination_config:
        type: page
        page_size: 50
        max_pages: 10
      rate_limit_delay: 1.0

  # SharePoint connector for Los Tajibos
  - org_id: los_tajibos
    type: sharepoint
    config:
      site_url: https://lostajibos.sharepoint.com/sites/hotel
      folder_path: /Shared Documents/Operaciones
      client_id: env:SHAREPOINT_CLIENT_ID
      client_secret: env:SHAREPOINT_CLIENT_SECRET
      business_unit: Hotel
      recursive: true
      file_extensions: ['.pdf', '.docx', '.xlsx']
```

### 2. Set Environment Variables

```bash
export TAJIBOS_GMAIL_TOKEN="ya29.a0AfH6SMBx..."
export BOLIVIAN_FOODS_API_TOKEN="bf_live_abc123..."
export SHAREPOINT_CLIENT_ID="12345678-1234-1234-1234-123456789012"
export SHAREPOINT_CLIENT_SECRET="abc123..."
export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
```

### 3. Run Connectors

```python
import asyncio
from pathlib import Path
from intelligence_capture.connectors import ConnectorRegistry

async def run_connectors():
    # Load connectors from config
    connectors = ConnectorRegistry.create_from_config_file(
        Path("config/connectors.yaml")
    )

    # Run all connectors
    for key, connector in connectors.items():
        print(f"\n🔌 Running {key}...")
        result = await connector.run()
        print(f"✓ Status: {result['status']}")
        print(f"  Documents fetched: {result.get('documents_fetched', 0)}")

if __name__ == "__main__":
    asyncio.run(run_connectors())
```

## Connector Details

### EmailConnector

**Purpose**: Fetch email attachments via IMAP with OAuth authentication.

**Supported Providers**:
- Gmail (imap.gmail.com)
- Outlook (outlook.office365.com)
- Any IMAP server with OAuth support

**Configuration**:
```yaml
type: email
config:
  imap_host: imap.gmail.com           # IMAP server
  imap_user: user@domain.com           # Email address
  oauth_token: env:GMAIL_TOKEN         # OAuth token
  folder: INBOX                        # IMAP folder (default: INBOX)
  max_emails: 100                      # Max emails per run
  unread_only: true                    # Only fetch unread
  business_unit: Hotel                 # Optional
  department: Recepción                # Optional
```

**OAuth Setup**:
1. Create OAuth app in Google/Microsoft admin console
2. Request IMAP scope: `https://mail.google.com/`
3. Store access token in environment variable
4. Token refresh handled by connector

**Output**:
- Attachments saved to `data/documents/inbox/email/{org_id}/`
- Metadata includes: email subject, sender, date, attachment name

### WhatsAppConnector

**Purpose**: Parse WhatsApp export files and media attachments.

**Supported Formats**:
- Text exports (`_chat.txt`)
- JSON exports (official WhatsApp format)
- Media files (images, videos, documents)

**Configuration**:
```yaml
type: whatsapp
config:
  export_directory: data/whatsapp_exports/comversa  # Export location
  include_media: true                                 # Include media files
  business_unit: Construcción                        # Optional
```

**Export Process**:
1. Open WhatsApp chat
2. Menu → More → Export chat
3. Choose "With Media" or "Without Media"
4. Extract ZIP to `export_directory`

**Output**:
- Structured JSON documents with message history
- Media files preserved with original names
- Message count and format tracked in metadata

### APIConnector

**Purpose**: Fetch documents from REST API endpoints with pagination.

**Supported Auth**:
- API Key (custom header or query param)
- Bearer Token
- Basic Auth
- No auth

**Configuration**:
```yaml
type: api
config:
  api_url: https://api.example.com/documents
  auth_config:
    type: bearer                    # api_key | bearer | basic | none
    token: env:API_TOKEN             # For bearer type
    # OR
    # type: api_key
    # api_key: env:API_KEY
    # header_name: X-API-Key
    # OR
    # type: basic
    # username: user
    # password: env:PASSWORD
  pagination_config:
    type: page                       # offset | page | cursor | none
    page_size: 100
    max_pages: 10
  rate_limit_delay: 1.0              # Seconds between requests
```

**Pagination Types**:
- **page**: `?page=1&page_size=100`
- **offset**: `?offset=0&limit=100`
- **cursor**: `?cursor=abc123&page_size=100`
- **none**: Single request, no pagination

**Custom Response Parsers**:
```python
def custom_parser(response_data):
    """Extract documents from custom API response"""
    return response_data["documents"]["items"]

connector = APIConnector(
    org_id="custom_org",
    api_url="https://api.custom.com/docs",
    auth_config={"type": "none"},
    response_parser=custom_parser
)
```

### SharePointConnector

**Purpose**: Fetch documents from SharePoint/OneDrive folders.

**Supported Sources**:
- SharePoint Online document libraries
- OneDrive for Business shared folders
- Office 365 Groups document libraries

**Configuration**:
```yaml
type: sharepoint
config:
  site_url: https://company.sharepoint.com/sites/team
  folder_path: /Shared Documents/Projects
  client_id: env:SP_CLIENT_ID          # Azure AD app ID
  client_secret: env:SP_CLIENT_SECRET  # Azure AD app secret
  recursive: true                       # Scan subfolders
  file_extensions:                      # Optional filter
    - .pdf
    - .docx
    - .xlsx
```

**Azure AD Setup**:
1. Register app in Azure AD
2. Grant SharePoint permissions:
   - `Sites.Read.All` (application permission)
3. Create client secret
4. Note Application (client) ID and secret

**Output**:
- Files downloaded to `data/documents/inbox/sharepoint/{org_id}/`
- Metadata includes: SharePoint URL, created/modified dates, author

## Inbox Taxonomy

All connectors organize files using consistent taxonomy:

```
data/documents/inbox/
├── email/
│   └── los_tajibos/
│       ├── a1b2c3d4e5f6_attachment.pdf
│       └── a1b2c3d4e5f6_attachment.pdf.meta.json
├── whatsapp/
│   └── comversa/
│       ├── x1y2z3a4b5c6_chat.json
│       └── x1y2z3a4b5c6_chat.json.meta.json
├── api/
│   └── bolivian_foods/
│       └── ...
└── sharepoint/
    └── los_tajibos/
        └── ...
```

**Naming Convention**:
- `{checksum[0:16]}_{original_filename}`
- Prevents duplicates, enables resume
- Metadata JSON alongside each file

## Metadata Envelope Format

Each file has accompanying `.meta.json`:

```json
{
  "source_path": "data/documents/inbox/email/los_tajibos/a1b2c3d4e5f6_doc.pdf",
  "source_type": "email",
  "source_format": "application/pdf",
  "org_id": "los_tajibos",
  "business_unit": "Hotel",
  "department": null,
  "connector_metadata": {
    "email_id": "12345",
    "subject": "Informe mensual de ocupación",
    "sender": "gerente@lostajibos.com",
    "received_date": "Mon, 9 Nov 2025 10:30:00 -0400",
    "attachment_name": "doc.pdf",
    "imap_folder": "INBOX"
  },
  "checksum": "a1b2c3d4e5f6789012345678901234567890123456789012345678901234",
  "collected_at": "2025-11-09T14:30:00Z",
  "consent_validated": true
}
```

## Activity Logging

All connector operations logged to `reports/connector_activity/{YYYY-MM-DD}.jsonl`:

```json
{"timestamp": "2025-11-09T14:30:00Z", "connector_type": "email", "org_id": "los_tajibos", "action": "attachment_saved", "status": "success", "details": {"filename": "doc.pdf", "mime_type": "application/pdf"}}
{"timestamp": "2025-11-09T14:31:00Z", "connector_type": "whatsapp", "org_id": "comversa", "action": "whatsapp_export_processed", "status": "success", "details": {"file": "chat.txt", "messages": 1234}}
```

**Log Analysis**:
```bash
# Count successful operations today
grep "\"status\": \"success\"" reports/connector_activity/2025-11-09.jsonl | wc -l

# Find errors
grep "\"status\": \"error\"" reports/connector_activity/*.jsonl
```

## Programmatic Usage

### Single Connector

```python
import asyncio
from intelligence_capture.connectors import EmailConnector

async def fetch_emails():
    connector = EmailConnector(
        org_id="los_tajibos",
        imap_host="imap.gmail.com",
        imap_user="hotel@lostajibos.com",
        oauth_token=os.getenv("GMAIL_TOKEN"),
        business_unit="Hotel"
    )

    result = await connector.run()
    print(f"Fetched {result['documents_fetched']} documents")

asyncio.run(fetch_emails())
```

### Connector Factory

```python
from intelligence_capture.connectors import ConnectorRegistry

# Create from config dict
connector = ConnectorRegistry.create_connector(
    connector_type="whatsapp",
    org_id="comversa",
    config={
        "export_directory": "data/whatsapp_exports/comversa",
        "business_unit": "Construcción"
    }
)

# Validate config before creating
is_valid, error = ConnectorRegistry.validate_config(
    connector_type="email",
    config={"imap_host": "imap.gmail.com"}  # Missing required fields
)
if not is_valid:
    print(f"Config error: {error}")  # Spanish error message
```

## Error Handling

All connectors return **Spanish error messages** for compliance:

```python
try:
    connector = EmailConnector(org_id="test", ...)
    await connector.run()
except ValueError as e:
    # Spanish error:
    # "Archivo 'document.pdf' excede el límite de 50 MB: 75.3 MB"
    # "Organización 'test' no encontrada en el registro de contexto"
    print(e)
```

**Common Errors**:
- File size exceeded: `"Archivo excede el límite de 50 MB"`
- Batch size exceeded: `"Lote excede el límite de 100 documentos"`
- Missing consent: `"Falta metadatos de consentimiento"`
- Auth failure: `"Error de conexión IMAP: credenciales inválidas"`

## Integration with Ingestion Queue

Connectors work with IngestionQueue for job management:

```python
import asyncio
from pathlib import Path
from intelligence_capture.connectors import EmailConnector
from intelligence_capture.queues import IngestionQueue

async def fetch_and_enqueue():
    # Run connector
    connector = EmailConnector(...)
    result = await connector.run()

    # Enqueue documents for processing
    queue = IngestionQueue(db_url=os.getenv("DATABASE_URL"))

    for metadata in result['metadata_list']:
        job_id = await queue.enqueue(
            org_id=metadata.org_id,
            file_path=Path(metadata.source_path),
            connector_type=metadata.source_type,
            source_format=metadata.source_format,
            metadata=metadata.to_dict()
        )
        print(f"Enqueued job {job_id}")

asyncio.run(fetch_and_enqueue())
```

## Testing

### Unit Tests

```bash
# Test individual connectors
pytest tests/test_connectors.py -v

# Test with coverage
pytest tests/test_connectors.py --cov=intelligence_capture.connectors
```

### Integration Tests

```bash
# Test with sanitized fixtures
pytest tests/integration/test_connector_pipeline.py
```

**Important**: Use sanitized fixtures, never real client data in tests.

## Monitoring

### Queue Statistics

```python
from intelligence_capture.queues import IngestionQueue

queue = IngestionQueue(db_url=os.getenv("DATABASE_URL"))
stats = await queue.get_queue_stats()

print(f"Pending: {stats['pending']}")
print(f"In progress: {stats['in_progress']}")
print(f"Completed: {stats['completed']}")
print(f"Failed: {stats['failed']}")

if stats['backlog_alert']:
    print(f"⚠️  Backlog alert: {stats['backlog_hours']:.1f} hours old")
```

### Activity Summary

```bash
# Daily summary
python scripts/connector_activity_summary.py --date 2025-11-09

# Weekly report
python scripts/connector_activity_summary.py --week 2025-11-03
```

## Troubleshooting

### Gmail OAuth Issues

**Error**: `"Error de conexión IMAP: credenciales inválidas"`

**Solution**:
1. Verify OAuth token not expired
2. Check IMAP scope: `https://mail.google.com/`
3. Enable "Less secure app access" if using legacy auth
4. Use OAuth 2.0 with refresh token for production

### SharePoint Permission Errors

**Error**: `"Error de conexión SharePoint: Access denied"`

**Solution**:
1. Verify Azure AD app has `Sites.Read.All` permission
2. Grant admin consent in Azure portal
3. Check client ID/secret are correct
4. Verify site URL format: `https://{tenant}.sharepoint.com/sites/{site}`

### File Size Warnings

**Warning**: `"Archivo excede el límite de 50 MB"`

**Solution**:
1. File skipped automatically, check activity log
2. Contact user to split large files
3. For permanent increase, modify `BaseConnector.MAX_FILE_SIZE`
4. Requires approval (see CLAUDE.md guardrails)

## Security

### Secrets Management

✅ **DO**:
- Store credentials in environment variables
- Use `env:VARIABLE_NAME` in YAML configs
- Rotate OAuth tokens regularly
- Use Azure Key Vault for SharePoint secrets

❌ **DON'T**:
- Hardcode credentials in config files
- Commit `.env` files to git
- Share OAuth tokens between environments
- Use same credentials across orgs

### Consent Validation

All connectors validate consent before operations:

```python
# Automatic validation in connector.run()
result = await connector.run()  # Raises ValueError if consent invalid

# Manual validation
is_valid = await connector.validate_consent(operation="ingestion")
```

**Bolivian Privacy Compliance**:
- Law 164 (Telecommunications and ICTs)
- Constitution Article 21 (Habeas Data)
- Consent tracked in ContextRegistry
- 12-month audit trail retention

## Next Steps

After connector setup:

1. **Task 3**: Multi-format DocumentProcessor with adapters
2. **Task 4**: OCR engine (Mistral Pixtral + Tesseract)
3. **Task 5**: Spanish-aware chunking with spaCy
4. **Task 20**: Ingestion workers for end-to-end pipeline

## Support

**Documentation**: See `docs/ARCHITECTURE.md` for system overview
**Issues**: Check `reports/connector_activity/` logs for errors
**Testing**: Run `pytest tests/test_connectors.py -v`
**Configuration**: Example YAML in `config/connectors.yaml.example`

---

**Version**: 1.0.0
**Last Updated**: 2025-11-09
**Status**: ✅ Production Ready (Tasks 1-2 Complete)
