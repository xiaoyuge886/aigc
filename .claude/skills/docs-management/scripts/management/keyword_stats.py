#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
keyword_stats.py - Simple keyword frequency report from index.yaml.

Helps identify overly-generic or noisy keywords so filtering rules can be tuned.

Usage:
    python keyword_stats.py
    python keyword_stats.py --top 50
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from collections import Counter
from typing import Any

from utils.script_utils import configure_utf8_output, EXIT_SUCCESS

# Configure UTF-8 output for Windows consoles
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="index")

try:
    from management.index_manager import IndexManager
except ImportError as e:  # pragma: no cover
    print(f"❌ Error importing index_manager: {e}")
    raise SystemExit(1)

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show most common keywords from index.yaml",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python keyword_stats.py --top 50
""",
    )
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    parser.add_argument(
        "--top",
        type=int,
        default=25,
        help="Number of top keywords to display (default: 25)",
    )
    parser.add_argument(
        "--top-docs",
        type=int,
        help="(Alias for --top) Number of top keywords to display",
    )

    args = parser.parse_args()

    # Support both --top and --top-docs, treating them identically so that
    # older prompts using --top-docs continue to work without errors.
    effective_top = args.top_docs if args.top_docs is not None else args.top

    logger.start({"base_dir": args.base_dir, "top": effective_top})
    exit_code = EXIT_SUCCESS

    try:
        base_dir = resolve_base_dir_from_args(args)
        manager = IndexManager(base_dir)
        index: dict[str, dict[str, Any]] = manager.load_all() or {}

        counter: Counter[str] = Counter()
        for metadata in index.values():
            keywords = metadata.get("keywords") or []
            if isinstance(keywords, str):
                keywords = [k.strip() for k in keywords.split(",") if k.strip()]
            if isinstance(keywords, list):
                for kw in keywords:
                    if isinstance(kw, str) and kw.strip():
                        counter[kw.strip().lower()] += 1

        total_entries = len(index)
        unique_keywords = len(counter)

        print("\n📊 Keyword Frequency Summary")
        print("=" * 60)
        print(f"Base directory:      {base_dir}")
        print(f"Total index entries: {total_entries}")
        print(f"Unique keywords:     {unique_keywords}")
        print()
        print(f"Top {min(effective_top, unique_keywords)} keywords:")

        for kw, count in counter.most_common(effective_top):
            print(f"  {kw:30s} {count:4d}")

        logger.end(
            exit_code=exit_code,
            summary={
                "total_entries": total_entries,
                "unique_keywords": unique_keywords,
                "top_reported": min(effective_top, unique_keywords),
            },
        )
        return exit_code

    except SystemExit:
        raise
    except Exception as e:  # pragma: no cover
        logger.log_error("Fatal error in keyword_stats", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        return exit_code

if __name__ == "__main__":
    raise SystemExit(main())
