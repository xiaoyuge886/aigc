#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
get_subsection_content.py - Get subsection content from documents (token-optimized)

Retrieves specific subsection content from documents without loading the full document.
Designed for token-efficient access when search results indicate a subsection match.

Usage:
    # Get subsection by doc_id and heading
    python get_subsection_content.py <doc_id> --section "Section Heading"
    
    # Get subsection by doc_id and anchor
    python get_subsection_content.py <doc_id> --anchor "#section-heading"
    
    # Output JSON format (for tools/agents)
    python get_subsection_content.py <doc_id> --section "Skills vs slash commands" --json

Examples:
    python get_subsection_content.py code-claude-com-docs-en-slash-commands \\
        --section "Skills vs slash commands"
    
    python get_subsection_content.py code-claude-com-docs-en-plugins \\
        --anchor "#add-skills-to-your-plugin"
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import argparse
import json

from utils.cli_utils import add_common_index_args
from utils.script_utils import configure_utf8_output, EXIT_SUCCESS, EXIT_NO_RESULTS, EXIT_BAD_ARGS, normalize_url_for_display
from utils.logging_utils import get_or_setup_logger

# Configure UTF-8 output for Windows console compatibility
configure_utf8_output()

# Script logger
logger = get_or_setup_logger(__file__, log_category="search")

try:
    from core.doc_resolver import DocResolver
except ImportError:
    print("❌ Error: Could not import doc_resolver")
    print("Make sure doc_resolver.py is available (core/doc_resolver.py).")
    sys.exit(1)

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

def list_document_sections(resolver: DocResolver, doc_id: str) -> list[dict]:
    """
    List all sections/headings in a document.

    Args:
        resolver: DocResolver instance
        doc_id: Document identifier

    Returns:
        List of section dicts with heading and level info
    """
    import re

    # First, get the document path
    path = resolver.resolve_doc_id(doc_id)
    if not path or not path.exists():
        return []

    # Read the document and extract headings
    content = path.read_text(encoding='utf-8')

    # Parse ATX headings (# ## ### etc.)
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)

    sections = []
    for match in heading_pattern.finditer(content):
        level = len(match.group(1))
        heading = match.group(2).strip()
        # Generate anchor
        anchor = '#' + re.sub(r'[^\w\s-]', '', heading.lower()).replace(' ', '-')
        sections.append({
            'level': level,
            'heading': heading,
            'anchor': anchor
        })

    return sections


def anchor_to_heading(anchor: str) -> str:
    """
    Convert anchor (#section-heading) to heading text (Section Heading)

    Args:
        anchor: Anchor string (with or without leading #)

    Returns:
        Heading text with title case
    """
    # Remove leading #
    if anchor.startswith('#'):
        anchor = anchor[1:]

    # Replace hyphens with spaces and title case
    heading = anchor.replace('-', ' ').title()
    return heading

def find_fuzzy_section_match(resolver: DocResolver, doc_id: str, search_term: str) -> dict | None:
    """
    Find a section heading that fuzzy-matches the search term.

    Args:
        resolver: DocResolver instance
        doc_id: Document identifier
        search_term: The section name to search for

    Returns:
        Dict with 'match' (best match heading) and 'suggestions' (other close matches),
        or None if no matches found
    """
    sections = list_document_sections(resolver, doc_id)
    if not sections:
        return None

    search_lower = search_term.lower()
    exact_matches = []
    contains_matches = []
    word_matches = []

    for s in sections:
        heading_lower = s['heading'].lower()

        # Exact match (case-insensitive)
        if heading_lower == search_lower:
            exact_matches.append(s['heading'])
        # Contains the search term
        elif search_lower in heading_lower:
            contains_matches.append(s['heading'])
        # Any word from search term appears in heading
        else:
            search_words = set(search_lower.split())
            heading_words = set(heading_lower.split())
            if search_words & heading_words:  # Intersection
                word_matches.append(s['heading'])

    # Priority: exact > contains > word overlap
    all_matches = exact_matches + contains_matches + word_matches

    if not all_matches:
        return None

    return {
        'match': all_matches[0],
        'suggestions': all_matches[1:5] if len(all_matches) > 1 else []
    }


def get_subsection_content(resolver: DocResolver, doc_id: str,
                          section: str | None = None,
                          anchor: str | None = None) -> dict | None:
    """
    Get subsection content from a document

    Args:
        resolver: DocResolver instance
        doc_id: Document identifier
        section: Section heading (optional if anchor provided)
        anchor: Section anchor like #section-heading (optional if section provided)

    Returns:
        Dictionary with content and metadata, or None if not found
    """
    # Use doc_resolver's get_content method
    if anchor and not section:
        # Convert anchor to heading
        section = anchor_to_heading(anchor)

    content_result = resolver.get_content(doc_id, section)

    # If section was specified but not found (content_type='full' means fallback to full doc),
    # try fuzzy matching before returning full document
    if section and content_result and content_result.get('content_type') == 'full':
        fuzzy = find_fuzzy_section_match(resolver, doc_id, section)
        if fuzzy and fuzzy.get('match'):
            matched_heading = fuzzy['match']
            fuzzy_result = resolver.get_content(doc_id, matched_heading)
            # Only use fuzzy result if it found the actual section (partial)
            if fuzzy_result and fuzzy_result.get('content_type') == 'partial':
                content_result = fuzzy_result
                content_result['fuzzy_matched'] = True
                content_result['original_query'] = section
                content_result['matched_section'] = matched_heading
                if fuzzy.get('suggestions'):
                    content_result['other_suggestions'] = fuzzy['suggestions']

    if not content_result:
        return None

    # Add token count estimate (rough: 1 token ≈ 4 characters)
    if content_result.get('content'):
        content_len = len(content_result['content'])
        content_result['token_estimate'] = content_len // 4
    else:
        content_result['token_estimate'] = 0

    return content_result

