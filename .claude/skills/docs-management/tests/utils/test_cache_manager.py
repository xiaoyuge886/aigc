"""
Tests for cache_manager module.
"""
import json
import hashlib
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from scripts.utils.cache_manager import (
    CacheManager,
    compute_file_hash,
    compute_plugin_fingerprint,
    CACHE_FORMAT_VERSION,
    INVERTED_INDEX_CACHE,
    CACHE_VERSION_FILE,
    LLMS_CACHE_DIR,
    MANIFEST_STATE_FILE,
)

# Mock plugin fingerprint for tests to avoid dependency on actual script content
MOCK_PLUGIN_FINGERPRINT = "sha256:test_fingerprint"


class TestComputeFileHash:
    """Test suite for compute_file_hash function."""

    def test_compute_file_hash_returns_sha256_format(self, tmp_path):
        """Test that hash is returned in sha256:<hex> format."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        result = compute_file_hash(test_file)

        assert result.startswith("sha256:")
        assert len(result) == 7 + 64  # "sha256:" + 64 hex chars

    def test_compute_file_hash_deterministic(self, tmp_path):
        """Test that same content produces same hash."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        hash1 = compute_file_hash(test_file)
        hash2 = compute_file_hash(test_file)

        assert hash1 == hash2

    def test_compute_file_hash_different_content_different_hash(self, tmp_path):
        """Test that different content produces different hash."""
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file1.write_text("content 1", encoding="utf-8")
        file2.write_text("content 2", encoding="utf-8")

        hash1 = compute_file_hash(file1)
        hash2 = compute_file_hash(file2)

        assert hash1 != hash2

    def test_compute_file_hash_missing_file_raises(self, tmp_path):
        """Test that missing file raises FileNotFoundError."""
        missing_file = tmp_path / "missing.txt"

        with pytest.raises(FileNotFoundError):
            compute_file_hash(missing_file)


