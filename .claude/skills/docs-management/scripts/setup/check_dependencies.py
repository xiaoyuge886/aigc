#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_dependencies.py - Check Python dependencies for docs-management scripts

Checks for required and optional dependencies, provides installation instructions.
Can be run by agents to verify environment setup.

Usage:
    python check_dependencies.py
    python check_dependencies.py --install-optional  # Suggests installing optional deps
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import subprocess
from typing import Any

from utils.script_utils import configure_utf8_output, suppress_pydantic_v1_warning
configure_utf8_output()
suppress_pydantic_v1_warning()  # Must be called before spacy import

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="diagnostics")

def check_import(module_name: str, package_name: str = None) -> tuple[bool, str]:
    """
    Check if a module can be imported
    
    Args:
        module_name: Name of module to import
        package_name: Name of package (for pip install), defaults to module_name
    
    Returns:
        Tuple of (is_available, error_message)
    """
    if package_name is None:
        package_name = module_name
    
    try:
        mod = __import__(module_name)
        # Try to get location if available
        if hasattr(mod, '__file__'):
            mod_path = Path(mod.__file__).parent
            return True, f"Found at {mod_path}"
        return True, ""
    except ImportError:
        return False, f"Module '{module_name}' not found"
    except Exception as e:
        # Catch other errors (e.g., type inference issues on Python 3.14+)
        return False, f"Module '{module_name}' failed to import: {e}"

