#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rebuild_index.py - Rebuild index.yaml from filesystem

Scans the filesystem for all markdown files in the base directory (default:
.claude/skills/docs-management/canonical from config) and rebuilds the index.yaml file. Handles:
- New files (adds to index)
- Renamed files (detects via content hash, keeps NEW doc_id as primary,
  adds OLD doc_id as alias for backward compatibility, removes old entry)
- Moved files (updates path)
- Removed files (marks as stale or removes)

Usage:
    python rebuild_index.py [--base-dir <path>] [--dry-run]

    # Uses default base-dir from config (typically .claude/skills/docs-management/canonical)
    python rebuild_index.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
from datetime import datetime, timezone

from utils.script_utils import configure_utf8_output, ensure_yaml_installed, EXIT_SUCCESS, EXIT_INDEX_ERROR

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="index")

yaml = ensure_yaml_installed()

try:
    from management.index_manager import IndexManager
except ImportError:
    print("❌ Error: Could not import index_manager")
    print("Make sure index_manager.py is available (management/index_manager.py).")
    sys.exit(EXIT_INDEX_ERROR)

try:
    from management.extract_metadata import MetadataExtractor
except ImportError:
    MetadataExtractor = None

def strip_frontmatter(content: str) -> str:
    """Strip YAML frontmatter from content, returning body only.

    Args:
        content: Full markdown content that may include frontmatter

    Returns:
        Content body without frontmatter
    """
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content

def calculate_hash(content: str, body_only: bool = True) -> str:
    """Calculate SHA-256 hash of content.

    Args:
        content: Full file content
        body_only: If True, strip frontmatter before hashing (default: True)
                   This prevents timestamp-only changes from triggering hash updates

    Returns:
        SHA-256 hash with sha256: prefix
    """
    if body_only:
        content = strip_frontmatter(content)
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return f"sha256:{hash_obj.hexdigest()}"

def extract_doc_id_from_path(path: Path, base_dir: Path) -> str:
    """Generate doc_id from file path"""
    try:
        relative = path.relative_to(base_dir)
    except ValueError:
        # Path is not relative to base_dir, use filename only
        relative = Path(path.name)
    
    # Remove .md extension and convert to kebab-case
    # Normalize path separators first, then replace with hyphens
    relative_str = str(relative).replace('\\', '/')
    doc_id = relative_str.replace('.md', '').replace('/', '-')
    return doc_id

