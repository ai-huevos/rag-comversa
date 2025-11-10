#!/usr/bin/env python3
"""
Documentation Cleanup Script

Purpose: Archive temporary reports, identify stale docs, and maintain clean master docs.
Usage:
    python scripts/cleanup_docs.py --list              # List archivable docs
    python scripts/cleanup_docs.py --archive           # Archive old reports
    python scripts/cleanup_docs.py --validate          # Validate master docs
"""

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

# Master documentation files that should NEVER be archived
MASTER_DOCS = {
    'docs/ARCHITECTURE.md',
    'docs/RUNBOOK.md',
    'docs/DECISIONS.md',
    'docs/EXPERIMENTS.md',
    'docs/README.md',
    'CLAUDE.md',
    '.ai/CODING_STANDARDS.md',
    '.codex/agent_roles.yaml',
    '.codex/manifest.yaml'
}

# Patterns for temporary/archivable documents
ARCHIVABLE_PATTERNS = [
    'reports/qa_*.md',
    'reports/phase*.md',
    'reports/*_report.md',
    'reports/*_summary.md',
    'reports/*_package.md',
    'reports/compliance/*.md',
    'reports/*.json',
    'docs/*_COMPLETE.md',
    'docs/*_AUDIT.md',
    'docs/*_REVIEW.md',
    'docs/*_SUMMARY.md',
    'docs/TASK_*.md'
]

# Archive destinations by month
ARCHIVE_BASE = Path('docs/archive')


class DocCleanup:
    """Documentation cleanup and archival manager."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.archive_month = datetime.now().strftime('%Y-%m')
        self.archive_dir = repo_root / ARCHIVE_BASE / self.archive_month

    def find_archivable_docs(self) -> List[Tuple[Path, str]]:
        """Find documents that can be archived."""
        archivable = []
        seen = set()

        for pattern in ARCHIVABLE_PATTERNS:
            for doc in self.repo_root.glob(pattern):
                if doc.is_file() and doc not in seen:
                    # Determine category
                    category = self._categorize_doc(doc)
                    archivable.append((doc, category))
                    seen.add(doc)

        return archivable

    def _categorize_doc(self, doc: Path) -> str:
        """Categorize document for archival."""
        name = doc.name.lower()

        if 'qa' in name or 'review' in name:
            return 'qa-reviews'
        elif 'phase' in name or 'completion' in name:
            return 'phase-reports'
        elif 'task' in name:
            return 'task-reports'
        elif doc.parent.name == 'compliance':
            return 'compliance'
        elif doc.suffix == '.json':
            return 'metrics'
        else:
            return 'misc'

    def list_archivable(self) -> None:
        """List all documents that can be archived."""
        docs = self.find_archivable_docs()

        if not docs:
            print("✅ No archivable documents found")
            return

        print(f"📋 Found {len(docs)} archivable documents:\n")

        # Group by category
        by_category: Dict[str, List[Path]] = {}
        for doc, category in docs:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(doc)

        for category, doc_list in sorted(by_category.items()):
            print(f"  📁 {category}:")
            for doc in sorted(doc_list):
                size_kb = doc.stat().st_size / 1024
                print(f"    - {doc.relative_to(self.repo_root)} ({size_kb:.1f} KB)")
            print()

    def archive_docs(self, dry_run: bool = False) -> None:
        """Archive documents to monthly archive directory."""
        docs = self.find_archivable_docs()

        if not docs:
            print("✅ No documents to archive")
            return

        print(f"📦 Archiving {len(docs)} documents to {self.archive_dir}/")

        if dry_run:
            print("🔍 DRY RUN - No files will be moved\n")

        archived_count = 0

        for doc, category in docs:
            # Skip if file no longer exists (may have been moved in previous run)
            if not doc.exists():
                continue

            # Create category subdirectory
            dest_dir = self.archive_dir / category

            if not dry_run:
                dest_dir.mkdir(parents=True, exist_ok=True)

            dest_path = dest_dir / doc.name

            # Skip if destination already exists
            if dest_path.exists():
                print(f"  ⏭  {doc.relative_to(self.repo_root)} (already archived)")
                continue

            print(f"  {'[DRY RUN]' if dry_run else '✓'} {doc.relative_to(self.repo_root)}")
            print(f"           → {self.archive_dir.relative_to(self.repo_root) / category / doc.name}")

            if not dry_run:
                shutil.move(str(doc), str(dest_path))
                archived_count += 1

        print(f"\n{'[DRY RUN] Would archive' if dry_run else '✅ Archived'} {len(docs)} documents")

        if not dry_run:
            # Create archive index
            self._create_archive_index(docs)

    def _create_archive_index(self, archived_docs: List[Tuple[Path, str]]) -> None:
        """Create index of archived documents."""
        index_path = self.archive_dir / 'INDEX.md'

        content = f"""# Archive Index - {self.archive_month}

