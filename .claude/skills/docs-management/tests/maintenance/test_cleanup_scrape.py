"""
Tests for cleanup_scrape.py script.

Tests the cleanup_scrape.py script for cleaning up failed scrape directories.

Refactored to use refs_dir fixture for automatic cleanup, eliminating try/finally patterns.
See tests/conftest.py for fixture definition.
"""

import sys
from pathlib import Path

import pytest


class TestCleanupScrape:
    """Test suite for cleanup_scrape.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        try:
            from scripts.maintenance import cleanup_scrape
            assert True
        except ImportError:
            pytest.fail("cleanup_scrape.py could not be imported")

    def test_cleanup_failed_scrape_function_exists(self, refs_dir):
        """Test that cleanup_failed_scrape function exists."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_scrape import cleanup_failed_scrape

        # Should be callable
        assert callable(cleanup_failed_scrape)

    def test_cleanup_failed_scrape_dry_run(self, refs_dir):
        """Test cleanup_failed_scrape in dry-run mode."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_scrape import cleanup_failed_scrape

        # Create output directory with markdown files
        output_dir = refs_dir.references_dir / 'docs-claude-com' / 'docs'
        output_dir.mkdir(parents=True)

        # Create test markdown files
        (output_dir / 'test1.md').write_text('# Test 1')
        (output_dir / 'test2.md').write_text('# Test 2')
        (output_dir / 'subdir').mkdir()
        (output_dir / 'subdir' / 'test3.md').write_text('# Test 3')

        # Run cleanup in dry-run mode
        result = cleanup_failed_scrape(output_dir, dry_run=True, require_confirm=False)

        # Should succeed
        assert result is True

        # Files should still exist (dry-run)
        assert (output_dir / 'test1.md').exists()
        assert (output_dir / 'test2.md').exists()
        assert (output_dir / 'subdir' / 'test3.md').exists()

    def test_cleanup_failed_scrape_nonexistent_directory(self, refs_dir):
        """Test cleanup_failed_scrape with nonexistent directory."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_scrape import cleanup_failed_scrape

        # Try to cleanup nonexistent directory
        nonexistent_dir = refs_dir.references_dir / 'nonexistent'
        result = cleanup_failed_scrape(nonexistent_dir, dry_run=True, require_confirm=False)

        # Should return False
        assert result is False

    def test_cleanup_failed_scrape_empty_directory(self, refs_dir):
        """Test cleanup_failed_scrape with empty directory."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_scrape import cleanup_failed_scrape

        # Create empty directory
        output_dir = refs_dir.references_dir / 'empty-dir'
        output_dir.mkdir(parents=True)

        # Run cleanup
        result = cleanup_failed_scrape(output_dir, dry_run=True, require_confirm=False)

        # Should succeed (no files to delete)
        assert result is True

    def test_cleanup_failed_scrape_no_markdown_files(self, refs_dir):
        """Test cleanup_failed_scrape with directory containing no markdown files."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_scrape import cleanup_failed_scrape

        # Create directory with non-markdown files
        output_dir = refs_dir.references_dir / 'no-md-dir'
        output_dir.mkdir(parents=True)
        (output_dir / 'test.txt').write_text('test')
        (output_dir / 'test.yaml').write_text('test: value')

        # Run cleanup
        result = cleanup_failed_scrape(output_dir, dry_run=True, require_confirm=False)

        # Should succeed (no markdown files found)
        assert result is True
