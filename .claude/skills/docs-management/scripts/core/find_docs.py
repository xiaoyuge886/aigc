#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
find_docs.py - Find and resolve documentation references

CLI tool for discovering and resolving documentation:
- Resolve doc_id to file path
- Search by keywords
- Search by natural language query
- Filter by category/tag
- Find related documents

Usage:
    python find_docs.py resolve <doc_id>
    python find_docs.py search <keyword1> [keyword2 ...]
    python find_docs.py query "natural language query"
    python find_docs.py category <category>
    python find_docs.py tag <tag>
    python find_docs.py related <doc_id>
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json

from utils.cli_utils import add_common_index_args
from utils.script_utils import (
    configure_utf8_output,
    resolve_base_dir,
    EXIT_SUCCESS,
    EXIT_NO_RESULTS,
    EXIT_BAD_ARGS,
    EXIT_INDEX_ERROR,
    normalize_url_for_display,
)
from utils.logging_utils import get_or_setup_logger

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Script logger (structured, with performance tracking)
logger = get_or_setup_logger(__file__, log_category="search")

try:
    from core.doc_resolver import DocResolver
except ImportError:
    try:
        from scripts.core.doc_resolver import DocResolver
    except ImportError:
        print("❌ Error: Could not import doc_resolver")
        print("Make sure doc_resolver.py is available (core/doc_resolver.py).")
        sys.exit(EXIT_INDEX_ERROR)

# Hybrid pattern reminder for CLI output (not JSON)
HYBRID_REMINDER = """
----------------------------------------
HYBRID PATTERN - LOCAL CACHE ONLY

For COMPLETE Claude Code documentation coverage:

IF MAIN AGENT: Also spawn claude-code-guide subagent (Task tool)
               for live web search in the SAME message.

IF SUBAGENT:   Include in your response:
               "For comprehensive coverage, main agent should also
               query claude-code-guide subagent for live web search."
----------------------------------------
"""


def cmd_resolve(resolver: DocResolver, doc_id: str, extract_path: str | None = None, json_output: bool = False) -> int:
    """Resolve doc_id to file path. Returns 1 if found, 0 if not found.

    Note: Caller should check return value and handle exit codes appropriately.
    """
    path = resolver.resolve_doc_id(doc_id, extract_path)

    if json_output:
        result = {
            'doc_id': doc_id,
            'path': str(path) if path else None,
            'found': path is not None
        }
        print(json.dumps(result, indent=2))
    else:
        if path:
            print(f"✅ Resolved: {path}")
            print(f"   doc_id: {doc_id}")
        else:
            print(f"❌ Not found: {doc_id}")

    return 1 if path else 0


def _format_result_entry(doc_id: str, metadata: dict) -> dict:
    """
    Format a single result entry with standardized field ordering and classification.

    Result Classification:
    - 'subsection': Document has relevant subsection match
    - 'general': Document matches query (full document match)

    Priority ordering:
    1. doc_id (primary identifier for Claude Code references)
    2. path (local file path - PRIMARY reference for Claude Code)
    3. section_ref (subsection anchor if applicable)
    4. section_heading (human-readable section title)
    5. title (document title)
    6. url (web URL - SECONDARY/informational only)
    7. type (subsection or general)
    8. description, category, tags (metadata)
    9. extraction_command (if subsection match)
    """
    # Build result with proper field ordering
    result = {
        'doc_id': doc_id,
        'path': metadata.get('path')
    }

    # Get matched subsection (if any)
    matched_subsection = metadata.get('_matched_subsection')

    # Classify result type
    if matched_subsection:
        # Document has relevant subsection
        result['type'] = 'subsection'
        result['section_ref'] = matched_subsection.get('anchor')
        result['section_heading'] = matched_subsection.get('heading')
    else:
        # General match (full document match)
        result['type'] = 'general'

    # Add remaining fields
    result['title'] = metadata.get('title')
    result['url'] = normalize_url_for_display(metadata.get('url'))
    result['description'] = metadata.get('description')
    result['category'] = metadata.get('category')
    result['tags'] = metadata.get('tags', [])

    # Add extraction command for subsections
    if matched_subsection and metadata.get('_extraction_command'):
        result['extraction_command'] = metadata.get('_extraction_command')

    return result


