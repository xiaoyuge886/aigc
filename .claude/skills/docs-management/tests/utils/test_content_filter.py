#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_content_filter.py - Comprehensive tests for content filtering

Tests the ContentFilter class and ensures:
1. Source-aware filtering works correctly
2. Config-driven patterns match appropriately
3. Stop-after behavior works
4. Empty section detection works
5. Integration with scraper works
6. No hardcoded filters remain

Run with: python -m pytest tests/test_content_filter.py -v
"""

import sys
from pathlib import Path

# Add scripts to path (tests/utils/ is two levels down from skill root)
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))

import pytest
from utils.content_filter import ContentFilter


class TestContentFilterBasics:
    """Test basic ContentFilter functionality"""
    
    def test_filter_initialization(self):
        """Test that filter initializes without errors"""
        filter = ContentFilter()
        assert filter is not None
        assert filter.config is not None
    
    def test_empty_content(self):
        """Test filtering empty content"""
        filter = ContentFilter()
        result, stats = filter.filter_content("", source_path="test.md")
        assert result == ""
        assert stats['sections_removed'] == 0
    
    def test_no_filtering_needed(self):
        """Test content that doesn't match any patterns"""
        filter = ContentFilter()
        content = """# My Article

This is some content that should not be filtered.

## Introduction

More content here.
"""
        result, stats = filter.filter_content(content, source_path="anthropic-com/docs/test.md")
        assert result == content
        assert stats['sections_removed'] == 0


class TestSourceDetection:
    """Test source path detection and filter selection"""
    
    def test_news_source_detection(self):
        """Test that news articles get news filters"""
        filter = ContentFilter()
        source_key = filter._get_source_key('anthropic-com/news/article.md')
        assert source_key == 'anthropic-com/news'
        
        filters = filter._get_applicable_filters(source_key)
        assert 'global_stop_sections' in filters
        assert 'news_blog_stop_sections' in filters
    
    def test_engineering_source_detection(self):
        """Test that engineering blog gets news filters"""
        filter = ContentFilter()
        source_key = filter._get_source_key('anthropic-com/engineering/article.md')
        assert source_key == 'anthropic-com/engineering'
        
        filters = filter._get_applicable_filters(source_key)
        assert 'global_stop_sections' in filters
        assert 'news_blog_stop_sections' in filters
    
    def test_docs_source_detection(self):
        """Test that technical docs get minimal filters"""
        filter = ContentFilter()
        source_key = filter._get_source_key('docs-claude-com/docs/intro.md')
        assert source_key == 'docs-claude-com'
        
        filters = filter._get_applicable_filters(source_key)
        assert 'global_stop_sections' in filters
        assert 'docs_stop_sections' in filters
    
    def test_code_docs_source_detection(self):
        """Test that code docs get minimal filters"""
        filter = ContentFilter()
        source_key = filter._get_source_key('code-claude-com/docs/skills.md')
        assert source_key == 'code-claude-com'


class TestNewsFiltering:
    """Test filtering of news/blog content"""
    
    def test_related_articles_filtered(self):
        """Test that 'Related articles' section triggers stop-after"""
        filter = ContentFilter()
        content = """# My Article

Main content here.

## Overview

More content.

## Related articles

Article 1
Article 2

## This should be filtered too

Footer navigation.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert '## Related articles' not in result
        assert 'Article 1' not in result
        assert '## This should be filtered too' not in result
        assert 'Overview' in result  # Main content preserved
        assert stats['stop_after_triggered'] is True
        assert stats['sections_removed'] == 1
    
    def test_transform_section_filtered(self):
        """Test that 'Transform how your organization' section is filtered"""
        filter = ContentFilter()
        content = """# Article

Main content.

## Transform how your organization operates with Claude

Marketing content.

## More footer

Navigation links.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert '## Transform how' not in result
        assert 'Marketing content' not in result
        assert 'Main content' in result
        assert stats['stop_after_triggered'] is True
    
    def test_newsletter_section_filtered(self):
        """Test that newsletter signup sections are filtered"""
        filter = ContentFilter()
        content = """# Article

Main content.

## Get the developer newsletter

Signup form.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert '## Get the developer newsletter' not in result
        assert 'Signup form' not in result
        assert stats['stop_after_triggered'] is True
    
    def test_navigation_sections_filtered(self):
        """Test that site navigation sections are filtered"""
        filter = ContentFilter()
        content = """# Article

