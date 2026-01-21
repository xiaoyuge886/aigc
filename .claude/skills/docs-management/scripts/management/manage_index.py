#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
manage_index.py - CLI tool for managing index.yaml

Standalone CLI tool for common index operations that can be used by
Claude Code or manually.

Usage:
    python manage_index.py get <doc_id>
    python manage_index.py update <doc_id> <metadata_json>
    python manage_index.py remove <doc_id>
    python manage_index.py list [--filter <field>=<value>]
    python manage_index.py count
    python manage_index.py verify

Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json

from utils.cli_utils import add_common_index_args
from utils.metadata_utils import normalize_keywords, normalize_tags
from utils.script_utils import (
    configure_utf8_output,
    resolve_base_dir,
    EXIT_SUCCESS,
    EXIT_INDEX_ERROR,
    EXIT_BAD_ARGS,
    EXIT_NO_RESULTS,
)
from utils.logging_utils import get_or_setup_logger

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Script logger (structured, with performance tracking)
logger = get_or_setup_logger(__file__, log_category="index")

# Import index manager
try:
    from management.index_manager import IndexManager
except ImportError:
    print("❌ Error: Could not import index_manager")
    print("Make sure index_manager.py is available (management/index_manager.py).")
    sys.exit(EXIT_INDEX_ERROR)

# Import metadata extractor (optional)
try:
    from management.extract_metadata import MetadataExtractor
except ImportError:
    MetadataExtractor = None

def cmd_get(manager: IndexManager, doc_id: str) -> None:
    """Get entry by ID"""
    entry = manager.get_entry(doc_id)
    if entry:
        print(f"📋 Entry: {doc_id}")
        for key, value in entry.items():
            # Format lists and complex types nicely
            if isinstance(value, list):
                if value:
                    print(f"   {key}: {', '.join(str(v) for v in value)}")
                else:
                    print(f"   {key}: []")
            elif isinstance(value, dict):
                print(f"   {key}:")
                for k, v in value.items():
                    print(f"     {k}: {v}")
            else:
                print(f"   {key}: {value}")
    else:
        print(f"❌ Entry not found: {doc_id}")
        sys.exit(EXIT_NO_RESULTS)

def cmd_update(manager: IndexManager, doc_id: str, metadata_json: str) -> None:
    """Update entry"""
    try:
        metadata = json.loads(metadata_json)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(EXIT_BAD_ARGS)
    
    if manager.update_entry(doc_id, metadata):
        print(f"✅ Updated entry: {doc_id}")
    else:
        print(f"❌ Failed to update entry: {doc_id}")
        sys.exit(EXIT_INDEX_ERROR)

def cmd_remove(manager: IndexManager, doc_id: str) -> None:
    """Remove entry"""
    if manager.remove_entry(doc_id):
        print(f"✅ Removed entry: {doc_id}")
    else:
        print(f"❌ Entry not found or failed to remove: {doc_id}")
        sys.exit(1)

def cmd_list(manager: IndexManager, filters: dict[str, str], limit: int | None = None) -> None:
    """List entries with optional filtering"""
    if filters:
        entries = manager.search_entries(**filters)
        print(f"📋 Found {len(entries)} matching entries:")
    else:
        entries = list(manager.list_entries())
        print(f"📋 All entries ({len(entries)}):")
    
    try:
        count = 0
        for doc_id, metadata in entries:
            if limit is not None and count >= limit:
                break
            print(f"\n{doc_id}:")
            for key, value in metadata.items():
                print(f"  {key}: {value}")
            count += 1
    except BrokenPipeError:
        # Piped output closed early (e.g., head command) - this is normal
        # Close stderr to prevent cascading errors, then exit gracefully
        try:
            sys.stderr.close()
        except Exception:
            pass
        sys.exit(0)

def cmd_count(manager: IndexManager) -> None:
    """Get total entry count"""
    count = manager.get_entry_count()
    print(f"📊 Total entries: {count}")

def cmd_verify(manager: IndexManager, base_dir: Path) -> None:
    """Verify index integrity"""
    print("🔍 Verifying index integrity...")
    
    if not manager.index_path.exists():
        print(f"❌ Index file does not exist: {manager.index_path}")
        sys.exit(1)
    
    issues = []
    entry_count = 0
    
    # Check each entry
    for doc_id, metadata in manager.list_entries():
        entry_count += 1
        
        if not isinstance(metadata, dict):
            issues.append(f"Invalid metadata for {doc_id}: not a dict")
            continue
        
        # Check required fields
        required = ['path', 'url', 'hash', 'last_fetched']
        missing = [f for f in required if f not in metadata]
        if missing:
            issues.append(f"Missing fields {missing} for {doc_id}")
            continue
        
        # Check file exists
        file_path = base_dir / metadata['path']
        if not file_path.exists():
            issues.append(f"File not found: {metadata['path']} (doc_id: {doc_id})")
    
    print(f"\n📋 Index Verification: {manager.index_path}")
    print(f"   Entries: {entry_count}")
    
    if issues:
        print(f"   ❌ Issues found: {len(issues)}")
        for issue in issues[:20]:  # Show first 20
            print(f"      - {issue}")
        if len(issues) > 20:
            print(f"      ... and {len(issues) - 20} more")
        sys.exit(1)
    else:
        print(f"   ✅ All checks passed")
        print(f"   ✅ All files exist")

