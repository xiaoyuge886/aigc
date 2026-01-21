#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_llms_full.py - Scrape documentation from llms-full.txt files

!!! WARNING: CONTENT TRUNCATION RISK !!!
Investigation on 2025-11-27 found that some llms-full.txt files contain
TRUNCATED/SUMMARIZED content compared to the actual documentation pages.
For example, code.claude.com/docs/llms-full.txt loses ~131 lines from
amazon-bedrock.md compared to fetching the actual page.

RECOMMENDATION: Use llms-txt type (URL discovery) + individual page fetching
instead of llms-full. This ensures you get complete documentation content.

This script is kept for:
- Sites where llms-full.txt actually has full content
- Manual testing/comparison
- Offline documentation where truncation is acceptable

This script processes llms-full.txt files, which contain rendered documentation
content in a single file. Each page is separated by title/source headers:

    # Page Title
    Source: https://example.com/page.md

    [Full markdown content...]

Benefits (when content is complete):
- Single HTTP request for all content
- Memory-efficient stream processing for large files (10MB+)
- Faster than individual URL scraping

Usage:
    python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt
    python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt --output code-claude-com

Dependencies:
    pip install requests pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

from utils.script_utils import configure_utf8_output, format_duration
from utils.path_config import get_base_dir, get_index_path
from utils.config_helpers import get_http_timeout, get_output_dir_mapping
from utils.logging_utils import get_or_setup_logger
from utils.http_utils import fetch_with_retry
from llms_parser import LlmsFullParser, LlmsFullPage

configure_utf8_output()

try:
    import requests
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Install with: pip install requests")
    sys.exit(1)

from utils.script_utils import ensure_yaml_installed
yaml = ensure_yaml_installed()

logger = get_or_setup_logger(__file__, log_category="scrape")


def url_to_local_path(source_url: str, output_dir: Path) -> Path:
    """
    Convert a source URL to a local file path.

    Args:
        source_url: URL like "https://code.claude.com/docs/en/overview.md"
        output_dir: Base output directory like "canonical/code-claude-com"

    Returns:
        Local path like "canonical/code-claude-com/docs/en/overview.md"
    """
    parsed = urlparse(source_url)
    path = parsed.path

    # Remove leading slash
    if path.startswith('/'):
        path = path[1:]

    # Ensure .md extension
    if not path.endswith('.md'):
        path = path + '.md'

    return output_dir / path


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]


def add_frontmatter(content: str, source_url: str, title: str, content_hash: str) -> str:
    """
    Add YAML frontmatter to content.

    Args:
        content: Markdown content
        source_url: Source URL
        title: Page title
        content_hash: Content hash

    Returns:
        Content with frontmatter prepended
    """
    now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

    frontmatter = f"""---
source_url: {source_url}
title: {title}
content_hash: {content_hash}
last_fetched: {now}
source_type: llms-full
---

"""
    return frontmatter + content


