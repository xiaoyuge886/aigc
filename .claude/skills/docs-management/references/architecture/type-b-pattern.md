# Type B Meta-Skill Pattern

This document explains the Type B meta-skill architectural pattern used by the docs-management skill. This pattern is designed for meta-skills that store documentation and provide discovery/resolution APIs to other skills.

## Overview

The Type B meta-skill pattern separates **official documentation storage** (private implementation) from **usage guidance** (public documentation) and provides a clean **delegation API** for external skills to discover and resolve documentation references.

## Architecture Diagram

```text
┌──────────────────────────────────────────────────────────────────┐
│ docs-management SKILL (Public Interface)                           │
│                                                                   │
│ ├─ SKILL.md          ← Hub (navigation, usage instructions)      │
│ ├─ references/       ← Technical guides (how to use the skill)   │
│ │   ├─ capabilities/      (skill features)                       │
│ │   ├─ workflows.md       (operational workflows)                │
│ │   ├─ technical-details.md (implementation details)             │
│ │   └─ troubleshooting.md (common issues)                        │
│ │                                                                 │
│ └─ PUBLIC API                                                    │
│     ├─ find_document()           (natural language queries)      │
│     ├─ resolve_doc_id()          (doc_id → content)              │
│     ├─ get_docs_by_tag()         (filtered retrieval)            │
│     ├─ search_by_keywords()      (keyword-based search)          │
│     └─ detect_drift()            (change detection)              │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
            │
            │ (Internal implementation - not exposed to external skills)
            ↓
┌──────────────────────────────────────────────────────────────────┐
│ canonical/ (PRIVATE - Internal Storage)                          │
│                                                                   │
│ ├─ docs-claude-com/     ← Scraped official docs (encapsulated)   │
│ ├─ code-claude-com/     ← Scraped official docs (encapsulated)   │
│ ├─ anthropic-com/       ← Scraped official docs (encapsulated)   │
│ ├─ index.yaml           ← Metadata index (encapsulated)          │
│ └─ scripts/             ← Implementation scripts (encapsulated)   │
│                                                                   │
└──────────────────────────────────────────────────────────────────┘
```

## Core Principles

### 1. Public Interface = Usage Guides Only

The public interface (SKILL.md + references/) contains **ONLY**:

- How to use the skill (workflows, workflows, best practices)
- Technical details about the skill's implementation
- Troubleshooting guides for using the skill
- Examples of how to invoke the skill's API

The public interface does **NOT** contain:

- Copies of official Claude Code documentation
- Official documentation content
- Direct references to canonical storage locations

### 2. Private Implementation = Encapsulated Storage

The `canonical/` directory is **purely internal**:

- Stores official documentation (like a database)
- Accessed only via the skill's API
- Never accessed directly by external skills
- Location and structure can change without breaking external skills

### 3. Clean Delegation API

External skills invoke docs-management using **natural language**:

```markdown
"Find documentation about skills"
"Locate the official guide for creating skills"
"Get the best practices documentation"
"Resolve the documentation reference for hooks"
```

They **never** need to know:

- Where files are stored
- How the index works
- The structure of canonical/
- File paths or directory layouts

## Why This Pattern Works

### Separation of Concerns

- **Skills** focus on their domain (implementation, features, workflows)
- **Canonical storage** focuses on holding official documentation
- **API** focuses on discovery and resolution

### Encapsulation Benefits

1. **Implementation hiding**: Internal structure can change without breaking external skills
2. **Consistent access**: All skills use the same API regardless of skill-specific differences
3. **Maintainability**: Updates to canonical storage don't require changes to external skills
4. **Resilience**: Doc_id references survive file moves/renames (alias resolution)

### Scalability

- Multiple meta-skills can provide different kinds of discovery/resolution
- Each meta-skill encapsulates its own implementation details
- External skills compose meta-skills via clean APIs

## Comparison: Type B vs Single-File Documentation

### Traditional (Anti-Pattern)

```text
skill/
├─ SKILL.md (contains 100 topics, 5,000+ lines)
├─ Copy of official docs about skills (duplication)
├─ Copy of official docs about hooks (duplication)
└─ Copy of official docs about memory (duplication)
```

