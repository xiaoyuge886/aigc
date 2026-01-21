#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_helpers.py - Convenience functions for configuration access.

Provides simple, consistent access to configuration values across all scripts.
All functions use config_registry internally and support environment variable overrides.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; config_dir = bootstrap.config_dir

from typing import Any

# Import config registry (bootstrap already set up paths)
# NOTE: This is the CANONICAL source for get_default. Other files that need
# config access at module level (before full imports) may duplicate this pattern,
# but should import from config_helpers when possible.
try:
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from config_registry import get_default, get_registry
except ImportError:
    # Fallback if config registry not available
    def get_default(section: str, key: str, default: Any = None) -> Any:
        return default
    def get_registry():
        raise ImportError("ConfigRegistry not available")


def get_config_value_safe(section: str, key: str, default: Any = None) -> Any:
    """Load a value from ConfigRegistry with graceful fallback.

    This is a convenience wrapper around get_default that handles all edge cases.
    Use this when you need config access in a function (not at module level).

    Args:
        section: Config section name (e.g., 'http', 'scraping', 'index')
        key: Key within the section
        default: Default value if config not available or key not found

    Returns:
        The config value, or default if not found

    Example:
        timeout = get_config_value_safe('http', 'default_timeout', 30.0)
    """
    return get_default(section, key, default)

# HTTP Configuration Helpers

def get_http_timeout() -> float:
    """Get default HTTP timeout in seconds."""
    result = get_default('http', 'default_timeout', 30.0)
    return result if result is not None else 30.0

def get_http_max_timeout() -> float:
    """Get maximum HTTP timeout for long-running operations."""
    return get_default('http', 'max_timeout', 1800.0)

def get_http_user_agent() -> str:
    """Get user agent string for HTTP requests."""
    return get_default('http', 'user_agent', "Claude-Docs-Scraper/1.0 (Educational purposes)")

def get_management_user_agent() -> str:
    """Get user agent string for management/cleanup operations."""
    return get_default('user_agents', 'management', "Claude-Docs-Management-Bot/1.0")

def get_scraper_user_agent() -> str:
    """Get user agent string for scraping operations."""
    return get_default('user_agents', 'scraper', "Claude-Docs-Scraper/1.0 (Educational purposes)")

def get_http_max_retries() -> int:
    """Get maximum number of retry attempts for HTTP requests."""
    return get_default('http', 'default_max_retries', 3)

def get_http_initial_retry_delay() -> float:
    """Get initial delay for exponential backoff."""
    return get_default('http', 'initial_retry_delay', 1.0)

def get_http_backoff_factor() -> float:
    """Get backoff multiplier for exponential backoff."""
    return get_default('http', 'backoff_factor', 2.0)

def get_http_head_request_timeout() -> float:
    """Get timeout for HEAD requests."""
    return get_default('http', 'head_request_timeout', 10.0)

def get_http_markdown_request_timeout() -> float:
    """Get timeout for markdown URL requests."""
    return get_default('http', 'markdown_request_timeout', 30.0)

def get_retryable_status_codes() -> list[int]:
    """Get list of HTTP status codes that should trigger retries."""
    return get_default('http', 'retryable_status_codes', [429, 500, 502, 503, 504])

# Scraping Configuration Helpers

def get_scraping_rate_limit() -> float:
    """Get delay between scraping requests in seconds."""
    return get_default('scraping', 'rate_limit', 0.5)

def get_scraping_header_rate_limit() -> float:
    """Get delay between HEAD requests in seconds."""
    return get_default('scraping', 'header_rate_limit', 0.3)

def get_scraping_max_workers() -> int:
    """Get maximum parallel workers for scraping."""
    return get_default('scraping', 'max_workers', 4)

def get_scraping_max_source_workers() -> int:
    """Get maximum parallel workers for multi-source scraping."""
    return get_default('scraping', 'max_source_workers', 4)

def get_scraping_timeout() -> float:
    """Get default timeout for scraping operations."""
    return get_default('scraping', 'default_timeout', 1800.0)

def get_max_content_age_days() -> int:
    """Get maximum content age in days (0 = no filtering)."""
    return get_default('scraping', 'max_content_age_days', 0)

def get_skip_existing_default() -> bool:
    """Get default value for skip_existing flag."""
    return get_default('scraping', 'skip_existing', True)

def get_sources_default_timeout() -> float:
    """Get default timeout for source scraping operations (seconds)."""
    return get_default('scraping', 'sources_default_timeout', 1800.0)

def get_scraping_progress_lock_timeout() -> float:
    """Get timeout for progress lock operations."""
    return get_default('scraping', 'progress_lock_timeout', 30.0)

