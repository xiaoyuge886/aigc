#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enrich_categories.py - Enrich index with hierarchical categories from docs_map.md

This script fetches the official Claude Code docs map and enriches the local
index with category metadata. It maps URLs to their categories as defined
in the official documentation hierarchy.

Categories from docs_map.md:
- Getting started
- Build with Claude Code
- Deployment
- Administration
- Configuration
- Reference
- Resources

Usage:
    # Enrich all code.claude.com entries with categories
    python enrich_categories.py

    # Dry run (show what would be updated without making changes)
    python enrich_categories.py --dry-run

    # Verbose output
    python enrich_categories.py --verbose

Dependencies:
    pip install requests pyyaml
"""

from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; scripts_dir = bootstrap.scripts_dir

import argparse
import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

import requests

from utils.script_utils import configure_utf8_output, ensure_yaml_installed
from utils.path_config import get_base_dir
from utils.logging_utils import get_or_setup_logger
from core.docs_map_parser import DocsMapParser, get_category_mapping

configure_utf8_output()
yaml = ensure_yaml_installed()

# Script logger
logger = get_or_setup_logger(__file__, log_category="enrich")


# Default docs map URL
DEFAULT_DOCS_MAP_URL = "https://code.claude.com/docs/en/claude_code_docs_map.md"


def fetch_docs_map(url: str, timeout: int = 30) -> str:
    """
    Fetch docs_map.md content from the given URL.

    Args:
        url: URL to fetch
        timeout: Request timeout in seconds

    Returns:
        Content of the docs map file

    Raises:
        requests.RequestException: If fetch fails
    """
    logger.info(f"Fetching docs map from: {url}")

    response = requests.get(url, timeout=timeout, headers={
        'User-Agent': 'Claude-Code-Docs-Management/1.0'
    })
    response.raise_for_status()

    logger.info(f"Fetched {len(response.text)} characters")
    return response.text


def load_index(base_dir: Path) -> tuple[Dict[str, Any], Path]:
    """
    Load the index from YAML or JSON file.

    Args:
        base_dir: Base directory (canonical/ directory from get_base_dir())

    Returns:
        Tuple of (index dict, index file path)
    """
    # get_base_dir() returns the canonical directory directly
    # Try JSON first (faster)
    json_path = base_dir / "index.json"
    yaml_path = base_dir / "index.yaml"

    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            index = json.load(f)
        logger.info(f"Loaded index from JSON: {len(index)} entries")
        return index, yaml_path  # Still write to YAML for git diffs
    elif yaml_path.exists():
        with open(yaml_path, 'r', encoding='utf-8') as f:
            index = yaml.safe_load(f) or {}
        logger.info(f"Loaded index from YAML: {len(index)} entries")
        return index, yaml_path
    else:
        raise FileNotFoundError(f"No index found at {json_path} or {yaml_path}")


def save_index(index: Dict[str, Any], yaml_path: Path, json_path: Path | None = None):
    """
    Save index to YAML (and optionally JSON).

    Args:
        index: Index dictionary
        yaml_path: Path to YAML file
        json_path: Optional path to JSON file (for fast reads)
    """
    # Save YAML (for human readability and git diffs)
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(index, f, default_flow_style=False, allow_unicode=True, sort_keys=True)
    logger.info(f"Saved index to YAML: {yaml_path}")

    # Save JSON (for fast reads)
    if json_path is None:
        json_path = yaml_path.with_suffix('.json')

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(index, f, indent=2, ensure_ascii=False)
        f.write('\n')
    logger.info(f"Saved index to JSON: {json_path}")


def normalize_url(url: str) -> str:
    """
    Normalize URL for comparison by adding .md suffix if missing.

    Args:
        url: URL to normalize

    Returns:
        Normalized URL with .md suffix
    """
    if url and not url.endswith('.md'):
        return url + '.md'
    return url


def enrich_index_with_categories(
    index: Dict[str, Any],
    category_mapping: Dict[str, str],
    verbose: bool = False
) -> tuple[int, int, Dict[str, str]]:
    """
    Enrich index entries with category metadata.

    Args:
        index: Index dictionary to modify in-place
        category_mapping: URL to category mapping from docs_map.md
        verbose: Print detailed output

    Returns:
        Tuple of (updated_count, unchanged_count, updates_dict)
    """
    updated = 0
    unchanged = 0
    updates: Dict[str, str] = {}  # doc_id -> category

    for doc_id, entry in index.items():
        # Only process code.claude.com entries
        if not doc_id.startswith('code-claude-com'):
            continue

        url = entry.get('url', '')
        if not url:
            continue

        # Normalize URL for comparison (add .md if missing)
        normalized_url = normalize_url(url)

        # Check if URL is in the category mapping
        if normalized_url in category_mapping:
            new_category = category_mapping[normalized_url]
            old_category = entry.get('doc_map_category')

            if old_category != new_category:
                entry['doc_map_category'] = new_category
                updated += 1
                updates[doc_id] = new_category

                if verbose:
                    if old_category:
                        print(f"  Updated: {doc_id}")
                        print(f"    {old_category} -> {new_category}")
                    else:
                        print(f"  Added: {doc_id} -> {new_category}")
            else:
                unchanged += 1
        else:
            # URL not in docs map (might be changelog or other non-doc page)
            if verbose and entry.get('doc_map_category'):
                print(f"  Note: {doc_id} not in docs map (keeping existing category)")

    return updated, unchanged, updates


def get_docs_map_url_from_sources(base_dir: Path) -> str | None:
    """
    Get docs map URL from sources.json if configured.

    Args:
        base_dir: Base directory (skill root)

    Returns:
        URL if found, None otherwise
    """
    sources_path = base_dir.parent.parent.parent / 'references' / 'sources.json'
    if not sources_path.exists():
        return None

    try:
        with open(sources_path, 'r', encoding='utf-8') as f:
            sources = json.load(f)

        for source in sources:
            if source.get('type') == 'docs-map-metadata' and source.get('enabled', True):
                return source.get('url')
    except Exception:
        pass

    return None


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Enrich index with hierarchical categories from docs_map.md',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich categories using default docs map URL
  python enrich_categories.py

  # Dry run (show what would be updated)
  python enrich_categories.py --dry-run

  # Verbose output
  python enrich_categories.py --verbose

  # Custom docs map URL
  python enrich_categories.py --url https://example.com/docs_map.md
        """
    )

    parser.add_argument('--url',
                       help='URL of docs_map.md (default: code.claude.com)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--base-dir', type=Path,
                       help='Base directory containing canonical/')

    args = parser.parse_args()

    # Resolve base directory
    if args.base_dir:
        base_dir = args.base_dir.resolve()
    else:
        base_dir = get_base_dir()

    # Get docs map URL
    if args.url:
        docs_map_url = args.url
    else:
        # Try to get from sources.json, fall back to default
        docs_map_url = get_docs_map_url_from_sources(base_dir) or DEFAULT_DOCS_MAP_URL

    print(f"\n{'='*60}")
    print("CATEGORY ENRICHMENT")
    print(f"{'='*60}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Base dir: {base_dir}")
    print(f"Docs map URL: {docs_map_url}")
    print(f"Dry run: {args.dry_run}")
    print()

    try:
        # Fetch docs map
        print("📥 Fetching docs map...")
        docs_map_content = fetch_docs_map(docs_map_url)

        # Parse to get category mapping
        print("🔍 Parsing docs map...")
        parser_instance = DocsMapParser()
        entries = parser_instance.parse(docs_map_content)
        category_mapping = {url: entry.category for url, entry in entries.items()}
        print(f"   Found {len(category_mapping)} pages in {len(set(category_mapping.values()))} categories")

        # List categories
        categories = set(category_mapping.values())
        if args.verbose:
            print("   Categories:")
            for cat in sorted(categories):
                count = sum(1 for c in category_mapping.values() if c == cat)
                print(f"     - {cat}: {count} pages")

        # Load index
        print("\n📂 Loading index...")
        index, yaml_path = load_index(base_dir)

        # Enrich with categories
        print("\n🏷️  Enriching categories...")
        updated, unchanged, updates = enrich_index_with_categories(
            index, category_mapping, verbose=args.verbose
        )

        print(f"\n📊 Results:")
        print(f"   - Updated: {updated}")
        print(f"   - Unchanged: {unchanged}")

        if updates and args.verbose:
            print(f"\n   Updates:")
            for doc_id, category in sorted(updates.items()):
                print(f"     {doc_id}: {category}")

        # Save if not dry run
        if args.dry_run:
            print(f"\n⏭️  Dry run - no changes made")
        elif updated > 0:
            print(f"\n💾 Saving index...")
            save_index(index, yaml_path)
            print(f"   ✅ Saved {updated} updates")
        else:
            print(f"\n✅ No updates needed")

        print(f"\n{'='*60}\n")
        return 0

    except requests.RequestException as e:
        print(f"\n❌ Failed to fetch docs map: {e}")
        return 1
    except FileNotFoundError as e:
        print(f"\n❌ {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
