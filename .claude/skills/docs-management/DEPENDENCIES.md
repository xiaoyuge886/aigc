# Script Dependencies and Execution Order

This document describes the dependency graph, prerequisites, and recommended execution order for all scripts in the docs-management skill.

## Overview

The docs-management skill consists of multiple scripts that can run independently or as part of orchestrated workflows. Understanding dependencies helps ensure scripts run in the correct order and have required prerequisites.

## Dependency Graph

```text
┌─────────────────────────────────────────────────────────────┐
│                    Core Utilities                            │
│  (config_loader, http_utils, logging_utils, script_utils)   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Index Management Scripts                       │
│  (index_manager, manage_index, rebuild_index)              │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Scraping Scripts                                │
│  (scrape_docs, scrape_all_sources)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Validation & Drift Detection                    │
│  (detect_changes, cleanup_drift)                             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Orchestration Scripts                           │
│  (refresh_index)                                             │
└─────────────────────────────────────────────────────────────┘
```

## Script Categories

### Core Utilities (No Dependencies)

These scripts provide shared functionality and have no dependencies on other scripts:

- **config_loader.py** - Configuration loading (sources.json, filtering.yaml, tag_detection.yaml)
- **http_utils.py** - HTTP fetching with retry logic
- **logging_utils.py** - Logging and observability
- **script_utils.py** - Common script utilities (UTF-8 config, YAML checks)
- **common_paths.py** - Path resolution utilities
- **cli_utils.py** - CLI argument helpers
- **metadata_utils.py** - Metadata normalization utilities

**Prerequisites:**

- Python 3.7+
- pyyaml (for config_loader)
- requests (for http_utils)

### Index Management Scripts

These scripts manage the index.yaml file:

- **index_manager.py** - Low-level index operations (load, update, remove entries)
- **manage_index.py** - High-level index operations (add keywords, tags, extract metadata)
- **rebuild_index.py** - Rebuild index from filesystem
- **verify_index.py** - Verify index integrity

**Dependencies:**

- Core utilities (config_loader, logging_utils, script_utils)
- index_manager.py

**Prerequisites:**

- `canonical/index.yaml` (created automatically if missing)
- `canonical/` directory structure

**Execution Order:**

1. `rebuild_index.py` - Rebuild index from filesystem (handles renames/moves)
2. `manage_index.py extract-keywords` - Extract keywords and metadata
3. `verify_index.py` - Verify integrity

### Scraping Scripts

These scripts fetch documentation from remote sources:

- **scrape_docs.py** - Scrape single source (sitemap or docs map)
- **scrape_all_sources.py** - Orchestrate scraping from multiple sources

**Dependencies:**

- Core utilities (http_utils, logging_utils, script_utils, config_loader)
- index_manager.py (for updating index during scraping)
- scrape_docs.py (used by scrape_all_sources.py)

**Prerequisites:**

- `sources.json` configuration file
- Network access to documentation sources
- `canonical/` directory (created automatically)

**Execution Order:**

1. `scrape_all_sources.py` - Scrapes all configured sources
   - Internally calls `scrape_docs.py` for each source
   - Updates index.yaml during scraping

### Validation & Drift Detection Scripts

These scripts validate documentation and detect drift:

- **validate_scraped_docs.py** - Validate scraped documentation
- **validate_index_vs_docs.py** - Validate index metadata against actual docs
- **detect_changes.py** - Detect new/removed pages from sitemaps
- **cleanup_drift.py** - Clean up stale documentation (404s, missing files)

**Dependencies:**

- Core utilities
- index_manager.py
- detect_changes.py (used by cleanup_drift.py)

**Prerequisites:**

- `canonical/index.yaml` (for validation)
- `canonical/` directory with scraped docs (for validation)
- Network access (for drift detection)

**Execution Order:**

1. `detect_changes.py` - Detect drift (404s, hash mismatches)
2. `cleanup_drift.py` - Clean up detected drift
3. `validate_index_vs_docs.py` - Validate index metadata

### Metadata & Analysis Scripts

These scripts analyze and manage metadata:

- **extract_metadata.py** - Extract metadata from documents
- **extract_publication_dates.py** - Extract publication dates
- **keyword_stats.py** - Analyze keyword statistics
- **generate_report.py** - Generate comprehensive metadata reports

**Dependencies:**

- Core utilities
- index_manager.py

**Prerequisites:**

- `canonical/index.yaml`
- `canonical/` directory with docs

### Discovery & Resolution Scripts

These scripts help find and resolve documentation:

- **discover_categories.py** - Discover categories from sitemaps
- **find_docs.py** - Find documents by keywords, tags, or natural language
- **doc_resolver.py** - Resolve doc_id to file paths

**Dependencies:**

- Core utilities
- index_manager.py

**Prerequisites:**

- `canonical/index.yaml`

### Orchestration Scripts

These scripts orchestrate multiple operations:

- **refresh_index.py** - Full index refresh workflow (rebuild → extract keywords → validate)

**Dependencies:**

- All scripts in their respective categories

**Prerequisites:**

- All prerequisites from dependent scripts

**Execution Order:**

1. `refresh_index.py` - Refresh index without scraping

### Utility Scripts

These scripts provide setup and maintenance utilities:

