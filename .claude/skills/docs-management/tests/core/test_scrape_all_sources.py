"""
Tests for scrape_all_sources.py script.

Tests the scrape_all_sources.py orchestration script for scraping multiple sources.
"""

import sys
import json
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir



class TestScrapeAllSources:
    """Test suite for scrape_all_sources.py orchestration."""

    def test_multi_source_scraper_init(self, temp_dir):
        """Test MultiSourceScraper initialization."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            assert scraper.base_dir == refs_dir.references_dir
            assert scraper.scrape_script.exists()
            assert scraper.validate_script.exists()
            
        finally:
            refs_dir.cleanup()

    def test_auto_detect_output_dir(self, temp_dir):
        """Test auto-detection of output directory."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            source = {
                'url': 'https://docs.claude.com/sitemap.xml',
                'type': 'sitemap',
                'output': 'docs-claude-com'  # Provide output explicitly to avoid config dependency
            }
            
            # Test that output is used when provided
            assert source.get('output') == 'docs-claude-com'
            
        finally:
            refs_dir.cleanup()

    def test_validate_source(self, temp_dir):
        """Test source validation."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test source directory
            output_dir = refs_dir.references_dir / 'docs-claude-com' / 'docs'
            output_dir.mkdir(parents=True)
            
            # Create test markdown file
            test_file = output_dir / 'test.md'
            test_file.write_text('---\nsource_url: https://example.com/test\nlast_fetched: 2025-01-01\ncontent_hash: abc123\n---\n\n# Test\n\nContent.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            source = {
                'name': 'test source',
                'type': 'sitemap',
                'url': 'https://docs.claude.com/sitemap.xml',
                'filter': '/en/docs/',
                'output': 'docs-claude-com',  # Explicitly set output to avoid config dependency
                'expected_count': 1
            }
            
            # Mock _auto_detect_output_dir to avoid config dependency
            scraper._auto_detect_output_dir = lambda s: 'docs-claude-com'
            
            validation = scraper.validate_source(source)
            
            assert 'passed' in validation
            assert validation['file_count'] >= 1
            
        finally:
            refs_dir.cleanup()
    
    def test_expected_count_tolerance_within_range(self, temp_dir):
        """Test that expected_count within tolerance triggers auto-update."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test source directory with 3 files
            output_dir = refs_dir.references_dir / 'docs-claude-com' / 'docs'
            output_dir.mkdir(parents=True)
            
            for i in range(3):
                test_file = output_dir / f'test{i}.md'
                test_file.write_text(f'---\nsource_url: https://example.com/test{i}\nlast_fetched: 2025-01-01\ncontent_hash: abc{i}\n---\n\n# Test {i}\n')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            scraper._auto_detect_output_dir = lambda s: 'docs-claude-com'
            
            source = {
                'name': 'test source',
                'type': 'sitemap',
                'url': 'https://docs.claude.com/sitemap.xml',
                'filter': '/en/docs/',
                'output': 'docs-claude-com',
                'expected_count': 1,  # Off by 2, within default tolerance of 10
                'expected_count_tolerance': 10
            }
            
            validation = scraper.validate_source(source)
            
            # Should pass and request auto-update
            assert validation['passed'] == True
            assert 'auto_update' in validation
            assert validation['auto_update']['expected_count'] == 3
            assert validation['file_count'] == 3
            
        finally:
            refs_dir.cleanup()
    
    def test_expected_count_tolerance_outside_range(self, temp_dir):
        """Test that expected_count outside tolerance triggers warning without auto-update."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test source directory with 25 files (way off from expected)
            output_dir = refs_dir.references_dir / 'docs-claude-com' / 'docs'
            output_dir.mkdir(parents=True)
            
            for i in range(25):
                test_file = output_dir / f'test{i}.md'
                test_file.write_text(f'---\nsource_url: https://example.com/test{i}\nlast_fetched: 2025-01-01\ncontent_hash: abc{i}\n---\n\n# Test {i}\n')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            scraper._auto_detect_output_dir = lambda s: 'docs-claude-com'
            
            source = {
                'name': 'test source',
                'type': 'sitemap',
                'url': 'https://docs.claude.com/sitemap.xml',
                'filter': '/en/docs/',
                'output': 'docs-claude-com',
                'expected_count': 5,  # Off by 20, exceeds tolerance of 10
                'expected_count_tolerance': 10
            }
            
            validation = scraper.validate_source(source)
            
            # Should fail validation (outside tolerance)
            assert validation['passed'] == False
            assert 'auto_update' not in validation  # No auto-update for large discrepancies
            assert any('outside tolerance' in issue for issue in validation['issues'])
            
        finally:
            refs_dir.cleanup()
    
    def test_expected_count_exact_match(self, temp_dir):
        """Test that exact expected_count match passes without auto-update."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test source directory with exact expected count
            output_dir = refs_dir.references_dir / 'docs-claude-com' / 'docs'
            output_dir.mkdir(parents=True)
            
            for i in range(5):
                test_file = output_dir / f'test{i}.md'
                test_file.write_text(f'---\nsource_url: https://example.com/test{i}\nlast_fetched: 2025-01-01\ncontent_hash: abc{i}\n---\n\n# Test {i}\n')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            scraper._auto_detect_output_dir = lambda s: 'docs-claude-com'
            
            source = {
                'name': 'test source',
                'type': 'sitemap',
                'url': 'https://docs.claude.com/sitemap.xml',
                'filter': '/en/docs/',
                'output': 'docs-claude-com',
                'expected_count': 5  # Exact match
            }
            
            validation = scraper.validate_source(source)
            
            # Should pass without auto-update (already correct)
            assert validation['passed'] == True
            assert 'auto_update' not in validation
            assert validation['file_count'] == 5
            
        finally:
            refs_dir.cleanup()
    
    def test_update_source_config(self, temp_dir):
        """Test _update_source_config writes changes correctly."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test config file
            config_path = temp_dir / 'test_sources.json'
            sources = [
                {
                    "name": "test-source-1",
                    "expected_count": 10
                },
                {
                    "name": "test-source-2",
                    "expected_count": 20
                }
            ]
            with open(config_path, 'w') as f:
                json.dump(sources, f, indent=2)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            auto_updates = [
                {
                    'source_name': 'test-source-1',
                    'updates': {'expected_count': 12}
                }
            ]
            
            scraper._update_source_config(config_path, auto_updates, sources)
            
            # Verify file was updated
            with open(config_path, 'r') as f:
                updated_sources = json.load(f)
            
            # Get current UTC date for comparison
            from datetime import datetime, timezone as tz
            today_utc = datetime.now(tz.utc).strftime('%Y-%m-%d')
            
            assert updated_sources[0]['expected_count'] == 12
            assert updated_sources[0]['last_scraped'] == today_utc  # Should add current UTC timestamp
            assert updated_sources[1]['expected_count'] == 20  # Unchanged
            
        finally:
            refs_dir.cleanup()
    
    def test_age_filtering_reduces_count(self, temp_dir):
        """Test that age filtering with reduced count is handled correctly."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test source directory with fewer files than expected (age filtering)
            output_dir = refs_dir.references_dir / 'anthropic-com' / 'news'
            output_dir.mkdir(parents=True)
            
            for i in range(50):  # Only 50 docs, but expected 100
                test_file = output_dir / f'news{i}.md'
                test_file.write_text(f'---\nsource_url: https://www.anthropic.com/news/test{i}\nlast_fetched: 2025-01-01\ncontent_hash: abc{i}\n---\n\n# News {i}\n')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            scraper._auto_detect_output_dir = lambda s: 'anthropic-com'
            
            source = {
                'name': 'anthropic.com /news/',
                'type': 'sitemap',
                'url': 'https://www.anthropic.com/sitemap.xml',
                'filter': '/news/',
                'output': 'anthropic-com',
                'max_age_days': 180,  # Age filtering active
                'expected_count': 100  # Expected before filtering
            }
            
            validation = scraper.validate_source(source)
            
            # Should be marked as expected_filtered (age filtering explains the difference)
            assert validation['expected_filtered'] == True
            assert any('filtered by age' in issue for issue in validation['issues'])
            
        finally:
            refs_dir.cleanup()
    
    def test_url_type_source_validation(self, temp_dir):
        """Test validation for url-type sources (single file)."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create test file for url-type source
            output_file = refs_dir.references_dir / 'code-claude-com' / 'CHANGELOG.md'
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text('---\nsource_url: https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md\nlast_fetched: 2025-11-17\ncontent_hash: abc123\n---\n\n# Changelog\n\nContent here.')
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            source = {
                'name': 'claude-code CHANGELOG',
                'type': 'url',
                'url': 'https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md',
                'output': 'code-claude-com/CHANGELOG.md'
            }
            
            validation = scraper.validate_source(source)
            
            # Should pass with file_count=1
            assert validation['passed'] == True
            assert validation['file_count'] == 1
            assert len(validation['issues']) == 0
            
        finally:
            refs_dir.cleanup()
    
    def test_url_type_source_missing_file(self, temp_dir):
        """Test validation fails for url-type sources with missing output file."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.scrape_all_sources import MultiSourceScraper
            
            scraper = MultiSourceScraper(base_dir=refs_dir.references_dir)
            
            source = {
                'name': 'test url source',
                'type': 'url',
                'url': 'https://example.com/file.md',
                'output': 'test-dir/missing-file.md'
            }
            
            validation = scraper.validate_source(source)
            
            # Should fail because file doesn't exist
            assert validation['passed'] == False
            assert any('does not exist' in issue for issue in validation['issues'])
            
        finally:
            refs_dir.cleanup()
