#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_stale.py - Clean up stale documentation files

Finds documents marked as "stale" (no longer in sitemap) and removes them
after manual confirmation. Updates index.yaml and logs deletions.

Usage:
    # List all stale documents
    python cleanup_stale.py --list

    # Remove stale documents (with confirmation)
    python cleanup_stale.py --remove

    # Remove stale documents (no confirmation, use with caution)
    python cleanup_stale.py --remove --force

    # Remove specific output directory only
    python cleanup_stale.py --remove --output platform-docs

Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from datetime import datetime, timezone

from utils.script_utils import configure_utf8_output, ensure_yaml_installed
configure_utf8_output()

yaml = ensure_yaml_installed()

# Import index_manager for large file support
try:
    from management.index_manager import IndexManager
except ImportError:
    IndexManager = None

class StaleCleanup:
    """Clean up stale documentation files"""

    def __init__(self, base_output_dir: Path):
        """
        Initialize cleanup manager

        Args:
            base_output_dir: Base directory for canonical storage (default: .claude/skills/docs-management/canonical from config)
        """
        self.base_output_dir = base_output_dir
        from utils.path_config import get_index_path
        self.index_path = get_index_path(base_output_dir)
        
        # Initialize index manager if available
        if IndexManager:
            self.index_manager = IndexManager(base_output_dir)
        else:
            self.index_manager = None

    def find_stale_files(self, output_filter: str = None) -> list[tuple[Path, dict]]:
        """
        Find all files marked as stale

        Args:
            output_filter: Optional filter for output subdirectory (e.g., 'platform-docs')

        Returns:
            List of tuples: (file_path, frontmatter_dict)
        """
        stale_files = []

        # Search for markdown files with status: stale in frontmatter
        for md_file in self.base_output_dir.rglob('*.md'):
            # Apply output filter if specified
            if output_filter:
                rel_path = md_file.relative_to(self.base_output_dir)
                if not str(rel_path).startswith(output_filter):
                    continue

            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check for frontmatter with status: stale
                if content.startswith('---\n'):
                    end_idx = content.find('\n---\n', 4)
                    if end_idx != -1:
                        frontmatter_text = content[4:end_idx]
                        frontmatter = yaml.safe_load(frontmatter_text) or {}

                        if frontmatter.get('status') == 'stale':
                            stale_files.append((md_file, frontmatter))

            except Exception as e:
                print(f"⚠️  Failed to read {md_file}: {e}")

        return stale_files

    def display_stale_files(self, stale_files: list[tuple[Path, dict]]):
        """
        Display stale files in a readable format

        Args:
            stale_files: List of tuples (file_path, frontmatter_dict)
        """
        if not stale_files:
            print("✅ No stale files found.")
            return

        print(f"\n📋 Found {len(stale_files)} stale file(s):\n")
        print("-" * 80)

        for filepath, frontmatter in stale_files:
            rel_path = filepath.relative_to(self.base_output_dir)
            url = frontmatter.get('source_url', 'N/A')
            last_fetched = frontmatter.get('last_fetched', 'N/A')
            marked_stale = frontmatter.get('marked_stale', 'N/A')

            print(f"\n📄 {rel_path}")
            print(f"   URL: {url}")
            print(f"   Last fetched: {last_fetched}")
            print(f"   Marked stale: {marked_stale}")

        print("\n" + "-" * 80)

    def remove_stale_files(self, stale_files: list[tuple[Path, dict]], force: bool = False) -> int:
        """
        Remove stale files after confirmation

        Args:
            stale_files: List of tuples (file_path, frontmatter_dict)
            force: Skip confirmation prompt

        Returns:
            Number of files removed
        """
        if not stale_files:
            print("✅ No stale files to remove.")
            return 0

        # Display files to be removed
        self.display_stale_files(stale_files)

        # Confirmation prompt
        if not force:
            print(f"\n⚠️  You are about to DELETE {len(stale_files)} file(s).")
            print("   This action cannot be undone.")
            response = input("\n   Type 'yes' to confirm deletion: ")

            if response.lower() != 'yes':
                print("\n❌ Deletion cancelled.")
                return 0

        # Remove files
        removed_count = 0
        removed_files = []

        print(f"\n🗑️  Removing stale files...")

        for filepath, frontmatter in stale_files:
            try:
                filepath.unlink()
                rel_path = filepath.relative_to(self.base_output_dir)
                print(f"   ✅ Removed: {rel_path}")
                removed_files.append((str(rel_path), frontmatter))
                removed_count += 1
            except Exception as e:
                print(f"   ❌ Failed to remove {filepath}: {e}")

        # Update index.yaml
        if removed_count > 0:
            self.update_index(removed_files)
            self.write_audit_log(removed_files)

        print(f"\n✅ Removed {removed_count}/{len(stale_files)} file(s)")
        return removed_count

    def update_index(self, removed_files: list[tuple[str, dict]]):
        """
        Update index.yaml to remove entries for deleted files

        Args:
            removed_files: List of tuples (rel_path, frontmatter_dict)
        """
        if not self.index_path.exists():
            print("⚠️  Index file not found, skipping index update")
            return

        # Use index_manager if available (handles large files and locking)
        if self.index_manager:
            try:
                original_count = self.index_manager.get_entry_count()
                
                # Find and remove matching entries
                removed_count = 0
                for rel_path, frontmatter in removed_files:
                    url = frontmatter.get('source_url')
                    
                    # Search for entries matching path or URL
                    matching = self.index_manager.search_entries(path=rel_path)
                    if not matching:
                        matching = self.index_manager.search_entries(url=url)
                    
                    # Remove matching entries
                    for doc_id, _ in matching:
                        if self.index_manager.remove_entry(doc_id):
                            removed_count += 1
                
                print(f"\n📝 Updated index.yaml: removed {removed_count} entry/entries")
            except Exception as e:
                print(f"⚠️  Failed to update index: {e}")
        else:
            # Fallback to original implementation
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    index = yaml.safe_load(f) or {}

                original_count = len(index)

                # Remove entries for deleted files
                for rel_path, frontmatter in removed_files:
                    url = frontmatter.get('source_url')

                    # Find and remove matching index entry
                    doc_ids_to_remove = []
                    for doc_id, metadata in index.items():
                        if metadata.get('path') == rel_path or metadata.get('url') == url:
                            doc_ids_to_remove.append(doc_id)

                    for doc_id in doc_ids_to_remove:
                        del index[doc_id]

                # Write updated index
                with open(self.index_path, 'w', encoding='utf-8') as f:
                    yaml.dump(index, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

                removed_from_index = original_count - len(index)
                print(f"\n📝 Updated index.yaml: removed {removed_from_index} entry/entries")

            except Exception as e:
                print(f"⚠️  Failed to update index: {e}")

    def write_audit_log(self, removed_files: list[tuple[str, dict]]):
        """
        Write audit log for deleted files

        Args:
            removed_files: List of tuples (rel_path, frontmatter_dict)
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        from utils.path_config import get_temp_dir
        temp_dir = get_temp_dir()
        temp_dir.mkdir(exist_ok=True)

        log_file = temp_dir / f"{timestamp}-cleanup-stale.md"

        log_content = f"""# Stale Documentation Cleanup

**Date:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}
**Files removed:** {len(removed_files)}

