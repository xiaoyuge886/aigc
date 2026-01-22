"""
Tests for config_helpers module.
"""
import tempfile
from unittest.mock import patch, MagicMock


from scripts.utils.config_helpers import (
    get_http_timeout,
    get_http_user_agent,
    get_management_user_agent,
    get_scraper_user_agent,
    get_scraping_rate_limit,
    get_scraping_max_workers,
    get_scraping_max_source_workers,
    get_index_chunk_size,
    get_validation_timeout,
    is_parallel_enabled,
    get_markdown_extension,
    get_drift_max_workers,
    get_drift_timeout,
    reload_configs,
)


class TestConfigHelpers:
    """Test suite for config_helpers module."""

    def test_get_http_timeout(self):
        """Test that get_http_timeout returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 60.0
            result = get_http_timeout()
            assert result == 60.0
            mock_get_default.assert_called_with('http', 'default_timeout', 30.0)

    def test_get_http_timeout_default(self):
        """Test that get_http_timeout returns default if config not available."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = None
            result = get_http_timeout()
            assert result == 30.0

    def test_get_http_user_agent(self):
        """Test that get_http_user_agent returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = "Custom-Agent/1.0"
            result = get_http_user_agent()
            assert result == "Custom-Agent/1.0"
            mock_get_default.assert_called_with('http', 'user_agent', "Claude-Docs-Scraper/1.0 (Educational purposes)")

    def test_get_management_user_agent(self):
        """Test that get_management_user_agent returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = "Custom-Management/1.0"
            result = get_management_user_agent()
            assert result == "Custom-Management/1.0"
            mock_get_default.assert_called_with('user_agents', 'management', "Claude-Docs-Management-Bot/1.0")

    def test_get_scraper_user_agent(self):
        """Test that get_scraper_user_agent returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = "Custom-Scraper/1.0"
            result = get_scraper_user_agent()
            assert result == "Custom-Scraper/1.0"
            mock_get_default.assert_called_with('user_agents', 'scraper', "Claude-Docs-Scraper/1.0 (Educational purposes)")

    def test_get_scraping_rate_limit(self):
        """Test that get_scraping_rate_limit returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 2.0
            result = get_scraping_rate_limit()
            assert result == 2.0
            mock_get_default.assert_called_with('scraping', 'rate_limit', 0.5)

    def test_get_scraping_max_workers(self):
        """Test that get_scraping_max_workers returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 5
            result = get_scraping_max_workers()
            assert result == 5
            mock_get_default.assert_called_with('scraping', 'max_workers', 4)

    def test_get_scraping_max_source_workers(self):
        """Test that get_scraping_max_source_workers returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 5
            result = get_scraping_max_source_workers()
            assert result == 5
            mock_get_default.assert_called_with('scraping', 'max_source_workers', 4)

    def test_get_index_chunk_size(self):
        """Test that get_index_chunk_size returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 2000
            result = get_index_chunk_size()
            assert result == 2000
            mock_get_default.assert_called_with('index', 'chunk_size', 1000)

    def test_get_validation_timeout(self):
        """Test that get_validation_timeout returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 120.0
            result = get_validation_timeout()
            assert result == 120.0
            mock_get_default.assert_called_with('validation', 'timeout', 60.0)

    def test_is_parallel_enabled(self):
        """Test that is_parallel_enabled returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = False
            result = is_parallel_enabled()
            assert result is False
            mock_get_default.assert_called_with('performance', 'parallel_enabled', True)

    def test_get_markdown_extension(self):
        """Test that get_markdown_extension returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = ".markdown"
            result = get_markdown_extension()
            assert result == ".markdown"
            mock_get_default.assert_called_with('files', 'markdown_extension', '.md')

    def test_get_drift_max_workers(self):
        """Test that get_drift_max_workers returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 10
            result = get_drift_max_workers()
            assert result == 10
            mock_get_default.assert_called_with('drift', 'max_workers', 5)

    def test_get_drift_max_workers_default(self):
        """Test that get_drift_max_workers uses default value from config."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 5  # Default value
            result = get_drift_max_workers()
            assert result == 5
            mock_get_default.assert_called_with('drift', 'max_workers', 5)

    def test_get_drift_timeout(self):
        """Test that get_drift_timeout returns config value."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 600.0
            result = get_drift_timeout()
            assert result == 600.0
            mock_get_default.assert_called_with('drift', 'timeout', 300.0)

    def test_get_drift_timeout_default(self):
        """Test that get_drift_timeout uses default value from config."""
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 300.0  # Default value
            result = get_drift_timeout()
            assert result == 300.0
            mock_get_default.assert_called_with('drift', 'timeout', 300.0)

    def test_reload_configs(self):
        """Test that reload_configs calls registry reload."""
        with patch('scripts.utils.config_helpers.get_registry') as mock_get_registry:
            mock_registry = MagicMock()
            mock_get_registry.return_value = mock_registry
            
            reload_configs()
            
            mock_registry.reload.assert_called_once()

    def test_get_sources_default_timeout(self):
        """Test that get_sources_default_timeout returns config value."""
        from scripts.utils.config_helpers import get_sources_default_timeout
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = 1800.0
            result = get_sources_default_timeout()
            assert result == 1800.0
            mock_get_default.assert_called_with('scraping', 'sources_default_timeout', 1800.0)

    def test_get_sources_default_timeout_fallback(self):
        """Test that get_sources_default_timeout uses fallback value."""
        from scripts.utils.config_helpers import get_sources_default_timeout
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            # get_default returns the default value (3rd arg) when config not found
            mock_get_default.return_value = 1800.0
            result = get_sources_default_timeout()
            assert result == 1800.0  # Fallback value
            mock_get_default.assert_called_with('scraping', 'sources_default_timeout', 1800.0)

    def test_get_output_dir_mapping(self):
        """Test that get_output_dir_mapping returns config value."""
        from scripts.utils.config_helpers import get_output_dir_mapping
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = {
                'docs.claude.com': 'docs-claude-com',
                'code.claude.com': 'code-claude-com'
            }
            result = get_output_dir_mapping('docs.claude.com')
            assert result == 'docs-claude-com'
            mock_get_default.assert_called_with('paths', 'output_dirs', {})

    def test_get_output_dir_mapping_not_found(self):
        """Test that get_output_dir_mapping uses smart fallback when domain not in config."""
        from scripts.utils.config_helpers import get_output_dir_mapping
        with patch('scripts.utils.config_helpers.get_default') as mock_get_default:
            mock_get_default.return_value = {
                'docs.claude.com': 'docs-claude-com'
            }
            # Smart fallback: strips www. and replaces dots with hyphens
            result = get_output_dir_mapping('unknown.com')
            assert result == 'unknown-com'

    def test_scrape_all_sources_smart_fallback(self):
        """Test that scrape_all_sources.py uses smart fallback for unconfigured domains."""
        from scripts.core.scrape_all_sources import MultiSourceScraper
        from pathlib import Path

        scraper = MultiSourceScraper(base_dir=Path(tempfile.gettempdir()) / 'test')

        # Source with unconfigured domain
        source = {
            'name': 'test-source',
            'type': 'sitemap',
            'url': 'https://unknown-domain.com/sitemap.xml'
        }

        # get_output_dir_mapping now uses smart fallback (strips www., replaces dots)
        output_dir = scraper._auto_detect_output_dir(source)
        assert output_dir == 'unknown-domain-com'

    def test_scrape_docs_smart_fallback(self):
        """Test that scrape_docs.py uses smart fallback for unconfigured domains."""
        from scripts.core.scrape_docs import DocScraper
        from pathlib import Path

        scraper = DocScraper(base_output_dir=Path(tempfile.gettempdir()) / 'test')

        # get_output_dir_mapping now uses smart fallback (strips www., replaces dots)
        output_dir = scraper.auto_detect_output_dir('https://unknown-domain.com/page')
        assert output_dir == 'unknown-domain-com'
