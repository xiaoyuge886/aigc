#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
index_manager.py - Utility module for managing large index.yaml files

Provides efficient read/write access to index.yaml files that may exceed
token limits, supporting chunked reading and single-entry operations.

Usage:
    from management.index_manager import IndexManager
    from path_config import get_base_dir
    
    # Use config default (typically .claude/skills/docs-management/canonical)
    base_dir = get_base_dir()
    manager = IndexManager(base_dir)
    index = manager.load_all()  # Load entire index with chunked reading
    entry = manager.get_entry('doc-id')  # Get single entry without full load
    manager.update_entry('doc-id', metadata)  # Update with locking
    manager.remove_entry('doc-id')  # Remove with locking

Dependencies:
    pip install pyyaml
    pip install ruamel.yaml  # Optional, for better YAML handling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; config_dir = bootstrap.config_dir

import json
import os
import shutil
import time
from typing import Any, Dict, Iterator

from utils.script_utils import configure_utf8_output, ensure_yaml_installed

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Try to use ruamel.yaml for better YAML handling, fallback to pyyaml
try:
    from ruamel.yaml import YAML
    HAS_RUAMEL = True
except ImportError:
    HAS_RUAMEL = False
    yaml = ensure_yaml_installed()

# Import config registry for defaults (bootstrap already set up paths)
try:
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from config.config_registry import get_default
except ImportError:
    # Fallback if config registry not available
    def get_default(section: str, key: str, default: Any) -> Any:
        return default

# Constants (loaded from config with fallbacks)
CHUNK_SIZE = get_default('index', 'chunk_size', 1000)  # Lines per chunk for chunked reading
TOKEN_ESTIMATE_THRESHOLD = get_default('index', 'token_estimate_threshold', 20000)  # Estimated tokens - if file is smaller, load all at once
LOCK_TIMEOUT = get_default('index', 'lock_timeout', 30.0)  # Lock timeout for index operations
LOCK_RETRY_DELAY = get_default('index', 'lock_retry_delay', 0.1)  # Delay between lock acquisition attempts
LOCK_RETRY_BACKOFF = get_default('index', 'lock_retry_backoff', 0.5)  # Delay after failed lock acquisition
FILE_RETRY_DELAY = get_default('index', 'file_retry_delay', 0.2)  # Delay for atomic file operations
FILE_MAX_RETRIES = get_default('index', 'file_max_retries', 5)  # Maximum retries for file operations
STALE_LOCK_THRESHOLD = get_default('index', 'stale_lock_threshold', 300.0)  # Locks older than 5 minutes are considered stale
BATCH_PROGRESS_INTERVAL = get_default('index', 'batch_progress_interval', 100)  # Log progress every N entries in batch operations

# Additional constants for DRY compliance
YAML_WIDTH = 4096  # Wide width for long URLs in YAML output
LOCK_STALE_CHECK_INTERVAL = 50  # Check for stale lock every N retry attempts

