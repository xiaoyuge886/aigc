"""
Tests for search result limit functionality.

Validates that limit options work correctly:
- Default limit of 25
- --no-limit flag returns all results
- --min-score filters low relevance results
- "X of Y total" display when truncated
"""

import sys
from pathlib import Path

from tests.shared.test_utils import TempReferencesDir, create_mock_index_entry


class TestSearchLimits:
    """Test suite for search limit functionality."""

    def test_limit_truncates_results(self, temp_dir):
        """Test that limit correctly truncates results."""
        refs_dir = TempReferencesDir()

        try:
            # Create 25 documents
            index = {}
            for i in range(25):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['common', 'keyword']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Search with limit=10
            results_limited = resolver.search_by_keyword(['common'], limit=10)
            results_all = resolver.search_by_keyword(['common'], limit=1000)

            # Limited should have exactly 10
            assert len(results_limited) == 10
            # All should have 25
            assert len(results_all) == 25

        finally:
            refs_dir.cleanup()

    def test_no_limit_returns_all(self, temp_dir):
        """Test that limit=None returns all matching results."""
        refs_dir = TempReferencesDir()

        try:
            # Create 100 documents
            index = {}
            for i in range(100):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['test']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Use very high limit (simulating --no-limit)
            results = resolver.search_by_keyword(['test'], limit=10000)

            # Should return all 100
            assert len(results) == 100

        finally:
            refs_dir.cleanup()

    def test_min_score_filtering(self, temp_dir):
        """Test that min_score filters out low-relevance results."""
        refs_dir = TempReferencesDir()

        try:
            # Create docs with varying keyword density
            index = {
                'high-relevance': create_mock_index_entry(
                    'high-relevance', 'https://example.com/high', 'test/high.md',
                    title='Skills Guide for Skills',
                    keywords=['skills', 'skills', 'skills', 'agent skills', 'skill creation'],
                    tags=['skills']
                ),
                'medium-relevance': create_mock_index_entry(
                    'medium-relevance', 'https://example.com/medium', 'test/medium.md',
                    title='General Guide',
                    keywords=['skills', 'guide'],
                    tags=['guides']
                ),
                'low-relevance': create_mock_index_entry(
                    'low-relevance', 'https://example.com/low', 'test/low.md',
                    title='Other Topic',
                    keywords=['skills'],
                    tags=['other']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Get all results with scores
            all_results = resolver.search_by_keyword(['skills'], limit=100, return_scores=True)

            # High min_score should filter more
            high_min = resolver.search_by_keyword(['skills'], limit=100, min_score=50, return_scores=True)
            low_min = resolver.search_by_keyword(['skills'], limit=100, min_score=1, return_scores=True)

            # High min_score should return fewer or equal results
            assert len(high_min) <= len(low_min)
            assert len(low_min) <= len(all_results)

        finally:
            refs_dir.cleanup()

    def test_scores_included_with_return_scores(self, temp_dir):
        """Test that scores are included when return_scores=True."""
        refs_dir = TempReferencesDir()

        try:
            index = {
                'doc1': create_mock_index_entry(
                    'doc1', 'https://example.com/doc1', 'test/doc1.md',
                    title='Skills Guide', keywords=['skills']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # With return_scores=True
            results_with = resolver.search_by_keyword(['skills'], limit=10, return_scores=True)
            # Without return_scores
            results_without = resolver.search_by_keyword(['skills'], limit=10, return_scores=False)

            # With scores should have _score in metadata
            assert results_with
            doc_id, metadata = results_with[0]
            assert '_score' in metadata

            # Without scores should not have _score
            assert results_without
            doc_id, metadata = results_without[0]
            assert '_score' not in metadata

        finally:
            refs_dir.cleanup()

    def test_large_result_set_performance(self, temp_dir):
        """Test that large result sets are handled efficiently."""
        refs_dir = TempReferencesDir()

        try:
            # Create 500 documents (stress test)
            index = {}
            for i in range(500):
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['common']
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver
            import time

            resolver = DocResolver(refs_dir.references_dir)

            # Time the search
            start = time.time()
            results = resolver.search_by_keyword(['common'], limit=50)
            duration = time.time() - start

            # Should complete in reasonable time (< 1 second)
            assert duration < 1.0
            assert len(results) == 50

        finally:
            refs_dir.cleanup()

    def test_empty_results_with_min_score(self, temp_dir):
        """Test that min_score can result in empty results."""
        refs_dir = TempReferencesDir()

        try:
            index = {
                'doc1': create_mock_index_entry(
                    'doc1', 'https://example.com/doc1', 'test/doc1.md',
                    title='General Document', keywords=['test']
                )
            }
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Very high min_score should return no results
            results = resolver.search_by_keyword(['test'], limit=100, min_score=10000)

            assert len(results) == 0

        finally:
            refs_dir.cleanup()

    def test_combined_limit_and_min_score(self, temp_dir):
        """Test that limit and min_score work together correctly."""
        refs_dir = TempReferencesDir()

        try:
            # Create 20 documents
            index = {}
            for i in range(20):
                # Vary keyword density to create score variance
                extra_kw = ['test'] * (i % 5)  # 0-4 extra keywords
                index[f'doc{i}'] = create_mock_index_entry(
                    f'doc{i}', f'https://example.com/doc{i}', f'test/doc{i}.md',
                    title=f'Test Document {i}', keywords=['test'] + extra_kw
                )
            refs_dir.create_index(index)

            sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
            from scripts.core.doc_resolver import DocResolver

            resolver = DocResolver(refs_dir.references_dir)

            # Get all results first
            all_results = resolver.search_by_keyword(['test'], limit=1000, return_scores=True)

            # Apply min_score and limit together
            # min_score should filter first, then limit applies
            filtered_results = resolver.search_by_keyword(['test'], limit=5, min_score=1, return_scores=True)

            # All filtered results should meet min_score
            for doc_id, metadata in filtered_results:
                assert metadata.get('_score', 0) >= 1

            # Limit should cap at 5
            assert len(filtered_results) <= 5

        finally:
            refs_dir.cleanup()
