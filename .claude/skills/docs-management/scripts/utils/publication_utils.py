#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
publication_utils.py - Publication date extraction and formatting utilities

Provides shared utilities for extracting, parsing, and formatting publication dates
from various sources (HTML meta tags, article content, time elements).

This module consolidates date extraction logic previously duplicated across
scrape_docs.py and extract_publication_dates.py and is tested via
`scripts.utils.publication_utils`.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from .logging_utils import get_or_setup_logger

logger = get_or_setup_logger(__file__, log_category="scrape")


# Publication date extraction patterns (for Anthropic blog posts and articles)
DATE_PATTERNS = [
    # Examples: "Mar 27, 2025●8 min read", "Mar 7, 2024"
    (re.compile(r'\b([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})'), "%b %d, %Y"),
    # Examples: "March 27, 2025"
    (re.compile(r'\b([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})'), "%B %d, %Y"),
    # Examples: "2025-03-27", "2024-01-15"
    (re.compile(r'\b(\d{4})-(\d{2})-(\d{2})\b'), "%Y-%m-%d"),
    # Examples: "27/03/2025", "15/01/2024"
    (re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b'), "%d/%m/%Y"),
    # Examples: "03/27/2025" (US format)
    (re.compile(r'\b(\d{2})/(\d{2})/(\d{4})\b'), "%m/%d/%Y"),
]


def extract_publication_date(soup, url: str | None = None) -> datetime | None:
    """
    Extract publication date from HTML document using various strategies.

    Attempts to extract dates from:
    1. <meta property="article:published_time"> tags
    2. <meta property="article:modified_time"> tags
    3. <meta name="date"> tags
    4. <time> elements with datetime attributes
    5. Common date patterns in article content

    Args:
        soup: BeautifulSoup object of the HTML document
        url: URL of the document (for logging context, optional)

    Returns:
        datetime object (UTC) if date found, otherwise None

    Examples:
        >>> from bs4 import BeautifulSoup
        >>> html = '<meta property="article:published_time" content="2025-03-27T10:00:00Z">'
        >>> soup = BeautifulSoup(html, 'html.parser')
        >>> dt = extract_publication_date(soup, "https://example.com/article")
        >>> print(dt.date())
        2025-03-27
    """
    # Strategy 1: Check meta tags for article:published_time
    meta_published = soup.find('meta', property='article:published_time')
    if meta_published and meta_published.get('content'):
        date_str = meta_published['content']
        dt = parse_date_string(date_str)
        if dt:
            logger.debug(
                f"Found publication date in article:published_time meta tag: {dt.date()} ({url})"
            )
            return dt

    # Strategy 2: Check meta tags for article:modified_time
    meta_modified = soup.find('meta', property='article:modified_time')
    if meta_modified and meta_modified.get('content'):
        date_str = meta_modified['content']
        dt = parse_date_string(date_str)
        if dt:
            logger.debug(
                f"Found publication date in article:modified_time meta tag: {dt.date()} ({url})"
            )
            return dt

    # Strategy 3: Check meta tags for name="date"
    meta_date = soup.find('meta', attrs={'name': 'date'})
    if meta_date and meta_date.get('content'):
        date_str = meta_date['content']
        dt = parse_date_string(date_str)
        if dt:
            logger.debug(f"Found publication date in date meta tag: {dt.date()} ({url})")
            return dt

    # Strategy 4: Check <time> elements with datetime attribute
    time_elem = soup.find('time', datetime=True)
    if time_elem:
        date_str = time_elem['datetime']
        dt = parse_date_string(date_str)
        if dt:
            logger.debug(f"Found publication date in time element: {dt.date()} ({url})")
            return dt

    # Strategy 5: Search article content for common date patterns
    # Look in article, main, or body content
    content_areas = soup.find_all(['article', 'main', 'body'])
    for area in content_areas:
        if not area:
            continue

        # Only inspect first ~40 lines of text content
        text = area.get_text()
        lines = text.splitlines()[:40]

        for line in lines:
            for pattern, fmt in DATE_PATTERNS:
                m = pattern.search(line)
                if not m:
                    continue
                try:
                    date_str = m.group(0)
                    dt = datetime.strptime(date_str, fmt)
                    # Assume UTC if no timezone info
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                    logger.debug(
                        f"Found publication date in content: {dt.date()} ({url})"
                    )
                    return dt
                except Exception as e:
                    logger.debug(
                        f"Failed to parse date '{date_str}' with format '{fmt}': {e}"
                    )
                    continue

    logger.debug(f"No publication date found for {url}")
    return None


def extract_date_from_content(content: str) -> str | None:
    """
    Extract publication date from markdown or text content.

    This is the legacy function compatible with scrape_docs.py and
    extract_publication_dates.py. For new code, prefer extract_publication_date()
    which handles HTML sources.

    Args:
        content: Markdown or plain text content to parse

    Returns:
        ISO date string (YYYY-MM-DD) if found, otherwise None

    Examples:
        >>> content = "Mar 27, 2025●8 min read\\nArticle content..."
        >>> extract_date_from_content(content)
        '2025-03-27'
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


def parse_date_string(date_str: str) -> datetime | None:
    """
    Parse various date format strings into datetime objects.

    Handles:
    - ISO 8601 formats (with/without timezone)
    - RFC 2822 formats (e.g., "Fri, 15 Nov 2025 10:30:00 GMT")
    - Common date formats (Month DD, YYYY)
    - Slash/dot/hyphen-separated dates

    Args:
        date_str: Date string to parse (None/empty returns None)

    Returns:
        datetime object (UTC) if parsed successfully, otherwise None
    """
    if not date_str:
        return None

    # Try ISO 8601 formats first (most common for meta tags)
    iso_formats = [
        "%Y-%m-%dT%H:%M:%SZ",           # 2025-03-27T10:00:00Z
        "%Y-%m-%dT%H:%M:%S%z",          # 2025-03-27T10:00:00+00:00
        "%Y-%m-%dT%H:%M:%S.%fZ",        # 2025-03-27T10:00:00.123Z
        "%Y-%m-%dT%H:%M:%S.%f%z",       # 2025-03-27T10:00:00.123+00:00
        "%Y-%m-%d",                     # 2025-03-27
    ]

    for fmt in iso_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Ensure UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            elif dt.tzinfo != timezone.utc:
                dt = dt.astimezone(timezone.utc)
            return dt
        except ValueError:
            continue

    # RFC 2822 / email-style dates (e.g., "Fri, 15 Nov 2025 10:30:00 GMT")
    try:
        dt = parsedate_to_datetime(date_str)
        if dt is not None:
            # Ensure UTC timezone
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            elif dt.tzinfo != timezone.utc:
                dt = dt.astimezone(timezone.utc)
            return dt
    except Exception:
        pass

    # Try simple separators: YYYY/MM/DD, YYYY.MM.DD
    separator_formats = ["%Y/%m/%d", "%Y.%m.%d"]
    for fmt in separator_formats:
        try:
            dt = datetime.strptime(date_str, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    # Try common text date patterns (using DATE_PATTERNS)
    for pattern, fmt in DATE_PATTERNS:
        try:
            dt = datetime.strptime(date_str, fmt)
            # Assume UTC if no timezone info
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    logger.warning(f"Failed to parse date string: {date_str}")
    return None


def is_recent(dt: datetime | None, days: int = 180) -> bool:
    """
    Check if a date is within the specified number of days from now.

    Args:
        dt: datetime object to check (None returns False)
        days: Number of days to consider "recent" (default: 180)

    Returns:
        True if date is within the last N days, False otherwise

    Examples:
        >>> from datetime import datetime, timezone
        >>> recent_date = datetime.now(timezone.utc)
        >>> is_recent(recent_date, days=30)
        True

        >>> old_date = datetime(2020, 1, 1, tzinfo=timezone.utc)
        >>> is_recent(old_date, days=30)
        False
    """
    if dt is None:
        return False

    # Ensure dt has timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)

    return dt >= cutoff


def format_date_for_index(dt: datetime | None) -> str | None:
    """
    Format datetime object for index.yaml storage (YYYY-MM-DD).

    Args:
        dt: datetime object to format (None returns None)

    Returns:
        ISO date string (YYYY-MM-DD) or None

    Examples:
        >>> from datetime import datetime, timezone
        >>> dt = datetime(2025, 3, 27, 10, 30, tzinfo=timezone.utc)
        >>> format_date_for_index(dt)
        '2025-03-27'
    """
    if dt is None:
        return None

    return dt.date().isoformat()


def get_date_age_days(dt: datetime | None) -> int | None:
    """
    Get the age of a date in days from now.

    Args:
        dt: datetime object to check (None returns None)

    Returns:
        Number of days between dt and now, or None if dt is None

    Examples:
        >>> from datetime import datetime, timezone, timedelta
        >>> yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        >>> get_date_age_days(yesterday)
        1
    """
    if dt is None:
        return None

    # Ensure dt has timezone info
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    now = datetime.now(timezone.utc)
    delta = now - dt

    return delta.days


# Example usage
if __name__ == "__main__":
    # Test date parsing
    test_dates = [
        "2025-03-27T10:00:00Z",
        "Mar 27, 2025",
        "March 5, 2024",
        "2024-01-15",
    ]

    print("Testing date parsing:")
    for date_str in test_dates:
        dt = parse_date_string(date_str)
        if dt:
            print(f"  ✅ '{date_str}' → {format_date_for_index(dt)} (age: {get_date_age_days(dt)} days)")
        else:
            print(f"  ❌ '{date_str}' → failed to parse")

    # Test HTML extraction
    try:
        from bs4 import BeautifulSoup

        print("\nTesting HTML extraction:")
        html_samples = [
            '<meta property="article:published_time" content="2025-03-27T10:00:00Z">',
            '<meta name="date" content="2024-12-15">',
            '<time datetime="2025-01-10T14:30:00Z">January 10, 2025</time>',
        ]

        for html in html_samples:
            soup = BeautifulSoup(html, 'html.parser')
            dt = extract_publication_date(soup, "https://example.com/test")
            if dt:
                print(f"  ✅ {html[:50]}... → {format_date_for_index(dt)}")
            else:
                print(f"  ❌ {html[:50]}... → no date found")
    except ImportError:
        print("\nSkipping HTML extraction tests (BeautifulSoup not available)")

    # Test recency check
    print("\nTesting recency check:")
    now = datetime.now(timezone.utc)
    recent = now - timedelta(days=15)
    old = now - timedelta(days=60)

    print(f"  Recent date (15 days old): is_recent={is_recent(recent, days=30)}")
    print(f"  Old date (60 days old): is_recent={is_recent(old, days=30)}")
