#!/usr/bin/env python3
"""
Safe test runner that prevents path doubling issues.

This script can be called from anywhere and will always run pytest from the
correct skill directory, preventing path resolution errors.

Usage:
    python .claude/skills/docs-management/scripts/run_tests_safely.py
    python .claude/skills/docs-management/scripts/run_tests_safely.py -v
    python .claude/skills/docs-management/scripts/run_tests_safely.py tests/test_specific.py

This script uses Path(__file__).resolve() to get the absolute path of the script,
then resolves the skill directory from there, preventing path doubling issues
that occur when using relative paths with cd commands.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir

import subprocess
import os

# Get skill directory using centralized utility (depth-independent)
try:
    # Since we're in utils/, import common_paths after setting up path
    from utils.common_paths import get_skill_dir
    skill_dir = get_skill_dir()
except ImportError:
    # Fallback if common_paths not available (shouldn't happen)
    skill_dir = Path(__file__).resolve().parents[2]
    
if not skill_dir.exists():
    print(f"Error: Skill directory not found: {skill_dir}", file=sys.stderr)
    sys.exit(1)

# Change to skill directory using absolute path (prevents path doubling)
os.chdir(str(skill_dir))

# Run pytest with all arguments (defaults to tests/ if no args)
if len(sys.argv) > 1:
    cmd = [sys.executable, "-m", "pytest"] + sys.argv[1:]
else:
    cmd = [sys.executable, "-m", "pytest", "tests/"]

sys.exit(subprocess.run(cmd).returncode)

