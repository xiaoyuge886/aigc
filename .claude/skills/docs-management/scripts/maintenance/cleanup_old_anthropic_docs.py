#!/usr/bin/env python3
"""
Cleanup old Anthropic documentation files based on published_at dates.

This script removes documentation files older than the specified age threshold
from both the filesystem and the index.

**Purpose:** General cleanup for any Anthropic documentation that has a published_at
date and exceeds the age threshold. Works across all categories (engineering, news,
research, etc.).

**Features:**
- Reads max_age_days from sources.json configuration (if available)
- Dry-run mode by default (use --execute to actually delete)
- Groups results by category for visibility
- Supports CLI override via --max-age argument
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta
from typing import Optional
import argparse
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))
from management.index_manager import IndexManager
from utils.script_utils import configure_utf8_output


def get_anthropic_max_age_from_config(base_dir: Path) -> Optional[int]:
    """
    Read max_age_days from sources.json for Anthropic sources.

    Returns the max_age_days value if found and consistent across all Anthropic sources,
    or None if not configured or inconsistent.

    Note: base_dir is the canonical directory (where docs are stored).
    sources.json is in the skill's references folder (base_dir's parent).
    """
    # base_dir is typically 'canonical/', sources.json is in 'references/' (sibling)
    sources_path = base_dir.parent / "references" / "sources.json"
    if not sources_path.exists():
        # Fallback: try base_dir directly (in case structure differs)
        sources_path = base_dir / "references" / "sources.json"
        if not sources_path.exists():
            return None

    try:
        with open(sources_path, 'r', encoding='utf-8') as f:
            sources = json.load(f)

        # Find all Anthropic sources with max_age_days
        anthropic_ages = []
        for source in sources:
            name = source.get('name', '')
            if 'anthropic.com' in name and 'max_age_days' in source:
                anthropic_ages.append(source['max_age_days'])

        if not anthropic_ages:
            return None

        # Check consistency - all Anthropic sources should have same max_age
        if len(set(anthropic_ages)) == 1:
            return anthropic_ages[0]
        else:
            # Inconsistent values - use the minimum (most conservative)
            print(f"⚠️  Warning: Inconsistent max_age_days across Anthropic sources: {set(anthropic_ages)}")
            print(f"   Using minimum value: {min(anthropic_ages)}")
            return min(anthropic_ages)

    except (json.JSONDecodeError, KeyError) as e:
        print(f"⚠️  Warning: Could not read sources.json: {e}")
        return None

configure_utf8_output()

def cleanup_old_docs(base_dir: Path, max_age_days: int, dry_run: bool = True, delete_files: bool = True):
    """
    Remove documentation files older than max_age_days based on published_at.

    Args:
        base_dir: Base directory containing references
        max_age_days: Maximum age in days (files older than this will be removed)
        dry_run: If True, only report what would be deleted without actually deleting
        delete_files: If True, delete files from filesystem (in addition to removing from index)
    """
    manager = IndexManager(base_dir)
    index = manager.load_all()

    cutoff_date = datetime.now() - timedelta(days=max_age_days)
    cutoff_str = cutoff_date.strftime('%Y-%m-%d')

    print(f"🗑️  Cleanup old Anthropic documentation")
    print(f"Threshold: {cutoff_str} ({max_age_days} days ago)")
    print(f"Mode: {'DRY RUN (no changes)' if dry_run else 'LIVE (will delete)'}")
    print()

    old_docs = []

    # Find all documents with published_at older than cutoff
    for doc_id, entry in index.items():
        if 'published_at' not in entry:
            continue

        # Only process Anthropic docs
        if not entry.get('domain', '').startswith('anthropic'):
            continue

        published_at = entry['published_at']
        pub_date = datetime.strptime(published_at, '%Y-%m-%d')

        if pub_date < cutoff_date:
            days_old = (datetime.now() - pub_date).days
            old_docs.append({
                'doc_id': doc_id,
                'path': entry.get('path', ''),
                'published_at': published_at,
                'days_old': days_old,
                'category': entry.get('category', 'unknown')
            })

    if not old_docs:
        print("✅ No old documents found. All Anthropic docs are within the age threshold.")
        return 0

    # Sort by age (oldest first)
    old_docs.sort(key=lambda x: x['days_old'], reverse=True)

    print(f"Found {len(old_docs)} documents older than {max_age_days} days:")
    print()

    # Group by category
    by_category = {}
    for doc in old_docs:
        cat = doc['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(doc)

    for category, docs in sorted(by_category.items()):
        print(f"📁 {category.upper()} ({len(docs)} files):")
        for doc in docs:
            print(f"   {doc['published_at']} ({doc['days_old']:4d} days old): {doc['path']}")
        print()

    if dry_run:
        print("🔍 DRY RUN MODE - No changes made")
        print(f"Run with --execute to actually delete {len(old_docs)} files")
        return 0

    # Actually delete files
    print(f"🗑️  Deleting {len(old_docs)} files...")
    deleted_count = 0
    failed_count = 0

    for doc in old_docs:
        doc_id = doc['doc_id']
        file_path = base_dir / doc['path']

        try:
            # Delete file if it exists
            if file_path.exists():
                file_path.unlink()
                print(f"✅ Deleted: {doc['path']}")
            else:
                print(f"⚠️  File not found (already deleted?): {doc['path']}")

            # Remove from index
            manager.remove_entry(doc_id)
            deleted_count += 1

        except Exception as e:
            print(f"❌ Failed to delete {doc['path']}: {e}")
            failed_count += 1

    print()
    print(f"✅ Cleanup complete:")
    print(f"   Deleted: {deleted_count} files")
    if failed_count > 0:
        print(f"   Failed:  {failed_count} files")

    return deleted_count

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Cleanup old Anthropic documentation files based on published_at dates'
    )
    parser.add_argument(
        '--max-age',
        type=int,
        default=None,
        help='Maximum age in days (default: read from sources.json, fallback: 365)'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Actually delete files (default is dry-run)'
    )
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)

    args = parser.parse_args()

    # Resolve base directory using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)

    if not base_dir.exists():
        print(f"❌ Error: Base directory not found: {base_dir}")
        return 1

    # Determine max_age: CLI arg > sources.json config > fallback 365
    max_age_days = args.max_age
    if max_age_days is None:
        config_max_age = get_anthropic_max_age_from_config(base_dir)
        if config_max_age is not None:
            max_age_days = config_max_age
            print(f"📋 Using max_age_days from sources.json: {max_age_days}")
        else:
            max_age_days = 365
            print(f"📋 No max_age_days in sources.json, using default: {max_age_days}")
        print()

    cleanup_old_docs(
        base_dir=base_dir,
        max_age_days=max_age_days,
        dry_run=not args.execute
    )

    return 0

if __name__ == '__main__':
    sys.exit(main())
