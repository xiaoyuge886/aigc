"""
Tests for enrich_categories.py module.

Tests category enrichment from docs_map.md to the local index.
"""

import pytest


class TestEnrichCategories:
    """Test suite for category enrichment functions."""

    def test_normalize_url_adds_md_suffix(self):
        """Test that normalize_url adds .md suffix when missing."""
        from scripts.core.enrich_categories import normalize_url

        url = 'https://code.claude.com/docs/en/skills'
        result = normalize_url(url)
        assert result == 'https://code.claude.com/docs/en/skills.md'

    def test_normalize_url_preserves_existing_md(self):
        """Test that normalize_url preserves existing .md suffix."""
        from scripts.core.enrich_categories import normalize_url

        url = 'https://code.claude.com/docs/en/skills.md'
        result = normalize_url(url)
        assert result == 'https://code.claude.com/docs/en/skills.md'

    def test_normalize_url_handles_empty(self):
        """Test that normalize_url handles empty string."""
        from scripts.core.enrich_categories import normalize_url

        result = normalize_url('')
        assert result == ''

    def test_enrich_index_with_categories_adds_new_category(self):
        """Test adding category to entry without one."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'code-claude-com-docs-en-skills': {
                'url': 'https://code.claude.com/docs/en/skills',
                'file_path': 'code-claude-com/skills.md'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 1
        assert unchanged == 0
        assert 'code-claude-com-docs-en-skills' in updates
        assert index['code-claude-com-docs-en-skills']['doc_map_category'] == 'Build with Claude Code'

    def test_enrich_index_with_categories_updates_existing_category(self):
        """Test updating entry with different category."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'code-claude-com-docs-en-skills': {
                'url': 'https://code.claude.com/docs/en/skills',
                'file_path': 'code-claude-com/skills.md',
                'doc_map_category': 'Old Category'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 1
        assert unchanged == 0
        assert index['code-claude-com-docs-en-skills']['doc_map_category'] == 'Build with Claude Code'

    def test_enrich_index_with_categories_skips_unchanged(self):
        """Test that unchanged entries are not counted as updated."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'code-claude-com-docs-en-skills': {
                'url': 'https://code.claude.com/docs/en/skills',
                'file_path': 'code-claude-com/skills.md',
                'doc_map_category': 'Build with Claude Code'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 0
        assert unchanged == 1
        assert updates == {}

    def test_enrich_index_with_categories_ignores_non_code_claude_entries(self):
        """Test that non-code.claude.com entries are ignored."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'docs-anthropic-com-api-reference': {
                'url': 'https://docs.anthropic.com/api-reference',
                'file_path': 'docs-anthropic-com/api-reference.md'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 0
        assert unchanged == 0
        assert 'doc_map_category' not in index['docs-anthropic-com-api-reference']

    def test_enrich_index_with_categories_handles_url_without_md(self):
        """Test that URLs without .md suffix are normalized for matching."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        # Index has URL without .md
        index = {
            'code-claude-com-docs-en-hooks': {
                'url': 'https://code.claude.com/docs/en/hooks',
                'file_path': 'code-claude-com/hooks.md'
            }
        }
        # Category mapping has URL with .md
        category_mapping = {
            'https://code.claude.com/docs/en/hooks.md': 'Reference'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 1
        assert index['code-claude-com-docs-en-hooks']['doc_map_category'] == 'Reference'

    def test_enrich_index_with_categories_multiple_entries(self):
        """Test enriching multiple entries at once."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'code-claude-com-docs-en-skills': {
                'url': 'https://code.claude.com/docs/en/skills',
                'file_path': 'code-claude-com/skills.md'
            },
            'code-claude-com-docs-en-hooks': {
                'url': 'https://code.claude.com/docs/en/hooks',
                'file_path': 'code-claude-com/hooks.md'
            },
            'code-claude-com-docs-en-overview': {
                'url': 'https://code.claude.com/docs/en/overview',
                'file_path': 'code-claude-com/overview.md'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code',
            'https://code.claude.com/docs/en/hooks.md': 'Reference',
            'https://code.claude.com/docs/en/overview.md': 'Getting started'
        }

        updated, unchanged, updates = enrich_index_with_categories(index, category_mapping)

        assert updated == 3
        assert unchanged == 0
        assert index['code-claude-com-docs-en-skills']['doc_map_category'] == 'Build with Claude Code'
        assert index['code-claude-com-docs-en-hooks']['doc_map_category'] == 'Reference'
        assert index['code-claude-com-docs-en-overview']['doc_map_category'] == 'Getting started'

    def test_enrich_index_with_categories_verbose_mode(self, capsys):
        """Test verbose mode outputs updates."""
        from scripts.core.enrich_categories import enrich_index_with_categories

        index = {
            'code-claude-com-docs-en-skills': {
                'url': 'https://code.claude.com/docs/en/skills',
                'file_path': 'code-claude-com/skills.md'
            }
        }
        category_mapping = {
            'https://code.claude.com/docs/en/skills.md': 'Build with Claude Code'
        }

        enrich_index_with_categories(index, category_mapping, verbose=True)

        captured = capsys.readouterr()
        assert 'Added:' in captured.out or 'code-claude-com-docs-en-skills' in captured.out
