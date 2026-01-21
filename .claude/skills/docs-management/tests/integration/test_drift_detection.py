"""
Tests for drift detection functionality.
"""
from unittest.mock import patch, MagicMock


import pytest


# Import modules to test
try:
    from scripts.maintenance.cleanup_drift import DriftCleaner
    from scripts.maintenance.detect_changes import ChangeDetector
    DRIFT_MODULES_AVAILABLE = True
except ImportError:
    DRIFT_MODULES_AVAILABLE = False


@pytest.mark.skipif(not DRIFT_MODULES_AVAILABLE, reason="Drift detection modules not available")
class TestDriftDetection:
    """Test suite for drift detection functionality."""

    @pytest.fixture
    def mock_index(self, temp_dir):
        """Create a mock index.yaml structure."""
        index = {
            "doc-1": {
                "path": "docs-claude-com/docs/doc1.md",
                "url": "https://docs.claude.com/en/docs/doc1",
                "source_url": "https://docs.claude.com/en/docs/doc1",
                "content_hash": "abc123"
            },
            "doc-2": {
                "path": "docs-claude-com/docs/doc2.md",
                "url": "https://docs.claude.com/en/docs/doc2",
                "source_url": "https://docs.claude.com/en/docs/doc2",
                "content_hash": "def456"
            },
            "doc-3": {
                "path": "docs-claude-com/api/doc3.md",
                "url": "https://docs.claude.com/en/api/doc3",
                "source_url": "https://docs.claude.com/en/api/doc3",
                "content_hash": "ghi789"
            }
        }
        return index

    @pytest.fixture
    def base_dir_with_files(self, temp_dir, mock_index):
        """Create a base directory with some files matching index."""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create some files that exist
        (base_dir / "docs-claude-com" / "docs").mkdir(parents=True, exist_ok=True)
        (base_dir / "docs-claude-com" / "docs" / "doc1.md").write_text("# Doc 1")
        
        # doc2.md is missing (drift case)
        # doc3.md exists
        (base_dir / "docs-claude-com" / "api").mkdir(parents=True, exist_ok=True)
        (base_dir / "docs-claude-com" / "api" / "doc3.md").write_text("# Doc 3")
        
        return base_dir

    def test_find_missing_files(self, base_dir_with_files, mock_index):
        """Test that find_missing_files detects missing files."""
        cleaner = DriftCleaner(base_dir_with_files, dry_run=True)
        
        missing = cleaner.find_missing_files(mock_index)
        
        # doc2.md should be missing
        assert len(missing) == 1
        assert missing[0][0] == "doc-2"
        assert "doc2.md" in str(missing[0][1])

    def test_find_missing_files_no_missing(self, temp_dir):
        """Test that find_missing_files returns empty list when all files exist."""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        index = {
            "doc-1": {
                "path": "docs-claude-com/docs/doc1.md",
                "url": "https://docs.claude.com/en/docs/doc1"
            }
        }
        
        # Create the file
        (base_dir / "docs-claude-com" / "docs").mkdir(parents=True, exist_ok=True)
        (base_dir / "docs-claude-com" / "docs" / "doc1.md").write_text("# Doc 1")
        
        cleaner = DriftCleaner(base_dir, dry_run=True)
        missing = cleaner.find_missing_files(index)
        
        assert len(missing) == 0

    @patch('scripts.maintenance.cleanup_drift.requests.Session')
    def test_check_url_404(self, mock_session_class, temp_dir):
        """Test that check_url_404 correctly identifies 404 URLs."""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock session with 404 response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        cleaner = DriftCleaner(base_dir, dry_run=True)
        
        is_404 = cleaner.check_url_404("https://example.com/404")
        
        assert is_404 is True
        mock_session.head.assert_called_once()

    @patch('scripts.maintenance.cleanup_drift.requests.Session')
    def test_check_url_404_not_404(self, mock_session_class, temp_dir):
        """Test that check_url_404 correctly identifies non-404 URLs."""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Mock session with 200 response
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.head.return_value = mock_response
        mock_session_class.return_value = mock_session
        
        cleaner = DriftCleaner(base_dir, dry_run=True)
        
        is_404 = cleaner.check_url_404("https://example.com/ok")
        
        assert is_404 is False

    def test_cleanup_drift_dry_run(self, base_dir_with_files, mock_index):
        """Test that cleanup_drift in dry-run mode doesn't actually remove files."""
        cleaner = DriftCleaner(base_dir_with_files, dry_run=True)
        
        # File should still exist after dry-run cleanup
        doc2_path = base_dir_with_files / "docs-claude-com" / "docs" / "doc2.md"
        assert not doc2_path.exists()  # File doesn't exist (missing)
        
        # In dry-run, we should detect but not remove
        missing = cleaner.find_missing_files(mock_index)
        assert len(missing) == 1

    def test_drift_cleaner_initialization(self, temp_dir):
        """Test that DriftCleaner initializes correctly."""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        cleaner = DriftCleaner(base_dir, dry_run=True)
        
        assert cleaner.base_dir == base_dir
        assert cleaner.dry_run is True
        assert cleaner.cleanup_log == []
    
    def test_hash_mismatch_marks_stale(self, temp_dir, mock_index):
        """Test that hash mismatches mark docs as stale in index"""
        base_dir = temp_dir / ".claude" / "references"
        base_dir.mkdir(parents=True, exist_ok=True)
        
        # Create index with IndexManager
        from scripts.management.index_manager import IndexManager
        manager = IndexManager(base_dir)
        for doc_id, entry in mock_index.items():
            manager.update_entry(doc_id, entry)
        
        # Create file with different content (hash mismatch)
        doc1_path = base_dir / "docs-claude-com" / "docs" / "doc1.md"
        doc1_path.parent.mkdir(parents=True, exist_ok=True)
        doc1_path.write_text("# Doc 1 - Modified Content", encoding='utf-8')
        
        # Mock remote hash that differs from local
        detector = ChangeDetector(base_dir)
        # compare_content_hashes expects {url: doc_id} format
        indexed_urls = {"https://docs.claude.com/en/docs/doc1": "doc-1"}
        
        with patch('scripts.maintenance.detect_changes.fetch_with_retry') as mock_fetch:
            # Mock remote content with different hash
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.content = b"# Doc 1 - Remote Content"
            mock_fetch.return_value = mock_response
            
            hash_comparisons = detector.compare_content_hashes(indexed_urls, "docs-claude-com")
            
            # Check that doc was marked as stale
            entry = manager.get_entry("doc-1")
            assert entry is not None
            assert entry.get('stale') is True
            assert entry.get('stale_reason') == 'content_hash_mismatch'
            assert 'stale_detected' in entry
