"""
Tests for detect_changes.py script.
"""

from unittest.mock import patch, MagicMock


from tests.shared.test_utils import TempReferencesDir, create_mock_sitemap, create_mock_index_entry



class TestDetectChanges:
    """Test suite for detect_changes.py"""
    
    def test_detect_new_urls(self, temp_dir):
        """Test detection of new URLs in sitemap"""
        refs_dir = TempReferencesDir()
        try:
            # Create index with one URL
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md')
            }
            refs_dir.create_index(index)
            
            # Create sitemap with two URLs (one new)
            sitemap_content = create_mock_sitemap([
                'https://example.com/doc1',
                'https://example.com/doc2'  # New URL
            ])
            
            from scripts.maintenance.detect_changes import ChangeDetector
            
            detector = ChangeDetector(refs_dir.references_dir)
            sitemap_urls = detector.parse_sitemap(sitemap_content)
            indexed_urls = {'https://example.com/doc1': 'doc1'}
            
            new_urls, removed_urls = detector.detect_changes(sitemap_urls, indexed_urls)
            
            assert 'https://example.com/doc2' in new_urls
            assert len(new_urls) == 1
            assert len(removed_urls) == 0
        finally:
            refs_dir.cleanup()
    
    def test_detect_removed_urls(self, temp_dir):
        """Test detection of removed URLs from sitemap"""
        refs_dir = TempReferencesDir()
        try:
            # Create index with two URLs
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            # Create sitemap with one URL (one removed)
            sitemap_content = create_mock_sitemap([
                'https://example.com/doc1'
            ])
            
            from scripts.maintenance.detect_changes import ChangeDetector
            
            detector = ChangeDetector(refs_dir.references_dir)
            sitemap_urls = detector.parse_sitemap(sitemap_content)
            indexed_urls = {
                'https://example.com/doc1': 'doc1',
                'https://example.com/doc2': 'doc2'
            }
            
            new_urls, removed_urls = detector.detect_changes(sitemap_urls, indexed_urls)
            
            assert 'https://example.com/doc2' in removed_urls
            assert len(new_urls) == 0
            assert len(removed_urls) == 1
        finally:
            refs_dir.cleanup()
    
    @patch('scripts.maintenance.detect_changes.requests.Session')
    def test_check_404_urls(self, mock_session_class, temp_dir):
        """Test 404 URL detection"""
        refs_dir = TempReferencesDir()
        try:
            # Mock session with 404 response
            mock_session = MagicMock()
            mock_response_404 = MagicMock()
            mock_response_404.status_code = 404
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            
            # Create a function that returns different responses based on URL
            def head_side_effect(url, **kwargs):
                if '404' in url:
                    return mock_response_404
                else:
                    return mock_response_200
            
            mock_session.head.side_effect = head_side_effect
            mock_session_class.return_value = mock_session
            
            from scripts.maintenance.detect_changes import ChangeDetector
            
            detector = ChangeDetector(refs_dir.references_dir)
            urls = {'https://example.com/404', 'https://example.com/ok'}
            
            url_404s = detector.check_404_urls(urls, max_workers=1)
            
            assert url_404s['https://example.com/404'] is True
            assert url_404s['https://example.com/ok'] is False
        finally:
            refs_dir.cleanup()
    
    def test_generate_report(self, temp_dir):
        """Test report generation"""
        from scripts.maintenance.detect_changes import ChangeDetector
        
        refs_dir = TempReferencesDir()
        try:
            detector = ChangeDetector(refs_dir.references_dir)
            
            new_urls = {'https://example.com/new1', 'https://example.com/new2'}
            removed_urls = {'https://example.com/removed1'}
            indexed_urls = {
                'https://example.com/removed1': 'doc1',
                'https://example.com/existing': 'doc2'
            }
            
            report = detector.generate_report(new_urls, removed_urls, indexed_urls, 'test')
            
            assert 'New pages' in report
            assert 'Removed pages' in report
            assert 'https://example.com/new1' in report
            assert 'https://example.com/new2' in report
            assert 'https://example.com/removed1' in report
        finally:
            refs_dir.cleanup()
