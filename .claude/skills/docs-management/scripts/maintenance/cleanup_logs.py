#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_logs.py - Log retention management for docs-management skill

Cleans up old log files to prevent unbounded growth:
- Delete logs older than N days (configurable, default: 30)
- Keep last N diagnostics per script (configurable, default: 10)
- Dry-run mode for preview
- Summary of cleaned files

Usage:
    python cleanup_logs.py                          # Default cleanup (30 days, keep 10)
    python cleanup_logs.py --days 7                 # Delete logs older than 7 days
    python cleanup_logs.py --keep-diagnostics 5     # Keep only 5 latest diagnostics per script
    python cleanup_logs.py --dry-run                # Preview what would be deleted
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir

import argparse
from datetime import datetime, timezone
from collections import defaultdict

from utils.script_utils import configure_utf8_output, EXIT_SUCCESS
from utils.logging_utils import get_or_setup_logger

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

logger = get_or_setup_logger(__file__, log_category="maintenance")


def get_file_age_days(file_path: Path) -> float:
    """Get file age in days based on modification time."""
    mtime = file_path.stat().st_mtime
    age_seconds = datetime.now(timezone.utc).timestamp() - mtime
    return age_seconds / (24 * 60 * 60)


def cleanup_old_logs(logs_dir: Path, max_age_days: int, dry_run: bool = False) -> dict:
    """
    Delete log files older than max_age_days.

    Args:
        logs_dir: Directory containing log files
        max_age_days: Maximum age in days before deletion
        dry_run: If True, don't actually delete files

    Returns:
        Dictionary with cleanup statistics
    """
    stats = {
        'files_checked': 0,
        'files_deleted': 0,
        'bytes_freed': 0,
        'skipped': 0
    }

    if not logs_dir.exists():
        print(f"⚠️  Logs directory does not exist: {logs_dir}")
        return stats

    # Find all log files
    log_patterns = ['*.log', '*.txt']
    log_files = []
    for pattern in log_patterns:
        log_files.extend(logs_dir.rglob(pattern))

    for log_file in log_files:
        stats['files_checked'] += 1
        age_days = get_file_age_days(log_file)

        if age_days > max_age_days:
            file_size = log_file.stat().st_size
            if dry_run:
                print(f"  [DRY-RUN] Would delete: {log_file.relative_to(logs_dir)} ({age_days:.1f} days old, {file_size:,} bytes)")
            else:
                try:
                    log_file.unlink()
                    stats['files_deleted'] += 1
                    stats['bytes_freed'] += file_size
                    print(f"  ✅ Deleted: {log_file.relative_to(logs_dir)} ({age_days:.1f} days old)")
                except Exception as e:
                    print(f"  ❌ Failed to delete {log_file}: {e}")
                    stats['skipped'] += 1
        else:
            stats['skipped'] += 1

    return stats


def cleanup_diagnostics(diagnostics_dir: Path, keep_count: int, dry_run: bool = False) -> dict:
    """
    Keep only the latest N diagnostics files per script.

    Args:
        diagnostics_dir: Directory containing diagnostics JSON files
        keep_count: Number of latest files to keep per script
        dry_run: If True, don't actually delete files

    Returns:
        Dictionary with cleanup statistics
    """
    stats = {
        'files_checked': 0,
        'files_deleted': 0,
        'bytes_freed': 0,
        'scripts_processed': 0
    }

    if not diagnostics_dir.exists():
        print(f"⚠️  Diagnostics directory does not exist: {diagnostics_dir}")
        return stats

    # Group diagnostics by script name
    script_files = defaultdict(list)

    for diag_file in diagnostics_dir.glob('*_diagnostics.json'):
        stats['files_checked'] += 1
        # Parse filename: script_name_YYYYMMDD_HHMMSS_diagnostics.json
        name = diag_file.stem.replace('_diagnostics', '')
        # Extract script name (everything before the timestamp)
        parts = name.rsplit('_', 2)
        if len(parts) >= 3:
            script_name = parts[0]
        else:
            script_name = name

        script_files[script_name].append(diag_file)

    # For each script, keep only the latest N files
    for script_name, files in script_files.items():
        stats['scripts_processed'] += 1

        # Sort by modification time (newest first)
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Delete older files beyond keep_count
        files_to_delete = files[keep_count:]

        for old_file in files_to_delete:
            file_size = old_file.stat().st_size
            if dry_run:
                print(f"  [DRY-RUN] Would delete: {old_file.name} ({script_name})")
            else:
                try:
                    old_file.unlink()
                    stats['files_deleted'] += 1
                    stats['bytes_freed'] += file_size
                    print(f"  ✅ Deleted: {old_file.name} ({script_name})")
                except Exception as e:
                    print(f"  ❌ Failed to delete {old_file}: {e}")

    return stats


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Clean up old log files and diagnostics',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--days', type=int, default=30,
                       help='Delete logs older than N days (default: 30)')
    parser.add_argument('--keep-diagnostics', type=int, default=10,
                       help='Keep N latest diagnostics per script (default: 10)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Preview what would be deleted without deleting')

    args = parser.parse_args()

    # Log script start
    logger.start({
        'max_age_days': args.days,
        'keep_diagnostics': args.keep_diagnostics,
        'dry_run': args.dry_run
    })

    logs_dir = skill_dir / 'logs'
    diagnostics_dir = logs_dir / 'diagnostics'

    print("=" * 60)
    print("LOG CLEANUP")
    print("=" * 60)
    print(f"Logs directory: {logs_dir}")
    print(f"Max age: {args.days} days")
    print(f"Keep diagnostics per script: {args.keep_diagnostics}")
    print(f"Mode: {'DRY-RUN (no files will be deleted)' if args.dry_run else 'LIVE'}")
    print()

    total_stats = {
        'files_deleted': 0,
        'bytes_freed': 0
    }

    # Clean up old log files
    print("📂 Cleaning up old log files...")
    log_subdirs = ['scrape', 'index', 'maintenance']
    for subdir in log_subdirs:
        subdir_path = logs_dir / subdir
        if subdir_path.exists():
            print(f"\n  {subdir}/")
            stats = cleanup_old_logs(subdir_path, args.days, args.dry_run)
            total_stats['files_deleted'] += stats['files_deleted']
            total_stats['bytes_freed'] += stats['bytes_freed']

    # Clean up diagnostics
    print("\n📊 Cleaning up diagnostics (keeping latest {})...".format(args.keep_diagnostics))
    diag_stats = cleanup_diagnostics(diagnostics_dir, args.keep_diagnostics, args.dry_run)
    total_stats['files_deleted'] += diag_stats['files_deleted']
    total_stats['bytes_freed'] += diag_stats['bytes_freed']

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if args.dry_run:
        print("🔍 DRY-RUN - No files were actually deleted")
    print(f"Files deleted: {total_stats['files_deleted']}")
    print(f"Space freed: {total_stats['bytes_freed']:,} bytes ({total_stats['bytes_freed'] / 1024:.1f} KB)")

    # Track metrics
    logger.track_metric('files_deleted', total_stats['files_deleted'])
    logger.track_metric('bytes_freed', total_stats['bytes_freed'])

    logger.end(exit_code=EXIT_SUCCESS, summary={
        'files_deleted': total_stats['files_deleted'],
        'bytes_freed': total_stats['bytes_freed'],
        'dry_run': args.dry_run
    })

    return EXIT_SUCCESS


if __name__ == '__main__':
    sys.exit(main())
