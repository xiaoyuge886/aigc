#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
clear_cache.py - CLI tool for cache management.

Provides commands to clear and inspect caches used by the docs-management plugin.

Usage:
    python clear_cache.py              # Clear all caches
    python clear_cache.py --info       # Show cache info without clearing
    python clear_cache.py --inverted   # Clear only inverted index cache
    python clear_cache.py --llms       # Clear only LLMS/scraper cache
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json

from utils.script_utils import configure_utf8_output
from utils.cache_manager import CacheManager
from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()


def cmd_info(cm: CacheManager) -> int:
    """Show cache information without clearing."""
    info = cm.get_cache_info()

    print("📊 Cache Status\n")

    # Inverted index cache
    inv = info['inverted_index']
    inv_status = "✅ Valid" if inv['valid'] else "❌ Invalid/Missing"
    inv_size = f"{inv['size_bytes'] / 1024:.1f} KB" if inv['size_bytes'] > 0 else "N/A"
    print(f"Inverted Index Cache:")
    print(f"  Status: {inv_status}")
    print(f"  Path: {inv['path']}")
    print(f"  Size: {inv_size}")
    print()

    # Cache version info
    ver = info.get('cache_version', {})
    if ver.get('exists') and ver.get('data'):
        ver_data = ver['data']
        print(f"Cache Version Info:")
        print(f"  Format: {ver_data.get('cache_format_version', 'unknown')}")
        print(f"  Created: {ver_data.get('created_at', 'unknown')}")
        print(f"  Index Hash: {ver_data.get('index_yaml_hash', 'unknown')[:20]}...")
        print()

    # LLMS cache
    llms = info['llms_cache']
    llms_status = "✅ Exists" if llms['exists'] else "❌ Missing"
    llms_size = f"{llms['size_bytes'] / 1024:.1f} KB" if llms['size_bytes'] > 0 else "N/A"
    print(f"LLMS/Scraper Cache:")
    print(f"  Status: {llms_status}")
    print(f"  Path: {llms['path']}")
    print(f"  Size: {llms_size}")
    print()

    # Index file
    idx = info['index_yaml']
    idx_status = "✅ Exists" if idx['exists'] else "❌ Missing"
    print(f"Index File (source of truth):")
    print(f"  Status: {idx_status}")
    print(f"  Path: {idx['path']}")
    if idx.get('current_hash'):
        print(f"  Current Hash: {idx['current_hash'][:20]}...")

    return 0


def cmd_clear_all(cm: CacheManager) -> int:
    """Clear all caches."""
    result = cm.clear_all()

    cleared_any = False
    if result['inverted_index']:
        print("✅ Cleared inverted index cache")
        cleared_any = True
    if result['llms_cache']:
        print("✅ Cleared LLMS/scraper cache")
        cleared_any = True

    if not cleared_any:
        print("ℹ️  No caches to clear (already empty)")
    else:
        print("\n💡 Next search will rebuild the inverted index from index.yaml")

    return 0


def cmd_clear_inverted(cm: CacheManager) -> int:
    """Clear only inverted index cache."""
    if cm.clear_inverted_index():
        print("✅ Cleared inverted index cache")
        print("\n💡 Next search will rebuild the index from index.yaml")
    else:
        print("ℹ️  Inverted index cache was already empty")
    return 0


def cmd_clear_llms(cm: CacheManager) -> int:
    """Clear only LLMS/scraper cache."""
    if cm.clear_llms_cache():
        print("✅ Cleared LLMS/scraper cache")
        print("\n💡 Next scrape will fetch all sources fresh")
    else:
        print("ℹ️  LLMS cache was already empty")
    return 0


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Cache management for docs-management plugin',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Show cache status
  python clear_cache.py --info

  # Clear all caches (inverted index + LLMS)
  python clear_cache.py

  # Clear only inverted index cache (search cache)
  python clear_cache.py --inverted

  # Clear only LLMS/scraper cache
  python clear_cache.py --llms

  # Use with custom base directory
  python clear_cache.py --base-dir custom/path --info
        """
    )

    add_base_dir_argument(parser)

    # Cache-specific options
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--info', action='store_true',
                       help='Show cache status without clearing')
    group.add_argument('--inverted', action='store_true',
                       help='Clear only inverted index cache')
    group.add_argument('--llms', action='store_true',
                       help='Clear only LLMS/scraper cache')

    # JSON output for scripting
    parser.add_argument('--json', action='store_true',
                        help='Output as JSON (for scripting)')

    args = parser.parse_args()

    # Resolve base directory
    base_dir = resolve_base_dir_from_args(args)

    # Initialize CacheManager
    cm = CacheManager(base_dir)

    # Handle JSON output for --info
    if args.json and args.info:
        info = cm.get_cache_info()
        print(json.dumps(info, indent=2, default=str))
        return 0

    # Execute requested command
    if args.info:
        return cmd_info(cm)
    elif args.inverted:
        return cmd_clear_inverted(cm)
    elif args.llms:
        return cmd_clear_llms(cm)
    else:
        # Default: clear all
        return cmd_clear_all(cm)


if __name__ == '__main__':
    sys.exit(main())
