#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_publication_dates.py - Extract publication dates for Anthropic blog posts

Purpose:
- Derive a content-based `published_at` date for Anthropic engineering, news,
  and research posts, based on the date rendered in the article body.
- Store `published_at` in the index.yaml metadata for those documents so
  downstream workflows can reason about true publication recency, even when
  sitemap <lastmod> is imperfect.

Scope (initial version):
- Targets markdown files under anthropic-com subdirectories:
  - {base_dir}/anthropic-com/engineering/ (default: .claude/skills/docs-management/canonical from config)
  - {base_dir}/anthropic-com/news/
  - {base_dir}/anthropic-com/research/
- Looks for dates in common Anthropic formats, e.g.:
  - "Mar 27, 2025●8 min read"
  - "March 5, 2024"

Usage:
    python extract_publication_dates.py

Design notes:
- This script is intentionally conservative:
  - If it cannot confidently parse a date from the content, it leaves
    the index entry unchanged and logs a warning.
  - It does not delete or modify canonical markdown content.
- It uses IndexManager to update index.yaml safely with locking.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
from datetime import datetime

from management.index_manager import IndexManager
from utils.script_utils import configure_utf8_output

configure_utf8_output()

DATE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # Examples: "Mar 27, 2025●8 min read", "Mar 7, 2024"
    (re.compile(r'\b([A-Z][a-z]{2})\s+(\d{1,2}),\s+(\d{4})'), "%b %d, %Y"),
    # Examples: "March 27, 2025"
    (re.compile(r'\b([A-Z][a-z]+)\s+(\d{1,2}),\s+(\d{4})'), "%B %d, %Y"),
]

def extract_date_from_content(content: str) -> str | None:
    """
    Try to extract a publication date from the article body.

    Returns:
        ISO date string (YYYY-MM-DD) if found, otherwise None.
    """
    # Only inspect the first ~40 lines; dates are typically near the top.
    lines = content.splitlines()[:40]
    for line in lines:
        for pattern, fmt in DATE_PATTERNS:
            m = pattern.search(line)
            if not m:
                continue
            try:
                # Join matched groups back into a single date string.
                date_str = m.group(0)
                dt = datetime.strptime(date_str, fmt)
                return dt.date().isoformat()
            except Exception:
                continue
    return None

def update_publication_dates() -> int:
    """
    Extract and write `published_at` for Anthropic engineering/news/research posts.

    Returns:
        Number of index entries updated.
    """
    # Use path_config for base_dir
    from path_config import get_base_dir
    base_dir = get_base_dir()
    manager = IndexManager(base_dir)
    index = manager.load_all()

    # Directories to scan
    target_dirs = [
        base_dir / "anthropic-com" / "engineering",
        base_dir / "anthropic-com" / "news",
        base_dir / "anthropic-com" / "research",
    ]

    updated = 0

    for target_dir in target_dirs:
        if not target_dir.exists():
            continue
        for md_path in target_dir.rglob("*.md"):
            rel_path = md_path.relative_to(base_dir).as_posix()

            # Find corresponding doc_id in index by matching path
            doc_id = None
            for key, meta in index.items():
                if isinstance(meta, dict) and meta.get("path") == rel_path:
                    doc_id = key
                    break

            if not doc_id:
                # No index entry yet; skip (scraper should create it on next run)
                continue

            # Skip if published_at is already present
            existing_meta = index[doc_id]
            if existing_meta.get("published_at"):
                continue

            try:
                content = md_path.read_text(encoding="utf-8")
            except Exception as e:
                print(f"⚠️  Skipping {md_path}: failed to read content ({e})")
                continue

            iso_date = extract_date_from_content(content)
            if not iso_date:
                print(f"⚠️  No publication date found in {md_path}")
                continue

            # Update index entry with locking
            new_meta = dict(existing_meta)
            new_meta["published_at"] = iso_date
            if manager.update_entry(doc_id, new_meta):
                # Keep local copy in sync for subsequent lookups in this run
                index[doc_id] = new_meta
                print(f"✅ Set published_at={iso_date} for {doc_id} ({rel_path})")
                updated += 1
            else:
                print(f"⚠️  Failed to persist published_at for {doc_id}")

    print(f"\nSummary: updated published_at for {updated} document(s)")
    return updated

def main() -> int:
    try:
        update_publication_dates()
        return 0
    except KeyboardInterrupt:
        print("\nAborted by user.")
        return 1
    except Exception as e:
        print(f"❌ Fatal error in extract_publication_dates.py: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

