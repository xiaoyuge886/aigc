"""
Tests for validate_index_vs_docs.py script.

Tests the validate_index_vs_docs.py script for validating index metadata against docs.
"""

import sys
from pathlib import Path

import pytest


class TestValidateIndexVsDocs:
    """Test suite for validate_index_vs_docs.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act & Assert
        try:
            from scripts.validation import validate_index_vs_docs
            assert True
        except ImportError:
            pytest.fail("validate_index_vs_docs.py could not be imported")

    def test_validation_function_exists(self):
        """Test that validation function exists."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act
        from scripts.validation import validate_index_vs_docs

        # Assert
        assert hasattr(validate_index_vs_docs, 'main') and callable(validate_index_vs_docs.main)
