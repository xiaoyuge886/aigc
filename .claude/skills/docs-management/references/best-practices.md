# Best Practices

## Scraping

- ✅ **Discover before scraping** - Use the Documentation Discovery Workflow (see Core Capabilities > Scraping) to identify all available categories. Never assume you know all categories - always discover them from the sitemap.
- ✅ **English-only by default** - Always use `/en/` URL paths (English documentation only). Anthropic documentation is available in multiple languages, but this repository uses English exclusively. Filter patterns must include `/en/` (e.g., `/en/docs/`, `/en/api/`, `/en/resources/`).
- ✅ **Use auto-detection** - Let the script auto-detect output directories from domain names (domain-based folders prevent collisions and are future-proof)
- ✅ **Use sitemaps when available** - Auto-discovery ensures comprehensive coverage
- ✅ **Filter by pattern** - Narrow to specific categories (e.g., `/en/docs/`, `/en/api/`)
- ✅ **Rate limit** - Default 1.5s delay, be polite to servers
- ✅ **Test with --limit** - Validate before scraping hundreds of docs
- ❌ **Don't hardcode paths** - Use discovery workflow instead of assuming categories exist
- ❌ **Don't scrape non-English content** - Only `/en/` paths (no `/fr/`, `/de/`, `/ja/`, etc.)

## Maintenance

- ✅ **Document in SYSTEM-CHANGES.md** - If modifying system configs
- ✅ **Use conventional commits** - `docs: update canonical documentation`
- ✅ **Review before committing** - `git diff` to understand changes
- ❌ **Don't manually edit canonical docs** - Will be overwritten on next scrape

## Troubleshooting

### Scripts Not Found

**Symptom:** `python script_name.py` fails with "No such file or directory"

**Solutions:**

1. **Check current directory** - Scripts must be run from repository root

   ```bash
   cd /path/to/onboarding
   python .claude/skills/docs-management/scripts/script_name.py
   ```

2. **Use full path** - Specify complete path to script

   ```bash
   python .claude/skills/docs-management/scripts/core/scrape_docs.py
   ```

3. **Verify script exists** - Ensure scripts directory is present

   ```bash
   ls .claude/skills/docs-management/scripts/
   ```

### Pip Install Fails

**Symptom:** `pip install pyyaml` or other packages fail

**Solutions:**

1. **Use pip3** - On some systems, use `pip3` instead of `pip`
2. **Check Python version** - Ensure Python 3.7+ is installed
3. **Use virtual environment** - Isolate dependencies

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate   # Windows
   pip install -r .claude/skills/docs-management/requirements.txt
   ```

### Rate Limiting Issues

**Symptom:** Scraping fails with 429 errors or timeouts

**Solutions:**

1. **Increase delay** - Use longer rate limit delay

   ```bash
   python scrape_docs.py --delay 3.0
   ```

2. **Scrape fewer docs** - Use --limit to reduce load

   ```bash
   python scrape_docs.py --limit 10
   ```

3. **Wait and retry** - Rate limits reset after time period

### Unexpected Non-English Content

**Symptom:** Non-English documentation appears in canonical storage

**Solutions:**

1. **Check filter patterns** - Ensure `/en/` is in filters
2. **Use discovery workflow** - Systematically discover only English categories
3. **Clean and re-scrape** - Remove non-English content, re-run with correct filters

   ```bash
   # Remove non-English content
   # Use docs-management skill cleanup tools to remove non-English content

   # Re-scrape with English-only filter
   python scrape_docs.py --filter "/en/"
   ```

## Related Guides

- **[Scraping Guide](capabilities/scraping-guide.md)** - Detailed scraping documentation
- **[Extraction Guide](capabilities/extraction-guide.md)** - Internal subsection extraction
- **[Technical Details](technical-details.md)** - Dependencies and file structure
