"""
Tests for cleanup_stale.py script.

Tests the cleanup_stale.py script for marking stale entries.
"""

import sys
from pathlib import Path

import pytest


class TestCleanupStale:
    """Test suite for cleanup_stale.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act & Assert
        try:
            from scripts.maintenance import cleanup_stale
            assert True
        except ImportError:
            pytest.fail("cleanup_stale.py could not be imported")

    def test_mark_stale_function_exists(self, refs_dir):
        """Test that StaleCleanup class exists."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.maintenance.cleanup_stale import StaleCleanup

        # Act
        cleanup = StaleCleanup(refs_dir.references_dir)

        # Assert
        assert cleanup is not None
