"""
Tests for refresh_index.py script.

Tests the refresh_index.py orchestration script for refreshing the index.
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir



class TestRefreshIndex:
    """Test suite for refresh_index.py orchestration."""

    def test_step_functions_exist(self):
        """Test that all step functions exist."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        from scripts.management.refresh_index import (
            step_check_dependencies,
            step_rebuild_index,
            step_extract_keywords,
            step_validate_metadata,
            step_generate_report
        )
        
        assert callable(step_check_dependencies)
        assert callable(step_rebuild_index)
        assert callable(step_extract_keywords)
        assert callable(step_validate_metadata)
        assert callable(step_generate_report)

    def test_check_missing_files_function(self, temp_dir):
        """Test check_missing_files function."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.refresh_index import check_missing_files
            
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            result = check_missing_files(scripts_dir, refs_dir.references_dir, cleanup=False)
            
            assert isinstance(result, bool)
            
        finally:
            refs_dir.cleanup()

    def test_detect_drift_function(self, temp_dir):
        """Test detect_drift function."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.management.refresh_index import detect_drift
            
            scripts_dir = Path(__file__).parent.parent / 'scripts'
            result = detect_drift(scripts_dir, refs_dir.references_dir, cleanup=False, max_workers=1)
            
            assert isinstance(result, bool)
            
        finally:
            refs_dir.cleanup()
