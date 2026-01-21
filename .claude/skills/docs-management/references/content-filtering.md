# Content Filtering for Scraped Documentation

## Overview

The content filtering system removes non-primary content (site navigation, marketing sections, footers) from scraped documentation to improve search quality and reduce index pollution.

### Problem Statement

When scraping documentation from websites, the scraper often captures:

- Site navigation menus (Products, Features, Company, etc.)
- Marketing call-to-action sections ("Transform how your organization")
- Newsletter signup forms ("Get the developer newsletter")
- Related articles/cross-links
- Social media links and footers
- Terms and policies sections

These sections pollute the search index, causing irrelevant results. For example, a search for "skills overview" was returning a news article about fine-tuning Claude 3 Haiku simply because it had "Introducing Agent Skills" in its "Related articles" section.

## Solution Design

### Source-Aware Filtering

Different content types require different filtering strategies:

| Source Type | Example | Filtering Strategy |
| --- | --- | --- |
| **News & Blog** | `anthropic-com/news/*` | **Aggressive** - Filter marketing, navigation, related articles |
| **Engineering Blog** | `anthropic-com/engineering/*` | **Aggressive** - Same as news |
| **Technical Docs** | `docs-claude-com/*` | **Conservative** - Only filter empty placeholders |
| **Code Docs** | `code-claude-com/*` | **Conservative** - Only filter empty placeholders |

### Configuration-Driven Approach

All filtering rules are defined in `config/content_filtering.yaml`:

- **Global filters** - Applied to all sources (social media links)
- **Source-specific filters** - Different rules for news vs docs
- **Stop-after behavior** - Everything after certain headings is filtered
- **Empty section detection** - Filter sections with "No items found"

### Filter Behavior

When a filter matches:

1. **Regular filter**: Removes just that section (until next heading at same level)
2. **Stop-after filter**: Removes everything from that heading to end of file
3. **Marker insertion**: Adds `<!-- Content filtered: site navigation/footer -->` comment

## Implementation

### Files Created

1. **`config/content_filtering.yaml`** - Filter configuration
   - Global stop sections
   - News/blog stop sections
   - Docs stop sections
   - Source mapping
   - Behavior configuration

2. **`scripts/content_filter.py`** - Filter implementation
   - `ContentFilter` class for filtering content
   - `filter_file()` function for batch processing
   - CLI for testing and manual filtering

### How It Works

```python
from content_filter import ContentFilter

filter = ContentFilter()
filtered_markdown, stats = filter.filter_content(
    markdown_content, 
    source_path='anthropic-com/news/article.md'
)

print(f"Removed {stats['sections_removed']} sections")
print(f"Reduced from {original_lines} to {filtered_lines} lines")
```

The filter:

1. Determines source type from path (e.g., `anthropic-com/news`)
2. Loads applicable filter sets (global + news_blog_stop_sections)
3. Compiles regex patterns
4. Processes content line-by-line
5. Matches headings against patterns
6. Removes matched sections or stops processing

## Usage

### Test Filtering (Dry Run)

```bash
python scripts/content_filter.py canonical/anthropic-com/news/article.md --dry-run --verbose
```

### Filter a Single File

```bash
python scripts/content_filter.py canonical/anthropic-com/news/article.md
```

### Filter With Output to New File

```bash
python scripts/content_filter.py canonical/anthropic-com/news/article.md -o filtered-article.md
```

## Integration with Scraper

**TODO**: The filter needs to be integrated into `scrape_docs.py` to automatically filter content during scraping.

### Recommended Integration Points

1. **Option A: Filter during scraping** (preferred)
   - Integrate into `fetch_and_save_url()` function
   - Filter content before saving to disk
   - Update index with filtered content

2. **Option B: Filter after scraping**
   - Run as post-processing step
   - Batch filter all files in a directory
   - Rebuild index after filtering

### Integration Code Example

```python
from content_filter import ContentFilter

def fetch_and_save_url(url, output_path, ...):
    # ... existing fetch logic ...
    
    # NEW: Filter content before saving
    if should_filter_content(output_path):
        filter = ContentFilter()
        markdown_content, stats = filter.filter_content(
            markdown_content,
            source_path=get_relative_path(output_path)
        )
        
        if stats['sections_removed'] > 0:
            logger.info(f"Filtered {stats['sections_removed']} sections from {url}")
    
    # ... existing save logic ...
```

## Test Results

### Before Filtering

```text
fine-tune-claude-3-haiku.md:
  - 576 lines
  - 23,996 characters
  - Contains: article content + Related articles + Transform CTA + full site navigation
```

### After Filtering

```text
fine-tune-claude-3-haiku.md:
  - 186 lines (67.7% reduction)
  - 9,036 characters (62.3% reduction)
  - Contains: article content only
  - Removed: 390 lines of navigation/footer
```

## Adding New Filter Rules

To add new filter patterns, edit `config/content_filtering.yaml`:

```yaml
news_blog_stop_sections:
  - pattern: '^## Your New Section Title'
    regex: true  # Required for regex patterns
    stop_after: true  # Optional - stop processing after this
    reason: 'Brief explanation of why this is filtered'
```

Pattern syntax:

- `^` - Start of line
- `##` - Heading level (literal text)
- `\s+` - One or more whitespace
- `?` - Optional character
- `$` - End of line
- Always set `regex: true` for regex patterns

## Future Enhancements

1. **Scraper integration** - Automatic filtering during scraping
2. **Batch filtering tool** - Filter all files in a directory
3. **Index rebuild** - Rebuild index after filtering existing files
4. **Pattern learning** - Detect common navigation patterns automatically
5. **Visual reports** - Show what was filtered with before/after comparison

## Security Considerations

- All regex patterns are compiled safely using `re.compile()`
- No arbitrary code execution
- File operations use UTF-8 encoding
- Backup original files before filtering in production

## Performance

- Filtering is fast: ~100ms for typical news article
- Regex compilation is done once per filter session
- Memory efficient: processes line-by-line
- Scales well to large files

## Troubleshooting

### Patterns Not Matching

1. Check that `regex: true` is set in config
2. Test pattern with online regex tester (regex101.com)
3. Run debug script: `python .claude/temp/debug_filter.py`
4. Check heading format in actual file (spaces, capitalization)

### Too Much Content Filtered

1. Review filter rules for your source type
2. Consider using source-specific rules
3. Remove overly broad patterns
4. Test with `--dry-run` before applying

### Not Enough Content Filtered

1. Check source path detection (see logs)
2. Verify correct filter set is being applied
3. Add new patterns for missing sections
4. Check pattern syntax (regex errors logged)

## Version History

- **1.0 (2025-11-17)**: Initial implementation
  - Source-aware filtering (news vs docs)
  - Stop-after behavior for footer sections
  - Configuration-driven approach
  - CLI tool for testing