def check_spacy_model() -> tuple[bool, str, dict[str, Any]]:
    """
    Check if spaCy English model is installed using multiple verification methods
    
    Returns:
        Tuple of (is_available, error_message, diagnostic_info)
    """
    diagnostic_info = {
        'spacy_importable': False,
        'spacy_version': None,
        'model_loadable': False,
        'model_location': None,
        'pip_list_has_spacy': False,
        'pip_list_has_model': False,
    }
    
    # Method 1: Try direct import
    try:
        import spacy
        diagnostic_info['spacy_importable'] = True
        try:
            diagnostic_info['spacy_version'] = spacy.__version__
        except Exception:
            pass
    except ImportError:
        # Check if spaCy is installed via pip list (might be in different Python)
        try:
            from config_helpers import get_subprocess_default_timeout
            timeout = get_subprocess_default_timeout()
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'spacy' in output:
                    diagnostic_info['pip_list_has_spacy'] = True
        except Exception:
            pass
        return False, "spaCy not installed (cannot import)", diagnostic_info
    except Exception as e:
        # Catch other errors (e.g., type inference issues on Python 3.14+)
        diagnostic_info['import_error'] = str(e)
        return False, f"spaCy failed to import: {e}", diagnostic_info
    
    # Method 2: Try to load the model
    try:
        nlp = spacy.load('en_core_web_sm')
        diagnostic_info['model_loadable'] = True
        try:
            # Try to get model location
            if hasattr(nlp, 'path'):
                diagnostic_info['model_location'] = str(nlp.path)
            elif hasattr(nlp, '_path'):
                diagnostic_info['model_location'] = str(nlp._path)
        except Exception:
            pass
        return True, "", diagnostic_info
    except OSError as e:
        # Model not found - check if it's listed in pip
        try:
            from config_helpers import get_subprocess_default_timeout
            timeout = get_subprocess_default_timeout()
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'list'],
                capture_output=True,
                text=True,
                timeout=timeout
            )
            if result.returncode == 0:
                output = result.stdout.lower()
                if 'en-core-web-sm' in output or 'en_core_web_sm' in output:
                    diagnostic_info['pip_list_has_model'] = True
        except Exception:
            pass
        
        error_msg = f"Model 'en_core_web_sm' not found"
        if 'en-core-web-sm' in str(e).lower() or 'en_core_web_sm' in str(e).lower():
            error_msg += " (package may be installed but model not downloaded)"
        return False, error_msg, diagnostic_info
    except Exception as e:
        return False, f"Error loading model: {str(e)}", diagnostic_info

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Check dependencies for docs-management scripts',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check all dependencies
  python check_dependencies.py
  
  # Check and suggest installing optional dependencies
  python check_dependencies.py --install-optional
        """
    )
    parser.add_argument(
        '--install-optional',
        action='store_true',
        help='Show installation commands for missing optional dependencies'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output results as JSON'
    )
    parser.add_argument(
        '--diagnose',
        action='store_true',
        help='Show detailed environment diagnostics'
    )
    
    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'install_optional': args.install_optional,
        'json': args.json,
        'diagnose': args.diagnose
    })
    
    # Import environment detection functions
    try:
        from setup_dependencies import (
            get_python_environment_info,
            diagnose_environment,
            print_environment_info,
            detect_python_for_spacy,
            check_compiler_accessible,
            locate_vcvarsall_bat,
            get_effective_spacy_status,
        )
        env_info_available = True
    except ImportError:
        env_info_available = False
        if args.diagnose:
            print("⚠️  Warning: Could not import environment detection functions")
            print("   Make sure setup_dependencies.py is in the same directory")
    
    # Show environment info if requested or if diagnosing
    if args.diagnose and env_info_available:
        print()
        print_environment_info(verbose=True)
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
    elif env_info_available:
        # Always show basic environment info
        env_info = get_python_environment_info()
        logger.logger.info(f"Python: {env_info['python_version']} at {env_info['python_executable']}")
        if env_info['is_venv']:
            logger.logger.info(f"Virtual Environment: {env_info['venv_path']}")
    
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
        
        results = {
            'required': {},
            'optional': {},
            'spacy_model': None,
            'all_required': True,
            'all_optional': True,
        }
        
        # Check required dependencies
        print("📦 Checking Required Dependencies:")
        print("=" * 60)
        all_required_ok = True
        
        for module, package in required_deps.items():
            available, error = check_import(module, package)
            results['required'][package] = available
            status = "✅" if available else "❌"
            print(f"  {status} {package:20s}", end="")
            if available:
                print(" ✓ Installed")
            else:
                print(f" ✗ Missing: {error}")
                all_required_ok = False
                if not args.json:
                    print(f"      Install with: pip install {package}")
        
        results['all_required'] = all_required_ok
        print()
        
        # Check optional dependencies
        print("📦 Checking Optional Dependencies (Recommended):")
        print("=" * 60)
        all_optional_ok = True
        
        # Check Python version compatibility for spaCy
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        python313_available = None
        if env_info_available:
            try:
                python313_available = detect_python_for_spacy()
            except Exception:
                pass
        
        # Check effective spaCy status first (before checking current interpreter)
        effective_spacy_precheck = None
        if env_info_available:
            try:
                effective_spacy_precheck = get_effective_spacy_status()
            except Exception:
                pass
        
        for module, package in optional_deps.items():
            available, error = check_import(module, package)
            results['optional'][package] = available
            
            # Special handling for spaCy - show effective status if available
            if package == 'spacy' and effective_spacy_precheck:
                effective_available = effective_spacy_precheck.get('effective_available', False)
                effective_model_available = effective_spacy_precheck.get('effective_model_available', False)
                effective_python = effective_spacy_precheck.get('effective_python')
                
                if effective_available and effective_model_available:
                    status = "✅"
                    print(f"  {status} {package:20s}", end="")
                    if available:
                        print(" ✓ Installed (current interpreter)")
                    else:
                        print(" ✓ Available (effective)")
                        if effective_python and effective_python != sys.executable:
                            print(f"      Available via: {effective_python}")
                    # Don't mark as missing if effective is available
                    if not available:
                        all_optional_ok = False  # Still mark as not OK for current interpreter
                else:
                    status = "⚠️ " if available else "⚠️ "
                    print(f"  {status} {package:20s}", end="")
                    if available:
                        print(" ✓ Installed")
                    else:
                        print(f" ✗ Missing (optional)")
                        all_optional_ok = False
                        if not args.json:
                            print(f"      Install with: pip install {package}")
                            if python_version >= '3.14' or python_version < '3.7':
                                print(f"      ⚠️  Note: spaCy requires Python 3.7-3.13, but Python {python_version} is being used")
                                if python313_available:
                                    print(f"      ✅ Python 3.13 is available - will be used automatically for spaCy")
                                    print(f"      Recommended: {'py -3.13' if sys.platform == 'win32' else 'python3.13'} -m pip install spacy")
                                else:
                                    print(f"      ❌ Python 3.13 not found - install it first:")
                                    if sys.platform == 'win32':
                                        print(f"         winget install --id Python.Python.3.13 -e --source winget")
                                    elif sys.platform == 'darwin':
                                        print(f"         brew install python@3.13")
                                    else:
                                        print(f"         sudo apt install python3.13 python3.13-venv python3.13-dev")
            else:
                status = "✅" if available else "⚠️ "
                print(f"  {status} {package:20s}", end="")
                if available:
                    print(" ✓ Installed")
                else:
                    print(f" ✗ Missing (optional)")
                    all_optional_ok = False
                    if not args.json:
                        print(f"      Install with: pip install {package}")
        
        results['all_optional'] = all_optional_ok  # will be refined after spaCy effective status
        results['python_version'] = python_version
        results['python313_available'] = python313_available is not None
        print()
        
        # Check spaCy model (with enhanced detection across interpreters)
        print("📦 Checking spaCy Model:")
        print("=" * 60)
        model_available, model_error, model_diag = check_spacy_model()
        results['spacy_model'] = model_available
        results['spacy_diagnostics'] = model_diag

        effective_spacy = get_effective_spacy_status()
        results['spacy_effective'] = effective_spacy

        effective_available = effective_spacy.get('effective_available', False)
        effective_model_available = effective_spacy.get('effective_model_available', False)
        effective_python = effective_spacy.get('effective_python')

        # Report per-interpreter and effective status
        status = "✅" if effective_model_available else "⚠️ "
        print(f"  {status} en_core_web_sm (effective)", end="")
        if effective_model_available:
            print(" ✓ Installed")
            loc = effective_spacy.get('model_location')
            if loc and not args.json:
                print(f"      Location: {loc}")
        else:
            print(" ✗ Missing (optional)")
            if not args.json and model_error:
                print(f"      Error (current interpreter): {model_error}")
        print()

        # Summary
        print("📊 Summary:")
        print("=" * 60)

        if all_required_ok:
            print("  ✅ All required dependencies are installed")
        else:
            print("  ❌ Some required dependencies are missing")
            print("\n  Install missing required dependencies:")
            missing_required = [pkg for pkg, avail in results['required'].items() if not avail]
            print(f"     pip install {' '.join(missing_required)}")
        
        # Determine effective optional status (for human and JSON summary):
        yake_available = results['optional'].get('yake', False)
        effective_optional_ok = bool(yake_available and effective_model_available)
        results['all_optional'] = effective_optional_ok

        if all_required_ok and effective_optional_ok:
            print("  ✅ All optional dependencies are installed")
            print("     (YAKE and spaCy+model available via at least one Python interpreter)")
        else:
            print("  ⚠️  Optional dependencies status:")

            # Show detailed status for each optional dependency
            spacy_available_current = results['optional'].get('spacy', False)

            if not yake_available:
                print("     ❌ YAKE - Missing")
                print("        Install: pip install yake")
            else:
                print("     ✅ YAKE - Installed")

            # spaCy: current vs effective
            if effective_available:
                if spacy_available_current:
                    print("     ✅ spaCy (current interpreter) - Installed")
                else:
                    if effective_python and effective_python != sys.executable:
                        print(f"     ✅ spaCy (effective) - Available via {effective_python}")
                        print(f"     ⚠️  spaCy (current interpreter) - Not importable (will use {effective_python} automatically)")
                    else:
                        print("     ⚠️  spaCy (current interpreter) - Not importable")
                if effective_python and effective_python != sys.executable and spacy_available_current:
                    print(f"     ✅ spaCy (effective) - Also available via {effective_python}")
                if effective_model_available:
                    loc = effective_spacy.get('model_location')
                    if loc:
                        print(f"        Model location: {loc}")
                else:
                    print("     ⚠️  spaCy model - Not loadable in any interpreter")
            else:
                print("     ❌ spaCy - Missing in all supported interpreters")

                # Check Python version compatibility
                if python_version >= '3.14' or python_version < '3.7':
                    print(f"        ⚠️  spaCy requires Python 3.7-3.13, but Python {python_version} is being used")
                    if python313_available:
                        print(f"        ✅ Python 3.13 is available - will be used automatically")
                        python_cmd = 'py -3.13' if sys.platform == 'win32' else 'python3.13'
                        print(f"        Recommended: {python_cmd} -m pip install spacy")
                        print(f"        (Pre-built wheels available, no compilation needed)")
                    else:
                        print(f"        ❌ Python 3.13 not found - install it first:")
                        if sys.platform == 'win32':
                            print(f"           winget install --id Python.Python.3.13 -e --source winget")
                        elif sys.platform == 'darwin':
                            print(f"           brew install python@3.13")
                        else:
                            print(f"           sudo apt install python3.13 python3.13-venv python3.13-dev")
                    print()
                    print(f"        Alternative: Install spaCy with current Python (requires C++ build tools)")
                else:
                    print(f"        Install: {sys.executable} -m pip install spacy")

                # Import setup_dependencies for build tools instructions
                try:
                    from setup_dependencies import (
                        get_build_tools_install_instructions, detect_package_manager,
                        check_compiler_accessible, locate_vcvarsall_bat
                    )

                    # Check compiler accessibility
                    compiler_accessible = check_compiler_accessible()
                    vcvarsall_path = locate_vcvarsall_bat() if sys.platform == 'win32' else None

                    if not compiler_accessible:
                        build_instructions = get_build_tools_install_instructions()
                        pkg_mgr = detect_package_manager()
                        if build_instructions['auto'] and pkg_mgr:
                            print(f"        Build tools auto-install via {pkg_mgr}:")
                            print(f"          {build_instructions['command']}")
                        if sys.platform == 'win32' and vcvarsall_path:
                            print(f"        ✅ VS Build Tools detected at: {vcvarsall_path}")
                            print(f"        The script will automatically configure VS environment")
                        print("        Manual installation:")
                        for line in build_instructions['manual']:
                            print(f"          {line}")
                except Exception:
                    print("        Windows: Install Visual Studio Build Tools")
                    print("        macOS: xcode-select --install")
                    print("        Linux: sudo apt install build-essential")

                # Show diagnostic info if available
                if env_info_available:
                    env_info = get_python_environment_info()
                    if not env_info['pip_python_match']:
                        print(f"        ⚠️  Warning: pip may not match current Python")
                        print(f"        Current Python: {env_info['python_executable']}")
                        print(f"        pip Location: {env_info['pip_location'] or 'Not found'}")
            
            print("\n  Note: Scripts work fine with fallbacks if optional deps are missing")
            print("        Enhanced features (YAKE keyword extraction, spaCy stop words) require these")
            
            if args.install_optional:
                missing_optional = [pkg for pkg, avail in results['optional'].items() if not avail]
                if missing_optional:
                    print("\n  Quick install all optional dependencies:")
                    print(f"     {sys.executable} -m pip install {' '.join(missing_optional)}")
                    print(f"     Or: python setup_dependencies.py --install-all")
            
            if args.diagnose and env_info_available:
                print("\n  💡 For more detailed diagnostics, run:")
                print(f"     python check_dependencies.py --diagnose")
        
        print()
        
        # Exit code
        if args.json:
            import json
            print(json.dumps(results, indent=2))
        
        summary = {
            'required_ok': all_required_ok,
            'optional_ok': effective_optional_ok,
            'missing_required': len([pkg for pkg, avail in results['required'].items() if not avail]),
            'missing_optional': len([pkg for pkg, avail in results['optional'].items() if not avail])
        }
        
        logger.end(exit_code=0 if all_required_ok else 1, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in check_dependencies", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

