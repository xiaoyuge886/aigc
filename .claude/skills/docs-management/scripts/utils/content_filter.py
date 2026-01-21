#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
content_filter.py - Filter non-primary content from scraped documentation

Removes site navigation, marketing sections, and other non-content elements
based on source-aware rules defined in config/content_filtering.yaml.

Usage:
    from content_filter import ContentFilter
    
    filter = ContentFilter()
    filtered_markdown = filter.filter_content(markdown_content, source_path='anthropic-com/news/article.md')
    
Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bootstrap; skill_dir = bootstrap.skill_dir; scripts_dir = bootstrap.scripts_dir

import re
import logging

from .script_utils import ensure_yaml_installed

yaml = ensure_yaml_installed()

class ContentFilter:
    """Filter non-primary content from scraped documentation"""
    
    def __init__(self, config_path: Path | None = None):
        """
        Initialize content filter
        
        Args:
            config_path: Path to content_filtering.yaml (auto-detects if not provided)
        """
        self.logger = logging.getLogger(__name__)
        
        # Auto-detect config path if not provided
        if config_path is None:
            script_dir = Path(__file__).parent  # scripts/utils/
            scripts_dir = script_dir.parent      # scripts/
            skill_dir = scripts_dir.parent       # skill root
            config_path = skill_dir / 'config' / 'content_filtering.yaml'
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load filtering configuration from YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            self.logger.debug(f"Loaded content filtering config from {self.config_path}")
            return config
        except Exception as e:
            self.logger.warning(f"Failed to load content filtering config: {e}")
            # Return minimal config so filtering can still work
            return {
                'global_stop_sections': [],
                'source_filters': {},
                'filtering_behavior': {
                    'keep_stop_heading': False,
                    'log_filtered_content': True,
                    'add_filtered_marker': True,
                    'marker_text': '<!-- Content filtered -->'
                }
            }
    
    def _get_source_key(self, source_path: str) -> str | None:
        """
        Extract source key from file path
        
        Args:
            source_path: Path like 'anthropic-com/news/article.md' or 'docs-claude-com/docs/intro.md'
        
        Returns:
            Source key like 'anthropic-com/news' or 'docs-claude-com'
        """
        if not source_path:
            return None
        
        # Normalize path separators
        source_path = source_path.replace('\\', '/')
        
        # Extract domain and first-level subdirectory
        parts = source_path.split('/')
        if len(parts) < 2:
            return parts[0] if parts else None
        
        # Check for news/engineering/research subdirectories
        if parts[0] == 'anthropic-com' and parts[1] in ['news', 'engineering', 'research']:
            return f"{parts[0]}/{parts[1]}"
        
        # Otherwise just return the domain
        return parts[0]
    
    def _get_applicable_filters(self, source_key: str | None) -> list[str]:
        """
        Get list of filter sets that apply to this source
        
        Args:
            source_key: Source key like 'anthropic-com/news'
        
        Returns:
            List of filter set names to apply
        """
        if not source_key or 'source_filters' not in self.config:
            # Default to global filters only
            return ['global_stop_sections']
        
        source_filters = self.config['source_filters']
        
        # Check for exact match
        if source_key in source_filters:
            return source_filters[source_key].get('applies', ['global_stop_sections'])
        
        # No match - use global only
        return ['global_stop_sections']
    
    def _compile_patterns(self, filter_names: list[str]) -> list[dict]:
        """
        Compile regex patterns for the specified filter sets
        
        Args:
            filter_names: Names of filter sets to compile
        
        Returns:
            List of compiled filter rules
        """
        compiled = []
        
        for filter_name in filter_names:
            if filter_name not in self.config:
                continue
            
            filter_rules = self.config[filter_name]
            for rule in filter_rules:
                pattern_str = rule.get('pattern', '')
                if not pattern_str:
                    continue
                
                # Compile regex pattern
                try:
                    if rule.get('regex', False):
                        # Already a regex pattern
                        pattern = re.compile(pattern_str, re.MULTILINE)
                    else:
                        # Literal string match
                        pattern = re.compile(re.escape(pattern_str), re.MULTILINE)
                    
                    compiled.append({
                        'pattern': pattern,
                        'pattern_str': pattern_str,
                        'stop_after': rule.get('stop_after', False),
                        'exclude_if_empty': rule.get('exclude_if_empty', False),
                        'reason': rule.get('reason', 'Filtered section')
                    })
                except re.error as e:
                    self.logger.warning(f"Invalid regex pattern '{pattern_str}': {e}")
        
        return compiled
    
    def _is_section_empty(self, section_content: str) -> bool:
        """
        Check if a section is empty or contains only placeholder text
        
        Args:
            section_content: Content between this heading and next heading
        
        Returns:
            True if section should be considered empty
        """
        if not section_content or section_content.strip() == '':
            return True
        
        # Check against empty section patterns
        empty_patterns = self.config.get('empty_section_patterns', [])
        for pattern in empty_patterns:
            if re.search(pattern, section_content, re.IGNORECASE):
                return True
        
        return False
    
    def filter_content(self, content: str, source_path: str | None = None) -> tuple[str, dict]:
        """
        Filter non-primary content from markdown
        
        Args:
            content: Markdown content to filter
            source_path: Source path for determining filter rules (e.g., 'anthropic-com/news/article.md')
        
        Returns:
            Tuple of (filtered_content, filter_stats)
        """
        if not content:
            return content, {'sections_removed': 0, 'stop_after_triggered': False}
        
        # Determine which filters to apply
        source_key = self._get_source_key(source_path)
        filter_names = self._get_applicable_filters(source_key)
        patterns = self._compile_patterns(filter_names)
        
        if not patterns:
            # No filtering needed
            return content, {'sections_removed': 0, 'stop_after_triggered': False}
        
        # Split content into lines for processing
        lines = content.split('\n')
        filtered_lines = []
        stats = {
            'sections_removed': 0,
            'stop_after_triggered': False,
            'removed_sections': []
        }
        
        keep_stop_heading = self.config.get('filtering_behavior', {}).get('keep_stop_heading', False)
        add_marker = self.config.get('filtering_behavior', {}).get('add_filtered_marker', True)
        marker_text = self.config.get('filtering_behavior', {}).get('marker_text', '<!-- Content filtered -->')
        log_filtered = self.config.get('filtering_behavior', {}).get('log_filtered_content', True)
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check if this line matches any filter pattern
            matched = False
            for rule in patterns:
                if rule['pattern'].search(line):
                    matched = True
                    
                    # Check if we should exclude based on empty content
                    if rule['exclude_if_empty']:
                        # Look ahead to get section content
                        section_lines = []
                        j = i + 1
                        while j < len(lines) and not lines[j].startswith('##'):
                            section_lines.append(lines[j])
                            j += 1
                        section_content = '\n'.join(section_lines)
                        
                        if not self._is_section_empty(section_content):
                            # Section not empty, don't filter
                            matched = False
                            break
                    
                    # Log what we're filtering
                    if log_filtered:
                        self.logger.info(f"Filtering section: {line.strip()} (reason: {rule['reason']})")
                    
                    stats['sections_removed'] += 1
                    stats['removed_sections'].append({
                        'heading': line.strip(),
                        'reason': rule['reason'],
                        'line_number': i + 1
                    })
                    
                    if rule['stop_after']:
                        # Stop processing - everything after this is filtered
                        stats['stop_after_triggered'] = True
                        
                        if keep_stop_heading:
                            filtered_lines.append(line)
                        
                        if add_marker:
                            filtered_lines.append('')
                            filtered_lines.append(marker_text)
                        
                        # Done processing
                        if log_filtered:
                            self.logger.info(f"Stop-after triggered at line {i+1}: {line.strip()}")
                        
                        return '\n'.join(filtered_lines), stats
                    else:
                        # Skip just this section (until next ## heading)
                        if not keep_stop_heading:
                            i += 1  # Skip the heading itself
                        
                        # Skip until next heading of same or higher level
                        heading_level = len(re.match(r'^(#+)', line).group(1))
                        while i < len(lines):
                            next_line = lines[i]
                            if next_line.startswith('#'):
                                next_level = len(re.match(r'^(#+)', next_line).group(1))
                                if next_level <= heading_level:
                                    # Found next section at same or higher level
                                    break
                            i += 1
                        
                        # Continue processing from next section
                        matched = True
                        break
            
            if not matched:
                filtered_lines.append(line)
                i += 1
        
        filtered_content = '\n'.join(filtered_lines)
        
        if log_filtered and stats['sections_removed'] > 0:
            self.logger.info(f"Filtered {stats['sections_removed']} sections from {source_path or 'content'}")
        
        return filtered_content, stats

