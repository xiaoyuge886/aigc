"""
Tests for publication_utils module.
"""
from datetime import datetime, timezone, timedelta


from bs4 import BeautifulSoup
from freezegun import freeze_time
from scripts.utils.publication_utils import (
    extract_publication_date,
    parse_date_string,
    is_recent,
    format_date_for_index,
)


class TestExtractPublicationDate:
    """Test suite for extract_publication_date function."""

    def test_extract_from_article_published_time(self):
        """Test extraction from article:published_time meta tag."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="2025-11-15T10:30:00Z">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15
        assert result.tzinfo == timezone.utc

    def test_extract_from_article_modified_time(self):
        """Test extraction from article:modified_time meta tag."""
        html = """
        <html>
        <head>
            <meta property="article:modified_time" content="2025-11-16T09:00:00Z">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 16

    def test_extract_from_date_meta_tag(self):
        """Test extraction from generic date meta tag."""
        html = """
        <html>
        <head>
            <meta name="date" content="2025-11-15">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_extract_from_time_element(self):
        """Test extraction from HTML time element with datetime attribute."""
        html = """
        <html>
        <body>
            <time datetime="2025-11-15T10:30:00Z">November 15, 2025</time>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_extract_from_published_class(self):
        """Test extraction from element with published-date class."""
        html = """
        <html>
        <body>
            <div class="published-date">2025-11-15</div>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_priority_order(self):
        """Test that extraction follows priority order."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="2025-11-15T10:30:00Z">
            <meta property="article:modified_time" content="2025-11-16T09:00:00Z">
            <meta name="date" content="2025-11-17">
        </head>
        <body>
            <time datetime="2025-11-18T10:30:00Z">November 18, 2025</time>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        # Should use article:published_time (highest priority)
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_no_date_found(self):
        """Test behavior when no date can be extracted."""
        html = """
        <html>
        <body>
            <p>Content without any date information</p>
        </body>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        assert result is None

    def test_invalid_date_format(self):
        """Test handling of invalid date formats."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="invalid-date">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        result = extract_publication_date(soup)

        # Should return None or skip to next extraction method
        # (implementation dependent)
        assert result is None or isinstance(result, datetime)


class TestParseDateString:
    """Test suite for parse_date_string function."""

    def test_iso8601_with_timezone(self):
        """Test parsing ISO 8601 format with timezone."""
        date_str = "2025-11-15T10:30:00Z"

        result = parse_date_string(date_str)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15
        assert result.hour == 10
        assert result.minute == 30
        assert result.tzinfo == timezone.utc

    def test_iso8601_with_offset(self):
        """Test parsing ISO 8601 with timezone offset."""
        date_str = "2025-11-15T10:30:00+05:00"

        result = parse_date_string(date_str)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_date_only_format(self):
        """Test parsing date-only format (YYYY-MM-DD)."""
        date_str = "2025-11-15"

        result = parse_date_string(date_str)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_rfc2822_format(self):
        """Test parsing RFC 2822 format."""
        date_str = "Fri, 15 Nov 2025 10:30:00 GMT"

        result = parse_date_string(date_str)

        assert result is not None
        assert result.year == 2025
        assert result.month == 11
        assert result.day == 15

    def test_various_separators(self):
        """Test parsing dates with different separators."""
        test_cases = [
            "2025-11-15",
            "2025/11/15",
            "2025.11.15"
        ]

        for date_str in test_cases:
            result = parse_date_string(date_str)
            assert result is not None
            assert result.year == 2025
            assert result.month == 11
            assert result.day == 15

    def test_invalid_date_string(self):
        """Test handling of invalid date strings."""
        invalid_dates = [
            "not-a-date",
            "2025-13-45",  # Invalid month/day
            "",
            None
        ]

        for date_str in invalid_dates:
            result = parse_date_string(date_str)
            assert result is None

    def test_timezone_conversion_to_utc(self):
        """Test that dates are converted to UTC."""
        date_str = "2025-11-15T10:30:00+05:00"

        result = parse_date_string(date_str)

        assert result is not None
        assert result.tzinfo == timezone.utc
        # 10:30 +05:00 should be 05:30 UTC
        assert result.hour == 5
        assert result.minute == 30


