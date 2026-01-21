#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_dependencies.py - Setup Python dependencies for docs-management scripts

Checks and optionally installs missing dependencies. Safe to run multiple times.
Designed for agentic tools to ensure environment is ready.

Usage:
    python setup_dependencies.py                    # Check only
    python setup_dependencies.py --install-required  # Install required deps
    python setup_dependencies.py --install-all       # Install all deps (required + optional)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import os
import subprocess
import shutil
import site
import json
from datetime import datetime
from typing import Dict, Any

from utils.script_utils import configure_utf8_output, suppress_pydantic_v1_warning
from utils.logging_utils import get_or_setup_logger

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()
suppress_pydantic_v1_warning()  # Must be called before spacy import

# Script logger (structured, with performance tracking)
logger = get_or_setup_logger(__file__, log_category="diagnostics")

# Import config helpers for subprocess timeouts
try:
    from config_helpers import (
        get_subprocess_default_timeout,
        get_subprocess_quick_timeout,
        get_subprocess_install_timeout,
        get_subprocess_build_timeout,
        get_subprocess_long_timeout
    )
except ImportError:
    # Fallback if config_helpers not available
    def get_subprocess_default_timeout(): return 10.0
    def get_subprocess_quick_timeout(): return 5.0
    def get_subprocess_install_timeout(): return 300.0
    def get_subprocess_build_timeout(): return 600.0
    def get_subprocess_long_timeout(): return 600.0

# Global installation log for reporting
_installation_log: list[Dict] = []

def detect_package_manager():
    """Detect available package manager for the current platform"""
    if sys.platform == 'win32':
        # Check for winget
        if shutil.which('winget'):
            return 'winget'
        # Check for chocolatey
        if shutil.which('choco'):
            return 'choco'
        return None
    elif sys.platform == 'darwin':  # macOS
        if shutil.which('brew'):
            return 'brew'
        return None
    else:  # Linux
        if shutil.which('apt'):
            return 'apt'
        elif shutil.which('dnf'):
            return 'dnf'
        elif shutil.which('yum'):
            return 'yum'
        elif shutil.which('pacman'):
            return 'pacman'
        return None

def get_python_environment_info() -> dict[str, Any]:
    """
    Get comprehensive information about the current Python environment
    
    Returns:
        Dictionary with environment details:
        - python_version: Version string (e.g., "3.12.0")
        - python_executable: Path to Python interpreter
        - python_major_minor: Version tuple (e.g., (3, 12))
        - is_venv: Boolean indicating if running in virtual environment
        - venv_path: Path to virtual environment (if applicable)
        - site_packages: List of site-packages directories
        - pip_location: Path to pip executable (if available)
        - pip_python_match: Boolean indicating if pip matches Python interpreter
    """
    info = {
        'python_version': sys.version.split()[0],
        'python_executable': sys.executable,
        'python_major_minor': (sys.version_info.major, sys.version_info.minor),
        'is_venv': False,
        'venv_path': None,
        'site_packages': [],
        'pip_location': None,
        'pip_python_match': False,
    }
    
    # Detect virtual environment
    venv_env = os.environ.get('VIRTUAL_ENV')
    if venv_env:
        info['is_venv'] = True
        info['venv_path'] = venv_env
    else:
        # Check if sys.prefix differs from sys.base_prefix (venv indicator)
        if sys.prefix != sys.base_prefix:
            info['is_venv'] = True
            info['venv_path'] = sys.prefix
    
    # Get site-packages locations
    try:
        info['site_packages'] = site.getsitepackages()
        # Also check user site-packages
        user_site = site.getusersitepackages()
        if user_site:
            info['site_packages'].append(user_site)
    except Exception:
        # Fallback: try to find site-packages manually
        lib_path = Path(sys.executable).parent / 'lib'
        if lib_path.exists():
            for py_dir in lib_path.glob('python*'):
                site_pkg = py_dir / 'site-packages'
                if site_pkg.exists():
                    info['site_packages'].append(str(site_pkg))
    
    # Find pip location
    pip_exe = shutil.which('pip')
    if pip_exe:
        info['pip_location'] = pip_exe
        # Check if pip's Python matches current interpreter
        try:
            result = subprocess.run(
                [pip_exe, '--version'],
                capture_output=True,
                text=True,
                timeout=get_subprocess_quick_timeout()
            )
            # Try to extract Python path from pip output or check pip's shebang
            pip_python = None
            if sys.platform != 'win32':
                # On Unix, check shebang (validation only, result not used)
                try:
                    with open(pip_exe, 'r') as f:
                        first_line = f.readline()
                        # Verify shebang format is valid
                        if first_line.startswith('#!'):
                            _ = first_line[2:].strip().split()[0]
                except Exception:
                    pass
            else:
                # On Windows, pip is a .exe or launcher, check via pip show
                try:
                    result = subprocess.run(
                        [pip_exe, 'show', 'pip'],
                        capture_output=True,
                        text=True,
                        timeout=int(get_subprocess_quick_timeout())
                    )
                    # Pip show doesn't directly show Python, but we can infer
                    # by checking if pip can import from same site-packages
                except Exception:
                    pass
            
            # Simple check: if pip is in same directory as Python or in Scripts/bin
            pip_path = Path(pip_exe)
            python_dir = Path(sys.executable).parent
            if pip_path.parent == python_dir or pip_path.parent.name in ['Scripts', 'bin']:
                # Likely matches, but verify by trying to get pip's Python
                try:
                    # Use pip to check its Python
                    result = subprocess.run(
                        [pip_exe, '--python-version'],
                        capture_output=True,
                        text=True,
                        timeout=int(get_subprocess_quick_timeout())
                    )
                    if result.returncode == 0:
                        pip_version = result.stdout.strip()
                        current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
                        info['pip_python_match'] = pip_version.startswith(current_version)
                    else:
                        # Fallback: assume match if in same directory structure
                        info['pip_python_match'] = True
                except Exception:
                    # If check fails, assume match based on location
                    info['pip_python_match'] = True
        except Exception:
            pass
    
    return info

def diagnose_environment(verbose: bool = False) -> dict[str, Any]:
    """
    Perform comprehensive environment diagnosis
    
    Args:
        verbose: If True, include additional diagnostic information
    
    Returns:
        Dictionary with diagnostic results
    """
    diagnosis = {
        'python_info': get_python_environment_info(),
        'path_entries': [],
        'other_pythons': [],
        'package_locations': {},
    }
    
    # Check PATH for Python-related entries
    path_env = os.environ.get('PATH', '')
    python_related = []
    for entry in path_env.split(os.pathsep):
        entry_path = Path(entry)
        if entry_path.exists():
            # Check if it contains Python executables
            if (entry_path / 'python.exe').exists() or (entry_path / 'python').exists() or \
               (entry_path / 'python3.exe').exists() or (entry_path / 'python3').exists():
                python_related.append(str(entry_path))
    diagnosis['path_entries'] = python_related
    
    # Try to find other Python installations (if verbose)
    if verbose:
        other_pythons = []
        common_paths = []
        
        if sys.platform == 'win32':
            # Check common Windows Python locations
            common_paths = [
                Path('C:/Python*'),
                Path('C:/Program Files/Python*'),
                Path('C:/Program Files (x86)/Python*'),
                Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python',
                Path(os.environ.get('APPDATA', '')) / 'Python',
            ]
        else:
            # Unix-like systems
            common_paths = [
                Path('/usr/bin'),
                Path('/usr/local/bin'),
                Path.home() / '.local' / 'bin',
            ]
        
        for base_path in common_paths:
            try:
                if '*' in str(base_path):
                    # Handle glob patterns
                    parent = base_path.parent
                    pattern = base_path.name
                    if parent.exists():
                        for py_dir in parent.glob(pattern):
                            for py_exe in ['python', 'python3', 'python.exe', 'python3.exe']:
                                py_path = py_dir / py_exe
                                if py_path.exists() and py_path != Path(sys.executable):
                                    other_pythons.append(str(py_path))
                else:
                    if base_path.exists():
                        for py_exe in ['python', 'python3', 'python.exe', 'python3.exe']:
                            py_path = base_path / py_exe
                            if py_path.exists() and py_path != Path(sys.executable):
                                other_pythons.append(str(py_path))
            except Exception:
                pass
        
        diagnosis['other_pythons'] = sorted(set(other_pythons))[:10]  # Limit to 10, sorted for determinism
    
    # Check package locations for key packages
    if verbose:
        key_packages = ['spacy', 'yake', 'yaml', 'requests']
        for pkg in key_packages:
            try:
                mod = __import__(pkg)
                if hasattr(mod, '__file__'):
                    pkg_path = Path(mod.__file__).parent
                    diagnosis['package_locations'][pkg] = str(pkg_path)
            except ImportError:
                diagnosis['package_locations'][pkg] = None
    
    return diagnosis

