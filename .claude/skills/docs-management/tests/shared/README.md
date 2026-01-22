# Test Suite for docs-management Skill

This directory contains comprehensive test coverage for the docs-management skill utility modules.

## Test Structure

```text
tests/
├── __init__.py                    # Package initialization
├── conftest.py                    # Pytest configuration and fixtures
├── test_http_utils.py            # Tests for HTTP utilities
├── test_publication_utils.py      # Tests for publication date utilities
├── test_config_loader.py         # Tests for configuration loader
├── test_script_utils.py          # Tests for script utilities
├── test_logging_utils.py         # Tests for logging utilities
├── requirements-test.txt         # Test dependencies
└── README.md                     # This file
```

## Running Tests

**⚠️ CRITICAL: Always run pytest from the skill directory (`.claude/skills/docs-management`) to avoid path resolution errors.**

Pytest automatically detects the skill directory as its rootdir (via `conftest.py` or `pytest.ini`), so paths must be relative to that directory, not the repository root.

### Install Test Dependencies

```bash
# From the skill root directory
cd .claude/skills/docs-management
pip install -r tests/requirements-test.txt
```

### Run All Tests

**RECOMMENDED - Use helper scripts (prevents path doubling issues):**

**Windows (PowerShell):**

```powershell
# From repository root - ALWAYS use helper script (prevents path doubling)
.\.claude\skills\docs-management\.pytest_runner.ps1

# Alternative 1: Use Python-based safe runner with absolute path
$repoRoot = (Get-Location).Path
python "$repoRoot\.claude\skills\docs-management\scripts\run_tests_safely.py"

# Alternative 2: Use separate commands with absolute path resolution
$repoRoot = (Get-Location).Path
$skillDir = Join-Path $repoRoot ".claude" "skills" "docs-management"
Set-Location -LiteralPath $skillDir
python -m pytest tests/
```

**⚠️ CRITICAL:** If you're already in `.claude\skills\docs-management`, using relative paths causes path doubling. Always use absolute paths or helper scripts.

**macOS/Linux:**

```bash
# From repository root - ALWAYS use helper script
bash .claude/skills/docs-management/.pytest_runner.sh

# Alternative (if helper script unavailable)
cd .claude/skills/docs-management
python -m pytest tests/
```

**⚠️ CRITICAL:** Never use `cd .claude/skills/docs-management && python -m pytest` in PowerShell - this causes path doubling. Always use helper scripts or separate commands.

### Run Specific Test File

**Windows (PowerShell):**

```powershell
# Use helper script with arguments
.\.claude\skills\docs-management\.pytest_runner.ps1 tests/test_http_utils.py
.\.claude\skills\docs-management\.pytest_runner.ps1 tests/test_publication_utils.py
```

**macOS/Linux:**

```bash
# Use helper script with arguments
bash .claude/skills/docs-management/.pytest_runner.sh tests/test_http_utils.py
bash .claude/skills/docs-management/.pytest_runner.sh tests/test_publication_utils.py
```

### Run Specific Test

**Windows (PowerShell):**

```powershell
.\.claude\skills\docs-management\.pytest_runner.ps1 tests/test_official_docs_api.py::TestOfficialDocsAPI::test_resolve_doc_id -v
```

**macOS/Linux:**

```bash
bash .claude/skills/docs-management/.pytest_runner.sh tests/test_official_docs_api.py::TestOfficialDocsAPI::test_resolve_doc_id -v
```

### Run with Coverage Report

**Windows (PowerShell):**

```powershell
.\.claude\skills\docs-management\.pytest_runner.ps1 --cov=scripts --cov-report=html --cov-report=term

# View HTML coverage report
# macOS:
open htmlcov/index.html
# Windows:
start htmlcov/index.html
# Linux:
xdg-open htmlcov/index.html
```

### Run in Parallel

**Windows (PowerShell):**

```powershell
.\.claude\skills\docs-management\.pytest_runner.ps1 -n auto
```

**macOS/Linux:**

```bash
bash .claude/skills/docs-management/.pytest_runner.sh -n auto
```

### Verbose Output

**Windows (PowerShell):**

```powershell
.\.claude\skills\docs-management\.pytest_runner.ps1 -v
```

**macOS/Linux:**

```bash
bash .claude/skills/docs-management/.pytest_runner.sh -v
```

## Common Issues

### Path Resolution Errors

If you see errors like `ERROR: file or directory not found: .claude/skills/docs-management/tests/` or path doubling (`.claude\skills\docs-management\.claude\skills\docs-management`), you're running pytest incorrectly.

