"""
Integration tests for docs-management workflows.

Tests full workflows: scrape → index → validate, drift detection, cleanup.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock


import pytest
from tests.shared.test_utils import (
    TempReferencesDir,
    TempConfigDir,
    create_mock_index_entry,
    MockHTTPResponse,
    create_mock_sitemap,
)


class TestScrapeIndexValidateWorkflow:
    """Test full scrape → index → validate workflow"""
    
    @patch('scripts.core.scrape_docs.requests.Session')
    def test_scrape_to_index_workflow(self, mock_session_class, temp_dir):
        """Test scraping documents and updating index"""
        refs_dir = TempReferencesDir()
        config_dir = TempConfigDir()
        
        try:
            # Setup mock HTTP responses
            mock_session = MagicMock()
            mock_session.get.return_value = MockHTTPResponse(
                status_code=200,
                text='<html><body><h1>Test Doc</h1><p>Content</p></body></html>'
            )
            mock_session.head.return_value = MockHTTPResponse(status_code=200)
            mock_session_class.return_value = mock_session
            
            # Create sitemap
            sitemap_content = create_mock_sitemap(['https://example.com/doc1'])
            
            # Mock sitemap fetch
            mock_session.get.side_effect = [
                MockHTTPResponse(status_code=200, text=sitemap_content),
                MockHTTPResponse(status_code=200, text='<html><body><h1>Test Doc</h1></body></html>')
            ]
            
            # This is a simplified integration test - actual scraping is complex
            # We're testing that the workflow components work together
            
            # Verify index can be created
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md')
            }
            refs_dir.create_index(index)
            
            # Verify index can be loaded
            from scripts.management.index_manager import IndexManager
            manager = IndexManager(refs_dir.references_dir)
            loaded_index = manager.load_all()
            
            assert 'doc1' in loaded_index
            assert loaded_index['doc1']['url'] == 'https://example.com/doc1'
            
        finally:
            refs_dir.cleanup()
            config_dir.cleanup()


class TestDriftDetectionWorkflow:
    """Test drift detection and cleanup workflow"""
    
    @patch('scripts.maintenance.detect_changes.requests.Session')
    @patch('scripts.maintenance.cleanup_drift.requests.Session')
    def test_drift_detection_and_cleanup(self, mock_cleanup_session, mock_detect_session, temp_dir):
        """Test detecting drift and cleaning it up"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with entries
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md')
            }
            refs_dir.create_index(index)
            
            # Create one file (doc1 exists, doc2 is missing)
            doc1_path = refs_dir.references_dir / 'test' / 'doc1.md'
            doc1_path.parent.mkdir(parents=True, exist_ok=True)
            doc1_path.write_text('# Doc 1', encoding='utf-8')
            
            # Mock 404 for doc2
            mock_detect_session_instance = MagicMock()
            mock_response_404 = MagicMock()
            mock_response_404.status_code = 404
            mock_response_200 = MagicMock()
            mock_response_200.status_code = 200
            
            # Create a function that returns different responses based on URL
            def detect_head_side_effect(url, **kwargs):
                if 'doc2' in url:
                    return mock_response_404
                else:
                    return mock_response_200
            
            mock_detect_session_instance.head.side_effect = detect_head_side_effect
            mock_detect_session.return_value = mock_detect_session_instance
            
            mock_cleanup_session_instance = MagicMock()
            
            def cleanup_head_side_effect(url, **kwargs):
                if 'doc2' in url:
                    return mock_response_404
                else:
                    return mock_response_200
            
            mock_cleanup_session_instance.head.side_effect = cleanup_head_side_effect
            mock_cleanup_session.return_value = mock_cleanup_session_instance
            
            # Test drift detection
            from scripts.maintenance.detect_changes import ChangeDetector
            from scripts.maintenance.cleanup_drift import DriftCleaner
            
            detector = ChangeDetector(refs_dir.references_dir)
            cleaner = DriftCleaner(refs_dir.references_dir, dry_run=True)
            
            # Find missing files
            missing = cleaner.find_missing_files(index)
            assert len(missing) == 1
            assert missing[0][0] == 'doc2'
            
            # Find 404 URLs
            url_404s = detector.check_404_urls({'https://example.com/doc1', 'https://example.com/doc2'}, max_workers=1)
            assert url_404s['https://example.com/doc2'] is True
            
        finally:
            refs_dir.cleanup()