def print_environment_info(info: dict[str, Any | None] = None, verbose: bool = False) -> None:
    """
    Print formatted environment information
    
    Args:
        info: Environment info dict (if None, will be generated)
        verbose: If True, print additional details
    """
    if info is None:
        info = get_python_environment_info()
    
    print("🐍 Python Environment:")
    print("=" * 60)
    print(f"  Version:        {info['python_version']}")
    print(f"  Executable:     {info['python_executable']}")
    print(f"  Virtual Env:    {'Yes' if info['is_venv'] else 'No'}")
    if info['is_venv'] and info['venv_path']:
        print(f"  Venv Path:      {info['venv_path']}")
    
    if info['pip_location']:
        match_status = "✅ Matches" if info['pip_python_match'] else "⚠️  May not match"
        print(f"  pip Location:   {info['pip_location']} ({match_status})")
    else:
        print(f"  pip Location:   Not found in PATH")
    
    if verbose and info['site_packages']:
        print(f"  Site-packages:")
        for sp in info['site_packages'][:3]:  # Show first 3
            print(f"    - {sp}")
        if len(info['site_packages']) > 3:
            print(f"    ... and {len(info['site_packages']) - 3} more")
    print()

def detect_python_for_spacy() -> str | None:
    """
    Detect Python 3.13 installation for spaCy (spaCy supports 3.7-3.13, not 3.14+)
    
    Returns:
        Path to Python 3.13 executable if available, None otherwise
    """
    if sys.platform == 'win32':
        # On Windows, use py launcher to find Python 3.13
        try:
            result = subprocess.run(
                ['py', '-3.13', '--version'],
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_quick_timeout())
            )
            if result.returncode == 0:
                # Get the actual Python 3.13 executable path
                try:
                    result2 = subprocess.run(
                        ['py', '-3.13', '-c', 'import sys; print(sys.executable)'],
                        capture_output=True,
                        text=True,
                        timeout=int(get_subprocess_quick_timeout())
                    )
                    if result2.returncode == 0:
                        python_path = result2.stdout.strip()
                        if python_path and Path(python_path).exists():
                            return python_path
                except Exception:
                    pass
                # Fallback: use py -3.13 as command
                return 'py -3.13'
        except Exception:
            pass
        
        # Fallback: check common installation paths
        common_paths = [
            Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python' / 'Python313' / 'python.exe',
            Path(os.environ.get('APPDATA', '')) / 'Python' / 'Python313' / 'python.exe',
            Path('C:/Python313/python.exe'),
            Path('C:/Program Files/Python313/python.exe'),
            Path('C:/Program Files (x86)/Python313/python.exe'),
        ]
        for python_path in common_paths:
            if python_path.exists():
                return str(python_path)
    else:
        # On Unix-like systems, check for python3.13
        python313_path = shutil.which('python3.13')
        if python313_path:
            return python313_path
    
    return None

def check_compiler_accessible() -> bool:
    """
    Check if C++ compiler is accessible in PATH
    
    Returns:
        True if compiler (cl.exe, gcc, or g++) is accessible, False otherwise
    """
    if sys.platform == 'win32':
        # Check for MSVC compiler or MinGW
        return bool(shutil.which('cl') or shutil.which('gcc') or shutil.which('g++'))
    elif sys.platform == 'darwin':
        # macOS: Check for clang/gcc
        return bool(shutil.which('clang') or shutil.which('gcc'))
    else:
        # Linux: Check for gcc/g++
        return bool(shutil.which('gcc') and shutil.which('g++'))

def locate_vcvarsall_bat() -> Path | None:
    """
    Locate vcvarsall.bat using vswhere.exe or standard paths
    
    Returns:
        Path to vcvarsall.bat if found, None otherwise
    """
    if sys.platform != 'win32':
        return None
    
    # Method 1: Use vswhere.exe (most reliable - official Microsoft tool)
    vswhere_paths = [
        Path('C:/Program Files (x86)/Microsoft Visual Studio/Installer/vswhere.exe'),
        Path('C:/Program Files/Microsoft Visual Studio/Installer/vswhere.exe'),
    ]
    
    for vswhere_path in vswhere_paths:
        if vswhere_path.exists():
            try:
                # Find VS installation path
                result = subprocess.run(
                    [str(vswhere_path), '-latest', '-products', '*', '-requires', 
                     'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
                     '-property', 'installationPath'],
                    capture_output=True,
                    text=True,
                    timeout=int(get_subprocess_default_timeout())
                )
                if result.returncode == 0 and result.stdout.strip():
                    vs_path = Path(result.stdout.strip())
                    # Check for vcvarsall.bat in this installation
                    vcvarsall_paths = [
                        vs_path / 'VC/Auxiliary/Build/vcvarsall.bat',
                        vs_path / 'VC/vcvarsall.bat',  # Older versions
                    ]
                    for vcvarsall_path in vcvarsall_paths:
                        if vcvarsall_path.exists():
                            return vcvarsall_path
            except Exception:
                pass
    
    # Method 2: Check standard installation paths (fallback)
    standard_paths = [
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2022/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2019/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2017/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2017/BuildTools/VC/Auxiliary/Build/vcvarsall.bat'),
        # Also check for full Visual Studio (not just Build Tools)
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2022/Community/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2022/Professional/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvarsall.bat'),
        Path('C:/Program Files/Microsoft Visual Studio/2022/Enterprise/VC/Auxiliary/Build/vcvarsall.bat'),
    ]
    
    for path in standard_paths:
        if path.exists():
            return path
    
    return None

def get_effective_spacy_status() -> dict[str, Any]:
    """
    Determine effective spaCy availability across current and compatible Pythons.

    Returns:
        Dictionary with keys:
        - current: diagnostics for current interpreter (spacy_importable/model_loadable/etc.)
        - alt: diagnostics for an alternate compatible interpreter (e.g. Python 3.13), or None
        - effective_available: True if spaCy import is available in any supported interpreter
        - effective_model_available: True if en_core_web_sm is loadable in any supported interpreter
        - effective_python: Python executable used for spaCy if different from current, else None
    """
    status: dict[str, Any] = {
        "current": {},
        "alt": None,
        "effective_available": False,
        "effective_model_available": False,
        "effective_python": None,
    }

    # First, check current interpreter directly (without relying on check_spacy_model signature).
    current_diag: dict[str, Any] = {
        "spacy_importable": False,
        "spacy_version": None,
        "model_loadable": False,
        "model_location": None,
    }
    try:
        import spacy  # type: ignore

        current_diag["spacy_importable"] = True
        try:
            current_diag["spacy_version"] = spacy.__version__
        except Exception:
            pass
        try:
            nlp = spacy.load("en_core_web_sm")  # type: ignore
            current_diag["model_loadable"] = True
            if hasattr(nlp, "path") and getattr(nlp, "path", None):
                current_diag["model_location"] = str(nlp.path)
            elif hasattr(nlp, "_path") and getattr(nlp, "_path", None):
                current_diag["model_location"] = str(nlp._path)
        except Exception:
            pass
    except Exception:
        # spaCy not importable in current interpreter
        pass

    status["current"] = current_diag

    current_has_spacy = bool(current_diag.get("spacy_importable"))
    current_has_model = bool(current_diag.get("model_loadable"))

    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python313_path = None
    try:
        python313_path = detect_python_for_spacy()
    except Exception:
        python313_path = None

    alt_diag: dict[str, Any | None] = None

    # If an alternate compatible Python exists (e.g., 3.12), try diagnostics there as well.
    if python313_path:
        try:
            # Build a small helper script that reports spaCy diagnostics as JSON.
            helper_code = (
                "import json\n"
                "info = {\n"
                "  'spacy_importable': False,\n"
                "  'spacy_version': None,\n"
                "  'model_loadable': False,\n"
                "  'model_location': None,\n"
                "}\n"
                "try:\n"
                "  import spacy\n"
                "  info['spacy_importable'] = True\n"
                "  try:\n"
                "    info['spacy_version'] = spacy.__version__\n"
                "  except Exception:\n"
                "    pass\n"
                "  try:\n"
                "    nlp = spacy.load('en_core_web_sm')\n"
                "    info['model_loadable'] = True\n"
                "    if hasattr(nlp, 'path') and nlp.path:\n"
                "      info['model_location'] = str(nlp.path)\n"
                "    elif hasattr(nlp, '_path') and nlp._path:\n"
                "      info['model_location'] = str(nlp._path)\n"
                "  except Exception:\n"
                "    pass\n"
                "except Exception:\n"
                "  pass\n"
                "print(json.dumps(info))\n"
            )

            # python313_path can be an executable path or 'py -3.13'
            if " " in str(python313_path):
                # Treat as launcher command (e.g., 'py -3.13')
                cmd = str(python313_path).split() + ["-c", helper_code]
            else:
                cmd = [str(python313_path), "-c", helper_code]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_default_timeout()),
            )
            if result.returncode == 0 and result.stdout.strip():
                alt_diag = json.loads(result.stdout.strip())
        except Exception:
            alt_diag = None

    if alt_diag is not None:
        status["alt"] = alt_diag

    effective_available = current_has_spacy or bool(alt_diag and alt_diag.get("spacy_importable"))
    effective_model_available = current_has_model or bool(alt_diag and alt_diag.get("model_loadable"))

    status["effective_available"] = effective_available
    status["effective_model_available"] = effective_model_available

    # Decide which Python should be considered the effective spaCy provider.
    if effective_available and not current_has_spacy and alt_diag and alt_diag.get("spacy_importable"):
        status["effective_python"] = python313_path

    # Attach version/model_location for convenience at top level when available.
    if effective_available:
        if current_has_spacy:
            status["spacy_version"] = current_diag.get("spacy_version")
        elif alt_diag:
            status["spacy_version"] = alt_diag.get("spacy_version")
    if effective_model_available:
        if current_has_model:
            status["model_location"] = current_diag.get("model_location")
        elif alt_diag:
            status["model_location"] = alt_diag.get("model_location")

    status["python_version"] = python_version
    status["python313_available"] = python313_path is not None
    return status

