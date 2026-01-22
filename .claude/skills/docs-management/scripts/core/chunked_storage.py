#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
chunked_storage.py - Efficient storage for llms-full.txt content.

Converts massive concatenated llms-full.txt files (6M+ tokens) into individual
page files, matching the existing storage pattern used by sitemap scraping.

Storage pattern:
    Source: https://platform.claude.com/en/docs/agents
    Stored: canonical/platform-claude-com/en/docs/agents.md

This maintains compatibility with the existing canonical storage structure
and enables per-page deduplication.

Usage:
    from core.chunked_storage import ChunkedStorage
    from core.dedup_manager import DeduplicationManager

    storage = ChunkedStorage(canonical_dir)
    dedup = DeduplicationManager()

    for page, path, skip_reason in storage.process_llms_full(
        content=llms_full_content,
        source_name="platform.claude.com",
        dedup_manager=dedup,
        priority=1,
        dedup_group="docs-management"
    ):
        if skip_reason:
            print(f"Skipped: {page.source_url} - {skip_reason}")
        else:
            print(f"Stored: {page.title} -> {path}")
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
from typing import Generator
from urllib.parse import urlparse

from utils.path_config import get_base_dir

# Import sibling modules
from core.llms_parser import LlmsFullParser, LlmsFullPage


class ChunkedStorage:
    """
    Splits llms-full.txt into individual markdown files.

    Storage pattern matches existing sitemap storage:
        canonical/{domain}/{path-segments}/page-name.md

    Example:
        Source: https://platform.claude.com/en/docs/agents
        Stored: canonical/platform-claude-com/en/docs/agents.md
    """

    def __init__(self, canonical_dir: Path | None = None):
        """
        Initialize chunked storage.

        Args:
            canonical_dir: Directory for storing canonical files.
                          If None, uses config-based default.
        """
        self.canonical_dir = canonical_dir if canonical_dir else get_base_dir()
        self.parser = LlmsFullParser()

    def url_to_path(self, url: str) -> Path:
        """
        Convert URL to storage path.

        Transform:
            https://platform.claude.com/en/docs/agents
            -> platform-claude-com/en/docs/agents.md

        Args:
            url: Source URL

        Returns:
            Path relative to canonical_dir
        """
        parsed = urlparse(url)

        # Convert domain to directory name (dots to dashes)
        domain = parsed.netloc.replace('.', '-')

        # Get path, strip leading/trailing slashes
        path = parsed.path.strip('/')

        # Handle empty path (root page)
        if not path:
            path = 'index'

        # Remove .html/.htm extensions if present
        path = re.sub(r'\.html?$', '', path)

        # If path doesn't end with .md, add it
        if not path.endswith('.md'):
            # Check if it already has an extension
            if '.' in Path(path).name:
                # Has extension (like .md), keep as is
                pass
            else:
                # No extension, add .md
                path = f"{path}.md"

        return self.canonical_dir / domain / path

    def store_page(self, page: LlmsFullPage, add_metadata: bool = True) -> Path:
        """
        Store a single page, returning the storage path.

        Args:
            page: LlmsFullPage object to store
            add_metadata: If True, add source URL as metadata comment

        Returns:
            Path where the file was stored
        """
        storage_path = self.url_to_path(page.source_url)

        # Create directory structure
        storage_path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare content with optional metadata
        if add_metadata:
            # Check if content already has a title
            content = page.content.strip()
            if not content.startswith('#'):
                # Add title if not present
                content = f"# {page.title}\n\n{content}"

            # Add source metadata as HTML comment (doesn't affect rendering)
            full_content = f"<!-- Source: {page.source_url} -->\n\n{content}"
        else:
            full_content = page.content

        # Write file
        storage_path.write_text(full_content, encoding='utf-8')

        return storage_path

    def process_llms_full(
        self,
        content: str,
        source_name: str,
        dedup_manager=None,
        priority: int = 1,
        dedup_group: str | None = None,
        add_metadata: bool = True
    ) -> Generator[tuple[LlmsFullPage, Path | None, str | None], None, None]:
        """
        Process llms-full.txt content, storing pages individually.

        Yields tuples for each page found:
        - (page, storage_path, None) - page was stored successfully
        - (page, None, skip_reason) - page was skipped

        Args:
            content: Full text content of llms-full.txt
            source_name: Name of the source (for logging/dedup)
            dedup_manager: Optional DeduplicationManager for deduplication
            priority: Deduplication priority (lower = higher priority)
            dedup_group: Group name for deduplication
            add_metadata: Add source URL metadata to stored files

        Yields:
            Tuple of (page: LlmsFullPage, path: Path | None, skip_reason: str | None)
        """
        for page in self.parser.parse_stream(content):
            # Check deduplication if manager provided
            if dedup_manager and dedup_group:
                should_process, reason = dedup_manager.should_process(
                    url=page.source_url,
                    source_name=source_name,
                    priority=priority,
                    group=dedup_group,
                    content=page.content
                )

                if not should_process:
                    yield page, None, reason
                    continue

            # Store the page
            storage_path = self.store_page(page, add_metadata=add_metadata)

            # Register with dedup manager
            if dedup_manager and dedup_group:
                content_hash = dedup_manager.compute_hash(page.content)
                dedup_manager.register(
                    url=page.source_url,
                    source_name=source_name,
                    priority=priority,
                    group=dedup_group,
                    content_hash=content_hash
                )

            yield page, storage_path, None

    def process_and_count(
        self,
        content: str,
        source_name: str,
        dedup_manager=None,
        priority: int = 1,
        dedup_group: str | None = None,
        add_metadata: bool = True
    ) -> dict:
        """
        Process llms-full.txt and return summary statistics.

        Args:
            content: Full text content of llms-full.txt
            source_name: Name of the source
            dedup_manager: Optional DeduplicationManager
            priority: Deduplication priority
            dedup_group: Group name for deduplication
            add_metadata: Add source URL metadata

        Returns:
            Dictionary with processed, skipped counts and file paths
        """
        processed = 0
        skipped = 0
        stored_paths: list[str] = []
        skipped_urls: list[str] = []

        for page, path, skip_reason in self.process_llms_full(
            content=content,
            source_name=source_name,
            dedup_manager=dedup_manager,
            priority=priority,
            dedup_group=dedup_group,
            add_metadata=add_metadata
        ):
            if skip_reason:
                skipped += 1
                skipped_urls.append(page.source_url)
            else:
                processed += 1
                if path:
                    stored_paths.append(str(path))

        return {
            'processed': processed,
            'skipped': skipped,
            'stored_paths': stored_paths,
            'skipped_urls': skipped_urls
        }


