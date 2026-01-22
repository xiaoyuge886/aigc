#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
common_paths.py - Centralized path resolution utilities for docs-management scripts.

This module provides a single source of truth for all path resolution needs.
All functions use absolute path resolution from known anchors to avoid brittle
.parent.parent chains that break when files move.

Core utilities:
- find_repo_root: Locate git repository root
- get_skill_dir: Get docs-management skill root directory
- get_scripts_dir: Get scripts directory
- get_config_dir: Get config directory
- setup_python_path: Setup sys.path for imports

Note: For config-based path utilities (get_base_dir, get_index_path, get_temp_dir),
import from path_config directly to avoid circular imports.

Usage:
    from utils.common_paths import get_skill_dir, get_scripts_dir, setup_python_path
    
    # Setup paths and get directories
    skill_dir, scripts_dir, config_dir = setup_python_path()
    
    # Or get individual directories
    skill_dir = get_skill_dir()
"""

import sys
from pathlib import Path


def find_repo_root(start: Path | None = None) -> Path:
    """Find repository root by walking up until a .git directory is found.

    Args:
        start: Optional starting directory. Defaults to the current working dir.

    Returns:
        Path to the repository root (or the starting directory if .git is not found).
    """
    current = Path.cwd() if start is None else Path(start)
    repo_root = current
    while repo_root != repo_root.parent:
        if (repo_root / '.git').exists():
            return repo_root
        repo_root = repo_root.parent
    return current


def get_skill_dir(from_path: Path | None = None) -> Path:
    """Get the docs-management skill root directory.
    
    Uses absolute path resolution to find the skill directory by walking up
    from a known location until SKILL.md is found. This is depth-independent
    and works regardless of where the caller is located in the directory tree.
    
    Args:
        from_path: Optional starting path. If None, uses this file's location.
    
    Returns:
        Path to skill root directory (absolute)
    
    Example:
        >>> skill_dir = get_skill_dir()
        >>> print(skill_dir)
        /path/to/repo/.claude/skills/docs-management
    """
    if from_path is None:
        # Start from this file's location
        from_path = Path(__file__).resolve()
    else:
        from_path = Path(from_path).resolve()
    
    # Walk up to find SKILL.md (marker for skill root)
    current = from_path if from_path.is_dir() else from_path.parent
    while current != current.parent:
        if (current / 'SKILL.md').exists():
            return current
        current = current.parent
    
    # Fallback: if we're in the scripts tree, go up appropriately
    # This handles the case where SKILL.md doesn't exist yet
    if from_path.is_file():
        parts = from_path.parts
        if 'scripts' in parts:
            scripts_idx = parts.index('scripts')
            # skill_dir is one level up from scripts
            return Path(*parts[:scripts_idx]).resolve()

    # If we still can't find it, raise an error
    # Note: Removed hardcoded directory name check (official-docs + skills)
    # to make this more portable and avoid brittleness
    raise RuntimeError(f"Could not determine skill directory from {from_path} - SKILL.md marker not found")


def get_scripts_dir(from_path: Path | None = None) -> Path:
    """Get the scripts directory.
    
    Args:
        from_path: Optional starting path. If None, uses this file's location.
    
    Returns:
        Path to scripts directory (absolute)
    
    Example:
        >>> scripts_dir = get_scripts_dir()
        >>> print(scripts_dir)
        /path/to/repo/.claude/skills/docs-management/scripts
    """
    skill_dir = get_skill_dir(from_path)
    return skill_dir / 'scripts'


def get_config_dir(from_path: Path | None = None) -> Path:
    """Get the config directory.
    
    Args:
        from_path: Optional starting path. If None, uses this file's location.
    
    Returns:
        Path to config directory (absolute)
    
    Example:
        >>> config_dir = get_config_dir()
        >>> print(config_dir)
        /path/to/repo/.claude/skills/docs-management/config
    """
    skill_dir = get_skill_dir(from_path)
    return skill_dir / 'config'


def setup_python_path(from_path: Path | None = None) -> tuple[Path, Path, Path]:
    """Setup sys.path for imports and return key directories.
    
    This function configures Python's import path to allow absolute imports
    from scripts/ and config/ directories. Call this at the top of scripts
    instead of using brittle boilerplate with .parent.parent chains.
    
    Args:
        from_path: Optional starting path. If None, uses this file's location.
    
    Returns:
        Tuple of (skill_dir, scripts_dir, config_dir) as absolute paths
    
    Example:
        >>> skill_dir, scripts_dir, config_dir = setup_python_path()
        >>> # Now you can do: from utils.common_paths import ...
    """
    skill_dir = get_skill_dir(from_path)
    scripts_dir = skill_dir / 'scripts'
    config_dir = skill_dir / 'config'
    
    # Add to sys.path if not already present
    for path_dir in [scripts_dir, config_dir]:
        path_str = str(path_dir)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)
    
    return skill_dir, scripts_dir, config_dir


# Note: For get_base_dir, get_index_path, get_temp_dir, import from path_config directly.
# These config-based path utilities are intentionally kept separate to avoid circular imports.
# Example: from utils.path_config import get_base_dir, get_index_path, get_temp_dir