def setup_vs_environment(arch: str = "x64", verbose: bool = False) -> bool:
    """
    Set up Visual Studio Build Tools environment by running vcvarsall.bat
    
    Args:
        arch: Architecture to set up ('x64', 'x86', 'x86_amd64', etc.)
        verbose: Print detailed progress messages
    
    Returns:
        True if environment was set up successfully, False otherwise
    """
    if sys.platform != 'win32':
        return False
    
    vcvarsall_path = locate_vcvarsall_bat()
    if not vcvarsall_path:
        if verbose:
            print("  ⚠️  vcvarsall.bat not found - cannot set up VS environment")
        return False
    
    if verbose:
        print(f"  🔧 Setting up VS Build Tools environment...")
        print(f"     Using: {vcvarsall_path}")
        print(f"     Architecture: {arch}")
    
    try:
        # Run vcvarsall.bat and capture environment variables
        # We use cmd.exe to run the batch file and capture the environment
        # The trick is to run a command that outputs all environment variables after vcvarsall.bat runs
        cmd = f'@echo off && call "{vcvarsall_path}" {arch} && set'
        
        result = subprocess.run(
            ['cmd.exe', '/c', cmd],
            capture_output=True,
            text=True,
            timeout=int(get_subprocess_long_timeout()),
            shell=False
        )
        
        if result.returncode != 0:
            if verbose:
                print(f"  ⚠️  Failed to run vcvarsall.bat (exit code: {result.returncode})")
            return False
        
        # Parse environment variables from output
        env_vars = {}
        for line in result.stdout.split('\n'):
            line = line.strip()
            if '=' in line and not line.startswith('_='):
                key, value = line.split('=', 1)
                env_vars[key] = value
        
        # Apply environment variables to current process
        for key, value in env_vars.items():
            os.environ[key] = value
        
        # Verify compiler is now accessible
        if check_compiler_accessible():
            if verbose:
                print("  ✅ VS Build Tools environment set up successfully")
            return True
        else:
            if verbose:
                print("  ⚠️  Environment set up but compiler still not accessible")
            return False
            
    except subprocess.TimeoutExpired:
        if verbose:
            print("  ⚠️  VS environment setup timed out")
        return False
    except Exception as e:
        if verbose:
            print(f"  ⚠️  Error setting up VS environment: {e}")
        return False

