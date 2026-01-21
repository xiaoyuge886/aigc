#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_index_vs_docs.py - Compare index.yaml metadata with source markdown files.

Checks that title, description, keywords, tags, category, and domain in index.yaml
match what would be extracted from the underlying documents today.

Usage:
    python validate_index_vs_docs.py
    python validate_index_vs_docs.py --summary-only
    python validate_index_vs_docs.py --show-examples 10
    python validate_index_vs_docs.py --fix-low-quality-keywords
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
from typing import Any

from utils.script_utils import configure_utf8_output, EXIT_SUCCESS, EXIT_INDEX_ERROR

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="diagnostics")

try:
    from management.index_manager import IndexManager
    from management.extract_metadata import MetadataExtractor
except ImportError as e:  # pragma: no cover - hard failure
    print(f"❌ Error importing helpers: {e}")
    print("Make sure index_manager.py and extract_metadata.py are available in the same directory.")
    raise SystemExit(EXIT_INDEX_ERROR)

def _is_low_quality_keywords(keywords: Any) -> bool:
    """Heuristic to determine whether an existing keywords list is low quality.

    - Treat None/empty as low quality
    - Treat lists with fewer than 2 \"meaningful\" items (len >= 4) as low quality
    """
    if not keywords:
        return True
    if isinstance(keywords, str):
        keywords = [k.strip() for k in keywords.split(",") if k.strip()]
    if not isinstance(keywords, list):
        return False
    meaningful = [k for k in keywords if isinstance(k, str) and len(k.strip()) >= 4]
    return len(meaningful) < 2

def validate_index_vs_docs(
    base_dir: Path,
    summary_only: bool = False,
    show_examples: int = 0,
    fix_low_quality_keywords: bool = False,
) -> tuple[int, dict[str, Any]]:
    """
    Validate index.yaml metadata against live extraction from documents.

    Returns:
        exit_code, stats dict
    """
    manager = IndexManager(base_dir)
    index = manager.load_all() or {}

    stats: dict[str, Any] = {
        "total_entries": len(index),
        "missing_files": 0,
        "title_mismatches": 0,
        "description_mismatches": 0,
        "domain_mismatches": 0,
        "category_mismatches": 0,
        "missing_keywords": 0,
        "low_quality_keywords": 0,
        "examples": {
            "title_mismatches": [],
            "description_mismatches": [],
            "domain_mismatches": [],
            "category_mismatches": [],
            "missing_keywords": [],
            "low_quality_keywords": [],
        },
        "updated_entries": 0,
    }

    updates: dict[str, dict[str, Any]] = {}

    for doc_id, metadata in index.items():
        path_str = metadata.get("path")
        if not path_str:
            continue

        file_path = base_dir / path_str
        if not file_path.exists():
            stats["missing_files"] += 1
            continue

        url = metadata.get("url", "")
        try:
            extractor = MetadataExtractor(file_path, url)
            extracted = extractor.extract_all(track_stats=False)
        except Exception:
            # If extraction fails for a specific doc, skip but do not abort the whole run
            continue

        # Compare primary fields
        stored_title = metadata.get("title")
        new_title = extracted.get("title")
        if stored_title and new_title and stored_title != new_title:
            stats["title_mismatches"] += 1
            if not summary_only and len(stats["examples"]["title_mismatches"]) < show_examples:
                stats["examples"]["title_mismatches"].append(
                    {"doc_id": doc_id, "stored": stored_title, "new": new_title}
                )

        stored_desc = metadata.get("description")
        new_desc = extracted.get("description")
        if stored_desc and new_desc and stored_desc != new_desc:
            stats["description_mismatches"] += 1
            if not summary_only and len(stats["examples"]["description_mismatches"]) < show_examples:
                stats["examples"]["description_mismatches"].append(
                    {"doc_id": doc_id, "stored": stored_desc, "new": new_desc}
                )

        stored_domain = metadata.get("domain")
        new_domain = extracted.get("domain")
        if stored_domain and new_domain and stored_domain != new_domain:
            stats["domain_mismatches"] += 1
            if not summary_only and len(stats["examples"]["domain_mismatches"]) < show_examples:
                stats["examples"]["domain_mismatches"].append(
                    {"doc_id": doc_id, "stored": stored_domain, "new": new_domain}
                )

        stored_category = metadata.get("category")
        new_category = extracted.get("category")
        if stored_category and new_category and stored_category != new_category:
            stats["category_mismatches"] += 1
            if not summary_only and len(stats["examples"]["category_mismatches"]) < show_examples:
                stats["examples"]["category_mismatches"].append(
                    {"doc_id": doc_id, "stored": stored_category, "new": new_category}
                )

        # Keywords analysis / optional repair
        stored_keywords = metadata.get("keywords")
        new_keywords = extracted.get("keywords", [])

        if not stored_keywords and new_keywords:
            stats["missing_keywords"] += 1
            if not summary_only and len(stats["examples"]["missing_keywords"]) < show_examples:
                stats["examples"]["missing_keywords"].append(
                    {"doc_id": doc_id, "new_keywords": new_keywords}
                )
            if fix_low_quality_keywords:
                updates.setdefault(doc_id, {})["keywords"] = new_keywords

        elif stored_keywords and _is_low_quality_keywords(stored_keywords) and new_keywords:
            stats["low_quality_keywords"] += 1
            if not summary_only and len(stats["examples"]["low_quality_keywords"]) < show_examples:
                stats["examples"]["low_quality_keywords"].append(
                    {
                        "doc_id": doc_id,
                        "stored_keywords": stored_keywords,
                        "new_keywords": new_keywords,
                    }
                )
            if fix_low_quality_keywords:
                updates.setdefault(doc_id, {})["keywords"] = new_keywords

    # Apply updates if requested
    exit_code = EXIT_SUCCESS
    if updates and fix_low_quality_keywords:
        print(f"\n💾 Applying keyword updates for {len(updates)} entries...")
        if manager.batch_update_entries(updates):
            stats["updated_entries"] = len(updates)
            print("   ✅ Updates applied successfully")
        else:
            print("   ❌ Failed to apply batch updates")
            exit_code = EXIT_INDEX_ERROR

    return exit_code, stats

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate index.yaml metadata against source markdown documents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Summary only (no fixes)
  python validate_index_vs_docs.py --summary-only

  # Show up to 5 examples for each mismatch type
  python validate_index_vs_docs.py --show-examples 5

  # Fix missing / low-quality keywords using fresh extraction
  python validate_index_vs_docs.py --fix-low-quality-keywords