## Removed Files

"""

        for rel_path, frontmatter in removed_files:
            url = frontmatter.get('source_url', 'N/A')
            last_fetched = frontmatter.get('last_fetched', 'N/A')
            marked_stale = frontmatter.get('marked_stale', 'N/A')

            log_content += f"""### {rel_path}

- **URL:** {url}
- **Last fetched:** {last_fetched}
- **Marked stale:** {marked_stale}
- **Reason:** No longer in sitemap

"""

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)

        print(f"📝 Audit log written: {log_file}")

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Clean up stale documentation files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all stale documents
  python cleanup_stale.py --list

  # Remove stale documents (with confirmation)
  python cleanup_stale.py --remove

  # Remove stale documents (no confirmation)
  python cleanup_stale.py --remove --force

  # Remove stale documents from specific directory
  python cleanup_stale.py --remove --output platform-docs
        """
    )

    parser.add_argument('--list', action='store_true',
                       help='List all stale files without removing')
    parser.add_argument('--remove', action='store_true',
                       help='Remove stale files (requires confirmation unless --force)')
    parser.add_argument('--force', action='store_true',
                       help='Skip confirmation prompt (use with caution)')
    parser.add_argument('--output', help='Filter by output subdirectory (e.g., platform-docs)')
    
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)

    args = parser.parse_args()

    # Require either --list or --remove
    if not args.list and not args.remove:
        parser.error("Either --list or --remove is required")

    # Initialize cleanup manager - resolve base_dir using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)

    cleanup = StaleCleanup(base_dir)

    # Find stale files
    print(f"🔍 Searching for stale files...")
    stale_files = cleanup.find_stale_files(output_filter=args.output)

    # List or remove
    if args.list:
        cleanup.display_stale_files(stale_files)
    elif args.remove:
        cleanup.remove_stale_files(stale_files, force=args.force)

    sys.exit(0)

if __name__ == '__main__':
    main()
