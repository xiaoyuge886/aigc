#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_index.py - One-shot orchestration to refresh the docs-management index

Runs the full, typical pipeline in the foreground so agents don't need to
chain multiple background commands:

1. Check dependencies
2. Rebuild index from filesystem
3. Extract keywords / metadata for all documents
4. Validate metadata coverage
5. Generate a summary report

This script is designed specifically so tools like Claude Code can run a
single, short-lived command (no background job, no polling loops) and rely
on the final "REFRESH_INDEX_DONE" sentinel line.

IMPORTANT: This script only prints plain ASCII to avoid Windows console
encoding issues. Do not wrap it in additional environment prefixes; just run:

    python .claude/skills/docs-management/scripts/refresh_index.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; scripts_dir = bootstrap.scripts_dir

import argparse
import os
import subprocess
from datetime import datetime, timezone

from utils.script_utils import format_duration, EXIT_SUCCESS
from utils.logging_utils import get_or_setup_logger

logger = get_or_setup_logger(__file__, log_category="index")

# Import path_config for base_dir
try:
    from utils.path_config import get_base_dir
except ImportError:
    def get_base_dir(start=None):
        from utils.common_paths import find_repo_root
        repo_root = find_repo_root(start)
        return repo_root / ".claude" / "skills" / "docs-management" / "canonical"

def run_step(description: str, cmd: list) -> bool:
    """Run a subprocess step with simple logging (ASCII-only)."""
    print()
    print("=" * 80)
    print(f">>> {description}")
    print(f"    Command: {' '.join(cmd)}")
    print("=" * 80)
    start = datetime.now()
    logger.debug(f"Starting step: {description}")

    try:
        # Let subprocess inherit stdout/stderr to avoid encoding issues
        result = subprocess.run(
            cmd,
            check=False,
            text=True,
        )
    except KeyboardInterrupt:
        print("\n[ERROR] Aborted by user (KeyboardInterrupt)")
        logger.warning(f"Step aborted by user: {description}")
        return False

    duration = (datetime.now() - start).total_seconds()
    status = "OK" if result.returncode == 0 else "FAIL"
    print()
    print(f"[{status}] Finished: {description} (exit code {result.returncode}, {format_duration(duration)})")

    # Log structured metrics for step
    logger.info(f"Step completed: {description} [{status}]")
    logger.track_metric(f"step_{description.lower().replace(' ', '_')}_duration", duration)
    logger.track_metric(f"step_{description.lower().replace(' ', '_')}_exit_code", result.returncode)

    return result.returncode == 0

# Individual step functions for modular execution
def step_check_dependencies(root_scripts_dir: Path) -> bool:
    """Step 1: Check dependencies"""
    return run_step(
        "Check dependencies",
        [sys.executable, str(root_scripts_dir / "setup" / "check_dependencies.py")],
    )

def step_rebuild_index(scripts_dir: Path) -> bool:
    """Step 2: Rebuild index from filesystem"""
    return run_step(
        "Rebuild index from filesystem",
        [sys.executable, str(scripts_dir / "management" / "rebuild_index.py")],
    )

def step_extract_keywords(scripts_dir: Path) -> bool:
    """Step 3: Extract keywords and metadata for all documents"""
    return run_step(
        "Extract keywords and metadata for all documents",
        [
            sys.executable,
            str(scripts_dir / "management" / "manage_index.py"),
            "extract-keywords",
        ],
    )

def step_validate_metadata(scripts_dir: Path) -> bool:
    """Step 4: Validate metadata coverage"""
    return run_step(
        "Validate metadata coverage",
        [
            sys.executable,
            str(scripts_dir / "management" / "manage_index.py"),
            "validate-metadata",
        ],
    )

def step_generate_report(scripts_dir: Path) -> bool:
    """Step 5: Generate index metadata report"""
    return run_step(
        "Generate index metadata report",
        [sys.executable, str(scripts_dir / "management" / "generate_report.py")],
    )

