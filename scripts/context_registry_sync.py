#!/usr/bin/env python3
"""
Context Registry Sync Script
Populates context_registry table from companies.json configuration

Task 0: Stand up Context Registry & Org Namespace Controls
Usage:
    python scripts/context_registry_sync.py [--config path/to/companies.json] [--dry-run]
"""
import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from intelligence_capture.context_registry import ContextRegistry, OrganizationContext


def load_companies_config(config_path: Path) -> Dict[str, Any]:
    """
    Load companies configuration from JSON file

    Args:
        config_path: Path to companies.json file

    Returns:
        Parsed companies configuration
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Companies config not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_org_id(company_name: str) -> str:
    """
    Generate organization ID from company name

    Args:
        company_name: Full company name

    Returns:
        Organization ID (lowercase, underscores)
    """
    # Convert to lowercase and replace spaces with underscores
    org_id = company_name.lower()
    org_id = org_id.replace(" ", "_")
    org_id = org_id.replace("hotel_", "")  # Remove hotel prefix if present

    return org_id


def generate_consent_metadata(org_id: str, org_name: str) -> Dict[str, Any]:
    """
    Generate default consent metadata for organization

    Args:
        org_id: Organization identifier
        org_name: Full organization name

    Returns:
        Consent metadata dictionary
    """
    return {
        "consent_obtained": True,
        "consent_date": datetime.now().isoformat(),
        "consent_version": "1.0",
        "allowed_operations": ["ingestion", "retrieval", "export", "analysis"],
        "data_retention_days": 365,
        "privacy_framework": "Bolivian Law 164 - Telecommunications and ICTs",
        "constitutional_reference": "Article 21 - Right to Privacy",
        "habeas_data_compliance": True,
        "authorized_by": "Program Director",
        "organization": org_name,
        "notes": f"Initial consent for {org_name} RAG 2.0 system integration"
    }


def generate_contact_owner(org_name: str) -> Dict[str, Any]:
    """
    Generate default contact owner information

    Args:
        org_name: Full organization name

    Returns:
        Contact owner dictionary
    """
    return {
        "role": "Operations Manager",
        "organization": org_name,
        "contact_method": "internal_system",
        "escalation_path": "Program Director → IT Director",
        "notes": "Default contact for system operations"
    }


async def sync_organizations(
    config_path: Path,
    dry_run: bool = False,
    registry: Optional[ContextRegistry] = None
) -> Dict[str, Any]:
    """
    Sync organizations from companies.json to context registry

    Args:
        config_path: Path to companies.json
        dry_run: If True, only show what would be synced
        registry: Optional ContextRegistry instance (creates new if None)

    Returns:
        Sync results dictionary
    """
    # Load configuration
    print(f"📂 Loading companies configuration from: {config_path}")
    config = load_companies_config(config_path)

    holding_name = config.get("holding_name", "Unknown Holding")
    companies = config.get("companies", [])

    print(f"✓ Found {len(companies)} companies in {holding_name}")
    print()

    # Initialize registry
    if registry is None:
        registry = ContextRegistry()

    if not dry_run:
        await registry.connect()

    # Sync results
    results = {
        "holding_name": holding_name,
        "total_companies": len(companies),
        "total_entries": 0,
        "created": 0,
        "skipped": 0,
        "errors": 0,
        "entries": []
    }

    # Process each company
    for company in companies:
        company_name = company["name"]
        org_id = generate_org_id(company_name)
        industry_context = company.get("industry_context", "General Business")
        business_units = company.get("business_units", [])

        print(f"🏢 Processing: {company_name} (org_id: {org_id})")
        print(f"   Industry: {industry_context}")
        print(f"   Business Units: {len(business_units)}")

        # Process each business unit
        for bu in business_units:
            bu_name = bu["name"]
            departments = bu.get("departments", [None])

            # If no departments, create entry with department=None
            if not departments:
                departments = [None]

            for dept in departments:
                entry = {
                    "org_id": org_id,
                    "org_name": company_name,
                    "business_unit": bu_name,
                    "department": dept,
                    "industry_context": industry_context,
                    "priority_tier": "standard",
                    "contact_owner": generate_contact_owner(company_name),
                    "consent_metadata": generate_consent_metadata(org_id, company_name)
                }

                namespace = f"{org_id}:{bu_name}"
                if dept:
                    namespace += f":{dept}"

                results["total_entries"] += 1

                if dry_run:
                    print(f"   [DRY RUN] Would create: {namespace}")
                    results["entries"].append({
                        "namespace": namespace,
                        "action": "would_create",
                        "entry": entry
                    })
                    results["created"] += 1
                else:
                    try:
                        # Try to register organization
                        context = await registry.register_organization(**entry)
                        print(f"   ✓ Created: {namespace}")
                        results["entries"].append({
                            "namespace": namespace,
                            "action": "created",
                            "context": context.to_dict()
                        })
                        results["created"] += 1
                    except Exception as e:
                        error_str = str(e)
                        if "duplicate key" in error_str or "already exists" in error_str:
                            print(f"   ⊘ Skipped (exists): {namespace}")
                            results["entries"].append({
                                "namespace": namespace,
                                "action": "skipped",
                                "reason": "already_exists"
                            })
                            results["skipped"] += 1
                        else:
                            print(f"   ✗ Error: {namespace} - {error_str}")
                            results["entries"].append({
                                "namespace": namespace,
                                "action": "error",
                                "error": error_str
                            })
                            results["errors"] += 1

        print()

    # Close registry connection
    if not dry_run:
        await registry.close()

    return results


def print_sync_summary(results: Dict[str, Any]):
    """
    Print sync summary

    Args:
        results: Sync results dictionary
    """
    print("=" * 70)
    print("SYNC SUMMARY")
    print("=" * 70)
    print(f"Holding: {results['holding_name']}")
    print(f"Companies Processed: {results['total_companies']}")
    print(f"Total Entries: {results['total_entries']}")
    print(f"  ✓ Created: {results['created']}")
    print(f"  ⊘ Skipped: {results['skipped']}")
    print(f"  ✗ Errors: {results['errors']}")
    print("=" * 70)


async def list_organizations(registry: Optional[ContextRegistry] = None):
    """
    List all organizations in context registry

    Args:
        registry: Optional ContextRegistry instance
    """
    if registry is None:
        registry = ContextRegistry()

    await registry.connect()

    print("📋 Listing all organizations in context registry:")
    print()

    orgs = await registry.get_all_organizations()

    if not orgs:
        print("   No organizations found.")
        await registry.close()
        return

    # Group by org_id
    by_org = {}
    for org in orgs:
        if org.org_id not in by_org:
            by_org[org.org_id] = []
        by_org[org.org_id].append(org)

    for org_id, contexts in by_org.items():
        first = contexts[0]
        print(f"🏢 {first.org_name} (org_id: {org_id})")
        print(f"   Industry: {first.industry_context}")
        print(f"   Namespaces: {len(contexts)}")

        for ctx in contexts:
            namespace = ctx.namespace
            print(f"      - {namespace}")

        print()

    print(f"Total Organizations: {len(by_org)}")
    print(f"Total Namespaces: {len(orgs)}")

    await registry.close()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Sync organizations from companies.json to context registry"
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=project_root / "config" / "companies.json",
        help="Path to companies.json configuration file"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be synced without making changes"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all organizations in registry"
    )

    args = parser.parse_args()

    # Check DATABASE_URL
    if not os.getenv("DATABASE_URL"):
        print("✗ ERROR: DATABASE_URL environment variable not set")
        print("  Please set DATABASE_URL to PostgreSQL connection string")
        print("  Example: export DATABASE_URL='postgresql://user:pass@localhost:5432/dbname'")
        sys.exit(1)

    try:
        if args.list:
            await list_organizations()
        else:
            results = await sync_organizations(args.config, dry_run=args.dry_run)
            print_sync_summary(results)

            if args.dry_run:
                print()
                print("💡 Run without --dry-run to apply changes to database")

    except KeyboardInterrupt:
        print("\n⚠️  Sync interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