class IndexManager:
    """Manage index files with support for large files and JSON optimization

    Supports dual-format storage (YAML + JSON) for optimal performance:
    - JSON is used for reads (>100x faster than YAML parsing)
    - YAML is maintained for human readability and git diffs
    - Both formats are kept in sync on writes
    """

    def __init__(self, base_dir: Path, index_filename: str = "index.yaml"):
        """
        Initialize index manager

        Args:
            base_dir: Base directory containing index.yaml
            index_filename: Name of index file (default: index.yaml)
        """
        self.base_dir = Path(base_dir)
        self.index_path = self.base_dir / index_filename
        # JSON path for fast loading (>100x faster than YAML)
        self.json_path = self.base_dir / index_filename.replace('.yaml', '.json')
        self.lock_file = self.base_dir / '.index.lock'

        # Initialize YAML parser
        if HAS_RUAMEL:
            self.yaml = YAML()
            self.yaml.preserve_quotes = True
            self.yaml.width = YAML_WIDTH
        else:
            self.yaml = None
    
    def _check_stale_lock(self) -> bool:
        """
        Check if lock file is stale (older than threshold) and remove it.

        Returns:
            True if a stale lock was removed, False otherwise
        """
        if not self.lock_file.exists():
            return False

        try:
            lock_age = time.time() - self.lock_file.stat().st_mtime
            if lock_age > STALE_LOCK_THRESHOLD:
                print(f"⚠️  Removing stale lock file (age: {lock_age:.1f}s > {STALE_LOCK_THRESHOLD:.0f}s threshold)")
                self.lock_file.unlink()
                return True
        except Exception:
            pass  # Lock file might have been removed by another process

        return False

    def _acquire_lock(self, timeout: float | None = None) -> bool:
        """
        Acquire file lock for index.yaml updates (parallel-safe)

        Args:
            timeout: Maximum time to wait for lock (seconds). If None, uses config default.

        Returns:
            True if lock acquired, False if timeout
        """
        if timeout is None:
            timeout = LOCK_TIMEOUT

        start_time = time.time()
        retry_count = 0

        # Check for stale lock before starting
        self._check_stale_lock()

        while time.time() - start_time < timeout:
            try:
                # Try to create lock file exclusively (Windows-compatible)
                fd = os.open(str(self.lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return True
            except OSError:
                # Lock file exists, check if stale
                retry_count += 1
                if retry_count % LOCK_STALE_CHECK_INTERVAL == 0:
                    self._check_stale_lock()
                time.sleep(LOCK_RETRY_DELAY)
                continue
            except Exception:
                retry_count += 1
                time.sleep(LOCK_RETRY_DELAY)
                continue

        # Timeout - provide context for debugging
        elapsed = time.time() - start_time
        print(f"⚠️  Lock acquisition timed out after {elapsed:.1f}s ({retry_count} retries)")
        return False  # Timeout
    
    def _release_lock(self):
        """Release file lock for index.yaml"""
        try:
            if self.lock_file.exists():
                self.lock_file.unlink()
        except Exception:
            pass  # Ignore errors when releasing lock

    def _acquire_lock_with_retry(self, operation: str) -> bool:
        """
        Acquire lock with single retry and logging.

        Args:
            operation: Name of the operation requiring the lock (for logging)

        Returns:
            True if lock acquired, False otherwise
        """
        if self._acquire_lock():
            return True
        print(f"⚠️  Warning: Could not acquire index lock for {operation}, retrying...")
        time.sleep(LOCK_RETRY_BACKOFF)
        if self._acquire_lock():
            return True
        print(f"❌ Error: Failed to acquire index lock after retry for {operation}")
        return False

    def _atomic_move_with_retry(self, temp_path: Path, dest: Path) -> bool:
        """
        Atomic file move with exponential backoff retry.

        Args:
            temp_path: Source temporary file path
            dest: Destination file path

        Returns:
            True if successful, False otherwise
        """
        retry_delay = FILE_RETRY_DELAY
        for attempt in range(FILE_MAX_RETRIES):
            try:
                if dest.exists():
                    dest.unlink()
                shutil.move(str(temp_path), str(dest))
                return True
            except (OSError, PermissionError) as e:
                if attempt < FILE_MAX_RETRIES - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                raise e
        return False

    def _validate_index_not_empty(self, index: Dict, operation: str) -> bool:
        """
        Validate index is not empty before write operation (data loss prevention).

        Args:
            index: The loaded index dictionary
            operation: Name of the operation (for error message)

        Returns:
            True if validation passes, False if index appears corrupted
        """
        if not index and self.index_path.exists() and self.index_path.stat().st_size > 0:
            print(f"❌ Error: Loaded index is empty but file exists and has content. "
                  f"Aborting {operation} to prevent data loss.")
            return False
        return True

    def _estimate_file_size(self) -> int:
        """
        Estimate file size in tokens (rough estimate: 1 token ≈ 4 characters)
        
        Returns:
            Estimated token count
        """
        if not self.index_path.exists():
            return 0
        
        try:
            size_bytes = self.index_path.stat().st_size
            # Rough estimate: 1 token ≈ 4 characters
            return size_bytes // 4
        except Exception:
            return 0
    
    def _load_yaml_chunked(self) -> Dict:
        """
        Load YAML file in chunks for large files
        
        Returns:
            Dictionary of index entries
        """
        if not self.index_path.exists():
            return {}
        
        # If file is small enough, load all at once
        estimated_tokens = self._estimate_file_size()
        if estimated_tokens < TOKEN_ESTIMATE_THRESHOLD:
            return self._load_yaml_full()
        
        # For large files, read in chunks and parse incrementally
        index = {}
        current_key = None
        current_entry = {}
        current_entry_lines = []
        
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Check if this is a new entry (key starts at column 0, no leading spaces)
                    stripped = line.rstrip()
                    if stripped and not line.startswith(' ') and not line.startswith('\t'):
                        # Save previous entry if exists
                        if current_key and current_entry:
                            index[current_key] = current_entry
                        
                        # Start new entry
                        if ':' in stripped:
                            current_key = stripped.split(':', 1)[0].strip()
                            current_entry = {}
                            current_entry_lines = [line]
                        else:
                            current_key = None
                            current_entry = {}
                            current_entry_lines = []
                    else:
                        # Continuation of current entry
                        if current_key:
                            current_entry_lines.append(line)
                            
                            # Try to parse completed fields
                            if ':' in stripped:
                                parts = stripped.split(':', 1)
                                if len(parts) == 2:
                                    key = parts[0].strip()
                                    value = parts[1].strip()
                                    # Remove quotes if present
                                    if value.startswith("'") and value.endswith("'"):
                                        value = value[1:-1]
                                    elif value.startswith('"') and value.endswith('"'):
                                        value = value[1:-1]
                                    current_entry[key] = value
                
                # Save last entry
                if current_key and current_entry:
                    index[current_key] = current_entry
            
            return index
        
        except Exception as e:
            # Don't fall back to full load if file is too large - it will also fail
            estimated_tokens = self._estimate_file_size()
            if estimated_tokens >= TOKEN_ESTIMATE_THRESHOLD:
                print(f"❌ Chunked parsing failed for large file ({estimated_tokens} estimated tokens): {e}")
                print(f"   File is too large to load. Use manage_index.py or get_entry() for single entries.")
                raise RuntimeError(f"Cannot load large index.yaml file: {e}")
            # Only fall back to full load if file is small enough
            print(f"⚠️  Chunked parsing failed: {e}, falling back to full load (file is small)")
            return self._load_yaml_full()
    
    def _load_yaml_full(self) -> Dict:
        """
        Load entire YAML file at once
        
        Returns:
            Dictionary of index entries
        """
        if not self.index_path.exists():
            return {}
        
        try:
            if HAS_RUAMEL:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    return self.yaml.load(f) or {}
            else:
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"❌ Error loading index.yaml: {e}")
            return {}

    def _save_json(self, index: Dict) -> bool:
        """
        Save index to JSON file for fast loading (>100x faster than YAML)

        Args:
            index: Dictionary of index entries to save

        Returns:
            True if successful, False otherwise
        """
        if not index:
            return True  # Nothing to save

        temp_path = self.json_path.with_suffix('.json.tmp')
        try:
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False, sort_keys=True)

            # Atomic rename with retry
            return self._atomic_move_with_retry(temp_path, self.json_path)
        except Exception as e:
            print(f"⚠️  Error saving index.json: {e}")
            # Clean up temp file on error
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False

    def load_all(self) -> Dict:
        """
        Load entire index - prefers JSON for speed (>100x faster), falls back to YAML

        Returns:
            Dictionary of all index entries (doc_id -> metadata)
        """
        # Prefer JSON for speed (>100x faster than YAML parsing)
        if self.json_path.exists():
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    return json.load(f) or {}
            except Exception as e:
                print(f"⚠️  JSON load failed, falling back to YAML: {e}")
                # Fall through to YAML loading

        # Fallback to YAML for compatibility
        return self._load_yaml_full()
    
    def get_entry(self, doc_id: str) -> Dict | None:
        """
        Get single entry - uses full YAML parsing for accuracy (handles lists, complex types)
        
        Args:
            doc_id: Document ID to look up
        
        Returns:
            Metadata dict if found, None otherwise
        """
        if not self.index_path.exists():
            return None
        
        # Use full YAML parsing to handle lists and complex types correctly
        # For single entry lookups, this is still fast enough
        try:
            index = self.load_all()
            return index.get(doc_id)
        except Exception as e:
            print(f"⚠️  Error reading entry {doc_id}: {e}")
            return None
    
    def list_entries(self) -> Iterator[tuple[str, Dict]]:
        """
        Iterator for all entries - uses full YAML parsing for accuracy (handles lists, complex types)
        
        Note: This loads the entire index into memory for accuracy. For very large files,
        consider using get_entry() for individual lookups instead.
        
        Yields:
            Tuples of (doc_id, metadata)
        """
        if not self.index_path.exists():
            return
        
        # Use full YAML parsing to handle lists and complex types correctly
        # The naive line-by-line parser cannot handle YAML lists (tags, keywords)
        # which causes tags to appear as empty strings
        try:
            index = self.load_all()
            for doc_id, metadata in index.items():
                yield (doc_id, metadata)
        except Exception as e:
            print(f"⚠️  Error loading entries: {e}")
    
    def get_entry_count(self) -> int:
        """
        Quick count of entries without loading full file
        
        Returns:
            Number of entries in index
        """
        if not self.index_path.exists():
            return 0
        
        count = 0
        try:
            with open(self.index_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Count entry keys (lines starting at column 0 with ':')
                    stripped = line.rstrip()
                    if stripped and not line.startswith(' ') and not line.startswith('\t'):
                        if ':' in stripped:
                            count += 1
        except Exception:
            # Fallback to full load
            index = self.load_all()
            return len(index)
        
        return count
    
    def search_entries(self, **filters) -> list[tuple[str, Dict]]:
        """
        Search entries by metadata fields
        
        Args:
            **filters: Field name and value pairs to filter by
        
        Returns:
            List of (doc_id, metadata) tuples matching filters
        """
        results = []
        
        for doc_id, metadata in self.list_entries():
            match = True
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                results.append((doc_id, metadata))
        
        return results
    
    def update_entry(self, doc_id: str, metadata: Dict) -> bool:
        """
        Update single entry with locking

        Args:
            doc_id: Document ID
            metadata: Metadata dictionary to update

        Returns:
            True if successful, False otherwise
        """
        # Acquire lock with retry
        if not self._acquire_lock_with_retry("update"):
            return False

        try:
            # Load existing index
            index = self.load_all()

            # Safety check: prevent writing empty index (data loss prevention)
            if not self._validate_index_not_empty(index, "update"):
                return False

            # Update entry
            index[doc_id] = metadata

            # Write to temporary file first, then rename (atomic write)
            temp_path = self.index_path.with_suffix('.yaml.tmp')
            try:
                if HAS_RUAMEL:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        self.yaml.dump(index, f)
                else:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        yaml.dump(index, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

                # Atomic rename with retry
                self._atomic_move_with_retry(temp_path, self.index_path)
                # Also save JSON for fast loading (>100x faster)
                self._save_json(index)
                return True
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        except Exception as e:
            print(f"❌ Error updating entry {doc_id}: {e}")
            return False

        finally:
            # Always release lock
            self._release_lock()

    def remove_entry(self, doc_id: str) -> bool:
        """
        Remove entry with locking

        Args:
            doc_id: Document ID to remove

        Returns:
            True if successful, False otherwise
        """
        # Acquire lock with retry
        if not self._acquire_lock_with_retry("remove"):
            return False

        try:
            # Load existing index
            index = self.load_all()

            # Safety check: prevent writing empty index (data loss prevention)
            if not self._validate_index_not_empty(index, "removal"):
                return False

            # Remove entry if exists
            if doc_id in index:
                del index[doc_id]
            else:
                return False  # Entry not found

            # Write to temporary file first, then rename (atomic write)
            temp_path = self.index_path.with_suffix('.yaml.tmp')
            try:
                if HAS_RUAMEL:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        self.yaml.dump(index, f)
                else:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        yaml.dump(index, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

                # Atomic rename with retry
                self._atomic_move_with_retry(temp_path, self.index_path)
                # Also save JSON for fast loading (>100x faster)
                self._save_json(index)
                return True
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        except Exception as e:
            print(f"❌ Error removing entry {doc_id}: {e}")
            return False

        finally:
            # Always release lock
            self._release_lock()
    
    def batch_update_entries(self, updates: dict[str, Dict]) -> bool:
        """
        Update multiple entries in a single operation (much faster than individual updates)

        Args:
            updates: Dictionary mapping doc_id -> metadata dict to update

        Returns:
            True if successful, False otherwise
        """
        if not updates:
            return True

        # Acquire lock with retry
        if not self._acquire_lock_with_retry("batch update"):
            return False

        try:
            # Load existing index once
            index = self.load_all()

            # Safety check: prevent writing empty index (data loss prevention)
            if not self._validate_index_not_empty(index, "batch update"):
                return False

            # Update all entries in memory with progress logging
            total_updates = len(updates)
            for i, (doc_id, metadata) in enumerate(updates.items()):
                # Progress logging for large batches
                if i > 0 and i % BATCH_PROGRESS_INTERVAL == 0:
                    pct = (i * 100) // total_updates
                    print(f"   Batch progress: {i}/{total_updates} entries ({pct}%)")

                # Merge with existing metadata if entry exists
                if doc_id in index:
                    existing = index[doc_id]
                    # Only update metadata fields, preserve critical fields like 'path', 'url', 'hash'
                    protected_fields = ['path', 'url', 'hash', 'last_fetched', 'source_type', 'sitemap_url']
                    for key, value in metadata.items():
                        # Only update if not a protected field, or if it's None/missing
                        if key not in protected_fields or existing.get(key) is None:
                            existing[key] = value
                    index[doc_id] = existing
                else:
                    index[doc_id] = metadata

            # Write to temporary file first, then rename (atomic write)
            temp_path = self.index_path.with_suffix('.yaml.tmp')
            try:
                if HAS_RUAMEL:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        self.yaml.dump(index, f)
                else:
                    with open(temp_path, 'w', encoding='utf-8') as f:
                        yaml.dump(index, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

                # Atomic rename with retry
                self._atomic_move_with_retry(temp_path, self.index_path)
                # Also save JSON for fast loading (>100x faster)
                self._save_json(index)
                return True
            except Exception as e:
                # Clean up temp file on error
                if temp_path.exists():
                    temp_path.unlink()
                raise e

        except Exception as e:
            print(f"❌ Error in batch update: {e}")
            return False

        finally:
            # Always release lock
            self._release_lock()
    
    def remove_entries_by_filter(self, **filters) -> int:
        """
        Remove multiple entries matching filters

        Args:
            **filters: Field name and value pairs to filter by

        Returns:
            Number of entries removed
        """
        # Find matching entries
        matching = self.search_entries(**filters)

        if not matching:
            return 0

        # Acquire lock with retry
        if not self._acquire_lock_with_retry("remove by filter"):
            return 0

        try:
            # Load existing index
            index = self.load_all()

            # Remove matching entries
            removed_count = 0
            for doc_id, _ in matching:
                if doc_id in index:
                    del index[doc_id]
                    removed_count += 1

            # Write back
            if HAS_RUAMEL:
                with open(self.index_path, 'w', encoding='utf-8') as f:
                    self.yaml.dump(index, f)
            else:
                with open(self.index_path, 'w', encoding='utf-8') as f:
                    yaml.dump(index, f, default_flow_style=False, sort_keys=True, allow_unicode=True)

            # Also save JSON for fast loading (>100x faster)
            self._save_json(index)

            return removed_count

        except Exception as e:
            print(f"❌ Error removing entries: {e}")
            return 0

        finally:
            # Always release lock
            self._release_lock()

    def regenerate_json(self) -> bool:
        """
        Regenerate JSON index from YAML (for migration or repair)

        This method loads the YAML index and saves it as JSON for fast loading.
        Use this after manual YAML edits or when the JSON file is missing/corrupted.

        Returns:
            True if successful, False otherwise
        """
        try:
            # Force load from YAML (bypass JSON even if it exists)
            index = self._load_yaml_full()

            if not index:
                print("⚠️  YAML index is empty, nothing to regenerate")
                return False

            # Save as JSON
            if self._save_json(index):
                print(f"✅ Regenerated index.json ({len(index)} entries)")
                return True
            else:
                print("❌ Failed to save index.json")
                return False

        except Exception as e:
            print(f"❌ Error regenerating JSON: {e}")
            return False