def _display_search_results(results: list[tuple[str, dict]], header: str, verbose: bool = False) -> None:
    """Display search results with consistent formatting.

    Args:
        results: List of (doc_id, metadata) tuples
        header: Header text to display (e.g., "Found X document(s):")
        verbose: If True, show score details
    """
    print(f"📋 {header}\n")
    for i, (doc_id, metadata) in enumerate(results, 1):
        entry = _format_result_entry(doc_id, metadata)

        # Display with clear hierarchy
        type_indicator = " [SUBSECTION]" if entry['type'] == 'subsection' else ""
        score_indicator = f" (score: {metadata.get('_score', 'N/A')})" if verbose else ""
        print(f"{i}. {entry['title']}{type_indicator}{score_indicator}")
        print(f"   doc_id: {entry['doc_id']}")
        if entry['path']:
            print(f"   path: {entry['path']}")
        if entry.get('section_ref'):
            print(f"   section: {entry['section_ref']} ({entry.get('section_heading')})")
        if entry['url']:
            print(f"   url: {entry['url']} (web reference only)")
        if entry.get('description'):
            desc = entry['description'][:100] + '...' if len(entry['description']) > 100 else entry['description']
            print(f"   description: {desc}")
        if entry.get('extraction_command'):
            print(f"   extract: {entry['extraction_command']}")
        print()


def _display_search_results_merged(results: list[tuple[str, dict]], index_doc_ids: set[str],
                                    verbose: bool = False, show_context: bool = False,
                                    total_available: int | None = None, limit: int | None = None) -> None:
    """Display merged search results showing match source (index vs content).

    Args:
        results: List of (doc_id, metadata) tuples
        index_doc_ids: Set of doc_ids that matched via keyword index
        verbose: If True, show score details
        show_context: If True, show grep match line numbers and snippets
        total_available: Total number of results available before limiting
        limit: The limit that was applied (None if no limit)
    """
    # Show truncation notice if results were limited
    if total_available is not None and len(results) < total_available:
        print(f"📋 Found {len(results)} document(s) (showing {len(results)} of {total_available} total, use --no-limit for all):\n")
    else:
        print(f"📋 Found {len(results)} document(s):\n")
    for i, (doc_id, metadata) in enumerate(results, 1):
        entry = _format_result_entry(doc_id, metadata)

        # Determine match source indicator
        is_content_only = metadata.get('_content_match') and doc_id not in index_doc_ids
        type_indicator = " [CONTENT]" if is_content_only else ""
        if entry['type'] == 'subsection':
            type_indicator = " [SUBSECTION]" + type_indicator

        score_indicator = f" (score: {metadata.get('_score', 'N/A')})" if verbose else ""
        print(f"{i}. {entry['title']}{type_indicator}{score_indicator}")
        print(f"   doc_id: {entry['doc_id']}")
        if entry['path']:
            print(f"   path: {entry['path']}")
        if entry.get('section_ref'):
            print(f"   section: {entry['section_ref']} ({entry.get('section_heading')})")
        if entry['url']:
            print(f"   url: {entry['url']} (web reference only)")
        if entry.get('description'):
            desc = entry['description'][:100] + '...' if len(entry['description']) > 100 else entry['description']
            print(f"   description: {desc}")
        if entry.get('extraction_command'):
            print(f"   extract: {entry['extraction_command']}")
        # Show grep matches if available and requested
        if show_context and metadata.get('_grep_matches'):
            print(f"   grep_matches:")
            for match in metadata['_grep_matches']:
                print(f"      L{match['line']}: {match['text']}")
        print()


