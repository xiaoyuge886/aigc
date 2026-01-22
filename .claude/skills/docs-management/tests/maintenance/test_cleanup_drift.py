"""
Tests for cleanup_drift.py script.
"""

from unittest.mock import patch, MagicMock


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestCleanupDrift:
    """Test suite for cleanup_drift.py"""
    
    def test_find_missing_files(self, temp_dir):
        """Test finding index entries with missing files"""
        refs_dir = TempReferencesDir()
        try:
            # Create index with entries, one missing file
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            # Create only one file (doc1 exists, doc2 is missing)
            # Note: create_doc creates files in domain/category subdirectory
            # But index path is 'test/doc1.md' which is relative to base_dir
            doc1_path = refs_dir.references_dir / 'test' / 'doc1.md'
            doc1_path.parent.mkdir(parents=True, exist_ok=True)
            doc1_path.write_text('# Doc 1', encoding='utf-8')
            
            from scripts.maintenance.cleanup_drift import DriftCleaner
            
            cleaner = DriftCleaner(refs_dir.references_dir, dry_run=True)
            missing = cleaner.find_missing_files(index)
            
            assert len(missing) == 1
            assert missing[0][0] == 'doc2'
        finally:
            refs_dir.cleanup()
    
    @patch('scripts.maintenance.cleanup_drift.requests.Session')
    def test_find_404_urls(self, mock_session_class, temp_dir):
        """Test finding documents with 404 source URLs"""
        refs_dir = TempReferencesDir()
        try:
            # Mock session with 404 response
            mock_session = MagicMock()
            mock_response_404 = MagicMock()
            mock_response_404.status_code = 404
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            
            mock_session.head.side_effect = [
                mock_response_404,  # First URL returns 404
                mock_response_200   # Second URL returns 200
            ]
            mock_session_class.return_value = mock_session
            
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/404', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/ok', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            from scripts.maintenance.cleanup_drift import DriftCleaner
            
            cleaner = DriftCleaner(refs_dir.references_dir, dry_run=True)
            url_404s = cleaner.find_404_urls(index, max_workers=1)
            
            assert len(url_404s) == 1
            assert url_404s[0][0] == 'doc1'
            assert url_404s[0][1] == 'https://example.com/404'
        finally:
            refs_dir.cleanup()
    
    def test_clean_missing_files_dry_run(self, temp_dir):
        """Test cleaning missing files in dry-run mode"""
        refs_dir = TempReferencesDir()
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            # Create only one file (doc1 exists, doc2 is missing)
            doc1_path = refs_dir.references_dir / 'test' / 'doc1.md'
            doc1_path.parent.mkdir(parents=True, exist_ok=True)
            doc1_path.write_text('# Doc 1', encoding='utf-8')
            
            from scripts.maintenance.cleanup_drift import DriftCleaner
            
            cleaner = DriftCleaner(refs_dir.references_dir, dry_run=True)
            files_checked, index_removed = cleaner.clean_missing_files(index)
            
            assert files_checked == 1
            # In dry-run mode, index_removed counts what would be removed (for reporting)
            # but no actual removals happen. The function returns the count for reporting purposes.
            assert index_removed == 1  # Would remove 1 entry in dry-run
        finally:
            refs_dir.cleanup()
    
    def test_generate_audit_log(self, temp_dir):
        """Test audit log generation"""
        refs_dir = TempReferencesDir()
        try:
            from scripts.maintenance.cleanup_drift import DriftCleaner
            
            cleaner = DriftCleaner(refs_dir.references_dir, dry_run=True)
            
            # Simulate some cleanup operations
            cleaner.cleanup_log = [
                {
                    'action': 'remove_file',
                    'doc_id': 'doc1',
                    'filepath': 'test/doc1.md',
                    'timestamp': '2025-01-01T00:00:00Z'
                },
                {
                    'action': 'remove_index_entry',
                    'doc_id': 'doc2',
                    'timestamp': '2025-01-01T00:00:00Z'
                }
            ]
            
            log = cleaner.generate_audit_log()
            
            assert 'Drift Cleanup Audit Log' in log
            assert 'Remove File' in log or 'remove_file' in log
            assert 'Remove Index Entry' in log or 'remove_index_entry' in log
            assert 'doc1' in log
            assert 'doc2' in log
        finally:
            refs_dir.cleanup()
