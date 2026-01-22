#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
audit_performance.py - Audit scraping performance and identify bottlenecks

Analyzes scrape logs and execution metrics to identify performance issues
and suggest improvements.

Usage:
    python audit_performance.py --log scrape_output.log
    python audit_performance.py --analyze-recent
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json
import re
from typing import Dict

from utils.script_utils import configure_utf8_output
configure_utf8_output()

def parse_log_file(log_path: Path) -> Dict:
    """Parse scrape output log to extract performance metrics"""
    if not log_path.exists():
        print(f"❌ Log file not found: {log_path}")
        return {}
    
    metrics = {
        'sources': [],
        'total_duration': 0,
        'total_docs': 0,
        'total_skipped': 0,
        'start_time': None,
        'end_time': None
    }
    
    content = log_path.read_text(encoding='utf-8')
    
    # Parse source completions: "✅ name: X docs (Y skipped) (Z.Zs)"
    completion_pattern = r'✅\s+([^:]+):\s+(\d+)\s+docs(?:\s+\((\d+)\s+skipped\))?\s+\(([\d.]+)s\)'
    for match in re.finditer(completion_pattern, content):
        name = match.group(1).strip()
        docs_scraped = int(match.group(2))
        docs_skipped = int(match.group(3)) if match.group(3) else 0
        duration = float(match.group(4))
        
        metrics['sources'].append({
            'name': name,
            'docs_scraped': docs_scraped,
            'docs_skipped': docs_skipped,
            'duration': duration
        })
    
    # Parse total duration: "Total duration: X.X seconds"
    total_match = re.search(r'Total duration:\s+([\d.]+)\s+seconds?', content)
    if total_match:
        metrics['total_duration'] = float(total_match.group(1))
    else:
        # Calculate from source durations if not found
        metrics['total_duration'] = sum(s['duration'] for s in metrics['sources'])
    
    # Calculate totals
    metrics['total_docs'] = sum(s['docs_scraped'] for s in metrics['sources'])
    metrics['total_skipped'] = sum(s['docs_skipped'] for s in metrics['sources'])
    
    return metrics

def analyze_bottlenecks(metrics: Dict) -> Dict:
    """Analyze metrics to identify bottlenecks"""
    analysis = {
        'bottlenecks': [],
        'recommendations': [],
        'stats': {}
    }
    
    if not metrics.get('sources'):
        return analysis
    
    sources = metrics['sources']
    total_docs = sum(s.get('docs_scraped', 0) for s in sources)
    total_skipped = sum(s.get('docs_skipped', 0) for s in sources)
    total_duration = metrics.get('total_duration', 0)
    
    # Calculate per-document times
    times_per_doc = []
    for source in sources:
        if source.get('docs_scraped', 0) > 0 and source.get('duration'):
            time_per_doc = source['duration'] / source['docs_scraped']
            times_per_doc.append(time_per_doc)
            source['time_per_doc'] = time_per_doc
    
    avg_time_per_doc = sum(times_per_doc) / len(times_per_doc) if times_per_doc else 0
    
    analysis['stats'] = {
        'total_sources': len(sources),
        'total_docs': total_docs,
        'total_skipped': total_skipped,
        'total_duration_seconds': total_duration,
        'total_duration_minutes': total_duration / 60,
        'avg_time_per_doc': avg_time_per_doc,
        'slowest_source': max(sources, key=lambda s: s.get('duration', 0)) if sources else None,
        'fastest_source': min(sources, key=lambda s: s.get('duration', 0)) if sources else None
    }
    
    # Identify bottlenecks
    if avg_time_per_doc > 3.0:
        analysis['bottlenecks'].append({
            'issue': 'High per-document processing time',
            'severity': 'high',
            'details': f'Average {avg_time_per_doc:.2f}s per document (target: <2s)',
            'impact': f'Processing {total_docs} documents takes {total_duration/60:.1f} minutes'
        })
        analysis['recommendations'].append({
            'priority': 'high',
            'recommendation': 'Consider parallelizing URL processing within sources',
            'details': 'Currently URLs are processed sequentially. Use ThreadPoolExecutor to process 3-5 URLs concurrently per source.'
        })
        analysis['recommendations'].append({
            'priority': 'high',
            'recommendation': 'Optimize skip-existing check',
            'details': 'Use HEAD requests or ETags to check if content changed before fetching full content. Current implementation fetches full content even when checking hash.'
        })
    
    if avg_time_per_doc > 1.5:
        analysis['bottlenecks'].append({
            'issue': 'Rate limiting delay',
            'severity': 'medium',
            'details': f'1.5s rate limit between requests adds significant overhead',
            'impact': f'For {total_docs} documents, rate limiting alone adds {total_docs * 1.5 / 60:.1f} minutes'
        })
        analysis['recommendations'].append({
            'priority': 'medium',
            'recommendation': 'Reduce rate limit or use adaptive rate limiting',
            'details': 'Consider reducing to 0.5-1.0s if server allows, or implement adaptive rate limiting based on 429 responses.'
        })
    
    # Check for sequential processing bottlenecks
    if len(sources) > 1:
        sequential_overhead = sum(s.get('duration', 0) for s in sources) - total_duration
        if sequential_overhead > 0:
            analysis['bottlenecks'].append({
                'issue': 'Sequential source processing',
                'severity': 'low',
                'details': f'Sources processed sequentially within domains',
                'impact': f'Parallelization saves {sequential_overhead:.1f}s'
            })
    
    # Check skip efficiency
    skip_rate = total_skipped / total_docs if total_docs > 0 else 0
    if skip_rate > 0.8:
        analysis['bottlenecks'].append({
            'issue': 'Inefficient skip-existing check',
            'severity': 'medium',
            'details': f'{skip_rate*100:.1f}% of documents skipped, but still required fetching to check hash',
            'impact': f'Wasted {total_skipped * avg_time_per_doc / 60:.1f} minutes fetching unchanged content'
        })
        analysis['recommendations'].append({
            'priority': 'high',
            'recommendation': 'Use HTTP headers (ETag, Last-Modified) for change detection',
            'details': 'Check ETag/Last-Modified headers before fetching full content. Only fetch if headers indicate change.'
        })
    
    return analysis