def filter_file(input_path: Path, output_path: Path | None = None, source_path: str | None = None) -> dict:
    """
    Filter a markdown file in place or to a new location
    
    Args:
        input_path: Path to input markdown file
        output_path: Path to output file (defaults to input_path - in-place filtering)
        source_path: Source path for determining filter rules (auto-detected if not provided)
    
    Returns:
        Filter statistics
    """
    # Auto-detect source path from input path if not provided
    if source_path is None:
        # Try to extract source path relative to canonical directory
        try:
            canonical_idx = input_path.parts.index('canonical')
            source_path = '/'.join(input_path.parts[canonical_idx + 1:])
        except (ValueError, IndexError):
            source_path = None
    
    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Filter content
    filter = ContentFilter()
    filtered_content, stats = filter.filter_content(content, source_path=source_path)
    
    # Write output
    output_path = output_path or input_path
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(filtered_content)
    
    return stats

if __name__ == '__main__':
    import argparse
    from logging_utils import get_or_setup_logger

    logger = get_or_setup_logger(__file__, log_category="diagnostics")
    
    parser = argparse.ArgumentParser(description='Filter non-primary content from markdown files')
    parser.add_argument('input', type=Path, help='Input markdown file')
    parser.add_argument('--output', '-o', type=Path, help='Output file (default: overwrite input)')
    parser.add_argument('--source-path', '-s', help='Source path for filter rules (auto-detected if not provided)')
    parser.add_argument('--dry-run', '-n', action='store_true', help='Show what would be filtered without modifying files')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    if not args.input.exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    if args.dry_run:
        # Read and filter without writing
        with open(args.input, 'r', encoding='utf-8') as f:
            content = f.read()
        
        filter = ContentFilter()
        filtered_content, stats = filter.filter_content(content, source_path=args.source_path)
        
        print(f"\nDry run results for {args.input}:")
        print(f"  Sections removed: {stats['sections_removed']}")
        print(f"  Stop-after triggered: {stats['stop_after_triggered']}")
        
        if stats['removed_sections']:
            print("\nRemoved sections:")
            for section in stats['removed_sections']:
                print(f"  Line {section['line_number']}: {section['heading']}")
                print(f"    Reason: {section['reason']}")
    else:
        # Filter and write
        stats = filter_file(args.input, output_path=args.output, source_path=args.source_path)
        
        output_file = args.output or args.input
        logger.info(f"Filtered {stats['sections_removed']} sections, wrote to {output_file}")

