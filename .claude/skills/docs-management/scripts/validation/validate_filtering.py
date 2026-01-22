#!/usr/bin/env python3
"""
Validate filtering.yaml for duplicates and structural integrity.

This script checks the filtering configuration for:
- Duplicate terms across all categories
- Valid YAML syntax
- Category statistics

Exit codes:
  0 - Validation passed (no duplicates, valid YAML)
  1 - Validation failed (duplicates found or invalid YAML)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from collections import defaultdict

try:
    import yaml
except ImportError:
    print("ERROR: pyyaml not installed. Run: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

def validate_filtering_yaml(config_path: Path) -> bool:
    """
    Validate filtering.yaml for duplicates and structure.

    Args:
        config_path: Path to filtering.yaml

    Returns:
        True if validation passed, False otherwise
    """
    # Load YAML
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {config_path}", file=sys.stderr)
        return False
    except yaml.YAMLError as e:
        print(f"ERROR: Invalid YAML syntax in {config_path}:", file=sys.stderr)
        print(f"  {e}", file=sys.stderr)
        return False

    if not isinstance(config, dict):
        print("ERROR: filtering.yaml must contain a dictionary at root level", file=sys.stderr)
        return False

    # Track all terms and where they appear
    term_locations = defaultdict(list)
    category_stats = {}

    # Scan all categories
    for category_name, terms in config.items():
        if not isinstance(terms, list):
            print(f"WARNING: Category '{category_name}' is not a list, skipping", file=sys.stderr)
            continue

        category_stats[category_name] = len(terms)

        for term in terms:
            term_str = str(term).lower().strip()
            term_locations[term_str].append(category_name)

    # Find duplicates
    duplicates = {term: locations for term, locations in term_locations.items()
                  if len(locations) > 1}

    # Report results
    print("=" * 70)
    print("filtering.yaml Validation Report")
    print("=" * 70)
    print()

    # Category statistics
    print("Category Statistics:")
    print("-" * 70)
    total_terms = 0
    for category, count in sorted(category_stats.items()):
        print(f"  {category:30s} {count:4d} terms")
        total_terms += count
    print("-" * 70)
    print(f"  {'TOTAL':30s} {total_terms:4d} terms")
    print()

    # Duplicate report
    if duplicates:
        print("DUPLICATES FOUND:")
        print("-" * 70)
        for term, locations in sorted(duplicates.items()):
            print(f"  '{term}' appears in: {', '.join(locations)}")
        print("-" * 70)
        print(f"  Total duplicates: {len(duplicates)}")
        print()
        print("VALIDATION FAILED: Duplicates detected")
        print("=" * 70)
        return False
    else:
        print("VALIDATION PASSED: No duplicates found")
        print("=" * 70)
        return True

def main() -> None:
    """Main entry point."""
    # Determine script location
    script_dir = Path(__file__).parent
    skill_root = script_dir.parent
    config_path = skill_root / "config" / "filtering.yaml"

    print(f"Validating: {config_path}")
    print()

    success = validate_filtering_yaml(config_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
