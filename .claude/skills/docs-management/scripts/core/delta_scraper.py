#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
delta_scraper.py - Delta-based scraping using llms.txt manifests.

Provides efficient change detection by:
1. Caching llms.txt manifest state (hash + URL list)
2. Comparing current manifest against previous version
3. Computing URL-level deltas (new, removed, unchanged)
4. Only fetching pages that have changed

This can reduce HTTP requests by 80-99% for typical runs where few pages change.

Usage:
    from core.delta_scraper import DeltaScraper, DeltaResult

    delta = DeltaScraper(cache_dir)

    # Check if manifest changed
    if not delta.manifest_changed("platform.claude.com", llms_txt_url):
        print("No changes detected - skipping scrape")
        return

    # Compute delta
    result = delta.compute_delta("platform.claude.com", current_content, previous_content)
    print(f"New URLs: {len(result.new)}")
    print(f"Removed URLs: {len(result.removed)}")
    print(f"Unchanged URLs: {len(result.unchanged)}")

    # Only scrape new/changed URLs
    for url in result.new:
        scrape_url(url)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Set

from utils.path_config import get_base_dir

# Import llms_parser for URL extraction
from core.llms_parser import LlmsParser


@dataclass
class DeltaResult:
    """Result of computing URL delta between manifest versions."""
    new: Set[str] = field(default_factory=set)       # URLs in current but not previous
    removed: Set[str] = field(default_factory=set)   # URLs in previous but not current
    unchanged: Set[str] = field(default_factory=set) # URLs in both
    current_count: int = 0                           # Total URLs in current manifest
    previous_count: int = 0                          # Total URLs in previous manifest

    @property
    def has_changes(self) -> bool:
        """True if there are any new or removed URLs."""
        return len(self.new) > 0 or len(self.removed) > 0

    @property
    def change_summary(self) -> str:
        """Human-readable change summary."""
        if not self.has_changes:
            return f"No changes ({len(self.unchanged)} URLs unchanged)"
        return f"+{len(self.new)} new, -{len(self.removed)} removed, {len(self.unchanged)} unchanged"


@dataclass
class ManifestState:
    """Cached state of an llms.txt manifest."""
    source_name: str
    url: str
    content_hash: str
    url_count: int
    urls: Set[str]
    last_checked: str  # ISO format datetime
    last_changed: str | None = None  # ISO format datetime when content changed

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'source_name': self.source_name,
            'url': self.url,
            'content_hash': self.content_hash,
            'url_count': self.url_count,
            'urls': list(self.urls),
            'last_checked': self.last_checked,
            'last_changed': self.last_changed
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'ManifestState':
        """Create from dictionary."""
        return cls(
            source_name=data['source_name'],
            url=data['url'],
            content_hash=data['content_hash'],
            url_count=data['url_count'],
            urls=set(data.get('urls', [])),
            last_checked=data['last_checked'],
            last_changed=data.get('last_changed')
        )