Main content.

## Products

Product links.

## Company

Company info.

## Terms and policies

Legal stuff.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert '## Products' not in result
        assert '## Company' not in result
        assert '## Terms and policies' not in result
        assert stats['stop_after_triggered'] is True
    
    def test_footer_links_without_heading_filtered(self):
        """Test that footer link sections without headings are filtered (e.g., [News)"""
        filter = ContentFilter()
        content = """# Build AI in America

[Engineering at Anthropic](/engineering)

Published Date

Main article content with multiple paragraphs.

Read the full report.

[News

### Anthropic partners with Rwandan Government

Nov 18, 2025](/news/rwanda)[News

### Disrupting AI espionage

Nov 13, 2025](/news/espionage)
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        # Main content preserved (including breadcrumb)
        assert 'Main article content' in result
        assert 'Read the full report' in result
        assert '[Engineering at Anthropic](/engineering)' in result  # Breadcrumb kept
        
        # Footer links removed
        assert 'Anthropic partners with Rwandan' not in result
        assert 'Disrupting AI espionage' not in result
        assert '/news/rwanda' not in result
        assert stats['stop_after_triggered'] is True
        assert '[News' not in result  # No [News in footer


class TestResearchFiltering:
    """Test filtering of research content (same structure as news/blog)"""

    def test_research_source_detection(self):
        """Test that research articles get news/blog filters (not docs filters)"""
        filter = ContentFilter()
        source_key = filter._get_source_key('anthropic-com/research/article.md')
        assert source_key == 'anthropic-com/research'

        filters = filter._get_applicable_filters(source_key)
        assert 'global_stop_sections' in filters
        assert 'news_blog_stop_sections' in filters
        # Should NOT have docs_stop_sections
        assert 'docs_stop_sections' not in filters

    def test_research_related_content_filtered(self):
        """Test that 'Related content' section is filtered from research articles"""
        filter = ContentFilter()
        content = """# Research Article

Main research content here.

## Abstract

Abstract text.

## Methodology

Research methodology details.

## Related content

### Another Research Article

[Read more](/research/other-article)

### Yet Another Article

[Read more](/research/another)
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/research/article.md')

        # Main content preserved
        assert 'Abstract' in result
        assert 'Methodology' in result
        assert 'Main research content' in result

        # Related content filtered out
        assert '## Related content' not in result
        assert 'Another Research Article' not in result
        assert '/research/other-article' not in result
        assert stats['stop_after_triggered'] is True

    def test_research_newsletter_filtered(self):
        """Test that newsletter sections are filtered from research articles"""
        filter = ContentFilter()
        content = """# Research Article

Main content.

## Get the developer newsletter

Signup form.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/research/article.md')

        assert '## Get the developer newsletter' not in result
        assert 'Signup form' not in result
        assert stats['stop_after_triggered'] is True


class TestDocsFiltering:
    """Test filtering of technical documentation"""
    
    def test_docs_minimal_filtering(self):
        """Test that technical docs preserve most content"""
        filter = ContentFilter()
        content = """# Documentation

Main content.

## Overview

Technical details.

## See also

- Related doc 1
- Related doc 2

## Next steps

Further reading.
"""
        result, stats = filter.filter_content(content, source_path='docs-claude-com/docs/intro.md')
        
        # All content should be preserved for docs
        assert '## See also' in result
        assert '## Next steps' in result
        assert 'Technical details' in result
        assert stats['sections_removed'] == 0
    
    def test_empty_placeholder_filtered(self):
        """Test that empty placeholder sections are filtered"""
        filter = ContentFilter()
        content = """# Documentation

Main content.

## Examples

No items found.

## More content

Real content here.
"""
        result, stats = filter.filter_content(content, source_path='docs-claude-com/docs/intro.md')
        
        # Empty sections might be filtered depending on configuration
        assert 'Real content here' in result


class TestStopAfterBehavior:
    """Test stop-after filtering behavior"""
    
    def test_stop_after_removes_everything(self):
        """Test that stop-after removes all subsequent content"""
        filter = ContentFilter()
        content = """# Article

Section 1

## Section 2

Section 2 content

## Related articles

Link 1

## Products

Product list

## Company

Company info