def get_scraping_index_lock_timeout() -> float:
    """Get timeout for index lock operations during scraping."""
    return get_default('scraping', 'index_lock_timeout', 30.0)

def get_output_dir_mapping(domain: str) -> str:
    """
    Get output directory mapping for a domain.

    First checks explicit config mappings, then falls back to automatic transformation:
    - Strip 'www.' prefix if present
    - Replace dots with hyphens

    Examples:
        docs.claude.com → docs-claude-com
        www.anthropic.com → anthropic-com
        raw.githubusercontent.com → raw-githubusercontent-com

    Args:
        domain: Domain name to map

    Returns:
        Output directory name (always returns a value via smart fallback)
    """
    output_dirs = get_default('paths', 'output_dirs', {})

    # Check explicit config first
    if domain in output_dirs:
        return output_dirs[domain]

    # Smart fallback: strip www. and replace dots with hyphens
    normalized = domain.removeprefix('www.')
    return normalized.replace('.', '-')

def get_scraping_progress_interval() -> int:
    """Get progress reporting interval in seconds."""
    return get_default('scraping', 'progress_interval', 30)

def get_scraping_progress_url_interval() -> int:
    """Get progress reporting interval in number of URLs."""
    return get_default('scraping', 'progress_url_interval', 10)

# Index Configuration Helpers

def get_index_chunk_size() -> int:
    """Get chunk size for reading large YAML files."""
    return get_default('index', 'chunk_size', 1000)

def get_index_token_threshold() -> int:
    """Get token estimate threshold for loading files."""
    return get_default('index', 'token_estimate_threshold', 20000)

def get_index_lock_timeout() -> float:
    """Get lock timeout for index operations."""
    return get_default('index', 'lock_timeout', 30.0)

def get_index_lock_retry_delay() -> float:
    """Get delay between lock acquisition attempts."""
    return get_default('index', 'lock_retry_delay', 0.1)

def get_index_lock_retry_backoff() -> float:
    """Get delay after failed lock acquisition."""
    return get_default('index', 'lock_retry_backoff', 0.5)

def get_index_file_retry_delay() -> float:
    """Get delay for atomic file operations."""
    return get_default('index', 'file_retry_delay', 0.2)

def get_file_io_max_retries() -> int:
    """Get maximum number of retry attempts for file I/O operations."""
    return get_default('index', 'file_max_retries', 5)

def get_file_io_initial_retry_delay() -> float:
    """Get initial delay for file I/O retry exponential backoff."""
    return get_default('index', 'file_retry_delay', 0.2)

def get_index_file_max_retries() -> int:
    """Get maximum retries for file operations."""
    return get_default('index', 'file_max_retries', 5)

# Validation Configuration Helpers

def get_validation_timeout() -> float:
    """Get timeout for validation operations."""
    return get_default('validation', 'timeout', 60.0)

def get_validation_max_retries() -> int:
    """Get maximum retries for validation operations."""
    return get_default('validation', 'max_retries', 1)

# Drift Detection Configuration Helpers

def get_drift_max_workers() -> int:
    """Get maximum parallel workers for drift detection."""
    return get_default('drift', 'max_workers', 5)

def get_drift_timeout() -> float:
    """Get timeout for drift detection operations."""
    return get_default('drift', 'timeout', 300.0)

# Performance Configuration Helpers

def is_parallel_enabled() -> bool:
    """Check if parallel processing is enabled by default."""
    return get_default('performance', 'parallel_enabled', True)

def get_parallel_min_urls() -> int:
    """Get minimum number of URLs to trigger parallel processing."""
    return get_default('performance', 'parallel_min_urls', 2)

# File Pattern Configuration

def get_markdown_extension() -> str:
    """Get markdown file extension (default: .md)."""
    return get_default('files', 'markdown_extension', '.md')

def get_yaml_extension() -> str:
    """Get YAML file extension (default: .yaml)."""
    return get_default('files', 'yaml_extension', '.yaml')

def get_json_extension() -> str:
    """Get JSON file extension (default: .json)."""
    return get_default('files', 'json_extension', '.json')

# Subprocess Configuration Helpers

def get_subprocess_default_timeout() -> float:
    """Get default timeout for subprocess operations."""
    return get_default('subprocess', 'default_timeout', 10.0)

def get_subprocess_quick_timeout() -> float:
    """Get timeout for quick subprocess checks."""
    return get_default('subprocess', 'quick_timeout', 5.0)

def get_subprocess_install_timeout() -> float:
    """Get timeout for package installation operations."""
    return get_default('subprocess', 'install_timeout', 300.0)

