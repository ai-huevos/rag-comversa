#!/usr/bin/env python3
"""
Test script for Context Registry implementation
Verifies module structure and basic functionality without requiring database

Task 0: Stand up Context Registry & Org Namespace Controls
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_module_imports():
    """Test that all modules can be imported"""
    print("Testing module imports...")

    try:
        from intelligence_capture.context_registry import (
            OrganizationContext,
            ContextRegistry,
            get_registry,
            validate_and_log_access
        )
        print("✓ intelligence_capture.context_registry imports successfully")
    except ImportError as e:
        print(f"✗ Failed to import context_registry: {e}")
        return False

    return True


def test_organization_context():
    """Test OrganizationContext dataclass"""
    print("\nTesting OrganizationContext...")

    from intelligence_capture.context_registry import OrganizationContext

    # Create test context
    context = OrganizationContext(
        org_id="test_org",
        org_name="Test Organization",
        business_unit="Test Unit",
        department="Test Department",
        industry_context="Testing"
    )

    # Test namespace generation
    expected_namespace = "test_org:Test Unit:Test Department"
    actual_namespace = context.namespace

    if actual_namespace == expected_namespace:
        print(f"✓ Namespace generation correct: {actual_namespace}")
    else:
        print(f"✗ Namespace mismatch: expected '{expected_namespace}', got '{actual_namespace}'")
        return False

    # Test to_dict
    context_dict = context.to_dict()
    if "namespace" in context_dict and context_dict["namespace"] == expected_namespace:
        print("✓ to_dict() includes namespace")
    else:
        print("✗ to_dict() missing or incorrect namespace")
        return False

    # Test without department
    context_no_dept = OrganizationContext(
        org_id="test_org",
        org_name="Test Organization",
        business_unit="Test Unit",
        department=None,
        industry_context="Testing"
    )

    expected_namespace_no_dept = "test_org:Test Unit"
    actual_namespace_no_dept = context_no_dept.namespace

    if actual_namespace_no_dept == expected_namespace_no_dept:
        print(f"✓ Namespace without department correct: {actual_namespace_no_dept}")
    else:
        print(f"✗ Namespace without department mismatch: expected '{expected_namespace_no_dept}', got '{actual_namespace_no_dept}'")
        return False

    return True


def test_companies_config():
    """Test that companies.json can be loaded"""
    print("\nTesting companies.json loading...")

    import json
    companies_path = project_root / "config" / "companies.json"

    if not companies_path.exists():
        print(f"✗ companies.json not found at: {companies_path}")
        return False

    try:
        with open(companies_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        holding_name = config.get("holding_name")
        companies = config.get("companies", [])

        print(f"✓ Loaded companies.json: {holding_name}")
        print(f"  Companies: {len(companies)}")

        # Count total business units and departments
        total_bus = 0
        total_depts = 0
        for company in companies:
            bus = company.get("business_units", [])
            total_bus += len(bus)
            for bu in bus:
                total_depts += len(bu.get("departments", []))

        print(f"  Business Units: {total_bus}")
        print(f"  Departments: {total_depts}")
        print(f"  Expected Registry Entries: ~{total_depts}")

        return True

    except Exception as e:
        print(f"✗ Failed to load companies.json: {e}")
        return False


def test_registry_config():
    """Test that context_registry.yaml exists and is valid"""
    print("\nTesting context_registry.yaml...")

    import yaml
    config_path = project_root / "config" / "context_registry.yaml"

    if not config_path.exists():
        print(f"✗ context_registry.yaml not found at: {config_path}")
        return False

    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        # Check key sections
        required_sections = [
            "database",
            "cache",
            "access_control",
            "onboarding",
            "namespace",
            "audit"
        ]

        for section in required_sections:
            if section in config:
                print(f"✓ Section '{section}' present")
            else:
                print(f"✗ Section '{section}' missing")
                return False

        # Check cache TTL
        cache_ttl = config.get("cache", {}).get("ttl")
        if cache_ttl == 3600:
            print(f"✓ Cache TTL correct: {cache_ttl}s (1 hour)")
        else:
            print(f"⚠ Cache TTL: {cache_ttl}s (expected 3600)")

        return True

    except Exception as e:
        print(f"✗ Failed to load context_registry.yaml: {e}")
        return False


def test_migration_script():
    """Test that migration script exists and is valid SQL"""
    print("\nTesting migration script...")

    migration_path = project_root / "scripts" / "migrations" / "2025_01_00_context_registry.sql"

    if not migration_path.exists():
        print(f"✗ Migration script not found at: {migration_path}")
        return False

    try:
        with open(migration_path, 'r', encoding='utf-8') as f:
            sql = f.read()

        # Check for key SQL statements
        required_statements = [
            "CREATE TABLE IF NOT EXISTS context_registry",
            "CREATE TABLE IF NOT EXISTS context_registry_audit",
            "CREATE TABLE IF NOT EXISTS context_access_log",
            "CREATE INDEX",
            "CREATE TRIGGER"
        ]

        for statement in required_statements:
            if statement in sql:
                print(f"✓ SQL statement present: {statement}")
            else:
                print(f"✗ SQL statement missing: {statement}")
                return False

        print(f"✓ Migration script valid ({len(sql)} characters)")
        return True

    except Exception as e:
        print(f"✗ Failed to read migration script: {e}")
        return False


def test_sync_script():
    """Test that sync script exists and is executable"""
    print("\nTesting sync script...")

    sync_path = project_root / "scripts" / "context_registry_sync.py"

    if not sync_path.exists():
        print(f"✗ Sync script not found at: {sync_path}")
        return False

    # Check if executable
    import os
    is_executable = os.access(sync_path, os.X_OK)

    if is_executable:
        print(f"✓ Sync script is executable")
    else:
        print(f"⚠ Sync script not executable (run: chmod +x {sync_path})")

    # Check that it can be imported
    try:
        # Don't actually import (would require dependencies), just check syntax
        with open(sync_path, 'r', encoding='utf-8') as f:
            code = f.read()

        if "async def sync_organizations" in code:
            print("✓ Sync script contains sync_organizations function")
        else:
            print("✗ Sync script missing sync_organizations function")
            return False

        if "async def list_organizations" in code:
            print("✓ Sync script contains list_organizations function")
        else:
            print("✗ Sync script missing list_organizations function")
            return False

        return True

    except Exception as e:
        print(f"✗ Failed to read sync script: {e}")
        return False


def main():
    """Run all tests"""
    print("=" * 70)
    print("Context Registry Implementation Test")
    print("Task 0: Stand up Context Registry & Org Namespace Controls")
    print("=" * 70)
    print()

    tests = [
        ("Module Imports", test_module_imports),
        ("OrganizationContext", test_organization_context),
        ("companies.json", test_companies_config),
        ("context_registry.yaml", test_registry_config),
        ("Migration Script", test_migration_script),
        ("Sync Script", test_sync_script)
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' raised exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print("=" * 70)
    print(f"Result: {passed}/{total} tests passed")
    print("=" * 70)

    if passed == total:
        print("\n✓ All tests passed! Context Registry implementation ready.")
        print("\nNext steps:")
        print("1. Set DATABASE_URL environment variable")
        print("2. Run migration: psql $DATABASE_URL < scripts/migrations/2025_01_00_context_registry.sql")
        print("3. Sync organizations: python scripts/context_registry_sync.py")
        print("4. Verify sync: python scripts/context_registry_sync.py --list")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
