# Index Management Documentation

## Purpose

Manage index.yaml operations including metadata, verification, and rebuilding.

**Script:** `scripts/management/manage_index.py`

## Capabilities

- **Index statistics** - Count documents and check coverage
- **Metadata management** - Keywords, tags, aliases, categories
- **Index verification** - Detect corruption and inconsistencies
- **Filtering** - Query index by various criteria
- **Keyword extraction** - Generate keywords from existing docs
- **Coverage analysis** - Identify gaps in metadata
- **Index rebuilding** - Reconstruct from filesystem

## Table of Contents

- [Purpose](#purpose)
- [Capabilities](#capabilities)
- [Usage Patterns](#usage-patterns)
- [Subcommands Reference](#subcommands-reference)
- [Metadata Management](#metadata-management)
- [Index Rebuilding](#index-rebuilding)
- [Corruption Detection](#corruption-detection)
- [Coverage Analysis](#coverage-analysis)

## Usage Patterns

```bash
# Count total documents in index
python manage_index.py count

# List all doc_ids
python manage_index.py list

# Get metadata for specific document
python manage_index.py get intro-to-claude

# Verify index integrity
python manage_index.py verify

# Filter by keyword
python manage_index.py filter --keyword "prompt engineering"

# Filter by tag
python manage_index.py filter --tag api

# Filter by category
python manage_index.py filter --category getting-started

# Extract keywords from document content
python manage_index.py extract-keywords intro-to-claude

# Check metadata coverage
python manage_index.py check-coverage

# Rebuild index from filesystem
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical
```

## Subcommands Reference

### `count` - Document Statistics

Display total number of documents in index.

```bash
python manage_index.py count
```

**Output:**

```text
Total documents in index: 147
```

**Use cases:**

- Quick health check
- Verify scraping completeness
- Track index growth over time

---

### `list` - List All Documents

Display all doc_ids in the index.

```bash
python manage_index.py list
```

**Output:**

```text
intro-to-claude
prompt-engineering-basics
api-messages-endpoint
...
```

**Options:**

- `--format json` - Output as JSON array
- `--filter-domain docs.claude.com` - Show only specific domain

**Use cases:**

- Browse available documentation
- Generate doc_id lists for batch operations
- Audit what's been scraped

---

### `get` - Retrieve Document Metadata

Get full metadata for a specific document.

```bash
python manage_index.py get intro-to-claude
```

**Output:**

```yaml
doc_id: intro-to-claude
title: Introduction to Claude
description: Getting started with Claude AI assistant
keywords:
  - introduction
  - getting started
  - claude basics
tags:
  - documentation
  - tutorial
category: getting-started
source_url: https://docs.claude.com/en/docs/intro-to-claude
fetch_date: '2025-11-16'
file_path: docs-claude-com/docs/intro-to-claude.md
content_hash: abc123...
```

**Use cases:**

- Inspect metadata quality
- Debug doc_id resolution
- Verify metadata after updates

---

### `verify` - Index Integrity Check

Verify index structure and detect corruption.

```bash
python manage_index.py verify
```

**Checks performed:**

- YAML syntax validity
- Required fields present (doc_id, file_path, source_url)
- File references point to existing files
- No duplicate doc_ids
- Hash consistency with file contents

**Output:**

```text
Verifying index integrity...

✓ YAML syntax valid
✓ All documents have required fields
✓ All file paths exist
✗ WARNING: 3 documents have mismatched content hashes
✗ ERROR: Duplicate doc_id found: 'getting-started' (2 entries)

Index verification FAILED (2 errors, 1 warning)
```

**Use cases:**

- Detect index corruption after manual edits
- Verify after bulk operations
- Troubleshoot doc resolution failures

---

### `filter` - Query Index by Criteria

Filter index by keywords, tags, categories, or aliases.

```bash
# By keyword
python manage_index.py filter --keyword "prompt engineering"

# By tag
python manage_index.py filter --tag api

# By category
python manage_index.py filter --category getting-started

# Combine filters (AND logic)
python manage_index.py filter --tag api --category reference

# By alias
python manage_index.py filter --alias "messages API"
```

**Output formats:**

- `--format list` (default) - doc_ids only, one per line
- `--format json` - Full metadata as JSON array
- `--format table` - Formatted table with key fields

**Use cases:**

- Find documentation by topic
- Generate filtered doc lists
- Audit metadata consistency

---

### `extract-keywords` - Generate Keywords from Content

Extract keywords from document content using NLP.

```bash
# Extract for single document
python manage_index.py extract-keywords intro-to-claude

# Extract and update index
python manage_index.py extract-keywords intro-to-claude --update

# Batch extraction for all documents
python manage_index.py extract-keywords --all

# Extract for documents missing keywords
python manage_index.py extract-keywords --missing-only
```

**Keyword extraction methods:**

1. Title and heading analysis
2. Frequency analysis (TF-IDF)
3. Named entity recognition
4. Tag-based inference

**Output:**

```text
Extracted keywords for 'intro-to-claude':
  - claude ai assistant
  - getting started
  - prompt engineering
  - conversation basics
  - claude capabilities

Added 5 keywords to index.
```

**Use cases:**

- Improve search discoverability
- Fill missing metadata
- Audit keyword quality

---

### `check-coverage` - Metadata Coverage Analysis

Analyze metadata completeness across all documents.

```bash
python manage_index.py check-coverage

# Show details for incomplete documents
python manage_index.py check-coverage --verbose
```

**Metrics reported:**

- Documents with missing titles
- Documents with missing descriptions
- Documents with no keywords
- Documents with no tags
- Documents with no category
- Documents with no aliases

**Output:**

```text
Metadata Coverage Report
========================

Total documents: 147

Title:       147/147 (100.0%)
Description: 145/147 (98.6%) - 2 missing
Keywords:    132/147 (89.8%) - 15 missing
Tags:        140/147 (95.2%) - 7 missing
Category:    147/147 (100.0%)
Aliases:     98/147 (66.7%) - 49 missing

Documents missing keywords:
  - api-advanced-features
  - troubleshooting-common-issues
  ...
```

**Use cases:**

- Identify metadata gaps
- Prioritize metadata improvements
- Quality assurance for scraped content

---

## Metadata Management

### Adding/Updating Metadata Manually

While `refresh_index.py` handles automatic metadata generation, you can manually edit `index.yaml` for corrections:

```yaml
- doc_id: custom-guide
  title: Custom Integration Guide
  description: How to integrate Claude with custom systems
  keywords:
    - custom integration
    - api integration
    - enterprise setup
  tags:
    - integration
    - enterprise
  category: advanced
  aliases:
    - "custom systems"
    - "enterprise integration"
  source_url: https://docs.claude.com/en/docs/custom-guide
  file_path: docs-claude-com/docs/custom-guide.md
  content_hash: def456...
  fetch_date: '2025-11-16'
```

**Best practices:**

- Always run `manage_index.py verify` after manual edits
- Use `extract-keywords` to generate keyword suggestions
- Keep aliases human-friendly (natural phrases users might search)
- Assign meaningful categories (consistency matters)

---

## Index Rebuilding

### When to Rebuild

Rebuild the index from filesystem when:

- Index is corrupted or missing
- Mass file reorganization occurred
- Starting fresh after major changes
- Manual edits broke index structure

### Rebuild Process

```bash
# Full rebuild from canonical storage
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical

# Rebuild with metadata generation
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical --extract-metadata

# Dry run (preview without writing)
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical --dry-run
```

**Rebuild workflow:**

1. Scans all `.md` files in base directory recursively
2. Extracts frontmatter metadata from each file
3. Generates doc_id from file path
4. Computes content hash for change detection
5. Writes new `index.yaml` with all discovered documents

**Metadata sources during rebuild:**

- Frontmatter fields (title, description, keywords, tags)
- Filename-based inference (category from folder structure)
- Content analysis (if `--extract-metadata` used)

---

## Corruption Detection

### Common Corruption Scenarios

**Duplicate doc_ids:**

- Cause: Manual edits, merge conflicts
- Detection: `verify` subcommand
- Fix: Remove duplicate entries manually

**Mismatched content hashes:**

- Cause: File modified without index update
- Detection: `verify` subcommand
- Fix: Run `refresh_index.py` to recompute hashes

**Missing file references:**

- Cause: Files deleted/moved without index update
- Detection: `verify` subcommand
- Fix: Remove stale entries or restore files

**Invalid YAML syntax:**

- Cause: Manual editing errors
- Detection: `verify` subcommand fails to load
- Fix: Use YAML linter, check for indentation errors

### Recovery Steps

1. **Backup current index:**

   ```bash
   cp .claude/skills/docs-management/canonical/index.yaml .claude/skills/docs-management/canonical/index.yaml.bak
   ```

2. **Run verification:**

   ```bash
   python manage_index.py verify > verification_report.txt
   ```

3. **Fix issues or rebuild:**

   ```bash
   # Option A: Fix specific issues manually
   # Edit index.yaml based on verification report

   # Option B: Rebuild from scratch
   python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical
   ```

4. **Verify fix:**

   ```bash
   python manage_index.py verify
   ```

---

## Coverage Analysis

### Improving Metadata Coverage

**For missing keywords:**

```bash
# Extract keywords for all documents missing them
python manage_index.py extract-keywords --missing-only --update
```

**For missing descriptions:**

- Run `refresh_index.py` which generates descriptions from content
- Manually edit frontmatter in source files
- Rebuild index to pick up changes

**For missing tags:**

- Review `config/tag_detection.yaml` patterns
- Add custom tags to frontmatter
- Run `refresh_index.py` to regenerate

**For missing aliases:**

- Think about alternative phrasings users might search
- Add to frontmatter: `aliases: ["phrase 1", "phrase 2"]`
- Run `refresh_index.py`

### Best Practices

1. **Keyword quality over quantity** - 3-7 meaningful keywords better than 20 generic ones
2. **Consistent tagging** - Establish tag vocabulary, avoid tag sprawl
3. **Category hierarchy** - Use broad categories (getting-started, api, guides, reference)
4. **Alias naturalness** - Aliases should match how users actually search
5. **Regular coverage audits** - Run `check-coverage` monthly

---

## Examples

### Workflow 1: Audit and Fix Metadata Gaps

```bash
# Step 1: Check current coverage
python manage_index.py check-coverage

# Step 2: Extract missing keywords
python manage_index.py extract-keywords --missing-only --update

# Step 3: Verify improvements
python manage_index.py check-coverage

# Step 4: Manual review of changes
git diff .claude/skills/docs-management/canonical/index.yaml
```

### Workflow 2: Debug Doc Resolution Failure

```bash
# User reports: "Can't find 'prompt engineering' docs"

# Step 1: List all docs to see what exists
python manage_index.py list | grep -i prompt

# Step 2: Check specific doc metadata
python manage_index.py get prompt-engineering-guide

# Step 3: Search by keyword
python manage_index.py filter --keyword "prompt engineering" --format json

# Step 4: If not found, check if file exists but not indexed
# Use docs-management skill to find prompt-related documentation

# Step 5: Rebuild if necessary
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical
```

### Workflow 3: Major Cleanup After Reorganization

```bash
# Files were moved/renamed outside of scripts

# Step 1: Backup index
cp .claude/skills/docs-management/canonical/index.yaml .claude/skills/docs-management/canonical/index.yaml.bak

# Step 2: Rebuild from filesystem
python manage_index.py rebuild --base-dir .claude/skills/docs-management/canonical

# Step 3: Verify new index
python manage_index.py verify

# Step 4: Check coverage
python manage_index.py check-coverage

# Step 5: Extract metadata if needed
python manage_index.py extract-keywords --all --update
```

---

**Last Updated:** 2025-11-16
**Related Guides:** discovery-guide.md
