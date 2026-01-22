"""
Tests for hooks-specific search quality improvements.

Validates that hooks queries return relevant results with proper ranking.
"""

import sys
from pathlib import Path

from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry


class TestHooksSearchQuality:
    """Test suite for hooks search quality improvements."""

    def test_hooks_pretooluse_query(self, temp_dir):
        """Test that 'hooks PreToolUse' returns hooks docs first"""
        refs_dir = TempReferencesDir()
        
        try:
            # Create mock index with hooks docs and other docs
            index = {
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://code.claude.com/docs/hooks', 'test/hooks.md',
                    title='Hooks reference',
                    description='Reference documentation for implementing hooks',
                    keywords=['PreToolUse', 'PostToolUse', 'hooks', 'hook events'],
                    tags=['hooks']
                ),
                'hooks-guide': create_mock_index_entry(
                    'hooks-guide', 'https://code.claude.com/docs/hooks-guide', 'test/hooks-guide.md',
                    title='Get started with hooks',
                    description='Learn how to use hooks',
                    keywords=['PreToolUse', 'hooks', 'tutorial'],
                    tags=['hooks']
                ),
                'model-config': create_mock_index_entry(
                    'model-config', 'https://code.claude.com/docs/model-config', 'test/model-config.md',
                    title='Model configuration',
                    description='Configure model settings',
                    keywords=['configuration', 'model', 'settings'],
                    tags=['configuration']
                ),
                'network-config': create_mock_index_entry(
                    'network-config', 'https://code.claude.com/docs/network-config', 'test/network-config.md',
                    title='Network configuration',
                    description='Configure network settings',
                    keywords=['configuration', 'network', 'proxy'],
                    tags=['configuration']
                ),
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for hooks PreToolUse
            results = resolver.search_by_keyword(['hooks', 'pretooluse'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # hooks-doc and hooks-guide should be top 2 results
            assert len(doc_ids) >= 2, "Should return at least 2 results"
            assert doc_ids[0] in ['hooks-doc', 'hooks-guide'], f"Top result should be hooks doc, got {doc_ids[0]}"
            assert doc_ids[1] in ['hooks-doc', 'hooks-guide'], f"Second result should be hooks doc, got {doc_ids[1]}"
            
            # model-config and network-config should NOT be in top 2
            assert 'model-config' not in doc_ids[:2], "model-config should not rank in top 2"
            assert 'network-config' not in doc_ids[:2], "network-config should not rank in top 2"
            
        finally:
            refs_dir.cleanup()

    def test_hook_configuration_query(self, temp_dir):
        """Test that 'hook configuration' returns hooks docs, not generic config docs"""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://code.claude.com/docs/hooks', 'test/hooks.md',
                    title='Hooks reference',
                    description='Reference documentation for implementing hooks',
                    keywords=['hook configuration', 'hooks', 'configuration'],
                    tags=['hooks']
                ),
                'hooks-guide': create_mock_index_entry(
                    'hooks-guide', 'https://code.claude.com/docs/hooks-guide', 'test/hooks-guide.md',
                    title='Get started with hooks',
                    description='Learn how to configure hooks',
                    keywords=['hooks', 'hook configuration', 'tutorial'],
                    tags=['hooks']
                ),
                'iam-doc': create_mock_index_entry(
                    'iam-doc', 'https://code.claude.com/docs/iam', 'test/iam.md',
                    title='Identity and Access Management',
                    description='Permission control with hooks',
                    keywords=['hooks', 'permissions', 'iam'],
                    tags=['hooks', 'security']
                ),
                'llm-gateway': create_mock_index_entry(
                    'llm-gateway', 'https://code.claude.com/docs/llm-gateway', 'test/llm-gateway.md',
                    title='LLM gateway configuration',
                    description='Configure LLM gateway',
                    keywords=['configuration', 'gateway', 'llm'],
                    tags=['configuration']
                ),
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for hook configuration
            results = resolver.search_by_keyword(['hook', 'configuration'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # hooks-doc, hooks-guide, and iam-doc should be top 3
            assert len(doc_ids) >= 3, "Should return at least 3 results"
            assert doc_ids[0] in ['hooks-doc', 'hooks-guide', 'iam-doc'], \
                f"Top result should be hooks-related doc, got {doc_ids[0]}"
            
            # llm-gateway should NOT be in top 3 (generic configuration doc)
            assert 'llm-gateway' not in doc_ids[:3], \
                "llm-gateway should not rank in top 3 for 'hook configuration' query"
            
        finally:
            refs_dir.cleanup()

    def test_posttooluse_event_query(self, temp_dir):
        """Test that 'PostToolUse event' returns hooks docs first"""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://code.claude.com/docs/hooks', 'test/hooks.md',
                    title='Hooks reference',
                    description='Reference documentation for hooks events',
                    keywords=['PostToolUse', 'PreToolUse', 'hook events'],
                    tags=['hooks']
                ),
                'github-actions': create_mock_index_entry(
                    'github-actions', 'https://code.claude.com/docs/github-actions', 'test/github-actions.md',
                    title='GitHub Actions',
                    description='CI/CD integration',
                    keywords=['github', 'actions', 'ci/cd'],
                    tags=['cicd']
                ),
                'gitlab-cicd': create_mock_index_entry(
                    'gitlab-cicd', 'https://code.claude.com/docs/gitlab-cicd', 'test/gitlab-cicd.md',
                    title='GitLab CI/CD',
                    description='CI/CD integration',
                    keywords=['gitlab', 'ci/cd', 'pipeline'],
                    tags=['cicd']
                ),
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for PostToolUse event
            results = resolver.search_by_keyword(['posttooluse', 'event'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # hooks-doc should be #1
            assert len(doc_ids) >= 1, "Should return at least 1 result"
            assert doc_ids[0] == 'hooks-doc', f"Top result should be hooks-doc, got {doc_ids[0]}"
            
            # CI/CD docs should not appear in results
            assert 'github-actions' not in doc_ids, "github-actions should not match PostToolUse query"
            assert 'gitlab-cicd' not in doc_ids, "gitlab-cicd should not match PostToolUse query"
            
        finally:
            refs_dir.cleanup()

    def test_simple_hooks_query(self, temp_dir):
        """Test that simple 'hooks' query returns hooks docs first"""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'hooks-guide': create_mock_index_entry(
                    'hooks-guide', 'https://code.claude.com/docs/hooks-guide', 'test/hooks-guide.md',
                    title='Get started with Claude Code hooks',
                    description='Learn how to use hooks',
                    keywords=['hooks', 'tutorial', 'getting started'],
                    tags=['hooks', 'guides']
                ),
                'hooks-doc': create_mock_index_entry(
                    'hooks-doc', 'https://code.claude.com/docs/hooks', 'test/hooks.md',
                    title='Hooks reference',
                    description='Reference documentation for hooks',
                    keywords=['hooks', 'reference', 'events'],
                    tags=['hooks']
                ),
                'iam-doc': create_mock_index_entry(
                    'iam-doc', 'https://code.claude.com/docs/iam', 'test/iam.md',
                    title='Identity and Access Management',
                    description='Permission control with hooks',
                    keywords=['hooks', 'permissions', 'iam'],
                    tags=['hooks', 'security']
                ),
                'plugins-doc': create_mock_index_entry(
                    'plugins-doc', 'https://code.claude.com/docs/plugins', 'test/plugins.md',
                    title='Plugins',
                    description='Extend Claude Code with plugins',
                    keywords=['plugins', 'hooks', 'extensions'],
                    tags=['plugins']  # hooks in keywords, not tags
                ),
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for hooks
            results = resolver.search_by_keyword(['hooks'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # Top 3 should be hooks-guide, hooks-doc, iam-doc (all have hooks tag)
            assert len(doc_ids) >= 3, "Should return at least 3 results"
            assert doc_ids[0] in ['hooks-guide', 'hooks-doc', 'iam-doc'], \
                f"Top result should be primary hooks doc, got {doc_ids[0]}"
            assert doc_ids[1] in ['hooks-guide', 'hooks-doc', 'iam-doc'], \
                f"Second result should be primary hooks doc, got {doc_ids[1]}"
            assert doc_ids[2] in ['hooks-guide', 'hooks-doc', 'iam-doc'], \
                f"Third result should be primary hooks doc, got {doc_ids[2]}"
            
            # plugins-doc should rank lower (hooks in keywords, not primary topic)
            if 'plugins-doc' in doc_ids:
                plugins_rank = doc_ids.index('plugins-doc')
                assert plugins_rank >= 3, \
                    f"plugins-doc should rank 4th or lower, got rank {plugins_rank + 1}"
            
        finally:
            refs_dir.cleanup()

    def test_generic_term_penalty_applied(self, temp_dir):
        """Test that generic terms like 'configuration' are penalized appropriately"""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'specific-doc': create_mock_index_entry(
                    'specific-doc', 'https://example.com/specific', 'test/specific.md',
                    title='PreToolUse Hook Configuration',
                    description='Configure PreToolUse hooks',
                    keywords=['PreToolUse', 'hooks', 'configuration'],
                    tags=['hooks']
                ),
                'generic-config-1': create_mock_index_entry(
                    'generic-config-1', 'https://example.com/config1', 'test/config1.md',
                    title='General Configuration Guide',
                    description='Configuration documentation',
                    keywords=['configuration', 'setup', 'guide'],
                    tags=['guides']
                ),
                'generic-config-2': create_mock_index_entry(
                    'generic-config-2', 'https://example.com/config2', 'test/config2.md',
                    title='Configuration Reference',
                    description='Configuration reference documentation',
                    keywords=['configuration', 'reference', 'documentation'],
                    tags=['reference']
                ),
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Search for specific term + generic term
            results = resolver.search_by_keyword(['pretooluse', 'configuration'], limit=10)
            doc_ids = [doc_id for doc_id, _ in results]
            
            # specific-doc should rank first (has specific term PreToolUse)
            assert len(doc_ids) >= 1, "Should return at least 1 result"
            assert doc_ids[0] == 'specific-doc', \
                f"Specific doc should rank first, got {doc_ids[0]}"
            
            # Generic docs may appear but should rank significantly lower (after specific doc)
            # They match "configuration" but only generic terms, so penalty applies
            if 'generic-config-1' in doc_ids:
                generic_rank = doc_ids.index('generic-config-1')
                assert generic_rank > 0, \
                    f"generic-config-1 should rank lower than specific-doc, got rank {generic_rank + 1}"
            if 'generic-config-2' in doc_ids:
                generic_rank = doc_ids.index('generic-config-2')
                assert generic_rank > 0, \
                    f"generic-config-2 should rank lower than specific-doc, got rank {generic_rank + 1}"
            
        finally:
            refs_dir.cleanup()

