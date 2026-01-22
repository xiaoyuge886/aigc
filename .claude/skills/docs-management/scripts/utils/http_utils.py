#!/usr/bin/env python3
"""
HTTP Utilities with Retry Logic

Provides robust HTTP fetching with exponential backoff retry logic,
proper error handling, and timeout management. Designed to be used
across multiple scraping scripts to eliminate code duplication.

This module is also exercised by the docs-management test suite via
`scripts.utils.http_utils`, so the public API (constants and function
signature) must remain stable.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; config_dir = bootstrap.config_dir

import time
from typing import Any, Iterable

import requests
from requests import Session
from requests.exceptions import (
    ConnectionError,
    Timeout,
    HTTPError,
    RequestException,
)

from .logging_utils import get_or_setup_logger
from .script_utils import HTTP_STATUS_RATE_LIMITED

# Initialize logger
logger = get_or_setup_logger(__file__, log_category="scrape")

# Import config registry for defaults (bootstrap already set up paths)
try:
    if str(config_dir) not in sys.path:
        sys.path.insert(0, str(config_dir))
    from config.config_registry import get_default
except ImportError:
    # Fallback if config registry not available
    def get_default(section: str, key: str, default: Any) -> Any:
        return default

# Public constants expected by tests (loaded from config with fallbacks)
DEFAULT_TIMEOUT: int = get_default('http', 'default_timeout', 30)
DEFAULT_MAX_RETRIES: int = get_default('http', 'default_max_retries', 3)

# Retryable status codes (tests iterate over this collection)
# Load from config with fallback
_retryable_codes = get_default('http', 'retryable_status_codes', [429, 500, 502, 503, 504])
RETRY_STATUS_CODES: list[int] = _retryable_codes if isinstance(_retryable_codes, list) else [429, 500, 502, 503, 504]

# Default user agent for requests (can be overridden by caller headers)
USER_AGENT = get_default('http', 'user_agent', "Claude-Docs-Scraper/1.0 (Educational purposes)")

def is_retryable_error(error: Exception, status_code: int | None = None) -> bool:
    """
    Determine if an error should trigger a retry.

    Args:
        error: The exception that was raised
        status_code: HTTP status code if applicable

    Returns:
        True if the error is retryable, False otherwise

    Retryable errors:
        - ConnectionError, Timeout (network issues)
        - 429 (Rate Limit)
        - 500-series errors (server issues)

    Non-retryable errors:
        - 404 (Not Found)
        - 403 (Forbidden)
        - 401 (Unauthorized)
        - 400 (Bad Request)
    """
    # Network-level errors are always retryable
    if isinstance(error, (ConnectionError, Timeout)):
        return True

    # HTTP errors - check status code
    if isinstance(error, HTTPError):
        if status_code is None:
            # Try to extract status code from error
            if hasattr(error, 'response') and error.response is not None:
                status_code = error.response.status_code

        if status_code is not None:
            # Explicitly retry configured retryable codes
            if status_code in RETRY_STATUS_CODES:
                return True

            # Client errors - not retryable
            if 400 <= status_code < 500:
                return False

    # Unknown errors - don't retry to be safe
    return False

def _merge_headers(custom_headers: dict[str, str | None]) -> dict[str, str]:
    """
    Merge caller headers with default User-Agent.

    Caller-supplied headers always win, including User-Agent overrides.
    """
    base = {"User-Agent": USER_AGENT}
    if custom_headers:
        base.update(custom_headers)
    return base

def _iter_retry_delays(
    max_retries: int,
    initial_delay: float,
    backoff_factor: float,
) -> Iterable[float]:
    """
    Yield delay values for each retry attempt.

    The tests assert an exponential pattern (1s, 2s, 4s with ~10% tolerance),
    so we keep this simple and deterministic.
    """
    delay = initial_delay
    # We yield `max_retries` delays; the initial attempt happens before any sleep.
    for _ in range(max_retries):
        yield delay
        delay *= backoff_factor

def fetch_with_retry(
    url: str,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    timeout: float = DEFAULT_TIMEOUT,
    headers: dict | None = None,
    verify: bool = True,
    session: Session | None = None,
    etag: str | None = None,
    last_modified: str | None = None,
) -> requests.Response:
    """
    Fetch a URL with exponential backoff retry logic.

    Args:
        url: The URL to fetch
        max_retries: Maximum number of retry attempts (default: DEFAULT_MAX_RETRIES)
        initial_delay: Initial backoff duration in seconds (default: 1.0)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        timeout: Request timeout in seconds (default: DEFAULT_TIMEOUT)
        headers: Optional additional headers to include
        verify: Whether to verify SSL certificates (default: True)
        session: Optional requests.Session instance to use
        etag: Optional ETag for conditional request (If-None-Match header)
        last_modified: Optional Last-Modified date for conditional request (If-Modified-Since header)

    Returns:
        requests.Response object on success. If conditional headers were provided and
        server returned 304 Not Modified, response.status_code will be 304 (not raised as error).

    Raises:
        requests.exceptions.HTTPError: For non-retryable HTTP errors (404, 403, etc.)
        requests.exceptions.RequestException: After all retries exhausted

    Example:
        >>> response = fetch_with_retry("https://docs.anthropic.com")
        >>> print(response.status_code)
        200
        >>> content = response.text

        >>> # With conditional request (ETag caching)
        >>> response = fetch_with_retry(
        ...     "https://api.example.com/data",
        ...     etag='"abc123"',
        ...     last_modified='Wed, 21 Oct 2015 07:28:00 GMT'
        ... )
        >>> if response.status_code == 304:
        ...     print("Content unchanged, use cached version")
    """
    request_headers = _merge_headers(headers)

    # Add conditional request headers if provided
    if etag:
        request_headers['If-None-Match'] = etag
        logger.debug(f"Adding If-None-Match header: {etag}")
    if last_modified:
        request_headers['If-Modified-Since'] = last_modified
        logger.debug(f"Adding If-Modified-Since header: {last_modified}")

    # Use provided session or create a short-lived one
    sess = session or Session()

    last_exception: Exception | None = None

    # Attempt counter: 0 = initial attempt, then retries
    attempt_index = 0
    status_code: int | None = None

    # Initial attempt happens before any delay
    while True:
        try:
            logger.debug(f"Fetching {url} (attempt {attempt_index + 1}/{max_retries + 1})")
            request_start = time.time()
            response = sess.get(url, headers=request_headers, timeout=timeout, verify=verify)
            request_duration_ms = (time.time() - request_start) * 1000
            status_code = getattr(response, "status_code", None)
            logger.debug(f"HTTP GET {url} completed in {request_duration_ms:.0f}ms (status={status_code})")

            # Handle 429 (rate limiting) explicitly using Retry-After header.
            if status_code == HTTP_STATUS_RATE_LIMITED:
                if attempt_index >= max_retries:
                    err = HTTPError(f"Max retries exceeded for {url}")
                    last_exception = err
                    logger.error(str(err))
                    raise err

                retry_after = response.headers.get("Retry-After")
                delay = initial_delay * (backoff_factor ** attempt_index)
                if retry_after:
                    try:
                        header_delay = float(retry_after)
                        delay = max(delay, header_delay)
                    except ValueError:
                        # Retry-After might be a date; keep exponential delay
                        pass

                logger.warning(
                    f"HTTP error 429 for {url}, retrying in {delay:.1f}s "
                    f"(attempt {attempt_index + 1}/{max_retries + 1})"
                )
                time.sleep(delay)
                attempt_index += 1
                continue

            # Handle 304 Not Modified - return without raising error
            # This indicates a successful conditional request (content unchanged)
            if status_code == 304:
                logger.debug(f"HTTP 304 Not Modified for {url} (conditional request succeeded)")
                return response

            # For all other statuses, use standard raise_for_status handling.
            response.raise_for_status()

            if attempt_index > 0:
                logger.info(f"Successfully fetched {url} after {attempt_index} retries")
            else:
                logger.debug(f"Successfully fetched {url}")
            return response

        except HTTPError as e:
            if status_code is None and getattr(e, "response", None) is not None:
                status_code = e.response.status_code  # type: ignore[assignment]
            last_exception = e

            if not is_retryable_error(e, status_code):
                logger.error(f"Non-retryable HTTP error {status_code} for {url}: {e}")
                raise

            # Decide whether we can retry again
            if attempt_index >= max_retries:
                logger.error(f"Max retries exceeded for {url}. Last error: {e}")
                raise HTTPError(f"Max retries exceeded for {url}") from e

            # Determine delay (special handling for 429 Retry-After)
            delay = initial_delay * (backoff_factor ** attempt_index)
            if status_code == HTTP_STATUS_RATE_LIMITED:
                retry_after = e.response.headers.get("Retry-After") if e.response else None
                if retry_after:
                    try:
                        header_delay = float(retry_after)
                        # For simplicity and test friendliness, use the header value directly.
                        delay = header_delay
                        logger.warning(
                            f"Rate limited. Retry-After header suggests {delay}s"
                        )
                    except ValueError:
                        # Retry-After might be a date; keep exponential delay
                        pass

            logger.warning(
                f"HTTP error {status_code} for {url}, retrying in {delay:.1f}s "
                f"(attempt {attempt_index + 1}/{max_retries + 1})"
            )
            time.sleep(delay)
            attempt_index += 1
            continue

        except (ConnectionError, Timeout) as e:
            last_exception = e

            if attempt_index >= max_retries:
                logger.error(f"Max retries exceeded for {url}. Last error: {e}")
                raise HTTPError(f"Max retries exceeded for {url}") from e

            delay = initial_delay * (backoff_factor ** attempt_index)
            logger.warning(
                f"Network error for {url}: {type(e).__name__}, retrying in {delay:.1f}s "
                f"(attempt {attempt_index + 1}/{max_retries + 1})"
            )
            time.sleep(delay)
            attempt_index += 1
            continue

        except RequestException as e:
            last_exception = e
            logger.error(f"Request failed for {url}: {e}")
            raise

        # Safety guard; normally loop always returns or raises above
        if attempt_index > max_retries:
            break

    if last_exception:
        raise last_exception
    raise RequestException(f"Failed to fetch {url} after {max_retries} retries")

def get_response_with_timeout(
    url: str,
    timeout: int | None = None,
    headers: dict | None = None
) -> requests.Response:
    """
    Simple wrapper for getting a response with timeout (no retry logic).

    Useful for cases where retry logic is not desired or handled elsewhere.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: DEFAULT_TIMEOUT from config)
        headers: Optional additional headers to include

    Returns:
        requests.Response object

    Raises:
        requests.exceptions.RequestException: On any request failure

    Example:
        >>> response = get_response_with_timeout("https://example.com", timeout=10)
        >>> print(response.status_code)
    """
    if timeout is None:
        timeout = DEFAULT_TIMEOUT
    
    request_headers = _merge_headers(headers)

    logger.debug(f"Fetching {url} (no retry)")
    request_start = time.time()
    response = requests.get(url, headers=request_headers, timeout=timeout)
    request_duration_ms = (time.time() - request_start) * 1000
    logger.debug(f"HTTP GET {url} completed in {request_duration_ms:.0f}ms (status={response.status_code})")
    response.raise_for_status()

    return response

def read_file_with_retry(
    file_path: Path,
    max_retries: int | None = None,
    initial_delay: float | None = None,
    backoff_factor: float = 2.0,
    encoding: str = 'utf-8'
) -> str:
    """
    Read a file with exponential backoff retry logic for transient I/O errors.

    Args:
        file_path: Path to the file to read
        max_retries: Maximum number of retry attempts (default: from config)
        initial_delay: Initial backoff duration in seconds (default: from config)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        encoding: File encoding (default: 'utf-8')

    Returns:
        File contents as string

    Raises:
        FileNotFoundError: If file doesn't exist (not retried)
        PermissionError: After all retries exhausted
        OSError: After all retries exhausted for other I/O errors

    Example:
        >>> content = read_file_with_retry(Path("document.md"))
        >>> print(content[:100])
    """
    # Import config helpers here to avoid circular imports
    try:
        from utils.config_helpers import get_file_io_max_retries, get_file_io_initial_retry_delay
        if max_retries is None:
            max_retries = get_file_io_max_retries()
        if initial_delay is None:
            initial_delay = get_file_io_initial_retry_delay()
    except ImportError:
        # Fallback if config helpers not available
        if max_retries is None:
            max_retries = 3
        if initial_delay is None:
            initial_delay = 0.2

    last_exception: Exception | None = None
    attempt_index = 0

    while attempt_index <= max_retries:
        try:
            logger.debug(f"Reading file {file_path} (attempt {attempt_index + 1}/{max_retries + 1})")
            content = file_path.read_text(encoding=encoding)
            
            if attempt_index > 0:
                logger.info(f"Successfully read {file_path} after {attempt_index} retries")
            else:
                logger.debug(f"Successfully read {file_path}")
            return content

        except FileNotFoundError:
            # File doesn't exist - don't retry
            logger.error(f"File not found: {file_path}")
            raise

        except (PermissionError, OSError) as e:
            last_exception = e
            
            # Check if this is a retryable error (file locked, busy, etc.)
            error_str = str(e).lower()
            is_retryable = (
                'locked' in error_str or
                'busy' in error_str or
                'access is denied' in error_str or
                'permission denied' in error_str or
                'resource temporarily unavailable' in error_str
            )

            if not is_retryable:
                # Non-retryable error (e.g., invalid path, disk full)
                logger.error(f"Non-retryable I/O error for {file_path}: {e}")
                raise

            if attempt_index >= max_retries:
                logger.error(f"Max retries exceeded for {file_path}. Last error: {e}")
                raise OSError(f"Max retries exceeded for {file_path}") from e

            delay = initial_delay * (backoff_factor ** attempt_index)
            logger.warning(
                f"I/O error for {file_path}: {type(e).__name__}, retrying in {delay:.2f}s "
                f"(attempt {attempt_index + 1}/{max_retries + 1})"
            )
            time.sleep(delay)
            attempt_index += 1
            continue

        except Exception as e:
            # Unexpected error - don't retry
            logger.error(f"Unexpected error reading {file_path}: {e}")
            raise

    if last_exception:
        raise last_exception
    raise OSError(f"Failed to read {file_path} after {max_retries} retries")

def write_file_with_retry(
    file_path: Path,
    content: str,
    max_retries: int | None = None,
    initial_delay: float | None = None,
    backoff_factor: float = 2.0,
    encoding: str = 'utf-8'
) -> None:
    """
    Write a file with exponential backoff retry logic for transient I/O errors.

    Args:
        file_path: Path to the file to write
        content: Content to write to the file
        max_retries: Maximum number of retry attempts (default: from config)
        initial_delay: Initial backoff duration in seconds (default: from config)
        backoff_factor: Multiplier for exponential backoff (default: 2.0)
        encoding: File encoding (default: 'utf-8')

    Raises:
        PermissionError: After all retries exhausted
        OSError: After all retries exhausted for other I/O errors

    Example:
        >>> write_file_with_retry(Path("output.md"), "# Title\\n\\nContent")
    """
    # Import config helpers here to avoid circular imports
    try:
        from utils.config_helpers import get_file_io_max_retries, get_file_io_initial_retry_delay
        if max_retries is None:
            max_retries = get_file_io_max_retries()
        if initial_delay is None:
            initial_delay = get_file_io_initial_retry_delay()
    except ImportError:
        # Fallback if config helpers not available
        if max_retries is None:
            max_retries = 3
        if initial_delay is None:
            initial_delay = 0.2

    last_exception: Exception | None = None
    attempt_index = 0

    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)

    while attempt_index <= max_retries:
        try:
            logger.debug(f"Writing file {file_path} (attempt {attempt_index + 1}/{max_retries + 1})")
            file_path.write_text(content, encoding=encoding)
            
            if attempt_index > 0:
                logger.info(f"Successfully wrote {file_path} after {attempt_index} retries")
            else:
                logger.debug(f"Successfully wrote {file_path}")
            return

        except (PermissionError, OSError) as e:
            last_exception = e
            
            # Check if this is a retryable error (file locked, busy, etc.)
            error_str = str(e).lower()
            is_retryable = (
                'locked' in error_str or
                'busy' in error_str or
                'access is denied' in error_str or
                'permission denied' in error_str or
                'resource temporarily unavailable' in error_str
            )

            if not is_retryable:
                # Non-retryable error (e.g., invalid path, disk full)
                logger.error(f"Non-retryable I/O error for {file_path}: {e}")
                raise

            if attempt_index >= max_retries:
                logger.error(f"Max retries exceeded for {file_path}. Last error: {e}")
                raise OSError(f"Max retries exceeded for {file_path}") from e

            delay = initial_delay * (backoff_factor ** attempt_index)
            logger.warning(
                f"I/O error for {file_path}: {type(e).__name__}, retrying in {delay:.2f}s "
                f"(attempt {attempt_index + 1}/{max_retries + 1})"
            )
            time.sleep(delay)
            attempt_index += 1
            continue

        except Exception as e:
            # Unexpected error - don't retry
            logger.error(f"Unexpected error writing {file_path}: {e}")
            raise

    if last_exception:
        raise last_exception
    raise OSError(f"Failed to write {file_path} after {max_retries} retries")

if __name__ == "__main__":
    """
    Simple test cases for http_utils module.

    Run with: python http_utils.py
    """

    print("Testing http_utils module...")
    print("-" * 60)

    # Test 1: Successful fetch
    print("\nTest 1: Fetch a known-good URL")
    try:
        response = fetch_with_retry("https://httpbin.org/get", timeout=10)
        print(f"✓ Success: Status {response.status_code}")
        print(f"  Content length: {len(response.content)} bytes")
    except Exception as e:
        print(f"✗ Failed: {e}")

    # Test 2: 404 error (should not retry)
    print("\nTest 2: Fetch a 404 URL (should fail without retry)")
    try:
        response = fetch_with_retry("https://httpbin.org/status/404", timeout=10)
        print(f"✗ Should have raised HTTPError")
    except HTTPError as e:
        print(f"✓ Correctly raised HTTPError for 404: {e.response.status_code}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test 3: Timeout with retry
    print("\nTest 3: Fetch with very short timeout (should retry)")
    try:
        response = fetch_with_retry(
            "https://httpbin.org/delay/5",
            timeout=1,
            max_retries=2,
            initial_backoff=0.5
        )
        print(f"✗ Should have timed out")
    except Timeout:
        print(f"✓ Correctly timed out and exhausted retries")
    except Exception as e:
        print(f"? Unexpected error: {e}")

    # Test 4: 500 error (should retry)
    print("\nTest 4: Fetch a 500 URL (should retry)")
    try:
        response = fetch_with_retry(
            "https://httpbin.org/status/500",
            timeout=10,
            max_retries=2,
            initial_backoff=0.5
        )
        print(f"✗ Should have raised HTTPError after retries")
    except HTTPError as e:
        print(f"✓ Correctly retried and raised HTTPError for 500: {e.response.status_code}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")

    # Test 5: is_retryable_error function
    print("\nTest 5: is_retryable_error() function")
    test_cases = [
        (ConnectionError("Network error"), None, True, "ConnectionError"),
        (Timeout("Request timeout"), None, True, "Timeout"),
        (HTTPError("404 error"), 404, False, "404 Not Found"),
        (HTTPError("403 error"), 403, False, "403 Forbidden"),
        (HTTPError("429 error"), 429, True, "429 Rate Limit"),
        (HTTPError("500 error"), 500, True, "500 Server Error"),
        (HTTPError("503 error"), 503, True, "503 Service Unavailable"),
    ]

    all_passed = True
    for error, status_code, expected, description in test_cases:
        result = is_retryable_error(error, status_code)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        print(f"  {status} {description}: {'retryable' if result else 'not retryable'} (expected: {'retryable' if expected else 'not retryable'})")

    if all_passed:
        print("  ✓ All is_retryable_error tests passed")

    # Test 6: Simple wrapper
    print("\nTest 6: get_response_with_timeout() wrapper")
    try:
        response = get_response_with_timeout("https://httpbin.org/get", timeout=10)
        print(f"✓ Success: Status {response.status_code}")
    except Exception as e:
        print(f"✗ Failed: {e}")

    print("\n" + "-" * 60)
    print("Testing complete!")
