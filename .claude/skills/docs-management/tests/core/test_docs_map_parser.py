"""
Tests for docs_map_parser.py module.

Tests parsing of claude_code_docs_map.md hierarchical format.
"""

import pytest


class TestDocsMapParser:
    """Test suite for DocsMapParser class."""

    def test_parse_simple_entry(self):
        """Test parsing a single page entry."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Build with Claude Code

### [Skills](https://code.claude.com/docs/en/skills.md)

* Creating custom skills
* YAML frontmatter
"""
        parser = DocsMapParser()
        entries = parser.parse(content)

        assert len(entries) == 1
        url = 'https://code.claude.com/docs/en/skills.md'
        assert url in entries
        entry = entries[url]
        assert entry.title == 'Skills'
        assert entry.category == 'Build with Claude Code'
        assert 'Creating custom skills' in entry.subsections
        assert 'YAML frontmatter' in entry.subsections

    def test_parse_multiple_categories(self):
        """Test parsing multiple categories with entries."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Getting started

### [Overview](https://code.claude.com/docs/en/overview.md)

## Build with Claude Code

### [Skills](https://code.claude.com/docs/en/skills.md)

### [Hooks](https://code.claude.com/docs/en/hooks.md)
"""
        parser = DocsMapParser()
        entries = parser.parse(content)

        assert len(entries) == 3

        # Check Getting started category
        overview_url = 'https://code.claude.com/docs/en/overview.md'
        assert entries[overview_url].category == 'Getting started'

        # Check Build with Claude Code category
        skills_url = 'https://code.claude.com/docs/en/skills.md'
        hooks_url = 'https://code.claude.com/docs/en/hooks.md'
        assert entries[skills_url].category == 'Build with Claude Code'
        assert entries[hooks_url].category == 'Build with Claude Code'

    def test_parse_entry_without_subsections(self):
        """Test parsing entry with no subsection bullets."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Reference

### [CLI Reference](https://code.claude.com/docs/en/cli-reference.md)

## Resources
"""
        parser = DocsMapParser()
        entries = parser.parse(content)

        assert len(entries) == 1
        url = 'https://code.claude.com/docs/en/cli-reference.md'
        assert entries[url].title == 'CLI Reference'
        assert entries[url].category == 'Reference'
        assert entries[url].subsections == []

    def test_doc_id_generation(self):
        """Test doc_id property generation from URL."""
        from scripts.core.docs_map_parser import DocsMapEntry

        entry = DocsMapEntry(
            url='https://code.claude.com/docs/en/skills.md',
            title='Skills',
            category='Build with Claude Code'
        )

        assert entry.doc_id == 'code-claude-com-docs-en-skills'

    def test_doc_id_strips_md_extension(self):
        """Test doc_id doesn't include .md extension."""
        from scripts.core.docs_map_parser import DocsMapEntry

        entry = DocsMapEntry(
            url='https://code.claude.com/docs/en/hooks-guide.md',
            title='Hooks Guide',
            category='Build with Claude Code'
        )

        doc_id = entry.doc_id
        assert not doc_id.endswith('.md')
        assert doc_id == 'code-claude-com-docs-en-hooks-guide'

    def test_get_category_mapping(self):
        """Test get_category_mapping helper function."""
        from scripts.core.docs_map_parser import get_category_mapping

        content = """## Build with Claude Code

### [Skills](https://code.claude.com/docs/en/skills.md)

### [Hooks](https://code.claude.com/docs/en/hooks.md)
"""
        mapping = get_category_mapping(content)

        skills_url = 'https://code.claude.com/docs/en/skills.md'
        hooks_url = 'https://code.claude.com/docs/en/hooks.md'

        assert skills_url in mapping
        assert hooks_url in mapping
        assert mapping[skills_url] == 'Build with Claude Code'
        assert mapping[hooks_url] == 'Build with Claude Code'

    def test_parse_handles_empty_content(self):
        """Test parser handles empty content gracefully."""
        from scripts.core.docs_map_parser import DocsMapParser

        parser = DocsMapParser()
        entries = parser.parse('')

        assert entries == {}

    def test_parse_handles_no_entries(self):
        """Test parser handles content with no page entries."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Category Name

Some description text but no page links.

## Another Category
"""
        parser = DocsMapParser()
        entries = parser.parse(content)

        assert entries == {}

    def test_parse_preserves_special_characters_in_title(self):
        """Test that special characters in titles are preserved."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Configuration

### [VS Code Integration](https://code.claude.com/docs/en/vs-code.md)
"""
        parser = DocsMapParser()
        entries = parser.parse(content)

        url = 'https://code.claude.com/docs/en/vs-code.md'
        assert entries[url].title == 'VS Code Integration'

    def test_get_categories_returns_category_list(self):
        """Test get_categories returns list of categories with page counts."""
        from scripts.core.docs_map_parser import DocsMapParser

        content = """## Getting started

### [Overview](https://code.claude.com/docs/en/overview.md)

## Build with Claude Code

### [Skills](https://code.claude.com/docs/en/skills.md)

### [Hooks](https://code.claude.com/docs/en/hooks.md)
"""
        parser = DocsMapParser()
        categories = parser.get_categories(content)

        assert 'Getting started' in categories
        assert 'Build with Claude Code' in categories
        assert len(categories['Getting started']) == 1
        assert len(categories['Build with Claude Code']) == 2


class TestDocsMapEntry:
    """Test suite for DocsMapEntry dataclass."""

    def test_entry_with_all_fields(self):
        """Test creating entry with all fields populated."""
        from scripts.core.docs_map_parser import DocsMapEntry

        entry = DocsMapEntry(
            url='https://code.claude.com/docs/en/skills.md',
            title='Skills',
            category='Build with Claude Code',
            subsections=['Creating skills', 'YAML frontmatter', 'Best practices']
        )

        assert entry.url == 'https://code.claude.com/docs/en/skills.md'
        assert entry.title == 'Skills'
        assert entry.category == 'Build with Claude Code'
        assert len(entry.subsections) == 3

    def test_entry_subsections_default_empty(self):
        """Test that subsections defaults to empty list."""
        from scripts.core.docs_map_parser import DocsMapEntry

        entry = DocsMapEntry(
            url='https://example.com/doc.md',
            title='Doc',
            category='Category'
        )

        assert entry.subsections == []
