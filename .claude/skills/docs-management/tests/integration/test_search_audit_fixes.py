"""
Tests for search audit fixes (TDD approach).

These tests document the expected behavior for search quality issues
identified in the 2025-11-17 search audit. Tests are written first (failing),
then fixes are implemented to make them pass.

Audit Reference: .claude/temp/2025-11-17_search-audit-root-cause-analysis.md
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestMemorySearchFixes:
    """Tests for memory search issues (Issue #1)"""
    
    def test_memory_claude_md_query_returns_memory_doc(self, temp_dir):
        """
        Test that "claude.md memory" query returns memory doc first.
        
        Issue: Query "claude.md memory" was returning Troubleshooting doc instead of Memory doc.
        Root Cause: Memory doc missing "claude.md" keyword, troubleshooting has "memory" tag.
        Fix: Add "claude.md" to memory doc keywords, remove "memory" tag from troubleshooting.
        """
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with memory and troubleshooting docs
            index = {
                'code-claude-com-docs-en-memory': create_mock_index_entry(
                    'code-claude-com-docs-en-memory',
                    'https://code.claude.com/docs/en/memory',
                    'code-claude-com/docs/en/memory.md',
                    title="Manage Claude's memory",
                    description="Learn how to manage Claude Code's memory across sessions",
                    keywords=['claude.md', 'memory', 'individual preferences', 'level memory', 'locations', 'practices', 'sessions'],
                    tags=['memory'],
                    domain='code.claude.com'
                ),
                'code-claude-com-docs-en-troubleshooting': create_mock_index_entry(
                    'code-claude-com-docs-en-troubleshooting',
                    'https://code.claude.com/docs/en/troubleshooting',
                    'code-claude-com/docs/en/troubleshooting.md',
                    title='Troubleshooting',
                    description='Discover solutions to common issues with Claude Code',
                    keywords=['memory usage', 'code installation', 'troubleshooting', 'solutions'],
                    tags=['troubleshooting'],  # Should NOT have 'memory' tag
                    domain='code.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for "claude.md memory"
            results = resolver.search_by_keyword(['claude.md', 'memory'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # Memory doc should be ranked first
            assert doc_ids, "No results returned for 'claude.md memory' query"
            assert doc_ids[0] == 'code-claude-com-docs-en-memory', \
                f"Expected memory doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()


class TestInstallationSearchFixes:
    """Tests for installation search issues (Issue #2)"""
    
    def test_installation_simple_query_returns_setup_doc(self, temp_dir):
        """
        Test that "installation" query returns setup doc first.
        
        Issue: Query "installation" was returning Troubleshooting doc instead of Setup doc.
        Root Cause: Troubleshooting doc has "code installation" keyword, higher overall score.
        Fix: Boost title matching, add "installation" tag to setup doc.
        """
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'code-claude-com-docs-en-setup': create_mock_index_entry(
                    'code-claude-com-docs-en-setup',
                    'https://code.claude.com/docs/en/setup',
                    'code-claude-com/docs/en/setup.md',
                    title='Install, authenticate, and start using Claude Code',
                    description='Install Claude Code on your development machine',
                    keywords=['installation', 'standard installation', 'install', 'setup', 'authenticate'],
                    tags=['installation'],  # Should have installation tag
                    domain='code.claude.com'
                ),
                'code-claude-com-docs-en-troubleshooting': create_mock_index_entry(
                    'code-claude-com-docs-en-troubleshooting',
                    'https://code.claude.com/docs/en/troubleshooting',
                    'code-claude-com/docs/en/troubleshooting.md',
                    title='Troubleshooting',
                    description='Discover solutions to common issues',
                    keywords=['code installation', 'troubleshooting', 'solutions'],
                    tags=['troubleshooting'],
                    domain='code.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_keyword(['installation'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            assert doc_ids, "No results returned for 'installation' query"
            assert doc_ids[0] == 'code-claude-com-docs-en-setup', \
                f"Expected setup doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()
    
    def test_installation_howto_query_returns_setup_doc(self, temp_dir):
        """
        Test that "how to create installation" returns setup doc first.
        
        Issue: This query was also returning Troubleshooting doc.
        Fix: Same as simple query - boost title matching, add tags.
        """
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'code-claude-com-docs-en-setup': create_mock_index_entry(
                    'code-claude-com-docs-en-setup',
                    'https://code.claude.com/docs/en/setup',
                    'code-claude-com/docs/en/setup.md',
                    title='Install, authenticate, and start using Claude Code',
                    description='Install Claude Code on your development machine',
                    keywords=['installation', 'install', 'setup'],
                    tags=['installation'],
                    domain='code.claude.com'
                ),
                'code-claude-com-docs-en-troubleshooting': create_mock_index_entry(
                    'code-claude-com-docs-en-troubleshooting',
                    'https://code.claude.com/docs/en/troubleshooting',
                    'code-claude-com/docs/en/troubleshooting.md',
                    title='Troubleshooting',
                    description='Discover solutions to common issues',
                    keywords=['code installation', 'troubleshooting'],
                    tags=['troubleshooting'],
                    domain='code.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_natural_language('how to create installation', limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            assert doc_ids, "No results returned"
            assert doc_ids[0] == 'code-claude-com-docs-en-setup', \
                f"Expected setup doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()
    
    def test_installation_usecase_query_returns_setup_doc(self, temp_dir):
        """
        Test that "when to use installation" returns setup doc first.
        
        Issue: This query was returning MCP doc (completely wrong).
        Fix: Boost title matching + tags should fix this.
        """
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'code-claude-com-docs-en-setup': create_mock_index_entry(
                    'code-claude-com-docs-en-setup',
                    'https://code.claude.com/docs/en/setup',
                    'code-claude-com/docs/en/setup.md',
                    title='Install, authenticate, and start using Claude Code',
                    description='Install Claude Code on your development machine',
                    keywords=['installation', 'install', 'setup'],
                    tags=['installation'],
                    domain='code.claude.com'
                ),
                'code-claude-com-docs-en-mcp': create_mock_index_entry(
                    'code-claude-com-docs-en-mcp',
                    'https://code.claude.com/docs/en/mcp',
                    'code-claude-com/docs/en/mcp.md',
                    title='Connect Claude Code to tools via MCP',
                    description='Model Context Protocol integration',
                    keywords=['mcp', 'tools', 'integration'],
                    tags=['mcp'],
                    domain='code.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_natural_language('when to use installation', limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            assert doc_ids, "No results returned"
            assert doc_ids[0] == 'code-claude-com-docs-en-setup', \
                f"Expected setup doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()
    
    def test_installation_best_practices_query_returns_setup_doc(self, temp_dir):
        """
        Test that "installation best practices" returns setup doc first.
        
        Issue: This query was returning Security doc (completely wrong).
        Fix: Add "best practices" keyword to setup doc or boost title matching.
        """
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'code-claude-com-docs-en-setup': create_mock_index_entry(
                    'code-claude-com-docs-en-setup',
                    'https://code.claude.com/docs/en/setup',
                    'code-claude-com/docs/en/setup.md',
                    title='Install, authenticate, and start using Claude Code',
                    description='Install Claude Code on your development machine',
                    keywords=['installation', 'install', 'setup', 'best practices'],
                    tags=['installation'],
                    domain='code.claude.com'
                ),
                'code-claude-com-docs-en-security': create_mock_index_entry(
                    'code-claude-com-docs-en-security',
                    'https://code.claude.com/docs/en/security',
                    'code-claude-com/docs/en/security.md',
                    title='Security',
                    description='Security features and best practices',
                    keywords=['security', 'best practices'],
                    tags=['security'],
                    domain='code.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_natural_language('installation best practices', limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            assert doc_ids, "No results returned"
            assert doc_ids[0] == 'code-claude-com-docs-en-setup', \
                f"Expected setup doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()


class TestModelsSearchFixes:
    """Tests for models search issues (Issue #3)"""
    
    def test_models_best_practices_query_returns_model_doc(self, temp_dir):
        """
        Test that "models best practices" returns model doc first.
        
        Issue: Query was returning Skills best practices doc.
        Root Cause: Skills doc has "best practices" in title, models doc doesn't.
        Fix: Add "best practices" keyword to model docs.
        """
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'code-claude-com-docs-en-model-configuration': create_mock_index_entry(
                    'code-claude-com-docs-en-model-configuration',
                    'https://code.claude.com/docs/en/model-configuration',
                    'code-claude-com/docs/en/model-configuration.md',
                    title='Model configuration',
                    description='Configure models in Claude Code',
                    keywords=['model', 'models', 'configuration', 'best practices'],
                    tags=['models'],
                    domain='code.claude.com'
                ),
                'docs-claude-com-docs-agents-and-tools-agent-skills-best-practices': create_mock_index_entry(
                    'docs-claude-com-docs-agents-and-tools-agent-skills-best-practices',
                    'https://docs.claude.com/en/docs/agents-and-tools/agent-skills/best-practices',
                    'docs-claude-com/docs/agents-and-tools/agent-skills/best-practices.md',
                    title='Skill authoring best practices',
                    description='Best practices for creating agent skills',
                    keywords=['skills', 'best practices', 'authoring'],
                    tags=['skills'],
                    domain='docs.claude.com'
                )
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            results = resolver.search_by_natural_language('models best practices', limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            assert doc_ids, "No results returned"
            assert doc_ids[0] == 'code-claude-com-docs-en-model-configuration', \
                f"Expected model configuration doc first, got {doc_ids[0]}"
            
        finally:
            refs_dir.cleanup()