def check_missing_files(scripts_dir: Path, base_dir: Path, cleanup: bool = False) -> bool:
    """
    Check for missing files (orphaned index entries) before rebuilding index.
    
    Args:
        scripts_dir: Directory containing scripts
        base_dir: Base directory for canonical storage
        cleanup: If True, automatically cleanup orphaned entries (default: False)
    
    Returns:
        True if check succeeded (non-fatal), False if fatal error
    """
    try:
        from maintenance.cleanup_drift import DriftCleaner
        cleaner = DriftCleaner(base_dir, dry_run=not cleanup)
        
        # Load index to check for missing files
        try:
            from management.index_manager import IndexManager
            manager = IndexManager(base_dir)
            index = manager.load_all()
        except Exception as e:
            print(f"⚠️  Could not load index for missing file check: {e}")
            return True  # Continue if we can't check
        
        missing = cleaner.find_missing_files(index)
        if missing:
            print(f"\n⚠️  Found {len(missing)} orphaned index entries (files missing from filesystem):")
            for doc_id, path in missing[:10]:  # Show first 10
                print(f"     - {doc_id}: {path}")
            if len(missing) > 10:
                print(f"     ... and {len(missing) - 10} more")
            
            if cleanup:
                print("\n🧹 Cleaning up orphaned entries...")
                files_checked, index_removed = cleaner.clean_missing_files(index)
                print(f"     Removed {index_removed} index entries for missing files")
                if index_removed > 0:
                    cleaner.write_audit_log()
            else:
                print("\n💡 Tip: Use --cleanup-missing-files to automatically remove orphaned entries")
            return True  # Non-fatal, continue
        else:
            print("✅ No missing files detected")
            return True
    except ImportError:
        print("⚠️  cleanup_drift module not available, skipping missing file check")
        return True  # Non-fatal, continue
    except Exception as e:
        print(f"⚠️  Error checking for missing files: {e}")
        return True  # Non-fatal, continue

def detect_drift(scripts_dir: Path, base_dir: Path, cleanup: bool = False, max_workers: int | None = None) -> bool:
    """
    Detect drift in documentation (404s, missing files, hash mismatches).
    
    Args:
        scripts_dir: Directory containing scripts
        base_dir: Base directory for canonical storage
        cleanup: If True, automatically cleanup detected drift
        max_workers: Maximum parallel workers for drift detection. If None, uses config default.
    
    Returns:
        True if drift was detected, False otherwise
    """
    # Import config helpers for default max_workers (should always be available)
    from utils.config_helpers import get_drift_max_workers
    if max_workers is None:
        max_workers = get_drift_max_workers()
    try:
        from maintenance.cleanup_drift import DriftCleaner
        from maintenance.detect_changes import ChangeDetector
        from management.index_manager import IndexManager
        
        print("\n🔍 Detecting drift...")
        
        # Load index
        manager = IndexManager(base_dir)
        index = manager.load_all()
        
        if not index:
            print("  ⏭️  No index entries found, skipping drift detection")
            return False
        
        drift_detected = False
        
        # Check for missing files
        cleaner = DriftCleaner(base_dir, dry_run=not cleanup)
        missing = cleaner.find_missing_files(index)
        missing_count = len(missing)
        
        if missing_count > 0:
            drift_detected = True
            print(f"\n  ⚠️  Found {missing_count} missing files:")
            for doc_id, path in missing[:10]:  # Show first 10
                print(f"     - {doc_id}: {path}")
            if missing_count > 10:
                print(f"     ... and {missing_count - 10} more")
            
            if cleanup:
                print("\n  🧹 Cleaning up missing files...")
                files_checked, index_removed = cleaner.clean_missing_files(index)
                print(f"     Removed {index_removed} index entries for missing files")
        
        # Check for 404 URLs (sample check - full check would be expensive)
        # We'll check a sample of URLs to detect if there are widespread 404s
        detector = ChangeDetector(base_dir)
        sample_urls = []
        for doc_id, metadata in list(index.items())[:50]:  # Sample first 50
            url = metadata.get('source_url') or metadata.get('url')
            if url:
                sample_urls.append(url)
        
        if sample_urls:
            print(f"\n  Checking sample of {len(sample_urls)} URLs for 404 status...")
            url_404s = detector.check_404_urls(set(sample_urls), max_workers=max_workers)
            url_404_count = sum(1 for is_404 in url_404s.values() if is_404)
            
            if url_404_count > 0:
                drift_detected = True
                print(f"  ⚠️  Found {url_404_count} 404 URLs in sample")
                print(f"     💡 Tip: Run cleanup_drift.py --clean-404s for full cleanup")
        
        if not drift_detected:
            print("  ✅ No drift detected")
        
        return drift_detected
        
    except ImportError as e:
        print(f"⚠️  Drift detection not available: {e}")
        print("   Ensure cleanup_drift.py and detect_changes.py are available")
        return False
    except Exception as e:
        print(f"⚠️  Error during drift detection: {e}")
        import traceback
        traceback.print_exc()
        return False

