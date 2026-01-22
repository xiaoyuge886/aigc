# Configuration System

The docs-management skill uses a unified configuration system with a single source of truth for all configurable values.

## Configuration Files

- **`config/defaults.yaml`** - Central configuration file with all default values
- **`config/config_registry.py`** - Canonical configuration system with environment variable support
- **`references/sources.json`** - Documentation sources configuration (required for scraping; located in references directory, default for `scrape_all_sources.py`)
- **`config/filtering.yaml`** - Filtering rules for keyword extraction
- **`config/tag_detection.yaml`** - Tag and category detection rules

## Path Configuration

All paths are configured in `config/defaults.yaml` under the `paths` section:

```yaml
paths:
  base_dir: ".claude/skills/docs-management/canonical"    # Base directory for canonical storage
  index_filename: "index.yaml"         # Index filename
  temp_dir: ".claude/temp"             # Temporary directory for reports/logs
  output_dirs:                         # Output directory mappings (domain -> subdirectory)
    docs.claude.com: "docs-claude-com"
    code.claude.com: "code-claude-com"
    www.anthropic.com: "anthropic-com"
    anthropic.com: "anthropic-com"
```

Scripts use `path_config.py` to resolve paths, ensuring consistency across all operations. Output directory mappings are used by `scrape_docs.py` and `scrape_all_sources.py` for auto-detecting output subdirectories based on source URLs.

**Important:** All domain-to-output-directory mappings must be configured in `config/defaults.yaml` under `paths.output_dirs`. Scripts will raise a `ValueError` with helpful instructions if a domain is not configured (hardcoded fallbacks have been removed to ensure single source of truth).

## Lock and Retry Configuration

Lock acquisition and file operation retries are configurable in `config/defaults.yaml`:

```yaml
index:
  lock_timeout: 30.0                  # Lock timeout for index operations (seconds)
  lock_retry_delay: 0.1               # Delay between lock acquisition attempts (seconds)
  lock_retry_backoff: 0.5             # Delay after failed lock acquisition (seconds)
  file_retry_delay: 0.2               # Delay for atomic file operations (seconds)
  file_max_retries: 5                 # Maximum retries for file operations
```

## Drift Detection Configuration

Drift detection settings are configurable in `config/defaults.yaml`:

```yaml
drift:
  max_workers: 5                      # Maximum parallel workers for drift detection (404 checks, hash comparisons)
  timeout: 300                        # Timeout for drift detection operations (seconds)
```

These values are used by `index_manager.py` and `scrape_docs.py` for thread-safe operations.

## Environment Variable Overrides

All configuration values can be overridden using environment variables:

```bash
# Override HTTP timeout
export CLAUDE_DOCS_HTTP_DEFAULT_TIMEOUT=60

# Override scraping rate limit
export CLAUDE_DOCS_SCRAPING_RATE_LIMIT=2.0

# Override base directory
export CLAUDE_DOCS_PATHS_BASE_DIR="custom/references"

# Override drift detection max workers
export CLAUDE_DOCS_DRIFT_MAX_WORKERS=10
```

Environment variables follow the pattern: `CLAUDE_DOCS_<SECTION>_<KEY>` (uppercase, underscores).

## Configurable Values

All hardcoded values have been externalized to `defaults.yaml` and accessed via `config_helpers`:

- **HTTP**: timeouts (default, max, HEAD, markdown), retries, retryable status codes, user agent, initial retry delay, backoff factor
- **Scraping**: rate limits (main and header), max workers, lock timeouts (progress, index), sources default timeout, skip existing default, progress reporting intervals (time and URL count)
- **Index**: chunk size, token thresholds, lock timeouts, lock retry delays, file retry delays, max retries
- **Paths**: base directory, index filename, temp directory, output directory mappings
- **Validation**: timeouts, max retries
- **Drift Detection**: max workers, timeout for 404 checks and hash comparisons
- **Files**: markdown, YAML, JSON extensions
- **User Agents**: default, management, scraper user agent strings
- **Performance**: parallel processing settings
- **Subprocess**: timeouts (default, quick, install, build, long) for dependency installation and other subprocess operations

**No hardcoded fallbacks:** All scripts use `config_helpers` functions which read from `defaults.yaml` with environment variable override support. This ensures a single source of truth for all configuration.

## Using Configuration in Scripts

**Recommended approach:** Use `config_helpers` for convenient access to configuration values:

```python
from config_helpers import (
    get_http_timeout,
    get_http_max_retries,
    get_http_initial_retry_delay,
    get_http_markdown_request_timeout,
    get_scraping_max_workers,
    get_scraping_rate_limit,
    get_scraping_header_rate_limit,
    get_scraping_progress_lock_timeout,
    get_scraping_index_lock_timeout,
    get_drift_max_workers,
    get_management_user_agent,
    get_scraper_user_agent,
    get_sources_default_timeout,
    get_output_dir_mapping,
    get_index_lock_retry_delay,
    get_index_lock_retry_backoff,
    get_validation_timeout
)

timeout = get_http_timeout()
max_workers = get_scraping_max_workers()
drift_workers = get_drift_max_workers()  # For drift detection operations
user_agent = get_management_user_agent()
sources_timeout = get_sources_default_timeout()  # Default timeout for source scraping
output_dir = get_output_dir_mapping('docs.claude.com')  # Get output dir mapping for domain
rate_limit = get_scraping_rate_limit()
header_rate_limit = get_scraping_header_rate_limit()
```

**All scripts should use `config_helpers` instead of directly calling `get_default()` from `config_registry`.** This ensures consistency and makes it easier to maintain configuration access patterns.

**Alternative approach:** Use `get_default()` from `config_registry` directly:

```python
from config.config_registry import get_default

# Get config value with fallback
timeout = get_default('http', 'default_timeout', 30)
rate_limit = get_default('scraping', 'rate_limit', 1.0)
```

**For CLI argument handling:** Use `cli_utils` helpers:

```python
from cli_utils import add_base_dir_argument, resolve_base_dir_from_args

parser = argparse.ArgumentParser()
add_base_dir_argument(parser)  # Adds --base-dir with config default
args = parser.parse_args()
base_dir = resolve_base_dir_from_args(args)  # Resolves to absolute Path
```

**For paths:** Use `path_config` functions:

```python
from path_config import get_base_dir, get_index_path, get_temp_dir

base_dir = get_base_dir()
index_path = get_index_path(base_dir)
temp_dir = get_temp_dir()
```

## Backward Compatibility

The configuration system maintains backward compatibility:

- `scripts/config_loader.py` is a thin wrapper around `config_registry`
- `scripts/utils/config_loader.py` provides test-compatible API
- Legacy path resolution falls back to `filesystem` section in `defaults.yaml`
