"""
Tests for check_dependencies.py script.

Tests the check_dependencies.py script for verifying dependencies.
"""

import sys
from pathlib import Path


import pytest



class TestCheckDependencies:
    """Test suite for check_dependencies.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        # Should not raise ImportError
        try:
            from scripts.setup import check_dependencies
            assert True
        except ImportError:
            pytest.fail("check_dependencies.py could not be imported")

    def test_check_import_function(self):
        """Test check_import function."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        from scripts.setup.check_dependencies import check_import
        
        # Test checking for a module that should exist
        is_available, message = check_import('sys', 'sys')
        assert is_available is True
        
        # Test checking for a module that doesn't exist
        is_available, message = check_import('nonexistent_module_xyz', 'nonexistent_module_xyz')
        assert is_available is False
