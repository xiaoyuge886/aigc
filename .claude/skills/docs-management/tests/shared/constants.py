"""
Test constants for docs-management test suite.

Centralizes magic strings, numbers, and stable test values to:
1. Reduce duplication across test files
2. Make test data easier to maintain
3. Provide consistent values for test fixtures

For dynamic/time-sensitive values (timestamps, dates), use fixtures in conftest.py.
"""

from dataclasses import dataclass
from typing import Final


# =============================================================================
# Test Domain Constants
# =============================================================================

# Base test domains (use for URL construction in tests)
TEST_DOMAIN: Final[str] = "https://example.com"
TEST_DOMAIN_WITH_SLASH: Final[str] = "https://example.com/"

# Specific test URL patterns
TEST_DOC_URL: Final[str] = "https://example.com/docs/test"
TEST_API_URL: Final[str] = "https://example.com/api/test"
TEST_SKILLS_URL: Final[str] = "https://example.com/skills/guide"
TEST_HOOKS_URL: Final[str] = "https://example.com/hooks"
TEST_NOT_FOUND_URL: Final[str] = "https://example.com/not-found"
TEST_FORBIDDEN_URL: Final[str] = "https://example.com/forbidden"


# =============================================================================
# HTTP Configuration Constants
# =============================================================================

# Timeout values for HTTP operations
TEST_HTTP_TIMEOUT: Final[float] = 60.0
TEST_VALIDATION_TIMEOUT: Final[float] = 30.0
TEST_SHORT_TIMEOUT: Final[float] = 5.0

# HTTP status codes for test scenarios
HTTP_OK: Final[int] = 200
HTTP_NOT_FOUND: Final[int] = 404
HTTP_FORBIDDEN: Final[int] = 403
HTTP_SERVER_ERROR: Final[int] = 500
HTTP_SERVICE_UNAVAILABLE: Final[int] = 503
HTTP_RATE_LIMITED: Final[int] = 429

# Retry configuration for tests
TEST_MAX_RETRIES: Final[int] = 3
TEST_RETRY_DELAY: Final[float] = 0.01  # Short delay for tests


# =============================================================================
# Test Data Values
# =============================================================================

# Common test document IDs
TEST_DOC_ID: Final[str] = "test-doc-id"
TEST_DOC_ID_2: Final[str] = "another-doc"
TEST_DOC_ID_HOOKS: Final[str] = "hooks-doc"

# Common test paths
TEST_DOC_PATH: Final[str] = "canonical/example-com/docs/test.md"
TEST_DOC_PATH_2: Final[str] = "canonical/example-com/docs/another.md"

# Common test content hashes
TEST_CONTENT_HASH: Final[str] = "abc123def456"
TEST_CONTENT_HASH_2: Final[str] = "xyz789abc"


# =============================================================================
# Test Keywords and Tags
# =============================================================================

# Common test keywords
TEST_KEYWORDS: Final[list[str]] = ["test", "example", "documentation"]
TEST_KEYWORDS_HOOKS: Final[list[str]] = ["hooks", "PreToolUse", "PostToolUse", "automation"]

# Common test tags
TEST_TAGS: Final[list[str]] = ["test", "example"]
TEST_TAGS_GUIDE: Final[list[str]] = ["guide", "tutorial"]
TEST_TAGS_HOOKS: Final[list[str]] = ["hooks", "automation"]

# Common test categories
TEST_CATEGORY_DOCS: Final[str] = "documentation"
TEST_CATEGORY_GUIDE: Final[str] = "guide"
TEST_CATEGORY_REFERENCE: Final[str] = "reference"


# =============================================================================
# Test Content Templates
# =============================================================================

# Minimal valid markdown content
TEST_MARKDOWN_MINIMAL: Final[str] = "# Test Document\n\nTest content."

