"""
Tests for validate_scraped_docs.py script.

Tests the validate_scraped_docs.py script for validating scraped documentation.
"""

import sys
from pathlib import Path

import pytest


class TestValidateScrapedDocs:
    """Test suite for validate_scraped_docs.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act & Assert
        try:
            from scripts.validation import validate_scraped_docs
            assert True
        except ImportError:
            pytest.fail("validate_scraped_docs.py could not be imported")

    def test_validation_function_exists(self, refs_dir):
        """Test that validation function exists."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        from scripts.validation.validate_scraped_docs import ScrapedDocsValidator

        # Act
        validator = ScrapedDocsValidator(refs_dir.references_dir)

        # Assert
        assert validator is not None