def main() -> int:
    """Main entry point for refresh_index orchestration."""
    parser = argparse.ArgumentParser(
        description='Refresh docs-management index (rebuild, extract keywords, validate)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--check-missing-files',
        action='store_true',
        help='Check for missing files (orphaned index entries) before rebuilding index'
    )
    parser.add_argument(
        '--cleanup-missing-files',
        action='store_true',
        help='Automatically cleanup orphaned index entries (requires --check-missing-files)'
    )
    parser.add_argument(
        '--check-drift',
        action='store_true',
        help='Detect drift (404s, missing files) after rebuilding index'
    )
    parser.add_argument(
        '--cleanup-drift',
        action='store_true',
        help='Automatically cleanup detected drift (requires --check-drift)'
    )
    # Get default from config (config_helpers should always be available)
    try:
        from utils.config_helpers import get_drift_max_workers
        default_max_workers = get_drift_max_workers()
    except ImportError:
        # Fallback if config_helpers not available (shouldn't happen)
        default_max_workers = 5
    
    parser.add_argument(
        '--drift-max-workers',
        type=int,
        default=default_max_workers,
        help=f'Maximum parallel workers for drift detection (default: {default_max_workers}, from config)'
    )
    parser.add_argument(
        '--step',
        choices=['check-dependencies', 'rebuild-index', 'extract-keywords', 'validate-metadata', 'generate-report'],
        help='Run a specific step only (modular execution)'
    )
    parser.add_argument(
        '--clear-cache',
        action='store_true',
        help='Clear all caches before refresh (inverted index + LLMS)'
    )
    args = parser.parse_args()

    # Print dev/prod mode banner for visibility
    from utils.dev_mode import print_mode_banner
    print_mode_banner(logger)

    # Validate arguments
    if args.cleanup_missing_files and not args.check_missing_files:
        print("❌ --cleanup-missing-files requires --check-missing-files")
        return 1
    if args.cleanup_drift and not args.check_drift:
        print("❌ --cleanup-drift requires --check-drift")
        return 1
    
    # scripts_dir already set by setup_python_path() at top of file
    start_time = datetime.now()
    base_dir = get_base_dir()

    # Clear cache if requested
    if args.clear_cache:
        try:
            from utils.cache_manager import CacheManager
            cm = CacheManager(base_dir)
            result = cm.clear_all()
            if result['inverted_index'] or result['llms_cache']:
                print("Cache cleared:")
                if result['inverted_index']:
                    print("  - Inverted index cache cleared")
                if result['llms_cache']:
                    print("  - LLMS/scraper cache cleared")
            else:
                print("Cache was already empty")
            print()
        except ImportError:
            print("Warning: CacheManager not available, skipping cache clear")
        except Exception as e:
            print(f"Warning: Failed to clear cache: {e}")

    # Log script start with parameters
    logger.start({
        'check_missing_files': args.check_missing_files,
        'cleanup_missing_files': args.cleanup_missing_files,
        'check_drift': args.check_drift,
        'cleanup_drift': args.cleanup_drift,
        'drift_max_workers': args.drift_max_workers,
        'step': args.step,
        'base_dir': str(base_dir),
    })

    # Print basic Python environment summary for observability
    print("=" * 80)
    print("Claude Docs – refresh_index.py")
    print(f"Python version : {sys.version.split()[0]}")
    print(f"Python exe     : {sys.executable}")
    print(f"Scripts folder : {scripts_dir}")
    if args.step:
        print(f"Running step   : {args.step}")
    print("=" * 80)

    # Handle single-step execution
    if args.step:
        step_ok = False
        if args.step == 'check-dependencies':
            step_ok = step_check_dependencies(scripts_dir)
        elif args.step == 'rebuild-index':
            step_ok = step_rebuild_index(scripts_dir)
        elif args.step == 'extract-keywords':
            step_ok = step_extract_keywords(scripts_dir)
        elif args.step == 'validate-metadata':
            step_ok = step_validate_metadata(scripts_dir)
        elif args.step == 'generate-report':
            step_ok = step_generate_report(scripts_dir)

        if not step_ok:
            print(f"❌ Step '{args.step}' failed. See output above.")
            logger.end(exit_code=1, summary={'step': args.step, 'status': 'failed'})
            return 1

        print("\nStep execution complete.")
        print("REFRESH_INDEX_DONE")
        logger.end(exit_code=EXIT_SUCCESS, summary={'step': args.step, 'status': 'ok'})
        return EXIT_SUCCESS

    # Full workflow execution
    # Optional: Check for missing files before rebuilding
    if args.check_missing_files:
        print()
        print("=" * 80)
        print(">>> Pre-flight: Check for missing files")
        print("=" * 80)
        check_missing_files(scripts_dir, base_dir, cleanup=args.cleanup_missing_files)
        print()

    # 1) Check dependencies
    step1_ok = step_check_dependencies(scripts_dir)
    if not step1_ok:
        print("❌ Dependency check failed. See output above.")
        logger.end(exit_code=1, summary={'failed_step': 'check_dependencies'})
        return 1

    # 2) Rebuild index from filesystem
    step2_ok = step_rebuild_index(scripts_dir)
    if not step2_ok:
        print("❌ Index rebuild failed. See output above.")
        logger.end(exit_code=1, summary={'failed_step': 'rebuild_index'})
        return 1

    # 3) Extract keywords / metadata (foreground, no background jobs)
    #    This typically completes in under 30 seconds for ~500 docs.
    step3_ok = step_extract_keywords(scripts_dir)
    if not step3_ok:
        print("❌ Keyword/metadata extraction failed. See output above.")
        logger.end(exit_code=1, summary={'failed_step': 'extract_keywords'})
        return 1

    # 4) Validate metadata coverage
    step4_ok = step_validate_metadata(scripts_dir)
    if not step4_ok:
        print("❌ Metadata validation reported issues. See output above.")
        # Keep going so we still generate the report, but return non‑zero at the end
        validation_failed = True
    else:
        validation_failed = False

    # 5) Generate summary report
    step5_ok = step_generate_report(scripts_dir)
    if not step5_ok:
        print("❌ Report generation failed. See output above.")
        logger.end(exit_code=1, summary={'failed_step': 'generate_report'})
        return 1

    # Optional: Detect and cleanup drift
    drift_detected = False
    if args.check_drift:
        print()
        print("=" * 80)
        print(">>> Optional: Detect drift")
        print("=" * 80)
        drift_detected = detect_drift(
            scripts_dir,
            base_dir,
            cleanup=args.cleanup_drift,
            max_workers=args.drift_max_workers
        )
        print()

    # Calculate total duration
    total_duration = (datetime.now() - start_time).total_seconds()
    
    print()
    print("Index refresh complete.")
    print("  - Dependencies checked")
    print("  - Index rebuilt from filesystem")
    print("  - Keywords / metadata extracted")
    print("  - Metadata validated")
    print("  - Summary report generated")
    if args.check_drift:
        print("  - Drift detection completed" + (" (drift detected)" if drift_detected else " (no drift)"))
    print()
    print(f"Total duration: {format_duration(total_duration)}")
    print()
    print("Expected runtime: ~20-30 seconds for ~500 documents on a typical dev machine.")
    print("This command is designed to be run in the foreground (no background job needed).")
    print()

    # Optional per-run markdown report for humans/agents
    if os.environ.get("CLAUDE_DOCS_RUN_REPORT"):
        try:
            # scripts_dir = <project-root>/.claude/skills/docs-management/scripts
            # Use path_config for temp directory
            from path_config import get_temp_dir
            temp_dir = get_temp_dir()
            temp_dir.mkdir(parents=True, exist_ok=True)
            now_utc = datetime.now(timezone.utc)
            timestamp = now_utc.strftime("%Y-%m-%d_%H%M%S")
            report_path = temp_dir / f"{timestamp}-docs-management-refresh-report.md"
            with report_path.open("w", encoding="utf-8") as f:
                f.write("# Claude Docs Index Refresh Report\n\n")
                f.write(f"- **Timestamp (UTC)**: {now_utc.isoformat().replace('+00:00', 'Z')}\n")
                f.write(f"- **Python**: `{sys.version.split()[0]}`\n")
                f.write(f"- **Executable**: `{sys.executable}`\n")
                f.write("\n## Step Status\n\n")
                f.write(f"- Check dependencies: {'OK' if step1_ok else 'FAIL'}\n")
                f.write(f"- Rebuild index: {'OK' if step2_ok else 'FAIL'}\n")
                f.write(f"- Extract keywords/metadata: {'OK' if step3_ok else 'FAIL'}\n")
                f.write(f"- Validate metadata: {'OK' if step4_ok else 'FAIL'}\n")
                f.write(f"- Generate report: {'OK' if step5_ok else 'FAIL'}\n")
                f.write("\n> This file is generated by `refresh_index.py` when `CLAUDE_DOCS_RUN_REPORT=1`.\n")
            print(f"Run report written to: {report_path}")
        except Exception as e:
            print(f"⚠️  Failed to write run report: {e}")
            # Non-fatal; continue

    # Sentinel line for tools/agents to detect completion reliably
    print("REFRESH_INDEX_DONE")

    # Track total metrics
    logger.track_metric('total_duration_seconds', total_duration)
    logger.track_metric('validation_failed', int(validation_failed))
    logger.track_metric('drift_detected', int(drift_detected))

    # Exit code: 0 = success, 1 = validation failed, 2 = drift detected
    if validation_failed:
        logger.end(exit_code=1, summary={
            'status': 'validation_failed',
            'total_duration': format_duration(total_duration),
            'drift_detected': drift_detected,
        })
        return 1
    elif drift_detected:
        logger.end(exit_code=2, summary={
            'status': 'drift_detected',
            'total_duration': format_duration(total_duration),
        })
        return 2
    else:
        logger.end(exit_code=EXIT_SUCCESS, summary={
            'status': 'success',
            'total_duration': format_duration(total_duration),
            'steps_completed': 5,
        })
        return EXIT_SUCCESS

if __name__ == "__main__":
    sys.exit(main())

