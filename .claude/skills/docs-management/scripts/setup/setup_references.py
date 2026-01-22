#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
setup_references.py - Setup references directory structure

Creates the base directory for canonical documentation storage (default:
.claude/skills/docs-management/canonical from config) and initializes index.yaml if needed.

Usage:
    # Uses default base-dir from config (typically .claude/skills/docs-management/canonical)
    python setup_references.py
    
    # Custom base directory
    python setup_references.py --base-dir custom/references

Dependencies:
    None (standard library only)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from utils.script_utils import configure_utf8_output

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="diagnostics")

# Import path_config for default base_dir
try:
    from path_config import get_base_dir, get_index_path
    from utils.common_paths import find_repo_root
except ImportError:
    def get_base_dir(start=None):
        from utils.common_paths import find_repo_root
        repo_root = find_repo_root(start)
        return repo_root / ".claude" / "references"
    def get_index_path(base_dir=None):
        if base_dir is None:
            base_dir = get_base_dir()
        return base_dir / "index.yaml"
    def find_repo_root(start=None):
        current = Path.cwd() if start is None else Path(start)
        repo_root = current
        while repo_root != repo_root.parent:
            if (repo_root / '.git').exists():
                return repo_root
            repo_root = repo_root.parent
        return current

def setup_references(base_dir: Path) -> bool:
    """
    Setup references directory structure
    
    Args:
        base_dir: Base directory to setup
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create directory
        base_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Directory ready: {base_dir}")
        
        # Create index.yaml if doesn't exist
        index_file = get_index_path(base_dir)
        if not index_file.exists():
            index_file.write_text("{}\n", encoding='utf-8')
            print(f"✅ Created {index_file}")
        else:
            print(f"ℹ️  {index_file} already exists")
        
        return True
    except Exception as e:
        print(f"❌ Error setting up references: {e}")
        return False

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Setup references directory structure',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Setup default directory
  python setup_references.py
  
  # Custom base directory
  python setup_references.py --base-dir custom/references
        """
    )
    
    from cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    
    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'base_dir': args.base_dir
    })
    
    exit_code = 0
    try:
        # Resolve base directory using cli_utils helper
        base_dir = resolve_base_dir_from_args(args)
        
        success = setup_references(base_dir)
        exit_code = 0 if success else 1
        
        summary = {'success': success}
        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in setup_references", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