def url_to_canonical_path(url: str, canonical_dir: Path | None = None) -> Path:
    """
    Convenience function to convert URL to canonical storage path.

    Args:
        url: Source URL
        canonical_dir: Optional canonical directory (uses default if None)

    Returns:
        Full path where the file would be stored
    """
    storage = ChunkedStorage(canonical_dir)
    return storage.url_to_path(url)


if __name__ == '__main__':
    """Self-test for chunked_storage module."""
    import tempfile
    import shutil

    print("chunked_storage Self-Test")
    print("=" * 60)

    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    print(f"\nUsing temp directory: {temp_dir}")

    try:
        storage = ChunkedStorage(temp_dir)

        # Test URL to path conversion
        print("\n1. Testing URL to path conversion:")
        test_urls = [
            "https://platform.claude.com/en/docs/agents",
            "https://docs.claude.com/en/api/messages",
            "https://example.com/page.html",
            "https://example.com/",
        ]
        for url in test_urls:
            path = storage.url_to_path(url)
            rel_path = path.relative_to(temp_dir)
            print(f"   {url}")
            print(f"   -> {rel_path}")

        # Test storing a page
        print("\n2. Testing page storage:")
        test_page = LlmsFullPage(
            title="Test Page",
            source_url="https://platform.claude.com/en/docs/test",
            content="# Test Page\n\nThis is test content.\n\n## Section\n\nMore content here."
        )
        stored_path = storage.store_page(test_page)
        print(f"   Stored: {test_page.title}")
        print(f"   Path: {stored_path.relative_to(temp_dir)}")
        print(f"   File exists: {stored_path.exists()}")

        if stored_path.exists():
            print(f"   File size: {stored_path.stat().st_size} bytes")

        # Test processing llms-full.txt with deduplication
        print("\n3. Testing llms-full.txt processing with deduplication:")

        # Import dedup_manager for testing
        from core.dedup_manager import DeduplicationManager

        sample_content = """# Introduction
Source: https://platform.claude.com/en/docs/intro

Welcome to Claude documentation.

# Quickstart
Source: https://platform.claude.com/en/docs/quickstart

Get started with Claude.

# Introduction
Source: https://docs.claude.com/en/docs/intro

Duplicate introduction from docs.claude.com.
"""

        dedup = DeduplicationManager()

        # Process first source (platform, priority 1)
        stats = storage.process_and_count(
            content=sample_content,
            source_name="platform.claude.com",
            dedup_manager=dedup,
            priority=1,
            dedup_group="docs-management"
        )
        print(f"   Platform.claude.com: processed={stats['processed']}, skipped={stats['skipped']}")

        # Check dedup stats
        dedup_stats = dedup.get_stats("docs-management")
        print(f"   Dedup stats: processed={dedup_stats['processed']}, skipped={dedup_stats['skipped']}")

        # List created files
        print("\n4. Created files:")
        for f in temp_dir.rglob("*.md"):
            rel_path = f.relative_to(temp_dir)
            print(f"   {rel_path}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temp directory")

    print("\n" + "=" * 60)
    print("Self-test complete!")