def _display_search_results_separate(index_results: list[tuple[str, dict]],
                                      content_only_results: list[tuple[str, dict]],
                                      content_doc_ids: set[str],
                                      verbose: bool = False,
                                      show_context: bool = False,
                                      total_available: int | None = None,
                                      limit: int | None = None) -> None:
    """Display search results in separate sections for index vs content matches.

    Args:
        index_results: List of (doc_id, metadata) tuples from keyword index
        content_only_results: List of (doc_id, metadata) tuples from content search only
        content_doc_ids: Set of all doc_ids that matched via content search
        verbose: If True, show score details
        show_context: If True, show grep match line numbers and snippets
        total_available: Total number of results available before limiting
        limit: The limit that was applied (None if no limit)
    """
    total = len(index_results) + len(content_only_results)
    overlap = len([doc_id for doc_id, _ in index_results if doc_id in content_doc_ids])

    # Index results section
    if index_results:
        print(f"📋 Index Matches ({len(index_results)} from keyword index):\n")
        for i, (doc_id, metadata) in enumerate(index_results, 1):
            entry = _format_result_entry(doc_id, metadata)
            type_indicator = " [SUBSECTION]" if entry['type'] == 'subsection' else ""
            also_in_content = " (+content)" if doc_id in content_doc_ids else ""
            score_indicator = f" (score: {metadata.get('_score', 'N/A')})" if verbose else ""
            print(f"{i}. {entry['title']}{type_indicator}{also_in_content}{score_indicator}")
            print(f"   doc_id: {entry['doc_id']}")
            if entry['path']:
                print(f"   path: {entry['path']}")
            if entry.get('section_ref'):
                print(f"   section: {entry['section_ref']} ({entry.get('section_heading')})")
            if entry['url']:
                print(f"   url: {entry['url']} (web reference only)")
            if entry.get('description'):
                desc = entry['description'][:100] + '...' if len(entry['description']) > 100 else entry['description']
                print(f"   description: {desc}")
            print()
    else:
        print("📋 Index Matches: (none)\n")

    # Content-only results section
    if content_only_results:
        print(f"📋 Content Matches ({len(content_only_results)} from file grep, not in index):\n")
        for i, (doc_id, metadata) in enumerate(content_only_results, 1):
            entry = _format_result_entry(doc_id, metadata)
            type_indicator = " [SUBSECTION]" if entry['type'] == 'subsection' else ""
            print(f"{i}. {entry['title']}{type_indicator}")
            print(f"   doc_id: {entry['doc_id']}")
            if entry['path']:
                print(f"   path: {entry['path']}")
            if entry['url']:
                print(f"   url: {entry['url']} (web reference only)")
            if entry.get('description'):
                desc = entry['description'][:100] + '...' if len(entry['description']) > 100 else entry['description']
                print(f"   description: {desc}")
            # Show grep matches if available and requested
            if show_context and metadata.get('_grep_matches'):
                print(f"   grep_matches:")
                for match in metadata['_grep_matches']:
                    print(f"      L{match['line']}: {match['text']}")
            print()
    else:
        print("📋 Content Matches: (none - all matches found in index)\n")

    # Summary
    summary = f"📊 Summary: {len(index_results)} index + {len(content_only_results)} content-only = {total} total"
    if overlap > 0:
        summary += f" ({overlap} found in both)"
    if total_available is not None and total < total_available:
        summary += f" [showing {total} of {total_available} available, use --no-limit for all]"
    print(summary)


