#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
script_utils.py - Small shared helpers for docs-management scripts.

Currently provides:
- configure_utf8_output: standard Windows UTF-8 console configuration
- ensure_yaml_installed: common pyyaml import + error handling
- resolve_base_dir: shared base-dir resolution for index-related scripts
- exit code constants for more structured error signalling
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


import importlib
import subprocess
from typing import Any

from .common_paths import find_repo_root


# Shared exit codes for scripts (non-breaking: 0 still success, non-zero failure)
EXIT_SUCCESS = 0
EXIT_NO_RESULTS = 1
EXIT_BAD_ARGS = 2
EXIT_INDEX_ERROR = 3
EXIT_MISSING_DEPS = 4

# HTTP status codes for consistent checks across scripts
# Note: Only rate limiting is defined here as it requires special handling.
# Other status codes (500, 502, 503, 504) are handled via RETRY_STATUS_CODES
# list in http_utils.py which is loaded from config with appropriate fallbacks.
HTTP_STATUS_RATE_LIMITED = 429


def configure_utf8_output() -> None:
    """Configure UTF-8 output on Windows consoles where supported.

    Safe to call unconditionally at script startup.
    """
    if sys.platform == "win32":
        # Not all Python builds expose reconfigure; ignore if unavailable.
        stdout = getattr(sys, "stdout", None)
        stderr = getattr(sys, "stderr", None)
        try:
            if hasattr(stdout, "reconfigure"):
                stdout.reconfigure(encoding="utf-8")
            if hasattr(stderr, "reconfigure"):
                stderr.reconfigure(encoding="utf-8")
        except Exception:
            # Best-effort only; don't let console quirks break scripts.
            pass


def suppress_pydantic_v1_warning() -> None:
    """Suppress Pydantic V1 compatibility warning from confection (spacy dependency).

    On Python 3.14+, confection (a spacy dependency) emits a UserWarning about
    Pydantic V1 compatibility. This function suppresses that specific warning.

    Call this before importing spacy or any spacy-related modules.
    """
    import warnings
    warnings.filterwarnings(
        "ignore",
        message="Core Pydantic V1 functionality isn't compatible with Python 3.14",
        category=UserWarning,
        module="confection"
    )


def ensure_yaml_installed(auto_install: bool = True) -> Any:
    """Import and return PyYAML, installing it on-demand if missing."""

    def _import_yaml() -> Any:
        return importlib.import_module('yaml')  # type: ignore

    try:
        return _import_yaml()
    except ImportError:
        if not auto_install:
            print("❌ Missing dependency: pyyaml")
            print("Install with: pip install pyyaml")
            sys.exit(EXIT_MISSING_DEPS)

        python_executable = sys.executable or 'python'
        install_cmd = [python_executable, '-m', 'pip', 'install', 'pyyaml']
        try:
            subprocess.check_call(install_cmd)
        except Exception as exc:
            print(f"❌ Unable to install pyyaml: {exc}")
            sys.exit(EXIT_MISSING_DEPS)

        try:
            return _import_yaml()
        except ImportError as exc:
            print(f"❌ PyYAML still unavailable after install attempt: {exc}")
            sys.exit(EXIT_MISSING_DEPS)


def resolve_base_dir(base_dir_arg: str, default_rel: str | None = None) -> Path:
    """Resolve a base directory argument into an absolute path with path traversal protection.

    - If base_dir_arg is absolute, it's returned as-is (after validation).
    - If relative, it's interpreted relative to the skill directory (for plugin mode)
      or repository root (for local mode).
    - If empty, uses path_config.get_base_dir() (or default_rel if path_config unavailable).

    Validates that the resolved path is within a trusted root (skill directory for
    plugin installations, repository root for local installations) to prevent
    path traversal attacks.

    Args:
        base_dir_arg: Base directory argument (can be absolute or relative path)
        default_rel: Fallback relative path if base_dir_arg is empty and path_config unavailable
                     (default: "canonical" - relative to skill dir)

    Raises:
        ValueError: If resolved path is outside the trusted root
    """
    # Get skill directory for plugin-mode validation
    from .common_paths import get_skill_dir
    skill_dir = get_skill_dir()

    if not base_dir_arg:
        # Use path_config if available, otherwise fall back to default_rel
        try:
            from path_config import get_base_dir
            resolved = get_base_dir()
        except ImportError:
            if default_rel is None:
                default_rel = "canonical"
            resolved = (skill_dir / default_rel).resolve()
    else:
        base = Path(base_dir_arg)
        if not base.is_absolute():
            # Resolve relative paths from skill directory (plugin-friendly)
            base = skill_dir / base
        resolved = base.resolve()

    # Path traversal protection: ensure resolved path is within a trusted root
    # For plugins, trust the skill directory; for local installs, trust repo root
    trusted_root = skill_dir

    try:
        resolved.relative_to(trusted_root)
    except ValueError:
        # Also allow paths within CWD's repo root for backward compatibility
        try:
            repo_root = find_repo_root()
            resolved.relative_to(repo_root)
        except ValueError:
            raise ValueError(
                f"Base directory must be within skill directory or repository: {resolved} "
                f"is outside both skill dir {trusted_root} and repo root"
            )

    return resolved


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.
    
    Examples:
        format_duration(0.5) -> "500ms"
        format_duration(45.67) -> "45.67s"
        format_duration(125.5) -> "2m 5.50s"
        format_duration(3665.0) -> "1h 1m 5.00s"
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Human-readable duration string
    """
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.2f}s"


def normalize_url_for_display(url: str | None) -> str | None:
    """Strip .md extension from URLs for display purposes.
    
    URLs stored in metadata may include .md extensions (used for scraping),
    but website URLs should not have this extension. This function normalizes
    URLs by removing .md before the fragment (if present) or at the end.
    
    Examples:
        normalize_url_for_display("https://code.claude.com/docs/en/skills.md")
        -> "https://code.claude.com/docs/en/skills"
        
        normalize_url_for_display("https://code.claude.com/docs/en/skills.md#create")
        -> "https://code.claude.com/docs/en/skills#create"
        
        normalize_url_for_display("https://code.claude.com/docs/en/skills#create")
        -> "https://code.claude.com/docs/en/skills#create"  (unchanged)
        
        normalize_url_for_display(None) -> None
    
    Args:
        url: URL string (may include .md extension)
        
    Returns:
        Normalized URL without .md extension, or None if input was None
    """
    if not url:
        return url
    
    # Split URL at fragment (#) if present
    if '#' in url:
        base_url, fragment = url.rsplit('#', 1)
        # Remove .md from base URL
        if base_url.endswith('.md'):
            base_url = base_url[:-3]
        return f"{base_url}#{fragment}"
    else:
        # No fragment, just remove .md from end if present
        if url.endswith('.md'):
            return url[:-3]
        return url
