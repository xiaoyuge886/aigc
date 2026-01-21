"""
Tests for cleanup_utils module.

Tests the shared cleanup utility functions used across maintenance scripts.
"""

from pathlib import Path
from unittest.mock import patch, MagicMock


from scripts.utils.cleanup_utils import (
    create_cleanup_stats,
    log_dry_run,
    log_success,
    log_failure,
    log_skip,
    log_warning,
    log_info,
    safe_delete_file,
    format_bytes,
    print_cleanup_summary,
    confirm_action,
    print_section_header,
)


class TestCreateCleanupStats:
    """Tests for create_cleanup_stats function."""

    def test_returns_dict_with_all_keys(self):
        """Test that create_cleanup_stats returns dict with all required keys."""
        stats = create_cleanup_stats()

        assert isinstance(stats, dict)
        assert 'files_checked' in stats
        assert 'files_deleted' in stats
        assert 'bytes_freed' in stats
        assert 'skipped' in stats
        assert 'errors' in stats

    def test_all_values_initialized_to_zero(self):
        """Test that all stats values start at zero."""
        stats = create_cleanup_stats()

        assert stats['files_checked'] == 0
        assert stats['files_deleted'] == 0
        assert stats['bytes_freed'] == 0
        assert stats['skipped'] == 0
        assert stats['errors'] == 0

    def test_stats_can_be_incremented(self):
        """Test that stats values can be modified."""
        stats = create_cleanup_stats()

        stats['files_deleted'] += 5
        stats['bytes_freed'] += 1024

        assert stats['files_deleted'] == 5
        assert stats['bytes_freed'] == 1024


class TestLogFunctions:
    """Tests for logging utility functions."""

    def test_log_dry_run_basic(self, capsys):
        """Test log_dry_run outputs expected format."""
        log_dry_run("delete", "/path/to/file.md")
        captured = capsys.readouterr()

        assert "[DRY-RUN]" in captured.out
        assert "Would delete" in captured.out
        assert "/path/to/file.md" in captured.out

    def test_log_dry_run_with_details(self, capsys):
        """Test log_dry_run includes details when provided."""
        log_dry_run("remove", "/path/to/file.md", "stale file")
        captured = capsys.readouterr()

        assert "(stale file)" in captured.out

    def test_log_success_basic(self, capsys):
        """Test log_success outputs expected format with checkmark."""
        log_success("Deleted", "/path/to/file.md")
        captured = capsys.readouterr()

        assert "Deleted" in captured.out
        assert "/path/to/file.md" in captured.out

    def test_log_success_with_details(self, capsys):
        """Test log_success includes details when provided."""
        log_success("Removed", "/path/file.md", "5 KB")
        captured = capsys.readouterr()

        assert "(5 KB)" in captured.out

    def test_log_failure_outputs_error_info(self, capsys):
        """Test log_failure outputs error information."""
        log_failure("delete", "/path/to/file.md", "permission denied")
        captured = capsys.readouterr()

        assert "Failed to delete" in captured.out
        assert "/path/to/file.md" in captured.out
        assert "permission denied" in captured.out

    def test_log_skip_outputs_reason(self, capsys):
        """Test log_skip outputs skip reason."""
        log_skip("/path/to/file.md", "not stale")
        captured = capsys.readouterr()

        assert "Skipped" in captured.out
        assert "/path/to/file.md" in captured.out
        assert "(not stale)" in captured.out

    def test_log_warning_outputs_message(self, capsys):
        """Test log_warning outputs warning message."""
        log_warning("Directory does not exist")
        captured = capsys.readouterr()

        assert "Directory does not exist" in captured.out

    def test_log_info_outputs_message(self, capsys):
        """Test log_info outputs info message."""
        log_info("No files found")
        captured = capsys.readouterr()

        assert "No files found" in captured.out


class TestSafeDeleteFile:
    """Tests for safe_delete_file function."""

    def test_delete_existing_file(self, tmp_path):
        """Test deleting an existing file succeeds."""
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")
        stats = create_cleanup_stats()

        result = safe_delete_file(test_file, stats)

        assert result is True
        assert not test_file.exists()
        assert stats['files_deleted'] == 1
        assert stats['bytes_freed'] > 0

    def test_delete_nonexistent_file(self, tmp_path):
        """Test deleting nonexistent file returns False and increments skipped."""
        test_file = tmp_path / "nonexistent.md"
        stats = create_cleanup_stats()

        result = safe_delete_file(test_file, stats)

        assert result is False
        assert stats['skipped'] == 1
        assert stats['files_deleted'] == 0

    def test_delete_without_stats(self, tmp_path):
        """Test deleting without stats dict works."""
        test_file = tmp_path / "test.md"
        test_file.write_text("test content")

        result = safe_delete_file(test_file, stats=None)

        assert result is True
        assert not test_file.exists()

    def test_delete_permission_error(self, tmp_path):
        """Test handling permission errors."""
        test_file = tmp_path / "test.md"
        stats = create_cleanup_stats()

        with patch.object(Path, 'unlink', side_effect=PermissionError("Access denied")):
            with patch.object(Path, 'stat', return_value=MagicMock(st_size=100)):
                result = safe_delete_file(test_file, stats)

        assert result is False
        assert stats['errors'] == 1


