#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_docs.py - Fetch documentation from sitemaps and URLs

Automates documentation scraping from:
- Sitemap.xml files (with URL filtering)
- Claude Code docs map (claude_code_docs_map.md)
- Individual URLs

Updates index.yaml with metadata tracking (source URL, hash, fetch date).

Usage:
    # Scrape from sitemap
    python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml \\
                          --filter "/en/docs/" \\
                          --output platform-docs/

    # Scrape from docs map
    python scrape_docs.py --docs-map https://code.claude.com/docs/en/claude_code_docs_map.md \\
                          --output claude-code/

    # Scrape specific URL
    python scrape_docs.py --url https://docs.claude.com/en/docs/intro \\
                          --output platform-docs/intro.md

Dependencies:
    pip install requests beautifulsoup4 markdownify pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
import json
import os
import re
import subprocess
import threading
import time
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from urllib.parse import urlparse

from utils.script_utils import configure_utf8_output, format_duration, HTTP_STATUS_RATE_LIMITED
from utils.path_config import get_base_dir, get_index_path
from utils.config_helpers import (
    get_scraper_user_agent,
    get_index_lock_retry_delay,
    get_index_lock_retry_backoff,
    get_scraping_rate_limit,
    get_scraping_header_rate_limit,
    get_scraping_max_workers,
    get_scraping_progress_lock_timeout,
    get_scraping_index_lock_timeout,
    get_http_timeout,
    get_http_max_retries,
    get_http_initial_retry_delay,
    get_http_markdown_request_timeout,
    get_validation_timeout,
    get_scraping_progress_interval,
    get_scraping_progress_url_interval
)
from utils.http_utils import fetch_with_retry
configure_utf8_output()

# Lock retry delays (loaded from config via config_helpers)
LOCK_RETRY_DELAY = get_index_lock_retry_delay()  # Delay between lock acquisition attempts
LOCK_RETRY_BACKOFF = get_index_lock_retry_backoff()  # Delay after failed lock acquisition

# Ensure unbuffered output for real-time streaming
if sys.stdout.isatty():
    # If running in terminal, use line buffering
    sys.stdout.reconfigure(line_buffering=True)
else:
    # If piped (e.g., from subprocess), force unbuffered
    sys.stdout.reconfigure(line_buffering=True)

# Thread-safe print helper for parallel processing (threading imported above)
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print that flushes immediately for real-time output"""
    with _print_lock:
        print(*args, **kwargs, flush=True)

from utils.logging_utils import get_or_setup_logger

# Get source name from environment (set by scrape_all_sources.py for parallel worker identification)
_source_name = os.environ.get('CLAUDE_DOCS_SOURCE_NAME', '')
_log_prefix = f"[{_source_name}] " if _source_name else ""

logger = get_or_setup_logger(__file__, log_category="scrape")

from utils.script_utils import ensure_yaml_installed

try:
    import requests
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip install requests beautifulsoup4 markdownify")
    sys.exit(1)

yaml = ensure_yaml_installed()

# Import content filter for config-driven content filtering
try:
    from utils.content_filter import ContentFilter
    HAS_CONTENT_FILTER = True
except ImportError:
    HAS_CONTENT_FILTER = False
    logger.warning("ContentFilter not available - content filtering disabled")

class RateLimiter:
    """Thread-safe rate limiter for controlling request frequency"""
    
    def __init__(self, delay: float):
        """
        Initialize rate limiter
        
        Args:
            delay: Minimum delay between requests in seconds
        """
        self.delay = delay
        self.lock = threading.Lock()
        self.last_request_time = 0.0
    
    def wait(self):
        """Wait if necessary to maintain rate limit"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.delay:
                sleep_time = self.delay - time_since_last
                time.sleep(sleep_time)
            self.last_request_time = time.time()

# Import index_manager for large file support
try:
    from management.index_manager import IndexManager
except ImportError:
    # Fallback if index_manager not available
    IndexManager = None

# Import metadata extractor
try:
    from management.extract_metadata import MetadataExtractor
except ImportError:
    MetadataExtractor = None

# Publication date extraction patterns (for Anthropic blog posts)
DATE_PATTERNS: list[tuple] = [
    # Examples: "Mar 27, 2025●8 min read", "Mar 7, 2024"
    (re.compile(r'\b([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})'), "%b %d, %Y"),
    # Examples: "March 27, 2025"
    (re.compile(r'\b([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})'), "%B %d, %Y"),
]

def extract_publication_date(content: str) -> str | None:
    """
    Extract publication date from article content (Anthropic blog format).

    Args:
        content: Markdown content to parse

    Returns:
        ISO date string (YYYY-MM-DD) if found, otherwise None
    """
    # Only inspect first ~40 lines; dates are typically near the top
    lines = content.splitlines()[:40]
    for line in lines:
        for pattern, fmt in DATE_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            try:
                # Join matched groups back into a single date string
                date_str = m.group(0)
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except Exception:
                continue
    return None

