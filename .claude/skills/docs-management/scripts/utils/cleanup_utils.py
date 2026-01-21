#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_utils.py - Shared utilities for cleanup scripts

Provides common patterns used across cleanup scripts:
- Stats tracking dictionaries
- Consistent dry-run and result messaging
- Safe file deletion with stats tracking
- Human-readable size formatting
- Summary printing

Usage:
    from utils.cleanup_utils import (
        create_cleanup_stats,
        log_dry_run,
        log_success,
        log_failure,
        log_skip,
        safe_delete_file,
        format_bytes,
        print_cleanup_summary,
        confirm_action,
    )

    stats = create_cleanup_stats()

    if dry_run:
        log_dry_run("delete", filepath, "stale file")
    else:
        if safe_delete_file(filepath, stats):
            log_success("Deleted", filepath)
        else:
            log_failure("delete", filepath, "permission denied")

    print_cleanup_summary(stats, dry_run=dry_run)
"""

from pathlib import Path


def create_cleanup_stats() -> dict:
    """Create a standard stats dictionary for cleanup operations.

    Returns:
        Dictionary with standard cleanup metrics initialized to zero.

    Example:
        >>> stats = create_cleanup_stats()
        >>> stats['files_deleted'] += 1
    """
    return {
        'files_checked': 0,
        'files_deleted': 0,
        'bytes_freed': 0,
        'skipped': 0,
        'errors': 0,
    }


def log_dry_run(action: str, target: str | Path, details: str = "") -> None:
    """Log a dry-run action consistently.

    Args:
        action: The action that would be performed (e.g., "delete", "remove")
        target: The target file/directory path
        details: Optional additional context

    Example:
        >>> log_dry_run("delete", "/path/to/file.md", "stale file")
        [DRY-RUN] Would delete: /path/to/file.md (stale file)
    """
    detail_str = f" ({details})" if details else ""
    print(f"  [DRY-RUN] Would {action}: {target}{detail_str}")


def log_success(action: str, target: str | Path, details: str = "") -> None:
    """Log a successful action consistently.

    Args:
        action: The action performed (e.g., "Deleted", "Removed")
        target: The target file/directory path
        details: Optional additional context

    Example:
        >>> log_success("Deleted", "/path/to/file.md")
        ✅ Deleted: /path/to/file.md
    """
    detail_str = f" ({details})" if details else ""
    print(f"  ✅ {action}: {target}{detail_str}")


def log_failure(action: str, target: str | Path, error: str) -> None:
    """Log a failed action consistently.

    Args:
        action: The action that failed (e.g., "delete", "remove")
        target: The target file/directory path
        error: Error message or description

    Example:
        >>> log_failure("delete", "/path/to/file.md", "permission denied")
        ❌ Failed to delete /path/to/file.md: permission denied
    """
    print(f"  ❌ Failed to {action} {target}: {error}")


def log_skip(target: str | Path, reason: str) -> None:
    """Log a skipped file/action consistently.

    Args:
        target: The target file/directory path
        reason: Why the file was skipped

    Example:
        >>> log_skip("/path/to/file.md", "not stale")
        ⏭️  Skipped: /path/to/file.md (not stale)
    """
    print(f"  ⏭️  Skipped: {target} ({reason})")


def log_warning(message: str) -> None:
    """Log a warning message consistently.

    Args:
        message: Warning message

    Example:
        >>> log_warning("Directory does not exist")
        ⚠️  Directory does not exist
    """
    print(f"⚠️  {message}")


def log_info(message: str) -> None:
    """Log an informational message consistently.

    Args:
        message: Info message

    Example:
        >>> log_info("No files found")
        ℹ️  No files found
    """
    print(f"ℹ️  {message}")


def safe_delete_file(filepath: Path, stats: dict | None = None) -> bool:
    """Safely delete a file with stats tracking.

    Args:
        filepath: Path to the file to delete
        stats: Optional stats dictionary to update

    Returns:
        True if file was deleted successfully, False otherwise

    Example:
        >>> stats = create_cleanup_stats()
        >>> if safe_delete_file(Path("/path/to/file.md"), stats):
        ...     print("File deleted")
    """
    try:
        file_size = filepath.stat().st_size
        filepath.unlink()

        if stats is not None:
            stats['files_deleted'] += 1
            stats['bytes_freed'] += file_size

        return True
    except FileNotFoundError:
        # File already deleted - not an error
        if stats is not None:
            stats['skipped'] += 1
        return False
    except PermissionError as e:
        if stats is not None:
            stats['errors'] += 1
        log_failure("delete", filepath, str(e))
        return False
    except Exception as e:
        if stats is not None:
            stats['errors'] += 1
        log_failure("delete", filepath, str(e))
        return False


def format_bytes(bytes_count: int) -> str:
    """Format bytes count as human-readable string.

    Args:
        bytes_count: Number of bytes

    Returns:
        Human-readable string (e.g., "1.5 KB", "2.3 MB", "1.0 GB")

    Example:
        >>> format_bytes(1536)
        '1.5 KB'
        >>> format_bytes(1048576)
        '1.0 MB'
    """
    if bytes_count < 1024:
        return f"{bytes_count} B"
    elif bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    elif bytes_count < 1024 * 1024 * 1024:
        return f"{bytes_count / (1024 * 1024):.2f} MB"
    else:
        return f"{bytes_count / (1024 * 1024 * 1024):.2f} GB"


def print_cleanup_summary(stats: dict, dry_run: bool = False,
                          title: str = "CLEANUP SUMMARY") -> None:
    """Print a standardized cleanup summary.

    Args:
        stats: Stats dictionary from cleanup operation
        dry_run: Whether this was a dry run
        title: Title for the summary section

    Example:
        >>> stats = create_cleanup_stats()
        >>> stats['files_deleted'] = 5
        >>> stats['bytes_freed'] = 10240
        >>> print_cleanup_summary(stats)
    """
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)

    if dry_run:
        print("🔍 DRY-RUN - No files were actually deleted")

    # Print stats
    if 'files_checked' in stats and stats['files_checked'] > 0:
        print(f"Files checked: {stats['files_checked']}")

    print(f"Files deleted: {stats['files_deleted']}")

    if stats['bytes_freed'] > 0:
        print(f"Space freed: {format_bytes(stats['bytes_freed'])}")

    if stats.get('skipped', 0) > 0:
        print(f"Files skipped: {stats['skipped']}")

    if stats.get('errors', 0) > 0:
        print(f"Errors: {stats['errors']}")

    print("=" * 60)


def confirm_action(message: str, item_count: int = 0,
                   size_bytes: int = 0) -> bool:
    """Prompt user for confirmation before destructive action.

    Args:
        message: Description of the action
        item_count: Number of items affected (optional)
        size_bytes: Size in bytes affected (optional)

    Returns:
        True if user confirms, False otherwise

    Example:
        >>> if confirm_action("Delete stale files", item_count=5, size_bytes=10240):
        ...     # Proceed with deletion
    """
    print()
    print(f"⚠️  WARNING: {message}")

    if item_count > 0:
        print(f"   Items affected: {item_count}")

    if size_bytes > 0:
        print(f"   Size: {format_bytes(size_bytes)}")

    print("   This action cannot be undone.")
    response = input("\n   Type 'yes' to confirm: ")

    return response.lower() == 'yes'


def print_section_header(title: str, char: str = "=", width: int = 60) -> None:
    """Print a section header consistently.

    Args:
        title: Section title
        char: Character to use for the line
        width: Width of the header line

    Example:
        >>> print_section_header("LOG CLEANUP")
        ============================================================
        LOG CLEANUP
        ============================================================
    """
    print(char * width)
    print(title)
    print(char * width)