def rebuild_index(base_dir: Path, dry_run: bool = False) -> dict:
    """
    Rebuild index from filesystem
    
    Args:
        base_dir: Base directory for canonical documentation storage
        dry_run: If True, don't write changes
    
    Returns:
        Dictionary with statistics
    """
    logger.info("🔍 Scanning filesystem for markdown files...")

    # Find all markdown files (excluding README.md)
    # Sort the glob results to ensure deterministic processing order
    md_files = []
    for md_file in sorted(base_dir.rglob("*.md")):
        if md_file.name == "README.md":
            continue
        md_files.append(md_file)

    logger.info(f"   Found {len(md_files)} markdown files")
    
    # Load existing index (may be empty on first run)
    manager = IndexManager(base_dir)
    existing_index = manager.load_all()
    if (
        not existing_index
        and manager.index_path.exists()
        and manager.index_path.stat().st_size > 0
        and md_files
    ):
        logger.warning("⚠️  Existing index.yaml is non-empty but loaded as empty.")
        logger.warning("    Skipping writes to avoid accidental data loss – investigate index format.")
    
    # Build hash -> doc_id mapping for rename detection
    hash_to_doc_id: dict[str, str] = {}
    for doc_id, metadata in existing_index.items():
        content_hash = metadata.get('hash')
        if content_hash:
            hash_to_doc_id[content_hash] = doc_id
    
    # Process each file
    new_entries = {}
    updated_entries = {}
    renamed_entries = []
    unchanged_entries = []
    
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding='utf-8')
            content_hash = calculate_hash(content)
            
            # Extract URL from frontmatter
            url = None
            if content.startswith('---'):
                try:
                    parts = content.split('---', 2)
                    if len(parts) >= 3:
                        frontmatter = yaml.safe_load(parts[1])
                        url = frontmatter.get('source_url', '')
                except Exception:
                    pass
            
            # Generate doc_id from path (use forward slashes for cross-platform)
            doc_id = extract_doc_id_from_path(md_file, base_dir)
            relative_path = md_file.relative_to(base_dir)
            # Normalize path to use forward slashes for cross-platform compatibility
            relative_path_str = str(relative_path).replace('\\', '/')
            
            # Check if this hash exists in old index (rename detection)
            # A rename is ONLY detected if:
            # 1. The content hash matches an existing entry
            # 2. The doc_id is different (file path changed)
            # 3. The OLD file path no longer exists on disk
            # If both files exist, they're separate documents with same content, not a rename
            old_doc_id = hash_to_doc_id.get(content_hash)
            if old_doc_id and old_doc_id != doc_id:
                # Check if the old file still exists
                old_entry = existing_index.get(old_doc_id, {})
                old_path_str = old_entry.get('path', '')
                old_file_path = base_dir / old_path_str if old_path_str else None

                if old_file_path and old_file_path.exists():
                    # Both files exist - these are separate documents with same content
                    # NOT a rename - each should have its own index entry
                    pass
                else:
                    # Old file is gone - this is a genuine rename
                    # Keep NEW doc_id (matching actual filename)
                    # Old doc_id will become an alias for backward compatibility
                    renamed_entries.append((old_doc_id, doc_id))
                # doc_id stays as-is (the new one from the actual file path)
            
            # Check if entry exists
            if doc_id in existing_index:
                existing = existing_index[doc_id]
                existing_path = existing.get('path', '')
                
                # Check if path changed (normalize for comparison)
                existing_path_normalized = existing_path.replace('\\', '/')
                if existing_path_normalized != relative_path_str:
                    existing['path'] = relative_path_str
                    updated_entries[doc_id] = existing
                elif existing.get('hash') != content_hash:
                    # Content changed, update hash and date
                    existing['hash'] = content_hash
                    existing['last_fetched'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    updated_entries[doc_id] = existing
                else:
                    unchanged_entries.append(doc_id)
            else:
                # New entry
                new_entry = {
                    'path': relative_path_str,
                    'hash': content_hash,
                    'last_fetched': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
                }
                
                if url:
                    new_entry['url'] = url
                
                # Extract metadata if available
                if MetadataExtractor:
                    try:
                        extractor = MetadataExtractor(md_file, url)
                        extracted = extractor.extract_all()
                        new_entry.update(extracted)
                    except Exception:
                        pass
                
                new_entries[doc_id] = new_entry
        
        except Exception as e:
            logger.warning(f"  ⚠️  Error processing {md_file}: {e}")
            continue
    
    # Find orphaned entries (in index but not in filesystem)
    orphaned = []
    for doc_id, metadata in existing_index.items():
        path_str = metadata.get('path')
        if path_str:
            file_path = base_dir / path_str
            if not file_path.exists():
                orphaned.append(doc_id)
    
    # Log summary
    logger.info(f"\n📊 Rebuild Summary:")
    logger.info(f"   New entries: {len(new_entries)}")
    logger.info(f"   Updated entries: {len(updated_entries)}")
    logger.info(f"   Renamed entries: {len(renamed_entries)}")
    logger.info(f"   Unchanged entries: {len(unchanged_entries)}")
    logger.info(f"   Orphaned entries: {len(orphaned)}")

    if renamed_entries:
        logger.info(f"\n📝 Renamed files (old becomes alias of new):")
        for old_id, new_id in renamed_entries[:10]:
            logger.info(f"   {old_id} -> {new_id} (old removed, added as alias)")
        if len(renamed_entries) > 10:
            logger.info(f"   ... and {len(renamed_entries) - 10} more")

    if orphaned:
        logger.warning(f"\n⚠️  Orphaned entries (file not found):")
        for doc_id in orphaned[:10]:
            logger.warning(f"   {doc_id}")
        if len(orphaned) > 10:
            logger.warning(f"   ... and {len(orphaned) - 10} more")

    # Apply changes if not dry run
    # (existing_index may be empty for first-time builds or after deletion)
    if not dry_run and (existing_index or new_entries):
        logger.info(f"\n💾 Applying changes...")
        
        # Add new entries
        for doc_id, entry in new_entries.items():
            manager.update_entry(doc_id, entry)
        
        # Update existing entries
        for doc_id, entry in updated_entries.items():
            manager.update_entry(doc_id, entry)
        
        # Handle renamed files: OLD doc_id becomes alias of NEW doc_id
        for old_id, new_id in renamed_entries:
            # Get the new entry (just created or updated above)
            new_entry = manager.get_entry(new_id)
            if new_entry:
                # Add old doc_id as alias for backward compatibility
                aliases = new_entry.get('aliases', [])
                if isinstance(aliases, str):
                    aliases = [aliases]
                elif not isinstance(aliases, list):
                    aliases = []
                if old_id not in aliases:
                    aliases.append(old_id)
                    new_entry['aliases'] = aliases
                    manager.update_entry(new_id, new_entry)

            # Remove the old entry if it still exists
            if manager.get_entry(old_id):
                manager.remove_entry(old_id)
        
        logger.info(f"✅ Index rebuilt successfully")
    else:
        logger.info(f"\n🔍 Dry run - no changes applied")
    
    return {
        'scanned': len(md_files),
        'added': len(new_entries),
        'updated': len(updated_entries),
        'renamed': len(renamed_entries),
        'unchanged': len(unchanged_entries),
        'orphaned': len(orphaned)
    }

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Rebuild index.yaml from filesystem',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be changed without applying')
    parser.add_argument('--verify-determinism', action='store_true',
                       help='Run rebuild twice and verify outputs are identical (self-test)')

    args = parser.parse_args()

    # Print dev/prod mode banner for visibility
    from utils.dev_mode import print_mode_banner
    from utils.path_config import get_base_dir
    print_mode_banner(logger)
    logger.info(f"Canonical dir: {get_base_dir()}")

    # Log script start
    logger.start({
        'base_dir': args.base_dir,
        'dry_run': args.dry_run
    })
    
    exit_code = EXIT_SUCCESS
    try:
        # Resolve base directory using cli_utils helper
        base_dir = resolve_base_dir_from_args(args)
        
        if not base_dir.exists():
            logger.error(f"❌ Directory does not exist: {base_dir}")
            exit_code = EXIT_INDEX_ERROR
            raise SystemExit(exit_code)

        # Rebuild index
        with logger.time_operation('rebuild_index'):
            stats = rebuild_index(base_dir, dry_run=args.dry_run)

        if stats['orphaned'] > 0 and not args.dry_run:
            logger.warning(f"\n⚠️  Warning: {stats['orphaned']} orphaned entries found. Review and remove manually if needed.")

        # Determinism verification (self-test)
        if args.verify_determinism and not args.dry_run:
            logger.info(f"\n{'='*60}")
            logger.info(f"DETERMINISM VERIFICATION")
            logger.info(f"{'='*60}")

            # Read first index content
            index_path = base_dir / "index.yaml"
            first_content = index_path.read_text(encoding='utf-8') if index_path.exists() else ""

            # Rebuild again
            logger.info("Running second rebuild for comparison...")
            with logger.time_operation('determinism_verify_rebuild'):
                rebuild_index(base_dir, dry_run=False)

            # Read second index content
            second_content = index_path.read_text(encoding='utf-8') if index_path.exists() else ""

            # Compare
            if first_content == second_content:
                logger.info(f"\n✅ DETERMINISM VERIFIED: Index outputs are identical")
            else:
                # Calculate diff size
                first_lines = first_content.splitlines()
                second_lines = second_content.splitlines()
                diff_count = sum(1 for a, b in zip(first_lines, second_lines) if a != b)
                diff_count += abs(len(first_lines) - len(second_lines))

                logger.warning(f"\n❌ DETERMINISM FAILED: Index outputs differ by {diff_count} lines")
                logger.warning(f"   This indicates non-deterministic behavior that needs investigation.")
                exit_code = 2  # Special exit code for determinism failure

        logger.track_metric('files_scanned', stats.get('scanned', 0))
        logger.track_metric('entries_added', stats.get('added', 0))
        logger.track_metric('entries_updated', stats.get('updated', 0))
        logger.track_metric('orphaned_entries', stats.get('orphaned', 0))
        
        summary = {
            'scanned': stats.get('scanned', 0),
            'added': stats.get('added', 0),
            'updated': stats.get('updated', 0),
            'orphaned': stats.get('orphaned', 0)
        }
        
        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in rebuild_index", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

