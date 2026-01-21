#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_drift.py - Clean up stale documentation and drift

Removes documentation that no longer exists at source URLs (404s) or has
missing files, and cleans up index entries accordingly. Generates audit logs
for all cleanup operations.

Usage:
    # Dry-run (show what would be cleaned)
    python cleanup_drift.py --dry-run

    # Clean up 404 URLs
    python cleanup_drift.py --clean-404s

    # Clean up missing files
    python cleanup_drift.py --clean-missing-files

    # Mark stale entries for review
    python cleanup_drift.py --mark-stale

    # Full cleanup (all operations)
    python cleanup_drift.py --full-cleanup

    # Custom base directory (default: .claude/skills/docs-management/canonical from config)
    python cleanup_drift.py --base-dir custom/path --dry-run

Dependencies:
    pip install requests pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from datetime import datetime, timezone
from typing import Dict

from utils.script_utils import configure_utf8_output, ensure_yaml_installed
from utils.http_utils import DEFAULT_TIMEOUT
from management.index_manager import IndexManager
from utils.path_config import get_base_dir, get_index_path, get_temp_dir
from utils.config_helpers import get_management_user_agent, get_drift_max_workers
from utils.logging_utils import get_or_setup_logger
configure_utf8_output()

# Script logger for structured logging
logger = get_or_setup_logger(__file__, log_category="diagnostics")

try:
    import requests
except ImportError as e:
    logger.error(f"Missing dependency: {e}")
    logger.error("Install with: pip install requests")
    sys.exit(1)

yaml = ensure_yaml_installed()

