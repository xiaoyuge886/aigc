#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_search_audit.py - Analyze search audit results and identify issues

Reviews search results for:
- Relevance issues (top result not matching topic)
- Domain distribution issues
- Missing relevant docs
- Irrelevant docs in top 10
"""

import json
import sys
from pathlib import Path
from typing import Any

# Configure UTF-8 output for Windows console compatibility
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def analyze_topic(topic: str, topic_data: dict[str, Any]) -> dict[str, Any]:
    """Analyze all queries for a single topic"""
    
    issues = []
    stats = {
        "total_queries": len(topic_data["queries"]),
        "queries_with_issues": 0,
        "total_results": 0,
        "domain_distribution": {}
    }
    
    for query in topic_data["queries"]:
        query_type = query["type"]
        query_text = query["query"]
        results = query["results"]
        result_count = query["result_count"]
        
        stats["total_results"] += result_count
        
        # Check if top result is relevant
        if results:
            top_result = results[0]
            top_title = top_result["title"].lower()
            top_doc_id = top_result["doc_id"]
            top_domain = top_result["domain"]
            
            # Aggregate domain distribution
            for domain, count in query["domain_distribution"].items():
                stats["domain_distribution"][domain] = stats["domain_distribution"].get(domain, 0) + count
            
            # Relevance checks based on topic
            is_relevant = False

            # Define expected keywords for each topic
            topic_mapping = {
                "skills": ["skill", "agent skill"],
                "subagents": ["subagent", "sub-agent"],
                "commands": ["slash command", "command"],
                "hooks": ["hook"],
                "memory": ["memory", "claude.md"],
                "output-styles": ["output style"],
                "plugins": ["plugin"],
                "installation": ["install", "setup", "getting started"],
                "settings": ["setting", "configuration"],
                "config": ["config", "configuration"],
                "models": ["model"],
            }
            
            expected = topic_mapping.get(topic, [topic])
            
            # Check if any expected keyword is in title or doc_id
            for keyword in expected:
                if keyword in top_title or keyword in top_doc_id.lower():
                    is_relevant = True
                    break
            
            if not is_relevant:
                stats["queries_with_issues"] += 1
                issues.append({
                    "severity": "HIGH",
                    "query_type": query_type,
                    "query": query_text,
                    "issue": "Top result not relevant to topic",
                    "top_result_title": top_result["title"],
                    "top_result_doc_id": top_doc_id,
                    "top_result_domain": top_domain,
                    "expected_keywords": expected
                })
            
            # Check if code.claude.com docs are present
            has_code_claude = any(r["domain"] == "code.claude.com" for r in results)
            if not has_code_claude and topic in ["skills", "hooks", "commands", "memory", "output-styles", "subagents", "plugins"]:
                issues.append({
                    "severity": "MEDIUM",
                    "query_type": query_type,
                    "query": query_text,
                    "issue": "No code.claude.com results for Claude Code feature",
                    "note": "Claude Code features should include code.claude.com docs"
                })
            
            # Check for very low result counts on common topics
            if result_count < 5 and topic in ["skills", "hooks", "memory", "plugins"]:
                issues.append({
                    "severity": "MEDIUM",
                    "query_type": query_type,
                    "query": query_text,
                    "issue": f"Low result count ({result_count}) for common topic",
                })
        else:
            stats["queries_with_issues"] += 1
            issues.append({
                "severity": "CRITICAL",
                "query_type": query_type,
                "query": query_text,
                "issue": "No results returned",
            })
    
    return {
        "topic": topic,
        "issues": issues,
        "stats": stats
    }


def main() -> None:
    """Main entry point"""
    
    # Load audit results
    results_file = Path(".claude/temp/2025-11-17_search-audit-results.json")
    if not results_file.exists():
        print(f"❌ Results file not found: {results_file}")
        return 1
    
    with open(results_file, "r", encoding="utf-8") as f:
        audit_results = json.load(f)
    
    print("=" * 80)
    print("SEARCH AUDIT ANALYSIS")
    print("=" * 80)
    print()
    
    all_issues = []
    critical_count = 0
    high_count = 0
    medium_count = 0
    
    for topic, topic_data in audit_results["topics"].items():
        analysis = analyze_topic(topic, topic_data)
        
        if analysis["issues"]:
            all_issues.append(analysis)
            
            # Count by severity
            for issue in analysis["issues"]:
                severity = issue["severity"]
                if severity == "CRITICAL":
                    critical_count += 1
                elif severity == "HIGH":
                    high_count += 1
                elif severity == "MEDIUM":
                    medium_count += 1
    
    # Print summary
    print(f"📊 Summary:")
    print(f"  - Total topics analyzed: {len(audit_results['topics'])}")
    print(f"  - Topics with issues: {len(all_issues)}")
    print(f"  - Critical issues: {critical_count}")
    print(f"  - High severity issues: {high_count}")
    print(f"  - Medium severity issues: {medium_count}")
    print()
    
    # Print detailed issues by topic
    if all_issues:
        print("🔍 Detailed Issues by Topic:")
        print()
        
        for analysis in all_issues:
            topic = analysis["topic"]
            issues = analysis["issues"]
            stats = analysis["stats"]
            
            print(f"📌 Topic: {topic}")
            print(f"   Queries with issues: {stats['queries_with_issues']}/{stats['total_queries']}")
            print(f"   Domain distribution: {stats['domain_distribution']}")
            print()
            
            for issue in issues:
                severity = issue["severity"]
                emoji = "🔴" if severity == "CRITICAL" else "🟠" if severity == "HIGH" else "🟡"
                
                print(f"   {emoji} [{severity}] {issue['query_type']}: {issue['issue']}")
                print(f"      Query: {issue['query']}")
                
                if "top_result_title" in issue:
                    print(f"      Top result: {issue['top_result_title']}")
                    print(f"      Top doc_id: {issue['top_result_doc_id']}")
                    print(f"      Expected keywords: {issue['expected_keywords']}")
                
                if "note" in issue:
                    print(f"      Note: {issue['note']}")
                
                print()
    else:
        print("✅ No issues found!")
    
    # Save analysis report
    output_file = Path(".claude/temp/2025-11-17_search-audit-analysis.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump({
            "summary": {
                "total_topics": len(audit_results["topics"]),
                "topics_with_issues": len(all_issues),
                "critical_issues": critical_count,
                "high_severity_issues": high_count,
                "medium_severity_issues": medium_count
            },
            "issues_by_topic": all_issues
        }, f, indent=2, ensure_ascii=False)
    
    print("=" * 80)
    print(f"📄 Detailed analysis saved to: {output_file}")
    print("=" * 80)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

