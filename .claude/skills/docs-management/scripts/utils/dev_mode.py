#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dev_mode.py - Development mode detection and path override for docs-management plugin.

This module provides explicit dev/prod mode separation via environment variable.
When OFFICIAL_DOCS_DEV_ROOT is set to a valid skill directory, all paths resolve
there instead of the installed plugin location.

Mode Detection Priority:
1. Dev Mode: OFFICIAL_DOCS_DEV_ROOT env var set to valid skill directory
2. Prod Mode: No env var set, use standard skill_dir resolution

Usage:
    from utils.dev_mode import is_dev_mode, get_effective_skill_dir, print_mode_banner

    # Check current mode
    if is_dev_mode():
        print("Running in development mode")

    # Get effective skill directory (respects dev mode)
    skill_dir = get_effective_skill_dir(fallback_skill_dir)

    # Print mode banner at script startup
    print_mode_banner(logger)

Environment Variables:
    OFFICIAL_DOCS_DEV_ROOT: Path to development skill directory.
                           Must contain SKILL.md to be valid.
"""

import io
import logging
import os
import sys
from pathlib import Path
from typing import NamedTuple


# Environment variable name for dev mode
DEV_ROOT_ENV_VAR = "OFFICIAL_DOCS_DEV_ROOT"


class ModeInfo(NamedTuple):
    """Information about current operating mode."""
    is_dev: bool
    skill_dir: Path
    source: str  # "env_var", "fallback", or "default"
    env_var_value: str | None


def _validate_skill_dir(path: Path) -> bool:
    """Check if path is a valid skill directory (contains SKILL.md).

    Args:
        path: Path to validate

    Returns:
        True if path exists and contains SKILL.md
    """
    if not path.exists():
        return False
    if not path.is_dir():
        return False
    if not (path / "SKILL.md").exists():
        return False
    return True


def is_dev_mode() -> bool:
    """Check if running in development mode.

    Returns True if OFFICIAL_DOCS_DEV_ROOT is set to a valid skill directory.

    Returns:
        True if in dev mode, False otherwise
    """
    env_value = os.environ.get(DEV_ROOT_ENV_VAR, "").strip()
    if not env_value:
        return False

    dev_path = Path(env_value)
    return _validate_skill_dir(dev_path)


def get_effective_skill_dir(fallback: Path) -> Path:
    """Get the effective skill directory, respecting dev mode override.

    If OFFICIAL_DOCS_DEV_ROOT is set and valid, returns that path.
    Otherwise returns the fallback (usually bootstrap.skill_dir).

    Args:
        fallback: Default skill directory to use if not in dev mode

    Returns:
        Path to effective skill directory (absolute)

    Raises:
        ValueError: If env var is set but path is invalid
    """
    env_value = os.environ.get(DEV_ROOT_ENV_VAR, "").strip()

    if not env_value:
        # No env var set - use fallback (prod mode)
        return fallback.resolve()

    dev_path = Path(env_value).resolve()

    # Validate the dev path
    if not dev_path.exists():
        raise ValueError(
            f"{DEV_ROOT_ENV_VAR} is set but path does not exist: {dev_path}\n"
            f"Either unset the variable or set it to a valid skill directory."
        )

    if not dev_path.is_dir():
        raise ValueError(
            f"{DEV_ROOT_ENV_VAR} is set but path is not a directory: {dev_path}\n"
            f"Either unset the variable or set it to a valid skill directory."
        )

    if not (dev_path / "SKILL.md").exists():
        raise ValueError(
            f"{DEV_ROOT_ENV_VAR} is set but path is not a valid skill directory "
            f"(missing SKILL.md): {dev_path}\n"
            f"Either unset the variable or set it to a directory containing SKILL.md."
        )

    return dev_path


def get_mode_info(fallback: Path | None = None) -> ModeInfo:
    """Get detailed information about current operating mode.

    Args:
        fallback: Default skill directory (optional, for full info)

    Returns:
        ModeInfo with mode details
    """
    env_value = os.environ.get(DEV_ROOT_ENV_VAR, "").strip()

    if not env_value:
        # Prod mode - no env var
        if fallback:
            return ModeInfo(
                is_dev=False,
                skill_dir=fallback.resolve(),
                source="fallback",
                env_var_value=None
            )
        else:
            return ModeInfo(
                is_dev=False,
                skill_dir=Path("."),  # Placeholder
                source="default",
                env_var_value=None
            )

    dev_path = Path(env_value).resolve()

    if _validate_skill_dir(dev_path):
        return ModeInfo(
            is_dev=True,
            skill_dir=dev_path,
            source="env_var",
            env_var_value=env_value
        )
    else:
        # Env var set but invalid - still report it
        return ModeInfo(
            is_dev=False,
            skill_dir=fallback.resolve() if fallback else Path("."),
            source="fallback",
            env_var_value=env_value  # Report the invalid value
        )


def print_mode_banner(logger: logging.Logger | None = None) -> None:
    """Print mode status banner to logger or stdout.

    Provides immediate visual feedback on which mode is active.

    Args:
        logger: Optional logger to use. If None, prints to stdout.
    """
    # Force UTF-8 output on Windows
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    env_value = os.environ.get(DEV_ROOT_ENV_VAR, "").strip()

    def output(msg: str) -> None:
        if logger:
            logger.info(msg)
        else:
            print(msg)

    if not env_value:
        output("[PROD MODE] Using installed skill directory")
        output(f"  (Set {DEV_ROOT_ENV_VAR} to enable dev mode)")
        return

    dev_path = Path(env_value).resolve()

    if _validate_skill_dir(dev_path):
        output("[DEV MODE] Using development skill directory:")
        output(f"  {dev_path}")
        output(f"  Set via: {DEV_ROOT_ENV_VAR}")
    else:
        output(f"[WARNING] {DEV_ROOT_ENV_VAR} is set but invalid:")
        output(f"  Value: {env_value}")
        if not dev_path.exists():
            output("  Error: Path does not exist")
        elif not dev_path.is_dir():
            output("  Error: Path is not a directory")
        else:
            output("  Error: Missing SKILL.md marker file")
        output("  Falling back to installed location")


def format_shell_commands(skill_dir: Path) -> dict[str, str]:
    """Generate shell commands to enable dev mode for different shells.

    Args:
        skill_dir: Path to skill directory

    Returns:
        Dict with shell names as keys and command strings as values
    """
    skill_path = str(skill_dir.resolve())

    # Escape backslashes for Windows paths in PowerShell
    ps_path = skill_path.replace("\\", "\\\\") if "\\" in skill_path else skill_path

    return {
        "powershell": f'$env:{DEV_ROOT_ENV_VAR} = "{skill_path}"',
        "powershell_unset": f'Remove-Item Env:{DEV_ROOT_ENV_VAR}',
        "bash": f'export {DEV_ROOT_ENV_VAR}="{skill_path}"',
        "bash_unset": f'unset {DEV_ROOT_ENV_VAR}',
        "cmd": f'set {DEV_ROOT_ENV_VAR}={skill_path}',
        "cmd_unset": f'set {DEV_ROOT_ENV_VAR}=',
    }


if __name__ == "__main__":
    """Self-test for dev_mode module."""
    print("Dev Mode Module Self-Test")
    print("=" * 60)

    print(f"\nEnvironment variable: {DEV_ROOT_ENV_VAR}")
    env_val = os.environ.get(DEV_ROOT_ENV_VAR, "")
    print(f"Current value: {repr(env_val) if env_val else '(not set)'}")

    print(f"\nis_dev_mode(): {is_dev_mode()}")

    print("\nget_mode_info():")
    info = get_mode_info()
    print(f"  is_dev: {info.is_dev}")
    print(f"  skill_dir: {info.skill_dir}")
    print(f"  source: {info.source}")
    print(f"  env_var_value: {info.env_var_value}")

    print("\nMode banner:")
    print("-" * 40)
    print_mode_banner()
    print("-" * 40)

    # Show shell commands using this file's parent as example skill_dir
    example_skill_dir = Path(__file__).resolve().parents[1]
    print(f"\nExample shell commands for: {example_skill_dir}")
    commands = format_shell_commands(example_skill_dir)
    print("\n# PowerShell:")
    print(f"  Enable:  {commands['powershell']}")
    print(f"  Disable: {commands['powershell_unset']}")
    print("\n# Bash/Zsh:")
    print(f"  Enable:  {commands['bash']}")
    print(f"  Disable: {commands['bash_unset']}")

    print("\n" + "=" * 60)
    print("Self-test complete!")
