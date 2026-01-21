#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bootstrap.py - Minimal bootstrap module for docs-management scripts.

This module provides a single entry point for path setup. Scripts can use this
instead of the 2-line boilerplate pattern that was duplicated across 45+ files.

BEFORE (2 lines repeated everywhere):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from utils.common_paths import setup_python_path; skill_dir, scripts_dir, config_dir = setup_python_path()

AFTER (1 line):
    from bootstrap import setup; skill_dir, scripts_dir, config_dir = setup()

OR for scripts in scripts/ root:
    import bootstrap; skill_dir, scripts_dir, config_dir = bootstrap.setup()

The setup() function handles:
1. Adding scripts/ and config/ to sys.path
2. Returning (skill_dir, scripts_dir, config_dir) paths
3. Working from any depth in the scripts tree

Note: This file must live in scripts/ root to be importable from subdirectories
after the initial sys.path.insert() call.
"""

import sys
from pathlib import Path


def _find_scripts_dir(from_path: Path | None = None) -> Path:
    """Find the scripts directory by walking up from caller location.

    Args:
        from_path: Starting path. If None, uses caller's __file__.

    Returns:
        Path to scripts directory (absolute)
    """
    if from_path is None:
        # Default to this file's location (scripts/)
        return Path(__file__).resolve().parent

    from_path = Path(from_path).resolve()

    # Walk up to find scripts/ directory
    current = from_path if from_path.is_dir() else from_path.parent
    while current != current.parent:
        if current.name == 'scripts' and (current / 'bootstrap.py').exists():
            return current
        current = current.parent

    # Fallback: this file's location
    return Path(__file__).resolve().parent


def setup(from_path: Path | None = None) -> tuple[Path, Path, Path]:
    """Setup sys.path and return key directories.

    This is the main entry point. Call this at the top of any script
    to configure imports and get standard directory paths.

    Args:
        from_path: Optional starting path for resolution.

    Returns:
        Tuple of (skill_dir, scripts_dir, config_dir) as absolute paths

    Example:
        from bootstrap import setup
        skill_dir, scripts_dir, config_dir = setup()

        # Now imports work:
        from utils.logging_utils import get_or_setup_logger
        from core.doc_resolver import DocResolver
    """
    scripts_dir = _find_scripts_dir(from_path)
    skill_dir = scripts_dir.parent
    config_dir = skill_dir / 'config'

    # Add to sys.path if not already present
    for path_dir in [scripts_dir, config_dir]:
        path_str = str(path_dir)
        if path_str not in sys.path:
            sys.path.insert(0, path_str)

    return skill_dir, scripts_dir, config_dir


# Auto-setup when imported (for simple `import bootstrap` usage)
# Scripts can ignore return value if they don't need the paths
_skill_dir, _scripts_dir, _config_dir = setup()

# Apply dev mode override if OFFICIAL_DOCS_DEV_ROOT is set
# This allows developers to run scripts from the installed location
# but have paths resolve to their dev repo for testing
try:
    from utils.dev_mode import get_effective_skill_dir
    _effective_skill_dir = get_effective_skill_dir(_skill_dir)
    if _effective_skill_dir != _skill_dir:
        _skill_dir = _effective_skill_dir
        _scripts_dir = _skill_dir / 'scripts'
        _config_dir = _skill_dir / 'config'
        # Update sys.path for the new directories
        for path_dir in [_scripts_dir, _config_dir]:
            path_str = str(path_dir)
            if path_str not in sys.path:
                sys.path.insert(0, path_str)
except ImportError:
    # dev_mode not available during initial setup or in minimal environments
    pass
except ValueError as e:
    # Invalid dev root path - print warning but continue with fallback
    import sys as _sys
    print(f"Warning: {e}", file=_sys.stderr)

# Export for scripts that want paths via attribute access
skill_dir = _skill_dir
scripts_dir = _scripts_dir
config_dir = _config_dir
