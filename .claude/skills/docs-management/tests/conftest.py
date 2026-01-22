"""
pytest configuration and fixtures for docs-management tests.
"""
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable


import pytest
import yaml


# Add scripts directory to Python path for absolute imports
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))


# =============================================================================
# Dynamic Timestamp Fixtures (for time-sensitive tests)
# =============================================================================

@pytest.fixture
def current_utc_timestamp() -> str:
    """Generate current UTC timestamp in ISO 8601 format.

    Returns:
        ISO 8601 formatted timestamp, e.g., '2025-11-26T14:30:00Z'
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@pytest.fixture
def timestamp_factory() -> Callable[..., str]:
    """Factory function to generate timestamps with optional offset.

    Returns:
        A callable that generates ISO 8601 timestamps.

    Usage:
        ts = timestamp_factory()
        now = ts()                    # Current time
        yesterday = ts(days=-1)       # 1 day ago
        next_week = ts(days=7)        # 7 days from now
        specific = ts(hours=-2, minutes=-30)  # 2.5 hours ago
    """
    def _create_timestamp(
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0
    ) -> str:
        delta = timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        dt = datetime.now(timezone.utc) + delta
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    return _create_timestamp


@pytest.fixture
def date_range_factory() -> Callable[..., tuple[str, str]]:
    """Factory function to generate date ranges relative to now.

    Returns:
        A callable that generates (start, end) timestamp tuples.

    Usage:
        range_factory = date_range_factory()
        start, end = range_factory(days_back=7)  # Last 7 days
        start, end = range_factory(days_back=30, days_forward=0)  # Last 30 days
    """
    def _create_range(
        days_back: int = 7,
        days_forward: int = 0
    ) -> tuple[str, str]:
        now = datetime.now(timezone.utc)
        start = (now - timedelta(days=days_back)).strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (now + timedelta(days=days_forward)).strftime("%Y-%m-%dT%H:%M:%SZ")
        return start, end

    return _create_range


@pytest.fixture
def mock_scraped_timestamp(timestamp_factory) -> str:
    """Generate a realistic 'last_scraped' timestamp (recent, within last hour)."""
    return timestamp_factory(minutes=-30)


# =============================================================================
# Index Entry Factory (with dynamic timestamps)
# =============================================================================

@pytest.fixture
def index_entry_factory(current_utc_timestamp) -> Callable[..., dict]:
    """Factory to create index entries with dynamic timestamps.

    Returns:
        A callable that creates index entry dicts with customizable fields.

    Usage:
        factory = index_entry_factory()
        entry = factory()  # Default entry with current timestamp
        entry = factory(doc_id="custom-id", title="Custom Title")
        entry = factory(last_scraped="2025-01-01T00:00:00Z")  # Override timestamp
    """
    def _create_entry(
        doc_id: str = "test-doc-id",
        url: str = "https://example.com/docs/test",
        title: str = "Test Document",
        description: str = "A test document for unit tests",
        category: str = "documentation",
        tags: list[str] | None = None,
        keywords: list[str] | None = None,
        path: str = "canonical/example-com/docs/test.md",
        content_hash: str = "abc123def456",
        last_scraped: str | None = None
    ) -> dict:
        return {
            "doc_id": doc_id,
            "url": url,
            "title": title,
            "description": description,
            "category": category,
            "tags": tags if tags is not None else ["test", "example"],
            "keywords": keywords if keywords is not None else ["test", "example", "documentation"],
            "path": path,
            "content_hash": content_hash,
            "last_scraped": last_scraped if last_scraped is not None else current_utc_timestamp
        }

    return _create_entry


# =============================================================================
# Basic Fixtures
# =============================================================================

@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_config_dir(temp_dir):
    """Create a mock config directory with sample YAML files."""
    config_dir = temp_dir / "config"
    config_dir.mkdir()
    return config_dir


@pytest.fixture
def mock_sources_config(mock_config_dir):
    """Create a mock sources.json configuration (ConfigRegistry expects JSON format)."""
    sources = [
        {
            "name": "anthropic-com",
            "url": "https://www.anthropic.com/sitemap.xml",
            "type": "sitemap",
            "filter": "/news/"
        },
        {
            "name": "docs-claude-com",
            "url": "https://docs.claude.com/sitemap.xml",
            "type": "sitemap",
            "filter": "/en/docs/"
        }
    ]
    
    # ConfigRegistry expects sources.json (JSON format)
    config_file = mock_config_dir / "sources.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(sources, f)
    
    return config_file


@pytest.fixture
def mock_filtering_config(mock_config_dir):
    """Create a mock filtering.yaml configuration."""
    filtering = {
        "title_patterns": {
            "exclude": [
                r"\[Draft\]",
                r"^Test:",
                r"(WIP)"
            ]
        },
        "content_patterns": {
            "exclude": [
                r"<!-- DRAFT -->",
                r"TODO:",
                r"FIXME:"
            ]
        },
        "url_patterns": {
            "exclude": [
                r"/draft/",
                r"/test/",
                r"/internal/"
            ]
        }
    }

    config_file = mock_config_dir / "filtering.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(filtering, f)

    return config_file


@pytest.fixture
def mock_tag_detection_config(mock_config_dir):
    """Create a mock tag-detection.yaml configuration."""
    tag_detection = {
        "technology_keywords": {
            "python": ["python", "pip", "virtualenv", "pytest"],
            "javascript": ["javascript", "node", "npm", "jest"],
            "git": ["git", "github", "gitlab", "version control"]
        },
        "platform_keywords": {
            "windows": ["windows", "win32", "powershell", "wsl"],
            "macos": ["macos", "darwin", "homebrew", "xcode"],
            "linux": ["linux", "ubuntu", "debian", "apt"]
        },
        "topic_keywords": {
            "ai": ["artificial intelligence", "machine learning", "llm", "claude"],
            "devops": ["docker", "kubernetes", "ci/cd", "deployment"],
            "security": ["security", "authentication", "encryption", "oauth"]
        }
    }

    config_file = mock_config_dir / "tag-detection.yaml"
    with open(config_file, 'w', encoding='utf-8') as f:
        yaml.dump(tag_detection, f)

    return config_file


@pytest.fixture
def mock_html_content():
    """Sample HTML content for testing publication date extraction."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta property="article:published_time" content="2025-11-15T10:30:00Z">
        <meta property="article:modified_time" content="2025-11-16T09:00:00Z">
        <meta name="date" content="2025-11-15">
    </head>
    <body>
        <time datetime="2025-11-15T10:30:00Z">November 15, 2025</time>
        <article>
            <div class="published-date">Published: 2025-11-15</div>
            <p>Content here...</p>
        </article>
    </body>
    </html>
    """


@pytest.fixture
def mock_http_response():
    """Mock HTTP response data."""
    return {
        "status_code": 200,
        "headers": {
            "Content-Type": "text/html; charset=utf-8",
            "Last-Modified": "Fri, 15 Nov 2025 10:30:00 GMT"
        },
        "text": "<html><body>Test content</body></html>"
    }


@pytest.fixture(autouse=True)
def reset_config_cache(request):
    """Reset all config and singleton state before each test.

    NOTE: Tests marked with @pytest.mark.no_config_reset will skip this fixture.
    This is needed for integration tests that depend on stable config state,
    such as search relevance tests that use the actual canonical index.
    """
    import sys

    # Skip for tests marked with no_config_reset
    if request.node.get_closest_marker('no_config_reset'):
        yield
        return

    # Clear config registry cache
    try:
        from config.config_registry import get_registry, ConfigRegistry
        registry = get_registry()
        registry.clear_cache()
        # Also clear the singleton instance to force fresh state
        ConfigRegistry._instance = None
    except (ImportError, AttributeError):
        pass
    
    # Clear ConfigLoader instances
    try:
        from scripts.utils.config_loader import ConfigLoader
        if hasattr(ConfigLoader, '_instances'):
            ConfigLoader._instances.clear()
    except (ImportError, AttributeError):
        pass
    
    # Clear logging cache
    try:
        if 'utils.logging_utils' in sys.modules:
            logging_mod = sys.modules['utils.logging_utils']
            if hasattr(logging_mod, '_script_logger_cache'):
                logging_mod._script_logger_cache.clear()
    except (AttributeError, KeyError):
        pass
    
    yield
    
    # Clean up after test
    try:
        from config.config_registry import get_registry, ConfigRegistry
        registry = get_registry()
        registry.clear_cache()
        ConfigRegistry._instance = None
    except (ImportError, AttributeError):
        pass

    try:
        from scripts.utils.config_loader import ConfigLoader
        if hasattr(ConfigLoader, '_instances'):
            ConfigLoader._instances.clear()
    except (ImportError, AttributeError):
        pass


# =============================================================================
# Index and Document Fixtures
# =============================================================================

@pytest.fixture
def mock_index_entry():
    """Create a mock index entry for testing."""
    return {
        "doc_id": "test-doc-id",
        "url": "https://example.com/docs/test",
        "title": "Test Document",
        "description": "A test document for unit tests",
        "category": "documentation",
        "tags": ["test", "example"],
        "keywords": ["test", "example", "documentation"],
        "path": "canonical/example-com/docs/test.md",
        "content_hash": "abc123def456",
        "last_scraped": "2025-11-26T12:00:00Z"
    }


@pytest.fixture
def mock_index_data(mock_index_entry):
    """Create mock index data with multiple entries."""
    return {
        "test-doc-id": mock_index_entry,
        "another-doc": {
            "doc_id": "another-doc",
            "url": "https://example.com/docs/another",
            "title": "Another Document",
            "description": "Another test document",
            "category": "guide",
            "tags": ["guide", "tutorial"],
            "keywords": ["guide", "tutorial", "howto"],
            "path": "canonical/example-com/docs/another.md",
            "content_hash": "xyz789abc",
            "last_scraped": "2025-11-26T12:00:00Z"
        },
        "hooks-doc": {
            "doc_id": "hooks-doc",
            "url": "https://code.claude.com/docs/hooks",
            "title": "Claude Code Hooks",
            "description": "Documentation about hooks",
            "category": "reference",
            "tags": ["hooks", "automation"],
            "keywords": ["hooks", "PreToolUse", "PostToolUse", "automation"],
            "path": "canonical/code-claude-com/docs/hooks.md",
            "content_hash": "hooks123",
            "last_scraped": "2025-11-26T12:00:00Z"
        }
    }


@pytest.fixture
def mock_index_file(temp_dir, mock_index_data):
    """Create a mock index.yaml file."""
    index_file = temp_dir / "index.yaml"
    with open(index_file, 'w', encoding='utf-8') as f:
        yaml.dump(mock_index_data, f)
    return index_file


@pytest.fixture
def mock_markdown_content():
    """Sample markdown content for testing."""
    return """# Test Document

