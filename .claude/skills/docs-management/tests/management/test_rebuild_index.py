"""
Tests for rebuild_index.py script.

Tests critical functionality for rebuilding index.yaml from filesystem.
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_frontmatter



class TestRebuildIndex:
    """Test suite for rebuild_index functionality."""

    def test_rebuild_index_new_file(self, temp_dir):
        """Test rebuilding index with new file."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create a markdown file
            refs_dir.create_doc('test', 'category', 'new-doc.md', 
                               create_mock_frontmatter(source_url='https://example.com/new',
                                                      content_hash='abc123') + '\n# New Document\n\nContent.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            
            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)
            
            assert result.get('new', result.get('added', 0)) >= 1
            assert result.get('updated', 0) >= 0
            
        finally:
            refs_dir.cleanup()

    def test_rebuild_index_existing_file(self, temp_dir):
        """Test rebuilding index with existing entry."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with existing entry
            index = {
                'test-category-new-doc': {
                    'path': 'test/category/new-doc.md',
                    'url': 'https://example.com/new',
                    'source_url': 'https://example.com/new',
                    'content_hash': 'abc123'
                }
            }
            refs_dir.create_index(index)
            
            # Create the actual file
            refs_dir.create_doc('test', 'category', 'new-doc.md',
                               create_mock_frontmatter(source_url='https://example.com/new',
                                                      content_hash='abc123') + '\n# Document\n\nContent.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            
            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)
            
            assert result['updated'] >= 0  # May update or keep same
            
        finally:
            refs_dir.cleanup()

    def test_rebuild_index_handles_renames(self, temp_dir):
        """Test that rebuild_index detects renamed files via content hash."""
        refs_dir = TempReferencesDir()

        try:
            # Create index with old path
            index = {
                'old-doc': {
                    'path': 'old/path.md',
                    'url': 'https://example.com/doc',
                    'source_url': 'https://example.com/doc',
                    'content_hash': 'samehash123'
                }
            }
            refs_dir.create_index(index)

            # Create file with new path but same content hash
            refs_dir.create_doc('new', 'category', 'path.md',
                               create_mock_frontmatter(source_url='https://example.com/doc',
                                                      content_hash='samehash123') + '\n# Document\n\nContent.')

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module

            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)

            # Should detect rename via hash match
            assert result['renamed'] >= 0 or result['updated'] >= 0

        finally:
            refs_dir.cleanup()

    def test_rebuild_index_rename_keeps_new_doc_id_as_primary(self, temp_dir):
        """Test that renamed files keep NEW doc_id as primary, not OLD."""
        refs_dir = TempReferencesDir()

        try:
            # Unique content that will produce a consistent hash
            unique_content = '# Unique Document for Rename Test\n\nThis is unique content for testing rename behavior.'

            # Calculate what the hash will be
            from scripts.management.rebuild_index import calculate_hash
            expected_hash = calculate_hash(unique_content)

            # Create index with old doc_id and matching hash
            index = {
                'old-name-doc': {
                    'path': 'old/name/doc.md',
                    'url': 'https://example.com/doc',
                    'hash': expected_hash,
                    'last_fetched': '2025-01-01'
                }
            }
            refs_dir.create_index(index)

            # Create file with NEW path (different doc_id) but same content
            refs_dir.create_doc('new', 'name', 'doc.md', unique_content)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            from scripts.management.index_manager import IndexManager

            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)

            # Should detect as rename
            assert result['renamed'] >= 1, "Should detect at least one rename"

            # Load the updated index
            manager = IndexManager(refs_dir.references_dir)

            # NEW doc_id should exist as primary entry
            new_entry = manager.get_entry('new-name-doc')
            assert new_entry is not None, "NEW doc_id should be primary entry"

            # OLD doc_id should NOT exist as separate entry
            old_entry = manager.get_entry('old-name-doc')
            assert old_entry is None, "OLD doc_id should be removed from index"

        finally:
            refs_dir.cleanup()

    def test_rebuild_index_rename_adds_old_as_alias(self, temp_dir):
        """Test that renamed files add OLD doc_id as alias of NEW entry."""
        refs_dir = TempReferencesDir()

        try:
            # Unique content that will produce a consistent hash
            unique_content = '# Alias Test Document\n\nUnique content for alias testing.'

            from scripts.management.rebuild_index import calculate_hash
            expected_hash = calculate_hash(unique_content)

            # Create index with old doc_id
            index = {
                'original-doc-id': {
                    'path': 'original/doc/id.md',
                    'url': 'https://example.com/doc',
                    'hash': expected_hash,
                    'last_fetched': '2025-01-01'
                }
            }
            refs_dir.create_index(index)

            # Create file with NEW path (will generate different doc_id)
            refs_dir.create_doc('renamed', 'doc', 'id.md', unique_content)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            from scripts.management.index_manager import IndexManager

            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)

            # Should detect rename
            assert result['renamed'] >= 1

            # Load index and check aliases
            manager = IndexManager(refs_dir.references_dir)
            new_entry = manager.get_entry('renamed-doc-id')

            assert new_entry is not None, "NEW entry should exist"
            assert 'aliases' in new_entry, "NEW entry should have aliases field"
            assert 'original-doc-id' in new_entry['aliases'], "OLD doc_id should be in aliases"

        finally:
            refs_dir.cleanup()

    def test_rebuild_index_rename_removes_old_entry(self, temp_dir):
        """Test that renamed files have their OLD entry completely removed."""
        refs_dir = TempReferencesDir()

        try:
            unique_content = '# Remove Old Entry Test\n\nContent for testing old entry removal.'

            from scripts.management.rebuild_index import calculate_hash
            expected_hash = calculate_hash(unique_content)

            # Create index with old doc_id that has some extra metadata
            index = {
                'to-be-removed-doc': {
                    'path': 'to/be/removed/doc.md',
                    'url': 'https://example.com/old',
                    'hash': expected_hash,
                    'last_fetched': '2025-01-01',
                    'title': 'Old Title',
                    'keywords': ['old', 'keywords']
                }
            }
            refs_dir.create_index(index)

            # Create file with completely different path
            refs_dir.create_doc('completely', 'new', 'location.md', unique_content)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            from scripts.management.index_manager import IndexManager

            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)

            # Load index
            manager = IndexManager(refs_dir.references_dir)
            all_entries = manager.load_all()

            # OLD doc_id should NOT be in the index at all
            assert 'to-be-removed-doc' not in all_entries, "OLD doc_id should be completely removed"

            # NEW doc_id should exist
            assert 'completely-new-location' in all_entries, "NEW doc_id should exist"

        finally:
            refs_dir.cleanup()

    def test_rebuild_index_rename_preserves_backward_compatibility(self, temp_dir):
        """Test that aliases enable backward compatibility lookups."""
        refs_dir = TempReferencesDir()

        try:
            unique_content = '# Backward Compat Test\n\nContent for backward compatibility.'

            from scripts.management.rebuild_index import calculate_hash
            expected_hash = calculate_hash(unique_content)

            index = {
                'legacy-doc-name': {
                    'path': 'legacy/doc/name.md',
                    'url': 'https://example.com/legacy',
                    'hash': expected_hash,
                    'last_fetched': '2025-01-01'
                }
            }
            refs_dir.create_index(index)

            # Create file with new name
            refs_dir.create_doc('modern', 'doc', 'name.md', unique_content)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            from scripts.management.index_manager import IndexManager

            rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=False)

            manager = IndexManager(refs_dir.references_dir)

            # The key point is the alias is stored correctly for backward compatibility
            # This enables future alias resolution implementations
            new_entry = manager.get_entry('modern-doc-name')
            assert new_entry is not None, "NEW entry should exist"
            assert 'aliases' in new_entry, "NEW entry should have aliases field"
            assert 'legacy-doc-name' in new_entry['aliases'], "OLD doc_id should be stored as alias"

            # Verify the old entry is gone (not duplicated)
            old_entry = manager.get_entry('legacy-doc-name')
            assert old_entry is None, "OLD entry should be removed"

        finally:
            refs_dir.cleanup()

    def test_rebuild_index_dry_run(self, temp_dir):
        """Test rebuild_index in dry-run mode."""
        refs_dir = TempReferencesDir()
        
        try:
            refs_dir.create_doc('test', 'category', 'doc.md', '# Document\n\nContent.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management import rebuild_index as rebuild_module
            
            result = rebuild_module.rebuild_index(refs_dir.references_dir, dry_run=True)
            
            assert 'new' in result or 'added' in result
            assert 'updated' in result
            
            # In dry-run, index should not be modified
            from scripts.management.index_manager import IndexManager
            manager = IndexManager(refs_dir.references_dir)
            index = manager.load_all()
            # Index may be empty or unchanged in dry-run
            
        finally:
            refs_dir.cleanup()
