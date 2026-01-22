# DocResolver API Reference

This document provides the Python API reference for `DocResolver`, the main class for documentation discovery and resolution.

## Quick Start

```python
from pathlib import Path
import sys

# Add scripts directory to path
skill_dir = Path("plugins/claude-ecosystem/skills/docs-management")
sys.path.insert(0, str(skill_dir / "scripts"))

from core.doc_resolver import DocResolver

# Initialize resolver with canonical directory
base_dir = skill_dir / "canonical"
resolver = DocResolver(base_dir)
```

## Constructor

### `DocResolver(base_dir: Path)`

Initialize the resolver with a base directory containing `index.yaml`.

**Parameters:**

- `base_dir` (Path): Base directory containing `index.yaml` (typically `canonical/`)

**Example:**

```python
from pathlib import Path
resolver = DocResolver(Path("canonical"))
```

---

## Core Methods

### `resolve_doc_id(doc_id: str, extract_path: str | None = None) -> Path | None`

Resolve a doc_id to its file path.

**Parameters:**

- `doc_id` (str): Document identifier (e.g., "code-claude-com-docs-en-skills")
- `extract_path` (str | None): Optional extract path for subsection

**Returns:** `Path` to the document file, or `None` if not found

**Example:**

```python
path = resolver.resolve_doc_id("code-claude-com-docs-en-skills")
# Returns: Path("canonical/code-claude-com/docs/en/skills.md")
```

---

### `search_by_keyword(keywords: list[str], category: str | None = None, limit: int = 25, min_score: float = 0.0) -> list[tuple[str, dict, float]]`

Search documents by keywords.

**Parameters:**

- `keywords` (list[str]): Keywords to search for
- `category` (str | None): Optional category filter
- `limit` (int): Maximum results (default: 25)
- `min_score` (float): Minimum relevance score (default: 0.0)

**Returns:** List of tuples: `(doc_id, metadata_dict, score)`

**Example:**

```python
results = resolver.search_by_keyword(["skills", "frontmatter"])
for doc_id, metadata, score in results:
    print(f"{doc_id}: {metadata.get('title')} (score: {score})")
```

---

### `search_by_natural_language(query: str, limit: int = 10, category: str | None = None) -> list[tuple[str, dict, float]]`

Search using natural language query.

**Parameters:**

- `query` (str): Natural language query (e.g., "how to create skills")
- `limit` (int): Maximum results (default: 10)
- `category` (str | None): Optional category filter

**Returns:** List of tuples: `(doc_id, metadata_dict, score)`

**Example:**

```python
results = resolver.search_by_natural_language("how to create custom hooks")
```

---

## Category Methods

### `get_by_category(category: str) -> list[tuple[str, dict]]`

Get all documents in a category.

**Parameters:**

- `category` (str): Category name (case-insensitive)

**Returns:** List of tuples: `(doc_id, metadata_dict)`

**Note:** Searches both `category` and `doc_map_category` fields.

**Example:**

```python
results = resolver.get_by_category("Build with Claude Code")
for doc_id, metadata in results:
    print(f"{doc_id}: {metadata.get('doc_map_category')}")

# Output:
# code-claude-com-docs-en-skills: Build with Claude Code
# code-claude-com-docs-en-hooks: Build with Claude Code
# ...
```

---

### `list_categories() -> dict[str, int]`

List all categories with document counts.

**Returns:** Dictionary mapping category names to document counts

**Example:**

```python
categories = resolver.list_categories()
# Returns:
# {
#     'Build with Claude Code': 10,
#     'Configuration': 19,
#     'Getting started': 5,
#     ...
# }
```

---

### `get_doc_map_categories() -> dict[str, list[str]]`

Get docs_map.md category hierarchy.

**Returns:** Dictionary mapping category names to lists of doc_ids

**Example:**

```python
doc_map = resolver.get_doc_map_categories()
# Returns:
# {
#     'Build with Claude Code': ['code-claude-com-docs-en-skills', ...],
#     'Reference': ['code-claude-com-docs-en-cli-reference', ...],
#     ...
# }
```

---

## Tag Methods

### `get_by_tag(tag: str) -> list[tuple[str, dict]]`

Get all documents with a specific tag.

**Parameters:**

- `tag` (str): Tag name (case-insensitive, normalized)

**Returns:** List of tuples: `(doc_id, metadata_dict)`

**Example:**

```python
results = resolver.get_by_tag("skills")
```

---

## Related Documents

### `get_related_docs(doc_id: str, limit: int = 5) -> list[tuple[str, dict]]`

Find documents related to a given document.

**Parameters:**

- `doc_id` (str): Source document identifier
- `limit` (int): Maximum results (default: 5)

**Returns:** List of tuples: `(doc_id, metadata_dict)`

**Example:**

```python
related = resolver.get_related_docs("code-claude-com-docs-en-skills")
```

---

## Content Methods

### `get_content(doc_id: str, section: str | None = None) -> dict[str, Any | None]`

Get document content, optionally extracting a specific section.

**Parameters:**

- `doc_id` (str): Document identifier
- `section` (str | None): Optional section heading to extract

**Returns:** Dictionary with keys:

- `content` (str | None): Document content (or section content)
- `path` (Path | None): File path
- `error` (str | None): Error message if failed

**Example:**

```python
result = resolver.get_content("code-claude-com-docs-en-skills", section="YAML frontmatter")
if result["content"]:
    print(result["content"])  # Prints just the YAML frontmatter section
```

---

## Content Search

### `search_content(keywords: list[str], limit: int = 10, min_score: float = 0.0) -> list[tuple[str, dict, float]]`

Search within document content (slower but more thorough).

**Parameters:**

- `keywords` (list[str]): Keywords to search for
- `limit` (int): Maximum results (default: 10)
- `min_score` (float): Minimum relevance score (default: 0.0)

**Returns:** List of tuples: `(doc_id, metadata_dict, score)`

---

## Common Patterns

### Category-Based Filtering

```python
# Get all skills documentation
skills_docs = resolver.get_by_category("Build with Claude Code")
print(f"Found {len(skills_docs)} documents in 'Build with Claude Code' category")

# List all available categories
all_categories = resolver.list_categories()
for category, count in sorted(all_categories.items()):
    print(f"  {category}: {count} docs")
```

### Keyword Search with Score Filtering

```python
# Search with minimum score threshold
results = resolver.search_by_keyword(
    keywords=["hooks", "PreToolUse"],
    min_score=50.0,  # Only high-relevance results
    limit=10
)

for doc_id, metadata, score in results:
    print(f"[{score:.1f}] {metadata.get('title')}")
```

### Subsection Extraction

```python
# Get just the section you need (60-90% token savings)
result = resolver.get_content(
    doc_id="code-claude-com-docs-en-skills",
    section="Configuration fields"
)

if result["content"]:
    # Only loads ~380 tokens instead of ~5,800 for full document
    print(result["content"])
```

---

## Error Handling

All methods return `None`, empty lists, or error dictionaries on failure - they do not raise exceptions.

```python
# Safe resolution
path = resolver.resolve_doc_id("nonexistent-doc-id")
if path is None:
    print("Document not found")

# Safe content retrieval
result = resolver.get_content("code-claude-com-docs-en-skills", section="Nonexistent")
if result.get("error"):
    print(f"Error: {result['error']}")
```
