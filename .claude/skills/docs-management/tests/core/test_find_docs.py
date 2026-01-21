"""
Tests for find_docs.py CLI script.

Tests the find_docs.py command-line interface for finding and resolving documentation.
"""

import sys
from pathlib import Path


from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry



class TestFindDocsCLI:
    """Test suite for find_docs.py CLI."""

    def test_resolve_command(self, temp_dir):
        """Test resolve command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'test-doc': create_mock_index_entry('test-doc', 'https://example.com/test', 'test/doc.md',
                                                    title='Test Document')
            }
            refs_dir.create_index(index)
            refs_dir.create_doc('test', 'category', 'doc.md', '# Test Document\n\nContent.')
            
            # Import find_docs module functions
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_resolve
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            # Test resolve command
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_resolve(resolver, 'test-doc', json_output=False)
                except SystemExit:
                    pass  # Expected if doc not found
            
            output = f.getvalue()
            assert 'test-doc' in output or 'Test Document' in output
            
        finally:
            refs_dir.cleanup()

    def test_search_command(self, temp_dir):
        """Test search command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                title='Skills Guide', keywords=['skills', 'guide']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                title='API Reference', keywords=['api'])
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_search(resolver, ['skills'], limit=10, json_output=False)
                except SystemExit:
                    pass
            
            output = f.getvalue()
            assert 'doc1' in output or 'Skills Guide' in output
            
        finally:
            refs_dir.cleanup()

    def test_query_command(self, temp_dir):
        """Test natural language query command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                title='How to Create Skills', description='Guide for creating skills',
                                                keywords=['skills', 'create', 'guide'])
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_query
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_query(resolver, 'how to create skills', limit=10, json_output=False)
                except SystemExit:
                    pass
            
            output = f.getvalue()
            assert 'doc1' in output or 'Create Skills' in output
            
        finally:
            refs_dir.cleanup()

    def test_category_command(self, temp_dir):
        """Test category command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                category='api'),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                category='guides')
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_category
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_category(resolver, 'api', json_output=False)
                except SystemExit:
                    pass
            
            output = f.getvalue()
            assert 'doc1' in output
            
        finally:
            refs_dir.cleanup()

    def test_tag_command(self, temp_dir):
        """Test tag command."""
        refs_dir = TempReferencesDir()
        
        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                tags=['skills', 'guide']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2', 'test/doc2.md',
                                                tags=['api'])
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_tag
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            import io
            import contextlib
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_tag(resolver, 'skills', json_output=False)
                except SystemExit:
                    pass
            
            output = f.getvalue()
            assert 'doc1' in output
            
        finally:
            refs_dir.cleanup()

    def test_url_normalization_no_md_extension(self, temp_dir):
        """Test that URLs are normalized (no .md extension) in search results."""
        refs_dir = TempReferencesDir()
        
        try:
            # Create index with URL that has .md extension
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1.md', 'test/doc1.md',
                                                title='Test Document', keywords=['test']),
                'doc2': create_mock_index_entry('doc2', 'https://example.com/doc2.md#section', 'test/doc2.md',
                                                title='Test Document 2', keywords=['test'])
            }
            refs_dir.create_index(index)
            
            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search, cmd_query
            from scripts.core.doc_resolver import DocResolver
            
            resolver = DocResolver(refs_dir.references_dir)
            
            import io
            import contextlib
            import json
            
            # Test cmd_search JSON output
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_search(resolver, ['test'], limit=10, json_output=True)
                except SystemExit:
                    pass
            
            output = f.getvalue()
            json_data = json.loads(output)
            # Handle new format with 'results' key or legacy list format
            results = json_data.get('results', json_data) if isinstance(json_data, dict) else json_data

            # Verify URLs don't have .md extension
            for result in results:
                url = result.get('url', '')
                if url:
                    # URL should not have .md extension (except in path)
                    assert not url.endswith('.md'), f"URL should not end with .md: {url}"
                    assert '.md#' not in url, f"URL should not have .md before fragment: {url}"

            # Test cmd_query JSON output
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_query(resolver, 'test', limit=10, json_output=True)
                except SystemExit:
                    pass

            output = f.getvalue()
            json_data = json.loads(output)
            # Handle new format with 'results' key or legacy list format
            results = json_data.get('results', json_data) if isinstance(json_data, dict) else json_data

            # Verify URLs don't have .md extension
            for result in results:
                url = result.get('url', '')
                if url:
                    assert not url.endswith('.md'), f"URL should not end with .md: {url}"
                    assert '.md#' not in url, f"URL should not have .md before fragment: {url}"

            # Test that URLs with fragments still work correctly
            # doc2 has URL with .md and fragment - should be normalized
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_query(resolver, 'test', limit=10, json_output=True)
                except SystemExit:
                    pass

            output = f.getvalue()
            json_data = json.loads(output)
            # Handle new format with 'results' key or legacy list format
            results = json_data.get('results', json_data) if isinstance(json_data, dict) else json_data

            # Find doc2 in results
            for result in results:
                if result.get('doc_id') == 'doc2':
                    url = result.get('url', '')
                    # Should have fragment but not .md before it
                    assert '#' in url, "URL should have fragment"
                    assert url.endswith('#section'), f"URL should end with fragment: {url}"
                    assert '.md#' not in url, f"URL should not have .md before fragment: {url}"

        finally:
            refs_dir.cleanup()

    def test_search_merges_index_and_content_results(self, temp_dir):
        """Test that search merges results from keyword index AND file content."""
        refs_dir = TempReferencesDir()

        try:
            # Create doc with keyword in index
            index = {
                'indexed-doc': create_mock_index_entry('indexed-doc', 'https://example.com/indexed', 'test/indexed.md',
                                                       title='Indexed Document', keywords=['settings', 'config']),
                'content-only-doc': create_mock_index_entry('content-only-doc', 'https://example.com/content', 'test/content.md',
                                                            title='Content Only Doc', keywords=['other', 'stuff'])
            }
            refs_dir.create_index(index)

            # Create file for content-only-doc with 'enabledPlugins' in content
            content_file = refs_dir.references_dir / 'test' / 'content.md'
            content_file.parent.mkdir(parents=True, exist_ok=True)
            content_file.write_text('# Content\n\nThis has enabledPlugins setting.')

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib
            import json

            # Search for term only in file content
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_search(resolver, ['enabledPlugins'], limit=10, json_output=True)
                except SystemExit:
                    pass

            output = f.getvalue()
            json_data = json.loads(output)
            # Handle new format with 'results' key or legacy list format
            results = json_data.get('results', json_data) if isinstance(json_data, dict) else json_data

            # Should find content-only-doc via content search
            assert len(results) > 0
            doc_ids = [r['doc_id'] for r in results]
            assert 'content-only-doc' in doc_ids

            # Verify match_source is 'content'
            for r in results:
                if r['doc_id'] == 'content-only-doc':
                    assert r.get('match_source') == 'content'

        finally:
            refs_dir.cleanup()

    def test_search_fast_flag_skips_content_search(self, temp_dir):
        """Test that --fast flag (no_content=True) skips content search."""
        refs_dir = TempReferencesDir()

        try:
            # Create doc where term is ONLY in file content, not in index
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                title='Document', keywords=['other', 'keywords'])
            }
            refs_dir.create_index(index)

            # Create file with 'enabledPlugins' in content
            doc_file = refs_dir.references_dir / 'test' / 'doc1.md'
            doc_file.parent.mkdir(parents=True, exist_ok=True)
            doc_file.write_text('# Doc\n\nThis has enabledPlugins in content.')

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib

            # Search with no_content=True (fast mode)
            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    # no_content=True should skip content search
                    cmd_search(resolver, ['enabledPlugins'], limit=10, json_output=False, no_content=True)
                except SystemExit:
                    pass

            output = f.getvalue()

            # Should NOT find the document (term only in content, content search disabled)
            assert 'No documents found' in output or 'doc1' not in output

        finally:
            refs_dir.cleanup()

    def test_search_shows_content_tag_for_content_only_matches(self, temp_dir):
        """Test that [CONTENT] tag is shown for content-only matches in human output."""
        refs_dir = TempReferencesDir()

        try:
            index = {
                'doc1': create_mock_index_entry('doc1', 'https://example.com/doc1', 'test/doc1.md',
                                                title='Settings Doc', keywords=['other'])
            }
            refs_dir.create_index(index)

            doc_file = refs_dir.references_dir / 'test' / 'doc1.md'
            doc_file.parent.mkdir(parents=True, exist_ok=True)
            doc_file.write_text('# Settings\n\nThe enabledPlugins setting.')

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    cmd_search(resolver, ['enabledPlugins'], limit=10, json_output=False)
                except SystemExit:
                    pass

            output = f.getvalue()

            # Should show [CONTENT] tag for content-only match
            assert '[CONTENT]' in output

        finally:
            refs_dir.cleanup()

    def test_search_shows_truncation_message(self, temp_dir):
        """Test that truncation message shows when results are limited."""
        refs_dir = TempReferencesDir()

        try:
            # Create 60 documents to exceed default limit
            index = {}
            for i in range(60):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['test', 'document']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    # Use limit=10 to force truncation (no_content=True to skip content search)
                    result_count = cmd_search(resolver, ['test'], limit=10, json_output=False, no_content=True)
                except SystemExit:
                    pass

            output = f.getvalue()

            # Should show truncation message with total count
            assert '10 of 60 total' in output or 'showing 10' in output

        finally:
            refs_dir.cleanup()

    def test_search_no_limit_returns_all(self, temp_dir):
        """Test that limit=None returns all results."""
        refs_dir = TempReferencesDir()

        try:
            # Create 60 documents
            index = {}
            for i in range(60):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['test', 'document']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib
            import json

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    # Use limit=None (no limit)
                    result_count = cmd_search(resolver, ['test'], limit=None, json_output=True)
                except SystemExit:
                    pass

            output = f.getvalue()
            json_data = json.loads(output)
            results = json_data.get('results', json_data) if isinstance(json_data, dict) else json_data

            # Should return all 60 documents
            assert len(results) == 60
            # JSON should show total_available equals count
            if isinstance(json_data, dict):
                assert json_data.get('total_available') == 60
                assert json_data.get('count') == 60

        finally:
            refs_dir.cleanup()

    def test_search_min_score_filter(self, temp_dir):
        """Test that min_score filters low-relevance results."""
        refs_dir = TempReferencesDir()

        try:
            # Create docs with varying relevance
            index = {
                'high-relevance': create_mock_index_entry(
                    'high-relevance', 'https://example.com/high', 'test/high.md',
                    title='Skills Guide', keywords=['skills', 'guide', 'skills', 'agent skills'],
                    tags=['skills']
                ),
                'medium-relevance': create_mock_index_entry(
                    'medium-relevance', 'https://example.com/medium', 'test/medium.md',
                    title='General Guide', keywords=['skills'],
                    tags=['guides']
                ),
                'low-relevance': create_mock_index_entry(
                    'low-relevance', 'https://example.com/low', 'test/low.md',
                    title='Other Document', keywords=['other'],
                    tags=['other']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Search with high min_score
            results_high = resolver.search_by_keyword(['skills'], limit=10, return_scores=True, min_score=20)
            results_low = resolver.search_by_keyword(['skills'], limit=10, return_scores=True, min_score=1)

            # High min_score should return fewer results
            assert len(results_high) <= len(results_low)

            # All results with high min_score should have score >= 20
            for doc_id, metadata in results_high:
                assert metadata.get('_score', 0) >= 20

        finally:
            refs_dir.cleanup()

    def test_json_output_includes_total_available(self, temp_dir):
        """Test that JSON output includes total_available metadata."""
        refs_dir = TempReferencesDir()

        try:
            # Create 20 documents
            index = {}
            for i in range(20):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['test']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.find_docs import cmd_search
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            import io
            import contextlib
            import json

            f = io.StringIO()
            with contextlib.redirect_stdout(f):
                try:
                    # Use limit=5 to trigger truncation (no_content=True to skip content search)
                    cmd_search(resolver, ['test'], limit=5, json_output=True, no_content=True)
                except SystemExit:
                    pass

            output = f.getvalue()
            json_data = json.loads(output)

            # Should have count, total_available, and results keys
            assert 'count' in json_data
            assert 'total_available' in json_data
            assert 'results' in json_data
            assert json_data['count'] == 5
            assert json_data['total_available'] == 20
            assert len(json_data['results']) == 5

        finally:
            refs_dir.cleanup()