def print_content_result(result: dict, json_output: bool = False):
    """Print content result in CLI or JSON format"""
    if json_output:
        # Normalize URL in JSON output
        result_copy = result.copy()
        if 'url' in result_copy:
            result_copy['url'] = normalize_url_for_display(result_copy['url'])
        print(json.dumps(result_copy, indent=2))
        return
    
    # CLI output
    print(f"📄 Document: {result.get('title', 'Unknown')}")
    print(f"   doc_id: {result.get('doc_id', 'Unknown')}")
    
    if result.get('url'):
        print(f"   url: {normalize_url_for_display(result.get('url'))}")
    
    content_type = result.get('content_type', 'unknown')
    if content_type == 'partial':
        print(f"   section: {result.get('section_ref', 'Unknown')}")
        print(f"   type: Subsection (token-optimized)")
    elif content_type == 'full':
        print(f"   type: Full document")
    else:
        print(f"   type: Link only (content not extracted)")
    
    token_est = result.get('token_estimate', 0)
    if token_est > 0:
        print(f"   tokens: ~{token_est:,} tokens")

    # Show fuzzy match info
    if result.get('fuzzy_matched'):
        print()
        print(f"🔍 Fuzzy match: '{result.get('original_query')}' → '{result.get('matched_section')}'")
        if result.get('other_suggestions'):
            print(f"   Other matches: {', '.join(result['other_suggestions'][:3])}")

    print()

    if result.get('warning'):
        print(f"⚠️  {result['warning']}")
        print()
    
    if result.get('content'):
        content = result['content']
        # Show preview for long content
        if len(content) > 500 and not json_output:
            print("Content preview (first 500 chars):")
            print("-" * 70)
            print(content[:500])
            print(f"\n... ({len(content) - 500} more characters)")
            print("-" * 70)
            print()
            print(f"💡 Use --json flag to get full content")
        else:
            print("Content:")
            print("-" * 70)
            print(content)
            print("-" * 70)
    else:
        print("(Content not available - link only)")

    # Print hybrid pattern reminder for CLI output
    print(HYBRID_REMINDER)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Get subsection content from documents (token-optimized)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all sections in a document (discover available sections)
  python get_subsection_content.py code-claude-com-docs-en-skills --list-sections

  # Get subsection by heading
  python get_subsection_content.py code-claude-com-docs-en-slash-commands \\
      --section "Skills vs slash commands"

  # Get subsection by anchor
  python get_subsection_content.py code-claude-com-docs-en-plugins \\
      --anchor "#add-skills-to-your-plugin"

  # Output JSON for tools/agents
  python get_subsection_content.py code-claude-com-docs-en-skills \\
      --section "Progressive disclosure" --json

  # Get full document (no section specified)
  python get_subsection_content.py code-claude-com-docs-en-overview
        """
    )
    
    add_common_index_args(parser, include_json=True)
    
    parser.add_argument('doc_id', help='Document ID')
    parser.add_argument('--section', help='Section heading to extract')
    parser.add_argument('--anchor', help='Section anchor (e.g., #section-heading)')
    parser.add_argument('--list-sections', action='store_true',
                        help='List all available sections in the document')

    args = parser.parse_args()
    
    if not args.doc_id:
        parser.print_help()
        sys.exit(EXIT_BAD_ARGS)
    
    # Log script start
    logger.start({
        'doc_id': args.doc_id,
        'section': args.section,
        'anchor': args.anchor,
        'json': args.json
    })
    
    exit_code = EXIT_SUCCESS
    try:
        # Resolve base directory
        from utils.cli_utils import resolve_base_dir_from_args
        base_dir = resolve_base_dir_from_args(args)
        
        # Initialize resolver
        resolver = DocResolver(base_dir)

        # Handle --list-sections flag
        if getattr(args, 'list_sections', False):
            sections = list_document_sections(resolver, args.doc_id)
            if not sections:
                print(f"No sections found or document not found: {args.doc_id}")
                exit_code = EXIT_NO_RESULTS
            else:
                if args.json:
                    print(json.dumps({'doc_id': args.doc_id, 'sections': sections}, indent=2))
                else:
                    print(f"Sections in {args.doc_id}:")
                    print("-" * 60)
                    for s in sections:
                        indent = "  " * (s['level'] - 1)
                        print(f"{indent}{'#' * s['level']} {s['heading']}")
                    print("-" * 60)
                    print(f"\nTotal: {len(sections)} sections")
                    print("\nTo extract a section, use:")
                    print(f'  python get_subsection_content.py {args.doc_id} --section "Section Name"')
            logger.end(exit_code=exit_code)
            sys.exit(exit_code)

        # Get subsection content
        result = get_subsection_content(resolver, args.doc_id, args.section, args.anchor)
        
        if result:
            print_content_result(result, args.json)
            
            # Exit with appropriate code based on content type
            if result.get('content_type') == 'link':
                exit_code = EXIT_NO_RESULTS
        else:
            print(f"❌ Document not found or section not available: {args.doc_id}")
            if args.section:
                print(f"   Section: {args.section}")
            if args.anchor:
                print(f"   Anchor: {args.anchor}")
            exit_code = EXIT_NO_RESULTS
        
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)
        
    except SystemExit:
        raise
    except Exception as e:
        logger.log_error("Fatal error in get_subsection_content", error=e)
        exit_code = 1
        logger.end(exit_code=exit_code)
        sys.exit(exit_code)

if __name__ == '__main__':
    main()

