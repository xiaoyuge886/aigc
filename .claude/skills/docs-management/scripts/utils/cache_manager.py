#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cache_manager.py - Centralized cache management for docs-management plugin.

Provides robust cache invalidation using content hashes (not just file mtime),
which is essential for correct behavior after git pull operations where
Git sets file mtime to checkout time rather than commit time.

Two cache types are managed:
1. Inverted index cache (.cache/inverted_index.json) - search index
2. LLMS/scraper cache (.llms_cache/manifest_state.json) - delta scraper state

Usage:
    from utils.cache_manager import CacheManager

    cm = CacheManager(base_dir)
    if not cm.is_inverted_index_valid():
        # Cache needs rebuild
        ...

    # Clear caches
    cm.clear_inverted_index()
    cm.clear_all()
"""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.script_utils import configure_utf8_output

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Cache format version - bump when cache structure changes
CACHE_FORMAT_VERSION = "1.0"

# Cache file names
INVERTED_INDEX_CACHE = "inverted_index.json"
CACHE_VERSION_FILE = "cache_version.json"
LLMS_CACHE_DIR = ".llms_cache"
MANIFEST_STATE_FILE = "manifest_state.json"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of file content.

    Args:
        file_path: Path to file to hash

    Returns:
        Hash string in format "sha256:<hex_digest>"

    Raises:
        FileNotFoundError: If file doesn't exist
        OSError: If file can't be read
    """
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        # Read in chunks for memory efficiency with large files
        for chunk in iter(lambda: f.read(65536), b''):
            hasher.update(chunk)
    return f"sha256:{hasher.hexdigest()}"

def compute_plugin_fingerprint() -> str:
    """
    Compute fingerprint of all plugin Python scripts.

    Any code change will change this hash, triggering cache invalidation.
    This is fool-proof: no manual version updates needed.

    Returns:
        Hash string in format "sha256:<short_hex_digest>"
    """
    # Navigate to scripts directory (this file is in scripts/utils/)
    scripts_dir = Path(__file__).resolve().parents[1]  # scripts/

    hasher = hashlib.sha256()

    # Hash all .py files in sorted order for determinism
    py_files = sorted(scripts_dir.rglob("*.py"))
    for py_file in py_files:
        try:
            # Include relative path in hash (detects renames/moves)
            rel_path = py_file.relative_to(scripts_dir)
            hasher.update(str(rel_path).encode('utf-8'))
            hasher.update(py_file.read_bytes())
        except OSError:
            continue

    return f"sha256:{hasher.hexdigest()[:16]}"  # Short hash sufficient


