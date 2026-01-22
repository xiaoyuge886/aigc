# Configuration Guide

## Purpose

Configure the docs-management skill for scraping, filtering, and metadata detection.

## Configuration Files

The skill uses three primary configuration files:

| File | Purpose | Location |
| --- | --- | --- |
| `tag_detection.yaml` | Tag and category detection rules | `.claude/skills/docs-management/config/` |
| `filtering.yaml` | Keyword filtering for noise reduction | `.claude/skills/docs-management/config/` |
| `references/sources.json` | Scraping source definitions | Passed to `scrape_all_sources.py` (default location) |

## Table of Contents

- [Purpose](#purpose)
- [Configuration Files](#configuration-files)
- [tag_detection.yaml](#tag_detectionyaml)
- [filtering.yaml](#filteringyaml)
- [sources.json](#sourcesjson)
- [Adding New Domains](#adding-new-domains)
- [Custom Extraction Patterns](#custom-extraction-patterns)
- [Validation](#validation)
- [Examples](#examples)

---

## tag_detection.yaml

### Purpose - Tag Detection

Defines how tags and categories are automatically detected from document content during metadata generation.

**Location:** `.claude/skills/docs-management/config/tag_detection.yaml`

### Structure

```yaml
tags:
  tag-name:
    terms: ['keyword1', 'keyword2', 'phrase with spaces']
    min_mentions: 2
    additional_terms: ['optional-term']  # Optional
    additional_min_mentions: 3           # Optional
```

**Fields:**

- `tag-name` - The tag to apply (e.g., `api`, `troubleshooting`)
- `terms` - List of keywords/phrases that trigger this tag
- `min_mentions` - Minimum occurrences required to apply tag
- `additional_terms` - Optional secondary terms (less strict matching)
- `additional_min_mentions` - Threshold for additional terms

### Detection Logic

1. **Content scanning:** Script scans document for term occurrences
2. **Case-insensitive matching:** Terms matched regardless of case
3. **Threshold checking:** If `min_mentions` reached, tag is applied
4. **Multiple tags:** Document can receive multiple tags
5. **Fallback tag:** If no tags detected, `reference` tag applied automatically

### Example Configuration

```yaml
tags:
  api:
    terms: ['authentication', 'authorization', 'oauth', 'api key', 'token', 'endpoint', 'rest api']
    min_mentions: 2

  troubleshooting:
    terms: ['troubleshoot', 'troubleshooting', 'fix error', 'error handling', 'debug', 'debugging']
    min_mentions: 1
    additional_terms: ['issue', 'problem']
    additional_min_mentions: 3

  security:
    terms: ['security', 'secure', 'permission', 'permissions', 'access control', 'authentication', 'authorization']
    min_mentions: 2
```

### Adding New Tags

1. **Identify the concept:**
   - What topic does this tag represent?
   - Example: `vision` for image analysis features

2. **Define trigger terms:**
   - List keywords/phrases that indicate this topic
   - Include variations and synonyms
   - Example: `['vision', 'image analysis', 'computer vision', 'visual input']`

3. **Set threshold:**
   - How many mentions constitute signal vs noise?
   - Common tags: `min_mentions: 2`
   - Rare tags: `min_mentions: 1`

4. **Add to configuration:**

   ```yaml
   tags:
     vision:
       terms: ['vision', 'image analysis', 'computer vision', 'visual input', 'image upload']
       min_mentions: 2
   ```

5. **Test and refine:**

   ```bash
   # Regenerate metadata with new tag
   python refresh_index.py

   # Check which docs received the tag
   python manage_index.py filter --tag vision
   ```

### Best Practices

**Term selection:**

- ✅ Use specific technical terms (`"oauth"`, `"rate limiting"`)
- ✅ Include common variations (`"debug"`, `"debugging"`)
- ✅ Add multi-word phrases (`"prompt engineering"`, `"api key"`)
- ❌ Avoid generic words (`"use"`, `"get"`, `"guide"`)
- ❌ Don't overlap with filtering.yaml terms

**Threshold tuning:**

- Start with `min_mentions: 2` (balanced)
- Increase if tag is over-applied (too noisy)
- Decrease for rare but important topics
- Monitor tag distribution via `manage_index.py check-coverage`

**Maintenance:**

- Review tag assignments periodically
- Consolidate overlapping tags
- Remove unused tags
- Keep tag count manageable (10-20 tags ideal)

---

## filtering.yaml

### Purpose - Keyword Filtering

Filters out low-signal keywords during metadata extraction to reduce noise and improve keyword quality.

**Location:** `.claude/skills/docs-management/config/filtering.yaml`

**Version:** 1.1 (Deduplicated 2025-11-16)

### Structure - Filtering Categories

```yaml
# Domain-specific stop words (brand names, product names)
domain_stop_words:
  - 'claude'
  - 'anthropic'

# Generic verbs that often start incomplete phrases
generic_verbs:
  - 'start'
  - 'use'
  - 'make'

# Incomplete phrase endings (words that make phrases incomplete)
incomplete_endings:
  - 'your'
  - 'the'
  - 'a'

# Generic single words to exclude (even if 5+ chars)
generic_single_words:
  - 'terminal'
  - 'faster'
```

### Categories Explained

**domain_stop_words:**

- Brand names that appear in every document
- Product names that don't help discoverability
- Example: `"claude"` appears everywhere, not useful as keyword

**generic_verbs:**

- Action words that don't convey specific meaning
- Often start incomplete phrases (`"use the"`, `"get started"`)
- Example: `"use"` is too vague to be a useful keyword

**incomplete_endings:**

- Words that make phrases incomplete if they're the last word
- Example: `"getting your"` ends incomplete, should be filtered

**generic_single_words:**

- Single words (even if 5+ characters) that are too generic
- Example: `"faster"` doesn't indicate topic

### Validation - Filtering File

**Check for duplicates:**

```bash
python scripts/validation/validate_filtering.py
```

**Expected output (if valid):**

```text
======================================================================
filtering.yaml Validation Report
======================================================================

Category Statistics:
----------------------------------------------------------------------
  domain_stop_words                 2 terms
  generic_single_words             64 terms
  generic_verbs                    15 terms
  generic_words                    56 terms
  incomplete_endings               13 terms
----------------------------------------------------------------------
  TOTAL                           150 terms

VALIDATION PASSED: No duplicates found
======================================================================
```

### Adding New Filters

1. **Identify noise patterns:**
   - Review extracted keywords via `manage_index.py get <doc_id>`
   - Note low-signal terms that appear frequently
   - Example: `"guide"` appears in many docs but doesn't indicate topic

2. **Classify the term:**
   - Is it a brand name? → `domain_stop_words`
   - Is it a generic verb? → `generic_verbs`
   - Does it create incomplete phrases? → `incomplete_endings`
   - Is it a vague single word? → `generic_single_words`

3. **Add to appropriate category:**

   ```yaml
   generic_single_words:
     - 'terminal'
     - 'faster'
     - 'guide'  # NEW ADDITION
   ```

4. **Validate no duplicates:**

   ```bash
   python scripts/validation/validate_filtering.py
   ```

5. **Regenerate keywords:**

   ```bash
   python refresh_index.py
   ```

### Best Practices - Filtering

**What to filter:**

- ✅ Brand names (`"claude"`, `"anthropic"`)
- ✅ Generic verbs (`"use"`, `"get"`, `"make"`)
- ✅ Articles and determiners (`"the"`, `"a"`, `"an"`)
- ✅ Vague single words (`"faster"`, `"better"`, `"guide"`)

**What NOT to filter:**

- ❌ Technical terms (`"api"`, `"authentication"`)
- ❌ Feature names (`"vision"`, `"streaming"`)
- ❌ Specific concepts (`"prompt engineering"`, `"rate limiting"`)

**Maintenance:**

- Run `validate_filtering.py` after every edit
- Review keyword quality quarterly
- Add terms based on observed noise in metadata
- Keep categories organized (don't mix concepts)

---

## sources.json

### Purpose - Source Definitions

Defines scraping sources for `scrape_all_sources.py` orchestration script.

**Location:** Default: `references/sources.json` (relative to script directory). Can be overridden via `--config` flag.

### Structure - Sources Schema

```json
{
  "sources": [
    {
      "name": "Claude Documentation",
      "type": "sitemap",
      "url": "https://docs.claude.com/sitemap.xml",
      "filter": "/en/docs/",
      "expected_count": 50,
      "skip_existing": true
    },
    {
      "name": "Anthropic Engineering Blog",
      "type": "sitemap",
      "url": "https://anthropic.com/sitemap.xml",
      "filter": "/engineering/",
      "max_age_days": 180,
      "expected_count": 20
    },
    {
      "name": "Claude Code Documentation",
      "type": "docs-map",
      "url": "https://code.claude.com/docs/en/claude_code_docs_map.md",
      "expected_count": 15,
      "skip_existing": true
    }
  ]
}
```

### Field Reference

**Required fields:**

- `name` - Human-readable source name (for progress tracking)
- `type` - Source type: `"sitemap"` or `"docs-map"`
- `url` - URL to sitemap.xml or docs map markdown file

**Optional fields:**

- `filter` - Regex pattern to filter URLs (sitemap only)
  - Example: `"/en/docs/"` matches only `/en/docs/*` paths
- `max_age_days` - Maximum age in days for sitemap entries (filters by `<lastmod>`)
  - Example: `180` excludes URLs older than 6 months
  - Used for news/blog content to maintain recency
- `expected_count` - Expected number of documents (for validation)
  - Warns if actual count deviates significantly
- `skip_existing` - Skip documents that already exist (default: false)
  - `true` = Only scrape new/changed docs
  - `false` = Re-scrape all docs
- `resume` - Resume from previous interrupted run (default: false)

### Source Types

**sitemap:**

```json
{
  "name": "API Reference",
  "type": "sitemap",
  "url": "https://docs.claude.com/sitemap.xml",
  "filter": "/en/api/",
  "expected_count": 25
}
```

**docs-map:**

```json
{
  "name": "Claude Code Docs",
  "type": "docs-map",
  "url": "https://code.claude.com/docs/en/claude_code_docs_map.md",
  "expected_count": 15
}
```

### Recency Filtering (max_age_days)

For time-sensitive content (news, blog posts, research), use `max_age_days` to maintain freshness:

```json
{
  "name": "Anthropic Engineering Blog",
  "type": "sitemap",
  "url": "https://anthropic.com/sitemap.xml",
  "filter": "/engineering/",
  "max_age_days": 180,
  "expected_count": 20
}
```

**How it works:**

1. `scrape_all_sources.py` passes `max_age_days` to `scrape_docs.py` via `--max-age`
2. `scrape_docs.py` checks sitemap `<lastmod>` dates
3. URLs with `<lastmod>` older than threshold are excluded
4. Only recent content is scraped and indexed

**Recommended values:**

- Engineering/news blogs: `180` days (6 months)
- Research papers: `365` days (1 year)
- Documentation: Omit (no age filtering)

### Usage

```bash
# Scrape all sources defined in references/sources.json (uses default)
python scrape_all_sources.py --parallel --auto-validate

# Or specify custom config path
python scrape_all_sources.py --config sources.json --parallel --auto-validate

# Skip existing documents (incremental update)
python scrape_all_sources.py --config sources.json --skip-existing
```

---

## Adding New Domains

### Step 1: Identify Source Information

**For sitemap-based sources:**

- Find sitemap URL (usually `https://domain.com/sitemap.xml`)
- Determine filter pattern (URL path to scrape)
- Estimate document count

**For docs-map sources:**

- Find docs map markdown URL
- Verify format (should list URLs)

### Step 2: Add to references/sources.json

```json
{
  "sources": [
    {
      "name": "New Documentation Source",
      "type": "sitemap",
      "url": "https://newdomain.com/sitemap.xml",
      "filter": "/docs/",
      "expected_count": 30,
      "skip_existing": true
    }
  ]
}
```

### Step 3: Test Scrape

```bash
# Test with --limit to scrape first 5 docs only
python scrape_docs.py \
  --sitemap https://newdomain.com/sitemap.xml \
  --filter "/docs/" \
  --limit 5
```

### Step 4: Full Scrape

```bash
# Run full scrape via sources.json
python scrape_all_sources.py --config sources.json
```

### Step 5: Validate Results

```bash
# Verify document count matches expected
python manage_index.py count

# Check metadata quality
python manage_index.py check-coverage

# Validate index integrity
python manage_index.py verify
```

---

## Custom Extraction Patterns

### Customizing Keyword Extraction

The `refresh_index.py` script uses keyword extraction from content. To customize:

1. **Review current keywords:**

   ```bash
   python manage_index.py get <doc_id>
   ```

2. **Adjust filtering.yaml** to reduce noise

3. **Regenerate keywords:**

   ```bash
   python refresh_index.py
   ```

4. **Manually curate high-value docs:**
   - Edit frontmatter in `.md` files directly
   - Add/remove keywords as needed
   - Run `refresh_index.py` to sync to index

### Customizing Tag Detection

See [tag_detection.yaml](#tag_detectionyaml) section above.

### Customizing Category Assignment

Categories can be assigned:

- **Automatically:** Based on folder structure or tag patterns
- **Manually:** Edit frontmatter `category` field
- **Via configuration:** Add category detection rules to `tag_detection.yaml`

---

## Validation

### Validate Configuration Files Syntax

**Check tag_detection.yaml syntax:**

```bash
python -c "import yaml; yaml.safe_load(open('.claude/skills/docs-management/config/tag_detection.yaml'))"
```

**Check filtering.yaml for duplicates:**

```bash
python scripts/validation/validate_filtering.py
```

**Check sources.json syntax:**

```bash
python -c "import json; json.load(open('sources.json'))"
```

### Validate After Changes

After modifying any configuration:

1. **Syntax validation** (see above)
2. **Regenerate metadata:**

   ```bash
   python refresh_index.py
   ```

3. **Verify index integrity:**

   ```bash
   python manage_index.py verify
   ```

4. **Check coverage:**

   ```bash
   python manage_index.py check-coverage
   ```

5. **Spot-check results:**

   ```bash
   python manage_index.py get <doc_id>
   ```

---

## Examples

### Example 1: Add New Tag for "Prompt Engineering"

**1. Edit tag_detection.yaml:**

```yaml
tags:
  prompt-engineering:
    terms: ['prompt engineering', 'prompt design', 'prompt optimization', 'system prompt', 'few-shot']
    min_mentions: 2
```

**2. Validate syntax:**

```bash
python -c "import yaml; yaml.safe_load(open('.claude/skills/docs-management/config/tag_detection.yaml'))"
```

**3. Regenerate metadata:**

```bash
python refresh_index.py
```

**4. Check which docs received new tag:**

```bash
python manage_index.py filter --tag prompt-engineering
```

---

### Example 2: Filter Out Noisy Keywords

**1. Identify noise:**

```bash
# Review keywords for several docs
python manage_index.py get intro-to-claude
python manage_index.py get api-quickstart

# Notice "guide" appears frequently but adds no value
```

**2. Add to filtering.yaml:**

```yaml
generic_single_words:
  - 'guide'
  - 'tutorial'  # Also generic
```

**3. Validate no duplicates:**

```bash
python scripts/validation/validate_filtering.py
```

**4. Regenerate keywords:**

```bash
python refresh_index.py
```

**5. Verify improvement:**

```bash
# Keywords should be more specific now
python manage_index.py get intro-to-claude
```

---

### Example 3: Add Anthropic Research Blog with Recency Filter

**1. Create sources.json:**

```json
{
  "sources": [
    {
      "name": "Anthropic Research Blog",
      "type": "sitemap",
      "url": "https://anthropic.com/sitemap.xml",
      "filter": "/research/",
      "max_age_days": 365,
      "expected_count": 15,
      "skip_existing": true
    }
  ]
}
```

**2. Test scrape:**

```bash
# Scrape first 3 docs to test
python scrape_docs.py \
  --sitemap https://anthropic.com/sitemap.xml \
  --filter "/research/" \
  --max-age 365 \
  --limit 3
```

**3. Full scrape:**

```bash
python scrape_all_sources.py --config sources.json --parallel
```

**4. Validate:**

```bash
python manage_index.py verify
python manage_index.py count
```

---

### Example 4: Complete Configuration Workflow

**Scenario:** Setting up docs-management skill from scratch

**1. Configure filtering:**

```bash
# Use existing filtering.yaml or customize
python scripts/validation/validate_filtering.py
```

**2. Configure tag detection:**

```bash
# Edit tag_detection.yaml to match your domain
# Add tags relevant to your documentation
vim .claude/skills/docs-management/config/tag_detection.yaml
```

**3. Create sources.json:**

```json
{
  "sources": [
    {
      "name": "Claude Docs",
      "type": "sitemap",
      "url": "https://docs.claude.com/sitemap.xml",
      "filter": "/en/docs/",
      "expected_count": 50,
      "skip_existing": true
    },
    {
      "name": "Claude Code Docs",
      "type": "docs-map",
      "url": "https://code.claude.com/docs/en/claude_code_docs_map.md",
      "expected_count": 15,
      "skip_existing": true
    }
  ]
}
```

**4. Initial scrape:**

```bash
python scrape_all_sources.py --config sources.json --parallel --auto-validate
```

**5. Generate metadata:**

```bash
python refresh_index.py
```

**6. Validate setup:**

```bash
python manage_index.py verify
python manage_index.py check-coverage
```

**7. Test discovery:**

```bash
python find_docs.py --keyword "api"
python resolve_doc.py intro-to-claude
```

---

**Last Updated:** 2025-11-16
**Related Guides:** scraping-guide.md, index-management-guide.md, discovery-guide.md
