# Dependencies and Setup

## Overview

**Required:** `pyyaml`, `requests`, `beautifulsoup4`, `markdownify`
**Optional (recommended):** `spacy`, `yake` (for enhanced keyword extraction)

## Quick Setup for Agents

```bash
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required
```

## Auto-Installation

**AUTO-INSTALLATION ENABLED:** The `extract-keywords` command now **automatically installs** optional dependencies (spaCy, YAKE) if they're missing! No manual setup needed.

**Use Python 3.13** for extract-keywords (spaCy compatibility):

```bash
# Just run extract-keywords - it will auto-install dependencies if needed
# Use Python 3.13 for spaCy compatibility
py -3.13 .claude/skills/docs-management/scripts/management/manage_index.py extract-keywords
```

**Manual setup (optional):** If you want to install dependencies separately:

```bash
# Quick check and install
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required
```

**Auto-installation behavior:**

- ✅ **Enabled by default** - `extract-keywords` auto-installs missing optional dependencies
- ✅ **Pre-built wheels first** - Tries to use pre-built wheels (no compiler needed)
- ✅ **Graceful fallbacks** - If installation fails, scripts continue with fallbacks
- ✅ **Individual installation** - Packages install one at a time so one failure doesn't block others
- 🔧 **Disable if needed** - Use `--no-auto-install` flag to skip auto-installation

## Windows/Compiler Issues

- ✅ **Automatic resolution**: The script automatically uses Python 3.13 if available (pre-built wheels, no compiler needed)
- ✅ **VS Build Tools auto-setup**: The script automatically locates and configures VS Build Tools environment if needed
- ✅ **No terminal restart required**: VS environment is set up in the current session automatically
- **Fallback**: Scripts work fine with fallbacks if installation fails
- **Optional manual setup** (only if you want the enhanced features):
  - Install Python 3.13 (recommended): `winget install --id Python.Python.3.13 -e --source winget`
  - Or install Visual Studio Build Tools: `winget install --id Microsoft.VisualStudio.BuildTools --exact`

This ensures all required dependencies are available. Optional NLP libraries (spaCy, YAKE) enhance keyword extraction but are not required - scripts will use fallbacks if missing.

## Statistics & Observability

The skill provides detailed extraction and search statistics:

- **extract-keywords command** reports which extraction methods were used (YAKE, spaCy, fallbacks), keyword source breakdown, and dependency status warnings
- **extract_metadata.py --stats** provides detailed per-document extraction statistics:
  - NLP methods used (spaCy, YAKE, or basic extraction)
  - Keyword sources breakdown (technical phrases, frontmatter, title/description, YAKE extraction, headings, filename, body content)
- **find_docs.py --verbose** displays relevance scores for search results, useful for debugging and tuning search quality
- **rebuild_index.py --verify-determinism** runs the index rebuild twice and compares outputs to verify deterministic behavior

## spaCy Troubleshooting

When spaCy is installed but not being used during keyword extraction:

- Run dependency diagnostics:
  - `python .claude/skills/docs-management/scripts/setup/check_dependencies.py --diagnose --json`
- Check where the spaCy model is installed:
  - `python .claude/skills/docs-management/scripts/setup/check_spacy_model_location.py`
- Ensure the interpreter used for this repo has spaCy + `en_core_web_sm`:
  - On Windows (recommended): `py -3.13 -m pip install -U spacy` and `py -3.13 -m spacy download en_core_web_sm`
- If spaCy appears in a different Python than the one running `refresh_index.py`, either:
  - Configure your shell/IDE to use that Python, or
  - Explicitly invoke: `py -3.13 .claude/skills/docs-management/scripts/management/refresh_index.py`

## Detailed Installation Issues

### spaCy Installation Issues

#### Python Version Compatibility

**Problem**: spaCy installation fails with Python 3.14 or higher.

**Root Cause**: spaCy supports Python 3.7-3.13, but does not support Python 3.14+.

**Solution**: The script **automatically detects and uses Python 3.13** if available. No manual intervention needed!

- ✅ **Automatic**: If Python 3.13 is installed, the script will use it automatically for spaCy installation
- ✅ **Pre-built wheels**: Python 3.13 has pre-built wheels available, so no compilation needed
- ✅ **No compiler required**: Using Python 3.13 means you don't need C++ build tools

**If Python 3.13 is not available:**

Install Python 3.13:

- **Windows**: `winget install --id Python.Python.3.13 -e --source winget`
- **macOS**: `brew install python@3.13`
- **Linux**: `sudo apt install python3.13 python3.13-venv python3.13-dev`

The script will automatically use Python 3.13 once installed.

#### Visual Studio Build Tools (Windows)

**Problem**: "Compiler not accessible in current session" error on Windows.

**Root Cause**: Visual Studio Build Tools are installed but compiler (`cl.exe`) is not in PATH.

**Solution**: The script **automatically locates and configures** VS Build Tools environment using `vcvarsall.bat`. No terminal restart needed!

The script will:

1. ✅ Automatically locate `vcvarsall.bat` using `vswhere.exe` or standard paths
2. ✅ Run `vcvarsall.bat` to set up the VS Build Tools environment
3. ✅ Apply environment variables to the current process
4. ✅ Verify compiler accessibility before proceeding

**If automatic setup fails:**

1. **Option 1 (Recommended)**: Use Python 3.13 instead (pre-built wheels, no compiler needed):

   ```bash
   py -3.13 -m pip install spacy
   ```

2. **Option 2**: Manual VS Build Tools setup (if you need Python 3.9-3.11):

   - Install VS Build Tools if not already installed: `winget install --id Microsoft.VisualStudio.BuildTools --exact`
   - Restart terminal after installation
   - Run setup script again

## Python Version Requirements

- **Python 3.14 works by default** - Scripts use modern type hints (lowercase `dict`, etc.)
- **Python 3.13 required for spaCy operations** - spaCy/Pydantic have compatibility issues with Python 3.14+
- When spaCy is involved (keyword extraction, metadata extraction), use `py -3.13` explicitly
- For scraping without spaCy, Python 3.14 works fine
