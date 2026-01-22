# Workflows

## Table of Contents

- [Adding New Documentation Source](#adding-new-documentation-source)
- [Scraping Multiple Sources with Validation Checkpoints](#scraping-multiple-sources-with-validation-checkpoints)

---

## Adding New Documentation Source

**Scenario:** Anthropic adds a new documentation category or domain.

**Steps:**

**Linux/macOS:**

```bash
# 1. Discover new category using Documentation Discovery Workflow
curl -s https://docs.claude.com/sitemap.xml | grep -oP 'docs\.claude\.com/en/[^/]+/' | sort -u

# 2. Scrape the new category (auto-detects output directory)
python scripts/core/scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/NEW-CATEGORY/"
# Output automatically goes to: docs-claude-com/NEW-CATEGORY/

# 3. Verify scraping succeeded
ls -la canonical storage (use docs-management skill to access)docs-claude-com/NEW-CATEGORY/
```

**Windows (PowerShell):**

```powershell
# 1. Discover new category using PowerShell
$sitemap = Invoke-WebRequest -Uri "https://docs.claude.com/sitemap.xml" -UseBasicParsing
$sitemap.Content | Select-String -Pattern 'docs\.claude\.com/en/[^/]+/' -AllMatches |
    ForEach-Object { $_.Matches.Value } | Sort-Object -Unique

# 2. Scrape the new category (auto-detects output directory)
pwsh -Command "cd .claude/skills/docs-management; python scripts/core/scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml --filter '/en/NEW-CATEGORY/'"
# Output automatically goes to: docs-claude-com/NEW-CATEGORY/

# 3. Verify scraping succeeded
ls -la canonical storage (use docs-management skill to access)docs-claude-com/NEW-CATEGORY/
```

## Scraping Multiple Sources with Validation Checkpoints

**Scenario:** Scraping documentation from multiple sources (e.g., all docs.claude.com categories, anthropic.com sections, etc.).

**Critical principle:** VALIDATE after EACH source to prevent wasting time/tokens on bad scrapes.

**⚠️ Windows Users:** Use PowerShell for scraping commands to avoid Git Bash path conversion issues. See SKILL.md Platform-Specific Requirements section for details.

**Steps:**

**Linux/macOS:**

```bash
# 1. Scrape FIRST source
python scripts/core/scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/docs/"

# 2. VALIDATE IMMEDIATELY - Do NOT proceed until verified
# Check file count (should match expected number from sitemap output)
find canonical storage (use docs-management skill to access)docs-claude-com/docs -type f -name "*.md" | wc -l

# Check sample files for quality
head -20 canonical storage (use docs-management skill to access)docs-claude-com/docs/about-claude/glossary.md
# Verify:
#   - Frontmatter present (source_url, last_fetched, content_hash, fetch_method)
#   - Content quality (proper markdown, no HTML artifacts)
#   - No path errors (files in correct directory)

# Check for errors in output
# Look for: conversion errors, 404s, malformed frontmatter

# 3. STOP if issues found
# Fix root cause before continuing (wrong filter? path issues? network errors?)
# Delete bad files if needed: rm -rf canonical storage (use docs-management skill to access)docs-claude-com/docs

# 4. ONLY proceed to next source after validation passes

# 5. Scrape SECOND source (repeat validation)
python scripts/core/scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/api/"

# 6. VALIDATE IMMEDIATELY (same checks as step 2)
find canonical storage (use docs-management skill to access)docs-claude-com/api -type f -name "*.md" | wc -l
head -20 canonical storage (use docs-management skill to access)docs-claude-com/api/messages.md

# 7. Repeat for each source with validation checkpoints
```

**Windows (PowerShell):**

```powershell
# 1. Scrape FIRST source
pwsh -Command "cd .claude/skills/docs-management; python scripts/core/scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml --filter '/en/docs/'"

# 2. VALIDATE IMMEDIATELY - Do NOT proceed until verified
# Check file count (should match expected number from sitemap output)
(Get-ChildItem -Path canonical storage (use docs-management skill to access)docs-claude-com/docs -Filter *.md -Recurse -File).Count

# Check sample files for quality
Get-Content canonical storage (use docs-management skill to access)docs-claude-com/docs/about-claude/glossary.md -Head 20
# Verify:
#   - Frontmatter present (source_url, last_fetched, content_hash, fetch_method)
#   - Content quality (proper markdown, no HTML artifacts)
#   - No path errors (files in correct directory)

# Check for errors in output
# Look for: conversion errors, 404s, malformed frontmatter

# 3. STOP if issues found
# Fix root cause before continuing (wrong filter? path issues? network errors?)
# Delete bad files if needed: Remove-Item -Path canonical storage (use docs-management skill to access)docs-claude-com/docs -Recurse -Force

# 4. ONLY proceed to next source after validation passes

# 5. Scrape SECOND source (repeat validation)
pwsh -Command "cd .claude/skills/docs-management; python scripts/core/scrape_docs.py --sitemap https://docs.claude.com/sitemap.xml --filter '/en/api/'"

# 6. VALIDATE IMMEDIATELY (same checks as step 2)
(Get-ChildItem -Path canonical storage (use docs-management skill to access)docs-claude-com/api -Filter *.md -Recurse -File).Count
Get-Content canonical storage (use docs-management skill to access)docs-claude-com/api/messages.md -Head 20

# 7. Repeat for each source with validation checkpoints
```

**Validation checklist (after EACH source):**

- ✅ File count matches expected (compare to sitemap output: "Filtered to X URLs")
- ✅ Files in correct output directory (check domain/category structure)
- ✅ Sample files have valid frontmatter (all required fields present)
- ✅ Content quality is good (clean markdown, no HTML artifacts)
- ✅ No errors in script output (404s, conversion failures, path issues)

**When to STOP and investigate:**

- ❌ File count mismatch (expected 95, got 0 or wrong number)
- ❌ Files in wrong location (path conversion issues, working directory problems)
- ❌ Missing frontmatter fields
- ❌ Poor content quality (HTML not converted, malformed markdown)
- ❌ Errors in script output

**Recovery actions:**

1. **Wrong output location:** Check working directory, use absolute paths, verify `--base-dir`
2. **Path conversion issues (Windows):** Switch from Git Bash to PowerShell
3. **Poor content quality:** Check network connectivity, verify URL patterns
4. **Missing frontmatter:** Script bug - investigate scrape_docs.py logic
5. **File count mismatch:** Wrong filter pattern, network timeout, permission issues

**Why this matters:**

- **Token efficiency:** Don't waste tokens scraping 8 sources if the first one failed
- **Time savings:** Catch issues early rather than debugging at the end
- **Quality assurance:** Ensure each source produces valid output before moving on
- **Error isolation:** Know exactly which source caused problems