- **setup_dependencies.py** - Install required dependencies
- **setup_references.py** - Setup references directory structure
- **check_dependencies.py** - Check if dependencies are installed
- **check_spacy_model_location.py** - Check spaCy model location
- **audit_performance.py** - Audit script performance
- **quick_validate.py** - Quick validation of scraped docs

**Dependencies:**

- Core utilities

**Prerequisites:**

- Python 3.7+

## Common Workflows

### Initial Setup

```bash
# 1. Check dependencies
python scripts/setup/check_dependencies.py

# 2. Install dependencies if needed
python scripts/setup/setup_dependencies.py --install-required

# 3. Setup references directory
python scripts/setup/setup_references.py

# 4. Scrape all sources
python scripts/core/scrape_all_sources.py --config sources.json

# 5. Refresh index
python scripts/management/refresh_index.py
```

### Regular Maintenance

```bash
# 1. Scrape all sources (with skip-existing for speed)
python scripts/core/scrape_all_sources.py --config sources.json --skip-existing --detect-drift

# 2. Refresh index
python scripts/management/refresh_index.py

# 3. Validate
python scripts/validation/validate_index_vs_docs.py --summary-only
```

### Drift Detection & Cleanup

```bash
# 1. Detect drift (dry-run)
python scripts/maintenance/detect_changes.py --sitemap <sitemap_url> --filter <pattern> --output <subdir> --check-404s --check-hashes

# 2. Cleanup drift (dry-run first)
python scripts/maintenance/cleanup_drift.py --base-dir .claude/skills/docs-management/canonical --dry-run --full-cleanup

# 3. Cleanup drift (live)
python scripts/maintenance/cleanup_drift.py --base-dir .claude/skills/docs-management/canonical --full-cleanup --audit-log
```

### Index Refresh Workflow

```bash
# Refresh index (rebuild → extract keywords → validate)
python scripts/management/refresh_index.py
```

## Prerequisites by Script

### Required Files

- **sources.json** - Required by: `scrape_all_sources.py`
- **config/filtering.yaml** - Required by: `config_loader.py`, `extract_metadata.py`
- **config/tag_detection.yaml** - Required by: `config_loader.py`, `extract_metadata.py`
- **config/defaults.yaml** - Required by: `config_registry.py` (optional, has fallbacks)
- **canonical/index.yaml** - Required by: Most scripts (created automatically)

### Required Directories

- **canonical/** - Base directory for canonical docs (created automatically)
- **canonical/{domain}/{category}/** - Domain/category subdirectories (created during scraping)

### Required Python Packages

**Required:**

- pyyaml >= 6.0
- requests >= 2.28.0
- beautifulsoup4 >= 4.11.0
- markdownify >= 0.11.6

**Optional (recommended):**

- spacy >= 3.7.0 (for enhanced keyword extraction)
  - **spaCy Model**: Install `en_core_web_sm` version 3.7.1 or later
  - Install with: `python -m spacy download en_core_web_sm`
  - Check version: `python -m spacy info en_core_web_sm`
  - **Why version matters**: Different model versions may have different stop word lists, affecting keyword extraction consistency across environments
- yake >= 0.4.8 (for enhanced keyword extraction)
- ruamel.yaml (for better YAML handling in index_manager)

**Fallback behavior without optional libraries:**

- Without spaCy: Uses comprehensive static English stop word list (326 words, matching spaCy 3.7+ list)
- Without YAKE: Falls back to heading/content-based keyword extraction
- Scripts work fully without optional dependencies, with reduced keyword extraction quality

### Network Requirements

- Internet access for scraping from remote sources
- Access to documentation sitemaps and docs maps
- Access to source URLs for drift detection

## Execution Order Recommendations

### First-Time Setup

1. `check_dependencies.py` - Verify dependencies
2. `setup_dependencies.py` - Install dependencies
3. `setup_references.py` - Setup directory structure
4. `scrape_all_sources.py` - Scrape all sources
5. `refresh_index.py` - Build index

### Regular Updates

1. `scrape_all_sources.py --skip-existing` - Update changed docs
2. `refresh_index.py` - Update index
3. `validate_index_vs_docs.py` - Validate metadata

### Quarterly Maintenance

1. `scrape_all_sources.py` - Full re-scrape
2. `detect_changes.py --check-404s --check-hashes` - Detect drift
3. `cleanup_drift.py` - Clean up drift
4. `refresh_index.py` - Rebuild index

## Script Independence

Most scripts can run independently if prerequisites are met:

- **Scraping scripts** - Can run without index (will create minimal entries)
- **Index scripts** - Can run without scraping (rebuilds from filesystem)
- **Validation scripts** - Can run independently (read-only operations)
- **Drift detection** - Can run independently (requires index and network)

## Error Handling

All scripts should:

- Check prerequisites before execution
- Provide helpful error messages
- Exit with appropriate exit codes (0 = success, non-zero = failure)
- Support dry-run modes where applicable

## Notes

- Scripts use `index_manager.py` for large file support (index.yaml may exceed token limits)
- Configuration can be overridden via environment variables (see config_registry.py)
- Most scripts support `--base-dir` argument for custom base directory
- Parallel execution is available for multi-source operations
- Dry-run modes are available for destructive operations
