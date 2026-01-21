#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dedup_manager.py - Smart deduplication manager for handling overlapping sources.

When scraping documentation from multiple sources (e.g., platform.claude.com and
docs.claude.com), many pages may overlap. This module provides intelligent
deduplication using:

1. URL path normalization - Strip protocol and domain to compare paths
2. Priority-based resolution - Lower priority number wins (e.g., priority=1 > priority=2)
3. Content hash comparison - For same-priority conflicts, use content hash

Usage:
    from core.dedup_manager import DeduplicationManager

    dedup = DeduplicationManager()

    # Check if URL should be processed
    should_process, reason = dedup.should_process(
        url="https://docs.claude.com/en/docs/agents",
        source_name="docs.claude.com",
        priority=2,
        group="docs-management"
    )

    if should_process:
        # Process the page...
        dedup.register(url, source_name, priority, group, content_hash="abc123")
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hashlib
from dataclasses import dataclass, field
from typing import Dict, Set
from urllib.parse import urlparse


@dataclass
class DedupEntry:
    """Tracks a deduplicated page."""
    normalized_path: str
    source_url: str
    source_name: str
    priority: int
    content_hash: str | None = None


class DeduplicationManager:
    """
    Manages deduplication across sources in the same group.

    Sources are grouped by dedup_group (e.g., "docs-management"). Within a group,
    pages are deduplicated by normalized URL path using priority-based resolution.

    Example:
        - platform.claude.com/en/docs/agents (priority=1) - WINS
        - docs.claude.com/en/docs/agents (priority=2) - SKIPPED

    Both normalize to /en/docs/agents, and priority 1 < priority 2, so platform wins.
    """

    def __init__(self):
        # group -> normalized_path -> DedupEntry
        self._registry: Dict[str, Dict[str, DedupEntry]] = {}
        # group -> set of skipped URLs
        self._skipped: Dict[str, Set[str]] = {}
        # Statistics
        self._stats: Dict[str, Dict[str, int]] = {}

    def normalize_path(self, url: str) -> str:
        """
        Normalize URL to comparable path.

        Strips protocol and domain, keeping only the path portion.
        This allows comparison across different domains serving the same content.

        Examples:
            https://platform.claude.com/en/docs/agents -> /en/docs/agents
            https://docs.claude.com/en/docs/agents -> /en/docs/agents
            https://example.com/page.html -> /page.html
            https://example.com/page.md -> /page.md

        Args:
            url: Full URL to normalize

        Returns:
            Normalized path string
        """
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')

        # Normalize empty path to /
        if not path:
            path = '/'

        # Remove common file extensions for comparison
        # e.g., /page.html and /page.md should match
        # But keep .md extension as it's meaningful for documentation
        # for ext in ['.html', '.htm']:
        #     if path.endswith(ext):
        #         path = path[:-len(ext)]

        return path

    def compute_hash(self, content: str) -> str:
        """
        Compute content hash for comparison.

        Args:
            content: String content to hash

        Returns:
            First 16 characters of SHA-256 hash
        """
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

    def should_process(
        self,
        url: str,
        source_name: str,
        priority: int,
        group: str,
        content: str | None = None
    ) -> tuple[bool, str | None]:
        """
        Determine if a page should be processed or skipped.

        Decision logic:
        1. If path not seen before -> process
        2. If path seen with higher priority (lower number) -> skip
        3. If path seen with lower priority (higher number) -> process (replace)
        4. If same priority, use content hash if available
        5. Same priority, no hash -> first wins

        Args:
            url: URL to check
            source_name: Name of the source (for logging)
            priority: Priority number (lower = higher priority)
            group: Deduplication group name
            content: Optional content for hash comparison

        Returns:
            Tuple of (should_process: bool, skip_reason: str | None)
            - should_process=True, skip_reason=None -> process this URL
            - should_process=False, skip_reason="..." -> skip with reason
        """
        # Initialize group if needed
        if group not in self._registry:
            self._registry[group] = {}
            self._skipped[group] = set()
            self._stats[group] = {'processed': 0, 'skipped': 0, 'replaced': 0}

        normalized = self.normalize_path(url)
        registry = self._registry[group]

        # Check if path already registered
        if normalized in registry:
            existing = registry[normalized]

            # Higher priority (lower number) always wins
            if priority < existing.priority:
                # We have higher priority - process and replace
                self._stats[group]['replaced'] += 1
                return True, None

            elif priority > existing.priority:
                # Lower priority - skip
                self._skipped[group].add(url)
                self._stats[group]['skipped'] += 1
                return False, f"Lower priority ({priority}) than {existing.source_name} ({existing.priority})"

            else:
                # Same priority - use content hash if available
                if content and existing.content_hash:
                    new_hash = self.compute_hash(content)
                    if new_hash == existing.content_hash:
                        self._skipped[group].add(url)
                        self._stats[group]['skipped'] += 1
                        return False, f"Duplicate content (hash match with {existing.source_name})"

                # Same priority, different/unknown content - first wins
                self._skipped[group].add(url)
                self._stats[group]['skipped'] += 1
                return False, f"Same priority, {existing.source_name} processed first"

        # Path not seen before - process
        return True, None

    def register(
        self,
        url: str,
        source_name: str,
        priority: int,
        group: str,
        content_hash: str | None = None
    ) -> None:
        """
        Register a processed page.

        Call this after successfully processing a page to track it for deduplication.

        Args:
            url: URL that was processed
            source_name: Name of the source
            priority: Priority number
            group: Deduplication group
            content_hash: Optional content hash for future comparison
        """
        if group not in self._registry:
            self._registry[group] = {}
            self._stats[group] = {'processed': 0, 'skipped': 0, 'replaced': 0}

        normalized = self.normalize_path(url)

        # Check if replacing existing entry
        if normalized in self._registry[group]:
            # This is a replacement (higher priority)
            pass
        else:
            self._stats[group]['processed'] += 1

        self._registry[group][normalized] = DedupEntry(
            normalized_path=normalized,
            source_url=url,
            source_name=source_name,
            priority=priority,
            content_hash=content_hash
        )

    def get_stats(self, group: str) -> dict:
        """
        Get deduplication statistics for a group.

        Args:
            group: Deduplication group name

        Returns:
            Dictionary with processed, skipped, replaced counts and skipped URLs
        """
        if group not in self._stats:
            return {
                'processed': 0,
                'skipped': 0,
                'replaced': 0,
                'skipped_urls': []
            }

        return {
            **self._stats.get(group, {}),
            'skipped_urls': list(self._skipped.get(group, set()))
        }

    def get_all_stats(self) -> dict:
        """Get statistics for all groups."""
        return {
            group: self.get_stats(group)
            for group in self._registry.keys()
        }

    def get_registered_paths(self, group: str) -> dict[str, DedupEntry]:
        """Get all registered paths for a group."""
        return dict(self._registry.get(group, {}))

    def is_registered(self, url: str, group: str) -> bool:
        """Check if a URL's path is already registered in a group."""
        if group not in self._registry:
            return False
        normalized = self.normalize_path(url)
        return normalized in self._registry[group]

    def clear_group(self, group: str) -> None:
        """Clear all data for a specific group."""
        if group in self._registry:
            del self._registry[group]
        if group in self._skipped:
            del self._skipped[group]
        if group in self._stats:
            del self._stats[group]

    def clear_all(self) -> None:
        """Clear all deduplication data."""
        self._registry.clear()
        self._skipped.clear()
        self._stats.clear()


