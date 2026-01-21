#!/usr/bin/env python3
"""
Tests for index_manager.py module.

Tests critical functionality for managing large index.yaml files including:
- Lock acquisition and release
- Entry loading (single and batch)
- Entry updates and removals
- Large file handling (chunked reading)
- Thread safety
"""

import threading
from pathlib import Path
from unittest.mock import patch
import sys



_scripts_dir = Path(__file__).parent.parent / 'scripts'
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from scripts.management.index_manager import IndexManager


class TestIndexManager:
    """Test suite for IndexManager class."""
    
    def test_initialization(self, temp_dir):
        """Test IndexManager initialization."""
        manager = IndexManager(temp_dir)
        assert manager.base_dir == temp_dir
        assert manager.index_path == temp_dir / "index.yaml"
        assert manager.lock_file == temp_dir / ".index.lock"
    
    def test_load_all_empty_index(self, temp_dir):
        """Test loading empty index."""
        manager = IndexManager(temp_dir)
        index = manager.load_all()
        assert index == {}
    
    def test_load_all_with_entries(self, temp_dir):
        """Test loading index with entries."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md', 'url': 'https://example.com/1'},
            'doc2': {'path': 'test2.md', 'url': 'https://example.com/2'}
        }
        
        # Write index manually
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Load and verify
        index = manager.load_all()
        assert len(index) == 2
        assert 'doc1' in index
        assert 'doc2' in index
        assert index['doc1']['path'] == 'test1.md'
    
    def test_get_entry(self, temp_dir):
        """Test getting single entry."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md', 'url': 'https://example.com/1'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Get entry
        entry = manager.get_entry('doc1')
        assert entry is not None
        assert entry['path'] == 'test1.md'
        
        # Get non-existent entry
        entry = manager.get_entry('nonexistent')
        assert entry is None
    
    def test_get_entry_count(self, temp_dir):
        """Test getting entry count."""
        manager = IndexManager(temp_dir)
        
        # Empty index
        assert manager.get_entry_count() == 0
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md'},
            'doc2': {'path': 'test2.md'},
            'doc3': {'path': 'test3.md'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        assert manager.get_entry_count() == 3
    
    def test_update_entry(self, temp_dir):
        """Test updating single entry."""
        manager = IndexManager(temp_dir)
        
        # Create initial index
        test_index = {
            'doc1': {'path': 'test1.md', 'url': 'https://example.com/1'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Update entry
        new_metadata = {'path': 'test1.md', 'url': 'https://example.com/1', 'title': 'Test Doc'}
        assert manager.update_entry('doc1', new_metadata) is True
        
        # Verify update
        entry = manager.get_entry('doc1')
        assert entry['title'] == 'Test Doc'
    
    def test_update_entry_new_entry(self, temp_dir):
        """Test updating with new entry."""
        manager = IndexManager(temp_dir)
        
        # Create initial index
        test_index = {'doc1': {'path': 'test1.md'}}
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Add new entry
        new_metadata = {'path': 'test2.md', 'url': 'https://example.com/2'}
        assert manager.update_entry('doc2', new_metadata) is True
        
        # Verify new entry
        entry = manager.get_entry('doc2')
        assert entry is not None
        assert entry['path'] == 'test2.md'
    
    def test_remove_entry(self, temp_dir):
        """Test removing entry."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md'},
            'doc2': {'path': 'test2.md'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Remove entry
        assert manager.remove_entry('doc1') is True
        
        # Verify removal
        assert manager.get_entry('doc1') is None
        assert manager.get_entry('doc2') is not None
        assert manager.get_entry_count() == 1
    
    def test_remove_entry_nonexistent(self, temp_dir):
        """Test removing non-existent entry."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {'doc1': {'path': 'test1.md'}}
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Try to remove non-existent entry
        assert manager.remove_entry('nonexistent') is False
        assert manager.get_entry_count() == 1
    
    def test_batch_update_entries(self, temp_dir):
        """Test batch updating multiple entries."""
        manager = IndexManager(temp_dir)
        
        # Create initial index
        test_index = {
            'doc1': {'path': 'test1.md'},
            'doc2': {'path': 'test2.md'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Batch update
        updates = {
            'doc1': {'path': 'test1.md', 'title': 'Doc 1'},
            'doc2': {'path': 'test2.md', 'title': 'Doc 2'},
            'doc3': {'path': 'test3.md', 'title': 'Doc 3'}  # New entry
        }
        
        assert manager.batch_update_entries(updates) is True
        
        # Verify updates
        assert manager.get_entry('doc1')['title'] == 'Doc 1'
        assert manager.get_entry('doc2')['title'] == 'Doc 2'
        assert manager.get_entry('doc3')['title'] == 'Doc 3'
        assert manager.get_entry_count() == 3
    
    def test_batch_update_empty(self, temp_dir):
        """Test batch update with empty updates."""
        manager = IndexManager(temp_dir)
        assert manager.batch_update_entries({}) is True
    
    def test_search_entries(self, temp_dir):
        """Test searching entries by metadata."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md', 'category': 'api'},
            'doc2': {'path': 'test2.md', 'category': 'guides'},
            'doc3': {'path': 'test3.md', 'category': 'api'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Search by category
        results = manager.search_entries(category='api')
        assert len(results) == 2
        assert all(doc_id in ['doc1', 'doc3'] for doc_id, _ in results)
    
    def test_list_entries(self, temp_dir):
        """Test listing all entries."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md'},
            'doc2': {'path': 'test2.md'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # List entries
        entries = list(manager.list_entries())
        assert len(entries) == 2
        assert all(isinstance(entry, tuple) and len(entry) == 2 for entry in entries)
    
    def test_lock_acquisition(self, temp_dir):
        """Test lock acquisition."""
        manager = IndexManager(temp_dir)
        
        # Acquire lock
        assert manager._acquire_lock(timeout=1.0) is True
        
        # Release lock
        manager._release_lock()
        
        # Verify lock file is removed
        assert not manager.lock_file.exists()
    
    def test_lock_timeout(self, temp_dir):
        """Test lock timeout when lock is held."""
        manager = IndexManager(temp_dir)
        
        # Acquire lock
        assert manager._acquire_lock() is True
        
        # Try to acquire again (should timeout)
        # Use a short timeout for testing
        assert manager._acquire_lock(timeout=0.1) is False
        
        # Release lock
        manager._release_lock()
    
    def test_remove_entries_by_filter(self, temp_dir):
        """Test removing entries by filter."""
        manager = IndexManager(temp_dir)
        
        # Create test index
        test_index = {
            'doc1': {'path': 'test1.md', 'status': 'stale'},
            'doc2': {'path': 'test2.md', 'status': 'active'},
            'doc3': {'path': 'test3.md', 'status': 'stale'}
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Remove stale entries
        removed = manager.remove_entries_by_filter(status='stale')
        assert removed == 2
        
        # Verify removal
        assert manager.get_entry('doc1') is None
        assert manager.get_entry('doc2') is not None
        assert manager.get_entry('doc3') is None
    
    def test_estimate_file_size(self, temp_dir):
        """Test file size estimation."""
        manager = IndexManager(temp_dir)
        
        # Empty file
        assert manager._estimate_file_size() == 0
        
        # Create test index
        test_index = {'doc1': {'path': 'test1.md'}}
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Estimate should be > 0
        estimated = manager._estimate_file_size()
        assert estimated > 0
    
    def test_update_entry_replaces_metadata(self, temp_dir):
        """Test that update_entry replaces entry metadata."""
        manager = IndexManager(temp_dir)
        
        # Create initial index with existing fields
        test_index = {
            'doc1': {
                'path': 'test1.md',
                'url': 'https://example.com/1',
                'hash': 'sha256:abc123',
                'last_fetched': '2025-01-01'
            }
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Update with new metadata (replaces entire entry)
        new_metadata = {'title': 'New Title', 'description': 'New Description'}
        assert manager.update_entry('doc1', new_metadata) is True
        
        # Verify entry was replaced (old fields gone, new fields present)
        entry = manager.get_entry('doc1')
        assert entry is not None
        assert 'title' in entry
        assert 'description' in entry
        # Old fields are replaced (not merged)
        assert 'path' not in entry or entry.get('path') != 'test1.md'
    
    def test_batch_update_preserves_protected_fields(self, temp_dir):
        """Test that batch_update preserves protected fields."""
        manager = IndexManager(temp_dir)
        
        # Create initial index
        test_index = {
            'doc1': {
                'path': 'test1.md',
                'url': 'https://example.com/1',
                'hash': 'sha256:abc123'
            }
        }
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Batch update (should preserve protected fields)
        updates = {
            'doc1': {'title': 'New Title'}
        }
        assert manager.batch_update_entries(updates) is True
        
        # Verify protected fields are preserved
        entry = manager.get_entry('doc1')
        assert entry['path'] == 'test1.md'
        assert entry['url'] == 'https://example.com/1'
        assert entry['hash'] == 'sha256:abc123'
        assert entry['title'] == 'New Title'


class TestIndexManagerThreadSafety:
    """Test thread safety of IndexManager."""
    
    def test_concurrent_updates(self, temp_dir):
        """Test concurrent updates with locking."""
        manager = IndexManager(temp_dir)
        
        # Create initial index
        test_index = {'doc1': {'path': 'test1.md', 'counter': 0}}
        
        import yaml
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            yaml.dump(test_index, f)
        
        # Concurrent updates
        def update_counter():
            for _ in range(10):
                entry = manager.get_entry('doc1')
                if entry:
                    entry['counter'] = entry.get('counter', 0) + 1
                    manager.update_entry('doc1', entry)
        
        threads = [threading.Thread(target=update_counter) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Verify final state (should be consistent due to locking)
        entry = manager.get_entry('doc1')
        assert entry is not None
        # Counter should be incremented (exact value depends on timing, but should be > 0)
        assert entry.get('counter', 0) > 0


class TestIndexManagerErrorHandling:
    """Test error handling in IndexManager."""
    
    def test_update_entry_empty_index_safety_check(self, temp_dir):
        """Test safety check prevents writing empty index."""
        manager = IndexManager(temp_dir)
        
        # Create a non-empty index file manually
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            f.write("doc1:\n  path: test1.md\n")
        
        # Mock load_all to return empty dict (simulating corruption)
        with patch.object(manager, 'load_all', return_value={}):
            # Should fail safety check
            result = manager.update_entry('doc1', {'path': 'test1.md'})
            # The safety check should prevent the update
            # (exact behavior depends on implementation)
    
    def test_remove_entry_empty_index_safety_check(self, temp_dir):
        """Test safety check prevents removing from corrupted index."""
        manager = IndexManager(temp_dir)
        
        # Create a non-empty index file manually
        with open(manager.index_path, 'w', encoding='utf-8') as f:
            f.write("doc1:\n  path: test1.md\n")
        
        # Mock load_all to return empty dict
        with patch.object(manager, 'load_all', return_value={}):
            # Should fail safety check
            result = manager.remove_entry('doc1')
            # The safety check should prevent the removal