**Problems**:

- Duplication of official docs
- Massive SKILL.md file
- Hard to maintain (update doc_id means updating multiple locations)
- Poor token efficiency (all content loaded at once)
- Tight coupling (external skills depend on SKILL.md content staying in sync)

### Type B Pattern (Recommended)

```text
skill/
├─ SKILL.md (contains only usage guidance ~450 lines)
├─ references/
│  ├─ capabilities/ (how to use each feature)
│  ├─ workflows.md (operational workflows)
│  └─ troubleshooting.md (common issues)
└─ PUBLIC API (discovery and resolution functions)

canonical/  (private)
├─ docs-claude-com/ (official docs stored here)
├─ code-claude-com/ (official docs stored here)
└─ index.yaml (metadata index)
```

**Benefits**:

- Zero duplication (official docs in one place)
- Lean public interface (only what external skills need)
- Progressive disclosure (load references on-demand)
- Token efficient (external skills load only what they need)
- Resilient references (doc_id resolution survives renames)
- Clean API (natural language invocation)

## Implementation Details

### How Discovery Works

#### Step 1: External skill invokes docs-management

```text
"Find documentation about skills"
```

#### Step 2: Skill receives natural language query

- Converts to keywords: ["skills", "documentation", "guide"]
- Searches index.yaml for matching documents

#### Step 3: Skill returns results

```python
[
    {
        'doc_id': 'code-claude-com-docs-en-skills',
        'path': 'code-claude-com/docs/en/skills.md',
        'title': 'Skills',
        'url': 'https://code.claude.com/en/docs/skills',
        'keywords': ['skills', 'progressive disclosure', 'agent skills'],
        'relevance_score': 0.95
    }
]
```

#### Step 4: External skill uses result

- Typically calls `resolve_doc_id()` to get content
- Uses only the public API (never accesses canonical/)
- Doesn't need to know how discovery works

### How Resolution Works

#### Step 1: External skill has doc_id

```python
doc_id = 'code-claude-com-docs-en-skills'
```

#### Step 2: Skill resolves doc_id to metadata

- Looks up in index.yaml
- Returns metadata: path, title, description, keywords, tags
- Returns full content if requested

#### Step 3: External skill uses content

- Reads the resolved document
- Works with the content regardless of file location
- If doc is renamed/moved, alias resolution still works

## Real-World Example: skill-development Skill

The skill-development skill follows the same Type B pattern:

```text
skill-development/
├─ SKILL.md (usage guides only)
├─ references/
│  ├─ metadata/ (naming, frontmatter, keywords)
│  ├─ patterns/ (progressive disclosure, composition)
│  ├─ workflows/ (creation, validation, testing)
│  └─ quality/ (audit guide)
└─ Delegates to docs-management for official documentation
```

Key similarity: Both separate **skill-specific guidance** from **official documentation**.

## When to Use Type B Pattern

Use Type B pattern when creating a meta-skill that:

1. **Stores or indexes documentation** - You maintain a repository of documents
2. **Provides discovery APIs** - You help other skills find documentation
3. **Stores metadata** - You maintain metadata (keywords, tags, aliases)
4. **Needs encapsulation** - You want to hide implementation details
5. **Serves other skills** - External skills delegate to you

## When NOT to Use Type B Pattern

Don't use Type B pattern for:

1. **Single-purpose skills** - Skills that do one thing and don't serve others
2. **Skill-specific documentation** - Documentation that describes only your skill (use SKILL.md instead)
3. **Application code** - Not appropriate for production applications (use Type A/C patterns instead)

## Summary

The Type B meta-skill pattern provides:

- **Clear separation**: Public interface vs private implementation
- **Clean API**: Natural language invocation, no file paths
- **Scalability**: Can be composed with other meta-skills
- **Maintainability**: Official docs in one place, no duplication
- **Resilience**: References survive structural changes

This pattern is ideal for documentation-serving skills and similar metadata-heavy meta-skills that need to maintain consistency across multiple consumers.

---

**See Also**:

- [Technical Details](../technical-details.md) - Implementation details
- [Best Practices](../best-practices.md) - Operational guidance
- [Workflows](../workflows.md) - Common operational patterns