**Problem:** PowerShell's `&&` operator causes path doubling when used with `cd` if you're already in the skill directory or a subdirectory. The relative path `.claude\skills\docs-management` gets resolved relative to the current directory, causing doubling (`.claude\skills\docs-management\.claude\skills\docs-management`).

**Solution:** ALWAYS use the helper scripts - they resolve paths absolutely from the repo root:

```powershell
# CORRECT - Use PowerShell helper script (works from anywhere)
.\.claude\skills\docs-management\.pytest_runner.ps1

# CORRECT - Use Python-based helper script (works from anywhere, most reliable)
python .claude\skills\docs-management\scripts\run_tests_safely.py

# CORRECT - Use separate commands with absolute path resolution
$repoRoot = (Get-Location).Path
$skillDir = Join-Path $repoRoot ".claude" "skills" "docs-management"
Set-Location -LiteralPath $skillDir
python -m pytest tests/

# WRONG - Causes path doubling if already in skill directory
cd .claude\skills\docs-management && python -m pytest tests/
```

**Why Helper Scripts Work:** Both helper scripts resolve the skill directory absolutely:

- `.pytest_runner.ps1`: Finds repo root, then resolves skill directory absolutely
- `run_tests_safely.py`: Uses `Path(__file__).resolve()` to get absolute script location, then resolves skill directory

### Run with Verbose Output

```bash
pytest -v tests/
```

## Test Coverage Summary

### test_http_utils.py (18 tests)

Tests for `scripts/utils/http_utils.py`:

- ✅ Successful HTTP fetch
- ✅ Retry on 500/503 errors
- ✅ No retry on 404/403 errors
- ✅ Rate limit handling (429 with Retry-After)
- ✅ Exponential backoff timing
- ✅ Max retries exceeded behavior
- ✅ Timeout error handling
- ✅ Connection error handling
- ✅ Custom timeout parameters
- ✅ Custom headers
- ✅ Default retry status codes
- ✅ Jitter in backoff delays
- ✅ SSL verification control

**Coverage Goal:** 95%+ line coverage, 100% of critical paths

### test_publication_utils.py (25 tests)

Tests for `scripts/utils/publication_utils.py`:

- ✅ Extract from article:published_time
- ✅ Extract from article:modified_time
- ✅ Extract from generic date meta tag
- ✅ Extract from HTML time element
- ✅ Extract from CSS class selectors
- ✅ Extraction priority order
- ✅ ISO 8601 date parsing
- ✅ RFC 2822 date parsing
- ✅ Various date separators
- ✅ Timezone handling and UTC conversion
- ✅ Recency checks with custom thresholds
- ✅ Date formatting for index
- ✅ Backward compatibility with existing code

**Coverage Goal:** 90%+ line coverage

### test_config_loader.py (20 tests)

Tests for `scripts/utils/config_loader.py`:

- ✅ Singleton pattern implementation
- ✅ Load sources configuration
- ✅ Load filtering configuration
- ✅ Load tag detection configuration
- ✅ Configuration caching
- ✅ Error handling (missing files, invalid YAML)
- ✅ Cache clearing
- ✅ Relative path resolution
- ✅ Unicode in configuration
- ✅ Large configuration files
- ✅ Thread safety (basic)

**Coverage Goal:** 90%+ line coverage

### test_script_utils.py (12 tests)

Tests for `scripts/utils/script_utils.py`:

- ✅ UTF-8 output configuration
- ✅ Handle missing reconfigure method
- ✅ Idempotent configuration
- ✅ YAML installation check
- ✅ Automatic YAML installation
- ✅ Installation failure handling
- ✅ Error message printing
- ✅ Correct Python executable usage

**Coverage Goal:** 85%+ line coverage

### test_logging_utils.py (16 tests)

Tests for `scripts/utils/logging_utils.py`:

- ✅ Logger creation with name
- ✅ Default log level (INFO)
- ✅ Custom log levels
- ✅ Handler configuration
- ✅ Log formatting
- ✅ Logger reuse (same name)
- ✅ Log level filtering
- ✅ UTF-8 character support
- ✅ No duplicate handlers
- ✅ Thread safety (basic)

**Coverage Goal:** 85%+ line coverage

## Test Coverage Goals

### Overall Coverage Targets

- **Line Coverage:** 90%+ across all utility modules
- **Branch Coverage:** 80%+ for conditional logic
- **Critical Paths:** 100% coverage of error handling and retry logic

