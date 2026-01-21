# Running Tests for docs-management Skill

## Quick Start

**ALWAYS use the helper scripts to avoid path errors. They handle path resolution correctly.**

### Windows (PowerShell)

```powershell
# RECOMMENDED: Use helper script (prevents path doubling issues)
# Works from anywhere - resolves paths absolutely from repo root
.\.claude\skills\docs-management\.pytest_runner.ps1

# Alternative 1: Use Python-based safe runner (works from anywhere)
# IMPORTANT: Use absolute path or ensure you're in repo root
$repoRoot = (Get-Location).Path
python "$repoRoot\.claude\skills\docs-management\scripts\run_tests_safely.py"

# Alternative 2: Use separate commands with absolute path resolution
# IMPORTANT: Must resolve paths absolutely to prevent doubling
$repoRoot = (Get-Location).Path
$skillDir = Join-Path $repoRoot ".claude" "skills" "docs-management"
Set-Location -LiteralPath $skillDir
python -m pytest tests/
```

**⚠️ CRITICAL:** If you're already in `.claude\skills\docs-management` or a subdirectory, using relative paths like `python .claude\skills\docs-management\scripts\run_tests_safely.py` will cause path doubling. Always use absolute paths or the helper scripts.

### macOS/Linux

```bash
# RECOMMENDED: Use helper script (prevents path doubling issues)
bash .claude/skills/docs-management/.pytest_runner.sh

# Alternative 1: Use Python-based safe runner (works from anywhere)
python .claude/skills/docs-management/scripts/utils/run_tests_safely.py

# Alternative 2: Change directory first (if helper scripts unavailable)
cd .claude/skills/docs-management
python -m pytest tests/
```

## Why This Matters

Pytest automatically detects the skill directory as its rootdir (via `conftest.py`), so:

- ✅ **Correct:** Use helper scripts (`.pytest_runner.ps1` or `.pytest_runner.sh`)
- ✅ **Correct:** `cd .claude/skills/docs-management` then `pytest tests/` (separate commands, not `&&`)
- ❌ **Wrong:** `cd .claude/skills/docs-management && pytest tests/` (PowerShell `&&` causes path doubling)
- ❌ **Wrong:** `pytest .claude/skills/docs-management/tests/` from repo root

The helper scripts use absolute path resolution to prevent path doubling issues that occur when using `cd` with `&&` in PowerShell.

## Helper Scripts

Three helper scripts are provided:

- `.pytest_runner.ps1` (Windows PowerShell) - Finds repo root, then resolves skill directory absolutely
- `.pytest_runner.sh` (macOS/Linux) - Uses `dirname` and `cd` with absolute paths
- `scripts/utils/run_tests_safely.py` (Cross-platform Python) - Can be called from anywhere, always resolves correctly

These scripts automatically resolve the skill directory path absolutely before changing directories, preventing path resolution errors and path doubling issues. The Python script is the most reliable as it uses Python's `Path(__file__)` which always resolves correctly.

## Path Doubling Issue (Fixed)

**Problem:** Using `cd .claude/skills/docs-management && python -m pytest` in PowerShell can cause path doubling (`.claude\skills\docs-management\.claude\skills\docs-management`) because PowerShell's `&&` operator resolves relative paths relative to the current directory, not the repo root.

**Root Cause:** If you're already in `.claude/skills/docs-management` or a subdirectory, `cd .claude/skills/docs-management` tries to resolve relative to the current directory, causing doubling.

**Solution:** ALWAYS use the helper scripts - they resolve paths absolutely from the repo root:

```powershell
# WRONG (causes path doubling if already in skill directory):
cd .claude\skills\docs-management && python -m pytest tests/

# CORRECT (use helper script - works from anywhere):
.\.claude\skills\docs-management\.pytest_runner.ps1

# CORRECT (Python-based runner - also works from anywhere):
python .claude\skills\docs-management\scripts\run_tests_safely.py

# CORRECT (separate commands with absolute path resolution):
$repoRoot = (Get-Location).Path
$skillDir = Join-Path $repoRoot ".claude" "skills" "docs-management"
Set-Location -LiteralPath $skillDir
python -m pytest tests/
```

**Why Helper Scripts Work:** The `.pytest_runner.ps1` script:

1. Finds the repo root by walking up from script location
2. Resolves skill directory absolutely from repo root: `Join-Path $RepoRoot ".claude" "skills" "docs-management"`
3. Uses `Set-Location -LiteralPath` with absolute path (prevents relative path resolution issues)
