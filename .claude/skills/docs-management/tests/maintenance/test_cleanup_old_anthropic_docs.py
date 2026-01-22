"""
Tests for cleanup_old_anthropic_docs.py script.

Tests the cleanup_old_anthropic_docs.py script for removing old Anthropic documentation.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta


import pytest
from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestCleanupOldAnthropicDocs:
    """Test suite for cleanup_old_anthropic_docs.py."""

    def test_script_imports(self):
        """Test that script can be imported."""
        sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
        
        try:
            from scripts.maintenance import cleanup_old_anthropic_docs
            assert True
        except ImportError:
            pytest.fail("cleanup_old_anthropic_docs.py could not be imported")

    def test_cleanup_old_docs_function_exists(self, temp_dir):
        """Test that cleanup_old_docs function exists."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.maintenance.cleanup_old_anthropic_docs import cleanup_old_docs
            
            # Should not raise
            result = cleanup_old_docs(refs_dir.references_dir, max_age_days=365, dry_run=True)
            assert isinstance(result, int)
            
        finally:
            refs_dir.cleanup()

    def test_cleanup_old_docs_dry_run(self):
        """Test cleanup_old_docs in dry-run mode."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.maintenance.cleanup_old_anthropic_docs import cleanup_old_docs
            
            # Create old doc entry
            old_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
            index = {
                'test-doc': create_mock_index_entry(
                    'test-doc',
                    'https://anthropic.com/test',
                    'anthropic-com/test.md',
                    domain='anthropic.com',
                    category='engineering',
                    published_at=old_date
                )
            }
            
            # Create index file
            refs_dir.create_index(index)
            
            # Create doc file
            refs_dir.create_doc('anthropic-com', 'engineering', 'test.md', '# Test')
            
            # Run cleanup in dry-run mode
            result = cleanup_old_docs(refs_dir.references_dir, max_age_days=365, dry_run=True)
            
            # Should return 0 (success) in dry-run
            assert result == 0
            
            # File should still exist (dry-run)
            doc_file = refs_dir.references_dir / 'anthropic-com' / 'engineering' / 'test.md'
            assert doc_file.exists()
            
        finally:
            refs_dir.cleanup()

    def test_cleanup_old_docs_skips_recent_docs(self):
        """Test that recent docs are not cleaned up."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.maintenance.cleanup_old_anthropic_docs import cleanup_old_docs
            
            # Create recent doc entry
            recent_date = (datetime.now() - timedelta(days=100)).strftime('%Y-%m-%d')
            index = {
                'test-doc': create_mock_index_entry(
                    'test-doc',
                    'https://anthropic.com/test',
                    'anthropic-com/test.md',
                    domain='anthropic.com',
                    category='engineering',
                    published_at=recent_date
                )
            }
            
            refs_dir.create_index(index)
            refs_dir.create_doc('anthropic-com', 'engineering', 'test.md', '# Test')
            
            # Run cleanup
            result = cleanup_old_docs(refs_dir.references_dir, max_age_days=365, dry_run=True)
            
            # Should return 0 (no old docs found)
            assert result == 0
            
        finally:
            refs_dir.cleanup()

    def test_cleanup_old_docs_skips_non_anthropic_docs(self):
        """Test that non-Anthropic docs are not cleaned up."""
        refs_dir = TempReferencesDir()
        
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.maintenance.cleanup_old_anthropic_docs import cleanup_old_docs
            
            # Create old doc entry for non-Anthropic domain
            old_date = (datetime.now() - timedelta(days=400)).strftime('%Y-%m-%d')
            index = {
                'test-doc': create_mock_index_entry(
                    'test-doc',
                    'https://docs.claude.com/test',
                    'docs-claude-com/test.md',
                    domain='docs.claude.com',
                    category='api',
                    published_at=old_date
                )
            }
            
            refs_dir.create_index(index)
            refs_dir.create_doc('docs-claude-com', 'api', 'test.md', '# Test')
            
            # Run cleanup
            result = cleanup_old_docs(refs_dir.references_dir, max_age_days=365, dry_run=True)
            
            # Should return 0 (no Anthropic docs found)
            assert result == 0
            
        finally:
            refs_dir.cleanup()