class DocScraper:
    """Documentation scraper with sitemap and docs map support"""

    def __init__(self, base_output_dir: Path | None = None, rate_limit: float | None = None,
                 header_rate_limit: float | None = None, trust_existing: bool = False,
                 skip_age_days: int = 0, max_workers: int | None = None, try_markdown: bool = True):
        """
        Initialize scraper

        Args:
            base_output_dir: Base directory for canonical storage. If None, uses config default.
            rate_limit: Delay between requests in seconds. If None, uses config default.
            header_rate_limit: Delay between HEAD requests in seconds. If None, uses config default.
            trust_existing: If True, skip hash check when HTTP headers unavailable (default: False)
            skip_age_days: Skip files fetched within this many days if hash matches (default: 0 = today only)
            max_workers: Maximum parallel workers for URL processing. If None, uses config default.
            try_markdown: If True, try fetching .md URLs before HTML conversion (default: True)
        """
        # Use config defaults if not provided
        self.base_output_dir = base_output_dir if base_output_dir else get_base_dir()
        self.rate_limit = rate_limit if rate_limit is not None else get_scraping_rate_limit()
        self.header_rate_limit = header_rate_limit if header_rate_limit is not None else get_scraping_header_rate_limit()
        self.trust_existing = trust_existing
        self.skip_age_days = skip_age_days
        self.max_workers = max_workers if max_workers is not None else get_scraping_max_workers()
        self.try_markdown = try_markdown
        self.index_path = get_index_path(self.base_output_dir)
        self.progress_file = self.base_output_dir / ".scrape_progress.json"
        
        # Thread-safe rate limiters (use instance values, not parameters)
        self.rate_limiter = RateLimiter(self.rate_limit)
        self.header_rate_limiter = RateLimiter(self.header_rate_limit)
        
        # Use thread-local sessions for thread safety
        self._session_local = threading.local()
        self.session_headers = {
            'User-Agent': get_scraper_user_agent()
        }
        
        # Initialize index manager if available
        if IndexManager:
            self.index_manager = IndexManager(base_output_dir)
        else:
            self.index_manager = None
        
        # Track 404 URLs for drift detection
        self.url_404s: set[str] = set()

        # Track skip reasons for observability (thread-safe counters)
        self._skip_lock = threading.Lock()
        self.skip_reasons: dict[str, int] = {
            'http_headers_unchanged': 0,
            'trust_existing_no_headers': 0,
            'content_hash_unchanged': 0,
            'fetched_within_age': 0,
            'fetched_today': 0,
            'resume_already_scraped': 0,
        }
    
    @property
    def session(self):
        """Get thread-local session"""
        if not hasattr(self._session_local, 'session'):
            self._session_local.session = requests.Session()
            self._session_local.session.headers.update(self.session_headers)
        return self._session_local.session

    def _track_skip(self, reason: str) -> None:
        """Thread-safe skip reason tracking for observability."""
        with self._skip_lock:
            if reason in self.skip_reasons:
                self.skip_reasons[reason] += 1
            else:
                self.skip_reasons[reason] = 1

    def get_skip_summary(self) -> str:
        """Get formatted summary of skip reasons for logging."""
        with self._skip_lock:
            active_reasons = {k: v for k, v in self.skip_reasons.items() if v > 0}
            if not active_reasons:
                return "No skips"
            parts = [f"{k}={v}" for k, v in active_reasons.items()]
            return f"SKIP REASONS: {', '.join(parts)}"
    
    def load_progress(self) -> set[str]:
        """Load already-scraped URLs from progress file (parallel-safe with locking)"""
        if not self.progress_file.exists():
            return set()
        
        lock_file = self.progress_file.parent / '.progress.lock'
        start_time = time.time()
        timeout = get_scraping_progress_lock_timeout()
        
        # Acquire lock
        while time.time() - start_time < timeout:
            try:
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except OSError:
                time.sleep(LOCK_RETRY_DELAY)
                continue
        else:
            print(f"  ⚠️  Warning: Could not acquire progress lock, retrying...")
            return set()  # Return empty set if lock fails
        
        try:
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return set(json.load(f))
            except Exception as e:
                print(f"  ⚠️  Error loading progress: {e}")
                return set()
        finally:
            # Release lock
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except Exception:
                pass
    
    def save_progress(self, url: str):
        """Save successfully scraped URL (parallel-safe with locking)"""
        lock_file = self.progress_file.parent / '.progress.lock'
        start_time = time.time()
        timeout = get_scraping_progress_lock_timeout()
        
        # Acquire lock
        while time.time() - start_time < timeout:
            try:
                fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except OSError:
                time.sleep(LOCK_RETRY_DELAY)
                continue
        else:
            print(f"  ⚠️  Warning: Could not acquire progress lock, skipping save...")
            return
        
        try:
            progress = self.load_progress()
            progress.add(url)
            try:
                with open(self.progress_file, 'w', encoding='utf-8') as f:
                    json.dump(list(progress), f, indent=2)
            except Exception as e:
                print(f"  ⚠️  Error saving progress: {e}")
        finally:
            # Release lock
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except Exception:
                pass
    
    def clear_progress(self):
        """Clear progress file"""
        if self.progress_file.exists():
            try:
                self.progress_file.unlink()
            except Exception:
                pass

    def fetch_url(self, url: str, max_retries: int | None = None, base_delay: float | None = None) -> tuple[str | None, str | None]:
        """
        Fetch content from URL with retry logic and exponential backoff

        Args:
            url: URL to fetch
            max_retries: Maximum retry attempts. If None, uses config default.
            base_delay: Base delay in seconds for exponential backoff. If None, uses config default.

        Returns:
            Tuple of (content, final_url) or (None, None) if fetch fails permanently
        """
        # Use config defaults if not provided
        if max_retries is None:
            max_retries = get_http_max_retries()
        if base_delay is None:
            base_delay = get_http_initial_retry_delay()
        
        for attempt in range(max_retries):
            try:
                if attempt == 0:
                    print(f"  Fetching: {url}")
                else:
                    print(f"  Fetching: {url} (attempt {attempt + 1}/{max_retries})")
                
                self.rate_limiter.wait()  # Thread-safe rate limiting
                http_timeout = get_http_timeout()
                response = self.session.get(url, timeout=http_timeout)
                response.raise_for_status()
                return (response.text, response.url)
                
            except requests.HTTPError as e:
                status_code = e.response.status_code if e.response else None
                
                # 404 = permanent failure, don't retry
                if status_code == 404:
                    print(f"  ❌ 404 Not Found: {url}")
                    # Track 404 for drift detection
                    self.url_404s.add(url)
                    return (None, None)
                
                # 429 = rate limit, retry with longer delay
                elif status_code == HTTP_STATUS_RATE_LIMITED:
                    if attempt < max_retries - 1:
                        retry_after = int(e.response.headers.get('Retry-After', base_delay * (2 ** attempt)))
                        wait_time = max(retry_after, base_delay * (2 ** attempt))
                        print(f"  ⚠️  Rate limited (429), retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ❌ Rate limit exceeded after {max_retries} attempts: {url}")
                        return (None, None)
                
                # 5xx = server error, retry
                elif status_code and status_code >= 500:
                    if attempt < max_retries - 1:
                        wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                        print(f"  ⚠️  Server error {status_code} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"  ❌ Server error {status_code} after {max_retries} attempts: {url}")
                        return (None, None)
                
                # Other HTTP errors, don't retry
                else:
                    print(f"  ❌ HTTP {status_code}: {url}")
                    return (None, None)
                    
            except requests.ConnectionError:
                # Network error, retry
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"  ⚠️  Connection error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  ❌ Connection error after {max_retries} attempts: {url}")
                    return (None, None)
                    
            except requests.Timeout:
                # Timeout, retry
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"  ⚠️  Timeout (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  ❌ Timeout after {max_retries} attempts: {url}")
                    return (None, None)
                    
            except requests.RequestException:
                # Other request errors, retry once
                if attempt < max_retries - 1:
                    wait_time = base_delay * (2 ** attempt)
                    print(f"  ⚠️  Request error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"  ❌ Request error after {max_retries} attempts: {url}")
                    return (None, None)
        
        return (None, None)

    def try_fetch_markdown(self, url: str) -> tuple[str | None, str | None, str | None]:
        """
        Try to fetch clean markdown from URL with retry logic

        For URLs ending in .md, fetches directly.
        For other URLs, resolves redirects and appends .md before fetching.

        Args:
            url: URL to try (with or without .md extension)

        Returns:
            Tuple of (content, fetch_method, final_url) where:
            - content: Markdown content or None
            - fetch_method: "markdown" if successful, or None
            - final_url: The final URL after redirects (without .md extension), or None
        """
        # Skip markdown attempt if disabled
        if not self.try_markdown:
            return (None, None, None)

        try:
            # Handle URLs that already end with .md vs URLs that need .md appended
            if url.endswith('.md'):
                # URL already has .md extension - fetch directly without redirect resolution
                markdown_url = url
                final_url = url.removesuffix('.md')  # Remove .md for final_url
                print(f"  Trying markdown URL (direct): {markdown_url}")
            else:
                # URL doesn't have .md - resolve redirects first, then append .md
                # First, resolve redirects to get the final URL
                # We use a HEAD request to be efficient
                head_timeout = get_http_timeout()
                self.rate_limiter.wait()

                # Use session to persist cookies/headers across redirects
                head_response = self.session.head(url, timeout=head_timeout, allow_redirects=True)

                # Get the final URL after redirects
                final_url = head_response.url

                # If redirected, log it
                if final_url != url:
                    print(f"  ↪️  Redirected: {url} -> {final_url}")

                # Now append .md to the FINAL url
                if final_url.endswith('/'):
                    final_url = final_url[:-1]

                if final_url.endswith('.md'):
                    markdown_url = final_url
                else:
                    markdown_url = f"{final_url}.md"

                print(f"  Trying markdown URL: {markdown_url}")

            # Common fetch logic for both paths
            markdown_timeout = get_http_markdown_request_timeout()
            max_retries = get_http_max_retries()
            initial_delay = get_http_initial_retry_delay()

            # Use fetch_with_retry for robust retry logic with exponential backoff
            response = fetch_with_retry(
                markdown_url,
                max_retries=max_retries,
                initial_delay=initial_delay,
                timeout=markdown_timeout,
                session=self.session
            )

            time.sleep(self.rate_limiter.delay)  # Rate limiting

            content = response.text

            # Verify content is markdown (starts with # or --- for frontmatter)
            content_stripped = content.strip()
            if content_stripped.startswith('#') or content_stripped.startswith('---'):
                print(f"  ✅ Successfully fetched clean markdown from {markdown_url}")
                return (content, "markdown", final_url)
            else:
                print(f"  ⚠️  URL returned content but doesn't appear to be markdown")
                return (None, None, None)

        except requests.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            # If the HEAD request failed (e.g. 404 on the base URL), we can't proceed
            # If the .md request failed, we catch it here too

            # Determine which request failed
            failed_url = e.request.url if e.request else "unknown"

            if status_code == 404:
                # Track 404 for drift detection ONLY if it was the markdown URL that failed
                # If the base URL failed, it's a different issue
                if 'markdown_url' in locals() and failed_url == markdown_url:
                    self.url_404s.add(markdown_url)
                    print(f"  ❌ Markdown URL 404: {markdown_url}")
                else:
                    print(f"  ❌ Base URL 404: {url}")
            else:
                status_str = str(status_code) if status_code else 'HTTP error'
                print(f"  ℹ️  Markdown URL not available ({status_str}), will try HTML conversion")
            return (None, None, None)
        except (requests.ConnectionError, requests.Timeout, requests.RequestException) as e:
            # Network errors are already retried by fetch_with_retry, but if all retries fail,
            # we fall back to HTML conversion
            error_type = type(e).__name__
            print(f"  ℹ️  Markdown URL not available ({error_type}), will try HTML conversion")
            return (None, None, None)

    def parse_sitemap(self, sitemap_url: str, url_filter: str | None = None,
                      max_age_days: int | None = None) -> list[str]:
        """
        Parse sitemap.xml and extract URLs

        Args:
            sitemap_url: URL to sitemap.xml
            url_filter: Optional regex pattern to filter URLs (e.g., "/en/docs/")
            max_age_days: Optional maximum age in days (filter by <lastmod> date)

        Returns:
            List of matching URLs
        """
        print(f"📄 Parsing sitemap: {sitemap_url}")
        content, _ = self.fetch_url(sitemap_url)
        if not content:
            return []

        try:
            root = ET.fromstring(content)
            # Handle XML namespace
            namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

            # Extract URLs with optional date filtering
            urls = []
            cutoff_date = None

            if max_age_days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=max_age_days)
                print(f"  Filtering by max age: {max_age_days} days (since {cutoff_date.strftime('%Y-%m-%d')})")

            for url_elem in root.findall('.//ns:url', namespace):
                loc = url_elem.find('ns:loc', namespace)
                if loc is None or loc.text is None:
                    continue

                url = loc.text

                # Apply date filter if specified
                if cutoff_date:
                    lastmod = url_elem.find('ns:lastmod', namespace)
                    if lastmod is not None and lastmod.text:
                        try:
                            lastmod_date = datetime.fromisoformat(lastmod.text.replace('Z', '+00:00'))
                            if lastmod_date < cutoff_date:
                                continue  # Skip URLs older than cutoff
                        except ValueError:
                            # If date parsing fails, include the URL (don't filter out)
                            pass

                urls.append(url)

            print(f"  Found {len(urls)} URLs in sitemap")

            # Apply URL pattern filter if provided
            if url_filter:
                # Auto-fix Git Bash path conversion issue (Windows-specific)
                # Git Bash converts /en/docs/ to C:/Program Files/Git/en/docs/
                original_filter = url_filter
                if re.match(r'^[A-Z]:[/\\]', url_filter):
                    # Try to detect and fix Git Bash path conversion
                    # Pattern: C:/Program Files/Git/{path} -> /{path}
                    git_path_pattern = re.compile(r'^[A-Z]:[/\\].*?[/\\]Git[/\\](.+)$', re.IGNORECASE)
                    match = git_path_pattern.match(url_filter)
                    if match:
                        # Extract path after Git/ and restore original pattern
                        restored_path = '/' + match.group(1).replace('\\', '/')
                        url_filter = restored_path
                        print(f"  ⚠️  Auto-fixed Git Bash path conversion: {original_filter} -> {url_filter}")
                    else:
                        # Windows path but not Git Bash conversion - this is unexpected
                        print(f"\n  ⚠️  WARNING: Filter pattern appears to be a Windows path: {url_filter}")
                        print(f"  This may not work as expected. Consider using a Unix-style path pattern.\n")

                pattern = re.compile(url_filter)
                urls = [url for url in urls if pattern.search(url)]
                print(f"  Filtered to {len(urls)} URLs matching pattern: {url_filter}")

            return urls
        except ET.ParseError as e:
            print(f"  ❌ Failed to parse sitemap XML: {e}")
            return []

    def parse_docs_map(self, docs_map_url: str) -> list[str]:
        """
        Parse claude_code_docs_map.md and extract documentation URLs

        Args:
            docs_map_url: URL to docs map markdown file

        Returns:
            List of documentation URLs
        """
        print(f"📋 Parsing docs map: {docs_map_url}")
        content, _ = self.fetch_url(docs_map_url)
        if not content:
            return []

        # Extract URLs from markdown links
        # Pattern: [text](url) where url ends with .md
        pattern = r'\[([^\]]+)\]\((https?://[^\)]+\.md)\)'
        matches = re.findall(pattern, content)
        urls = [url for title, url in matches]

        print(f"  Found {len(urls)} documentation URLs")
        return urls

    def parse_llms_txt(self, llms_txt_url: str) -> list[str]:
        """
        Parse llms.txt and extract documentation URLs

        Args:
            llms_txt_url: URL to llms.txt file

        Returns:
            List of documentation URLs
        """
        print(f"📋 Parsing llms.txt: {llms_txt_url}")
        content, _ = self.fetch_url(llms_txt_url)
        if not content:
            return []

        # Extract base URL for resolving relative paths
        from urllib.parse import urlparse
        parsed = urlparse(llms_txt_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Use LlmsParser from llms_parser module with base_url for relative path resolution
        from llms_parser import LlmsParser
        parser = LlmsParser(base_url=base_url)
        urls = parser.extract_urls(content)

        print(f"  Found {len(urls)} documentation URLs")
        return urls

    def html_to_markdown(self, html_content: str, source_url: str | None = None) -> str:
        """
        Convert HTML content to markdown

        Args:
            html_content: HTML string
            source_url: Optional source URL for domain-specific filtering

        Returns:
            Markdown string
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        # Pre-process media elements (videos, YouTube embeds) BEFORE removing scripts
        # This extracts YouTube video data from JSON in script tags before they're removed
        self._preprocess_media_elements(soup)

        # Remove script and style elements (after extracting media data)
        for element in soup(['script', 'style', 'nav', 'header', 'footer']):
            element.decompose()

        # Convert to markdown
        markdown = md(str(soup), heading_style="ATX")

        # Fix Next.js image optimization URLs (/_next/image?url=...)
        # These are CDN proxy URLs that should be converted back to actual image URLs
        markdown = self._fix_nextjs_image_urls(markdown)

        # Clean up excessive whitespace
        markdown = re.sub(r'\n\n\n+', '\n\n', markdown)

        # Apply domain-specific content filtering
        if source_url:
            markdown = self._filter_domain_specific_content(markdown, source_url)

        # Remove trailing page titles (e.g., "Title \ Anthropic" at end of document)
        markdown = self._remove_trailing_page_title(markdown)

        return markdown.strip()
    
    def _filter_domain_specific_content(self, content: str, source_url: str) -> str:
        """
        Apply config-driven content filtering to remove boilerplate/navigation elements
        
        Uses ContentFilter for source-aware filtering based on config/content_filtering.yaml.
        Removes site navigation, marketing sections, and related articles from news/blog content
        while preserving technical documentation cross-references.
        
        Args:
            content: Markdown content
            source_url: Source URL for domain detection
        
        Returns:
            Filtered markdown content
        """
        if not HAS_CONTENT_FILTER:
            # ContentFilter not available, return unfiltered content
            return content
        
        try:
            # Convert URL to source path for filter detection
            # e.g., https://www.anthropic.com/news/article -> anthropic-com/news/article.md
            parsed = urlparse(source_url)
            domain = parsed.netloc.replace('www.', '').replace('.', '-')
            url_path = parsed.path.strip('/')
            source_path = f"{domain}/{url_path}.md" if url_path else f"{domain}/index.md"
            
            # Apply config-driven filtering
            filter = ContentFilter()
            filtered_content, stats = filter.filter_content(content, source_path=source_path)
            
            # Log filtering results if significant content was removed (include reasons for observability)
            if stats.get('sections_removed', 0) > 0:
                removed_sections = stats.get('removed_sections', [])
                if removed_sections:
                    # Extract unique filter reasons for summary
                    reasons = set(s.get('reason', 'unknown') for s in removed_sections)
                    headings = [s.get('heading', '')[:50] for s in removed_sections[:3]]  # First 3 headings
                    reason_summary = ', '.join(reasons)
                    heading_preview = '; '.join(h for h in headings if h)
                    logger.info(f"Filtered {stats['sections_removed']} sections from {source_url}: reasons=[{reason_summary}], headings=[{heading_preview}]")
                else:
                    logger.info(f"Filtered {stats['sections_removed']} sections from {source_url}")
            
            return filtered_content
        
        except Exception as e:
            # If filtering fails, log warning and return unfiltered content
            logger.warning(f"Content filtering failed for {source_url}: {e}")
            return content

    def _preprocess_media_elements(self, soup: BeautifulSoup) -> None:
        """
        Pre-process media elements (videos, YouTube embeds) before markdownify conversion.
        
        This method modifies the soup in-place, replacing media elements with markdown-friendly
        alternatives that will render properly in GitHub/VS Code markdown preview.
        
        Handles:
        - YouTube iframes: Converts to clickable thumbnail images
        - YouTube embeds in Next.js/Sanity JSON data: Extracts and adds as thumbnails
        - Video elements: Converts to descriptive text links
        
        Args:
            soup: BeautifulSoup object to modify in-place
        """
        # Track YouTube video IDs already present as thumbnail images (to avoid duplicates)
        # We only skip if there's already an image linking to YouTube, not just text links
        existing_youtube_thumbnail_ids = set()
        
        # Find existing YouTube thumbnail links (images that link to YouTube)
        for img in soup.find_all('img'):
            parent = img.parent
            if parent and parent.name == 'a':
                href = parent.get('href', '')
                match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)', href)
                if match:
                    existing_youtube_thumbnail_ids.add(match.group(1))
        
        # Also check for YouTube thumbnail URLs in images
        for img in soup.find_all('img'):
            src = img.get('src', '')
            match = re.search(r'img\.youtube\.com/vi/([a-zA-Z0-9_-]+)/', src)
            if match:
                existing_youtube_thumbnail_ids.add(match.group(1))
        
        # Extract YouTube video IDs from Next.js/Sanity JSON data in script tags
        # These are JavaScript-rendered embeds that don't exist in the static HTML
        json_youtube_ids = []
        youtube_url_pattern = re.compile(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)')
        
        for script in soup.find_all('script'):
            text = script.string or ''
            # Look for YouTube URLs in script content (handles both regular and escaped JSON)
            # Only consider scripts that look like they contain video embed data
            if 'embedUrl' in text or ('_type' in text and 'video' in text.lower()):
                for match in youtube_url_pattern.finditer(text):
                    video_id = match.group(1)
                    # Only skip if already exists as a thumbnail, not just a text link
                    if video_id not in existing_youtube_thumbnail_ids and video_id not in json_youtube_ids:
                        json_youtube_ids.append(video_id)
        
        # Add YouTube videos from JSON data to the content
        # Insert them at the beginning of the article/main content
        if json_youtube_ids:
            # Find the main content area or first heading
            main_content = soup.find('main') or soup.find('article') or soup.find('body')
            if main_content:
                # Find the first h1 or h2 to insert after
                first_heading = main_content.find(['h1', 'h2'])
                insert_point = first_heading if first_heading else main_content
                
                for video_id in json_youtube_ids:
                    thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    markdown_text = f"[![Video](https://img.youtube.com/vi/{video_id}/maxresdefault.jpg)](https://www.youtube.com/watch?v={video_id})"
                    
                    new_tag = soup.new_tag('p')
                    new_tag.string = markdown_text
                    
                    # Insert after the heading or at the start
                    if first_heading:
                        first_heading.insert_after(new_tag)
                    else:
                        insert_point.insert(0, new_tag)
        
        # Process YouTube iframes - convert to clickable thumbnail images
        # YouTube embeds use iframes with src like:
        # - https://www.youtube.com/embed/VIDEO_ID
        # - https://www.youtube-nocookie.com/embed/VIDEO_ID?params
        youtube_pattern = re.compile(r'youtube(?:-nocookie)?\.com/embed/([a-zA-Z0-9_-]+)')
        
        for iframe in soup.find_all('iframe'):
            src = iframe.get('src', '') or iframe.get('data-src', '')
            match = youtube_pattern.search(src)
            if match:
                video_id = match.group(1)
                # Get title from iframe if available
                title = iframe.get('title', 'Video')
                # Create clickable thumbnail markdown
                # Format: [![alt](thumbnail_url)](video_url)
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                markdown_text = f"[![{title}]({thumbnail_url})]({video_url})"
                
                # Replace iframe with a text node containing markdown
                new_tag = soup.new_tag('p')
                new_tag.string = markdown_text
                iframe.replace_with(new_tag)
            else:
                # Non-YouTube iframe - remove it to avoid empty content
                iframe.decompose()
        
        # Also check for div elements that might contain YouTube embed data
        # Some sites use data attributes instead of direct iframes
        for div in soup.find_all('div', attrs={'data-original-tag': 'iframe'}):
            src = div.get('src', '')
            match = youtube_pattern.search(src)
            if match:
                video_id = match.group(1)
                title = div.get('title', 'Video')
                thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                markdown_text = f"[![{title}]({thumbnail_url})]({video_url})"
                
                new_tag = soup.new_tag('p')
                new_tag.string = markdown_text
                div.replace_with(new_tag)
        
        # Process video elements - convert to descriptive links
        for video in soup.find_all('video'):
            # Get video source URL from src attribute or nested source element
            video_url = video.get('src', '')
            if not video_url:
                source = video.find('source')
                if source:
                    video_url = source.get('src', '')
            
            if video_url:
                # Create descriptive link markdown
                markdown_text = f"[Video]({video_url})"
                
                new_tag = soup.new_tag('p')
                new_tag.string = markdown_text
                video.replace_with(new_tag)
            else:
                # No valid source found, remove empty video element
                video.decompose()

    def _fix_nextjs_image_urls(self, markdown: str) -> str:
        """
        Fix Next.js image optimization URLs in markdown content.

        Next.js uses /_next/image?url=... for image optimization/CDN proxy.
        These URLs are not portable and should be converted back to actual image URLs.

        Example:
            /_next/image?url=https%3A%2F%2Fexample.com%2Fimage.png&w=1920&q=75
            -> https://example.com/image.png

        Args:
            markdown: Markdown content that may contain Next.js image URLs

        Returns:
            Markdown with Next.js image URLs converted to actual image URLs
        """
        from urllib.parse import unquote

        # Pattern matches /_next/image?url=ENCODED_URL followed by optional query params like &w=3840&q=75
        # Must capture everything up to the closing ) to remove trailing CDN params
        pattern = re.compile(r'/_next/image\?url=([^)&\s]+)(?:&[^)\s]*)?')

        def replace_nextjs_url(match):
            encoded_url = match.group(1)
            # URL decode the actual image URL
            actual_url = unquote(encoded_url)
            # Remove any trailing query params like ?w=3840&q=75 from the decoded URL
            if '?' in actual_url:
                actual_url = actual_url.split('?')[0]
            return actual_url

        return pattern.sub(replace_nextjs_url, markdown)

    def _remove_trailing_page_title(self, markdown: str) -> str:
        """
        Remove trailing page title lines that appear at the end of Anthropic docs.

        HTML-to-markdown conversion sometimes captures the <title> element content
        at the end of the document (from <noscript> or similar tags), resulting in
        lines like "Article Title \\ Anthropic" appearing after the main content.

        Args:
            markdown: Markdown content that may have trailing title

        Returns:
            Markdown with trailing title line removed if present
        """
        lines = markdown.rstrip().split('\n')

        # Check if last non-empty line matches pattern "... \ Anthropic" or "... \\ Anthropic"
        # The backslash may be escaped in markdown
        if lines:
            last_line = lines[-1].strip()
            # Match patterns like "Title \ Anthropic" or "Title \\ Anthropic"
            if re.match(r'^.+\s*\\+\s*Anthropic$', last_line):
                lines = lines[:-1]
                # Also remove any trailing empty lines that were before the title
                while lines and not lines[-1].strip():
                    lines.pop()

        return '\n'.join(lines)

    def normalize_for_hash(self, content: str) -> str:
        """
        Normalize content for stable hash comparison.

        This removes volatile elements that change between scrapes but don't
        represent meaningful content changes (e.g., rotating redirect GUIDs).

        Args:
            content: Content to normalize

        Returns:
            Normalized content for hash comparison
        """
        # Normalize claude.ai redirect GUIDs (e.g., claude.ai/redirect/website.v1.{uuid})
        # These GUIDs rotate between scrapes but the destination remains the same
        pattern = r'(claude\.ai/redirect/website\.v1\.)[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
        normalized = re.sub(pattern, r'\1NORMALIZED', content)
        return normalized

    def calculate_hash(self, content: str, normalize: bool = True) -> str:
        """
        Calculate SHA-256 hash of content

        Args:
            content: Content to hash
            normalize: If True, normalize content before hashing to ignore
                      volatile elements like rotating GUIDs (default: True)

        Returns:
            SHA-256 hash as hex string with 'sha256:' prefix
        """
        if normalize:
            content = self.normalize_for_hash(content)
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"sha256:{hash_obj.hexdigest()}"
    
    def normalize_etag(self, etag: str | None) -> str | None:
        """
        Normalize ETag for comparison (handles weak ETags like W/"hash")
        
        Args:
            etag: ETag string (may include W/ prefix and quotes)
        
        Returns:
            Normalized ETag string (hash only, no quotes or W/ prefix) or None
        """
        if etag is None:
            return None
        
        # Handle empty string
        if etag == '':
            return ''
        
        # Remove W/ prefix for weak ETags first (before removing quotes)
        # This handles cases like W/"hash" -> "hash" -> hash
        if etag.startswith('W/'):
            etag = etag[2:]
        
        # Remove quotes (both single and double, from start and end)
        # Do this after removing W/ prefix to handle W/"hash" correctly
        etag = etag.strip('"').strip("'")
        
        return etag
    
    def check_http_headers(self, url: str, existing_etag: str | None = None, 
                          existing_last_modified: str | None = None) -> bool | None:
        """
        Check HTTP headers (ETag, Last-Modified) for fast change detection
        
        Args:
            url: URL to check
            existing_etag: Existing ETag from frontmatter
            existing_last_modified: Existing Last-Modified from frontmatter
        
        Returns:
            True if unchanged (skip), False if changed (scrape), None if headers unavailable
        """
        try:
            # Use HEAD request for efficiency (with faster rate limit)
            self.header_rate_limiter.wait()  # Thread-safe rate limiting
            head_timeout = get_http_timeout()  # Use config default timeout for HEAD requests
            head_response = self.session.head(url, timeout=head_timeout, allow_redirects=True)
            head_response.raise_for_status()
            
            # Check ETag (most reliable)
            if 'ETag' in head_response.headers and existing_etag:
                current_etag_raw = head_response.headers['ETag']
                current_etag = self.normalize_etag(current_etag_raw)
                existing_etag_normalized = self.normalize_etag(existing_etag)
                if current_etag and existing_etag_normalized and current_etag == existing_etag_normalized:
                    return True  # Unchanged, skip
            
            # Check Last-Modified
            if 'Last-Modified' in head_response.headers and existing_last_modified:
                try:
                    from email.utils import parsedate_to_datetime
                    last_modified_str = head_response.headers['Last-Modified']
                    server_date = parsedate_to_datetime(last_modified_str)

                    # Parse existing date - handle both ISO8601 and RFC 2822 formats
                    existing_date = None
                    try:
                        # Try ISO8601 format first (new format: 2025-12-01T02:03:17Z)
                        existing_date = datetime.fromisoformat(existing_last_modified.replace('Z', '+00:00'))
                    except ValueError:
                        # Fall back to RFC 2822 format (old format: Mon, 01 Dec 2025 02:03:17 GMT)
                        existing_date = parsedate_to_datetime(existing_last_modified)

                    if existing_date and server_date <= existing_date:
                        return True  # Not modified, skip
                except (ValueError, TypeError):
                    pass  # Date parsing failed, fall back to content check
            
            return None  # Headers unavailable or changed
        except requests.RequestException:
            return None  # HEAD request failed, fall back to content check
    
    def should_skip_url(self, url: str, output_path: Path, use_http_headers: bool = True, 
                        verbose: bool = False) -> bool:
        """
        Check if URL should be skipped (already exists with matching hash and source URL)
        
        Uses multiple strategies in order:
        1. HTTP headers (ETag, Last-Modified) - fastest, no content download
        2. Content hash comparison - accurate, requires fetching content (skipped if trust_existing=True)
        3. Date-based check - fallback if hash unavailable
        
        Args:
            url: URL being scraped
            output_path: Expected output file path
            use_http_headers: If True, check HTTP headers first (faster)
            verbose: If True, log skip decision reasoning
        
        Returns:
            True if should skip, False if should scrape
        """
        if not output_path.exists():
            return False
        
        try:
            content = output_path.read_text(encoding='utf-8')
            if not content.startswith('---'):
                return False  # No frontmatter, re-scrape
            
            # Extract frontmatter
            frontmatter_end = content.find('---', 3)
            if frontmatter_end == -1:
                return False  # Invalid frontmatter, re-scrape
            
            frontmatter_text = content[3:frontmatter_end].strip()
            frontmatter = yaml.safe_load(frontmatter_text)
            
            # Check if source URL matches
            if frontmatter.get('source_url') != url:
                return False  # Different URL, re-scrape
            
            # Strategy 1: HTTP headers (fastest, no content download)
            header_result = None
            if use_http_headers:
                existing_etag = frontmatter.get('etag')
                existing_last_modified = frontmatter.get('last_modified')
                header_result = self.check_http_headers(url, existing_etag, existing_last_modified)
                if header_result is True:
                    if verbose:
                        print(f"  ⏭️  Skipping (HTTP headers unchanged): {url}")
                    self._track_skip('http_headers_unchanged')
                    return True  # Headers indicate unchanged, skip
                elif header_result is False:
                    # Headers indicate content changed, definitely scrape
                    return False
                # If header_result is None, headers unavailable, fall through to next strategy
            
            # Strategy 2: Content hash comparison (most accurate, but requires fetching)
            # Skip this if trust_existing=True when headers unavailable (optimization)
            existing_hash = frontmatter.get('content_hash')
            if existing_hash and (not use_http_headers or header_result is None):
                # If trust_existing is True and headers unavailable, skip hash check
                if self.trust_existing and header_result is None:
                    if verbose:
                        print(f"  ⏭️  Skipping (trust existing, headers unavailable): {url}")
                    self._track_skip('trust_existing_no_headers')
                    return True  # Trust existing file when headers unavailable
                
                # Otherwise, perform hash check
                try:
                    # Try to get markdown directly first (most efficient)
                    markdown_content, _, _ = self.try_fetch_markdown(url)
                    if markdown_content is None:
                        # Fallback: fetch and convert HTML
                        fetched_content, _ = self.fetch_url(url, max_retries=1)  # Single retry for hash check
                        if fetched_content:
                            # We don't have the final URL here easily without refactoring, 
                            # but for hash check it matters less. 
                            # Ideally we should handle it, but this is just a check.
                            markdown_content = self.html_to_markdown(fetched_content, source_url=url)
                        else:
                            markdown_content = None
                    
                    if markdown_content:
                        new_hash = self.calculate_hash(markdown_content)
                        if new_hash == existing_hash:
                            if verbose:
                                print(f"  ⏭️  Skipping (content hash unchanged): {url}")
                            self._track_skip('content_hash_unchanged')
                            return True  # Content unchanged, skip
                        # Hash differs, content changed - scrape
                except Exception:
                    # If hash check fails, fall through to date check
                    pass
            
            # Strategy 3: Date-based check (fallback if hash unavailable)
            last_fetched = frontmatter.get('last_fetched')
            if last_fetched:
                try:
                    fetch_date = datetime.fromisoformat(last_fetched).date()
                    today = datetime.now(timezone.utc).date()
                    days_ago = (today - fetch_date).days

                    # Check if within skip_age_days threshold
                    if days_ago <= self.skip_age_days:
                        # If we have a hash and it matches, or if trust_existing, skip
                        if existing_hash and self.trust_existing:
                            if verbose:
                                print(f"  ⏭️  Skipping (fetched {days_ago} days ago, trust existing): {url}")
                            self._track_skip('fetched_within_age')
                            return True
                        elif days_ago == 0:  # Fetched today
                            if verbose:
                                print(f"  ⏭️  Skipping (fetched today): {url}")
                            self._track_skip('fetched_today')
                            return True  # Fetched today, skip
                except (ValueError, TypeError):
                    pass  # Invalid date, re-scrape
            
            return False
        except Exception as e:
            # On any error, re-scrape to be safe
            if verbose:
                print(f"  ⚠️  Error checking skip status: {e}, will re-scrape")
            return False

    def fetch_http_headers(self, url: str, verbose: bool = False) -> dict[str, str | None]:
        """
        Fetch HTTP headers for change detection
        
        Args:
            url: URL to check
            verbose: If True, log when headers are unavailable
        
        Returns:
            Dict with 'etag' and 'last_modified' (or None if unavailable)
        """
        headers = {'etag': None, 'last_modified': None}
        try:
            self.header_rate_limiter.wait()  # Thread-safe rate limiting
            head_timeout = get_http_timeout()  # Use config default timeout for HEAD requests
            head_response = self.session.head(url, timeout=head_timeout, allow_redirects=True)
            head_response.raise_for_status()
            
            if 'ETag' in head_response.headers:
                # Store normalized ETag (without W/ prefix and quotes) for consistent comparison
                raw_etag = head_response.headers['ETag']
                normalized_etag = self.normalize_etag(raw_etag)
                if normalized_etag:
                    # Store in original format for reference, but comparison will use normalized
                    headers['etag'] = raw_etag
            if 'Last-Modified' in head_response.headers:
                # Convert RFC 2822 format to ISO8601 UTC format
                from email.utils import parsedate_to_datetime
                try:
                    last_modified_dt = parsedate_to_datetime(head_response.headers['Last-Modified'])
                    headers['last_modified'] = last_modified_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                except (ValueError, TypeError):
                    # If parsing fails, store raw value as fallback
                    headers['last_modified'] = head_response.headers['Last-Modified']
            
            # Log if headers are not available (informational, not an error)
            if verbose and not headers['etag'] and not headers['last_modified']:
                # Only log once per run, not for every URL
                pass  # Suppress per-URL logging to avoid spam
        except requests.RequestException:
            # Headers unavailable, continue without them (expected for many servers)
            pass
        
        return headers
    
    def add_frontmatter(self, content: str, url: str, source_type: str,
                        sitemap_url: str | None = None, fetch_method: str | None = None,
                        include_http_headers: bool = True) -> str:
        """
        Add YAML frontmatter to content

        Args:
            content: Markdown content
            url: Source URL
            source_type: Type of source (sitemap, docs-map, manual)
            sitemap_url: URL of sitemap if source_type is sitemap
            fetch_method: Method used to fetch content (markdown or html)
            include_http_headers: If True, fetch and include ETag/Last-Modified headers

        Returns:
            Content with frontmatter
        """
        content_hash = self.calculate_hash(content)

        # Note: last_fetched is stored ONLY in index.yaml, not in frontmatter
        # This prevents git noise from timestamp-only changes
        frontmatter = {
            'source_url': url,
            'source_type': source_type,
            'content_hash': content_hash
        }

        if sitemap_url:
            frontmatter['sitemap_url'] = sitemap_url

        if fetch_method:
            frontmatter['fetch_method'] = fetch_method
        
        # Add HTTP headers for change detection
        if include_http_headers:
            http_headers = self.fetch_http_headers(url)
            if http_headers['etag']:
                frontmatter['etag'] = http_headers['etag']
            if http_headers['last_modified']:
                frontmatter['last_modified'] = http_headers['last_modified']

        # Extract publication date from content (for Anthropic blog posts)
        published_at = extract_publication_date(content)
        if published_at:
            frontmatter['published_at'] = published_at

        yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        return f"---\n{yaml_frontmatter}---\n\n{content}"

    def scrape_url(self, url: str, output_path: Path, source_type: str,
                   sitemap_url: str | None = None, skip_existing: bool = False,
                   max_retries: int | None = None, max_content_age_days: int | None = None) -> bool:
        """
        Scrape single URL and save with frontmatter

        Args:
            url: URL to scrape
            output_path: Path to save markdown file
            source_type: Type of source (sitemap, docs-map, manual)
            sitemap_url: URL of sitemap if applicable
            skip_existing: If True, skip if file exists with matching hash and source URL
            max_retries: Maximum retry attempts for transient failures
            max_content_age_days: If set, skip content older than this many days (based on published_at)

        Returns:
            Metadata dict if successful and scraped, True if skipped, False otherwise
        """
        url_start_time = time.time()

        # Use config default if not provided
        if max_retries is None:
            max_retries = get_http_max_retries()
        
        # Check if should skip
        if skip_existing:
            if self.should_skip_url(url, output_path, use_http_headers=True, verbose=True):
                # Message already printed by should_skip_url if verbose
                return True  # Consider skipped as success
        
        # Try fetching clean markdown first
        markdown, fetch_method, final_url = self.try_fetch_markdown(url)
        
        # If we found a final URL (redirected or not), use it
        if final_url:
            # If redirected, update output path and URL
            if final_url != url:
                # Update URL to final URL
                url = final_url
                
                # Recalculate output path based on new URL
                try:
                    # Auto-detect new output directory
                    new_output_subdir = self.auto_detect_output_dir(url)
                    new_output_dir = self.base_output_dir / new_output_subdir
                    
                    # Get new filename
                    new_relative_path = self.url_to_filename(url, base_pattern=None)
                    output_path = new_output_dir / new_relative_path
                    
                    # Ensure directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    print(f"  🔄 Updated output path due to redirect: {output_path}")
                except Exception as e:
                    print(f"  ⚠️  Warning: Failed to update output path for redirect {url}: {e}")
                    # Fallback to original output path if update fails
        
        # Check if markdown fetch returned 404
        markdown_url = f"{url}.md" if not url.endswith('.md') else url
        if markdown is None and (url in self.url_404s or markdown_url in self.url_404s):
            # Source URL returned 404, mark existing doc as stale
            self.mark_doc_stale_for_404(url, output_path)
            return False
        
        if markdown is None:
            # Fallback: fetch and convert HTML
            # We use the original URL here (or final_url if we found one but markdown fetch failed)
            # fetch_url will follow redirects
            html_content, final_html_url = self.fetch_url(url)
            
            if not html_content:
                print(f"  ❌ Failed to fetch HTML from {url}")
                return False
            
            # Check if HTML fetch resulted in a redirect that we haven't handled yet
            if final_html_url and final_html_url != url:
                # Update URL to final URL
                url = final_html_url
                
                # Recalculate output path based on new URL
                try:
                    # Auto-detect new output directory
                    new_output_subdir = self.auto_detect_output_dir(url)
                    new_output_dir = self.base_output_dir / new_output_subdir
                    
                    # Get new filename
                    new_relative_path = self.url_to_filename(url, base_pattern=None)
                    output_path = new_output_dir / new_relative_path
                    
                    # Ensure directory exists
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    print(f"  🔄 Updated output path due to HTML redirect: {output_path}")
                except Exception as e:
                    print(f"  ⚠️  Warning: Failed to update output path for HTML redirect {url}: {e}")
            
            # Convert to markdown
            markdown = self.html_to_markdown(html_content, url)
            fetch_method = "html"

        # Check content age if max_content_age_days is set
        if max_content_age_days is not None:
            published_at = extract_publication_date(markdown)
            if published_at:
                pub_date = datetime.fromisoformat(published_at).date()
                cutoff_date = (datetime.now() - timedelta(days=max_content_age_days)).date()
                if pub_date < cutoff_date:
                    days_old = (datetime.now().date() - pub_date).days
                    print(f"  ⏭️  Skipping (published {published_at}, {days_old} days old, exceeds max age of {max_content_age_days} days): {url}")
                    return True  # Return True to indicate successful processing (just skipped)

        # Normalize volatile content (e.g., claude.ai redirect GUIDs) before saving
        # This prevents unnecessary file changes when only GUIDs rotate
        markdown = self.normalize_for_hash(markdown)

        # Add frontmatter (include HTTP headers for change detection)
        final_content = self.add_frontmatter(markdown, url, source_type, sitemap_url, fetch_method,
                                            include_http_headers=True)

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Ensure content ends with newline (POSIX convention)
        if not final_content.endswith('\n'):
            final_content += '\n'

        # Write file
        output_path.write_text(final_content, encoding='utf-8')
        safe_print(f"  ✅ Saved: {output_path}")

        # Construct metadata for index
        # Calculate path relative to base_output_dir for the index
        try:
            relative_to_base = output_path.relative_to(self.base_output_dir)
            path_normalized = str(relative_to_base).replace('\\', '/')
        except ValueError:
            # Fallback if output_path is not relative to base_output_dir
            path_normalized = str(output_path).replace('\\', '/')

        metadata = {
            'path': path_normalized,
            'url': url,
            'hash': self.calculate_hash(final_content),
            'last_fetched': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            'source_type': source_type,
            'sitemap_url': sitemap_url
        }

        # Add extracted metadata if extractor available
        if MetadataExtractor:
            try:
                extractor = MetadataExtractor(output_path, url)
                extracted = extractor.extract_all()
                metadata.update(extracted)
            except Exception:
                pass

        url_duration_ms = (time.time() - url_start_time) * 1000
        logger.debug(f"URL scraped in {url_duration_ms:.0f}ms: {url}")
        return metadata

    def normalize_domain(self, url: str) -> str:
        """
        Extract and normalize domain name for use as folder name

        Args:
            url: URL to extract domain from

        Returns:
            Normalized domain (dots replaced with hyphens)

        Examples:
            "https://docs.claude.com/en/docs/intro" → "docs-claude-com"
            "https://code.claude.com/docs/en/overview" → "code-claude-com"
        """
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
        # Replace dots with hyphens
        return domain.replace('.', '-')

    def auto_detect_output_dir(self, url: str, url_filter: str | None = None) -> str:
        """
        Auto-detect output directory based on URL domain and path

        Args:
            url: URL being scraped (can be sitemap URL or actual doc URL)
            url_filter: Optional URL filter pattern (e.g., "/en/docs/")

        Returns:
            Output subdirectory name (e.g., "docs-claude-com")

        Examples:
            sitemap: "https://docs.claude.com/sitemap.xml", filter: "/en/docs/"
            → "docs-claude-com"

            docs_map: "https://code.claude.com/docs/en/claude_code_docs_map.md"
            → "code-claude-com"
        """
        from urllib.parse import urlparse
        from utils.config_helpers import get_output_dir_mapping

        # Extract domain from URL
        parsed = urlparse(url)
        domain = parsed.netloc

        # Get mapping (always returns a value via smart fallback)
        return get_output_dir_mapping(domain)

    def url_to_filename(self, url: str, base_pattern: str = None) -> str:
        """
        Convert URL to relative filepath preserving directory structure
        Automatically strips language codes (e.g., /en/, /fr/, /ja/)

        Args:
            url: URL to convert
            base_pattern: Base URL pattern to remove (e.g., "/en/docs/", "/en/api/")

        Returns:
            Relative filepath (with .md extension)

        Examples:
            url="https://docs.claude.com/en/docs/about-claude/models/overview"
            base_pattern="/en/docs/"
            returns="docs/about-claude/models/overview.md"

            url="https://code.claude.com/docs/en/overview"
            base_pattern=None
            returns="docs/en/overview.md"
        """
        # Extract path from URL
        parsed = urlparse(url)
        path = parsed.path.strip('/')

        # Remove base pattern if provided (e.g., "en/docs", "en/api")
        if base_pattern:
            base_pattern = base_pattern.strip('/')
            if path.startswith(base_pattern):
                path = path[len(base_pattern):].strip('/')

        # Strip language code from beginning if present
        # Matches: en/, fr/, de/, es/, ja/, ko/, zh-CN/, zh-TW/, etc.
        path = re.sub(r'^[a-z]{2}(-[A-Z]{2})?/', '', path)

        # Ensure .md extension
        if not path.endswith('.md'):
            path += '.md'

        return path

    def mark_doc_stale_for_404(self, url: str, output_path: Path) -> None:
        """
        Mark existing document as stale when source URL returns 404
        
        Args:
            url: Source URL that returned 404
            output_path: Path to the document file
        """
        if not self.index_manager:
            return  # Can't update index without index manager
        
        # Find doc_id by URL in index
        try:
            index = self.index_manager.load_all()
            doc_id = None
            for candidate_id, entry in index.items():
                if entry.get('url') == url:
                    doc_id = candidate_id
                    break
            
            if doc_id:
                # Update entry to mark as stale
                entry = self.index_manager.get_entry(doc_id)
                if entry:
                    entry['stale'] = True
                    entry['stale_reason'] = 'source_url_404'
                    entry['stale_detected'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    self.index_manager.update_entry(doc_id, entry)
                    safe_print(f"  ⚠️  Marked doc as stale (404): {doc_id}")
        except Exception as e:
            # Don't fail scraping if marking stale fails
            safe_print(f"  ⚠️  Warning: Failed to mark doc as stale for 404: {e}")

    def update_index(self, doc_id: str, metadata: dict) -> None:
        """
        Update index.yaml with document metadata (parallel-safe with file locking)

        Args:
            doc_id: Document identifier (kebab-case)
            metadata: Metadata dict to add
        """
        # Use index_manager if available (handles large files and locking)
        if self.index_manager:
            if not self.index_manager.update_entry(doc_id, metadata):
                print(f"  ⚠️  Warning: Failed to update index entry: {doc_id}")
        else:
            # Fallback to original implementation for backward compatibility
            lock_file = self.index_path.parent / '.index.lock'
            start_time = time.time()
            timeout = get_scraping_index_lock_timeout()
            
            # Acquire lock
            while time.time() - start_time < timeout:
                try:
                    fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                    os.close(fd)
                    break
                except OSError:
                    time.sleep(LOCK_RETRY_DELAY)
                    continue
            else:
                print(f"  ⚠️  Warning: Could not acquire index lock, retrying update...")
                time.sleep(LOCK_RETRY_BACKOFF)
                start_time = time.time()
                while time.time() - start_time < timeout:
                    try:
                        fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                        os.close(fd)
                        break
                    except OSError:
                        time.sleep(LOCK_RETRY_DELAY)
                        continue
                else:
                    print(f"  ❌ Error: Failed to acquire index lock after retry")
                    return
            
            try:
                # Load existing index
                if self.index_path.exists():
                    with open(self.index_path, 'r', encoding='utf-8') as f:
                        index = yaml.safe_load(f) or {}
                else:
                    index = {}

                # Update entry
                index[doc_id] = metadata

                # Write back
                with open(self.index_path, 'w', encoding='utf-8') as f:
                    yaml.dump(index, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            finally:
                # Release lock
                try:
                    if lock_file.exists():
                        lock_file.unlink()
                except Exception:
                    pass

    def scrape_from_sitemap(self, sitemap_url: str, output_subdir: str | None = None,
                            url_filter: str | None = None, limit: int | None = None,
                            max_age_days: int | None = None, skip_existing: bool = False,
                            max_retries: int | None = None, auto_validate: bool = False,
                            expected_count: int | None = None, resume: bool = False) -> int:
        """
        Scrape multiple URLs from sitemap

        Args:
            sitemap_url: URL to sitemap.xml
            output_subdir: Subdirectory within base_output_dir (auto-detected if not provided)
            url_filter: Optional regex pattern to filter URLs
            limit: Optional limit on number of URLs to scrape (for testing)
            max_age_days: Optional maximum age in days (filter by lastmod date)
            skip_existing: If True, skip URLs that already exist with matching hash
            max_retries: Maximum retry attempts for transient failures
            auto_validate: If True, automatically validate after scraping completes
            expected_count: Expected file count for validation
            resume: If True, resume from last successful URL (skip already-scraped URLs)

        Returns:
            Number of documents successfully scraped
        """
        # Use config default if not provided
        if max_retries is None:
            max_retries = get_http_max_retries()
        
        urls = self.parse_sitemap(sitemap_url, url_filter, max_age_days)
        
        # Load progress if resuming
        if resume:
            progress = self.load_progress()
            urls_to_scrape = [u for u in urls if u not in progress]
            skipped_count = len(urls) - len(urls_to_scrape)
            if skipped_count > 0:
                print(f"  ⏭️  Resuming: {skipped_count} URLs already scraped, {len(urls_to_scrape)} remaining")
                # Track resume skips for observability
                for _ in range(skipped_count):
                    self._track_skip('resume_already_scraped')
            urls = urls_to_scrape
        else:
            # Clear progress if not resuming
            self.clear_progress()

        if limit:
            urls = urls[:limit]
            print(f"  Limiting to first {limit} URLs")

        # Auto-detect output directory from first URL if not provided
        if not output_subdir:
            if urls:
                output_subdir = self.auto_detect_output_dir(urls[0], url_filter)
                print(f"  Auto-detected output directory: {output_subdir}")
            else:
                print("  ❌ No URLs found in sitemap, cannot auto-detect output directory")
                return 0

        output_dir = self.base_output_dir / output_subdir
        
        # Prepare URLs for processing
        url_tasks = []
        for url in urls:
            relative_path = self.url_to_filename(url, base_pattern=None)
            output_path = output_dir / relative_path
            url_tasks.append({
                'url': url,
                'relative_path': relative_path,
                'output_path': output_path
            })
        
        # Process URLs in parallel
        success_count = 0
        skipped_count = 0
        failed_count = 0
        failed_urls = []
        index_updates = []  # Batch index updates
        url_timings: list[float] = []  # Collect per-URL timing for metrics
        scrape_start_time = time.time()  # Track total scrape time
        last_progress_time = time.time()
        progress_interval = get_scraping_progress_interval()  # Report progress every N seconds
        progress_url_interval = get_scraping_progress_url_interval()  # Report progress every N URLs
        
        def process_url(task: dict) -> dict:
            """Process a single URL (for parallel execution)"""
            url = task['url']
            output_path = task['output_path']
            relative_path = task['relative_path']
            url_start = time.time()

            result = {
                'url': url,
                'success': False,
                'skipped': False,
                'failed': False,
                'relative_path': relative_path,
                'duration_ms': 0
            }

            # Check if should skip before scraping
            if skip_existing and self.should_skip_url(url, output_path, use_http_headers=True, verbose=False):
                result['skipped'] = True
                result['duration_ms'] = (time.time() - url_start) * 1000
                return result
            
            scrape_result = self.scrape_url(url, output_path, source_type='sitemap', sitemap_url=sitemap_url,
                             skip_existing=skip_existing, max_retries=max_retries,
                             max_content_age_days=max_age_days)
            
            if scrape_result:
                result['success'] = True
                if resume:
                    self.save_progress(url)
            else:
                result['failed'] = True
            
            # Prepare index update if file was scraped
            if result['success']:
                # Use the metadata returned by scrape_url if available
                # This ensures we use the updated URL and path if redirects occurred
                if scrape_result and isinstance(scrape_result, dict):
                    metadata = scrape_result
                    
                    # Re-calculate doc_id based on the actual output path used
                    # scrape_result['path'] should be the relative path from base_dir
                    # We need to extract the subdir and relative path from it
                    
                    # But scrape_result['path'] is "subdir/file.md"
                    # So we can just use it to generate doc_id
                    path_str = metadata['path']
                    # doc_id convention: subdir-filename_without_ext
                    # e.g. platform-claude-com/docs/en/overview.md -> platform-claude-com-docs-en-overview
                    
                    doc_id_suffix = path_str.replace('.md', '').replace('/', '-')
                    doc_id = doc_id_suffix
                    
                    result['index_update'] = {'doc_id': doc_id, 'metadata': metadata}
                elif output_path.exists():
                    # Fallback to original logic if scrape_result is not a dict (shouldn't happen with updated scrape_url)
                    doc_id_suffix = relative_path.replace('.md', '').replace('/', '-')
                    doc_id = f"{output_subdir.replace('/', '-')}-{doc_id_suffix}"
                    path_normalized = f"{output_subdir}/{relative_path}".replace('\\', '/')
                    
                    metadata = {
                        'path': path_normalized,
                        'url': url,
                        'hash': self.calculate_hash(output_path.read_text(encoding='utf-8')),
                        'last_fetched': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                        'source_type': 'sitemap',
                        'sitemap_url': sitemap_url
                    }
                    
                    # Add extracted metadata if extractor available
                    if MetadataExtractor:
                        try:
                            extractor = MetadataExtractor(output_path, url)
                            extracted = extractor.extract_all()
                            metadata.update(extracted)
                        except Exception:
                            pass  # Don't fail on metadata extraction errors
                    
                    result['index_update'] = {'doc_id': doc_id, 'metadata': metadata}

            result['duration_ms'] = (time.time() - url_start) * 1000
            return result
        
        # Use parallel processing if multiple URLs and max_workers > 1
        use_parallel = len(url_tasks) > 1 and self.max_workers > 1
        
        if use_parallel:
            safe_print(f"  🚀 Processing {len(url_tasks)} URLs in parallel (max {self.max_workers} workers)")
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                futures = {executor.submit(process_url, task): i for i, task in enumerate(url_tasks, 1)}
                
                for future in as_completed(futures):
                    i = futures[future]
                    try:
                        result = future.result()
                        
                        # Print progress (thread-safe, flushed immediately)
                        if i % progress_url_interval == 0 or (time.time() - last_progress_time) >= progress_interval:
                            safe_print(f"\n[{i}/{len(url_tasks)}] Processing: {result['url']}")
                            last_progress_time = time.time()
                        
                        # Collect timing data
                        if 'duration_ms' in result:
                            url_timings.append(result['duration_ms'])

                        if result['skipped']:
                            skipped_count += 1
                            safe_print(f"  ⏭️  Skipping (content hash unchanged): {result['url']}")
                        elif result['success']:
                            success_count += 1
                            if 'index_update' in result:
                                index_updates.append(result['index_update'])
                        elif result['failed']:
                            failed_count += 1
                            failed_urls.append(result['url'])
                            safe_print(f"  ❌ Failed: {result['url']}")
                    except Exception as e:
                        failed_count += 1
                        failed_urls.append(url_tasks[i-1]['url'])
                        safe_print(f"  ❌ Error processing {url_tasks[i-1]['url']}: {e}")
        else:
            # Sequential processing (for small batches or single-threaded mode)
            for i, task in enumerate(url_tasks, 1):
                safe_print(f"\n[{i}/{len(url_tasks)}] Processing: {task['url']}")
                result = process_url(task)
                
                # Collect timing data
                if 'duration_ms' in result:
                    url_timings.append(result['duration_ms'])

                if result['skipped']:
                    skipped_count += 1
                elif result['success']:
                    success_count += 1
                    if 'index_update' in result:
                        index_updates.append(result['index_update'])
                elif result['failed']:
                    failed_count += 1
                    failed_urls.append(task['url'])

                # Periodic progress reporting (flushed immediately)
                current_time = time.time()
                should_report = (
                    i % progress_url_interval == 0 or
                    (current_time - last_progress_time) >= progress_interval
                )
                if should_report:
                    new_count = success_count
                    safe_print(f"  📊 Progress: [{i}/{len(url_tasks)}] processed, {skipped_count} skipped, {new_count} new/updated")
                    last_progress_time = current_time
        
        # Batch update index (single operation - much faster than individual updates)
        if index_updates and self.index_manager:
            batch_dict = {update['doc_id']: update['metadata'] for update in index_updates}
            if not self.index_manager.batch_update_entries(batch_dict):
                print(f"  ⚠️  Warning: Batch index update failed for {len(index_updates)} entries")
        elif index_updates:
            # Fallback to individual updates if index_manager not available
            for update in index_updates:
                self.update_index(update['doc_id'], update['metadata'])

        # Calculate performance metrics
        total_scrape_time = time.time() - scrape_start_time
        avg_time_ms = sum(url_timings) / len(url_timings) if url_timings else 0
        max_time_ms = max(url_timings) if url_timings else 0
        min_time_ms = min(url_timings) if url_timings else 0
        throughput = len(urls) / total_scrape_time if total_scrape_time > 0 else 0

        # Print detailed summary
        print(f"\n{'='*60}")
        print(f"Scraping Summary for {len(urls)} URLs:")
        print(f"{'='*60}")
        new_updated = max(0, success_count - skipped_count)
        print(f"  ✅ New/Updated:      {new_updated}")
        print(f"  ⏭️  Skipped (hash):   {skipped_count}")
        if failed_count > 0:
            print(f"  ❌ Failed:           {failed_count}")
        print(f"  📊 Total processed:  {len(urls)}")
        # Log skip reason breakdown for observability
        skip_summary = self.get_skip_summary()
        if skip_summary != "No skips":
            logger.info(skip_summary)
        print(f"{'='*60}")
        # Performance metrics
        print(f"  ⏱️  Total time:       {total_scrape_time:.1f}s")
        print(f"  📈 Throughput:       {throughput:.2f} URLs/sec")
        print(f"  ⏳ Avg per URL:      {avg_time_ms:.0f}ms")
        if len(url_timings) > 1:
            print(f"  🐢 Slowest URL:      {max_time_ms:.0f}ms")
            print(f"  🚀 Fastest URL:      {min_time_ms:.0f}ms")
        print(f"{'='*60}")

        # List failed URLs if any
        if failed_urls:
            print(f"\n⚠️  Failed URLs ({len(failed_urls)}):")
            for failed_url in failed_urls:
                print(f"  - {failed_url}")

        # Auto-validate if requested
        if auto_validate:
            if not self.auto_validate(output_subdir, expected_count):
                print(f"\n❌ Auto-validation failed for {output_subdir}")
                return success_count  # Still return success count, but validation failed
        
        return success_count
    
    def auto_validate(self, output_subdir: str, expected_count: int | None = None) -> bool:
        """
        Automatically validate scraped source using quick_validate.py
        
        Args:
            output_subdir: Output subdirectory to validate
            expected_count: Expected file count for validation
        
        Returns:
            True if validation passes, False otherwise
        """
        # Find quick_validate.py script (should be in same directory as this script)
        script_dir = Path(__file__).parent
        validate_script = script_dir / "quick_validate.py"
        
        if not validate_script.exists():
            print(f"  ⚠️  quick_validate.py not found at {validate_script}, skipping auto-validation")
            return True  # Don't fail if validation script missing
        
        print(f"\n🔍 Auto-validating scraped source...")
        
        cmd = [
            sys.executable,
            str(validate_script),
            '--output', output_subdir,
            '--base-dir', str(self.base_output_dir)
        ]
        
        if expected_count:
            cmd.extend(['--expected', str(expected_count)])
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',  # Force UTF-8 encoding for Windows compatibility
                timeout=get_validation_timeout()
            )
            
            # Print validation output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr, file=sys.stderr)
            
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            print(f"  ⚠️  Validation timed out")
            return False
        except Exception as e:
            print(f"  ⚠️  Error running validation: {e}")
            return False
    
    def scrape_from_docs_map(self, docs_map_url: str, output_subdir: str | None = None,
                             limit: int | None = None, max_age_days: int | None = None,
                             skip_existing: bool = False, max_retries: int | None = None,
                             auto_validate: bool = False, expected_count: int | None = None,
                             resume: bool = False, skip_urls: list[str] | None = None) -> int:
        """
        Scrape multiple URLs from docs map

        Args:
            docs_map_url: URL to docs map markdown file
            output_subdir: Subdirectory within base_output_dir (auto-detected if not provided)
            limit: Optional limit on number of URLs to scrape (for testing)
            skip_existing: If True, skip URLs that already exist with matching hash
            max_retries: Maximum retry attempts for transient failures
            auto_validate: If True, automatically validate after scraping completes
            expected_count: Expected file count for validation
            resume: If True, resume from last successful URL (skip already-scraped URLs)

        Returns:
            Number of documents successfully scraped
        """
        # Use config default if not provided
        if max_retries is None:
            max_retries = get_http_max_retries()
        
        urls = self.parse_docs_map(docs_map_url)

        # Filter out known-bad URLs (e.g., expected 404s from sources.json)
        if skip_urls:
            original_count = len(urls)
            skip_urls_set = set(skip_urls)  # O(1) lookup
            original_urls_set = set(urls)  # For checking which skips actually matched
            urls = [u for u in urls if u not in skip_urls_set]
            skipped_known_bad = original_count - len(urls)
            if skipped_known_bad > 0:
                logger.info(f"Skipped {skipped_known_bad} known-bad URL(s) from expected_errors config")
                for skipped_url in skip_urls_set:
                    if skipped_url in original_urls_set:
                        logger.debug(f"  Skipped known-bad URL: {skipped_url}")
                        self._track_skip('expected_error_404')

        # Load progress if resuming
        if resume:
            progress = self.load_progress()
            urls_to_scrape = [u for u in urls if u not in progress]
            skipped_count = len(urls) - len(urls_to_scrape)
            if skipped_count > 0:
                print(f"  ⏭️  Resuming: {skipped_count} URLs already scraped, {len(urls_to_scrape)} remaining")
                # Track resume skips for observability
                for _ in range(skipped_count):
                    self._track_skip('resume_already_scraped')
            urls = urls_to_scrape
        else:
            # Clear progress if not resuming
            self.clear_progress()

        if limit:
            urls = urls[:limit]
            print(f"  Limiting to first {limit} URLs")

        # Auto-detect output directory from docs map URL if not provided
        if not output_subdir:
            output_subdir = self.auto_detect_output_dir(docs_map_url)
            print(f"  Auto-detected output directory: {output_subdir}")

        output_dir = self.base_output_dir / output_subdir
        success_count = 0
        skipped_count = 0
        failed_count = 0
        failed_urls = []  # Track URLs that failed
        url_timings: list[float] = []  # Collect per-URL timing for metrics
        scrape_start_time = time.time()  # Track total scrape time
        last_progress_time = time.time()
        progress_interval = get_scraping_progress_interval()  # Report progress every N seconds
        progress_url_interval = get_scraping_progress_url_interval()  # Report progress every N URLs

        for i, url in enumerate(urls, 1):
            url_start = time.time()
            print(f"\n[{i}/{len(urls)}] Processing: {url}")

            # Get relative filepath preserving directory structure
            # url_to_filename already strips language codes, so no base_pattern needed
            relative_path = self.url_to_filename(url, base_pattern=None)
            output_path = output_dir / relative_path

            # Check if should skip before scraping
            was_skipped = False
            if skip_existing and self.should_skip_url(url, output_path):
                was_skipped = True
                skipped_count += 1

            scrape_result = self.scrape_url(url, output_path, source_type='docs-map', sitemap_url=docs_map_url,
                             skip_existing=skip_existing, max_retries=max_retries,
                             max_content_age_days=max_age_days)
            if scrape_result:
                success_count += 1
                
                # Save progress if resuming
                if resume:
                    self.save_progress(url)
                
                # Only update index if file was actually scraped (not skipped)
                # Check if file exists to handle all skip scenarios (including age-based skips inside scrape_url)
                if not was_skipped and output_path.exists():
                    
                    # Use metadata from scrape_url if available
                    if isinstance(scrape_result, dict):
                        metadata = scrape_result
                        path_str = metadata['path']
                        doc_id_suffix = path_str.replace('.md', '').replace('/', '-')
                        doc_id = doc_id_suffix
                        self.update_index(doc_id, metadata)
                    else:
                        # Fallback logic
                        # Update index with full path-based doc_id
                        doc_id_suffix = relative_path.replace('.md', '').replace('/', '-')
                        doc_id = f"{output_subdir.replace('/', '-')}-{doc_id_suffix}"

                        # Extract metadata from scraped file
                        # Normalize path to use forward slashes for cross-platform compatibility
                        path_normalized = f"{output_subdir}/{relative_path}".replace('\\', '/')
                        metadata = {
                            'path': path_normalized,
                            'url': url,
                            'hash': self.calculate_hash(output_path.read_text(encoding='utf-8')),
                            'last_fetched': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                            'source_type': 'docs-map',
                            'sitemap_url': docs_map_url
                        }
                        
                        # Add extracted metadata if extractor available
                        if MetadataExtractor and output_path.exists():
                            try:
                                extractor = MetadataExtractor(output_path, url)
                                extracted = extractor.extract_all()
                                metadata.update(extracted)
                            except Exception:
                                # Don't fail scraping if metadata extraction fails
                                pass
                        
                        self.update_index(doc_id, metadata)

            # Record URL timing
            url_timings.append((time.time() - url_start) * 1000)

            # Periodic progress reporting
            current_time = time.time()
            should_report = (
                i % progress_url_interval == 0 or  # Every N URLs
                (current_time - last_progress_time) >= progress_interval  # Every N seconds
            )
            if should_report:
                new_count = success_count - skipped_count
                print(f"  📊 Progress: [{i}/{len(urls)}] processed, {skipped_count} skipped, {new_count} new/updated")
                last_progress_time = current_time

        # Calculate performance metrics
        total_scrape_time = time.time() - scrape_start_time
        avg_time_ms = sum(url_timings) / len(url_timings) if url_timings else 0
        max_time_ms = max(url_timings) if url_timings else 0
        min_time_ms = min(url_timings) if url_timings else 0
        throughput = len(urls) / total_scrape_time if total_scrape_time > 0 else 0

        # Print detailed summary
        print(f"\n{'='*60}")
        print(f"Scraping Summary for {len(urls)} URLs:")
        print(f"{'='*60}")
        new_updated = max(0, success_count - skipped_count)
        print(f"  ✅ New/Updated:      {new_updated}")
        print(f"  ⏭️  Skipped (hash):   {skipped_count}")
        if failed_count > 0:
            print(f"  ❌ Failed:           {failed_count}")
        print(f"  📊 Total processed:  {len(urls)}")
        # Log skip reason breakdown for observability
        skip_summary = self.get_skip_summary()
        if skip_summary != "No skips":
            logger.info(skip_summary)
        print(f"{'='*60}")
        # Performance metrics
        print(f"  ⏱️  Total time:       {total_scrape_time:.1f}s")
        print(f"  📈 Throughput:       {throughput:.2f} URLs/sec")
        print(f"  ⏳ Avg per URL:      {avg_time_ms:.0f}ms")
        if len(url_timings) > 1:
            print(f"  🐢 Slowest URL:      {max_time_ms:.0f}ms")
            print(f"  🚀 Fastest URL:      {min_time_ms:.0f}ms")
        print(f"{'='*60}")

        # List failed URLs if any
        if failed_urls:
            print(f"\n⚠️  Failed URLs ({len(failed_urls)}):")
            for failed_url in failed_urls:
                print(f"  - {failed_url}")

        # Auto-validate if requested
        if auto_validate:
            if not self.auto_validate(output_subdir, expected_count):
                print(f"\n❌ Auto-validation failed for {output_subdir}")
                return success_count  # Still return success count, but validation failed

        return success_count

    def scrape_from_llms_txt(self, llms_txt_url: str, output_subdir: str | None = None,
                             limit: int | None = None, max_age_days: int | None = None,
                             skip_existing: bool = False, max_retries: int | None = None,
                             auto_validate: bool = False, expected_count: int | None = None,
                             resume: bool = False, skip_urls: list[str] | None = None) -> int:
        """
        Scrape multiple URLs from llms.txt index

        Args:
            llms_txt_url: URL to llms.txt file
            output_subdir: Subdirectory within base_output_dir (auto-detected if not provided)
            limit: Optional limit on number of URLs to scrape (for testing)
            skip_existing: If True, skip URLs that already exist with matching hash
            max_retries: Maximum retry attempts for transient failures
            auto_validate: If True, automatically validate after scraping completes
            expected_count: Expected file count for validation
            resume: If True, resume from last successful URL (skip already-scraped URLs)
            skip_urls: URLs to skip (e.g., known 404s)

        Returns:
            Number of documents successfully scraped
        """
        # Use config default if not provided
        if max_retries is None:
            max_retries = get_http_max_retries()

        urls = self.parse_llms_txt(llms_txt_url)

        # Filter out known-bad URLs (e.g., expected 404s from sources.json)
        if skip_urls:
            original_count = len(urls)
            skip_urls_set = set(skip_urls)
            original_urls_set = set(urls)
            urls = [u for u in urls if u not in skip_urls_set]
            skipped_known_bad = original_count - len(urls)
            if skipped_known_bad > 0:
                logger.info(f"Skipped {skipped_known_bad} known-bad URL(s) from expected_errors config")
                for skipped_url in skip_urls_set:
                    if skipped_url in original_urls_set:
                        logger.debug(f"  Skipped known-bad URL: {skipped_url}")
                        self._track_skip('expected_error_404')

        # Load progress if resuming
        if resume:
            progress = self.load_progress()
            urls_to_scrape = [u for u in urls if u not in progress]
            skipped_count = len(urls) - len(urls_to_scrape)
            if skipped_count > 0:
                print(f"  ⏭️  Resuming: {skipped_count} URLs already scraped, {len(urls_to_scrape)} remaining")
                for _ in range(skipped_count):
                    self._track_skip('resume_already_scraped')
            urls = urls_to_scrape
        else:
            self.clear_progress()

        if limit:
            urls = urls[:limit]
            print(f"  Limiting to first {limit} URLs")

        # Auto-detect output directory from llms.txt URL if not provided
        if not output_subdir:
            output_subdir = self.auto_detect_output_dir(llms_txt_url)
            print(f"  Auto-detected output directory: {output_subdir}")

        output_dir = self.base_output_dir / output_subdir
        success_count = 0
        skipped_count = 0
        failed_count = 0
        failed_urls = []
        url_timings: list[float] = []
        scrape_start_time = time.time()
        last_progress_time = time.time()
        progress_interval = get_scraping_progress_interval()
        progress_url_interval = get_scraping_progress_url_interval()

        for i, url in enumerate(urls, 1):
            url_start = time.time()
            print(f"\n[{i}/{len(urls)}] Processing: {url}")

            # Get relative filepath preserving directory structure
            relative_path = self.url_to_filename(url, base_pattern=None)
            output_path = output_dir / relative_path

            # Check if should skip before scraping
            was_skipped = False
            if skip_existing and self.should_skip_url(url, output_path):
                was_skipped = True
                skipped_count += 1

            scrape_result = self.scrape_url(url, output_path, source_type='llms-txt', sitemap_url=llms_txt_url,
                             skip_existing=skip_existing, max_retries=max_retries,
                             max_content_age_days=max_age_days)
            if scrape_result:
                success_count += 1

                if resume:
                    self.save_progress(url)

                # Only update index if file was actually scraped (not skipped)
                if not was_skipped and output_path.exists():
                    if isinstance(scrape_result, dict):
                        metadata = scrape_result
                        path_str = metadata['path']
                        doc_id_suffix = path_str.replace('.md', '').replace('/', '-')
                        doc_id = doc_id_suffix
                        self.update_index(doc_id, metadata)
                    else:
                        doc_id_suffix = relative_path.replace('.md', '').replace('/', '-')
                        doc_id = f"{output_subdir.replace('/', '-')}-{doc_id_suffix}"
                        try:
                            content = output_path.read_text(encoding='utf-8')
                            frontmatter = {}
                            if content.startswith('---'):
                                end = content.find('---', 3)
                                if end > 0:
                                    frontmatter = yaml.safe_load(content[3:end])
                            path_str = str(output_path.relative_to(self.base_output_dir))
                            metadata = {
                                'source_url': url,
                                'content_hash': frontmatter.get('content_hash', ''),
                                'last_fetched': frontmatter.get('last_fetched', ''),
                                'path': path_str,
                                'doc_id': doc_id
                            }
                            self.update_index(doc_id, metadata)
                        except Exception as e:
                            logger.warning(f"Could not extract metadata for index: {e}")
            else:
                failed_count += 1
                failed_urls.append(url)

            url_time = time.time() - url_start
            url_timings.append(url_time)

            # Periodic progress report
            current_time = time.time()
            if current_time - last_progress_time >= progress_interval or i % progress_url_interval == 0:
                elapsed = current_time - scrape_start_time
                rate = i / elapsed if elapsed > 0 else 0
                remaining = len(urls) - i
                eta = remaining / rate if rate > 0 else 0
                print(f"  📊 Progress: {i}/{len(urls)} ({i/len(urls)*100:.1f}%) | "
                      f"Rate: {rate:.1f} URL/s | ETA: {format_duration(eta)}")
                last_progress_time = current_time

        # Print summary
        total_scrape_time = time.time() - scrape_start_time
        throughput = len(urls) / total_scrape_time if total_scrape_time > 0 else 0
        avg_time_ms = (sum(url_timings) / len(url_timings) * 1000) if url_timings else 0
        max_time_ms = max(url_timings) * 1000 if url_timings else 0
        min_time_ms = min(url_timings) * 1000 if url_timings else 0

        print(f"\n{'='*60}")
        print(f"Scraping Summary for {len(urls)} URLs:")
        print(f"{'='*60}")
        new_updated = max(0, success_count - skipped_count)
        print(f"  ✅ New/Updated:      {new_updated}")
        print(f"  ⏭️  Skipped (hash):   {skipped_count}")
        if failed_count > 0:
            print(f"  ❌ Failed:           {failed_count}")
        print(f"  📊 Total processed:  {len(urls)}")
        skip_summary = self.get_skip_summary()
        if skip_summary != "No skips":
            logger.info(skip_summary)
        print(f"{'='*60}")
        print(f"  ⏱️  Total time:       {total_scrape_time:.1f}s")
        print(f"  📈 Throughput:       {throughput:.2f} URLs/sec")
        print(f"  ⏳ Avg per URL:      {avg_time_ms:.0f}ms")
        if len(url_timings) > 1:
            print(f"  🐢 Slowest URL:      {max_time_ms:.0f}ms")
            print(f"  🚀 Fastest URL:      {min_time_ms:.0f}ms")
        print(f"{'='*60}")

        if failed_urls:
            print(f"\n⚠️  Failed URLs ({len(failed_urls)}):")
            for failed_url in failed_urls:
                print(f"  - {failed_url}")

        if auto_validate:
            if not self.auto_validate(output_subdir, expected_count):
                print(f"\n❌ Auto-validation failed for {output_subdir}")
                return success_count

        return success_count

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape documentation from sitemaps and URLs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape from sitemap (auto-detects output directory from domain)
  python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml \\
                        --filter "/en/docs/"
  # Output: docs-claude-com/docs/...

  # Scrape API reference (auto-detects output directory)
  python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml \\
                        --filter "/en/api/"
  # Output: docs-claude-com/api/...

  # Scrape from Claude Code docs map (auto-detects output directory)
  python scrape_docs.py --docs-map https://code.claude.com/docs/en/claude_code_docs_map.md
  # Output: code-claude-com/docs/en/...

  # Override auto-detection with custom output directory
  python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml \\
                        --filter "/en/docs/" \\
                        --output custom-folder

  # Scrape single URL
  python scrape_docs.py --url https://docs.claude.com/en/docs/intro \\
                        --output docs-claude-com/docs/intro.md

  # Test with limit
  python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml \\
                        --filter "/en/docs/" \\
                        --limit 5
        """
    )

    # Input source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--sitemap', help='URL to sitemap.xml')
    source_group.add_argument('--docs-map', help='URL to docs map markdown file')
    source_group.add_argument('--llms-txt', help='URL to llms.txt file (markdown link index)')
    source_group.add_argument('--url', help='Single URL to scrape')

    # Output
    parser.add_argument('--output',
                       help='Output path (auto-detected from URL if not provided; required for --url)')

    # Options
    parser.add_argument('--filter', help='Regex pattern to filter sitemap URLs (e.g., "/en/docs/")')
    parser.add_argument('--limit', type=int, help='Limit number of URLs to scrape (for testing)')
    parser.add_argument('--max-age', type=int, dest='max_age_days',
                       help='Maximum age in days for sitemap URLs (filters by <lastmod> date, e.g., 365 for 12 months)')
    # Get defaults from config
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    default_rate_limit = get_scraping_rate_limit()
    default_header_rate_limit = get_scraping_header_rate_limit()
    default_max_workers = get_scraping_max_workers()
    
    add_base_dir_argument(parser)
    parser.add_argument('--rate-limit', type=float, default=default_rate_limit,
                       help=f'Delay between requests in seconds (default: {default_rate_limit}, from config)')
    parser.add_argument('--header-rate-limit', type=float, default=default_header_rate_limit,
                       help=f'Delay between HEAD requests in seconds (default: {default_header_rate_limit}, from config)')
    parser.add_argument('--max-workers', type=int, default=default_max_workers,
                       help=f'Maximum parallel workers for URL processing (default: {default_max_workers}, from config)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip URLs that already exist with matching hash and source URL (idempotent mode)')
    parser.add_argument('--trust-existing', action='store_true',
                       help='Skip hash check when HTTP headers unavailable (faster, but less accurate)')
    parser.add_argument('--no-try-markdown', action='store_true',
                       help='Skip trying .md URLs (go straight to HTML conversion)')
    parser.add_argument('--skip-age-days', type=int, default=0,
                       help='Skip files fetched within this many days if hash matches (default: 0 = today only)')
    default_max_retries = get_http_max_retries()
    parser.add_argument('--max-retries', type=int, default=default_max_retries,
                       help=f'Maximum retry attempts for transient failures (default: {default_max_retries}, from config)')
    parser.add_argument('--auto-validate', action='store_true',
                       help='Automatically validate after scraping completes (uses quick_validate.py)')
    parser.add_argument('--expected-count', type=int,
                       help='Expected file count for validation (used with --auto-validate)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from last successful URL (uses .scrape_progress.json)')
    parser.add_argument('--skip-urls', type=str, nargs='*', default=[],
                       help='URLs to skip (e.g., known 404s from expected_errors in sources.json)')

    args = parser.parse_args()

    # Print dev/prod mode banner for visibility (only if not running as child worker)
    # Child workers (with CLAUDE_DOCS_SOURCE_NAME) don't need banner - parent already printed it
    if not _source_name:
        from utils.dev_mode import print_mode_banner
        from utils.path_config import get_base_dir
        print_mode_banner(logger)
        logger.info(f"Canonical dir: {get_base_dir()}")

    # Log script start (include source_name for parallel worker identification)
    start_context = {
        'source': 'sitemap' if args.sitemap else ('docs_map' if args.docs_map else ('llms_txt' if args.llms_txt else 'url')),
        'base_dir': args.base_dir,
        'limit': args.limit,
        'skip_existing': args.skip_existing
    }
    if _source_name:
        start_context['source_name'] = _source_name
    logger.start(start_context)
    
    exit_code = 0
    try:
        # Validation: --url requires --output
        if args.url and not args.output:
            parser.error("--url requires --output to be specified")

        # Initialize scraper - resolve base directory using cli_utils helper
        base_dir = resolve_base_dir_from_args(args)
        
        # Create directory if needed (idempotent)
        base_dir.mkdir(parents=True, exist_ok=True)

        print(f"📁 Using base directory: {base_dir}")
        print(f"   (Absolute path: {base_dir.absolute()})")

        scraper = DocScraper(
            base_dir,
            rate_limit=args.rate_limit if args.rate_limit != default_rate_limit else None,
            header_rate_limit=args.header_rate_limit if args.header_rate_limit != default_header_rate_limit else None,
            max_workers=args.max_workers if args.max_workers != default_max_workers else None,
            trust_existing=args.trust_existing,
            skip_age_days=args.skip_age_days,
            try_markdown=not args.no_try_markdown
        )

        # Execute scraping
        if args.sitemap:
            success_count = scraper.scrape_from_sitemap(
                args.sitemap,
                args.output,
                url_filter=args.filter,
                limit=args.limit,
                max_age_days=args.max_age_days,
                skip_existing=args.skip_existing,
                max_retries=args.max_retries,
                auto_validate=args.auto_validate,
                expected_count=args.expected_count,
                resume=args.resume
            )
        elif args.docs_map:
            success_count = scraper.scrape_from_docs_map(
                args.docs_map,
                args.output,
                limit=args.limit,
                skip_existing=args.skip_existing,
                max_retries=args.max_retries,
                auto_validate=args.auto_validate,
                expected_count=args.expected_count,
                resume=args.resume,
                skip_urls=args.skip_urls if args.skip_urls else None
            )
        elif args.llms_txt:
            success_count = scraper.scrape_from_llms_txt(
                args.llms_txt,
                args.output,
                limit=args.limit,
                skip_existing=args.skip_existing,
                max_retries=args.max_retries,
                auto_validate=args.auto_validate,
                expected_count=args.expected_count,
                resume=args.resume,
                skip_urls=args.skip_urls if args.skip_urls else None
            )
        elif args.url:
            # Single URL
            output_path = base_dir / args.output
            result = scraper.scrape_url(args.url, output_path, source_type='manual',
                                        skip_existing=args.skip_existing,
                                        max_retries=args.max_retries)

            # Handle different return types (True/False for skipped/failed, dict for success)
            if isinstance(result, dict):
                # Successfully scraped, got metadata
                success = True
                metadata = result
                # Use metadata doc_id calculation (path-based)
                path_str = metadata['path']
                doc_id = path_str.replace('.md', '').replace('/', '-')
                scraper.update_index(doc_id, metadata)
            elif result is True:
                # Skipped (content unchanged or too old)
                success = True
            else:
                # Failed
                success = False

            success_count = 1 if success else 0

        # Print summary
        print(f"\n{'='*60}")
        print(f"Scraping complete: {success_count} document(s) processed")
        
        # Calculate total size if output directory exists
        if args.sitemap or args.docs_map or args.llms_txt:
            output_subdir = args.output or scraper.auto_detect_output_dir(
                args.sitemap or args.docs_map or args.llms_txt, args.filter
            )
            output_dir = base_dir / output_subdir
            if output_dir.exists():
                md_files = list(output_dir.glob("**/*.md"))
                total_size = sum(f.stat().st_size for f in md_files)
                size_mb = total_size / 1024 / 1024
                print(f"Files: {len(md_files)}")
                print(f"Size: {size_mb:.2f} MB")
                logger.track_metric('total_files', len(md_files))
                logger.track_metric('total_size_mb', size_mb)
        
        # Report total duration
        duration_seconds = logger.performance_metrics.get('duration_seconds', 0)
        if duration_seconds > 0:
            print(f"⏱️  Total duration: {format_duration(duration_seconds)}")
        
        logger.track_metric('success_count', success_count)
        
        summary = {
            'success_count': success_count,
            'source': 'sitemap' if args.sitemap else ('docs_map' if args.docs_map else ('llms_txt' if args.llms_txt else 'url'))
        }
        if _source_name:
            summary['source_name'] = _source_name

        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in scrape_docs", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
