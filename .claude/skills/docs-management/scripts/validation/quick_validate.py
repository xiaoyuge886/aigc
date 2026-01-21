#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
quick_validate.py - Quick validation of scraped source

Combines file count verification, sample file validation, and directory structure checks.

Usage:
    python quick_validate.py --output docs-claude-com/docs --expected 95
    python quick_validate.py --output docs-claude-com/api

Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse

from utils.script_utils import configure_utf8_output, ensure_yaml_installed
configure_utf8_output()

yaml = ensure_yaml_installed()

def quick_validate(output_dir: Path, expected_count: int | None = None) -> bool:
    """
    Quick validation combining multiple checks
    
    Args:
        output_dir: Directory to validate
        expected_count: Expected number of markdown files
    
    Returns:
        True if validation passes, False otherwise
    """
    print(f"\n🔍 Quick Validation: {output_dir}\n")
    
    if not output_dir.exists():
        print(f"❌ Directory does not exist: {output_dir}")
        return False
    
    # 1. File count
    md_files = list(output_dir.glob("**/*.md"))
    actual_count = len(md_files)
    
    print(f"📊 File Count: {actual_count}")
    if expected_count:
        if actual_count == expected_count:
            print(f"   ✅ Matches expected: {expected_count}")
        else:
            print(f"   ❌ Expected: {expected_count}, Got: {actual_count}")
            return False
    else:
        print(f"   ℹ️  No expected count provided")
    
    if actual_count == 0:
        print(f"   ⚠️  No markdown files found")
        return False
    
    # 2. Sample files validation
    sample_files = md_files[:5] if len(md_files) >= 5 else md_files
    print(f"\n📄 Sample Files ({len(sample_files)} checked):")
    
    valid_samples = 0
    issues = []
    
    for f in sample_files:
        try:
            content = f.read_text(encoding='utf-8')
            
            # Check frontmatter
            if not content.startswith('---'):
                issues.append(f"{f.name}: Missing frontmatter")
                print(f"   ❌ {f.name} (no frontmatter)")
                continue
            
            # Parse frontmatter
            frontmatter_end = content.find('---', 3)
            if frontmatter_end == -1:
                issues.append(f"{f.name}: Invalid frontmatter")
                print(f"   ❌ {f.name} (invalid frontmatter)")
                continue
            
            frontmatter_text = content[3:frontmatter_end].strip()
            try:
                frontmatter = yaml.safe_load(frontmatter_text)
            except yaml.YAMLError as e:
                issues.append(f"{f.name}: YAML parse error: {e}")
                print(f"   ❌ {f.name} (YAML error)")
                continue
            
            # Check required fields
            required = ['source_url', 'last_fetched', 'content_hash']
            missing = [field for field in required if field not in frontmatter]
            if missing:
                issues.append(f"{f.name}: Missing fields {missing}")
                print(f"   ❌ {f.name} (missing: {', '.join(missing)})")
                continue
            
            # Check content quality (basic)
            body = content[frontmatter_end + 3:].strip()
            if len(body) < 50:  # Suspiciously short
                issues.append(f"{f.name}: Suspiciously short content ({len(body)} chars)")
                print(f"   ⚠️  {f.name} (very short content)")
            else:
                valid_samples += 1
                print(f"   ✅ {f.name}")
                
        except Exception as e:
            issues.append(f"{f.name}: Error reading file: {e}")
            print(f"   ❌ {f.name} (error: {e})")
    
    # 3. Directory structure check
    print(f"\n📁 Directory Structure:")
    top_level_dirs = [d for d in output_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
    if top_level_dirs:
        for d in sorted(top_level_dirs):
            sub_md_count = len(list(d.glob("**/*.md")))
            print(f"   {d.name}/ ({sub_md_count} files)")
    else:
        print(f"   (flat structure)")
    
    # Summary
    print(f"\n{'='*60}")
    if valid_samples == len(sample_files) and (expected_count is None or actual_count == expected_count):
        print(f"✅ Quick validation PASSED")
        print(f"   Files: {actual_count}")
        print(f"   Valid samples: {valid_samples}/{len(sample_files)}")
        return True
    else:
        print(f"❌ Quick validation FAILED")
        if valid_samples < len(sample_files):
            print(f"   Only {valid_samples}/{len(sample_files)} samples valid")
        if expected_count and actual_count != expected_count:
            print(f"   File count mismatch: {actual_count} != {expected_count}")
        if issues:
            print(f"\n   Issues found:")
            for issue in issues[:10]:  # Limit to first 10
                print(f"      - {issue}")
            if len(issues) > 10:
                print(f"      ... and {len(issues) - 10} more")
        return False

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Quick validation of scraped source',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Validate with expected count
  python quick_validate.py --output docs-claude-com/docs --expected 95
  
  # Validate without expected count
  python quick_validate.py --output docs-claude-com/api
  
  # Custom base directory
  python quick_validate.py --output docs-claude-com/docs --base-dir custom/references
        """
    )
    
    parser.add_argument('--output', required=True,
                       help='Output directory to validate (relative to base-dir)')
    parser.add_argument('--expected', type=int,
                       help='Expected file count for validation')
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    add_base_dir_argument(parser)
    
    args = parser.parse_args()
    
    # Resolve base directory using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)
    output_dir = base_dir / args.output
    
    success = quick_validate(output_dir, args.expected)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

