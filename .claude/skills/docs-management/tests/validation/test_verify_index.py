"""
Tests for verify_index.py script.

Tests the verify_index.py script for verifying index integrity.
"""

import sys
from pathlib import Path

import pytest
from tests.shared.test_utils import create_mock_index_entry


class TestVerifyIndex:
    """Test suite for verify_index.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        # Arrange
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act & Assert
        try:
            from scripts.validation import verify_index
            assert True
        except ImportError:
            pytest.fail("verify_index.py could not be imported")

    def test_verification_function_exists(self, refs_dir):
        """Test that verification function exists."""
        # Arrange
        index = {
            'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md')
        }
        refs_dir.create_index(index)
        refs_dir.create_doc('test', 'category', 'doc1.md', '# Doc1\n\nContent.')
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

        # Act
        from scripts.validation import verify_index

        # Assert
        assert hasattr(verify_index, 'main') and callable(verify_index.main)
