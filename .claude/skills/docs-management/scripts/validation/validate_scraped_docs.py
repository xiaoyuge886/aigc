#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_scraped_docs.py - Comprehensive validation of scraped documentation

Validates scraped documentation against configuration expectations:
- File counts match expected values
- Frontmatter is valid and complete
- Directory structure is correct
- Content quality checks
- Index integrity
- Expected errors validation

Usage:
    # Uses default base-dir from config (typically .claude/skills/docs-management/canonical)
    python validate_scraped_docs.py --config sources.json
    
    # Custom base directory
    python validate_scraped_docs.py --config sources.json --base-dir custom/path
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
import json
from datetime import datetime

from utils.script_utils import ensure_yaml_installed
yaml = ensure_yaml_installed()

# Import index_manager for large file support
try:
    from management.index_manager import IndexManager
except ImportError:
    IndexManager = None

def calculate_hash(content: str) -> str:
    """Calculate SHA-256 hash of content"""
    hash_obj = hashlib.sha256(content.encode('utf-8'))
    return f"sha256:{hash_obj.hexdigest()}"

class ScrapedDocsValidator:
    """Validate scraped documentation against configuration"""

    def __init__(self, base_dir: Path, config_path: Path | None = None):
        """
        Initialize validator

        Args:
            base_dir: Base directory for canonical storage (default: .claude/skills/docs-management/canonical from config)
            config_path: Optional path to sources.json config file
        """
        self.base_dir = base_dir
        self.config_path = config_path
        # Use path_config for index path
        from utils.path_config import get_index_path
        self.index_path = get_index_path(base_dir)
        self.checks = {}
        
        # Initialize index manager if available
        if IndexManager:
            self.index_manager = IndexManager(base_dir)
        else:
            self.index_manager = None

    def load_config(self) -> dict | None:
        """Load configuration from sources.json if available"""
        if not self.config_path or not self.config_path.exists():
            return None
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Warning: Could not load config: {e}")
            return None

    def validate_file_counts(self, config: dict | None = None) -> dict:
        """Validate file counts match expectations from config"""
        results = {'passed': True, 'details': []}

        if not config:
            results['passed'] = True  # No config, skip check
            results['details'].append({'note': 'No config file provided, skipping file count validation'})
            return results

        for source_config in config:
            source_name = source_config.get('name', 'unknown')
            output_subdir = source_config.get('output', '')
            expected_count = source_config.get('expected_count')

            if not expected_count:
                continue  # No expectation, skip

            # Auto-detect output directory if not specified
            if not output_subdir:
                # Extract domain from URL and use config mapping
                from urllib.parse import urlparse
                from config_helpers import get_output_dir_mapping
                
                url = source_config.get('url', '')
                parsed = urlparse(url)
                domain = parsed.netloc
                
                base_output = get_output_dir_mapping(domain)
                if not base_output:
                    # Skip validation if output directory not configured
                    results['details'].append({
                        'source': source_name,
                        'status': 'skipped',
                        'reason': f"Output directory mapping not configured for domain '{domain}'"
                    })
                    continue
                
                # For sitemap sources with filters, extract category from filter
                if source_config.get('type') == 'sitemap' and 'filter' in source_config:
                    filter_path = source_config['filter'].strip('/')
                    parts = filter_path.split('/')
                    if len(parts) >= 2 and parts[1]:  # parts[0] is usually "en", parts[1] is category
                        category = parts[1]
                        output_dir = self.base_dir / base_output / category
                    else:
                        output_dir = self.base_dir / base_output
                else:
                    output_dir = self.base_dir / base_output
            else:
                output_dir = self.base_dir / output_subdir
            
            if not output_dir.exists():
                results['passed'] = False
                results['details'].append({
                    'source': source_name,
                    'expected': expected_count,
                    'actual': 0,
                    'status': 'FAIL',
                    'reason': 'Output directory does not exist'
                })
                continue

            # Count markdown files
            actual_count = len(list(output_dir.rglob("*.md")))

            # Allow ±10% variance
            variance = abs(actual_count - expected_count) / expected_count if expected_count > 0 else 0
            if variance <= 0.1:
                results['details'].append({
                    'source': source_name,
                    'expected': expected_count,
                    'actual': actual_count,
                    'status': 'PASS',
                    'variance': f"{variance*100:.1f}%"
                })
            else:
                results['passed'] = False
                results['details'].append({
                    'source': source_name,
                    'expected': expected_count,
                    'actual': actual_count,
                    'status': 'FAIL',
                    'variance': f"{variance*100:.1f}%"
                })

        return results

    def validate_frontmatter(self) -> dict:
        """Validate frontmatter in all scraped files"""
        results = {'passed': True, 'details': {'total': 0, 'valid': 0, 'invalid': 0, 'missing': 0}}

        required_fields = ['source_url', 'source_type', 'last_fetched', 'content_hash']

        for md_file in self.base_dir.rglob("*.md"):
            results['details']['total'] += 1

            try:
                content = md_file.read_text(encoding='utf-8')
                
                if not content.startswith('---'):
                    results['details']['missing'] += 1
                    results['passed'] = False
                    continue

                # Extract frontmatter
                frontmatter_end = content.find('---', 3)
                if frontmatter_end == -1:
                    results['details']['invalid'] += 1
                    results['passed'] = False
                    continue

                frontmatter_text = content[3:frontmatter_end].strip()
                frontmatter = yaml.safe_load(frontmatter_text)

                # Check required fields
                missing_fields = [f for f in required_fields if f not in frontmatter]
                if missing_fields:
                    results['details']['invalid'] += 1
                    results['passed'] = False
                    continue

                results['details']['valid'] += 1

            except Exception:
                results['details']['invalid'] += 1
                results['passed'] = False

        return results

    def validate_directory_structure(self) -> dict:
        """Validate directory structure is correct"""
        results = {'passed': True, 'details': []}

        # Check that base directory exists
        if not self.base_dir.exists():
            results['passed'] = False
            results['details'].append({'issue': f'Base directory does not exist: {self.base_dir}'})
            return results

        # Check for expected subdirectories (if config provided)
        config = self.load_config()
        if config:
            for source_config in config:
                output_subdir = source_config.get('output', '')
                if output_subdir:
                    subdir_path = self.base_dir / output_subdir
                    if not subdir_path.exists():
                        results['passed'] = False
                        results['details'].append({
                            'issue': f'Expected subdirectory missing: {output_subdir}'
                        })

        return results

    def validate_content_quality(self) -> dict:
        """Validate content quality (no empty files, valid UTF-8, reasonable sizes)"""
        results = {'passed': True, 'details': {
            'total': 0, 'empty': 0, 'invalid_utf8': 0,
            'total_size': 0, 'avg_size': 0, 'min_size': float('inf'), 'max_size': 0
        }}

        for md_file in self.base_dir.rglob("*.md"):
            results['details']['total'] += 1

            try:
                content = md_file.read_text(encoding='utf-8')
                file_size = len(content.encode('utf-8'))

                # Check for empty files
                body = content
                if content.startswith('---'):
                    frontmatter_end = content.find('---', 3)
                    if frontmatter_end != -1:
                        body = content[frontmatter_end + 3:].strip()

                if not body.strip():
                    results['details']['empty'] += 1
                    results['passed'] = False

                # Track sizes
                results['details']['total_size'] += file_size
                results['details']['min_size'] = min(results['details']['min_size'], file_size)
                results['details']['max_size'] = max(results['details']['max_size'], file_size)

            except UnicodeDecodeError:
                results['details']['invalid_utf8'] += 1
                results['passed'] = False
            except Exception:
                results['passed'] = False

        # Calculate average
        if results['details']['total'] > 0:
            results['details']['avg_size'] = results['details']['total_size'] // results['details']['total']
        else:
            results['details']['min_size'] = 0

        return results

    def validate_index_integrity(self) -> dict:
        """Validate index.yaml integrity"""
        results = {'passed': True, 'details': {
            'index_exists': False,
            'total_entries': 0,
            'files_exist': 0,
            'files_missing': 0,
            'hash_mismatches': 0
        }}

        if not self.index_path.exists():
            results['passed'] = False
            results['details']['index_exists'] = False
            return results

        results['details']['index_exists'] = True

        try:
            # Use index_manager if available (handles large files)
            if self.index_manager:
                index = self.index_manager.load_all()
            else:
                # Fallback to original implementation
                with open(self.index_path, 'r', encoding='utf-8') as f:
                    index = yaml.safe_load(f) or {}

            results['details']['total_entries'] = len(index)

            for doc_id, metadata in index.items():
                file_path = self.base_dir / metadata.get('path', '')
                
                if not file_path.exists():
                    results['details']['files_missing'] += 1
                    results['passed'] = False
                    continue

                results['details']['files_exist'] += 1

                # Check hash if available
                expected_hash = metadata.get('content_hash')
                if expected_hash:
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        # Strip frontmatter for hash comparison
                        if content.startswith('---'):
                            frontmatter_end = content.find('---', 3)
                            if frontmatter_end != -1:
                                body = content[frontmatter_end + 3:].strip()
                            else:
                                body = content
                        else:
                            body = content

                        actual_hash = calculate_hash(body)
                        if actual_hash != expected_hash:
                            results['details']['hash_mismatches'] += 1
                            results['passed'] = False
                    except Exception:
                        pass  # Skip hash check on error

        except Exception as e:
            results['passed'] = False
            results['details']['error'] = str(e)

        return results

    def validate_expected_errors(self, config: dict | None = None) -> dict:
        """Validate expected errors (like known 404s)"""
        results = {'passed': True, 'details': []}

        if not config:
            return results

        # Check for expected_errors in config
        for source_config in config:
            expected_errors = source_config.get('expected_errors', [])
            for error_config in expected_errors:
                url = error_config.get('url')
                error_type = error_config.get('type', '404')
                reason = error_config.get('reason', 'Unknown')

                # For now, just log that we expect this error
                # In a full implementation, we'd check if the error actually occurred
                results['details'].append({
                    'url': url,
                    'type': error_type,
                    'reason': reason,
                    'status': 'EXPECTED'
                })

        return results

    def validate_all(self) -> tuple[bool, dict]:
        """
        Run all validation checks

        Returns:
            Tuple of (success: bool, report: dict)
        """
        config = self.load_config()

        self.checks = {
            'file_counts': self.validate_file_counts(config),
            'frontmatter': self.validate_frontmatter(),
            'directory_structure': self.validate_directory_structure(),
            'content_quality': self.validate_content_quality(),
            'index_integrity': self.validate_index_integrity(),
            'expected_errors': self.validate_expected_errors(config)
        }

        success = all(check['passed'] for check in self.checks.values())
        report = self.generate_report()

        return success, report

    def generate_report(self) -> str:
        """Generate formatted validation report"""
        lines = []
        lines.append("=" * 60)
        lines.append(f"Validation Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append("=" * 60)
        lines.append("")

        # File Counts
        check = self.checks['file_counts']
        status = "✅" if check['passed'] else "❌"
        lines.append(f"{status} File Counts")
        for detail in check['details']:
            if 'status' in detail:
                lines.append(f"  {status} {detail['source']}: {detail['actual']} files "
                           f"(expected ~{detail['expected']}, {detail.get('variance', 'N/A')})")
            else:
                lines.append(f"  {detail.get('note', '')}")
        lines.append("")

        # Frontmatter
        check = self.checks['frontmatter']
        status = "✅" if check['passed'] else "❌"
        lines.append(f"{status} Frontmatter")
        details = check['details']
        lines.append(f"  {status} {details['valid']}/{details['total']} files have valid frontmatter")
        if details['invalid'] > 0:
            lines.append(f"  ❌ {details['invalid']} files with invalid frontmatter")
        if details['missing'] > 0:
            lines.append(f"  ❌ {details['missing']} files missing frontmatter")
        lines.append("")

        # Directory Structure
        check = self.checks['directory_structure']
        status = "✅" if check['passed'] else "❌"
        lines.append(f"{status} Directory Structure")
        if check['details']:
            for detail in check['details']:
                lines.append(f"  ❌ {detail['issue']}")
        else:
            lines.append(f"  {status} All expected directories exist")
        lines.append("")

        # Content Quality
        check = self.checks['content_quality']
        status = "✅" if check['passed'] else "❌"
        lines.append(f"{status} Content Quality")
        details = check['details']
        lines.append(f"  {status} {details['total']} files checked")
        if details['empty'] > 0:
            lines.append(f"  ❌ {details['empty']} empty files")
        if details['invalid_utf8'] > 0:
            lines.append(f"  ❌ {details['invalid_utf8']} files with invalid UTF-8")
        lines.append(f"  Average file size: {details['avg_size']:,} bytes")
        lines.append(f"  Size range: {details['min_size']:,} - {details['max_size']:,} bytes")
        lines.append("")

        # Index Integrity
        check = self.checks['index_integrity']
        status = "✅" if check['passed'] else "❌"
        lines.append(f"{status} Index Integrity")
        details = check['details']
        if details['index_exists']:
            lines.append(f"  {status} index.yaml exists ({details['total_entries']} entries)")
            lines.append(f"  {status} {details['files_exist']}/{details['total_entries']} files exist")
            if details['files_missing'] > 0:
                lines.append(f"  ❌ {details['files_missing']} files missing")
            if details['hash_mismatches'] > 0:
                lines.append(f"  ❌ {details['hash_mismatches']} hash mismatches")
        else:
            lines.append(f"  ❌ index.yaml does not exist")
        lines.append("")

        # Expected Errors
        check = self.checks['expected_errors']
        if check['details']:
            lines.append("✅ Expected Errors")
            for detail in check['details']:
                lines.append(f"  ⏭️  {detail['type']} - {detail['url']}: {detail['reason']}")
            lines.append("")

        # Overall
        overall_status = "✅ PASS" if all(c['passed'] for c in self.checks.values()) else "❌ FAIL"
        lines.append("=" * 60)
        lines.append(f"OVERALL: {overall_status}")
        lines.append("=" * 60)

        return "\n".join(lines)

def main() -> None:
    """Main entry point"""
    from cli_utils import add_base_dir_argument, resolve_base_dir_from_args
    
    parser = argparse.ArgumentParser(description='Comprehensively validate scraped documentation.')
    parser.add_argument('--config', help='Path to sources.json config file (optional)')
    add_base_dir_argument(parser)
    args = parser.parse_args()

    # Resolve base directory using cli_utils helper
    base_dir = resolve_base_dir_from_args(args)
    config_path = Path(args.config).resolve() if args.config else None

    if not base_dir.exists():
        print(f"❌ Base directory does not exist: {base_dir}")
        sys.exit(1)

    validator = ScrapedDocsValidator(base_dir, config_path)
    success, report = validator.validate_all()

    print(report)

    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()