def cmd_add_keywords(manager: IndexManager, doc_id: str, keywords: list[str]) -> None:
    """Add/update keywords for an entry"""
    entry = manager.get_entry(doc_id)
    if not entry:
        print(f"❌ Entry not found: {doc_id}")
        sys.exit(1)
    
    # Merge with existing keywords
    existing_keywords = normalize_keywords(entry.get('keywords', []))
    new_keywords = normalize_keywords(keywords)

    # Add new keywords (lowercase, unique)
    all_keywords = set(existing_keywords)
    all_keywords.update(new_keywords)
    
    entry['keywords'] = sorted(all_keywords)
    
    if manager.update_entry(doc_id, entry):
        print(f"✅ Updated keywords for {doc_id}: {', '.join(sorted(all_keywords))}")
    else:
        print(f"❌ Failed to update keywords for {doc_id}")
        sys.exit(1)

def cmd_add_tags(manager: IndexManager, doc_id: str, tags: list[str]) -> None:
    """Add/update tags for an entry"""
    entry = manager.get_entry(doc_id)
    if not entry:
        print(f"❌ Entry not found: {doc_id}")
        sys.exit(1)
    
    # Merge with existing tags
    existing_tags = normalize_tags(entry.get('tags', []))
    new_tags = normalize_tags(tags)

    # Add new tags (lowercase, unique)
    all_tags = set(existing_tags)
    all_tags.update(new_tags)
    
    entry['tags'] = sorted(all_tags)
    
    if manager.update_entry(doc_id, entry):
        print(f"✅ Updated tags for {doc_id}: {', '.join(sorted(all_tags))}")
    else:
        print(f"❌ Failed to update tags for {doc_id}")
        sys.exit(1)

def cmd_set_alias(manager: IndexManager, doc_id: str, alias: str) -> None:
    """Add alias for an entry (for renamed docs)"""
    entry = manager.get_entry(doc_id)
    if not entry:
        print(f"❌ Entry not found: {doc_id}")
        sys.exit(1)
    
    # Add alias to existing aliases
    existing_aliases = entry.get('aliases', [])
    if isinstance(existing_aliases, str):
        existing_aliases = [existing_aliases]
    elif not isinstance(existing_aliases, list):
        existing_aliases = []
    
    if alias not in existing_aliases:
        existing_aliases.append(alias)
        entry['aliases'] = existing_aliases
        
        if manager.update_entry(doc_id, entry):
            print(f"✅ Added alias '{alias}' for {doc_id}")
        else:
            print(f"❌ Failed to add alias for {doc_id}")
            sys.exit(1)
    else:
        print(f"ℹ️  Alias '{alias}' already exists for {doc_id}")

def cmd_update_metadata(manager: IndexManager, doc_id: str, field: str, value: str) -> None:
    """Update a specific metadata field"""
    entry = manager.get_entry(doc_id)
    if not entry:
        print(f"❌ Entry not found: {doc_id}")
        sys.exit(1)
    
    # Try to parse value as JSON (for lists, etc.)
    try:
        parsed_value = json.loads(value)
    except json.JSONDecodeError:
        parsed_value = value
    
    entry[field] = parsed_value
    
    if manager.update_entry(doc_id, entry):
        print(f"✅ Updated {field} for {doc_id}: {parsed_value}")
    else:
        print(f"❌ Failed to update {field} for {doc_id}")
        sys.exit(1)

