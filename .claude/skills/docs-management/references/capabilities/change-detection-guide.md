# Change Detection

**Purpose:** Detect new and removed documentation pages from sitemaps.

**Script:** `scripts/maintenance/detect_changes.py`

**Capabilities:**

- **New page detection** - Identify URLs in sitemap but not yet indexed
- **Removed page detection** - Find indexed docs no longer in sitemap
- **Stale marking** - Add `status: stale` to frontmatter for manual review
- **Change reporting** - Generate audit logs with before/after comparison
- **CI/CD integration** - Non-zero exit codes when changes detected

**Usage patterns:**

```bash
# Detect changes (dry-run, no modifications)
python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \
                         --filter "docs.claude.com/en/docs"

# Mark removed pages as stale
python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \
                         --filter "docs.claude.com/en/api" \
                         --mark-stale

# Generate change report for audit
python detect_changes.py --sitemap https://docs.claude.com/sitemap.xml \
                         --filter "docs.claude.com/en/docs" \
                         --report
```

**Change detection logic:**

1. Fetch and parse sitemap.xml
2. Apply URL filter (e.g., `/en/docs/`, `/en/api/`)
3. Load index.yaml to get currently indexed URLs
4. Compare sitemap URLs with indexed URLs:
   - **New URLs**: In sitemap but not indexed
   - **Removed URLs**: Indexed but not in sitemap
5. Optionally mark removed docs as `status: stale`
6. Generate change report and write to audit log

**Cleanup workflow:**

After detecting removed pages and marking them as stale, use `cleanup_stale.py` to review and delete:

```bash
# List all stale documents
python cleanup_stale.py --list

# Remove stale documents (with confirmation)
python cleanup_stale.py --remove

# Remove stale documents (no confirmation)
python cleanup_stale.py --remove --force

# Remove stale documents from specific output directory only
python cleanup_stale.py --remove --output {domain-folder}
```

**Cleanup script:** `scripts/maintenance/cleanup_stale.py`

**Cleanup capabilities:**

- **Stale file discovery** - Finds all docs with `status: stale` in frontmatter
- **Metadata display** - Shows URL, last_fetched, marked_stale dates
- **Confirmation prompt** - Requires `yes` confirmation (unless --force)
- **Index updates** - Removes deleted entries from index.yaml
- **Audit logging** - Records all deletions with metadata

**Recommended maintenance schedule:**

- **Weekly or bi-weekly**: Run change detection to identify new/removed pages (Claude documentation updates frequently)
- **As needed**: Review and clean up stale documents marked as stale
- **During active feature development**: May need to run multiple times per week when Anthropic pushes many new features
- **Before major releases**: Ensure documentation is current

**Known limitations:**

- False positives: Temporary sitemap issues may incorrectly mark pages as removed
- Manual review required: Always review stale pages before deletion to avoid losing valid content
