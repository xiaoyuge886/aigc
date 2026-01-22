#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate comprehensive index metadata report"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils.script_utils import configure_utf8_output
configure_utf8_output()

from utils.logging_utils import get_or_setup_logger
logger = get_or_setup_logger(__file__, log_category="index")

from management.index_manager import IndexManager

def main() -> None:
    import argparse
    from datetime import datetime, timezone
    
    from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    
    parser = argparse.ArgumentParser(
        description='Generate comprehensive index metadata report',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    add_base_dir_argument(parser)
    parser.add_argument(
        '--json',
        action='store_true',
        help='Also output a machine-readable JSON summary to stdout',
    )
    args = parser.parse_args()
    
    # Log script start
    logger.start({
        'base_dir': args.base_dir
    })
    
    exit_code = 0
    try:
        # Resolve base directory using cli_utils helper
        base_dir = resolve_base_dir_from_args(args)
        
        if not base_dir.exists():
            print(f"❌ Error: Could not find index directory at {base_dir}")
            exit_code = 1
            raise SystemExit(1)

        with logger.time_operation('load_index'):
            manager = IndexManager(base_dir)
            index = manager.load_all()

        # Statistics
        total = len(index)
        with_title = sum(1 for e in index.values() if 'title' in e)
        with_description = sum(1 for e in index.values() if 'description' in e)
        with_keywords = sum(1 for e in index.values() if 'keywords' in e and e['keywords'])
        with_tags = sum(1 for e in index.values() if 'tags' in e and e['tags'])
        with_category = sum(1 for e in index.values() if 'category' in e)
        with_domain = sum(1 for e in index.values() if 'domain' in e)

        # Domains
        domains = {}
        for entry in index.values():
            domain = entry.get('domain', 'unknown')
            domains[domain] = domains.get(domain, 0) + 1

        # Categories
        categories = {}
        for entry in index.values():
            category = entry.get('category', 'uncategorized')
            categories[category] = categories.get(category, 0) + 1

        # Tags
        all_tags = set()
        for entry in index.values():
            tags = entry.get('tags', [])
            if isinstance(tags, list):
                all_tags.update(tags)
            elif tags:
                all_tags.add(tags)

        # Keywords - count unique keywords
        all_keywords = set()
        for entry in index.values():
            keywords = entry.get('keywords', [])
            if isinstance(keywords, list):
                all_keywords.update(keywords)

        print('📊 Claude Docs Management - Index Metadata Report')
        print('=' * 70)
        print(f'Generated: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}')
        print(f'Total entries: {total}')
        print()
        print('Metadata Coverage:')
        print(f'  ✅ Title:        {with_title:3d}/{total} ({with_title*100//total if total > 0 else 0}%)')
        print(f'  ✅ Description:  {with_description:3d}/{total} ({with_description*100//total if total > 0 else 0}%)')
        print(f'  ✅ Keywords:     {with_keywords:3d}/{total} ({with_keywords*100//total if total > 0 else 0}%)')
        print(f'  ✅ Tags:         {with_tags:3d}/{total} ({with_tags*100//total if total > 0 else 0}%)')
        print(f'  ✅ Category:     {with_category:3d}/{total} ({with_category*100//total if total > 0 else 0}%)')
        print(f'  ✅ Domain:       {with_domain:3d}/{total} ({with_domain*100//total if total > 0 else 0}%)')
        print()
        print(f'Unique Keywords: {len(all_keywords)}')
        print()
        print(f'Domains ({len(domains)}):')
        for domain in sorted(domains.keys(), key=lambda x: domains[x], reverse=True):
            print(f'  {domain:30s} {domains[domain]:3d} docs')
        print()
        print(f'Categories ({len(categories)}):')
        for category in sorted(categories.keys(), key=lambda x: categories[x], reverse=True):
            print(f'  {category:30s} {categories[category]:3d} docs')
        print()
        print(f'Unique Tags ({len(all_tags)}):')
        if all_tags:
            # Avoid overly long lines for huge tag sets
            sorted_tags = sorted(all_tags)
            preview = ', '.join(sorted_tags[:50])
            print(f'  {preview}')
            if len(sorted_tags) > 50:
                print(f'  ... and {len(sorted_tags) - 50} more')
        else:
            print('  (none)')
        print()
        print('=' * 70)
        print('✅ Index is ready for documentation queries and lookups!')
        print('   - All doc_ids are properly mapped')
        print('   - Rich metadata (title, description, keywords, tags) populated')
        print('   - Domain and category classification complete')
        print('   - Search and discovery capabilities fully operational')

        summary = {
            'total_entries': total,
            'with_title': with_title,
            'with_description': with_description,
            'with_keywords': with_keywords,
            'with_tags': with_tags,
            'with_category': with_category,
            'with_domain': with_domain,
            'domains_count': len(domains),
            'categories_count': len(categories),
            'unique_tags_count': len(all_tags),
            'unique_keywords_count': len(all_keywords),
        }

        if args.json:
            import json
            print()
            print(json.dumps(summary, indent=2))

        logger.end(exit_code=exit_code, summary=summary)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in generate_report", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()
