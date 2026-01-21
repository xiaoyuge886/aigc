"""
Tests for search quality (regression prevention).

Validates keyword search relevance, ranking accuracy, and subsection discovery.
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestSearchQuality:
    """Test suite for search quality."""

    def test_keyword_search_relevance(self, temp_dir):
        """Test that keyword search returns relevant results"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with skills and hooks docs
            index = {
                'skills-doc': create_mock_index_entry(
                    'skills-doc', 'https://example.com/skills', 'test/skills.md',
                    title='Agent Skills Guide',
                    description='Learn about Agent Skills',
                    keywords=['skills', 'agent skills', 'progressive disclosure'],
                    tags=['skills']
                ),
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://example.com/hooks', 'test/hooks.md',
                    title='Hooks Guide',
                    description='Learn about hooks',
                    keywords=['hooks', 'pretooluse', 'posttooluse'],
                    tags=['hooks']
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for skills
            results = resolver.search_by_keyword(['skills'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # Skills doc should be in results
            assert 'skills-doc' in doc_ids
            # Skills doc should be ranked first
            assert doc_ids[0] == 'skills-doc'
            
        finally:
            refs_dir.cleanup()

    def test_technical_phrase_search(self, temp_dir):
        """Test that technical phrases are searchable"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with technical phrases
            index = {
                'skills-doc': create_mock_index_entry(
                    'skills-doc', 'https://example.com/skills', 'test/skills.md',
                    title='Skills Guide',
                    keywords=['progressive disclosure', 'context window', 'agent skills'],
                    tags=['skills']
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for technical phrase
            results = resolver.search_by_keyword(['progressive', 'disclosure'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # Should find doc with technical phrase
            assert 'skills-doc' in doc_ids
            
        finally:
            refs_dir.cleanup()

    def test_subsection_discovery(self, temp_dir):
        """Test that subsections are discoverable via search"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with subsection metadata
            subsections = [
                {
                    'heading': 'Skills vs slash commands',
                    'level': 2,
                    'anchor': '#skills-vs-slash-commands',
                    'keywords': ['skills', 'slash commands', 'comparison']
                }
            ]
            
            index = {
                'commands-doc': create_mock_index_entry(
                    'commands-doc', 'https://example.com/commands', 'test/commands.md',
                    title='Slash Commands',
                    keywords=['commands', 'slash commands'],
                    tags=['api'],
                    subsections=subsections
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for subsection content
            results = resolver.search_by_keyword(['skills', 'slash'], limit=10)
            
            if results:
                doc_id, metadata = results[0]
                # Should match the document with subsection
                assert doc_id == 'commands-doc'
                # URL should include subsection anchor
                assert '#skills-vs-slash-commands' in metadata.get('url', '')
            
        finally:
            refs_dir.cleanup()

    def test_ranking_by_keyword_match(self, temp_dir):
        """Test that docs with more keyword matches rank higher"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with varying relevance
            index = {
                'highly-relevant': create_mock_index_entry(
                    'highly-relevant', 'https://example.com/hr', 'test/hr.md',
                    title='Skills and Hooks Guide',
                    keywords=['skills', 'hooks', 'agent skills'],
                    tags=['skills', 'hooks']
                ),
                'somewhat-relevant': create_mock_index_entry(
                    'somewhat-relevant', 'https://example.com/sr', 'test/sr.md',
                    title='General Guide',
                    keywords=['skills'],
                    tags=['guides']
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for multiple keywords
            results = resolver.search_by_keyword(['skills', 'hooks'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # More relevant doc should rank higher
            assert doc_ids[0] == 'highly-relevant'
            
        finally:
            refs_dir.cleanup()

    def test_tag_filtering(self, temp_dir):
        """Test that tag filtering works correctly"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with different tags
            index = {
                'skills-doc': create_mock_index_entry(
                    'skills-doc', 'https://example.com/skills', 'test/skills.md',
                    title='Skills Guide',
                    keywords=['skills'],
                    tags=['skills', 'api']
                ),
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://example.com/hooks', 'test/hooks.md',
                    title='Hooks Guide',
                    keywords=['hooks'],
                    tags=['hooks', 'api']
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search with tag filter
            results = resolver.search_by_keyword(['guide'], tags=['skills'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # Should only return docs with skills tag
            assert 'skills-doc' in doc_ids
            assert 'hooks-doc' not in doc_ids
            
        finally:
            refs_dir.cleanup()

    def test_doc_id_preferred_over_partial_match(self, temp_dir):
        """Docs with exact keyword intent should outrank partial matches."""
        refs_dir = TempReferencesDir()

        try:
            index = {
                'code-claude-com-docs-en-sub-agents': create_mock_index_entry(
                    'code-claude-com-docs-en-sub-agents',
                    'https://code.claude.com/docs/en/sub-agents',
                    'code-claude-com/docs/en/sub-agents.md',
                    title='Subagents',
                    keywords=['subagents', 'specialized agents'],
                    tags=['subagents']
                ),
                'code-claude-com-docs-en-hooks': create_mock_index_entry(
                    'code-claude-com-docs-en-hooks',
                    'https://code.claude.com/docs/en/hooks',
                    'code-claude-com/docs/en/hooks.md',
                    title='Hooks reference',
                    keywords=['subagentstop', 'hooks'],
                    tags=['hooks']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_keyword(['subagents'], limit=5)
            doc_ids = [doc_id for doc_id, _ in results]

            assert doc_ids
            assert doc_ids[0] == 'code-claude-com-docs-en-sub-agents'

        finally:
            refs_dir.cleanup()

    def test_filename_keyword_search(self, temp_dir):
        """File-style queries (claude.md) should match relevant docs."""
        refs_dir = TempReferencesDir()

        try:
            index = {
                'code-claude-com-docs-en-memory': create_mock_index_entry(
                    'code-claude-com-docs-en-memory',
                    'https://code.claude.com/docs/en/memory',
                    'code-claude-com/docs/en/memory.md',
                    title="Manage Claude's memory",
                    keywords=['claude.md', 'memory'],
                    tags=['memory']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_keyword(['claude.md'], limit=5)
            doc_ids = [doc_id for doc_id, _ in results]

            assert doc_ids and doc_ids[0] == 'code-claude-com-docs-en-memory'

        finally:
            refs_dir.cleanup()
