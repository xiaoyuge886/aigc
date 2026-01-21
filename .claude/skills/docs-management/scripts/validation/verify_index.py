#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verify_index.py - Verify index.yaml integrity

Checks index.yaml for missing fields, invalid entries, and optionally verifies files exist.

Usage:
    python verify_index.py
    python verify_index.py --check-files
    python verify_index.py --base-dir custom/references

Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
from typing import Dict

from utils.script_utils import configure_utf8_output

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="diagnostics")

from utils.script_utils import ensure_yaml_installed
yaml = ensure_yaml_installed()

# Import path_config for default base_dir
try:
    from path_config import get_base_dir, get_index_path
except ImportError:
    # Fallback if path_config not available
    def get_base_dir(start=None):
        from utils.common_paths import find_repo_root
        repo_root = find_repo_root(start)
        return repo_root / ".claude" / "references"
    def get_index_path(base_dir=None):
        if base_dir is None:
            base_dir = get_base_dir()
        return base_dir / "index.yaml"

# Import index_manager for large file support
try:
    from management.index_manager import IndexManager
except ImportError:
    IndexManager = None

def verify_index(index_path: Path, base_dir: Path, check_files: bool = False) -> Dict:
    """
    Verify index.yaml integrity
    
    Args:
        index_path: Path to index.yaml
        base_dir: Base directory for file existence checks
        check_files: If True, verify files exist
    
    Returns:
        Dict with 'passed', 'issues', 'entry_count'
    """
    if not index_path.exists():
        return {
            'passed': False,
            'issues': [f'index.yaml does not exist: {index_path}'],
            'entry_count': 0
        }
    
    # Use index_manager if available (handles large files)
    if IndexManager:
        try:
            manager = IndexManager(base_dir)
            index = manager.load_all()
        except Exception as e:
            return {
                'passed': False,
                'issues': [f'Error reading index.yaml: {e}'],
                'entry_count': 0
            }
    else:
        # Fallback to original implementation
        try:
            with open(index_path, 'r', encoding='utf-8') as f:
                index = yaml.safe_load(f) or {}
        except Exception as e:
            return {
                'passed': False,
                'issues': [f'Error reading index.yaml: {e}'],
                'entry_count': 0
            }
    
    issues = []
    entry_count = len(index)
    
    # Check each entry
    for doc_id, metadata in index.items():
        if not isinstance(metadata, dict):
            issues.append(f"Invalid metadata for {doc_id}: not a dict")
            continue
        
        # Check required fields
        required = ['path', 'url', 'hash', 'last_fetched']
        missing = [f for f in required if f not in metadata]
        if missing:
            issues.append(f"Missing fields {missing} for {doc_id}")
            continue
        
        # Check file exists if requested
        if check_files:
            file_path = base_dir / metadata['path']
            if not file_path.exists():
                issues.append(f"File not found: {metadata['path']} (doc_id: {doc_id})")
    
    return {
        'passed': len(issues) == 0,
        'issues': issues,
        'entry_count': entry_count
    }

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Verify index.yaml integrity',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic verification (check structure and required fields)
  python verify_index.py
  
  # Verify files exist
  python verify_index.py --check-files
  
  # Custom base directory
  python verify_index.py --base-dir custom/references
        """
    )
    
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    parser.add_argument(
        '--check-files',
        action='store_true',
        help='Verify files exist',
    )
    parser.add_argument(
        '--summary-json',
        action='store_true',
        help='Also output a machine-readable JSON summary to stdout',
    )
    
    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'base_dir': args.base_dir,
        'check_files': args.check_files
    })
    
    exit_code = 0
    try:
        # Resolve base directory using cli_utils helper
        base_dir = resolve_base_dir_from_args(args)
        index_path = get_index_path(base_dir)
        
        with logger.time_operation('verify_index'):
            result = verify_index(index_path, base_dir, args.check_files)
        
        print(f"\n📋 Index Verification: {index_path}")
        print(f"   Entries: {result['entry_count']}")
        
        if result['passed']:
            print(f"   ✅ All checks passed")
            if args.check_files:
                print(f"   ✅ All files exist")
            exit_code = 0
        else:
            print(f"   ❌ Issues found: {len(result['issues'])}")
            for issue in result['issues'][:20]:  # Show first 20
                print(f"      - {issue}")
            if len(result['issues']) > 20:
                print(f"      ... and {len(result['issues']) - 20} more")
            exit_code = 1

        logger.track_metric('entry_count', result['entry_count'])
        logger.track_metric('issues_count', len(result['issues']))

        summary = {
            'passed': result['passed'],
            'entry_count': result['entry_count'],
            'issues_count': len(result['issues']),
            'check_files': args.check_files,
        }

        if args.summary_json:
            import json
            print()
            print(json.dumps(summary, indent=2))

        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in verify_index", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