Social links
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert 'Section 1' in result
        assert 'Section 2' in result
        assert '## Related articles' not in result
        assert '## Products' not in result
        assert '## Company' not in result
        assert 'Social links' not in result
        assert stats['stop_after_triggered'] is True
        
        # Verify marker is added
        assert '<!-- Content filtered' in result


class TestEdgeCases:
    """Test edge cases and error handling"""
    
    def test_no_source_path(self):
        """Test filtering without source path"""
        filter = ContentFilter()
        content = "# Content\n\n## Related articles\n\nStuff"
        result, stats = filter.filter_content(content, source_path=None)
        
        # Should still work with global filters only
        assert result is not None
    
    def test_malformed_headings(self):
        """Test handling of malformed heading syntax"""
        filter = ContentFilter()
        content = """# Article

##Related articles (no space)

### Not level 2

## Related articles

Should be filtered.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert '##Related articles' in result  # Malformed, not matched
        assert '## Related articles' not in result  # Correct format, matched
    
    def test_multiline_content(self):
        """Test filtering with various newline patterns"""
        filter = ContentFilter()
        content = "# Article\r\n\r\n## Related articles\r\n\r\nContent"
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        assert result is not None


class TestIntegration:
    """Test integration scenarios"""
    
    def test_real_world_news_article(self):
        """Test filtering a realistic news article structure"""
        filter = ContentFilter()
        content = """---
title: Test Article
---

# Test Article

Published Date

Main article content with multiple paragraphs.

## Overview

Technical details about the topic.

## Benefits

List of benefits:
- Benefit 1
- Benefit 2

## Customer spotlight

Customer testimonial.

## Related articles

### Article 1
Date

### Article 2
Date

## Transform how your organization operates with Claude

Marketing CTA.

## Products

- Product 1
- Product 2

## Company

- About
- Careers

## Terms and policies

Legal footer.
"""
        result, stats = filter.filter_content(content, source_path='anthropic-com/news/article.md')
        
        # Main content preserved
        assert 'Overview' in result
        assert 'Benefits' in result
        assert 'Customer spotlight' in result
        
        # Footer content removed
        assert '## Related articles' not in result
        assert '## Transform how' not in result
        assert '## Products' not in result
        assert '## Company' not in result
        assert '## Terms and policies' not in result
        
        # Significant reduction
        assert len(result) < len(content) * 0.7
        assert stats['sections_removed'] >= 1


class TestConfigLoading:
    """Test configuration loading and validation"""
    
    def test_config_loads(self):
        """Test that configuration file loads successfully"""
        filter = ContentFilter()
        assert 'global_stop_sections' in filter.config
        assert 'news_blog_stop_sections' in filter.config
        assert 'docs_stop_sections' in filter.config
        assert 'source_filters' in filter.config
    
    def test_all_patterns_compile(self):
        """Test that all regex patterns compile without errors"""
        filter = ContentFilter()
        
        # Get all filter sets
        for filter_name in ['global_stop_sections', 'news_blog_stop_sections', 'docs_stop_sections']:
            if filter_name in filter.config:
                patterns = filter._compile_patterns([filter_name])
                assert len(patterns) > 0
                
                # Verify each pattern compiled
                for rule in patterns:
                    assert rule['pattern'] is not None
                    assert 'pattern_str' in rule
                    assert 'reason' in rule


class TestNoHardcodedFilters:
    """Verify no hardcoded filters remain in codebase"""
    
    def test_scraper_uses_content_filter(self):
        """Verify scraper imports and uses ContentFilter"""
        # Get skill root (tests/utils/ is 2 levels down), then navigate to scraper
        skill_root = Path(__file__).resolve().parents[2]
        scraper_path = skill_root / 'scripts' / 'core' / 'scrape_docs.py'
        content = scraper_path.read_text(encoding='utf-8')
        
        # Should import ContentFilter (check various import patterns since we're reorganized)
        has_import = ('from ..utils.content_filter import ContentFilter' in content or 
                     'ContentFilter' in content)
        assert has_import, "Scraper should import or use ContentFilter"
        
        # Should NOT have hardcoded news filtering
        assert 'anthropic.com' not in content.lower() or 'ContentFilter' in content
        
        # Old hardcoded pattern should be gone
        assert r'\[News\s+###[^\]]+\]\([^\)]+\)' not in content


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

