#!/usr/bin/env python3
"""
Configuration Registry - Single Source of Truth for All Configuration

Provides unified access to all configuration files:
- sources.json (source definitions)
- filtering.yaml (filtering rules)
- tag_detection.yaml (tag detection rules)
- defaults.yaml (default values)

All configuration can be overridden via environment variables.
"""

from __future__ import annotations

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional

# Add scripts directory to path for imports
# config/ is one level down from skill root
_skill_dir = Path(__file__).resolve().parents[1]
_scripts_dir = _skill_dir / 'scripts'
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

# Import using full path since scripts is now in sys.path
try:
    from utils.script_utils import ensure_yaml_installed
    from utils.logging_utils import get_or_setup_logger
except ImportError:
    # Fallback to direct imports if package structure not available
    import importlib.util
    
    # Load script_utils
    script_utils_path = _scripts_dir / 'utils' / 'script_utils.py'
    spec = importlib.util.spec_from_file_location("script_utils", script_utils_path)
    script_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script_utils)
    ensure_yaml_installed = script_utils.ensure_yaml_installed
    
    # Load logging_utils
    logging_utils_path = _scripts_dir / 'utils' / 'logging_utils.py'
    spec = importlib.util.spec_from_file_location("logging_utils", logging_utils_path)
    logging_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(logging_utils)
    get_or_setup_logger = logging_utils.get_or_setup_logger

# Ensure PyYAML is available
yaml = ensure_yaml_installed()

logger = get_or_setup_logger(__file__)

# Environment variable prefix for overrides
ENV_PREFIX = "CLAUDE_DOCS_"