## Overview

This is a test document with multiple sections.

## Installation

Follow these steps to install:

1. Step one
2. Step two
3. Step three

## Configuration

Configure the tool by editing the config file.

### Basic Configuration

Simple configuration options.

### Advanced Configuration

More complex options for power users.

## Troubleshooting

Common issues and solutions.
"""


@pytest.fixture
def mock_canonical_dir(temp_dir, mock_markdown_content):
    """Create a mock canonical directory with markdown files."""
    canonical_dir = temp_dir / "canonical"
    canonical_dir.mkdir()

    # Create example-com subdirectory
    example_dir = canonical_dir / "example-com" / "docs"
    example_dir.mkdir(parents=True)

    # Write test markdown file
    test_md = example_dir / "test.md"
    test_md.write_text(mock_markdown_content, encoding='utf-8')

    return canonical_dir


# =============================================================================
# Performance Testing Fixtures
# =============================================================================

@pytest.fixture
def performance_timer():
    """Fixture for timing test execution."""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None

        @property
        def elapsed_ms(self):
            elapsed = self.elapsed
            return elapsed * 1000 if elapsed else None

    return Timer()


# =============================================================================
# Logging Test Fixtures
# =============================================================================

@pytest.fixture
def temp_logs_dir(temp_dir):
    """Create a temporary logs directory structure for testing."""
    logs_dir = temp_dir / "logs"
    logs_dir.mkdir()
    for category in ["scrape", "index", "search", "diagnostics"]:
        (logs_dir / category).mkdir()
    return logs_dir


@pytest.fixture
def cleanup_test_loggers():
    """Cleanup loggers created during tests to avoid handler accumulation."""
    import logging

    created_loggers = []
    yield created_loggers

    # Cleanup after test
    for logger_name in created_loggers:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers[:]:
            try:
                handler.close()
            except Exception:
                pass
        logger.handlers.clear()


# =============================================================================
# Auto-Cleanup Fixtures (reduces boilerplate in test files)
# =============================================================================

@pytest.fixture
def refs_dir():
    """TempReferencesDir with automatic cleanup.

    Reduces boilerplate in tests by eliminating try/finally patterns.
    Automatically cleans up temporary directory after test completes.

    Usage:
        def test_something(self, refs_dir):
            refs_dir.create_index({"doc-id": {...}})
            # ... test code ...
            # cleanup is automatic - no try/finally needed

    Instead of the old pattern:
        refs_dir = TempReferencesDir()
        try:
            refs_dir.create_index({"doc-id": {...}})
            # ... test code ...
        finally:
            refs_dir.cleanup()
    """
    from tests.shared.test_utils import TempReferencesDir
    dir_instance = TempReferencesDir()
    yield dir_instance
    dir_instance.cleanup()


@pytest.fixture
def config_dir():
    """TempConfigDir with automatic cleanup.

    Similar to refs_dir but for configuration directory testing.
    """
    from tests.shared.test_utils import TempConfigDir
    dir_instance = TempConfigDir()
    yield dir_instance
    dir_instance.cleanup()
