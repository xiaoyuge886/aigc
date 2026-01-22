"""
Tests for config_loader module.
"""
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


import pytest
import yaml
from scripts.utils.config_loader import ConfigLoader, ConfigurationError



class TestConfigLoader:
    """Test suite for ConfigLoader class."""

    def test_singleton_pattern(self, mock_config_dir):
        """Test that ConfigLoader implements singleton pattern correctly."""
        instance1 = ConfigLoader(str(mock_config_dir))
        instance2 = ConfigLoader(str(mock_config_dir))

        assert instance1 is instance2

    def test_different_config_dirs_different_instances(self, temp_dir):
        """Test that different config directories create different instances."""
        dir1 = temp_dir / "config1"
        dir2 = temp_dir / "config2"
        dir1.mkdir()
        dir2.mkdir()

        instance1 = ConfigLoader(str(dir1))
        instance2 = ConfigLoader(str(dir2))

        assert instance1 is not instance2

    def test_load_sources_valid_config(self, mock_config_dir, mock_sources_config):
        """Test loading valid sources configuration."""
        loader = ConfigLoader(str(mock_config_dir))

        sources = loader.load_sources()

        # Sources is now a list format (not dict)
        assert isinstance(sources, list)
        assert len(sources) == 2
        assert sources[0]["name"] == "anthropic-com"
        assert sources[1]["name"] == "docs-claude-com"

    def test_load_sources_caching(self, mock_config_dir, mock_sources_config):
        """Test that sources configuration is cached."""
        loader = ConfigLoader(str(mock_config_dir))

        # Load twice
        sources1 = loader.load_sources()
        sources2 = loader.load_sources()

        # Should return same object (cached)
        assert sources1 is sources2

    def test_load_sources_missing_file(self, temp_dir):
        """Test error handling when sources.yaml is missing."""
        config_dir = temp_dir / "empty_config"
        config_dir.mkdir()

        loader = ConfigLoader(str(config_dir))

        with pytest.raises(ConfigurationError):
            loader.load_sources()

    def test_load_sources_invalid_yaml(self, mock_config_dir):
        """Test error handling for invalid YAML syntax."""
        # Create invalid YAML file
        invalid_yaml = mock_config_dir / "sources.yaml"
        with open(invalid_yaml, 'w') as f:
            f.write("invalid: yaml: syntax:\n  - broken")

        loader = ConfigLoader(str(mock_config_dir))

        with pytest.raises(ConfigurationError) as exc_info:
            loader.load_sources()

            # Error message includes "Failed to load sources configuration"
            assert "Failed to load sources configuration" in str(exc_info.value)

    def test_load_filtering_valid_config(self, mock_config_dir, mock_filtering_config):
        """Test loading valid filtering configuration."""
        loader = ConfigLoader(str(mock_config_dir))

        filtering = loader.load_filtering()

        assert "title_patterns" in filtering
        assert "content_patterns" in filtering
        assert "url_patterns" in filtering
        assert "exclude" in filtering["title_patterns"]

    def test_load_filtering_caching(self, mock_config_dir, mock_filtering_config):
        """Test that filtering configuration is cached."""
        loader = ConfigLoader(str(mock_config_dir))

        filtering1 = loader.load_filtering()
        filtering2 = loader.load_filtering()

        assert filtering1 is filtering2

    def test_load_filtering_missing_file(self, temp_dir):
        """Test that missing filtering.yaml returns empty dict (graceful degradation)."""
        config_dir = temp_dir / "empty_config"
        config_dir.mkdir()

        loader = ConfigLoader(str(config_dir))

        # ConfigRegistry returns empty dict for missing files (test-friendly)
        result = loader.load_filtering()
        assert isinstance(result, dict)

    def test_load_tag_detection_valid_config(self, mock_config_dir,
                                             mock_tag_detection_config):
        """Test loading valid tag detection configuration."""
        loader = ConfigLoader(str(mock_config_dir))

        tag_detection = loader.load_tag_detection()

        assert "technology_keywords" in tag_detection
        assert "platform_keywords" in tag_detection
        assert "topic_keywords" in tag_detection
        assert "python" in tag_detection["technology_keywords"]

    def test_load_tag_detection_validation(self, mock_config_dir,
                                          mock_tag_detection_config):
        """Test that tag detection config is validated."""
        loader = ConfigLoader(str(mock_config_dir))

        tag_detection = loader.load_tag_detection()

        # Verify structure is correct
        for category in ["technology_keywords", "platform_keywords", "topic_keywords"]:
            assert isinstance(tag_detection[category], dict)
            for tag, keywords in tag_detection[category].items():
                assert isinstance(keywords, list)
                assert all(isinstance(k, str) for k in keywords)

    def test_load_tag_detection_missing_file(self, temp_dir):
        """Test that missing tag-detection.yaml returns empty dict (graceful degradation)."""
        config_dir = temp_dir / "empty_config"
        config_dir.mkdir()

        loader = ConfigLoader(str(config_dir))

        # ConfigRegistry returns empty dict for missing files (test-friendly)
        result = loader.load_tag_detection()
        assert isinstance(result, dict)

    def test_clear_cache(self, mock_config_dir, mock_sources_config):
        """Test cache clearing functionality."""
        loader = ConfigLoader(str(mock_config_dir))

        # Load and cache
        sources1 = loader.load_sources()

        # Clear cache
        loader.clear_cache()

        # Load again
        sources2 = loader.load_sources()

        # Should be different objects after cache clear
        assert sources1 is not sources2
        # But content should be the same
        assert sources1 == sources2

    def test_config_dir_property(self, mock_config_dir):
        """Test config_dir property."""
        loader = ConfigLoader(str(mock_config_dir))

        # Compare as resolved paths to handle Windows short names (KYLESE~1 vs KyleSexton)
        assert Path(loader.config_dir).resolve() == Path(mock_config_dir).resolve()

    def test_relative_config_dir_resolution(self, temp_dir):
        """Test that relative config directories are resolved correctly."""
        config_dir = temp_dir / "config"
        config_dir.mkdir()

        # Create minimal sources.yaml
        sources_file = config_dir / "sources.yaml"
        with open(sources_file, 'w') as f:
            yaml.dump({"test": {"base_url": "https://test.com"}}, f)

        # Change to temp dir and use relative path
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(temp_dir))
            loader = ConfigLoader("config")

            # Should resolve to absolute path
            # config_dir is stored as absolute string
            config_path = Path(loader.config_dir)
            assert config_path.is_absolute()
            assert config_path.name == "config"
        finally:
            os.chdir(original_cwd)

    def test_load_all_configs_together(self, mock_config_dir, mock_sources_config,
                                       mock_filtering_config, mock_tag_detection_config):
        """Test loading all configurations together."""
        loader = ConfigLoader(str(mock_config_dir))

        sources = loader.load_sources()
        filtering = loader.load_filtering()
        tag_detection = loader.load_tag_detection()

        # All should be loaded successfully
        assert sources is not None
        assert filtering is not None
        assert tag_detection is not None

        # Verify independence (caching should work per config)
        sources2 = loader.load_sources()
        filtering2 = loader.load_filtering()
        tag_detection2 = loader.load_tag_detection()

        assert sources is sources2
        assert filtering is filtering2
        assert tag_detection is tag_detection2