class LlmsFullScraper:
    """Scraper for llms-full.txt files."""

    def __init__(self, base_output_dir: Path | None = None):
        """
        Initialize scraper.

        Args:
            base_output_dir: Base directory for canonical storage
        """
        self.base_output_dir = base_output_dir if base_output_dir else get_base_dir()
        self.parser = LlmsFullParser()
        self.index = {}
        self.index_path = get_index_path(self.base_output_dir)
        self._load_index()

    def _load_index(self):
        """Load existing index if available."""
        if self.index_path.exists():
            try:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    self.index = yaml.safe_load(f) or {}
            except Exception as e:
                logger.warning(f"Could not load index: {e}")
                self.index = {}

    def _save_index(self):
        """Save index to disk."""
        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.index_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.index, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            logger.warning(f"Could not save index: {e}")

    def auto_detect_output_dir(self, url: str) -> str:
        """Auto-detect output directory from URL domain."""
        parsed = urlparse(url)
        domain = parsed.netloc
        return get_output_dir_mapping(domain)

    def should_skip_page(self, page: LlmsFullPage, output_path: Path) -> bool:
        """
        Check if page should be skipped based on existing content.

        Args:
            page: Page from llms-full.txt
            output_path: Where file would be saved

        Returns:
            True if page should be skipped (unchanged)
        """
        if not output_path.exists():
            return False

        try:
            existing_content = output_path.read_text(encoding='utf-8')

            # Extract existing hash from frontmatter
            if existing_content.startswith('---'):
                end = existing_content.find('---', 3)
                if end > 0:
                    frontmatter_text = existing_content[3:end]
                    frontmatter = yaml.safe_load(frontmatter_text)
                    existing_hash = frontmatter.get('content_hash', '')

                    # Compare with new content hash
                    new_hash = compute_content_hash(page.content)
                    if existing_hash == new_hash:
                        return True
        except Exception as e:
            logger.debug(f"Error checking existing file: {e}")

        return False

    def scrape_llms_full(self, llms_full_url: str, output_subdir: str | None = None,
                         skip_existing: bool = True, limit: int | None = None) -> int:
        """
        Scrape documentation from llms-full.txt.

        Args:
            llms_full_url: URL to llms-full.txt file
            output_subdir: Output subdirectory (auto-detected if not provided)
            skip_existing: Skip pages with unchanged content
            limit: Optional limit on pages to process (for testing)

        Returns:
            Number of pages successfully processed
        """
        print(f"Fetching llms-full.txt: {llms_full_url}")
        start_time = time.time()

        # Fetch llms-full.txt content
        try:
            timeout = get_http_timeout()
            response = requests.get(llms_full_url, timeout=timeout)
            response.raise_for_status()
            content = response.text
            print(f"  Downloaded {len(content):,} bytes")
        except Exception as e:
            print(f"Failed to fetch llms-full.txt: {e}")
            return 0

        # Auto-detect output directory if not provided
        if not output_subdir:
            output_subdir = self.auto_detect_output_dir(llms_full_url)
            print(f"  Auto-detected output directory: {output_subdir}")

        output_dir = self.base_output_dir / output_subdir

        # Stream process pages
        success_count = 0
        skipped_count = 0
        failed_count = 0
        page_count = 0

        print(f"\n{'='*60}")
        print(f"Processing pages from llms-full.txt")
        print(f"{'='*60}")

        for page in self.parser.parse_stream(content):
            page_count += 1

            if limit and page_count > limit:
                print(f"\n  Reached limit of {limit} pages")
                break

            # Convert source URL to local path
            output_path = url_to_local_path(page.source_url, output_dir)

            print(f"\n[{page_count}] {page.title}")
            print(f"    Source: {page.source_url}")
            print(f"    Output: {output_path.relative_to(self.base_output_dir)}")

            # Check if should skip
            if skip_existing and self.should_skip_page(page, output_path):
                print(f"    Skipped (unchanged)")
                skipped_count += 1
                success_count += 1
                continue

            try:
                # Compute content hash
                content_hash = compute_content_hash(page.content)

                # Add frontmatter
                full_content = add_frontmatter(page.content, page.source_url, page.title, content_hash)

                # Ensure directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                output_path.write_text(full_content, encoding='utf-8')
                print(f"    Saved ({len(full_content):,} bytes)")

                # Update index
                doc_id = str(output_path.relative_to(self.base_output_dir)).replace('.md', '').replace('/', '-').replace('\\', '-')
                self.index[doc_id] = {
                    'source_url': page.source_url,
                    'content_hash': content_hash,
                    'last_fetched': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'path': str(output_path.relative_to(self.base_output_dir)),
                    'title': page.title
                }

                success_count += 1

            except Exception as e:
                print(f"    Failed: {e}")
                failed_count += 1
                logger.error(f"Failed to process page {page.source_url}: {e}")

        # Save index
        self._save_index()

        # Print summary
        duration = time.time() - start_time
        print(f"\n{'='*60}")
        print(f"Scraping Summary")
        print(f"{'='*60}")
        print(f"  Total pages:    {page_count}")
        print(f"  New/Updated:    {success_count - skipped_count}")
        print(f"  Skipped:        {skipped_count}")
        print(f"  Failed:         {failed_count}")
        print(f"  Duration:       {format_duration(duration)}")
        print(f"{'='*60}")

        return success_count


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Scrape documentation from llms-full.txt files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape from llms-full.txt (auto-detects output directory)
  python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt

  # With custom output directory
  python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt --output code-claude-com

  # Force re-scrape (don't skip existing)
  python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt --no-skip-existing

  # Limit pages for testing
  python scrape_llms_full.py --url https://code.claude.com/docs/llms-full.txt --limit 5
        """
    )

    parser.add_argument('--url', required=True, help='URL to llms-full.txt file')
    parser.add_argument('--output', help='Output subdirectory (auto-detected if not provided)')
    parser.add_argument('--skip-existing', action='store_true', default=True,
                        help='Skip pages with unchanged content (default: True)')
    parser.add_argument('--no-skip-existing', dest='skip_existing', action='store_false',
                        help='Force re-scrape all pages')
    parser.add_argument('--limit', type=int, help='Limit number of pages to process (for testing)')

    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)

    args = parser.parse_args()

    # Resolve base directory
    base_dir = resolve_base_dir_from_args(args)
    base_dir.mkdir(parents=True, exist_ok=True)

    print(f"Using base directory: {base_dir}")

    # Create scraper and run
    scraper = LlmsFullScraper(base_dir)
    success_count = scraper.scrape_llms_full(
        args.url,
        output_subdir=args.output,
        skip_existing=args.skip_existing,
        limit=args.limit
    )

    print(f"\nScraping complete: {success_count} page(s) processed")
    sys.exit(0 if success_count > 0 else 1)


if __name__ == '__main__':
    main()
