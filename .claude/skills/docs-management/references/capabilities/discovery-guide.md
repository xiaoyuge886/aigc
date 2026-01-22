# Documentation Discovery Guide

## Purpose

Find and resolve Claude documentation using various discovery methods.

**Scripts:** `scripts/core/find_docs.py`, `scripts/resolve_doc.py`

## Capabilities

- **doc_id resolution** - Canonical identifier lookup
- **Keyword search** - Find documents by keywords
- **Natural language queries** - Discover docs using plain language
- **Tag filtering** - Browse by topic tags
- **Category filtering** - Find by documentation category
- **Alias resolution** - Match alternative phrasings
- **Multi-criteria search** - Combine filters for precision

## Table of Contents

- [Purpose](#purpose)
- [Capabilities](#capabilities)
- [Discovery Methods](#discovery-methods)
- [doc_id Resolution Process](#doc_id-resolution-process)
- [Keyword-Based Search](#keyword-based-search)
- [Natural Language Queries](#natural-language-queries)
- [Tag and Category Filtering](#tag-and-category-filtering)
- [Alias Resolution](#alias-resolution)
- [Combined Search Strategies](#combined-search-strategies)
- [Best Practices](#best-practices)

## Discovery Methods

The docs-management skill supports multiple discovery strategies, each suited for different use cases:

| Method | Use Case | Example |
| --- | --- | --- |
| **doc_id** | Direct lookup by canonical ID | `intro-to-claude` |
| **Keywords** | Topic-based search | `"prompt engineering"` |
| **Natural language** | Conversational queries | `"how do I use the API?"` |
| **Tags** | Browse by topic category | `tag: api` |
| **Category** | Browse by doc type | `category: getting-started` |
| **Alias** | Alternative phrasing match | `"messages endpoint"` → `api-messages` |

---

## doc_id Resolution Process

### What is a doc_id?

A **doc_id** is the canonical identifier for a document in the index. It's derived from the file path and serves as the primary key for lookups.

**Format:** `kebab-case-name` (lowercase, hyphens only, no file extension)

**Examples:**

- File: `docs-claude-com/docs/intro-to-claude.md` → doc_id: `intro-to-claude`
- File: `code-claude-com/docs/en/quickstart.md` → doc_id: `quickstart`

### Resolution Methods

#### Method 1: Direct lookup in index.yaml

```bash
python resolve_doc.py intro-to-claude
```

Searches `index.yaml` for exact doc_id match.

#### Method 2: Fuzzy matching

```bash
python resolve_doc.py "intro claude"
```

If exact match fails, tries fuzzy matching:

- Normalizes input (lowercase, replace spaces with hyphens)
- Tries partial matches
- Suggests closest matches if not found

#### Method 3: Alias resolution

```bash
python resolve_doc.py "getting started with claude"
```

Checks aliases field in index entries:

```yaml
- doc_id: intro-to-claude
  aliases:
    - "getting started with claude"
    - "claude introduction"
```

### Resolution Output

```bash
$ python resolve_doc.py intro-to-claude

Document found: intro-to-claude
Title: Introduction to Claude
File: (use docs-management skill to find file)
URL: https://docs.claude.com/en/docs/intro-to-claude
```

**Exit codes:**

- `0` - Document found and resolved
- `1` - Document not found

---

## Keyword-Based Search

### Using find_docs.py

```bash
# Single keyword
python find_docs.py --keyword "prompt engineering"

# Multiple keywords (AND logic)
python find_docs.py --keyword "prompt engineering" --keyword "best practices"

# Case-insensitive matching
python find_docs.py --keyword "API"  # Matches "api", "Api", "API"
```

### How Keyword Search Works

1. **Normalizes query** - Lowercase, trim whitespace
2. **Searches index** - Checks `keywords` field in each document
3. **Ranks results** - By relevance (exact match > partial match)
4. **Returns matches** - With title, doc_id, file_path

### Output Format

```bash
$ python find_docs.py --keyword "prompt engineering"

Found 5 documents matching: prompt engineering

1. prompt-engineering-guide
   Title: Prompt Engineering Guide
   Keywords: prompt engineering, best practices, optimization
   File: docs-claude-com/docs/prompt-engineering-guide.md

2. advanced-prompting
   Title: Advanced Prompting Techniques
   Keywords: prompting, prompt engineering, advanced
   File: docs-claude-com/docs/advanced-prompting.md

...
```

### Keyword Quality Tips

**Good keywords** (high signal):

- Specific technical terms: `"prompt engineering"`, `"API authentication"`
- Feature names: `"vision capabilities"`, `"tool use"`
- Concepts: `"rate limiting"`, `"context window"`

**Poor keywords** (low signal):

- Generic verbs: `"use"`, `"get"`, `"make"`
- Brand names: `"claude"`, `"anthropic"` (filtered via `filtering.yaml`)
- Single common words: `"guide"`, `"documentation"`

---

## Natural Language Queries

### Using Natural Language Discovery

```bash
# Conversational queries
python find_docs.py --query "how do I authenticate with the API?"

# Question-based discovery
python find_docs.py --query "what are claude's capabilities?"

# Problem-based search
python find_docs.py --query "I'm getting rate limit errors"
```

### How Natural Language Search Works

1. **Extracts intent** - Identifies key concepts from query
2. **Generates keywords** - Converts query to keyword set
3. **Searches index** - Uses extracted keywords for matching
4. **Ranks by relevance** - Prioritizes documents matching intent

**Example transformation:**

```text
Query: "how do I authenticate with the API?"
  ↓
Keywords: ["authenticate", "api", "authentication"]
  ↓
Matches: api-authentication.md, api-quickstart.md
```

### Query Optimization Tips

**Effective queries:**

- ✅ `"how to use vision with images"` → Extracts: vision, images
- ✅ `"rate limiting best practices"` → Extracts: rate limiting, best practices
- ✅ `"difference between claude models"` → Extracts: models, comparison

**Less effective queries:**

- ❌ `"help me"` → Too vague
- ❌ `"claude docs"` → Filtered out (brand name)
- ❌ `"I need to know about things"` → No clear intent

---

## Tag and Category Filtering

### Browsing by Tag

```bash
# Find all API documentation
python find_docs.py --tag api

# Find tutorials
python find_docs.py --tag tutorial

# Multiple tags (AND logic)
python find_docs.py --tag api --tag reference
```

### Browsing by Category

```bash
# Getting started guides
python find_docs.py --category getting-started

# API reference docs
python find_docs.py --category reference

# Advanced guides
python find_docs.py --category advanced
```

### Tag vs Category

**Tags** - Fine-grained topic labels (many per document)

- Examples: `api`, `tutorial`, `vision`, `prompt-engineering`
- Multiple tags per document
- User-defined, flexible

**Categories** - Broad document type (one per document)

- Examples: `getting-started`, `reference`, `guides`, `advanced`
- Single category per document
- Structural classification

### Common Tag Patterns

**By feature:**

- `vision`, `tool-use`, `streaming`, `embeddings`

**By topic:**

- `prompt-engineering`, `authentication`, `rate-limits`

**By audience:**

- `beginner`, `advanced`, `enterprise`

**By doc type:**

- `tutorial`, `reference`, `troubleshooting`, `best-practices`

---

## Alias Resolution

### What are Aliases?

Aliases allow documents to be discovered using alternative phrasings that users might search for.

**Example:**

```yaml
- doc_id: api-messages
  title: Messages API Reference
  aliases:
    - "messages endpoint"
    - "send messages API"
    - "chat completion API"
    - "conversation API"
```

### Using Aliases for Discovery

```bash
# Exact alias match
python resolve_doc.py "messages endpoint"
# → Resolves to: api-messages

# Partial alias match
python find_docs.py --query "send messages"
# → Finds: api-messages (via "send messages API" alias)
```

### When to Add Aliases

**Add aliases for:**

- ✅ Common alternative names (`"messages API"` vs `"chat API"`)
- ✅ Acronyms and expansions (`"NLP"` vs `"natural language processing"`)
- ✅ Synonyms (`"authenticate"` vs `"log in"`)
- ✅ User-facing vs internal names (`"vision"` vs `"image analysis"`)

**Don't add aliases for:**

- ❌ Trivial variations (`"api"` vs `"API"` - case-insensitive by default)
- ❌ Generic terms (`"guide"`, `"documentation"`)
- ❌ Redundant keywords (if already in `keywords` field)

---

## Combined Search Strategies

### Strategy 1: Narrow by Category, Search by Keyword

```bash
# Find prompt engineering docs in getting-started category
python find_docs.py --category getting-started --keyword "prompt engineering"

# Find API reference docs about authentication
python find_docs.py --category reference --keyword "authentication"
```

### Strategy 2: Multi-Keyword + Tag Filtering

```bash
# Advanced prompt engineering tutorials
python find_docs.py --keyword "prompt engineering" --keyword "advanced" --tag tutorial

# Vision-related API references
python find_docs.py --keyword "vision" --tag api --category reference
```

### Strategy 3: Natural Language + Refinement

```bash
# Step 1: Broad natural language query
python find_docs.py --query "how to use images with claude"

# Step 2: Refine with tags
python find_docs.py --keyword "images" --tag vision --tag tutorial

# Step 3: Direct doc_id once identified
python resolve_doc.py vision-quickstart
```

---

## Best Practices

### For Users Discovering Documentation

1. **Start broad, narrow down**

   ```bash
   # Too specific initially might miss relevant docs
   python find_docs.py --keyword "vision"  # Start here
   python find_docs.py --keyword "vision" --tag tutorial  # Refine
   ```

2. **Use natural language when unsure**

   ```bash
   # If you don't know exact terminology
   python find_docs.py --query "analyze images with claude"
   ```

3. **Browse by category first**

   ```bash
   # Get oriented in documentation structure
   python find_docs.py --category getting-started  # See what's available
   ```

4. **Check aliases for common phrases**
   - The index may have aliases for common user queries
   - Try natural phrasings even if they don't match doc_id exactly

### For Skill Maintainers

1. **Enrich keywords during indexing**
   - Use `manage_index.py extract-keywords` to improve discoverability
   - Review and manually curate keywords for high-value docs

2. **Add thoughtful aliases**
   - Think about how users actually search
   - Include common synonyms and alternative names
   - Don't over-alias (diminishing returns after 3-5 per doc)

3. **Tag consistently**
   - Establish tag vocabulary in `tag_detection.yaml`
   - Avoid tag sprawl (50 tags better than 500)
   - Review tags periodically for consistency

4. **Categorize meaningfully**
   - Keep category count low (5-10 categories ideal)
   - Categories should reflect user intent, not internal structure

---

## Examples

### Example 1: New User Finding Getting Started Docs

```bash
# Scenario: User new to Claude, wants to get started

# Approach 1: Browse getting-started category
python find_docs.py --category getting-started

# Approach 2: Natural language query
python find_docs.py --query "how do I get started with claude?"

# Approach 3: Direct doc_id (if they know it)
python resolve_doc.py intro-to-claude
```

### Example 2: Developer Looking for API Auth Docs

```bash
# Scenario: Developer needs API authentication documentation

# Approach 1: Keyword search
python find_docs.py --keyword "authentication" --tag api

# Approach 2: Natural language
python find_docs.py --query "how to authenticate API requests"

# Approach 3: Category + tag
python find_docs.py --category reference --tag api --keyword "auth"
```

### Example 3: Finding Vision-Related Tutorials

```bash
# Scenario: Want to learn about vision capabilities

# Step 1: Broad keyword search
python find_docs.py --keyword "vision"
# → Returns: vision-quickstart, vision-api-reference, vision-best-practices

# Step 2: Narrow to tutorials only
python find_docs.py --keyword "vision" --tag tutorial
# → Returns: vision-quickstart, vision-tutorial

# Step 3: Resolve specific doc
python resolve_doc.py vision-quickstart
# → Shows file path and URL for access
```

### Example 4: Troubleshooting Rate Limit Errors

```bash
# Scenario: Getting rate limit errors, need troubleshooting docs

# Approach 1: Natural language (problem-based)
python find_docs.py --query "rate limit errors"

# Approach 2: Keyword + tag
python find_docs.py --keyword "rate limiting" --tag troubleshooting

# Approach 3: Browse by category
python find_docs.py --category troubleshooting --keyword "rate"
```

---

## Discovery Workflow Diagram

```text
User Query
    ↓
┌─────────────────────────────────────────┐
│ Do you know the exact doc_id?           │
├─────────────────────────────────────────┤
│ YES → Use resolve_doc.py                │
│ NO  → Continue to discovery strategy    │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ What are you looking for?               │
├─────────────────────────────────────────┤
│ Specific topic → Keyword search         │
│ General guidance → Browse by category   │
│ Vague question → Natural language       │
│ Known alternative name → Check aliases  │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│ Refine results                          │
├─────────────────────────────────────────┤
│ Too many results → Add tags/filters     │
│ Too few results → Broaden keywords      │
│ Wrong results → Try natural language    │
└─────────────────────────────────────────┘
    ↓
Document Resolved ✓
```

---

**Last Updated:** 2025-11-16
**Related Guides:** index-management-guide.md, scraping-guide.md
