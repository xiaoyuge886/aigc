# Extracting Subsections

## Table of Contents

- [Purpose](#purpose)
- [Capabilities](#capabilities)
- [Usage Patterns](#usage-patterns)
- [Examples](#examples)
- [Token Economics](#token-economics)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [Related Guides](#related-guides)

---

## Purpose

Extract specific markdown sections for token-optimized operations. This functionality is used internally by the docs-management skill for on-demand subsection extraction.

**Script:** `scripts/management/extract_subsection.py`

**Note:** This is an internal capability used by `doc_resolver.py` and `get_subsection_content.py`. External skills should use the skill's documentation discovery and resolution functions rather than calling extraction scripts directly.

**Key benefits:**

- 60-90% token savings compared to loading full documents
- Maintain provenance with source tracking frontmatter
- Enable progressive disclosure pattern (just-in-time context loading)
- Automatic drift detection via content hashing

## Capabilities

- **Heading structure parsing** - Identify ATX-style headings (`## Heading`)
- **Section extraction** - Target heading + all child subsections
- **Provenance frontmatter** - Track source doc, section, URL, hash
- **Automatic boundaries** - Extract until next same-level heading
- **Error handling** - Clear messages if section not found
- **Multi-level support** - Extract any heading level (h1-h6)
- **Hash generation** - Content hash for drift detection

## Usage Patterns

### Basic Extraction

```bash
# Extract single section for a skill reference
python extract_subsection.py \
    --source <path-to-source-doc> \
    --section "Skills vs slash commands" \
    --output .claude/skills/my-skill/references/slash-commands-skills-section.md
```

### With Source URL

```bash
# Include source URL for linking back to canonical docs
python extract_subsection.py \
    --source <path-to-source-doc> \claude-code/plugins.md \
    --section "Skills plugin" \
    --output .claude/skills/my-skill/references/plugins-skills-section.md \
    --url https://code.claude.com/docs/en/plugins#skills-plugin
```

### Batch Extraction

```bash
# Extract multiple sections from same source
for section in "Overview" "Configuration" "Examples"; do
    python extract_subsection.py \
        --source <path-to-source-doc> \docs-claude-com/docs/api-reference.md \
        --section "$section" \
        --output .claude/skills/my-skill/references/api-${section,,}.md
done
```

## Examples

### Example 1: Multi-Section Extraction for Comprehensive Topic

When creating a skill that needs multiple related sections:

```bash
# Extract all sections about prompt engineering
python extract_subsection.py \
    --source <path-to-source-doc> \docs-claude-com/docs/prompt-engineering.md \
    --section "Best Practices" \
    --output .claude/skills/prompt-helper/references/best-practices.md

python extract_subsection.py \
    --source <path-to-source-doc> \docs-claude-com/docs/prompt-engineering.md \
    --section "Examples" \
    --output .claude/skills/prompt-helper/references/examples.md

python extract_subsection.py \
    --source <path-to-source-doc> \docs-claude-com/docs/prompt-engineering.md \
    --section "Common Pitfalls" \
    --output .claude/skills/prompt-helper/references/pitfalls.md
```

**Why multiple extracts?**

- Load only relevant sections based on user query
- Further token optimization beyond single large extract
- Progressive disclosure: add sections as needed

### Example 2: Nested Section Extraction

Extract a specific subsection from a large document:

```bash
# Extract "Memory Tool" section from Claude Code memory documentation
python extract_subsection.py \
    --source <path-to-source-doc> \code-claude-com/docs/en/memory.md \
    --section "Memory Tool" \
    --output .claude/skills/claude-memory/references/memory-tool.md \
    --url https://code.claude.com/docs/en/memory#memory-tool
```

**Result:** Only the "Memory Tool" section and its child subsections, not the entire memory guide.

## Token Economics

### Single Document Example

| Metric | Full Document | Extract | Savings |
| --- | --- | --- | --- |
| **Source:** slash-commands.md | 15,000 chars | 2,000 chars | 13,000 (87%) |
| **Est. tokens** | ~3,750 | ~500 | ~3,250 (87%) |

### Multi-Document Skill Example

| Component | Without Extraction | With Extraction | Savings |
| --- | --- | --- | --- |
| 3 full docs (45K chars) | ~11,250 tokens | ~1,800 tokens | ~9,450 (84%) |
| Context per invocation | 11,250 tokens | 1,800 tokens | 84% reduction |

**Result:** More context budget for actual task execution

### When Extraction Pays Off

- ✅ **Extract when source > 2,500 tokens** - Significant savings justify overhead
- ✅ **Extract when using < 30% of document** - Most skills need narrow focus
- ✅ **Extract for frequently-invoked skills** - Token savings compound over time
- ❌ **Don't extract tiny sections (< 500 tokens)** - Overhead (frontmatter) exceeds benefit

## Best Practices

### Section Naming

- ✅ **Use exact heading text** - Case-insensitive but must match
- ✅ **Include quotes for multi-word sections** - `--section "Best Practices"`
- ✅ **Check available headings first** - Script lists all headings if section not found
- ❌ **Don't assume heading names** - Verify in source document

### Output Organization

- ✅ **Group extracts in skill references/** - Keep extracts with skills that use them
- ✅ **Use descriptive filenames** - `api-authentication.md` not `extract1.md`
- ✅ **Mirror source structure when helpful** - `capabilities/extraction-guide.md`
- ❌ **Don't scatter extracts randomly** - Centralize per skill

### Source URL Usage

- ✅ **Always provide --url when available** - Enables linking to official docs
- ✅ **Use anchor links for sections** - `https://example.com/docs#section-name`
- ✅ **Keep URLs up to date** - Check for accuracy periodically
- ❌ **Don't use relative URLs** - Use absolute canonical URLs

### After Extraction

- ✅ **Review generated frontmatter** - Ensure metadata is correct
- ✅ **Test in skill context** - Verify extract has sufficient context
- ✅ **Verify section boundaries** - Ensure content is complete
- ❌ **Don't assume extraction is perfect** - Always review output

## Troubleshooting

### Section Not Found

**Symptom:** Error message "Section 'X' not found in source document"

**Solutions:**

1. **Review available headings** - Script lists all headings in source
2. **Check exact heading text** - Must match exactly (case-insensitive)
3. **Verify heading level** - Script extracts based on ATX heading level
4. **Check for special characters** - Some characters may need escaping

**Example:**

```bash
# If section "API Reference" not found, check available headings:
python extract_subsection.py \
    --source <path-to-source-doc> \docs-claude-com/docs/api.md \
    --section "Nonexistent Section"

# Script output shows:
# Available headings:
# - Overview
# - Authentication
# - API Reference (v2)  ← Note: includes "(v2)"
# - Examples

# Use exact heading:
python extract_subsection.py \
    --source <path-to-source-doc> \docs-claude-com/docs/api.md \
    --section "API Reference (v2)" \
    --output ...
```

### Empty or Incomplete Extraction

**Symptom:** Extracted file is very short or missing expected content

**Causes:**

1. **Wrong heading level** - Extracted only one level, not child sections
2. **Boundary detection issue** - Next same-level heading immediately follows
3. **Source formatting issues** - Markdown structure not as expected

**Solutions:**

1. **Inspect source document** - Verify heading structure
2. **Extract parent section** - Go up one level to get more context
3. **Manual review** - Check if automated extraction is appropriate

### Frontmatter Hash Mismatch

**Symptom:** Validation shows extract as stale immediately after extraction

**Causes:**

1. **Whitespace differences** - Trailing spaces or line ending variations
2. **Frontmatter included in hash** - Should be excluded
3. **Source file changed during extraction** - Race condition

**Solutions:**

1. **Re-run extraction** - Ensure source is stable
2. **Check source file** - Look for formatting inconsistencies
3. **Report issue** - May indicate script bug if persistent

### Permission Errors

**Symptom:** Cannot write output file

**Solutions:**

1. **Check directory exists** - Create output directory first: `mkdir -p $(dirname output.md)`
2. **Verify write permissions** - Ensure you have write access
3. **Check file locks** - Close any editors with the file open

## Related Guides

- **[Best Practices](../best-practices.md)** - Overall workflow guidance
- **[Technical Details](../technical-details.md)** - Dependencies and file structure
