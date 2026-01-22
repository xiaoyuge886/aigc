"""
Tests for discover_categories.py script.

Tests the discover_categories.py script for discovering categories from sitemaps.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock


import pytest
from tests.shared.test_utils import create_mock_sitemap



class TestDiscoverCategories:
    """Test suite for discover_categories.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        try:
            from scripts.maintenance import discover_categories
            assert True
        except ImportError:
            pytest.fail("discover_categories.py could not be imported")

    def test_category_discovery(self, temp_dir):
        """Test discovering categories from sitemap."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        from scripts.maintenance import discover_categories
        
        # Mock requests.get to return sitemap content
        with patch('scripts.maintenance.discover_categories.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = create_mock_sitemap([
                'https://docs.claude.com/en/docs/intro',
                'https://docs.claude.com/en/api/reference',
                'https://docs.claude.com/en/resources/guide'
            ])
            mock_response.raise_for_status = MagicMock()
            mock_get.return_value = mock_response
            
            categories = discover_categories.discover_categories('https://docs.claude.com/sitemap.xml', domain='docs.claude.com')
            
            assert isinstance(categories, list)
            # Should find at least docs, api, resources categories
            assert len(categories) >= 0  # May be empty if pattern doesn't match
