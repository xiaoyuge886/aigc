#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_search_audit.py - Comprehensive search audit for docs-management skill

Runs systematic searches for all topics and collects detailed results.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import json
from typing import Any
from core.doc_resolver import DocResolver
from utils.path_config import get_base_dir

# Topics to audit
TOPICS = [
    "skills",
    "subagents",
    "commands",
    "hooks",
    "memory",
    "output-styles",
    "plugins",
    "installation",
    "settings",
    "config",
    "models"
]

# Query templates for each topic
def get_queries(topic: str) -> list[dict[str, Any]]:
    """Get all query variations for a topic"""
    
    # Map special topics to their canonical forms
    topic_mapping = {
        "commands": "slash commands",
        "memory": "claude.md memory",
        "output-styles": "output styles",
    }
    
    search_term = topic_mapping.get(topic, topic)
    
    return [
        {
            "type": "simple",
            "description": f"Simple query: exact topic name",
            "keywords": [search_term]
        },
        {
            "type": "how-to",
            "description": f"How-to question",
            "query": f"how to create {search_term}",
        },
        {
            "type": "use-case",
            "description": f"Use-case question",
            "query": f"when to use {search_term}",
        },
        {
            "type": "comparison",
            "description": f"Comparison/troubleshooting",
            "query": f"{search_term} best practices",
        }
    ]


def format_result(doc_id: str, metadata: dict[str, Any], rank: int) -> dict[str, Any]:
    """Format a single search result for output"""
    return {
        "rank": rank,
        "doc_id": doc_id,
        "title": metadata.get("title", "N/A"),
        "url": metadata.get("url", "N/A"),
        "domain": metadata.get("domain", "N/A"),
        "category": metadata.get("category", "N/A"),
        "keywords": metadata.get("keywords", [])[:10],  # First 10 keywords
        "tags": metadata.get("tags", []),
        "description": metadata.get("description", "N/A")[:200],  # First 200 chars
        "has_subsection_match": metadata.get("_subsection_hint", False),
        "subsection": metadata.get("_matched_subsection", {}).get("heading", None) if "_matched_subsection" in metadata else None,
    }


def run_audit() -> dict[str, Any]:
    """Run complete search audit"""
    
    # Initialize resolver
    base_dir = get_base_dir()
    resolver = DocResolver(base_dir)
    
    results = {
        "metadata": {
            "total_topics": len(TOPICS),
            "total_queries": len(TOPICS) * 4,  # 4 query types per topic
            "base_dir": str(base_dir)
        },
        "topics": {}
    }
    
    print(f"🔍 Starting search audit for {len(TOPICS)} topics...")
    print(f"📊 Base directory: {base_dir}")
    print()
    
    for topic in TOPICS:
        print(f"🔎 Testing topic: {topic}")
        topic_results = {
            "queries": []
        }
        
        queries = get_queries(topic)
        
        for query_def in queries:
            query_type = query_def["type"]
            description = query_def["description"]
            
            # Execute search based on query type
            if "keywords" in query_def:
                # Keyword search
                search_results = resolver.search_by_keyword(query_def["keywords"], limit=10)
                query_text = " ".join(query_def["keywords"])
            else:
                # Natural language search
                search_results = resolver.search_by_natural_language(query_def["query"], limit=10)
                query_text = query_def["query"]
            
            # Format results
            formatted_results = [
                format_result(doc_id, metadata, rank + 1)
                for rank, (doc_id, metadata) in enumerate(search_results)
            ]
            
            # Count domain distribution
            domain_counts = {}
            for doc_id, metadata in search_results:
                domain = metadata.get("domain", "unknown")
                domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            query_result = {
                "type": query_type,
                "description": description,
                "query": query_text,
                "result_count": len(search_results),
                "domain_distribution": domain_counts,
                "results": formatted_results
            }
            
            topic_results["queries"].append(query_result)
            
            # Print summary
            top_result = formatted_results[0] if formatted_results else None
            if top_result:
                print(f"  ✓ {query_type:15s} ({len(formatted_results)} results) - Top: {top_result['title'][:60]}")
            else:
                print(f"  ✗ {query_type:15s} - NO RESULTS")
        
        results["topics"][topic] = topic_results
        print()
    
    return results


def main() -> None:
    """Main entry point"""
    print("=" * 80)
    print("CLAUDE DOCS SEARCH AUDIT")
    print("=" * 80)
    print()
    
    try:
        results = run_audit()
        
        # Save results to JSON file
        output_file = Path(".claude/temp/2025-11-17_search-audit-results.json")
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print("=" * 80)
        print(f"✅ Audit complete! Results saved to: {output_file}")
        print(f"📊 Total queries run: {results['metadata']['total_queries']}")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Error during audit: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