""",
    )

    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Only show aggregate stats, no example details",
    )
    parser.add_argument(
        "--show-examples",
        type=int,
        default=0,
        help="Show up to N example mismatches per category",
    )
    parser.add_argument(
        "--fix-low-quality-keywords",
        action="store_true",
        help="Rewrite missing/low-quality keywords using fresh extraction",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output machine-readable JSON summary to stdout",
    )

    args = parser.parse_args()

    # Log script start
    logger.start(
        {
            "base_dir": args.base_dir,
            "summary_only": args.summary_only,
            "show_examples": args.show_examples,
            "fix_low_quality_keywords": args.fix_low_quality_keywords,
        }
    )

    try:
        base_dir = resolve_base_dir_from_args(args)

        with logger.time_operation("validate_index_vs_docs"):
            exit_code, stats = validate_index_vs_docs(
                base_dir=base_dir,
                summary_only=args.summary_only,
                show_examples=args.show_examples,
                fix_low_quality_keywords=args.fix_low_quality_keywords,
            )

        # Human-readable summary
        print("\n📊 Index vs Docs Validation")
        print("=" * 60)
        print(f"Base directory: {base_dir}")
        print(f"Total entries:  {stats['total_entries']}")
        print()
        print(f"Missing files:          {stats['missing_files']}")
        print(f"Title mismatches:       {stats['title_mismatches']}")
        print(f"Description mismatches: {stats['description_mismatches']}")
        print(f"Domain mismatches:      {stats['domain_mismatches']}")
        print(f"Category mismatches:    {stats['category_mismatches']}")
        print(f"Missing keywords:       {stats['missing_keywords']}")
        print(f"Low-quality keywords:   {stats['low_quality_keywords']}")
        if stats.get("updated_entries"):
            print(f"Updated entries:        {stats['updated_entries']}")
        print()

        if not args.summary_only and args.show_examples > 0:
            def _print_examples(label: str, key: str) -> None:
                examples = stats["examples"].get(key) or []
                if not examples:
                    return
                print(f"{label}:")
                for ex in examples:
                    print(f"  - {ex.get('doc_id')}")
                print()

            _print_examples("Title mismatches (sample)", "title_mismatches")
            _print_examples("Description mismatches (sample)", "description_mismatches")
            _print_examples("Domain mismatches (sample)", "domain_mismatches")
            _print_examples("Category mismatches (sample)", "category_mismatches")
            _print_examples("Missing keywords (sample)", "missing_keywords")
            _print_examples("Low-quality keywords (sample)", "low_quality_keywords")

        if args.json:
            print(json.dumps(stats, indent=2))

        logger.end(exit_code=exit_code, summary={"total_entries": stats["total_entries"]})
        return exit_code

    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover - defensive
        logger.log_error("Fatal error in validate_index_vs_docs", error=e)
        logger.end(exit_code=EXIT_INDEX_ERROR)
        return EXIT_INDEX_ERROR

if __name__ == "__main__":
    raise SystemExit(main())