class TestFormatBytes:
    """Tests for format_bytes function."""

    def test_format_bytes_zero(self):
        """Test formatting zero bytes."""
        assert format_bytes(0) == "0 B"

    def test_format_bytes_small(self):
        """Test formatting small byte values."""
        assert format_bytes(512) == "512 B"
        assert format_bytes(1023) == "1023 B"

    def test_format_kilobytes(self):
        """Test formatting kilobyte values."""
        assert format_bytes(1024) == "1.0 KB"
        assert format_bytes(1536) == "1.5 KB"
        assert format_bytes(10240) == "10.0 KB"

    def test_format_megabytes(self):
        """Test formatting megabyte values."""
        assert format_bytes(1024 * 1024) == "1.00 MB"
        assert format_bytes(5 * 1024 * 1024) == "5.00 MB"

    def test_format_gigabytes(self):
        """Test formatting gigabyte values."""
        assert format_bytes(1024 * 1024 * 1024) == "1.00 GB"
        assert format_bytes(2 * 1024 * 1024 * 1024) == "2.00 GB"


class TestPrintCleanupSummary:
    """Tests for print_cleanup_summary function."""

    def test_summary_shows_files_deleted(self, capsys):
        """Test summary shows files deleted count."""
        stats = create_cleanup_stats()
        stats['files_deleted'] = 5

        print_cleanup_summary(stats)
        captured = capsys.readouterr()

        assert "Files deleted: 5" in captured.out

    def test_summary_shows_bytes_freed(self, capsys):
        """Test summary shows space freed when > 0."""
        stats = create_cleanup_stats()
        stats['files_deleted'] = 1
        stats['bytes_freed'] = 10240

        print_cleanup_summary(stats)
        captured = capsys.readouterr()

        assert "Space freed:" in captured.out
        assert "10.0 KB" in captured.out

    def test_dry_run_indicator(self, capsys):
        """Test dry-run mode indicator is shown."""
        stats = create_cleanup_stats()

        print_cleanup_summary(stats, dry_run=True)
        captured = capsys.readouterr()

        assert "DRY-RUN" in captured.out

    def test_custom_title(self, capsys):
        """Test custom title is used."""
        stats = create_cleanup_stats()

        print_cleanup_summary(stats, title="CUSTOM TITLE")
        captured = capsys.readouterr()

        assert "CUSTOM TITLE" in captured.out

    def test_shows_errors_when_present(self, capsys):
        """Test errors count is shown when > 0."""
        stats = create_cleanup_stats()
        stats['errors'] = 3

        print_cleanup_summary(stats)
        captured = capsys.readouterr()

        assert "Errors: 3" in captured.out

    def test_shows_skipped_when_present(self, capsys):
        """Test skipped count is shown when > 0."""
        stats = create_cleanup_stats()
        stats['skipped'] = 7

        print_cleanup_summary(stats)
        captured = capsys.readouterr()

        assert "Files skipped: 7" in captured.out


class TestConfirmAction:
    """Tests for confirm_action function."""

    def test_confirm_returns_true_on_yes(self):
        """Test confirmation returns True when user types 'yes'."""
        with patch('builtins.input', return_value='yes'):
            result = confirm_action("Delete files")

        assert result is True

    def test_confirm_returns_false_on_no(self):
        """Test confirmation returns False when user types 'no'."""
        with patch('builtins.input', return_value='no'):
            result = confirm_action("Delete files")

        assert result is False

    def test_confirm_returns_false_on_empty(self):
        """Test confirmation returns False on empty input."""
        with patch('builtins.input', return_value=''):
            result = confirm_action("Delete files")

        assert result is False

    def test_confirm_case_insensitive(self):
        """Test confirmation accepts 'YES', 'Yes', etc."""
        with patch('builtins.input', return_value='YES'):
            result = confirm_action("Delete files")

        assert result is True

    def test_confirm_shows_item_count(self, capsys):
        """Test confirmation shows item count."""
        with patch('builtins.input', return_value='no'):
            confirm_action("Delete files", item_count=10)
            captured = capsys.readouterr()

        assert "Items affected: 10" in captured.out

    def test_confirm_shows_size(self, capsys):
        """Test confirmation shows size."""
        with patch('builtins.input', return_value='no'):
            confirm_action("Delete files", size_bytes=10240)
            captured = capsys.readouterr()

        assert "Size:" in captured.out
        assert "10.0 KB" in captured.out


class TestPrintSectionHeader:
    """Tests for print_section_header function."""

    def test_prints_header_with_default_char(self, capsys):
        """Test section header uses default character."""
        print_section_header("TEST HEADER")
        captured = capsys.readouterr()

        assert "TEST HEADER" in captured.out
        assert "=" * 60 in captured.out

    def test_prints_header_with_custom_char(self, capsys):
        """Test section header uses custom character."""
        print_section_header("TEST HEADER", char="-")
        captured = capsys.readouterr()

        assert "-" * 60 in captured.out

    def test_prints_header_with_custom_width(self, capsys):
        """Test section header uses custom width."""
        print_section_header("TEST", char="=", width=40)
        captured = capsys.readouterr()

        assert "=" * 40 in captured.out