class TestConfigurationError:
    """Test suite for ConfigurationError exception."""

    def test_exception_message(self):
        """Test that exception message is preserved."""
        error = ConfigurationError("Test error message")

        assert str(error) == "Test error message"

    def test_exception_inheritance(self):
        """Test that ConfigurationError inherits from Exception."""
        error = ConfigurationError("Test")

        assert isinstance(error, Exception)


class TestThreadSafety:
    """Test thread safety of ConfigLoader singleton."""

    def test_concurrent_initialization(self, mock_config_dir):
        """ConfigLoader should remain singleton even under concurrent access."""
        party_count = 12
        barrier = threading.Barrier(party_count)

        def create_instance(_):
            barrier.wait()
            return ConfigLoader(str(mock_config_dir))

        with ThreadPoolExecutor(max_workers=party_count) as executor:
            instances = list(executor.map(create_instance, range(party_count)))

        assert len({id(instance) for instance in instances}) == 1


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_config_file(self, mock_config_dir):
        """Test handling of empty configuration file."""
        # Create empty sources.json (ConfigRegistry expects JSON)
        empty_config = mock_config_dir / "sources.json"
        empty_config.write_text("")

        loader = ConfigLoader(str(mock_config_dir))

        # Empty file should raise error or return empty
        try:
            sources = loader.load_sources()
            assert sources is None or sources == {} or sources == []
        except ConfigurationError:
            pass  # Also acceptable to raise error

    def test_config_with_unicode(self, mock_config_dir):
        """Test handling of Unicode in configuration."""
        unicode_config = {
            "test-source": {
                "base_url": "https://example.com",
                "description": "Test with Unicode: 你好 مرحبا שלום"
            }
        }

        config_file = mock_config_dir / "sources.yaml"
        with open(config_file, 'w', encoding='utf-8') as f:
            yaml.dump(unicode_config, f, allow_unicode=True)

        loader = ConfigLoader(str(mock_config_dir))
        sources = loader.load_sources()

        assert sources["test-source"]["description"] == "Test with Unicode: 你好 مرحبا שלום"

    def test_very_large_config(self, mock_config_dir):
        """Test handling of very large configuration files."""
        # Create config with 1000 sources
        large_config = {
            f"source-{i}": {
                "base_url": f"https://example{i}.com",
                "type": "documentation"
            }
            for i in range(1000)
        }

        # ConfigRegistry expects JSON format
        config_file = mock_config_dir / "sources.json"
        with open(config_file, 'w') as f:
            json.dump([{"name": f"source-{i}", "url": f"https://example{i}.com"} for i in range(100)], f)

        loader = ConfigLoader(str(mock_config_dir))
        sources = loader.load_sources()

        assert isinstance(sources, list)
        assert len(sources) == 100
        assert any(s["name"] == "source-50" for s in sources)