class DriftCleaner:
    """Clean up stale documentation and drift"""
    
    def __init__(self, base_dir: Path | None = None, dry_run: bool = False):
        """
        Initialize drift cleaner
        
        Args:
            base_dir: Base directory for canonical storage. If None, uses config default.
            dry_run: If True, only report what would be cleaned (no actual changes)
        """
        self.base_dir = Path(base_dir) if base_dir else get_base_dir()
        self.dry_run = dry_run
        self.index_path = get_index_path(self.base_dir)
        self.index_manager = IndexManager(self.base_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_management_user_agent()
        })
        
        # Track cleanup operations
        self.cleanup_log: list[dict[str, any]] = []
    
    def load_index(self) -> dict[str, Dict]:
        """Load index.yaml"""
        if not self.index_path.exists():
            print(f"⚠️  Index file not found: {self.index_path}")
            return {}
        
        try:
            index = self.index_manager.load_all()
            print(f"📋 Loaded {len(index)} entries from index")
            return index
        except Exception as e:
            print(f"❌ Failed to load index: {e}")
            sys.exit(1)
    
    def check_url_404(self, url: str) -> bool:
        """Check if URL returns 404"""
        try:
            response = self.session.head(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
            return response.status_code == 404
        except Exception:
            # On error, assume not 404 (could be network issue)
            return False
    
    def find_404_urls(self, index: dict[str, Dict], max_workers: int | None = None) -> list[tuple[str, str]]:
        """
        Find indexed documents with 404 source URLs
        
        Args:
            index: Index dictionary
            max_workers: Maximum parallel workers for checking. If None, uses config default.
        
        Returns:
            List of (doc_id, url) tuples for 404 URLs
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        if max_workers is None:
            max_workers = get_drift_max_workers()
        
        # Collect all URLs to check
        urls_to_check = []
        for doc_id, metadata in index.items():
            url = metadata.get('source_url') or metadata.get('url')
            if url:
                urls_to_check.append((doc_id, url))
        
        print(f"  Checking {len(urls_to_check)} URLs for 404 status...")
        
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.check_url_404, url): (doc_id, url) 
                      for doc_id, url in urls_to_check}
            for future in as_completed(futures):
                doc_id, url = futures[future]
                is_404 = future.result()
                if is_404:
                    results.append((doc_id, url))
                    print(f"    ❌ 404: {doc_id} ({url})")
        
        return results
    
    def find_missing_files(self, index: dict[str, Dict]) -> list[tuple[str, Path]]:
        """
        Find indexed documents with missing files
        
        Args:
            index: Index dictionary
        
        Returns:
            List of (doc_id, filepath) tuples for missing files
        """
        missing = []
        
        for doc_id, metadata in index.items():
            filepath = metadata.get('path')
            if not filepath:
                continue
            
            # Resolve relative paths
            full_path = self.base_dir / filepath
            if not full_path.exists():
                missing.append((doc_id, full_path))
                print(f"    ❌ Missing file: {doc_id} ({filepath})")
        
        return missing
    
    def detect_source_removed_docs(self, sitemap_url: str, filter_pattern: str | None = None,
                                   output_subdir: str = "", max_workers: int | None = None) -> list[tuple[str, str]]:
        """
        Detect documents that exist in index but are no longer in source sitemap.
        
        This detects when source content is removed - documents that were previously
        scraped but no longer appear in the source sitemap.
        
        Args:
            sitemap_url: URL to sitemap.xml
            filter_pattern: Optional regex pattern to filter sitemap URLs
            output_subdir: Output subdirectory to check (e.g., "docs-claude-com")
            max_workers: Maximum parallel workers. If None, uses config default.
        
        Returns:
            List of (doc_id, url) tuples for removed documents
        """
        from detect_changes import ChangeDetector
        
        if max_workers is None:
            max_workers = get_drift_max_workers()
        
        print(f"\n🔍 Detecting documents removed from source...")
        print(f"   Sitemap: {sitemap_url}")
        if filter_pattern:
            print(f"   Filter: {filter_pattern}")
        print(f"   Output subdir: {output_subdir}")
        
        # Use ChangeDetector to compare sitemap with index
        detector = ChangeDetector(self.base_dir)
        
        # Fetch and parse sitemap
        sitemap_content = detector.fetch_sitemap(sitemap_url)
        sitemap_urls = detector.parse_sitemap(sitemap_content, filter_pattern)
        
        # Get indexed URLs for this output subdir
        index = detector.load_index()
        indexed_urls = detector.get_indexed_urls(index, output_subdir)
        
        # Find removed URLs (in index but not in sitemap)
        _, removed_urls = detector.detect_changes(sitemap_urls, indexed_urls)
        
        # Convert removed URLs to (doc_id, url) tuples
        removed_docs = []
        for url in removed_urls:
            doc_id = indexed_urls.get(url)
            if doc_id:
                removed_docs.append((doc_id, url))
                print(f"    ❌ Removed from source: {doc_id} ({url})")
        
        return removed_docs
    
    def clean_source_removed_docs(self, sitemap_url: str, filter_pattern: str | None = None,
                                  output_subdir: str = "", max_workers: int | None = None) -> tuple[int, int]:
        """
        Clean up documents that are no longer in source sitemap.
        
        Args:
            sitemap_url: URL to sitemap.xml
            filter_pattern: Optional regex pattern to filter sitemap URLs
            output_subdir: Output subdirectory to check
            max_workers: Maximum parallel workers. If None, uses config default.
        
        Returns:
            Tuple of (files_removed, index_entries_removed)
        """
        removed_docs = self.detect_source_removed_docs(sitemap_url, filter_pattern, output_subdir, max_workers)
        
        if not removed_docs:
            print("  ✅ No removed documents found")
            return 0, 0
        
        print(f"\n🧹 Cleaning up {len(removed_docs)} documents removed from source...")
        
        files_removed = 0
        index_removed = 0
        
        for doc_id, url in removed_docs:
            # Get metadata to find file path
            index = self.load_index()
            metadata = index.get(doc_id, {})
            filepath = metadata.get('path')
            
            # Remove file if it exists
            if filepath:
                full_path = self.base_dir / filepath
                if self.remove_doc_file(doc_id, full_path):
                    files_removed += 1
            
            # Remove index entry
            if self.remove_index_entry(doc_id):
                index_removed += 1
        
        return files_removed, index_removed
    
    def remove_doc_file(self, doc_id: str, filepath: Path) -> bool:
        """
        Remove a documentation file
        
        Args:
            doc_id: Document ID
            filepath: Path to file
        
        Returns:
            True if removed successfully
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would remove file: {filepath}")
            return True
        
        try:
            if filepath.exists():
                filepath.unlink()
                print(f"  ✅ Removed file: {filepath}")
                self.cleanup_log.append({
                    'action': 'remove_file',
                    'doc_id': doc_id,
                    'filepath': str(filepath),
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                return True
        except Exception as e:
            print(f"  ❌ Failed to remove {filepath}: {e}")
            return False
    
    def remove_index_entry(self, doc_id: str) -> bool:
        """
        Remove an index entry
        
        Args:
            doc_id: Document ID
        
        Returns:
            True if removed successfully
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would remove index entry: {doc_id}")
            return True
        
        try:
            self.index_manager.remove_entry(doc_id)
            print(f"  ✅ Removed index entry: {doc_id}")
            self.cleanup_log.append({
                'action': 'remove_index_entry',
                'doc_id': doc_id,
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            return True
        except Exception as e:
            print(f"  ❌ Failed to remove index entry {doc_id}: {e}")
            return False
    
    def mark_as_stale(self, doc_id: str, reason: str) -> bool:
        """
        Mark an index entry as stale
        
        Args:
            doc_id: Document ID
            reason: Reason for marking as stale
        
        Returns:
            True if marked successfully
        """
        if self.dry_run:
            print(f"  [DRY-RUN] Would mark as stale: {doc_id} ({reason})")
            return True
        
        try:
            entry = self.index_manager.get_entry(doc_id)
            if entry:
                entry['status'] = 'stale'
                entry['stale_reason'] = reason
                entry['marked_stale'] = datetime.now(timezone.utc).isoformat()
                self.index_manager.update_entry(doc_id, entry)
                print(f"  ✅ Marked as stale: {doc_id} ({reason})")
                self.cleanup_log.append({
                    'action': 'mark_stale',
                    'doc_id': doc_id,
                    'reason': reason,
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
                return True
        except Exception as e:
            print(f"  ❌ Failed to mark {doc_id} as stale: {e}")
            return False
    
    def _remove_paired_extracts(self, index: dict[str, Dict], source_identifiers: set[str], 
                                by_path: bool = False) -> tuple[int, int]:
        """
        Remove extract documents that reference missing/404 source documents.
        
        Extracts store source_doc or source_url in their frontmatter. When a source
        document is removed (404 or missing file), we need to remove all extracts
        that reference it.
        
        Args:
            index: Index dictionary
            source_identifiers: Set of source URLs or source file paths that are missing/404
            by_path: If True, match by source file path; if False, match by source_url
        
        Returns:
            Tuple of (files_removed, index_entries_removed)
        """
        if not source_identifiers:
            return 0, 0
        
        print(f"\n🔍 Finding paired extracts for {len(source_identifiers)} removed sources...")
        
        files_removed = 0
        index_removed = 0
        
        # Find all extracts that reference the removed sources
        for doc_id, metadata in list(index.items()):
            if not isinstance(metadata, dict):
                continue
            
            # Check if this is an extract (has source_doc or source_url in metadata)
            source_doc = metadata.get('source_doc')
            source_url = metadata.get('source_url')
            
            should_remove = False
            match_reason = None
            
            if by_path and source_doc:
                # Match by source file path
                # source_doc might be relative or absolute path
                for missing_source in source_identifiers:
                    if source_doc == missing_source or source_doc.endswith(missing_source):
                        should_remove = True
                        match_reason = f"source_doc={source_doc}"
                        break
            elif not by_path and source_url:
                # Match by source URL
                if source_url in source_identifiers:
                    should_remove = True
                    match_reason = f"source_url={source_url}"
            
            if should_remove:
                filepath = metadata.get('path')
                
                # Remove file if it exists
                if filepath:
                    full_path = self.base_dir / filepath
                    if self.remove_doc_file(doc_id, full_path):
                        files_removed += 1
                        print(f"  ✅ Removed paired extract: {doc_id} (matches {match_reason})")
                
                # Remove index entry
                if self.remove_index_entry(doc_id):
                    index_removed += 1
        
        if files_removed > 0 or index_removed > 0:
            print(f"  ✅ Removed {files_removed} extract files and {index_removed} index entries")
        else:
            print("  ✅ No paired extracts found")
        
        return files_removed, index_removed
    
    def clean_404_urls(self, index: dict[str, Dict], max_workers: int | None = None) -> tuple[int, int]:
        """
        Clean up documents with 404 source URLs and their paired extracts
        
        Args:
            index: Index dictionary
            max_workers: Maximum parallel workers. If None, uses config default.
        
        Returns:
            Tuple of (files_removed, index_entries_removed)
        """
        if max_workers is None:
            max_workers = get_drift_max_workers()
        
        print(f"\n🔍 Finding documents with 404 source URLs...")
        url_404s = self.find_404_urls(index, max_workers)
        
        if not url_404s:
            print("  ✅ No 404 URLs found")
            return 0, 0
        
        print(f"\n🧹 Cleaning up {len(url_404s)} documents with 404 URLs...")
        
        files_removed = 0
        index_removed = 0
        
        # Track source URLs that are 404 for paired doc removal
        source_urls_404 = {url for _, url in url_404s}
        
        for doc_id, url in url_404s:
            metadata = index.get(doc_id, {})
            filepath = metadata.get('path')
            
            # Remove file if it exists
            if filepath:
                full_path = self.base_dir / filepath
                if self.remove_doc_file(doc_id, full_path):
                    files_removed += 1
            
            # Remove index entry
            if self.remove_index_entry(doc_id):
                index_removed += 1
        
        # Remove paired extracts that reference 404 source URLs
        paired_removed = self._remove_paired_extracts(index, source_urls_404)
        files_removed += paired_removed[0]
        index_removed += paired_removed[1]
        
        return files_removed, index_removed
    
    def clean_missing_files(self, index: dict[str, Dict]) -> tuple[int, int]:
        """
        Clean up index entries for missing files and their paired extracts
        
        Args:
            index: Index dictionary
        
        Returns:
            Tuple of (files_checked, index_entries_removed)
        """
        print(f"\n🔍 Finding index entries with missing files...")
        missing = self.find_missing_files(index)
        
        if not missing:
            print("  ✅ No missing files found")
            return 0, 0
        
        print(f"\n🧹 Cleaning up {len(missing)} index entries with missing files...")
        
        index_removed = 0
        
        # Track source file paths that are missing for paired doc removal
        # Store both relative paths and absolute paths for matching
        missing_source_paths = set()
        for doc_id, filepath in missing:
            # Add both the full path and relative path for matching
            missing_source_paths.add(str(filepath))
            # Also add relative path from base_dir
            try:
                rel_path = filepath.relative_to(self.base_dir)
                missing_source_paths.add(str(rel_path))
            except ValueError:
                # If not relative to base_dir, use as-is
                pass
            
            if self.remove_index_entry(doc_id):
                index_removed += 1
        
        # Remove paired extracts that reference missing source files
        paired_removed = self._remove_paired_extracts(index, missing_source_paths, by_path=True)
        index_removed += paired_removed[1]
        
        return len(missing), index_removed
    
    def mark_stale_entries(self, index: dict[str, Dict], 
                          stale_urls: list[tuple[str, str | None]] = None) -> int:
        """
        Mark entries as stale for review
        
        Args:
            index: Index dictionary
            stale_urls: Optional list of (doc_id, url) tuples to mark as stale
        
        Returns:
            Number of entries marked as stale
        """
        print(f"\n🏷️  Marking entries as stale...")
        
        marked_count = 0
        
        if stale_urls:
            for doc_id, url in stale_urls:
                if self.mark_as_stale(doc_id, f"Source URL returns 404: {url}"):
                    marked_count += 1
        
        return marked_count
    
    def generate_audit_log(self) -> str:
        """
        Generate audit log of cleanup operations
        
        Returns:
            Audit log as markdown string
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        log = f"""# Drift Cleanup Audit Log

**Generated:** {timestamp}
**Mode:** {'DRY-RUN' if self.dry_run else 'LIVE'}
**Operations:** {len(self.cleanup_log)}

## Summary

"""
        
        # Group by action
        by_action: dict[str, list[Dict]] = {}
        for entry in self.cleanup_log:
            action = entry['action']
            if action not in by_action:
                by_action[action] = []
            by_action[action].append(entry)
        
        for action, entries in by_action.items():
            log += f"### {action.replace('_', ' ').title()}\n\n"
            log += f"**Count:** {len(entries)}\n\n"
            for entry in entries[:20]:  # Limit to first 20 per action
                log += f"- `{entry.get('doc_id', 'unknown')}`"
                if 'filepath' in entry:
                    log += f" - {entry['filepath']}"
                if 'reason' in entry:
                    log += f" - {entry['reason']}"
                log += f"\n"
            if len(entries) > 20:
                log += f"\n... and {len(entries) - 20} more\n"
            log += "\n"
        
        if not self.cleanup_log:
            log += "✅ No cleanup operations performed.\n\n"
        
        return log
    
    def write_audit_log(self):
        """Write audit log to file"""
        log_content = self.generate_audit_log()
        
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        temp_dir = get_temp_dir()
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = temp_dir / f"{timestamp}-drift-cleanup.md"
        
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(log_content)
        
        print(f"\n📝 Audit log written: {log_file}")

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Clean up stale documentation and drift',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry-run (show what would be cleaned, uses default base-dir from config)
  python cleanup_drift.py --dry-run

  # Clean up 404 URLs
  python cleanup_drift.py --clean-404s

  # Clean up missing files
  python cleanup_drift.py --clean-missing-files

  # Full cleanup (all operations)
  python cleanup_drift.py --full-cleanup

  # Custom base directory
  python cleanup_drift.py --base-dir custom/path --dry-run
        """
    )
    
    # Get defaults from config
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    
    default_max_workers = get_drift_max_workers()
    
    add_base_dir_argument(parser)
    parser.add_argument('--dry-run', action='store_true',
                       help='Dry-run mode (show what would be cleaned, no actual changes)')
    parser.add_argument('--clean-404s', action='store_true',
                       help='Remove documents with 404 source URLs')
    parser.add_argument('--clean-missing-files', action='store_true',
                       help='Remove index entries for missing files')
    parser.add_argument('--mark-stale', action='store_true',
                       help='Mark stale entries for review (instead of removing)')
    parser.add_argument('--full-cleanup', action='store_true',
                       help='Perform all cleanup operations')
    parser.add_argument('--clean-source-removed', action='store_true',
                       help='Detect and clean documents removed from source sitemap')
    parser.add_argument('--sitemap', help='Sitemap URL (required for --clean-source-removed)')
    parser.add_argument('--filter', help='Filter pattern for sitemap URLs (optional)')
    parser.add_argument('--output-subdir', help='Output subdirectory to check (e.g., docs-claude-com)')
    parser.add_argument('--max-workers', type=int, default=default_max_workers,
                       help=f'Maximum parallel workers for 404 checks (default: {default_max_workers}, from config)')
    parser.add_argument('--audit-log', action='store_true',
                       help='Write audit log to file')
    
    args = parser.parse_args()
    
    # Initialize cleaner - resolve base_dir using helper
    from utils.cli_utils import resolve_base_dir_from_args
    base_dir = resolve_base_dir_from_args(args)
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)
    
    cleaner = DriftCleaner(base_dir, dry_run=args.dry_run)
    
    # Load index
    index = cleaner.load_index()
    
    # Determine operations
    clean_404s = args.clean_404s or args.full_cleanup
    clean_missing = args.clean_missing_files or args.full_cleanup
    clean_source_removed = args.clean_source_removed or args.full_cleanup
    mark_stale_only = args.mark_stale and not args.full_cleanup
    
    if not (clean_404s or clean_missing or clean_source_removed or mark_stale_only):
        print("❌ No cleanup operations specified. Use --clean-404s, --clean-missing-files, --clean-source-removed, --mark-stale, or --full-cleanup")
        sys.exit(1)
    
    # Validate source-removed cleanup requirements
    if clean_source_removed:
        if not args.sitemap:
            print("❌ --clean-source-removed requires --sitemap")
            sys.exit(1)
        if not args.output_subdir:
            print("❌ --clean-source-removed requires --output-subdir")
            sys.exit(1)
    
    # Perform cleanup operations
    total_files_removed = 0
    total_index_removed = 0
    total_marked_stale = 0
    
    if clean_404s:
        if mark_stale_only:
            url_404s = cleaner.find_404_urls(index, max_workers=args.max_workers)
            total_marked_stale = cleaner.mark_stale_entries(index, url_404s)
        else:
            files_removed, index_removed = cleaner.clean_404_urls(index, max_workers=args.max_workers)
            total_files_removed += files_removed
            total_index_removed += index_removed
    
    if clean_missing:
        files_checked, index_removed = cleaner.clean_missing_files(index)
        total_index_removed += index_removed
    
    if clean_source_removed:
        files_removed, index_removed = cleaner.clean_source_removed_docs(
            args.sitemap,
            args.filter,
            args.output_subdir,
            max_workers=args.max_workers if args.max_workers != default_max_workers else None
        )
        total_files_removed += files_removed
        total_index_removed += index_removed
    
    # Generate summary
    print(f"\n{'='*60}")
    print(f"Cleanup Summary")
    print(f"{'='*60}")
    print(f"Files removed: {total_files_removed}")
    print(f"Index entries removed: {total_index_removed}")
    print(f"Entries marked stale: {total_marked_stale}")
    print(f"Total operations: {len(cleaner.cleanup_log)}")
    
    # Write audit log
    if args.audit_log or len(cleaner.cleanup_log) > 0:
        cleaner.write_audit_log()
    
    # Exit code
    if len(cleaner.cleanup_log) > 0:
        print(f"\n✅ Cleanup completed: {len(cleaner.cleanup_log)} operations")
        sys.exit(0)
    else:
        print(f"\n✅ No cleanup needed")
        sys.exit(0)

if __name__ == '__main__':
    main()

