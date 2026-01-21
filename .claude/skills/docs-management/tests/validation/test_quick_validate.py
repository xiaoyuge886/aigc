"""
Tests for quick_validate.py script.

Tests the quick_validate.py script for quick validation of scraped docs.
"""

import sys
from pathlib import Path

import pytest


class TestQuickValidate:
    """Test suite for quick_validate.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act & Assert
        try:
            from scripts.validation import quick_validate
            assert True
        except ImportError:
            pytest.fail("quick_validate.py could not be imported")

    def test_validation_function_exists(self):
        """Test that validation function exists."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act
        from scripts.validation import quick_validate

        # Assert
        assert hasattr(quick_validate, 'quick_validate') and callable(quick_validate.quick_validate)
