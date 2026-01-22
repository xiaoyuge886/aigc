# Parallelization Strategy: Script-Level vs Task Agents

## Two Parallelization Approaches

This skill supports **two complementary parallelization strategies**:

1. **Script-level parallelization** (ThreadPoolExecutor) - Fast, efficient for I/O-bound operations
2. **Task agent parallelization** (Claude Code Task tool) - Intelligent, context-aware, better error handling

## When to Use Task Agents for Parallelization

**Use Task agents for parallel scraping when:**

- ✅ **Complex error recovery needed** - Task agents can intelligently retry, analyze failures, and adapt strategies
- ✅ **Context management critical** - Each source needs separate context to avoid information overload
- ✅ **Intelligent task distribution** - Claude can dynamically allocate resources based on source complexity
- ✅ **User explicitly requests it** - "Use Task agents to scrape all sources in parallel"
- ✅ **Pre-scraping analysis required** - Spawn Task agents to analyze sitemaps, estimate counts, verify accessibility in parallel
- ✅ **Post-scraping deep validation** - Use Task agents for complex content analysis across multiple sources

**Use script-level parallelization (default) when:**

- ✅ **Routine operations** - Standard scraping with known sources
- ✅ **Speed is priority** - ThreadPoolExecutor is faster for I/O-bound tasks
- ✅ **Simple error handling sufficient** - Scripts handle retries and rate limiting adequately
- ✅ **Token efficiency matters** - Script-level avoids per-agent context overhead

## Current Implementation

**Script-level parallelization (default):**

- **Domain-level parallelization** - Different domains scrape in parallel via ThreadPoolExecutor
- **Sequential within domains** - Respects rate limits and prevents overwhelming servers  
- **Parallel validation** - All source validations run concurrently after scraping completes
- **Fast and efficient** - Minimal overhead, optimal for routine operations

**To use Task agents instead:**

When the skill is invoked, you can request Task agent parallelization:

```markdown
"Scrape all sources using Task agents in parallel - each source should be handled by a separate Task agent for better error recovery and context management."
```

The skill will then spawn parallel Task agents, one per source or domain, each with:

- Independent context window
- Specialized error handling
- Intelligent retry strategies
- Better isolation between sources

## Task Agent Usage Examples

### Example 1: Parallel scraping with Task agents

```markdown
Spawn parallel Task agents for each domain:
1. Task agent: Scrape docs.claude.com (all 4 sources sequentially within agent)
2. Task agent: Scrape code.claude.com  
3. Task agent: Scrape anthropic.com (all 3 sources sequentially within agent)

Each agent operates independently with its own context, error handling, and retry logic.
```

### Example 2: Complex troubleshooting with Task agents

```markdown
When scraping fails, spawn parallel Task agents to investigate:
1. Task agent: Analyze sitemap structure and URL patterns for docs.claude.com
2. Task agent: Investigate file system permissions and directory structure
3. Task agent: Check network connectivity and rate limiting issues
4. Task agent: Review frontmatter quality and hash calculation logic

Each agent investigates independently, then results are synthesized.
```

## Decision Tree

**Use single Task agent + script (default) when:**

- Routine scraping operations
- All sources are known and well-tested
- Speed is priority
- Token efficiency matters
- Simple error handling is sufficient

**Use multiple Task agents when:**

- User explicitly requests: "scrape using Task agents" or "each source independently"
- Complex error scenarios requiring intelligent recovery
- New sources needing analysis before scraping
- Deep validation requiring per-source intelligence
- Troubleshooting where isolation helps

## Implementation Notes

**The scripts support both approaches:**

1. **Single agent approach**: Call `scrape_all_sources.py` which handles all parallelization internally
2. **Multiple agent approach**: Each agent calls `scrape_docs.py` for its specific source

**Scripts are already optimized for both:**

- `scrape_all_sources.py` - Orchestrates multiple sources with ThreadPoolExecutor
- `scrape_docs.py` - Handles single source scraping (can be called independently)

**No script changes needed** - both modes are already supported. The choice is in how you invoke them via Task agents.

## Troubleshooting Parallel Failures

### Task Agents Fail to Spawn

**Symptom:** Task tool calls fail or agents don't start

**Causes:**

1. **Context limit reached** - Too many agents requested
2. **Invalid agent configuration** - Malformed Task parameters
3. **System resource constraints** - Too many concurrent processes

**Solutions:**

1. **Reduce parallelism** - Use fewer agents (3-5 is optimal)
2. **Sequential fallback** - Run tasks one at a time
3. **Check Task syntax** - Verify parameters are correct

### Agents Complete But Results Missing

**Symptom:** Agents finish but output is empty or incomplete

**Causes:**

1. **Agent prompt unclear** - Insufficient task description
2. **File write failures** - Permission or path issues
3. **Agent encountered errors** - Failed silently

**Solutions:**

1. **Review agent prompts** - Ensure comprehensive instructions
2. **Check output files** - Verify agents created expected files
3. **Review agent logs** - Look for error messages
4. **Add explicit deliverables** - Specify exactly what agent should produce

### Script-Level Parallelization Hangs

**Symptom:** ThreadPoolExecutor never completes

**Causes:**

1. **Deadlock** - Thread synchronization issue
2. **Network timeout** - One thread waiting indefinitely
3. **Exception swallowed** - Error not propagated

**Solutions:**

1. **Add timeouts** - Set maximum wait time per operation
2. **Enable verbose logging** - See which thread is stuck
3. **Fallback to sequential** - Disable parallelization temporarily

### Inconsistent Results Across Agents

**Symptom:** Different agents produce conflicting output

**Causes:**

1. **Race conditions** - Agents modifying shared resources
2. **Non-deterministic behavior** - Agents interpreting prompts differently
3. **Stale context** - Agents using outdated information

**Solutions:**

1. **Isolate agent tasks** - Ensure complete independence
2. **Clarify prompts** - Make instructions more specific
3. **Validate agent outputs** - Cross-check results before using
4. **Use sequential when needed** - Some tasks require ordering

### Performance Worse with Parallelization

**Symptom:** Parallel execution slower than sequential

**Causes:**

1. **Too many agents** - Overhead exceeds benefit
2. **I/O bottleneck** - Disk/network can't keep up
3. **Small tasks** - Parallelization overhead dominates

**Solutions:**

1. **Reduce agent count** - Optimal is usually 3-5
2. **Batch small tasks** - Group into larger units of work
3. **Profile execution** - Measure where time is spent
4. **Use sequential for simple tasks** - Parallelization overkill

## Related Guides

- **[Best Practices](best-practices.md)** - Overall workflow guidance
- **[Technical Details](technical-details.md)** - Implementation details
- **[Scraping Guide](capabilities/scraping-guide.md)** - Scraping-specific workflows
