#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
detect_changes.py - Detect new and removed documentation pages

Compares sitemap URLs with indexed documentation to identify:
- New pages (in sitemap but not indexed)
- Removed pages (indexed but no longer in sitemap)

Supports marking removed pages as "stale" for manual review before deletion.

Usage:
    # Detect changes (dry-run, no modifications)
    python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                             --filter "docs.claude.com/en/docs" \\
                             --output platform-docs

    # Mark removed pages as stale
    python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                             --filter "docs.claude.com/en/docs" \\
                             --output platform-docs \\
                             --mark-stale

    # Generate change report
    python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                             --filter "docs.claude.com/en/docs" \\
                             --output platform-docs \\
                             --report

Dependencies:
    pip install requests pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from utils.script_utils import configure_utf8_output, ensure_yaml_installed
from utils.http_utils import fetch_with_retry, DEFAULT_TIMEOUT
from utils.path_config import get_base_dir, get_index_path
from utils.config_helpers import get_management_user_agent, get_http_timeout, get_drift_max_workers
from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
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

# Import index_manager for large file support
try:
    from management.index_manager import IndexManager
except ImportError:
    IndexManager = None

class ChangeDetector:
    """Detect new and removed documentation pages"""

    def __init__(self, base_output_dir: Path | None = None):
        """
        Initialize change detector

        Args:
            base_output_dir: Base directory for canonical storage. If None, uses config default.
        """
        self.base_output_dir = base_output_dir if base_output_dir else get_base_dir()
        self.index_path = get_index_path(self.base_output_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': get_management_user_agent()
        })
        
        # Initialize index manager if available
        if IndexManager:
            self.index_manager = IndexManager(self.base_output_dir)
        else:
            self.index_manager = None

    def fetch_sitemap(self, sitemap_url: str) -> str:
        """
        Fetch sitemap.xml content

        Args:
            sitemap_url: URL to sitemap.xml

        Returns:
            Sitemap XML content as string
        """
        try:
            print(f"📄 Fetching sitemap: {sitemap_url}")
            timeout = get_http_timeout()
            response = self.session.get(sitemap_url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"❌ Failed to fetch sitemap: {e}")
            sys.exit(1)

    def parse_sitemap(self, sitemap_content: str, url_filter: str = None) -> set[str]:
        """
        Parse sitemap.xml and extract URLs

        Args:
            sitemap_content: Sitemap XML content
            url_filter: Optional regex pattern to filter URLs

        Returns:
            Set of URLs from sitemap
        """
        try:
            root = ET.fromstring(sitemap_content)
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            urls = {loc.text for loc in root.findall('.//ns:loc', namespace)}

            print(f"  Found {len(urls)} URLs in sitemap")

            if url_filter:
                pattern = re.compile(url_filter)
                urls = {url for url in urls if pattern.search(url)}
                print(f"  Filtered to {len(urls)} URLs matching pattern: {url_filter}")

            return urls
        except ET.ParseError as e:
            print(f"❌ Failed to parse sitemap XML: {e}")
            sys.exit(1)

    def load_index(self) -> dict[str, dict]:
        """
        Load index.yaml

        Returns:
            Dictionary of indexed documents (doc_id -> metadata)
        """
        if not self.index_path.exists():
            print(f"⚠️  Index file not found: {self.index_path}")
            return {}

        # Use index_manager if available (handles large files)
        if self.index_manager:
            try:
                index = self.index_manager.load_all()
                print(f"📋 Loaded {len(index)} entries from index")
                return index
            except Exception as e:
                print(f"❌ Failed to load index: {e}")
                sys.exit(1)
        else:
            # Fallback to original implementation
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    index = yaml.safe_load(f) or {}
                print(f"📋 Loaded {len(index)} entries from index")
                return index
            except Exception as e:
                print(f"❌ Failed to load index: {e}")
                sys.exit(1)

    def get_indexed_urls(self, index: dict, output_subdir: str) -> dict[str, str]:
        """
        Extract URLs from index for specific output directory

        Args:
            index: Index dictionary
            output_subdir: Subdirectory to filter by (e.g., 'platform-docs')

        Returns:
            Dictionary mapping URL to doc_id
        """
        url_to_doc_id = {}
        for doc_id, metadata in index.items():
            if metadata.get('path', '').startswith(f"{output_subdir}/"):
                url = metadata.get('url')
                if url:
                    url_to_doc_id[url] = doc_id

        print(f"  Found {len(url_to_doc_id)} indexed URLs for {output_subdir}")
        return url_to_doc_id

    def detect_changes(self, sitemap_urls: set[str], indexed_urls: dict[str, str]) -> tuple[set[str], set[str]]:
        """
        Compare sitemap URLs with indexed URLs

        Args:
            sitemap_urls: Set of URLs from sitemap
            indexed_urls: Dictionary of indexed URLs (url -> doc_id)

        Returns:
            Tuple of (new_urls, removed_urls)
        """
        indexed_url_set = set(indexed_urls.keys())

        new_urls = sitemap_urls - indexed_url_set
        removed_urls = indexed_url_set - sitemap_urls

        return new_urls, removed_urls
    
    def check_404_urls(self, urls: set[str], max_workers: int | None = None) -> dict[str, bool]:
        """
        Check which URLs return 404 (removed from source)
        
        Args:
            urls: Set of URLs to check
            max_workers: Maximum parallel workers for checking. If None, uses config default.
        
        Returns:
            Dictionary mapping URL to is_404 (True if 404, False otherwise)
        """
        if max_workers is None:
            max_workers = get_drift_max_workers()
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        def check_url(url: str) -> tuple[str, bool]:
            """Check if URL returns 404"""
            try:
                response = self.session.head(url, timeout=DEFAULT_TIMEOUT, allow_redirects=True)
                return url, response.status_code == 404
            except Exception:
                # On error, assume not 404 (could be network issue)
                return url, False
        
        print(f"  Checking {len(urls)} URLs for 404 status...")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_url, url): url for url in urls}
            for future in as_completed(futures):
                url, is_404 = future.result()
                results[url] = is_404
                if is_404:
                    print(f"    ❌ 404: {url}")
        
        return results
    
    def compare_content_hashes(self, indexed_urls: dict[str, str], output_subdir: str) -> dict[str, tuple[str, str | None]]:
        """
        Compare content hashes between local files and source URLs
        
        Args:
            indexed_urls: Dictionary of indexed URLs (url -> doc_id)
            output_subdir: Output subdirectory
        
        Returns:
            Dictionary mapping doc_id to (local_hash, remote_hash)
            remote_hash is None if fetch failed
        """
        import concurrent.futures

        hash_comparisons = {}
        
        def get_file_hash(filepath: Path) -> str | None:
            """Get SHA256 hash of file content"""
            if not filepath.exists():
                return None
            try:
                with open(filepath, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
            except Exception:
                return None
        
        def get_remote_hash(url: str) -> str | None:
            """Get SHA256 hash of remote content"""
            try:
                response = fetch_with_retry(url, timeout=DEFAULT_TIMEOUT, max_retries=1)
                if response.status_code == 200:
                    return hashlib.sha256(response.content).hexdigest()
            except Exception:
                pass
            return None
        
        print(f"  Comparing content hashes for {len(indexed_urls)} documents...")
        
        # Load index to get file paths from metadata
        index = self.load_index()
        
        max_workers = get_drift_max_workers()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {}
            for url, doc_id in indexed_urls.items():
                # Get file path from index metadata
                metadata = index.get(doc_id, {})
                filepath_rel = metadata.get('path')
                if not filepath_rel:
                    continue
                
                # Resolve full path relative to base_output_dir
                filepath = self.base_output_dir / filepath_rel
                
                # Submit hash comparison
                future = executor.submit(
                    lambda u, fp: (u, get_file_hash(fp), get_remote_hash(u)),
                    url, filepath
                )
                futures[future] = doc_id
            
            for future in concurrent.futures.as_completed(futures):
                doc_id = futures[future]
                try:
                    url, local_hash, remote_hash = future.result()
                    hash_comparisons[doc_id] = (local_hash, remote_hash)
                    if local_hash and remote_hash and local_hash != remote_hash:
                        print(f"    ⚠️  Hash mismatch: {doc_id} (content changed)")
                        # Mark doc as stale in index
                        self._mark_doc_stale_in_index(doc_id, 'content_hash_mismatch')
                except Exception as e:
                    print(f"    ❌ Error comparing hash for {doc_id}: {e}")
        
        return hash_comparisons
    
    def _mark_doc_stale_in_index(self, doc_id: str, reason: str) -> None:
        """
        Mark document as stale in index metadata
        
        Args:
            doc_id: Document identifier
            reason: Reason for marking stale (e.g., 'content_hash_mismatch', 'source_url_404')
        """
        if not self.index_manager:
            return  # Can't update index without index manager
        
        try:
            entry = self.index_manager.get_entry(doc_id)
            if entry:
                entry['stale'] = True
                entry['stale_reason'] = reason
                entry['stale_detected'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                self.index_manager.update_entry(doc_id, entry)
        except Exception as e:
            # Don't fail drift detection if marking stale fails
            print(f"    ⚠️  Warning: Failed to mark doc as stale in index: {e}")

    def mark_as_stale(self, doc_ids: list[str], output_subdir: str) -> int:
        """
        Mark documents as stale by adding status field to frontmatter

        Args:
            doc_ids: List of document IDs to mark as stale
            output_subdir: Output subdirectory (e.g., 'platform-docs')

        Returns:
            Number of documents marked as stale
        """
        marked_count = 0
        
        # Load index to get file paths from metadata
        index = self.load_index()

        for doc_id in doc_ids:
            # Get file path from index metadata
            metadata = index.get(doc_id, {})
            filepath_rel = metadata.get('path')
            if not filepath_rel:
                print(f"  ⚠️  No path found for doc_id: {doc_id}")
                continue

            # Resolve full path relative to base_output_dir
            filepath = self.base_output_dir / filepath_rel

            if not filepath.exists():
                print(f"  ⚠️  File not found: {filepath}")
                continue

            try:
                # Read file
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Check if already stale
                if 'status: stale' in content:
                    print(f"  ⏭️  Already stale: {filepath_rel}")
                    continue

                # Add status field to frontmatter
                # Find frontmatter boundaries
                if content.startswith('---\n'):
                    end_idx = content.find('\n---\n', 4)
                    if end_idx != -1:
                        frontmatter = content[4:end_idx]
                        body = content[end_idx + 5:]

                        # Add status field
                        frontmatter_dict = yaml.safe_load(frontmatter) or {}
                        frontmatter_dict['status'] = 'stale'
                        frontmatter_dict['marked_stale'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')

                        # Reconstruct file
                        new_frontmatter = yaml.dump(frontmatter_dict, default_flow_style=False, sort_keys=False)
                        new_content = f"---\n{new_frontmatter}---\n{body}"

                        # Write back
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)

                        print(f"  ✅ Marked as stale: {filepath_rel}")
                        marked_count += 1
                    else:
                        print(f"  ⚠️  Invalid frontmatter: {filepath_rel}")
                else:
                    print(f"  ⚠️  No frontmatter found: {filepath_rel}")

            except Exception as e:
                print(f"  ❌ Failed to mark {filepath_rel} as stale: {e}")

        return marked_count

    def generate_report(self, new_urls: set[str], removed_urls: set[str],
                       indexed_urls: dict[str, str], output_subdir: str,
                       url_404s: dict[str, bool | None] = None,
                       hash_mismatches: dict[str, tuple[str, str | None]] = None) -> str:
        """
        Generate comprehensive change report

        Args:
            new_urls: Set of new URLs
            removed_urls: Set of removed URLs
            indexed_urls: Dictionary of indexed URLs (url -> doc_id)
            output_subdir: Output subdirectory
            url_404s: Optional dictionary mapping URL to is_404 status
            hash_mismatches: Optional dictionary mapping doc_id to (local_hash, remote_hash)

        Returns:
            Report as markdown string
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')
        
        # Count 404s
        url_404_count = 0
        if url_404s:
            url_404_count = sum(1 for is_404 in url_404s.values() if is_404)
        
        # Count hash mismatches
        hash_mismatch_count = 0
        if hash_mismatches:
            hash_mismatch_count = sum(1 for local, remote in hash_mismatches.values() 
                                     if local and remote and local != remote)

        report = f"""# Documentation Change Report

**Generated:** {timestamp}
**Source:** {output_subdir}

## Summary

- **New pages:** {len(new_urls)}
- **Removed pages (sitemap):** {len(removed_urls)}
- **404 URLs (removed from source):** {url_404_count}
- **Content changes (hash mismatch):** {hash_mismatch_count}
- **Total changes:** {len(new_urls) + len(removed_urls) + url_404_count + hash_mismatch_count}

"""

        if new_urls:
            report += "## New Pages\n\n"
            report += "These URLs are in the sitemap but not yet indexed:\n\n"
            for url in sorted(new_urls):
                report += f"- {url}\n"
            report += "\n"

        if removed_urls:
            report += "## Removed Pages (Sitemap)\n\n"
            report += "These URLs are indexed but no longer in the sitemap:\n\n"
            for url in sorted(removed_urls):
                doc_id = indexed_urls.get(url, 'unknown')
                report += f"- {url} (doc_id: `{doc_id}`)\n"
            report += "\n"
        
        if url_404s:
            url_404_list = [url for url, is_404 in url_404s.items() if is_404]
            if url_404_list:
                report += "## 404 URLs (Removed from Source)\n\n"
                report += "These source URLs return 404 (content removed):\n\n"
                for url in sorted(url_404_list):
                    doc_id = indexed_urls.get(url, 'unknown')
                    report += f"- {url} (doc_id: `{doc_id}`)\n"
                report += "\n"
        
        if hash_mismatches:
            mismatches = [(doc_id, local, remote) for doc_id, (local, remote) in hash_mismatches.items()
                         if local and remote and local != remote]
            if mismatches:
                report += "## Content Changes (Hash Mismatch)\n\n"
                report += "These documents have changed content (hash mismatch):\n\n"
                for doc_id, local_hash, remote_hash in sorted(mismatches):
                    url = next((u for u, d in indexed_urls.items() if d == doc_id), 'unknown')
                    report += f"- {doc_id} ({url})\n"
                    report += f"  - Local hash:  `{local_hash[:16]}...`\n"
                    report += f"  - Remote hash: `{remote_hash[:16]}...`\n"
                report += "\n"

        if not new_urls and not removed_urls and url_404_count == 0 and hash_mismatch_count == 0:
            report += "✅ No changes detected. All indexed documents are current.\n\n"

        return report

    def write_audit_log(self, report: str, output_subdir: str):
        """
        Write change report to audit log

        Args:
            report: Change report content
            output_subdir: Output subdirectory
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')
        temp_dir = self.base_output_dir.parent / "temp"
        temp_dir.mkdir(exist_ok=True)

        log_file = temp_dir / f"{timestamp}-doc-changes-{output_subdir}.md"

        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"\n📝 Audit log written: {log_file}")

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Detect new and removed documentation pages',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Detect changes (dry-run)
  python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                           --filter "docs.claude.com/en/docs" \\
                           --output platform-docs

  # Mark removed pages as stale
  python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                           --filter "docs.claude.com/en/docs" \\
                           --output platform-docs \\
                           --mark-stale

  # Generate change report
  python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \\
                           --filter "docs.claude.com/en/api" \\
                           --output api-reference \\
                           --report
        """
    )

    parser.add_argument('--sitemap', required=True, help='URL to sitemap.xml')
    parser.add_argument('--filter', help='Regex pattern to filter sitemap URLs (e.g., "docs.claude.com/en/docs")')
    parser.add_argument('--output', required=True, help='Output subdirectory (e.g., platform-docs, api-reference)')
    
    # Get defaults from config (config_helpers should always be available)
    default_max_workers = get_drift_max_workers()
    
    add_base_dir_argument(parser)
    parser.add_argument('--mark-stale', action='store_true',
                       help='Mark removed pages as stale in frontmatter')
    parser.add_argument('--report', action='store_true',
                       help='Write change report to audit log')
    parser.add_argument('--check-404s', action='store_true',
                       help='Check indexed URLs for 404 status (removed from source)')
    parser.add_argument('--check-hashes', action='store_true',
                       help='Compare content hashes between local files and source URLs')
    parser.add_argument('--max-workers', type=int, default=default_max_workers,
                       help=f'Maximum parallel workers for 404/hash checks (default: {default_max_workers}, from config)')

    args = parser.parse_args()

    # Initialize detector - resolve base_dir using helper
    base_dir = resolve_base_dir_from_args(args)
    
    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)

    detector = ChangeDetector(base_dir)

    # Fetch and parse sitemap
    sitemap_content = detector.fetch_sitemap(args.sitemap)
    sitemap_urls = detector.parse_sitemap(sitemap_content, args.filter)

    # Load index and get indexed URLs
    index = detector.load_index()
    indexed_urls = detector.get_indexed_urls(index, args.output)

    # Detect changes
    print(f"\n🔍 Detecting changes...")
    new_urls, removed_urls = detector.detect_changes(sitemap_urls, indexed_urls)
    
    # Check for 404s if requested
    url_404s = None
    if args.check_404s:
        print(f"\n🔍 Checking for 404 URLs...")
        all_indexed_urls = set(indexed_urls.keys())
        max_workers_val = args.max_workers if args.max_workers != default_max_workers else None
        url_404s = detector.check_404_urls(all_indexed_urls, max_workers=max_workers_val)
    
    # Compare content hashes if requested
    hash_mismatches = None
    if args.check_hashes:
        print(f"\n🔍 Comparing content hashes...")
        hash_mismatches = detector.compare_content_hashes(indexed_urls, args.output)

    # Generate report
    report = detector.generate_report(new_urls, removed_urls, indexed_urls, args.output,
                                     url_404s=url_404s, hash_mismatches=hash_mismatches)
    print(f"\n{report}")

    # Mark stale if requested
    if args.mark_stale and removed_urls:
        print(f"\n🏷️  Marking removed pages as stale...")
        removed_doc_ids = [indexed_urls[url] for url in removed_urls]
        marked_count = detector.mark_as_stale(removed_doc_ids, args.output)
        print(f"\n✅ Marked {marked_count}/{len(removed_urls)} documents as stale")

    # Write audit log if requested
    if args.report:
        detector.write_audit_log(report, args.output)

    # Exit code based on changes
    total_changes = len(new_urls) + len(removed_urls)
    if url_404s:
        total_changes += sum(1 for is_404 in url_404s.values() if is_404)
    if hash_mismatches:
        total_changes += sum(1 for local, remote in hash_mismatches.values() 
                           if local and remote and local != remote)
    
    if total_changes > 0:
        print(f"\n⚠️  Changes detected: {len(new_urls)} new, {len(removed_urls)} removed from sitemap")
        if url_404s:
            print(f"   {sum(1 for is_404 in url_404s.values() if is_404)} URLs return 404")
        if hash_mismatches:
            print(f"   {sum(1 for local, remote in hash_mismatches.values() if local and remote and local != remote)} content changes")
        sys.exit(1)  # Non-zero exit code for CI/CD integration
    else:
        print(f"\n✅ No changes detected")
        sys.exit(0)

if __name__ == '__main__':
    main()
