#!/usr/bin/env python3
"""
Configuration Loader - Thin Wrapper Around ConfigRegistry

This module provides a compatibility layer for scripts that use ConfigLoader.
It delegates to config.config_registry.ConfigRegistry, which is the canonical
configuration system with environment variable support and caching.

**IMPORTANT: Config Loader Duality**

There are two config loader implementations in this skill:

1. **scripts/config_loader.py** (this file) - Runtime wrapper
   - Used by production scripts at runtime
   - Wraps ConfigRegistry for backward compatibility
   - Supports both JSON (sources.json) and YAML formats
   - Use this for runtime script execution

2. **scripts/utils/config_loader.py** - Test-compatible wrapper
   - Used by test suite for compatibility with test fixtures
   - Provides YAML-only API expected by tests
   - Use this ONLY in test files

**For new code:**
Prefer importing directly from config.config_registry:
    from config.config_registry import get_registry, get_default, load_sources

**For backward compatibility:**
Use this module (scripts/config_loader.py) for legacy code:
    from config_loader import ConfigLoader

    config = ConfigLoader()
    sources = config.load_sources('path/to/sources.json')
    filtering = config.load_filtering()
    tag_config = config.load_tag_detection()

    # Force reload
    config.reload()
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; config_dir = bootstrap.config_dir

import threading
from typing import Any

# Import the canonical config registry
try:
    # Use centralized path utility (already in sys.path from bootstrap)
    from utils.common_paths import get_config_dir
    config_dir_path = get_config_dir()
    if str(config_dir_path) not in sys.path:
        sys.path.insert(0, str(config_dir_path))
    from config.config_registry import ConfigRegistry, get_registry
except ImportError:
    # Fallback if config registry not available
    ConfigRegistry = None
    get_registry = None

# Import logger after config_registry to avoid circular import
from .logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="index")

class ConfigurationError(Exception):
    """Raised when configuration files are missing or invalid."""
    pass

class ConfigLoader:
    """
    Configuration loader - thin wrapper around ConfigRegistry.
    
    This class provides backward compatibility for scripts using the old
    ConfigLoader API. It delegates to ConfigRegistry internally.
    
    For new code, use ConfigRegistry directly:
        from config.config_registry import get_registry
        registry = get_registry()
        defaults = registry.load_defaults()
    """

    # Per-config-dir instance cache for singleton behavior
    _instances: dict[str, 'ConfigLoader'] = {}
    _instance_lock = threading.Lock()

    def __new__(cls, config_dir: str | None = None) -> 'ConfigLoader':
        """
        Ensure only one instance exists per config directory (singleton pattern).
        
        Args:
            config_dir: Optional config directory path (for tests)
        """
        # Use config_dir as cache key, or "default" if None
        cache_key = str(Path(config_dir).resolve()) if config_dir else "default"
        
        with cls._instance_lock:
            if cache_key not in cls._instances:
                instance = super().__new__(cls)
                instance._initialized = False
                instance._config_dir = config_dir
                cls._instances[cache_key] = instance
            
            return cls._instances[cache_key]

    def __init__(self, config_dir: str | None = None):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Optional config directory path (for tests)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return

        # Resolve config_dir to absolute path
        if config_dir:
            self._config_dir = str(Path(config_dir).resolve())
        else:
            self._config_dir = None
        
        # Use canonical config registry
        if ConfigRegistry is None:
            raise ImportError("ConfigRegistry not available. Ensure config/config_registry.py exists.")
        
        self._registry = get_registry()
        self._initialized = True
        logger.debug(f"ConfigLoader initialized (wrapping ConfigRegistry, config_dir: {config_dir})")

    def load_sources(self, path: str | Path | None = None) -> dict[str, Any]:
        """
        Load and validate sources.json configuration.

        Delegates to ConfigRegistry.load_sources().

        Args:
            path: Optional path to sources file. If None, uses config_dir/sources.yaml.

        Returns:
            Validated sources configuration dictionary or list

        Raises:
            FileNotFoundError: If sources file doesn't exist
            ValueError: If configuration is invalid
        """
        resolved_path: Path | None = None
        if path is not None:
            resolved_path = Path(path)
        elif self._config_dir:
            json_path = Path(self._config_dir) / "sources.json"
            yaml_path = Path(self._config_dir) / "sources.yaml"
            if json_path.exists():
                resolved_path = json_path
            elif yaml_path.exists():
                resolved_path = yaml_path

        if resolved_path is None or not resolved_path.exists():
            raise ConfigurationError(f"Sources configuration not found: {resolved_path or self._config_dir}")
        
        try:
            return self._registry.load_sources(resolved_path)
        except FileNotFoundError as e:
            raise ConfigurationError(f"Sources configuration not found: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load sources configuration: {e}")

    def load_filtering(self, path: str | Path | None = None) -> dict[str, Any]:
        """
        Load filtering.yaml configuration.

        Delegates to ConfigRegistry.load_filtering().

        Args:
            path: Optional path to filtering.yaml. If None, uses config_dir/filtering.yaml.

        Returns:
            Filtering configuration dictionary

        Raises:
            FileNotFoundError: If filtering.yaml doesn't exist
        """
        if path is None and self._config_dir:
            path = Path(self._config_dir) / "filtering.yaml"
        
        try:
            return self._registry.load_filtering(Path(path) if path else None)
        except FileNotFoundError as e:
            raise ConfigurationError(f"Filtering configuration not found: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load filtering configuration: {e}")

    def load_tag_detection(self, path: str | Path | None = None) -> dict[str, Any]:
        """
        Load tag_detection.yaml configuration.

        Delegates to ConfigRegistry.load_tag_detection().

        Args:
            path: Optional path to tag_detection.yaml. If None, uses config_dir/tag-detection.yaml.

        Returns:
            Tag detection configuration dictionary

        Raises:
            FileNotFoundError: If tag_detection.yaml doesn't exist
        """
        if path is None and self._config_dir:
            path = Path(self._config_dir) / "tag-detection.yaml"
        
        try:
            return self._registry.load_tag_detection(Path(path) if path else None)
        except FileNotFoundError as e:
            raise ConfigurationError(f"Tag detection configuration not found: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load tag detection configuration: {e}")

    @property
    def config_dir(self) -> str | None:
        """Get the config directory path."""
        return self._config_dir

    def clear_cache(self) -> None:
        """Clear all cached configurations. Delegates to ConfigRegistry."""
        self._registry.clear_cache()

    def reload(self) -> None:
        """Force reload of all configurations. Delegates to ConfigRegistry."""
        self._registry.reload()

if __name__ == '__main__':
    # Self-test
    print("ConfigLoader Self-Test")
    print("=" * 50)
    
    loader = ConfigLoader()
    
    print("\nTesting load_sources()...")
    try:
        sources = loader.load_sources()
        print(f"✓ Loaded sources config")
        if isinstance(sources, list):
            print(f"  - Sources: {len(sources)}")
        elif isinstance(sources, dict) and 'sources' in sources:
            print(f"  - Sources: {len(sources['sources'])}")
    except Exception as e:
        print(f"✗ Failed to load sources: {e}")
    
    print("\nTesting load_filtering()...")
    try:
        filtering = loader.load_filtering()
        print(f"✓ Loaded filtering config")
        print(f"  - Stop words: {len(filtering.get('domain_stop_words', []))}")
    except Exception as e:
        print(f"✗ Failed to load filtering: {e}")
    
    print("\nTesting load_tag_detection()...")
    try:
        tag_config = loader.load_tag_detection()
        print(f"✓ Loaded tag detection config")
        if 'tags' in tag_config:
            print(f"  - Tags: {len(tag_config['tags'])}")
    except Exception as e:
        print(f"✗ Failed to load tag detection: {e}")
    
    print("\n" + "=" * 50)
    print("Self-test complete!")
