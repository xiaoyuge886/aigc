# Universal Audit Principles

**All auditor agents MUST follow these principles.** This file prevents hallucinated findings and cross-contamination of rules.

## Principle 1: Citation Required

**Every audit finding MUST have a citation.** No exceptions.

### Valid Citation Sources

| Source Type | Format | When to Use |
| --- | --- | --- |
| Official docs | `doc_id: [id]` | Rules from Claude Code documentation |
| Repo-specific | `repo-specific: [file]` | Standards specific to this repository |
| Technical analysis | `analysis: [type]` | Factual checks (file exists, syntax valid, circular refs) |

### Invalid Citation Sources

These are NOT valid:

- "Common sense" or "best practice" without documentation
- Rules inferred from other component types
- Security concerns without specific documented rule
- Assumptions about what "should" be true

**If you cannot cite a source, do not include the finding.**

## Principle 2: Component Scope

**Rules are scoped to specific component types.** Do NOT cross-apply rules.

| Component | Rules Apply From | Do NOT Apply From |
| --- | --- | --- |
| Memory files (CLAUDE.md) | Memory docs only | Skills, Hooks, MCP, Commands |
| Skills | Skills docs only | Memory, Hooks, MCP, Commands |
| Hooks | Hooks docs only | Memory, Skills, MCP, Commands |
| Commands | Commands docs only | Memory, Skills, Hooks, MCP |
| MCP servers | MCP docs only | Memory, Skills, Hooks, Commands |
| Agents | Agent docs only | Memory, Skills, Hooks, Commands |

### Common Cross-Contamination Mistakes

| Rule | Actually Applies To | Commonly Misapplied To |
| --- | --- | --- |
| "External sources are risky" | Skills (runtime fetch) | Memory files (static URLs) |
| "Sandboxing requirements" | Bash, MCP servers | Memory files, Skills |
| "Tool permission rules" | Agents | Memory files |
| "allowedTools validation" | Skills | Commands, Memory files |

**Before applying any rule, verify it explicitly mentions the component type you're auditing.**

## Principle 3: Distinguish Static vs Dynamic

| Content Type | Risk Level | Why |
| --- | --- | --- |
| Static reference URLs in docs | None | Just text - no code execution, no fetching |
| Dynamic URL fetching (WebFetch) | Medium | Content could contain injection |
| Code execution (Bash, scripts) | High | Arbitrary code execution |

**Static URLs in memory files or documentation are NOT a security risk** - they're the same as URLs in a README.

## Principle 4: Self-Check Before Reporting

Before finalizing any audit, verify:

- [ ] Every finding has a citation
- [ ] Every citation is from documentation for THIS component type
- [ ] No findings based on inferred or assumed rules
- [ ] No cross-contamination from other component types

## Applying These Principles

Each auditor agent should:

1. **Load this file** at the start of every audit
2. **Query docs-management** for component-specific rules
3. **Cite every finding** with source type
4. **Run self-check** before reporting
5. **Remove invalid findings** that fail citation requirements

---

**Last Updated:** 2025-12-15
**Purpose:** Prevent hallucinated audit findings across all component types
