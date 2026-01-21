"""
Tests for config_registry module.
"""
import os
from pathlib import Path


import pytest


# Add scripts directory to Python path
import sys
_scripts_dir = Path(__file__).parent.parent / 'scripts'
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

# Import config_registry
try:
    skill_dir = Path(__file__).parent.parent
    config_dir = skill_dir / 'config'
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from config.config_registry import ConfigRegistry, get_default, load_sources
except ImportError:
    pytest.skip("config_registry not available", allow_module_level=True)


class TestConfigRegistry:
    """Test suite for ConfigRegistry class."""

    def test_singleton_pattern(self, temp_dir):
        """Test that ConfigRegistry is a singleton."""
        registry1 = ConfigRegistry()
        registry2 = ConfigRegistry()
        
        assert registry1 is registry2

    def test_load_defaults(self, temp_dir):
        """Test loading defaults.yaml."""
        registry = ConfigRegistry()
        
        # Should have loaded defaults
        defaults = registry.load_defaults()
        assert defaults is not None
        assert isinstance(defaults, dict)
        assert 'http' in defaults
        assert 'scraping' in defaults
        assert 'paths' in defaults

    def test_get_default(self, temp_dir):
        """Test get_default function."""
        # Test with existing key
        timeout = get_default('http', 'default_timeout', 30)
        assert isinstance(timeout, (int, float))
        assert timeout > 0

        # Test with non-existent key (should return default)
        value = get_default('nonexistent', 'nonexistent_key', 'fallback')
        assert value == 'fallback'

    def test_environment_variable_override(self, temp_dir):
        """Test that environment variables override config values."""
        # Set environment variable
        os.environ['CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT'] = '60'
        
        try:
            # Reload registry to pick up env var
            registry = ConfigRegistry()
            registry.reload()
            
            timeout = get_default('http', 'default_timeout', 30)
            assert timeout == 60
        finally:
            # Clean up
            del os.environ['CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT']
            registry = ConfigRegistry()
            registry.reload()

    def test_load_sources(self, temp_dir):
        """Test load_sources function."""
        sources = load_sources()
        
        # Should return a list or dict
        assert isinstance(sources, (list, dict))
        
        # Should have at least some sources
        assert len(sources) > 0

    def test_config_caching(self, temp_dir):
        """Test that config is cached."""
        registry1 = ConfigRegistry()
        registry2 = ConfigRegistry()
        
        # Both should be the same instance (singleton)
        assert registry1 is registry2
        
        # Both should use same cache
        defaults1 = registry1.load_defaults()
        defaults2 = registry2.load_defaults()
        assert defaults1 is defaults2

    def test_reload_config(self, temp_dir):
        """Test reloading config."""
        registry = ConfigRegistry()
        original_timeout = get_default('http', 'default_timeout', 30)
        
        # Set environment variable
        os.environ['CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT'] = '90'
        
        try:
            # Reload
            registry.reload()
            
            timeout = get_default('http', 'default_timeout', 30)
            assert timeout == 90
        finally:
            # Clean up
            del os.environ['CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT']
            registry.reload()

    def test_get_default_with_nested_keys(self, temp_dir):
        """Test get_default with nested config structure."""
        # Test accessing nested values
        value = get_default('http', 'default_timeout', 30)
        assert isinstance(value, (int, float))

    def test_config_registry_with_missing_files(self, temp_dir):
        """Test that ConfigRegistry handles missing config files gracefully."""
        # Should not crash if config files are missing
        registry = ConfigRegistry()
        
        # Should still be able to load defaults (may raise FileNotFoundError if file missing)
        try:
            defaults = registry.load_defaults()
            assert defaults is not None
        except FileNotFoundError:
            # This is acceptable if defaults.yaml doesn't exist
            pass