def ensure_compiler_accessible(verbose: bool = False) -> tuple[bool, str]:
    """
    Ensure C++ compiler is accessible, setting up VS environment if needed
    
    Args:
        verbose: Print detailed progress messages
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # First check if compiler is already accessible
    if check_compiler_accessible():
        return True, "Compiler already accessible in PATH"
    
    # For Windows, try to set up VS environment
    if sys.platform == 'win32':
        if verbose:
            print("  🔍 Compiler not in PATH. Attempting to locate and configure VS Build Tools...")
        
        # Try x64 first (most common)
        if setup_vs_environment(arch='x64', verbose=verbose):
            return True, "VS Build Tools environment configured successfully (x64)"
        
        # Try x86_amd64 (cross-compile)
        if setup_vs_environment(arch='x86_amd64', verbose=verbose):
            return True, "VS Build Tools environment configured successfully (x86_amd64)"
        
        # Try x86
        if setup_vs_environment(arch='x86', verbose=verbose):
            return True, "VS Build Tools environment configured successfully (x86)"
        
        return False, "Compiler not accessible and could not set up VS Build Tools environment"
    else:
        # For macOS/Linux, compiler should already be in PATH if build tools are installed
        return False, "Compiler not found in PATH. Install build tools: " + (
            "xcode-select --install" if sys.platform == 'darwin' 
            else "sudo apt install -y build-essential"
        )

def get_troubleshooting_guide(issue: str) -> list[str]:
    """
    Get platform-specific troubleshooting steps for common issues
    
    Args:
        issue: Type of issue ('python_version', 'compiler', 'spacy_install', etc.)
    
    Returns:
        List of troubleshooting steps
    """
    steps = []
    
    if issue == 'python_version':
        if sys.platform == 'win32':
            steps = [
                "Python 3.14 is not supported by spaCy (supports up to 3.13)",
                "Install Python 3.13:",
                "  winget install --id Python.Python.3.13 -e --source winget",
                "Or use py launcher:",
                "  py -3.13 -m pip install spacy",
                "The script will automatically use Python 3.13 if available"
            ]
        else:
            steps = [
                "Python 3.14 is not supported by spaCy (supports up to 3.13)",
                "Install Python 3.13:",
                "  macOS: brew install python@3.13",
                "  Linux: sudo apt install python3.13 python3.13-venv python3.13-dev",
                "Then use: python3.13 -m pip install spacy"
            ]
    
    elif issue == 'compiler':
        if sys.platform == 'win32':
            steps = [
                "Compiler not accessible in PATH",
                "The script will automatically try to locate and configure VS Build Tools",
                "If that fails:",
                "1. Install Visual Studio Build Tools:",
                "   winget install --id Microsoft.VisualStudio.BuildTools --exact",
                "2. Restart your terminal/PowerShell window",
                "3. Or use Python 3.13 (pre-built wheels, no compilation needed):",
                "   py -3.13 -m pip install spacy"
            ]
        elif sys.platform == 'darwin':
            steps = [
                "Install Xcode Command Line Tools:",
                "  xcode-select --install",
                "Or use Python 3.13 with pre-built wheels:",
                "  python3.13 -m pip install spacy"
            ]
        else:
            steps = [
                "Install build-essential:",
                "  sudo apt update && sudo apt install -y build-essential",
                "Or use Python 3.13 with pre-built wheels:",
                "  python3.13 -m pip install spacy"
            ]
    
    elif issue == 'spacy_install':
        steps = [
            "Recommended: Use Python 3.13 (pre-built wheels available, no compilation needed)",
            f"  {'py -3.13' if sys.platform == 'win32' else 'python3.13'} -m pip install -U pip setuptools wheel",
            f"  {'py -3.13' if sys.platform == 'win32' else 'python3.13'} -m pip install -U spacy",
            f"  {'py -3.13' if sys.platform == 'win32' else 'python3.13'} -m spacy download en_core_web_sm",
            "",
            "The script will automatically detect and use Python 3.13 if available"
        ]
    
    return steps

def check_build_tools_installed():
    """Check if C++ build tools are already installed (package installation check, separate from compiler accessibility)"""
    if sys.platform == 'win32':
        # Note: This checks if package is installed, not if compiler is accessible
        # Use check_compiler_accessible() to verify compiler accessibility
        
        # Also check if Visual Studio Build Tools package is installed (even if not in PATH yet)
        # This handles cases where build tools were just installed but PATH hasn't been refreshed
        for package_id in ['Microsoft.VisualStudio.BuildTools', 'Microsoft.VisualStudio.2022.BuildTools']:
            try:
                result = subprocess.run(
                    ['winget', 'list', '--id', package_id, '--exact'],
                    capture_output=True,
                    text=True,
                    timeout=int(get_subprocess_default_timeout())
                )
                # Check if package appears in the list (winget list shows installed packages)
                if result.returncode == 0:
                    # Package is listed - check if it's actually installed (not just available)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if package_id.lower() in line.lower() and any(word in line.lower() for word in ['installed', 'installedversion']):
                            return True
                        # Simple check: if package_id appears and line has version-like pattern
                        if package_id in line and any(char.isdigit() for char in line):
                            return True
            except Exception:
                pass
        
        # Also check if VS Build Tools directory exists (more reliable after install)
        vs_paths = [
            Path('C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools'),
            Path('C:/Program Files/Microsoft Visual Studio/2022/BuildTools'),
        ]
        for vs_path in vs_paths:
            if vs_path.exists() and (vs_path / 'VC/Tools/MSVC').exists():
                return True
        
        # Check if vcvarsall.bat exists (indicates VS Build Tools are installed)
        if locate_vcvarsall_bat():
            return True
        
        return False
    elif sys.platform == 'darwin':  # macOS
        # Check if xcode-select tools are installed
        try:
            result = subprocess.run(
                ['xcode-select', '-p'],
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_quick_timeout())
            )
            return result.returncode == 0 and '/Library/Developer/CommandLineTools' in result.stdout
        except Exception:
            return False
    else:  # Linux
        # Check if gcc is available
        return shutil.which('gcc') is not None and shutil.which('g++') is not None

def get_build_tools_install_instructions():
    """Get platform-specific instructions for installing C++ build tools"""
    pkg_mgr = detect_package_manager()
    
    if sys.platform == 'win32':
        if pkg_mgr == 'winget':
            return {
                'auto': True,
                'command': ['winget', 'install', '--id', 'Microsoft.VisualStudio.BuildTools', '--exact', '--silent', '--accept-package-agreements', '--accept-source-agreements'],
                'check_command': ['winget', 'list', '--id', 'Microsoft.VisualStudio.BuildTools', '--exact'],
                'package_name': 'Visual Studio Build Tools',
                'package_id': 'Microsoft.VisualStudio.BuildTools',
                'install_location': 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools',
                'manual': [
                    '1. Download Visual Studio Build Tools:',
                    '   https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022',
                    '2. Run installer and select "C++ build tools" workload',
                    '3. Or use winget (idempotent, installs latest version):',
                    '   winget install --id Microsoft.VisualStudio.BuildTools --exact'
                ]
            }
        elif pkg_mgr == 'choco':
            return {
                'auto': True,
                'command': ['choco', 'install', 'visualstudio2022buildtools', '--params', '"--add Microsoft.VisualStudio.Workload.VCTools --quiet"', '-y'],
                'check_command': ['choco', 'list', 'visualstudio2022buildtools', '--local-only'],
                'package_name': 'Visual Studio 2022 Build Tools',
                'package_id': 'visualstudio2022buildtools',
                'install_location': 'C:\\Program Files (x86)\\Microsoft Visual Studio\\2022\\BuildTools',
                'manual': [
                    '1. Install via Chocolatey (idempotent):',
                    '   choco install visualstudio2022buildtools --params "--add Microsoft.VisualStudio.Workload.VCTools" -y',
                    '2. Or download from: https://visualstudio.microsoft.com/downloads/'
                ]
            }
        else:
            return {
                'auto': False,
                'command': None,
                'check_command': None,
                'package_name': 'Visual Studio Build Tools',
                'package_id': None,
                'install_location': None,
                'manual': [
                    '1. Download Visual Studio Build Tools:',
                    '   https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022',
                    '2. Run installer and select "C++ build tools" workload',
                    '3. Or install winget first, then:',
                    '   winget install --id Microsoft.VisualStudio.BuildTools --exact'
                ]
            }
    elif sys.platform == 'darwin':  # macOS
        # xcode-select --install is idempotent (exits gracefully if already installed)
        return {
            'auto': True,
            'command': ['xcode-select', '--install'],
            'check_command': ['xcode-select', '-p'],
            'package_name': 'Xcode Command Line Tools',
            'package_id': 'xcode-command-line-tools',
            'install_location': '/Library/Developer/CommandLineTools',
            'manual': [
                '1. Install Xcode Command Line Tools (idempotent):',
                '   xcode-select --install',
                '2. Note: This shows a dialog if not installed, exits silently if already installed'
            ]
        }
    else:  # Linux
        if pkg_mgr == 'apt':
            return {
                'auto': True,
                'command': ['sudo', 'apt', 'update', '&&', 'sudo', 'apt', 'install', '-y', 'build-essential'],
                'check_command': ['dpkg', '-l', 'build-essential'],
                'package_name': 'build-essential',
                'package_id': 'build-essential',
                'install_location': '/usr/bin (system-wide)',
                'manual': [
                    '1. Install build tools (idempotent):',
                    '   sudo apt update && sudo apt install -y build-essential',
                    '2. This installs gcc, g++, make, and other essential build tools',
                    '3. Safe to run multiple times - won\'t reinstall if already present'
                ]
            }
        elif pkg_mgr == 'dnf' or pkg_mgr == 'yum':
            return {
                'auto': True,
                'command': [pkg_mgr, 'groupinstall', '-y', 'Development Tools'],
                'check_command': [pkg_mgr, 'grouplist', 'installed', 'Development Tools'],
                'package_name': 'Development Tools',
                'package_id': 'Development Tools',
                'install_location': '/usr/bin (system-wide)',
                'manual': [
                    f'1. Install development tools (idempotent):',
                    f'   sudo {pkg_mgr} groupinstall -y "Development Tools"',
                    '2. This installs gcc, g++, make, and other essential build tools',
                    '3. Safe to run multiple times - won\'t reinstall if already present'
                ]
            }
        elif pkg_mgr == 'pacman':
            return {
                'auto': True,
                'command': ['pacman', '-S', '--noconfirm', 'base-devel'],
                'check_command': ['pacman', '-Q', 'base-devel'],
                'package_name': 'base-devel',
                'package_id': 'base-devel',
                'install_location': '/usr/bin (system-wide)',
                'manual': [
                    '1. Install base development tools (idempotent):',
                    '   sudo pacman -S --noconfirm base-devel',
                    '2. This installs gcc, g++, make, and other essential build tools',
                    '3. Safe to run multiple times - won\'t reinstall if already present'
                ]
            }
        else:
            return {
                'auto': False,
                'command': None,
                'check_command': None,
                'manual': [
                    '1. Install build-essential or equivalent for your distribution:',
                    '   - Debian/Ubuntu: sudo apt install -y build-essential',
                    '   - Fedora/RHEL: sudo dnf groupinstall -y "Development Tools"',
                    '   - Arch: sudo pacman -S --noconfirm base-devel'
                ]
            }

def try_install_build_tools(auto_install: bool = False, verbose: bool = False):
    """
    Try to install C++ build tools via package manager (idempotent)
    
    Returns:
        Tuple of (success: bool, instructions: dict, message: str)
    """
    instructions = get_build_tools_install_instructions()
    
    # Check if already installed first
    if check_build_tools_installed():
        return True, instructions, "Build tools already installed"
    
    if not instructions['auto']:
        return False, instructions, "No package manager available for auto-installation"
    
    if not auto_install:
        return False, instructions, "Auto-installation disabled"
    
    pkg_mgr = detect_package_manager()
    cmd = instructions['command']
    
    # Handle commands - they're lists, but may contain '&&' as a string element
    # Convert to string, split on &&, then back to lists
    cmd_str = ' '.join(str(c) for c in cmd)
    if ' && ' in cmd_str:
        # Split on && and execute sequentially
        parts = cmd_str.split(' && ')
        commands = [part.strip().split() for part in parts]
    else:
        commands = [cmd]
    
    install_start_time = datetime.now()
    install_command_str = ' '.join(str(c) for c in cmd)
    
    try:
        print(f"  🔧 Installing C++ build tools via {pkg_mgr}...")
        print(f"     Command: {install_command_str}")
        print(f"     (This is idempotent - safe to run multiple times)")
        
        for cmd_parts in commands:
            # Skip empty commands
            cmd_parts = [c for c in cmd_parts if c and c != '&&']
            if not cmd_parts:
                continue
            
            # Handle sudo commands - can't auto-run without user interaction on Linux/macOS
            if cmd_parts[0] == 'sudo' and sys.platform != 'win32':
                if verbose:
                    print(f"     ⚠️  Sudo required - cannot auto-install without user interaction")
                    print(f"     Run manually: {' '.join(cmd_parts)}")
                return False, instructions, "Sudo required - manual installation needed"
            
            # For Windows, we can run winget/choco directly
            # Execute command
            result = subprocess.run(
                cmd_parts,
                check=False,  # Don't fail on non-zero - might be "already installed"
                capture_output=True,
                text=True,
                    timeout=get_subprocess_build_timeout()  # Configurable timeout for build tools
            )
            
            # Check if command succeeded or if it's a "already installed" scenario
            if result.returncode != 0:
                # Some package managers return non-zero for "already installed"
                # Check if tools are now available
                if check_build_tools_installed():
                    print("  ✅ Build tools already installed")
                    return True, instructions, "Build tools already installed"
                # Check for "already installed" messages in output
                output_lower = (result.stdout + result.stderr).lower()
                if any(phrase in output_lower for phrase in ['already installed', 'already exists', 'is already', 'no change']):
                    print("  ✅ Build tools already installed (detected from output)")
                    return True, instructions, "Build tools already installed"
                # If not installed and command failed, raise error
                if verbose:
                    print(f"     Error output: {result.stderr[:200] if result.stderr else result.stdout[:200]}")
                raise subprocess.CalledProcessError(result.returncode, cmd_parts, result.stdout, result.stderr)
        
        # Verify installation
        install_end_time = datetime.now()
        install_duration = (install_end_time - install_start_time).total_seconds()
        
        if check_build_tools_installed():
            # Check if compiler is actually accessible in PATH (vs just package installed)
            compiler_accessible = shutil.which('cl') or shutil.which('gcc') or shutil.which('g++')
            
            if compiler_accessible:
                print("  ✅ Build tools installed successfully (compiler accessible)")
            else:
                print("  ✅ Build tools package installed successfully")
                print("     ⚠️  Note: Compiler may not be in PATH in this session")
                print("     💡 Tip: If spaCy installation fails, restart your terminal and try again")
            
            # Log the installation
            _installation_log.append({
                'type': 'build_tools',
                'package_name': instructions.get('package_name', 'C++ Build Tools'),
                'package_id': instructions.get('package_id', 'unknown'),
                'install_location': instructions.get('install_location', 'unknown'),
                'command': install_command_str,
                'package_manager': pkg_mgr,
                'status': 'success',
                'compiler_accessible': compiler_accessible,
                'timestamp': install_start_time.isoformat(),
                'duration_seconds': install_duration,
                'platform': sys.platform
            })
            
            return True, instructions, "Build tools installed successfully"
        else:
            print("  ⚠️  Build tools installation completed, but verification failed")
            print("     (May need to restart terminal or run: python setup_dependencies.py --install-all)")
            
            # Log the installation attempt
            _installation_log.append({
                'type': 'build_tools',
                'package_name': instructions.get('package_name', 'C++ Build Tools'),
                'package_id': instructions.get('package_id', 'unknown'),
                'install_location': instructions.get('install_location', 'unknown'),
                'command': install_command_str,
                'package_manager': pkg_mgr,
                'status': 'verification_pending',
                'timestamp': install_start_time.isoformat(),
                'duration_seconds': install_duration,
                'platform': sys.platform
            })
            
            return True, instructions, "Installation completed (verification pending)"
            
    except subprocess.CalledProcessError as e:
        install_end_time = datetime.now()
        install_duration = (install_end_time - install_start_time).total_seconds()
        
        # Check if it's because it's already installed (some package managers return non-zero)
        if check_build_tools_installed():
            print("  ✅ Build tools already installed")
            
            # Log as already installed
            _installation_log.append({
                'type': 'build_tools',
                'package_name': instructions.get('package_name', 'C++ Build Tools'),
                'package_id': instructions.get('package_id', 'unknown'),
                'install_location': instructions.get('install_location', 'unknown'),
                'command': install_command_str,
                'package_manager': pkg_mgr,
                'status': 'already_installed',
                'timestamp': install_start_time.isoformat(),
                'duration_seconds': install_duration,
                'platform': sys.platform
            })
            
            return True, instructions, "Build tools already installed"
        
        error_msg = e.stderr[:200] if e.stderr else str(e)
        if verbose:
            print(f"  ❌ Installation failed: {error_msg}")
        
        # Log the failure
        _installation_log.append({
            'type': 'build_tools',
            'package_name': instructions.get('package_name', 'C++ Build Tools'),
            'package_id': instructions.get('package_id', 'unknown'),
            'install_location': instructions.get('install_location', 'unknown'),
            'command': install_command_str,
            'package_manager': pkg_mgr,
            'status': 'failed',
            'error': error_msg,
            'timestamp': install_start_time.isoformat(),
            'duration_seconds': install_duration,
            'platform': sys.platform
        })
        
        return False, instructions, f"Installation failed: {error_msg}"
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        install_end_time = datetime.now()
        install_duration = (install_end_time - install_start_time).total_seconds()
        
        # Log the error
        _installation_log.append({
            'type': 'build_tools',
            'package_name': instructions.get('package_name', 'C++ Build Tools'),
            'package_id': instructions.get('package_id', 'unknown'),
            'command': install_command_str,
            'package_manager': pkg_mgr,
            'status': 'error',
            'error': str(e),
            'timestamp': install_start_time.isoformat(),
            'duration_seconds': install_duration,
            'platform': sys.platform
        })
        
        return False, instructions, f"Installation error: {str(e)}"

def check_import(module_name: str) -> bool:
    """
    Check if a module can be imported
    
    Args:
        module_name: Name of module to import
    
    Returns:
        True if module can be imported, False otherwise
    """
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def run_pip_install(packages: list[str], dry_run: bool = False, install_individually: bool = False) -> bool:
    """
    Install packages using pip
    
    Args:
        packages: List of package names to install
        dry_run: If True, only print what would be installed
        install_individually: If True, install packages one at a time (for better error handling)
    
    Returns:
        True if at least one package installed successfully, False if all failed
    """
    if not packages:
        return True
    
    if dry_run:
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages
        print(f"  [DRY RUN] Would run: {' '.join(cmd)}")
        return True
    
    if install_individually:
        # Install packages one at a time so failures don't block others
        # Try pre-built wheels first (no compiler needed), fall back to source if needed
        success_count = 0
        for package in packages:
            install_start = datetime.now()
            install_method = None
            install_location = None
            
            try:
                print(f"  Installing: {package} (trying pre-built wheels first)...")
                # First try with --only-binary to use pre-built wheels (no compiler needed)
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', '--only-binary', ':all:', package],
                    check=True,
                    capture_output=True,
                    text=True
                )
                install_method = 'pre-built wheel'
                print(f"  ✅ Successfully installed: {package} (pre-built wheel)")
                success_count += 1
                
                # Try to get install location
                try:
                    import importlib.util
                    spec = importlib.util.find_spec(package)
                    if spec and spec.origin:
                        install_location = str(Path(spec.origin).parent)
                except Exception:
                    pass
            except subprocess.CalledProcessError as e:
                # If pre-built wheels fail, try regular install (may require compiler)
                try:
                    print(f"  ⚠️  Pre-built wheel not available, trying source install...")
                    result = subprocess.run(
                        [sys.executable, '-m', 'pip', 'install', package],
                        check=True,
                        capture_output=True,
                        text=True
                    )
                    install_method = 'source'
                    print(f"  ✅ Successfully installed: {package} (from source)")
                    success_count += 1
                    
                    # Try to get install location
                    try:
                        import importlib.util
                        spec = importlib.util.find_spec(package)
                        if spec and spec.origin:
                            install_location = str(Path(spec.origin).parent)
                    except Exception:
                        pass
                except subprocess.CalledProcessError as e2:
                    install_end = datetime.now()
                    install_duration = (install_end - install_start).total_seconds()
                    error_text = (e.stderr + e2.stderr).lower()
                    
                    # Log the failure
                    _installation_log.append({
                        'type': 'python_package',
                        'package_name': package,
                        'package_id': package,
                        'install_method': 'pip',
                        'status': 'failed',
                        'error': e2.stderr[:200] if e2.stderr else str(e2),
                        'timestamp': install_start.isoformat(),
                        'duration_seconds': install_duration,
                        'platform': sys.platform
                    })
                    
                    print(f"  ⚠️  Failed to install: {package}")
                    # Check if it's a build/compiler error
                    if 'compiler' in error_text or 'build' in error_text or 'c++' in error_text or 'microsoft visual c++' in error_text:
                        # Check if build tools might be installed but not in PATH
                        build_tools_maybe_installed = check_build_tools_installed()
                        if build_tools_maybe_installed:
                            print(f"     Note: Build tools appear to be installed but compiler not accessible in this session")
                            print(f"     💡 Try restarting your terminal/PowerShell and running the installation again")
                            print(f"     Or: Install in a new terminal window after build tools installation completes")
                        else:
                            print(f"     Note: Package requires C++ build tools (not installed)")
                            print(f"     Pre-built wheels may not be available for Python {sys.version_info.major}.{sys.version_info.minor}")
                        print(f"     This is optional - scripts will use fallbacks")
                        print()
                        if not build_tools_maybe_installed:
                            print(f"     Build Tools Installation Options:")
                            build_instructions = get_build_tools_install_instructions()
                            pkg_mgr = detect_package_manager()
                            if build_instructions['auto'] and pkg_mgr:
                                print(f"     Auto-install via {pkg_mgr}:")
                                print(f"       {build_instructions['command']}")
                                print()
                            print(f"     Manual installation:")
                            for line in build_instructions['manual']:
                                print(f"       {line}")
                            print()
                            print(f"     Alternative: Use Python 3.11/3.12/3.13 (better pre-built wheel support)")
                    else:
                        print(f"     Error: {e2.stderr[:300] if e2.stderr else str(e2)}...")  # Truncate long errors
                else:
                    # Log successful installation
                    install_end = datetime.now()
                    install_duration = (install_end - install_start).total_seconds()
                    _installation_log.append({
                        'type': 'python_package',
                        'package_name': package,
                        'package_id': package,
                        'install_method': install_method or 'pip',
                        'install_location': install_location or 'site-packages',
                        'status': 'success',
                        'timestamp': install_start.isoformat(),
                        'duration_seconds': install_duration,
                        'platform': sys.platform
                    })
        
        return success_count > 0
    else:
        # Install all packages together (original behavior)
        cmd = [sys.executable, '-m', 'pip', 'install'] + packages
        try:
            print(f"  Installing: {' '.join(packages)}")
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            print(f"  ✅ Successfully installed: {' '.join(packages)}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Failed to install: {' '.join(packages)}")
            print(f"     Error: {e.stderr[:500]}...")  # Truncate long errors
            return False

def print_installation_report() -> None:
    """Print a comprehensive report of all auto-installations"""
    if not _installation_log:
        return
    
    print()
    print("=" * 60)
    print("📋 AUTO-INSTALLATION REPORT")
    print("=" * 60)
    print()
    print("The following items were automatically installed or checked:")
    print()
    
    for i, entry in enumerate(_installation_log, 1):
        status_icon = {
            'success': '✅',
            'already_installed': 'ℹ️ ',
            'failed': '❌',
            'error': '⚠️ ',
            'verification_pending': '⏳'
        }.get(entry.get('status', 'unknown'), '❓')
        
        print(f"{i}. {status_icon} {entry.get('package_name', 'Unknown')}")
        print(f"   Type: {entry.get('type', 'unknown')}")
        print(f"   Status: {entry.get('status', 'unknown')}")
        
        if entry.get('package_id'):
            print(f"   Package ID: {entry.get('package_id')}")
        
        if entry.get('install_location'):
            print(f"   Location: {entry.get('install_location')}")
        
        if entry.get('install_method'):
            print(f"   Method: {entry.get('install_method')}")
        
        if entry.get('package_manager'):
            print(f"   Package Manager: {entry.get('package_manager')}")
        
        if entry.get('command'):
            print(f"   Command: {entry.get('command')}")
        
        if entry.get('timestamp'):
            print(f"   Timestamp: {entry.get('timestamp')}")
        
        if entry.get('duration_seconds'):
            print(f"   Duration: {entry.get('duration_seconds', 0):.2f} seconds")
        
        if entry.get('error'):
            print(f"   Error: {entry.get('error')}")
        
        print()
    
    print("=" * 60)
    print()

def check_spacy_model(model_name: str = 'en_core_web_sm') -> bool:
    """Check if spaCy model is installed"""
    try:
        import spacy
        _ = spacy.load(model_name)  # Load to verify model exists
        return True
    except (OSError, ImportError):
        return False

def install_spacy_with_model(
    prefer_wheel: bool = True,
    model_name: str = 'en_core_web_sm',
    verbose: bool = False,
    auto_install_build_tools: bool = True
) -> tuple[bool, str]:
    """
    Install spaCy and model with comprehensive error handling
    
    Automatically uses Python 3.13 if available (spaCy supports 3.7-3.13, not 3.14+)
    Sets up VS Build Tools environment automatically if needed for source installs.
    
    Args:
        prefer_wheel: Try to install pre-built wheels first (no compiler needed)
        model_name: Name of spaCy model to download (default: en_core_web_sm)
        verbose: Print detailed progress messages
        auto_install_build_tools: Attempt to auto-install build tools if needed
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    # Step 1: Check if already installed (check with current Python first)
    if check_import('spacy') and check_spacy_model(model_name):
        return True, "spaCy and model already installed"
    
    install_start = datetime.now()
    
    # Step 2: Detect and use Python 3.13 for spaCy (spaCy supports 3.7-3.13, not 3.14+)
    python_executable = sys.executable
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python313_executable = detect_python_for_spacy()
    using_python313 = False
    install_method = None
    
    # Check if we need Python 3.13 (current version is 3.14+ or not supported)
    if python_version >= '3.14' or (python313_executable and python_version < '3.7'):
        if python313_executable:
            if isinstance(python313_executable, str) and python313_executable.startswith('py -3.13'):
                # Use py launcher command
                python_executable = python313_executable
                using_python313 = True
                if verbose:
                    print(f"  🔍 Python {python_version} detected - spaCy requires 3.7-3.13")
                    print(f"  ✅ Using Python 3.13 via py launcher (pre-built wheels available, no compilation needed)")
            elif Path(python313_executable).exists():
                # Use direct path
                python_executable = python313_executable
                using_python313 = True
                if verbose:
                    print(f"  🔍 Python {python_version} detected - spaCy requires 3.7-3.13")
                    print(f"  ✅ Using Python 3.13: {python_executable}")
                    print(f"     (Pre-built wheels available, no compilation needed)")
        else:
            # Python 3.13 not available - provide clear error message
            error_msg = f"spaCy requires Python 3.7-3.13, but Python {python_version} is being used. "
            troubleshooting = get_troubleshooting_guide('python_version')
            error_msg += "Python 3.13 not found. "
            if troubleshooting:
                error_msg += "\n".join(troubleshooting[:3])  # First few steps
            return False, error_msg
    
    # Step 3: Check if VS Build Tools needed (only for source installs or Python 3.14)
    # If using Python 3.13, skip VS setup (pre-built wheels don't need compiler)
    build_tools_needed = False
    if not using_python313 and not prefer_wheel:
        build_tools_available = check_build_tools_installed()
        build_tools_needed = not build_tools_available
        
        if build_tools_needed:
            if verbose:
                print("  🔍 Checking for C++ build tools (needed for source install)...")
            if auto_install_build_tools:
                build_success, instructions, msg = try_install_build_tools(
                    auto_install=True,
                    verbose=verbose
                )
                if build_success:
                    build_tools_available = check_build_tools_installed()
                    if build_tools_available:
                        print("  ✅ Build tools detected - ready for spaCy compilation")
                    else:
                        print("  ⚠️  Build tools installed but compiler not in PATH yet")
                        print("     Attempting to configure VS environment automatically...")
                        # Try to set up VS environment automatically
                        compiler_success, compiler_msg = ensure_compiler_accessible(verbose=verbose)
                        if not compiler_success:
                            print(f"     ⚠️  {compiler_msg}")
                            print("     Proceeding anyway - installation will verify availability...")
                else:
                    return False, f"Build tools required for source installation: {msg}"
            else:
                if not build_tools_available:
                    instructions = get_build_tools_install_instructions()
                    error_msg = "Build tools required for source installation. "
                    if using_python313:
                        error_msg += "Alternatively, use Python 3.13 (pre-built wheels, no compiler needed). "
                    error_msg += f"Run: {' '.join(instructions.get('command', []))}"
                    return False, error_msg
    
    # Step 4: If not using Python 3.13 and source install needed, ensure compiler accessible
    if not using_python313 and not prefer_wheel:
        if verbose:
            print("  🔍 Ensuring compiler is accessible for source installation...")
        compiler_success, compiler_msg = ensure_compiler_accessible(verbose=verbose)
        if not compiler_success and verbose:
            print(f"     ⚠️  {compiler_msg}")
    
    # Step 5: Upgrade pip, setuptools, and wheel first (as recommended by spaCy)
    if verbose:
        print("  🔧 Upgrading pip, setuptools, and wheel...")
    try:
        # Build command based on Python executable
        if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
            # Use py launcher - split command
            cmd = ['py', '-3.13', '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
        else:
            cmd = [python_executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
        
        subprocess.run(
            cmd,
            check=False,  # Don't fail if already up to date
            capture_output=True,
            text=True,
            timeout=int(get_subprocess_install_timeout())
        )
    except Exception:
        pass  # Continue even if upgrade fails
    
    # Step 6: Install spaCy
    # Per official guide: https://spacy.io/usage#installation
    # Use `pip install -U spacy` which automatically prefers wheels if available
    if prefer_wheel:
        if verbose:
            print("  📦 Installing spaCy (pip will automatically prefer pre-built wheels if available)...")
            if using_python313:
                print("     Using Python 3.13 - pre-built wheels should be available")
        try:
            # Build command based on Python executable
            if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
                # Use py launcher - split command
                cmd = ['py', '-3.13', '-m', 'pip', 'install', '-U', 'spacy']
            else:
                cmd = [python_executable, '-m', 'pip', 'install', '-U', 'spacy']
            
            # Official recommendation: pip automatically prefers wheels if available
            # This matches the official guide: https://spacy.io/usage#installation
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=get_subprocess_install_timeout()  # Configurable timeout for install operations
            )
            # Check if wheel was used by examining output
            if 'wheel' in result.stdout.lower() or 'already satisfied' in result.stdout.lower():
                install_method = 'pre-built wheel (auto-selected by pip)'
            else:
                install_method = 'source (compiled)'
            if verbose:
                print(f"  ✅ spaCy installed via {install_method}")
        except subprocess.CalledProcessError as e:
            # If prefer_wheel but installation failed, handle the error
            install_end = datetime.now()
            install_duration = (install_end - install_start).total_seconds()
            error_msg = e.stderr[:300] if e.stderr else (e.stdout[:300] if e.stdout else str(e))
            
            # Log the failure
            _installation_log.append({
                'type': 'python_package',
                'package_name': 'spacy',
                'package_id': 'spacy',
                'install_method': 'pip',
                'status': 'failed',
                'error': error_msg,
                'timestamp': install_start.isoformat(),
                'duration_seconds': install_duration,
                'platform': sys.platform
            })
            
            # Check if it's a build error
            error_text_lower = error_msg.lower()
            if 'compiler' in error_text_lower or 'build' in error_text_lower or 'c++' in error_text_lower or 'microsoft visual c++' in error_text_lower:
                # Build error - check if we can use Python 3.13 instead
                if not using_python313:
                    python313_available = detect_python_for_spacy()
                    if python313_available:
                        msg = ("spaCy installation failed: Compilation required but compiler not accessible. "
                               "Switching to Python 3.13 (pre-built wheels available, no compilation needed)...")
                        # Retry with Python 3.13
                        return install_spacy_with_model(
                            prefer_wheel=True,
                            model_name=model_name,
                            verbose=verbose,
                            auto_install_build_tools=auto_install_build_tools
                        )
                
                # Check if build tools are actually installed (maybe just not in PATH)
                build_tools_installed = check_build_tools_installed()
                if build_tools_installed:
                    msg = ("spaCy installation failed: Build tools are installed but compiler not accessible. "
                           "Attempting to configure VS environment automatically...")
                    # Try to set up VS environment
                    compiler_success, compiler_msg = ensure_compiler_accessible(verbose=verbose)
                    if compiler_success:
                        # Retry installation after setting up environment
                        if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
                            cmd = ['py', '-3.13', '-m', 'pip', 'install', '-U', 'spacy']
                        else:
                            cmd = [python_executable, '-m', 'pip', 'install', '-U', 'spacy']
                        try:
                            result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=int(get_subprocess_install_timeout()))
                            install_method = 'pre-built wheel (auto-selected by pip)'
                            if verbose:
                                print(f"  ✅ spaCy installed successfully after configuring VS environment")
                        except subprocess.CalledProcessError:
                            msg = ("spaCy installation failed: Compiler configured but installation still failed. "
                                   "Try restarting your terminal or use Python 3.13 (pre-built wheels, no compilation needed): "
                                   f"{'py -3.13 -m pip install spacy' if sys.platform == 'win32' else 'python3.13 -m pip install spacy'}")
                            return False, msg
                    else:
                        msg = ("spaCy installation failed: Build tools are installed but compiler not accessible in current session. "
                               "Try restarting your terminal or run in a new PowerShell/CMD window. "
                               f"Or use Python 3.13 (pre-built wheels, no compilation needed): {'py -3.13 -m pip install spacy' if sys.platform == 'win32' else 'python3.13 -m pip install spacy'}")
                        return False, msg
                else:
                    instructions = get_build_tools_install_instructions()
                    pkg_mgr = detect_package_manager()
                    msg = "spaCy installation failed: C++ build tools required"
                    if instructions.get('auto') and pkg_mgr and auto_install_build_tools:
                        msg += f". Auto-install via: {' '.join(instructions['command'])}"
                    else:
                        msg += ". Install manually: https://visualstudio.microsoft.com/downloads/#build-tools-for-visual-studio-2022"
                    msg += f"\nAlternatively, use Python 3.13 (pre-built wheels, no compilation needed): {'py -3.13 -m pip install spacy' if sys.platform == 'win32' else 'python3.13 -m pip install spacy'}"
                    return False, msg
            else:
                return False, f"spaCy installation failed: {error_msg}"
        except subprocess.TimeoutExpired:
            return False, "spaCy installation timed out (may need manual intervention)"
    else:
        # Install from source directly (explicitly requested)
        if verbose:
            print("  📦 Installing spaCy from source...")
        try:
            # Build command based on Python executable
            if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
                cmd = ['py', '-3.13', '-m', 'pip', 'install', '-U', 'spacy']
            else:
                cmd = [python_executable, '-m', 'pip', 'install', '-U', 'spacy']
            
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                timeout=get_subprocess_build_timeout()  # Configurable timeout for compilation
            )
            install_method = 'source (compiled)'
            if verbose:
                print("  ✅ spaCy installed from source")
        except subprocess.CalledProcessError as e2:
            install_end = datetime.now()
            install_duration = (install_end - install_start).total_seconds()
            error_msg = e2.stderr[:300] if e2.stderr else (e2.stdout[:300] if e2.stdout else str(e2))
            
            # Log the failure
            _installation_log.append({
                'type': 'python_package',
                'package_name': 'spacy',
                'package_id': 'spacy',
                'install_method': 'pip',
                'status': 'failed',
                'error': error_msg,
                'timestamp': install_start.isoformat(),
                'duration_seconds': install_duration,
                'platform': sys.platform
            })
            
            # Check if it's a build error (for source install)
            error_text_lower = error_msg.lower()
            if 'compiler' in error_text_lower or 'build' in error_text_lower or 'c++' in error_text_lower or 'microsoft visual c++' in error_text_lower:
                # Try to set up VS environment and retry
                compiler_success, compiler_msg = ensure_compiler_accessible(verbose=verbose)
                if compiler_success:
                    # Retry installation
                    try:
                        result = subprocess.run(
                            cmd,
                            check=True,
                            capture_output=True,
                            text=True,
                            timeout=int(get_subprocess_build_timeout())
                        )
                        install_method = 'source (compiled)'
                        if verbose:
                            print("  ✅ spaCy installed from source after configuring VS environment")
                    except subprocess.CalledProcessError:
                        msg = ("spaCy installation failed: Compiler configured but installation still failed. "
                               "Try restarting your terminal or use Python 3.13 (pre-built wheels, no compilation needed): "
                               f"{'py -3.13 -m pip install spacy' if sys.platform == 'win32' else 'python3.13 -m pip install spacy'}")
                        return False, msg
                else:
                    msg = ("spaCy installation failed: C++ build tools required for source installation. "
                           f"{compiler_msg}. "
                           f"Or use Python 3.13 (pre-built wheels, no compilation needed): {'py -3.13 -m pip install spacy' if sys.platform == 'win32' else 'python3.13 -m pip install spacy'}")
                    return False, msg
            else:
                return False, f"spaCy installation failed: {error_msg}"
        except subprocess.TimeoutExpired:
            return False, "spaCy installation timed out (may need manual intervention)"
    
    # Step 7: Verify spaCy is installed (check with the Python we used)
    if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
        # For py launcher, we need to check differently
        try:
            result = subprocess.run(
                ['py', '-3.13', '-c', 'import spacy'],
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_quick_timeout())
            )
            if result.returncode != 0:
                return False, "spaCy installation completed but import verification failed"
        except Exception:
            # Fallback: assume success if we can't verify
            pass
    else:
        # Temporarily switch to check import with the Python we used
        # Note: This might not work perfectly if Python 3.13 was used, but it's the best we can do
        if not check_import('spacy'):
            # If using Python 3.13, this check might fail because we're still in Python 3.14
            # So we do a subprocess check instead
            try:
                result = subprocess.run(
                    [python_executable, '-c', 'import spacy'],
                    capture_output=True,
                    text=True,
                    timeout=int(get_subprocess_quick_timeout())
                )
                if result.returncode != 0:
                    return False, "spaCy installation completed but import verification failed"
            except Exception:
                pass  # If we can't verify, assume success
    
    # Step 8: Download model (using the Python we used for installation)
    if verbose:
        print(f"  📥 Downloading spaCy model: {model_name}...")

    try:
        # Temporarily update sys.executable for model download
        if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
            # Use py launcher
            result = subprocess.run(
                ['py', '-3.13', '-m', 'spacy', 'download', model_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_install_timeout())
            )
        else:
            result = subprocess.run(
                [python_executable, '-m', 'spacy', 'download', model_name],
                check=True,
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_install_timeout())
            )
    except subprocess.CalledProcessError:
        return False, "spaCy installed but model download failed"
    
    # Step 9: Verify model can be loaded (using the Python we used)
    try:
        if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
            result = subprocess.run(
                ['py', '-3.13', '-c', f"import spacy; nlp = spacy.load('{model_name}'); print('OK')"],
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_default_timeout())
            )
            if result.returncode != 0:
                return False, "spaCy and model installed but verification failed"
        else:
            result = subprocess.run(
                [python_executable, '-c', f"import spacy; nlp = spacy.load('{model_name}'); print('OK')"],
                capture_output=True,
                text=True,
                timeout=int(get_subprocess_default_timeout())
            )
            if result.returncode != 0:
                return False, "spaCy and model installed but verification failed"
    except Exception:
        # If verification fails, assume success (model might be in different Python)
        pass
    
    install_end = datetime.now()
    install_duration = (install_end - install_start).total_seconds()
    
    # Log successful installation
    _installation_log.append({
        'type': 'spacy_full',
        'package_name': f'spaCy + {model_name}',
        'package_id': f'spacy-{model_name}',
        'install_method': install_method or 'pre-built wheel',
        'python_version': '3.13' if using_python313 else python_version,
        'status': 'success',
        'timestamp': install_start.isoformat(),
        'duration_seconds': install_duration,
        'platform': sys.platform
    })
    
    python_info = f"Python 3.13" if using_python313 else f"Python {python_version}"
    return True, f"spaCy and {model_name} installed successfully via {install_method or 'pre-built wheel'} using {python_info}"