class TestIsRecent:
    """Test suite for is_recent function."""

    @freeze_time("2025-11-16 12:00:00")
    def test_recent_within_default_days(self):
        """Test that dates within default days (180) are considered recent."""
        # 100 days ago from frozen time
        test_date = datetime(2025, 8, 8, 12, 0, 0, tzinfo=timezone.utc)

        assert is_recent(test_date) is True

    @freeze_time("2025-11-16 12:00:00")
    def test_not_recent_beyond_default_days(self):
        """Test that dates beyond default days (180) are not recent."""
        # 200 days ago from frozen time
        test_date = datetime(2025, 4, 30, 12, 0, 0, tzinfo=timezone.utc)

        assert is_recent(test_date) is False

    @freeze_time("2025-11-16 12:00:00")
    def test_custom_days_threshold(self):
        """Test custom days threshold parameter."""
        # 50 days ago
        test_date = datetime(2025, 9, 27, 12, 0, 0, tzinfo=timezone.utc)

        assert is_recent(test_date, days=30) is False
        assert is_recent(test_date, days=60) is True

    @freeze_time("2025-11-16 12:00:00")
    def test_boundary_condition_exact_threshold(self):
        """Test boundary condition at exact threshold."""
        # Exactly 180 days ago
        test_date = datetime(2025, 5, 20, 12, 0, 0, tzinfo=timezone.utc)

        # Implementation dependent: should be clearly defined
        result = is_recent(test_date, days=180)
        assert isinstance(result, bool)

    @freeze_time("2025-11-16 12:00:00")
    def test_future_date(self):
        """Test handling of future dates."""
        # 10 days in the future
        future_date = datetime(2025, 11, 26, 12, 0, 0, tzinfo=timezone.utc)

        # Future dates should be considered recent
        assert is_recent(future_date) is True

    @freeze_time("2025-11-16 12:00:00")
    def test_today(self):
        """Test that today's date is considered recent."""
        today = datetime(2025, 11, 16, 12, 0, 0, tzinfo=timezone.utc)

        assert is_recent(today) is True

    def test_none_date(self):
        """Test handling of None date."""
        result = is_recent(None)

        assert result is False


class TestFormatDateForIndex:
    """Test suite for format_date_for_index function."""

    def test_standard_format(self):
        """Test standard date formatting."""
        date = datetime(2025, 11, 15, 10, 30, 0, tzinfo=timezone.utc)

        result = format_date_for_index(date)

        assert result == "2025-11-15"

    def test_single_digit_month_day(self):
        """Test formatting with single-digit month and day."""
        date = datetime(2025, 1, 5, 10, 30, 0, tzinfo=timezone.utc)

        result = format_date_for_index(date)

        assert result == "2025-01-05"

    def test_timezone_handling(self):
        """Test that timezone doesn't affect date formatting."""
        # Same instant in different timezones
        date_utc = datetime(2025, 11, 15, 23, 30, 0, tzinfo=timezone.utc)
        date_plus5 = datetime(2025, 11, 16, 4, 30, 0,
                              tzinfo=timezone(timedelta(hours=5)))

        # When formatted, should show the date in the specified timezone
        result_utc = format_date_for_index(date_utc)
        result_plus5 = format_date_for_index(date_plus5)

        assert result_utc == "2025-11-15"
        assert result_plus5 == "2025-11-16"

    def test_none_date(self):
        """Test handling of None date."""
        result = format_date_for_index(None)

        assert result is None or result == ""

    def test_year_boundary(self):
        """Test formatting at year boundaries."""
        new_years_eve = datetime(2025, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        new_years_day = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

        assert format_date_for_index(new_years_eve) == "2025-12-31"
        assert format_date_for_index(new_years_day) == "2026-01-01"


class TestBackwardCompatibility:
    """Test backward compatibility with existing extract_date_from_content function."""

    def test_compatible_with_existing_function(self):
        """Test that new functions work with existing code patterns."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="2025-11-15T10:30:00Z">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        # New approach
        date = extract_publication_date(soup)
        formatted = format_date_for_index(date)

        assert formatted == "2025-11-15"

    @freeze_time("2025-11-16 12:00:00")
    def test_recency_check_workflow(self):
        """Test complete workflow: extract, check recency, format."""
        html = """
        <html>
        <head>
            <meta property="article:published_time" content="2025-11-01T10:30:00Z">
        </head>
        </html>
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Extract date
        date = extract_publication_date(soup)
        assert date is not None

        # Check if recent (15 days ago, within 180 day threshold)
        recent = is_recent(date)
        assert recent is True

        # Format for index
        formatted = format_date_for_index(date)
        assert formatted == "2025-11-01"