if __name__ == '__main__':
    """Self-test for dedup_manager module."""
    print("dedup_manager Self-Test")
    print("=" * 60)

    dedup = DeduplicationManager()

    # Test URL normalization
    print("\n1. Testing URL normalization:")
    test_urls = [
        "https://platform.claude.com/en/docs/agents",
        "https://docs.claude.com/en/docs/agents",
        "https://example.com/page.md",
        "https://example.com/",
    ]
    for url in test_urls:
        normalized = dedup.normalize_path(url)
        print(f"   {url}")
        print(f"   -> {normalized}")

    # Test deduplication with priorities
    print("\n2. Testing priority-based deduplication:")

    # First source: platform.claude.com (priority 1)
    print("\n   Processing platform.claude.com (priority=1):")
    urls_platform = [
        "https://platform.claude.com/en/docs/intro",
        "https://platform.claude.com/en/docs/agents",
        "https://platform.claude.com/en/docs/quickstart",
    ]
    for url in urls_platform:
        should_process, reason = dedup.should_process(
            url=url,
            source_name="platform.claude.com",
            priority=1,
            group="docs-management"
        )
        print(f"   {url}: process={should_process}")
        if should_process:
            dedup.register(url, "platform.claude.com", 1, "docs-management")

    # Second source: docs.claude.com (priority 2)
    print("\n   Processing docs.claude.com (priority=2):")
    urls_docs = [
        "https://docs.claude.com/en/docs/intro",  # Should be skipped (exists in platform)
        "https://docs.claude.com/en/docs/agents",  # Should be skipped (exists in platform)
        "https://docs.claude.com/en/docs/unique",  # Should process (new)
    ]
    for url in urls_docs:
        should_process, reason = dedup.should_process(
            url=url,
            source_name="docs.claude.com",
            priority=2,
            group="docs-management"
        )
        if should_process:
            print(f"   {url}: PROCESS (new path)")
            dedup.register(url, "docs.claude.com", 2, "docs-management")
        else:
            print(f"   {url}: SKIP ({reason})")

    # Print statistics
    print("\n3. Deduplication statistics:")
    stats = dedup.get_stats("docs-management")
    print(f"   Processed: {stats['processed']}")
    print(f"   Skipped: {stats['skipped']}")
    print(f"   Replaced: {stats['replaced']}")
    print(f"   Skipped URLs: {stats['skipped_urls']}")

    print("\n" + "=" * 60)
    print("Self-test complete!")
