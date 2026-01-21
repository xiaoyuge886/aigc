#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_subsection.py - Extract specific sections from markdown documents

Parses markdown heading structure and extracts target section with all child subsections.
Adds provenance frontmatter for drift detection.

Usage:
    python extract_subsection.py \\
        --source <path-to-source-doc> \\
        --section "Section Heading" \\
        --output <path-for-extract> \\
        --url <source-url>

    # Example:
    python extract_subsection.py \\
        --source <path-to-source-doc> \\
        --section "Skills vs slash commands" \\
        --output .claude/skills/my-skill/references/slash-commands-skills-section.md \\
        --url https://code.claude.com/docs/en/slash-commands#skills-vs-slash-commands

Dependencies:
    pip install pyyaml
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import hashlib
import re
from datetime import datetime, timezone

from utils.script_utils import configure_utf8_output
configure_utf8_output()

from utils.http_utils import read_file_with_retry, write_file_with_retry

try:
    import yaml
except ImportError:
    print("❌ Missing dependency: pyyaml")
    print("Install with: pip install pyyaml")
    sys.exit(1)

class MarkdownExtractor:
    """Extract sections from markdown documents"""

    def __init__(self, source_path: Path):
        """
        Initialize extractor

        Args:
            source_path: Path to source markdown file
        """
        self.source_path = source_path
        # Use retry logic for file reading to handle transient I/O errors
        self.content = read_file_with_retry(source_path, encoding='utf-8')

        # Remove frontmatter if present
        self.body = self._strip_frontmatter(self.content)

    def _strip_frontmatter(self, content: str) -> str:
        """Remove YAML frontmatter if present"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    def _parse_headings(self) -> list[tuple[int, str, int, int]]:
        """
        Parse markdown headings

        Returns:
            List of tuples: (level, title, start_line, end_line)
            where level is number of # characters
        """
        headings = []
        lines = self.body.split('\n')

        for i, line in enumerate(lines):
            # Match ATX-style headings (## Heading)
            match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if match:
                level = len(match.group(1))
                title = match.group(2).strip()
                headings.append((level, title, i, i))

        return headings

    def _find_section_bounds(self, target_title: str) -> tuple[int, int, int | None]:
        """
        Find start and end lines of target section

        Args:
            target_title: Title of section to find

        Returns:
            Tuple of (level, start_line, end_line) or None if not found
        """
        headings = self._parse_headings()
        lines = self.body.split('\n')

        # Find target heading
        target_heading = None
        for i, (level, title, start, _) in enumerate(headings):
            if title.lower() == target_title.lower():
                target_heading = (i, level, start)
                break

        if target_heading is None:
            return None

        idx, target_level, start_line = target_heading

        # Find end line (next heading at same or higher level)
        end_line = len(lines)  # Default to end of document
        for i in range(idx + 1, len(headings)):
            level, title, line, _ = headings[i]
            if level <= target_level:
                end_line = line
                break

        return (target_level, start_line, end_line)

    def extract_section(self, section_title: str) -> str | None:
        """
        Extract target section with child subsections

        Args:
            section_title: Title of section to extract

        Returns:
            Extracted markdown content, or None if section not found
        """
        bounds = self._find_section_bounds(section_title)
        if not bounds:
            return None

        level, start, end = bounds
        lines = self.body.split('\n')

        # Extract section content
        section_lines = lines[start:end]
        content = '\n'.join(section_lines).strip()

        return content

    def calculate_hash(self, content: str) -> str:
        """Calculate SHA-256 hash of content"""
        hash_obj = hashlib.sha256(content.encode('utf-8'))
        return f"sha256:{hash_obj.hexdigest()}"

    def add_frontmatter(self, extracted_content: str, section_title: str,
                       source_url: str | None = None) -> str:
        """
        Add provenance frontmatter to extracted content

        Args:
            extracted_content: Markdown content that was extracted
            section_title: Title of extracted section
            source_url: Optional URL to original doc section

        Returns:
            Content with frontmatter
        """
        content_hash = self.calculate_hash(extracted_content)
        today = datetime.now(timezone.utc).strftime('%Y-%m-%d')

        # Get source doc relative path (from base_dir)
        try:
            from path_config import get_base_dir
            from utils.common_paths import find_repo_root
            base_dir = get_base_dir()
            source_relative = self.source_path.relative_to(base_dir)
            # Use relative path format that matches config
            repo_root = find_repo_root()
            if base_dir.is_relative_to(repo_root):
                base_dir_str = str(base_dir.relative_to(repo_root))
            else:
                # Fallback: use absolute path if not relative to repo root
                source_doc = str(self.source_path)
                return f"---\n{yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)}---\n\n{extracted_content}"
            source_doc = f"{base_dir_str}/{source_relative}"
        except (ValueError, ImportError):
            # If not in base_dir or path_config unavailable, use absolute path
            source_doc = str(self.source_path)

        frontmatter = {
            'source_doc': source_doc,
            'source_section': section_title,
            'last_synced': today,
            'content_hash': content_hash
        }

        if source_url:
            frontmatter['source_url'] = source_url

        yaml_frontmatter = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)

        return f"---\n{yaml_frontmatter}---\n\n{extracted_content}"

def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Extract specific sections from markdown documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python extract_subsection.py \\
      --source <path-to-source-doc> \\
      --section "Skills vs slash commands" \\
      --output .claude/skills/my-skill/references/slash-commands-skills-section.md

  python extract_subsection.py \\
      --source <path-to-source-doc> \\
      --section "Skills plugin" \\
      --output .claude/skills/my-skill/references/plugins-skills-section.md \\
      --url https://code.claude.com/docs/en/plugins#skills-plugin
        """
    )

    parser.add_argument('--source', required=True,
                       help='Path to source markdown file')
    parser.add_argument('--section', required=True,
                       help='Title of section to extract (case-insensitive)')
    parser.add_argument('--output', required=True,
                       help='Path to output file')
    parser.add_argument('--url', help='Optional URL to original doc section')

    args = parser.parse_args()

    # Validate source file exists
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Source file does not exist: {source_path}")
        sys.exit(1)

    if not source_path.is_file():
        print(f"❌ Source path is not a file: {source_path}")
        sys.exit(1)

    # Initialize extractor
    print(f"📖 Reading source: {source_path}")
    extractor = MarkdownExtractor(source_path)

    # Extract section
    print(f"🔍 Searching for section: '{args.section}'")
    extracted = extractor.extract_section(args.section)

    if extracted is None:
        print(f"❌ Section not found: '{args.section}'")
        print("\nAvailable headings:")
        headings = extractor._parse_headings()
        for level, title, _, _ in headings:
            indent = "  " * (level - 1)
            print(f"  {indent}{'#' * level} {title}")
        sys.exit(1)

    # Add frontmatter
    final_content = extractor.add_frontmatter(extracted, args.section, args.url)

    # Write output with retry logic for transient I/O errors
    output_path = Path(args.output)
    write_file_with_retry(output_path, final_content, encoding='utf-8')

    # Report success
    print(f"✅ Extracted section: '{args.section}'")
    print(f"   Characters: {len(extracted)}")
    print(f"   Est. tokens: ~{len(extracted) // 4}")
    print(f"   Output: {output_path}")

    sys.exit(0)

if __name__ == '__main__':
    main()
