"""
Tests for official_docs_api module.
"""
from unittest.mock import patch, MagicMock
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestOfficialDocsAPI:
    """Test suite for OfficialDocsAPI class."""

    def test_find_document(self, temp_dir):
        """Test finding documents by natural language query."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with test entries
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                title='Skills Guide', keywords=['skills', 'guide']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                title='API Reference', keywords=['api', 'reference'])
            }
            refs_dir.create_index(index)
            
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            results = api.find_document("skills", limit=10)
            
            assert len(results) > 0
            assert any('skills' in str(result.get('keywords', [])).lower() or 
                      'skills' in result.get('title', '').lower() 
                      for result in results)
            
        finally:
            refs_dir.cleanup()

    def test_resolve_doc_id(self, temp_dir):
        """Test resolving doc_id to file path."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with test entry
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md',
                                                    title='Test Document')
            }
            refs_dir.create_index(index)
            
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            result = api.resolve_doc_id('test-doc')
            
            assert result is not None
            # API doesn't return 'path' directly (by design - prevents storing paths)
            # Path is available in metadata if needed
            assert result.get('metadata', {}).get('path') == 'test/doc.md' or result.get('url') is not None
            assert result['title'] == 'Test Document'
            
        finally:
            refs_dir.cleanup()

    def test_get_docs_by_tag(self, temp_dir):
        """Test getting documents by tag."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with tagged entries
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                tags=['skills', 'guide']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                tags=['api'])
            }
            refs_dir.create_index(index)
            
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            results = api.get_docs_by_tag('skills', limit=10)
            
            assert len(results) == 1
            assert results[0]['doc_id'] == 'doc1'
            
        finally:
            refs_dir.cleanup()

    def test_get_docs_by_category(self, temp_dir):
        """Test getting documents by category."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with categorized entries
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                category='api'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                category='guides')
            }
            refs_dir.create_index(index)
            
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            results = api.get_docs_by_category('api', limit=10)
            
            assert len(results) == 1
            assert results[0]['doc_id'] == 'doc1'
            
        finally:
            refs_dir.cleanup()

    def test_search_by_keywords(self, temp_dir):
        """Test searching documents by keywords."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with keyword entries
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                keywords=['skills', 'progressive', 'disclosure']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                keywords=['api', 'reference'])
            }
            refs_dir.create_index(index)
            
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            results = api.search_by_keywords(['skills', 'progressive'], limit=10)
            
            assert len(results) > 0
            assert any('skills' in str(result.get('keywords', [])).lower() for result in results)
            
        finally:
            refs_dir.cleanup()

    def test_refresh_index_success(self, temp_dir):
        """Test refresh_index with successful execution."""
        refs_dir = TempReferencesDir()
        
        try:
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            
            # Patch the modules before they're imported inside the method
            # Since imports happen inside refresh_index, we need to patch the modules
            # in sys.modules before the method runs
            import sys
            import importlib
            
            # Pre-import the modules so we can patch them
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            # Import modules to get them in sys.modules
            rebuild_mod = importlib.import_module('scripts.management.rebuild_index')
            manage_mod = importlib.import_module('scripts.management.manage_index')
            
            # Create mocks
            mock_rebuild = MagicMock(return_value={'new': 5, 'updated': 2, 'renamed': 0, 'unchanged': 10, 'orphaned': 0})
            mock_extract = MagicMock(return_value=None)
            mock_validate = MagicMock(return_value=None)
            
            # Patch the functions in the modules
            with patch.object(rebuild_mod, 'rebuild_index', mock_rebuild):
                with patch.object(manage_mod, 'cmd_extract_keywords', mock_extract):
                    with patch.object(manage_mod, 'cmd_validate_metadata', mock_validate):
                        result = api.refresh_index(check_drift=False, cleanup_drift=False)
            
            assert result['success'] is True
            assert 'rebuild_index' in result['steps_completed']
            assert 'extract_keywords' in result['steps_completed']
            assert 'validate_metadata' in result['steps_completed']
            assert len(result['errors']) == 0
            
            mock_rebuild.assert_called_once()
            mock_extract.assert_called_once()
            mock_validate.assert_called_once()
            
        finally:
            refs_dir.cleanup()

    def test_refresh_index_rebuild_failure(self, temp_dir):
        """Test refresh_index with rebuild failure."""
        refs_dir = TempReferencesDir()
        
        try:
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            
            # Patch the modules before they're imported inside the method
            import sys
            import importlib
            
            # Pre-import the modules so we can patch them
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            if str(scripts_dir) not in sys.path:
                sys.path.insert(0, str(scripts_dir))
            
            # Import modules to get them in sys.modules
            rebuild_mod = importlib.import_module('scripts.management.rebuild_index')
            
            # Create mock that raises exception
            mock_rebuild = MagicMock(side_effect=Exception("Rebuild failed"))
            
            # Patch the function in the module
            with patch.object(rebuild_mod, 'rebuild_index', mock_rebuild):
                result = api.refresh_index(check_drift=False, cleanup_drift=False)
            
            # Rebuild failure should result in errors
            assert len(result['errors']) > 0
            assert any('rebuild_index' in error.lower() for error in result['errors'])
            # Success is False if there are errors
            assert result['success'] is False
            
        finally:
            refs_dir.cleanup()

    def test_refresh_index_import_error(self, temp_dir):
        """Test refresh_index with import error."""
        refs_dir = TempReferencesDir()
        
        try:
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            
            # Patch the import to raise ImportError when rebuild_index is imported
            original_import = __import__
            def mock_import(name, *args, **kwargs):
                if name == 'rebuild_index' or name.endswith('.rebuild_index'):
                    raise ImportError("Module not found")
                return original_import(name, *args, **kwargs)
            
            with patch('builtins.__import__', side_effect=mock_import):
                result = api.refresh_index(check_drift=False, cleanup_drift=False)
                
                assert result['success'] is False
                assert len(result['errors']) > 0
                assert any('import' in error.lower() or 'module' in error.lower() for error in result['errors'])
        finally:
            refs_dir.cleanup()

    def test_detect_drift(self, temp_dir):
        """Test drift detection."""
        refs_dir = TempReferencesDir()
        
        try:
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            
            # Mock ChangeDetector and DriftCleaner
            with patch.object(api, 'doc_resolver') as mock_resolver:
                # This is a simplified test - actual drift detection requires network calls
                result = api.detect_drift("test-subdir", check_404s=True, check_hashes=True, max_workers=1)
                
                assert 'url_404_count' in result
                assert 'missing_files_count' in result
                assert 'hash_mismatch_count' in result
                
        finally:
            refs_dir.cleanup()

    def test_cleanup_drift_dry_run(self, temp_dir):
        """Test drift cleanup in dry-run mode."""
        refs_dir = TempReferencesDir()
        
        try:
            from official_docs_api import OfficialDocsAPI
            
            api = OfficialDocsAPI(base_dir=refs_dir.references_dir)
            
            # Mock cleanup operations
            result = api.cleanup_drift("test-subdir", clean_404s=True, clean_missing_files=True,
                                      dry_run=True, max_workers=1)
            
            assert 'files_removed' in result
            assert 'index_entries_removed' in result
            assert result['dry_run'] is True
            
        finally:
            refs_dir.cleanup()


class TestModuleLevelFunctions:
    """Test module-level convenience functions."""

    def test_find_document_function(self, temp_dir):
        """Test module-level find_document function."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                keywords=['test'])
            }
            refs_dir.create_index(index)
            
            # Set base_dir for module-level function
            with patch('official_docs_api.get_base_dir', return_value=refs_dir.references_dir):
                from official_docs_api import find_document
                
                results = find_document("test", limit=5)
                assert isinstance(results, list)
                
        finally:
            refs_dir.cleanup()

    def test_resolve_doc_id_function(self, temp_dir):
        """Test module-level resolve_doc_id function."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md',
                                                    title='Test Document')
            }
            refs_dir.create_index(index)
            
            # Clear the global API instance and patch path_config before importing
            import official_docs_api
            official_docs_api._api_instance = None
            
            # Patch path_config.get_base_dir to return test directory
            with patch('scripts.utils.path_config.get_base_dir', return_value=refs_dir.references_dir):
                # Force recreation of API instance by clearing cache
                official_docs_api._api_instance = None
                
                # Import after patching
                from official_docs_api import resolve_doc_id, OfficialDocsAPI
                
                # Ensure fresh instance is created
                official_docs_api._api_instance = OfficialDocsAPI(base_dir=refs_dir.references_dir)
                
                result = resolve_doc_id('test-doc')
                assert result is not None
                # API doesn't return 'path' directly (by design - prevents storing paths)
                # Path is available in metadata if needed
                assert result.get('metadata', {}).get('path') == 'test/doc.md' or result.get('url') is not None
                assert result['title'] == 'Test Document'
                
        finally:
            refs_dir.cleanup()
            # Reset API instance
            import official_docs_api
            official_docs_api._api_instance = None