def _auto_install_optional_dependencies(verbose: bool = False) -> None:
    """Auto-install optional dependencies if missing (uses pre-built wheels when possible)

    This function is intentionally best-effort only: failures here should never
    prevent keyword extraction from proceeding with fallback methods.
    """
    import sys  # Ensure sys is available in this scope
    try:
        from setup.setup_dependencies import (
            check_import,
            check_spacy_model,
            run_pip_install,
            install_spacy_with_model,
            detect_python_for_spacy,
            get_python_environment_info,
        )

        # Capture environment snapshot for diagnostics
        env_info = get_python_environment_info()

        # Check availability by trying to import directly (current interpreter)
        yake_available = check_import('yake')
        spacy_available = check_import('spacy')
        spacy_model_available = False
        if spacy_available:
            try:
                spacy_model_available = check_spacy_model()
            except Exception:
                spacy_model_available = False

        missing_optional = []
        if not yake_available:
            missing_optional.append('yake')

        # Check if spaCy or model is missing
        spacy_missing = not spacy_available
        spacy_model_missing = not spacy_model_available if spacy_available else False

        # Check Python version for spaCy compatibility
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        python313_available = detect_python_for_spacy()
        needs_python313 = python_version >= '3.14' or python_version < '3.7'

        # Always show what we're checking (diagnostic)
        if verbose:
            print("  🔍 Keyword extraction environment:")
            print(f"     Python: {env_info['python_version']} at {env_info['python_executable']}")
            if env_info.get('pip_location'):
                match = "matches" if env_info.get('pip_python_match') else "may not match"
                print(f"     pip:    {env_info['pip_location']} ({match} this interpreter)")
            print(f"  🔍 Dependency check: YAKE={yake_available}, spaCy={spacy_available}, spaCy model={spacy_model_available}")
            print(f"  🔍 Missing: YAKE={not yake_available}, spaCy={spacy_missing}, spaCy model={spacy_model_missing}")
            print(f"  🔍 Python version: {python_version}, Python 3.13 available: {python313_available is not None}")
            if needs_python313:
                print("  ℹ️  spaCy officially supports Python 3.7-3.13 - will prefer Python 3.13 if available")

        if missing_optional or spacy_missing or spacy_model_missing:
            print("📦 Auto-installing optional dependencies for better keyword extraction...")
            if needs_python313 and python313_available:
                print("   (Will use Python 3.13 for spaCy - pre-built wheels available, no compiler needed)")
            else:
                print("   (Using pre-built wheels when available - no compiler needed)")
            print("=" * 60)
            print()

            # Install YAKE if missing (use default Python)
            if missing_optional:
                print("  📦 Installing YAKE...")
                success = run_pip_install(missing_optional, install_individually=True)
                if success:
                    print("  ✅ YAKE installed successfully")
                else:
                    print("  ⚠️  YAKE installation failed (will use fallback)")
                print()

            # Install spaCy with model using unified helper (prefers 3.13 when appropriate)
            if spacy_missing or spacy_model_missing:
                print("  📦 Installing spaCy and model...")
                if needs_python313 and python313_available and verbose:
                    print(f"     Current Python {python_version} detected - preferring Python 3.13 for spaCy")
                    print("     (Pre-built wheels available, no compilation needed)")
                try:
                    success, message = install_spacy_with_model(
                        prefer_wheel=True,
                        model_name='en_core_web_sm',
                        verbose=verbose,
                        auto_install_build_tools=True,
                    )
                    if success:
                        print(f"  ✅ {message}")
                    else:
                        print(f"  ⚠️  {message}")
                        if not verbose:
                            print("     (Run with --verbose to see detailed installation progress)")
                        print("     Scripts will continue with fallback stop words")
                    print()
                except Exception as e:
                    print(f"  ❌ spaCy installation error: {e}")
                    if verbose:
                        import traceback
                        traceback.print_exc()
                    print("     Scripts will continue with fallback stop words")
                    print()

            # Force reload of extract_metadata to pick up newly installed packages
            # Remove from cache to force fresh import
            if 'extract_metadata' in sys.modules:
                del sys.modules['extract_metadata']
            # Re-import to get fresh constants
            import extract_metadata  # noqa: F401
            print("=" * 60)
            print()
    except Exception as e:
        # If auto-install fails, show error but continue with fallbacks
        print(f"⚠️  Auto-install failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        print("   Scripts will continue with fallback methods")
        print()

def cmd_extract_keywords(manager: IndexManager, base_dir: Path, skip_existing: bool = True, verbose: bool = False, auto_install: bool = True, json_output: bool = False) -> None:
    """
    Extract keywords from all documents (uses batch updates for efficiency)
    
    Args:
        manager: IndexManager instance
        base_dir: Base directory for references
        skip_existing: Skip files that already have all metadata fields (default: True)
        verbose: Print detailed progress (default: False)
        auto_install: Auto-install optional dependencies if missing (default: True)
    """
    if not MetadataExtractor:
        print("❌ Error: extract_metadata module not available")
        sys.exit(1)
    
    # Auto-install optional dependencies if missing (before checking status)
    if auto_install:
        if verbose:
            print("🔧 Auto-install enabled - checking for missing dependencies...")
        _auto_install_optional_dependencies(verbose=verbose)
    
    # Check and report dependency status (after potential auto-install)
    # Import or re-import to get current constants
    if 'extract_metadata' in sys.modules:
        from importlib import reload
        import extract_metadata
        reload(extract_metadata)
    else:
        import extract_metadata
    from management.extract_metadata import YAKE_AVAILABLE, SPACY_AVAILABLE

    # Attempt to get environment info and effective spaCy status for a clear summary
    env_info = None
    effective_spacy = None
    try:
        from setup.setup_dependencies import get_python_environment_info, get_effective_spacy_status  # type: ignore
        env_info = get_python_environment_info()
        effective_spacy = get_effective_spacy_status()
    except Exception:
        env_info = None
        effective_spacy = None

    print("🔍 Extracting metadata from all documents...")
    print()
    print("📦 Dependency Status:")
    print("=" * 60)

    print("   Required Dependencies: ✅ All installed")
    print()
    print("   Optional Dependencies:")
    print(f"      YAKE: {'✅ Available' if YAKE_AVAILABLE else '❌ Missing'}")
    if YAKE_AVAILABLE:
        print("         → Enhanced keyword extraction enabled")
    else:
        print("         → Using heading/content analysis (still effective)")

    # For spaCy, distinguish clearly between current-interpreter importability
    # and overall usage (which may come via a separate Python 3.13 process).
    if effective_spacy:
        current_diag = effective_spacy.get("current") or {}
        current_importable = bool(current_diag.get("spacy_importable"))
        current_model = bool(current_diag.get("model_loadable"))
        effective_available = bool(effective_spacy.get("effective_available"))
        effective_model_available = bool(effective_spacy.get("effective_model_available"))
        effective_python = effective_spacy.get("effective_python")

        if current_importable:
            print("      spaCy (current interpreter): ✅ Importable")
            if current_model:
                print("      spaCy Model (current): ✅ Available")
            else:
                print("      spaCy Model (current): ⚠️  Not loadable")
        else:
            print("      spaCy (current interpreter): ❌ Not importable")

        if effective_available:
            if effective_python and effective_python != sys.executable:
                print(f"      spaCy (effective): ✅ Available via {effective_python}")
            else:
                print("      spaCy (effective): ✅ Available in current interpreter")
        else:
            print("      spaCy (effective): ❌ Not available in any supported interpreter")

        if effective_model_available:
            loc = effective_spacy.get("model_location")
            if loc:
                print(f"      spaCy Model (effective): ✅ Available at {loc}")
        else:
            print("      spaCy Model (effective): ⚠️  Not loadable in any interpreter")
    else:
        print("      spaCy: ⚠️  Status unknown (could not determine effective spaCy availability)")

    # Show interpreter details for context
    if env_info is not None:
        print()
        print("   Python Environment (for this extraction run):")
        print(f"      Version:    {env_info['python_version']}")
        print(f"      Executable: {env_info['python_executable']}")
        if env_info.get('pip_location'):
            match = "matches" if env_info.get('pip_python_match') else "may not match"
            print(f"      pip:        {env_info['pip_location']} ({match} this interpreter)")

    print("=" * 60)
    print()
    if skip_existing:
        print("   (Skipping files that already have metadata)")
    print("   (Using batch updates for efficiency)")
    
    # Count total entries first for progress
    total_count = manager.get_entry_count()
    processed = 0
    skipped = 0
    updates = {}  # Batch all updates
    error_count = 0
    
    # Progress tracking for time estimates
    import time
    start_time = time.time()
    progress_interval = 50  # Show progress every N files

    def _format_eta(processed_count: int) -> str:
        """Return a human-friendly ETA string based on current progress."""
        elapsed = time.time() - start_time
        rate = processed_count / elapsed if elapsed > 0 else 0
        remaining = total_count - processed_count
        eta_seconds = remaining / rate if rate > 0 else 0
        eta_minutes = eta_seconds / 60
        if eta_minutes > 1:
            return f"{eta_minutes:.1f} minutes"
        if eta_seconds > 10:
            return f"{eta_seconds:.0f} seconds"
        return "less than 10 seconds"
    
    # Statistics tracking
    stats_aggregate = {
        'yake_used_count': 0,
        'spacy_used_count': 0,
        'total_yake_keywords': 0,
        'total_frontmatter_keywords': 0,
        'total_heading_keywords': 0,
        'total_title_desc_keywords': 0,
        'total_body_keywords': 0,
        'total_filename_keywords': 0,
    }
    
    for doc_id, metadata in manager.list_entries():
        processed += 1
        path_str = metadata.get('path')
        if not path_str:
            continue
        
        file_path = base_dir / path_str
        if not file_path.exists():
            if verbose:
                print(f"  [{processed}/{total_count}] ⚠️  File not found: {doc_id}")
            continue
        
        # Check if we should skip (already has all metadata)
        if skip_existing:
            has_all_metadata = all(key in metadata for key in ['title', 'description', 'keywords', 'tags', 'category', 'domain'])
            if has_all_metadata:
                skipped += 1
                # Show progress periodically (every progress_interval files or at milestones)
                if not verbose and (processed % progress_interval == 0 or processed == total_count):
                    eta_str = _format_eta(processed)
                    print(
                        f"  [{processed}/{total_count}] Progress: {skipped} skipped, {len(updates)} queued for update... "
                        f"({processed*100//total_count}% complete, ~{eta_str} remaining)"
                    )
                continue
        
        try:
            url = metadata.get('url', '')
            extractor = MetadataExtractor(file_path, url)
            extracted = extractor.extract_all(track_stats=True)
            
            # Collect statistics
            if '_stats' in extracted:
                stats = extracted.pop('_stats')  # Remove stats from metadata
                if stats.get('yake_used'):
                    stats_aggregate['yake_used_count'] += 1
                    stats_aggregate['total_yake_keywords'] += stats.get('yake_keywords_count', 0)
                if stats.get('spacy_used'):
                    stats_aggregate['spacy_used_count'] += 1
                stats_aggregate['total_frontmatter_keywords'] += stats.get('frontmatter_keywords_count', 0)
                stats_aggregate['total_heading_keywords'] += stats.get('heading_keywords_count', 0)
                stats_aggregate['total_title_desc_keywords'] += stats.get('title_desc_keywords_count', 0)
                stats_aggregate['total_body_keywords'] += stats.get('body_content_keywords_count', 0)
                stats_aggregate['total_filename_keywords'] += stats.get('filename_keywords_count', 0)
            
            # Collect updates (only new fields, or if existing field is empty/not useful)
            # When skip_existing=False (--no-skip-existing), force update all fields
            update_dict = {}
            for key in ['title', 'description', 'keywords', 'tags', 'category', 'domain', 'subsections']:
                if key in extracted:
                    # Update if field doesn't exist, is empty, or for keywords if it's not useful (empty or too short)
                    existing_value = metadata.get(key)
                    should_update = False

                    # When --no-skip-existing is used, force update keywords and tags
                    # FIX 2025-11-25: Previously ignored skip_existing for per-field decisions
                    if not skip_existing and key in ['keywords', 'tags']:
                        should_update = True
                    elif existing_value is None:
                        should_update = True
                    elif key == 'keywords':
                        # Update keywords if empty, empty string, or has fewer than 3 meaningful keywords
                        if not existing_value or (isinstance(existing_value, list) and len([k for k in existing_value if k and len(str(k)) >= 4]) < 3):
                            should_update = True
                    elif key == 'subsections':
                        # Always update subsections (new feature, always extract)
                        should_update = True
                    elif key == 'tags':
                        # Always re-extract tags to pick up config changes (threshold, term list updates)
                        should_update = True
                    elif not existing_value:  # Empty string or empty list
                        should_update = True

                    if should_update:
                        update_dict[key] = extracted[key]
            
            if update_dict:
                # Only pass the new fields to update, not the entire metadata dict
                # This prevents overwriting critical fields like 'path', 'url', 'hash'
                updates[doc_id] = update_dict
                
                if verbose:
                    print(f"  [{processed}/{total_count}] ✅ Queued {doc_id}")
                # Show progress periodically (every progress_interval files or at milestones)
                elif processed % progress_interval == 0 or processed == total_count:
                    eta_str = _format_eta(processed)
                    print(
                        f"  [{processed}/{total_count}] Progress: {skipped} skipped, {len(updates)} queued for update... "
                        f"({processed*100//total_count}% complete, ~{eta_str} remaining)"
                    )
            else:
                skipped += 1
                # Show progress periodically
                if not verbose and (processed % progress_interval == 0 or processed == total_count):
                    eta_str = _format_eta(processed)
                    print(
                        f"  [{processed}/{total_count}] Progress: {skipped} skipped, {len(updates)} queued for update... "
                        f"({processed*100//total_count}% complete, ~{eta_str} remaining)"
                    )
        except Exception as e:
            error_count += 1
            if verbose:
                print(f"  [{processed}/{total_count}] ⚠️  Error processing {doc_id}: {e}")
    
    # Batch update all entries at once (much faster!)
    if updates:
        print(f"\n💾 Applying {len(updates)} updates in batch...")
        if manager.batch_update_entries(updates):
            updated_count = len(updates)
            print(f"   ✅ Successfully updated {updated_count} entries")
        else:
            error_count += len(updates)
            print(f"   ❌ Failed to apply batch update")
            updated_count = 0
    else:
        updated_count = 0
    
    print(f"\n📊 Extraction complete:")
    print(f"   Processed: {processed}/{total_count}")
    print(f"   Updated: {updated_count}")
    print(f"   Skipped: {skipped}")
    print(f"   Errors: {error_count}")
    print()
    print("📈 Extraction Statistics:")
    if updated_count > 0:
        yake_used = stats_aggregate['yake_used_count']
        spacy_used = stats_aggregate['spacy_used_count']
        # Percentages are clamped at 100% to avoid confusing values when the
        # aggregate counts exceed the number of updated entries (e.g., stats
        # accumulated across multiple passes).
        yake_pct = min(100, yake_used * 100 // max(updated_count, 1))
        spacy_pct = min(100, spacy_used * 100 // max(updated_count, 1))
        print(f"   YAKE used: {yake_used}/{updated_count} docs ({yake_pct}%)")
        # This reflects actual spaCy-based stop-word usage (either via current
        # interpreter or via a Python 3.13 helper), not just importability.
        print(f"   spaCy-based stop words used: {spacy_used}/{updated_count} docs ({spacy_pct}%)")
        if stats_aggregate['yake_used_count'] > 0:
            avg_yake = stats_aggregate['total_yake_keywords'] // max(stats_aggregate['yake_used_count'], 1)
            print(f"   Average YAKE keywords per doc: {avg_yake}")
        print()
        print("   Keyword Sources (total extracted):")
        print(f"      Frontmatter: {stats_aggregate['total_frontmatter_keywords']}")
        print(f"      YAKE: {stats_aggregate['total_yake_keywords']}")
        print(f"      Headings: {stats_aggregate['total_heading_keywords']}")
        print(f"      Title/Description: {stats_aggregate['total_title_desc_keywords']}")
        print(f"      Body content: {stats_aggregate['total_body_keywords']}")
        print(f"      Filename: {stats_aggregate['total_filename_keywords']}")

        # Only warn about missing spaCy if we *didn't* manage to use spaCy-based
        # stop words at all. If spacy_used > 0, spaCy is in play (typically via
        # Python 3.13) even if the current interpreter can't import it.
        needs_optional_summary = (not YAKE_AVAILABLE) or (spacy_used == 0)
        if needs_optional_summary:
            print()
            print("   ⚠️  Optional Dependencies Status:")
            print("   " + "=" * 50)

            if not YAKE_AVAILABLE:
                print("   ❌ YAKE - Missing (affects keyword extraction quality)")
                print("      Install: pip install yake")
            else:
                print("   ✅ YAKE - Available")

            if spacy_used == 0:
                if not SPACY_AVAILABLE:
                    print("   ❌ spaCy - Missing (affects stop word filtering)")
                    print("      Impact: Using static stop-word list instead of spaCy's comprehensive list")
                else:
                    print("   ⚠️  spaCy importable but not used for stop words")
                    print("      Check spaCy model installation and configuration.")
                print("      This is optional - scripts work fine with fallbacks")
                print()
                print("      To install or repair spaCy + model:")
                try:
                    from setup_dependencies import install_spacy_with_model, detect_package_manager
                    _ = install_spacy_with_model  # type: ignore[unused-ignore]
                    _ = detect_package_manager()  # Called to verify import works
                    print("      Auto-install (recommended): python setup_dependencies.py --install-all")
                    print("      Or manual: python -c \"from setup_dependencies import install_spacy_with_model; install_spacy_with_model(verbose=True)\"")
                except Exception:
                    print("      Run: python setup_dependencies.py --install-all")
                    print("      Or: pip install spacy && python -m spacy download en_core_web_sm")

            print()
            print("   Quick install all optional deps:")
            print("      python setup_dependencies.py --install-all")
            print()
            print("   Note: Scripts work with fallbacks, but enhanced features require these dependencies")

def cmd_validate_metadata(manager: IndexManager, base_dir: Path, json_output: bool = False) -> None:
    """
    Validate metadata quality after extraction
    
    Checks for:
    - Missing required fields (title, description, keywords, tags, category, domain)
    - Empty or minimal keywords
    - Coverage statistics
    
    Args:
        manager: IndexManager instance
        base_dir: Base directory for references
        json_output: Output results as JSON
    """
    total_count = manager.get_entry_count()
    
    # Statistics
    stats = {
        'total': total_count,
        'has_title': 0,
        'has_description': 0,
        'has_keywords': 0,
        'has_tags': 0,
        'has_category': 0,
        'has_domain': 0,
        'has_all_metadata': 0,
        'empty_keywords': 0,
        'minimal_keywords': 0,  # Less than 3 keywords
        'missing_files': 0,
        'coverage': {}
    }
    
    for doc_id, metadata in manager.list_entries():
        # Check required fields
        if metadata.get('title'):
            stats['has_title'] += 1
        if metadata.get('description'):
            stats['has_description'] += 1
        if metadata.get('keywords'):
            stats['has_keywords'] += 1
            keywords = metadata.get('keywords', [])
            if not keywords:
                stats['empty_keywords'] += 1
            elif len([k for k in keywords if k and len(str(k)) >= 4]) < 3:
                stats['minimal_keywords'] += 1
        if metadata.get('tags'):
            stats['has_tags'] += 1
        if metadata.get('category'):
            stats['has_category'] += 1
        if metadata.get('domain'):
            stats['has_domain'] += 1
        
        # Check if has all metadata
        has_all = all(key in metadata and metadata[key] 
                     for key in ['title', 'description', 'keywords', 'tags', 'category', 'domain'])
        if has_all:
            stats['has_all_metadata'] += 1
        
        # Check if file exists
        path_str = metadata.get('path')
        if path_str:
            file_path = base_dir / path_str
            if not file_path.exists():
                stats['missing_files'] += 1
    
    # Calculate coverage percentages
    if total_count > 0:
        stats['coverage'] = {
            'title': (stats['has_title'] * 100) // total_count,
            'description': (stats['has_description'] * 100) // total_count,
            'keywords': (stats['has_keywords'] * 100) // total_count,
            'tags': (stats['has_tags'] * 100) // total_count,
            'category': (stats['has_category'] * 100) // total_count,
            'domain': (stats['has_domain'] * 100) // total_count,
            'all_metadata': (stats['has_all_metadata'] * 100) // total_count,
        }
    
    if json_output:
        import json
        print(json.dumps(stats, indent=2))
        # For JSON mode, treat all issues as informational so callers can decide.
        return
    
    # Print formatted output
    print("📊 Metadata Validation Report:")
    print("=" * 60)
    print(f"Total entries: {stats['total']}")
    print()
    print("Field Coverage:")
    print(f"  Title:       {stats['has_title']}/{stats['total']} ({stats['coverage']['title']}%)")
    print(f"  Description: {stats['has_description']}/{stats['total']} ({stats['coverage']['description']}%)")
    print(f"  Keywords:    {stats['has_keywords']}/{stats['total']} ({stats['coverage']['keywords']}%)")
    print(f"  Tags:        {stats['has_tags']}/{stats['total']} ({stats['coverage']['tags']}%)")
    print(f"  Category:    {stats['has_category']}/{stats['total']} ({stats['coverage']['category']}%)")
    print(f"  Domain:      {stats['has_domain']}/{stats['total']} ({stats['coverage']['domain']}%)")
    print()
    print(f"Complete Metadata: {stats['has_all_metadata']}/{stats['total']} ({stats['coverage']['all_metadata']}%)")
    print()
    
    # Quality issues
    issues = []
    if stats['empty_keywords'] > 0:
        issues.append(f"Empty keywords: {stats['empty_keywords']}")
    if stats['minimal_keywords'] > 0:
        issues.append(f"Minimal keywords (<3): {stats['minimal_keywords']}")
    if stats['missing_files'] > 0:
        issues.append(f"Missing files: {stats['missing_files']}")
    
    if issues:
        print("⚠️  Quality Issues:")
        for issue in issues:
            print(f"  - {issue}")
        print()
        print("💡 To fix non-critical issues (e.g., minimal keywords):")
        print("   python manage_index.py extract-keywords")

        # Treat missing files as a critical issue and signal via exit code so
        # orchestrators (e.g., refresh_index.py) can react appropriately.
        if stats['missing_files'] > 0:
            print()
            print("❌ Critical issue: One or more index entries reference missing files.")
            print("   Review index.yaml and underlying files before proceeding.")
            sys.exit(1)
    else:
        print("✅ No quality issues detected")
        print()

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Manage index.yaml',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Get entry
  python manage_index.py get code-claude-com-docs-en-overview
  
  # Update entry
  python manage_index.py update doc-id '{"path": "test.md", "url": "https://example.com"}'
  
  # Remove entry
  python manage_index.py remove doc-id
  
  # List all entries
  python manage_index.py list
  
  # List entries with filter
  python manage_index.py list --filter source_type=sitemap
  
  # Count entries
  python manage_index.py count
  
  # Verify index
  python manage_index.py verify
        """
    )
    
    add_common_index_args(parser, include_json=False)
    
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Get command
    get_parser = subparsers.add_parser('get', help='Get entry by ID')
    get_parser.add_argument('doc_id', help='Document ID')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update entry')
    update_parser.add_argument('doc_id', help='Document ID')
    update_parser.add_argument('metadata', help='Metadata as JSON string')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove entry')
    remove_parser.add_argument('doc_id', help='Document ID')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List entries')
    list_parser.add_argument('--filter', action='append', metavar='KEY=VALUE',
                             help='Filter by field (can be used multiple times)')
    list_parser.add_argument('--limit', type=int, metavar='N',
                             help='Limit output to first N entries (alternative to piping)')
    
    # Count command
    subparsers.add_parser('count', help='Get total entry count')
    
    # Verify command
    subparsers.add_parser('verify', help='Verify index integrity')
    
    # Validate metadata command
    validate_parser = subparsers.add_parser('validate-metadata', help='Validate metadata quality after extraction')
    validate_parser.add_argument('--json', action='store_true',
                                help='Output results as JSON (for machine-readable output)')
    
    # Add keywords command
    add_keywords_parser = subparsers.add_parser('add-keywords', help='Add/update keywords for an entry')
    add_keywords_parser.add_argument('doc_id', help='Document ID')
    add_keywords_parser.add_argument('keywords', nargs='+', help='Keywords to add')
    
    # Add tags command
    add_tags_parser = subparsers.add_parser('add-tags', help='Add/update tags for an entry')
    add_tags_parser.add_argument('doc_id', help='Document ID')
    add_tags_parser.add_argument('tags', nargs='+', help='Tags to add')
    
    # Set alias command
    set_alias_parser = subparsers.add_parser('set-alias', help='Add alias for an entry')
    set_alias_parser.add_argument('doc_id', help='Document ID')
    set_alias_parser.add_argument('alias', help='Alias to add')
    
    # Update metadata command
    update_metadata_parser = subparsers.add_parser('update-metadata', help='Update a specific metadata field')
    update_metadata_parser.add_argument('doc_id', help='Document ID')
    update_metadata_parser.add_argument('field', help='Field name to update')
    update_metadata_parser.add_argument('value', help='Value to set (JSON for lists/objects)')
    
    # Extract keywords command
    extract_parser = subparsers.add_parser('extract-keywords', help='Extract keywords from all documents')
    extract_parser.add_argument('--no-skip-existing', action='store_true', 
                               help='Re-extract metadata even if already present (default: skip existing)')
    extract_parser.add_argument('--verbose', '-v', action='store_true',
                               help='Print detailed progress for each file')
    extract_parser.add_argument('--no-auto-install', action='store_true',
                               help='Skip auto-installation of optional dependencies (default: auto-install if missing)')
    extract_parser.add_argument('--json', action='store_true',
                               help='Output results as JSON (for machine-readable output)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Log script start
    logger.start({
        'command': args.command,
        'base_dir': args.base_dir,
        'args': {k: v for k, v in vars(args).items() if k not in ['command', 'base_dir'] and v is not None}
    })
    
    exit_code = EXIT_SUCCESS
    try:
        # Resolve base directory
        base_dir = resolve_base_dir(args.base_dir)
        
        # Initialize manager
        manager = IndexManager(base_dir)
        
        # Execute command
        if args.command == 'get':
            cmd_get(manager, args.doc_id)
        elif args.command == 'update':
            cmd_update(manager, args.doc_id, args.metadata)
        elif args.command == 'remove':
            cmd_remove(manager, args.doc_id)
        elif args.command == 'list':
            filters = {}
            if args.filter:
                for f in args.filter:
                    if '=' in f:
                        key, value = f.split('=', 1)
                        filters[key] = value
            limit = getattr(args, 'limit', None)
            cmd_list(manager, filters, limit=limit)
        elif args.command == 'count':
            cmd_count(manager)
        elif args.command == 'verify':
            cmd_verify(manager, base_dir)
        elif args.command == 'validate-metadata':
            json_output = getattr(args, 'json', False)
            cmd_validate_metadata(manager, base_dir, json_output=json_output)
        elif args.command == 'add-keywords':
            cmd_add_keywords(manager, args.doc_id, args.keywords)
        elif args.command == 'add-tags':
            cmd_add_tags(manager, args.doc_id, args.tags)
        elif args.command == 'set-alias':
            cmd_set_alias(manager, args.doc_id, args.alias)
        elif args.command == 'update-metadata':
            cmd_update_metadata(manager, args.doc_id, args.field, args.value)
        elif args.command == 'extract-keywords':
            skip_existing = not getattr(args, 'no_skip_existing', False)
            verbose = getattr(args, 'verbose', False)
            auto_install = not getattr(args, 'no_auto_install', False)
            json_output = getattr(args, 'json', False)
            with logger.time_operation('extract_keywords'):
                cmd_extract_keywords(manager, base_dir, skip_existing=skip_existing, verbose=verbose, auto_install=auto_install, json_output=json_output)
        else:
            parser.print_help()
            exit_code = 1
        
        logger.end(exit_code=exit_code)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in manage_index", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