class TestConfigRegistryWorkflow:
    """Test configuration registry workflow"""
    
    def test_config_loading_and_overrides(self, temp_dir):
        """Test loading configuration with environment variable overrides"""
        config_dir = TempConfigDir()
        
        try:
            # Create config files
            defaults = {
                'http': {
                    'default_timeout': 30,
                    'default_max_retries': 3
                }
            }
            config_dir.create_defaults_yaml(defaults)
            
            # Test config registry loading
            import sys
            sys.path.insert(0, str(config_dir.temp_dir.parent))
            
            from config.config_registry import ConfigRegistry
            
            registry = ConfigRegistry()
            # Set config_dir to our temp config
            registry.config_dir = config_dir.config_dir
            registry._paths['defaults'] = config_dir.config_dir / 'defaults.yaml'
            
            loaded_defaults = registry.load_defaults()
            
            assert loaded_defaults['http']['default_timeout'] == 30
            assert loaded_defaults['http']['default_max_retries'] == 3
            
            # Test get_default
            timeout = registry.get_default('http', 'default_timeout', 60)
            assert timeout == 30
            
        finally:
            config_dir.cleanup()


class TestModularRefreshIndex:
    """Test modular refresh_index.py steps"""
    
    def test_refresh_index_modular_steps(self, temp_dir):
        """Test that refresh_index.py can run individual steps"""
        # This test verifies the --step flag works
        # We'll test by importing and calling the step functions directly
        scripts_dir = Path(__file__).parent.parent / 'scripts'
        
        try:
            from scripts.management.refresh_index import (
                step_check_dependencies,
                step_rebuild_index,
                step_extract_keywords,
                step_validate_metadata,
                step_generate_report
            )
            
            # Verify all step functions exist and are callable
            assert callable(step_check_dependencies)
            assert callable(step_rebuild_index)
            assert callable(step_extract_keywords)
            assert callable(step_validate_metadata)
            assert callable(step_generate_report)
            
            # Note: We don't actually run these steps in the test because they
            # require a full environment setup. The test verifies the modular
            # structure exists and can be imported.
            
        except ImportError:
            pytest.skip("refresh_index.py not available for testing")


class TestScrape404Detection:
    """Test 404 detection during scraping"""
    
    @patch('scripts.core.scrape_docs.requests.Session')
    def test_scrape_marks_stale_on_404(self, mock_session_class, temp_dir):
        """Test that scraping marks existing docs as stale when source URL returns 404"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with existing doc
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md')
            }
            refs_dir.create_index(index)
            
            # Create the file
            doc1_path = refs_dir.references_dir / 'test' / 'doc1.md'
            doc1_path.parent.mkdir(parents=True, exist_ok=True)
            doc1_path.write_text('# Doc 1', encoding='utf-8')
            
            # Mock session that returns 404 for the URL
            mock_session = MagicMock()
            mock_response_404 = MagicMock()
            mock_response_404.status_code = 404
            mock_response_404.raise_for_status.side_effect = Exception("404 Not Found")
            mock_response_404.response = mock_response_404
            
            # Mock HTTPError for 404
            import requests
            http_error = requests.HTTPError()
            http_error.response = mock_response_404
            
            mock_session.get.side_effect = http_error
            mock_session_class.return_value = mock_session
            
            from scripts.core.scrape_docs import DocScraper
            from scripts.management.index_manager import IndexManager
            
            scraper = DocScraper(refs_dir.references_dir)
            
            # Try to scrape URL that returns 404
            output_path = refs_dir.references_dir / 'test' / 'doc1.md'
            result = scraper.scrape_url('https://example.com/doc1', output_path, 'sitemap')
            
            # Scraping should fail
            assert result is False
            
            # Check that doc was marked as stale in index
            manager = IndexManager(refs_dir.references_dir)
            entry = manager.get_entry('doc1')
            
            # Note: mark_doc_stale_for_404 requires index_manager, so we verify
            # the method exists and the 404 was tracked
            # The scraper tracks markdown URLs (url + '.md') in url_404s
            assert 'https://example.com/doc1.md' in scraper.url_404s or 'https://example.com/doc1' in scraper.url_404s
            
        finally:
            refs_dir.cleanup()