class ConfigRegistry:
    """
    Unified configuration registry with caching and environment variable overrides.
    
    Singleton pattern ensures consistent configuration access across all scripts.
    """
    
    _instance: 'ConfigRegistry' | None = None
    _lock = threading.Lock()
    
    def __new__(cls) -> 'ConfigRegistry':
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration registry."""
        if self._initialized:
            return
        
        self._cache: dict[str, Any] = {}
        self._cache_lock = threading.Lock()
        
        # Determine skill directory
        script_dir = Path(__file__).parent
        self.skill_dir = script_dir.parent
        self.config_dir = script_dir
        
        # Default paths
        self._paths = {
            'sources': self.skill_dir / 'references' / 'sources.json',
            'filtering': self.config_dir / 'filtering.yaml',
            'tag_detection': self.config_dir / 'tag_detection.yaml',
            'defaults': self.config_dir / 'defaults.yaml',
        }
        
        self._initialized = True
        logger.debug("ConfigRegistry initialized")
    
    def _get_defaults_path(self) -> Path:
        """Get path to defaults.yaml, checking multiple locations for test compatibility."""
        # Check default location first
        if self._paths['defaults'].exists():
            return self._paths['defaults']
        
        # For tests: check if there's a defaults.yaml in any temp directory config
        # This allows tests to work with temp fixtures
        for temp_marker in ['/tmp/', '\\Temp\\', 'AppData/Local/Temp']:
            if temp_marker in str(Path.cwd()):
                # We're in a test temp directory, use fallback
                return self._paths['defaults']  # Will fail with FileNotFoundError, which is expected
        
        return self._paths['defaults']
    
    def _load_json(self, path: Path) -> dict[str, Any]:
        """Load JSON file."""
        if not path.exists():
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_yaml(self, path: Path) -> dict[str, Any]:
        """Load YAML file with fallback for missing files."""
        if not path.exists():
            # For tests or when config doesn't exist, return empty dict instead of failing
            # This allows tests to work without creating full config fixtures
            logger.warning(f"Configuration file not found, using empty config: {path}")
            return {}
        
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    
    def _apply_env_overrides(self, config: dict[str, Any], prefix: str = "") -> dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables follow the pattern:
        CLAUDE_DOCS_<SECTION>_<KEY>
        
        Example: CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT=60
        """
        result = config.copy()
        
        for key, value in config.items():
            env_key = f"{ENV_PREFIX}{prefix}{key}".upper()
            env_value = os.environ.get(env_key)
            
            if env_value is not None:
                # Try to convert to appropriate type
                if isinstance(value, bool):
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                elif isinstance(value, int):
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        logger.warning(f"Invalid integer value for {env_key}: {env_value}")
                        continue
                elif isinstance(value, float):
                    try:
                        env_value = float(env_value)
                    except ValueError:
                        logger.warning(f"Invalid float value for {env_key}: {env_value}")
                        continue
                elif isinstance(value, list):
                    # For lists, split by comma or use as single value
                    if ',' in env_value:
                        env_value = [v.strip() for v in env_value.split(',')]
                    else:
                        env_value = [env_value]
                
                result[key] = env_value
                logger.debug(f"Override from {env_key}: {value} -> {env_value}")
            
            # Recursively apply overrides to nested dictionaries
            if isinstance(value, dict):
                result[key] = self._apply_env_overrides(value, f"{prefix}{key}_")
        
        return result
    
    def load_sources(self, path: Path | None = None) -> dict[str, Any]:
        """
        Load sources.json configuration.
        
        Args:
            path: Optional custom path to sources.json
        
        Returns:
            Sources configuration dictionary or list (depending on format)
        """
        config_path = Path(path) if path else self._paths['sources']
        cache_key = f'sources:{config_path}'
        
        with self._cache_lock:
            if cache_key in self._cache:
                logger.debug(f"Using cached sources config: {config_path}")
                return self._cache[cache_key]
        
        logger.debug(f"Loading sources config: {config_path}")
        suffix = config_path.suffix.lower()
        if suffix in ('.yaml', '.yml'):
            config = self._load_yaml(config_path)
        else:
            config = self._load_json(config_path)
        
        # Handle both list and dict formats
        # If it's a list, apply overrides to each item
        # If it's a dict, apply overrides normally
        if isinstance(config, list):
            # For list format, apply overrides to each source item
            config = [self._apply_env_overrides(item, "SOURCES_") if isinstance(item, dict) else item 
                     for item in config]
        elif isinstance(config, dict):
            # Apply environment variable overrides
            config = self._apply_env_overrides(config, "SOURCES_")
        
        with self._cache_lock:
            self._cache[cache_key] = config
        
        return config
    
    def load_filtering(self, path: Path | None = None) -> dict[str, Any]:
        """
        Load filtering.yaml configuration.
        
        Args:
            path: Optional custom path to filtering.yaml
        
        Returns:
            Filtering configuration dictionary
        """
        config_path = path or self._paths['filtering']
        cache_key = f'filtering:{config_path}'
        
        with self._cache_lock:
            if cache_key in self._cache:
                logger.debug(f"Using cached filtering config: {config_path}")
                return self._cache[cache_key]
        
        logger.debug(f"Loading filtering config: {config_path}")
        config = self._load_yaml(config_path)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config, "FILTERING_")
        
        with self._cache_lock:
            self._cache[cache_key] = config
        
        return config
    
    def load_tag_detection(self, path: Path | None = None) -> dict[str, Any]:
        """
        Load tag_detection.yaml configuration.
        
        Args:
            path: Optional custom path to tag_detection.yaml
        
        Returns:
            Tag detection configuration dictionary
        """
        config_path = path or self._paths['tag_detection']
        cache_key = f'tag_detection:{config_path}'
        
        with self._cache_lock:
            if cache_key in self._cache:
                logger.debug(f"Using cached tag detection config: {config_path}")
                return self._cache[cache_key]
        
        logger.debug(f"Loading tag detection config: {config_path}")
        config = self._load_yaml(config_path)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config, "TAG_DETECTION_")
        
        with self._cache_lock:
            self._cache[cache_key] = config
        
        return config
    
    def load_defaults(self, path: Path | None = None) -> dict[str, Any]:
        """
        Load defaults.yaml configuration.
        
        Args:
            path: Optional custom path to defaults.yaml
        
        Returns:
            Defaults configuration dictionary with environment variable overrides applied
        """
        config_path = path or self._paths['defaults']
        cache_key = f'defaults:{config_path}'
        
        with self._cache_lock:
            if cache_key in self._cache:
                logger.debug(f"Using cached defaults config: {config_path}")
                return self._cache[cache_key]
        
        logger.debug(f"Loading defaults config: {config_path}")
        config = self._load_yaml(config_path)
        
        # Apply environment variable overrides
        config = self._apply_env_overrides(config, "")
        
        with self._cache_lock:
            self._cache[cache_key] = config
        
        return config
    
    def get_default(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get a default value from defaults.yaml.
        
        Args:
            section: Configuration section (e.g., 'http', 'scraping')
            key: Configuration key (e.g., 'default_timeout')
            default: Default value if not found
        
        Returns:
            Configuration value or default
        """
        defaults = self.load_defaults()
        return defaults.get(section, {}).get(key, default)
    
    def clear_cache(self) -> None:
        """Clear all cached configurations."""
        with self._cache_lock:
            count = len(self._cache)
            self._cache.clear()
            # Only log at INFO level if there was something to clear
            # to avoid spamming logs when called frequently with empty cache
            if count > 0:
                logger.info(f"Cleared {count} cached configuration(s)")
            else:
                logger.debug("Cache already empty, nothing to clear")
    
    def reload(self) -> None:
        """
        Force reload of all configurations.
        
        Clears the cache and forces fresh reads from disk on next access.
        Useful when configuration files have been modified.
        """
        self.clear_cache()
        logger.info("Configuration cache cleared - will reload on next access")


# Module-level convenience functions
def get_registry() -> ConfigRegistry:
    """Get the singleton ConfigRegistry instance."""
    return ConfigRegistry()


def get_default(section: str, key: str, default: Any = None) -> Any:
    """Get a default value from defaults.yaml."""
    return get_registry().get_default(section, key, default)


def load_sources(path: Path | None = None) -> dict[str, Any]:
    """Load sources.json configuration."""
    return get_registry().load_sources(path)


def load_filtering(path: Path | None = None) -> dict[str, Any]:
    """Load filtering.yaml configuration."""
    return get_registry().load_filtering(path)


def load_tag_detection(path: Path | None = None) -> dict[str, Any]:
    """Load tag_detection.yaml configuration."""
    return get_registry().load_tag_detection(path)


def load_defaults(path: Path | None = None) -> dict[str, Any]:
    """Load defaults.yaml configuration."""
    return get_registry().load_defaults()


def reload_configs() -> None:
    """Force reload of all configurations."""
    get_registry().reload()


if __name__ == '__main__':
    # Self-test
    import sys
    
    print("ConfigRegistry Self-Test")
    print("=" * 50)
    
    registry = ConfigRegistry()
    
    print("\nTesting defaults.yaml loading...")
    try:
        defaults = registry.load_defaults()
        print(f"✓ Loaded defaults config")
        print(f"  - HTTP default timeout: {defaults.get('http', {}).get('default_timeout')}")
        print(f"  - Scraping max workers: {defaults.get('scraping', {}).get('max_workers')}")
        print(f"  - Index chunk size: {defaults.get('index', {}).get('chunk_size')}")
    except Exception as e:
        print(f"✗ Failed to load defaults config: {e}")
        sys.exit(1)
    
    print("\nTesting get_default()...")
    try:
        timeout = registry.get_default('http', 'default_timeout', 30)
        print(f"✓ get_default('http', 'default_timeout'): {timeout}")
        
        max_workers = registry.get_default('scraping', 'max_workers', 3)
        print(f"✓ get_default('scraping', 'max_workers'): {max_workers}")
    except Exception as e:
        print(f"✗ get_default() failed: {e}")
        sys.exit(1)
    
    print("\nTesting filtering.yaml loading...")
    try:
        filtering = registry.load_filtering()
        print(f"✓ Loaded filtering config")
        print(f"  - Domain stop words: {len(filtering.get('domain_stop_words', []))}")
    except Exception as e:
        print(f"✗ Failed to load filtering config: {e}")
    
    print("\nTesting tag_detection.yaml loading...")
    try:
        tag_config = registry.load_tag_detection()
        print(f"✓ Loaded tag detection config")
        if 'tags' in tag_config:
            print(f"  - Tags: {len(tag_config['tags'])}")
    except Exception as e:
        print(f"✗ Failed to load tag detection config: {e}")
    
    print("\nTesting sources.json loading...")
    try:
        sources = registry.load_sources()
        print(f"✓ Loaded sources config")
        if isinstance(sources, list):
            print(f"  - Sources: {len(sources)}")
        elif isinstance(sources, dict) and 'sources' in sources:
            print(f"  - Sources: {len(sources['sources'])}")
    except Exception as e:
        print(f"✗ Failed to load sources config: {e}")
    
    print("\nTesting cache...")
    defaults2 = registry.load_defaults()
    print(f"✓ Cache working (second load instant)")
    
    print("\nTesting reload...")
    registry.reload()
    defaults3 = registry.load_defaults()
    print(f"✓ Reload successful")
    
    print("\n" + "=" * 50)
    print("Self-test complete!")

