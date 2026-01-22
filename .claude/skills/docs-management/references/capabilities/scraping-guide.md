# Scraping Documentation

## Purpose

Fetch documentation from official sources and store in canonical storage.

**Script:** `scripts/core/scrape_docs.py`

## Capabilities

- **Sitemap parsing** - Extract URLs from sitemap.xml with regex filtering
- **Docs map parsing** - Parse Claude Code docs map markdown for URLs
- **HTML→Markdown conversion** - Automatic conversion using BeautifulSoup + markdownify
- **Metadata tracking** - Add frontmatter with source URL, fetch date, content hash
- **Index management** - Automatic updates to `index.yaml`
- **Rate limiting** - Polite scraping with configurable delays

## Table of Contents

- [Purpose](#purpose)
- [Capabilities](#capabilities)
- [Usage Patterns](#usage-patterns)
- [Key Features](#key-features)
- [Markdown URL Strategy](#markdown-url-strategy)
- [Documentation Discovery Workflow](#documentation-discovery-workflow)
- [Folder Structure Convention](#folder-structure-convention)

## Usage Patterns

```bash
# Scrape from sitemap (auto-detects output directory from domain)
python scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/docs/"
# Output: docs-claude-com/docs/

# Scrape API reference (auto-detection)
python scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/api/"
# Output: docs-claude-com/api/

# Scrape resources (auto-detection)
python scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/resources/"
# Output: docs-claude-com/resources/

# Scrape from Claude Code docs map (auto-detection)
python scrape_docs.py \
    --docs-map https://code.claude.com/docs/en/claude_code_docs_map.md
# Output: code-claude-com/docs/en/

# Override auto-detection with custom output directory (rarely needed)
python scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/docs/" \
    --output custom-folder

# Scrape single URL (requires --output)
python scrape_docs.py \
    --url https://docs.claude.com/en/docs/intro \
    --output docs-claude-com/docs/intro.md

# Test with limit (first 5 URLs only)
python scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/docs/" \
    --limit 5
```

## Key Features

- **Auto-discovery:** Sitemaps ensure comprehensive coverage
- **Filtering:** Regex patterns reduce noise (`/en/docs/`, `/engineering/`, etc.)
- **Batch processing:** Progress tracking and error handling
- **Provenance:** Every doc includes source attribution

## Markdown URL Strategy

The scraper implements a two-step fetch strategy to obtain clean markdown without page navigation, footers, or other web UI elements:

1. **Try `.md` URL first:** Attempts to fetch `{url}.md` (e.g., `https://docs.claude.com/en/docs/intro.md`)
2. **Verify markdown content:** Checks if response starts with `#` or `---` (markdown or frontmatter)
3. **Fallback to HTML conversion:** If `.md` URL returns 404 or non-markdown content, fetches HTML and converts

**Rationale:**

- Claude platform docs support `.md` suffix for direct markdown access
- Direct markdown eliminates navigation pollution (30-40% token savings)
- Fallback ensures compatibility with docs that don't support `.md` suffix

**Tracking:**

- `fetch_method` field in frontmatter indicates how content was fetched
  - `fetch_method: markdown` - Clean markdown from `.md` URL
  - `fetch_method: html` - Converted from HTML page

**Example:**

```bash
# URL: https://docs.claude.com/en/docs/intro
# Tries: https://docs.claude.com/en/docs/intro.md (succeeds, fetch_method: markdown)
# Frontmatter includes: fetch_method: markdown
```

## Documentation Discovery Workflow

To discover and scrape all available documentation categories (prevents missing content):

1. **Fetch the sitemap:**

   ```bash
   curl -s https://docs.claude.com/sitemap.xml > sitemap.xml
   ```

2. **Analyze path patterns** (extract unique top-level categories):

   ```bash
   grep -oP 'docs\.claude\.com/en/[^/]+/' sitemap.xml | sort -u
   ```

   Example output: `/en/docs/`, `/en/api/`, `/en/resources/`, `/en/release-notes/`

3. **Scrape each category** discovered:

   ```bash
   # For each category found, run:
   python scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml --filter "/en/CATEGORY/"
   ```

4. **Verify folder structure** matches domains and categories:

   ```bash
   # Use docs-management skill to list documents
   # Should show: docs-claude-com/, code-claude-com/, etc.
   ```

**Why this approach works:**

- ✅ **Discovery-based, not hardcoded** - Finds all categories automatically
- ✅ **Domain-based folders** - No naming collisions (each domain gets its own folder)
- ✅ **Language-aware** - Always use `/en/` filters (English-only by default)
- ✅ **Future-proof** - New categories detected automatically
- ✅ **Resilient to restructures** - Domain changes → folder name changes mechanically

## Folder Structure Convention

```text
canonical storage (location managed by skill)
  ├── {domain-normalized}/     # Domain with dots → hyphens (e.g., docs-claude-com)
  │   ├── {category}/          # Category from URL path (e.g., docs, api, resources)
  │   │   └── {path}.md        # Document path preserved (language code stripped)
  │   └── ...
  └── ...

Examples:
  https://docs.claude.com/en/docs/about-claude/glossary
  → docs-claude-com/docs/about-claude/glossary.md

  https://code.claude.com/docs/en/overview
  → code-claude-com/docs/en/overview.md

  https://docs.claude.com/en/api/messages
  → docs-claude-com/api/messages.md
```