def get_subprocess_long_timeout() -> float:
    """Get timeout for long-running subprocess operations."""
    return get_default('subprocess', 'long_timeout', 600.0)

def get_subprocess_build_timeout() -> float:
    """Get timeout for build tool operations."""
    return get_default('subprocess', 'build_timeout', 600.0)

# Search Configuration Helpers

def get_domain_weight(domain: str) -> float:
    """
    Get priority weight for a domain.
    
    Args:
        domain: Domain name (e.g., "code.claude.com", "docs.claude.com")
    
    Returns:
        Weight multiplier (higher = higher priority in search results)
    """
    weights = get_default('search', 'domain_weights', {})
    
    # Try exact match first
    if domain in weights:
        return weights[domain]
    
    # Try to match by category path (e.g., anthropic.com/engineering)
    for pattern, weight in weights.items():
        if domain.startswith(pattern) or pattern.startswith(domain):
            return weight
    
    # Default weight if not configured
    return 1.0

def get_all_domain_weights() -> dict[str, float]:
    """Get all configured domain weights."""
    return get_default('search', 'domain_weights', {})

# Filtering configuration helpers
_filtering_cache: dict | None = None

def _get_filtering_config() -> dict:
    """Get filtering configuration, caching the result."""
    global _filtering_cache
    if _filtering_cache is None:
        try:
            # Try ConfigLoader first (handles all edge cases)
            from utils.config_loader import ConfigLoader
            loader = ConfigLoader()
            _filtering_cache = loader.load_filtering()
        except Exception:
            # Fallback: direct load from common_paths
            try:
                import yaml
                from utils.common_paths import find_repo_root
                repo_root = find_repo_root()
                config_path = repo_root / ".claude" / "skills" / "docs-management" / "config" / "filtering.yaml"
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        _filtering_cache = yaml.safe_load(f) or {}
                else:
                    _filtering_cache = {}
            except Exception:
                _filtering_cache = {}
    return _filtering_cache

def get_query_stop_words() -> set[str]:
    """Get query stop words from filtering.yaml.

    These words are stripped from search queries before processing.
    Example: "when to use subagents" → search for "subagents" only

    Returns:
        Set of stop words to filter from queries
    """
    config = _get_filtering_config()
    words = config.get('query_stop_words', [])
    return set(w.lower() for w in words if isinstance(w, str))

def get_generic_verbs() -> set[str]:
    """Get generic verbs from filtering.yaml.

    These verbs are deprioritized in search scoring.

    Returns:
        Set of generic verbs
    """
    config = _get_filtering_config()
    verbs = config.get('generic_verbs', [])
    return set(v.lower() for v in verbs if isinstance(v, str))

def get_generic_config_terms() -> set[str]:
    """Get generic configuration terms from filtering.yaml.

    These terms (configuration, setup, guide, etc.) cause ranking collapse
    when mixed with specific terms. Docs matching ONLY these terms are penalized.

    Returns:
        Set of generic configuration terms
    """
    config = _get_filtering_config()
    terms = config.get('generic_config_terms', [])
    return set(t.lower() for t in terms if isinstance(t, str))

def get_domain_stop_words() -> set[str]:
    """Get domain-specific stop words from filtering.yaml.

    These are brand names, product names, and URL domains that should
    be filtered from searches (e.g., claude, anthropic).

    Returns:
        Set of domain-specific stop words
    """
    config = _get_filtering_config()
    words = config.get('domain_stop_words', [])
    return set(w.lower() for w in words if isinstance(w, str))

def get_natural_language_stop_words() -> set[str]:
    """Get combined stop words for natural language query processing.

    Combines general English stop words with domain-specific stop words.
    Used by search_by_natural_language() for query preprocessing.

    Returns:
        Combined set of stop words for NL queries
    """
    # General English stop words (articles, prepositions, etc.)
    general_stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'about', 'how', 'what', 'where', 'when', 'why',
        'is', 'it', 'be', 'do', 'documentation'
    }

    # Combine with domain-specific stop words from config
    domain_words = get_domain_stop_words()

    return general_stop_words | domain_words

def clear_topics_config_cache() -> None:
    """Clear any cached topics configuration. No-op stub for backward compatibility."""
    # This function was previously used for clearing a topics config cache.
    # The cache has been removed but the function is kept for backward compatibility.
    pass

def clear_filtering_cache() -> None:
    """Clear the filtering configuration cache."""
    global _filtering_cache
    _filtering_cache = None

# Convenience function to reload all configs
def reload_configs() -> None:
    """Force reload of all configurations from disk."""
    try:
        registry = get_registry()
        registry.reload()
    except ImportError:
        pass

    # Clear all caches
    clear_topics_config_cache()
    clear_filtering_cache()