def cmd_search(resolver: DocResolver, keywords: list[str], category: str | None = None,
              tags: list[str] | None = None, limit: int | None = 25, json_output: bool = False,
              verbose: bool = False, no_content: bool = False, separate: bool = False,
              show_context: bool = False, min_score: float | None = None) -> int:
    """Search documents by keywords with optional content search.

    By default, searches both the keyword index AND file content, merging results.
    Use no_content=True to disable content search for faster index-only results.
    Use separate=True to display index and content results in separate sections.
    Use show_context=True to include line numbers and text snippets from grep matches.
    Use limit=None for no limit on results.
    Use min_score to filter results below a relevance threshold.

    Returns number of results found.
    """
    # Always use high limit internally to get all candidates for accurate "X of Y" display
    # User's limit is applied after merging results
    internal_limit = 10000

    # Step 1: Search keyword index (existing behavior)
    # Always request scores for min_score filtering (verbose will expose them to user)
    index_results = resolver.search_by_keyword(keywords, category=category, tags=tags,
                                                limit=internal_limit, return_scores=True,
                                                min_score=min_score)

    # Track which doc_ids came from index
    index_doc_ids = {doc_id for doc_id, _ in index_results}

    # Step 2: Search file content (unless disabled)
    content_results: list[tuple[str, dict]] = []
    content_only_results: list[tuple[str, dict]] = []
    content_metadata_by_id: dict[str, dict] = {}  # For merging grep matches
    if not no_content:
        content_results = resolver.search_content(keywords, limit=internal_limit, include_context=show_context)
        # Build lookup for content metadata (to merge grep matches into index results)
        for doc_id, metadata in content_results:
            content_metadata_by_id[doc_id] = metadata
            # Filter to content-only matches (not already in index results)
            if doc_id not in index_doc_ids:
                content_only_results.append((doc_id, metadata))

    # Build set of content-matched doc_ids for source tracking
    content_doc_ids = {doc_id for doc_id, _ in content_results}

    # Step 3: Merge results (index first, then content-only)
    # For index results that also have content matches, merge in the grep matches
    all_results = []
    for doc_id, metadata in index_results:
        if doc_id in content_metadata_by_id:
            # Merge grep matches from content search into index result
            content_meta = content_metadata_by_id[doc_id]
            if content_meta.get('_grep_matches'):
                metadata = dict(metadata)  # Copy to avoid mutating original
                metadata['_grep_matches'] = content_meta['_grep_matches']
                metadata['_content_match'] = True
        all_results.append((doc_id, metadata))
    # Add content-only results
    all_results.extend(content_only_results)

    # Track total available before applying limit
    total_available = len(all_results)

    # Apply limit if specified
    if limit is not None and len(all_results) > limit:
        results = all_results[:limit]
    else:
        results = all_results

    if json_output:
        output_data = {
            'results': [],
            'count': len(results),
            'total_available': total_available
        }
        for doc_id, metadata in results:
            entry = _format_result_entry(doc_id, metadata)
            # Add match source indicator
            if metadata.get('_content_match') and doc_id not in index_doc_ids:
                entry['match_source'] = 'content'
            elif doc_id in index_doc_ids:
                # Check if also matched by content
                if doc_id in content_doc_ids:
                    entry['match_source'] = 'index+content'
                else:
                    entry['match_source'] = 'index'
            # Add grep matches if available
            if metadata.get('_grep_matches'):
                entry['grep_matches'] = metadata['_grep_matches']
            # Include score if available (for debugging/verification)
            if metadata.get('_score') is not None:
                entry['score'] = metadata['_score']
            output_data['results'].append(entry)
        print(json.dumps(output_data, indent=2))
    else:
        if not results:
            print(f"❌ No documents found for keywords: {', '.join(keywords)}")
            sys.exit(EXIT_NO_RESULTS)

        if separate:
            _display_search_results_separate(index_results, content_only_results, content_doc_ids,
                                              verbose, show_context, total_available, limit)
        else:
            _display_search_results_merged(results, index_doc_ids, verbose, show_context,
                                            total_available, limit)

    return len(results)


def cmd_query(resolver: DocResolver, query: str, limit: int | None = 25, json_output: bool = False,
              verbose: bool = False, min_score: float | None = None) -> int:
    """Search documents using natural language query. Returns number of results found."""
    # Always use high limit internally to get all candidates for accurate "X of Y" display
    # User's limit is applied after getting all results
    internal_limit = 10000

    all_results = resolver.search_by_natural_language(query, limit=internal_limit,
                                                       return_scores=True, min_score=min_score)

    # Track total available before applying limit
    total_available = len(all_results)

    # Apply limit if specified
    if limit is not None and len(all_results) > limit:
        results = all_results[:limit]
    else:
        results = all_results

    if json_output:
        output_data = {
            'results': [_format_result_entry(doc_id, metadata) for doc_id, metadata in results],
            'count': len(results),
            'total_available': total_available
        }
        # Include scores if available
        for i, (doc_id, metadata) in enumerate(results):
            if metadata.get('_score') is not None:
                output_data['results'][i]['score'] = metadata['_score']
        print(json.dumps(output_data, indent=2))
    else:
        if not results:
            print(f"❌ No documents found for query: {query}")
            sys.exit(EXIT_NO_RESULTS)

        # Show truncation notice if results were limited
        if total_available > len(results):
            header = f"Found {len(results)} document(s) for query: '{query}' (showing {len(results)} of {total_available} total, use --no-limit for all)"
        else:
            header = f"Found {len(results)} document(s) for query: '{query}'"
        _display_search_results(results, header, verbose)

    return len(results)


def cmd_category(resolver: DocResolver, category: str, json_output: bool = False) -> int:
    """List all documents in a category. Returns number of results found."""
    results = resolver.get_by_category(category)

    if json_output:
        output = [_format_result_entry(doc_id, metadata) for doc_id, metadata in results]
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"❌ No documents found in category: {category}")
            sys.exit(EXIT_NO_RESULTS)

        print(f"📋 Documents in category '{category}' ({len(results)}):\n")
        for i, (doc_id, metadata) in enumerate(results, 1):
            title = metadata.get('title', 'Untitled')
            print(f"{i}. {title} ({doc_id})")
        print()

    return len(results)


