#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
from pathlib import Path
# Test files rely on conftest.py for path setup when run via pytest
# When run directly, setup paths manually
if __name__ == '__main__':
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
"""
test_search_validation.py - Comprehensive test and validation of search functionality

Tests:
1. Subsection search results include anchor URLs
2. Keyword and tag accuracy (sample validation)
3. SKILLS subsection discovery
4. Relevance ranking
5. Output format and logging
"""

import json
import sys
from pathlib import Path
from typing import Dict

# Add scripts directory to path
_scripts_dir = Path(__file__).parent
if str(_scripts_dir) not in sys.path:
    sys.path.insert(0, str(_scripts_dir))

from scripts.core.doc_resolver import DocResolver
from management.index_manager import IndexManager
from utils.path_config import get_base_dir
from utils.script_utils import configure_utf8_output

configure_utf8_output()


class SearchValidator:
    """Validate search functionality"""
    
    def __init__(self, base_dir: Path | None = None):
        if base_dir is None:
            base_dir = get_base_dir()
        self.base_dir = Path(base_dir)
        self.resolver = DocResolver(self.base_dir)
        self.index_manager = IndexManager(self.base_dir)
        self.issues = []
        self.test_results = []
    
    def test_subsection_url_anchors(self) -> Dict:
        """Test that subsection matches include anchor URLs in results"""
        print("\n" + "="*70)
        print("TEST 1: Subsection URL Anchors")
        print("="*70)
        
        issues = []
        tests = [
            {
                'query': 'skills vs slash',
                'expected_docs': ['code-claude-com-docs-en-slash-commands'],
                'expected_subsections': {
                    'code-claude-com-docs-en-slash-commands': ['#skills-vs-slash-commands']
                }
            },
            {
                'query': 'progressive disclosure',
                'expected_docs': [],
                'expected_subsections': {}
            },
            {
                'query': 'add skills to plugin',
                'expected_docs': ['code-claude-com-docs-en-plugins'],
                'expected_subsections': {
                    'code-claude-com-docs-en-plugins': ['#add-skills-to-your-plugin']
                }
            }
        ]
        
        for test in tests:
            print(f"\nTesting query: '{test['query']}'")
            results = self.resolver.search_by_keyword([test['query']], limit=10)
            
            print(f"  Found {len(results)} results")
            
            # Check if expected docs are in results
            found_doc_ids = [doc_id for doc_id, _ in results]
            for expected_doc in test['expected_docs']:
                if expected_doc not in found_doc_ids:
                    issue = f"Expected doc '{expected_doc}' not in results for query '{test['query']}'"
                    issues.append(issue)
                    print(f"  ❌ {issue}")
                else:
                    print(f"  ✓ Found expected doc: {expected_doc}")
                    
                    # Check if subsection match info is available
                    doc_id, metadata = next((d, m) for d, m in results if d == expected_doc)
                    url = metadata.get('url', '')
                    
                    # Check if we have subsection info in metadata
                    subsections = metadata.get('subsections', [])
                    matching_subsections = []
                    for sub in subsections:
                        if isinstance(sub, dict):
                            heading = sub.get('heading', '').lower()
                            if test['query'].lower() in heading or any(
                                test['query'].lower() in kw.lower() 
                                for kw in sub.get('keywords', [])
                            ):
                                matching_subsections.append(sub.get('anchor', ''))
                    
                    # Check if URL includes anchor
                    if test['expected_subsections'].get(expected_doc):
                        expected_anchors = test['expected_subsections'][expected_doc]
                        for expected_anchor in expected_anchors:
                            if expected_anchor in matching_subsections:
                                # URL should include anchor when subsection matches
                                if expected_anchor not in url:
                                    issue = f"URL missing anchor for subsection match: {expected_doc} should have {expected_anchor} in URL"
                                    issues.append(issue)
                                    print(f"  ❌ {issue}")
                                    print(f"     Current URL: {url}")
                                    print(f"     Expected anchor: {expected_anchor}")
                                else:
                                    print(f"  ✓ URL includes anchor: {expected_anchor}")
                            else:
                                print(f"  ⚠️  Subsection {expected_anchor} not found in matching subsections")
        
        result = {
            'test': 'subsection_url_anchors',
            'passed': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues)
        }
        self.test_results.append(result)
        return result
    
    def validate_keywords_tags_sample(self, sample_size: int = 5) -> Dict:
        """Sample documents and validate keywords/tags against actual content"""
        print("\n" + "="*70)
        print(f"TEST 2: Keyword and Tag Accuracy (sampling {sample_size} per source)")
        print("="*70)
        
        issues = []
        index = self.index_manager.load_all()
        
        # Sample documents from each source
        sources = {
            'code-claude-com': [],
            'docs-claude-com': [],
            'anthropic-com': []
        }
        
        for doc_id, metadata in index.items():
            if doc_id.startswith('code-claude-com'):
                sources['code-claude-com'].append((doc_id, metadata))
            elif doc_id.startswith('docs-claude-com'):
                sources['docs-claude-com'].append((doc_id, metadata))
            elif doc_id.startswith('anthropic-com'):
                sources['anthropic-com'].append((doc_id, metadata))
        
        # Sample from each source
        samples = {}
        for source, docs in sources.items():
            samples[source] = docs[:sample_size]
            print(f"\n{source}: Sampling {len(samples[source])} documents")
        
        # Validate each sample
        for source, sample_docs in samples.items():
            print(f"\n--- Validating {source} samples ---")
            for doc_id, metadata in sample_docs:
                print(f"\n  Document: {doc_id}")
                print(f"    Title: {metadata.get('title', 'N/A')}")
                
                # Get file path
                path_str = metadata.get('path')
                if not path_str:
                    issues.append(f"{doc_id}: No path in metadata")
                    continue
                
                file_path = self.base_dir / path_str
                if not file_path.exists():
                    issues.append(f"{doc_id}: File not found at {file_path}")
                    continue
                
                # Read actual content
                try:
                    content = file_path.read_text(encoding='utf-8')
                    content_lower = content.lower()
                except Exception as e:
                    issues.append(f"{doc_id}: Failed to read file: {e}")
                    continue
                
                # Validate keywords
                keywords = metadata.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                
                print(f"    Keywords ({len(keywords)}): {', '.join(keywords[:5])}...")
                
                # Check if keywords appear in content
                missing_keywords = []
                generic_keywords = ['steps', 'card', 'title', 'cardgroup', 'accordion', 'accordiongroup']
                found_generic = []
                
                for kw in keywords:
                    kw_lower = kw.lower()
                    # Check if keyword appears in content
                    if kw_lower not in content_lower and kw_lower.replace(' ', '-') not in content_lower:
                        # Allow some flexibility for multi-word keywords
                        words = kw_lower.split()
                        if len(words) > 1:
                            # Check if all words appear (maybe not together)
                            if not all(w in content_lower for w in words if len(w) > 3):
                                missing_keywords.append(kw)
                    # Check for generic keywords
                    if kw_lower in generic_keywords:
                        found_generic.append(kw)
                
                if missing_keywords:
                    issue = f"{doc_id}: Keywords not found in content: {missing_keywords[:3]}"
                    issues.append(issue)
                    print(f"    ❌ {issue}")
                else:
                    print(f"    ✓ All keywords found in content")
                
                if found_generic:
                    issue = f"{doc_id}: Generic keywords found: {found_generic}"
                    issues.append(issue)
                    print(f"    ⚠️  {issue}")
                
                # Validate tags
                tags = metadata.get('tags', [])
                if isinstance(tags, str):
                    tags = [tags]
                
                print(f"    Tags ({len(tags)}): {', '.join(tags)}")
                
                # Check if tags are reasonable (tags are more flexible, just check they're not completely wrong)
                # Tags can be inferred from path/category, so we just log them
                
                # Validate subsection keywords
                subsections = metadata.get('subsections', [])
                if subsections:
                    print(f"    Subsections: {len(subsections)}")
                    for sub in subsections[:3]:  # Check first 3
                        if isinstance(sub, dict):
                            heading = sub.get('heading', '')
                            sub_keywords = sub.get('keywords', [])
                            if isinstance(sub_keywords, str):
                                sub_keywords = [sub_keywords]
                            
                            # Check subsection content
                            # Extract section from content (simplified - just check heading exists)
                            if heading.lower() not in content_lower.replace('#', '').replace('##', '').replace('###', ''):
                                issue = f"{doc_id}: Subsection heading '{heading}' not found in content"
                                issues.append(issue)
                                print(f"      ❌ {issue}")
                            
                            # Check for generic subsection keywords
                            generic_sub_keywords = [kw for kw in sub_keywords if kw.lower() in generic_keywords]
                            if generic_sub_keywords:
                                issue = f"{doc_id}: Subsection '{heading}' has generic keywords: {generic_sub_keywords}"
                                issues.append(issue)
                                print(f"      ⚠️  {issue}")
        
        result = {
            'test': 'keywords_tags_accuracy',
            'passed': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues),
            'samples_validated': sum(len(docs) for docs in samples.values())
        }
        self.test_results.append(result)
        return result
    
    def test_skills_subsections(self) -> Dict:
        """Test SKILLS subsection discovery and indexing"""
        print("\n" + "="*70)
        print("TEST 3: SKILLS Subsection Discovery")
        print("="*70)
        
        issues = []
        
        # Test queries that should find Skills subsections
        test_queries = [
            'skills',
            'skills plugin',
            'add skills',
            'skills vs slash commands'
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            results = self.resolver.search_by_keyword(query.split(), limit=10)
            
            # Check for plugins.md with Skills subsection
            plugins_found = False
            slash_commands_found = False
            
            for doc_id, metadata in results:
                if doc_id == 'code-claude-com-docs-en-plugins':
                    plugins_found = True
                    subsections = metadata.get('subsections', [])
                    skills_subsections = [
                        sub for sub in subsections
                        if isinstance(sub, dict) and 'skills' in sub.get('heading', '').lower()
                    ]
                    if skills_subsections:
                        print(f"  ✓ Found plugins.md with Skills subsection: {skills_subsections[0].get('heading')}")
                        print(f"    Anchor: {skills_subsections[0].get('anchor')}")
                    else:
                        issue = f"plugins.md found but no Skills subsection detected for query '{query}'"
                        issues.append(issue)
                        print(f"  ❌ {issue}")
                
                if doc_id == 'code-claude-com-docs-en-slash-commands':
                    slash_commands_found = True
                    subsections = metadata.get('subsections', [])
                    skills_subsections = [
                        sub for sub in subsections
                        if isinstance(sub, dict) and 'skills' in sub.get('heading', '').lower()
                    ]
                    if skills_subsections:
                        print(f"  ✓ Found slash-commands.md with Skills subsection: {skills_subsections[0].get('heading')}")
                        print(f"    Anchor: {skills_subsections[0].get('anchor')}")
                    else:
                        issue = f"slash-commands.md found but no Skills subsection detected for query '{query}'"
                        issues.append(issue)
                        print(f"  ❌ {issue}")
            
            if 'skills' in query.lower() and not plugins_found and not slash_commands_found:
                issue = f"Query '{query}' should find Skills subsections but didn't"
                issues.append(issue)
                print(f"  ❌ {issue}")
        
        result = {
            'test': 'skills_subsections',
            'passed': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues)
        }
        self.test_results.append(result)
        return result
    
    def test_relevance_ranking(self) -> Dict:
        """Test that search results are ranked by relevance"""
        print("\n" + "="*70)
        print("TEST 4: Relevance Ranking")
        print("="*70)
        
        issues = []
        
        test_cases = [
            {
                'query': 'skills',
                'expected_order': [
                    # Should prioritize documents with "skills" in title or main keywords
                    # Then documents with Skills subsections
                ]
            },
            {
                'query': 'progressive disclosure',
                'expected_order': []
            }
        ]
        
        for test_case in test_cases:
            query = test_case['query']
            print(f"\nTesting query: '{query}'")
            
            results = self.resolver.search_by_keyword(query.split(), limit=10)
            
            print(f"  Results (top 5):")
            for i, (doc_id, metadata) in enumerate(results[:5], 1):
                title = metadata.get('title', 'N/A')
                # Calculate a simple relevance indicator
                title_match = query.lower() in title.lower()
                keywords = metadata.get('keywords', [])
                if isinstance(keywords, str):
                    keywords = [keywords]
                keyword_match = any(query.lower() in str(kw).lower() for kw in keywords)
                
                match_type = []
                if title_match:
                    match_type.append('title')
                if keyword_match:
                    match_type.append('keywords')
                
                print(f"    {i}. {title} ({doc_id})")
                print(f"       Match: {', '.join(match_type) if match_type else 'other'}")
            
            # Basic check: documents with query in title should rank higher
            title_matches = [
                (i, doc_id, metadata) for i, (doc_id, metadata) in enumerate(results)
                if query.lower() in metadata.get('title', '').lower()
            ]
            
            if title_matches:
                # Check if title matches are in top positions
                top_5_indices = [i for i, _, _ in title_matches if i < 5]
                if not top_5_indices:
                    issue = f"Query '{query}': Title matches not in top 5 results"
                    issues.append(issue)
                    print(f"  ⚠️  {issue}")
                else:
                    print(f"  ✓ Title matches found in top results")
        
        result = {
            'test': 'relevance_ranking',
            'passed': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues)
        }
        self.test_results.append(result)
        return result
    
    def test_output_format(self) -> Dict:
        """Test output format and logging"""
        print("\n" + "="*70)
        print("TEST 5: Output Format and Logging")
        print("="*70)
        
        issues = []
        
        # Test API output format
        print("\nTesting API output format...")
        try:
            # Import from parent directory
            api_path = self.base_dir.parent / 'official_docs_api.py'
            if api_path.exists():
                import importlib.util
                spec = importlib.util.spec_from_file_location("official_docs_api", api_path)
                official_docs_api = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(official_docs_api)
                api = official_docs_api.OfficialDocsAPI(self.base_dir)
            else:
                raise ImportError(f"official_docs_api.py not found at {api_path}")
            
            results = api.find_document("skills", limit=3)
            
            if not results:
                issue = "API returned no results for 'skills' query"
                issues.append(issue)
                print(f"  ❌ {issue}")
            else:
                print(f"  ✓ API returned {len(results)} results")
                
                # Check result structure
                required_keys = ['doc_id', 'url', 'title', 'description', 'keywords', 'tags']
                for i, result in enumerate(results[:2], 1):
                    print(f"\n  Result {i}:")
                    print(f"    doc_id: {result.get('doc_id', 'MISSING')}")
                    print(f"    url: {result.get('url', 'MISSING')}")
                    print(f"    title: {result.get('title', 'MISSING')}")
                    
                    missing_keys = [key for key in required_keys if key not in result]
                    if missing_keys:
                        issue = f"Result {i} missing keys: {missing_keys}"
                        issues.append(issue)
                        print(f"    ❌ {issue}")
                    else:
                        print(f"    ✓ All required keys present")
                    
                    # Check if URL should include anchor for subsection matches
                    # (This will be an issue we need to fix)
                    url = result.get('url', '')
                    if '#add-skills-to-your-plugin' in url or 'skills' in result.get('title', '').lower():
                        # If this is a Skills-related result, check if it should have an anchor
                        # We'll note this as something to check
                        pass
        except Exception as e:
            issue = f"API test failed: {e}"
            issues.append(issue)
            print(f"  ❌ {issue}")
        
        result = {
            'test': 'output_format',
            'passed': len(issues) == 0,
            'issues': issues,
            'issue_count': len(issues)
        }
        self.test_results.append(result)
        return result
    
    def generate_report(self) -> str:
        """Generate comprehensive test report"""
        report = []
        report.append("="*70)
        report.append("CLAUDE-DOCS SEARCH VALIDATION REPORT")
        report.append("="*70)
        report.append("")
        
        total_issues = sum(r['issue_count'] for r in self.test_results)
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['passed'])
        
        report.append(f"Summary: {passed_tests}/{total_tests} tests passed, {total_issues} issues found")
        report.append("")
        
        for result in self.test_results:
            report.append(f"Test: {result['test']}")
            report.append(f"  Status: {'PASSED' if result['passed'] else 'FAILED'}")
            report.append(f"  Issues: {result['issue_count']}")
            if result['issues']:
                report.append("  Details:")
                for issue in result['issues'][:5]:  # Show first 5 issues
                    report.append(f"    - {issue}")
                if len(result['issues']) > 5:
                    report.append(f"    ... and {len(result['issues']) - 5} more")
            report.append("")
        
        # Recommendations
        report.append("="*70)
        report.append("RECOMMENDATIONS")
        report.append("="*70)
        report.append("")
        
        if any(r['test'] == 'subsection_url_anchors' and not r['passed'] for r in self.test_results):
            report.append("1. FIX: Subsection matches should include anchor URLs in results")
            report.append("   - Modify doc_resolver.py to track which subsection matched")
            report.append("   - Update API responses to include subsection anchor in URL")
            report.append("   - Update CLI output to show subsection anchors")
            report.append("")
        
        if any(r['test'] == 'keywords_tags_accuracy' and r['issue_count'] > 0 for r in self.test_results):
            report.append("2. IMPROVE: Keyword extraction accuracy")
            report.append("   - Filter out generic keywords (steps, card, title, etc.)")
            report.append("   - Improve subsection keyword extraction")
            report.append("   - Review filtering.yaml for better keyword quality")
            report.append("")
        
        if any(r['test'] == 'relevance_ranking' and not r['passed'] for r in self.test_results):
            report.append("3. IMPROVE: Relevance ranking")
            report.append("   - Ensure title matches rank highest")
            report.append("   - Subsection matches should rank appropriately")
            report.append("   - Consider boosting exact phrase matches")
            report.append("")
        
        return "\n".join(report)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Test and validate docs-management search functionality'
    )
    parser.add_argument('--base-dir', help='Base directory for canonical docs')
    parser.add_argument('--sample-size', type=int, default=5, help='Number of documents to sample per source')
    parser.add_argument('--output', help='Output file for report (JSON)')
    
    args = parser.parse_args()
    
    base_dir = Path(args.base_dir) if args.base_dir else get_base_dir()
    
    validator = SearchValidator(base_dir)
    
    # Run all tests
    print("Starting comprehensive search validation...")
    print(f"Base directory: {base_dir}")
    
    validator.test_subsection_url_anchors()
    validator.validate_keywords_tags_sample(sample_size=args.sample_size)
    validator.test_skills_subsections()
    validator.test_relevance_ranking()
    validator.test_output_format()
    
    # Generate report
    report = validator.generate_report()
    print("\n" + report)
    
    # Save JSON report if requested
    if args.output:
        output_path = Path(args.output)
        report_data = {
            'summary': {
                'total_tests': len(validator.test_results),
                'passed_tests': sum(1 for r in validator.test_results if r['passed']),
                'total_issues': sum(r['issue_count'] for r in validator.test_results)
            },
            'test_results': validator.test_results,
            'text_report': report
        }
        output_path.write_text(json.dumps(report_data, indent=2), encoding='utf-8')
        print(f"\nReport saved to: {output_path}")
    
    # Exit with error code if any tests failed
    if any(not r['passed'] for r in validator.test_results):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()