class CacheManager:
    """
    Centralized cache management with content hash-based invalidation.

    Unlike mtime-based invalidation, content hashes correctly detect
    changes after git pull operations.
    """

    def __init__(self, base_dir: Path):
        """
        Initialize cache manager.

        Args:
            base_dir: Base directory containing index.yaml (canonical dir)
        """
        self.base_dir = Path(base_dir)

        # Cache locations
        # .cache is at skill root level (parent of canonical)
        self._skill_dir = self.base_dir.parent
        self._cache_dir = self._skill_dir / ".cache"
        self._inverted_index_path = self._cache_dir / INVERTED_INDEX_CACHE
        self._cache_version_path = self._cache_dir / CACHE_VERSION_FILE

        # LLMS cache is inside canonical dir
        self._llms_cache_dir = self.base_dir / LLMS_CACHE_DIR
        self._manifest_state_path = self._llms_cache_dir / MANIFEST_STATE_FILE

        # Index file (source of truth for inverted index)
        self._index_path = self.base_dir / "index.yaml"

    def _load_cache_version(self) -> dict | None:
        """Load cache version info from disk."""
        if not self._cache_version_path.exists():
            return None
        try:
            with open(self._cache_version_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _save_cache_version(self, index_hash: str) -> None:
        """
        Save cache version info to disk.

        Args:
            index_hash: Hash of index.yaml content
        """
        try:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

            version_info = {
                "cache_format_version": CACHE_FORMAT_VERSION,
                "plugin_fingerprint": compute_plugin_fingerprint(),
                "index_yaml_hash": index_hash,
                "index_yaml_mtime": self._index_path.stat().st_mtime if self._index_path.exists() else 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "source_path": str(self._index_path.relative_to(self._skill_dir))
            }

            # Write atomically
            temp_path = self._cache_version_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(version_info, f, indent=2)
            temp_path.replace(self._cache_version_path)
        except OSError:
            pass  # Best effort - don't fail on cache version write errors

    def is_inverted_index_valid(self) -> bool:
        """
        Check if inverted index cache is valid.

        Uses hybrid approach:
        1. Fast path: check if cache exists and version file exists
        2. Plugin fingerprint: invalidate if any script changed
        3. mtime check: if index.yaml mtime unchanged, assume valid
        4. Hash check: if mtime changed, verify content hash

        Returns:
            True if cache is valid and can be used, False if rebuild needed
        """
        # Cache must exist
        if not self._inverted_index_path.exists():
            return False

        # Version info must exist
        version_info = self._load_cache_version()
        if not version_info:
            return False

        # Check format version
        if version_info.get("cache_format_version") != CACHE_FORMAT_VERSION:
            return False

        # Check plugin fingerprint - invalidate if ANY script changed
        if version_info.get("plugin_fingerprint") != compute_plugin_fingerprint():
            return False

        # Index file must exist
        if not self._index_path.exists():
            return False

        # Fast path: mtime unchanged means content unchanged
        try:
            current_mtime = self._index_path.stat().st_mtime
            cached_mtime = version_info.get("index_yaml_mtime", 0)

            if current_mtime == cached_mtime:
                return True

            # mtime changed - could be git checkout or actual content change
            # Verify with content hash
            current_hash = compute_file_hash(self._index_path)
            cached_hash = version_info.get("index_yaml_hash", "")

            if current_hash == cached_hash:
                # Content unchanged despite mtime change (git checkout)
                # Update mtime in version file to avoid repeated hash checks
                self._save_cache_version(current_hash)
                return True

            # Content actually changed - cache is invalid
            return False

        except OSError:
            return False

    def mark_inverted_index_built(self) -> None:
        """
        Mark that inverted index was just built.

        Call this after building the inverted index to save version info.
        """
        if not self._index_path.exists():
            return

        try:
            current_hash = compute_file_hash(self._index_path)
            self._save_cache_version(current_hash)
        except OSError:
            pass

    def clear_inverted_index(self) -> bool:
        """
        Clear inverted index cache.

        Returns:
            True if cache was cleared, False if nothing to clear
        """
        cleared = False

        try:
            if self._inverted_index_path.exists():
                self._inverted_index_path.unlink()
                cleared = True
        except OSError:
            pass

        try:
            if self._cache_version_path.exists():
                self._cache_version_path.unlink()
                cleared = True
        except OSError:
            pass

        return cleared

    def clear_llms_cache(self) -> bool:
        """
        Clear LLMS/scraper cache.

        Returns:
            True if cache was cleared, False if nothing to clear
        """
        try:
            if self._manifest_state_path.exists():
                self._manifest_state_path.unlink()
                return True
        except OSError:
            pass
        return False

    def clear_all(self) -> dict:
        """
        Clear all caches.

        Returns:
            Dict with keys 'inverted_index' and 'llms_cache' indicating what was cleared
        """
        return {
            'inverted_index': self.clear_inverted_index(),
            'llms_cache': self.clear_llms_cache()
        }

    def get_cache_info(self) -> dict:
        """
        Get information about cache state.

        Returns:
            Dict with cache status and statistics
        """
        info = {
            'cache_dir': str(self._cache_dir),
            'inverted_index': {
                'path': str(self._inverted_index_path),
                'exists': self._inverted_index_path.exists(),
                'valid': self.is_inverted_index_valid(),
                'size_bytes': self._inverted_index_path.stat().st_size if self._inverted_index_path.exists() else 0
            },
            'cache_version': {
                'path': str(self._cache_version_path),
                'exists': self._cache_version_path.exists(),
            },
            'llms_cache': {
                'path': str(self._manifest_state_path),
                'exists': self._manifest_state_path.exists(),
                'size_bytes': self._manifest_state_path.stat().st_size if self._manifest_state_path.exists() else 0
            },
            'index_yaml': {
                'path': str(self._index_path),
                'exists': self._index_path.exists(),
            }
        }

        # Add version info if available
        version_info = self._load_cache_version()
        if version_info:
            info['cache_version']['data'] = version_info

        # Add current index hash for comparison
        if self._index_path.exists():
            try:
                info['index_yaml']['current_hash'] = compute_file_hash(self._index_path)
            except OSError:
                info['index_yaml']['current_hash'] = None

        return info


if __name__ == '__main__':
    # Simple CLI for testing
    import argparse

    parser = argparse.ArgumentParser(description='Cache manager utility')
    parser.add_argument('--base-dir', type=Path, help='Base directory (canonical)')
    parser.add_argument('--info', action='store_true', help='Show cache info')
    parser.add_argument('--clear', action='store_true', help='Clear all caches')
    parser.add_argument('--check', action='store_true', help='Check cache validity')

    args = parser.parse_args()

    if args.base_dir:
        base_dir = args.base_dir
    else:
        # Default to canonical dir relative to this script
        base_dir = Path(__file__).resolve().parents[2] / "canonical"

    cm = CacheManager(base_dir)

    if args.info:
        info = cm.get_cache_info()
        print(json.dumps(info, indent=2, default=str))
    elif args.clear:
        result = cm.clear_all()
        print(f"Cleared: {result}")
    elif args.check:
        valid = cm.is_inverted_index_valid()
        print(f"Inverted index valid: {valid}")
    else:
        parser.print_help()
