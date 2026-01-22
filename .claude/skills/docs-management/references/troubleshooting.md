# Troubleshooting

## Scraping fails for specific URL

**Symptom:** `scrape_docs.py` errors on specific URL

**Solutions:**

1. Check if URL is accessible (try in browser)
2. Check if content format changed (HTML structure)
3. Check rate limiting (wait and retry)
4. Manual fallback (copy content, add frontmatter manually)

## Section not found during extraction

**Symptom:** `extract_subsection.py` can't find section (internal use)

**Solutions:**

1. List available headings (script shows hierarchy)
2. Check for typos in section title
3. Check if upstream renamed the section
4. Update index.yaml with new section title

## Windows-Specific Issues

### Unicode Encoding Errors (FIXED)

**Symptom:** `UnicodeEncodeError: 'charmap' codec can't encode character` when running scripts

**Status:** ✅ **FIXED** - Scripts now auto-detect Windows and configure UTF-8 encoding

**Previous workaround (no longer needed):**

```bash
# Old approach (before fix)
PYTHONIOENCODING=utf-8 python scripts/core/scrape_docs.py ...
```

**Current behavior:** Scripts work without environment variables on Windows.

### Git Bash Path Conversion

**Symptom:** Filter patterns converted to Windows paths (e.g., `/en/docs/` becomes `C:/Program Files/Git/en/docs/`)

**Status:** ✅ **AUTO-FIXED** - Scripts now automatically detect and correct Git Bash path conversion

**Current behavior:**

- `scrape_docs.py` automatically detects Git Bash path conversion and restores the original pattern
- `scrape_all_sources.py` sets `MSYS_NO_PATHCONV=1` to prevent conversion when calling `scrape_docs.py`
- Scripts work correctly from Git Bash without manual workarounds

**Manual workaround (if needed):** Use `MSYS_NO_PATHCONV=1` environment variable with Git Bash:

```bash
# Manual workaround (usually not needed)
MSYS_NO_PATHCONV=1 python scripts/core/scrape_docs.py \
    --sitemap https://docs.claude.com/sitemap.xml \
    --filter "/en/docs/" \
    --output platform-docs
```

**Alternative:** Use PowerShell or CMD instead of Git Bash (no path conversion issues).

### Expected 404 Errors

**Symptom:** Some URLs return 404 during scraping

**Status:** ✅ **EXPECTED** - Scripts handle gracefully

**Explanation:**

- Docs map may reference docs that don't exist yet
- Upstream docs may be moved/removed
- Scripts log error and continue processing remaining URLs

**Example:**

```text
[14/44] Processing: https://code.claude.com/docs/en/migration-guide.md
❌ Failed to fetch: 404 Client Error: Not Found
[15/44] Processing: https://code.claude.com/docs/en/troubleshooting.md
✅ Saved: .claude\references\claude-code\troubleshooting.md
```

**Action:** None required - this is normal behavior.
