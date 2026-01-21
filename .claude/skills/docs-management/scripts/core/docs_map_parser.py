#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
docs_map_parser.py - Parse claude_code_docs_map.md hierarchical format.

This module parses the official Claude Code docs map which provides:
- Hierarchical categories (## Category headings)
- Page entries (### [Title](URL) links)
- Subsection headings (* bullet points)

The docs map is used for category enrichment - llms.txt provides URLs,
docs_map.md provides hierarchical categorization.

Usage:
    from core.docs_map_parser import DocsMapParser, DocsMapEntry

    parser = DocsMapParser()
    entries = parser.parse(content)

    # Get category for a URL
    url = "https://code.claude.com/docs/en/skills.md"
    if url in entries:
        entry = entries[url]
        print(f"{entry.title}: {entry.category}")  # "skills: Build with Claude Code"

    # List all categories
    categories = parser.get_categories(content)
    for category, urls in categories.items():
        print(f"{category}: {len(urls)} pages")
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import re
from dataclasses import dataclass, field
from typing import Generator


@dataclass
class DocsMapEntry:
    """
    Entry from docs_map.md with hierarchical metadata.

    Attributes:
        url: Full URL to the documentation page
        title: Page title from the markdown link
        category: Top-level category (## heading)
        subsections: List of subsection headings (* bullets)
    """
    url: str
    title: str
    category: str
    subsections: list[str] = field(default_factory=list)

    @property
    def doc_id(self) -> str:
        """Generate doc_id from URL (e.g., 'code-claude-com-docs-en-skills')."""
        # Extract path from URL and normalize to doc_id format
        from urllib.parse import urlparse
        parsed = urlparse(self.url)
        domain = parsed.netloc.replace('.', '-')
        path = parsed.path.rstrip('/').replace('/', '-').lstrip('-')
        if path.endswith('.md'):
            path = path[:-3]
        return f"{domain}-{path}"


class DocsMapParser:
    """
    Parser for claude_code_docs_map.md hierarchical format.

    docs_map.md format:
        ## Category Name

        ### [Page Title](https://code.claude.com/docs/en/page.md)

        * subsection heading
        * another subsection
          * nested subsection (ignored, only top-level captured)

        ## Another Category

        ### [Another Page](URL)
        ...

    This parser extracts the hierarchical structure to enrich the index
    with category metadata from the official docs map.
    """

    # Category heading: ## Category Name
    CATEGORY_PATTERN = re.compile(r'^##\s+(.+)$')

    # Page entry: ### [Title](URL)
    PAGE_PATTERN = re.compile(
        r'^###\s+\[([^\]]+)\]\((https?://[^\)]+)\)\s*$'
    )

    # Subsection bullet: * heading (top-level only, not indented)
    SUBSECTION_PATTERN = re.compile(r'^\*\s+(.+)$')

    # Indented subsection (to skip): starts with spaces then *
    NESTED_SUBSECTION_PATTERN = re.compile(r'^\s+\*\s+')

    def __init__(self):
        """Initialize parser."""
        pass

    def parse(self, content: str) -> dict[str, DocsMapEntry]:
        """
        Parse docs_map.md content, returning entries keyed by URL.

        Args:
            content: Full text content of docs_map.md file

        Returns:
            Dict mapping URL to DocsMapEntry with category metadata
        """
        entries: dict[str, DocsMapEntry] = {}
        current_category: str | None = None
        current_entry: DocsMapEntry | None = None

        for line in content.splitlines():
            # Skip empty lines
            if not line.strip():
                continue

            # Check for category heading (## Category)
            category_match = self.CATEGORY_PATTERN.match(line)
            if category_match:
                # Save previous entry if exists
                if current_entry:
                    entries[current_entry.url] = current_entry
                    current_entry = None

                current_category = category_match.group(1).strip()
                continue

            # Check for page entry (### [Title](URL))
            page_match = self.PAGE_PATTERN.match(line)
            if page_match and current_category:
                # Save previous entry if exists
                if current_entry:
                    entries[current_entry.url] = current_entry

                title = page_match.group(1).strip()
                url = page_match.group(2).strip()

                current_entry = DocsMapEntry(
                    url=url,
                    title=title,
                    category=current_category,
                    subsections=[]
                )
                continue

            # Check for top-level subsection bullet (* heading)
            # Skip nested/indented bullets
            if self.NESTED_SUBSECTION_PATTERN.match(line):
                continue

            subsection_match = self.SUBSECTION_PATTERN.match(line)
            if subsection_match and current_entry:
                subsection = subsection_match.group(1).strip()
                current_entry.subsections.append(subsection)

        # Don't forget the last entry
        if current_entry:
            entries[current_entry.url] = current_entry

        return entries

    def parse_to_list(self, content: str) -> list[DocsMapEntry]:
        """Parse docs_map.md and return all entries as a list."""
        return list(self.parse(content).values())

    def get_categories(self, content: str) -> dict[str, list[str]]:
        """
        Extract URLs grouped by category.

        Args:
            content: docs_map.md content

        Returns:
            Dict mapping category name to list of URLs
        """
        entries = self.parse(content)
        categories: dict[str, list[str]] = {}

        for entry in entries.values():
            if entry.category not in categories:
                categories[entry.category] = []
            categories[entry.category].append(entry.url)

        return categories

    def get_category_for_url(self, content: str, target_url: str) -> str | None:
        """
        Get the category for a specific URL.

        Args:
            content: docs_map.md content
            target_url: URL to look up

        Returns:
            Category name or None if not found
        """
        entries = self.parse(content)
        if target_url in entries:
            return entries[target_url].category
        return None

    def extract_urls(self, content: str) -> list[str]:
        """Extract just the URLs from docs_map.md content."""
        return list(self.parse(content).keys())


def parse_docs_map_hierarchy(content: str) -> dict[str, DocsMapEntry]:
    """
    Convenience function to parse docs_map.md and extract hierarchical metadata.

    Args:
        content: docs_map.md file content

    Returns:
        Dict mapping URL to DocsMapEntry
    """
    parser = DocsMapParser()
    return parser.parse(content)


def get_category_mapping(content: str) -> dict[str, str]:
    """
    Create a URL-to-category mapping for enrichment.

    Args:
        content: docs_map.md file content

    Returns:
        Dict mapping URL to category name
    """
    parser = DocsMapParser()
    entries = parser.parse(content)
    return {url: entry.category for url, entry in entries.items()}


if __name__ == '__main__':
    """Self-test for docs_map_parser module."""
    print("docs_map_parser Self-Test")
    print("=" * 60)

    # Test with sample docs_map.md content
    sample_docs_map = """# Claude Code Documentation Map

This is a comprehensive map of all Claude Code documentation pages.

## Getting started

### [overview](https://code.claude.com/docs/en/overview.md)

* Get started in 30 seconds
* What Claude Code does for you
* Why developers love Claude Code
* Next steps

### [quickstart](https://code.claude.com/docs/en/quickstart.md)

* Before you begin
* Step 1: Install Claude Code
* Step 2: Log in to your account

## Build with Claude Code

### [sub-agents](https://code.claude.com/docs/en/sub-agents.md)

* What are subagents?
* Key benefits
* Quick start

### [skills](https://code.claude.com/docs/en/skills.md)

* Prerequisites
* What are Agent Skills?
* Create a Skill
  * Personal Skills
  * Project Skills

## Deployment

### [amazon-bedrock](https://code.claude.com/docs/en/amazon-bedrock.md)

* Prerequisites
* Setup

### [google-vertex-ai](https://code.claude.com/docs/en/google-vertex-ai.md)

* Prerequisites
* Region Configuration
"""

    print("\n1. Testing DocsMapParser:")
    parser = DocsMapParser()
    entries = parser.parse(sample_docs_map)
    print(f"   Found {len(entries)} entries")

    for url, entry in entries.items():
        print(f"\n   [{entry.category}] {entry.title}")
        print(f"   URL: {url}")
        print(f"   doc_id: {entry.doc_id}")
        if entry.subsections:
            print(f"   Subsections ({len(entry.subsections)}):")
            for sub in entry.subsections[:3]:
                print(f"     - {sub}")
            if len(entry.subsections) > 3:
                print(f"     ... and {len(entry.subsections) - 3} more")

    print("\n2. Testing category extraction:")
    categories = parser.get_categories(sample_docs_map)
    for category, urls in categories.items():
        print(f"   {category}: {len(urls)} pages")

    print("\n3. Testing URL lookup:")
    test_url = "https://code.claude.com/docs/en/skills.md"
    category = parser.get_category_for_url(sample_docs_map, test_url)
    print(f"   {test_url}")
    print(f"   -> Category: {category}")

    print("\n4. Testing category mapping:")
    mapping = get_category_mapping(sample_docs_map)
    print(f"   Created mapping with {len(mapping)} entries")

    print("\n" + "=" * 60)
    print("Self-test complete!")
