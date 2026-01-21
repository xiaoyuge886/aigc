#!/usr/bin/env python3
"""
Automated Tag Configuration Audit Script

This script audits tag_detection.yaml configuration against the actual documentation
corpus to detect staleness, coverage issues, and suggest improvements.

Performance: Designed to run in < 30 seconds for ~444 documents.
Relies on existing index.yaml metadata (no document re-reading).

Usage:
    python audit_tag_config.py                    # Full audit
    python audit_tag_config.py --json             # JSON output
    python audit_tag_config.py --summary-only     # Quick summary only
"""

import argparse
import sys
from pathlib import Path


import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; config_dir = bootstrap.config_dir
from collections import Counter, defaultdict
from datetime import datetime, timezone



class TagConfigAuditor:
    """Audits tag configuration against documentation corpus."""
    
    def __init__(self, base_dir: Path, config_dir: Path):
        self.base_dir = base_dir
        self.config_dir = config_dir
        self.index_path = base_dir / 'index.yaml'
        self.tag_config_path = config_dir / 'tag_detection.yaml'
        
        # Load data - read index directly since list_entries() may have issues
        with open(self.index_path, 'r', encoding='utf-8') as f:
            index_data = yaml.safe_load(f) or {}
        
        # Convert dict of doc_id -> entry to list of entries with doc_id included
        self.entries = [
            {**entry, 'doc_id': doc_id} 
            for doc_id, entry in index_data.items()
        ]
        
        with open(self.tag_config_path, 'r', encoding='utf-8') as f:
            self.tag_config = yaml.safe_load(f) or {}
    
    def audit(self) -> dict:
        """Run complete audit and return results."""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_documents': len(self.entries),
            'tag_coverage': self._audit_tag_coverage(),
            'tag_usage': self._audit_tag_usage(),
            'config_staleness': self._audit_config_staleness(),
            'keyword_suggestions': self._suggest_new_tags(),
            'under_tagged_docs': self._find_under_tagged_docs()
        }
        
        return results
    
    def _audit_tag_coverage(self) -> dict:
        """Analyze tag distribution and coverage."""
        tag_counts = Counter()
        docs_by_tag_count = defaultdict(int)
        
        for entry in self.entries:
            tags = entry.get('tags', [])
            tag_count = len(tags)
            docs_by_tag_count[tag_count] += 1
            
            for tag in tags:
                tag_counts[tag] += 1
        
        total_docs = len(self.entries)
        
        return {
            'tags_defined': len(self.tag_config.get('tags', {})),
            'tags_in_use': len(tag_counts),
            'tag_distribution': {tag: count for tag, count in tag_counts.most_common()},
            'docs_by_tag_count': dict(docs_by_tag_count),
            'under_tagged_percent': (docs_by_tag_count.get(0, 0) + docs_by_tag_count.get(1, 0)) / total_docs * 100 if total_docs > 0 else 0
        }
    
    def _audit_tag_usage(self) -> dict:
        """Identify tags with unusual usage patterns."""
        tag_counts = Counter()
        for entry in self.entries:
            for tag in entry.get('tags', []):
                tag_counts[tag] += 1
        
        total_docs = len(self.entries)
        
        # Classify tags by usage
        zero_usage = []
        low_usage = []  # < 5 docs
        very_high_usage = []  # > 50% of docs
        
        for tag, config in self.tag_config.get('tags', {}).items():
            count = tag_counts.get(tag, 0)
            percent = (count / total_docs * 100) if total_docs > 0 else 0
            
            if count == 0:
                zero_usage.append(tag)
            elif count < 5:
                low_usage.append((tag, count))
            elif percent > 50:
                very_high_usage.append((tag, count, percent))
        
        return {
            'zero_usage_tags': zero_usage,
            'low_usage_tags': low_usage,
            'very_high_usage_tags': very_high_usage
        }
    
    def _audit_config_staleness(self) -> dict:
        """Detect stale or outdated configuration."""
        issues = []
        
        # Check for tags with zero usage
        tag_counts = Counter()
        for entry in self.entries:
            for tag in entry.get('tags', []):
                tag_counts[tag] += 1
        
        for tag in self.tag_config.get('tags', {}).keys():
            if tag == 'reference':  # Skip fallback tag
                continue
            if tag_counts.get(tag, 0) == 0:
                issues.append({
                    'tag': tag,
                    'issue': 'zero_usage',
                    'severity': 'high',
                    'recommendation': 'Review terms and min_mentions threshold'
                })
        
        return {
            'issues_found': len(issues),
            'issues': issues
        }
    
    def _suggest_new_tags(self) -> list:
        """Suggest new tags based on high-frequency keywords."""
        keyword_frequency = Counter()
        
        for entry in self.entries:
            keywords = entry.get('keywords', [])
            for kw in keywords:
                keyword_frequency[kw.lower()] += 1
        
        # Get existing tags
        existing_tags = set(self.tag_config.get('tags', {}).keys())
        
        # Find high-frequency keywords that aren't tags
        suggestions = []
        for keyword, count in keyword_frequency.most_common(50):
            # Skip if keyword is already a tag
            if keyword in existing_tags:
                continue
            
            # Skip very common/generic words
            if keyword in {'the', 'and', 'for', 'with', 'this', 'that', 'from', 'have'}:
                continue
            
            # Suggest if appears in 10+ documents
            if count >= 10:
                suggestions.append({
                    'keyword': keyword,
                    'frequency': count,
                    'percent_of_docs': round(count / len(self.entries) * 100, 2)
                })
        
        return suggestions[:10]  # Top 10 suggestions
    
    def _find_under_tagged_docs(self) -> dict:
        """Find documents with insufficient tags."""
        no_tags = []
        only_reference = []
        few_tags = []
        
        for entry in self.entries:
            doc_id = entry.get('doc_id', 'unknown')
            tags = entry.get('tags', [])
            
            if not tags:
                no_tags.append(doc_id)
            elif tags == ['reference']:
                only_reference.append(doc_id)
            elif len(tags) < 2:
                few_tags.append((doc_id, tags))
        
        return {
            'no_tags_count': len(no_tags),
            'only_reference_count': len(only_reference),
            'few_tags_count': len(few_tags),
            'total_under_tagged': len(no_tags) + len(only_reference) + len(few_tags),
            'percent_under_tagged': (len(no_tags) + len(only_reference) + len(few_tags)) / len(self.entries) * 100 if self.entries else 0
        }
    
    def print_report(self, results: dict, summary_only: bool = False):
        """Print human-readable audit report."""
        print('=' * 80)
        print('TAG CONFIGURATION AUDIT REPORT')
        print('=' * 80)
        print(f"Timestamp: {results['timestamp']}")
        print(f"Documents analyzed: {results['total_documents']}")
        print()
        
        # Tag Coverage
        coverage = results['tag_coverage']
        print('TAG COVERAGE:')
        print(f"  Tags defined in config: {coverage['tags_defined']}")
        print(f"  Tags in use: {coverage['tags_in_use']}")
        print(f"  Under-tagged documents: {coverage['under_tagged_percent']:.2f}%")
        print()
        
        # Tag Usage Issues
        usage = results['tag_usage']
        if usage['zero_usage_tags'] or usage['low_usage_tags']:
            print('USAGE ISSUES:')
            if usage['zero_usage_tags']:
                print(f"  Zero-usage tags ({len(usage['zero_usage_tags'])}): {', '.join(usage['zero_usage_tags'])}")
            if usage['low_usage_tags']:
                print(f"  Low-usage tags (< 5 docs): {len(usage['low_usage_tags'])}")
                for tag, count in usage['low_usage_tags'][:5]:
                    print(f"    - {tag}: {count} docs")
            print()
        
        # Config Staleness
        staleness = results['config_staleness']
        if staleness['issues_found'] > 0:
            print(f"CONFIG STALENESS: {staleness['issues_found']} issues found")
            for issue in staleness['issues'][:5]:
                print(f"  - {issue['tag']}: {issue['issue']} ({issue['severity']})")
            print()
        
        # Under-tagged Documents
        under_tagged = results['under_tagged_docs']
        print('UNDER-TAGGED DOCUMENTS:')
        print(f"  No tags: {under_tagged['no_tags_count']}")
        print(f"  Only 'reference' tag: {under_tagged['only_reference_count']}")
        print(f"  Fewer than 2 tags: {under_tagged['few_tags_count']}")
        print(f"  Total: {under_tagged['total_under_tagged']} ({under_tagged['percent_under_tagged']:.2f}%)")
        print()
        
        if not summary_only:
            # New Tag Suggestions
            suggestions = results['keyword_suggestions']
            if suggestions:
                print(f"NEW TAG SUGGESTIONS (top 10 high-frequency keywords):")
                for sugg in suggestions:
                    print(f"  - {sugg['keyword']}: {sugg['frequency']} docs ({sugg['percent_of_docs']}%)")
                print()
        
        print('=' * 80)
        print(f"RECOMMENDATION: {'PASS' if under_tagged['percent_under_tagged'] < 15 else 'ACTION NEEDED'}")
        print('=' * 80)


def main() -> None:
    parser = argparse.ArgumentParser(description='Audit tag configuration against documentation corpus')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--summary-only', action='store_true', help='Show summary only (faster)')
    args = parser.parse_args()
    
    # Get paths
    base_dir = skill_dir / 'canonical'
    config_dir = skill_dir / 'config'
    
    # Run audit
    auditor = TagConfigAuditor(base_dir, config_dir)
    results = auditor.audit()
    
    # Output results
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        auditor.print_report(results, summary_only=args.summary_only)


if __name__ == '__main__':
    main()