class TestCacheManager:
    """Test suite for CacheManager class."""

    @pytest.fixture
    def setup_dirs(self, tmp_path):
        """Create test directory structure."""
        # Create structure: skill_dir/canonical/index.yaml
        skill_dir = tmp_path / "skill"
        canonical_dir = skill_dir / "canonical"
        canonical_dir.mkdir(parents=True)

        # Create index.yaml
        index_yaml = canonical_dir / "index.yaml"
        index_yaml.write_text("doc1:\n  title: Test Doc\n", encoding="utf-8")

        return {
            "skill_dir": skill_dir,
            "canonical_dir": canonical_dir,
            "index_yaml": index_yaml,
            "cache_dir": skill_dir / ".cache",
        }

    def test_init_sets_paths_correctly(self, setup_dirs):
        """Test that CacheManager initializes paths correctly."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        assert cm.base_dir == setup_dirs["canonical_dir"]
        assert cm._cache_dir == setup_dirs["skill_dir"] / ".cache"
        assert cm._index_path == setup_dirs["canonical_dir"] / "index.yaml"

    def test_is_inverted_index_valid_no_cache_returns_false(self, setup_dirs):
        """Test that missing cache file returns invalid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        result = cm.is_inverted_index_valid()

        assert result is False

    def test_is_inverted_index_valid_no_version_file_returns_false(self, setup_dirs):
        """Test that missing version file returns invalid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create cache file but no version file
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")

        result = cm.is_inverted_index_valid()

        assert result is False

    def test_is_inverted_index_valid_with_matching_hash(self, setup_dirs):
        """Test that matching hash returns valid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create cache structure
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")

        # Create version file with correct hash
        current_hash = compute_file_hash(setup_dirs["index_yaml"])
        version_info = {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "plugin_fingerprint": MOCK_PLUGIN_FINGERPRINT,
            "index_yaml_hash": current_hash,
            "index_yaml_mtime": setup_dirs["index_yaml"].stat().st_mtime,
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        with patch("scripts.utils.cache_manager.compute_plugin_fingerprint", return_value=MOCK_PLUGIN_FINGERPRINT):
            result = cm.is_inverted_index_valid()

        assert result is True

    def test_is_inverted_index_valid_wrong_format_version(self, setup_dirs):
        """Test that wrong format version returns invalid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create cache structure
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")

        # Create version file with wrong format version
        version_info = {
            "cache_format_version": "0.0",  # Wrong version
            "index_yaml_hash": "sha256:abc",
            "index_yaml_mtime": 0,
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        result = cm.is_inverted_index_valid()

        assert result is False

    def test_is_inverted_index_valid_hash_mismatch(self, setup_dirs):
        """Test that hash mismatch returns invalid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create cache structure
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")

        # Create version file with wrong hash
        version_info = {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "index_yaml_hash": "sha256:wrong_hash",
            "index_yaml_mtime": 0,  # Different mtime to trigger hash check
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        result = cm.is_inverted_index_valid()

        assert result is False

    def test_mark_inverted_index_built_creates_version_file(self, setup_dirs):
        """Test that marking cache built creates version file."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        cm.mark_inverted_index_built()

        assert cm._cache_version_path.exists()

        # Verify content
        version_info = json.loads(cm._cache_version_path.read_text(encoding="utf-8"))
        assert version_info["cache_format_version"] == CACHE_FORMAT_VERSION
        assert version_info["index_yaml_hash"].startswith("sha256:")

    def test_clear_inverted_index_removes_files(self, setup_dirs):
        """Test that clearing inverted index removes cache files."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create cache files
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")
        cm._cache_version_path.write_text("{}", encoding="utf-8")

        result = cm.clear_inverted_index()

        assert result is True
        assert not cm._inverted_index_path.exists()
        assert not cm._cache_version_path.exists()

    def test_clear_inverted_index_returns_false_if_nothing_to_clear(self, setup_dirs):
        """Test that clearing empty cache returns False."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        result = cm.clear_inverted_index()

        assert result is False

    def test_clear_llms_cache_removes_manifest_state(self, setup_dirs):
        """Test that clearing LLMS cache removes manifest state file."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create LLMS cache file
        cm._llms_cache_dir.mkdir(parents=True, exist_ok=True)
        cm._manifest_state_path.write_text("{}", encoding="utf-8")

        result = cm.clear_llms_cache()

        assert result is True
        assert not cm._manifest_state_path.exists()

    def test_clear_llms_cache_returns_false_if_nothing_to_clear(self, setup_dirs):
        """Test that clearing empty LLMS cache returns False."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        result = cm.clear_llms_cache()

        assert result is False

    def test_clear_all_clears_both_caches(self, setup_dirs):
        """Test that clear_all clears both cache types."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create both cache types
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")
        cm._cache_version_path.write_text("{}", encoding="utf-8")
        cm._llms_cache_dir.mkdir(parents=True, exist_ok=True)
        cm._manifest_state_path.write_text("{}", encoding="utf-8")

        result = cm.clear_all()

        assert result["inverted_index"] is True
        assert result["llms_cache"] is True
        assert not cm._inverted_index_path.exists()
        assert not cm._manifest_state_path.exists()

    def test_get_cache_info_returns_status(self, setup_dirs):
        """Test that get_cache_info returns cache status."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        info = cm.get_cache_info()

        assert "cache_dir" in info
        assert "inverted_index" in info
        assert "llms_cache" in info
        assert "index_yaml" in info
        assert info["index_yaml"]["exists"] is True

    def test_get_cache_info_with_valid_cache(self, setup_dirs):
        """Test get_cache_info when cache is valid."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create valid cache
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")
        current_hash = compute_file_hash(setup_dirs["index_yaml"])
        version_info = {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "plugin_fingerprint": MOCK_PLUGIN_FINGERPRINT,
            "index_yaml_hash": current_hash,
            "index_yaml_mtime": setup_dirs["index_yaml"].stat().st_mtime,
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        with patch("scripts.utils.cache_manager.compute_plugin_fingerprint", return_value=MOCK_PLUGIN_FINGERPRINT):
            info = cm.get_cache_info()

        assert info["inverted_index"]["exists"] is True
        assert info["inverted_index"]["valid"] is True
        assert info["cache_version"]["exists"] is True


class TestCacheManagerMtimeOptimization:
    """Test suite for mtime fast-path optimization."""

    @pytest.fixture
    def setup_dirs(self, tmp_path):
        """Create test directory structure."""
        skill_dir = tmp_path / "skill"
        canonical_dir = skill_dir / "canonical"
        canonical_dir.mkdir(parents=True)

        index_yaml = canonical_dir / "index.yaml"
        index_yaml.write_text("doc1:\n  title: Test Doc\n", encoding="utf-8")

        return {
            "skill_dir": skill_dir,
            "canonical_dir": canonical_dir,
            "index_yaml": index_yaml,
        }

    def test_mtime_unchanged_skips_hash_check(self, setup_dirs):
        """Test that unchanged mtime uses fast path."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create valid cache with current mtime
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")
        current_hash = compute_file_hash(setup_dirs["index_yaml"])
        current_mtime = setup_dirs["index_yaml"].stat().st_mtime
        version_info = {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "plugin_fingerprint": MOCK_PLUGIN_FINGERPRINT,
            "index_yaml_hash": current_hash,
            "index_yaml_mtime": current_mtime,
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        # Patch compute_file_hash to verify it's not called, and mock plugin fingerprint
        with patch("scripts.utils.cache_manager.compute_file_hash") as mock_hash, \
             patch("scripts.utils.cache_manager.compute_plugin_fingerprint", return_value=MOCK_PLUGIN_FINGERPRINT):
            result = cm.is_inverted_index_valid()

        assert result is True
        mock_hash.assert_not_called()

    def test_mtime_changed_content_same_updates_mtime(self, setup_dirs):
        """Test that changed mtime with same content updates version file."""
        cm = CacheManager(setup_dirs["canonical_dir"])

        # Create valid cache with different mtime but same hash
        cm._cache_dir.mkdir(parents=True, exist_ok=True)
        cm._inverted_index_path.write_text("{}", encoding="utf-8")
        current_hash = compute_file_hash(setup_dirs["index_yaml"])
        version_info = {
            "cache_format_version": CACHE_FORMAT_VERSION,
            "plugin_fingerprint": MOCK_PLUGIN_FINGERPRINT,
            "index_yaml_hash": current_hash,
            "index_yaml_mtime": 0,  # Different mtime
        }
        cm._cache_version_path.write_text(json.dumps(version_info), encoding="utf-8")

        # Should still be valid (hash matches)
        with patch("scripts.utils.cache_manager.compute_plugin_fingerprint", return_value=MOCK_PLUGIN_FINGERPRINT):
            result = cm.is_inverted_index_valid()

        assert result is True

        # Version file should be updated with new mtime
        updated_info = json.loads(cm._cache_version_path.read_text(encoding="utf-8"))
        assert updated_info["index_yaml_mtime"] == setup_dirs["index_yaml"].stat().st_mtime
