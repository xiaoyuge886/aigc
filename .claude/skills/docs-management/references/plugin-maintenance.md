# Plugin Maintenance Guide

This guide covers maintaining and updating the docs-management skill, including scraping updates, version management, and publishing workflows.

## Update Workflow

### Complete Update Cycle

```text
1. Scrape    → Fetch latest docs from official sources
2. Validate  → Run index refresh and validation
3. Review    → Check output for errors, 404s, drift
4. Cleanup   → Remove stale/deleted documents
5. Commit    → Commit with descriptive message
6. Version   → Bump version if significant changes
7. Push      → Push to remote repository
```

### Step-by-Step Commands

#### 1. Scrape Documentation

```bash
# Navigate to skill directory
cd plugins/claude-ecosystem/skills/docs-management

# Scrape all sources (parallel, skip unchanged)
python scripts/core/scrape_all_sources.py --parallel --skip-existing
```

#### 2. Validate and Refresh Index

```bash
# Use Python 3.13 for spaCy compatibility
py -3.13 scripts/management/refresh_index.py
```

#### 3. Check for Drift (Optional)

```bash
# Detect 404s and missing files
py -3.13 scripts/management/refresh_index.py --check-drift

# Auto-cleanup drift
py -3.13 scripts/management/refresh_index.py --check-drift --cleanup-drift
```

#### 4. Commit Changes

```bash
# From repo root
cd /path/to/claude-code-plugins

git add .
git commit -m "docs(docs-management): update scraped documentation

- Refreshed X documents from Y sources
- Added N new documents
- Removed M stale documents"
```

#### 5. Version Bump (If Needed)

Edit `plugins/claude-ecosystem/.claude-plugin/plugin.json`:

```json
{
  "version": "1.1.0"
}
```

#### 6. Push

```bash
git push origin main
```

## Version Management

### Semantic Versioning

Follow semver for plugin versions:

| Change Type | Version Bump | Example |
| --- | --- | --- |
| Documentation refresh (same sources) | Patch | 1.0.0 → 1.0.1 |
| New documentation source added | Minor | 1.0.1 → 1.1.0 |
| New skill features or capabilities | Minor | 1.1.0 → 1.2.0 |
| Breaking changes to skill API | Major | 1.2.0 → 2.0.0 |
| Major restructuring | Major | 2.0.0 → 3.0.0 |

### When to Bump

**Always bump** when:

- Adding new documentation sources
- Significant content changes (100+ docs updated)
- New features or scripts
- Bug fixes that affect behavior

**Skip bump** when:

- Minor documentation refresh (<10 docs)
- Internal-only changes (comments, formatting)
- README updates only

## Testing Before Publishing

### Local Validation Checklist

Before pushing updates:

- [ ] Scrape completed without errors
- [ ] Index refresh completed successfully
- [ ] No unexpected 404s or drift
- [ ] Search queries return expected results
- [ ] doc_id resolution works correctly

### Quick Validation Commands

```bash
# Verify index integrity
python scripts/management/manage_index.py verify

# Test search functionality
python scripts/core/find_docs.py search hooks memory

# Test doc_id resolution
python scripts/core/find_docs.py resolve <known-doc-id>

# Check document count
python scripts/management/manage_index.py count
```

## Changelog Maintenance

### Updating Version History

When making significant changes, update the "Version History" section in SKILL.md:

```markdown
## Version History

- v1.2.0 (2025-12-01): Added new documentation source X
- v1.1.0 (2025-11-29): Initial plugin release
- v1.0.0 (2025-11-28): Migrated from onboarding repo
```

### Commit Message Format

Use conventional commits:

```text
docs(docs-management): brief description

- Bullet point details
- What changed and why
```

Types:

- `docs`: Documentation updates
- `feat`: New features
- `fix`: Bug fixes
- `refactor`: Code restructuring
- `chore`: Maintenance tasks

## Troubleshooting Updates

### Common Issues

**Scrape hangs or times out:**

- Check network connectivity
- Try with `--skip-existing` to skip unchanged docs
- Run sources individually to isolate problem

**Index validation fails:**

- Run `rebuild_index.py` to regenerate from filesystem
- Check for corrupted files in `canonical/`
- Verify Python version (3.13 for spaCy)

**Push rejected:**

- Pull latest changes first: `git pull --rebase`
- Resolve any conflicts
- Push again

### Recovery Commands

```bash
# Rebuild index from scratch
python scripts/management/rebuild_index.py

# Force regenerate metadata
py -3.13 scripts/management/extract_metadata.py --force

# Clean up stale entries
python scripts/maintenance/cleanup_stale.py
```

## Automation (Future)

### GitHub Actions (Planned)

Future automation possibilities:

- Scheduled weekly scraping
- Automated validation on PR
- Version bump automation
- Changelog generation

### Manual Triggers

Until automation is set up, run updates manually:

1. Monthly: Full scrape and validation
2. As needed: When official docs have major updates
3. On request: When users report stale content

## Related Documentation

- **SKILL.md**: Complete skill documentation and commands
- **workflows.md**: General operational workflows
- **troubleshooting.md**: Detailed troubleshooting guide
- **DEPENDENCIES.md**: Script dependency graph

## Last Updated

2025-11-29
