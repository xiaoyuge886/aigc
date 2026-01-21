#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
cli_utils.py - Shared CLI helpers for docs-management scripts.

Keeps argparse configuration for common flags consistent across scripts.
Provides unified helpers for base_dir argument handling and path resolution.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; config_dir = bootstrap.config_dir

import argparse

# Import path_config for default base_dir
try:
    from .path_config import get_base_dir
    from .common_paths import find_repo_root, get_skill_dir
except ImportError:
    # Fallback if path_config not available
    def get_base_dir(start: Path | None = None) -> Path:
        from .common_paths import find_repo_root, get_skill_dir
        repo_root = find_repo_root(start)
        return repo_root / ".claude" / "references"

# Centralized default for canonical path (DRY - avoid magic string duplication)
DEFAULT_CANONICAL_RELATIVE = ".claude/skills/docs-management/canonical"


def _get_config_default_base_dir() -> str:
    """Get the default base_dir from config, with fallback to default constant.

    This is called once at module load to avoid duplicate config lookups.
    """
    try:
        skill_dir_path = Path(__file__).parent.parent
        config_dir_path = skill_dir_path / 'config'
        if str(config_dir_path) not in sys.path:
            sys.path.insert(0, str(config_dir_path))
        from config.config_registry import get_default
        return get_default('paths', 'base_dir', DEFAULT_CANONICAL_RELATIVE)
    except ImportError:
        return DEFAULT_CANONICAL_RELATIVE


# Module-level constant for config default (computed once at import)
_CONFIG_DEFAULT_BASE_DIR = _get_config_default_base_dir()


def add_base_dir_argument(parser: argparse.ArgumentParser, 
                          help_text: str | None = None,
                          default_override: str | None = None) -> None:
    """
    Add a standardized --base-dir argument to an argument parser.
    
    Gets default from path_config.get_base_dir() and handles relative/absolute
    path resolution. Provides consistent help text across all scripts.
    
    Args:
        parser: ArgumentParser to add the argument to
        help_text: Optional custom help text (if None, uses standard text)
        default_override: Optional override for default value (if None, uses config)
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_base_dir_argument(parser)
        >>> args = parser.parse_args(['--base-dir', 'custom/path'])
        >>> base_dir = resolve_base_dir_from_args(args)
    """
    # Get default base_dir from config, convert to relative path for display
    # Use skill_dir (not repo_root) because resolve_base_dir resolves relative to skill_dir
    default_base_dir = get_base_dir()
    skill_dir = get_skill_dir()

    if default_override:
        default_base_dir_str = default_override
    elif default_base_dir.is_relative_to(skill_dir):
        default_base_dir_str = str(default_base_dir.relative_to(skill_dir))
    else:
        default_base_dir_str = _CONFIG_DEFAULT_BASE_DIR
    
    if help_text is None:
        help_text = f"Base directory for canonical documentation storage (default: {default_base_dir_str}, from config)"
    
    parser.add_argument(
        "--base-dir",
        default=default_base_dir_str,
        help=help_text,
    )


def resolve_base_dir_from_args(args: argparse.Namespace) -> Path:
    """
    Resolve base_dir from parsed arguments into an absolute Path.
    
    Handles both relative and absolute paths. If the argument matches the
    default string, uses path_config.get_base_dir() to ensure config overrides
    are respected.
    
    Args:
        args: Parsed arguments with base_dir attribute
    
    Returns:
        Absolute Path to base directory
    
    Example:
        >>> parser = argparse.ArgumentParser()
        >>> add_base_dir_argument(parser)
        >>> args = parser.parse_args()
        >>> base_dir = resolve_base_dir_from_args(args)
    """
    from .script_utils import resolve_base_dir

    # Get the default to check if user provided the default value
    default_base_dir = get_base_dir()
    repo_root = find_repo_root()

    if default_base_dir.is_relative_to(repo_root):
        default_base_dir_str = str(default_base_dir.relative_to(repo_root))
    else:
        default_base_dir_str = _CONFIG_DEFAULT_BASE_DIR
    
    # If user provided the default string, use config to respect env overrides
    if args.base_dir == default_base_dir_str:
        return get_base_dir()
    
    # Otherwise resolve the provided path
    return resolve_base_dir(args.base_dir)


def add_common_index_args(parser: argparse.ArgumentParser, include_json: bool = False) -> None:
    """
    Attach standard index-related arguments to a parser.
    
    This is a convenience function that adds --base-dir and optionally --json.
    For more control, use add_base_dir_argument() directly.
    
    Args:
        parser: ArgumentParser to add arguments to
        include_json: If True, also add --json flag for JSON output
    """
    add_base_dir_argument(parser)
    if include_json:
        parser.add_argument(
            "--json",
            action="store_true",
            help="Output results as JSON (for tools/agents)",
        )


