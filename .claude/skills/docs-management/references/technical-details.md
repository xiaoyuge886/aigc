# Technical Details

## Table of Contents

- [Encapsulation Boundary](#encapsulation-boundary)
- [Dependencies](#dependencies)
- [Keyword Extraction Strategy](#keyword-extraction-strategy)
- [File Structure](#file-structure)
- [References Folder Structure](#references-folder-structure)

---

## Encapsulation Boundary

The docs-management skill maintains a clear boundary between its **public interface** (what external skills interact with) and **private implementation** (internal storage and logic).

### Public Interface (Accessible to External Skills)

**What external skills can access:**

- **SKILL.md** - Usage documentation and guidance (how to use the skill)
- **references/** - Technical guides, workflows, and best practices (how the skill works)
- **Public API** - Programmatic access via functions:
  - `find_document()` - Natural language search
  - `resolve_doc_id()` - Convert doc_id to content
  - `get_docs_by_tag()` - Tag-based filtering
  - `search_by_keywords()` - Keyword search
  - `detect_drift()` - Change detection
  - `cleanup_drift()` - Drift cleanup

**How external skills invoke the skill:**

- Natural language: "Find documentation about skills"
- Programmatic: `from official_docs_api import find_document`
- File paths: Never - external skills use API, not file paths

### Private Implementation (Internal to Skill)

**What is NOT exposed to external skills:**

- **canonical/** - Official documentation storage (internal database)
  - `docs-claude-com/` - Scraped docs from docs.claude.com
  - `code-claude-com/` - Scraped docs from code.claude.com
  - `anthropic-com/` - Scraped docs from anthropic.com
  - `index.yaml` - Metadata index (accessed via API only)

- **scripts/** - Implementation scripts (use via API commands, never accessed directly)
  - Core scripts (scraping, discovery, resolution)
  - Management scripts (index maintenance, cleanup)
  - Validation scripts (drift detection, metadata auditing)

- **Internal APIs** - Not exposed:
  - `index_manager.py` - Low-level index operations
  - `scrape_docs.py` - Scraping implementation
  - `doc_resolver.py` - Resolution logic

### Why This Boundary Matters

**Encapsulation benefits:**

1. **Implementation hiding** - Internal structure can change without breaking external skills
2. **Consistent access** - All external skills use same API regardless of internal changes
3. **Maintainability** - Updates to canonical storage don't require changes to external skills
4. **Resilience** - Doc references survive file moves/renames (via alias resolution)
5. **Clean API** - External skills never need to know file paths, structure, or implementation details

### Example: Discovery Without Knowing Implementation

**External skill:**

```python
docs = find_document("skills progressive disclosure")
# Returns results, never needs to know:
# - Where canonical/ directory is located
# - How index.yaml is structured
# - How document metadata is extracted
# - How file paths are resolved
```

**Internal (hidden from external skills):**

- Reads index.yaml
- Matches against keywords and tags
- Ranks by relevance
- Resolves file paths
- Loads content if needed

External skill only sees the result, never the implementation details.

---

## Dependencies

### For Agentic Tools (Claude Code, etc.)

**Before running scripts, check dependencies:**

```bash
python .claude/skills/docs-management/scripts/setup/check_dependencies.py
```

**To install missing dependencies:**

```bash
# Install required dependencies only
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required

# Install all dependencies (required + optional)
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-all
```

**Quick setup (recommended for agents):**

```bash
# Check and install required dependencies
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required
```

### Required Dependencies

Core dependencies (must be installed):

- `pyyaml` - YAML parsing
- `requests` - HTTP requests for scraping
- `beautifulsoup4` - HTML parsing
- `markdownify` - HTML to Markdown conversion

**Install manually:**

```bash
pip install pyyaml requests beautifulsoup4 markdownify
```

**Or from requirements file:**

```bash
pip install -r .claude/skills/docs-management/requirements.txt
```

### Optional NLP Libraries (Recommended)

For enhanced keyword extraction and stop word filtering:

- `spacy` - Stop word lists and NLP
- `yake` - Automatic keyword extraction

**Install manually:**

```bash
pip install spacy yake
python -m spacy download en_core_web_sm
```

**Benefits:**

- **spaCy**: Provides comprehensive stop word lists (replaces hardcoded 200+ stop words)
- **YAKE**: Automatic keyword extraction using unsupervised learning (no training required)

**Fallback behavior:** If optional libraries are not installed, the script uses:

- Basic English stop words (fallback for spaCy)
- Heading/content-based keyword extraction (fallback for YAKE)

### Configuration Files

The skill uses YAML configuration files for tag/category detection and filtering:

- `.claude/skills/docs-management/config/tag_detection.yaml` - Tag and category detection rules
- `.claude/skills/docs-management/config/filtering.yaml` - Domain-specific filtering terms

**Update these files to add new tags/categories or modify detection rules without code changes.**

### Dependency Management Scripts

**`check_dependencies.py`** - Check which dependencies are installed:

```bash
python .claude/skills/docs-management/scripts/setup/check_dependencies.py
python .claude/skills/docs-management/scripts/setup/check_dependencies.py --install-optional  # Show install commands
```

**`setup_dependencies.py`** - Check and install dependencies:

```bash
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py                    # Check only
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required # Install required
python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-all       # Install all
```

**For agents:** Run `setup_dependencies.py --install-required` before using metadata extraction scripts.

## Keyword Extraction Strategy

The metadata extraction system (`extract_metadata.py`) uses a 7-source extraction pipeline to generate high-quality keywords for search and discovery.

### Extraction Pipeline (Prioritized by Reliability)

Keywords are extracted from 7 sources in decreasing order of trust/reliability:

1. **Technical Phrases** (Highest Trust)
   - Multi-word technical terms from `config/filtering.yaml`
   - Examples: "context window", "agent skills", "prompt caching"
   - **Why first**: Domain-specific, manually curated, high precision
   - **No filtering applied** - preserved as-is

2. **Frontmatter Keywords/Tags** (Author-Provided)
   - Explicitly defined in YAML frontmatter by document authors
   - Fields: `keywords:` and `tags:`
   - **Why second**: Human-provided signal, author knows document best
   - **No filtering applied** - trusted source

3. **Title & Description** (High Signal-to-Noise)
   - Meaningful words from document title (3+ chars)
   - Technical terms from first paragraph (5+ chars)
   - **Why third**: Title/intro represent core content, structurally important
   - **Filtered**: Stop words removed, ranked by length

4. **YAKE Automatic Extraction** (ML-Based, Optional)
   - Unsupervised keyword extraction using YAKE library
   - Extracts 1-3 word n-grams ranked by statistical relevance
   - **Only runs if**: `yake` installed and text >= 50 chars
   - **Why fourth**: Automatic, good for technical content, but can generate noise
   - **Configurable**: `defaults.yaml` → `keyword_extraction.yake`

5. **Heading Keywords** (Structural Importance)
   - Multi-word phrases from h1-h6 headings (max 10)
   - Single words from headings (max 8)
   - File tokens like "claude.md" from headings (max 4)
   - **Why fifth**: Headings indicate structure/topics, but can be generic
   - **Filtered**: Generic verbs, incomplete phrases removed

6. **Filename** (Semantic Meaning)
   - Meaningful parts extracted from filename
   - Example: `agent-skills-guide.md` → ["agent", "skills", "guide"]
   - **Why sixth**: Filename hints at content, but often generic
   - **Filtered**: Common doc terms (md, doc, guide, api) removed

7. **Body Content** (Last Resort, Frequency-Based)
   - Technical terms appearing 2+ times (5+ chars)
   - Only used if insufficient keywords from other sources
   - Limited to top 6 terms by frequency and length
   - **Why last**: Noisy, can extract common but non-distinctive terms
   - **Heavily filtered**: Generic words, weak terms removed

### Filtering & Cleaning Process

After extraction, keywords go through multi-stage filtering:

1. **Stop Phrase Removal** - Filter noise patterns (`config/filtering.yaml` → `stop_phrases`)
2. **Length Checks** - Min 3 chars general, min 6 chars for single words
3. **Generic Term Removal** - Filter generic verbs, incomplete endings, weak words
4. **Phrase Quality Checks**:
   - Skip if starts/ends with generic words
   - Skip 2-word phrases ending with weak adverbs (automatically, manually, etc.)
   - Skip if ALL words are generic
5. **Domain Exclusions** - Filter domain-specific common terms (e.g., "skills" in Claude docs)
6. **Deduplication** - Remove single words that appear in phrases

### Output

Returns up to **12 keywords** (configurable in `defaults.yaml`):

- Multi-word phrases prioritized over single words
- Longer keywords prioritized (more specific)
- Alphabetically sorted within priority groups

### Configuration

All extraction limits and parameters are configurable:

**File**: `config/defaults.yaml` → `keyword_extraction` section

```yaml
keyword_extraction:
  limits:
    max_file_tokens: 4         # File references like "claude.md"
    max_heading_phrases: 10     # Multi-word terms from headings
    max_heading_keywords: 8     # Single words from headings
    max_body_keywords: 6        # Frequency-based from body
    max_total_keywords: 12      # Final output limit
  
  yake:
    language: 'en'
    max_ngram_size: 3           # 1=unigrams, 2=bigrams, 3=trigrams
    dedup_threshold: 0.7        # Remove near-duplicates
    top_keywords: 15            # Extract before filtering
    min_text_length: 50         # Minimum chars for YAKE
```

**File**: `config/filtering.yaml` → Multiple sections

- `technical_phrases`: Multi-word terms to preserve
- `stop_phrases`: Noise patterns to reject
- `generic_verbs`, `incomplete_endings`: Phrase filtering
- `generic_single_words`, `generic_words`: Single-word filtering
- `weak_phrase_words`: Weak terms in phrases
- `weak_two_word_adverbs`: Adverbs for 2-word phrases
- `single_word_exclusions`: Domain-specific exclusions

### Rationale: Why This Approach?

**Balanced Recall & Precision**: 7 sources ensure comprehensive coverage (recall) while filtering reduces noise (precision).

**Trust-Based Prioritization**: Sources are ordered by reliability - human-curated (technical phrases, frontmatter) before automatic (YAKE, frequency) before fallback (body content).

**Config-Driven Behavior**: All limits and rules in config files enable tuning without code changes. Supports experimentation and domain adaptation.

**Graceful Degradation**: System works without optional dependencies (YAKE, spaCy) by falling back to simpler extraction methods.

**Multi-Word Emphasis**: Phrases like "context window" are more distinctive than "context" or "window" alone. Pipeline prioritizes multi-word terms throughout.

## File Structure

```text
.claude/skills/docs-management/
├── SKILL.md                    # This file
├── scripts/
│   ├── scrape_docs.py          # Scraping automation
│   └── extract_subsection.py   # Subsection extraction (internal use)
├── references/
│   └── (future: scraping guide, extraction guide)
└── assets/
    └── (future: templates, examples)
```

## References Folder Structure

Documentation is stored in canonical storage (location managed by skill) using domain-based organization:

```text
canonical/
├── index.yaml                           # Document and extract registry
├── docs-claude-com/                     # Domain: docs.claude.com
│   ├── docs/                            # Category: /en/docs/
│   │   ├── about-claude/
│   │   │   ├── glossary.md
│   │   │   └── pricing.md
│   │   ├── build-with-claude/
│   │   │   └── prompt-engineering/
│   │   └── ...
│   ├── api/                             # Category: /en/api/
│   │   ├── messages.md
│   │   ├── models.md
│   │   └── ...
│   ├── resources/                       # Category: /en/resources/
│   │   └── prompt-library/
│   │       ├── meeting-scribe.md
│   │       └── ...
│   └── release-notes/                   # Category: /en/release-notes/
│       ├── overview.md
│       └── system-prompts.md
└── code-claude-com/                     # Domain: code.claude.com
    └── docs/en/                         # Category: /docs/en/
        ├── overview.md
        ├── quickstart.md
        └── ...

URL Mapping Examples:
  https://docs.claude.com/en/docs/about-claude/glossary
  → docs-claude-com/docs/about-claude/glossary.md

  https://code.claude.com/docs/en/overview
  → code-claude-com/docs/en/overview.md

  https://docs.claude.com/en/api/messages
  → docs-claude-com/api/messages.md
```

**Key conventions:**

- **Domain normalization**: Dots → hyphens (e.g., `docs.claude.com` → `docs-claude-com`)
- **Language code stripping**: `/en/` removed from paths (English-only repository)
- **Path preservation**: Category and document structure preserved
- **No collisions**: Each domain gets its own top-level folder

**Content Exclusions (do NOT scrape):**

- ❌ **Blog posts** - Anthropic engineering blog content (editorial, not reference documentation)
- ❌ **Research papers** - Academic research publications (frequently updated, not operational docs)
- ❌ **News articles** - Press releases and announcements (time-sensitive, not evergreen)
- ❌ **Non-English content** - Any language other than English (repository policy)

**What TO scrape:**

- ✅ **Product documentation** - Operational guides, how-tos, reference materials
- ✅ **API reference** - Endpoint documentation, SDK references
- ✅ **Resources** - Prompt libraries, examples, templates
- ✅ **Release notes** - Version-specific changes and updates
- ✅ **Tool documentation** - Claude Code and related tools

**Cleanup before re-scraping:**

When re-scraping to fix structure issues:

1. **Identify unwanted content** by checking folder names:
   - Blog/news/research folders (content type exclusions)
   - Arbitrary folder names not matching domains (old structure)
   - Duplicate path segments (e.g., `category/category/` patterns)

2. **Remove old content** that will be replaced:

   ```bash
   # Remove folders matching the patterns identified above
   # Be explicit about what you're removing
   ```

3. **Remove index** so it regenerates cleanly:

   ```bash
   rm index.yaml
   ```

4. **Re-scrape** using Documentation Discovery Workflow to ensure completeness

## Troubleshooting Dependency Issues

### ImportError: No module named 'yaml'

**Symptom:** Scripts fail with missing module errors

**Solutions:**

1. **Install required dependencies**

   ```bash
   pip install pyyaml requests beautifulsoup4 markdownify
   ```

2. **Use setup script**

   ```bash
   python .claude/skills/docs-management/scripts/setup/setup_dependencies.py --install-required
   ```

3. **Check Python environment** - Ensure using correct Python/virtualenv

   ```bash
   which python
   python --version
   ```

### spaCy Model Download Fails

**Symptom:** `python -m spacy download en_core_web_sm` fails

**Solutions:**

1. **Install spaCy first**

   ```bash
   pip install spacy
   python -m spacy download en_core_web_sm
   ```

2. **Use direct download** - If download command fails

   ```bash
   pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.7.0/en_core_web_sm-3.7.0.tar.gz
   ```

3. **Skip optional dependencies** - spaCy is optional, fallback exists
   - Scripts work without spaCy (uses basic stop words)

### YAML Parsing Errors

**Symptom:** `yaml.scanner.ScannerError` when reading config files

**Causes:**

1. **Malformed YAML** - Syntax error in config file
2. **Encoding issues** - Non-UTF-8 characters
3. **Indentation errors** - Incorrect spacing

**Solutions:**

1. **Validate YAML syntax** - Use online validator or yamllint

   ```bash
   pip install yamllint
   yamllint .claude/skills/docs-management/config/
   ```

2. **Check file encoding** - Ensure UTF-8

   ```bash
   file -i .claude/skills/docs-management/config/tag_detection.yaml
   ```

3. **Fix indentation** - Use spaces, not tabs (2-space indent)

### Script Finds Wrong Python Packages

**Symptom:** Dependencies reported as installed but imports fail

**Causes:**

1. **Multiple Python installations** - Using different Python than pip
2. **Virtual environment mismatch** - Installed in different venv
3. **PATH issues** - Wrong Python/pip in PATH

**Solutions:**

1. **Use Python module pip** - Ensures correct Python

   ```bash
   python -m pip install pyyaml
   ```

2. **Activate correct venv** - If using virtual environments

   ```bash
   which python
   which pip
   # Should both point to same environment
   ```

3. **Reinstall in current environment**

   ```bash
   python -m pip install --force-reinstall pyyaml
   ```

### Permission Denied Creating Directories

**Symptom:** Cannot create `canonical/` directories

**Solutions:**

1. **Check write permissions**

   ```bash
   ls -la .claude/
   ```

2. **Fix permissions**

   ```bash
   chmod -R u+w canonical/
   ```

3. **Run from repository root** - Ensure correct working directory

   ```bash
   cd /path/to/onboarding
   pwd  # Should show repository root
   ```

### Configuration Files Not Found

**Symptom:** `FileNotFoundError` for config YAML files

**Solutions:**

1. **Verify files exist**

   ```bash
   ls .claude/skills/docs-management/config/
   ```

2. **Run from correct directory** - Must be repository root

   ```bash
   pwd
   # Should be: /path/to/onboarding
   ```

3. **Check paths in scripts** - Ensure relative paths correct

## Related Guides

- **[Best Practices](best-practices.md)** - Workflow guidance
- **[Scraping Guide](capabilities/scraping-guide.md)** - Scraping documentation
- **[Extraction Guide](capabilities/extraction-guide.md)** - Extraction workflows
- **[spaCy Installation Guide](spacy-installation.md)** - Detailed spaCy setup