def print_analysis_report(metrics: Dict, analysis: Dict) -> None:
    """Print formatted analysis report"""
    print("\n" + "="*70)
    print("PERFORMANCE AUDIT REPORT")
    print("="*70)
    
    stats = analysis['stats']
    print(f"\n📊 Execution Statistics:")
    print(f"   Total sources:        {stats['total_sources']}")
    print(f"   Total documents:      {stats['total_docs']}")
    print(f"   Skipped (unchanged): {stats['total_skipped']}")
    print(f"   Total duration:       {stats['total_duration_minutes']:.1f} minutes ({stats['total_duration_seconds']:.1f}s)")
    print(f"   Avg time per doc:    {stats['avg_time_per_doc']:.2f}s")
    
    if stats['slowest_source']:
        slowest = stats['slowest_source']
        print(f"\n🐌 Slowest source:")
        print(f"   {slowest['name']}: {slowest.get('duration', 0):.1f}s for {slowest.get('docs_scraped', 0)} docs ({slowest.get('time_per_doc', 0):.2f}s/doc)")
    
    if stats['fastest_source']:
        fastest = stats['fastest_source']
        print(f"\n⚡ Fastest source:")
        print(f"   {fastest['name']}: {fastest.get('duration', 0):.1f}s for {fastest.get('docs_scraped', 0)} docs ({fastest.get('time_per_doc', 0):.2f}s/doc)")
    
    if analysis['bottlenecks']:
        print(f"\n⚠️  Bottlenecks Identified ({len(analysis['bottlenecks'])}):")
        for i, bottleneck in enumerate(analysis['bottlenecks'], 1):
            severity_icon = '🔴' if bottleneck['severity'] == 'high' else '🟡' if bottleneck['severity'] == 'medium' else '🟢'
            print(f"\n   {i}. {severity_icon} {bottleneck['issue']}")
            print(f"      {bottleneck['details']}")
            print(f"      Impact: {bottleneck['impact']}")
    
    if analysis['recommendations']:
        print(f"\n💡 Recommendations ({len(analysis['recommendations'])}):")
        for i, rec in enumerate(analysis['recommendations'], 1):
            priority_icon = '🔴' if rec['priority'] == 'high' else '🟡' if rec['priority'] == 'medium' else '🟢'
            print(f"\n   {i}. {priority_icon} {rec['recommendation']}")
            print(f"      {rec['details']}")
    
    print("\n" + "="*70)

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Audit scraping performance and identify bottlenecks',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument('--log', type=Path,
                       help='Path to scrape output log file')
    parser.add_argument('--analyze-recent', action='store_true',
                       help='Analyze most recent scrape_output.log')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    args = parser.parse_args()
    
    # Determine log file
    if args.analyze_recent:
        script_dir = Path(__file__).parent
        # Log file is in parent directory (docs-management/)
        log_path = script_dir.parent / "scrape_output.log"
        if not log_path.exists():
            # Fallback to scripts directory
            log_path = script_dir / "scrape_output.log"
    elif args.log:
        log_path = args.log
    else:
        print("❌ Must specify --log or --analyze-recent")
        sys.exit(1)
    
    # Parse log
    metrics = parse_log_file(log_path)
    if not metrics:
        print("❌ No metrics found in log file")
        sys.exit(1)
    
    # Analyze
    analysis = analyze_bottlenecks(metrics)
    
    # Output
    if args.json:
        output = {
            'metrics': metrics,
            'analysis': analysis
        }
        print(json.dumps(output, indent=2))
    else:
        print_analysis_report(metrics, analysis)

if __name__ == '__main__':
    main()

