"""
Tests for manage_index.py CLI script.

Tests the manage_index.py command-line interface for managing index.yaml.
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestManageIndexCLI:
    """Test suite for manage_index.py CLI commands."""

    def test_cmd_get(self, temp_dir):
        """Test get command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md',
                                                    title='Test Document')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_get
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cmd_get(manager, 'test-doc')
            
            output = f.getvalue()
            assert 'test-doc' in output
            assert 'Test Document' in output or 'test/doc.md' in output
            
        finally:
            refs_dir.cleanup()

    def test_cmd_update(self, temp_dir):
        """Test update command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_update
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import json
            metadata_json = json.dumps({'title': 'Updated Title'})
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cmd_update(manager, 'test-doc', metadata_json)
            
            output = f.getvalue()
            assert 'Updated' in output
            
            # Verify update
            entry = manager.get_entry('test-doc')
            assert entry['title'] == 'Updated Title'
            
        finally:
            refs_dir.cleanup()

    def test_cmd_remove(self, temp_dir):
        """Test remove command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_remove
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cmd_remove(manager, 'test-doc')
            
            output = f.getvalue()
            assert 'Removed' in output
            
            # Verify removal
            entry = manager.get_entry('test-doc')
            assert entry is None
            
        finally:
            refs_dir.cleanup()

    def test_cmd_list(self, temp_dir):
        """Test list command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_list
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cmd_list(manager, {}, limit=None)
            
            output = f.getvalue()
            assert 'doc1' in output
            assert 'doc2' in output
            
        finally:
            refs_dir.cleanup()

    def test_cmd_count(self, temp_dir):
        """Test count command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md'),
                'doc3': create_mock_index_entry('doc3', 'https://example.com/doc3', 'test/doc3.md')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_count
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                cmd_count(manager)
            
            output = f.getvalue()
            assert '3' in output or 'entries' in output.lower()
            
        finally:
            refs_dir.cleanup()

    def test_cmd_verify(self, temp_dir):
        """Test verify command."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index entry with all required fields for verification
            index = {
                'doc1': {
                    'path': 'test/category/doc1.md',
                    'url': 'https://example.com/doc1',
                    'hash': 'abc123',
                    'last_fetched': '2025-01-01',
                    'source_url': 'https://example.com/doc1'
                }
            }
            refs_dir.create_index(index)
            refs_dir.create_doc('test', 'category', 'doc1.md', '# Doc1\n\nContent.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.manage_index import cmd_verify
            from scripts.management.index_manager import IndexManager
            
            manager = IndexManager(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_verify(manager, refs_dir.references_dir)
                except SystemExit:
                    pass  # cmd_verify exits with code 1 if issues found, 0 if OK
            
            output = f.getvalue()
            assert 'verify' in output.lower() or 'integrity' in output.lower() or 'verification' in output.lower()
            
        finally:
            refs_dir.cleanup()
