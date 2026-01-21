#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scrape_all_sources.py - Scrape multiple sources in parallel

Orchestrates scraping from multiple documentation sources with:
- Parallel execution across different domains
- Automatic validation after each source
- Progress tracking and resume capability
- Error recovery with natural language guidance

Usage:
    # Uses default config: references/sources.json (relative to script directory)
    python scrape_all_sources.py
    
    # Custom config file path
    python scrape_all_sources.py --config sources.json
    python scrape_all_sources.py --config /path/to/sources.json
    
    # With flags
    python scrape_all_sources.py --parallel --auto-validate --skip-existing

Dependencies:
    pip install pyyaml
"""

from __future__ import annotations

import os
import uuid

# Early import of constants (no side effects, safe before logger setup)
from typing import Final
RUN_ID_LENGTH: Final[int] = 8  # Inline constant to avoid import cycle issues

# CRITICAL: Set run ID BEFORE any imports that create loggers
# This ensures all log messages (including from module-level logger creation)
# have consistent run ID for correlation across parallel processes
if not os.environ.get("CLAUDE_DOCS_RUN_ID"):
    os.environ["CLAUDE_DOCS_RUN_ID"] = uuid.uuid4().hex[:RUN_ID_LENGTH]

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; scripts_dir = bootstrap.scripts_dir

import argparse
import concurrent.futures
import json
import subprocess
# Note: os and uuid imported early at module top for run ID initialization
import time
from datetime import datetime, timezone
from typing import Dict

from utils.script_utils import configure_utf8_output, ensure_yaml_installed, format_duration
from utils.path_config import get_base_dir
from utils.config_helpers import get_scraping_max_source_workers, get_sources_default_timeout
from utils.cli_utils import add_base_dir_argument, resolve_base_dir_from_args
from utils.logging_utils import get_or_setup_logger
configure_utf8_output()

yaml = ensure_yaml_installed()

# Script logger for structured logging
logger = get_or_setup_logger(__file__, log_category="scrape")

def log_with_timestamp(message: str) -> None:
    """Log message with timestamp using structured logger"""
    logger.info(message)

class MultiSourceScraper:
    """Scrape multiple sources with parallelization"""
    
    def __init__(self, base_dir: Path | None = None, scripts_dir: Path | None = None, max_workers: int | None = None):
        """
        Initialize multi-source scraper
        
        Args:
            base_dir: Base directory. If None, uses config default.
            scripts_dir: Directory containing scripts. If None, uses script's parent directory.
            max_workers: Maximum parallel workers. If None, uses config default.
        """
        self.base_dir = base_dir if base_dir else get_base_dir()
        self.scripts_dir = scripts_dir if scripts_dir else Path(__file__).parent.parent  # Go up to scripts/ level
        self.max_workers = max_workers if max_workers is not None else get_scraping_max_source_workers()
        self.scrape_script = self.scripts_dir / "core" / "scrape_docs.py"
        self.validate_script = self.scripts_dir / "validation" / "quick_validate.py"
    
    def scrape_source(self, source: Dict) -> Dict:
        """
        Scrape a single source.

        Uses a streaming subprocess so that `scrape_docs.py` output is visible
        in real time, while still collecting enough output to compute summary
        statistics (doc_count, skipped_count).
        """
        name = source['name']
        expected = source.get('expected_count', 'Unknown')
        filter_str = source.get('filter', 'None')

        print(f"\n📥 Scraping: {name}")
        log_with_timestamp(f"   Expected docs: {expected}")
        log_with_timestamp(f"   Filter: {filter_str}")
        start_time = time.time()
        
        cmd = [
            sys.executable,
            str(self.scrape_script),
            '--base-dir', str(self.base_dir),
        ]
        
        if source['type'] == 'sitemap':
            cmd.extend(['--sitemap', source['url']])
            if 'filter' in source:
                cmd.extend(['--filter', source['filter']])
            # Optional max-age in days (filters sitemap URLs by <lastmod> date)
            if source.get('max_age_days'):
                cmd.extend(['--max-age', str(source['max_age_days'])])
        elif source['type'] == 'docs-map':
            cmd.extend(['--docs-map', source['url']])
        elif source['type'] == 'url':
            # Direct URL scraping (single file)
            cmd.extend(['--url', source['url']])
            # For single URL, output must be the full file path
            if 'output' not in source:
                raise ValueError(f"Source '{name}' with type 'url' must specify 'output' field with full file path (e.g., 'code-claude-com/CHANGELOG.md')")
            cmd.extend(['--output', source['output']])
        elif source['type'] == 'llms-txt':
            # llms.txt URL index (like sitemap but parses markdown link format)
            cmd.extend(['--llms-txt', source['url']])
        # NOTE: llms-full type is DISABLED - content is often truncated/summarized
        # compared to fetching individual URLs. Use llms-txt (URL discovery) instead.
        # The scrape_llms_full.py script exists for manual testing but is not
        # integrated here to prevent accidental content loss.
        # See: 2025-11-27 investigation showing code.claude.com/docs/llms-full.txt
        # has truncated content vs the full documentation pages.

        # Common flags for all active types (scrape_docs.py based)
        if True:
            if source.get('skip_existing', False):
                cmd.append('--skip-existing')

            if source.get('resume', False):
                cmd.append('--resume')

            if source.get('max_retries'):
                cmd.extend(['--max-retries', str(source['max_retries'])])

            # Add try_markdown flag (defaults to True if not specified)
            if source.get('try_markdown', True) is False:
                cmd.append('--no-try-markdown')

            # Extract URLs from expected_errors to skip (e.g., known 404s)
            expected_errors = source.get('expected_errors', [])
            skip_urls = [
                e['url'] for e in expected_errors
                if e.get('type') == '404' and 'url' in e
            ]
            if skip_urls:
                cmd.extend(['--skip-urls'] + skip_urls)
                log_with_timestamp(f"   Skipping {len(skip_urls)} known-bad URL(s) from expected_errors")

            # Only add --output for non-url types (url types already added it above)
            if source['type'] != 'url' and source.get('output'):
                cmd.extend(['--output', source['output']])
        
        # Set MSYS_NO_PATHCONV=1 to prevent Git Bash path conversion on Windows
        env = os.environ.copy()
        env['MSYS_NO_PATHCONV'] = '1'
        env['PYTHONUNBUFFERED'] = '1'  # Enable unbuffered output for real-time progress
        env['CLAUDE_DOCS_SOURCE_NAME'] = name  # Pass source name for log correlation

        # Use config default if source doesn't specify timeout
        timeout = source.get('timeout', get_sources_default_timeout())
        output_lines: list[str] = []
        doc_count = 0
        skipped_count = 0

        try:
            # Stream stdout (and stderr) line-by-line so the user can see progress
            # Use bufsize=1 for line buffering to ensure real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                bufsize=1,  # Line buffered for real-time streaming
                env=env
            )

            assert process.stdout is not None  # For type checkers
            while True:
                line = process.stdout.readline()
                if not line:
                    break

                # Echo child output immediately for real-time observability
                # Flush immediately to ensure output appears in real-time
                print(line, end='', flush=True)
                output_lines.append(line)

                # Enforce a simple wall-clock timeout
                if timeout and (time.time() - start_time) > timeout:
                    print(f"\n❌ Timeout after {timeout} seconds while scraping: {name}")
                    process.kill()
                    process.wait()
                    return {
                        'success': False,
                        'name': name,
                        'error': f'Timeout after {timeout} seconds',
                        'duration': time.time() - start_time
                    }

            return_code = process.wait()
            duration = time.time() - start_time

            combined_output = ''.join(output_lines)

            # Parse output to get document and skipped counts from "Scraping Summary" format
            try:
                import re

                for line in combined_output.split('\n'):
                    # Parse "Scraping Summary for X URLs:"
                    if 'Scraping Summary for' in line:
                        match = re.search(r'Scraping Summary for (\d+) URLs', line)
                        if match:
                            doc_count = int(match.group(1))
                    # Parse "⏭️  Skipped (hash):   X"
                    elif '⏭️  Skipped (hash):' in line or 'Skipped (hash):' in line:
                        match = re.search(r'Skipped \(hash\):\s+(\d+)', line)
                        if match:
                            skipped_count = int(match.group(1))
                    # Parse "✅ New/Updated:      X" (fallback if skipped count not found)
                    elif '✅ New/Updated:' in line or 'New/Updated:' in line:
                        match = re.search(r'New/Updated:\s+(-?\d+)', line)
                        if match:
                            new_updated = int(match.group(1))
                            # If negative, all were skipped; calculate doc_count if not already set
                            if new_updated < 0 and doc_count == 0:
                                doc_count = abs(new_updated) + skipped_count
                    # Parse "Scraping complete: X document(s) processed" (used by URL-type sources)
                    elif 'Scraping complete:' in line and 'document(s) processed' in line:
                        match = re.search(r'Scraping complete:\s*(\d+)\s*document', line)
                        if match and doc_count == 0:
                            doc_count = int(match.group(1))
            except Exception:
                # Parsing errors should not fail the whole scrape; just fall back to zeros
                pass

            if return_code != 0:
                # Treat non-zero exit as failure, include tail of output for context
                tail = '\n'.join(output_lines[-20:])
                error_msg = f"Non-zero exit code {return_code} for {name}.\n{tail}"
                return {
                    'success': False,
                    'name': name,
                    'error': error_msg,
                    'duration': duration
                }

            return {
                'success': True,
                'name': name,
                'doc_count': doc_count,
                'skipped_count': skipped_count,
                'duration': duration,
                'output': combined_output
            }
        except Exception as e:
            return {
                'success': False,
                'name': name,
                'error': str(e),
                'duration': time.time() - start_time
            }
    
    def _scrape_domain_sequential(self, domain: str, domain_sources: list[Dict], 
                                  auto_validate: bool, validate_per_source: bool = False) -> Dict:
        """
        Scrape all sources for a domain sequentially (within a single thread)
        
        Args:
            domain: Domain name (for logging)
            domain_sources: List of sources for this domain
            auto_validate: If True, validate after all sources complete
            validate_per_source: If True, validate after each source (default: False)
        
        Returns:
            Dict with 'successful', 'failed', and 'validation_failures' lists
        """
        domain_results = {
            'successful': [],
            'failed': [],
            'validation_failures': []
        }
        
        print(f"\n📦 Domain: {domain} ({len(domain_sources)} sources)")
        
        for source in domain_sources:
            result = self.scrape_source(source)
            if result['success']:
                domain_results['successful'].append(result)
                skipped_msg = f" ({result['skipped_count']} skipped)" if result.get('skipped_count', 0) > 0 else ""
                print(f"  ✅ {result['name']}: {result['doc_count']} docs{skipped_msg} ({format_duration(result['duration'])})")
            else:
                domain_results['failed'].append(result)
                print(f"  ❌ {result['name']}: {result.get('error', 'Unknown error')}")
            
            # Auto-validate per-source if requested (default: False to avoid redundancy)
            if validate_per_source and auto_validate and result['success']:
                validation = self.validate_source(source)
                if not validation['passed']:
                    # Distinguish expected vs unexpected failures
                    domain_results['validation_failures'].append({
                        'name': source['name'],
                        'issues': validation['issues'],
                        'expected': validation.get('expected_filtered', False)
                    })
                    if validation.get('expected_filtered'):
                        print(f"  ⚠️  Validation warning for {source['name']} (expected due to age filtering): {len(validation['issues'])} issues")
                    else:
                        print(f"  ⚠️  Validation issues for {source['name']}: {len(validation['issues'])} issues")
        
        return domain_results
    
    def validate_source(self, source: Dict) -> Dict:
        """Validate scraped source"""
        # Handle url-type sources differently (single file, not directory)
        if source['type'] == 'url':
            if 'output' not in source:
                return {'passed': False, 'issues': ["url-type source must have 'output' field"]}
            
            output_file = self.base_dir / source['output']
            if not output_file.exists():
                return {'passed': False, 'issues': [f"Output file does not exist: {output_file}"]}
            
            # For single file sources, validate it has frontmatter
            content = output_file.read_text(encoding='utf-8')
            if not content.startswith('---'):
                return {'passed': False, 'issues': [f"Missing frontmatter in {output_file.name}"]}
            
            # Check required frontmatter fields
            try:
                frontmatter_end = content.find('---', 3)
                frontmatter_text = content[3:frontmatter_end].strip()
                frontmatter = yaml.safe_load(frontmatter_text)
                
                required_fields = ['source_url', 'last_fetched', 'content_hash']
                issues = []
                for field in required_fields:
                    if field not in frontmatter:
                        issues.append(f"Missing frontmatter field '{field}'")
                
                if issues:
                    return {'passed': False, 'issues': issues}
                
                return {'passed': True, 'issues': [], 'file_count': 1}
            except Exception as e:
                return {'passed': False, 'issues': [f"Invalid frontmatter: {e}"]}
        
        # For sitemap/docs-map sources, validate directory of files
        base_output = source.get('output', self._auto_detect_output_dir(source))
        
        # For sitemap sources with filters, extract category from filter to check correct subdirectory
        # Example: filter="/en/docs/" -> category="docs", check "docs-claude-com/docs/"
        # Example: filter="/engineering/" -> category="engineering", check "anthropic-com/engineering/"
        if source['type'] == 'sitemap' and 'filter' in source:
            filter_path = source['filter'].strip('/')
            # Extract category from filter
            parts = filter_path.split('/')
            if len(parts) >= 2 and parts[1]:
                # Format: "/en/docs/" -> parts = ["en", "docs"] -> category = "docs"
                category = parts[1]
                output_dir = self.base_dir / base_output / category
            elif len(parts) == 1 and parts[0]:
                # Format: "/engineering/" -> parts = ["engineering"] -> category = "engineering"
                category = parts[0]
                output_dir = self.base_dir / base_output / category
            else:
                # Fallback: check base directory if filter format is unexpected
                output_dir = self.base_dir / base_output
        else:
            # For docs-map or sources without filters, check base directory
            output_dir = self.base_dir / base_output
        
        if not output_dir.exists():
            return {'passed': False, 'issues': [f"Output directory does not exist: {output_dir}"]}
        
        md_files = list(output_dir.glob("**/*.md"))
        issues = []
        expected_filtered = False
        
        # Check file count (if expected_count provided)
        # Note: expected_count is optional and auto-updates within tolerance
        if 'expected_count' in source:
            expected = source['expected_count']
            actual = len(md_files)
            tolerance = source.get('expected_count_tolerance', 10)  # Allow ±10 docs by default
            
            # Check if count is within tolerance range
            if abs(actual - expected) > tolerance:
                # Check if age filtering is active (expected mismatch)
                if source.get('max_age_days') and actual < expected:
                    # Age filtering is active, lower count is expected
                    expected_filtered = True
                    issues.append(f"File count: {actual} (expected {expected}, filtered by age)")
                else:
                    # Significant mismatch - warn but don't fail
                    issues.append(f"File count outside tolerance: expected {expected} ±{tolerance}, got {actual}")
            elif actual != expected:
                # Within tolerance - auto-update expected_count for next run
                issues.append(f"File count: {actual} (expected {expected}, auto-updating)")
                # Return update request to caller
                return {
                    'passed': True,
                    'issues': issues,
                    'file_count': actual,
                    'expected_filtered': False,
                    'auto_update': {
                        'expected_count': actual
                    }
                }
        
        # Check sample files for frontmatter
        sample_files = md_files[:5] if len(md_files) >= 5 else md_files
        for file in sample_files:
            content = file.read_text(encoding='utf-8')
            if not content.startswith('---'):
                issues.append(f"Missing frontmatter: {file}")
                continue
            
            # Check required frontmatter fields
            try:
                frontmatter_end = content.find('---', 3)
                frontmatter_text = content[3:frontmatter_end].strip()
                frontmatter = yaml.safe_load(frontmatter_text)
                
                required_fields = ['source_url', 'last_fetched', 'content_hash']
                for field in required_fields:
                    if field not in frontmatter:
                        issues.append(f"Missing frontmatter field '{field}' in {file}")
            except Exception as e:
                issues.append(f"Invalid frontmatter in {file}: {e}")
        
        return {
            'passed': len(issues) == 0 or expected_filtered,  # Pass if only expected filtering issues
            'issues': issues,
            'file_count': len(md_files),
            'expected_filtered': expected_filtered
        }
    
    def _auto_detect_output_dir(self, source: Dict) -> str:
        """Auto-detect output directory from source URL using config mappings"""
        from urllib.parse import urlparse
        from utils.config_helpers import get_output_dir_mapping
        
        url = source.get('url', '')
        parsed = urlparse(url)
        domain = parsed.netloc

        # Get mapping (always returns a value via smart fallback)
        return get_output_dir_mapping(domain)
    
    def scrape_all(self, sources: list[Dict], parallel: bool = True,
                   auto_validate: bool = True, validate_per_source: bool = False,
                   config_path: Path | None = None) -> Dict:
        """
        Scrape all sources

        Args:
            sources: List of source dictionaries
            parallel: If True, scrape different domains in parallel
            auto_validate: If True, validate after all sources complete
            validate_per_source: If True, validate after each source (default: False, avoids redundancy)

        Returns:
            Dict with results
        """
        # Filter out disabled sources (enabled: false)
        disabled_sources = [s for s in sources if s.get('enabled') is False]
        if disabled_sources:
            disabled_names = [s['name'] for s in disabled_sources]
            print(f"\n⏭️  Skipping {len(disabled_sources)} disabled source(s): {', '.join(disabled_names)}")
        sources = [s for s in sources if s.get('enabled', True)]

        results = {
            'successful': [],
            'failed': [],
            'validation_failures': []
        }

        start_time = time.time()

        if parallel and len(sources) > 1:
            # Group sources by domain (for rate limiting safety)
            # Different domains can run in parallel, same domain runs sequentially
            from collections import defaultdict
            from urllib.parse import urlparse
            
            grouped_by_domain = defaultdict(list)
            for source in sources:
                domain = urlparse(source['url']).netloc
                grouped_by_domain[domain].append(source)
            
            print(f"\n🚀 Scraping {len(sources)} sources from {len(grouped_by_domain)} domains")
            print(f"   Parallel execution: max {self.max_workers} workers (one per domain)")
            
            # Scrape domains in parallel, but sources within same domain sequentially
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(grouped_by_domain), self.max_workers)) as executor:
                futures = {}
                for domain, domain_sources in grouped_by_domain.items():
                    # Each domain gets its own thread, sources within domain run sequentially
                    future = executor.submit(self._scrape_domain_sequential, domain, domain_sources, 
                                           auto_validate, validate_per_source)
                    futures[future] = domain
                
                for future in concurrent.futures.as_completed(futures):
                    domain = futures[future]
                    try:
                        domain_results = future.result()
                        # Merge results
                        results['successful'].extend(domain_results['successful'])
                        results['failed'].extend(domain_results['failed'])
                        results['validation_failures'].extend(domain_results.get('validation_failures', []))
                        
                        for result in domain_results['successful']:
                            skipped_msg = f" ({result['skipped_count']} skipped)" if result.get('skipped_count', 0) > 0 else ""
                            log_with_timestamp(f"✅ {result['name']}: {result['doc_count']} docs{skipped_msg} ({format_duration(result['duration'])})")
                        for result in domain_results['failed']:
                            log_with_timestamp(f"❌ {result['name']}: {result.get('error', 'Unknown error')}")
                    except Exception as e:
                        results['failed'].append({
                            'success': False,
                            'name': domain,
                            'error': str(e)
                        })
                        print(f"❌ {domain}: {e}")
        else:
            # Sequential scraping
            print(f"\n📥 Scraping {len(sources)} sources sequentially")
            for source in sources:
                result = self.scrape_source(source)
                if result['success']:
                    results['successful'].append(result)
                    skipped_msg = f" ({result['skipped_count']} skipped)" if result.get('skipped_count', 0) > 0 else ""
                    log_with_timestamp(f"✅ {result['name']}: {result['doc_count']} docs{skipped_msg} ({format_duration(result['duration'])})")
                else:
                    results['failed'].append(result)
                    log_with_timestamp(f"❌ {result['name']}: {result.get('error', 'Unknown error')}")
        
        # Auto-validate if requested (only validate successful sources)
        if auto_validate:
            # Only validate sources that were successfully scraped
            successful_source_names = {r['name'] for r in results['successful']}
            sources_to_validate = [s for s in sources if s['name'] in successful_source_names]
            
            if sources_to_validate:
                print(f"\n🔍 Validating sources...")
                # Parallelize validation since each source validation is independent
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(sources_to_validate), self.max_workers)) as executor:
                    validation_futures = {executor.submit(self.validate_source, source): source for source in sources_to_validate}
                    
                    for future in concurrent.futures.as_completed(validation_futures):
                        source = validation_futures[future]
                        try:
                            validation = future.result()
                            
                            # Check if auto-update is requested
                            if validation.get('auto_update'):
                                # Store auto-update for config file update later
                                if 'auto_updates' not in results:
                                    results['auto_updates'] = []
                                results['auto_updates'].append({
                                    'source_name': source['name'],
                                    'updates': validation['auto_update']
                                })
                                print(f"✅ Validation passed for {source['name']}: {validation['file_count']} files")
                                for issue in validation['issues']:
                                    print(f"   ℹ️  {issue}")
                            elif not validation['passed']:
                                # Distinguish between expected (age filtering) and unexpected failures
                                if validation.get('expected_filtered'):
                                    # Expected filtering - show as warning, not failure
                                    results['validation_failures'].append({
                                        'name': source['name'],
                                        'issues': validation['issues'],
                                        'expected': True
                                    })
                                    print(f"⚠️  Validation warning for {source['name']} (expected due to age filtering):")
                                    for issue in validation['issues']:
                                        print(f"   - {issue}")
                                else:
                                    # Unexpected failure
                                    results['validation_failures'].append({
                                        'name': source['name'],
                                        'issues': validation['issues'],
                                        'expected': False
                                    })
                                    print(f"❌ Validation failed for {source['name']}:")
                                    for issue in validation['issues']:
                                        print(f"   - {issue}")
                            else:
                                print(f"✅ Validation passed for {source['name']}: {validation['file_count']} files")
                        except Exception as e:
                            results['validation_failures'].append({
                                'name': source['name'],
                                'issues': [f"Validation error: {str(e)}"],
                                'expected': False
                            })
                            print(f"❌ Validation error for {source['name']}: {e}")
        
        total_duration = time.time() - start_time
        results['total_duration'] = total_duration
        
        # Auto-update config file if requested and config_path provided
        if config_path and results.get('auto_updates'):
            try:
                self._update_source_config(config_path, results['auto_updates'], sources)
            except Exception as e:
                print(f"\n⚠️  Failed to auto-update config: {e}")
                # Non-fatal - scraping succeeded even if auto-update failed
        
        return results
    
    def _update_source_config(self, config_path: Path, auto_updates: list[Dict], sources: list[Dict]):
        """Update sources.json with auto-updated expected_count values"""
        from datetime import datetime, timezone
        
        print(f"\n📝 Auto-updating config: {config_path.name}")
        
        # Apply updates to sources
        updated_count = 0
        for update_req in auto_updates:
            source_name = update_req['source_name']
            updates = update_req['updates']
            
            # Find source in list and update
            for source in sources:
                if source['name'] == source_name:
                    for key, value in updates.items():
                        old_value = source.get(key)
                        source[key] = value
                        if old_value != value:
                            print(f"   - {source_name}: {key} {old_value} → {value}")
                            updated_count += 1
                    # Add last_updated timestamp
                    source['last_scraped'] = datetime.now(timezone.utc).strftime('%Y-%m-%d')
                    break
        
        if updated_count > 0:
            # Write back to config file
            try:
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(sources, f, indent=2, ensure_ascii=False)
                    f.write('\n')  # Add trailing newline
                print(f"   ✅ Updated {updated_count} value(s) in {config_path.name}")
            except Exception as e:
                raise RuntimeError(f"Failed to write config: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scrape multiple sources in parallel',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Scrape all sources (uses default config: references/sources.json)
  python scrape_all_sources.py
  
  # Scrape all sources from custom config file
  python scrape_all_sources.py --config sources.json
  
  # Parallel execution with auto-validation
  python scrape_all_sources.py --config sources.json --parallel --auto-validate
  
  # Skip existing documents (idempotent mode)
  python scrape_all_sources.py --config sources.json --skip-existing
  
  # Sequential execution (no parallelization)
  python scrape_all_sources.py --config sources.json --no-parallel
  
  # Auto-detect and cleanup drift after scraping
  python scrape_all_sources.py --config sources.json --auto-cleanup
  
  # Detect drift only (no cleanup)
  python scrape_all_sources.py --config sources.json --detect-drift
  
  # Detect and cleanup drift
  python scrape_all_sources.py --config sources.json --detect-drift --cleanup-drift
        """
    )
    
    # Get defaults from config (before using in parser)
    default_max_workers = get_scraping_max_source_workers()
    
    # Default config path: sources.json in references directory (at skill root)
    from utils.common_paths import get_skill_dir
    skill_root = get_skill_dir()
    default_config_path = skill_root / 'references' / 'sources.json'
    
    parser.add_argument('--config', 
                       default=str(default_config_path),
                       help=f'JSON config file with sources (default: {default_config_path})')
    parser.add_argument('--parallel', action='store_true', default=True,
                       help='Enable parallel execution (default: True)')
    parser.add_argument('--no-parallel', dest='parallel', action='store_false',
                       help='Disable parallel execution')
    parser.add_argument('--max-workers', type=int, default=default_max_workers,
                       help=f'Max parallel workers (default: {default_max_workers}, from config)')
    parser.add_argument('--auto-validate', action='store_true', default=False,
                       help='Auto-validate after scraping (default: False)')
    parser.add_argument('--no-auto-validate', dest='auto_validate', action='store_false',
                       help='Disable auto-validation')
    parser.add_argument('--validate-per-source', action='store_true', default=False,
                       help='Validate after each source (default: False, only validates at end)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip unchanged documents (idempotent mode)')
    add_base_dir_argument(parser)
    parser.add_argument('--detect-drift', action='store_true',
                       help='Detect drift (404s, missing files, hash mismatches) after scraping')
    parser.add_argument('--cleanup-drift', action='store_true',
                       help='Automatically cleanup drift (requires --detect-drift)')
    parser.add_argument('--auto-cleanup', action='store_true',
                       help='Automatically detect and cleanup drift after scraping (equivalent to --detect-drift --cleanup-drift)')
    parser.add_argument('--drift-max-workers', type=int, default=5,
                       help='Maximum parallel workers for drift detection (default: 5)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable full debugging (file logging, DEBUG level)')
    parser.add_argument('--with-timing', action='store_true',
                       help='Enable HTTP timing tracking for audit runs (overrides runtime.yaml setting)')

    args = parser.parse_args()

    # Declare global so we can reassign logger if --debug is passed
    global logger

    # Print dev/prod mode banner for visibility
    from utils.dev_mode import print_mode_banner
    from utils.path_config import get_base_dir
    print_mode_banner(logger)
    logger.info(f"Canonical dir: {get_base_dir()}")

    # Handle --debug flag early (before any heavy work)
    # Sets environment variables for child processes and reconfigures logging
    if args.debug:
        os.environ['CLAUDE_DOCS_LOG_TO_FILE'] = 'true'
        os.environ['CLAUDE_DOCS_LOG_LEVEL'] = 'DEBUG'
        # Note: Main logger already initialized, but child processes will inherit these env vars
        # Reinitialize the logger with debug settings for this process
        import logging
        from utils.logging_utils import setup_script_logging
        logger = setup_script_logging(__file__, log_level=logging.DEBUG, log_category="scrape",
                                      enable_file_logging=True)
        logger.info("Debug mode enabled: file logging ON, log level DEBUG")

    # Handle --with-timing flag (overrides runtime.yaml track_http_timings setting)
    # Useful for one-off audit runs when you want HTTP timing data without modifying config
    if args.with_timing:
        os.environ['CLAUDE_DOCS_HTTP_TIMING'] = 'true'
        logger.info("HTTP timing enabled via --with-timing flag")
    
    # Load sources from config
    config_path = Path(args.config)
    
    # Get skill root using centralized utility (already imported above)
    skill_root_for_config = get_skill_dir()
    
    # Resolve relative paths relative to skill root
    if not config_path.is_absolute():
        # Try relative to skill root first
        candidate = skill_root_for_config / config_path
        if candidate.exists():
            config_path = candidate
        else:
            # Try relative to current working directory
            candidate = Path.cwd() / config_path
            if candidate.exists():
                config_path = candidate
    
    if not config_path.exists():
        default_config = skill_root_for_config / 'references' / 'sources.json'
        print(f"❌ Config file not found: {config_path}")
        print(f"\n💡 Helpful information:")
        print(f"   - Expected default location: {default_config}")
        print(f"   - Current working directory: {Path.cwd()}")
        print(f"   - Skill root directory: {skill_root_for_config}")
        print(f"   - Config argument provided: {args.config}")
        print(f"\n   To fix this:")
        print(f"   1. Create {default_config} with your source configurations")
        example_path = skill_root_for_config / 'references' / 'sources.json.example'
        if example_path.exists():
            print(f"   2. Copy from example: {example_path}")
        else:
            print(f"   2. Or copy from {skill_root_for_config / 'sources.json.example'} if it exists")
        print(f"   3. Or provide --config with an absolute path or path relative to skill root")
        print(f"\n   Example sources.json structure:")
        print(f'   [')
        print(f'     {{"name": "docs-claude-com-docs", "type": "sitemap", "url": "https://docs.claude.com/sitemap.xml", "filter": "/en/docs/", "skip_existing": true}},')
        print(f'     {{"name": "code-claude-com-docs", "type": "docs-map", "url": "https://code.claude.com/docs/en/claude_code_docs_map.md", "skip_existing": true}}')
        print(f'   ]')
        sys.exit(1)
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            sources = json.load(f)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)
    
    # Apply --skip-existing to all sources if specified
    if args.skip_existing:
        for source in sources:
            source['skip_existing'] = True
    
    # Resolve base directory using helper
    base_dir = resolve_base_dir_from_args(args)
    
    # Get scripts directory using centralized utility (already imported)
    from utils.common_paths import get_scripts_dir
    scripts_dir_resolved = get_scripts_dir()
    
    scraper = MultiSourceScraper(
        base_dir, 
        scripts_dir_resolved, 
        max_workers=args.max_workers if args.max_workers != default_max_workers else None
    )
    
    print(f"\n{'='*60}")
    print(f"MULTI-SOURCE SCRAPING")
    print(f"{'='*60}")
    print(f"Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Sources: {len(sources)}")
    print(f"Parallel: {args.parallel} (max {args.max_workers} workers)")
    print(f"Auto-validate: {args.auto_validate}")
    print(f"Validate per source: {args.validate_per_source}")
    print(f"Skip existing: {args.skip_existing}")
    print(f"Debug mode: {args.debug}")
    print(f"HTTP timing: {args.with_timing or 'config default'}")
    
    # Handle --auto-cleanup flag (equivalent to --detect-drift --cleanup-drift)
    if args.auto_cleanup:
        args.detect_drift = True
        args.cleanup_drift = True
        print(f"Auto-cleanup: Enabled (will detect and cleanup drift)")
    
    print()
    
    results = scraper.scrape_all(sources, parallel=args.parallel, auto_validate=args.auto_validate,
                                validate_per_source=args.validate_per_source, config_path=config_path)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successful sources: {len(results['successful'])}")
    print(f"❌ Failed sources: {len(results['failed'])}")

    # Log aggregate summary for observability (structured for log parsing)
    logger.info(f"AGGREGATE SUMMARY: sources={len(sources)}, successful={len(results['successful'])}, failed={len(results['failed'])}")
    
    # Count unexpected validation failures (exclude expected age filtering warnings)
    unexpected_validation_failures = [f for f in results['validation_failures'] if not f.get('expected', False)]
    if unexpected_validation_failures:
        print(f"⚠️  Validation failures: {len(unexpected_validation_failures)}")
    elif results['validation_failures']:
        print(f"⚠️  Validation warnings: {len(results['validation_failures'])} (expected due to age filtering)")
    
    total_docs = sum(r.get('doc_count', 0) for r in results['successful'])
    total_skipped = sum(r.get('skipped_count', 0) for r in results['successful'])
    total_new = max(0, total_docs - total_skipped)

    print(f"\n📄 Documents:")
    print(f"   - New/Updated: {total_new}")
    if total_skipped > 0:
        print(f"   - Skipped (unchanged): {total_skipped}")
    print(f"   - Total processed: {total_docs}")
    print(f"\n⏱️  Total duration: {format_duration(results['total_duration'])}")

    # Log document totals for observability (structured for log parsing)
    logger.info(f"DOCUMENT TOTALS: new_updated={total_new}, skipped={total_skipped}, total_processed={total_docs}, duration_seconds={results['total_duration']:.2f}")

    # Per-source timing breakdown (sorted by duration, slowest first)
    if results['successful']:
        print(f"\n📊 Per-Source Timing Breakdown:")
        print(f"   {'Source':<45} {'Duration':>10} {'Docs':>6} {'Rate':>10}")
        print(f"   {'-'*45} {'-'*10} {'-'*6} {'-'*10}")

        # Sort by duration descending (slowest first to identify bottlenecks)
        sorted_results = sorted(results['successful'], key=lambda r: r.get('duration', 0), reverse=True)

        for r in sorted_results:
            name = r['name'][:44]  # Truncate long names
            duration = format_duration(r.get('duration', 0))
            docs = r.get('doc_count', 0)
            rate = f"{docs / max(r.get('duration', 0.001), 0.001):.1f}/s" if docs > 0 else "N/A"
            print(f"   {name:<45} {duration:>10} {docs:>6} {rate:>10}")

        # Overall throughput
        if total_docs > 0 and results['total_duration'] > 0:
            overall_rate = total_docs / results['total_duration']
            print(f"\n   Overall throughput: {overall_rate:.1f} docs/sec")

        # Log per-source timing for observability (structured for log parsing)
        for r in sorted_results:
            logger.info(f"SOURCE TIMING: name={r['name']}, duration_seconds={r.get('duration', 0):.2f}, docs={r.get('doc_count', 0)}, skipped={r.get('skipped_count', 0)}")
    
    if results['failed']:
        print(f"\n❌ Failed sources:")
        for failure in results['failed']:
            print(f"   - {failure['name']}: {failure.get('error', 'Unknown error')}")
    
    if results['validation_failures']:
        # Separate expected (age filtering) from unexpected failures
        expected_failures = [f for f in results['validation_failures'] if f.get('expected', False)]
        unexpected_failures = [f for f in results['validation_failures'] if not f.get('expected', False)]
        
        if expected_failures:
            print(f"\n⚠️  Validation warnings (expected due to age filtering):")
            for failure in expected_failures:
                print(f"   - {failure['name']}: {', '.join(failure['issues'])}")
        
        if unexpected_failures:
            print(f"\n❌ Validation failures:")
            for failure in unexpected_failures:
                print(f"   - {failure['name']}: {', '.join(failure['issues'])}")
    
    # Detect drift if requested
    if args.detect_drift:
        print(f"\n{'='*60}")
        print(f"DRIFT DETECTION")
        print(f"{'='*60}")
        
        try:
            from detect_changes import ChangeDetector
            from cleanup_drift import DriftCleaner
            
            drift_detected = False
            for result in results['successful']:
                source = next((s for s in sources if s['name'] == result['name']), None)
                if not source:
                    continue
                
                # Determine output subdirectory
                output_subdir = scraper._auto_detect_output_dir(source)
                
                # Extract category from filter if sitemap source
                if source['type'] == 'sitemap' and 'filter' in source:
                    filter_path = source['filter'].strip('/')
                    parts = filter_path.split('/')
                    if len(parts) >= 2 and parts[1]:
                        category = parts[1]
                        output_subdir = f"{output_subdir}/{category}"
                    elif len(parts) == 1 and parts[0]:
                        category = parts[0]
                        output_subdir = f"{output_subdir}/{category}"
                
                print(f"\n🔍 Detecting drift for: {result['name']}")
                
                # Load index and get indexed URLs
                detector = ChangeDetector(base_dir)
                index = detector.load_index()
                indexed_urls = detector.get_indexed_urls(index, output_subdir.split('/')[0])
                
                if not indexed_urls:
                    print(f"  ⏭️  No indexed URLs found for {result['name']}")
                    continue
                
                # Check for 404s
                print(f"  Checking for 404 URLs...")
                url_404s = detector.check_404_urls(set(indexed_urls.keys()), max_workers=args.drift_max_workers)
                url_404_count = sum(1 for is_404 in url_404s.values() if is_404)
                
                # Check for missing files
                print(f"  Checking for missing files...")
                cleaner = DriftCleaner(base_dir, dry_run=not args.cleanup_drift)
                missing = cleaner.find_missing_files(index)
                missing_count = len(missing)
                
                # Compare content hashes
                print(f"  Comparing content hashes...")
                hash_mismatches = detector.compare_content_hashes(indexed_urls, output_subdir.split('/')[0])
                hash_mismatch_count = sum(1 for local, remote in hash_mismatches.values() 
                                         if local and remote and local != remote)
                
                if url_404_count > 0 or missing_count > 0 or hash_mismatch_count > 0:
                    drift_detected = True
                    print(f"\n  ⚠️  Drift detected for {result['name']}:")
                    print(f"     - 404 URLs: {url_404_count}")
                    print(f"     - Missing files: {missing_count}")
                    print(f"     - Content changes: {hash_mismatch_count}")
                    
                    if args.cleanup_drift:
                        print(f"\n  🧹 Cleaning up drift...")
                        # Clean 404s
                        if url_404_count > 0:
                            files_removed, index_removed = cleaner.clean_404_urls(index, max_workers=args.drift_max_workers)
                            print(f"     Removed {files_removed} files and {index_removed} index entries for 404 URLs")
                        
                        # Clean missing files
                        if missing_count > 0:
                            files_checked, index_removed = cleaner.clean_missing_files(index)
                            print(f"     Removed {index_removed} index entries for missing files")
                        
                        # Write audit log
                        cleaner.write_audit_log()
                else:
                    print(f"  ✅ No drift detected for {result['name']}")
            
            if not drift_detected:
                print(f"\n✅ No drift detected across all sources")
            
        except ImportError as e:
            print(f"⚠️  Drift detection not available: {e}")
            print(f"   Ensure detect_changes.py and cleanup_drift.py are available")
        except Exception as e:
            print(f"❌ Error during drift detection: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"{'='*60}\n")
    
    # Exit code - only fail on actual scraping failures, not validation warnings
    # Validation failures are warnings that don't prevent successful scraping
    # Only exit with code 1 if sources actually failed to scrape
    has_scraping_failures = len(results['failed']) > 0
    sys.exit(1 if has_scraping_failures else 0)

if __name__ == '__main__':
    main()