### Minimum Coverage Requirements

- `http_utils.py`: 95% (critical for reliability)
- `publication_utils.py`: 90%
- `config_loader.py`: 90%
- `script_utils.py`: 85%
- `logging_utils.py`: 85%

## Adding New Tests

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<FeatureName>`
- Test methods: `test_<specific_behavior>`

**Examples:**

```python
# test_http_utils.py
class TestFetchWithRetry:
    def test_successful_fetch(self):
        """Test successful HTTP fetch on first attempt."""
        pass

    def test_retry_on_500_error(self):
        """Test retry behavior on 500 Internal Server Error."""
        pass
```

### Test Structure Template

```python
"""
Tests for <module_name> module.
"""
import pytest
from unittest.mock import patch, MagicMock

from scripts.utils.<module_name> import <functions>


class Test<FeatureName>:
    """Test suite for <feature> function."""

    def test_<behavior>(self):
        """Test that <specific behavior>."""
        # Arrange
        # ... setup test data

        # Act
        # ... call function

        # Assert
        # ... verify results


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_<edge_case>(self):
        """Test handling of <edge case>."""
        pass
```

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_with_temp_dir(temp_dir):
    """Test using temporary directory fixture."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("content")
    assert test_file.exists()

def test_with_mock_config(mock_sources_config):
    """Test using mock configuration fixture."""
    loader = ConfigLoader(str(mock_sources_config.parent))
    sources = loader.load_sources()
    assert "anthropic-com" in sources
```

### Mocking Guidelines

**HTTP Requests (use responses library):**

```python
@responses.activate
def test_http_call():
    responses.add(
        responses.GET,
        "https://example.com/api",
        json={"status": "ok"},
        status=200
    )

    # Your test code here
```

**Time-dependent Tests (use freezegun):**

```python
@freeze_time("2025-11-16 12:00:00")
def test_recency():
    now = datetime.now(timezone.utc)
    assert now.year == 2025
    assert now.month == 11
```

**Function Patching (use unittest.mock):**

```python
@patch('module.function')
def test_with_mock(mock_function):
    mock_function.return_value = "mocked"
    result = call_code_that_uses_function()
    assert result == "expected"
```

## Running Specific Test Categories

### Run Only Fast Tests

```bash
pytest -m "not slow" tests/
```

### Run Only Integration Tests

```bash
pytest -m integration tests/
```

### Run Only Unit Tests

```bash
pytest -m "not integration" tests/
```

## Continuous Integration

### GitHub Actions Example

```yaml
- name: Run tests with coverage
  run: |
    pip install -r tests/requirements-test.txt
    pytest --cov=scripts.utils --cov-report=xml tests/

- name: Upload coverage to Codecov
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

## Troubleshooting

### Import Errors

If you see import errors when running tests:

```bash
# Ensure the skill directory is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"  # Linux/macOS
$env:PYTHONPATH="$env:PYTHONPATH;$(pwd)"  # Windows PowerShell
```

### Fixture Not Found

If pytest can't find fixtures:

```bash
# Verify conftest.py is in the tests directory
ls tests/conftest.py

# Run with verbose mode to debug
pytest -v --fixtures tests/
```

### Coverage Not Showing

If coverage isn't working:

```bash
# Install coverage dependencies
pip install coverage[toml] pytest-cov

# Verify .coveragerc or pyproject.toml configuration
# Run with explicit source
pytest --cov=scripts/utils tests/
```

## Best Practices

1. **Write Tests First:** Consider TDD for new features
2. **Test Edge Cases:** Don't just test happy paths
3. **Mock External Dependencies:** Use fixtures for HTTP, files, etc.
4. **Keep Tests Independent:** Each test should run in isolation
5. **Use Descriptive Names:** Test names should explain what they test
6. **Document Complex Tests:** Add docstrings explaining why
7. **Maintain Coverage:** Don't let coverage drop below targets
8. **Run Tests Locally:** Before committing changes

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [responses Library](https://github.com/getsentry/responses)
- [freezegun Documentation](https://github.com/spulec/freezegun)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Python Testing Best Practices](https://realpython.com/pytest-python-testing/)

## Questions or Issues?

If you encounter issues with the test suite:

1. Check this README for troubleshooting steps
2. Review conftest.py for available fixtures
3. Examine existing tests for patterns and examples
4. Consult pytest documentation for advanced features

**Last Updated:** 2025-11-16