def cmd_tag(resolver: DocResolver, tag: str, json_output: bool = False) -> int:
    """List all documents with a specific tag. Returns number of results found."""
    results = resolver.get_by_tag(tag)

    if json_output:
        output = [_format_result_entry(doc_id, metadata) for doc_id, metadata in results]
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"❌ No documents found with tag: {tag}")
            sys.exit(EXIT_NO_RESULTS)

        print(f"📋 Documents with tag '{tag}' ({len(results)}):\n")
        for i, (doc_id, metadata) in enumerate(results, 1):
            title = metadata.get('title', 'Untitled')
            print(f"{i}. {title} ({doc_id})")
        print()

    return len(results)


def cmd_content(resolver: DocResolver, doc_id: str, section: str | None = None, json_output: bool = False) -> int:
    """Get document content (full or partial section). Returns 1 if found, 0 if not found."""
    content_result = resolver.get_content(doc_id, section)

    if not content_result:
        print(f"❌ Document not found or content unavailable: {doc_id}")
        sys.exit(EXIT_NO_RESULTS)

    if json_output:
        # Normalize URL in JSON output
        content_result_copy = content_result.copy()
        if 'url' in content_result_copy:
            content_result_copy['url'] = normalize_url_for_display(content_result_copy['url'])
        print(json.dumps(content_result_copy, indent=2))
    else:
        print(f"📄 Document: {content_result.get('title', doc_id)}")
        print(f"   doc_id: {doc_id}")
        if content_result.get('url'):
            print(f"   url: {normalize_url_for_display(content_result.get('url'))}")
        if content_result.get('section_ref'):
            print(f"   section: {content_result.get('section_ref')}")
        print(f"   content_type: {content_result.get('content_type', 'unknown')}")
        print()
        print("⚠️ " + content_result.get('warning', 'Do not store file paths.'))
        print()
        if content_result.get('content'):
            content = content_result['content']
            # Show first 500 chars if content is long
            if len(content) > 500:
                print(content[:500] + "\n... (truncated, use --json for full content)")
            else:
                print(content)
        else:
            print("(Content not available - link only)")

    return 1 if content_result else 0


def cmd_related(resolver: DocResolver, doc_id: str, limit: int = 5, json_output: bool = False) -> int:
    """Find related documents. Returns number of results found."""
    results = resolver.get_related_docs(doc_id, limit=limit)

    if json_output:
        output = []
        for doc_id_result, metadata in results:
            output.append({
                'doc_id': doc_id_result,
                'title': metadata.get('title'),
                'url': normalize_url_for_display(metadata.get('url'))
            })
        print(json.dumps(output, indent=2))
    else:
        if not results:
            print(f"❌ No related documents found for: {doc_id}")
            sys.exit(EXIT_NO_RESULTS)

        print(f"📋 Related documents for '{doc_id}' ({len(results)}):\n")
        for i, (related_id, metadata) in enumerate(results, 1):
            title = metadata.get('title', 'Untitled')
            print(f"{i}. {title} ({related_id})")
        print()

    return len(results)