class DeltaScraper:
    """
    Delta-based scraper using llms.txt for change detection.

    Maintains a cache of manifest states to enable efficient change detection.
    When a manifest hasn't changed (same hash), no scraping is needed.
    When a manifest has changed, computes URL-level delta to minimize work.
    """

    CACHE_FILENAME = 'manifest_state.json'

    def __init__(self, cache_dir: Path | None = None):
        """
        Initialize delta scraper.

        Args:
            cache_dir: Directory for caching manifest state.
                      Defaults to canonical/.llms_cache/
        """
        if cache_dir is None:
            canonical_dir = get_base_dir()
            cache_dir = canonical_dir / '.llms_cache'

        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.cache_path = self.cache_dir / self.CACHE_FILENAME
        self._manifest_states: dict[str, ManifestState] = {}
        self._load_cache()

        self.parser = LlmsParser()

    def _load_cache(self) -> None:
        """Load cached manifest states from disk."""
        from utils.cache_manager import compute_plugin_fingerprint

        if not self.cache_path.exists():
            return

        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate fingerprint - if code changed, invalidate cache
            if data.get('_plugin_fingerprint') != compute_plugin_fingerprint():
                print("Plugin code changed - clearing stale manifest cache")
                self._manifest_states = {}
                return

            for source_name, state_dict in data.items():
                if source_name.startswith('_'):  # Skip metadata keys
                    continue
                self._manifest_states[source_name] = ManifestState.from_dict(state_dict)

        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Failed to load manifest cache: {e}")
            self._manifest_states = {}

    def _save_cache(self) -> None:
        """Save manifest states to disk."""
        from utils.cache_manager import compute_plugin_fingerprint

        data = {
            '_plugin_fingerprint': compute_plugin_fingerprint(),
            **{name: state.to_dict() for name, state in self._manifest_states.items()}
        }

        with open(self.cache_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def extract_urls(self, content: str) -> Set[str]:
        """Extract URLs from llms.txt content."""
        return set(self.parser.extract_urls(content))

    def get_previous_state(self, source_name: str) -> ManifestState | None:
        """Get cached state for a source."""
        return self._manifest_states.get(source_name)

    def manifest_changed(
        self,
        source_name: str,
        current_content: str
    ) -> bool:
        """
        Check if manifest has changed since last check.

        Fast check using content hash - no URL parsing needed.

        Args:
            source_name: Name of the source
            current_content: Current llms.txt content

        Returns:
            True if manifest has changed (or is new), False if unchanged
        """
        current_hash = self.compute_hash(current_content)
        previous = self.get_previous_state(source_name)

        if previous is None:
            return True  # New source, needs processing

        return current_hash != previous.content_hash

    def compute_delta(
        self,
        source_name: str,
        current_content: str
    ) -> DeltaResult:
        """
        Compute URL-level delta between current and previous manifest.

        Args:
            source_name: Name of the source
            current_content: Current llms.txt content

        Returns:
            DeltaResult with new, removed, and unchanged URL sets
        """
        current_urls = self.extract_urls(current_content)
        previous = self.get_previous_state(source_name)

        if previous is None:
            # All URLs are new
            return DeltaResult(
                new=current_urls,
                removed=set(),
                unchanged=set(),
                current_count=len(current_urls),
                previous_count=0
            )

        previous_urls = previous.urls

        return DeltaResult(
            new=current_urls - previous_urls,
            removed=previous_urls - current_urls,
            unchanged=current_urls & previous_urls,
            current_count=len(current_urls),
            previous_count=len(previous_urls)
        )

    def update_state(
        self,
        source_name: str,
        url: str,
        content: str,
        save: bool = True
    ) -> ManifestState:
        """
        Update cached state for a source.

        Call this after successfully processing a manifest.

        Args:
            source_name: Name of the source
            url: URL of the llms.txt file
            content: Current llms.txt content
            save: If True, persist to disk immediately

        Returns:
            Updated ManifestState
        """
        content_hash = self.compute_hash(content)
        urls = self.extract_urls(content)
        now = datetime.now(timezone.utc).isoformat()

        # Check if content changed
        previous = self.get_previous_state(source_name)
        if previous is None or previous.content_hash != content_hash:
            last_changed = now
        else:
            last_changed = previous.last_changed

        state = ManifestState(
            source_name=source_name,
            url=url,
            content_hash=content_hash,
            url_count=len(urls),
            urls=urls,
            last_checked=now,
            last_changed=last_changed
        )

        self._manifest_states[source_name] = state

        if save:
            self._save_cache()

        return state

    def get_all_states(self) -> dict[str, ManifestState]:
        """Get all cached manifest states."""
        return dict(self._manifest_states)

    def clear_source(self, source_name: str, save: bool = True) -> None:
        """Clear cached state for a source."""
        if source_name in self._manifest_states:
            del self._manifest_states[source_name]
            if save:
                self._save_cache()

    def clear_all(self, save: bool = True) -> None:
        """Clear all cached states."""
        self._manifest_states.clear()
        if save:
            self._save_cache()

    def get_cache_info(self) -> dict:
        """Get cache information and statistics."""
        return {
            'cache_dir': str(self.cache_dir),
            'cache_file': str(self.cache_path),
            'sources_cached': len(self._manifest_states),
            'sources': list(self._manifest_states.keys()),
            'total_urls_cached': sum(
                state.url_count for state in self._manifest_states.values()
            )
        }


def compute_url_delta(current_urls: Set[str], previous_urls: Set[str]) -> DeltaResult:
    """
    Convenience function to compute delta between two URL sets.

    Args:
        current_urls: Current set of URLs
        previous_urls: Previous set of URLs

    Returns:
        DeltaResult with new, removed, unchanged sets
    """
    return DeltaResult(
        new=current_urls - previous_urls,
        removed=previous_urls - current_urls,
        unchanged=current_urls & previous_urls,
        current_count=len(current_urls),
        previous_count=len(previous_urls)
    )


if __name__ == '__main__':
    """Self-test for delta_scraper module."""
    import tempfile
    import shutil

    print("delta_scraper Self-Test")
    print("=" * 60)

    # Create temporary directory for testing
    temp_dir = Path(tempfile.mkdtemp())
    print(f"\nUsing temp directory: {temp_dir}")

    try:
        delta = DeltaScraper(temp_dir)

        # Sample llms.txt content (version 1)
        sample_v1 = """# Claude Documentation

## Getting Started
- [Introduction](https://docs.claude.com/en/docs/intro.md): Welcome
- [Quickstart](https://docs.claude.com/en/docs/quickstart.md): Get started

## API
- [Messages](https://docs.claude.com/en/api/messages.md)
"""

        # Sample llms.txt content (version 2 - one new, one removed)
        sample_v2 = """# Claude Documentation

## Getting Started
- [Introduction](https://docs.claude.com/en/docs/intro.md): Welcome
- [Quickstart](https://docs.claude.com/en/docs/quickstart.md): Get started

## API
- [Models](https://docs.claude.com/en/api/models.md): New page
"""

        print("\n1. Testing initial state (no cache):")
        changed = delta.manifest_changed("test-source", sample_v1)
        print(f"   Manifest changed (new source): {changed}")

        print("\n2. Testing delta computation (initial):")
        result = delta.compute_delta("test-source", sample_v1)
        print(f"   {result.change_summary}")
        print(f"   New URLs: {len(result.new)}")

        print("\n3. Updating state after processing:")
        state = delta.update_state(
            source_name="test-source",
            url="https://example.com/llms.txt",
            content=sample_v1
        )
        print(f"   Cached {state.url_count} URLs")
        print(f"   Hash: {state.content_hash[:16]}...")

        print("\n4. Testing same content (no change):")
        changed = delta.manifest_changed("test-source", sample_v1)
        print(f"   Manifest changed: {changed}")

        print("\n5. Testing changed content:")
        changed = delta.manifest_changed("test-source", sample_v2)
        print(f"   Manifest changed: {changed}")

        print("\n6. Computing delta (v1 -> v2):")
        result = delta.compute_delta("test-source", sample_v2)
        print(f"   {result.change_summary}")
        print(f"   New: {result.new}")
        print(f"   Removed: {result.removed}")

        print("\n7. Cache info:")
        info = delta.get_cache_info()
        print(f"   Sources cached: {info['sources_cached']}")
        print(f"   Total URLs: {info['total_urls_cached']}")

        print("\n8. Verifying cache persistence:")
        # Create new instance to test loading from disk
        delta2 = DeltaScraper(temp_dir)
        state2 = delta2.get_previous_state("test-source")
        print(f"   Loaded from disk: {state2 is not None}")
        if state2:
            print(f"   URL count matches: {state2.url_count == state.url_count}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print(f"\nCleaned up temp directory")

    print("\n" + "=" * 60)
    print("Self-test complete!")
