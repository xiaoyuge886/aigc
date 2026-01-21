#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
enable_dev_mode.py - Generate shell commands to enable development mode.

This script outputs shell commands for different shells (PowerShell, Bash, CMD)
that set the OFFICIAL_DOCS_DEV_ROOT environment variable.

Usage:
    python enable_dev_mode.py              # Auto-detect skill directory
    python enable_dev_mode.py /path/to/skill  # Specify custom path

The output can be copied to your shell profile or run directly in your terminal.
"""

import sys
from pathlib import Path

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap

from utils.dev_mode import DEV_ROOT_ENV_VAR, format_shell_commands, _validate_skill_dir


def main():
    """Generate and print shell commands for enabling dev mode."""
    # Determine skill directory
    if len(sys.argv) > 1:
        # Custom path provided
        skill_dir = Path(sys.argv[1]).resolve()
    else:
        # Auto-detect from this script's location
        skill_dir = bootstrap.skill_dir

    # Validate the skill directory
    if not _validate_skill_dir(skill_dir):
        print(f"Error: Invalid skill directory: {skill_dir}")
        print("  - Directory must exist")
        print("  - Directory must contain SKILL.md")
        sys.exit(1)

    # Generate commands
    commands = format_shell_commands(skill_dir)

    print("=" * 70)
    print("Development Mode Setup for docs-management Plugin")
    print("=" * 70)
    print()
    print(f"Skill directory: {skill_dir}")
    print()
    print("-" * 70)
    print("POWERSHELL (Windows)")
    print("-" * 70)
    print()
    print("# Enable dev mode (run in terminal or add to $PROFILE):")
    print(f"  {commands['powershell']}")
    print()
    print("# Verify:")
    print(f"  echo $env:{DEV_ROOT_ENV_VAR}")
    print()
    print("# Disable:")
    print(f"  {commands['powershell_unset']}")
    print()
    print("-" * 70)
    print("BASH / ZSH (macOS, Linux, Git Bash)")
    print("-" * 70)
    print()
    print("# Enable dev mode (run in terminal or add to ~/.bashrc / ~/.zshrc):")
    print(f"  {commands['bash']}")
    print()
    print("# Verify:")
    print(f"  echo ${DEV_ROOT_ENV_VAR}")
    print()
    print("# Disable:")
    print(f"  {commands['bash_unset']}")
    print()
    print("-" * 70)
    print("CMD (Windows Command Prompt)")
    print("-" * 70)
    print()
    print("# Enable dev mode:")
    print(f"  {commands['cmd']}")
    print()
    print("# Verify:")
    print(f"  echo %{DEV_ROOT_ENV_VAR}%")
    print()
    print("# Disable:")
    print(f"  {commands['cmd_unset']}")
    print()
    print("=" * 70)
    print("USAGE")
    print("=" * 70)
    print()
    print("After setting the environment variable, running any script will")
    print("show a [DEV MODE] banner and write files to your dev repo instead")
    print("of the installed plugin location.")
    print()
    print("Example workflow:")
    print("  1. Set the environment variable (see above)")
    print("  2. Run: python scripts/core/scrape_all_sources.py --parallel")
    print("  3. Check changes: git diff canonical/")
    print("  4. Commit and push when ready")
    print()
    print("=" * 70)


if __name__ == "__main__":
    main()