def main() -> None:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Find and resolve documentation references',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Resolve doc_id to path (using default base directory)
  python find_docs.py resolve code-claude-com-docs-en-skills

  # Resolve doc_id and output JSON (for tools/agents)
  python find_docs.py --json resolve code-claude-com-docs-en-skills
  
  # Get full document content
  python find_docs.py content code-claude-com-docs-en-skills
  
  # Get specific section content
  python find_docs.py content code-claude-com-docs-en-skills --section "Progressive disclosure"
  
  # Search by keywords
  python find_docs.py search skills progressive-disclosure
  
  # Natural language search
  python find_docs.py query "how to create skills"
  
  # List by category
  python find_docs.py category api
  
  # List by tag
  python find_docs.py tag skills
  
  # Find related docs
  python find_docs.py related code-claude-com-docs-en-skills
        """
    )
    
    add_common_index_args(parser, include_json=True)
    parser.add_argument('--limit', type=int, default=25, help='Maximum results (default: 25)')
    parser.add_argument('--no-limit', action='store_true', help='Return all matching results (no limit)')
    parser.add_argument('--min-score', type=float, default=None, help='Only return results above this score threshold')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show scoring details for search results')
    parser.add_argument('--clear-cache', action='store_true', help='Clear cache before operation (forces rebuild)')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Resolve command
    resolve_parser = subparsers.add_parser('resolve', help='Resolve doc_id to file path')
    resolve_parser.add_argument('doc_id', help='Document ID to resolve')
    resolve_parser.add_argument('--extract-path', help='Optional extract path')
    
    # Content command
    content_parser = subparsers.add_parser('content', help='Get document content (full or partial section)')
    content_parser.add_argument('doc_id', help='Document ID')
    content_parser.add_argument('--section', help='Optional section heading to extract')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search by keywords')
    search_parser.add_argument('keywords', nargs='+', help='Keywords to search for')
    search_parser.add_argument('--category', help='Filter by category')
    search_parser.add_argument('--tags', nargs='+', help='Filter by tags')
    search_parser.add_argument('--fast', action='store_true', dest='no_content',
                              help='Fast mode: search index only, skip file content grep')
    search_parser.add_argument('--separate', action='store_true',
                              help='Display index and content matches in separate sections')
    search_parser.add_argument('--no-context', action='store_true', dest='no_context',
                              help='Hide line numbers and text snippets from grep results (shown by default)')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Natural language search')
    query_parser.add_argument('query', help='Natural language query')
    
    # Category command
    category_parser = subparsers.add_parser('category', help='List documents by category')
    category_parser.add_argument('category', help='Category name')
    
    # Tag command
    tag_parser = subparsers.add_parser('tag', help='List documents by tag')
    tag_parser.add_argument('tag', help='Tag name')
    
    # Related command
    related_parser = subparsers.add_parser('related', help='Find related documents')
    related_parser.add_argument('doc_id', help='Document ID to find related docs for')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(EXIT_BAD_ARGS)
    
    # Log script start
    logger.start({
        'command': args.command,
        'base_dir': args.base_dir,
        'json': args.json
    })
    
    exit_code = EXIT_SUCCESS
    result_count = 0
    try:
        # Resolve base directory
        base_dir = resolve_base_dir(args.base_dir)

        # Clear cache if requested
        if getattr(args, 'clear_cache', False):
            try:
                from utils.cache_manager import CacheManager
                cm = CacheManager(base_dir)
                cm.clear_inverted_index()
                print('Cache cleared. Rebuilding index...\n')
            except ImportError:
                print('Warning: CacheManager not available, skipping cache clear')

        # Initialize resolver
        resolver = DocResolver(base_dir)

        # Calculate effective limit (None means no limit)
        effective_limit = None if getattr(args, 'no_limit', False) else args.limit
        min_score = getattr(args, 'min_score', None)

        # Execute command and capture result count
        if args.command == 'resolve':
            result_count = cmd_resolve(resolver, args.doc_id, getattr(args, 'extract_path', None), args.json)
            if result_count == 0 and not args.json:
                exit_code = EXIT_NO_RESULTS
        elif args.command == 'content':
            result_count = cmd_content(resolver, args.doc_id, getattr(args, 'section', None), args.json)
        elif args.command == 'search':
            result_count = cmd_search(resolver, args.keywords, getattr(args, 'category', None),
                      getattr(args, 'tags', None), effective_limit, args.json, args.verbose,
                      getattr(args, 'no_content', False), getattr(args, 'separate', False),
                      not getattr(args, 'no_context', False), min_score)
        elif args.command == 'query':
            result_count = cmd_query(resolver, args.query, effective_limit, args.json, args.verbose, min_score)
        elif args.command == 'category':
            result_count = cmd_category(resolver, args.category, args.json)
        elif args.command == 'tag':
            result_count = cmd_tag(resolver, args.tag, args.json)
        elif args.command == 'related':
            result_count = cmd_related(resolver, args.doc_id, effective_limit, args.json)
        else:
            parser.print_help()
            exit_code = 1

        # Print hybrid pattern reminder for CLI output
        if not args.json and result_count > 0:
            print(HYBRID_REMINDER)

        logger.end(exit_code=exit_code, summary={'results_found': result_count})
        
    except SystemExit:
        raise
    except Exception as e:
        # Sanitize error to avoid exposing full paths or sensitive info in logs
        logger.log_error("Fatal error in find_docs", error_type=type(e).__name__,
                         message=str(e)[:200])
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)


if __name__ == '__main__':
    main()

