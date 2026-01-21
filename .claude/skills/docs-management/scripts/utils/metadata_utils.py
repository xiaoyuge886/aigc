#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metadata_utils.py - Helpers for normalizing metadata fields in index entries.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# Handle imports for both package and standalone execution
if __name__ == '__main__' or not __package__:
    # Add parent directories to path for standalone/direct import
    _script_dir = Path(__file__).resolve().parent
    _scripts_dir = _script_dir.parent if _script_dir.name != 'scripts' else _script_dir
    _skill_dir = _scripts_dir.parent
    # Add scripts and config to path
    for p in [str(_scripts_dir), str(_skill_dir / 'config')]:
        if p not in sys.path:
            sys.path.insert(0, p)

from typing import Iterable

def _normalize_list_like(value) -> list[str]:
    """Normalize a list-like metadata field (keywords/tags) into a list of str."""
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v is not None and str(v).strip()]
    if isinstance(value, str):
        # Allow comma-separated strings as well as single tokens.
        parts: Iterable[str] = value.split(",") if "," in value else [value]
        return [p.strip() for p in parts if p.strip()]
    # Anything else is treated as a single value if truthy.
    s = str(value).strip()
    return [s] if s else []

def normalize_keywords(value) -> list[str]:
    """Normalize a keywords field into a list of lowercase strings."""
    return [v.lower() for v in _normalize_list_like(value)]

def normalize_tags(value) -> list[str]:
    """Normalize a tags field into a list of lowercase strings."""
    return [v.lower() for v in _normalize_list_like(value)]
