# spaCy Installation Guide

Comprehensive guide for installing spaCy and its language models for the docs-management skill. spaCy provides enhanced stop word filtering for better keyword extraction quality.

> **Official Documentation:** This guide is based on the [official spaCy installation documentation](https://spacy.io/usage#installation). For the most up-to-date information, refer to the [official source](https://spacy.io/usage#installation).

## Overview

spaCy is an **optional** dependency that improves keyword extraction quality by providing comprehensive stop word filtering. The docs-management scripts work perfectly fine without spaCy, using fallback stop words. However, installing spaCy provides better keyword quality.

**System Requirements:**

- 64-bit CPython 3.7+ (Python 3.7 or higher)
- Runs on Unix/Linux, macOS/OS X, and Windows
- Compatible with pip and conda package managers

## Quick Installation

### Automatic Installation (Recommended)

The easiest way to install spaCy is using the automated installation:

```bash
# Auto-install spaCy + model with pre-built wheels (no compiler needed)
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-all
```

Or let the extract-keywords command auto-install it:

```bash
# Run extract-keywords - it will auto-install spaCy if missing
python .claude/skills/docs-management/scripts/management/manage_index.py extract-keywords
```

### Manual Installation

If you prefer manual installation, follow the [official spaCy installation steps](https://spacy.io/usage#installation):

**Step 1: Upgrade pip, setuptools, and wheel** (recommended)

```bash
pip install -U pip setuptools wheel
```

#### Step 2: Install spaCy

```bash
# Install spaCy (uses upgrade flag as recommended)
pip install -U spacy
```

#### Step 3: Download English language model

```bash
python -m spacy download en_core_web_sm
```

**Note:** When using pip, it's generally recommended to install packages in a [virtual environment](https://spacy.io/usage#installation) to avoid modifying system state.

## Platform-Specific Instructions

### Windows

#### Option 1: Pre-built Wheels (No Compiler Needed) - Recommended

Most Python versions (3.7+) have pre-built wheels available. Per the [official spaCy guide](https://spacy.io/usage#installation), pip automatically prefers wheels if available:

```bash
# Step 1: Upgrade pip, setuptools, wheel first (recommended by spaCy)
pip install -U pip setuptools wheel

# Step 2: Install spaCy (pip will automatically prefer pre-built wheels if available)
pip install -U spacy

# Step 3: Download English model
python -m spacy download en_core_web_sm
```

**Note:** According to the [official spaCy documentation](https://spacy.io/usage#installation), `pip install -U spacy` automatically prefers pre-built wheels when available. You don't need `--only-binary :all:` - pip handles this automatically. This matches the official installation guide exactly.

#### Option 2: With Build Tools (Source Install)

If pre-built wheels aren't available for your Python version:

1. **Install Visual Studio Build Tools:**

   ```powershell
   # Using winget (recommended)
   winget install --id Microsoft.VisualStudio.BuildTools --exact --silent
   
   # Or download from:
   # https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022
   ```

2. **Upgrade pip and install spaCy:**

   ```bash
   pip install -U pip setuptools wheel
   pip install -U spacy
   python -m spacy download en_core_web_sm
   ```

**Verification:**

```python
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ spaCy installed successfully')"
```

### macOS

#### Option 1: Pre-built Wheels (macOS)

Most Python versions have pre-built wheels:

```bash
# Upgrade pip, setuptools, wheel first (recommended)
pip install -U pip setuptools wheel

# Install spaCy with pre-built wheels
pip install -U --only-binary :all: spacy

# Download English model
python -m spacy download en_core_web_sm
```

#### Option 2: With Xcode Command Line Tools

If pre-built wheels aren't available:

1. **Install Xcode Command Line Tools:**

   ```bash
   xcode-select --install
   ```

   Note: This command is idempotent - safe to run multiple times.

2. **Upgrade pip and install spaCy:**

   ```bash
   pip install -U pip setuptools wheel
   pip install -U spacy
   python -m spacy download en_core_web_sm
   ```

**Verification:**

```bash
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ spaCy installed successfully')"
```

### Linux

#### Option 1: Pre-built Wheels (Linux)

Most Python versions have pre-built wheels:

```bash
# Upgrade pip, setuptools, wheel first (recommended)
pip install -U pip setuptools wheel

# Install spaCy with pre-built wheels
pip install -U --only-binary :all: spacy

# Download English model
python -m spacy download en_core_web_sm
```

#### Option 2: With Build Tools

If pre-built wheels aren't available:

1. **Install build-essential (Debian/Ubuntu):**

   ```bash
   sudo apt update
   sudo apt install -y build-essential
   ```

   **Or for Fedora/RHEL:**

   ```bash
   sudo dnf groupinstall -y "Development Tools"
   ```

   **Or for Arch Linux:**

   ```bash
   sudo pacman -S --noconfirm base-devel
   ```

2. **Upgrade pip and install spaCy:**

   ```bash
   pip install -U pip setuptools wheel
   pip install -U spacy
   python -m spacy download en_core_web_sm
   ```

**Verification:**

```bash
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('✅ spaCy installed successfully')"
```

## Using Python Scripts for Installation

The docs-management skill provides Python functions for automated installation:

```python
from setup_dependencies import install_spacy_with_model

# Install spaCy + model (prefers pre-built wheels)
success, message = install_spacy_with_model(
    prefer_wheel=True,           # Try pre-built wheels first
    model_name='en_core_web_sm',  # Default English model
    verbose=True,                 # Show detailed progress
    auto_install_build_tools=True  # Auto-install build tools if needed
)

if success:
    print(f"✅ {message}")
else:
    print(f"❌ {message}")
```

## Verification

After installation, verify spaCy is working:

### Method 1: Command Line

```bash
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py
```

This will show the status of all dependencies, including spaCy.

### Method 2: Python Check

```python
from setup_dependencies import check_import, check_spacy_model

if check_import('spacy') and check_spacy_model():
    print("✅ spaCy and model installed")
else:
    print("❌ spaCy or model missing")
```

### Method 3: Direct Import

```python
import spacy
nlp = spacy.load('en_core_web_sm')
print(f"✅ spaCy loaded successfully - model path: {nlp.path}")
```

## Troubleshooting

### Issue: "No module named 'spacy'"

**Solution:** spaCy package not installed

```bash
pip install spacy
```

### Issue: "Can't find model 'en_core_web_sm'"

**Solution:** Model not downloaded

```bash
python -m spacy download en_core_web_sm
```

### Issue: "error: Microsoft Visual C++ 14.0 or greater is required"

**Solution:** Build tools not installed (Windows)

**Option 1:** Install build tools:

```powershell
winget install --id Microsoft.VisualStudio.BuildTools --exact
```

**Option 2:** Use pre-built wheel (if available for your Python version):

```bash
pip install --only-binary :all: spacy
```

**Option 3:** Use Python 3.11+ (better pre-built wheel support):

```bash
# Install Python 3.11+ from python.org, then:
pip install --only-binary :all: spacy
```

### Issue: "command 'gcc' failed with exit status 1" (Linux/macOS)

**Solution:** Build tools not installed

**Linux (Debian/Ubuntu):**

```bash
sudo apt update && sudo apt install -y build-essential
```

**macOS:**

```bash
xcode-select --install
```

**Then retry:**

```bash
pip install spacy
```

### Issue: Installation succeeds but import fails

**Solution:** Verify Python environment

```bash
# Check which Python you're using
which python
python --version

# Reinstall spaCy in correct environment
pip install --force-reinstall spacy
python -m spacy download en_core_web_sm
```

### Issue: Model download fails

**Solution:** Check network and try again

```bash
# Download with verbose output
python -m spacy download en_core_web_sm --verbose

# Or manually download from:
# https://github.com/explosion/spacy-models/releases
```

## Performance Considerations

### Pre-built Wheels vs Source Install

- **Pre-built wheels:** Fast installation, no compiler needed (~30 seconds)
- **Source install:** Requires compiler, takes longer (~5-10 minutes)

The automated installation tries pre-built wheels first, falling back to source if needed.

### Model Size

The `en_core_web_sm` model is approximately 12-15 MB. Larger models (`en_core_web_md`, `en_core_web_lg`) provide better accuracy but are larger (40MB-500MB).

## Integration with docs-management Scripts

### Automatic Detection

The docs-management scripts automatically detect if spaCy is available:

```bash
python .claude/skills/docs-management/scripts/management/manage_index.py extract-keywords
```

Output will show:

- ✅ spaCy Available - Enhanced stop word filtering enabled
- ❌ spaCy Missing - Using basic stop words (still effective)

### Manual Check

```bash
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py
```

This shows the status of all dependencies, including spaCy and the model.

## Benefits of spaCy

While optional, spaCy provides:

1. **Better Stop Word Filtering:** Comprehensive list of stop words vs basic fallback
2. **Improved Keyword Quality:** Better filtering of common words
3. **Language Detection:** Can detect document language
4. **Future Features:** Enables potential future NLP features

**Note:** The docs-management scripts work perfectly fine without spaCy using fallback stop words. spaCy is an enhancement, not a requirement.

## Additional Resources

- **[Official spaCy Installation Guide](https://spacy.io/usage#installation)** - Source of truth for installation instructions
- [spaCy Official Documentation](https://spacy.io/usage) - Complete documentation
- [Available Language Models](https://spacy.io/usage/models) - List of all available models
- [Python Package Index (PyPI) - spaCy](https://pypi.org/project/spacy/) - Package information
- [spaCy Troubleshooting Guide](https://spacy.io/usage#troubleshooting) - Common issues and solutions

## Summary

**Recommended Installation Method (Matches Official Guide):**

Following the [official spaCy installation guide](https://spacy.io/usage#installation):

```bash
# One command installs everything (matches official guide steps)
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-all
```

**Or let it auto-install when needed:**

```bash
# Auto-installs spaCy if missing during keyword extraction
python .claude/skills/docs-management/scripts/management/manage_index.py extract-keywords
```

**Manual Installation (Matches Official Guide):**

```bash
# Step 1: Upgrade pip, setuptools, wheel (official recommendation)
pip install -U pip setuptools wheel

# Step 2: Install spaCy (pip automatically prefers wheels if available)
pip install -U spacy

# Step 3: Download English model
python -m spacy download en_core_web_sm
```

The automated installation handles:

- Pre-built wheel detection (pip automatically prefers wheels per official guide)
- Build tools checking
- Model download
- Verification
- Error handling with clear messages

**Compliance with Official Guide:**

- ✅ Step 1: Upgrades pip, setuptools, wheel first
- ✅ Step 2: Uses `pip install -U spacy` (pip automatically prefers wheels)
- ✅ Step 3: Uses `python -m spacy download en_core_web_sm` for model download

All steps match the [official spaCy installation documentation](https://spacy.io/usage#installation) exactly.