def install_spacy_model(dry_run: bool = False, python_executable: str | None = None) -> bool:
    """
    Install spaCy English model
    
    Args:
        dry_run: If True, only print what would be run
        python_executable: Python executable to use (default: sys.executable)
    
    Returns:
        True if successful, False otherwise
    """
    if python_executable is None:
        python_executable = sys.executable
    
    model_name = 'en_core_web_sm'
    
    if dry_run:
        if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
            print(f"  [DRY RUN] Would run: py -3.13 -m spacy download {model_name}")
        else:
            print(f"  [DRY RUN] Would run: {python_executable} -m spacy download {model_name}")
        return True
    
    install_start = datetime.now()
    if isinstance(python_executable, str) and python_executable.startswith('py -3.13'):
        install_command = f"py -3.13 -m spacy download {model_name}"
        cmd = ['py', '-3.13', '-m', 'spacy', 'download', model_name]
    else:
        install_command = f"{python_executable} -m spacy download {model_name}"
        cmd = [python_executable, '-m', 'spacy', 'download', model_name]
    
    try:
        print(f"  Downloading spaCy model: {model_name}...")
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            timeout=int(get_subprocess_install_timeout())
        )
        
        install_end = datetime.now()
        install_duration = (install_end - install_start).total_seconds()
        
        # Try to get model location
        model_location = None
        try:
            import spacy
            nlp = spacy.load('en_core_web_sm')
            model_location = str(Path(nlp.path).parent) if hasattr(nlp, 'path') else 'spacy models directory'
        except Exception:
            pass
        
        print("  ✅ Successfully downloaded spaCy model")
        
        # Log the installation
        _installation_log.append({
            'type': 'spacy_model',
            'package_name': 'en_core_web_sm',
            'package_id': 'en_core_web_sm',
            'install_method': 'spacy download',
            'install_location': model_location or 'spacy models directory',
            'command': install_command,
            'status': 'success',
            'timestamp': install_start.isoformat(),
            'duration_seconds': install_duration,
            'platform': sys.platform
        })
        
        return True
    except subprocess.CalledProcessError as e:
        install_end = datetime.now()
        install_duration = (install_end - install_start).total_seconds()
        
        print("  ❌ Failed to download spaCy model")
        print(f"     Error: {e.stderr}")
        
        # Log the failure
        _installation_log.append({
            'type': 'spacy_model',
            'package_name': 'en_core_web_sm',
            'package_id': 'en_core_web_sm',
            'install_method': 'spacy download',
            'command': install_command,
            'status': 'failed',
            'error': e.stderr[:200] if e.stderr else str(e),
            'timestamp': install_start.isoformat(),
            'duration_seconds': install_duration,
            'platform': sys.platform
        })
        
        return False

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Setup dependencies for docs-management scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check dependencies only
  python setup_dependencies.py
  
  # Install required dependencies
  python setup_dependencies.py --install-required
  
  # Install all dependencies (required + optional)
  python setup_dependencies.py --install-all
        """
    )
    parser.add_argument(
        '--install-required',
        action='store_true',
        help='Install missing required dependencies'
    )
    parser.add_argument(
        '--install-all',
        action='store_true',
        help='Install all missing dependencies (required + optional)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be installed without actually installing'
    )
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Show detailed environment diagnostics'
    )
    
    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'install_required': args.install_required,
        'install_all': args.install_all,
        'dry_run': args.dry_run,
        'diagnose': args.diagnose
    })
    
    # Show environment info
    env_info = get_python_environment_info()
    logger.logger.info(f"Python: {env_info['python_version']} at {env_info['python_executable']}")
    if env_info['is_venv']:
        logger.logger.info(f"Virtual Environment: {env_info['venv_path']}")
    if env_info['pip_location']:
        match_status = "matches" if env_info['pip_python_match'] else "may not match"
        logger.logger.info(f"pip: {env_info['pip_location']} ({match_status})")
    
    # Show detailed diagnostics if requested
    if args.diagnose:
        print()
        print_environment_info(env_info, verbose=True)
        diagnosis = diagnose_environment(verbose=True)
        if diagnosis.get('other_pythons'):
            print("🔍 Other Python Installations Found:")
            print("=" * 60)
            for py_path in diagnosis['other_pythons'][:5]:
                print(f"  - {py_path}")
            print()
        if diagnosis.get('package_locations'):
            print("📦 Package Locations:")
            print("=" * 60)
            for pkg, loc in diagnosis['package_locations'].items():
                if loc:
                    print(f"  {pkg}: {loc}")
                else:
                    print(f"  {pkg}: Not installed")
            print()
    
    exit_code = 0
    try:
        # Required dependencies
        required_deps = {
            'yaml': 'pyyaml',
            'requests': 'requests',
            'bs4': 'beautifulsoup4',
            'markdownify': 'markdownify',
        }

        # Optional dependencies
        optional_deps = {
            'spacy': 'spacy',
            'yake': 'yake',
        }

        if not args.diagnose:
            print("🔍 Checking Dependencies...")
            print("=" * 60)
            print()
        
        # Check required dependencies
        print("📦 Required Dependencies:")
        missing_required = []
        for module, package in required_deps.items():
            if check_import(module):
                print(f"  ✅ {package:20s} ✓ Installed")
            else:
                print(f"  ❌ {package:20s} ✗ Missing")
                missing_required.append(package)
        print()
        
        # Check optional dependencies
        print("📦 Optional Dependencies:")
        missing_optional = []
        for module, package in optional_deps.items():
            if check_import(module):
                print(f"  ✅ {package:20s} ✓ Installed")
            else:
                print(f"  ⚠️  {package:20s} ✗ Missing (optional)")
                missing_optional.append(package)
        print()
        
        # Check spaCy model
        print("📦 spaCy Model:")
        if check_spacy_model():
            print("  ✅ en_core_web_sm ✓ Installed")
            spacy_model_missing = False
        else:
            print("  ⚠️  en_core_web_sm ✗ Missing (optional)")
            spacy_model_missing = True
        print()
        
        # Auto-install optional deps if missing (unless explicitly disabled)
        auto_install_optional = not args.dry_run and (missing_optional or spacy_model_missing)
        
        # Install if requested
        if args.install_required or args.install_all or auto_install_optional:
            if missing_required:
                print("📥 Installing Required Dependencies...")
                print("=" * 60)
                success = run_pip_install(missing_required, dry_run=args.dry_run)
                if not success and not args.dry_run:
                    print("\n❌ Failed to install required dependencies")
                    exit_code = 1
                    raise SystemExit(1)
                print()
            
            if args.install_all or auto_install_optional:
                if missing_optional:
                    if auto_install_optional and not args.install_all:
                        print("📥 Auto-installing Optional Dependencies (for better keyword extraction)...")
                    else:
                        print("📥 Installing Optional Dependencies...")
                    print("=" * 60)
                    
                    # Check if spaCy is in missing_optional and build tools are needed
                    if 'spacy' in missing_optional and not check_build_tools_installed():
                        print("  🔍 spaCy requires C++ build tools - checking if available...")
                        build_success, build_instructions, build_msg = try_install_build_tools(
                            auto_install=(args.install_all or auto_install_optional) and not args.dry_run,
                            verbose=True
                        )
                        if build_success:
                            print("  ✅ Build tools available - spaCy installation should succeed")
                        else:
                            print(f"  ⚠️  {build_msg}")
                            if build_instructions.get('auto'):
                                print("  💡 Build tools can be auto-installed:")
                                if sys.platform == 'win32':
                                    print(f"     Run: {' '.join(build_instructions['command'])}")
                                else:
                                    print(f"     Note: Requires sudo/admin privileges")
                                    print(f"     Run: {' '.join(build_instructions['command'])}")
                        print()
                    
                    # Install individually so one failure doesn't block others
                    # This is especially important on Windows where C++ compiler may be missing
                    success = run_pip_install(missing_optional, dry_run=args.dry_run, install_individually=True)
                    if not success and not args.dry_run:
                        print("\n⚠️  Failed to install some optional dependencies (will use fallbacks)")
                        print("   This is normal on Windows without C++ build tools")
                        print("   Scripts will work with reduced functionality")
                    print()
                
                # Only try to install spaCy model if spaCy package is actually installed
                if spacy_model_missing:
                    if check_import('spacy'):
                        if auto_install_optional and not args.install_all:
                            print("📥 Auto-installing spaCy Model (for better stop word filtering)...")
                        else:
                            print("📥 Installing spaCy Model...")
                        print("=" * 60)
                        success = install_spacy_model(dry_run=args.dry_run)
                        if not success and not args.dry_run:
                            print("\n⚠️  Failed to install spaCy model (will use fallback stop words)")
                        print()
                    else:
                        if not args.dry_run:
                            print("⚠️  spaCy package not installed, skipping model download")
                            print("   Install spaCy first, then run: python -m spacy download en_core_web_sm")
                        print()
        
        # Final summary with detailed reporting
        print("📊 Final Status:")
        print("=" * 60)
        
        all_required_ok = len(missing_required) == 0
        all_optional_ok = len(missing_optional) == 0 and not spacy_model_missing
    
        if all_required_ok:
            print("  ✅ All required dependencies are installed")
        else:
            print("  ❌ Missing required dependencies:")
            for pkg in missing_required:
                print(f"     - {pkg}")
            print("\n  Install with:")
            print(f"     python setup_dependencies.py --install-required")
            exit_code = 1
            raise SystemExit(1)
        
        # Detailed optional dependency reporting
        if all_optional_ok:
            print("  ✅ All optional dependencies are installed")
            print("     (spaCy, YAKE, and spaCy model available)")
        else:
            print("  ⚠️  Optional dependencies status:")
            
            # Check what's actually available now (after potential installation)
            yake_now = check_import('yake')
            spacy_now = check_import('spacy')
            spacy_model_now = check_spacy_model() if spacy_now else False
            
            if not yake_now:
                print("     ❌ YAKE - Missing")
                print("        Install: pip install yake")
                pkg_mgr = detect_package_manager()
                if pkg_mgr:
                    print(f"        (Package manager detected: {pkg_mgr})")
            else:
                print("     ✅ YAKE - Installed")
            
            if not spacy_now:
                print("     ❌ spaCy - Missing (requires C++ build tools)")
                print("        Install: pip install spacy")
                build_instructions = get_build_tools_install_instructions()
                if build_instructions['auto']:
                    print(f"        Build tools can be installed via: {build_instructions['command']}")
                print("        Manual installation:")
                for line in build_instructions['manual']:
                    print(f"          {line}")
            else:
                print("     ✅ spaCy - Installed")
                if not spacy_model_now:
                    print("     ⚠️  spaCy model - Missing")
                    print("        Install: python -m spacy download en_core_web_sm")
                else:
                    print("     ✅ spaCy model - Installed")
            
            print("\n  Note: Scripts work fine with fallbacks if optional deps are missing")
            print("        Enhanced features (YAKE keyword extraction, spaCy stop words) require these")
            
            if missing_optional or spacy_model_missing:
                print("\n  Auto-install with:")
                print(f"     python setup_dependencies.py --install-all")
        
        print("\n✅ Environment is ready!")
        
        # Print installation report if any auto-installations occurred
        if _installation_log:
            print_installation_report()
        
        # Log summary
        summary = {
            'required_deps_ok': all_required_ok,
            'optional_deps_ok': all_optional_ok,
            'auto_installations': len(_installation_log)
        }
        
        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        # Re-raise SystemExit to preserve exit code
        raise
    except Exception as e:
        logger.log_error("Fatal error in setup_dependencies", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