# Markdown with sections
TEST_MARKDOWN_WITH_SECTIONS: Final[str] = """# Test Document

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

# HTML content for publication date extraction
TEST_HTML_WITH_DATES: Final[str] = '''<!DOCTYPE html>
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
</html>'''


# =============================================================================
# Test Configuration Values
# =============================================================================

@dataclass(frozen=True)
class TestConfigValues:
    """Frozen dataclass for test configuration values."""

    # Keyword extraction limits
    max_total_keywords: int = 12
    min_keyword_length: int = 3
    min_single_word_length: int = 5

    # Scraping configuration
    scraping_rate_limit: float = 0.5
    scraping_max_workers: int = 4

    # Index configuration
    index_chunk_size: int = 50

    # Drift detection
    drift_max_workers: int = 2
    drift_timeout: float = 30.0


# Singleton instance for tests to use
TEST_CONFIG = TestConfigValues()


# =============================================================================
# Expected Output Patterns (for assertion matching)
# =============================================================================

# Expected log message patterns
EXPECTED_LOG_INFO_PREFIX: Final[str] = "[INFO]"
EXPECTED_LOG_WARNING_PREFIX: Final[str] = "[WARNING]"
EXPECTED_LOG_ERROR_PREFIX: Final[str] = "[ERROR]"

# Expected JSON output fields
EXPECTED_INDEX_FIELDS: Final[set[str]] = {
    "doc_id", "url", "path", "title", "description",
    "category", "tags", "keywords", "content_hash", "last_scraped"
}

EXPECTED_METADATA_FIELDS: Final[set[str]] = {
    "title", "description", "keywords", "tags", "category"
}


# =============================================================================
# File System Constants
# =============================================================================

# Test file extensions
MD_EXTENSION: Final[str] = ".md"
YAML_EXTENSION: Final[str] = ".yaml"
JSON_EXTENSION: Final[str] = ".json"

# Test directory names
TEST_CANONICAL_DIR: Final[str] = "canonical"
TEST_CONFIG_DIR: Final[str] = "config"
TEST_LOGS_DIR: Final[str] = "logs"


# =============================================================================
# Static Timestamps (for deterministic tests - use conftest.py fixtures for dynamic)
# =============================================================================

# Stable timestamp for reproducible tests (not for time-sensitive assertions)
TEST_STATIC_TIMESTAMP: Final[str] = "2025-11-26T12:00:00Z"
TEST_STATIC_DATE: Final[str] = "2025-11-26"

# Common timestamp patterns for testing
TEST_TIMESTAMP_YESTERDAY: Final[str] = "2025-11-25T12:00:00Z"
TEST_TIMESTAMP_WEEK_AGO: Final[str] = "2025-11-19T12:00:00Z"
TEST_TIMESTAMP_MONTH_AGO: Final[str] = "2025-10-26T12:00:00Z"


# =============================================================================
# File Path Patterns (for constructing test paths)
# =============================================================================

# Pattern templates (use .format() or f-strings to substitute)
TEST_MD_PATH_PATTERN: Final[str] = "test/{filename}.md"
TEST_CANONICAL_PATH_PATTERN: Final[str] = "canonical/{domain}/{category}/{filename}.md"

# Common test file paths
TEST_INDEX_PATH: Final[str] = "canonical/index.yaml"
TEST_SKILLS_PATH: Final[str] = "canonical/code-claude-com/docs/skills.md"
TEST_HOOKS_PATH: Final[str] = "canonical/code-claude-com/docs/hooks.md"


# =============================================================================
# Search Terms (for search/query tests)
# =============================================================================

# Common search terms
TEST_SEARCH_TERM_SKILLS: Final[str] = "skills"
TEST_SEARCH_TERM_HOOKS: Final[str] = "hooks"
TEST_SEARCH_TERM_MEMORY: Final[str] = "memory"
TEST_SEARCH_TERM_SUBAGENTS: Final[str] = "subagents"
TEST_SEARCH_TERM_SETTINGS: Final[str] = "settings"

# Multi-word search terms
TEST_SEARCH_QUERY_PROGRESSIVE: Final[str] = "progressive disclosure"
TEST_SEARCH_QUERY_HOOK_EVENTS: Final[str] = "hook events"
TEST_SEARCH_QUERY_CLAUDE_CODE: Final[str] = "claude code"


# =============================================================================
# Test URL Patterns (for URL construction in tests)
# =============================================================================

# Sitemap and docs map URLs
TEST_SITEMAP_URL: Final[str] = "https://example.com/sitemap.xml"
TEST_DOCS_MAP_URL: Final[str] = "https://example.com/docs_map.md"

# Domain-specific test URLs
TEST_CODE_CLAUDE_URL: Final[str] = "https://code.claude.com/docs/skills"
TEST_ANTHROPIC_NEWS_URL: Final[str] = "https://www.anthropic.com/news/test-article"
TEST_DOCS_ANTHROPIC_URL: Final[str] = "https://docs.anthropic.com/en/docs/test"


# =============================================================================
# Display Limit Constants (for validation scripts)
# =============================================================================

@dataclass(frozen=True)
class DisplayLimits:
    """Constants for display limits in validation and reporting."""

    max_issues_shown: int = 20
    max_results_shown: int = 10
    max_description_chars: int = 200
    separator_width: int = 80
    truncation_suffix: str = "..."


# Singleton instance for tests to use
DISPLAY_LIMITS = DisplayLimits()
