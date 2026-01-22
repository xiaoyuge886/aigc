#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cleanup_scrape.py - Cleanup failed scrape

Safely removes files from a failed scrape directory.

Usage:
    python cleanup_scrape.py --output docs-claude-com/docs
    python cleanup_scrape.py --output docs-claude-com/docs --dry-run
    python cleanup_scrape.py --output docs-claude-com/docs --confirm

Dependencies:
    None (standard library only)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from utils.script_utils import configure_utf8_output
configure_utf8_output()

def cleanup_failed_scrape(output_dir: Path, dry_run: bool = False, 
                         require_confirm: bool = True) -> bool:
    """
    Cleanup failed scrape directory
    
    Args:
        output_dir: Directory to cleanup
        dry_run: If True, show what would be deleted without deleting
        require_confirm: If True, require confirmation before deleting
    
    Returns:
        True if successful, False otherwise
    """
    if not output_dir.exists():
        print(f"⚠️  Directory does not exist: {output_dir}")
        return False
    
    # Find all markdown files
    md_files = list(output_dir.glob("**/*.md"))
    
    if not md_files:
        print(f"ℹ️  No markdown files found in {output_dir}")
        return True
    
    # Count files and calculate size
    total_size = sum(f.stat().st_size for f in md_files)
    size_mb = total_size / 1024 / 1024
    
    print(f"\n📊 Cleanup Analysis: {output_dir}")
    print(f"   Files to delete: {len(md_files)}")
    print(f"   Total size: {size_mb:.2f} MB")
    
    if dry_run:
        print(f"\n[DRY RUN] Would delete:")
        for f in md_files[:10]:  # Show first 10
            print(f"   - {f.relative_to(output_dir)}")
        if len(md_files) > 10:
            print(f"   ... and {len(md_files) - 10} more files")
        print(f"\n⚠️  DRY RUN - No files were deleted")
        return True
    
    # Require confirmation unless --confirm flag is set
    if require_confirm:
        print(f"\n⚠️  WARNING: This will delete {len(md_files)} files ({size_mb:.2f} MB)")
        response = input("Type 'yes' to confirm: ")
        if response.lower() != 'yes':
            print("❌ Cleanup cancelled")
            return False
    
    # Delete all markdown files
    deleted_count = 0
    errors = []
    
    print(f"\n🗑️  Deleting files...")
    for f in md_files:
        try:
            f.unlink()
            deleted_count += 1
        except Exception as e:
            errors.append(f"Error deleting {f}: {e}")
    
    # Delete empty directories (bottom-up)
    print(f"   Cleaning up empty directories...")
    for d in reversed(list(output_dir.rglob('*'))):
        if d.is_dir() and not any(d.iterdir()):
            try:
                d.rmdir()
            except Exception:
                pass  # Ignore errors on directory removal
    
    # Summary
    print(f"\n{'='*60}")
    if deleted_count == len(md_files):
        print(f"✅ Cleanup complete: {deleted_count} files deleted")
        if errors:
            print(f"⚠️  {len(errors)} errors occurred (see above)")
        return True
    else:
        print(f"❌ Cleanup incomplete: {deleted_count}/{len(md_files)} files deleted")
        if errors:
            print(f"\n   Errors:")
            for error in errors[:10]:
                print(f"      - {error}")
        return False

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Cleanup failed scrape',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Dry run (show what would be deleted)
  python cleanup_scrape.py --output docs-claude-com/docs --dry-run
  
  # Cleanup with confirmation prompt
  python cleanup_scrape.py --output docs-claude-com/docs
  
  # Cleanup without confirmation (use with caution)
  python cleanup_scrape.py --output docs-claude-com/docs --confirm
  
  # Custom base directory
  python cleanup_scrape.py --output docs-claude-com/docs --base-dir custom/references
        """
    )
    
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args

    parser.add_argument('--output', required=True,
                       help='Output directory to cleanup (relative to base-dir)')
    add_base_dir_argument(parser)
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be deleted without deleting')
    parser.add_argument('--confirm', action='store_true',
                       help='Skip confirmation prompt (use with caution)')
    
    args = parser.parse_args()
    
    # Resolve base directory using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)
    output_dir = base_dir / args.output
    
    success = cleanup_failed_scrape(output_dir, dry_run=args.dry_run, 
                                   require_confirm=not args.confirm)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