**Archived**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Documents**: {len(archived_docs)}

## Contents

"""

        # Group by category
        by_category: Dict[str, List[Path]] = {}
        for doc, category in archived_docs:
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(doc)

        for category, doc_list in sorted(by_category.items()):
            content += f"### {category}\n\n"
            for doc in sorted(doc_list):
                content += f"- [{doc.name}]({category}/{doc.name})\n"
            content += "\n"

        content += """## Accessing Archived Documents

These documents are historical records and should not be modified.
For current documentation, see:

- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture
- [RUNBOOK.md](../../RUNBOOK.md) - Operational procedures
- [DECISIONS.md](../../DECISIONS.md) - Architecture decisions
- [EXPERIMENTS.md](../../EXPERIMENTS.md) - Technical experiments
- [README.md](../../README.md) - Documentation index
"""

        index_path.write_text(content, encoding='utf-8')
        print(f"📝 Created archive index: {index_path.relative_to(self.repo_root)}")

    def validate_master_docs(self) -> None:
        """Validate that all master docs exist and are up to date."""
        print("🔍 Validating master documentation...\n")

        issues = []

        for doc_path in MASTER_DOCS:
            full_path = self.repo_root / doc_path

            if not full_path.exists():
                issues.append(f"❌ Missing: {doc_path}")
                continue

            # Check last modified
            mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
            age_days = (datetime.now() - mtime).days

            if age_days > 30:
                issues.append(f"⚠️  Stale ({age_days} days old): {doc_path}")
            else:
                print(f"✅ {doc_path} (updated {age_days} days ago)")

        if issues:
            print("\n⚠️  Issues found:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ All master documents validated")

    def check_duplicate_content(self) -> None:
        """Check for potential duplicate content across docs."""
        print("🔍 Checking for duplicate content patterns...\n")

        # Common patterns that might indicate duplication
        patterns = [
            "## Entity Types",
            "## 17 Entity Types",
            "## Quick Start",
            "## Installation",
            "## Testing"
        ]

        matches: Dict[str, List[str]] = {pattern: [] for pattern in patterns}

        for doc_path in MASTER_DOCS:
            full_path = self.repo_root / doc_path
            if not full_path.exists():
                continue

            try:
                content = full_path.read_text(encoding='utf-8')
                for pattern in patterns:
                    if pattern in content:
                        matches[pattern].append(doc_path)
            except Exception:
                continue

        duplicates_found = False
        for pattern, docs in matches.items():
            if len(docs) > 1:
                duplicates_found = True
                print(f"⚠️  Pattern '{pattern}' found in {len(docs)} docs:")
                for doc in docs:
                    print(f"    - {doc}")
                print()

        if not duplicates_found:
            print("✅ No obvious duplicate content found")


def main():
    parser = argparse.ArgumentParser(
        description='Clean up and archive documentation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List archivable documents
  python scripts/cleanup_docs.py --list

  # Preview archive operation
  python scripts/cleanup_docs.py --archive --dry-run

  # Actually archive documents
  python scripts/cleanup_docs.py --archive

  # Validate master documentation
  python scripts/cleanup_docs.py --validate

  # Check for duplicate content
  python scripts/cleanup_docs.py --duplicates
"""
    )

    parser.add_argument('--list', action='store_true',
                        help='List archivable documents')
    parser.add_argument('--archive', action='store_true',
                        help='Archive old reports and temporary docs')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview archive without moving files')
    parser.add_argument('--validate', action='store_true',
                        help='Validate master documentation')
    parser.add_argument('--duplicates', action='store_true',
                        help='Check for duplicate content')

    args = parser.parse_args()

    # Find repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    cleanup = DocCleanup(repo_root)

    if args.list:
        cleanup.list_archivable()
    elif args.archive:
        cleanup.archive_docs(dry_run=args.dry_run)
    elif args.validate:
        cleanup.validate_master_docs()
    elif args.duplicates:
        cleanup.check_duplicate_content()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
